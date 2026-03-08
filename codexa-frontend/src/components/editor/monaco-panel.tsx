"use client";

import { useEffect, useRef } from "react";
import Editor, { Monaco } from "@monaco-editor/react";

import type { CodeRange, Language } from "@/types/contracts";

export function MonacoPanel({
  value,
  language,
  filePath,
  highlightedRange,
  onChange,
}: {
  value: string;
  language: Language;
  filePath: string;
  highlightedRange?: CodeRange;
  onChange: (value: string) => void;
}) {
  const editorRef = useRef<any>(null);
  const monacoRef = useRef<Monaco | null>(null);
  const decorationIdsRef = useRef<string[]>([]);

  useEffect(() => {
    if (!editorRef.current || !monacoRef.current || !highlightedRange) return;
    const monaco = monacoRef.current;
    const [[startLine, startColumn], [endLine, endColumn]] = highlightedRange;

    decorationIdsRef.current = editorRef.current.deltaDecorations(decorationIdsRef.current, [
      {
        range: new monaco.Range(startLine + 1, startColumn + 1, endLine + 1, endColumn + 1),
        options: {
          isWholeLine: false,
          className: "codexa-range-highlight",
        },
      },
    ]);

    editorRef.current.revealLineInCenter(startLine + 1);
  }, [highlightedRange]);

  return (
    <div className="h-full overflow-hidden rounded-xl border border-border">
      <Editor
        value={value}
        language={language}
        path={filePath}
        theme="vs-dark"
        onMount={(editor, monaco) => {
          editorRef.current = editor;
          monacoRef.current = monaco;
        }}
        onChange={(nextValue) => onChange(nextValue || "")}
        options={{
          automaticLayout: true,
          minimap: { enabled: false },
          fontSize: 13,
          fontFamily: "JetBrains Mono",
          smoothScrolling: true,
          tabSize: 2,
        }}
      />
    </div>
  );
}
