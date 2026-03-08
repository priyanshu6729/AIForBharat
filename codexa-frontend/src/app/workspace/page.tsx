"use client";

import { AppHeader } from "@/components/layout/app-header";
import { AuthGuard } from "@/components/layout/auth-guard";
import { WorkspaceStudio } from "@/components/workspace/workspace-studio";

export default function WorkspacePage() {
  return (
    <AuthGuard>
      <AppHeader />
      <main className="mx-auto max-w-[1700px] px-5 py-4">
        <WorkspaceStudio />
      </main>
    </AuthGuard>
  );
}
