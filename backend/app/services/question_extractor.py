import base64
import json
import re
from time import sleep
from google.genai import types
from app.services.gemini_client import client
from app.utils.pdf import pdf_to_images

QUESTION_PROMPT = """
You are an AI system that extracts questions from examination papers.

Extract EVERY question from the provided question paper.

STRICT RULES:
1. Preserve original question numbering exactly.
2. Preserve printed order.
3. Treat sub-parts as separate questions (e.g. 11(a) and 11(b) must be separate entries).
4. Extract the complete visible question text.
5. Do not invent questions.
6. Ignore general instructions, student details, signatures.
7. Identify the page number for every question.
8. Return a bounding box for every question in NORMALIZED coordinates (0 to 1000).
9. Extract max_marks for each question (e.g., "(5 marks)", "[3]", "5M"). Default to 5 if not specified.

Return ONLY valid JSON:
{
  "questions": [
    {
      "id": "q1",
      "number": "1",
      "text": "Question text",
      "page": 1,
      "max_marks": 5,
      "bbox": {
        "x": 100,
        "y": 200,
        "width": 700,
        "height": 120
      }
    }
  ]
}
"""

def clean_json_text(text: str) -> str:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()
    return text

def extract_questions(file_bytes: bytes, content_type: str):
    contents = [QUESTION_PROMPT]

    if content_type == "application/pdf":
        pages = pdf_to_images(file_bytes)
        for page in pages:
            image_bytes = base64.b64decode(page["image"])
            contents.append(f"This is page {page['page']} of the question paper.")
            contents.append(types.Part.from_bytes(data=image_bytes, mime_type="image/png"))
    else:
        contents.append(types.Part.from_bytes(data=file_bytes, mime_type=content_type or "image/jpeg"))

    last_error = None

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0
                )
            )

            raw = clean_json_text(response.text)
            return json.loads(raw)

        except Exception as error:
            last_error = error
            error_message = str(error)

            print(
                f"Gemini question extraction attempt "
                f"{attempt + 1}/3 failed: {error}"
            )

            # IMPORTANT: Do not retry quota/rate-limit errors
            if (
                "429" in error_message
                or "RESOURCE_EXHAUSTED" in error_message
            ):
                print(
                    "Gemini quota/rate limit reached. "
                    "Stopping retries immediately."
                )
                raise error

            # Retry only other temporary errors
            if attempt < 2:
                sleep((attempt + 1) * 3)

    raise last_error