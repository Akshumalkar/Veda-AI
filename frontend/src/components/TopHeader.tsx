import { useState, useEffect } from 'react';
import {
  ArrowLeft,
  Bell,
  Check,
  ChevronDown,
  FileText,
  HelpCircle,
  LayoutGrid,
  LogOut,
  PieChart,
  Settings,
  Sliders,
  Sparkles,
  User,
  Users,
  CheckCheck,
  Trash2,
  BookOpen
} from 'lucide-react';
import type { TeacherUser } from '../types/user';
import { notificationStore, type NotificationItem } from '../data/notificationStore';

type TopHeaderProps = {
  activeTab: string;
  onSelectTab?: (t: string) => void;
  onBack?: () => void;
  onReset?: () => void;
  showBack?: boolean;
  onOpenHelp: () => void;
  onOpenNotifications: () => void;
  onOpenToolkit: () => void;
  onToggleProfile: () => void;
  isProfileOpen: boolean;
  isNotifOpen: boolean;
  user?: TeacherUser;
  onSignOut: () => void;
  onOpenSettings: () => void;
};

export default function TopHeader({
  activeTab,
  onSelectTab,
  onBack,
  onReset,
  showBack,
  onOpenHelp,
  onOpenNotifications,
  onOpenToolkit,
  onToggleProfile,
  isProfileOpen,
  isNotifOpen,
  user,
  onSignOut,
  onOpenSettings
}: TopHeaderProps) {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    const update = () => {
      setNotifications(notificationStore.getNotifications());
      setUnreadCount(notificationStore.getUnreadCount());
    };
    update();
    return notificationStore.subscribe(update);
  }, []);

  const teacherName = user?.name || 'Akshay Mathur';
  const teacherRole = user?.role || 'Senior Computer Science & AI Educator';
  const schoolName = user?.school?.name || 'Delhi Public School';
  const initials = teacherName.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase() || 'AM';

  const getTabLabel = () => {
    switch (activeTab) {
      case 'home': return 'Home Dashboard';
      case 'classroom': return 'My Classroom';
      case 'assignments': return 'Assignments & Analytics';
      case 'library': return 'Academic Studio & Rubrics';
      case 'settings': return 'Settings & AI Model';
      default: return 'Exams & Assessment Analyzer';
    }
  };

  const getTabIcon = () => {
    switch (activeTab) {
      case 'home': return <LayoutGrid size={16} className="breadcrumb-icon" />;
      case 'classroom': return <Users size={16} className="breadcrumb-icon" />;
      case 'assignments': return <PieChart size={16} className="breadcrumb-icon" />;
      case 'library': return <BookOpen size={16} className="breadcrumb-icon" />;
      case 'settings': return <Settings size={16} className="breadcrumb-icon" />;
      default: return <FileText size={16} className="breadcrumb-icon" />;
    }
  };

  const handleNotificationClick = (n: NotificationItem) => {
    notificationStore.markAsRead(n.id);
    if (n.targetTab && onSelectTab) {
      onSelectTab(n.targetTab);
    }
  };

  return (
    <header className="veda-topbar">
      <div className="topbar-left">
        {showBack ? (
          <button className="topbar-back-btn" onClick={onBack || onReset} type="button">
            <ArrowLeft size={18} />
            <span className="breadcrumb-label">Back to Assessment Upload</span>
          </button>
        ) : (
          <div className="topbar-breadcrumb">
            {getTabIcon()}
            <span className="breadcrumb-label">{getTabLabel()}</span>
          </div>
        )}
      </div>

      <div className="topbar-right">
        <button
          className="topbar-icon-btn"
          onClick={(e) => {
            e.stopPropagation();
            onOpenHelp();
          }}
          title="Help &amp; Guide"
          type="button"
        >
          <HelpCircle size={19} />
        </button>

        {/* Dynamic Real-Time Notifications Dropdown */}
        <div className="dropdown-container" onClick={(e) => e.stopPropagation()}>
          <button
            className={'topbar-icon-btn notification-btn ' + (isNotifOpen ? 'active' : '')}
            onClick={(e) => {
              e.stopPropagation();
              onOpenNotifications();
            }}
            title="Notifications"
            type="button"
          >
            <Bell size={19} />
            {unreadCount > 0 && (
              <span className="notification-counter-pill">{unreadCount}</span>
            )}
          </button>

          {isNotifOpen && (
            <div className="dropdown-menu notif-dropdown" onClick={(e) => e.stopPropagation()}>
              <div className="dropdown-header">
                <div className="notif-header-title">
                  <strong>Notifications</strong>
                  {unreadCount > 0 && <span className="badge-count">{unreadCount} new</span>}
                </div>
                <div className="notif-header-actions">
                  <button
                    className="mini-text-action-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      notificationStore.markAllAsRead();
                    }}
                    title="Mark all as read"
                    type="button"
                  >
                    <CheckCheck size={14} /> Read All
                  </button>
                  <button
                    className="mini-text-action-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      notificationStore.clearAll();
                    }}
                    title="Clear all"
                    type="button"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>

              <div className="notif-list">
                {notifications.length === 0 ? (
                  <div className="notif-empty-state">
                    <Check size={24} className="text-muted" />
                    <p>All caught up! No unread notifications.</p>
                  </div>
                ) : (
                  notifications.map((notif) => (
                    <div
                      key={notif.id}
                      className={'notif-item ' + (notif.unread ? 'unread' : '')}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleNotificationClick(notif);
                      }}
                    >
                      <div className={'notif-icon-box ' + (notif.type === 'alert' ? 'orange' : (notif.type === 'success' ? 'green' : 'blue'))}>
                        {notif.type === 'alert' ? <Sparkles size={14} /> : (notif.type === 'success' ? <Check size={14} /> : <BookOpen size={14} />)}
                      </div>
                      <div className="notif-text">
                        <p><strong>{notif.title}:</strong> {notif.message}</p>
                        <span className="notif-time">{notif.timestamp}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        <button
          className="topbar-icon-btn"
          onClick={(e) => {
            e.stopPropagation();
            onOpenToolkit();
          }}
          title="AI Teacher's Toolkit"
          type="button"
        >
          <Sparkles size={19} />
        </button>

        {/* Profile Dropdown */}
        <div className="dropdown-container" onClick={(e) => e.stopPropagation()}>
          <div
            className="topbar-profile"
            onClick={(e) => {
              e.stopPropagation();
              onToggleProfile();
            }}
          >
            <div className="profile-avatar">
              <User size={16} />
            </div>
            <span className="profile-name">{teacherName}</span>
            <ChevronDown size={14} className="profile-chevron" />
          </div>

          {isProfileOpen && (
            <div className="dropdown-menu profile-dropdown" onClick={(e) => e.stopPropagation()}>
              <div className="profile-dropdown-header">
                <div className="large-avatar">{initials}</div>
                <div>
                  <strong>{teacherName}</strong>
                  <span>{teacherRole}</span>
                  <span className="profile-school-tag">{schoolName}</span>
                </div>
              </div>
              <div className="dropdown-divider" />
              <button
                className="dropdown-action-item"
                onClick={() => {
                  onOpenSettings();
                }}
                type="button"
              >
                <User size={15} /> Switch School / Profile
              </button>
              <button
                className="dropdown-action-item"
                onClick={() => {
                  onOpenSettings();
                }}
                type="button"
              >
                <Sliders size={15} /> Grading Preferences
              </button>
              <div className="dropdown-divider" />
              <button
                className="dropdown-action-item text-red"
                onClick={() => {
                  onSignOut();
                }}
                type="button"
              >
                <LogOut size={15} /> Reset / Switch Session
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
