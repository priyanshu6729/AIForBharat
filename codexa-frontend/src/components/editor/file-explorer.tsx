"use client";

import { Plus, FileCode2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { WorkspaceFile } from "@/types/contracts";
import { cn } from "@/utils/cn";

export function FileExplorer({
  files,
  activeFileId,
  onSelect,
  onAdd,
}: {
  files: WorkspaceFile[];
  activeFileId: string;
  onSelect: (id: string) => void;
  onAdd: () => void;
}) {
  return (
    <Card className="h-full min-h-0">
      <CardHeader className="flex flex-row items-center justify-between py-2">
        <CardTitle>Files</CardTitle>
        <Button variant="ghost" className="h-8 px-2" onClick={onAdd}>
          <Plus className="h-4 w-4" />
        </Button>
      </CardHeader>
      <CardContent className="space-y-1 overflow-y-auto px-2 pb-2">
        {files.map((file) => (
          <button
            key={file.id}
            onClick={() => onSelect(file.id)}
            className={cn(
              "flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-xs text-muted transition hover:bg-background/60 hover:text-text",
              activeFileId === file.id && "bg-primary/20 text-text"
            )}
          >
            <FileCode2 className="h-3.5 w-3.5" />
            <span className="truncate">{file.name}</span>
          </button>
        ))}
      </CardContent>
    </Card>
  );
}
