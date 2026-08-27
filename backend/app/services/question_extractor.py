import base64
import json
import re
from time import sleep
from typing import Any, Dict, List

from app.services.groq_client import client, MODEL_NAME
from app.utils.pdf import pdf_to_images


# ============================================================
# QUESTION EXTRACTION PROMPT
# ============================================================

QUESTION_PROMPT = """
Extract every visible examination question from this page.

IMPORTANT:
Return ONLY a JSON object.
Do NOT return markdown.
Do NOT return ```json.
Do NOT return explanations.
Do NOT return reasoning.
Do NOT return <think> tags.

Required JSON structure:

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

- Extract EVERY visible examination question.
- Preserve the printed question numbering exactly.
- Treat subquestions separately.
- Examples:
  - 5(a)
  - 5(b)
  - 6(i)
  - 6(ii)
- Preserve the COMPLETE visible question text.
- Do not summarize questions.
- Ignore headers.
- Ignore college names.
- Ignore exam instructions.
- Ignore student information.
- Ignore page numbers that are not part of a question.
- Use normalized bbox coordinates from 0 to 1000.
- The bbox must cover the visible question text.
- Use the printed marks if visible.
- If marks are not visible, use 5.
- Use the supplied page number.
- Every question must contain:
  id
  number
  text
  page
  max_marks
  bbox
- Do not invent questions.
- Do not duplicate questions.
- Return a valid JSON object.
"""


# ============================================================
# JSON CLEANING
# ============================================================

def clean_json_text(text: str) -> str:
    """
    Clean model output before JSON parsing.
    Handles:
    - markdown fences
    - <think> tags
    - accidental text before/after JSON
    """

    if not text:
        return ""

    text = str(text).strip()

    # Remove reasoning blocks.
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

    # Extract JSON object if extra text exists.
    first_brace = text.find("{")
    last_brace = text.rfind("}")

    if (
        first_brace != -1
        and last_brace != -1
        and last_brace > first_brace
    ):
        text = text[first_brace:last_brace + 1]

    return text.strip()


def parse_json_response(text: str) -> Dict[str, Any]:
    """
    Safely parse JSON returned by Groq.
    """

    if not text:
        raise ValueError(
            "Groq returned an empty response."
        )

    cleaned = clean_json_text(text)

    if not cleaned:
        raise ValueError(
            "Groq returned an empty JSON response."
        )

    try:
        result = json.loads(cleaned)

    except json.JSONDecodeError as error:

        # Log the exact problematic response.
        print(
            "\n========== INVALID GROQ JSON =========="
        )
        print(cleaned)
        print(
            "========================================\n"
        )

        raise ValueError(
            f"Invalid JSON returned by Groq: {error}"
        ) from error

    if not isinstance(result, dict):
        raise ValueError(
            "Groq JSON response is not an object."
        )

    return result


# ============================================================
# IMAGE -> BASE64 DATA URL
# ============================================================

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

    return (
        f"data:{mime_type};base64,{encoded}"
    )


# ============================================================
# BBOX SANITIZATION
# ============================================================

def sanitize_bbox(
    bbox: Dict[str, Any],
) -> Dict[str, int]:
    """
    Keep bbox values inside normalized 0-1000 coordinates.
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

    # Clamp x/y.
    x = max(
        0,
        min(1000, x),
    )

    y = max(
        0,
        min(1000, y),
    )

    # Clamp width/height.
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
    # 1.1 / 1.2 / 1.3
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
    # 1(a), 1[ii], 1-a, 1.a, 1a, 1(ii)
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

        # IMPORTANT:
        # Always force the actual page being processed.
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


# ============================================================
# EXTRACT QUESTIONS FROM ONE PAGE
# ============================================================

def extract_questions_from_page(
    image_bytes: bytes,
    page_number: int,
    mime_type: str = "image/png",
):
    """
    Send ONE page at a time to Groq.

    Improvements:
    - JSON mode enabled
    - reasoning disabled
    - lower output token limit
    - fewer retries
    - rate-limit errors stop immediately
    - malformed JSON is handled
    """

    page_prompt = (
        QUESTION_PROMPT
        + "\n\n"
        + f"IMPORTANT: This is page {page_number} "
        + "of the question paper.\n"
        + f"Every extracted question MUST use "
        + f"page={page_number}.\n"
        + "Return ONLY the JSON object."
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

    # Only retry once for malformed/temporary responses.
    # Do NOT waste daily tokens with 3 full requests.
    max_attempts = 2

    for attempt in range(
        max_attempts
    ):

        try:

            print(
                "\n========== QUESTION EXTRACTION "
                f"PAGE {page_number} "
                f"ATTEMPT {attempt + 1}/{max_attempts} =========="
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

                    # Deterministic extraction.
                    temperature=0,

                    # Qwen 3.6 supports hidden reasoning.
                    reasoning_format="hidden",

                    # Force valid JSON.
                    response_format={
                        "type": "json_object"
                    },

                    # Questions normally require
                    # much less output than 4096 tokens.
                    max_tokens=2048,
                )
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

            print(
                raw
            )

            print(
                "==========================================\n"
            )

            if not raw:
                raise ValueError(
                    "Groq returned an empty response."
                )

            result = parse_json_response(
                raw
            )

            result = sanitize_questions(
                result,
                page_number,
            )

            return result

        except Exception as error:

            last_error = error

            error_message = str(
                error
            )

            print(
                "Groq question extraction "
                f"page {page_number} "
                f"attempt {attempt + 1}/{max_attempts} "
                f"failed: {error_message}"
            )

            lower_error = (
                error_message.lower()
            )

            # ------------------------------------------------
            # RATE LIMIT
            # ------------------------------------------------

            if (
                "429" in error_message
                or "rate_limit" in lower_error
                or "rate limit" in lower_error
                or "tokens per day" in lower_error
                or "tokens per minute" in lower_error
            ):

                print(
                    "Groq rate limit reached. "
                    "Stopping retries immediately."
                )

                raise error

            # ------------------------------------------------
            # INVALID JSON
            # ------------------------------------------------

            if (
                "invalid json" in lower_error
                or "json" in lower_error
            ):

                if attempt < max_attempts - 1:

                    print(
                        "Invalid JSON detected. "
                        "Retrying once..."
                    )

                    sleep(2)

                    continue

            # ------------------------------------------------
            # OTHER TEMPORARY ERRORS
            # ------------------------------------------------

            if attempt < max_attempts - 1:

                wait_seconds = 2

                print(
                    "Retrying question extraction "
                    f"in {wait_seconds} seconds..."
                )

                sleep(
                    wait_seconds
                )

                continue

            raise

    if last_error:
        raise last_error

    raise RuntimeError(
        "Question extraction failed "
        f"for page {page_number}."
    )


# ============================================================
# EXTRACT QUESTIONS FROM FILE
# ============================================================

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

            page_number = page[
                "page"
            ]

            image_bytes = (
                base64.b64decode(
                    page[
                        "image"
                    ]
                )
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
    # SINGLE IMAGE
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
    # FINAL ORDERING
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

        match = re.match(
            r"^\d+",
            number,
        )

        if match:

            numeric_number = int(
                match.group()
            )

        else:

            numeric_number = 999999

        return (
            item.get(
                "page",
                999999,
            ),
            numeric_number,
            number,
        )

    all_questions = sorted(
        all_questions,
        key=question_sort_key,
    )

    # ========================================================
    # REMOVE DUPLICATE QUESTIONS
    # ========================================================

    unique_questions = []

    seen_numbers = set()

    for question in all_questions:

        key = (
            question.get(
                "page"
            ),
            question.get(
                "number"
            ),
        )

        if key in seen_numbers:

            print(
                "Duplicate question removed: "
                f"page={key[0]}, "
                f"number={key[1]}"
            )

            continue

        seen_numbers.add(
            key
        )

        unique_questions.append(
            question
        )

    all_questions = unique_questions

    # ========================================================
    # REBUILD STABLE IDS
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
            f'{question["text"][:100]}'
        )

    print(
        "===============================================\n"
    )

    return {
        "questions": all_questions
    }
