"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAuth } from "@/lib/auth/use-auth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export default function VerifyPage() {
  const router = useRouter();
  const { verify, authError, isAuthenticating } = useAuth();
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");

  useEffect(() => {
    if (typeof window !== "undefined") {
      const cached = window.localStorage.getItem("codexa_pending_email");
      if (cached) setEmail(cached);
    }
  }, []);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      await verify({ email, code });
      if (typeof window !== "undefined") {
        window.localStorage.removeItem("codexa_pending_email");
      }
      router.push("/auth/login");
    } catch {
      // Error state is handled via authError from useAuth.
    }
  };

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md items-center px-6">
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Verify Email</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="space-y-3">
            <div>
              <label className="mb-1 block text-xs uppercase tracking-wide text-muted">Email</label>
              <Input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            <div>
              <label className="mb-1 block text-xs uppercase tracking-wide text-muted">Verification Code</label>
              <Input required value={code} onChange={(e) => setCode(e.target.value)} />
            </div>
            {authError ? <p className="text-xs text-red-400">{authError.message}</p> : null}
            <Button className="w-full" disabled={isAuthenticating}>
              {isAuthenticating ? "Verifying..." : "Verify"}
            </Button>
            <p className="text-xs text-muted">
              Back to <Link href="/auth/login" className="text-primary">login</Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
