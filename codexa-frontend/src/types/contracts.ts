export type Language = "python" | "javascript";

export type CodePoint = [number, number];
export type CodeRange = [CodePoint, CodePoint];

export interface UserIdentity {
  sub: string;
  email: string;
  email_verified?: boolean;
  cognito_username?: string;
}

export interface AuthSession {
  isAuthenticated: boolean;
  isLoading: boolean;
  refreshInFlight: boolean;
  user: UserIdentity | null;
}

export interface AnalyzeRequest {
  code: string;
  language: Language;
}

export interface AstNodeMeta {
  name?: string;
  type?: string;
  range?: CodeRange;
  [key: string]: unknown;
}

export interface AnalyzeResponse {
  ast: {
    functions?: AstNodeMeta[];
    loops?: AstNodeMeta[];
    conditions?: AstNodeMeta[];
    dependencies?: AstNodeMeta[];
    calls?: AstNodeMeta[];
    [key: string]: unknown;
  };
  ai_analysis?: {
    summary?: string;
    hints?: string[];
    issues?: string[];
    [key: string]: unknown;
  } | null;
}

export interface ExecuteRequest {
  code: string;
  language: Language;
}

export interface ExecuteResponse {
  stdout: string;
  stderr: string;
  execution_time: number;
  complexity_hint: string;
}

export type GuidanceRequest = {
  user_question: string;   // ← must match backend
  code_context?: string;
  ast_context?: Record<string, unknown>;
  session_id?: number;
  goal?: string;
  guidance_level?: number;
};

export interface GuidanceResponse {
  response: string;
  session_id?: number | null;
}

export interface ChatResponse {
  response: string;
  session_id?: number | null;
}

export interface VisualizeRequest {
  ast: Record<string, unknown>;
  session_id?: number | null;
}

export interface GraphNode {
  id: string;
  label: string;
  type: "function" | "class" | "loop" | "condition" | "dependency" | "call" | "unknown";
  range?: CodeRange;
  metadata?: Record<string, unknown>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: "calls" | "imports" | "depends" | "contains" | "next" | "unknown";
  label?: string;
}

export interface GraphPayload {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface VisualizeResponse {
  s3_url?: string;
  graph: GraphPayload | Record<string, unknown>;
}

export interface MentorMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
  streaming?: boolean;
  mode?: "socratic" | "direct";
  tokens?: number;
  session_id?: number | null;
}

export interface WorkspaceFile {
  id: string;
  name: string;
  language: Language;
  content: string;
}

export interface WorkspaceSnapshot {
  files: WorkspaceFile[];
  activeFileId: string;
  sessionId: number | null;
  graph: GraphPayload | null;
  execution: ExecuteResponse | null;
  chat: MentorMessage[];
  selectedMode: "socratic" | "direct";
  guidanceLevel: number;
}

export interface LearningPathSummary {
  id: number;
  title: string;
  description: string;
  difficulty: string;
  lesson_count?: number;
}

export interface LessonSummary {
  id: number;
  title: string;
  content: string;
  order: number;
}

export interface LearningPathDetail extends LearningPathSummary {
  lessons: LessonSummary[];
}

export interface ProgressItem {
  lesson_id: number;
  status: string;
  updated_at: string;
}

export interface SessionListItem {
  session_id: number;
  title: string;
  created_at: string;
}

export interface SessionListResponse {
  sessions: SessionListItem[];
}

export interface SessionDetail {
  session_id: number;
  title: string;
  language: Language;
  code: string;
  visualization: Record<string, unknown>;
  chat_log: Array<{ question: string; response: string }>;
}
