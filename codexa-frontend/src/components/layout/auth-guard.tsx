"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/lib/auth/use-auth";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { session } = useAuth();

  useEffect(() => {
    if (!session.isLoading && !session.isAuthenticated) {
      router.replace("/auth/login");
    }
  }, [router, session.isAuthenticated, session.isLoading]);

  if (session.isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center text-sm text-muted">
        Checking your session...
      </div>
    );
  }

  if (!session.isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}
