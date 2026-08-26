export type NotificationItem = {
  id: string;
  title: string;
  message: string;
  timestamp: string;
  unread: boolean;
  type: 'success' | 'alert' | 'info';
  targetTab?: string;
};

const INITIAL_NOTIFICATIONS: NotificationItem[] = [
  {
    id: 'notif-1',
    title: 'Batch Evaluation Ready',
    message: 'Class 10 Physics Mid-Term Unit Test (45 submissions) evaluated with Gemini Vision OCR.',
    timestamp: '2 mins ago',
    unread: true,
    type: 'success',
    targetTab: 'exams'
  },
  {
    id: 'notif-2',
    title: 'Learning Gap Identified',
    message: 'Parallel Circuit Equivalent Resistance: 18% of students in Section A require remediation.',
    timestamp: '15 mins ago',
    unread: true,
    type: 'alert',
    targetTab: 'assignments'
  },
  {
    id: 'notif-3',
    title: 'New CBSE Rubric Available',
    message: 'Marking Scheme for Chemical Reactions & Equations (Chapter 1) synchronized.',
    timestamp: '1 hour ago',
    unread: false,
    type: 'info',
    targetTab: 'library'
  }
];

class NotificationStore {
  private notifications: NotificationItem[] = INITIAL_NOTIFICATIONS;
  private listeners: Array<() => void> = [];

  getNotifications(): NotificationItem[] {
    return [...this.notifications];
  }

  getUnreadCount(): number {
    return this.notifications.filter(n => n.unread).length;
  }

  addNotification(notif: Omit<NotificationItem, 'id' | 'timestamp' | 'unread'>) {
    const newItem: NotificationItem = {
      ...notif,
      id: 'notif-' + Date.now(),
      timestamp: 'Just now',
      unread: true
    };
    this.notifications = [newItem, ...this.notifications];
    this.notify();
  }

  markAsRead(id: string) {
    this.notifications = this.notifications.map(n =>
      n.id === id ? { ...n, unread: false } : n
    );
    this.notify();
  }

  markAllAsRead() {
    this.notifications = this.notifications.map(n => ({ ...n, unread: false }));
    this.notify();
  }

  clearAll() {
    this.notifications = [];
    this.notify();
  }

  subscribe(listener: () => void) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  private notify() {
    this.listeners.forEach(listener => listener());
  }
}

export const notificationStore = new NotificationStore();
