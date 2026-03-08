import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <main className="flex min-h-screen items-center justify-center px-6">
      <div className="max-w-md space-y-3 rounded-xl border border-border bg-panel p-5 text-center">
        <h1 className="text-xl font-semibold">Page not found</h1>
        <p className="text-sm text-muted">The route does not exist in Codexa v2.</p>
        <Link href="/">
          <Button>Go to Home</Button>
        </Link>
      </div>
    </main>
  );
}
