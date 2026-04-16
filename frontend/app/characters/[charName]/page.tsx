"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import {
  getMe, listBosses, getChecklist, saveChecklist,
  type User, type BossInfo, type BossChecklist,
} from "@/lib/api";

import BossChecklistEditor from "@/components/BossChecklistEditor";

function getWeeklyKey(date: Date = new Date()): string {
  // 메이플 주차: 목요일 시작, 수요일 종료
  // 날짜를 3일 앞당기면 목요일이 ISO 주차의 월요일이 됨
  const shifted = new Date(date);
  shifted.setDate(shifted.getDate() - 3);
  const d = new Date(Date.UTC(shifted.getFullYear(), shifted.getMonth(), shifted.getDate()));
  const dayNum = d.getUTCDay() || 7;
  d.setUTCDate(d.getUTCDate() + 4 - dayNum);
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  const weekNo = Math.ceil((((d.getTime() - yearStart.getTime()) / 86400000) + 1) / 7);
  return `${d.getUTCFullYear()}-W${String(weekNo).padStart(2, "0")}`;
}

export default function ChecklistPage() {
  const router = useRouter();
  const params = useParams<{ charName: string }>();
  const charName = decodeURIComponent(params.charName);
  const weeklyKey = getWeeklyKey();

  const [user,     setUser]     = useState<User | null>(null);
  const [bosses,   setBosses]   = useState<BossInfo[]>([]);
  const [initial,  setInitial]  = useState<BossChecklist | undefined>();
  const [saveMsg,  setSaveMsg]  = useState("");

  useEffect(() => {
    async function load() {
      try {
        const me = await getMe();
        setUser(me);
        const [bl, cl] = await Promise.all([
          listBosses(),
          getChecklist(me.user_id, charName, weeklyKey).catch(() => undefined),
        ]);
        setBosses(bl);
        setInitial(cl);
      } catch {
        router.push("/login");
      }
    }
    load();
  }, [charName, weeklyKey]);

  async function handleSave(checklist: BossChecklist) {
    if (!user) return;
    await saveChecklist(user.user_id, charName, checklist);
    setSaveMsg("저장 완료!");
    setTimeout(() => setSaveMsg(""), 2000);
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center text-maple-muted">
        로딩 중...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-maple-dark">
      <header className="border-b border-maple-border px-6 py-3 flex items-center gap-3 min-w-0">
        <button
          onClick={() => router.push("/dashboard")}
          className="text-maple-muted hover:text-maple-yellow transition-colors shrink-0"
        >
          ← 대시보드
        </button>
        <h2 className="font-semibold text-maple-text truncate min-w-0 flex-1">
          {charName} — 보스 체크리스트
        </h2>
        <span className="text-maple-muted text-xs shrink-0">{weeklyKey}</span>
        {saveMsg && <span className="text-maple-green text-xs shrink-0">{saveMsg}</span>}
      </header>

      <main className="max-w-3xl mx-auto px-4 py-6">
        <BossChecklistEditor
          userId={user.user_id}
          charName={charName}
          weeklyKey={weeklyKey}
          bossList={bosses}
          initial={initial}
          onSave={handleSave}
        />
      </main>
    </div>
  );
}
