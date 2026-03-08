"use client";

import * as React from "react";

import { cn } from "@/utils/cn";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(function Input(
  { className, ...props },
  ref
) {
  return (
    <input
      ref={ref}
      className={cn(
        "h-11 w-full rounded-lg border border-border bg-panel/70 px-3 text-sm text-text placeholder:text-muted focus:border-primary/70 focus:outline-none focus:ring-2 focus:ring-primary/40",
        className
      )}
      {...props}
    />
  );
});
