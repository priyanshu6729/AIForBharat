"use client";

import {
  AnalyzeRequest,
  AnalyzeResponse,
  ExecuteRequest,
  ExecuteResponse,
  GuidanceRequest,
  GuidanceResponse,
  ChatResponse,
  LearningPathDetail,
  LearningPathSummary,
  ProgressItem,
  SessionDetail,
  SessionListResponse,
  VisualizeRequest,
  VisualizeResponse,
} from "@/types/contracts";

const INTENT_HEADER = "x-codexa-intent";
const INTENT_VALUE = "codexa-web";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function parseResponse<T>(response: Response): Promise<T> {
  const contentType = response.headers.get("content-type") || "";
  if (!response.ok) {
    const errorBody = contentType.includes("application/json")
      ? await response.json().catch(() => ({}))
      : await response.text().catch(() => "");
    const detail =
      typeof errorBody === "object" && errorBody !== null
        ? (errorBody as { detail?: string; message?: string; error?: string }).detail ||
          (errorBody as { message?: string }).message ||
          (errorBody as { error?: string }).error
        : errorBody;
    throw new ApiError(response.status, (detail as string) || "Request failed");
  }

  if (contentType.includes("application/json")) {
    return response.json() as Promise<T>;
  }

  return (await response.text()) as T;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      ...(init?.method && init.method !== "GET" ? { [INTENT_HEADER]: INTENT_VALUE } : {}),
      ...(init?.headers || {}),
    },
    credentials: "include",
    cache: "no-store",
  });

  return parseResponse<T>(response);
}

export const authClient = {
  login: (payload: { email: string; password: string }) =>
    request<{ user?: { email?: string } }>("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  signup: (payload: { email: string; password: string }) =>
    request<{ message: string }>("/api/auth/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  verify: (payload: { email: string; code: string }) =>
    request<{ message: string }>("/api/auth/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  me: () =>
    request<{ sub: string; email: string; email_verified?: boolean } | { authenticated: false; user: null }>(
      "/api/auth/me"
    ),

  logout: () =>
    request<{ message: string }>("/api/auth/logout", {
      method: "POST",
    }),
};

export const mentorClient = {
  analyze: (payload: AnalyzeRequest) =>
    request<AnalyzeResponse>("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  execute: (payload: ExecuteRequest) =>
    request<ExecuteResponse>("/api/execute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  guidance: (payload: GuidanceRequest) =>
    request<GuidanceResponse>("/api/guidance", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  chat: (payload: GuidanceRequest) =>
    request<ChatResponse>("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  visualize: (payload: VisualizeRequest) =>
    request<VisualizeResponse>("/api/visualize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  sessionList: () => request<SessionListResponse>("/api/session"),

  sessionGet: (id: number) => request<SessionDetail>(`/api/session?id=${id}`),

  sessionSave: (payload: Record<string, unknown>) =>
    request<{ session_id: number }>("/api/session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  learningPaths: () => request<LearningPathSummary[]>("/api/learn"),

  learningPath: (pathId: number) => request<LearningPathDetail>(`/api/learn?pathId=${pathId}`),

  progressList: () => request<{ progress: ProgressItem[] }>("/api/progress"),

  progressUpdate: (payload: { lesson_id: number; status: string }) =>
    request<{ lesson_id: number; status: string; updated_at: string }>("/api/progress", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
};
