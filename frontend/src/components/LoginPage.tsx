import { useState } from 'react';
import {
  GraduationCap,
  Sparkles,
  Lock,
  Mail,
  Building2,
  BookOpen,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  HelpCircle,
  Eye,
  EyeOff
} from 'lucide-react';
import { DEFAULT_SCHOOLS, DEFAULT_USER, type TeacherUser } from '../types/user';

type LoginPageProps = {
  onLoginSuccess: (user: TeacherUser) => void;
};

export default function LoginPage({ onLoginSuccess }: LoginPageProps) {
  const [selectedSchoolId, setSelectedSchoolId] = useState<string>(DEFAULT_SCHOOLS[0].id);
  const [email, setEmail] = useState('madhur.rastogi@dpsbokaro.edu.in');
  const [password, setPassword] = useState('••••••••••••');
  const [showPassword, setShowPassword] = useState(false);
  const [teacherName, setTeacherName] = useState('Madhur Rastogi');
  const [subject, setSubject] = useState('Class 10 Science (Physics & Chemistry)');
  const [rememberMe, setRememberMe] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const selectedSchool = DEFAULT_SCHOOLS.find(s => s.id === selectedSchoolId) || DEFAULT_SCHOOLS[0];

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please fill in your teacher credentials.');
      return;
    }

    setLoading(true);
    setError('');

    setTimeout(() => {
      const user: TeacherUser = {
        id: 'teacher-' + Date.now(),
        name: teacherName.trim() || 'Educator',
        email: email.trim(),
        role: 'Senior Science Educator',
        subject: subject,
        gradeLevels: ['Class 9', 'Class 10'],
        school: selectedSchool,
        gradingStrictness: 'balanced',
        aiModel: 'Gemini 3.6 Flash'
      };

      onLoginSuccess(user);
      setLoading(false);
    }, 600);
  };

  const handleQuickDemoLogin = () => {
    setLoading(true);
    setTimeout(() => {
      onLoginSuccess(DEFAULT_USER);
      setLoading(false);
    }, 400);
  };

  return (
    <div className="login-page-wrapper">
      <div className="login-container-card">
        {/* Left Hero & School Branding Column */}
        <div className="login-left-brand-col">
          <div className="brand-top-row">
            <div className="veda-logo-mark large">V</div>
            <div className="brand-titles">
              <span className="veda-brand-text light">VedaAI</span>
              <span className="veda-tagline">AI Teacher's Evaluation Suite</span>
            </div>
          </div>

          <div className="login-hero-pitch">
            <h2>Evaluate Handwritten Answer Sheets in Seconds</h2>
            <p>
              Autonomous question paper parsing, student handwriting OCR, 
              deterministic question mapping, and AI-assisted rubric grading for modern schools.
            </p>

            <div className="brand-features-list">
              <div className="feature-item">
                <CheckCircle2 size={18} className="text-orange-light" />
                <span>Multi-page answer sheet bounding box detection</span>
              </div>
              <div className="feature-item">
                <CheckCircle2 size={18} className="text-orange-light" />
                <span>Deterministic 3-pass question-answer matching</span>
              </div>
              <div className="feature-item">
                <CheckCircle2 size={18} className="text-orange-light" />
                <span>Curriculum-aligned constructive AI feedback</span>
              </div>
              <div className="feature-item">
                <CheckCircle2 size={18} className="text-orange-light" />
                <span>Comprehensive batch learning gap analytics</span>
              </div>
            </div>
          </div>

          {/* Active School Badge */}
          <div className="login-school-banner">
            <div className="school-crest-box">
              <GraduationCap size={22} className="text-white" />
            </div>
            <div className="school-banner-info">
              <span className="affiliation-tag">{selectedSchool.board} Affiliated School • Aff. No. {selectedSchool.affiliationNumber}</span>
              <strong>{selectedSchool.name}</strong>
              <span className="school-city">{selectedSchool.location}</span>
            </div>
          </div>

          <div className="login-footer-security">
            <ShieldCheck size={16} />
            <span>Institutional-Grade AES-256 Data Protection &amp; Student Privacy</span>
          </div>
        </div>

        {/* Right Authentication Form Column */}
        <div className="login-right-form-col">
          <div className="login-form-header">
            <span className="portal-badge">
              <Sparkles size={13} className="text-orange" /> Teacher Portal Access
            </span>
            <h1 className="login-title">Sign In to Your Workspace</h1>
            <p className="login-subtitle">Select your school institution and educator profile</p>
          </div>

          {error && (
            <div className="login-error-alert">
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleLogin} className="login-form">
            {/* School Selector */}
            <div className="form-group">
              <label className="form-label">
                <Building2 size={15} /> Educational Institution / School
              </label>
              <select
                className="form-select"
                value={selectedSchoolId}
                onChange={(e) => setSelectedSchoolId(e.target.value)}
              >
                {DEFAULT_SCHOOLS.map((school) => (
                  <option key={school.id} value={school.id}>
                    {school.name} — {school.location} ({school.board})
                  </option>
                ))}
              </select>
            </div>

            {/* Teacher Name & Subject Row */}
            <div className="form-row-dual">
              <div className="form-group">
                <label className="form-label">
                  <GraduationCap size={15} /> Educator Name
                </label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Madhur Rastogi"
                  value={teacherName}
                  onChange={(e) => setTeacherName(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">
                  <BookOpen size={15} /> Subject &amp; Grade
                </label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Class 10 Science"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  required
                />
              </div>
            </div>

            {/* Email Address */}
            <div className="form-group">
              <label className="form-label">
                <Mail size={15} /> Institutional Email Address
              </label>
              <input
                type="email"
                className="form-input"
                placeholder="educator@school.edu.in"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            {/* Password */}
            <div className="form-group">
              <label className="form-label">
                <Lock size={15} /> Security Password
              </label>
              <div className="input-password-wrap">
                <input
                  type={showPassword ? "text" : "password"}
                  className="form-input"
                  placeholder="Enter password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  className="password-toggle-btn"
                  onClick={() => setShowPassword(!showPassword)}
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* Options Row */}
            <div className="form-options-row">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                />
                <span>Remember session</span>
              </label>
              <button type="button" className="forgot-pwd-link" onClick={() => alert('Password reset link sent to your institutional email.')}>
                Forgot password?
              </button>
            </div>

            {/* Action Buttons */}
            <button
              type="submit"
              className="login-submit-btn"
              disabled={loading}
            >
              {loading ? (
                <span>Signing in...</span>
              ) : (
                <>
                  <span>Enter Assessment Dashboard</span>
                  <ArrowRight size={18} />
                </>
              )}
            </button>

            <div className="login-divider">
              <span>OR FOR QUICK EVALUATION</span>
            </div>

            <button
              type="button"
              className="demo-oneclick-btn"
              onClick={handleQuickDemoLogin}
              disabled={loading}
            >
              <Sparkles size={16} className="text-orange" />
              <span>1-Click Educator Demo Access (Delhi Public School)</span>
            </button>
          </form>

          <div className="login-support-note">
            <HelpCircle size={14} />
            <span>Need help setting up your classroom? Contact IT Admin or support@vedaai.org</span>
          </div>
        </div>
      </div>
    </div>
  );
}
