import base64
import json
import re
from time import sleep
from typing import Any, Dict, List

from app.services.groq_client import client, MODEL_NAME
from app.utils.pdf import pdf_to_images


QUESTION_PROMPT = """
You are an expert examination-paper vision AI.

Analyze ONLY the supplied question-paper page.

Extract EVERY printed question visible on this page.

IMPORTANT:
- This is a QUESTION PAPER.
- Extract questions only.
- Do NOT extract instructions, headings, student information,
  signatures, college name, exam name, or page decorations.
- Do NOT invent missing questions.
- Do NOT combine separate questions.
- Preserve the original printed question numbering.
- Treat labelled sub-parts as separate questions.

Examples:

11(a) -> separate question
11(b) -> separate question

If the paper contains:

Q1. Define photosynthesis.
Q2. Explain respiration.
Q3(a). What is...
Q3(b). Explain...

Return:

1
2
3(a)
3(b)

QUESTION NUMBER RULES:

Preserve numbering as written.

Examples:

Q1       -> "1"
Q.1      -> "1"
1.       -> "1"

Q1(a)    -> "1(a)"
Q1 (a)   -> "1(a)"
1(a)     -> "1(a)"
1 (a)    -> "1(a)"

Do NOT convert 11(a) into 11.

MARKS:

Extract marks when visible.

Examples:

(5 marks)
[5]
5 Marks
5M
5

If marks are not visible, use:

5

QUESTION TEXT:

Transcribe the actual printed question accurately.

Do not rewrite the question.

Preserve:

- formulas
- chemical equations
- mathematical symbols
- technical terms
- punctuation
- sub-parts
- units

BBOX:

For every question, return a bounding box covering the actual
printed question.

Coordinates MUST be normalized from 0 to 1000.

Coordinate system:

x = left to right
y = top to bottom

Example:

{
    "x": 100,
    "y": 200,
    "width": 700,
    "height": 120
}

The bbox must NOT cover the entire page unless the question actually
occupies the entire page.

PAGE:

Use the supplied page number exactly.

OUTPUT:

Return ONLY valid JSON.

Do not return markdown.

Do not return explanations.

Required format:

{
    "questions": [
        {
            "id": "q1",
            "number": "1",
            "text": "Question text",
            "page": 1,
            "max_marks": 5,
            "bbox": {
                "x": 100,
                "y": 200,
                "width": 700,
                "height": 120
            }
        }
    ]
}

If there are no questions on the page:

{
    "questions": []
}
"""


def clean_json_text(text: str) -> str:
    """
    Clean model output before JSON parsing.
    """

    if not text:
        return ""

    text = text.strip()

    # Remove reasoning/think tags if returned by Groq models.
    text = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE).strip()

    # Remove markdown code fences.
    match = re.search(
        r"```(?:json)?\s*([\s\S]*?)\s*```",
        text,
        flags=re.IGNORECASE,
    )

    if match:
        text = match.group(1).strip()

    # Remove accidental leading/trailing text around JSON.
    first_brace = text.find("{")
    last_brace = text.rfind("}")

    if (
        first_brace != -1
        and last_brace != -1
        and last_brace > first_brace
    ):
        text = text[first_brace:last_brace + 1]

    return text.strip()


def image_to_data_url(
    image_bytes: bytes,
    mime_type: str = "image/png",
) -> str:
    """
    Convert image bytes to a base64 data URL.
    """

    encoded = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"


def sanitize_bbox(
    bbox: Dict[str, Any],
) -> Dict[str, int]:
    """
    Keep bbox values inside 0-1000 normalized coordinates.
    """

    if not isinstance(bbox, dict):
        return {
            "x": 0,
            "y": 0,
            "width": 1000,
            "height": 1000,
        }

    def safe_int(
        value: Any,
        default: int = 0,
    ) -> int:

        try:
            return int(float(value))
        except (
            TypeError,
            ValueError,
        ):
            return default

    x = safe_int(
        bbox.get("x"),
        0,
    )

    y = safe_int(
        bbox.get("y"),
        0,
    )

    width = safe_int(
        bbox.get("width"),
        0,
    )

    height = safe_int(
        bbox.get("height"),
        0,
    )

    x = max(
        0,
        min(1000, x),
    )

    y = max(
        0,
        min(1000, y),
    )

    width = max(
        0,
        min(
            1000 - x,
            width,
        ),
    )

    height = max(
        0,
        min(
            1000 - y,
            height,
        ),
    )

    return {
        "x": x,
        "y": y,
        "width": width,
        "height": height,
    }


def normalize_question_number(
    value: Any,
):
    """
    Normalize question numbering.

    Examples:

    Q1       -> 1
    Q.1      -> 1
    1.       -> 1
    Q1(a)    -> 1(a)
    1-a      -> 1(a)
    1.1      -> 1(a)
    1(ii)    -> 1(b)
    """

    if value is None:
        return None

    value = str(value).strip().lower()

    if not value:
        return None

    # Remove common prefixes.
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

    # 1.1 / 1.2 / 1.3
    match = re.match(
        r"^(\d+)\.(\d+)$",
        value,
    )

    if match:

        number = match.group(1)

        sub_number = int(
            match.group(2)
        )

        if 1 <= sub_number <= 26:

            sub = chr(
                ord("a")
                + sub_number
                - 1
            )

            return f"{number}({sub})"

    # 1(a), 1[ii], 1-a, 1.a, 1a, 1(ii)
    match = re.match(
        r"^(\d+)[\(\[\.\-_]?([a-z]+|[ivx]+)[\)\]]?$",
        value,
    )

    if match:

        number = match.group(1)

        sub = match.group(2)

        if sub in roman_map:
            sub = roman_map[sub]

        if (
            len(sub) == 1
            and sub.isalpha()
        ):
            return f"{number}({sub})"

    # Plain number.
    match = re.match(
        r"^(\d+)$",
        value,
    )

    if match:
        return match.group(1)

    return value


def sanitize_questions(
    result: Dict[str, Any],
    page_number: int,
) -> Dict[str, Any]:
    """
    Validate and normalize questions returned by Groq.
    """

    if not isinstance(
        result,
        dict,
    ):
        return {
            "questions": []
        }

    raw_questions = result.get(
        "questions",
        [],
    )

    if not isinstance(
        raw_questions,
        list,
    ):
        return {
            "questions": []
        }

    questions = []

    for index, question in enumerate(
        raw_questions,
        start=1,
    ):

        if not isinstance(
            question,
            dict,
        ):
            continue

        number = normalize_question_number(
            question.get(
                "number"
            )
        )

        if number is None:
            continue

        text = question.get(
            "text",
            "",
        )

        if text is None:
            text = ""

        text = str(
            text
        ).strip()

        if not text:
            continue

        question_id = question.get(
            "id"
        )

        if not question_id:
            question_id = (
                f"q{page_number}_{index}"
            )

        max_marks = question.get(
            "max_marks",
            5,
        )

        try:
            max_marks = int(
                float(max_marks)
            )
        except (
            TypeError,
            ValueError,
        ):
            max_marks = 5

        if max_marks <= 0:
            max_marks = 5

        returned_page = question.get(
            "page",
            page_number,
        )

        try:
            returned_page = int(
                returned_page
            )
        except (
            TypeError,
            ValueError,
        ):
            returned_page = page_number

        if returned_page < 1:
            returned_page = page_number

        bbox = sanitize_bbox(
            question.get(
                "bbox",
                {},
            )
        )

        questions.append(
            {
                "id": str(
                    question_id
                ),
                "number": number,
                "text": text,
                "page": returned_page,
                "max_marks": max_marks,
                "bbox": bbox,
            }
        )

    return {
        "questions": questions
    }


def extract_questions_from_page(
    image_bytes: bytes,
    page_number: int,
    mime_type: str = "image/png",
):
    """
    Send ONE page at a time to Groq.

    This is intentional because it improves:
    - page accuracy
    - bbox accuracy
    - question ordering
    - reliability
    - token usage
    """

    page_prompt = (
        QUESTION_PROMPT
        + "\n\n"
        + f"IMPORTANT: This is page {page_number} "
        + "of the question paper.\n"
        + f"Every question extracted from this image "
        + f"MUST use page={page_number}.\n"
        + "Do not use another page number.\n"
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
                "\n========== QUESTION EXTRACTION "
                f"PAGE {page_number} "
                f"ATTEMPT {attempt + 1}/3 =========="
            )

            response = (
                client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {
                            "role": "user",
                            "content": message_content,
                        }
                    ],
                    temperature=0,
                    max_completion_tokens=4096,
                    reasoning_effort="none",
                    response_format={
                        "type": "json_object"
                    },
                )
            )

            raw = (
                response
                .choices[0]
                .message
                .content
            )

            raw = clean_json_text(
                raw
            )

            print(
                "\n========== GROQ QUESTION PAGE "
                f"{page_number} =========="
            )

            print(raw)

            print(
                "==========================================\n"
            )

            if not raw:
                raise ValueError(
                    "Groq returned an empty response."
                )

            result = json.loads(
                raw
            )

            result = sanitize_questions(
                result,
                page_number,
            )

            return result

        except json.JSONDecodeError as error:

            last_error = error

            print(
                "Invalid JSON returned by Groq: "
                f"{error}"
            )

            if attempt < 2:

                sleep(
                    (attempt + 1) * 3
                )

        except Exception as error:

            last_error = error

            error_message = str(
                error
            )

            print(
                "Groq question extraction "
                f"page {page_number} "
                f"attempt {attempt + 1}/3 failed: "
                f"{error_message}"
            )

            # Never retry rate limits.
            if (
                "429" in error_message
                or "rate_limit"
                in error_message.lower()
                or "rate limit"
                in error_message.lower()
            ):

                print(
                    "Groq rate limit reached. "
                    "Stopping retries immediately."
                )

                raise error

            # Retry other temporary errors.
            if attempt < 2:

                wait_seconds = (
                    attempt + 1
                ) * 3

                print(
                    "Retrying question extraction "
                    f"in {wait_seconds} seconds..."
                )

                sleep(
                    wait_seconds
                )

    if last_error:
        raise last_error

    raise RuntimeError(
        "Question extraction failed "
        f"for page {page_number}."
    )


def extract_questions(
    file_bytes: bytes,
    content_type: str,
):
    """
    Extract questions from a PDF or image.

    PDF:
        Convert every page to an image and process
        each page independently.

    Image:
        Process it as page 1.
    """

    all_questions: List[
        Dict[str, Any]
    ] = []

    # ---------------------------------------------------------
    # PDF
    # ---------------------------------------------------------

    if content_type == "application/pdf":

        pages = pdf_to_images(
            file_bytes
        )

        if not pages:
            return {
                "questions": []
            }

        print(
            f"\nQuestion paper contains "
            f"{len(pages)} page(s)."
        )

        for page in pages:

            page_number = page[
                "page"
            ]

            image_bytes = base64.b64decode(
                page[
                    "image"
                ]
            )

            page_result = (
                extract_questions_from_page(
                    image_bytes=image_bytes,
                    page_number=page_number,
                    mime_type="image/png",
                )
            )

            page_questions = (
                page_result.get(
                    "questions",
                    [],
                )
            )

            print(
                f"Page {page_number}: "
                f"{len(page_questions)} "
                "question(s) detected."
            )

            all_questions.extend(
                page_questions
            )

    # ---------------------------------------------------------
    # Single image
    # ---------------------------------------------------------

    else:

        page_result = (
            extract_questions_from_page(
                image_bytes=file_bytes,
                page_number=1,
                mime_type=(
                    content_type
                    or "image/jpeg"
                ),
            )
        )

        all_questions.extend(
            page_result.get(
                "questions",
                [],
            )
        )

    # ---------------------------------------------------------
    # Final ordering
    # ---------------------------------------------------------

    # Preserve printed page order.
    # We intentionally do NOT sort alphabetically by question
    # number because questions may have complex subparts.

    all_questions = sorted(
        all_questions,
        key=lambda item: (
            int(
                re.match(
                    r"\d+",
                    str(
                        item.get(
                            "number",
                            "999999",
                        )
                    ),
                ).group()
            )
            if re.match(
                r"\d+",
                str(
                    item.get(
                        "number",
                        "",
                    )
                ),
            )
            else 999999,

            item.get(
                "page",
                999999,
            ),
        ),
    )

    # ---------------------------------------------------------
    # Rebuild stable IDs
    # ---------------------------------------------------------

    for index, question in enumerate(
        all_questions,
        start=1,
    ):

        question["id"] = (
            f"q{index}"
        )

    print(
        "\n========== FINAL QUESTION EXTRACTION =========="
    )

    print(
        f"Total questions extracted: "
        f"{len(all_questions)}"
    )

    for question in all_questions:

        print(
            f'{question["id"]} | '
            f'Q={question["number"]} | '
            f'Page={question["page"]} | '
            f'Marks={question["max_marks"]} | '
            f'{question["text"][:100]}'
        )

    print(
        "===============================================\n"
    )

    return {
        "questions": all_questions
    }