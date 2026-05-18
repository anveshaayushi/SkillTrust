/**
 * mockData.js
 * Realistic mock data matching the real API shape.
 * Import and use during dev / live demo fallback.
 */

export const MOCK_CANDIDATES = [
  {
    id: 'cand_001',
    name: 'Arjun Mehta',
    role: 'Senior Frontend Engineer',
    uploaded_at: '2024-03-12T10:20:00Z',
    sas_score: 87,
    fraud_flag: false,
    fraud_confidence: 0.04,
    skill_score: 82,
    profile_score: 91,
    overall_score: 87,
    skills_matched: ['React', 'TypeScript', 'GraphQL', 'Node.js'],
    skills_missing: ['Docker', 'AWS'],
    retest_triggered: false,
    status: 'done',
  },
  {
    id: 'cand_002',
    name: 'Priya Nair',
    role: 'ML Engineer',
    uploaded_at: '2024-03-12T11:05:00Z',
    sas_score: 73,
    fraud_flag: false,
    fraud_confidence: 0.12,
    skill_score: 78,
    profile_score: 69,
    overall_score: 73,
    skills_matched: ['Python', 'PyTorch', 'scikit-learn'],
    skills_missing: ['MLflow', 'Kubernetes'],
    retest_triggered: false,
    status: 'done',
  },
  {
    id: 'cand_003',
    name: 'Rohan Das',
    role: 'Backend Developer',
    uploaded_at: '2024-03-12T12:30:00Z',
    sas_score: 34,
    fraud_flag: true,
    fraud_confidence: 0.88,
    skill_score: 41,
    profile_score: 28,
    overall_score: 34,
    skills_matched: ['Java', 'Spring Boot'],
    skills_missing: ['SQL', 'REST APIs', 'Docker'],
    retest_triggered: true,
    status: 'done',
  },
  {
    id: 'cand_004',
    name: 'Sneha Rao',
    role: 'Full Stack Developer',
    uploaded_at: '2024-03-12T13:45:00Z',
    sas_score: 91,
    fraud_flag: false,
    fraud_confidence: 0.02,
    skill_score: 94,
    profile_score: 88,
    overall_score: 91,
    skills_matched: ['React', 'Node.js', 'PostgreSQL', 'Docker', 'AWS'],
    skills_missing: [],
    retest_triggered: false,
    status: 'done',
  },
  {
    id: 'cand_005',
    name: 'Kiran Patel',
    role: 'DevOps Engineer',
    uploaded_at: '2024-03-12T14:20:00Z',
    sas_score: 0,
    fraud_flag: false,
    fraud_confidence: 0,
    skill_score: 0,
    profile_score: 0,
    overall_score: 0,
    skills_matched: [],
    skills_missing: [],
    retest_triggered: false,
    status: 'running',
  },
]

export const MOCK_AGENT_STATUSES = [
  { agent: 'Orchestrator', status: 'healthy', last_run: '2s ago', message: 'Routing 1 active job', color: '#6C63FF' },
  { agent: 'Profile + Evidence', status: 'healthy', last_run: '45s ago', message: 'Processed 4 resumes', color: '#00D4AA' },
  { agent: 'Authenticity + Scoring', status: 'healthy', last_run: '45s ago', message: 'SAS score computed', color: '#FF6B35' },
  { agent: 'Skill Testing', status: 'running', last_run: 'now', message: 'Testing Kiran Patel — React task', color: '#FFB800' },
  { agent: 'Resume Engine', status: 'healthy', last_run: '3m ago', message: 'PDF generated for cand_004', color: '#E8EAF0' },
]

export const MOCK_CANDIDATE_DETAIL = {
  id: 'cand_001',
  name: 'Arjun Mehta',
  email: 'arjun.mehta@example.com',
  role: 'Senior Frontend Engineer',
  location: 'Bengaluru, India',
  github: 'github.com/arjunmehta',
  linkedin: 'linkedin.com/in/arjunmehta',
  uploaded_at: '2024-03-12T10:20:00Z',

  // Profile Agent output
  extracted_skills: ['React', 'TypeScript', 'GraphQL', 'Node.js', 'Redux', 'Webpack', 'Jest'],
  github_repos: [
    { name: 'react-dashboard', stars: 112, score: 88 },
    { name: 'ts-utils', stars: 43, score: 74 },
    { name: 'gql-playground', stars: 7, score: 61 },
  ],

  // Authenticity Agent output
  sas_score: 87,
  sas_breakdown: {
    code_similarity: 82,
    profile_consistency: 91,
    repo_depth: 84,
    commit_patterns: 88,
  },
  fraud_flag: false,
  fraud_confidence: 0.04,
  fraud_reasons: [],

  // Skill Testing Agent output
  skill_score: 82,
  skill_results: [
    { skill: 'React', score: 90, difficulty: 'Hard', passed: true },
    { skill: 'TypeScript', score: 85, difficulty: 'Medium', passed: true },
    { skill: 'GraphQL', score: 76, difficulty: 'Medium', passed: true },
    { skill: 'Node.js', score: 68, difficulty: 'Hard', passed: false },
  ],
  retest_triggered: false,

  profile_score: 91,
  overall_score: 87,
  recommendation: 'HIRE',

  // Resume Engine output
  resume_improvements: [
    { section: 'Summary', issue: 'Too generic; lacks quantified impact', fix: 'Added measurable achievements (40% perf improvement)' },
    { section: 'Skills', issue: 'Missing key tech stack keywords', fix: 'Added TypeScript, GraphQL, Jest for ATS compatibility' },
    { section: 'Experience', issue: 'Bullet points lack action verbs', fix: 'Rewritten with strong action verbs and metrics' },
    { section: 'Projects', issue: 'GitHub links missing', fix: 'Added live demo links and repo stars count' },
  ],
}

export const DASHBOARD_STATS = {
  total: 5,
  done: 4,
  running: 1,
  flagged: 1,
  avg_score: 72,
  top_score: 91,
}
