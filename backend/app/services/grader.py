import base64
import json
import re
from time import sleep
from typing import Any, Dict, List

from google.genai import types

from app.services.gemini_client import client
from app.utils.pdf import pdf_to_images


GRADING_PROMPT = """
You are an expert teacher grading a student's handwritten examination answer sheet.

You will be given a JSON list of matched question-answer pairs
(question text, answer text, max_marks), plus the question paper images
and answer sheet images for visual context.

For EACH item:

- status=answered:
  Assign a score from 0 to max_marks.
  Write 1-2 sentences of constructive feedback.

- status=unanswered:
  score=0
  feedback="Not attempted."

- status=parent:
  score=0
  feedback=""

SCORING RULES:

- Full marks: complete and accurate answer.
- Partial marks: partially correct or incomplete answer.
- 0: incorrect, irrelevant, or missing answer.
- Never give marks merely because an answer exists.
- Evaluate the actual content of the student's answer.
- Do not invent information that is not present in the answer.

Return ONLY valid JSON:

{
  "grades": [
    {
      "question_id": "q1",
      "score": 4,
      "max_score": 5,
      "feedback": "Good explanation. Accurate scientific terms used."
    }
  ]
}
"""


def clean_json_text(text: str) -> str:
    text = text.strip()

    match = re.search(
        r"```(?:json)?\s*([\s\S]*?)\s*```",
        text,
    )

    if match:
        return match.group(1).strip()

    return text


def grade_answers(
    matches: List[Dict[str, Any]],
    question_bytes: bytes,
    question_content_type: str,
    answer_bytes: bytes,
    answer_content_type: str,
) -> List[Dict[str, Any]]:

    matches_for_grading = []

    for match in matches:
        question = match.get("question") or {}
        answer = match.get("answer") or {}

        matches_for_grading.append(
            {
                "question_id": match.get("question_id"),
                "question_number": match.get("question_number"),
                "question_text": question.get("text", ""),
                "max_marks": question.get("max_marks", 5),
                "status": match.get("status"),
                "answer_text": answer.get("text", "") if answer else "",
            }
        )

    pairs_json = json.dumps(
        matches_for_grading,
        indent=2,
        ensure_ascii=False,
    )

    contents: List[Any] = [
        GRADING_PROMPT,
        "Matched pairs:\n"
        + pairs_json
        + "\n\nVisual references follow:\n",
    ]

    # ---------------------------------------------------------
    # Question paper images
    # ---------------------------------------------------------

    if question_content_type == "application/pdf":

        question_pages = pdf_to_images(
            question_bytes
        )

        for page in question_pages:
            contents.append(
                "Question paper page "
                + str(page["page"])
                + ":"
            )

            contents.append(
                types.Part.from_bytes(
                    data=base64.b64decode(
                        page["image"]
                    ),
                    mime_type="image/png",
                )
            )

    else:

        contents.append(
            "Question paper:"
        )

        contents.append(
            types.Part.from_bytes(
                data=question_bytes,
                mime_type=(
                    question_content_type
                    or "image/jpeg"
                ),
            )
        )

    # ---------------------------------------------------------
    # Student answer sheet images
    # ---------------------------------------------------------

    if answer_content_type == "application/pdf":

        answer_pages = pdf_to_images(
            answer_bytes
        )

        for page in answer_pages:
            contents.append(
                "Answer sheet page "
                + str(page["page"])
                + ":"
            )

            contents.append(
                types.Part.from_bytes(
                    data=base64.b64decode(
                        page["image"]
                    ),
                    mime_type="image/png",
                )
            )

    else:

        contents.append(
            "Answer sheet:"
        )

        contents.append(
            types.Part.from_bytes(
                data=answer_bytes,
                mime_type=(
                    answer_content_type
                    or "image/jpeg"
                ),
            )
        )

    # ---------------------------------------------------------
    # Gemini grading
    # ---------------------------------------------------------

    last_error = None

    for attempt in range(3):

        try:

            print(
                f"Gemini grading attempt "
                f"{attempt + 1}/3..."
            )

            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )

            raw = clean_json_text(
                response.text
            )

            result = json.loads(raw)

            grades = result.get(
                "grades",
                []
            )

            if not isinstance(
                grades,
                list,
            ):
                raise ValueError(
                    "Gemini returned an invalid grades format."
                )

            print(
                f"Gemini grading completed: "
                f"{len(grades)} grades returned."
            )

            return grades

        except Exception as error:

            last_error = error

            error_message = str(error)

            print(
                f"Gemini grading attempt "
                f"{attempt + 1}/3 failed: "
                f"{error_message}"
            )

            # -------------------------------------------------
            # NEVER retry quota/rate-limit errors
            # -------------------------------------------------

            if (
                "429" in error_message
                or "RESOURCE_EXHAUSTED" in error_message
            ):

                print(
                    "Gemini quota/rate limit reached. "
                    "Stopping grading retries immediately."
                )

                raise error

            # -------------------------------------------------
            # Retry other temporary errors
            # -------------------------------------------------

            if attempt < 2:

                wait_seconds = (
                    attempt + 1
                ) * 3

                print(
                    f"Retrying grading in "
                    f"{wait_seconds} seconds..."
                )

                sleep(
                    wait_seconds
                )

    # ---------------------------------------------------------
    # IMPORTANT:
    # Never return fake/full marks.
    # Propagate the real error.
    # ---------------------------------------------------------

    print(
        "Gemini grading failed after all retries."
    )

    if last_error:
        raise last_error

    raise RuntimeError(
        "Gemini grading failed without an available error."
    )