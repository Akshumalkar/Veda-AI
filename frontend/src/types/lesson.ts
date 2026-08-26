export type LessonPhase = {
  phase: 'Engage' | 'Explore' | 'Explain' | 'Elaborate' | 'Evaluate';
  durationMinutes: number;
  activity: string;
  teacherRole: string;
  studentRole: string;
};

export type LessonPlan = {
  id: string;
  chapter: string;
  subject: string;
  grade: string;
  duration: string;
  learningObjectives: string[];
  prerequisites: string[];
  boardQuestions: string[];
  phases: LessonPhase[];
  homework: string;
};

export type WorksheetQuestion = {
  id: string;
  type: 'MCQ' | 'Short Answer' | 'Numerical' | 'Derivation';
  marks: number;
  question: string;
  options?: string[];
  solution: string;
  markingGuide: string;
};

export type Worksheet = {
  id: string;
  title: string;
  chapter: string;
  totalMarks: number;
  timeAllowed: string;
  questions: WorksheetQuestion[];
};

export type RubricCriterion = {
  id: string;
  criterion: string;
  maxMarks: number;
  excellent: string;
  proficient: string;
  developing: string;
};

export type RubricTemplate = {
  id: string;
  title: string;
  chapter: string;
  totalMarks: number;
  criteria: RubricCriterion[];
};
