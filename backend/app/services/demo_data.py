from typing import Any, Dict, List

def get_demo_assessment_result(total_pages: int = 1, student_name: str = "Aarav Sharma", roll_no: str = "10A-01", score_factor: float = 1.0) -> Dict[str, Any]:
    questions = [
        {
            "id": "q1",
            "number": "1",
            "text": "What is Artificial Intelligence (AI)? State two real-world applications.",
            "page": 1,
            "max_marks": 5,
            "bbox": {"x": 60, "y": 80, "width": 880, "height": 70}
        },
        {
            "id": "q2",
            "number": "2",
            "text": "Define Machine Learning and differentiate between Supervised and Unsupervised Learning.",
            "page": 1,
            "max_marks": 5,
            "bbox": {"x": 60, "y": 170, "width": 880, "height": 80}
        },
        {
            "id": "q3",
            "number": "3",
            "text": "Explain the architecture and basic functioning of a Neural Network with an example.",
            "page": 1,
            "max_marks": 5,
            "bbox": {"x": 60, "y": 270, "width": 880, "height": 80}
        },
        {
            "id": "q4",
            "number": "4",
            "text": "What is Overfitting in machine learning models and how can it be reduced?",
            "page": 1,
            "max_marks": 5,
            "bbox": {"x": 60, "y": 370, "width": 880, "height": 80}
        },
        {
            "id": "q5a",
            "number": "5(a)",
            "text": "Differentiate between Precision and Recall with mathematical formulas.",
            "page": 1,
            "max_marks": 4,
            "bbox": {"x": 60, "y": 470, "width": 880, "height": 80}
        },
        {
            "id": "q6",
            "number": "6",
            "text": "Explain Natural Language Processing (NLP) and Computer Vision with use cases.",
            "page": 1,
            "max_marks": 5,
            "bbox": {"x": 60, "y": 570, "width": 880, "height": 80}
        }
    ]

    # Scores based on student variation
    q1_score = 5 if score_factor > 0.7 else 4
    q2_score = 0  # Question 2 is unanswered by student
    q3_score = 5 if score_factor > 0.8 else (4 if score_factor > 0.6 else 3)
    q4_score = 5 if score_factor > 0.75 else (3 if score_factor > 0.5 else 2)
    q5a_score = 4 if score_factor > 0.7 else (3 if score_factor > 0.5 else 2)
    q6_score = 5 if score_factor > 0.85 else 4

    answers = [
        {
            "answer_id": "a3",
            "question_number": "3",
            "text": "A neural network consists of input, hidden and output layers. Each neuron applies weights and an activation function. For example, a network can classify handwritten digits.",
            "regions": [{"page": 1, "bbox": {"x": 60, "y": 140, "width": 880, "height": 115}}]
        },
        {
            "answer_id": "a1",
            "question_number": "1",
            "text": "Artificial Intelligence is the ability of machines to perform tasks that normally require human intelligence. Applications include recommendation systems and medical diagnosis.",
            "regions": [{"page": 1, "bbox": {"x": 60, "y": 280, "width": 880, "height": 115}}]
        },
        {
            "answer_id": "a5a",
            "question_number": "5(a)",
            "text": "Precision measures how many predicted positive cases are actually positive. Recall measures how many actual positive cases were correctly identified.",
            "regions": [{"page": 1, "bbox": {"x": 60, "y": 425, "width": 880, "height": 105}}]
        },
        {
            "answer_id": "a4",
            "question_number": "4",
            "text": "Overfitting happens when a model learns training data too closely and performs poorly on new data. It can be reduced using regularization and dropout.",
            "regions": [{"page": 1, "bbox": {"x": 60, "y": 555, "width": 880, "height": 105}}]
        },
        {
            "answer_id": "a6",
            "question_number": "6",
            "text": "NLP helps computers understand human language. Computer Vision enables machines to interpret images and videos.",
            "regions": [{"page": 1, "bbox": {"x": 60, "y": 690, "width": 880, "height": 105}}]
        }
    ]

    matches = [
        {
            "question_id": "q1",
            "question_number": "1",
            "answer_id": "a1",
            "status": "answered",
            "question": questions[0],
            "answer": answers[1],
            "max_marks": 5,
            "grading": {
                "score": q1_score,
                "max_score": 5,
                "feedback": "Excellent definition of AI with valid real-world applications (recommendation engines & diagnosis)."
            }
        },
        {
            "question_id": "q2",
            "question_number": "2",
            "answer_id": None,
            "status": "unanswered",
            "question": questions[1],
            "answer": None,
            "max_marks": 5,
            "grading": {
                "score": 0,
                "max_score": 5,
                "feedback": "Question not attempted on student answer sheet."
            }
        },
        {
            "question_id": "q3",
            "question_number": "3",
            "answer_id": "a3",
            "status": "answered",
            "question": questions[2],
            "answer": answers[0],
            "max_marks": 5,
            "grading": {
                "score": q3_score,
                "max_score": 5,
                "feedback": "Correct structural breakdown: input, hidden, output layers with weights and activation functions."
            }
        },
        {
            "question_id": "q4",
            "question_number": "4",
            "answer_id": "a4",
            "status": "answered",
            "question": questions[3],
            "answer": answers[3],
            "max_marks": 5,
            "grading": {
                "score": q4_score,
                "max_score": 5,
                "feedback": "Accurately defined overfitting and cited standard mitigation strategies (regularization and dropout)."
            }
        },
        {
            "question_id": "q5a",
            "question_number": "5(a)",
            "answer_id": "a5a",
            "status": "answered",
            "question": questions[4],
            "answer": answers[2],
            "max_marks": 4,
            "grading": {
                "score": q5a_score,
                "max_score": 4,
                "feedback": "Clear conceptual distinction between Precision and Recall." if q5a_score == 4 else "Definitions correct, but explicit mathematical formula notations (TP/(TP+FP)) were omitted."
            }
        },
        {
            "question_id": "q6",
            "question_number": "6",
            "answer_id": "a6",
            "status": "answered",
            "question": questions[5],
            "answer": answers[4],
            "max_marks": 5,
            "grading": {
                "score": q6_score,
                "max_score": 5,
                "feedback": "Correct functional explanation of NLP and Computer Vision domain applications."
            }
        }
    ]

    answered_matches = [m for m in matches if m["status"] == "answered"]
    total_score = sum(m["grading"]["score"] for m in matches)
    max_score = sum(m["grading"]["max_score"] for m in matches)
    pct = round((total_score / max_score) * 100, 1) if max_score > 0 else 0
    grade = "A" if pct >= 80 else ("B" if pct >= 65 else ("C" if pct >= 50 else "D"))

    return {
        "student_id": f"std_{roll_no.replace('-', '_').lower()}",
        "student_name": student_name,
        "roll_no": roll_no,
        "success": True,
        "questions": questions,
        "answers": answers,
        "matches": matches,
        "unmatched_answers": [],
        "total_score": total_score,
        "max_score": max_score,
        "percentage": pct,
        "grade": grade,
        "summary": {
            "total_questions": len(questions),
            "answered": len(answered_matches),
            "unanswered": len(questions) - len(answered_matches),
            "unmatched_answers": 0,
            "total_score": total_score,
            "max_score": max_score
        },
        "message": f"Assessment evaluated for {student_name} ({roll_no})"
    }
