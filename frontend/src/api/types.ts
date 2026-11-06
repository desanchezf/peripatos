export interface User {
  id: number
  username: string
  is_staff: boolean
}

export interface Progress {
  location: string
  percent: number
  finished: boolean
  updated_at: string | null
}

export interface Material {
  id: number
  title: string
  kind: 'theory' | 'reading'
  kind_label: string
  format: 'pdf' | 'epub' | 'text'
  file_url: string | null
  source_url: string
  content: string
  progress: Progress
}

export interface Bookmark {
  id: number
  material: number
  location: string
  label: string
  created_at: string
}

export interface ReadingNote {
  id: number
  material: number
  location: string
  label: string
  quote: string
  text: string
  created_at: string
}

export interface QuizSummary {
  id: number
  title: string
  description: string
  topic: { id: number; name: string; description: string } | null
  question_count: number
  attempt_count: number
  best_percent: number | null
}

export interface QuizDetail extends QuizSummary {
  questions: { id: number; text: string; choices: { id: number; text: string }[] }[]
}

export interface QuizResult {
  score: number
  total: number
  percent: number
  results: { question: number; selected: number | null; correct: boolean; correct_choices: number[]; explanation: string }[]
}

export interface Submission {
  id: number
  lab: number
  file_name: string
  file_url: string
  comment: string
  status: 'submitted' | 'reviewed'
  status_label: string
  feedback: string
  submitted_at: string
  reviewed_at: string | null
}

export interface Lab {
  id: number
  title: string
  statement: string
  theory: string
  due_date: string | null
  submissions: Submission[]
}

export type StepType = 'reading' | 'quiz' | 'lab'

export interface Training {
  id: number
  title: string
  description: string
  target_date: string | null
  steps: { id: number; type: StepType; item_id: number; title: string; done: boolean }[]
  done_steps: number
  total_steps: number
  percent: number
  completed: boolean
}

export type NodeStatus = 'pending' | 'in_progress' | 'done' | 'skipped'

export interface PathNode {
  id: number
  title: string
  description: string
  kind: 'core' | 'recommended' | 'alternative' | 'optional'
  kind_label: string
  status: NodeStatus
  links: { type: string; title: string; to: string }[]
  resource_url: string
}

export interface PathSummary {
  id: number
  title: string
  summary: string
  stage_count: number
  node_count: number
  done_nodes: number
  percent: number
  enrolled: boolean
}

export interface PathDetail extends PathSummary {
  description: string
  stages: { id: number; title: string; description: string; nodes: PathNode[] }[]
}

export interface Notice {
  id: string
  notice_id: number | null
  title: string
  body: string
  level: 'info' | 'warning'
  link: string | null
}

export interface Dashboard {
  metrics: {
    readings: { pending: number; in_progress: number; finished: number; total: number }
    trainings: { pending: number; total: number; percent: number }
    quizzes: { pending: number; total: number }
    labs: { pending: number; total: number }
    average_score: number | null
  }
  notices: Notice[]
  pending_quizzes: { id: number; title: string; topic: string | null; question_count: number }[]
  pending_readings: { id: number; title: string; kind_label: string; format: string; percent: number }[]
}

export interface LLMModel {
  id: number
  provider: 'anthropic' | 'ollama'
  name: string
  label: string
}

export interface Conversation {
  id: number
  title: string
  model: number | null
  created_at: string
  updated_at: string
}

export interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  model: number | null
  created_at: string
}

export interface ConversationDetail extends Conversation {
  messages: ChatMessage[]
}

export type ChatEvent = { type: 'text'; text: string } | { type: 'error'; message: string } | { type: 'done' }
