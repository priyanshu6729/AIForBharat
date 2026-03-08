"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAuth } from "@/lib/auth/use-auth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export default function SignupPage() {
  const router = useRouter();
  const { signup, authError, isAuthenticating } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      await signup({ email, password });
      if (typeof window !== "undefined") {
        window.localStorage.setItem("codexa_pending_email", email);
      }
      router.push("/auth/verify");
    } catch {
      // Error state is handled via authError from useAuth.
    }
  };

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md items-center px-6">
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Create Codexa Account</CardTitle>
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
              {isAuthenticating ? "Creating..." : "Sign Up"}
            </Button>
            <p className="text-xs text-muted">
              Already registered? <Link href="/auth/login" className="text-primary">Login</Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
