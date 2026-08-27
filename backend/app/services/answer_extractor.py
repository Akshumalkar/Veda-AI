import base64
import json
import re
from time import sleep
from typing import Any, Dict, List

from app.services.groq_client import call_vision
from app.utils.pdf import pdf_to_images


ANSWER_PROMPT = """
You are an expert examination answer-sheet vision AI.

Analyze ONLY the student's handwritten answer sheet.

Your task is to extract EVERY answer that the student actually wrote.

IMPORTANT:
- The question paper is NOT available.
- Do NOT invent questions.
- Do NOT invent question numbers.
- Do NOT assume answers are sequential.
- Answers may be written out of order.
- An answer can continue onto another page.
- A student may leave questions unanswered.
- Extract only content actually visible in the student's answer sheet.

QUESTION NUMBER DETECTION
-------------------------

Detect question numbers written by the student.

Examples:

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
11.2

Normalize them:

Q1 -> "1"
Q.1 -> "1"
1. -> "1"

1(a) -> "1(a)"
1 (a) -> "1(a)"
1.a -> "1(a)"
1-a -> "1(a)"
1[a] -> "1(a)"
1b -> "1(b)"

Roman numerals:

1(i) -> "1(a)"
1(ii) -> "1(b)"
1(iii) -> "1(c)"
1(iv) -> "1(d)"

Numeric subparts:

1.1 -> "1(a)"
1.2 -> "1(b)"
1.3 -> "1(c)"

If there is clearly an answer but NO visible question number:

"question_number": null

NEVER guess the question number.

ANSWER SEGMENTATION
-------------------

Create ONE answer object for each distinct answer.

A new answer normally begins when:

- a new question number appears
- a new sub-question appears
- the student clearly begins answering another question

Everything after that belongs to the same answer until the next clearly identifiable question number.

DO NOT split an answer because of:

- paragraphs
- blank spaces
- formulas
- diagrams
- tables
- headings
- page breaks

If an answer continues onto another page, keep it as ONE answer
and add another region to the regions array.

ANSWER TEXT
-----------

Transcribe what the student actually wrote.

Preserve:

- technical terms
- equations
- chemical equations
- formulas
- numerical calculations
- units
- definitions
- headings
- bullet points
- diagram labels
- mathematical symbols

Do NOT improve the student's English.

Do NOT rewrite the student's answer.

Do NOT correct spelling unless completely unreadable.

Do NOT include question text unless the student actually wrote it.

DIAGRAMS
--------

If the student drew a diagram:

- keep the diagram as part of the answer
- include the diagram inside the answer region
- preserve meaningful labels
- do NOT invent labels
- do NOT describe a diagram that does not exist

BBOX
----

For EVERY answer identify ALL physical regions belonging to that answer.

Coordinates MUST be normalized from 0 to 1000.

Coordinate system:

x = left to right
y = top to bottom

The bbox must cover the actual handwritten content.

Do NOT return the entire page as the bbox.

Include:

- answer text
- formulas
- calculations
- diagrams
- tables
- labels

when they belong to that answer.

PAGE NUMBER
-----------

Use the actual page number supplied with the image.

Page numbers start at 1.

ACCURACY RULES
--------------

1. Extract EVERY visible answer.
2. Preserve student's answer-sheet order.
3. Answers can be out of order.
4. Never assume sequential numbering.
5. Never invent answers.
6. Never invent question numbers.
7. Do not merge separate numbered answers.
8. Do not unnecessarily split one answer.
9. Use null if question number is not visible.
10. Bounding boxes must use 0-1000 coordinates.
11. Include diagrams and formulas.
12. Return valid JSON only.
13. Do not return markdown.
14. Do not return explanations.

OUTPUT FORMAT
-------------

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

If no answers are detected:

{
  "answers": []
}
"""


def clean_json_text(text: str) -> str:
    """Clean model output before JSON parsing."""

    if not text:
        return ""

    text = str(text).strip()

    text = re.sub(
        r"<think>[\s\S]*?</think>",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()

    if "<think>" in text.lower():
        text = re.sub(
            r"<think>[\s\S]*",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()

    match = re.search(
        r"```(?:json)?\s*([\s\S]*?)\s*```",
        text,
        flags=re.IGNORECASE,
    )

    if match:
        text = match.group(1).strip()

    first = text.find("{")
    last = text.rfind("}")

    if first != -1 and last != -1 and last > first:
        text = text[first:last + 1]

    return text.strip()


def parse_json_response(text: str) -> Dict[str, Any]:
    """Safely parse JSON returned by Groq."""

    cleaned = clean_json_text(text)

    if not cleaned:
        raise ValueError(
            "Groq returned an empty JSON response."
        )

    try:
        result = json.loads(cleaned)

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid JSON returned by Groq: {error}"
        ) from error

    if not isinstance(result, dict):
        raise ValueError(
            "Groq JSON response is not an object."
        )

    return result


def image_to_data_url(
    image_bytes: bytes,
    mime_type: str = "image/png",
) -> str:
    """Convert image bytes into a base64 data URL."""

    encoded = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"


def normalize_answer_number(value: Any):
    """Normalize handwritten question numbers."""

    if value is None:
        return None

    value = str(value).strip().lower()

    if not value:
        return None

    value = re.sub(
        r"^(question|ques|que|answer|ans|q)\.?\s*",
        "",
        value,
    )

    value = re.sub(
        r"\s+",
        "",
        value,
    )

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

    match = re.match(
        r"^(\d+)\.(\d+)$",
        value,
    )

    if match:
        number = match.group(1)
        sub_number = int(match.group(2))

        if 1 <= sub_number <= 26:
            sub = chr(
                ord("a") + sub_number - 1
            )
            return f"{number}({sub})"

    match = re.match(
        r"^(\d+)[\(\[\.\-_]?([a-z]+|[ivx]+)[\)\]]?$",
        value,
    )

    if match:
        number = match.group(1)
        sub = match.group(2)

        if sub in roman_map:
            sub = roman_map[sub]

        if len(sub) == 1 and sub.isalpha():
            return f"{number}({sub})"

    match = re.match(
        r"^(\d+)$",
        value,
    )

    if match:
        return match.group(1)

    return value


def safe_int(
    value: Any,
    default: int = 0,
) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def sanitize_bbox(
    bbox: Dict[str, Any],
) -> Dict[str, int]:
    """Keep bbox values inside 0-1000."""

    if not isinstance(bbox, dict):
        return {
            "x": 0,
            "y": 0,
            "width": 1000,
            "height": 1000,
        }

    x = safe_int(bbox.get("x"), 0)
    y = safe_int(bbox.get("y"), 0)
    width = safe_int(bbox.get("width"), 0)
    height = safe_int(bbox.get("height"), 0)

    x = max(0, min(1000, x))
    y = max(0, min(1000, y))

    width = max(
        0,
        min(1000 - x, width),
    )

    height = max(
        0,
        min(1000 - y, height),
    )

    return {
        "x": x,
        "y": y,
        "width": width,
        "height": height,
    }


def sanitize_result(
    result: Dict[str, Any],
) -> Dict[str, Any]:
    """Validate and normalize extracted answers."""

    if not isinstance(result, dict):
        return {"answers": []}

    raw_answers = result.get(
        "answers",
        [],
    )

    if not isinstance(raw_answers, list):
        return {"answers": []}

    answers = []

    for index, answer in enumerate(
        raw_answers,
        start=1,
    ):
        if not isinstance(answer, dict):
            continue

        question_number = normalize_answer_number(
            answer.get("question_number")
        )

        text = answer.get("text", "")

        if text is None:
            text = ""

        text = str(text).strip()

        raw_regions = answer.get(
            "regions",
            [],
        )

        if not isinstance(raw_regions, list):
            raw_regions = []

        regions = []

        for region in raw_regions:
            if not isinstance(region, dict):
                continue

            page = safe_int(
                region.get("page"),
                1,
            )

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

        if not text and not regions:
            continue

        answers.append(
            {
                "answer_id": f"a{index}",
                "question_number": question_number,
                "text": text,
                "regions": regions,
            }
        )

    for index, answer in enumerate(
        answers,
        start=1,
    ):
        answer["answer_id"] = f"a{index}"

    return {
        "answers": answers
    }


def is_rate_limit_error(
    error: Exception,
) -> bool:
    """Detect Groq rate-limit errors."""

    message = str(error).lower()

    return (
        "429" in message
        or "rate_limit" in message
        or "rate limit" in message
        or "tokens per day" in message
        or "tokens per minute" in message
    )


def extract_answers_from_page(
    image_bytes: bytes,
    page_number: int,
    mime_type: str = "image/png",
):
    """Extract handwritten answers from one page."""

    page_prompt = (
        ANSWER_PROMPT
        + "\n\n"
        + f"This is page {page_number} "
        + "of the student's answer sheet.\n"
        + f"Every region MUST use page={page_number}.\n"
        + "Do not use another page number.\n"
        + "Coordinates MUST be normalized from 0 to 1000.\n"
        + "Return ONLY valid JSON."
    )

    message_content = [
        {
            "type": "text",
            "text": page_prompt,
        },
        {
            "type": "image_url",
            "image_url": {
                "url": image_to_data_url(
                    image_bytes,
                    mime_type,
                )
            },
        },
    ]

    last_error = None

    for attempt in range(3):
        try:
            print(
                "\n========== ANSWER EXTRACTION "
                f"PAGE {page_number} "
                f"ATTEMPT {attempt + 1}/3 =========="
            )

            response = call_vision(
                messages=[
                    {
                        "role": "user",
                        "content": message_content,
                    }
                ],
                temperature=0,
                max_tokens=3500,
            )

            raw = (
                response
                .choices[0]
                .message
                .content
            )

            print(
                "\n========== GROQ ANSWER PAGE "
                f"{page_number} =========="
            )

            print(raw)

            print(
                "========================================\n"
            )

            result = parse_json_response(raw)

            return sanitize_result(result)

        except Exception as error:
            last_error = error

            print(
                "Groq answer extraction "
                f"page {page_number} "
                f"attempt {attempt + 1}/3 failed: "
                f"{error}"
            )

            # call_vision() should already handle
            # vision-model fallback.
            if is_rate_limit_error(error):
                print(
                    "Groq rate limit reached. "
                    "Stopping retries immediately."
                )
                raise

            # Retry malformed JSON or temporary failures.
            if attempt < 2:
                wait_seconds = (
                    attempt + 1
                ) * 3

                print(
                    "Retrying answer extraction "
                    f"in {wait_seconds} seconds..."
                )

                sleep(wait_seconds)

    if last_error:
        raise last_error

    raise RuntimeError(
        "Answer extraction failed "
        f"for page {page_number}."
    )


def extract_answers(
    file_bytes: bytes,
    content_type: str,
):
    """
    Extract all handwritten answers.

    PDFs are processed one page at a time.
    Images are treated as page 1.
    """

    all_answers: List[
        Dict[str, Any]
    ] = []

    # =========================================================
    # PDF
    # =========================================================

    if content_type == "application/pdf":

        pages = pdf_to_images(
            file_bytes
        )

        if not pages:
            return {
                "answers": []
            }

        print(
            "\nStudent answer sheet contains "
            f"{len(pages)} page(s)."
        )

        for page in pages:

            page_number = page["page"]

            image_bytes = base64.b64decode(
                page["image"]
            )

            page_result = (
                extract_answers_from_page(
                    image_bytes=image_bytes,
                    page_number=page_number,
                    mime_type="image/png",
                )
            )

            page_answers = (
                page_result.get(
                    "answers",
                    [],
                )
            )

            print(
                f"Page {page_number}: "
                f"{len(page_answers)} "
                "answer(s) detected."
            )

            all_answers.extend(
                page_answers
            )

    # =========================================================
    # SINGLE IMAGE
    # =========================================================

    else:

        page_result = (
            extract_answers_from_page(
                image_bytes=file_bytes,
                page_number=1,
                mime_type=(
                    content_type
                    or "image/jpeg"
                ),
            )
        )

        all_answers.extend(
            page_result.get(
                "answers",
                [],
            )
        )

    # =========================================================
    # FINAL STABLE IDS
    # =========================================================

    for index, answer in enumerate(
        all_answers,
        start=1,
    ):
        answer["answer_id"] = f"a{index}"

    # =========================================================
    # FINAL LOG
    # =========================================================

    print(
        "\n========== FINAL ANSWER EXTRACTION =========="
    )

    print(
        f"Total answers extracted: "
        f"{len(all_answers)}"
    )

    for answer in all_answers:

        print(
            f'{answer["answer_id"]} | '
            f'Q={answer["question_number"]} | '
            f'regions={len(answer["regions"])} | '
            f'text={answer["text"][:100]}'
        )

    print(
        "=============================================\n"
    )

    return {
        "answers": all_answers
    }
