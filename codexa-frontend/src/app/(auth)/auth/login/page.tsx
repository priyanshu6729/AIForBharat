"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAuth } from "@/lib/auth/use-auth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export default function LoginPage() {
  const router = useRouter();
  const { session, login, authError, isAuthenticating } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  useEffect(() => {
    if (session.isAuthenticated) {
      router.replace("/mentor");
    }
  }, [router, session.isAuthenticated]);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      await login({ email, password });
      router.push("/mentor");
    } catch {
      // Error state is handled via authError from useAuth.
    }
  };

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md items-center px-6">
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Login to Codexa</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="space-y-3">
            <div>
              <label className="mb-1 block text-xs uppercase tracking-wide text-muted">Email</label>
              <Input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            <div>
              <label className="mb-1 block text-xs uppercase tracking-wide text-muted">Password</label>
              <Input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} />
            </div>
            {authError ? <p className="text-xs text-red-400">{authError.message}</p> : null}
            <Button className="w-full" disabled={isAuthenticating}>
              {isAuthenticating ? "Logging in..." : "Login"}
            </Button>
            <p className="text-xs text-muted">
              New to Codexa? <Link href="/auth/signup" className="text-primary">Create account</Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
