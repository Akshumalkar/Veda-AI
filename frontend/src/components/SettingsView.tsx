import { useState, useEffect } from 'react';
import {
  Cpu,
  Sliders,
  Save,
  CheckCircle,
  Building2,
  Plus,
  GraduationCap,
  Phone,
  Mail,
  Shield
} from 'lucide-react';
import { getAllSchools, saveCustomSchool, type SchoolProfile, type TeacherUser } from '../types/user';
import { AddSchoolModal } from './Modals';

type SettingsViewProps = {
  user: TeacherUser;
  onUpdateUser: (updated: TeacherUser) => void;
};

export default function SettingsView({ user, onUpdateUser }: SettingsViewProps) {
  const [schools, setSchools] = useState<SchoolProfile[]>([]);
  const [name, setName] = useState(user.name);
  const [email, setEmail] = useState(user.email);
  const [subject, setSubject] = useState(user.subject);
  const [selectedSchoolId, setSelectedSchoolId] = useState(user.school.id);
  const [strictness, setStrictness] = useState<'strict' | 'balanced' | 'lenient'>(user.gradingStrictness);
  const [aiModel, setAiModel] = useState(user.aiModel);
  const [autoMapThreshold, setAutoMapThreshold] = useState(45);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [isAddSchoolModalOpen, setIsAddSchoolModalOpen] = useState(false);

  useEffect(() => {
    setSchools(getAllSchools());
  }, []);

  const currentSchool = schools.find(s => s.id === selectedSchoolId) || user.school;

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    const updated: TeacherUser = {
      ...user,
      name,
      email,
      subject,
      school: currentSchool,
      gradingStrictness: strictness,
      aiModel
    };
    onUpdateUser(updated);
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  const handleAddNewSchool = (newSchool: SchoolProfile) => {
    const updatedSchools = saveCustomSchool(newSchool);
    setSchools(updatedSchools);
    setSelectedSchoolId(newSchool.id);

    const updatedUser: TeacherUser = {
      ...user,
      school: newSchool
    };
    onUpdateUser(updatedUser);
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  return (
    <div className="settings-view-wrapper">
      <div className="settings-header-bar">
        <div>
          <h2>Settings &amp; AI Engine Configuration</h2>
          <span className="school-subhead">
            <Sliders size={15} /> Customize OCR thresholds, evaluation strictness, and full institution details
          </span>
        </div>

        {savedSuccess && (
          <div className="save-toast-banner">
            <CheckCircle size={16} /> Preferences successfully updated &amp; synchronized
          </div>
        )}
      </div>

      <form onSubmit={handleSave} className="settings-grid-layout">
        {/* Left Column: AI Engine & Evaluation Rules */}
        <div className="settings-col">
          <div className="figma-dash-card">
            <div className="card-header-flex">
              <h3 className="card-title-plain">
                <Cpu size={16} className="text-orange" /> AI Evaluation Engine
              </h3>
            </div>

            <div className="settings-field-group">
              <label className="field-label">Active Generative Vision Model</label>
              <select
                className="form-select"
                value={aiModel}
                onChange={(e) => setAiModel(e.target.value)}
              >
                <option value="Gemini 3.6 Flash">Gemini 3.6 Flash (Recommended — Multimodal Handwriting OCR)</option>
                <option value="Gemini 2.5 Flash">Gemini 2.5 Flash (Fast Evaluation)</option>
                <option value="Gemini 1.5 Pro">Gemini 1.5 Pro (Deep Diagnostic Reasoning)</option>
              </select>
              <span className="field-hint">Uses high-resolution visual layout tokenization and bounding box detection.</span>
            </div>

            <div className="settings-field-group">
              <label className="field-label">Grading Strictness &amp; Rubric Alignment</label>
              <div className="strictness-pills-row">
                <button
                  type="button"
                  className={'strict-pill ' + (strictness === 'strict' ? 'active' : '')}
                  onClick={() => setStrictness('strict')}
                >
                  Strict CBSE
                </button>
                <button
                  type="button"
                  className={'strict-pill ' + (strictness === 'balanced' ? 'active' : '')}
                  onClick={() => setStrictness('balanced')}
                >
                  Balanced (Default)
                </button>
                <button
                  type="button"
                  className={'strict-pill ' + (strictness === 'lenient' ? 'active' : '')}
                  onClick={() => setStrictness('lenient')}
                >
                  Formative / Lenient
                </button>
              </div>
              <span className="field-hint">
                {strictness === 'strict' && 'Strict: Requires exact keyword match and complete derivations for full marks.'}
                {strictness === 'balanced' && 'Balanced: Evaluates conceptual understanding, allows minor phrasing variations.'}
                {strictness === 'lenient' && 'Lenient: Encourages effort and conceptual attempts with partial credit.'}
              </span>
            </div>

            <div className="settings-field-group">
              <div className="slider-header">
                <label className="field-label">Unnumbered Question Mapping Sensitivity</label>
                <strong className="slider-val">{autoMapThreshold}%</strong>
              </div>
              <input
                type="range"
                min="20"
                max="80"
                value={autoMapThreshold}
                onChange={(e) => setAutoMapThreshold(Number(e.target.value))}
                className="settings-range-slider"
              />
              <span className="field-hint">Jaccard semantic keyword threshold for matching unnumbered handwritten answers.</span>
            </div>
          </div>
        </div>

        {/* Right Column: School Institution & Educator Profile */}
        <div className="settings-col">
          <div className="figma-dash-card">
            <div className="card-header-flex">
              <h3 className="card-title-plain">
                <Building2 size={16} className="text-orange" /> Educational Institution &amp; Educator Profile
              </h3>
              <button
                type="button"
                className="add-custom-school-btn"
                onClick={() => setIsAddSchoolModalOpen(true)}
              >
                <Plus size={14} /> Add New School
              </button>
            </div>

            <div className="settings-field-group">
              <label className="field-label">Select Active Institution</label>
              <select
                className="form-select"
                value={selectedSchoolId}
                onChange={(e) => setSelectedSchoolId(e.target.value)}
              >
                {schools.map(s => (
                  <option key={s.id} value={s.id}>
                    {s.isCustom ? '⭐ [Custom] ' : ''}{s.name} — {s.location} ({s.board})
                  </option>
                ))}
              </select>
            </div>

            {/* Active School Badge Details Box */}
            <div className="active-school-details-card">
              <div className="school-details-top">
                <div className="school-crest-circle">{currentSchool.code || 'SCH'}</div>
                <div>
                  <strong>{currentSchool.name}</strong>
                  <span>{currentSchool.location} • {currentSchool.board} Affiliated</span>
                </div>
              </div>
              <div className="school-meta-tags-grid">
                <div className="sm-tag"><Shield size={12} /> Affiliation: {currentSchool.affiliationNumber}</div>
                {currentSchool.principalName && <div className="sm-tag"><GraduationCap size={12} /> Principal: {currentSchool.principalName}</div>}
                {currentSchool.email && <div className="sm-tag"><Mail size={12} /> {currentSchool.email}</div>}
                {currentSchool.phone && <div className="sm-tag"><Phone size={12} /> {currentSchool.phone}</div>}
              </div>
            </div>

            <div className="settings-field-group" style={{ marginTop: '14px' }}>
              <label className="field-label">Educator Full Name</label>
              <input
                type="text"
                className="form-input"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>

            <div className="settings-field-group">
              <label className="field-label">Institutional Email Address</label>
              <input
                type="email"
                className="form-input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="settings-field-group">
              <label className="field-label">Assigned Subject &amp; Grade Level</label>
              <input
                type="text"
                className="form-input"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                required
              />
            </div>

            <div className="save-btn-row">
              <button type="submit" className="primary-action-btn full-width">
                <Save size={16} /> Save All Preferences
              </button>
            </div>
          </div>
        </div>
      </form>

      {/* Add Custom School Modal */}
      {isAddSchoolModalOpen && (
        <AddSchoolModal
          onClose={() => setIsAddSchoolModalOpen(false)}
          onSave={handleAddNewSchool}
        />
      )}
    </div>
  );
}
