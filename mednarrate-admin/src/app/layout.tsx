import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "MedNarrate Admin",
  description: "Operational Command Center for MedNarrate",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} antialiased bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-50`}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
