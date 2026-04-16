"use client";

import { useState, useEffect, useMemo } from "react";
import type { BossInfo, BossEntry, BossChecklist } from "@/lib/api";

interface Props {
  userId: string;
  charName: string;
  weeklyKey: string;
  bossList: BossInfo[];
  initial?: BossChecklist;
  onSave: (checklist: BossChecklist) => Promise<void>;
}

const MAX_BOSSES = 12;

function formatMeso(n: number) {
  if (n >= 100_000_000) return `${(n / 100_000_000).toFixed(2).replace(/\.?0+$/, "")}억`;
  if (n >= 10_000)      return `${(n / 10_000).toFixed(0)}만`;
  return n.toLocaleString("ko-KR");
}

function isCrossMonthWeek(weeklyKey: string): boolean {
  // YYYY-Www 형식에서 목요일과 수요일이 다른 달인지 확인 (ISO 8601)
  const year = parseInt(weeklyKey.split("-W")[0]);
  const week = parseInt(weeklyKey.split("-W")[1]);

  const jan4 = new Date(year, 0, 4);
  // isoweekday: 1=Mon, ..., 7=Sun (Python) vs getDay: 0=Sun, ..., 6=Sat (JS)
  // JS: (getDay() + 6) % 7 || 7 converts to isoweekday
  const isoDay = (jan4.getDay() === 0 ? 7 : jan4.getDay());
  const daysToMonday = isoDay - 1; // Distance from Jan 4 to the Monday of its week

  const week1Monday = new Date(year, 0, 4 - daysToMonday);
  const targetMonday = new Date(week1Monday);
  targetMonday.setDate(week1Monday.getDate() + (week - 1) * 7);

  const thursday = new Date(targetMonday);
  thursday.setDate(targetMonday.getDate() + 3);

  const wednesday = new Date(targetMonday);
  wednesday.setDate(targetMonday.getDate() + 5);

  return thursday.getMonth() !== wednesday.getMonth();
}

const DIFFICULTY_ORDER = ["이지", "노말", "하드", "카오스", "익스트림"];

export default function BossChecklistEditor({
  userId, charName, weeklyKey, bossList, initial, onSave,
}: Props) {
  // key: boss_name, value: 선택된 BossEntry
  const [selected, setSelected] = useState<Record<string, BossEntry>>({});
  const [saving, setSaving] = useState(false);
  const [initialWeeklyKey, setInitialWeeklyKey] = useState<string>(weeklyKey);
  const [clearedMonthlyThisMonth, setClearedMonthlyThisMonth] = useState<Set<string>>(new Set());

  const { groupedWeekly, groupedMonthly } = useMemo(() => {
    const map: Record<string, BossInfo[]> = {};
    for (const b of bossList) {
      if (!map[b.name]) map[b.name] = [];
      map[b.name].push(b);
    }
    for (const name in map) {
      map[name].sort(
        (a, b) => DIFFICULTY_ORDER.indexOf(a.difficulty) - DIFFICULTY_ORDER.indexOf(b.difficulty)
      );
    }
    const sorted = Object.entries(map).sort(([, a], [, b]) => a[0].min_level - b[0].min_level);
    const weekly = sorted.filter(([, variants]) => !variants[0].is_monthly);
    const monthly = sorted.filter(([, variants]) => variants[0].is_monthly);
    return { groupedWeekly: weekly, groupedMonthly: monthly };
  }, [bossList]);

  useEffect(() => {
    if (!initial) {
      setInitialWeeklyKey(weeklyKey);
      setClearedMonthlyThisMonth(new Set());
      return;
    }
    setInitialWeeklyKey(initial.weekly_key);
    const map: Record<string, BossEntry> = {};
    const clearedMonthly = new Set<string>();
    for (const b of initial.bosses) {
      map[b.boss_name] = b;
      // 월간 보스이고 클리어된 것을 추적 (현재 주차에서)
      if (b.is_monthly && b.is_cleared) {
        clearedMonthly.add(b.boss_name);
      }
    }
    setSelected(map);
    setClearedMonthlyThisMonth(clearedMonthly);
  }, [initial, weeklyKey]);

  // bossList에서 월간 보스 판단 (is_monthly 필드)
  const monthlyBossNames = new Set(bossList.filter((b) => b.is_monthly).map((b) => b.name));

  // 주간 보스 선택 개수만 카운트
  const weeklySelectedCount = Object.values(selected).filter((b) => !monthlyBossNames.has(b.boss_name)).length;
  const monthlySelectedCount = Object.values(selected).filter((b) => monthlyBossNames.has(b.boss_name)).length;

  const weeklyEarnings = Object.values(selected)
    .filter((b) => !monthlyBossNames.has(b.boss_name))
    .reduce((sum, b) => sum + Math.floor(b.crystal_price / b.party_size), 0);

  const monthlyEarnings = Object.values(selected)
    .filter((b) => monthlyBossNames.has(b.boss_name))
    .reduce((sum, b) => sum + Math.floor(b.crystal_price / b.party_size), 0);

  // 초기 상태에서 변경이 있는지 확인
  const hasChanges = useMemo(() => {
    const totalSelected = weeklySelectedCount + monthlySelectedCount;
    if (!initial) return totalSelected > 0;

    // 선택된 보스 개수 다르면 변경됨
    if (totalSelected !== initial.bosses.length) return true;

    // 각 보스의 내용 비교
    const initialMap = new Map(initial.bosses.map(b => [b.boss_name, b]));
    for (const [bossName, entry] of Object.entries(selected)) {
      const initEntry = initialMap.get(bossName);
      if (!initEntry ||
          initEntry.difficulty !== entry.difficulty ||
          initEntry.party_size !== entry.party_size) {
        return true;
      }
    }
    return false;
  }, [initial, selected, weeklySelectedCount, monthlySelectedCount]);

  // 선택된 보스가 있는지 확인 (초기화 버튼용)
  const canReset = useMemo(() => {
    const totalSelected = weeklySelectedCount + monthlySelectedCount;
    return totalSelected > 0;
  }, [weeklySelectedCount, monthlySelectedCount]);

  function selectDifficulty(info: BossInfo) {
    setSelected((prev) => {
      const existing = prev[info.name];
      // 같은 난이도 재클릭 → 선택 해제
      if (existing?.difficulty === info.difficulty) {
        const next = { ...prev };
        delete next[info.name];
        return next;
      }
      // 주간 보스인데 12개 한도 초과
      if (!info.is_monthly && !existing) {
        const weeklyCount = Object.values(prev).filter((b) => !monthlyBossNames.has(b.boss_name)).length;
        if (weeklyCount >= MAX_BOSSES) return prev;
      }
      // 난이도 교체 또는 신규 선택 — 선택 = 클리어로 즉시 반영
      return {
        ...prev,
        [info.name]: {
          boss_name: info.name,
          difficulty: info.difficulty,
          crystal_price: info.crystal_price,
          party_size: existing?.party_size ?? 1,
          is_cleared: true,
          is_monthly: info.is_monthly,
        },
      };
    });
  }

  function setPartySize(bossName: string, size: number) {
    setSelected((prev) => ({
      ...prev,
      [bossName]: { ...prev[bossName], party_size: Math.max(1, Math.min(6, size)) },
    }));
  }

  function resetAll() {
    setSelected({});
  }

  async function handleSave() {
    setSaving(true);
    await onSave({
      user_id: userId,
      char_name: charName,
      weekly_key: weeklyKey,
      bosses: Object.values(selected),
      total_earnings: weeklyEarnings,
    });
    setSaving(false);
  }

  return (
    <div className="space-y-4">
      {/* 상단 요약 */}
      <div className="card flex items-center justify-between flex-wrap gap-3">
        <div>
          <p className="text-xs text-maple-muted">선택된 주간 보스</p>
          <p className="font-bold">
            <span className={weeklySelectedCount >= MAX_BOSSES ? "text-maple-red" : "text-maple-yellow"}>
              {weeklySelectedCount}
            </span>
            <span className="text-maple-muted"> / {MAX_BOSSES}</span>
          </p>
        </div>
        {monthlySelectedCount > 0 && (
          <div>
            <p className="text-xs text-maple-muted">선택된 월간 보스</p>
            <p className="font-bold text-maple-yellow">{monthlySelectedCount}</p>
          </div>
        )}
        <div className="text-right">
          <p className="text-xs text-maple-muted">예상 주간 수익</p>
          <p className="font-bold text-maple-green">{formatMeso(weeklyEarnings)}</p>
        </div>
        {monthlyEarnings > 0 && (
          <div className="text-right">
            <p className="text-xs text-maple-muted">예상 월간 수익</p>
            <p className="font-bold text-maple-yellow">{formatMeso(monthlyEarnings)}</p>
          </div>
        )}
        <div className="flex gap-2">
          <button
            className="btn-ghost text-sm py-1.5 px-3"
            onClick={resetAll}
            disabled={!canReset}
          >
            초기화
          </button>
          <button
            className="btn-primary"
            onClick={handleSave}
            disabled={saving || !hasChanges}
          >
            {saving ? "저장 중..." : "저장"}
          </button>
        </div>
      </div>

      {/* 보스 목록 */}
      <div className="space-y-4">
        {/* 주간 보스 섹션 */}
        <div className="card">
          {weeklySelectedCount >= MAX_BOSSES && (
            <p className="text-maple-red text-xs mb-3">⚠ 주간 보스 12개 한도 도달 — 초기화하거나 선택을 해제하세요.</p>
          )}
          <div className="mb-3 pb-3 border-b border-maple-border">
            <h3 className="text-sm font-semibold text-maple-yellow">주간 보스</h3>
          </div>
          <div className="space-y-1">
            {groupedWeekly.map(([bossName, variants]) => {
            const sel = selected[bossName];
            const earning = sel ? formatMeso(Math.floor(sel.crystal_price / sel.party_size)) : null;
            const diffButtons = variants.map((v) => {
              const isSelected = sel?.difficulty === v.difficulty;
              const isDisabled = !isSelected && !sel && weeklySelectedCount >= MAX_BOSSES;
              return (
                <button
                  key={v.id}
                  onClick={() => !isDisabled && selectDifficulty(v)}
                  disabled={isDisabled}
                  className={`px-2 py-0.5 rounded text-xs font-medium transition-colors border
                    ${isSelected
                      ? "bg-maple-yellow text-maple-dark border-maple-yellow"
                      : isDisabled
                        ? "border-maple-border text-maple-muted opacity-30 cursor-not-allowed"
                        : "border-maple-border text-maple-muted hover:border-maple-yellow hover:text-maple-yellow"
                    }`}
                >
                  {v.difficulty}
                </button>
              );
            });
            const stepper = sel ? (
              <div className="flex items-center gap-0.5 text-xs text-maple-muted shrink-0">
                <button
                  type="button"
                  onClick={() => setPartySize(bossName, sel.party_size - 1)}
                  disabled={sel.party_size <= 1}
                  className="w-5 h-5 rounded border border-maple-border hover:border-maple-yellow
                             hover:text-maple-yellow flex items-center justify-center
                             disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                >−</button>
                <span className="w-5 text-center font-medium text-maple-text">{sel.party_size}</span>
                <button
                  type="button"
                  onClick={() => setPartySize(bossName, sel.party_size + 1)}
                  disabled={sel.party_size >= 6}
                  className="w-5 h-5 rounded border border-maple-border hover:border-maple-yellow
                             hover:text-maple-yellow flex items-center justify-center
                             disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                >+</button>
                <span className="ml-0.5">인</span>
              </div>
            ) : null;

            return (
              <div
                key={bossName}
                className={`rounded-lg px-3 py-2 transition-colors
                  ${sel ? "bg-maple-yellow/5 border border-maple-yellow/30" : "border border-transparent hover:border-maple-border"}`}
              >
                {/* 모바일: 2행 레이아웃 */}
                <div className="sm:hidden">
                  <div className="flex items-center justify-between mb-1">
                    <span className={`text-sm font-medium ${sel ? "text-maple-yellow" : "text-maple-text"}`}>
                      {bossName}
                    </span>
                    {earning && <span className="text-maple-yellow text-xs font-medium">{earning}</span>}
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex flex-wrap gap-1 flex-1">{diffButtons}</div>
                    {stepper}
                  </div>
                </div>

                {/* 데스크탑: 1행 레이아웃 */}
                <div className="hidden sm:flex items-center gap-3">
                  <span className={`w-32 text-sm font-medium shrink-0 ${sel ? "text-maple-yellow" : "text-maple-text"}`}>
                    {bossName}
                  </span>
                  <div className="flex flex-wrap gap-1 flex-1">{diffButtons}</div>
                  {sel && (
                    <div className="flex items-center gap-2 shrink-0">
                      {stepper}
                      <span className="text-maple-yellow text-xs w-16 text-right">{earning}</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
          </div>
        </div>

        {/* 월간 보스 섹션 */}
        {groupedMonthly.length > 0 && (
          <div className="card">
            <div className="mb-3 pb-3 border-b border-maple-border">
              <h3 className="text-sm font-semibold text-maple-yellow">월간 보스</h3>
            </div>
            <div className="space-y-1">
              {groupedMonthly.map(([bossName, variants]) => {
                const sel = selected[bossName];
                const earning = sel ? formatMeso(Math.floor(sel.crystal_price / sel.party_size)) : null;
                const isMonthlyCleared = clearedMonthlyThisMonth.has(bossName);
                const isSameWeek = weeklyKey === initialWeeklyKey;
                const isCrossMonth = isCrossMonthWeek(weeklyKey);
                // 같은 주차가 아니고, 달 경계 주도 아니고, 이미 체크했으면 disabled
                const isMonthlyDisabled = isMonthlyCleared && !isSameWeek && !isCrossMonth;
                const diffButtons = variants.map((v) => {
                  const isSelected = sel?.difficulty === v.difficulty;
                  const isDisabled = isMonthlyDisabled && !isSelected;
                  return (
                    <button
                      key={v.id}
                      onClick={() => !isDisabled && selectDifficulty(v)}
                      disabled={isDisabled}
                      className={`px-2 py-0.5 rounded text-xs font-medium transition-colors border
                        ${isSelected
                          ? "bg-maple-yellow text-maple-dark border-maple-yellow"
                          : isDisabled
                            ? "border-maple-border text-maple-muted opacity-30 cursor-not-allowed"
                            : "border-maple-border text-maple-muted hover:border-maple-yellow hover:text-maple-yellow"
                        }`}
                    >
                      {v.difficulty}
                    </button>
                  );
                });
                const stepper = sel ? (
                  <div className="flex items-center gap-0.5 text-xs text-maple-muted shrink-0">
                    <button
                      type="button"
                      onClick={() => setPartySize(bossName, sel.party_size - 1)}
                      disabled={sel.party_size <= 1}
                      className="w-5 h-5 rounded border border-maple-border hover:border-maple-yellow
                                 hover:text-maple-yellow flex items-center justify-center
                                 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                    >−</button>
                    <span className="w-5 text-center font-medium text-maple-text">{sel.party_size}</span>
                    <button
                      type="button"
                      onClick={() => setPartySize(bossName, sel.party_size + 1)}
                      disabled={sel.party_size >= 6}
                      className="w-5 h-5 rounded border border-maple-border hover:border-maple-yellow
                                 hover:text-maple-yellow flex items-center justify-center
                                 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                    >+</button>
                    <span className="ml-0.5">인</span>
                  </div>
                ) : null;

                return (
                  <div
                    key={bossName}
                    className={`rounded-lg px-3 py-2 transition-colors
                      ${sel ? "bg-maple-yellow/5 border border-maple-yellow/30" : "border border-transparent hover:border-maple-border"}`}
                  >
                    {/* 모바일: 2행 레이아웃 */}
                    <div className="sm:hidden">
                      <div className="flex items-center justify-between mb-1">
                        <span className={`text-sm font-medium ${sel ? "text-maple-yellow" : "text-maple-text"}`}>
                          {bossName}
                        </span>
                        {earning && <span className="text-maple-yellow text-xs font-medium">{earning}</span>}
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="flex flex-wrap gap-1 flex-1">{diffButtons}</div>
                        {stepper}
                      </div>
                    </div>

                    {/* 데스크탑: 1행 레이아웃 */}
                    <div className="hidden sm:flex items-center gap-3">
                      <span className={`w-32 text-sm font-medium shrink-0 ${sel ? "text-maple-yellow" : "text-maple-text"}`}>
                        {bossName}
                      </span>
                      <div className="flex flex-wrap gap-1 flex-1">{diffButtons}</div>
                      {sel && (
                        <div className="flex items-center gap-2 shrink-0">
                          {stepper}
                          <span className="text-maple-yellow text-xs w-16 text-right">{earning}</span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
