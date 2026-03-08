"use client";

type StreamHandlers = {
  onText: (chunk: string) => void;
  onDone?: (sessionId?: number) => void;
};

export async function consumeChatStream(
  payload: Record<string, unknown>,
  handlers: StreamHandlers
): Promise<void> {
  // Normalize: accept both 'message' and 'user_question', backend now handles both
  const normalizedPayload = {
    ...payload,
    user_question: payload.user_question ?? payload.message ?? "",
  };

  const response = await fetch("/api/chat/stream", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-codexa-intent": "codexa-web",
    },
    body: JSON.stringify(normalizedPayload),
    credentials: "include",
  });

  if (!response.ok || !response.body) {
    throw new Error("Unable to stream mentor response");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() || "";

    for (const eventBlock of events) {
      const line = eventBlock
        .split("\n")
        .find((item) => item.startsWith("data:"));
      if (!line) continue;

      const raw = line.replace(/^data:\s*/, "").trim();
      if (!raw) continue;

      try {
        const parsed = JSON.parse(raw) as {
          text?: string;
          done?: boolean;
          session_id?: number;
        };
        if (parsed.text) {
          handlers.onText(parsed.text);
        }
        if (parsed.done) {
          handlers.onDone?.(parsed.session_id);
        }
      } catch {
        handlers.onText(raw);
      }
    }
  }
}
