"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { login } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError]       = useState("");
  const [loading, setLoading]   = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(username.trim(), password);
      router.push("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "로그인 실패");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-maple-dark">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-maple-yellow">🍁 MapleBoss</h1>
          <p className="text-maple-muted mt-1 text-sm">주간 보스 대시보드</p>
        </div>

        <form onSubmit={handleSubmit} className="card space-y-4">
          <div>
            <label className="block text-sm text-maple-muted mb-1">본캐 닉네임</label>
            <input
              className="input-field"
              placeholder="캐릭터 닉네임 입력"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoFocus
              required
            />
          </div>
          <div>
            <label className="block text-sm text-maple-muted mb-1">비밀번호</label>
            <input
              className="input-field"
              type="password"
              placeholder="비밀번호 입력"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          {error && (
            <p className="text-maple-red text-sm">{error}</p>
          )}

          <button
            type="submit"
            className="btn-primary w-full"
            disabled={loading}
          >
            {loading ? "로그인 중..." : "로그인"}
          </button>

          <div className="text-center">
            <p className="text-maple-muted text-sm">
              아직 계정이 없으신가요?{" "}
              <Link href="/signup" className="text-maple-yellow hover:underline">
                회원가입
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
}
