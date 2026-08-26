import { useState } from 'react';
import {
  Search,
  Plus,
  FileText,
  Eye,
  GraduationCap
} from 'lucide-react';
import type { TeacherUser } from '../types/user';
import { AddStudentModal } from './Modals';

type ClassroomViewProps = {
  user: TeacherUser;
  onEvaluateStudentSheet?: () => void;
};

type Student = {
  id: string;
  name: string;
  rollNo: string;
  section: string;
  attendance: string;
  latestScore: number;
  maxScore: number;
  grade: 'A' | 'B' | 'C' | 'D';
  learningGap: string;
};

const INITIAL_STUDENTS: Record<string, Student[]> = {
  '10-a': [
    { id: 'st-1', name: 'Aarav Sharma', rollNo: '10A-01', section: 'Section A', attendance: '96%', latestScore: 48, maxScore: 50, grade: 'A', learningGap: 'None detected — Exceptional derivation accuracy' },
    { id: 'st-2', name: 'Ananya Sen', rollNo: '10A-02', section: 'Section A', attendance: '98%', latestScore: 47, maxScore: 50, grade: 'A', learningGap: 'Minor calculation error in Ohm Law' },
    { id: 'st-3', name: 'Simran Kaur', rollNo: '10A-03', section: 'Section A', attendance: '88%', latestScore: 32, maxScore: 50, grade: 'C', learningGap: 'Misinterprets parallel vs series resistance' },
    { id: 'st-4', name: 'Rohan Gupta', rollNo: '10A-04', section: 'Section A', attendance: '92%', latestScore: 41, maxScore: 50, grade: 'B', learningGap: 'Needs practice in circuit ray diagrams' },
    { id: 'st-5', name: 'Pooja Verma', rollNo: '10A-05', section: 'Section A', attendance: '84%', latestScore: 28, maxScore: 50, grade: 'D', learningGap: 'Joule heating derivations incomplete' },
    { id: 'st-6', name: 'Karan Mehra', rollNo: '10A-06', section: 'Section A', attendance: '94%', latestScore: 44, maxScore: 50, grade: 'A', learningGap: 'Good grasp of concepts' },
  ],
  '10-b': [
    { id: 'st-7', name: 'Devika Nair', rollNo: '10B-01', section: 'Section B', attendance: '95%', latestScore: 46, maxScore: 50, grade: 'A', learningGap: 'Accurate explanations' },
    { id: 'st-8', name: 'Vikram Malhotra', rollNo: '10B-02', section: 'Section B', attendance: '89%', latestScore: 36, maxScore: 50, grade: 'B', learningGap: 'Formula unit conversion issues' },
    { id: 'st-9', name: 'Tanvi Joshi', rollNo: '10B-03', section: 'Section B', attendance: '91%', latestScore: 39, maxScore: 50, grade: 'B', learningGap: 'Needs more steps in 5-mark proofs' },
    { id: 'st-10', name: 'Aditya Roy', rollNo: '10B-04', section: 'Section B', attendance: '82%', latestScore: 25, maxScore: 50, grade: 'D', learningGap: 'Requires targeted remediation in EMF' },
  ]
};

export default function ClassroomView({ user, onEvaluateStudentSheet }: ClassroomViewProps) {
  const [studentsData, setStudentsData] = useState<Record<string, Student[]>>(INITIAL_STUDENTS);
  const [activeSection, setActiveSection] = useState<'10-a' | '10-b'>('10-a');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStudent, setSelectedStudent] = useState<Student | null>(null);
  const [isAddStudentOpen, setIsAddStudentOpen] = useState(false);

  const students = studentsData[activeSection] || [];
  const filteredStudents = students.filter(s =>
    s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.rollNo.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleAddNewStudent = (newSt: { name: string; rollNo: string; section: string }) => {
    const secKey = newSt.section.includes('B') ? '10-b' : '10-a';
    const created: Student = {
      id: 'st-' + Date.now(),
      name: newSt.name,
      rollNo: newSt.rollNo,
      section: newSt.section,
      attendance: '100%',
      latestScore: 42,
      maxScore: 50,
      grade: 'B',
      learningGap: 'Newly enrolled — Baseline evaluation pending'
    };
    setStudentsData(prev => ({
      ...prev,
      [secKey]: [created, ...(prev[secKey] || [])]
    }));
    setActiveSection(secKey);
  };

  return (
    <div className="classroom-view-wrapper">
      {/* Classroom Header Bar */}
      <div className="classroom-header-bar">
        <div className="header-left-info">
          <h2>My Classroom — {user.subject}</h2>
          <span className="school-subhead">
            <GraduationCap size={15} /> {user.school.name} ({user.school.location}) • Academic Year 2025–2026
          </span>
        </div>

        <div className="header-actions-row">
          <button className="primary-action-btn" onClick={() => setIsAddStudentOpen(true)} type="button">
            <Plus size={16} /> Add Student
          </button>
        </div>
      </div>

      {/* Section Filter Pills */}
      <div className="classroom-controls-bar">
        <div className="section-tabs-group">
          <button
            className={'section-tab-btn ' + (activeSection === '10-a' ? 'active' : '')}
            onClick={() => setActiveSection('10-a')}
            type="button"
          >
            Class 10 — Section A (28 Students)
          </button>
          <button
            className={'section-tab-btn ' + (activeSection === '10-b' ? 'active' : '')}
            onClick={() => setActiveSection('10-b')}
            type="button"
          >
            Class 10 — Section B (26 Students)
          </button>
        </div>

        <div className="classroom-search-box">
          <Search size={16} className="search-icon" />
          <input
            type="text"
            placeholder="Search student by name or roll no..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* Student Roster Table */}
      <div className="figma-dash-card student-roster-card">
        <div className="table-responsive-wrap">
          <table className="classroom-table">
            <thead>
              <tr>
                <th>Roll No</th>
                <th>Student Name</th>
                <th>Section</th>
                <th>Attendance</th>
                <th>Latest Exam Score</th>
                <th>Grade</th>
                <th>Identified Learning Gap</th>
                <th className="text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredStudents.map((student) => {
                const gradeClass =
                  student.grade === 'A' ? 'grade-badge-green' :
                  student.grade === 'B' ? 'grade-badge-yellow' :
                  student.grade === 'C' ? 'grade-badge-orange' : 'grade-badge-red';

                return (
                  <tr key={student.id} className="student-row">
                    <td className="roll-cell"><strong>{student.rollNo}</strong></td>
                    <td className="name-cell">
                      <div className="student-avatar-row">
                        <div className="student-mini-avatar">{student.name.charAt(0)}</div>
                        <span>{student.name}</span>
                      </div>
                    </td>
                    <td>{student.section}</td>
                    <td>{student.attendance}</td>
                    <td>
                      <strong>{student.latestScore}</strong> / {student.maxScore}
                      <span className="pct-muted"> ({Math.round((student.latestScore / student.maxScore) * 100)}%)</span>
                    </td>
                    <td>
                      <span className={'grade-pill ' + gradeClass}>{student.grade}</span>
                    </td>
                    <td className="gap-cell">
                      <span className="gap-text">{student.learningGap}</span>
                    </td>
                    <td className="text-right">
                      <button
                        className="view-sheet-btn"
                        onClick={() => setSelectedStudent(student)}
                        type="button"
                        title="View Student Answer Sheet Archive"
                      >
                        <Eye size={14} /> View
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Student Detail Modal */}
      {selectedStudent && (
        <div className="modal-overlay" onClick={() => setSelectedStudent(null)}>
          <div className="modal-card student-archive-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <strong>{selectedStudent.name} ({selectedStudent.rollNo})</strong>
                <span className="modal-sub-label">Class 10 Science • Answer Sheet &amp; Evaluation Record</span>
              </div>
              <button className="modal-close-btn" onClick={() => setSelectedStudent(null)} type="button">×</button>
            </div>

            <div className="modal-body">
              <div className="student-stats-row">
                <div className="stat-box">
                  <span className="stat-label">Score</span>
                  <strong>{selectedStudent.latestScore}/{selectedStudent.maxScore}</strong>
                </div>
                <div className="stat-box">
                  <span className="stat-label">Grade</span>
                  <strong>{selectedStudent.grade}</strong>
                </div>
                <div className="stat-box">
                  <span className="stat-label">Attendance</span>
                  <strong>{selectedStudent.attendance}</strong>
                </div>
              </div>

              <div className="archive-feedback-box">
                <div className="feedback-heading">AI Diagnostic Note:</div>
                <p>{selectedStudent.learningGap}</p>
              </div>
            </div>

            <div className="modal-footer">
              <button
                className="primary-action-btn"
                onClick={() => {
                  setSelectedStudent(null);
                  if (onEvaluateStudentSheet) onEvaluateStudentSheet();
                }}
                type="button"
              >
                <FileText size={16} /> Open in Assessment Analyzer
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Student Modal */}
      {isAddStudentOpen && (
        <AddStudentModal
          onClose={() => setIsAddStudentOpen(false)}
          onAdd={handleAddNewStudent}
        />
      )}
    </div>
  );
}
