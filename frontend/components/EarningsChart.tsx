"use client";

import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";
import { useMemo } from "react";
import type { EarningsRecord } from "@/lib/api";

interface Props {
  data: EarningsRecord[];
  weeklyTotal: number;
  monthlyTotal: number;
}

// 서비스 시작 주차 (4/9~4/15)
const SERVICE_START_WEEK = "2026-W15";

function formatMeso(v: number) {
  if (v >= 100_000_000) return `${(v / 100_000_000).toFixed(2).replace(/\.?0+$/, "")}억`;
  if (v >= 10_000)      return `${(v / 10_000).toFixed(0)}만`;
  return v.toLocaleString("ko-KR");
}

// 목요일 기준 현재 주차 키 (YYYY-Www)
function currentMapleWeekKey(): string {
  const date = new Date();
  const shifted = new Date(date);
  shifted.setDate(shifted.getDate() - 3);
  const d = new Date(Date.UTC(shifted.getFullYear(), shifted.getMonth(), shifted.getDate()));
  const dayNum = d.getUTCDay() || 7;
  d.setUTCDate(d.getUTCDate() + 4 - dayNum);
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  const weekNo = Math.ceil((((d.getTime() - yearStart.getTime()) / 86400000) + 1) / 7);
  return `${d.getUTCFullYear()}-W${String(weekNo).padStart(2, "0")}`;
}

// 주차 키 → 다음 주차 키
function nextWeekKey(key: string): string {
  const [yearStr, weekStr] = key.split("-W");
  const year = parseInt(yearStr);
  const week = parseInt(weekStr);
  const jan4 = new Date(Date.UTC(year, 0, 4));
  const jan4Day = jan4.getUTCDay() || 7;
  const monday = new Date(jan4);
  monday.setUTCDate(jan4.getUTCDate() - (jan4Day - 1) + (week - 1) * 7);
  monday.setUTCDate(monday.getUTCDate() + 7); // 다음 주 월요일 (시프트 기준)
  const d = new Date(monday);
  const dayNum = d.getUTCDay() || 7;
  d.setUTCDate(d.getUTCDate() + 4 - dayNum);
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  const weekNo = Math.ceil((((d.getTime() - yearStart.getTime()) / 86400000) + 1) / 7);
  return `${d.getUTCFullYear()}-W${String(weekNo).padStart(2, "0")}`;
}

// 주차 키 → "M/D~M/D" 레이블
function weekLabel(key: string): string {
  const [yearStr, weekStr] = key.split("-W");
  const year = parseInt(yearStr);
  const week = parseInt(weekStr);
  const jan4 = new Date(Date.UTC(year, 0, 4));
  const jan4Day = jan4.getUTCDay() || 7;
  const monday = new Date(jan4);
  monday.setUTCDate(jan4.getUTCDate() - (jan4Day - 1) + (week - 1) * 7);
  const thu = new Date(monday);
  thu.setUTCDate(monday.getUTCDate() + 3);
  const wed = new Date(thu);
  wed.setUTCDate(thu.getUTCDate() + 6);
  const fmt = (d: Date) => `${d.getUTCMonth() + 1}/${d.getUTCDate()}`;
  return `${fmt(thu)}~${fmt(wed)}`;
}

// SERVICE_START_WEEK 부터 현재 주차까지 키 목록 생성
function buildWeekRange(startKey: string, endKey: string): string[] {
  const keys: string[] = [];
  let cur = startKey;
  while (cur <= endKey && keys.length < 52) {
    keys.push(cur);
    cur = nextWeekKey(cur);
  }
  return keys;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="card text-xs py-2 px-3 shadow-xl">
      <p className="text-maple-muted mb-1">{label}</p>
      <p className="text-maple-yellow font-bold">{formatMeso(payload[0].value)}</p>
    </div>
  );
};

export default function EarningsChart({ data, weeklyTotal, monthlyTotal }: Props) {
  const chartData = useMemo(() => {
    const earningsMap: Record<string, number> = {};
    for (const d of data) {
      earningsMap[d.weekly_key] = d.total_earnings;
    }
    const weekRange = buildWeekRange(SERVICE_START_WEEK, currentMapleWeekKey());
    return weekRange.map((key) => ({
      label: weekLabel(key),
      total_earnings: earningsMap[key] ?? 0,
    }));
  }, [data]);

  return (
    <div className="card">
      <div className="flex items-center justify-between flex-wrap gap-2 mb-4">
        <h2 className="font-semibold text-maple-text">주간 수익 현황</h2>
        <div className="flex gap-4 text-right">
          <div>
            <p className="text-xs text-maple-muted">이번 주</p>
            <p className="text-maple-yellow font-bold">{formatMeso(weeklyTotal)}</p>
          </div>
          <div>
            <p className="text-xs text-maple-muted">이번 달</p>
            <p className="text-maple-green font-bold">{formatMeso(monthlyTotal)}</p>
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={chartData} margin={{ left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2A2A4A" />
          <XAxis
            dataKey="label"
            tick={{ fill: "#8888AA", fontSize: 10 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tickFormatter={formatMeso}
            tick={{ fill: "#8888AA", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={56}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="total_earnings" fill="#FFD700" radius={[4, 4, 0, 0]} activeBar={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
