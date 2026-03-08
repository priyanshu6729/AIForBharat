"use client";

import { FormEvent, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { SimpleMarkdown } from "@/components/mentor-chat/simple-markdown";
import type { MentorMessage } from "@/types/contracts";
import { cn } from "@/utils/cn";

export function MentorChatPanel({
  messages,
  isStreaming,
  onSend,
}: {
  messages: MentorMessage[];
  isStreaming: boolean;
  onSend: (question: string) => Promise<void>;
}) {
  const [question, setQuestion] = useState("");

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!question.trim() || isStreaming) return;
    const value = question.trim();
    setQuestion("");
    await onSend(value);
  };

  return (
    <Card className="h-full min-h-0">
      <CardHeader className="py-2">
        <CardTitle>Mentor Chat</CardTitle>
      </CardHeader>
      <CardContent className="flex h-[calc(100%-44px)] min-h-0 flex-col gap-3">
        <div className="flex-1 space-y-2 overflow-y-auto rounded-lg border border-border bg-background/70 p-3">
          {messages.length === 0 ? (
            <p className="text-xs text-muted">
              Ask a question to start your guided learning session.
            </p>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  "rounded-lg px-3 py-2 text-xs",
                  message.role === "user"
                    ? "ml-10 bg-primary/20 text-text"
                    : "mr-10 border border-border bg-panel text-text"
                )}
              >
                <p className="mb-1 text-[10px] uppercase tracking-wide text-muted">
                  {message.role === "user" ? "You" : "Codexa Mentor"}
                </p>
                <SimpleMarkdown content={message.content || (message.streaming ? "..." : "")} />
              </div>
            ))
          )}
        </div>

        <form onSubmit={submit} className="space-y-2">
          <Textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Ask for a step-by-step explanation..."
            className="min-h-20"
          />
          <Button type="submit" disabled={isStreaming || !question.trim()} className="w-full">
            {isStreaming ? "Streaming response..." : "Ask Mentor"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
