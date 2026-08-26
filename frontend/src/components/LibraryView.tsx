import { useState } from 'react';
import {
  BookOpen,
  Search,
  Sparkles,
  Plus,
  FileQuestion,
  Bookmark
} from 'lucide-react';
import type { TeacherUser } from '../types/user';

type LibraryViewProps = {
  user: TeacherUser;
  onUseQuestionInExam?: () => void;
};

type QuestionBankItem = {
  id: string;
  chapter: string;
  questionText: string;
  marks: number;
  difficulty: 'Easy' | 'Medium' | 'Hard';
  boardType: string;
  rubric: string;
};

const SAMPLE_QUESTIONS: QuestionBankItem[] = [
  {
    id: 'qb-1',
    chapter: 'Electricity & Circuits',
    questionText: "State Ohm's Law and write its mathematical formula with temperature condition.",
    marks: 5,
    difficulty: 'Medium',
    boardType: 'CBSE Class 10 Standard',
    rubric: '1M for statement, 1M for temperature condition, 1M for V=IR formula, 2M for circuit diagram.'
  },
  {
    id: 'qb-2',
    chapter: 'Electricity & Circuits',
    questionText: 'Derive the formula for equivalent resistance when three resistors are connected in parallel.',
    marks: 5,
    difficulty: 'Hard',
    boardType: 'CBSE Class 10 Standard',
    rubric: '1M for circuit diagram, 2M for current addition I=I1+I2+I3, 2M for substitution and 1/Rp equation.'
  },
  {
    id: 'qb-3',
    chapter: 'Magnetic Effects of Current',
    questionText: "State Fleming's Left-Hand Rule and mention its application in electric motors.",
    marks: 3,
    difficulty: 'Easy',
    boardType: 'CBSE Class 10 Standard',
    rubric: '1M each for Thumb (Force), Forefinger (Magnetic field), Middle finger (Current).'
  },
  {
    id: 'qb-4',
    chapter: 'Chemical Reactions & Equations',
    questionText: 'Write a balanced chemical equation for the reaction between iron and steam, stating oxidation states.',
    marks: 3,
    difficulty: 'Medium',
    boardType: 'CBSE Class 10 Standard',
    rubric: '2M for 3Fe + 4H2O -> Fe3O4 + 4H2, 1M for correct physical states (s, g).'
  },
  {
    id: 'qb-5',
    chapter: 'Light — Reflection & Refraction',
    questionText: 'A concave mirror produces three times magnified real image of an object placed at 10cm. Find focal length.',
    marks: 5,
    difficulty: 'Hard',
    boardType: 'CBSE Class 10 Standard',
    rubric: '1M for magnification m=-v/u=-3, 2M for v=-30cm, 2M for mirror formula 1/f = 1/v + 1/u -> f=-7.5cm.'
  }
];

export default function LibraryView({ user, onUseQuestionInExam }: LibraryViewProps) {
  const [selectedChapter, setSelectedChapter] = useState('All');
  const [selectedDifficulty, setSelectedDifficulty] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedItem, setSelectedItem] = useState<QuestionBankItem | null>(SAMPLE_QUESTIONS[0]);

  const chapters = ['All', 'Electricity & Circuits', 'Magnetic Effects of Current', 'Chemical Reactions & Equations', 'Light — Reflection & Refraction'];

  const filtered = SAMPLE_QUESTIONS.filter(q => {
    const matchChap = selectedChapter === 'All' || q.chapter === selectedChapter;
    const matchDiff = selectedDifficulty === 'All' || q.difficulty === selectedDifficulty;
    const matchSearch = q.questionText.toLowerCase().includes(searchQuery.toLowerCase()) || q.chapter.toLowerCase().includes(searchQuery.toLowerCase());
    return matchChap && matchDiff && matchSearch;
  });

  return (
    <div className="library-view-wrapper">
      {/* Library Top Bar */}
      <div className="library-header-bar">
        <div>
          <h2>CBSE &amp; ICSE Question Bank &amp; Rubrics</h2>
          <span className="school-subhead">
            <BookOpen size={15} /> Standardized Examination Questions for {user.subject}
          </span>
        </div>

        <div className="library-actions-row">
          <button className="primary-action-btn" onClick={() => alert('Rubric Builder activated.')} type="button">
            <Sparkles size={16} /> Generate AI Rubric
          </button>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="library-filters-bar">
        <div className="search-input-wrap">
          <Search size={16} className="search-icon" />
          <input
            type="text"
            placeholder="Search question bank by keyword, topic, or concept..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="filter-selects-row">
          <select
            className="form-select mini"
            value={selectedChapter}
            onChange={(e) => setSelectedChapter(e.target.value)}
          >
            {chapters.map(c => <option key={c} value={c}>{c}</option>)}
          </select>

          <select
            className="form-select mini"
            value={selectedDifficulty}
            onChange={(e) => setSelectedDifficulty(e.target.value)}
          >
            <option value="All">All Difficulties</option>
            <option value="Easy">Easy</option>
            <option value="Medium">Medium</option>
            <option value="Hard">Hard</option>
          </select>
        </div>
      </div>

      {/* Split Library Layout */}
      <div className="library-split-layout">
        {/* Left: Questions List */}
        <div className="library-questions-list">
          {filtered.map((item) => {
            const isSelected = selectedItem?.id === item.id;
            const diffClass = item.difficulty === 'Easy' ? 'diff-green' : item.difficulty === 'Medium' ? 'diff-yellow' : 'diff-red';

            return (
              <div
                key={item.id}
                className={'library-q-card ' + (isSelected ? 'selected' : '')}
                onClick={() => setSelectedItem(item)}
              >
                <div className="q-card-header">
                  <span className="chapter-tag">{item.chapter}</span>
                  <div className="badge-group">
                    <span className={'diff-pill ' + diffClass}>{item.difficulty}</span>
                    <span className="marks-pill">{item.marks} Marks</span>
                  </div>
                </div>
                <p className="q-text-content">{item.questionText}</p>
                <div className="q-card-footer">
                  <span className="board-label">{item.boardType}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Right: Rubric & Model Solution Preview */}
        <div className="library-detail-panel">
          {selectedItem ? (
            <div className="rubric-detail-card">
              <div className="detail-header">
                <div className="detail-topic-badge">
                  <Bookmark size={14} /> {selectedItem.chapter}
                </div>
                <h3>{selectedItem.questionText}</h3>
                <div className="detail-meta-tags">
                  <span className="meta-tag">{selectedItem.marks} Marks</span>
                  <span className="meta-tag">Difficulty: {selectedItem.difficulty}</span>
                  <span className="meta-tag">Board: {selectedItem.boardType}</span>
                </div>
              </div>

              <div className="rubric-content-box">
                <div className="rubric-title-row">
                  <Sparkles size={16} className="text-orange" />
                  <strong>Official AI Marking Scheme &amp; Step-by-step Rubric</strong>
                </div>
                <p className="rubric-text-body">{selectedItem.rubric}</p>
              </div>

              <div className="detail-actions-row">
                <button
                  className="primary-action-btn full-width"
                  onClick={() => {
                    alert('Question added to upcoming exam assessment.');
                    if (onUseQuestionInExam) onUseQuestionInExam();
                  }}
                  type="button"
                >
                  <Plus size={16} /> Use Question in Assessment
                </button>
              </div>
            </div>
          ) : (
            <div className="empty-detail-placeholder">
              <FileQuestion size={36} className="text-muted" />
              <p>Select a question from the repository to view its step-by-step marking rubric.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
