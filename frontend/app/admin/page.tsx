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
        const pending = await listPendingUsers();
        setPendingUsers(pending);
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
    if (!confirm(`"${userId}"을(를) 삭제하시겠습니까?`)) return;
    setActionInProgress(userId);
    try {
      await deleteUser(userId);
      setPendingUsers((prev) => prev.filter((u) => u.user_id !== userId));
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

        {/* 회원 관리 */}
        <section>
          <h2 className="font-semibold mb-3 text-maple-text">회원 관리</h2>
          <p className="text-maple-muted text-sm mb-3">
            필요시 회원을 삭제할 수 있습니다. 삭제 후 복구는 불가능합니다.
          </p>
        </section>
      </main>
    </div>
  );
}
