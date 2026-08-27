import base64
import json
import re
from typing import Any, Dict, List

from app.services.groq_client import (
    call_vision,
)
from app.utils.pdf import pdf_to_images


# ============================================================
# QUESTION EXTRACTION PROMPT
# ============================================================

QUESTION_PROMPT = """
You are an examination question extraction system.

Look carefully at the supplied examination paper image.

Extract EVERY visible examination question.

Return ONLY valid JSON.

The response MUST follow exactly this structure:

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

5. Do NOT summarize the question.

6. Do NOT rewrite the question.

7. Do NOT invent missing words.

8. Ignore:
   - college name
   - university name
   - examination name
   - subject name
   - date
   - student information
   - roll number
   - general instructions
   - page headers
   - page footers

9. Extract only actual examination questions.

10. Preserve mathematical expressions as accurately as possible.

11. Preserve chemical formulas and equations.

12. Preserve programming/code-related text when visible.

13. If marks are printed beside a question, use those marks.

14. If marks are not visible, use 5.

15. Coordinates must be normalized from 0 to 1000.

16. bbox.x and bbox.y represent the top-left corner.

17. bbox.width and bbox.height represent the question's region.

18. The bounding box should cover the COMPLETE question text.

19. Do not use negative coordinates.

20. Do not return coordinates outside 0-1000.

21. Use the supplied page number.

22. Every extracted question MUST contain:
   - id
   - number
   - text
   - page
   - max_marks
   - bbox

23. Return valid JSON only.

24. Do not use markdown.

25. Do not include explanations outside JSON.

26. If no examination questions are visible, return:

{
  "questions": []
}
"""


# ============================================================
# JSON CLEANING
# ============================================================

def clean_json_text(
    text: str,
) -> str:
    """
    Clean model output before JSON parsing.
    """

    if not text:
        return ""

    text = text.strip()

    # Remove <think> blocks.
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
# JSON PARSING
# ============================================================

def parse_json_response(
    text: str,
) -> Dict[str, Any]:
    """
    Safely parse Groq JSON response.
    """

    cleaned = clean_json_text(
        text
    )

    if not cleaned:

        raise ValueError(
            "Groq returned an empty "
            "question extraction response."
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
    ).decode(
        "utf-8"
    )

    return (
        f"data:{mime_type};base64,{encoded}"
    )


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

        return int(
            float(value)
        )

    except (
        TypeError,
        ValueError,
    ):

        return default


# ============================================================
# BOUNDING BOX
# ============================================================

def sanitize_bbox(
    bbox: Dict[str, Any],
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
    Normalize examination question numbering.

    Examples:

    Q1      -> 1
    1.1     -> 1(a)
    1(a)    -> 1(a)
    1-a     -> 1(a)
    1.a     -> 1(a)
    1(i)    -> 1(a)
    1(ii)   -> 1(b)
    """

    if value is None:
        return None

    value = str(
        value
    ).strip().lower()

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
            match.group(
                2
            )
        )

        if 1 <= sub_number <= 26:

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
        # MARKS
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

        # ----------------------------------------------------
        # FINAL OBJECT
        # ----------------------------------------------------

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
):
    """
    Extract questions from a single image page.

    Uses Groq vision automatically.
    """

    page_prompt = (
        QUESTION_PROMPT
        + "\n\n"
        + f"This is page {page_number}.\n"
        + f"Every question MUST use page={page_number}.\n"
        + "\nReturn JSON only."
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

        response = call_vision(
            messages=[
                {
                    "role": "user",
                    "content": message_content,
                }
            ],
            temperature=0,
            max_tokens=2500,
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

        result = parse_json_response(
            raw
        )

        return sanitize_questions(
            result,
            page_number,
        )

    except Exception as error:

        error_message = str(
            error
        )

        print(
            f"Question extraction page "
            f"{page_number} failed: "
            f"{error_message}"
        )

        # Do not retry here.
        #
        # call_vision() already handles:
        # - model fallback
        # - 429 detection
        #
        # Repeating the same request here would
        # unnecessarily consume Groq quota.

        raise


# ============================================================
# EXTRACT QUESTIONS FROM PDF / IMAGE
# ============================================================

def extract_questions(
    file_bytes: bytes,
    content_type: str,
):
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
            "\nQuestion paper contains "
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

    # ========================================================
    # IMAGE
    # ========================================================

    else:

        image_mime_type = (
            content_type
            or "image/jpeg"
        )

        page_result = (
            extract_questions_from_page(
                image_bytes=file_bytes,
                page_number=1,
                mime_type=image_mime_type,
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
        item,
    ):

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
            int(
                match.group(1)
            )
            if match
            else 999999
        )

        return (
            item.get(
                "page",
                999999,
            ),
            question_number,
        )

    all_questions = sorted(
        all_questions,
        key=question_sort_key,
    )

    # ========================================================
    # STABLE IDs
    # ========================================================

    for index, question in enumerate(
        all_questions,
        start=1,
    ):

        question[
            "id"
        ] = f"q{index}"

    # ========================================================
    # LOG FINAL RESULT
    # ========================================================

    print(
        "\n========== FINAL QUESTION EXTRACTION =========="
    )

    print(
        "Total questions extracted: "
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
