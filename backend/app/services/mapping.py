import re
from typing import Any, Dict, List, Set


# =========================================================
# QUESTION NUMBER NORMALIZATION
# =========================================================

ROMAN_TO_LETTER = {
    "i": "a",
    "ii": "b",
    "iii": "c",
    "iv": "d",
    "v": "e",
    "vi": "f",
    "vii": "g",
    "viii": "h",
    "ix": "i",
    "x": "j",
}


def normalize_question_number(value: Any) -> str:
    """
    Normalize question numbers into a consistent format.

    Examples:

        Q1       -> 1
        Q1.      -> 1
        1        -> 1
        Question 1 -> 1

        Q1(a)    -> 1(a)
        1(a)     -> 1(a)
        1a       -> 1(a)
        1.a      -> 1(a)
        1-a      -> 1(a)
        1[a]     -> 1(a)

        1(i)     -> 1(a)
        1(ii)    -> 1(b)

        1.1      -> 1(a)
        1.2      -> 1(b)
    """

    if value is None:
        return ""

    value = str(value).strip().lower()

    if not value:
        return ""

    # Remove common prefixes.
    value = re.sub(
        r"^(question|questions|ques|que|q|answer|ans)"
        r"\s*[\.:#-]?\s*",
        "",
        value,
    )

    # Remove spaces.
    value = re.sub(r"\s+", "", value)

    # Remove trailing punctuation.
    value = value.rstrip(".:")

    # -----------------------------------------------------
    # NUMBER + ROMAN
    # -----------------------------------------------------

    match = re.fullmatch(
        r"(\d+)[\(\[\.\-_]?([ivx]+)[\)\]]?",
        value,
    )

    if match:
        number = match.group(1)
        roman = match.group(2)

        letter = ROMAN_TO_LETTER.get(roman)

        if letter:
            return f"{number}({letter})"

    # -----------------------------------------------------
    # NUMBER + LETTER
    # -----------------------------------------------------

    match = re.fullmatch(
        r"(\d+)[\(\[\.\-_]?([a-z])[\)\]]?",
        value,
    )

    if match:
        number = match.group(1)
        letter = match.group(2)

        return f"{number}({letter})"

    # -----------------------------------------------------
    # NUMBER.SUBNUMBER
    # -----------------------------------------------------

    match = re.fullmatch(
        r"(\d+)\.(\d+)",
        value,
    )

    if match:
        number = match.group(1)
        sub_number = int(match.group(2))

        if 1 <= sub_number <= 26:
            letter = chr(
                ord("a") + sub_number - 1
            )

            return f"{number}({letter})"

    # -----------------------------------------------------
    # PLAIN NUMBER
    # -----------------------------------------------------

    match = re.fullmatch(
        r"\d+",
        value,
    )

    if match:
        return value

    return value


# =========================================================
# QUESTION NUMBER VARIANTS
# =========================================================

def get_question_number_variants(value: Any) -> Set[str]:

    normalized = normalize_question_number(value)

    if not normalized:
        return set()

    variants = {normalized}

    # -----------------------------------------------------
    # Parent question
    # 1 -> 1
    # -----------------------------------------------------

    if re.fullmatch(r"\d+", normalized):
        variants.add(normalized)

    # -----------------------------------------------------
    # Sub-question
    # 1(a)
    # -----------------------------------------------------

    match = re.fullmatch(
        r"(\d+)\(([a-z])\)",
        normalized,
    )

    if match:

        number = match.group(1)
        letter = match.group(2)

        variants.add(f"{number}{letter}")
        variants.add(f"{number}.{letter}")
        variants.add(f"{number}-{letter}")
        variants.add(f"{number}[{letter}]")

    return variants


# =========================================================
# QUESTION NUMBER MATCH
# =========================================================

def question_number_matches(
    question_number: Any,
    answer_number: Any,
) -> bool:

    q = normalize_question_number(
        question_number
    )

    a = normalize_question_number(
        answer_number
    )

    if not q or not a:
        return False

    return q == a


# =========================================================
# PARENT QUESTION DETECTION
# =========================================================

def is_parent_question(
    question: Dict[str, Any]
) -> bool:

    text = str(
        question.get("text", "")
    ).strip().lower()

    if not text:
        return False

    parent_phrases = [
        "answer the following",
        "answer the following questions",
        "following questions",
        "answer any",
        "attempt any",
        "attempt the following",
        "section a",
        "section b",
        "section c",
        "section d",
        "choose the correct",
        "read the passage",
    ]

    # Long questions are probably actual questions,
    # not section instructions.
    if len(text) > 180:
        return False

    return any(
        phrase in text
        for phrase in parent_phrases
    )


# =========================================================
# TEXT NORMALIZATION
# =========================================================

def normalize_text(text: Any) -> str:

    if text is None:
        return ""

    text = str(text).lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# =========================================================
# KEYWORD EXTRACTION
# =========================================================

def get_keywords(text: str) -> Set[str]:

    text = normalize_text(text)

    if not text:
        return set()

    stopwords = {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "and",
        "or",
        "but",
        "if",
        "then",
        "than",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "from",
        "by",
        "as",
        "into",
        "about",
        "what",
        "which",
        "who",
        "when",
        "where",
        "why",
        "how",
        "explain",
        "describe",
        "define",
        "state",
        "write",
        "give",
        "discuss",
        "answer",
        "question",
        "following",
        "student",
        "marks",
    }

    words = re.findall(
        r"[a-zA-Z0-9]{3,}",
        text,
    )

    return {
        word
        for word in words
        if word not in stopwords
    }


# =========================================================
# KEYWORD SIMILARITY
# =========================================================

def semantic_keyword_similarity(
    text1: str,
    text2: str,
) -> float:

    kw1 = get_keywords(text1)
    kw2 = get_keywords(text2)

    if not kw1 or not kw2:
        return 0.0

    intersection = kw1.intersection(kw2)

    if not intersection:
        return 0.0

    union = kw1.union(kw2)

    jaccard = (
        len(intersection) /
        len(union)
    )

    smaller_coverage = (
        len(intersection) /
        min(len(kw1), len(kw2))
    )

    return (
        jaccard * 0.4
        +
        smaller_coverage * 0.6
    )


# =========================================================
# MAIN MAPPING FUNCTION
# =========================================================

def map_questions_to_answers(
    questions: List[Dict[str, Any]],
    answers: List[Dict[str, Any]],
) -> Dict[str, Any]:

    matches: List[Dict[str, Any]] = []

    matched_answer_ids: Set[Any] = set()

    # =====================================================
    # BUILD NORMALIZED ANSWER LOOKUP
    # =====================================================

    answer_lookup: Dict[
        str,
        List[Dict[str, Any]]
    ] = {}

    for answer in answers:

        answer_id = answer.get(
            "answer_id"
        )

        answer_number = answer.get(
            "question_number"
        )

        normalized = normalize_question_number(
            answer_number
        )

        print(
            f"ANSWER: {answer_id} | "
            f"RAW NUMBER: {answer_number} | "
            f"NORMALIZED: {normalized}"
        )

        if normalized:

            answer_lookup.setdefault(
                normalized,
                [],
            ).append(answer)

    # =====================================================
    # PASS 1
    # EXACT QUESTION NUMBER
    # =====================================================

    for question in questions:

        question_id = question.get(
            "id"
        )

        question_number = question.get(
            "number",
            ""
        )

        max_marks = question.get(
            "max_marks",
            5,
        )

        normalized_question = (
            normalize_question_number(
                question_number
            )
        )

        print(
            f"QUESTION: {question_id} | "
            f"RAW NUMBER: {question_number} | "
            f"NORMALIZED: {normalized_question}"
        )

        # -------------------------------------------------
        # Parent / section question
        # -------------------------------------------------

        if is_parent_question(question):

            matches.append({
                "question_id": question_id,
                "question_number": question_number,
                "answer_id": None,
                "status": "parent",
                "question": question,
                "answer": None,
                "max_marks": max_marks,
            })

            continue

        chosen_answer = None

        # -------------------------------------------------
        # Exact normalized lookup
        # -------------------------------------------------

        possible_answers = answer_lookup.get(
            normalized_question,
            [],
        )

        for answer in possible_answers:

            answer_id = answer.get(
                "answer_id"
            )

            if answer_id not in matched_answer_ids:

                chosen_answer = answer
                break

        # -------------------------------------------------
        # Create result
        # -------------------------------------------------

        if chosen_answer:

            answer_id = chosen_answer.get(
                "answer_id"
            )

            matched_answer_ids.add(
                answer_id
            )

            matches.append({
                "question_id": question_id,
                "question_number": question_number,
                "answer_id": answer_id,
                "status": "answered",
                "question": question,
                "answer": chosen_answer,
                "max_marks": max_marks,
            })

            print(
                f"MAPPED: {question_number} "
                f"-> {answer_id}"
            )

        else:

            matches.append({
                "question_id": question_id,
                "question_number": question_number,
                "answer_id": None,
                "status": "unanswered",
                "question": question,
                "answer": None,
                "max_marks": max_marks,
            })

            print(
                f"UNANSWERED: {question_number}"
            )

    # =====================================================
    # PASS 2
    # SEMANTIC FALLBACK
    #
    # IMPORTANT:
    # Only use this when the answer itself has NO
    # recognizable question number.
    # =====================================================

    unmatched_answers = [
        answer
        for answer in answers
        if answer.get("answer_id")
        not in matched_answer_ids
    ]

    for match in matches:

        if match["status"] != "unanswered":
            continue

        question = match["question"]

        question_text = question.get(
            "text",
            "",
        )

        best_answer = None
        best_score = 0.0

        for answer in unmatched_answers:

            answer_number = answer.get(
                "question_number"
            )

            # Do NOT semantically remap an answer that
            # explicitly has a different question number.
            if answer_number not in (
                None,
                "",
            ):

                continue

            answer_text = answer.get(
                "text",
                "",
            )

            score = semantic_keyword_similarity(
                question_text,
                answer_text,
            )

            if score > best_score:

                best_score = score
                best_answer = answer

        # High threshold to avoid wrong mappings.
        if (
            best_answer
            and best_score >= 0.60
        ):

            answer_id = best_answer.get(
                "answer_id"
            )

            matched_answer_ids.add(
                answer_id
            )

            match["status"] = "answered"

            match["answer_id"] = (
                answer_id
            )

            match["answer"] = (
                best_answer
            )

            unmatched_answers.remove(
                best_answer
            )

            print(
                f"SEMANTIC MAPPING: "
                f"{match['question_number']} "
                f"-> {answer_id} "
                f"(score={best_score:.2f})"
            )

    # =====================================================
    # REMAINING UNMATCHED ANSWERS
    # =====================================================

    remaining_answers = []

    for answer in answers:

        answer_id = answer.get(
            "answer_id"
        )

        if answer_id not in matched_answer_ids:

            remaining_answers.append({
                "answer_id": answer_id,
                "question_number": answer.get(
                    "question_number"
                ),
                "text": answer.get(
                    "text",
                    "",
                ),
                "regions": answer.get(
                    "regions",
                    [],
                ),
                "status": "unmatched",
                "answer": answer,
            })

    # =====================================================
    # DEBUG OUTPUT
    # =====================================================

    print(
        "\n========== QUESTION MAPPING =========="
    )

    for match in matches:

        print(
            f"Question: "
            f"{match.get('question_number')} | "
            f"Answer: "
            f"{match.get('answer_id')} | "
            f"Status: "
            f"{match.get('status')}"
        )

    print(
        f"Total questions: {len(questions)}"
    )

    print(
        f"Total answers: {len(answers)}"
    )

    print(
        f"Matched answers: "
        f"{len(matched_answer_ids)}"
    )

    print(
        f"Unmatched answers: "
        f"{len(remaining_answers)}"
    )

    print(
        "======================================\n"
    )

    return {
        "matches": matches,
        "unmatched_answers": remaining_answers,
    }