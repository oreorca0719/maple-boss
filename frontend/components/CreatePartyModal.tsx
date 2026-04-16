"use client";

import { useState, useEffect, useMemo } from "react";
import { listCharacters, type BossInfo, type PartyMember, type Party, type User, type Character } from "@/lib/api";

interface Props {
  userId: string;
  displayName: string;
  myChars: Character[];
  allUsers: User[];
  bossList: BossInfo[];
  initial?: Party;
  onClose: () => void;
  onSubmit: (
    party: Omit<Party, "party_id" | "created_at" | "pk" | "sk" | "gsi1pk" | "gsi1sk">,
    oldParty?: Party
  ) => Promise<void>;
}

const DIFFICULTY_ORDER = ["이지", "노말", "하드", "카오스", "익스트림"];

function currentMaplestoryThursday(): string {
  const today = new Date();
  const daysSince = (today.getDay() + 3) % 7;
  const thu = new Date(today);
  thu.setDate(today.getDate() - daysSince);
  return thu.toISOString().split("T")[0];
}

export default function CreatePartyModal({
  userId, displayName, myChars, allUsers, bossList, initial, onClose, onSubmit,
}: Props) {
  const isEdit = !!initial;

  const bossGroups = useMemo(() => {
    const map: Record<string, BossInfo[]> = {};
    for (const b of bossList) {
      if (!map[b.name]) map[b.name] = [];
      map[b.name].push(b);
    }
    for (const name in map) {
      map[name].sort((a, b) =>
        DIFFICULTY_ORDER.indexOf(a.difficulty) - DIFFICULTY_ORDER.indexOf(b.difficulty)
      );
    }
    return map;
  }, [bossList]);

  const bossNames = useMemo(
    () =>
      Object.entries(bossGroups)
        .sort(([, a], [, b]) => a[0].min_level - b[0].min_level)
        .map(([name]) => name),
    [bossGroups]
  );

  // ── 폼 상태 ───────────────────────────────────────────────────────
  const [bossName,    setBossName]    = useState(initial?.boss_name ?? "");
  const [difficulty,  setDifficulty]  = useState(initial?.difficulty ?? "");
  const [memo,        setMemo]        = useState(initial?.memo ?? "");

  // 파티장 캐릭터 (초기값: 수정 모드면 기존 멤버 중 내 캐릭, 없으면 본캐)
  const defaultLeaderChar = useMemo(() => {
    if (initial) {
      const me = initial.members.find((m) => m.user_id === userId);
      return me?.char_name ?? (myChars.find((c) => c.is_main)?.char_name ?? myChars[0]?.char_name ?? userId);
    }
    return myChars.find((c) => c.is_main)?.char_name ?? myChars[0]?.char_name ?? userId;
  }, []);

  const [leaderChar, setLeaderChar] = useState(defaultLeaderChar);

  // 파티원 목록 (파티장 제외)
  const [members, setMembers] = useState<PartyMember[]>(
    initial
      ? initial.members.filter((m) => m.user_id !== userId)
      : []
  );

  // 보스 변경 시 해당 보스의 첫 번째 난이도로 초기화
  useEffect(() => {
    if (!bossName) { setDifficulty(""); return; }
    const variants = bossGroups[bossName] ?? [];
    if (!variants.find((v) => v.difficulty === difficulty)) {
      setDifficulty(variants[0]?.difficulty ?? "");
    }
  }, [bossName]);

  // ── 멤버 추가 ─────────────────────────────────────────────────────
  const [memberFilter,      setMemberFilter]      = useState("");
  const [selectedUser,      setSelectedUser]      = useState<User | null>(null);
  const [selectedUserChars, setSelectedUserChars] = useState<Character[]>([]);
  const [selectedChar,      setSelectedChar]      = useState("");
  const [charLoading,       setCharLoading]       = useState(false);
  const [externalInput,     setExternalInput]     = useState("");
  const [memberError,       setMemberError]       = useState("");

  const candidateUsers = useMemo(
    () => allUsers.filter(
      (u) => u.user_id !== userId && !members.some((m) => m.user_id === u.user_id)
    ),
    [allUsers, userId, members]
  );

  const filteredUsers = useMemo(() => {
    const q = memberFilter.trim().toLowerCase();
    return q ? candidateUsers.filter((u) => u.display_name.toLowerCase().includes(q)) : candidateUsers;
  }, [candidateUsers, memberFilter]);

  async function handleSelectUser(user: User) {
    setSelectedUser(user);
    setSelectedChar("");
    setMemberError("");
    setCharLoading(true);
    try {
      const chars = await listCharacters(user.user_id);
      const sorted = chars.sort((a, b) => {
        if (a.is_main !== b.is_main) return a.is_main ? -1 : 1;
        return (b.level ?? 0) - (a.level ?? 0);
      });
      setSelectedUserChars(sorted);
      setSelectedChar(sorted[0]?.char_name ?? user.user_id);
    } catch {
      setSelectedUserChars([]);
      setSelectedChar(user.user_id);
    } finally {
      setCharLoading(false);
    }
  }

  function addSelectedMember() {
    if (!selectedUser || 1 + members.length + 1 > 6) return;
    setMembers((prev) => [...prev, {
      user_id: selectedUser.user_id,
      display_name: selectedUser.display_name,
      char_name: selectedChar || selectedUser.user_id,
      is_external: false,
    }]);
    setSelectedUser(null);
    setSelectedUserChars([]);
    setSelectedChar("");
    setMemberFilter("");
    setMemberError("");
  }

  function addExternalMember() {
    const name = externalInput.trim();
    if (!name) return;
    if (1 + members.length + 1 > 6) { setMemberError("파티 인원이 가득 찼습니다."); return; }
    if (members.some((m) => m.display_name === name)) { setMemberError("이미 추가된 멤버입니다."); return; }
    setMembers((prev) => [...prev, {
      user_id: `external#${name}`,
      display_name: name,
      char_name: name,
      is_external: true,
    }]);
    setExternalInput("");
    setMemberError("");
  }

  function removeMember(userId: string) {
    setMembers((prev) => prev.filter((m) => m.user_id !== userId));
  }

  // ── 제출 ──────────────────────────────────────────────────────────
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!bossName) { setError("보스를 선택하세요."); return; }
    if (!difficulty) { setError("난이도를 선택하세요."); return; }
    setError("");
    setLoading(true);

    // 파티장을 첫 번째로 포함한 전체 멤버 목록
    const allMembers: PartyMember[] = [
      { user_id: userId, display_name: displayName, char_name: leaderChar },
      ...members,
    ];

    try {
      await onSubmit(
        {
          boss_name: bossName,
          difficulty,
          scheduled_date: currentMaplestoryThursday(),
          scheduled_time: "00:00",
          members: allMembers,
          memo: memo || undefined,
          created_by: userId,
        },
        initial
      );
      onClose();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "실패");
    } finally {
      setLoading(false);
    }
  }

  const difficulties = bossGroups[bossName] ?? [];
  const totalMembers = 1 + members.length;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-md mx-4 card max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold">{isEdit ? "파티 수정" : "파티 추가"}</h2>
          <button onClick={onClose} className="text-maple-muted hover:text-maple-red">✕</button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* 보스 + 난이도 */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-maple-muted mb-1 block">보스</label>
              <select
                className="input-field"
                value={bossName}
                onChange={(e) => setBossName(e.target.value)}
              >
                <option value="">보스 선택</option>
                {bossNames.map((n) => (
                  <option key={n} value={n}>{n}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-maple-muted mb-1 block">난이도</label>
              <select
                className="input-field"
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                disabled={!bossName}
              >
                {difficulties.length === 0
                  ? <option value="">—</option>
                  : difficulties.map((d) => (
                      <option key={d.id} value={d.difficulty}>{d.difficulty}</option>
                    ))
                }
              </select>
            </div>
          </div>

          {/* 파티장 캐릭터 선택 */}
          <div>
            <label className="text-xs text-maple-muted mb-1 block">
              내 참여 캐릭터 (파티장)
            </label>
            <select
              className="input-field"
              value={leaderChar}
              onChange={(e) => setLeaderChar(e.target.value)}
            >
              {myChars.length === 0 ? (
                <option value={userId}>{displayName}</option>
              ) : (
                myChars.map((c) => (
                  <option key={c.char_name} value={c.char_name}>
                    {c.char_name}{c.is_main ? " (본캐)" : ""}
                  </option>
                ))
              )}
            </select>
          </div>

          {/* 파티원 목록 */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs text-maple-muted">
                파티 멤버 ({totalMembers}/6)
              </label>
            </div>

            {/* 파티장 (고정) */}
            <div className="flex items-center gap-2 bg-maple-yellow/10 border border-maple-yellow/30 rounded px-3 py-1.5 mb-1.5">
              <span className="flex-1 text-sm text-maple-yellow">
                {displayName}
                <span className="text-xs text-maple-muted ml-1">
                  ({leaderChar}) · 파티장
                </span>
              </span>
            </div>

            {/* 파티원 */}
            <div className="space-y-1.5">
              {members.map((m) => (
                <div key={m.user_id} className="flex items-center gap-2 bg-maple-dark rounded px-3 py-1.5">
                  <span className="flex-1 text-sm text-maple-text">{m.display_name}</span>
                  {m.is_external && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-maple-border text-maple-muted border border-maple-border">
                      외부인
                    </span>
                  )}
                  <button
                    type="button"
                    onClick={() => removeMember(m.user_id)}
                    className="text-maple-muted hover:text-maple-red text-xs"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>

            {/* 멤버 추가 */}
            {totalMembers < 6 && (
              <div className="mt-2 space-y-2">
                {/* 가입 멤버 드롭다운 */}
                {candidateUsers.length > 0 && !selectedUser && (
                  <div className="space-y-1">
                    <input
                      className="input-field text-sm"
                      placeholder="닉네임 검색..."
                      value={memberFilter}
                      onChange={(e) => setMemberFilter(e.target.value)}
                    />
                    {filteredUsers.length > 0 && (
                      <div className="border border-maple-border rounded overflow-hidden max-h-32 overflow-y-auto">
                        {filteredUsers.map((u) => (
                          <button
                            key={u.user_id}
                            type="button"
                            onClick={() => handleSelectUser(u)}
                            className="w-full text-left px-3 py-1.5 text-sm text-maple-text hover:bg-maple-yellow/10 hover:text-maple-yellow transition-colors"
                          >
                            {u.display_name}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* 선택된 유저 + 캐릭터 선택 */}
                {selectedUser && (
                  <div className="bg-maple-yellow/10 border border-maple-yellow/30 rounded px-3 py-2 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-maple-yellow">{selectedUser.display_name}</span>
                      <button type="button" onClick={() => { setSelectedUser(null); setSelectedUserChars([]); }} className="text-maple-muted hover:text-maple-red text-xs">✕</button>
                    </div>
                    {charLoading ? (
                      <p className="text-xs text-maple-muted">캐릭터 불러오는 중...</p>
                    ) : selectedUserChars.length > 0 ? (
                      <select
                        className="input-field text-xs py-1"
                        value={selectedChar}
                        onChange={(e) => setSelectedChar(e.target.value)}
                      >
                        {selectedUserChars.map((c) => (
                          <option key={c.char_name} value={c.char_name}>
                            {c.char_name}{c.is_main ? " (본캐)" : ""} Lv.{c.level}
                          </option>
                        ))}
                      </select>
                    ) : null}
                    <button
                      type="button"
                      onClick={addSelectedMember}
                      className="w-full text-xs text-center text-maple-yellow hover:underline"
                    >
                      + 파티에 추가
                    </button>
                  </div>
                )}

                {/* 외부인 추가 */}
                <div className="flex gap-2 items-center">
                  <input
                    className="input-field flex-1 text-sm"
                    placeholder="외부인 닉네임 직접 입력"
                    value={externalInput}
                    onChange={(e) => { setExternalInput(e.target.value); setMemberError(""); }}
                    onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addExternalMember())}
                  />
                  <button
                    type="button"
                    onClick={addExternalMember}
                    disabled={!externalInput.trim()}
                    className="btn-ghost text-sm py-1 px-3 whitespace-nowrap"
                  >
                    외부인 추가
                  </button>
                </div>
                {memberError && <p className="text-maple-red text-xs">{memberError}</p>}
              </div>
            )}
          </div>

          {/* 메모 */}
          <div>
            <label className="text-xs text-maple-muted mb-1 block">메모 (선택)</label>
            <input
              className="input-field"
              placeholder="파티 공지 등"
              value={memo}
              onChange={(e) => setMemo(e.target.value)}
            />
          </div>

          {error && <p className="text-maple-red text-xs">{error}</p>}

          <div className="flex gap-2 justify-end">
            <button type="button" onClick={onClose} className="btn-ghost">취소</button>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? "처리 중..." : isEdit ? "수정 완료" : "파티 생성"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
