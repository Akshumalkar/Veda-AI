import {
  FileText,
  TrendingUp,
  Award,
  Users,
  Clock,
  CheckCircle,
  ArrowUpRight,
  Plus,
  BarChart2,
  BookOpen
} from 'lucide-react';
import type { TeacherUser } from '../types/user';

type HomeDashboardProps = {
  user: TeacherUser;
  assessmentHistory?: any[];
  onGoToExams: () => void;
  onGoToAssignments: () => void;
  onGoToClassroom: () => void;
};

export default function HomeDashboard({
  user,
  onGoToExams,
  onGoToAssignments,
  onGoToClassroom
}: HomeDashboardProps) {
  const recentAssessments = [
    {
      id: 'exam-1',
      title: 'Class 10 - Physics Mid-Term Unit Test',
      subject: 'Science (Electricity & Magnetism)',
      section: 'Section A & B',
      date: 'Today, 2:30 PM',
      submissions: '45/50',
      avgScore: '82%',
      status: 'Evaluated'
    },
    {
      id: 'exam-2',
      title: 'Class 10 - Chemistry Periodic Assessment',
      subject: 'Science (Acids, Bases & Salts)',
      section: 'Section A',
      date: 'Yesterday',
      submissions: '28/30',
      avgScore: '76%',
      status: 'Evaluated'
    },
    {
      id: 'exam-3',
      title: 'Class 9 - Motion & Force Practice Paper',
      subject: 'Physics',
      section: 'Section C',
      date: 'Aug 24, 2026',
      submissions: '32/32',
      avgScore: '88%',
      status: 'Evaluated'
    }
  ];

  return (
    <div className="home-dashboard-wrapper">
      {/* Welcome Banner */}
      <div className="home-welcome-card">
        <div className="welcome-text-col">
          <div className="school-context-pill">
            <span>{user.school.name} • {user.school.location}</span>
          </div>
          <h1>Welcome back, {user.name} 👋</h1>
          <p className="welcome-sub">
            Your AI-assisted evaluation engine is active with <strong>Gemini 3.6 Flash</strong>. 
            All assessments are mapped with strict bounding box accuracy.
          </p>

          <div className="welcome-cta-row">
            <button className="primary-action-btn" onClick={onGoToExams} type="button">
              <Plus size={16} /> Upload New Exam Paper
            </button>
            <button className="secondary-action-btn" onClick={onGoToAssignments} type="button">
              <BarChart2 size={16} /> View Learning Gaps
            </button>
          </div>
        </div>

        <div className="welcome-stats-badge-card">
          <div className="badge-header">
            <Award size={18} className="text-orange" />
            <span>Academic Performance Index</span>
          </div>
          <div className="badge-metric">82.4%</div>
          <div className="badge-sub">+4.2% improvement vs Term 1 Baseline</div>
          <div className="badge-progress-bar">
            <div className="badge-progress-fill" style={{ width: '82.4%' }} />
          </div>
        </div>
      </div>

      {/* 4 Metric Tiles Grid */}
      <div className="home-metrics-grid">
        <div className="metric-card">
          <div className="metric-icon-wrap orange">
            <FileText size={20} />
          </div>
          <div className="metric-content">
            <span className="metric-label">Papers Evaluated</span>
            <div className="metric-value-row">
              <strong className="metric-number">128</strong>
              <span className="metric-badge-trend positive">
                <TrendingUp size={12} /> +12 this wk
              </span>
            </div>
            <span className="metric-hint">Across 4 sections</span>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon-wrap green">
            <CheckCircle size={20} />
          </div>
          <div className="metric-content">
            <span className="metric-label">Class Average Score</span>
            <div className="metric-value-row">
              <strong className="metric-number">82.0%</strong>
              <span className="metric-badge-trend positive">
                <TrendingUp size={12} /> +5.8%
              </span>
            </div>
            <span className="metric-hint">Top score: 95% (Ananya S.)</span>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon-wrap blue">
            <Users size={20} />
          </div>
          <div className="metric-content">
            <span className="metric-label">Active Students</span>
            <div className="metric-value-row">
              <strong className="metric-number">112</strong>
              <span className="metric-badge-trend neutral">
                Class 10 (A, B)
              </span>
            </div>
            <span className="metric-hint">42 student answer archives</span>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon-wrap purple">
            <Clock size={20} />
          </div>
          <div className="metric-content">
            <span className="metric-label">Teacher Time Saved</span>
            <div className="metric-value-row">
              <strong className="metric-number">18.5 hrs</strong>
              <span className="metric-badge-trend positive">
                ~85% faster
              </span>
            </div>
            <span className="metric-hint">Instant OCR &amp; rubric scoring</span>
          </div>
        </div>
      </div>

      {/* Dual Column Bottom Grid */}
      <div className="home-bottom-grid">
        {/* Left: Recent Assessments List */}
        <div className="figma-dash-card recent-assessments-card">
          <div className="card-header-flex">
            <div>
              <h3 className="card-title-plain">Recent Exam Evaluations</h3>
              <span className="card-sub-hint">Live graded student answer batches</span>
            </div>
            <button className="view-all-pill-btn" onClick={onGoToExams} type="button">
              Start Evaluation <ArrowUpRight size={13} />
            </button>
          </div>

          <div className="recent-list">
            {recentAssessments.map((exam) => (
              <div key={exam.id} className="recent-item-card">
                <div className="item-icon-col">
                  <div className="exam-type-icon">
                    <BookOpen size={16} />
                  </div>
                </div>
                <div className="item-info-col">
                  <strong className="exam-title-text">{exam.title}</strong>
                  <div className="exam-meta-row">
                    <span>{exam.subject}</span>
                    <span>•</span>
                    <span>{exam.section}</span>
                    <span>•</span>
                    <span>{exam.date}</span>
                  </div>
                </div>
                <div className="item-stats-col">
                  <div className="subm-count">{exam.submissions} Submissions</div>
                  <div className="score-badge-green">Avg {exam.avgScore}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Quick Action Shortcuts & Quick Guide */}
        <div className="home-right-column">
          <div className="figma-dash-card quick-tools-card">
            <h3 className="card-title-plain">Educator Toolkit Shortcuts</h3>
            <div className="quick-actions-stack">
              <button className="quick-tool-btn" onClick={onGoToExams} type="button">
                <div className="tool-icon-circle"><Plus size={16} /></div>
                <div className="tool-btn-text">
                  <strong>Evaluate Answer Sheet</strong>
                  <span>Upload Question Paper &amp; Student PDF</span>
                </div>
                <ArrowUpRight size={16} className="arrow-indicator" />
              </button>

              <button className="quick-tool-btn" onClick={onGoToAssignments} type="button">
                <div className="tool-icon-circle"><BarChart2 size={16} /></div>
                <div className="tool-btn-text">
                  <strong>Analyze Learning Gaps</strong>
                  <span>Concept-wise student difficulty breakdown</span>
                </div>
                <ArrowUpRight size={16} className="arrow-indicator" />
              </button>

              <button className="quick-tool-btn" onClick={onGoToClassroom} type="button">
                <div className="tool-icon-circle"><Users size={16} /></div>
                <div className="tool-btn-text">
                  <strong>My Classroom Roster</strong>
                  <span>Student answer sheets &amp; progress logs</span>
                </div>
                <ArrowUpRight size={16} className="arrow-indicator" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
