import json
import re
from time import sleep
from typing import Any, Dict, List, Optional

from app.services.groq_client import client, MODEL_NAME


GRADING_PROMPT = """
You are an expert examination evaluator.

You are grading ONE examination question at a time.

Evaluate the student's answer against the question.

IMPORTANT RULES:

1. Grade only the provided question.
2. Grade only the provided student answer.
3. Do not invent missing content.
4. Do not give marks for information that the student did not write.
5. If the student answer is empty, give 0 marks.
6. Consider relevant theory, definitions, formulas, calculations,
   chemical equations, diagrams, and explanations.
7. For numerical questions, check:
   - formula
   - substitution
   - calculation
   - final answer
8. For chemistry questions, consider:
   - correct chemical equation
   - correct formula
   - correct terminology
   - correct explanation
9. Award partial marks when appropriate.
10. Do not exceed the maximum marks.
11. Keep feedback concise and useful.
12. Return valid JSON only.
13. Do not use markdown.
14. Do not include explanations outside JSON.

Return exactly this structure:

{
  "question_number": "1",
  "marks_awarded": 4,
  "max_marks": 5,
  "status": "correct",
  "feedback": "The answer correctly explains the main concept but one example is missing."
}

Allowed status values:

"correct"
"partially_correct"
"incorrect"
"unanswered"
"""


def clean_json_text(text: str) -> str:
    """
    Remove markdown code fences, think tags, and extract JSON object.
    """

    if not text:
        return ""

    text = text.strip()

    # Remove reasoning/think tags if returned by Groq models.
    text = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE).strip()

    match = re.search(
        r"```(?:json)?\s*([\s\S]*?)\s*```",
        text,
        flags=re.IGNORECASE,
    )

    if match:
        text = match.group(1).strip()

    first = text.find("{")
    last = text.rfind("}")

    if (
        first != -1
        and last != -1
        and last > first
    ):
        text = text[first:last + 1]

    return text.strip()


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


def sanitize_grade(
    result: Dict[str, Any],
    question_number: str,
    max_marks: int,
    question_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Validate and normalize one grading result.
    """

    if not isinstance(result, dict):
        result = {}

    awarded = safe_float(
        result.get(
            "score",
            result.get(
                "marks_awarded",
                0,
            ),
        ),
        0.0,
    )

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

    if awarded == 0 and not feedback:
        feedback = "No valid answer was provided."

    if awarded == float(max_marks):
        if status == "incorrect":
            status = "correct"

    elif awarded > 0:
        if status == "correct" and awarded < float(max_marks):
            status = "partially_correct"

    else:
        if status not in {
            "unanswered",
            "incorrect",
        }:
            status = "incorrect"

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


def grade_single_question(
    question: Dict[str, Any],
    answer_text: str,
    max_marks: int,
    question_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Grade one question independently.

    This is intentionally done one question at a time
    to avoid Groq TPM errors when a complete assessment
    is sent in one large request.
    """

    question_id = question_id or question.get("id") or question.get("question_id")

    question_number = str(
        question.get(
            "number",
            question.get(
                "question_number",
                "",
            ),
        )
    )

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

    # ---------------------------------------------------------
    # Unanswered question
    # ---------------------------------------------------------

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

Now evaluate this answer.

Return JSON only.
"""

    last_error: Optional[Exception] = None

    # ---------------------------------------------------------
    # Retry only temporary failures
    # ---------------------------------------------------------

    for attempt in range(3):

        try:

            print(
                f"Groq grading Q{question_number} "
                f"attempt {attempt + 1}/3..."
            )

            response = (
                client.chat.completions.create(
                    model=MODEL_NAME,

                    messages=[
                        {
                            "role": "user",
                            "content": user_prompt,
                        }
                    ],

                    temperature=0,

                    max_tokens=500,

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

            if not raw:
                raise ValueError(
                    "Groq returned an empty grading response."
                )

            result = json.loads(
                raw
            )

            return sanitize_grade(
                result,
                question_number,
                max_marks,
                question_id=question_id,
            )

        except json.JSONDecodeError as error:

            last_error = error

            print(
                f"Invalid JSON while grading "
                f"Q{question_number}: {error}"
            )

            if attempt < 2:
                sleep(
                    (attempt + 1) * 2
                )

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

            # -------------------------------------------------
            # Rate limits / oversized requests
            # -------------------------------------------------

            if (
                "429" in error_message
                or "413" in error_message
                or "rate_limit" in error_message.lower()
                or "rate limit" in error_message.lower()
                or "tokens per minute" in error_message.lower()
                or "requested" in error_message.lower()
                and "tokens" in error_message.lower()
            ):

                print(
                    f"Groq limit reached while grading "
                    f"Q{question_number}."
                )

                raise error

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


def combine_answer_text(
    answers: List[Dict[str, Any]],
) -> str:
    """
    Combine multiple answer objects belonging
    to the same question.

    This is important when an answer continues
    onto another page.
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


def grade_assessment(
    questions: List[Dict[str, Any]],
    answers: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Grade the complete assessment one question at a time.

    This avoids sending the entire assessment in one
    large Groq request.

    Answers with the same question number are combined.
    """

    print(
        "\n========== STARTING QUESTION-BY-QUESTION GRADING =========="
    )

    # ---------------------------------------------------------
    # Group answers by question number
    # ---------------------------------------------------------

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

    grades = []

    # ---------------------------------------------------------
    # Grade every question
    # ---------------------------------------------------------

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
            f"\n----------------------------------------"
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

        # -----------------------------------------------------
        # Grade
        # -----------------------------------------------------

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

        # Small delay between questions to avoid
        # immediately consuming the TPM window.
        sleep(0.5)

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


# -------------------------------------------------------------
# Backward-compatible function name
# -------------------------------------------------------------

def grade_answers(
    matches_or_questions: List[Dict[str, Any]],
    question_bytes_or_answers: Any = None,
    question_content_type: Optional[str] = None,
    answer_bytes: Optional[bytes] = None,
    answer_content_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Grade answers.

    Supports both signatures:
    1. grade_answers(matches, question_bytes, q_content_type, sheet_bytes, a_content_type)
    2. grade_answers(questions, answers)
    """

    # If first parameter is the list of matches from mapping.py
    if matches_or_questions and isinstance(matches_or_questions, list):
        first_item = matches_or_questions[0]
        if isinstance(first_item, dict) and (
            "question" in first_item
            or "answer" in first_item
            or "answer_id" in first_item
            or "question_id" in first_item
        ):
            print("\n========== STARTING QUESTION-BY-QUESTION GRADING FROM MATCHES ==========")
            grades = []
            for match in matches_or_questions:
                if not isinstance(match, dict):
                    continue

                question = match.get("question") or {}
                answer = match.get("answer") or {}
                question_id = match.get("question_id") or question.get("id")
                question_number = str(
                    match.get("question_number")
                    or question.get("number")
                    or question.get("question_number", "")
                ).strip()
                max_marks = safe_int(
                    question.get("max_marks", match.get("max_marks", 5)),
                    5,
                )
                if max_marks <= 0:
                    max_marks = 5

                status = match.get("status")
                answer_text = str(
                    answer.get("text", "") if isinstance(answer, dict) else ""
                ).strip()

                if status == "unanswered" or not answer_text:
                    print(f"\n----------------------------------------\nQUESTION {question_number} (Unanswered)")
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
                    grades.append(grade)
                    continue

                print(f"\n----------------------------------------\nQUESTION {question_number}")
                print(f"Max marks: {max_marks}")
                grade = grade_single_question(
                    question=question,
                    answer_text=answer_text,
                    max_marks=max_marks,
                    question_id=question_id,
                )
                grades.append(grade)
                print(
                    f"RESULT Q{question_number}: "
                    f"{grade['marks_awarded']}/"
                    f"{grade['max_marks']} "
                    f"({grade['status']})"
                )
                sleep(0.5)

            print("\n========== GRADING COMPLETE ==========")
            total_marks = sum(safe_float(g.get("marks_awarded", 0)) for g in grades)
            maximum_marks = sum(safe_float(g.get("max_marks", 0)) for g in grades)
            print(f"Total score: {total_marks}/{maximum_marks}")
            return grades

    return grade_assessment(
        questions=matches_or_questions,
        answers=question_bytes_or_answers if isinstance(question_bytes_or_answers, list) else [],
    )