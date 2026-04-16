import type { Character } from "@/lib/api";

interface Props {
  char: Character;
  onClick: () => void;
  onDelete?: () => void;
}

function formatCompact(n: number): string {
  if (n >= 100_000_000) return `${(n / 100_000_000).toFixed(1)}억`;
  if (n >= 10_000)      return `${(n / 10_000).toFixed(0)}만`;
  return n.toLocaleString("ko-KR");
}

export default function CharacterCard({ char, onClick, onDelete }: Props) {
  return (
    <div
      className="card cursor-pointer hover:border-maple-yellow transition-colors relative group"
      onClick={onClick}
    >
      {/* 본캐 배지 */}
      {char.is_main && (
        <span className="badge bg-maple-yellow text-maple-dark absolute top-3 right-3">
          본캐
        </span>
      )}

      {/* 캐릭터 이미지 */}
      <div className="flex justify-center mb-3 -mx-4 -mt-4 pt-2 bg-maple-dark/40 rounded-t-xl overflow-hidden">
        {char.image_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={char.image_url}
            alt={char.char_name}
            className="h-36 object-contain"
          />
        ) : (
          <div className="h-36 w-20 flex items-center justify-center text-4xl">
            🧙
          </div>
        )}
      </div>

      {/* 닉네임 */}
      <h3 className="font-semibold text-maple-text text-center truncate">
        {char.char_name}
      </h3>

      {/* 직업 / 서버 */}
      <p className="text-maple-muted text-xs text-center mt-0.5">
        {char.job || "직업 미확인"}{char.server ? ` · ${char.server}` : ""}
      </p>

      {/* 레벨 / 전투력 */}
      <div className="mt-3 grid grid-cols-2 gap-2 text-center text-xs">
        <div className="bg-maple-dark rounded p-2">
          <p className="text-maple-muted">레벨</p>
          <p className="font-bold text-maple-yellow">{char.level || "—"}</p>
        </div>
        <div className="bg-maple-dark rounded p-2">
          <p className="text-maple-muted">전투력</p>
          <p className="font-bold text-maple-yellow truncate">
            {char.combat_power ? formatCompact(char.combat_power) : "—"}
          </p>
        </div>
      </div>

      {/* 삭제 버튼 (본캐는 삭제 불가) */}
      {!char.is_main && onDelete && (
        <button
          onClick={(e) => { e.stopPropagation(); onDelete(); }}
          className="absolute bottom-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity
                     text-maple-red hover:text-red-400 text-xs"
        >
          삭제
        </button>
      )}
    </div>
  );
}
