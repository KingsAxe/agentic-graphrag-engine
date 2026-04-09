import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SovereignRAG Console",
  description: "Workspace console for uploads, jobs, streamed reasoning traces, and chat queries.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
