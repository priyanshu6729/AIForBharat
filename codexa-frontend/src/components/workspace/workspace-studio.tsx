"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { BookOpen, Save } from "lucide-react";

import { mentorClient } from "@/lib/api/client";
import { consumeChatStream } from "@/lib/sse/stream";
import { useWorkspaceStore } from "@/store/use-workspace-store";
import type { CodeRange, MentorMessage } from "@/types/contracts";
import { astToGraph } from "@/utils/graph";
import { normalizeGraphPayload } from "@/utils/normalize-graph";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { FileExplorer } from "@/components/editor/file-explorer";
import { MonacoPanel } from "@/components/editor/monaco-panel";
import { MentorChatPanel } from "@/components/mentor-chat/mentor-chat-panel";
import { GraphViewerPanel } from "@/components/graph-viewer/graph-viewer-panel";
import { OutputConsole } from "@/components/console/output-console";
import { LearningPanel } from "@/components/learning/learning-panel";

function nowISO() {
  return new Date().toISOString();
}

function toChatLog(messages: MentorMessage[]) {
  const logs: Array<{ question: string; response: string }> = [];
  let pendingQuestion = "";

  messages.forEach((message) => {
    if (message.role === "user") {
      pendingQuestion = message.content;
      return;
    }

    if (message.role === "assistant" && pendingQuestion && !message.streaming) {
      logs.push({ question: pendingQuestion, response: message.content });
      pendingQuestion = "";
    }
  });

  return logs;
}

export function WorkspaceStudio() {
  const searchParams = useSearchParams();
  const initialSession = searchParams.get("session");
  const initialPanel = searchParams.get("panel");

  const {
    files,
    activeFileId,
    goal,
    sessionId,
    analysis,
    graph,
    execution,
    chat,
    guidanceLevel,
    mode,
    setFiles,
    setActiveFileId,
    setGoal,
    setSessionId,
    setGraph,
    setAnalysis,
    setExecution,
    addChatMessage,
    setChat,
    appendChatChunk,
    updateChatMessage,
    setGuidanceLevel,
    setMode,
  } = useWorkspaceStore();

  const [selectedRange, setSelectedRange] = useState<CodeRange | undefined>(undefined);
  const [loadingAnalyze, setLoadingAnalyze] = useState(false);
  const [loadingExecute, setLoadingExecute] = useState(false);
  const [loadingVisualize, setLoadingVisualize] = useState(false);
  const [loadingExplain, setLoadingExplain] = useState(false);
  const [savingSession, setSavingSession] = useState(false);
  const [showLearning, setShowLearning] = useState(false);
  const [activeSideTab, setActiveSideTab] = useState<"learning" | "sessions">("learning");
  const [workspaceTitle, setWorkspaceTitle] = useState("Codexa Mentor Session");

  const sessionsQuery = useQuery({ queryKey: ["sessions", "list"], queryFn: mentorClient.sessionList });

  useEffect(() => {
    if (initialPanel === "sessions") {
      setShowLearning(true);
      setActiveSideTab("sessions");
    } else if (initialPanel === "learning") {
      setShowLearning(true);
      setActiveSideTab("learning");
    }
  }, [initialPanel]);

  const activeFile = useMemo(
    () => files.find((file) => file.id === activeFileId) || files[0],
    [activeFileId, files]
  );

  useEffect(() => {
    const loadSession = async () => {
      const maybeId = Number(initialSession);
      if (!maybeId || Number.isNaN(maybeId) || maybeId === sessionId) return;

      try {
        const loaded = await mentorClient.sessionGet(maybeId);
        setSessionId(loaded.session_id);
        setWorkspaceTitle(loaded.title);
        setFiles([
          {
            id: "main.py",
            name: loaded.language === "javascript" ? "main.js" : "main.py",
            language: loaded.language,
            content: loaded.code,
          },
        ]);
        setActiveFileId("main.py");

        const hydratedGraph = normalizeGraphPayload(loaded.visualization);
        setGraph(hydratedGraph);
        setChat(
          loaded.chat_log.flatMap((entry, index) => [
            {
              id: `q-${index}-${entry.question.slice(0, 8)}`,
              role: "user" as const,
              content: entry.question,
              createdAt: nowISO(),
            },
            {
              id: `a-${index}-${entry.response.slice(0, 8)}`,
              role: "assistant" as const,
              content: entry.response,
              createdAt: nowISO(),
            },
          ])
        );
      } catch {
        // Session load fallback handled by UI state
      }
    };

    void loadSession();
  }, [initialSession, sessionId, setActiveFileId, setChat, setFiles, setGraph, setSessionId]);

  const updateActiveContent = (content: string) => {
    setFiles(files.map((file) => (file.id === activeFile.id ? { ...file, content } : file)));
  };

  const addFile = () => {
    const nextId = `file-${Date.now()}`;
    const language = activeFile?.language || "python";
    const extension = language === "javascript" ? "js" : "py";
    const nextFile = {
      id: nextId,
      name: `untitled-${files.length + 1}.${extension}`,
      language,
      content: "",
    };
    setFiles([...files, nextFile]);
    setActiveFileId(nextId);
  };

  const runAnalyze = async () => {
    if (!activeFile?.content.trim()) return;
    setLoadingAnalyze(true);
    try {
      const result = await mentorClient.analyze({
        code: activeFile.content,
        language: activeFile.language,
      });
      setAnalysis(result);
      if (!graph || graph.nodes.length === 0) {
        setGraph(astToGraph(result));
      }
    } finally {
      setLoadingAnalyze(false);
    }
  };

  const runVisualize = async () => {
    if (!analysis?.ast) {
      await runAnalyze();
    }

    if (!analysis?.ast) return;

    setLoadingVisualize(true);
    try {
      const visualized = await mentorClient.visualize({
        ast: analysis.ast,
        session_id: sessionId || undefined,
      });
      setGraph(normalizeGraphPayload(visualized));
    } catch {
      setGraph(astToGraph(analysis));
    } finally {
      setLoadingVisualize(false);
    }
  };

  const runExecute = async () => {
    if (!activeFile?.content.trim()) return;

    setLoadingExecute(true);
    try {
      const response = await mentorClient.execute({
        code: activeFile.content,
        language: activeFile.language,
      });
      setExecution(response);
    } finally {
      setLoadingExecute(false);
    }
  };

  const askMentor = async (question: string) => {
    if (!question.trim()) return;

    const userMessage: MentorMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: question,
      createdAt: nowISO(),
    };
    const assistantMessageId = `assistant-${Date.now()}`;

    addChatMessage(userMessage);
    addChatMessage({
      id: assistantMessageId,
      role: "assistant",
      content: "",
      createdAt: nowISO(),
      streaming: true,
      mode,
      session_id: sessionId,
    });

    setLoadingExplain(true);
    const socraticPreface =
      mode === "socratic"
        ? "Use Socratic teaching mode with step-by-step prompts and questions. "
        : "";

    const payload = {
      user_question: `${socraticPreface}${question}`,
      code_context: activeFile.content,
      ast_context: analysis?.ast || {},
      session_id: sessionId || undefined,
      goal: goal || undefined,
      guidance_level: guidanceLevel,
    };

    try {
      await consumeChatStream(payload, {
        onText: (chunk) => {
          appendChatChunk(assistantMessageId, chunk);
          updateChatMessage(assistantMessageId, { streaming: true });
        },
        onDone: (nextSessionId) => {
          if (nextSessionId) {
            setSessionId(nextSessionId);
          }
          updateChatMessage(assistantMessageId, { streaming: false, session_id: nextSessionId || sessionId });
        },
      });
      updateChatMessage(assistantMessageId, { streaming: false });
    } catch {
      try {
        const chatFallback = await mentorClient.chat(payload);
        updateChatMessage(assistantMessageId, {
          content: chatFallback.response,
          streaming: false,
          session_id: chatFallback.session_id || sessionId,
        });
        if (chatFallback.session_id) {
          setSessionId(chatFallback.session_id);
        }
      } catch {
        try {
          const guidanceFallback = await mentorClient.guidance(payload);
          updateChatMessage(assistantMessageId, {
            content: guidanceFallback.response,
            streaming: false,
            session_id: guidanceFallback.session_id || sessionId,
          });
          if (guidanceFallback.session_id) {
            setSessionId(guidanceFallback.session_id);
          }
        } catch {
          updateChatMessage(assistantMessageId, {
            content:
              "Codexa could not reach the mentor backend right now. Your workspace is still available; retry in a moment.",
            streaming: false,
            session_id: sessionId,
          });
        }
      }
    } finally {
      setLoadingExplain(false);
    }
  };

  const saveSession = async () => {
    if (!activeFile?.content) return;

    setSavingSession(true);
    try {
      const result = await mentorClient.sessionSave({
        session_id: sessionId || undefined,
        title: workspaceTitle,
        language: activeFile.language,
        code: activeFile.content,
        visualization: {
          graph,
          files,
          activeFileId,
          goal,
        },
        chat_log: toChatLog(chat),
      });
      setSessionId(result.session_id);
    } finally {
      setSavingSession(false);
    }
  };

  return (
    <div className="space-y-3 pb-4">
      <Card className="p-3">
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_220px_180px_220px_180px]">
          <Input
            value={workspaceTitle}
            onChange={(event) => setWorkspaceTitle(event.target.value)}
            placeholder="Session title"
          />
          <Input
            value={goal}
            onChange={(event) => setGoal(event.target.value)}
            placeholder="What are you learning today?"
          />
          <select
            value={mode}
            onChange={(event) => setMode(event.target.value as "socratic" | "direct")}
            className="h-11 rounded-lg border border-border bg-panel/70 px-3 text-sm text-text"
          >
            <option value="socratic">Socratic Mode</option>
            <option value="direct">Direct Mode</option>
          </select>
          <div className="flex items-center gap-2 rounded-lg border border-border bg-panel/70 px-3 text-xs text-muted">
            <span>Guidance</span>
            <input
              type="range"
              min={0}
              max={5}
              value={guidanceLevel}
              onChange={(event) => setGuidanceLevel(Number(event.target.value))}
              className="w-full"
            />
            <span>{guidanceLevel}</span>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="secondary" className="h-11 w-full" onClick={() => setShowLearning((prev) => !prev)}>
              <BookOpen className="mr-2 h-4 w-4" />
              {showLearning ? "Hide Panel" : "Learning Panel"}
            </Button>
          </div>
        </div>

        <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
          <Button variant="secondary" onClick={runAnalyze} disabled={loadingAnalyze}>
            {loadingAnalyze ? "Analyzing..." : "Analyze Code"}
          </Button>
          <Button variant="secondary" onClick={runExecute} disabled={loadingExecute}>
            {loadingExecute ? "Running..." : "Run Code"}
          </Button>
          <Button variant="secondary" onClick={runVisualize} disabled={loadingVisualize}>
            {loadingVisualize ? "Rendering..." : "Visualize Graph"}
          </Button>
          <Button onClick={() => askMentor("Explain this code step-by-step.")} disabled={loadingExplain}>
            {loadingExplain ? "Explaining..." : "Explain Code"}
          </Button>
          <Button variant="secondary" onClick={saveSession} disabled={savingSession}>
            <Save className="mr-2 h-4 w-4" />
            {savingSession ? "Saving..." : "Save Session"}
          </Button>
        </div>
      </Card>

      <div
        className={`grid gap-3 ${
          showLearning
            ? "xl:grid-cols-[220px_minmax(0,1fr)_360px_280px]"
            : "xl:grid-cols-[220px_minmax(0,1fr)_360px]"
        }`}
      >
        <div className="h-[520px] min-h-0">
          <FileExplorer files={files} activeFileId={activeFileId} onSelect={setActiveFileId} onAdd={addFile} />
        </div>

        <div className="h-[520px] min-h-0">
          <MonacoPanel
            value={activeFile?.content || ""}
            language={activeFile?.language || "python"}
            filePath={activeFile?.name || "main.py"}
            highlightedRange={selectedRange}
            onChange={updateActiveContent}
          />
        </div>

        <div className="h-[520px] min-h-0">
          <MentorChatPanel messages={chat} isStreaming={loadingExplain} onSend={askMentor} />
        </div>

        {showLearning ? (
          <div className="h-[520px] min-h-0">
            <div className="mb-2 flex items-center gap-2">
              <Button
                variant={activeSideTab === "learning" ? "primary" : "ghost"}
                className="h-8 px-3"
                onClick={() => setActiveSideTab("learning")}
              >
                Learning
              </Button>
              <Button
                variant={activeSideTab === "sessions" ? "primary" : "ghost"}
                className="h-8 px-3"
                onClick={() => setActiveSideTab("sessions")}
              >
                Sessions
              </Button>
            </div>
            {activeSideTab === "learning" ? (
              <LearningPanel />
            ) : (
              <Card className="h-full overflow-y-auto p-2 text-xs">
                {sessionsQuery.isLoading ? (
                  <p className="text-muted">Loading sessions...</p>
                ) : (
                  <div className="space-y-2">
                    {(sessionsQuery.data?.sessions || []).map((session) => (
                      <button
                        key={session.session_id}
                        className="w-full rounded-lg border border-border bg-panel/60 p-2 text-left hover:border-primary/50"
                        onClick={async () => {
                          const loaded = await mentorClient.sessionGet(session.session_id);
                          setSessionId(loaded.session_id);
                          setWorkspaceTitle(loaded.title);
                          setFiles([
                            {
                              id: "main.py",
                              name: loaded.language === "javascript" ? "main.js" : "main.py",
                              language: loaded.language,
                              content: loaded.code,
                            },
                          ]);
                          setActiveFileId("main.py");
                          setGraph(normalizeGraphPayload(loaded.visualization));
                          setChat(
                            loaded.chat_log.flatMap((entry, index) => [
                              {
                                id: `q-${index}-${Date.now()}`,
                                role: "user" as const,
                                content: entry.question,
                                createdAt: nowISO(),
                              },
                              {
                                id: `a-${index}-${Date.now()}`,
                                role: "assistant" as const,
                                content: entry.response,
                                createdAt: nowISO(),
                              },
                            ])
                          );
                        }}
                      >
                        <p className="font-semibold text-text">{session.title}</p>
                        <p className="text-muted">{new Date(session.created_at).toLocaleString()}</p>
                      </button>
                    ))}
                  </div>
                )}
              </Card>
            )}
          </div>
        ) : null}
      </div>

      <div className="grid gap-3 xl:grid-cols-[minmax(0,1fr)_420px]">
        <div className="h-[300px] min-h-0">
          <GraphViewerPanel graph={graph} onSelectRange={(range) => setSelectedRange(range)} />
        </div>
        <div className="h-[300px] min-h-0">
          <OutputConsole execution={execution} />
        </div>
      </div>

      {activeFile?.language !== "python" ? (
        <p className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-xs text-amber-200">
          Runtime execution currently supports Python only. Switch file language to Python for Run Code.
        </p>
      ) : null}
    </div>
  );
}
