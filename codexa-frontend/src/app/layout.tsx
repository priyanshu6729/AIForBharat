import type { Metadata } from "next";

import { Providers } from "@/app/providers";

import "./globals.css";

export const metadata: Metadata = {
  title: "Codexa",
  description: "Stop vibe coding. Start understanding code.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-background font-sans text-text antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
