import base64
import io
import json
import re
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

from app.services.groq_client import (
    client,
    MODEL_NAME,
    MAX_COMPLETION_TOKENS,
)

from app.utils.pdf import pdf_to_images


# ============================================================
# CONFIGURATION
# ============================================================

# Maximum image dimension sent to Groq.
#
# The original PDF render may be unnecessarily large.
# Resizing reduces request size while keeping enough
# resolution for examination-paper OCR.
#
# Groq currently supports up to 20 MB per image request,
# but smaller images are preferable for token efficiency.
# ============================================================

MAX_IMAGE_DIMENSION = 1800


# ============================================================
# QUESTION EXTRACTION PROMPT
# ============================================================

QUESTION_PROMPT = """
You are an examination question extraction system.

Look carefully at the supplied examination paper image.

Extract ONLY the actual examination questions visible
on the page.

Return ONLY a JSON object using exactly this structure:

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

3. Treat subquestions separately.

   Examples:
   1(a)
   1(b)
   2(a)
   2(b)

4. Preserve the complete visible question text.

5. Do NOT summarize questions.

6. Do NOT invent missing text.

7. Ignore:
   - college name
   - university name
   - subject name
   - examination name
   - instructions
   - student information
   - registration number
   - date
   - time
   - page header
   - page footer
   - general instructions

8. If marks are visible beside a question,
   extract the marks.

9. If marks are not visible,
   use 5.

10. Coordinates must be normalized from 0 to 1000.

11. bbox should cover the complete question.

12. The page field must contain the supplied page number.

13. Every question must contain:
   - id
   - number
   - text
   - page
   - max_marks
   - bbox

14. Return JSON only.

15. Do not use markdown.

16. Do not write explanations outside JSON.

17. If no examination questions are visible,
    return:

{
  "questions": []
}
"""


# ============================================================
# IMAGE RESIZING
# ============================================================

def prepare_image_for_groq(
    image_bytes: bytes,
    mime_type: str = "image/png",
) -> Tuple[bytes, str]:
    """
    Resize/compress the image before sending it to Groq.

    This reduces unnecessary image payload size and helps
    reduce token consumption while preserving OCR quality.
    """

    try:

        image = Image.open(
            io.BytesIO(image_bytes)
        )

        image = image.convert(
            "RGB"
        )

        width, height = image.size

        # ----------------------------------------------------
        # Calculate resize ratio.
        # ----------------------------------------------------

        largest_dimension = max(
            width,
            height,
        )

        if (
            largest_dimension
            > MAX_IMAGE_DIMENSION
        ):

            scale = (
                MAX_IMAGE_DIMENSION
                / largest_dimension
            )

            new_width = max(
                1,
                int(width * scale),
            )

            new_height = max(
                1,
                int(height * scale),
            )

            image = image.resize(
                (
                    new_width,
                    new_height,
                ),
                Image.Resampling.LANCZOS,
            )

        # ----------------------------------------------------
        # Use JPEG for smaller payload.
        # ----------------------------------------------------

        output = io.BytesIO()

        image.save(
            output,
            format="JPEG",
            quality=85,
            optimize=True,
        )

        return (
            output.getvalue(),
            "image/jpeg",
        )

    except Exception as error:

        print(
            "Image optimization failed. "
            "Using original image. "
            f"Error: {error}"
        )

        return (
            image_bytes,
            mime_type,
        )


# ============================================================
# IMAGE -> DATA URL
# ============================================================

def image_to_data_url(
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
) -> str:
    """
    Convert image bytes to a base64 data URL.
    """

    encoded = base64.b64encode(
        image_bytes
    ).decode(
        "utf-8"
    )

    return (
        f"data:{mime_type};base64,{encoded}"
    )


# ============================================================
# CLEAN JSON
# ============================================================

def clean_json_text(
    text: str,
) -> str:
    """
    Clean model output before JSON parsing.
    """

    if not text:
        return ""

    text = str(
        text
    ).strip()

    # --------------------------------------------------------
    # Remove reasoning blocks.
    # --------------------------------------------------------

    text = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=(
            re.IGNORECASE
            | re.DOTALL
        ),
    ).strip()

    # --------------------------------------------------------
    # Remove markdown fences.
    # --------------------------------------------------------

    text = re.sub(
        r"```json",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"```",
        "",
        text,
    )

    text = text.strip()

    # --------------------------------------------------------
    # Extract JSON object.
    # --------------------------------------------------------

    first = text.find(
        "{"
    )

    last = text.rfind(
        "}"
    )

    if (
        first != -1
        and last != -1
        and last > first
    ):

        text = text[
            first:last + 1
        ]

    return text.strip()


# ============================================================
# JSON PARSER
# ============================================================

def parse_json_response(
    text: str,
) -> Dict[str, Any]:
    """
    Parse Groq JSON response safely.
    """

    cleaned = clean_json_text(
        text
    )

    if not cleaned:

        raise ValueError(
            "Groq returned an empty response."
        )

    try:

        result = json.loads(
            cleaned
        )

    except json.JSONDecodeError as error:

        print(
            "\n========== INVALID GROQ JSON =========="
        )

        print(
            cleaned
        )

        print(
            "========================================"
        )

        raise ValueError(
            "Invalid JSON returned by Groq: "
            f"{error}"
        ) from error

    if not isinstance(
        result,
        dict,
    ):

        raise ValueError(
            "Groq JSON response is not an object."
        )

    return result


# ============================================================
# SAFE INTEGER
# ============================================================

def safe_int(
    value: Any,
    default: int = 0,
) -> int:
    """
    Safely convert value to integer.
    """

    try:

        return int(
            float(value)
        )

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
    Normalize bounding box coordinates to 0-1000.
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
    Normalize common examination numbering formats.

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

    # Remove prefixes.
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
    value = value.rstrip(
        "."
    )

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

        number = match.group(
            1
        )

        sub_number = int(
            match.group(2)
        )

        if (
            1
            <= sub_number
            <= 26
        ):

            sub = chr(
                ord("a")
                + sub_number
                - 1
            )

            return (
                f"{number}({sub})"
            )

    # --------------------------------------------------------
    # 1(a), 1-a, 1.a, 1a, 1(ii)
    # --------------------------------------------------------

    match = re.match(
        r"^(\d+)[\(\[\.\-_]?([a-z]+|[ivx]+)[\)\]]?$",
        value,
    )

    if match:

        number = match.group(
            1
        )

        sub = match.group(
            2
        )

        if sub in roman_map:
            sub = roman_map[
                sub
            ]

        if (
            len(sub) == 1
            and sub.isalpha()
        ):

            return (
                f"{number}({sub})"
            )

    # --------------------------------------------------------
    # Plain number
    # --------------------------------------------------------

    match = re.match(
        r"^(\d+)$",
        value,
    )

    if match:
        return match.group(
            1
        )

    return value


# ============================================================
# QUESTION SANITIZATION
# ============================================================

def sanitize_questions(
    result: Dict[str, Any],
    page_number: int,
) -> Dict[str, Any]:
    """
    Validate and normalize model-generated questions.
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
        # BBOX
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
# GROQ ERROR INFORMATION
# ============================================================

def get_error_info(
    error: Exception,
) -> Dict[str, Any]:
    """
    Extract useful information from Groq/API exceptions.
    """

    message = str(
        error
    )

    status_code = getattr(
        error,
        "status_code",
        None,
    )

    response = getattr(
        error,
        "response",
        None,
    )

    headers = {}

    if response is not None:

        headers = getattr(
            response,
            "headers",
            {}
        )

    if headers is None:
        headers = {}

    retry_after = (
        headers.get(
            "retry-after"
        )
        or headers.get(
            "Retry-After"
        )
    )

    reset_tokens = (
        headers.get(
            "x-ratelimit-reset-tokens"
        )
        or headers.get(
            "X-RateLimit-Reset-Tokens"
        )
    )

    return {
        "message": message,
        "status_code": status_code,
        "retry_after": retry_after,
        "reset_tokens": reset_tokens,
    }


# ============================================================
# RATE LIMIT DETECTION
# ============================================================

def is_rate_limit_error(
    error: Exception,
) -> bool:
    """
    Detect Groq rate-limit errors.
    """

    info = get_error_info(
        error
    )

    message = info[
        "message"
    ].lower()

    status_code = info[
        "status_code"
    ]

    return (
        status_code == 429
        or "429" in message
        or "rate_limit" in message
        or "rate limit" in message
        or "tokens per day" in message
        or "tokens per minute" in message
        or "rate_limit_exceeded" in message
    )


# ============================================================
# RATE LIMIT MESSAGE
# ============================================================

def format_rate_limit_message(
    error: Exception,
) -> str:
    """
    Create a useful user/log message for 429 errors.
    """

    info = get_error_info(
        error
    )

    message = info[
        "message"
    ]

    retry_after = info[
        "retry_after"
    ]

    reset_tokens = info[
        "reset_tokens"
    ]

    # --------------------------------------------------------
    # Extract "try again in XX"
    # --------------------------------------------------------

    match = re.search(
        r"try again in\s+([^\.]+)",
        message,
        flags=re.IGNORECASE,
    )

    retry_text = (
        match.group(1).strip()
        if match
        else None
    )

    details = []

    if retry_text:
        details.append(
            f"try again in {retry_text}"
        )

    if retry_after:
        details.append(
            f"retry-after={retry_after}"
        )

    if reset_tokens:
        details.append(
            f"token-reset={reset_tokens}"
        )

    if details:

        return (
            "Groq rate limit reached: "
            + ", ".join(details)
        )

    return (
        "Groq rate limit reached. "
        "Please wait for the quota to reset."
    )


# ============================================================
# EXTRACT QUESTIONS FROM ONE PAGE
# ============================================================

def extract_questions_from_page(
    image_bytes: bytes,
    page_number: int,
    mime_type: str = "image/png",
) -> Dict[str, Any]:
    """
    Extract questions from one examination-paper page.
    """

    # --------------------------------------------------------
    # Optimize image
    # --------------------------------------------------------

    optimized_image, optimized_mime = (
        prepare_image_for_groq(
            image_bytes,
            mime_type,
        )
    )

    print(
        f"Original image size: "
        f"{len(image_bytes) / 1024:.1f} KB"
    )

    print(
        f"Groq image size: "
        f"{len(optimized_image) / 1024:.1f} KB"
    )

    # --------------------------------------------------------
    # Prompt
    # --------------------------------------------------------

    page_prompt = (
        QUESTION_PROMPT
        + "\n\n"
        + f"SUPPLIED PAGE NUMBER: {page_number}\n"
        + f"Every question MUST use page={page_number}.\n"
        + "\nReturn JSON only."
    )

    # --------------------------------------------------------
    # Image URL
    # --------------------------------------------------------

    image_data_url = image_to_data_url(
        optimized_image,
        optimized_mime,
    )

    # --------------------------------------------------------
    # Message
    # --------------------------------------------------------

    message_content = [
        {
            "type": "text",
            "text": page_prompt,
        },
        {
            "type": "image_url",
            "image_url": {
                "url": image_data_url,
            },
        },
    ]

    print(
        "\n========== QUESTION EXTRACTION "
        f"PAGE {page_number} =========="
    )

    print(
        f"Model: {MODEL_NAME}"
    )

    # ========================================================
    # SINGLE API REQUEST
    # ========================================================
    #
    # IMPORTANT:
    #
    # We intentionally do NOT retry a TPD error.
    #
    # Retrying a daily-token-limit request will not solve it.
    #
    # ========================================================

    try:

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

                max_completion_tokens=(
                    MAX_COMPLETION_TOKENS
                ),

                # JSON mode is supported by the current
                # Qwen 3.6 vision model.
                #
                # If the account/model rejects JSON mode,
                # the fallback below retries once without it.
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

        print(
            "\n========== GROQ QUESTION PAGE "
            f"{page_number} RESPONSE =========="
        )

        print(
            raw
        )

        print(
            "==========================================\n"
        )

        result = parse_json_response(
            raw
        )

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

        # ====================================================
        # 429
        # ====================================================

        if is_rate_limit_error(
            error
        ):

            rate_message = (
                format_rate_limit_message(
                    error
                )
            )

            print(
                "\n========== GROQ RATE LIMIT =========="
            )

            print(
                rate_message
            )

            print(
                "====================================="
            )

            # IMPORTANT:
            # Do not retry TPD errors.
            raise RuntimeError(
                rate_message
            ) from error

        # ====================================================
        # JSON VALIDATION FALLBACK
        # ====================================================
        #
        # Some model/account combinations can reject
        # response_format even though the model supports
        # JSON mode.
        #
        # In that case, make ONE fallback request without
        # response_format.
        # ====================================================

        error_message = str(
            error
        ).lower()

        json_validation_error = (
            "json_validate_failed"
            in error_message
            or "failed to validate json"
            in error_message
        )

        if json_validation_error:

            print(
                "Groq JSON mode rejected."
            )

            print(
                "Retrying once without "
                "response_format..."
            )

            try:

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

                        max_completion_tokens=(
                            MAX_COMPLETION_TOKENS
                        ),
                    )
                )

                raw = (
                    response
                    .choices[0]
                    .message
                    .content
                )

                print(
                    "\n========== GROQ FALLBACK RESPONSE =========="
                )

                print(
                    raw
                )

                print(
                    "============================================"
                )

                result = parse_json_response(
                    raw
                )

                return sanitize_questions(
                    result,
                    page_number,
                )

            except Exception as fallback_error:

                if is_rate_limit_error(
                    fallback_error
                ):

                    raise RuntimeError(
                        format_rate_limit_message(
                            fallback_error
                        )
                    ) from fallback_error

                raise

        # ====================================================
        # OTHER ERROR
        # ====================================================

        print(
            f"Question extraction page "
            f"{page_number} failed: "
            f"{error}"
        )

        raise


# ============================================================
# EXTRACT QUESTIONS
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

            page_number = page[
                "page"
            ]

            image_bytes = (
                base64.b64decode(
                    page["image"]
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

        # Main question number.
        match = re.match(
            r"(\d+)",
            number,
        )

        main_number = (
            int(
                match.group(1)
            )
            if match
            else 999999
        )

        # Subquestion letter.
        sub_number = 0

        sub_match = re.search(
            r"\(([a-z])\)",
            number,
        )

        if sub_match:

            sub_number = (
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
            main_number,
            sub_number,
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
