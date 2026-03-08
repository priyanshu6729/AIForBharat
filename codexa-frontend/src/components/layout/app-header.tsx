"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { useAuth } from "@/lib/auth/use-auth";
import { Button } from "@/components/ui/button";
import { cn } from "@/utils/cn";

const NAV = [
  { href: "/mentor", label: "Mentor" },
  { href: "/workspace", label: "Workspace" },
];

export function AppHeader() {
  const pathname = usePathname();
  const router = useRouter();
  const { session, logout } = useAuth();

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/90 backdrop-blur">
      <div className="mx-auto flex h-16 w-full max-w-[1600px] items-center justify-between px-5">
        <div className="flex items-center gap-6">
          <Link href="/" className="text-lg font-semibold tracking-tight text-text">
            Codexa
          </Link>
          <nav className="hidden gap-2 md:flex">
            {NAV.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "rounded-md px-3 py-2 text-sm text-muted transition hover:text-text",
                  pathname.startsWith(item.href) && "bg-panel text-text"
                )}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-3">
          {session.user ? <span className="hidden text-xs text-muted md:inline">{session.user.email}</span> : null}
          {session.isAuthenticated ? (
            <Button
              variant="secondary"
              onClick={async () => {
                await logout();
                router.push("/auth/login");
              }}
            >
              Logout
            </Button>
          ) : (
            <Button variant="secondary" onClick={() => router.push("/auth/login")}>
              Login
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}
