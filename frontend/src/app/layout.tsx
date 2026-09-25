import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/components/auth-provider";
import { AppShell } from "@/components/app-shell";
import { TooltipProvider } from "@/components/ui/tooltip";

const ICON = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='0' y2='1'%3E%3Cstop offset='0' stop-color='%23137a63'/%3E%3Cstop offset='1' stop-color='%2364b348'/%3E%3C/linearGradient%3E%3C/defs%3E%3Cpath d='M16 3C19 3 29 11 29 16S19 29 16 29 3 21 3 16 13 3 16 3Z' fill='url(%23g)'/%3E%3Crect x='10' y='11' width='4' height='6' rx='1.5' fill='%23fffdf9'/%3E%3Crect x='18' y='11' width='4' height='6' rx='1.5' fill='%23fffdf9'/%3E%3C/svg%3E";

export const metadata: Metadata = {
  title: "LangVis",
  description: "A speaking language teacher in your browser.",
  icons: { icon: ICON },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body data-page="home">
        <TooltipProvider>
          <AuthProvider>
            <AppShell>{children}</AppShell>
          </AuthProvider>
        </TooltipProvider>
      </body>
    </html>
  );
}
