import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
    "./src/lib/**/*.{ts,tsx}",
    "./src/store/**/*.{ts,tsx}",
    "./src/types/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#6366F1",
        background: "#0F172A",
        panel: "#1E293B",
        accent: "#22C55E",
        text: "#E2E8F0",
        muted: "#94A3B8",
        border: "#334155"
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"]
      },
      boxShadow: {
        panel: "0 12px 28px rgba(2, 6, 23, 0.35)",
        glow: "0 0 0 1px rgba(99, 102, 241, 0.25), 0 18px 40px rgba(99, 102, 241, 0.2)"
      }
    }
  },
  plugins: [require("tailwindcss-animate")]
};

export default config;
