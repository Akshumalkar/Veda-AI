import base64
import json
import re
from typing import Any, Dict, List

from app.services.groq_client import client, MODEL_NAME
from app.utils.pdf import pdf_to_images


# ============================================================
# QUESTION EXTRACTION PROMPT
# ============================================================

QUESTION_PROMPT = """
You are an examination question extraction system.

Look at the supplied examination paper image.

Extract ONLY the actual examination questions visible on the page.

Return JSON with exactly this structure:

{
  "questions": [
    {
      "id": "q1",
      "number": "1",
      "text": "Complete question text",
      "page": 1,
      "max_marks": 5,
      "bbox": {
        "x": 0,
        "y": 0,
        "width": 1000,
        "height": 100
      }
    }
  ]
}

IMPORTANT RULES:

1. Extract every visible examination question.

2. Preserve the printed question numbering.

3. Treat subquestions as separate questions.
   Examples:
   1(a)
   1(b)
   2(a)
   2(b)

4. Preserve the complete question text.

5. Do NOT summarize questions.

6. Do NOT invent text that is not visible.

7. Ignore:
   - college name
   - university name
   - examination name
   - subject name
   - instructions
   - student information
   - page headers
   - page footers
   - registration numbers
   - date
   - time
   - general instructions

8. If marks are visible beside a question, extract them.

9. If marks are not visible, use 5.

10. Coordinates must be normalized from 0 to 1000.

11. bbox should cover the complete question text.

12. "page" must contain the supplied page number.

13. Every question must have:
   - id
   - number
   - text
   - page
   - max_marks
   - bbox

14. Return JSON only.

15. Do not use markdown.

16. Do not write explanations outside the JSON.

17. If no examination questions are visible, return:

{
  "questions": []
}
"""


# ============================================================
# JSON CLEANING
# ============================================================

def clean_json_text(text: str) -> str:
    """
    Clean model output and extract a JSON object.
    """

    if not text:
        return ""

    text = str(text).strip()

    # Remove <think>...</think> blocks.
    text = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    ).strip()

    # Remove markdown code fences.
    text = re.sub(
        r"```json\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"```\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = text.strip()

    # Find JSON object.
    first = text.find("{")
    last = text.rfind("}")

    if first != -1 and last != -1 and last > first:
        text = text[first:last + 1]

    return text.strip()


def parse_json_response(text: str) -> Dict[str, Any]:
    """
    Safely parse model output.
    """

    cleaned = clean_json_text(text)

    if not cleaned:
        raise ValueError(
            "Groq returned an empty response."
        )

    try:
        result = json.loads(cleaned)

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

    if not isinstance(result, dict):
        raise ValueError(
            "Groq response is not a JSON object."
        )

    return result


# ============================================================
# IMAGE -> DATA URL
# ============================================================

def image_to_data_url(
    image_bytes: bytes,
    mime_type: str = "image/png",
) -> str:
    """
    Convert image bytes into a base64 data URL.
    """

    encoded = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"


# ============================================================
# SAFE INTEGER
# ============================================================

def safe_int(
    value: Any,
    default: int = 0,
) -> int:
    """
    Safely convert a value to integer.
    """

    try:
        return int(float(value))

    except (
        TypeError,
        ValueError,
    ):
        return default


# ============================================================
# BBOX SANITIZATION
# ============================================================

def sanitize_bbox(
    bbox: Any,
) -> Dict[str, int]:
    """
    Normalize bbox coordinates to 0-1000.
    """

    if not isinstance(
        bbox,
        dict,
    ):
        return {
            "x": 0,
            "y": 0,
            "width": 1000,
            "height": 1000,
        }

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
        min(
            1000,
            x,
        ),
    )

    y = max(
        0,
        min(
            1000,
            y,
        ),
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


# ============================================================
# QUESTION NUMBER NORMALIZATION
# ============================================================

def normalize_question_number(
    value: Any,
):
    """
    Normalize different question-number formats.

    Examples:

    Q1       -> 1
    Q.1      -> 1
    1.1      -> 1(a)
    1(a)     -> 1(a)
    1-a      -> 1(a)
    1.a      -> 1(a)
    1(ii)    -> 1(b)
    """

    if value is None:
        return None

    value = str(
        value
    ).strip().lower()

    if not value:
        return None

    # Remove common prefixes.
    value = re.sub(
        r"^(question|ques|que|answer|ans|q)\.?\s*",
        "",
        value,
    )

    # Remove whitespace.
    value = re.sub(
        r"\s+",
        "",
        value,
    )

    # Remove trailing period.
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

    # --------------------------------------------------------
    # 1.1 -> 1(a)
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # 1(a), 1-a, 1.a, 1a, 1(ii)
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Plain number
    # --------------------------------------------------------

    match = re.match(
        r"^(\d+)$",
        value,
    )

    if match:
        return match.group(1)

    return value


# ============================================================
# QUESTION SANITIZATION
# ============================================================

def sanitize_questions(
    result: Dict[str, Any],
    page_number: int,
) -> Dict[str, Any]:
    """
    Validate and normalize extracted questions.
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

        # ----------------------------------------------------
        # Number
        # ----------------------------------------------------

        number = normalize_question_number(
            question.get(
                "number"
            )
        )

        if number is None:
            continue

        # ----------------------------------------------------
        # Text
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # ID
        # ----------------------------------------------------

        question_id = question.get(
            "id"
        )

        if not question_id:

            question_id = (
                f"q{page_number}_{index}"
            )

        # ----------------------------------------------------
        # Marks
        # ----------------------------------------------------

        max_marks = safe_int(
            question.get(
                "max_marks",
                5,
            ),
            5,
        )

        if max_marks <= 0:
            max_marks = 5

        # ----------------------------------------------------
        # Bounding box
        # ----------------------------------------------------

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
                "page": page_number,
                "max_marks": max_marks,
                "bbox": bbox,
            }
        )

    return {
        "questions": questions
    }


# ============================================================
# EXTRACT QUESTIONS FROM ONE PAGE
# ============================================================

def extract_questions_from_page(
    image_bytes: bytes,
    page_number: int,
    mime_type: str = "image/png",
) -> Dict[str, Any]:
    """
    Extract examination questions from one page.
    """

    page_prompt = (
        QUESTION_PROMPT
        + "\n\n"
        + f"SUPPLIED PAGE NUMBER: {page_number}\n"
        + f"Every extracted question MUST have page={page_number}.\n"
        + "\nReturn JSON only."
    )

    image_data_url = image_to_data_url(
        image_bytes,
        mime_type,
    )

    message_content = [
        {
            "type": "text",
            "text": page_prompt,
        },
        {
            "type": "image_url",
            "image_url": {
                "url": image_data_url
            },
        },
    ]

    print(
        "\n========== QUESTION EXTRACTION "
        f"PAGE {page_number} =========="
    )

    try:

        # ====================================================
        # IMPORTANT:
        #
        # DO NOT USE:
        #
        # response_format={
        #     "type": "json_object"
        # }
        #
        # The current Groq/model combination is returning
        # json_validate_failed with this option.
        #
        # We ask for JSON in the prompt and parse it ourselves.
        # ====================================================

        response = client.chat.completions.create(
            model=MODEL_NAME,

            messages=[
                {
                    "role": "user",
                    "content": message_content,
                }
            ],

            temperature=0,

            max_tokens=3000,
        )

        # ----------------------------------------------------
        # Get model response
        # ----------------------------------------------------

        raw = (
            response
            .choices[0]
            .message
            .content
        )

        print(
            "\n========== GROQ QUESTION PAGE "
            f"{page_number} RESPONSE =========="
        )

        print(raw)

        print(
            "==========================================\n"
        )

        # ----------------------------------------------------
        # Parse JSON ourselves
        # ----------------------------------------------------

        result = parse_json_response(
            raw
        )

        # ----------------------------------------------------
        # Sanitize
        # ----------------------------------------------------

        sanitized = sanitize_questions(
            result,
            page_number,
        )

        print(
            f"Page {page_number}: "
            f"{len(sanitized['questions'])} "
            "question(s) extracted."
        )

        return sanitized

    except Exception as error:

        error_message = str(
            error
        )

        print(
            f"Question extraction page "
            f"{page_number} failed: "
            f"{error_message}"
        )

        # Do not retry rate-limit errors.
        if (
            "429" in error_message
            or "rate_limit" in error_message.lower()
            or "rate limit" in error_message.lower()
        ):

            print(
                "Groq rate limit reached. "
                "Stopping extraction."
            )

        raise


# ============================================================
# EXTRACT QUESTIONS FROM PDF / IMAGE
# ============================================================

def extract_questions(
    file_bytes: bytes,
    content_type: str,
) -> Dict[str, Any]:
    """
    Extract questions from PDF or image.
    """

    all_questions: List[
        Dict[str, Any]
    ] = []

    # ========================================================
    # PDF
    # ========================================================

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

    # ========================================================
    # IMAGE
    # ========================================================

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

    # ========================================================
    # SORT QUESTIONS
    # ========================================================

    def question_sort_key(
        item: Dict[str, Any],
    ):

        number = str(
            item.get(
                "number",
                "",
            )
        )

        # Extract first numeric portion.
        match = re.match(
            r"(\d+)",
            number,
        )

        question_number = (
            int(match.group(1))
            if match
            else 999999
        )

        # Extract subquestion letter.
        sub_letter = 0

        sub_match = re.search(
            r"\(([a-z])\)",
            number,
        )

        if sub_match:

            sub_letter = (
                ord(
                    sub_match.group(1)
                )
                - ord("a")
                + 1
            )

        return (
            item.get(
                "page",
                999999,
            ),
            question_number,
            sub_letter,
        )

    all_questions = sorted(
        all_questions,
        key=question_sort_key,
    )

    # ========================================================
    # STABLE IDS
    # ========================================================

    for index, question in enumerate(
        all_questions,
        start=1,
    ):

        question["id"] = (
            f"q{index}"
        )

    # ========================================================
    # FINAL LOG
    # ========================================================

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
            f'{question["text"][:120]}'
        )

    print(
        "===============================================\n"
    )

    return {
        "questions": all_questions
    }
