import Link from "next/link";
import { Code2, GitBranch, GraduationCap, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

const features = [
  {
    title: "AI Code Mentor",
    description: "Conversational teaching that explains why code works, not just what to type.",
    icon: Sparkles,
  },
  {
    title: "AST Code Analysis",
    description: "Tree-sitter backed program structure analysis with focused hints and breakdowns.",
    icon: Code2,
  },
  {
    title: "Interactive Graph Visualization",
    description: "See function flow, dependencies, and call relationships in live graph form.",
    icon: GitBranch,
  },
  {
    title: "Structured Learning Paths",
    description: "Track your progress through guided topics and concept checkpoints.",
    icon: GraduationCap,
  },
];

export default function LandingPage() {
  return (
    <main className="mx-auto max-w-[1200px] px-6 py-12 md:py-20">
      <section className="grid gap-8 lg:grid-cols-[1.2fr_1fr]">
        <div>
          <p className="mb-3 inline-flex rounded-full border border-primary/50 bg-primary/15 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-indigo-200">
            Codexa AI Mentor Platform
          </p>
          <h1 className="text-4xl font-semibold leading-tight text-text md:text-6xl">
            Stop Vibe Coding. Start Understanding Code.
          </h1>
          <p className="mt-4 max-w-2xl text-base text-slate-300 md:text-lg">
            AI mentor that explains code step-by-step with graphs and reasoning.
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            <Link href="/auth/login">
              <Button className="h-11 px-6">Start Learning</Button>
            </Link>
            <Link href="/mentor">
              <Button variant="secondary" className="h-11 px-6">Open Mentor</Button>
            </Link>
          </div>
          <div className="mt-8 flex flex-wrap gap-6 text-xs text-muted">
            <span>Tree-sitter</span>
            <span>AI reasoning</span>
            <span>code graphs</span>
          </div>
        </div>
        <Card className="overflow-hidden p-4">
          <div className="rounded-lg border border-border bg-[#0B1224] p-3">
            <div className="mb-3 flex items-center justify-between text-[11px] text-muted">
              <span>Demo Workspace</span>
              <span>Editor + Mentor + Graph</span>
            </div>
            <div className="grid gap-2 md:grid-cols-[1fr_1fr]">
              <div className="rounded-md border border-border bg-[#091126] p-2 text-[10px] text-slate-200">
                <p className="mb-1 text-muted">Editor</p>
                <p>def recurse(n):</p>
                <p>  if n == 0: return 1</p>
                <p>  return n * recurse(n-1)</p>
              </div>
              <div className="rounded-md border border-border bg-[#091126] p-2 text-[10px] text-slate-200">
                <p className="mb-1 text-muted">Mentor Chat</p>
                <p>Step 1: Identify base case.</p>
                <p>Step 2: Track recursive case.</p>
                <p>Step 3: Simulate call stack.</p>
              </div>
              <div className="md:col-span-2 rounded-md border border-border bg-[#091126] p-2 text-[10px] text-slate-200">
                <p className="mb-1 text-muted">Graph</p>
                <p>recurse() -calls-&gt; recurse()</p>
              </div>
            </div>
          </div>
        </Card>
      </section>

      <section className="mt-14 grid gap-4 md:grid-cols-2">
        {features.map((feature) => {
          const Icon = feature.icon;
          return (
            <Card key={feature.title} className="p-4">
              <div className="mb-2 inline-flex h-8 w-8 items-center justify-center rounded-md border border-primary/40 bg-primary/20">
                <Icon className="h-4 w-4 text-indigo-200" />
              </div>
              <h2 className="text-lg font-semibold text-text">{feature.title}</h2>
              <p className="mt-1 text-sm text-muted">{feature.description}</p>
            </Card>
          );
        })}
      </section>
    </main>
  );
}
