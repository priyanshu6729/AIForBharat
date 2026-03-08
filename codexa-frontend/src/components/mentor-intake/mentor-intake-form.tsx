"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export type MentorIntakePayload = {
  prompt: string;
  code: string;
  githubSnippet: string;
};

export function MentorIntakeForm({
  loading,
  onSubmit,
}: {
  loading: boolean;
  onSubmit: (payload: MentorIntakePayload) => Promise<void>;
}) {
  const [prompt, setPrompt] = useState("");
  const [code, setCode] = useState("");
  const [githubSnippet, setGithubSnippet] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  return (
    <Card className="mx-auto w-full max-w-4xl">
      <CardHeader>
        <CardTitle>Create Mentor Session</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-1">
          <label className="text-xs uppercase tracking-wide text-muted">What do you want help with?</label>
          <Input
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            placeholder="explain recursion in python"
          />
          <p className="text-[11px] text-muted">
            Try: help me understand this code · teach me graphs in java · explain dynamic programming
          </p>
        </div>

        <div className="space-y-1">
          <label className="text-xs uppercase tracking-wide text-muted">Paste code (optional)</label>
          <Textarea
            value={code}
            onChange={(event) => setCode(event.target.value)}
            placeholder="Paste your code here..."
          />
        </div>

        <div className="space-y-1">
          <label className="text-xs uppercase tracking-wide text-muted">GitHub snippet URL (optional)</label>
          <Input
            value={githubSnippet}
            onChange={(event) => setGithubSnippet(event.target.value)}
            placeholder="https://github.com/..."
          />
        </div>

        <Button
          disabled={loading || !prompt.trim()}
          onClick={async () => {
            setLocalError(null);
            try {
              await onSubmit({ prompt, code, githubSnippet });
            } catch {
              setLocalError("Could not create mentor session. Please retry.");
            }
          }}
          className="w-full"
        >
          {loading ? "Starting session..." : "Start Learning"}
        </Button>
        {localError ? (
          <p className="rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-xs text-red-300">
            {localError}
          </p>
        ) : null}
      </CardContent>
    </Card>
  );
}
