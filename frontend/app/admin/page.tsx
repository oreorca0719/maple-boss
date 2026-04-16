"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  getMe, listPendingUsers, approveUser, deleteUser,
  type User,
} from "@/lib/api";

export default function AdminPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [pendingUsers, setPendingUsers] = useState<User[]>([]);
  const [allUsers, setAllUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const me = await getMe();
        if (!me.is_admin) {
          router.push("/dashboard");
          return;
        }
        setUser(me);
        const [pending, all] = await Promise.all([
          listPendingUsers(),
          listUsers(),
        ]);
        setPendingUsers(pending);
        setAllUsers(all);
      } catch {
        router.push("/login");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleApprove = async (userId: string) => {
    setActionInProgress(userId);
    try {
      await approveUser(userId, true);
      setPendingUsers((prev) => prev.filter((u) => u.user_id !== userId));
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "승인 실패");
    } finally {
      setActionInProgress(null);
    }
  };

  const handleReject = async (userId: string) => {
    setActionInProgress(userId);
    try {
      await approveUser(userId, false);
      setPendingUsers((prev) => prev.filter((u) => u.user_id !== userId));
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "거절 실패");
    } finally {
      setActionInProgress(null);
    }
  };

  const handleDelete = async (userId: string) => {
    if (!confirm(`"${userId}"을(를) 삭제하시겠습니까? (복구 불가)`)) return;
    setActionInProgress(userId);
    try {
      await deleteUser(userId);
      setPendingUsers((prev) => prev.filter((u) => u.user_id !== userId));
      setAllUsers((prev) => prev.filter((u) => u.user_id !== userId));
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "삭제 실패");
    } finally {
      setActionInProgress(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-maple-muted">
        로딩 중...
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-maple-dark">
      {/* 헤더 */}
      <header className="border-b border-maple-border px-6 py-3 flex items-center justify-between">
        <h1 className="text-maple-yellow font-bold text-lg">🍁 관리자 패널</h1>
        <nav className="flex items-center gap-4">
          <button
            onClick={() => router.push("/dashboard")}
            className="btn-ghost text-sm py-1 px-3"
          >
            대시보드
          </button>
        </nav>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {/* 가입 승인 대기 */}
        <section>
          <h2 className="font-semibold mb-3 text-maple-text">
            가입 승인 대기 ({pendingUsers.length}명)
          </h2>
          {pendingUsers.length === 0 ? (
            <p className="text-maple-muted text-sm">대기 중인 회원이 없습니다.</p>
          ) : (
            <div className="space-y-2">
              {pendingUsers.map((u) => (
                <div
                  key={u.user_id}
                  className="card flex items-center justify-between"
                >
                  <div>
                    <p className="text-maple-text font-medium">{u.user_id}</p>
                    <p className="text-maple-muted text-xs">
                      {new Date(u.created_at).toLocaleString("ko-KR")}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleApprove(u.user_id)}
                      disabled={actionInProgress === u.user_id}
                      className="btn-primary text-sm py-1 px-3 disabled:opacity-50"
                    >
                      승인
                    </button>
                    <button
                      onClick={() => handleReject(u.user_id)}
                      disabled={actionInProgress === u.user_id}
                      className="btn-ghost text-sm py-1 px-3 disabled:opacity-50"
                    >
                      거절
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* 전체 회원 목록 */}
        <section>
          <h2 className="font-semibold mb-3 text-maple-text">
            전체 회원 ({allUsers.length}명)
          </h2>
          {allUsers.length === 0 ? (
            <p className="text-maple-muted text-sm">회원이 없습니다.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-maple-border text-maple-muted">
                    <th className="text-left py-2 px-3">닉네임</th>
                    <th className="text-left py-2 px-3">상태</th>
                    <th className="text-left py-2 px-3">가입일</th>
                    <th className="text-right py-2 px-3">작업</th>
                  </tr>
                </thead>
                <tbody>
                  {allUsers.map((u) => (
                    <tr
                      key={u.user_id}
                      className="border-b border-maple-border hover:bg-maple-darker"
                    >
                      <td className="py-2 px-3 text-maple-text font-medium">
                        {u.user_id}
                        {u.is_admin && (
                          <span className="ml-2 text-xs bg-maple-yellow text-maple-dark px-2 py-0.5 rounded">
                            관리자
                          </span>
                        )}
                      </td>
                      <td className="py-2 px-3">
                        {u.is_approved ? (
                          <span className="text-maple-green text-xs">✓ 승인</span>
                        ) : (
                          <span className="text-maple-muted text-xs">대기</span>
                        )}
                      </td>
                      <td className="py-2 px-3 text-maple-muted text-xs">
                        {new Date(u.created_at).toLocaleDateString("ko-KR")}
                      </td>
                      <td className="py-2 px-3 text-right">
                        <button
                          onClick={() => handleDelete(u.user_id)}
                          disabled={actionInProgress === u.user_id}
                          className="text-maple-red text-sm hover:underline disabled:opacity-50"
                        >
                          삭제
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
