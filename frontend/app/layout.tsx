import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MapleBoss — 주간 보스 대시보드",
  description: "메이플스토리 주간 보스 수익 및 파티 스케줄 관리",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
