"use client";

import { useEffect } from "react";

import { Button } from "@/components/ui/button";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="flex min-h-screen items-center justify-center px-6">
      <div className="max-w-md space-y-3 rounded-xl border border-border bg-panel p-5 text-center">
        <h1 className="text-xl font-semibold">Something went wrong</h1>
        <p className="text-sm text-muted">
          Codexa hit an unexpected error. Retry the action or reload the page.
        </p>
        <Button onClick={reset}>Try Again</Button>
      </div>
    </main>
  );
}
