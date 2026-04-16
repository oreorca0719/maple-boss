"use client";

import { type User, type ParticipationRank } from "@/lib/api";

interface Props {
  ranking: ParticipationRank[];
  allUsers: User[];
  currentUserId: string;
}

export default function PartyParticipationRanking({
  ranking,
  allUsers,
  currentUserId,
}: Props) {
  if (ranking.length === 0) {
    return (
      <div className="card h-full flex flex-col">
        <h3 className="font-semibold mb-3 text-maple-yellow shrink-0">🎭 파티 참여 순위</h3>
        <p className="text-maple-muted text-sm">파티 참여 데이터가 없습니다.</p>
      </div>
    );
  }

  const userMap = Object.fromEntries(
    allUsers.map((u) => [u.user_id, u.display_name])
  );

  // 알려진 사용자만 필터링
  const validRanking = ranking.filter((r) => r.user_id in userMap);

  const rankColors = ["text-yellow-400", "text-slate-300", "text-amber-600"];

  if (validRanking.length === 0) {
    return (
      <div className="card h-full flex flex-col">
        <h3 className="font-semibold mb-3 text-maple-yellow shrink-0">🎭 파티 참여 순위</h3>
        <p className="text-maple-muted text-sm">파티 참여 데이터가 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="card h-full flex flex-col">
      <h3 className="font-semibold mb-3 text-maple-yellow shrink-0">🎭 파티 참여 순위</h3>
      <div className="overflow-y-auto flex-1">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-maple-dark">
            <tr className="text-maple-muted border-b border-maple-border">
              <th className="text-left pb-2 w-8">#</th>
              <th className="text-left pb-2">닉네임</th>
              <th className="text-right pb-2">파티 수</th>
            </tr>
          </thead>
          <tbody>
            {validRanking.map((r, i) => {
              const displayName = userMap[r.user_id];
              const isMe = r.user_id === currentUserId;
              return (
                <tr
                  key={r.user_id}
                  className={`border-b border-maple-border/40 last:border-0 ${
                    isMe ? "bg-maple-yellow/5" : ""
                  }`}
                >
                  <td
                    className={`py-2 font-bold ${
                      rankColors[i] ?? "text-maple-muted"
                    }`}
                  >
                    {i + 1}
                  </td>
                  <td
                    className={`py-2 ${
                      isMe ? "text-maple-yellow font-medium" : "text-maple-text"
                    }`}
                  >
                    {displayName}
                    {isMe && (
                      <span className="ml-1 text-[10px] text-maple-yellow">
                        (나)
                      </span>
                    )}
                  </td>
                  <td className="py-2 text-right font-mono text-maple-text">
                    {r.party_count}회
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
