"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { AppHeader } from "@/components/layout/app-header";
import { AuthGuard } from "@/components/layout/auth-guard";
import { MentorIntakeForm } from "@/components/mentor-intake/mentor-intake-form";
import { ApiError, mentorClient } from "@/lib/api/client";
import { useWorkspaceStore } from "@/store/use-workspace-store";

export default function MentorPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    setPrompt,
    setGoal,
    setSessionId,
    setChat,
    setFiles,
    setActiveFileId,
    setAnalysis,
    setGraph,
    setExecution,
  } = useWorkspaceStore();

  return (
    <AuthGuard>
      <AppHeader />
      <main className="mx-auto max-w-[1100px] px-5 py-6">
        <MentorIntakeForm
          loading={loading}
          onSubmit={async ({ prompt, code, githubSnippet }) => {
            setLoading(true);
            setSubmitError(null);
            try {
              const initialCode = code?.trim() || "# Paste or write code here\n";
              const initialPrompt = githubSnippet?.trim()
                ? `${prompt}\nGitHub snippet: ${githubSnippet}`
                : prompt;
              const payload = {
                user_question: initialPrompt,
                code_context: initialCode,
                ast_context: {},
                goal: prompt,
                guidance_level: 1,
              };

              let guidance;
              try {
                guidance = await mentorClient.guidance(payload);
              } catch {
                guidance = await mentorClient.chat(payload);
              }

              setPrompt(initialPrompt);
              setGoal(prompt);
              setSessionId(guidance.session_id || null);
              setFiles([
                {
                  id: "main.py",
                  name: "main.py",
                  language: "python",
                  content: initialCode,
                },
              ]);
              setActiveFileId("main.py");
              setAnalysis(null);
              setGraph(null);
              setExecution(null);
              setChat([
                {
                  id: `u-${Date.now()}`,
                  role: "user",
                  content: initialPrompt,
                  createdAt: new Date().toISOString(),
                },
                {
                  id: `a-${Date.now()}`,
                  role: "assistant",
                  content: guidance.response,
                  createdAt: new Date().toISOString(),
                  session_id: guidance.session_id || null,
                },
              ]);

              router.push("/workspace");
            } catch (error) {
              const message =
                error instanceof ApiError
                  ? error.message
                  : "Could not create mentor session. Please retry.";
              setSubmitError(message);
            } finally {
              setLoading(false);
            }
          }}
        />
        {submitError ? (
          <p className="mx-auto mt-3 max-w-4xl rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-xs text-red-300">
            {submitError}
          </p>
        ) : null}
      </main>
    </AuthGuard>
  );
}
