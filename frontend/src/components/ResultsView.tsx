import { useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  Users,
  Printer,
} from 'lucide-react';
import type { AssessmentResult, StudentEvaluation } from '../types/assessment';
import type { SchoolProfile } from '../types/user';
import AnswerImageViewer from './AnswerImageViewer';

function ScorePill({ score, max }: { score: number; max: number }) {
  const pct = max > 0 ? score / max : 0;
  const isZero = score === 0;
  const pillClass = isZero ? 'score-pill-red' : pct >= 0.8 ? 'score-pill-green' : 'score-pill-orange';
  return <span className={'figma-score-pill ' + pillClass}>{score} / {max}</span>;
}

function SummaryBanner({ summary, studentName, rollNo }: { summary: AssessmentResult['summary']; studentName?: string; rollNo?: string }) {
  const pct = summary.max_score > 0 ? summary.total_score / summary.max_score : 0;
  const bannerClass =
    pct >= 0.8 ? 'summary-banner-green' : pct >= 0.5 ? 'summary-banner-orange' : 'summary-banner-red';

  return (
    <div className={'results-summary-banner ' + bannerClass}>
      <div className="summary-banner-score">
        <span className="summary-score-num">{summary.total_score}</span>
        <span className="summary-score-sep"> / </span>
        <span className="summary-score-max">{summary.max_score}</span>
        <span className="summary-score-label"> marks</span>
      </div>

      <div className="summary-banner-stats">
        {studentName && (
          <span className="summary-stat">
            <strong>{studentName}</strong> ({rollNo || '10A-01'}) ·
          </span>
        )}
        <span className="summary-stat">
          <strong>{summary.answered}</strong> of <strong>{summary.total_questions}</strong> answered
        </span>
        {summary.unanswered > 0 && (
          <span className="summary-stat summary-stat-warn">
            · {summary.unanswered} unanswered
          </span>
        )}
        {summary.unmatched_answers > 0 && (
          <span className="summary-stat summary-stat-warn">
            · {summary.unmatched_answers} unmatched
          </span>
        )}
      </div>

      <div className="summary-banner-pct">
        {Math.round(pct * 100)}%
      </div>
    </div>
  );
}

export default function ResultsView({
  result,
  school,
}: {
  result: AssessmentResult;
  school?: SchoolProfile;
  onReset?: () => void;
}) {
  const studentsList: StudentEvaluation[] = result.students && result.students.length > 0
    ? result.students
    : [
        {
          student_id: 'std_1',
          student_name: 'Aarav Sharma',
          roll_no: '10A-01',
          total_score: result.summary.total_score,
          max_score: result.summary.max_score,
          percentage: Math.round((result.summary.total_score / result.summary.max_score) * 100),
          grade: 'A',
          questions: result.questions,
          answers: result.answers,
          matches: result.matches,
          unmatched_answers: result.unmatched_answers,
          answer_pages: result.answer_pages,
          summary: result.summary
        }
      ];

  const [activeStudentIndex, setActiveStudentIndex] = useState(0);
  const activeStudent = studentsList[activeStudentIndex] || studentsList[0];

  const [selectedId, setSelectedId] = useState<string>(
    activeStudent.matches.find((m) => m.status !== 'parent')?.question_id || activeStudent.matches[0]?.question_id || ''
  );
  const [expandedAll, setExpandedAll] = useState(false);
  const [mobileTab, setMobileTab] = useState<'questions' | 'answers'>('questions');
  const [unmatchedExpanded, setUnmatchedExpanded] = useState(false);

  const selectedMatch = activeStudent.matches.find((m) => m.question_id === selectedId);

  const handleSelectStudent = (idx: number) => {
    setActiveStudentIndex(idx);
    const newStudent = studentsList[idx];
    if (newStudent && newStudent.matches.length > 0) {
      setSelectedId(newStudent.matches.find((m) => m.status !== 'parent')?.question_id || newStudent.matches[0]?.question_id || '');
    }
  };

  return (
    <div className="figma-results-workspace">
      {/* Printable Report Header (Visible only in Print / PDF export) */}
      <div className="print-only-report-header">
        <div className="print-header-top">
          <div className="print-school-info">
            <h2>{school?.name || 'Delhi Public School'}</h2>
            <span>{school?.location || 'Bokaro Steel City'} • {school?.board || 'CBSE'} Affiliated ({school?.affiliationNumber || '3430032'})</span>
          </div>
          <div className="print-report-title-col">
            <strong>STUDENT EVALUATION REPORT</strong>
            <span>Academic Assessment Session 2025–2026</span>
          </div>
        </div>
        <div className="print-student-bar">
          <div><strong>Student Name:</strong> {activeStudent.student_name}</div>
          <div><strong>Roll No:</strong> {activeStudent.roll_no}</div>
          <div><strong>Class:</strong> Class 10 — Science (Physics)</div>
          <div><strong>Final Score:</strong> {activeStudent.total_score} / {activeStudent.max_score} ({activeStudent.percentage}%) — Grade {activeStudent.grade}</div>
        </div>
      </div>

      {/* Multiple Students Batch Switcher Bar (if batch > 1) */}
      {studentsList.length > 1 && (
        <div className="batch-students-switcher-bar">
          <div className="batch-switcher-label">
            <Users size={15} />
            <span>Batch ({studentsList.length} Students):</span>
          </div>
          <div className="students-pills-scroll">
            {studentsList.map((st, idx) => {
              const isActive = idx === activeStudentIndex;
              const gradeClass =
                st.grade === 'A' ? 'badge-green' :
                st.grade === 'B' ? 'badge-yellow' :
                st.grade === 'C' ? 'badge-orange' : 'badge-red';

              return (
                <button
                  key={st.student_id || idx}
                  className={'student-selector-pill ' + (isActive ? 'active' : '')}
                  onClick={() => handleSelectStudent(idx)}
                  type="button"
                >
                  <span className="st-name">{st.student_name}</span>
                  <span className="st-score">{st.total_score}/{st.max_score}</span>
                  <span className={'st-grade-mini ' + gradeClass}>{st.grade}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Score Summary Banner */}
      <SummaryBanner
        summary={activeStudent.summary}
        studentName={activeStudent.student_name}
        rollNo={activeStudent.roll_no}
      />

      {/* Mobile Tab Switcher */}
      <div className="mobile-tab-switch">
        <button
          className={'tab-btn ' + (mobileTab === 'questions' ? 'active' : '')}
          onClick={() => setMobileTab('questions')}
          type="button"
        >
          Questions ({activeStudent.questions.length})
        </button>
        <button
          className={'tab-btn ' + (mobileTab === 'answers' ? 'active' : '')}
          onClick={() => setMobileTab('answers')}
          type="button"
        >
          Answer Sheet
        </button>
      </div>

      {/* Main Split Layout */}
      <div className="figma-split-grid">
        {/* Left Column: Extracted Questions & AI Feedback */}
        <div className={'figma-questions-col ' + (mobileTab === 'answers' ? 'mobile-hidden' : '')}>
          <div className="figma-questions-top-bar">
            <h2 className="extracted-q-title">
              {activeStudent.student_name}'s Answers ({activeStudent.questions.length} Qs)
            </h2>
            <div className="top-bar-btns-group">
              <button
                className="expand-all-btn print-btn-highlight"
                onClick={() => window.print()}
                title="Download or Print Official PDF Report for this student"
                type="button"
              >
                <Printer size={13} /> Export PDF Report
              </button>
              <button
                className="expand-all-btn"
                onClick={() => setExpandedAll(!expandedAll)}
                type="button"
              >
                {expandedAll ? 'Collapse All' : 'Expand All'}
              </button>
            </div>
          </div>

          <div className="figma-questions-list-scroll">
            {activeStudent.matches.map((match) => {
              const isSelected = match.question_id === selectedId;
              const isExpanded = expandedAll || isSelected;
              const isParent = match.status === 'parent';

              return (
                <div
                  key={match.question_id}
                  className={'figma-q-card ' + (isSelected ? 'selected-orange-border' : '') + (isParent ? ' parent-card' : '')}
                  onClick={() => {
                    setSelectedId(match.question_id);
                    setMobileTab('answers');
                  }}
                >
                  <div className="q-card-header-row">
                    <div className="q-badge-num-circle">
                      {match.question.number}
                    </div>

                    <div className="q-text-flex">
                      <p className="q-title-text">{match.question.text}</p>
                    </div>

                    <div className="q-right-controls">
                      {!isParent && match.grading && (
                        <ScorePill score={match.grading.score} max={match.grading.max_score} />
                      )}
                      <div className="chevron-icon-wrap">
                        {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      </div>
                    </div>
                  </div>

                  {/* AI Feedback Nested Block */}
                  {isExpanded && !isParent && (
                    <div className={'figma-ai-feedback-container ' + (match.status === 'unanswered' ? 'feedback-unanswered-box' : '')}>
                      <div className="ai-feedback-heading">
                        {match.status === 'unanswered' ? '⚠️ Evaluation Note:' : 'AI Evaluator Feedback:'}
                      </div>
                      <p className="ai-feedback-body">
                        {match.grading?.feedback || (match.status === 'unanswered' ? 'Question was not attempted by the student on this answer sheet.' : 'Evaluation pending.')}
                      </p>
                    </div>
                  )}
                </div>
              );
            })}

            {/* Unmatched Answers Section */}
            {activeStudent.unmatched_answers && activeStudent.unmatched_answers.length > 0 && (
              <div className="unmatched-answers-section">
                <button
                  className="unmatched-toggle-btn"
                  onClick={() => setUnmatchedExpanded(!unmatchedExpanded)}
                  type="button"
                >
                  <AlertTriangle size={14} className="unmatched-warn-icon" />
                  <span>{activeStudent.unmatched_answers.length} Unmatched Answer{activeStudent.unmatched_answers.length > 1 ? 's' : ''}</span>
                  {unmatchedExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </button>
                {unmatchedExpanded && (
                  <div className="unmatched-list">
                    {activeStudent.unmatched_answers.map((item, idx) => (
                      <div key={item.answer_id || idx} className="unmatched-item">
                        <span className="unmatched-qnum">
                          {item.question_number ? `Q${item.question_number}` : 'No number'}
                        </span>
                        <p className="unmatched-text">{item.text}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Answer Sheet View with Live Highlighting */}
        <div className={'figma-answer-sheet-col ' + (mobileTab === 'questions' ? 'mobile-hidden' : '')}>
          <AnswerImageViewer
            key={activeStudent.student_id || String(activeStudentIndex)}
            pages={activeStudent.answer_pages}
            regions={selectedMatch?.answer?.regions || []}
            selectedQuestionNumber={selectedMatch?.question.number || 'Q1'}
          />
        </div>
      </div>
    </div>
  );
}
