// File: /frontend/app/layout.tsx
// Purpose: Defines the root HTML layout and application metadata.

import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "STS Capstone Project",
  description:
    "An AI-powered study management and learning support platform.",
};

type RootLayoutProps = Readonly<{
  children: ReactNode;
}>;

export default function RootLayout({
  children,
}: RootLayoutProps) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}