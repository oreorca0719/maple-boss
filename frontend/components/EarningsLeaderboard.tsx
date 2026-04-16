"use client";

import { type User } from "@/lib/api";

interface Props {
  users: User[];
  currentUserId: string;
}

function RankTable({
  title,
  sorted,
  valueKey,
  currentUserId,
}: {
  title: string;
  sorted: User[];
  valueKey: "weekly_earnings" | "monthly_earnings";
  currentUserId: string;
}) {
  if (sorted.length === 0) {
    return (
      <div className="card flex-1">
        <h3 className="font-semibold mb-3 text-maple-yellow">{title}</h3>
        <p className="text-maple-muted text-sm">아직 수익 데이터가 없습니다.</p>
      </div>
    );
  }

  const rankColors = ["text-yellow-400", "text-slate-300", "text-amber-600"];

  return (
    <div className="card flex-1">
      <h3 className="font-semibold mb-3 text-maple-yellow">{title}</h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-maple-muted border-b border-maple-border">
            <th className="text-left pb-2 w-8">#</th>
            <th className="text-left pb-2">닉네임</th>
            <th className="text-right pb-2">수익 (메소)</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((u, i) => {
            const isMe = u.user_id === currentUserId;
            return (
              <tr
                key={u.user_id}
                className={`border-b border-maple-border/40 last:border-0 ${
                  isMe ? "bg-maple-yellow/5" : ""
                }`}
              >
                <td className={`py-2 font-bold ${rankColors[i] ?? "text-maple-muted"}`}>
                  {i + 1}
                </td>
                <td className={`py-2 ${isMe ? "text-maple-yellow font-medium" : "text-maple-text"}`}>
                  {u.display_name}
                  {isMe && <span className="ml-1 text-[10px] text-maple-yellow">(나)</span>}
                </td>
                <td className="py-2 text-right font-mono text-maple-text">
                  {u[valueKey].toLocaleString()}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default function EarningsLeaderboard({ users, currentUserId }: Props) {

  const weeklyRank = [...users]
    .filter((u) => u.weekly_earnings > 0)
    .sort((a, b) => b.weekly_earnings - a.weekly_earnings);

  const monthlyRank = [...users]
    .filter((u) => u.monthly_earnings > 0)
    .sort((a, b) => b.monthly_earnings - a.monthly_earnings);

  if (weeklyRank.length === 0 && monthlyRank.length === 0) return null;

  return (
    <div>
      <h2 className="font-semibold mb-3">수익 순위</h2>
      <div className="flex flex-col sm:flex-row gap-4">
        <RankTable
          title="🏆 주간 수익 순위"
          sorted={weeklyRank}
          valueKey="weekly_earnings"
          currentUserId={currentUserId}
        />
        <RankTable
          title="📅 월간 수익 순위"
          sorted={monthlyRank}
          valueKey="monthly_earnings"
          currentUserId={currentUserId}
        />
      </div>
    </div>
  );
}
