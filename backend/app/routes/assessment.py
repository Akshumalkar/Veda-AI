import asyncio
import base64
import json
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import APIRouter, File, UploadFile, Form, HTTPException

from app.services.question_extractor import extract_questions
from app.services.answer_extractor import extract_answers
from app.services.mapping import map_questions_to_answers
from app.services.grader import grade_answers
from app.services.cache import compute_cache_key, get_cached_result, set_cached_result
from app.utils.pdf import pdf_to_images


BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def create_error_response(error_type: str, message: str):
    return {
        "success": False,
        "error": {
            "type": error_type,
            "message": message,
        },
    }


@router.post("/process")
async def process_assessment(
    question_paper: UploadFile = File(...),
    answer_sheets: list[UploadFile] = File(...),
    student_names: Optional[str] = Form(None),
):
    try:
        # ---------------------------------------------------------
        # 1. Validate answer sheet count
        # ---------------------------------------------------------

        if not answer_sheets:
            raise HTTPException(
                status_code=400,
                detail=create_error_response(
                    "missing_answer_sheet",
                    "Please upload a student answer sheet.",
                ),
            )

        # For the assignment core flow, process one student only.
        if len(answer_sheets) > 1:
            raise HTTPException(
                status_code=400,
                detail=create_error_response(
                    "multiple_answer_sheets",
                    "Please upload exactly one student answer sheet for this assessment.",
                ),
            )

        # ---------------------------------------------------------
        # 2. Read Question Paper
        # ---------------------------------------------------------

        question_bytes = await question_paper.read()

        if not question_bytes:
            raise HTTPException(
                status_code=400,
                detail=create_error_response(
                    "empty_question_paper",
                    "The question paper is empty.",
                ),
            )

        if len(question_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=create_error_response(
                    "file_too_large",
                    "Question paper exceeds the maximum allowed size of 10 MB.",
                ),
            )

        q_content_type = question_paper.content_type or "application/pdf"

        # ---------------------------------------------------------
        # 3. Read Student Answer Sheet
        # ---------------------------------------------------------

        answer_sheet = answer_sheets[0]

        sheet_bytes = await answer_sheet.read()

        if not sheet_bytes:
            raise HTTPException(
                status_code=400,
                detail=create_error_response(
                    "empty_answer_sheet",
                    "The student answer sheet is empty.",
                ),
            )

        if len(sheet_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=create_error_response(
                    "file_too_large",
                    "Student answer sheet exceeds the maximum allowed size of 10 MB.",
                ),
            )

        a_content_type = answer_sheet.content_type or "application/pdf"

        # ---------------------------------------------------------
        # 4. Student information
        # ---------------------------------------------------------

        student_name = "Student"

        if student_names:
            try:
                parsed_names = json.loads(student_names)

                if isinstance(parsed_names, list) and parsed_names:
                    student_name = str(parsed_names[0]).strip()

                elif isinstance(parsed_names, str):
                    student_name = parsed_names.strip()

            except Exception:
                student_name = student_names.split(",")[0].strip()

        if not student_name:
            student_name = "Student"

        # ---------------------------------------------------------
        # 5. Prepare answer-sheet pages for frontend
        # ---------------------------------------------------------

        if a_content_type == "application/pdf":
            raw_pages = await asyncio.to_thread(
                pdf_to_images,
                sheet_bytes,
            )

            answer_pages = [
                {
                    "page": page["page"],
                    "image": page["image"],
                }
                for page in raw_pages
            ]

        else:
            encoded = base64.b64encode(sheet_bytes).decode("utf-8")

            answer_pages = [
                {
                    "page": 1,
                    "image": encoded,
                }
            ]

        # ---------------------------------------------------------
        # 6. Check cache
        # ---------------------------------------------------------

        cache_key = compute_cache_key(
            question_bytes,
            sheet_bytes,
        )

        # DEVELOPMENT MODE:
        # Disable cache while testing extraction, mapping,
        # highlighting and grading.

        cached_result = None

        # if cached_result:
        #     cached_result["student_name"] = student_name
        #     cached_result["answer_pages"] = answer_pages
        #     return cached_result

        # ---------------------------------------------------------
        # 7. Extract Questions
        # ---------------------------------------------------------

        print("STEP 1/4: Extracting questions...")

        try:
            question_result = await asyncio.to_thread(
                extract_questions,
                question_bytes,
                q_content_type,
            )
        except Exception as error:
            error_message = str(error)

            print(
                "QUESTION EXTRACTION FAILED:",
                error_message,
            )

            if (
                "429" in error_message
                or "RESOURCE_EXHAUSTED" in error_message
            ):
                raise HTTPException(
                    status_code=429,
                    detail=create_error_response(
                        "gemini_quota_exceeded",
                        "Gemini API quota has been exceeded while extracting questions. Please try again later.",
                    ),
                )

            raise HTTPException(
                status_code=502,
                detail=create_error_response(
                    "question_extraction_failed",
                    "Unable to extract questions from the uploaded question paper.",
                ),
            )

        questions = question_result.get("questions", [])

        if not questions:
            raise HTTPException(
                status_code=422,
                detail=create_error_response(
                    "no_questions_found",
                    "No questions could be extracted from the question paper.",
                ),
            )

        print(
            f"Question extraction complete: {len(questions)} questions"
        )

        # ---------------------------------------------------------
        # 8. Extract Answers
        # ---------------------------------------------------------

        print("STEP 2/4: Extracting student answers...")

        try:
            answer_result = await asyncio.to_thread(
                extract_answers,
                sheet_bytes,
                a_content_type,
            )
        except Exception as error:
            error_message = str(error)

            print(
                "ANSWER EXTRACTION FAILED:",
                error_message,
            )

            if (
                "429" in error_message
                or "RESOURCE_EXHAUSTED" in error_message
            ):
                raise HTTPException(
                    status_code=429,
                    detail=create_error_response(
                        "gemini_quota_exceeded",
                        "Gemini API quota has been exceeded while extracting answers. Please try again later.",
                    ),
                )

            raise HTTPException(
                status_code=502,
                detail=create_error_response(
                    "answer_extraction_failed",
                    "Unable to extract answers from the uploaded student answer sheet.",
                ),
            )

        answers = answer_result.get("answers", [])

        print(
            f"Answer extraction complete: {len(answers)} answers"
        )

        # ---------------------------------------------------------
        # 9. Map Questions to Answers
        # ---------------------------------------------------------

        print("STEP 3/4: Mapping questions to answers...")

        mapping_result = map_questions_to_answers(
            questions,
            answers,
        )

        matches = mapping_result.get("matches", [])
        unmatched_answers = mapping_result.get(
            "unmatched_answers",
            [],
        )

        # ---------------------------------------------------------
        # 10. Grade Answers
        # ---------------------------------------------------------

        print("STEP 4/4: Grading answers...")

        try:
            grades = await asyncio.to_thread(
                grade_answers,
                matches,
                question_bytes,
                q_content_type,
                sheet_bytes,
                a_content_type,
            )

        except Exception as error:
            error_message = str(error)

            print(
                "GRADING FAILED:",
                error_message,
            )

            if (
                "429" in error_message
                or "RESOURCE_EXHAUSTED" in error_message
            ):
                raise HTTPException(
                    status_code=429,
                    detail=create_error_response(
                        "gemini_quota_exceeded",
                        "Gemini API quota has been exceeded while grading the assessment. Please try again later.",
                    ),
                )

            raise HTTPException(
                status_code=502,
                detail=create_error_response(
                    "grading_failed",
                    "Unable to grade the extracted answers.",
                ),
            )

        # ---------------------------------------------------------
        # 11. Merge grades into matches
        # ---------------------------------------------------------

        grade_lookup = {
            grade.get("question_id"): grade
            for grade in grades
        }

        for match in matches:
            question_id = match.get("question_id")

            grade = grade_lookup.get(
                question_id,
                {},
            )

            match["grading"] = {
                "score": grade.get("score", 0),
                "max_score": grade.get(
                    "max_score",
                    match.get("max_marks", 5),
                ),
                "feedback": grade.get(
                    "feedback",
                    "",
                ),
            }

        # ---------------------------------------------------------
        # 12. Calculate score
        # ---------------------------------------------------------

        answered = [
            match
            for match in matches
            if match.get("status") == "answered"
        ]

        unanswered = [
            match
            for match in matches
            if match.get("status") == "unanswered"
        ]

        total_score = sum(
            match.get("grading", {}).get("score", 0)
            for match in answered
        )

        max_score = sum(
            match.get("grading", {}).get(
                "max_score",
                match.get("max_marks", 5),
            )
            for match in matches
            if match.get("status") in (
                "answered",
                "unanswered",
            )
        )

        percentage = (
            round((total_score / max_score) * 100, 1)
            if max_score > 0
            else 0
        )

        grade_letter = (
            "A"
            if percentage >= 80
            else "B"
            if percentage >= 65
            else "C"
            if percentage >= 50
            else "D"
        )

        # ---------------------------------------------------------
        # 13. Build final REAL result
        # ---------------------------------------------------------

        result = {
            "success": True,

            "student_name": student_name,

            "questions": questions,

            "answers": answers,

            "matches": matches,

            "unmatched_answers": unmatched_answers,

            "answer_pages": answer_pages,

            "total_score": total_score,

            "max_score": max_score,

            "percentage": percentage,

            "grade": grade_letter,

            "summary": {
                "total_questions": len(
                    [
                        match
                        for match in matches
                        if match.get("status") != "parent"
                    ]
                ),
                "answered": len(answered),
                "unanswered": len(unanswered),
                "unmatched_answers": len(unmatched_answers),
                "total_score": total_score,
                "max_score": max_score,
            },

            "message": (
                f"Assessment evaluated successfully "
                f"for {student_name}."
            ),
        }

        # ---------------------------------------------------------
        # 14. Cache REAL result
        # ---------------------------------------------------------

        set_cached_result(
            cache_key,
            result,
        )

        print(
            "ASSESSMENT COMPLETED SUCCESSFULLY"
        )

        return result

    except HTTPException:
        raise

    except Exception as error:
        print(
            "ASSESSMENT PROCESSING ERROR:",
            str(error),
        )

        import traceback
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                "internal_error",
                "An unexpected error occurred while processing the assessment.",
            ),
        )