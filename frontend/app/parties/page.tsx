"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  getMe, listPartiesByUser, listBosses, listCharacters, listUsers,
  createParty, deleteParty,
  type User, type Party, type BossInfo, type Character,
} from "@/lib/api";
import CreatePartyModal from "@/components/CreatePartyModal";

// 이번 주 목요일 날짜 문자열 (주간 키로 사용)
function currentWeekKey(): string {
  const today = new Date();
  const daysSince = (today.getDay() + 3) % 7;
  const thu = new Date(today);
  thu.setDate(today.getDate() - daysSince);
  return thu.toISOString().split("T")[0];
}

const STORAGE_KEY = `boss_done_${currentWeekKey()}`;

function loadDoneIds(): Set<string> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? new Set(JSON.parse(raw)) : new Set();
  } catch {
    return new Set();
  }
}

function saveDoneIds(ids: Set<string>) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify([...ids]));
}

export default function PartiesPage() {
  const router = useRouter();
  const [user,         setUser]         = useState<User | null>(null);
  const [parties,      setParties]      = useState<Party[]>([]);
  const [bossList,     setBossList]     = useState<BossInfo[]>([]);
  const [myChars,      setMyChars]      = useState<Character[]>([]);
  const [allUsers,     setAllUsers]     = useState<User[]>([]);
  const [showModal,    setShowModal]    = useState(false);
  const [editingParty, setEditingParty] = useState<Party | undefined>();
  const [doneIds,      setDoneIds]      = useState<Set<string>>(new Set());
  const [selectedChar, setSelectedChar] = useState<string>("");

  useEffect(() => {
    setDoneIds(loadDoneIds());
  }, []);

  async function load(me: User) {
    const [list, bl, chars, users] = await Promise.all([
      listPartiesByUser(me.user_id),
      listBosses(),
      listCharacters(me.user_id),
      listUsers(),
    ]);
    setParties(list.sort((a, b) => b.created_at.localeCompare(a.created_at)));
    setBossList(bl);
    const sortedChars = chars.sort((a, b) => {
      if (a.is_main !== b.is_main) return a.is_main ? -1 : 1;
      return (b.level ?? 0) - (a.level ?? 0);
    });
    setMyChars(sortedChars);
    // 첫 번째 캐릭터를 기본 선택
    if (sortedChars.length > 0) {
      setSelectedChar(sortedChars[0].char_name);
    }
    setAllUsers(users);
  }

  useEffect(() => {
    getMe()
      .then((me) => { setUser(me); load(me); })
      .catch(() => router.push("/login"));
  }, []);

  function toggleDone(partyId: string) {
    setDoneIds((prev) => {
      const next = new Set(prev);
      if (next.has(partyId)) next.delete(partyId);
      else next.add(partyId);
      saveDoneIds(next);
      return next;
    });
  }

  async function handleSubmit(
    partyData: Omit<Party, "party_id" | "created_at" | "pk" | "sk" | "gsi1pk" | "gsi1sk">,
    oldParty?: Party
  ) {
    if (!user) return;
    if (oldParty?.sk) {
      await deleteParty(oldParty.scheduled_date, oldParty.sk);
      setParties((prev) => prev.filter((p) => p.sk !== oldParty.sk));
    }
    const created = await createParty(partyData, user.user_id);
    setParties((prev) =>
      [created, ...prev].sort((a, b) => b.created_at.localeCompare(a.created_at))
    );
  }

  async function handleDelete(party: Party) {
    if (!confirm("파티를 삭제하시겠습니까?")) return;
    if (!party.sk) return;
    await deleteParty(party.scheduled_date, party.sk);
    setParties((prev) => prev.filter((p) => p.sk !== party.sk));
  }

  function openEdit(party: Party) {
    setEditingParty(party);
    setShowModal(true);
  }

  function closeModal() {
    setShowModal(false);
    setEditingParty(undefined);
  }

  // 선택된 캐릭터가 속한 파티들만 필터링
  const filteredParties = parties.filter((party) =>
    party.members.some((m) => m.char_name === selectedChar)
  );

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center text-maple-muted">
        로딩 중...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-maple-dark">
      <header className="border-b border-maple-border px-6 py-3 flex items-center gap-3">
        <button
          onClick={() => router.push("/dashboard")}
          className="text-maple-muted hover:text-maple-yellow transition-colors"
        >
          ← 대시보드
        </button>
        <h2 className="font-semibold text-maple-text">파티 스케줄러</h2>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-6 space-y-4">
        {/* 캐릭터 탭 */}
        <div className="space-y-2">
          <p className="text-xs text-maple-muted">캐릭터 선택</p>
          <div className="space-y-2">
            {myChars.map((char) => (
              <button
                key={char.char_name}
                onClick={() => setSelectedChar(char.char_name)}
                className={`w-full text-left px-4 py-3 rounded-lg font-medium transition-colors border
                  ${selectedChar === char.char_name
                    ? "bg-maple-yellow text-maple-dark border-maple-yellow"
                    : "border-maple-border text-maple-text hover:border-maple-yellow hover:bg-maple-border/30"
                  }`}
              >
                <div className="flex items-center justify-between">
                  <span>{char.char_name}</span>
                  <span className="text-xs opacity-70">Lv. {char.level}</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="flex justify-end">
          <button className="btn-primary" onClick={() => setShowModal(true)}>
            + 파티 추가
          </button>
        </div>

        {filteredParties.length === 0 ? (
          <div className="card text-center text-maple-muted py-12">
            {selectedChar}의 파티가 없습니다.
          </div>
        ) : (
          <div className="space-y-3">
            {filteredParties.map((party) => {
              const done = doneIds.has(party.party_id);
              return (
                <div
                  key={party.sk ?? party.party_id}
                  className={`card transition-opacity ${done ? "opacity-50" : ""}`}
                >
                  <div className="flex items-start justify-between gap-3">
                    {/* 완료 체크박스 */}
                    <button
                      onClick={() => toggleDone(party.party_id)}
                      className={`mt-0.5 shrink-0 w-5 h-5 rounded border-2 flex items-center justify-center transition-colors
                        ${done
                          ? "bg-maple-yellow border-maple-yellow text-maple-dark"
                          : "border-maple-border hover:border-maple-yellow"
                        }`}
                      title={done ? "완료 취소" : "이번 주 완료"}
                    >
                      {done && (
                        <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
                          <path d="M1 4L3.5 6.5L9 1" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      )}
                    </button>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <h3 className={`font-semibold ${done ? "line-through text-maple-muted" : "text-maple-text"}`}>
                            {party.boss_name}
                            <span className="text-maple-muted text-xs ml-2 no-underline">[{party.difficulty}]</span>
                          </h3>
                          {party.memo && (
                            <p className="text-maple-muted text-xs mt-1">{party.memo}</p>
                          )}
                        </div>
                        {party.members.some((m) => m.user_id === user.user_id) && (
                          <div className="flex gap-3 shrink-0">
                            <button
                              onClick={() => openEdit(party)}
                              className="text-maple-muted hover:text-maple-yellow text-xs transition-colors"
                            >
                              수정
                            </button>
                            <button
                              onClick={() => handleDelete(party)}
                              className="text-maple-muted hover:text-maple-red text-xs transition-colors"
                            >
                              삭제
                            </button>
                          </div>
                        )}
                      </div>

                      <div className="flex flex-wrap gap-1.5 mt-3">
                        {party.members.map((m, i) => (
                          <span
                            key={i}
                            className={`badge px-2 py-0.5 rounded text-xs
                              ${m.user_id === user.user_id
                                ? "bg-maple-yellow/20 text-maple-yellow"
                                : m.is_external
                                ? "bg-maple-border/50 text-maple-muted border border-maple-border"
                                : "bg-maple-border text-maple-muted"
                              }`}
                          >
                            {m.display_name}
                            {m.is_external && (
                              <span className="ml-1 opacity-60">외부인</span>
                            )}
                            {!m.is_external && m.char_name && m.char_name !== m.user_id && (
                              <span className="opacity-60 ml-1">({m.char_name})</span>
                            )}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </main>

      {showModal && user && (
        <CreatePartyModal
          userId={user.user_id}
          displayName={user.display_name}
          myChars={myChars}
          allUsers={allUsers}
          bossList={bossList}
          initial={editingParty}
          onClose={closeModal}
          onSubmit={handleSubmit}
        />
      )}
    </div>
  );
}
