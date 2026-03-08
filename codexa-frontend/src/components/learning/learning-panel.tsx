"use client";

import { useQuery } from "@tanstack/react-query";

import { mentorClient } from "@/lib/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function LearningPanel() {
  const paths = useQuery({ queryKey: ["learn", "paths"], queryFn: mentorClient.learningPaths });
  const progress = useQuery({ queryKey: ["progress", "list"], queryFn: mentorClient.progressList });

  return (
    <Card className="h-full min-h-0">
      <CardHeader className="py-2">
        <CardTitle>Learning Panel</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 overflow-y-auto text-xs">
        <section>
          <p className="mb-2 text-[11px] uppercase tracking-wide text-muted">Learning Paths</p>
          {paths.isLoading ? (
            <p className="text-muted">Loading paths...</p>
          ) : (
            <div className="space-y-2">
              {(paths.data || []).slice(0, 6).map((path) => (
                <div key={path.id} className="rounded-lg border border-border bg-background/50 p-2">
                  <p className="font-semibold text-text">{path.title}</p>
                  <p className="mt-1 text-muted">{path.description}</p>
                </div>
              ))}
            </div>
          )}
        </section>

        <section>
          <p className="mb-2 text-[11px] uppercase tracking-wide text-muted">Progress</p>
          {progress.isLoading ? (
            <p className="text-muted">Loading progress...</p>
          ) : (
            <div className="space-y-2">
              {(progress.data?.progress || []).slice(0, 8).map((item) => (
                <div key={`${item.lesson_id}-${item.updated_at}`} className="rounded-lg border border-border bg-background/50 p-2">
                  <p className="text-text">Lesson {item.lesson_id}</p>
                  <p className="text-muted">{item.status}</p>
                </div>
              ))}
            </div>
          )}
        </section>
      </CardContent>
    </Card>
  );
}
