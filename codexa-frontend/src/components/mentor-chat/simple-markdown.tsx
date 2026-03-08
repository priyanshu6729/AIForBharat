import React from "react";

function renderInline(text: string) {
  const parts = text.split(/(`[^`]+`)/g);
  return parts.map((part, index) => {
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code key={index} className="rounded bg-[#0B1224] px-1 py-0.5 text-[11px] text-indigo-200">
          {part.slice(1, -1)}
        </code>
      );
    }
    return <React.Fragment key={index}>{part}</React.Fragment>;
  });
}

export function SimpleMarkdown({ content }: { content: string }) {
  const blocks = content.split(/```/g);

  return (
    <div className="space-y-2 text-xs leading-relaxed">
      {blocks.map((block, index) => {
        if (index % 2 === 1) {
          return (
            <pre key={index} className="overflow-auto rounded border border-border bg-[#0B1224] p-2 text-[11px] text-indigo-100">
              <code>{block.trim()}</code>
            </pre>
          );
        }

        return block.split("\n").map((line, lineIndex) => (
          <p key={`${index}-${lineIndex}`} className="whitespace-pre-wrap text-slate-100">
            {renderInline(line)}
          </p>
        ));
      })}
    </div>
  );
}
