// File: /frontend/app/layout.tsx
// Purpose: Defines the root HTML structure, metadata, font,
// Mantine styles, color-scheme script, and application providers.

import "@mantine/core/styles.layer.css";
import "@mantine/notifications/styles.layer.css";
import "./globals.css";

import type { Metadata } from "next";
import { Inter } from "next/font/google";
import {
  ColorSchemeScript,
  mantineHtmlProps,
} from "@mantine/core";

import { Providers } from "./providers";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "STS Capstone Project",
  description:
    "An AI-powered study management and learning support platform.",
};

type RootLayoutProps = Readonly<{
  children: React.ReactNode;
}>;

export default function RootLayout({
  children,
}: RootLayoutProps) {
  return (
    <html
      lang="en"
      className={inter.variable}
      {...mantineHtmlProps}
    >
      <head>
        <ColorSchemeScript defaultColorScheme="light" />
      </head>

      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}