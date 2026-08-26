import { useState } from 'react';
import {
  FileCheck,
  FileQuestion,
  FileText,
  HelpCircle,
  Layers,
  Sparkles,
  X,
  Zap,
  Building2,
  CheckCircle,
  Plus,
  BookOpen,
  Sliders,
  Users
} from 'lucide-react';
import type { SchoolProfile } from '../types/user';

export function PlaceholderView({ title, desc, onGoToExams }: { title: string; desc: string; onGoToExams: () => void }) {
  return (
    <div className="placeholder-view">
      <div className="placeholder-card">
        <div className="placeholder-icon-ring">
          <Layers size={32} className="text-orange" />
        </div>
        <h2>{title}</h2>
        <p>{desc}</p>
        <button className="primary-action-btn" onClick={onGoToExams} type="button">
          <FileText size={16} /> Open Assessment Analyzer (Exams)
        </button>
      </div>
    </div>
  );
}

export function HelpModal({ onClose, onOpenExams, onOpenStudio }: { onClose: () => void; onOpenExams?: () => void; onOpenStudio?: () => void }) {
  const [activeHelpTab, setActiveHelpTab] = useState<'flow' | 'rubric' | 'batch' | 'faq'>('flow');

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card help-modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-header-left">
            <HelpCircle size={22} className="text-orange" />
            <div>
              <strong>VedaAI Educator Guide &amp; Knowledge Base</strong>
              <span className="modal-sub">How Automated Handwritten OCR &amp; Diagnostic Grading Works</span>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose} type="button" title="Close">
            <X size={18} />
          </button>
        </div>

        {/* Modal Subtabs */}
        <div className="modal-subtabs-row">
          <button
            type="button"
            className={'modal-subtab-btn ' + (activeHelpTab === 'flow' ? 'active' : '')}
            onClick={() => setActiveHelpTab('flow')}
          >
            3-Step Workflow
          </button>
          <button
            type="button"
            className={'modal-subtab-btn ' + (activeHelpTab === 'rubric' ? 'active' : '')}
            onClick={() => setActiveHelpTab('rubric')}
          >
            CBSE Rubric Grading
          </button>
          <button
            type="button"
            className={'modal-subtab-btn ' + (activeHelpTab === 'batch' ? 'active' : '')}
            onClick={() => setActiveHelpTab('batch')}
          >
            Batch Evaluation
          </button>
          <button
            type="button"
            className={'modal-subtab-btn ' + (activeHelpTab === 'faq' ? 'active' : '')}
            onClick={() => setActiveHelpTab('faq')}
          >
            FAQs &amp; Tips
          </button>
        </div>

        <div className="modal-body help-modal-body">
          {activeHelpTab === 'flow' && (
            <div className="guide-steps-list">
              <div className="guide-step">
                <div className="step-num">1</div>
                <div>
                  <strong>Upload Question Paper &amp; Student Sheets</strong>
                  <p>Upload printed or digital PDF/Image Question Paper and one or multiple student handwritten answer sheets.</p>
                </div>
              </div>
              <div className="guide-step">
                <div className="step-num">2</div>
                <div>
                  <strong>Deterministic Layout Extraction &amp; Mapping</strong>
                  <p>Gemini Vision multimodal models identify question numbers, text boundaries, and normalize question-to-answer linkages.</p>
                </div>
              </div>
              <div className="guide-step">
                <div className="step-num">3</div>
                <div>
                  <strong>Live Visual Bounding Box &amp; Score Feedback</strong>
                  <p>Click any question to highlight the exact handwriting region in green on the student's paper, accompanied by constructive marks feedback.</p>
                </div>
              </div>
            </div>
          )}

          {activeHelpTab === 'rubric' && (
            <div className="help-rubric-box">
              <h4>CBSE Standardized Step-by-Step Marking</h4>
              <p>The AI evaluator parses formula identification (1M), substitution &amp; steps (2M), and final answer with SI units (1M).</p>
              <div className="rubric-points-grid">
                <div className="rubric-point">
                  <strong className="text-green">Green Score Pill (≥80%)</strong>
                  <span>Mastery of core concepts and complete derivations.</span>
                </div>
                <div className="rubric-point">
                  <strong className="text-orange">Orange Score Pill (40–79%)</strong>
                  <span>Partial credit awarded for valid intermediate steps.</span>
                </div>
                <div className="rubric-point">
                  <strong className="text-red">Red Score Pill (&lt;40%)</strong>
                  <span>Misconceptions or unanswered question regions.</span>
                </div>
              </div>
            </div>
          )}

          {activeHelpTab === 'batch' && (
            <div className="help-rubric-box">
              <h4>Multi-Student Batch Evaluation</h4>
              <p>You can drag-and-drop 10+ student answer sheets simultaneously. The platform processes each sheet against the question paper and aggregates class-wide learning gaps, average scores, and student grade segmentation (A/B/C/D).</p>
              <div className="tip-box">
                <Sparkles size={16} className="text-orange" />
                <span>Tip: You can edit student names inline before clicking Start Batch Grading!</span>
              </div>
            </div>
          )}

          {activeHelpTab === 'faq' && (
            <div className="faq-list">
              <div className="faq-item">
                <strong>What file formats are supported?</strong>
                <p>PDF (multi-page documents up to 15 pages), PNG, JPG, and WEBP files up to 10MB each.</p>
              </div>
              <div className="faq-item">
                <strong>Can I print and export official evaluation reports?</strong>
                <p>Yes! Click "Export PDF Report" on any evaluated student sheet to generate a print-ready school document.</p>
              </div>
            </div>
          )}
        </div>

        <div className="modal-footer flex-right">
          {onOpenStudio && (
            <button
              className="secondary-btn"
              onClick={() => {
                onClose();
                onOpenStudio();
              }}
              type="button"
            >
              <BookOpen size={14} /> Open Studio
            </button>
          )}
          {onOpenExams && (
            <button
              className="primary-action-btn"
              onClick={() => {
                onClose();
                onOpenExams();
              }}
              type="button"
            >
              <FileCheck size={14} /> Start Assessment OCR
            </button>
          )}
          {!onOpenExams && (
            <button className="primary-action-btn full-width" onClick={onClose} type="button">
              Got it, continue
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export function ToolkitModal({
  onClose,
  onGoToExams,
  onGoToLibrary,
  onGoToAssignments,
  onGoToClassroom,
  onGoToSettings
}: {
  onClose: () => void;
  onGoToExams: () => void;
  onGoToLibrary: () => void;
  onGoToAssignments: () => void;
  onGoToClassroom?: () => void;
  onGoToSettings?: () => void;
}) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card toolkit-modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-header-left">
            <Sparkles size={22} className="text-orange" />
            <div>
              <strong>AI Teacher's Toolkit</strong>
              <span className="modal-sub">Launch specialized academic assistance tools</span>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose} type="button" title="Close">
            <X size={18} />
          </button>
        </div>

        <div className="toolkit-grid">
          <div
            className="toolkit-item active-tool"
            onClick={() => {
              onClose();
              onGoToExams();
            }}
          >
            <div className="toolkit-icon"><FileCheck size={22} /></div>
            <div className="toolkit-info">
              <strong>Assessment Analyzer &amp; OCR Mapper</strong>
              <p>Upload Question Paper &amp; Student Sheets for automated grading and visual bounding box matching.</p>
              <span className="tool-cta">Launch Tool →</span>
            </div>
          </div>

          <div
            className="toolkit-item"
            onClick={() => {
              onClose();
              onGoToLibrary();
            }}
          >
            <div className="toolkit-icon"><BookOpen size={22} /></div>
            <div className="toolkit-info">
              <strong>5E Lesson Plan Architect</strong>
              <p>Generate structured NEP/CBSE aligned instructional lesson plans with classroom activities.</p>
              <span className="tool-cta">Open Studio →</span>
            </div>
          </div>

          <div
            className="toolkit-item"
            onClick={() => {
              onClose();
              onGoToLibrary();
            }}
          >
            <div className="toolkit-icon"><FileQuestion size={22} /></div>
            <div className="toolkit-info">
              <strong>Curriculum Question Bank &amp; Rubrics</strong>
              <p>Explore chapter-wise CBSE questions with step-by-step point distribution rubrics.</p>
              <span className="tool-cta">Explore Bank →</span>
            </div>
          </div>

          <div
            className="toolkit-item"
            onClick={() => {
              onClose();
              onGoToAssignments();
            }}
          >
            <div className="toolkit-icon"><Zap size={22} /></div>
            <div className="toolkit-info">
              <strong>Learning Gap Diagnostic Assistant</strong>
              <p>Identify common student misconceptions, section comparisons, and remediation action items.</p>
              <span className="tool-cta">View Analytics →</span>
            </div>
          </div>

          {onGoToClassroom && (
            <div
              className="toolkit-item"
              onClick={() => {
                onClose();
                onGoToClassroom();
              }}
            >
              <div className="toolkit-icon"><Users size={22} /></div>
              <div className="toolkit-info">
                <strong>Classroom Student Roster &amp; Archives</strong>
                <p>Manage student profiles, view past graded exam archives, and track attendance.</p>
                <span className="tool-cta">Manage Class →</span>
              </div>
            </div>
          )}

          {onGoToSettings && (
            <div
              className="toolkit-item"
              onClick={() => {
                onClose();
                onGoToSettings();
              }}
            >
              <div className="toolkit-icon"><Sliders size={22} /></div>
              <div className="toolkit-info">
                <strong>AI Strictness &amp; School Settings</strong>
                <p>Customize grading strictness (Strict/Balanced/Lenient) and manage institution credentials.</p>
                <span className="tool-cta">Configure →</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function AddSchoolModal({
  onClose,
  onSave
}: {
  onClose: () => void;
  onSave: (school: SchoolProfile) => void;
}) {
  const [name, setName] = useState('');
  const [location, setLocation] = useState('');
  const [board, setBoard] = useState('CBSE');
  const [affiliationNumber, setAffiliationNumber] = useState('');
  const [code, setCode] = useState('');
  const [principalName, setPrincipalName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      alert('Please enter a School Name.');
      return;
    }
    const computedCode = code.trim() || name.split(' ').map(w => w[0]).join('').slice(0, 4).toUpperCase();
    const newSchool: SchoolProfile = {
      id: 'custom-' + Date.now(),
      name: name.trim(),
      location: location.trim() || 'Main Campus',
      board: board.trim(),
      affiliationNumber: affiliationNumber.trim() || 'N/A',
      code: computedCode,
      principalName: principalName.trim(),
      email: email.trim(),
      phone: phone.trim(),
      isCustom: true
    };
    onSave(newSchool);
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card add-school-modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-header-left">
            <Building2 size={22} className="text-orange" />
            <div>
              <strong>Add New Educational Institution</strong>
              <span className="modal-sub">Create and activate your custom school profile</span>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose} type="button" title="Close">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="add-school-form">
          <div className="modal-body">
            <div className="form-grid-2">
              <div className="form-field">
                <label className="field-label">School / Institution Name *</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. St. Xavier's Senior Secondary School"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>

              <div className="form-field">
                <label className="field-label">Campus Location / Branch *</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Sector 4, Bokaro Steel City"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="form-grid-3">
              <div className="form-field">
                <label className="field-label">Affiliation Board</label>
                <select
                  className="form-select"
                  value={board}
                  onChange={(e) => setBoard(e.target.value)}
                >
                  <option value="CBSE">CBSE (Central Board)</option>
                  <option value="ICSE">ICSE / ISC (CISCE)</option>
                  <option value="State Board">State Board</option>
                  <option value="IB">International Baccalaureate (IB)</option>
                  <option value="Cambridge">Cambridge International (CIE)</option>
                </select>
              </div>

              <div className="form-field">
                <label className="field-label">Board Affiliation No.</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. 3430155"
                  value={affiliationNumber}
                  onChange={(e) => setAffiliationNumber(e.target.value)}
                />
              </div>

              <div className="form-field">
                <label className="field-label">School Code (Prefix)</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. SXS"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                />
              </div>
            </div>

            <div className="form-grid-3">
              <div className="form-field">
                <label className="field-label">Principal / HOD Name</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Dr. Anirudh Sen"
                  value={principalName}
                  onChange={(e) => setPrincipalName(e.target.value)}
                />
              </div>

              <div className="form-field">
                <label className="field-label">Institutional Email</label>
                <input
                  type="email"
                  className="form-input"
                  placeholder="contact@school.edu.in"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>

              <div className="form-field">
                <label className="field-label">Contact Phone</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="+91 6542 245 889"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                />
              </div>
            </div>
          </div>

          <div className="modal-footer flex-right">
            <button className="secondary-btn" onClick={onClose} type="button">
              Cancel
            </button>
            <button className="primary-action-btn" type="submit">
              <CheckCircle size={16} /> Save &amp; Activate School
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function AddStudentModal({
  onClose,
  onAdd
}: {
  onClose: () => void;
  onAdd: (student: { name: string; rollNo: string; section: string }) => void;
}) {
  const [name, setName] = useState('');
  const [rollNo, setRollNo] = useState('');
  const [section, setSection] = useState('Section A');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    onAdd({
      name: name.trim(),
      rollNo: rollNo.trim() || '10A-99',
      section
    });
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card small-modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-header-left">
            <Users size={20} className="text-orange" />
            <strong>Enroll New Student</strong>
          </div>
          <button className="modal-close-btn" onClick={onClose} type="button" title="Close">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="form-field">
              <label className="field-label">Student Full Name *</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. Aryan Sengupta"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
            <div className="form-field" style={{ marginTop: '12px' }}>
              <label className="field-label">Roll Number *</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. 10A-07"
                value={rollNo}
                onChange={(e) => setRollNo(e.target.value)}
                required
              />
            </div>
            <div className="form-field" style={{ marginTop: '12px' }}>
              <label className="field-label">Class Section</label>
              <select
                className="form-select"
                value={section}
                onChange={(e) => setSection(e.target.value)}
              >
                <option value="Section A">Class 10 — Section A</option>
                <option value="Section B">Class 10 — Section B</option>
              </select>
            </div>
          </div>
          <div className="modal-footer flex-right">
            <button className="secondary-btn" onClick={onClose} type="button">Cancel</button>
            <button className="primary-action-btn" type="submit"><Plus size={16} /> Add to Roster</button>
          </div>
        </form>
      </div>
    </div>
  );
}

