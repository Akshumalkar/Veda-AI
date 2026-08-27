import base64
import json
import re
from time import sleep
from typing import Any, Dict, List

from app.services.groq_client import client, MODEL_NAME
from app.utils.pdf import pdf_to_images


QUESTION_PROMPT = """
Extract every visible examination question from this page.

Return ONLY valid JSON.

Use exactly this structure:

{
  "questions": [
    {
      "id": "q1",
      "number": "1",
      "text": "complete question text",
      "page": 1,
      "max_marks": 5,
      "bbox": {
        "x": 100,
        "y": 100,
        "width": 800,
        "height": 50
      }
    }
  ]
}

Rules:

- Extract every visible examination question.
- Preserve printed numbering exactly.
- Treat subquestions separately.
- Preserve complete visible question text.
- Ignore headers, instructions and student information.
- Coordinates must be normalized from 0 to 1000.
- Use printed marks if visible.
- If marks are not visible, use 5.
- Use the supplied page number.
- Do not add explanations.
- Do not use markdown.
- Return valid JSON only.
"""


def clean_json_text(text: str) -> str:
    """Clean model output before JSON parsing."""

    if not text:
        return ""

    text = text.strip()

    # Remove think/reasoning blocks.
    text = re.sub(
        r"<think>[\s\S]*?</think>",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()

    # Remove markdown code fences.
    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = text.strip()

    # Extract JSON object.
    first = text.find("{")
    last = text.rfind("}")

    if first != -1 and last != -1 and last > first:
        text = text[first:last + 1]

    return text.strip()


def parse_json_response(text: str) -> Dict[str, Any]:
    """Safely parse Groq JSON response."""

    cleaned = clean_json_text(text)

    if not cleaned:
        raise ValueError(
            "Groq returned an empty response."
        )

    try:
        result = json.loads(cleaned)

        if not isinstance(result, dict):
            raise ValueError(
                "Groq JSON response is not an object."
            )

        return result

    except json.JSONDecodeError as error:
        print(
            "\n========== INVALID GROQ JSON =========="
        )
        print(cleaned)
        print(
            "========================================"
        )

        raise ValueError(
            f"Invalid JSON returned by Groq: {error}"
        ) from error


def image_to_data_url(
    image_bytes: bytes,
    mime_type: str = "image/png",
) -> str:
    """Convert image bytes to base64 data URL."""

    encoded = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"


def sanitize_bbox(
    bbox: Dict[str, Any],
) -> Dict[str, int]:
    """Normalize bbox coordinates to 0-1000."""

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
        except (TypeError, ValueError):
            return default

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


def normalize_question_number(
    value: Any,
):
    """Normalize question numbering."""

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

    # 1.1 -> 1(a)
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

    # 1(a), 1-a, 1.a, 1a, 1(ii)
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
    """Validate extracted questions."""

    if not isinstance(result, dict):
        return {"questions": []}

    raw_questions = result.get(
        "questions",
        [],
    )

    if not isinstance(raw_questions, list):
        return {"questions": []}

    questions = []

    for index, question in enumerate(
        raw_questions,
        start=1,
    ):

        if not isinstance(question, dict):
            continue

        number = normalize_question_number(
            question.get("number")
        )

        if number is None:
            continue

        text = question.get(
            "text",
            "",
        )

        if text is None:
            text = ""

        text = str(text).strip()

        if not text:
            continue

        question_id = question.get("id")

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

        bbox = sanitize_bbox(
            question.get(
                "bbox",
                {},
            )
        )

        questions.append(
            {
                "id": str(question_id),
                "number": number,
                "text": text,
                "page": page_number,
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
    """Extract questions from one page."""

    page_prompt = (
        QUESTION_PROMPT
        + "\n\n"
        + f"This is page {page_number}.\n"
        + f"Every question MUST use page={page_number}.\n"
        + "Return ONLY JSON.\n"
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

    print(
        "\n========== QUESTION EXTRACTION "
        f"PAGE {page_number} =========="
    )

    try:

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": message_content,
                }
            ],
            temperature=0,
            max_tokens=2500,
            response_format={
                "type": "json_object"
            },
        )

        raw = (
            response
            .choices[0]
            .message
            .content
        )

        print(
            "\n========== GROQ QUESTION PAGE "
            f"{page_number} =========="
        )

        print(raw)

        print(
            "==========================================\n"
        )

        result = parse_json_response(raw)

        return sanitize_questions(
            result,
            page_number,
        )

    except Exception as error:

        error_message = str(error)

        print(
            f"Question extraction page "
            f"{page_number} failed: "
            f"{error_message}"
        )

        # Do NOT retry 429 errors.
        if (
            "429" in error_message
            or "rate_limit" in error_message.lower()
            or "rate limit" in error_message.lower()
        ):
            print(
                "Groq rate limit reached. "
                "Stopping immediately."
            )

        raise


def extract_questions(
    file_bytes: bytes,
    content_type: str,
):
    """Extract questions from PDF or image."""

    all_questions: List[
        Dict[str, Any]
    ] = []

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

            page_number = page["page"]

            image_bytes = base64.b64decode(
                page["image"]
            )

            page_result = (
                extract_questions_from_page(
                    image_bytes=image_bytes,
                    page_number=page_number,
                    mime_type="image/png",
                )
            )

            page_questions = page_result.get(
                "questions",
                [],
            )

            print(
                f"Page {page_number}: "
                f"{len(page_questions)} "
                "question(s) detected."
            )

            all_questions.extend(
                page_questions
            )

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

    # Sort by page first, then question number.
    def question_sort_key(item):
        number = str(
            item.get(
                "number",
                "",
            )
        )

        match = re.match(
            r"(\d+)",
            number,
        )

        question_number = (
            int(match.group(1))
            if match
            else 999999
        )

        return (
            item.get("page", 999999),
            question_number,
        )

    all_questions = sorted(
        all_questions,
        key=question_sort_key,
    )

    # Stable IDs.
    for index, question in enumerate(
        all_questions,
        start=1,
    ):
        question["id"] = f"q{index}"

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
