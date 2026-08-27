import type {
  AssessmentResult,
  StudentEvaluation,
} from '../types/assessment';

export type AssessmentHistoryItem = {
  id: string;
  createdAt: string;
  schoolId: string;
  schoolName: string;
  result: AssessmentResult;
};

const STORAGE_KEY = 'veda_assessment_history';

export function getAssessmentHistory(): AssessmentHistoryItem[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);

    if (!stored) {
      return [];
    }

    return JSON.parse(stored);
  } catch (error) {
    console.error('Failed to load assessment history:', error);
    return [];
  }
}

export function saveAssessmentResult(
  result: AssessmentResult,
  schoolId: string,
  schoolName: string
): AssessmentHistoryItem {
  const history = getAssessmentHistory();

  const item: AssessmentHistoryItem = {
    id: `assessment-${Date.now()}`,
    createdAt: new Date().toISOString(),
    schoolId,
    schoolName,
    result,
  };

  const updated = [item, ...history];

  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify(updated)
  );

  return item;
}

export function getSchoolAssessmentHistory(
  schoolId: string
): AssessmentHistoryItem[] {
  return getAssessmentHistory().filter(
    (item) => item.schoolId === schoolId
  );
}

export function getAllEvaluatedStudents(
  schoolId: string
): StudentEvaluation[] {
  const history = getSchoolAssessmentHistory(schoolId);

  const students: StudentEvaluation[] = [];

  history.forEach((item) => {
    if (
      item.result.students &&
      item.result.students.length > 0
    ) {
      students.push(...item.result.students);
    }
  });

  return students;
}

export function clearSchoolAssessmentHistory(
  schoolId: string
) {
  const history = getAssessmentHistory();

  const filtered = history.filter(
    (item) => item.schoolId !== schoolId
  );

  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify(filtered)
  );
}