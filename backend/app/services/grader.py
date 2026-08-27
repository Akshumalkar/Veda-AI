import json
import re
from time import sleep
from typing import Any, Dict, List, Optional

from app.services.groq_client import call_text


# ============================================================
# GRADING PROMPT
# ============================================================

GRADING_PROMPT = """
You are an expert examination evaluator.

You are grading ONE examination question at a time.

Evaluate ONLY the student's answer against the provided question.

IMPORTANT RULES:

1. Grade only the provided question.
2. Grade only the provided student answer.
3. Never invent missing content.
4. Never give marks for information the student did not write.
5. If the student answer is empty, give 0 marks.
6. Consider:
   - definitions
   - concepts
   - theory
   - formulas
   - calculations
   - diagrams
   - explanations
   - examples
   - technical terminology
7. For numerical questions check:
   - formula
   - substitution
   - calculation
   - final answer
8. Award partial marks when appropriate.
9. Never exceed maximum marks.
10. Keep feedback concise and useful.
11. Return ONLY valid JSON.
12. Do not return markdown.
13. Do not return explanations outside JSON.

The JSON must contain exactly these fields:

{
    "question_number": "1",
    "marks_awarded": 4,
    "max_marks": 5,
    "status": "partially_correct",
    "feedback": "The main concept is correct but one important point is missing."
}

Allowed status values:

correct
partially_correct
incorrect
unanswered
"""


# ============================================================
# JSON CLEANER
# ============================================================

def clean_json_text(text: str) -> str:
    """
    Clean model output and extract a JSON object.
    """

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


# ============================================================
# SAFE CONVERSIONS
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
    except (TypeError, ValueError):
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
    except (TypeError, ValueError):
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

    awarded = safe_float(
        result.get(
            "marks_awarded",
            result.get(
                "score",
                0,
            ),
        ),
        0.0,
    )

    awarded = max(
        0.0,
        awarded,
    )

    awarded = min(
        float(max_marks),
        awarded,
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

    if awarded == 0:

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
            feedback = "The answer satisfies the required points."

    else:

        if status == "correct":
            status = "partially_correct"

        if status == "incorrect":
            status = "partially_correct"

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

    # ========================================================
    # UNANSWERED
    # ========================================================

    if not answer_text:

        return {
            "question_id": question_id,
            "question_number": question_number,
            "score": 0,
            "max_score": max_marks,
            "marks_awarded": 0,
            "max_marks": max_marks,
            "status": "unanswered",
            "feedback": "No answer was written for this question.",
        }

    # ========================================================
    # USER PROMPT
    # ========================================================

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

Evaluate the student's answer now.

Return ONLY one JSON object.

Do not use markdown.
Do not use code fences.
Do not add any text before or after the JSON.

Example:

{{
    "question_number": "{question_number}",
    "marks_awarded": 3,
    "max_marks": {max_marks},
    "status": "partially_correct",
    "feedback": "The answer explains the main concept but misses two important points."
}}
"""

    last_error: Optional[Exception] = None

    # ========================================================
    # RETRIES
    # ========================================================

    for attempt in range(3):

        try:

            print(
                f"Groq grading Q{question_number} "
                f"attempt {attempt + 1}/3..."
            )

            # ====================================================
            # CENTRALIZED GROQ TEXT CALL
            # ====================================================

            response = call_text(
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt,
                    }
                ],
                temperature=0,
                max_tokens=2000,
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
                f"Raw grading response Q{question_number}: "
                f"{raw[:1000]}"
            )

            if not raw:
                raise ValueError(
                    "Groq returned an empty grading response."
                )

            result = json.loads(
                raw
            )

            return sanitize_grade(
                result=result,
                question_number=question_number,
                max_marks=max_marks,
                question_id=question_id,
            )

        # ====================================================
        # INVALID JSON
        # ====================================================

        except json.JSONDecodeError as error:

            last_error = error

            print(
                f"Invalid JSON while grading "
                f"Q{question_number}: {error}"
            )

            if attempt < 2:

                wait_seconds = (
                    attempt + 1
                ) * 2

                sleep(
                    wait_seconds
                )

        # ====================================================
        # OTHER ERRORS
        # ====================================================

        except Exception as error:

            last_error = error

            error_message = str(
                error
            )

            print(
                f"Groq grading Q{question_number} "
                f"attempt {attempt + 1}/3 failed: "
                f"{error_message}"
            )

            lower_error = (
                error_message.lower()
            )

            # ------------------------------------------------
            # DO NOT RETRY HARD API ERRORS
            # ------------------------------------------------

            if (
                "429" in error_message
                or "rate_limit" in lower_error
                or "rate limit" in lower_error
                or "tokens per minute" in lower_error
                or "413" in error_message
                or "model_not_found" in lower_error
                or "does not exist" in lower_error
                or "json_validate_failed" in lower_error
            ):

                print(
                    f"Non-retryable Groq error while "
                    f"grading Q{question_number}."
                )

                raise error

            # ------------------------------------------------
            # RETRY TEMPORARY ERRORS
            # ------------------------------------------------

            if attempt < 2:

                wait_seconds = (
                    attempt + 1
                ) * 2

                print(
                    f"Retrying Q{question_number} "
                    f"in {wait_seconds} seconds..."
                )

                sleep(
                    wait_seconds
                )

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

        if text:

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
        "\n========== STARTING QUESTION-BY-QUESTION GRADING =========="
    )

    # ========================================================
    # GROUP ANSWERS BY QUESTION NUMBER
    # ========================================================

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
            []
        ).append(
            answer
        )

    print(
        f"Answer groups detected: "
        f"{len(answer_map)}"
    )

    # ========================================================
    # GRADE EVERY QUESTION
    # ========================================================

    grades = []

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
            []
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
            f"Answer objects: "
            f"{len(matching_answers)}"
        )

        grade = grade_single_question(
            question=question,
            answer_text=answer_text,
            max_marks=max_marks,
            question_id=question.get("id"),
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

    # ========================================================
    # TOTAL
    # ========================================================

    print(
        "\n========== GRADING COMPLETE =========="
    )

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
        f"Total score: "
        f"{total_marks}/{maximum_marks}"
    )

    return grades


# ============================================================
# BACKWARD-COMPATIBLE grade_answers()
# ============================================================

def grade_answers(
    matches_or_questions: List[Dict[str, Any]],
    question_bytes_or_answers: Any = None,
    question_content_type: Optional[str] = None,
    answer_bytes: Optional[bytes] = None,
    answer_content_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Grade answers.

    Supported signatures:

    1.
    grade_answers(
        matches,
        question_bytes,
        question_content_type,
        answer_bytes,
        answer_content_type
    )

    2.
    grade_answers(
        questions,
        answers
    )
    """

    if not matches_or_questions:
        return []

    # ========================================================
    # MATCHES FROM mapping.py
    # ========================================================

    if isinstance(
        matches_or_questions,
        list,
    ):

        first_item = (
            matches_or_questions[0]
        )

        if (
            isinstance(
                first_item,
                dict,
            )
            and (
                "question" in first_item
                or "answer" in first_item
                or "answer_id" in first_item
                or "question_id" in first_item
            )
        ):

            print(
                "\n========== STARTING GRADING FROM MATCHES =========="
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

                match_status = (
                    match.get(
                        "status"
                    )
                )

                answer_text = str(
                    answer.get(
                        "text",
                        "",
                    )
                    if isinstance(
                        answer,
                        dict,
                    )
                    else ""
                ).strip()

                # =================================================
                # UNANSWERED
                # =================================================

                if (
                    match_status == "unanswered"
                    or not answer_text
                ):

                    print(
                        "\n----------------------------------------"
                    )

                    print(
                        f"QUESTION {question_number} "
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

                # =================================================
                # GRADE MATCH
                # =================================================

                print(
                    "\n----------------------------------------"
                )

                print(
                    f"QUESTION {question_number}"
                )

                print(
                    f"Max marks: {max_marks}"
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

            # =================================================
            # TOTAL
            # =================================================

            print(
                "\n========== GRADING COMPLETE =========="
            )

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
                f"Total score: "
                f"{total_marks}/{maximum_marks}"
            )

            return grades

    # ========================================================
    # NORMAL questions + answers
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
