import base64
import json
import re
from time import sleep
from typing import Any, Dict, List

from app.services.groq_client import client
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


def image_to_data_url(
    image_bytes: bytes,
    mime_type: str = "image/png",
) -> str:

    encoded = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"


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
                "question_id": match.get(
                    "question_id"
                ),

                "question_number": match.get(
                    "question_number"
                ),

                "question_text": question.get(
                    "text",
                    "",
                ),

                "max_marks": question.get(
                    "max_marks",
                    5,
                ),

                "status": match.get(
                    "status"
                ),

                "answer_text": (
                    answer.get("text", "")
                    if answer
                    else ""
                ),
            }
        )

    pairs_json = json.dumps(
        matches_for_grading,
        indent=2,
        ensure_ascii=False,
    )

    # ---------------------------------------------------------
    # Groq messages
    # ---------------------------------------------------------

    message_content = [
        {
            "type": "text",
            "text": GRADING_PROMPT,
        },
        {
            "type": "text",
            "text": (
                "Matched pairs:\n"
                + pairs_json
                + "\n\nVisual references follow:\n"
            ),
        },
    ]

    # ---------------------------------------------------------
    # Question paper images
    # ---------------------------------------------------------

    if question_content_type == "application/pdf":

        question_pages = pdf_to_images(
            question_bytes
        )

        for page in question_pages:

            message_content.append(
                {
                    "type": "text",
                    "text": (
                        "Question paper page "
                        + str(page["page"])
                        + ":"
                    ),
                }
            )

            image_bytes = base64.b64decode(
                page["image"]
            )

            message_content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_to_data_url(
                            image_bytes,
                            "image/png",
                        )
                    },
                }
            )

    else:

        message_content.append(
            {
                "type": "text",
                "text": "Question paper:",
            }
        )

        message_content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": image_to_data_url(
                        question_bytes,
                        question_content_type
                        or "image/jpeg",
                    )
                },
            }
        )

    # ---------------------------------------------------------
    # Student answer sheet images
    # ---------------------------------------------------------

    if answer_content_type == "application/pdf":

        answer_pages = pdf_to_images(
            answer_bytes
        )

        for page in answer_pages:

            message_content.append(
                {
                    "type": "text",
                    "text": (
                        "Answer sheet page "
                        + str(page["page"])
                        + ":"
                    ),
                }
            )

            image_bytes = base64.b64decode(
                page["image"]
            )

            message_content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_to_data_url(
                            image_bytes,
                            "image/png",
                        )
                    },
                }
            )

    else:

        message_content.append(
            {
                "type": "text",
                "text": "Answer sheet:",
            }
        )

        message_content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": image_to_data_url(
                        answer_bytes,
                        answer_content_type
                        or "image/jpeg",
                    )
                },
            }
        )

    # ---------------------------------------------------------
    # Groq grading
    # ---------------------------------------------------------

    last_error = None

    for attempt in range(3):

        try:

            print(
                f"Groq grading attempt "
                f"{attempt + 1}/3..."
            )

            response = client.chat.completions.create(
                model="qwen/qwen3.6-27b",

                messages=[
                    {
                        "role": "user",
                        "content": message_content,
                    }
                ],

                temperature=0.1,

                response_format={
                    "type": "json_object"
                },
            )

            raw = clean_json_text(
                response.choices[0]
                .message
                .content
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
                    "Groq returned an invalid "
                    "grades format."
                )

            print(
                f"Groq grading completed: "
                f"{len(grades)} grades returned."
            )

            return grades

        except Exception as error:

            last_error = error

            error_message = str(error)

            print(
                f"Groq grading attempt "
                f"{attempt + 1}/3 failed: "
                f"{error_message}"
            )

            # -------------------------------------------------
            # NEVER retry rate-limit errors
            # -------------------------------------------------

            if (
                "429" in error_message
                or "rate_limit"
                in error_message.lower()
                or "rate limit"
                in error_message.lower()
            ):

                print(
                    "Groq rate limit reached. "
                    "Stopping grading retries "
                    "immediately."
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
    # Never return fake/full marks.
    # ---------------------------------------------------------

    print(
        "Groq grading failed after "
        "all retries."
    )

    if last_error:
        raise last_error

    raise RuntimeError(
        "Groq grading failed without "
        "an available error."
    )