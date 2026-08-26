export type SchoolProfile = {
  id: string;
  name: string;
  location: string;
  code: string;
  board: string;
  affiliationNumber: string;
  principalName?: string;
  email?: string;
  phone?: string;
  isCustom?: boolean;
};

export type TeacherUser = {
  id: string;
  name: string;
  email: string;
  role: string;
  subject: string;
  gradeLevels: string[];
  school: SchoolProfile;
  avatarUrl?: string;
  gradingStrictness: 'strict' | 'balanced' | 'lenient';
  aiModel: string;
};

export const DEFAULT_SCHOOLS: SchoolProfile[] = [
  {
    id: 'dps-bokaro',
    name: 'Delhi Public School',
    location: 'Bokaro Steel City',
    code: 'DPS',
    board: 'CBSE',
    affiliationNumber: '3430032',
    principalName: 'Dr. A. S. Gangwar',
    email: 'info@dpsbokaro.edu.in',
    phone: '+91 6542 269 494'
  },
  {
    id: 'dps-rkp',
    name: 'Delhi Public School',
    location: 'R.K. Puram, New Delhi',
    code: 'DPS-RKP',
    board: 'CBSE',
    affiliationNumber: '2730018',
    principalName: 'Mrs. Padma Srinivasan',
    email: 'principal@dpsrkp.net',
    phone: '+91 11 4911 5555'
  },
  {
    id: 'modern-delhi',
    name: 'Modern School',
    location: 'Barakhamba Road, New Delhi',
    code: 'MS',
    board: 'CBSE',
    affiliationNumber: '2730005',
    principalName: 'Dr. Vijay Datta',
    email: 'principal@modernschool.net',
    phone: '+91 11 2331 1618'
  },
  {
    id: 'mothers-intl',
    name: "The Mother's International School",
    location: 'Sri Aurobindo Marg, New Delhi',
    code: 'MIS',
    board: 'CBSE',
    affiliationNumber: '2730035',
    principalName: 'Mrs. Manmeet Khurana',
    email: 'contact@themis.in',
    phone: '+91 11 2696 4140'
  }
];

export const DEFAULT_USER: TeacherUser = {
  id: 'teacher-1',
  name: 'Akshay Mathur',
  email: 'akshay.mathur@dpsbokaro.edu.in',
  role: 'Senior Computer Science & AI Educator',
  subject: 'Artificial Intelligence & Computer Science',
  gradeLevels: ['Class 9', 'Class 10'],
  school: DEFAULT_SCHOOLS[0],
  gradingStrictness: 'balanced',
  aiModel: 'Gemini 3.6 Flash (Fast & High-Accuracy)'
};

export function getCustomSchools(): SchoolProfile[] {
  try {
    const raw = localStorage.getItem('veda_custom_schools');
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function saveCustomSchool(school: SchoolProfile): SchoolProfile[] {
  const existing = getCustomSchools();
  const updated = [school, ...existing.filter(s => s.id !== school.id)];
  localStorage.setItem('veda_custom_schools', JSON.stringify(updated));
  return updated;
}

export function getAllSchools(): SchoolProfile[] {
  const custom = getCustomSchools();
  return [...custom, ...DEFAULT_SCHOOLS];
}
