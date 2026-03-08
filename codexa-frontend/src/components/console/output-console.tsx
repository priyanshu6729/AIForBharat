import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ExecuteResponse } from "@/types/contracts";

export function OutputConsole({ execution }: { execution: ExecuteResponse | null }) {
  return (
    <Card className="h-full min-h-0">
      <CardHeader className="py-2">
        <CardTitle>Output Console</CardTitle>
      </CardHeader>
      <CardContent className="h-[calc(100%-44px)] min-h-0">
        <pre className="h-full overflow-auto rounded-xl border border-border bg-[#0B1224] p-3 text-xs text-text">
          {execution
            ? `stdout:\n${execution.stdout || "(empty)"}\n\nstderr:\n${execution.stderr || "(empty)"}\n\nexecution_time: ${execution.execution_time.toFixed(4)}s\ncomplexity_hint: ${execution.complexity_hint}`
            : "Run code to inspect output and errors."}
        </pre>
      </CardContent>
    </Card>
  );
}
