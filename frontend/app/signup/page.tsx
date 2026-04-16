"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { registerUser, login } from "@/lib/api";

export default function SignupPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    // 검증
    if (!username.trim()) {
      setError("닉네임을 입력하세요.");
      return;
    }
    if (!password) {
      setError("비밀번호를 입력하세요.");
      return;
    }
    if (password !== passwordConfirm) {
      setError("비밀번호가 일치하지 않습니다.");
      return;
    }
    if (password.length < 4) {
      setError("비밀번호는 최소 4자 이상이어야 합니다.");
      return;
    }

    setLoading(true);
    try {
      // 회원가입
      await registerUser(username.trim(), password);
      // 승인 대기 알림
      alert("승인 대기중입니다. 잠시만 기다려주세요.");
      router.push("/login");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "회원가입 실패");
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
          <h2 className="text-maple-text font-semibold mb-4">회원가입</h2>

          <div>
            <label className="block text-sm text-maple-muted mb-1">닉네임</label>
            <input
              className="input-field"
              placeholder="로그인할 때 사용할 닉네임"
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

          <div>
            <label className="block text-sm text-maple-muted mb-1">비밀번호 확인</label>
            <input
              className="input-field"
              type="password"
              placeholder="비밀번호 재입력"
              value={passwordConfirm}
              onChange={(e) => setPasswordConfirm(e.target.value)}
              required
            />
          </div>

          {error && <p className="text-maple-red text-sm">{error}</p>}

          <button
            type="submit"
            className="btn-primary w-full"
            disabled={loading}
          >
            {loading ? "가입 중..." : "회원가입"}
          </button>

          <div className="text-center">
            <p className="text-maple-muted text-sm">
              이미 계정이 있으신가요?{" "}
              <Link href="/login" className="text-maple-yellow hover:underline">
                로그인
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
}
