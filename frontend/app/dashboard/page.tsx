"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  getMe, listCharacters, getEarningsHistory, registerCharacter,
  deleteCharacter, syncCharacter, listUsers, getPartyParticipationRanking,
  type User, type Character, type EarningsRecord, type ParticipationRank,
} from "@/lib/api";
import { removeToken } from "@/lib/api";
import CharacterCard from "@/components/CharacterCard";
import EarningsChart from "@/components/EarningsChart";
import EarningsLeaderboard from "@/components/EarningsLeaderboard";
import PartyParticipationRanking from "@/components/PartyParticipationRanking";

function getCurrentWeekKey(): string {
  const now = new Date();
  const jan4 = new Date(now.getFullYear(), 0, 4);
  const weekOne = new Date(jan4);
  weekOne.setDate(jan4.getDate() - jan4.getDay());
  const daysDiff = (now.getTime() - weekOne.getTime()) / (24 * 60 * 60 * 1000);
  const week = Math.floor(daysDiff / 7) + 1;
  return `${now.getFullYear()}-W${String(week).padStart(2, "0")}`;
}

export default function DashboardPage() {
  const router = useRouter();
  const [user,                  setUser]                  = useState<User | null>(null);
  const [chars,                 setChars]                 = useState<Character[]>([]);
  const [earnings,              setEarnings]              = useState<EarningsRecord[]>([]);
  const [allUsers,              setAllUsers]              = useState<User[]>([]);
  const [participationRanking,  setParticipationRanking]  = useState<ParticipationRank[]>([]);
  const [weeklyKey,             setWeeklyKey]             = useState("");
  const [newChar,               setNewChar]               = useState("");
  const [addLoading,            setAddLoading]            = useState(false);
  const [addError,              setAddError]              = useState("");
  const [syncing,               setSyncing]               = useState<string | null>(null);

  async function load() {
    try {
      const me = await getMe();
      setUser(me);
      const wk = getCurrentWeekKey();
      setWeeklyKey(wk);
      const [cs, hist, all, participation] = await Promise.all([
        listCharacters(me.user_id),
        getEarningsHistory(me.user_id),
        listUsers(),
        getPartyParticipationRanking(wk, 20),
      ]);
      setChars(cs.sort((a, b) => {
        if (a.is_main !== b.is_main) return a.is_main ? -1 : 1;
        return (b.level ?? 0) - (a.level ?? 0);
      }));
      setEarnings(hist);
      setAllUsers(all);
      setParticipationRanking(participation);
    } catch {
      router.push("/login");
    }
  }

  useEffect(() => { load(); }, []);

  async function handleAddChar() {
    if (!user || !newChar.trim()) return;
    setAddError("");
    setAddLoading(true);
    try {
      const char = await registerCharacter(user.user_id, newChar.trim());
      setChars((prev) => [...prev, char]);
      setNewChar("");
    } catch (e: unknown) {
      setAddError(e instanceof Error ? e.message : "등록 실패");
    } finally {
      setAddLoading(false);
    }
  }

  async function handleDelete(charName: string) {
    if (!user) return;
    if (!confirm(`"${charName}"을(를) 삭제하시겠습니까?`)) return;
    await deleteCharacter(user.user_id, charName);
    setChars((prev) => prev.filter((c) => c.char_name !== charName));
  }

  async function handleSync(charName: string) {
    if (!user) return;
    setSyncing(charName);
    try {
      const updated = await syncCharacter(user.user_id, charName);
      setChars((prev) => prev.map((c) => (c.char_name === charName ? updated : c)));
    } catch (e: unknown) {
      const errorMsg = e instanceof Error ? e.message : "넥슨 API 동기화 실패";
      alert(errorMsg);
    } finally {
      setSyncing(null);
    }
  }

  function logout() {
    removeToken();
    router.push("/login");
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
      {/* 헤더 */}
      <header className="border-b border-maple-border px-6 py-3 flex items-center justify-between">
        <h1 className="text-maple-yellow font-bold text-lg">🍁 MapleBoss</h1>
        <nav className="flex items-center gap-4">
          <span className="text-maple-muted text-sm">{user.display_name}</span>
          <button onClick={logout} className="btn-ghost text-sm py-1 px-3">
            로그아웃
          </button>
        </nav>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-6 space-y-6">
        {/* 수익 차트 배너 */}
        <EarningsChart
          data={earnings}
          weeklyTotal={user.weekly_earnings}
          monthlyTotal={user.monthly_earnings}
        />

        {/* 부캐 추가 + 파티 스케줄 */}
        <div className="flex flex-col sm:flex-row gap-3 items-stretch">
          <div className="card flex-1">
            <h2 className="font-semibold mb-3">부캐 추가</h2>
            <div className="flex gap-2">
              <input
                className="input-field flex-1"
                placeholder="부캐 닉네임 입력 (넥슨 API로 자동 동기화)"
                value={newChar}
                onChange={(e) => setNewChar(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAddChar()}
              />
              <button
                className="btn-primary whitespace-nowrap"
                onClick={handleAddChar}
                disabled={addLoading || !newChar.trim()}
              >
                {addLoading ? "추가 중..." : "추가"}
              </button>
            </div>
            {addError && <p className="text-maple-red text-xs mt-2">{addError}</p>}
            <p className="text-maple-muted text-xs mt-2">
              * 본캐는 자동 등록되어 있습니다. 직접 키운 부캐만 추가하세요.
            </p>
          </div>
          <button
            onClick={() => router.push("/parties")}
            className="card flex flex-col items-center justify-center gap-2 flex-1 hover:border-maple-yellow transition-colors"
          >
            <span className="text-2xl">🗓</span>
            <span className="text-sm font-medium text-maple-text">파티 스케줄러</span>
          </button>
        </div>

        {/* 캐릭터 카드 그리드 */}
        <div>
          <h2 className="font-semibold mb-3">
            내 캐릭터 ({chars.length}개)
          </h2>
          {chars.length === 0 ? (
            <p className="text-maple-muted text-sm">등록된 캐릭터가 없습니다.</p>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
              {chars.map((c) => (
                <div key={c.char_name} className="relative">
                  <CharacterCard
                    char={c}
                    onClick={() => router.push(`/characters/${encodeURIComponent(c.char_name)}`)}
                    onDelete={() => handleDelete(c.char_name)}
                  />
                  {/* 동기화 버튼 */}
                  <button
                    onClick={() => handleSync(c.char_name)}
                    disabled={syncing === c.char_name}
                    className="absolute top-2 left-2 text-[10px] text-maple-muted hover:text-maple-yellow
                               transition-colors disabled:opacity-50"
                    title="넥슨 API 동기화"
                  >
                    {syncing === c.char_name ? "⟳" : "↺"}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 수익 순위표 + 파티 참여 순위 */}
        <div>
          <h2 className="font-semibold mb-3">순위</h2>
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <EarningsLeaderboard users={allUsers} currentUserId={user.user_id} />
            </div>
            <div className="flex-1">
              <PartyParticipationRanking
                ranking={participationRanking}
                allUsers={allUsers}
                currentUserId={user.user_id}
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
