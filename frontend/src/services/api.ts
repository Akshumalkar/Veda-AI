import axios from 'axios';
import type { AssessmentResult } from '../types/assessment';

const API_URL =
  import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export interface ProcessAssessmentParams {
  questionFile: File;
  answerFiles: File[];
  studentNames: string[];
}

export async function processAssessment({
  questionFile,
  answerFiles,
  studentNames,
}: ProcessAssessmentParams): Promise<AssessmentResult> {
  const formData = new FormData();

  formData.append('question_paper', questionFile);

  answerFiles.forEach((file) => {
    formData.append('answer_sheets', file);
  });

  formData.append(
    'student_names',
    JSON.stringify(studentNames)
  );

  const response = await axios.post<AssessmentResult>(
    `${API_URL}/api/process`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 300000,
    }
  );

  return response.data;
}

export function getApiUrl(): string {
  return API_URL;
}