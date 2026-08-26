import { useState } from 'react';
import {
  Sparkles,
  BookOpen,
  FileSpreadsheet,
  Layers,
  Printer,
  CheckCircle,
  Clock,
  Award,
  ListChecks,
  Bookmark
} from 'lucide-react';
import type { TeacherUser } from '../types/user';
import type { LessonPlan, Worksheet, RubricTemplate } from '../types/lesson';

type LessonStudioProps = {
  user: TeacherUser;
};

const SAMPLE_LESSON_PLANS: Record<string, LessonPlan> = {
  'electricity': {
    id: 'lp-1',
    chapter: 'Electricity & Circuits (Chapter 12)',
    subject: 'Physics & Science',
    grade: 'Class 10 (CBSE)',
    duration: '45 Minutes (Single Period)',
    learningObjectives: [
      'Understand Ohm\'s law and the mathematical relation V = IR under constant temperature.',
      'Differentiate between series and parallel resistor combinations in domestic circuits.',
      'Calculate equivalent resistance and current in complex multi-loop circuits.'
    ],
    prerequisites: [
      'Concept of electric charge, potential difference (Volts), and electric current (Amperes).'
    ],
    boardQuestions: [
      'CBSE 2024: Why is a parallel arrangement used in domestic wiring instead of series?',
      'CBSE 2023: Calculate total resistance for three resistors of 2Ω, 3Ω and 6Ω in parallel.'
    ],
    phases: [
      {
        phase: 'Engage',
        durationMinutes: 7,
        activity: 'Demonstrate glowing of 2 light bulbs in series vs parallel when one is unscrewed.',
        teacherRole: 'Ask guiding questions: Why does the second bulb go off in series but stay lit in parallel?',
        studentRole: 'Observe bulb brightness differences and hypothesize voltage division.'
      },
      {
        phase: 'Explore',
        durationMinutes: 12,
        activity: 'Interactive Circuit Lab: Connect ammeter and voltmeter across 3 resistors to measure branch currents.',
        teacherRole: 'Facilitate breadboard circuit connections and supervise safe voltage supplies.',
        studentRole: 'Record current I1, I2, I3 and total voltage in their lab notebook.'
      },
      {
        phase: 'Explain',
        durationMinutes: 14,
        activity: 'Derivation of 1/Rp = 1/R1 + 1/R2 + 1/R3 on the smart board using Ohm\'s law.',
        teacherRole: 'Step-by-step mathematical derivation linking to current conservation I = I1 + I2 + I3.',
        studentRole: 'Copy derivation and solve sample numerical problem with teacher.'
      },
      {
        phase: 'Elaborate',
        durationMinutes: 7,
        activity: 'Real-world application: Discuss household electrical safety, circuit breakers, and fuse ratings.',
        teacherRole: 'Present an overloaded power strip problem and ask for calculated safety limits.',
        studentRole: 'Calculate total current draw for a 1000W iron and 200W refrigerator.'
      },
      {
        phase: 'Evaluate',
        durationMinutes: 5,
        activity: '3-Question Exit Ticket: Calculate Rp for 6Ω and 3Ω, and state 2 advantages of parallel wiring.',
        teacherRole: 'Collect exit slips for AI-assisted diagnostic evaluation.',
        studentRole: 'Submit independent written solutions on paper.'
      }
    ],
    homework: 'NCERT Textbook Exercise Q1 to Q6; Practice 3 past-year CBSE numericals on Joule heating.'
  }
};

const SAMPLE_WORKSHEETS: Record<string, Worksheet> = {
  'electricity': {
    id: 'ws-1',
    title: 'Class 10 Science Practice Worksheet: Current & Resistance',
    chapter: 'Electricity (Chapter 12)',
    totalMarks: 25,
    timeAllowed: '40 Minutes',
    questions: [
      {
        id: 'wq-1',
        type: 'MCQ',
        marks: 1,
        question: 'What happens to the resistance of a cylindrical conductor if its length is doubled and radius is halved?',
        options: ['(a) Halved', '(b) Doubled', '(c) Quadrupled', '(d) Increases 8 times'],
        solution: '(d) Increases 8 times. R = ρ*L/A. L\' = 2L, A\' = π*(r/2)^2 = A/4. R\' = ρ*(2L)/(A/4) = 8*R.',
        markingGuide: '1 Mark for correct option (d) with formula.'
      },
      {
        id: 'wq-2',
        type: 'Short Answer',
        marks: 3,
        question: 'State Joule\'s Law of Heating. Express it in mathematical form and name two electrical appliances based on this effect.',
        solution: 'Heat produced in a resistor is directly proportional to: (1) Square of current (I^2), (2) Resistance (R), (3) Time (t). H = I^2 * R * t. Appliances: Electric Iron, Electric Toaster/Heater.',
        markingGuide: '1M for statement, 1M for formula H=I^2Rt, 1M for two correct appliances.'
      },
      {
        id: 'wq-3',
        type: 'Numerical',
        marks: 5,
        question: 'An electric lamp of resistance 20Ω and a conductor of 4Ω resistance are connected in series to a 6V battery. Calculate: (a) Total resistance of circuit, (b) Total current flowing, (c) Potential difference across the lamp.',
        solution: '(a) R_total = 20 + 4 = 24Ω. (b) I = V / R_total = 6V / 24Ω = 0.25A. (c) V_lamp = I * R_lamp = 0.25A * 20Ω = 5.0V.',
        markingGuide: '1.5M for (a), 1.5M for (b), 2M for (c) with correct units.'
      }
    ]
  }
};

const SAMPLE_RUBRICS: Record<string, RubricTemplate> = {
  'electricity': {
    id: 'rub-1',
    title: 'CBSE 5-Mark Numerical Evaluation Rubric',
    chapter: 'Electricity & Circuits',
    totalMarks: 5,
    criteria: [
      {
        id: 'rc-1',
        criterion: 'Formula & Law Identification',
        maxMarks: 1.5,
        excellent: 'Correct formula stated with standard symbols and temperature condition mentioned.',
        proficient: 'Formula stated correctly without condition or minor symbol ambiguity.',
        developing: 'Incorrect or partially recalled formula.'
      },
      {
        id: 'rc-2',
        criterion: 'Substitution & Step-by-Step Working',
        maxMarks: 2.0,
        excellent: 'All given values substituted accurately with clear step-by-step algebraic manipulation.',
        proficient: 'Substitution correct with minor arithmetic hesitation.',
        developing: 'Values misplaced or intermediate calculation omitted.'
      },
      {
        id: 'rc-3',
        criterion: 'Final Answer & SI Units',
        maxMarks: 1.5,
        excellent: 'Exact numerical result calculated with proper SI units (e.g. Ω, Volts, Amperes).',
        proficient: 'Correct number but missing or incorrect SI unit.',
        developing: 'Wrong numerical result and missing units.'
      }
    ]
  }
};

export default function LessonStudio({ user }: LessonStudioProps) {
  const [activeTab, setActiveTab] = useState<'plans' | 'worksheets' | 'rubrics'>('plans');
  const [selectedTopic, setSelectedTopic] = useState('electricity');

  const activePlan = SAMPLE_LESSON_PLANS[selectedTopic] || SAMPLE_LESSON_PLANS['electricity'];
  const activeWorksheet = SAMPLE_WORKSHEETS[selectedTopic] || SAMPLE_WORKSHEETS['electricity'];
  const activeRubric = SAMPLE_RUBRICS[selectedTopic] || SAMPLE_RUBRICS['electricity'];

  return (
    <div className="classroom-view-wrapper">
      {/* Studio Header Bar */}
      <div className="classroom-header-bar">
        <div>
          <h2>Teacher's Academic Studio</h2>
          <span className="school-subhead">
            <Sparkles size={15} /> Lesson Plans, Customizable Worksheets &amp; Marking Rubrics • {user.school.name}
          </span>
        </div>

        <div className="top-bar-btns-group">
          <button
            className="primary-action-btn"
            onClick={() => window.print()}
            type="button"
          >
            <Printer size={16} /> Print / Export PDF
          </button>
        </div>
      </div>

      {/* Studio Tab Switcher */}
      <div className="classroom-controls-bar">
        <div className="section-tabs-group">
          <button
            className={'section-tab-btn ' + (activeTab === 'plans' ? 'active' : '')}
            onClick={() => setActiveTab('plans')}
            type="button"
          >
            <BookOpen size={14} /> 5E Lesson Plans
          </button>
          <button
            className={'section-tab-btn ' + (activeTab === 'worksheets' ? 'active' : '')}
            onClick={() => setActiveTab('worksheets')}
            type="button"
          >
            <FileSpreadsheet size={14} /> Practice Worksheets
          </button>
          <button
            className={'section-tab-btn ' + (activeTab === 'rubrics' ? 'active' : '')}
            onClick={() => setActiveTab('rubrics')}
            type="button"
          >
            <Layers size={14} /> Step Rubric Builder
          </button>
        </div>

        <div className="filter-selects-row">
          <select
            className="form-select mini"
            value={selectedTopic}
            onChange={(e) => setSelectedTopic(e.target.value)}
          >
            <option value="electricity">Class 10 Science: Electricity &amp; Circuits</option>
            <option value="magnetism">Class 10 Science: Magnetic Effects of Current</option>
            <option value="chemical">Class 10 Science: Chemical Reactions</option>
          </select>
        </div>
      </div>

      {/* Tab 1: 5E Lesson Plan */}
      {activeTab === 'plans' && (
        <div className="figma-dash-card lesson-plan-card">
          <div className="lesson-plan-header-box">
            <div className="lp-badge-row">
              <span className="lp-tag"><Bookmark size={13} /> {activePlan.chapter}</span>
              <span className="lp-time"><Clock size={13} /> {activePlan.duration}</span>
            </div>
            <h3>5E Pedagogical Instructional Plan</h3>
            <p className="lp-sub">Standardized instructional structure aligning with National Education Policy (NEP) &amp; CBSE Standards.</p>
          </div>

          <div className="lp-objectives-grid">
            <div className="objective-box">
              <strong><Award size={15} className="text-orange" /> Core Learning Objectives:</strong>
              <ul>
                {activePlan.learningObjectives.map((obj, i) => (
                  <li key={i}>{obj}</li>
                ))}
              </ul>
            </div>
            <div className="objective-box">
              <strong><ListChecks size={15} className="text-orange" /> Prior Concepts &amp; Board Focus:</strong>
              <ul>
                {activePlan.boardQuestions.map((q, i) => (
                  <li key={i}>{q}</li>
                ))}
              </ul>
            </div>
          </div>

          <div className="phases-table-wrap">
            <h4 className="phases-title">5E Instructional Phases &amp; Class Flow</h4>
            <table className="classroom-table phases-table">
              <thead>
                <tr>
                  <th style={{ width: '110px' }}>Phase</th>
                  <th style={{ width: '80px' }}>Time</th>
                  <th>Classroom Activity &amp; Demonstration</th>
                  <th>Teacher Role</th>
                  <th>Student Role</th>
                </tr>
              </thead>
              <tbody>
                {activePlan.phases.map((ph, idx) => (
                  <tr key={idx}>
                    <td><strong className="phase-name-badge">{ph.phase}</strong></td>
                    <td><span className="time-tag">{ph.durationMinutes} mins</span></td>
                    <td>{ph.activity}</td>
                    <td className="role-text">{ph.teacherRole}</td>
                    <td className="role-text">{ph.studentRole}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="homework-callout-box">
            <strong>Assigned Practice &amp; Homework:</strong>
            <p>{activePlan.homework}</p>
          </div>
        </div>
      )}

      {/* Tab 2: Customizable Worksheet */}
      {activeTab === 'worksheets' && (
        <div className="figma-dash-card worksheet-card">
          <div className="worksheet-header-row">
            <div>
              <span className="lp-tag">{activeWorksheet.chapter}</span>
              <h3>{activeWorksheet.title}</h3>
              <span className="meta-tag">Total Marks: {activeWorksheet.totalMarks} • Time: {activeWorksheet.timeAllowed}</span>
            </div>
          </div>

          <div className="worksheet-questions-list">
            {activeWorksheet.questions.map((q, idx) => (
              <div key={q.id} className="worksheet-q-box">
                <div className="wq-header">
                  <strong>Question {idx + 1} ({q.type})</strong>
                  <span className="marks-pill">{q.marks} Marks</span>
                </div>
                <p className="wq-text">{q.question}</p>

                {q.options && (
                  <div className="wq-options-grid">
                    {q.options.map((opt, oi) => (
                      <div key={oi} className="wq-opt-pill">{opt}</div>
                    ))}
                  </div>
                )}

                <div className="wq-solution-box">
                  <div className="sol-heading"><CheckCircle size={14} /> Teacher Answer Key &amp; Solution:</div>
                  <p>{q.solution}</p>
                  <span className="marking-rule">Guide: {q.markingGuide}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 3: Step Rubric Builder */}
      {activeTab === 'rubrics' && (
        <div className="figma-dash-card rubric-builder-card">
          <div className="lesson-plan-header-box">
            <span className="lp-tag">{activeRubric.chapter}</span>
            <h3>{activeRubric.title}</h3>
            <p className="lp-sub">Step-by-step point distribution matrix used by the AI grading engine for objective evaluation.</p>
          </div>

          <table className="classroom-table rubric-matrix-table">
            <thead>
              <tr>
                <th style={{ width: '220px' }}>Evaluation Criterion</th>
                <th style={{ width: '90px' }}>Max Marks</th>
                <th>Exemplary (Full Marks)</th>
                <th>Proficient (Partial Marks)</th>
                <th>Developing (Minimal Marks)</th>
              </tr>
            </thead>
            <tbody>
              {activeRubric.criteria.map((rc) => (
                <tr key={rc.id}>
                  <td><strong>{rc.criterion}</strong></td>
                  <td><span className="marks-pill">{rc.maxMarks} M</span></td>
                  <td className="rubric-cell-good">{rc.excellent}</td>
                  <td className="rubric-cell-mid">{rc.proficient}</td>
                  <td className="rubric-cell-low">{rc.developing}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
