import base64
import json
import re
from time import sleep
from typing import Any, Dict

from google.genai import types

from app.services.gemini_client import client
from app.utils.pdf import pdf_to_images


ANSWER_PROMPT = """
You are an expert exam-sheet vision AI.

Your task is to analyze a student's handwritten answer sheet and extract
EVERY answer that the student actually wrote.

IMPORTANT:
The question paper is NOT available here. You only have the student's
answer sheet. Therefore, NEVER invent a question number or answer.

==================================================
QUESTION NUMBER DETECTION
==================================================

Detect question numbers written by the student.

Examples of valid forms:

Q1
Q.1
Q 1
1
1.
Ans 1
Answer 1
Q1(a)
Q1 (a)
1(a)
1 (a)
1-a
1.a
1[a]
Q5(b)
5(b)
5b
11(ii)
11(ii)
11.2

Normalize question numbers to this format:

1       -> "1"
Q1      -> "1"
1.      -> "1"

1(a)    -> "1(a)"
1 (a)   -> "1(a)"
1.a     -> "1(a)"
1-a     -> "1(a)"
1[a]    -> "1(a)"
1b      -> "1(b)"

Roman numerals must be converted:

1(i)    -> "1(a)"
1(ii)   -> "1(b)"
1(iii)  -> "1(c)"
1(iv)   -> "1(d)"

Numeric subparts:

1.1 -> "1(a)"
1.2 -> "1(b)"
1.3 -> "1(c)"

DO NOT guess a number from the position of an answer.

If the student clearly starts an answer but there is no visible question
number, use:

"question_number": null

==================================================
ANSWER SEGMENTATION
==================================================

Create ONE answer object for each distinct answer.

An answer normally starts when:

- A new question number is written.
- A new sub-question is written.
- The student clearly starts answering another question.

Everything written after that question number belongs to that answer until
the next clearly identifiable question number.

Do NOT split one answer into multiple answers simply because:

- there are multiple paragraphs
- the answer continues on another page
- there is a diagram
- there is a table
- there is a large blank space

If the same answer continues onto another page, keep it as ONE answer object
and add another region to its "regions" array.

==================================================
ANSWER TEXT
==================================================

Transcribe the student's answer as accurately as possible.

Preserve:

- important technical terms
- equations
- numbers
- bullet points
- headings
- definitions
- formulas
- meaningful diagram labels

Do not rewrite the student's answer into better English.

Do not correct spelling unless the handwritten word is completely
unreadable.

If part of the handwriting is unreadable, use the best visual transcription
possible without inventing content.

Do NOT include the question text unless the student actually wrote it.

==================================================
BBOX / HIGHLIGHTING
==================================================

For every answer, identify ALL physical regions belonging to that answer.

Coordinates MUST be normalized from 0 to 1000.

The coordinate system is:

x = horizontal position from LEFT to RIGHT
y = vertical position from TOP to BOTTOM

bbox:

{
  "x": integer,
  "y": integer,
  "width": integer,
  "height": integer
}

The bbox must cover the actual handwritten answer content.

Do NOT return the entire page as the bbox.

Do NOT include unrelated answers.

Include diagrams, tables, formulas, and answer text when they belong to
that answer.

If an answer continues onto another page, create another region:

{
  "page": 2,
  "bbox": {...}
}

==================================================
PAGE NUMBERS
==================================================

Use the actual image/page number supplied with each page.

Page numbers start at 1.

==================================================
ANSWER ID
==================================================

Generate sequential IDs:

a1
a2
a3
a4
...

The IDs must be unique.

==================================================
IMPORTANT ACCURACY RULES
==================================================

1. Extract EVERY visible answer.
2. Preserve the student's actual order on the answer sheet.
3. Answers may be OUT OF ORDER.
4. Do NOT assume answers are sequential.
5. Do NOT create answers that do not exist.
6. Do NOT merge different numbered questions.
7. Do NOT split one numbered answer unnecessarily.
8. If no question number is visible, use null.
9. Use normalized question numbers.
10. Bounding boxes must be normalized 0-1000.
11. Return valid JSON only.
12. Do not include markdown.
13. Do not include explanations outside JSON.

==================================================
OUTPUT FORMAT
==================================================

Return exactly:

{
  "answers": [
    {
      "answer_id": "a1",
      "question_number": "1",
      "text": "Student's answer text",
      "regions": [
        {
          "page": 1,
          "bbox": {
            "x": 80,
            "y": 150,
            "width": 840,
            "height": 320
          }
        }
      ]
    }
  ]
}

If there are no detectable answers:

{
  "answers": []
}
"""


def clean_json_text(text: str) -> str:
    """
    Remove markdown code fences if Gemini returns them.
    """
    if not text:
        return ""

    text = text.strip()

    match = re.search(
        r"```(?:json)?\s*([\s\S]*?)\s*```",
        text,
        flags=re.IGNORECASE,
    )

    if match:
        return match.group(1).strip()

    return text


def normalize_answer_number(value: Any):
    """
    Normalize question numbers returned by Gemini.

    Examples:
        Q1       -> 1
        Q.1      -> 1
        1.       -> 1
        Q1(a)    -> 1(a)
        1-a      -> 1(a)
        1.2      -> 1(b)
        1(ii)    -> 1(b)
    """

    if value is None:
        return None

    value = str(value).strip().lower()

    if not value:
        return None

    # Remove prefixes.
    value = re.sub(
        r"^(question|ques|que|answer|ans|q)\.?\s*",
        "",
        value,
    )

    # Remove spaces.
    value = re.sub(r"\s+", "", value)

    # Remove trailing punctuation.
    value = value.rstrip(".")

    roman_map = {
        "i": "a",
        "ii": "b",
        "iii": "c",
        "iv": "d",
        "v": "e",
        "vi": "f",
        "vii": "g",
        "viii": "h",
    }

    # 1(a), 1[a], 1-a, 1.a, 1a, 1(ii)
    match = re.match(
        r"^(\d+)[\(\[\.\-_]?([a-z]+|[ivx]+)[\)\]]?$",
        value,
    )

    if match:
        number = match.group(1)
        sub = match.group(2)

        if sub in roman_map:
            sub = roman_map[sub]

        # Only accept a single alphabetic subpart.
        if len(sub) == 1 and sub.isalpha():
            return f"{number}({sub})"

    # 1.1, 1.2, 1.3
    match = re.match(r"^(\d+)\.(\d+)$", value)

    if match:
        number = match.group(1)
        sub_number = int(match.group(2))

        if 1 <= sub_number <= 26:
            sub = chr(ord("a") + sub_number - 1)
            return f"{number}({sub})"

    # Plain number.
    match = re.match(r"^(\d+)$", value)

    if match:
        return match.group(1)

    return value


def sanitize_bbox(bbox: Dict[str, Any]) -> Dict[str, int]:
    """
    Keep bounding box values inside normalized 0-1000 coordinates.
    """

    if not isinstance(bbox, dict):
        return {
            "x": 0,
            "y": 0,
            "width": 1000,
            "height": 1000,
        }

    def safe_int(value, default=0):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default

    x = safe_int(bbox.get("x"))
    y = safe_int(bbox.get("y"))
    width = safe_int(bbox.get("width"))
    height = safe_int(bbox.get("height"))

    x = max(0, min(1000, x))
    y = max(0, min(1000, y))

    width = max(0, min(1000 - x, width))
    height = max(0, min(1000 - y, height))

    return {
        "x": x,
        "y": y,
        "width": width,
        "height": height,
    }


def sanitize_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and normalize Gemini's answer extraction result before
    sending it to the mapping/highlighting stages.
    """

    if not isinstance(result, dict):
        return {"answers": []}

    raw_answers = result.get("answers", [])

    if not isinstance(raw_answers, list):
        return {"answers": []}

    answers = []

    for index, answer in enumerate(raw_answers, start=1):

        if not isinstance(answer, dict):
            continue

        answer_id = answer.get("answer_id")

        if not answer_id:
            answer_id = f"a{index}"

        question_number = normalize_answer_number(
            answer.get("question_number")
        )

        text = answer.get("text", "")

        if text is None:
            text = ""

        text = str(text).strip()

        raw_regions = answer.get("regions", [])

        if not isinstance(raw_regions, list):
            raw_regions = []

        regions = []

        for region in raw_regions:

            if not isinstance(region, dict):
                continue

            page = region.get("page", 1)

            try:
                page = int(page)
            except (TypeError, ValueError):
                page = 1

            if page < 1:
                page = 1

            bbox = sanitize_bbox(
                region.get("bbox", {})
            )

            regions.append(
                {
                    "page": page,
                    "bbox": bbox,
                }
            )

        answers.append(
            {
                "answer_id": str(answer_id),
                "question_number": question_number,
                "text": text,
                "regions": regions,
            }
        )

    return {
        "answers": answers
    }


def extract_answers(
    file_bytes: bytes,
    content_type: str,
):
    """
    Extract handwritten answers from an image or PDF using Gemini vision.
    """

    contents = [ANSWER_PROMPT]

    if content_type == "application/pdf":

        pages = pdf_to_images(file_bytes)

        for page in pages:

            page_number = page["page"]

            image_bytes = base64.b64decode(
                page["image"]
            )

            contents.append(
                f"""
IMPORTANT PAGE REFERENCE:

This image is page {page_number} of the student's answer sheet.

All bounding boxes detected on this image MUST use:
page = {page_number}

Coordinates must be normalized from 0 to 1000.
"""
            )

            contents.append(
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/png",
                )
            )

    else:

        contents.append(
            """
IMPORTANT PAGE REFERENCE:

This is page 1 of the student's answer sheet.

All bounding boxes detected on this image MUST use:
page = 1

Coordinates must be normalized from 0 to 1000.
"""
        )

        contents.append(
            types.Part.from_bytes(
                data=file_bytes,
                mime_type=content_type or "image/jpeg",
            )
        )

    last_error = None

    for attempt in range(3):

        try:

            print(
                f"\n========== ANSWER EXTRACTION "
                f"ATTEMPT {attempt + 1}/3 =========="
            )

            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0,
                ),
            )

            raw = clean_json_text(
                response.text
            )

            print(
                "\n========== GEMINI ANSWER EXTRACTION =========="
            )
            print(raw)
            print(
                "==============================================\n"
            )

            result = json.loads(raw)

            result = sanitize_result(result)

            print(
                "========== SANITIZED ANSWERS =========="
            )

            for answer in result["answers"]:

                print(
                    f'{answer["answer_id"]} | '
                    f'Q={answer["question_number"]} | '
                    f'regions={len(answer["regions"])} | '
                    f'text={answer["text"][:100]}'
                )

            print(
                "========================================\n"
            )

            return result

        except json.JSONDecodeError as error:

            last_error = error

            print(
                "Gemini returned invalid JSON: "
                + str(error)
            )

            if attempt < 2:
                sleep((attempt + 1) * 3)

        except Exception as error:

            last_error = error

            error_message = str(error)

            print(
                f"Gemini answer extraction attempt "
                f"{attempt + 1}/3 failed: "
                f"{error_message}"
            )

            # Do not retry quota/rate-limit errors.
            if (
                "429" in error_message
                or "RESOURCE_EXHAUSTED" in error_message
            ):
                print(
                    "Gemini quota/rate limit reached. "
                    "Stopping retries immediately."
                )
                raise error

            if attempt < 2:
                sleep((attempt + 1) * 3)

    if last_error:
        raise last_error

    raise RuntimeError(
        "Answer extraction failed without an exception."
    )