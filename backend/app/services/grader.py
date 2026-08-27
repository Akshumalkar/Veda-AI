import json
import re
from time import sleep
from typing import Any, Dict, List, Optional

from app.services.groq_client import client, MODEL_NAME


# ============================================================
# GRADING PROMPT
# ============================================================

GRADING_PROMPT = """
You are an expert examination evaluator.

Grade ONE examination question using ONLY:
1. The question provided.
2. The student's answer provided.

Rules:

- Do not invent information.
- Do not give marks for information the student did not write.
- If the answer is empty, give 0 marks.
- Award partial marks when appropriate.
- Never exceed the maximum marks.
- Consider definitions, concepts, explanations, formulas,
  calculations, diagrams, examples and relevant technical terms.
- For numerical questions consider formula, substitution,
  calculation and final answer.
- Keep feedback short and useful.
- Return ONLY valid JSON.
- Do not use markdown.
- Do not include any text outside JSON.

Use exactly this JSON structure:

{
  "marks_awarded": 4,
  "status": "partially_correct",
  "feedback": "The main concept is correct but one important point is missing."
}

Allowed status values:

"correct"
"partially_correct"
"incorrect"
"unanswered"
"""


# ============================================================
# JSON CLEANING
# ============================================================

def clean_json_text(text: str) -> str:
    """
    Clean and extract a JSON object from Groq output.
    """

    if not text:
        return ""

    text = str(text).strip()

    # Remove <think>...</think> blocks.
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

    # Extract first JSON object.
    first = text.find("{")
    last = text.rfind("}")

    if first != -1 and last != -1 and last > first:
        text = text[first:last + 1]

    return text.strip()


def parse_json_response(text: str) -> Dict[str, Any]:
    """
    Safely parse Groq JSON response.
    """

    cleaned = clean_json_text(text)

    if not cleaned:
        raise ValueError(
            "Groq returned an empty grading response."
        )

    try:
        result = json.loads(cleaned)

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid JSON returned by Groq: {error}"
        ) from error

    if not isinstance(result, dict):
        raise ValueError(
            "Groq grading response is not a JSON object."
        )

    return result


# ============================================================
# SAFE VALUE HELPERS
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


def safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """
    Safely convert a value to float.
    """

    try:
        return float(value)

    except (
        TypeError,
        ValueError,
    ):
        return default


# ============================================================
# SANITIZE GRADE
# ============================================================

def sanitize_grade(
    result: Dict[str, Any],
    question_number: str,
    max_marks: int,
    question_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Validate and normalize a grading result.
    """

    if not isinstance(result, dict):
        result = {}

    # Support both:
    # marks_awarded
    # score
    awarded = result.get(
        "marks_awarded",
        result.get(
            "score",
            0,
        ),
    )

    awarded = safe_float(
        awarded,
        0.0,
    )

    # Keep score inside valid range.
    awarded = max(
        0.0,
        min(
            float(max_marks),
            awarded,
        ),
    )

    status = str(
        result.get(
            "status",
            "incorrect",
        )
    ).strip().lower()

    allowed_statuses = {
        "correct",
        "partially_correct",
        "incorrect",
        "unanswered",
    }

    if status not in allowed_statuses:
        status = "incorrect"

    feedback = result.get(
        "feedback",
        "",
    )

    if feedback is None:
        feedback = ""

    feedback = str(
        feedback
    ).strip()

    # Make status consistent with score.
    if awarded <= 0:

        if status not in {
            "unanswered",
            "incorrect",
        }:
            status = "incorrect"

        if not feedback:
            feedback = "No valid answer was provided."

    elif awarded >= float(max_marks):

        awarded = float(max_marks)

        status = "correct"

        if not feedback:
            feedback = "The answer is correct."

    else:

        if status == "correct":
            status = "partially_correct"

        if status == "unanswered":
            status = "partially_correct"

        if not feedback:
            feedback = "The answer is partially correct."

    return {
        "question_id": question_id,
        "question_number": str(
            question_number
        ),
        "score": awarded,
        "max_score": max_marks,
        "marks_awarded": awarded,
        "max_marks": max_marks,
        "status": status,
        "feedback": feedback,
    }


# ============================================================
# GRADE ONE QUESTION
# ============================================================

def grade_single_question(
    question: Dict[str, Any],
    answer_text: str,
    max_marks: int,
    question_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Grade one question independently.

    One question is sent to Groq at a time to keep
    requests small and reduce token usage.
    """

    question_id = (
        question_id
        or question.get("id")
        or question.get("question_id")
    )

    question_number = str(
        question.get(
            "number",
            question.get(
                "question_number",
                "",
            ),
        )
    ).strip()

    question_text = str(
        question.get(
            "text",
            "",
        )
    ).strip()

    answer_text = str(
        answer_text or ""
    ).strip()

    max_marks = safe_int(
        max_marks,
        5,
    )

    if max_marks <= 0:
        max_marks = 5

    # --------------------------------------------------------
    # Unanswered
    # --------------------------------------------------------

    if not answer_text:

        print(
            f"Q{question_number}: No answer. "
            "Skipping Groq."
        )

        return {
            "question_id": question_id,
            "question_number": question_number,
            "score": 0,
            "max_score": max_marks,
            "marks_awarded": 0,
            "max_marks": max_marks,
            "status": "unanswered",
            "feedback": (
                "No answer was written for this question."
            ),
        }

    # --------------------------------------------------------
    # Build small grading prompt
    # --------------------------------------------------------

    user_prompt = f"""
{GRADING_PROMPT}

QUESTION NUMBER:
{question_number}

MAXIMUM MARKS:
{max_marks}

QUESTION:
{question_text}

STUDENT ANSWER:
{answer_text}

Return JSON only.
"""

    last_error: Optional[Exception] = None

    # --------------------------------------------------------
    # Retry only non-rate-limit failures
    # --------------------------------------------------------

    for attempt in range(2):

        try:

            print(
                f"Groq grading Q{question_number} "
                f"attempt {attempt + 1}/2..."
            )

            response = client.chat.completions.create(
                model=MODEL_NAME,

                messages=[
                    {
                        "role": "user",
                        "content": user_prompt,
                    }
                ],

                temperature=0,

                # Keep output small.
                max_tokens=300,

                # Force JSON response.
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
                f"\n========== GROQ GRADING Q"
                f"{question_number} =========="
            )

            print(raw)

            print(
                "==========================================\n"
            )

            result = parse_json_response(
                raw
            )

            grade = sanitize_grade(
                result=result,
                question_number=question_number,
                max_marks=max_marks,
                question_id=question_id,
            )

            return grade

        except json.JSONDecodeError as error:

            last_error = error

            print(
                f"Invalid JSON while grading "
                f"Q{question_number}: {error}"
            )

            if attempt == 0:
                sleep(2)

        except Exception as error:

            last_error = error

            error_message = str(
                error
            )

            error_lower = error_message.lower()

            print(
                f"Groq grading Q{question_number} "
                f"attempt {attempt + 1}/2 failed: "
                f"{error_message}"
            )

            # ------------------------------------------------
            # NEVER RETRY RATE LIMITS
            # ------------------------------------------------

            is_rate_limit = (
                "429" in error_message
                or "rate_limit" in error_lower
                or "rate limit" in error_lower
                or "tokens per minute" in error_lower
                or "tokens per day" in error_lower
                or "tpd" in error_lower
                or "tpm" in error_lower
            )

            if is_rate_limit:

                print(
                    f"Groq rate limit reached while "
                    f"grading Q{question_number}."
                )

                raise error

            # ------------------------------------------------
            # Oversized request
            # ------------------------------------------------

            is_too_large = (
                "413" in error_message
                or "request too large" in error_lower
                or "too many tokens" in error_lower
            )

            if is_too_large:

                print(
                    f"Groq request too large while "
                    f"grading Q{question_number}."
                )

                raise error

            # ------------------------------------------------
            # Retry temporary errors once
            # ------------------------------------------------

            if attempt == 0:

                print(
                    f"Retrying Q{question_number} "
                    "in 2 seconds..."
                )

                sleep(2)

    # --------------------------------------------------------
    # Final failure
    # --------------------------------------------------------

    if last_error:
        raise last_error

    raise RuntimeError(
        f"Grading failed for question "
        f"{question_number}."
    )


# ============================================================
# COMBINE ANSWER TEXT
# ============================================================

def combine_answer_text(
    answers: List[Dict[str, Any]],
) -> str:
    """
    Combine multiple answer objects belonging
    to the same question.

    Useful when an answer continues on another page.
    """

    if not answers:
        return ""

    parts = []

    for answer in answers:

        if not isinstance(
            answer,
            dict,
        ):
            continue

        text = answer.get(
            "text",
            "",
        )

        if text is None:
            continue

        text = str(
            text
        ).strip()

        if text:
            parts.append(
                text
            )

    return "\n".join(
        parts
    ).strip()


# ============================================================
# GRADE COMPLETE ASSESSMENT
# ============================================================

def grade_assessment(
    questions: List[Dict[str, Any]],
    answers: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Grade complete assessment one question at a time.
    """

    print(
        "\n========== STARTING QUESTION-BY-QUESTION "
        "GRADING =========="
    )

    # --------------------------------------------------------
    # Group answers by question number
    # --------------------------------------------------------

    answer_map: Dict[
        str,
        List[Dict[str, Any]]
    ] = {}

    for answer in answers:

        if not isinstance(
            answer,
            dict,
        ):
            continue

        question_number = answer.get(
            "question_number"
        )

        if question_number is None:
            continue

        question_number = str(
            question_number
        ).strip()

        if not question_number:
            continue

        answer_map.setdefault(
            question_number,
            [],
        ).append(
            answer
        )

    print(
        f"Questions received: {len(questions)}"
    )

    print(
        f"Answer objects received: {len(answers)}"
    )

    print(
        f"Mapped question numbers: "
        f"{len(answer_map)}"
    )

    grades = []

    # --------------------------------------------------------
    # Grade every question
    # --------------------------------------------------------

    for index, question in enumerate(
        questions,
        start=1,
    ):

        if not isinstance(
            question,
            dict,
        ):
            continue

        question_number = str(
            question.get(
                "number",
                question.get(
                    "question_number",
                    index,
                ),
            )
        ).strip()

        max_marks = safe_int(
            question.get(
                "max_marks",
                5,
            ),
            5,
        )

        if max_marks <= 0:
            max_marks = 5

        matching_answers = answer_map.get(
            question_number,
            [],
        )

        answer_text = combine_answer_text(
            matching_answers
        )

        print(
            "\n----------------------------------------"
        )

        print(
            f"QUESTION {question_number}"
        )

        print(
            f"Max marks: {max_marks}"
        )

        print(
            f"Matching answer objects: "
            f"{len(matching_answers)}"
        )

        # ----------------------------------------------------
        # Grade
        # ----------------------------------------------------

        grade = grade_single_question(
            question=question,
            answer_text=answer_text,
            max_marks=max_marks,
            question_id=question.get(
                "id"
            ),
        )

        grades.append(
            grade
        )

        print(
            f"RESULT Q{question_number}: "
            f"{grade['marks_awarded']}/"
            f"{grade['max_marks']} "
            f"({grade['status']})"
        )

        # Small delay between requests.
        sleep(0.5)

    # --------------------------------------------------------
    # Calculate totals
    # --------------------------------------------------------

    total_marks = sum(
        safe_float(
            grade.get(
                "marks_awarded",
                0,
            )
        )
        for grade in grades
    )

    maximum_marks = sum(
        safe_float(
            grade.get(
                "max_marks",
                0,
            )
        )
        for grade in grades
    )

    print(
        "\n========== GRADING COMPLETE =========="
    )

    print(
        f"Total score: "
        f"{total_marks}/{maximum_marks}"
    )

    print(
        "=======================================\n"
    )

    return grades


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

def grade_answers(
    matches_or_questions: List[Dict[str, Any]],
    question_bytes_or_answers: Any = None,
    question_content_type: Optional[str] = None,
    answer_bytes: Optional[bytes] = None,
    answer_content_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Backward-compatible grading function.

    Supports:

    1. grade_answers(matches, question_bytes,
                     question_content_type,
                     answer_bytes,
                     answer_content_type)

    2. grade_answers(questions, answers)
    """

    # ========================================================
    # EMPTY INPUT
    # ========================================================

    if not matches_or_questions:

        print(
            "No questions or matches available for grading."
        )

        return []

    # ========================================================
    # MATCHES FROM mapping.py
    # ========================================================

    if isinstance(
        matches_or_questions,
        list,
    ):

        first_item = matches_or_questions[0]

        if isinstance(
            first_item,
            dict,
        ) and (
            "question" in first_item
            or "answer" in first_item
            or "answer_id" in first_item
            or "question_id" in first_item
        ):

            print(
                "\n========== STARTING "
                "GRADING FROM MATCHES =========="
            )

            grades = []

            for match in matches_or_questions:

                if not isinstance(
                    match,
                    dict,
                ):
                    continue

                question = (
                    match.get(
                        "question"
                    )
                    or {}
                )

                answer = (
                    match.get(
                        "answer"
                    )
                    or {}
                )

                question_id = (
                    match.get(
                        "question_id"
                    )
                    or question.get(
                        "id"
                    )
                )

                question_number = str(
                    match.get(
                        "question_number"
                    )
                    or question.get(
                        "number"
                    )
                    or question.get(
                        "question_number",
                        "",
                    )
                ).strip()

                max_marks = safe_int(
                    question.get(
                        "max_marks",
                        match.get(
                            "max_marks",
                            5,
                        ),
                    ),
                    5,
                )

                if max_marks <= 0:
                    max_marks = 5

                status = str(
                    match.get(
                        "status",
                        "",
                    )
                ).strip().lower()

                answer_text = ""

                if isinstance(
                    answer,
                    dict,
                ):

                    answer_text = str(
                        answer.get(
                            "text",
                            "",
                        )
                        or ""
                    ).strip()

                # ------------------------------------------------
                # Unanswered
                # ------------------------------------------------

                if (
                    status == "unanswered"
                    or not answer_text
                ):

                    print(
                        "\n----------------------------------------"
                    )

                    print(
                        f"QUESTION "
                        f"{question_number} "
                        "(Unanswered)"
                    )

                    grade = {
                        "question_id": question_id,
                        "question_number": question_number,
                        "score": 0,
                        "max_score": max_marks,
                        "marks_awarded": 0,
                        "max_marks": max_marks,
                        "status": "unanswered",
                        "feedback": "Not attempted.",
                    }

                    grades.append(
                        grade
                    )

                    continue

                # ------------------------------------------------
                # Grade matched answer
                # ------------------------------------------------

                print(
                    "\n----------------------------------------"
                )

                print(
                    f"QUESTION "
                    f"{question_number}"
                )

                print(
                    f"Max marks: "
                    f"{max_marks}"
                )

                grade = grade_single_question(
                    question=question,
                    answer_text=answer_text,
                    max_marks=max_marks,
                    question_id=question_id,
                )

                grades.append(
                    grade
                )

                print(
                    f"RESULT Q{question_number}: "
                    f"{grade['marks_awarded']}/"
                    f"{grade['max_marks']} "
                    f"({grade['status']})"
                )

                sleep(0.5)

            # ------------------------------------------------
            # Match grading totals
            # ------------------------------------------------

            total_marks = sum(
                safe_float(
                    grade.get(
                        "marks_awarded",
                        0,
                    )
                )
                for grade in grades
            )

            maximum_marks = sum(
                safe_float(
                    grade.get(
                        "max_marks",
                        0,
                    )
                )
                for grade in grades
            )

            print(
                "\n========== MATCH GRADING COMPLETE =========="
            )

            print(
                f"Total score: "
                f"{total_marks}/"
                f"{maximum_marks}"
            )

            print(
                "=============================================\n"
            )

            return grades

    # ========================================================
    # QUESTIONS + ANSWERS
    # ========================================================

    answers = (
        question_bytes_or_answers
        if isinstance(
            question_bytes_or_answers,
            list,
        )
        else []
    )

    return grade_assessment(
        questions=matches_or_questions,
        answers=answers,
    )
