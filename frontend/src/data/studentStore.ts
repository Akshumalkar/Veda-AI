import type { SchoolProfile } from '../types/user';

export type Student = {
  id: string;
  schoolId: string;

  name: string;
  rollNo: string;

  className: string;
  section: string;

  attendance: string;

  latestScore: number;
  maxScore: number;

  grade: 'A' | 'B' | 'C' | 'D' | '-';

  learningGap: string;
};

const STORAGE_KEY = 'veda_school_students';

type StudentDatabase = Record<string, Student[]>;

/* =========================================================
   GET COMPLETE DATABASE
========================================================= */

function getDatabase(): StudentDatabase {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);

    if (!stored) {
      return {};
    }

    return JSON.parse(stored);
  } catch {
    return {};
  }
}

/* =========================================================
   SAVE COMPLETE DATABASE
========================================================= */

function saveDatabase(data: StudentDatabase) {
  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify(data)
  );
}

/* =========================================================
   GET STUDENTS FOR SCHOOL
========================================================= */

export function getStudentsBySchool(
  schoolId: string
): Student[] {

  const database = getDatabase();

  return database[schoolId] || [];
}

/* =========================================================
   ADD STUDENT TO SCHOOL
========================================================= */

export function addStudent(
  student: Student
) {

  const database = getDatabase();

  const schoolStudents =
    database[student.schoolId] || [];

  database[student.schoolId] = [
    student,
    ...schoolStudents
  ];

  saveDatabase(database);

  return database[student.schoolId];
}

/* =========================================================
   UPDATE STUDENT
========================================================= */

export function updateStudent(
  student: Student
) {

  const database = getDatabase();

  const students =
    database[student.schoolId] || [];

  database[student.schoolId] =
    students.map((item) =>
      item.id === student.id
        ? student
        : item
    );

  saveDatabase(database);

  return database[student.schoolId];
}

/* =========================================================
   DELETE STUDENT
========================================================= */

export function deleteStudent(
  schoolId: string,
  studentId: string
) {

  const database = getDatabase();

  database[schoolId] =
    (database[schoolId] || []).filter(
      (student) =>
        student.id !== studentId
    );

  saveDatabase(database);

  return database[schoolId];
}

/* =========================================================
   CLEAR SCHOOL STUDENTS
========================================================= */

export function clearSchoolStudents(
  schoolId: string
) {

  const database = getDatabase();

  delete database[schoolId];

  saveDatabase(database);
}

/* =========================================================
   CREATE STUDENT
========================================================= */

export function createStudent(
  school: SchoolProfile,
  data: {
    name: string;
    rollNo: string;
    section: string;
  }
): Student {

  return {
    id:
      'student-' +
      Date.now() +
      '-' +
      Math.random()
        .toString(36)
        .substring(2, 8),

    schoolId: school.id,

    name: data.name,

    rollNo: data.rollNo,

    className: 'Class 10',

    section: data.section,

    attendance: '-',

    latestScore: 0,

    maxScore: 0,

    grade: '-',

    learningGap:
      'No assessment data available yet'
  };
}