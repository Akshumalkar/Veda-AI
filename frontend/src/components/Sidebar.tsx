import {
  ChevronsRight,
  ChevronsLeft,
  FileText,
  GraduationCap,
  LayoutGrid,
  PieChart,
  Settings,
  Sparkles,
  Users,
  BookOpen,
} from 'lucide-react';

import type { SchoolProfile } from '../types/user';

type SidebarProps = {
  activeTab: string;
  onSelectTab: (t: string) => void;
  onOpenToolkit: () => void;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
  school?: SchoolProfile;
};

export default function Sidebar({
  activeTab,
  onSelectTab,
  onOpenToolkit,
  collapsed = false,
  onToggleCollapse,
  school
}: SidebarProps) {
  const schoolName = school?.name || 'Delhi Public School';
  const schoolLocation = school?.location || 'Bokaro Steel City';
  const schoolCode = school?.code || 'DPS';

  if (collapsed) {
    return (
      <aside className="veda-sidebar collapsed">
        <div className="veda-sidebar-top">
          <div className="veda-brand-icon" onClick={() => onSelectTab('exams')} title="VedaAI">
            <div className="veda-logo-mark">V</div>
          </div>

          <button className="veda-toolkit-icon-btn" onClick={onOpenToolkit} title="AI Teacher's Toolkit" type="button">
            <Sparkles size={16} />
          </button>

          <nav className="veda-nav-icons">
            <button
              className={'nav-icon-btn ' + (activeTab === 'home' ? 'active' : '')}
              onClick={() => onSelectTab('home')}
              title="Home Dashboard"
              type="button"
            >
              <LayoutGrid size={18} />
            </button>
            <button
              className={'nav-icon-btn ' + (activeTab === 'classroom' ? 'active' : '')}
              onClick={() => onSelectTab('classroom')}
              title="My Classroom"
              type="button"
            >
              <Users size={18} />
            </button>
            <button
              className={'nav-icon-btn ' + (activeTab === 'assignments' ? 'active' : '')}
              onClick={() => onSelectTab('assignments')}
              title="Assignments &amp; Analytics"
              type="button"
            >
              <PieChart size={18} />
            </button>
            <button
              className={'nav-icon-btn ' + (activeTab === 'exams' ? 'active' : '')}
              onClick={() => onSelectTab('exams')}
              title="Exams &amp; Assessment Analyzer"
              type="button"
            >
              <FileText size={18} />
            </button>
            <button
              className={'nav-icon-btn ' + (activeTab === 'library' ? 'active' : '')}
              onClick={() => onSelectTab('library')}
              title="Academic Studio (Plans, Worksheets &amp; Rubrics)"
              type="button"
            >
              <BookOpen size={18} />
            </button>
          </nav>
        </div>

        <div className="veda-sidebar-bottom">
          <div
            className="school-crest-mini clickable"
            title={`${schoolName}, ${schoolLocation} (Click to manage school)`}
            onClick={() => onSelectTab('settings')}
          >
            <div className="crest-logo">{schoolCode}</div>
          </div>
          {onToggleCollapse && (
            <button className="expand-toggle-btn" onClick={onToggleCollapse} title="Expand sidebar" type="button">
              <ChevronsRight size={16} />
            </button>
          )}
        </div>
      </aside>
    );
  }

  return (
    <aside className="veda-sidebar">
      <div className="veda-sidebar-top">
        <div className="veda-brand-row">
          <div className="veda-brand" onClick={() => onSelectTab('exams')} style={{ cursor: 'pointer' }}>
            <div className="veda-logo-mark">V</div>
            <span className="veda-brand-text">VedaAI</span>
          </div>
          {onToggleCollapse && (
            <button className="sidebar-collapse-btn" onClick={onToggleCollapse} title="Collapse sidebar" type="button">
              <ChevronsLeft size={16} />
            </button>
          )}
        </div>

        <button className="veda-toolkit-btn" onClick={onOpenToolkit} type="button">
          <Sparkles size={16} className="toolkit-sparkle" />
          <span>AI Teacher's Toolkit</span>
        </button>

        <nav className="veda-nav">
          <button
            className={'veda-nav-item ' + (activeTab === 'home' ? 'active' : '')}
            onClick={() => onSelectTab('home')}
            type="button"
          >
            <LayoutGrid size={18} />
            <span>Home</span>
          </button>
          <button
            className={'veda-nav-item ' + (activeTab === 'classroom' ? 'active' : '')}
            onClick={() => onSelectTab('classroom')}
            type="button"
          >
            <Users size={18} />
            <span>My Classroom</span>
          </button>
          <button
            className={'veda-nav-item ' + (activeTab === 'assignments' ? 'active' : '')}
            onClick={() => onSelectTab('assignments')}
            type="button"
          >
            <PieChart size={18} />
            <span>Assignments</span>
          </button>
          <button
            className={'veda-nav-item ' + (activeTab === 'exams' ? 'active' : '')}
            onClick={() => onSelectTab('exams')}
            type="button"
          >
            <FileText size={18} />
            <span>Exams</span>
          </button>
          <button
            className={'veda-nav-item ' + (activeTab === 'library' ? 'active' : '')}
            onClick={() => onSelectTab('library')}
            type="button"
          >
            <BookOpen size={18} />
            <span>Academic Studio</span>
          </button>
        </nav>
      </div>

      <div className="veda-sidebar-bottom">
        <button
          className={'veda-nav-item settings-item ' + (activeTab === 'settings' ? 'active' : '')}
          onClick={() => onSelectTab('settings')}
          type="button"
        >
          <Settings size={18} />
          <span>Settings</span>
        </button>

        {/* Dynamic School Crest Badge */}
        <div
          className="dps-school-badge clickable"
          onClick={() => onSelectTab('settings')}
          title="Click to configure School Institution data"
        >
          <div className="dps-crest-icon">
            <GraduationCap size={16} className="crest-svg" />
          </div>
          <div className="dps-info">
            <strong className="dps-name">{schoolName}</strong>
            <span className="dps-loc">{schoolLocation}</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
