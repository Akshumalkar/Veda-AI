import {
  useState,
  useEffect
} from 'react';

import {
  Search,
  Plus,
  FileText,
  Eye,
  GraduationCap,
  Users
} from 'lucide-react';

import type {
  TeacherUser
} from '../types/user';

import {
  getStudentsBySchool,
  addStudent,
  createStudent,
  type Student
} from '../data/studentStore';

import {
  AddStudentModal
} from './Modals';


type ClassroomViewProps = {
  user: TeacherUser;
  assessmentHistory?: any[];
  onEvaluateStudentSheet?: (
    student?: Student
  ) => void;
};


export default function ClassroomView({
  user,
  onEvaluateStudentSheet
}: ClassroomViewProps) {

  // =========================================================
  // STATE
  // =========================================================

  const [students, setStudents] =
    useState<Student[]>([]);

  const [searchQuery, setSearchQuery] =
    useState('');

  const [selectedStudent, setSelectedStudent] =
    useState<Student | null>(null);

  const [isAddStudentOpen, setIsAddStudentOpen] =
    useState(false);


  // =========================================================
  // LOAD STUDENTS WHEN SCHOOL CHANGES
  // =========================================================

  useEffect(() => {

    const schoolStudents =
      getStudentsBySchool(user.school.id);

    setStudents(schoolStudents);

    setSelectedStudent(null);

    setSearchQuery('');

  }, [user.school.id]);


  // =========================================================
  // SEARCH STUDENTS
  // =========================================================

  const filteredStudents =
    students.filter((student) => {

      const query =
        searchQuery.toLowerCase();

      return (
        student.name
          .toLowerCase()
          .includes(query)

        ||

        student.rollNo
          .toLowerCase()
          .includes(query)

        ||

        student.section
          .toLowerCase()
          .includes(query)
      );
    });


  // =========================================================
  // ADD STUDENT
  // =========================================================

  const handleAddNewStudent = (
    newStudent: {
      name: string;
      rollNo: string;
      section: string;
    }
  ) => {

    const student =
      createStudent(
        user.school,
        newStudent
      );

    const updatedStudents =
      addStudent(student);

    setStudents(updatedStudents);

    setIsAddStudentOpen(false);
  };


  // =========================================================
  // HELPERS
  // =========================================================

  const getGradeClass = (
    grade: Student['grade']
  ) => {

    if (grade === 'A') {
      return 'grade-badge-green';
    }

    if (grade === 'B') {
      return 'grade-badge-yellow';
    }

    if (grade === 'C') {
      return 'grade-badge-orange';
    }

    if (grade === 'D') {
      return 'grade-badge-red';
    }

    return '';
  };


  const hasStudents =
    students.length > 0;


  // =========================================================
  // UI
  // =========================================================

  return (

    <div className="classroom-view-wrapper">

      {/* ===================================================
          CLASSROOM HEADER
      =================================================== */}

      <div className="classroom-header-bar">

        <div className="header-left-info">

          <h2>
            My Classroom — {user.subject}
          </h2>

          <span className="school-subhead">

            <GraduationCap size={15} />

            {user.school.name}

            {' ('}
            {user.school.location}
            {')'}

            {' • '}

            Academic Year 2025–2026

          </span>

        </div>


        <div className="header-actions-row">

          <button
            className="primary-action-btn"
            onClick={() =>
              setIsAddStudentOpen(true)
            }
            type="button"
          >

            <Plus size={16} />

            Add Student

          </button>

        </div>

      </div>


      {/* ===================================================
          SCHOOL / STUDENT INFO BAR
      =================================================== */}

      <div className="classroom-controls-bar">

        <div className="section-tabs-group">

          <div className="section-tab-btn active">

            <Users size={15} />

            {students.length}

            {' '}

            Student
            {students.length !== 1 ? 's' : ''}

            {' • '}

            {user.school.name}

          </div>

        </div>


        <div className="classroom-search-box">

          <Search
            size={16}
            className="search-icon"
          />

          <input
            type="text"
            placeholder="Search student by name, roll no or section..."
            value={searchQuery}
            onChange={(e) =>
              setSearchQuery(e.target.value)
            }
          />

        </div>

      </div>


      {/* ===================================================
          EMPTY STATE
      =================================================== */}

      {!hasStudents ? (

        <div className="figma-dash-card student-roster-card">

          <div
            style={{
              padding: '70px 30px',
              textAlign: 'center'
            }}
          >

            <Users
              size={48}
              style={{
                marginBottom: '16px',
                opacity: 0.5
              }}
            />

            <h2>
              No Students Registered Yet
            </h2>

            <p
              style={{
                marginTop: '8px',
                opacity: 0.7
              }}
            >

              {user.school.name}
              {' '}
              currently has no students registered in VEDA.

            </p>

            <button
              className="primary-action-btn"
              style={{
                marginTop: '22px'
              }}
              onClick={() =>
                setIsAddStudentOpen(true)
              }
              type="button"
            >

              <Plus size={16} />

              Register First Student

            </button>

          </div>

        </div>

      ) : (

        /* ===================================================
            STUDENT TABLE
        =================================================== */

        <div className="figma-dash-card student-roster-card">

          <div className="table-responsive-wrap">

            <table className="classroom-table">

              <thead>

                <tr>

                  <th>
                    Roll No
                  </th>

                  <th>
                    Student Name
                  </th>

                  <th>
                    Section
                  </th>

                  <th>
                    Attendance
                  </th>

                  <th>
                    Latest Exam Score
                  </th>

                  <th>
                    Grade
                  </th>

                  <th>
                    Identified Learning Gap
                  </th>

                  <th className="text-right">
                    Actions
                  </th>

                </tr>

              </thead>


              <tbody>

                {filteredStudents.length === 0 ? (

                  <tr>

                    <td
                      colSpan={8}
                      style={{
                        textAlign: 'center',
                        padding: '40px'
                      }}
                    >

                      No students found.

                    </td>

                  </tr>

                ) : (

                  filteredStudents.map((student) => {

                    const gradeClass =
                      getGradeClass(student.grade);

                    const hasAssessment =
                      student.maxScore > 0;


                    return (

                      <tr
                        key={student.id}
                        className="student-row"
                      >

                        {/* Roll Number */}

                        <td className="roll-cell">

                          <strong>
                            {student.rollNo}
                          </strong>

                        </td>


                        {/* Student Name */}

                        <td className="name-cell">

                          <div className="student-avatar-row">

                            <div className="student-mini-avatar">

                              {student.name
                                .charAt(0)
                                .toUpperCase()}

                            </div>

                            <span>
                              {student.name}
                            </span>

                          </div>

                        </td>


                        {/* Section */}

                        <td>

                          {student.section}

                        </td>


                        {/* Attendance */}

                        <td>

                          {student.attendance}

                        </td>


                        {/* Score */}

                        <td>

                          {hasAssessment ? (

                            <>

                              <strong>
                                {student.latestScore}
                              </strong>

                              {' / '}

                              {student.maxScore}

                              <span className="pct-muted">

                                {' ('}

                                {Math.round(
                                  (
                                    student.latestScore /
                                    student.maxScore
                                  ) * 100
                                )}

                                {'%)'}

                              </span>

                            </>

                          ) : (

                            <span className="pct-muted">

                              Not evaluated

                            </span>

                          )}

                        </td>


                        {/* Grade */}

                        <td>

                          {student.grade !== '-' ? (

                            <span
                              className={
                                'grade-pill ' +
                                gradeClass
                              }
                            >

                              {student.grade}

                            </span>

                          ) : (

                            <span className="pct-muted">

                              -

                            </span>

                          )}

                        </td>


                        {/* Learning Gap */}

                        <td className="gap-cell">

                          <span className="gap-text">

                            {student.learningGap}

                          </span>

                        </td>


                        {/* Actions */}

                        <td className="text-right">

                          <button
                            className="view-sheet-btn"
                            onClick={() =>
                              setSelectedStudent(student)
                            }
                            type="button"
                            title="View Student Record"
                          >

                            <Eye size={14} />

                            View

                          </button>

                        </td>

                      </tr>

                    );

                  })

                )}

              </tbody>

            </table>

          </div>

        </div>

      )}


      {/* ===================================================
          STUDENT DETAIL MODAL
      =================================================== */}

      {selectedStudent && (

        <div
          className="modal-overlay"
          onClick={() =>
            setSelectedStudent(null)
          }
        >

          <div
            className="modal-card student-archive-modal"
            onClick={(e) =>
              e.stopPropagation()
            }
          >

            {/* HEADER */}

            <div className="modal-header">

              <div>

                <strong>

                  {selectedStudent.name}

                  {' ('}

                  {selectedStudent.rollNo}

                  {')'}

                </strong>

                <span className="modal-sub-label">

                  {selectedStudent.section}

                  {' • '}

                  Student Evaluation Record

                </span>

              </div>


              <button
                className="modal-close-btn"
                onClick={() =>
                  setSelectedStudent(null)
                }
                type="button"
              >

                ×

              </button>

            </div>


            {/* BODY */}

            <div className="modal-body">

              <div className="student-stats-row">


                {/* SCORE */}

                <div className="stat-box">

                  <span className="stat-label">

                    Score

                  </span>

                  <strong>

                    {selectedStudent.maxScore > 0
                      ? `${selectedStudent.latestScore}/${selectedStudent.maxScore}`
                      : 'Not evaluated'
                    }

                  </strong>

                </div>


                {/* GRADE */}

                <div className="stat-box">

                  <span className="stat-label">

                    Grade

                  </span>

                  <strong>

                    {selectedStudent.grade}

                  </strong>

                </div>


                {/* ATTENDANCE */}

                <div className="stat-box">

                  <span className="stat-label">

                    Attendance

                  </span>

                  <strong>

                    {selectedStudent.attendance}

                  </strong>

                </div>

              </div>


              {/* LEARNING GAP */}

              <div className="archive-feedback-box">

                <div className="feedback-heading">

                  Student Learning Status:

                </div>

                <p>

                  {selectedStudent.learningGap}

                </p>

              </div>

            </div>


            {/* FOOTER */}

            <div className="modal-footer">

              <button
                className="primary-action-btn"
                onClick={() => {

                  const student =
                    selectedStudent;

                  setSelectedStudent(null);

                  if (
                    onEvaluateStudentSheet
                  ) {

                    onEvaluateStudentSheet(
                      student
                    );

                  }

                }}
                type="button"
              >

                <FileText size={16} />

                Evaluate Answer Sheet

              </button>

            </div>

          </div>

        </div>

      )}


      {/* ===================================================
          ADD STUDENT MODAL
      =================================================== */}

      {isAddStudentOpen && (

        <AddStudentModal

          onClose={() =>
            setIsAddStudentOpen(false)
          }

          onAdd={handleAddNewStudent}

        />

      )}

    </div>

  );

}