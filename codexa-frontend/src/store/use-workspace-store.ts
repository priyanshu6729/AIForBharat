"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import {
  AnalyzeResponse,
  ExecuteResponse,
  GraphPayload,
  MentorMessage,
  WorkspaceFile,
} from "@/types/contracts";

type WorkspaceState = {
  files: WorkspaceFile[];
  activeFileId: string;
  goal: string;
  prompt: string;
  sessionId: number | null;
  graph: GraphPayload | null;
  analysis: AnalyzeResponse | null;
  execution: ExecuteResponse | null;
  chat: MentorMessage[];
  guidanceLevel: number;
  mode: "socratic" | "direct";
  setFiles: (files: WorkspaceFile[]) => void;
  setActiveFileId: (id: string) => void;
  setGoal: (goal: string) => void;
  setPrompt: (prompt: string) => void;
  setSessionId: (sessionId: number | null) => void;
  setGraph: (graph: GraphPayload | null) => void;
  setAnalysis: (analysis: AnalyzeResponse | null) => void;
  setExecution: (execution: ExecuteResponse | null) => void;
  addChatMessage: (message: MentorMessage) => void;
  setChat: (messages: MentorMessage[]) => void;
  appendChatChunk: (id: string, chunk: string) => void;
  updateChatMessage: (id: string, patch: Partial<MentorMessage>) => void;
  clearChat: () => void;
  setGuidanceLevel: (value: number) => void;
  setMode: (mode: "socratic" | "direct") => void;
  reset: () => void;
};

const defaultFile: WorkspaceFile = {
  id: "main.py",
  name: "main.py",
  language: "python",
  content: "# Start learning with Codexa\n",
};

const initialState = {
  files: [defaultFile],
  activeFileId: defaultFile.id,
  goal: "",
  prompt: "",
  sessionId: null,
  graph: null,
  analysis: null,
  execution: null,
  chat: [],
  guidanceLevel: 1,
  mode: "socratic" as const,
};

export const useWorkspaceStore = create<WorkspaceState>()(
  persist(
    (set) => ({
      ...initialState,
      setFiles: (files) => set({ files }),
      setActiveFileId: (activeFileId) => set({ activeFileId }),
      setGoal: (goal) => set({ goal }),
      setPrompt: (prompt) => set({ prompt }),
      setSessionId: (sessionId) => set({ sessionId }),
      setGraph: (graph) => set({ graph }),
      setAnalysis: (analysis) => set({ analysis }),
      setExecution: (execution) => set({ execution }),
      addChatMessage: (message) => set((state) => ({ chat: [...state.chat, message] })),
      setChat: (chat) => set({ chat }),
      appendChatChunk: (id, chunk) =>
        set((state) => ({
          chat: state.chat.map((message) =>
            message.id === id ? { ...message, content: `${message.content}${chunk}` } : message
          ),
        })),
      updateChatMessage: (id, patch) =>
        set((state) => ({
          chat: state.chat.map((message) => (message.id === id ? { ...message, ...patch } : message)),
        })),
      clearChat: () => set({ chat: [] }),
      setGuidanceLevel: (guidanceLevel) => set({ guidanceLevel }),
      setMode: (mode) => set({ mode }),
      reset: () => set({ ...initialState }),
    }),
    {
      name: "codexa-workspace-v2",
      partialize: (state) => ({
        files: state.files,
        activeFileId: state.activeFileId,
        goal: state.goal,
        prompt: state.prompt,
        sessionId: state.sessionId,
        graph: state.graph,
        analysis: state.analysis,
        execution: state.execution,
        chat: state.chat,
        guidanceLevel: state.guidanceLevel,
        mode: state.mode,
      }),
    }
  )
);
