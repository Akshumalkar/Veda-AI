import { useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  Printer,
} from 'lucide-react';

import type {
  AssessmentResult,
  StudentEvaluation,
} from '../types/assessment';

import type { SchoolProfile } from '../types/user';

import AnswerImageViewer from './AnswerImageViewer';


// ============================================================
// SCORE PILL
// ============================================================

function ScorePill({
  score,
  max,
}: {
  score: number;
  max: number;
}) {
  const percentage = max > 0 ? score / max : 0;

  const pillClass =
    score === 0
      ? 'score-pill-red'
      : percentage >= 0.8
        ? 'score-pill-green'
        : 'score-pill-orange';

  return (
    <span
      className={
        'figma-score-pill ' + pillClass
      }
    >
      {score} / {max}
    </span>
  );
}


// ============================================================
// SUMMARY BANNER
// ============================================================

function SummaryBanner({
  summary,
  studentName,
  rollNo,
}: {
  summary: AssessmentResult['summary'];
  studentName?: string;
  rollNo?: string;
}) {
  const percentage =
    summary.max_score > 0
      ? summary.total_score / summary.max_score
      : 0;

  const bannerClass =
    percentage >= 0.8
      ? 'summary-banner-green'
      : percentage >= 0.5
        ? 'summary-banner-orange'
        : 'summary-banner-red';

  return (
    <div
      className={
        'results-summary-banner ' + bannerClass
      }
    >
      {/* Score */}
      <div className="summary-banner-score">
        <span className="summary-score-num">
          {summary.total_score}
        </span>

        <span className="summary-score-sep">
          {' / '}
        </span>

        <span className="summary-score-max">
          {summary.max_score}
        </span>

        <span className="summary-score-label">
          {' '}marks
        </span>
      </div>


      {/* Student information */}
      <div className="summary-banner-stats">

        {studentName && (
          <span className="summary-stat">
            <strong>{studentName}</strong>

            {rollNo && (
              <>
                {' '}
                ({rollNo})
              </>
            )}

            {' · '}
          </span>
        )}

        <span className="summary-stat">
          <strong>{summary.answered}</strong>
          {' of '}
          <strong>
            {summary.total_questions}
          </strong>
          {' answered'}
        </span>

        {summary.unanswered > 0 && (
          <span className="summary-stat summary-stat-warn">
            {' · '}
            {summary.unanswered}
            {' unanswered'}
          </span>
        )}

        {summary.unmatched_answers > 0 && (
          <span className="summary-stat summary-stat-warn">
            {' · '}
            {summary.unmatched_answers}
            {' unmatched'}
          </span>
        )}
      </div>


      {/* Percentage */}
      <div className="summary-banner-pct">
        {Math.round(percentage * 100)}%
      </div>
    </div>
  );
}


// ============================================================
// RESULT VIEW
// ============================================================

export default function ResultsView({
  result,
  school,
  onReset,
}: {
  result: AssessmentResult;
  school?: SchoolProfile;
  onReset?: () => void;
}) {

  // ==========================================================
  // IMPORTANT:
  //
  // Never create a fake student such as "Aarav Sharma".
  //
  // If the backend provides a real student, use it.
  // Otherwise use the current assessment result itself.
  // ==========================================================

  const backendStudent =
    result.students &&
    result.students.length > 0
      ? result.students[0]
      : null;


  const activeStudent: StudentEvaluation =

    backendStudent ??

    {
      student_id:
        result.student_id ||
        'assessment-student',

      student_name:
        result.student_name?.trim() || '',

      roll_no:
        result.roll_no?.trim() || '',

      total_score:
        result.total_score ??
        result.summary.total_score,

      max_score:
        result.max_score ??
        result.summary.max_score,

      percentage:
        result.percentage ??
        (
          result.summary.max_score > 0
            ? Math.round(
                (
                  result.summary.total_score /
                  result.summary.max_score
                ) * 100
              )
            : 0
        ),

      grade:
        result.grade || '',

      questions:
        result.questions,

      answers:
        result.answers,

      matches:
        result.matches,

      unmatched_answers:
        result.unmatched_answers,

      answer_pages:
        result.answer_pages,

      summary:
        result.summary,
    };


  // ==========================================================
  // LOCAL UI STATE
  // ==========================================================

  const [selectedId, setSelectedId] =
    useState<string>(
      activeStudent.matches.find(
        (match) =>
          match.status !== 'parent'
      )?.question_id
      ||
      activeStudent.matches[0]
        ?.question_id
      ||
      ''
    );

  const [expandedAll, setExpandedAll] =
    useState(false);

  const [mobileTab, setMobileTab] =
    useState<'questions' | 'answers'>(
      'questions'
    );

  const [unmatchedExpanded, setUnmatchedExpanded] =
    useState(false);


  // ==========================================================
  // SELECTED QUESTION
  // ==========================================================

  const selectedMatch =
    activeStudent.matches.find(
      (match) =>
        match.question_id === selectedId
    );


  // ==========================================================
  // STUDENT DISPLAY
  // ==========================================================

  const displayStudentName =
    activeStudent.student_name ||
    'Student';


  // ==========================================================
  // UI
  // ==========================================================

  return (
    <div className="figma-results-workspace">

      {/* ====================================================
          PRINT REPORT HEADER
      ==================================================== */}

      <div className="print-only-report-header">

        <div className="print-header-top">

          <div className="print-school-info">

            <h2>
              {school?.name || 'School'}
            </h2>

            <span>
              {school?.location || ''}
              {school?.board
                ? ` • ${school.board} Affiliated`
                : ''}
              {school?.affiliationNumber
                ? ` (${school.affiliationNumber})`
                : ''}
            </span>

          </div>


          <div className="print-report-title-col">

            <strong>
              STUDENT EVALUATION REPORT
            </strong>

            <span>
              Academic Assessment Report
            </span>

          </div>

        </div>


        {/* Student information */}
        <div className="print-student-bar">

          <div>
            <strong>
              Student Name:
            </strong>{' '}
            {displayStudentName || 'Not assigned'}
          </div>

          {activeStudent.roll_no && (
            <div>
              <strong>
                Roll No:
              </strong>{' '}
              {activeStudent.roll_no}
            </div>
          )}

          <div>
            <strong>
              Final Score:
            </strong>{' '}
            {activeStudent.total_score}
            {' / '}
            {activeStudent.max_score}
            {' ('}
            {activeStudent.percentage}
            {'%)'}

            {activeStudent.grade && (
              <>
                {' — Grade '}
                {activeStudent.grade}
              </>
            )}
          </div>

        </div>
      </div>


      {/* ====================================================
          SCORE SUMMARY
      ==================================================== */}

      <SummaryBanner
        summary={activeStudent.summary}
        studentName={
          activeStudent.student_name ||
          undefined
        }
        rollNo={
          activeStudent.roll_no ||
          undefined
        }
      />


      {/* ====================================================
          MOBILE TABS
      ==================================================== */}

      <div className="mobile-tab-switch">

        <button
          className={
            'tab-btn ' +
            (
              mobileTab === 'questions'
                ? 'active'
                : ''
            )
          }
          onClick={() =>
            setMobileTab('questions')
          }
          type="button"
        >
          Questions (
          {activeStudent.questions.length}
          )
        </button>


        <button
          className={
            'tab-btn ' +
            (
              mobileTab === 'answers'
                ? 'active'
                : ''
            )
          }
          onClick={() =>
            setMobileTab('answers')
          }
          type="button"
        >
          Answer Sheet
        </button>

      </div>


      {/* ====================================================
          MAIN SPLIT LAYOUT
      ==================================================== */}

      <div className="figma-split-grid">

        {/* ==================================================
            LEFT — QUESTIONS
        ================================================== */}

        <div
          className={
            'figma-questions-col ' +
            (
              mobileTab === 'answers'
                ? 'mobile-hidden'
                : ''
            )
          }
        >

          {/* Top bar */}
          <div className="figma-questions-top-bar">

            <h2 className="extracted-q-title">
              {displayStudentName
                ? `${displayStudentName}'s Answers`
                : 'Assessment Answers'}
              {' ('}
              {activeStudent.questions.length}
              {' Qs)'}
            </h2>


            <div className="top-bar-btns-group">

              {/* Print / PDF */}
              <button
                className="expand-all-btn print-btn-highlight"
                onClick={() =>
                  window.print()
                }
                title="Print or save this assessment report as PDF"
                type="button"
              >
                <Printer size={13} />
                {' '}
                Export PDF Report
              </button>


              {/* Expand */}
              <button
                className="expand-all-btn"
                onClick={() =>
                  setExpandedAll(
                    !expandedAll
                  )
                }
                type="button"
              >
                {expandedAll
                  ? 'Collapse All'
                  : 'Expand All'}
              </button>

            </div>

          </div>


          {/* Question list */}
          <div className="figma-questions-list-scroll">

            {activeStudent.matches.map(
              (match) => {

                const isSelected =
                  match.question_id ===
                  selectedId;

                const isExpanded =
                  expandedAll ||
                  isSelected;

                const isParent =
                  match.status ===
                  'parent';


                return (
                  <div
                    key={
                      match.question_id
                    }
                    className={
                      'figma-q-card ' +
                      (
                        isSelected
                          ? 'selected-orange-border '
                          : ''
                      ) +
                      (
                        isParent
                          ? 'parent-card'
                          : ''
                      )
                    }
                    onClick={() => {

                      setSelectedId(
                        match.question_id
                      );

                      setMobileTab(
                        'answers'
                      );

                    }}
                  >

                    {/* Question header */}
                    <div className="q-card-header-row">

                      <div className="q-badge-num-circle">
                        {match.question.number}
                      </div>


                      <div className="q-text-flex">

                        <p className="q-title-text">
                          {match.question.text}
                        </p>

                      </div>


                      <div className="q-right-controls">

                        {!isParent &&
                          match.grading && (
                            <ScorePill
                              score={
                                match.grading
                                  .score
                              }
                              max={
                                match.grading
                                  .max_score
                              }
                            />
                          )}


                        <div className="chevron-icon-wrap">

                          {isExpanded
                            ? (
                              <ChevronUp
                                size={16}
                              />
                            )
                            : (
                              <ChevronDown
                                size={16}
                              />
                            )}

                        </div>

                      </div>

                    </div>


                    {/* AI / evaluation feedback */}
                    {isExpanded &&
                      !isParent && (

                        <div
                          className={
                            'figma-ai-feedback-container ' +
                            (
                              match.status ===
                              'unanswered'
                                ? 'feedback-unanswered-box'
                                : ''
                            )
                          }
                        >

                          <div className="ai-feedback-heading">

                            {match.status ===
                            'unanswered'
                              ? '⚠️ Evaluation Note:'
                              : 'AI Evaluator Feedback:'}

                          </div>


                          <p className="ai-feedback-body">

                            {match.grading?.feedback ||

                              (
                                match.status ===
                                'unanswered'
                                  ? 'Question was not attempted by the student on this answer sheet.'
                                  : 'Evaluation pending.'
                              )}

                          </p>

                        </div>

                      )}

                  </div>
                );
              }
            )}


            {/* =================================================
                UNMATCHED ANSWERS
            ================================================= */}

            {activeStudent.unmatched_answers &&
              activeStudent.unmatched_answers.length >
              0 && (

                <div className="unmatched-answers-section">

                  <button
                    className="unmatched-toggle-btn"
                    onClick={() =>
                      setUnmatchedExpanded(
                        !unmatchedExpanded
                      )
                    }
                    type="button"
                  >

                    <AlertTriangle
                      size={14}
                      className="unmatched-warn-icon"
                    />

                    <span>

                      {
                        activeStudent
                          .unmatched_answers
                          .length
                      }

                      {' Unmatched Answer'}

                      {
                        activeStudent
                          .unmatched_answers
                          .length > 1
                          ? 's'
                          : ''
                      }

                    </span>


                    {unmatchedExpanded
                      ? (
                        <ChevronUp size={14} />
                      )
                      : (
                        <ChevronDown size={14} />
                      )}

                  </button>


                  {unmatchedExpanded && (

                    <div className="unmatched-list">

                      {activeStudent
                        .unmatched_answers
                        .map(
                          (item, index) => (

                            <div
                              key={
                                item.answer_id ||
                                index
                              }
                              className="unmatched-item"
                            >

                              <span className="unmatched-qnum">

                                {item.question_number
                                  ? `Q${item.question_number}`
                                  : 'No number'}

                              </span>


                              <p className="unmatched-text">
                                {item.text}
                              </p>

                            </div>

                          )
                        )}

                    </div>

                  )}

                </div>

              )}

          </div>
        </div>


        {/* ==================================================
            RIGHT — ANSWER SHEET
        ================================================== */}

        <div
          className={
            'figma-answer-sheet-col ' +
            (
              mobileTab === 'questions'
                ? 'mobile-hidden'
                : ''
            )
          }
        >

          <AnswerImageViewer
            pages={
              activeStudent.answer_pages
            }

            regions={
              selectedMatch?.answer
                ?.regions || []
            }

            selectedQuestionNumber={
              selectedMatch
                ?.question.number ||
              'Q1'
            }
          />

        </div>

      </div>


      {/* ====================================================
          OPTIONAL RESET
      ==================================================== */}

      {onReset && (
        <div
          className="results-reset-container"
        >
          <button
            type="button"
            onClick={onReset}
            className="results-reset-btn"
          >
            Back to Assessment Upload
          </button>
        </div>
      )}

    </div>
  );
}