import Cookies from "js-cookie";

// 빌드 시 NEXT_PUBLIC_API_URL 미설정 → 빈 문자열 → nginx 상대 경로 라우팅
const BASE = process.env.NEXT_PUBLIC_API_URL || "";

function getToken(): string | undefined {
  return Cookies.get("maple_token");
}

export function setToken(token: string) {
  Cookies.set("maple_token", token, { expires: 7, sameSite: "lax" });
}

export function removeToken() {
  Cookies.remove("maple_token");
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  });
  if (!res.ok) {
    const msg = await res.text().catch(() => res.statusText);
    throw new Error(msg);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// ── Auth ──────────────────────────────────────────────────────
export async function login(username: string, password: string) {
  const body = new URLSearchParams({ username, password });
  const res = await fetch(`${BASE}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!res.ok) throw new Error("닉네임 또는 비밀번호가 올바르지 않습니다.");
  const data: { access_token: string } = await res.json();
  setToken(data.access_token);
  return data;
}

export function getMe() {
  return request<User>("/api/v1/auth/me");
}

// ── Users ─────────────────────────────────────────────────────
export function getUser(userId: string) {
  return request<User>(`/api/v1/users/${userId}`);
}

export function listUsers() {
  return request<User[]>("/api/v1/users");
}

export function getEarningsHistory(userId: string, weeks = 8) {
  return request<EarningsRecord[]>(
    `/api/v1/users/${userId}/earnings-history?weeks=${weeks}`
  );
}

// ── Characters ───────────────────────────────────────────────
export function listCharacters(userId: string) {
  return request<Character[]>(`/api/v1/users/${userId}/characters`);
}

export function registerCharacter(userId: string, charName: string) {
  return request<Character>(`/api/v1/users/${userId}/characters`, {
    method: "POST",
    body: JSON.stringify({ char_name: charName, user_id: userId }),
  });
}

export function syncCharacter(userId: string, charName: string) {
  return request<Character>(
    `/api/v1/users/${userId}/characters/${encodeURIComponent(charName)}/sync`,
    { method: "POST" }
  );
}

export function deleteCharacter(userId: string, charName: string) {
  return request<void>(
    `/api/v1/users/${userId}/characters/${encodeURIComponent(charName)}`,
    { method: "DELETE" }
  );
}

export function getChecklist(userId: string, charName: string, weeklyKey: string) {
  return request<BossChecklist>(
    `/api/v1/users/${userId}/characters/${encodeURIComponent(charName)}/checklist/${weeklyKey}`
  );
}

export function saveChecklist(userId: string, charName: string, checklist: BossChecklist) {
  return request<BossChecklist>(
    `/api/v1/users/${userId}/characters/${encodeURIComponent(charName)}/checklist`,
    { method: "PUT", body: JSON.stringify(checklist) }
  );
}

export function getClearedMonthlyBosses(userId: string, charName: string, weeklyKey: string) {
  return request<{ cleared_monthly_bosses: string[] }>(
    `/api/v1/users/${userId}/characters/${encodeURIComponent(charName)}/cleared-monthly?weekly_key=${weeklyKey}`
  );
}

// ── Bosses ────────────────────────────────────────────────────
export function listBosses() {
  return request<BossInfo[]>("/api/v1/bosses");
}

// ── Parties ───────────────────────────────────────────────────
export function listPartiesByDate(date: string) {
  return request<Party[]>(`/api/v1/parties/date/${date}`);
}

export function listPartiesByUser(userId: string, datePrefix?: string) {
  const qs = datePrefix ? `?date_prefix=${datePrefix}` : "";
  return request<Party[]>(`/api/v1/parties/user/${userId}${qs}`);
}

export function createParty(party: Omit<Party, "party_id" | "created_at" | "pk" | "sk" | "gsi1pk" | "gsi1sk">, createdBy: string) {
  return request<Party>(`/api/v1/parties?created_by=${encodeURIComponent(createdBy)}`, {
    method: "POST",
    body: JSON.stringify(party),
  });
}

export function deleteParty(date: string, sk: string) {
  return request<void>(`/api/v1/parties/${date}/${encodeURIComponent(sk)}`, {
    method: "DELETE",
  });
}

// ── Rankings ──────────────────────────────────────────────────
export function getPartyParticipationRanking(weeklyKey: string, limit = 10) {
  return request<ParticipationRank[]>(
    `/api/v1/rankings/party-participation/${weeklyKey}?limit=${limit}`
  );
}

// ── Types ─────────────────────────────────────────────────────
export interface User {
  user_id: string;
  display_name: string;
  weekly_earnings: number;
  monthly_earnings: number;
  created_at: string;
  updated_at: string;
}

export interface Character {
  char_name: string;
  user_id: string;
  job: string;
  job_detail: string;
  level: number;
  combat_power: number;
  image_url: string;
  server: string;
  synced_at: string;
  is_main?: boolean;
}

export interface BossEntry {
  boss_name: string;
  difficulty: string;
  crystal_price: number;
  party_size: number;
  is_cleared: boolean;
  is_monthly: boolean;
}

export interface BossChecklist {
  user_id: string;
  char_name: string;
  weekly_key: string;
  bosses: BossEntry[];
  total_earnings: number;
  pk?: string;
  sk?: string;
}

export interface BossInfo {
  id: string;
  name: string;
  difficulty: string;
  crystal_price: number;
  min_level: number;
  is_monthly: boolean;
}

export interface EarningsRecord {
  weekly_key: string;
  total_earnings: number;
}

export interface PartyMember {
  user_id: string;
  display_name: string;
  char_name: string;
  is_external?: boolean;
}

export interface Party {
  boss_name: string;
  difficulty: string;
  scheduled_date: string;
  scheduled_time: string;
  members: PartyMember[];
  memo?: string;
  party_id: string;
  created_by: string;
  created_at: string;
  pk?: string;
  sk?: string;
  gsi1pk?: string;
  gsi1sk?: string;
}

export interface ParticipationRank {
  user_id: string;
  party_count: number;
}
