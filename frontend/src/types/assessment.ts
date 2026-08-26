// ============================================================
// VEDA AI ASSESSMENT - ASSESSMENT TYPES
// ============================================================

/* ============================================================
   REGION / BOUNDING BOX
============================================================ */

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface Region {
  page: number;
  bbox: BoundingBox;

  label?: string;
  confidence?: number;

  // Optional alternative fields that may come from AI extraction
  text?: string;
}


/* ============================================================
   ANSWER PAGE
============================================================ */

export interface AnswerPage {
  page: number;
  image: string;
}


/* ============================================================
   QUESTION
============================================================ */

export interface AssessmentQuestion {
  question_id: string;
  number: string;
  text: string;

  max_marks?: number;
  marks?: number;

  type?: string;
  section?: string;

  parent_question_id?: string | null;
}


/* ============================================================
   STUDENT ANSWER
============================================================ */

export interface StudentAnswer {
  answer_id?: string;

  question_id?: string;

  question_number?: string;

  text?: string;

  answer?: string;

  page?: number;

  regions?: Region[];

  confidence?: number;
}


/* ============================================================
   GRADING
============================================================ */

export interface GradingResult {
  score: number;

  max_score: number;

  feedback: string;
}


/* ============================================================
   QUESTION ↔ ANSWER MATCH
============================================================ */

export interface AssessmentMatch {
  question_id: string;

  status:
    | 'answered'
    | 'unanswered'
    | 'parent'
    | string;

  max_marks?: number;

  question: AssessmentQuestion;

  answer?: StudentAnswer | null;

  grading?: GradingResult;

  confidence?: number;

  match_type?: string;
}


/* ============================================================
   UNMATCHED ANSWER
============================================================ */

export interface UnmatchedAnswer {
  answer_id?: string;

  question_number?: string;

  text?: string;

  answer?: string;

  page?: number;

  regions?: Region[];
}


/* ============================================================
   ASSESSMENT SUMMARY
============================================================ */

export interface AssessmentSummary {
  total_questions: number;

  answered: number;

  unanswered: number;

  unmatched_answers: number;

  total_score: number;

  max_score: number;

  percentage?: number;

  grade?: string;
}


/* ============================================================
   STUDENT EVALUATION
============================================================ */

export interface StudentEvaluation {
  student_id: string;

  student_name: string;

  roll_no?: string;

  questions: AssessmentQuestion[];

  answers: StudentAnswer[];

  matches: AssessmentMatch[];

  unmatched_answers: UnmatchedAnswer[];

  answer_pages: AnswerPage[];

  total_score: number;

  max_score: number;

  percentage: number;

  grade: string;

  summary: AssessmentSummary;

  message?: string;
}


/* ============================================================
   GRADE DISTRIBUTION
============================================================ */

export interface GradeDistribution {
  A: number;

  B: number;

  C: number;

  D: number;
}


/* ============================================================
   BATCH SUMMARY
============================================================ */

export interface BatchSummary {
  total_students: number;

  evaluated_students?: number;

  total_questions?: number;

  total_score?: number;

  max_score: number;

  average_score?: number;

  average_percentage?: number;

  median_score: number;

  top_score?: number;

  lowest_score?: number;

  top_percentage?: number;

  lowest_percentage?: number;

  grade_distribution: GradeDistribution;
}


/* ============================================================
   ASSESSMENT RESULT
============================================================ */

export interface AssessmentResult {
  success: boolean;

  student_name?: string;

  roll_no?: string;

  questions: AssessmentQuestion[];

  answers: StudentAnswer[];

  matches: AssessmentMatch[];

  unmatched_answers: UnmatchedAnswer[];

  answer_pages: AnswerPage[];

  total_score: number;

  max_score: number;

  percentage: number;

  grade: string;

  summary: AssessmentSummary;

  message?: string;

  /* ----------------------------------------------------------
     Batch result support
  ---------------------------------------------------------- */

  students?: StudentEvaluation[];

  batch_summary?: BatchSummary;
}


/* ============================================================
   API ERROR
============================================================ */

export interface AssessmentApiError {
  success: false;

  error: {
    type: string;

    message: string;
  };
}


/* ============================================================
   API RESPONSE
============================================================ */

export type AssessmentApiResponse =
  | AssessmentResult
  | AssessmentApiError;