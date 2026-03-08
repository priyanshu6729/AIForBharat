"use client";

import * as React from "react";

import { cn } from "@/utils/cn";

const buttonVariants = {
  primary:
    "bg-primary text-white hover:brightness-110 shadow-glow border border-primary/50",
  secondary:
    "bg-panel text-text border border-border hover:border-primary/60",
  ghost: "bg-transparent text-text border border-transparent hover:bg-panel/60",
  danger: "bg-red-600 text-white hover:bg-red-500 border border-red-500/60",
} as const;

type ButtonVariant = keyof typeof buttonVariants;

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { className, variant = "primary", ...props },
  ref
) {
  return (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center rounded-lg px-4 py-2.5 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60",
        buttonVariants[variant],
        className
      )}
      {...props}
    />
  );
});
