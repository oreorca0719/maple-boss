"""
메이플스토리 주간 보스 마스터 데이터.
결정석 가격 기준: 실제 게임 내 NPC 판매가 (메소).
"""

from typing import TypedDict


class BossInfo(TypedDict):
    id: str
    name: str
    difficulty: str
    crystal_price: int
    min_level: int
    is_monthly: bool  # 월간 보스 여부 (검은 마법사만 True)


BOSS_LIST: list[BossInfo] = [
    # ── Lv. 90 ──────────────────────────────────────
    {"id": "zakum_chaos",           "name": "자쿰",             "difficulty": "카오스",   "crystal_price":     8_080_000, "min_level": 90, "is_monthly": False},

    # ── Lv. 165 ─────────────────────────────────────
    {"id": "cygnus_easy",           "name": "시그너스",         "difficulty": "이지",     "crystal_price":     4_550_000, "min_level": 165, "is_monthly": False},
    {"id": "cygnus_normal",         "name": "시그너스",         "difficulty": "노말",     "crystal_price":     7_500_000, "min_level": 165, "is_monthly": False},

    # ── Lv. 170 ─────────────────────────────────────
    {"id": "hilla_hard",            "name": "힐라",             "difficulty": "하드",     "crystal_price":     5_750_000, "min_level": 170, "is_monthly": False},
    {"id": "pinkbean_chaos",        "name": "핑크빈",           "difficulty": "카오스",   "crystal_price":     6_580_000, "min_level": 170, "is_monthly": False},

    # ── Lv. 175 ─────────────────────────────────────
    {"id": "magnus_hard",           "name": "매그너스",         "difficulty": "하드",     "crystal_price":     8_560_000, "min_level": 175, "is_monthly": False},

    # ── Lv. 180 ─────────────────────────────────────
    {"id": "pierre_chaos",          "name": "피에르",           "difficulty": "카오스",   "crystal_price":     8_170_000, "min_level": 180, "is_monthly": False},
    {"id": "vonbonbon_chaos",       "name": "반반",             "difficulty": "카오스",   "crystal_price":     8_150_000, "min_level": 180, "is_monthly": False},
    {"id": "bloodyqueen_chaos",     "name": "블러디퀸",         "difficulty": "카오스",   "crystal_price":     8_140_000, "min_level": 180, "is_monthly": False},
    {"id": "vellum_chaos",          "name": "벨룸",             "difficulty": "카오스",   "crystal_price":     9_280_000, "min_level": 180, "is_monthly": False},

    # ── Lv. 190 ─────────────────────────────────────
    {"id": "papulatus_chaos",       "name": "파풀라투스",       "difficulty": "카오스",   "crystal_price":    13_800_000, "min_level": 190, "is_monthly": False},
    {"id": "suu_normal",            "name": "스우",             "difficulty": "노말",     "crystal_price":    17_600_000, "min_level": 190, "is_monthly": False},
    {"id": "suu_hard",              "name": "스우",             "difficulty": "하드",     "crystal_price":    54_200_000, "min_level": 190, "is_monthly": False},
    {"id": "suu_extreme",           "name": "스우",             "difficulty": "익스트림", "crystal_price":   604_000_000, "min_level": 200, "is_monthly": False},
    {"id": "demian_normal",         "name": "데미안",           "difficulty": "노말",     "crystal_price":    18_400_000, "min_level": 190, "is_monthly": False},
    {"id": "demian_hard",           "name": "데미안",           "difficulty": "하드",     "crystal_price":    51_500_000, "min_level": 190, "is_monthly": False},

    # ── Lv. 210 ─────────────────────────────────────
    {"id": "guardian_normal",       "name": "가디언 엔젤 슬라임", "difficulty": "노말",   "crystal_price":    26_800_000, "min_level": 210, "is_monthly": False},
    {"id": "guardian_chaos",        "name": "가디언 엔젤 슬라임", "difficulty": "카오스", "crystal_price":    79_100_000, "min_level": 210, "is_monthly": False},

    # ── Lv. 220 ─────────────────────────────────────
    {"id": "lucid_easy",            "name": "루시드",           "difficulty": "이지",     "crystal_price":    31_400_000, "min_level": 220, "is_monthly": False},
    {"id": "lucid_normal",          "name": "루시드",           "difficulty": "노말",     "crystal_price":    37_500_000, "min_level": 220, "is_monthly": False},
    {"id": "lucid_hard",            "name": "루시드",           "difficulty": "하드",     "crystal_price":    66_200_000, "min_level": 220, "is_monthly": False},

    # ── Lv. 235 ─────────────────────────────────────
    {"id": "will_easy",             "name": "윌",               "difficulty": "이지",     "crystal_price":    34_000_000, "min_level": 235, "is_monthly": False},
    {"id": "will_normal",           "name": "윌",               "difficulty": "노말",     "crystal_price":    43_300_000, "min_level": 235, "is_monthly": False},
    {"id": "will_hard",             "name": "윌",               "difficulty": "하드",     "crystal_price":    81_200_000, "min_level": 235, "is_monthly": False},

    # ── Lv. 245 ─────────────────────────────────────
    {"id": "dusk_normal",           "name": "더스크",           "difficulty": "노말",     "crystal_price":    46_300_000, "min_level": 245, "is_monthly": False},
    {"id": "dusk_chaos",            "name": "더스크",           "difficulty": "카오스",   "crystal_price":    73_500_000, "min_level": 245, "is_monthly": False},

    # ── Lv. 250 ─────────────────────────────────────
    {"id": "jinhilla_normal",       "name": "진 힐라",          "difficulty": "노말",     "crystal_price":    74_900_000, "min_level": 250, "is_monthly": False},
    {"id": "jinhilla_hard",         "name": "진 힐라",          "difficulty": "하드",     "crystal_price":   112_000_000, "min_level": 250, "is_monthly": False},

    # ── Lv. 255 ─────────────────────────────────────
    {"id": "dunkel_normal",         "name": "듄켈",             "difficulty": "노말",     "crystal_price":    50_000_000, "min_level": 255, "is_monthly": False},
    {"id": "dunkel_hard",           "name": "듄켈",             "difficulty": "하드",     "crystal_price":    99_400_000, "min_level": 255, "is_monthly": False},

    # ── Lv. 260 ─────────────────────────────────────
    {"id": "seren_normal",          "name": "선택받은 세렌",    "difficulty": "노말",     "crystal_price":   266_000_000, "min_level": 260, "is_monthly": False},
    {"id": "seren_hard",            "name": "선택받은 세렌",    "difficulty": "하드",     "crystal_price":   396_000_000, "min_level": 260, "is_monthly": False},
    {"id": "seren_extreme",         "name": "선택받은 세렌",    "difficulty": "익스트림", "crystal_price": 3_150_000_000, "min_level": 270, "is_monthly": False},

    # ── Lv. 265 ─────────────────────────────────────
    {"id": "kalos_easy",            "name": "감시자 칼로스",    "difficulty": "이지",     "crystal_price":   311_000_000, "min_level": 265, "is_monthly": False},
    {"id": "kalos_normal",          "name": "감시자 칼로스",    "difficulty": "노말",     "crystal_price":   561_000_000, "min_level": 265, "is_monthly": False},
    {"id": "kalos_chaos",           "name": "감시자 칼로스",    "difficulty": "카오스",   "crystal_price": 1_340_000_000, "min_level": 265, "is_monthly": False},
    {"id": "kalos_extreme",         "name": "감시자 칼로스",    "difficulty": "익스트림", "crystal_price": 4_320_000_000, "min_level": 275, "is_monthly": False},

    # ── Lv. 270 ─────────────────────────────────────
    {"id": "adversary_easy",        "name": "최초의 대적자",    "difficulty": "이지",     "crystal_price":   324_000_000, "min_level": 270, "is_monthly": False},
    {"id": "adversary_normal",      "name": "최초의 대적자",    "difficulty": "노말",     "crystal_price":   589_000_000, "min_level": 270, "is_monthly": False},
    {"id": "adversary_hard",        "name": "최초의 대적자",    "difficulty": "하드",     "crystal_price": 1_510_000_000, "min_level": 270, "is_monthly": False},
    {"id": "adversary_extreme",     "name": "최초의 대적자",    "difficulty": "익스트림", "crystal_price": 4_960_000_000, "min_level": 280, "is_monthly": False},

    # ── Lv. 275 ─────────────────────────────────────
    {"id": "kaling_easy",           "name": "카링",             "difficulty": "이지",     "crystal_price":   419_000_000, "min_level": 275, "is_monthly": False},
    {"id": "kaling_normal",         "name": "카링",             "difficulty": "노말",     "crystal_price":   714_000_000, "min_level": 275, "is_monthly": False},
    {"id": "kaling_hard",           "name": "카링",             "difficulty": "하드",     "crystal_price": 1_830_000_000, "min_level": 275, "is_monthly": False},
    {"id": "kaling_extreme",        "name": "카링",             "difficulty": "익스트림", "crystal_price": 5_670_000_000, "min_level": 285, "is_monthly": False},

    # ── Lv. 280 ─────────────────────────────────────
    {"id": "blackstar_normal",      "name": "찬란한 흉성",      "difficulty": "노말",     "crystal_price":   658_000_000, "min_level": 280, "is_monthly": False},
    {"id": "blackstar_hard",        "name": "찬란한 흉성",      "difficulty": "하드",     "crystal_price": 2_819_000_000, "min_level": 280, "is_monthly": False},

    # ── Lv. 285 ─────────────────────────────────────
    {"id": "limbo_normal",          "name": "림보",             "difficulty": "노말",     "crystal_price": 1_080_000_000, "min_level": 285, "is_monthly": False},
    {"id": "limbo_hard",            "name": "림보",             "difficulty": "하드",     "crystal_price": 2_510_000_000, "min_level": 285, "is_monthly": False},

    # ── Lv. 290 ─────────────────────────────────────
    {"id": "baldrix_normal",        "name": "발드릭스",         "difficulty": "노말",     "crystal_price": 1_440_000_000, "min_level": 290, "is_monthly": False},
    {"id": "baldrix_hard",          "name": "발드릭스",         "difficulty": "하드",     "crystal_price": 3_240_000_000, "min_level": 290, "is_monthly": False},

    # ── Lv. 295 ─────────────────────────────────────
    {"id": "jupiter_normal",        "name": "유피테르",         "difficulty": "노말",     "crystal_price": 1_700_000_000, "min_level": 295, "is_monthly": False},
    {"id": "jupiter_hard",          "name": "유피테르",         "difficulty": "하드",     "crystal_price": 5_100_000_000, "min_level": 295, "is_monthly": False},

    # ── Lv. 300 ─────────────────────────────────────
    {"id": "blackmage_hard",        "name": "검은 마법사",      "difficulty": "하드",     "crystal_price":   700_000_000, "min_level": 300, "is_monthly": True},
    {"id": "blackmage_extreme",     "name": "검은 마법사",      "difficulty": "익스트림", "crystal_price": 9_200_000_000, "min_level": 310, "is_monthly": True},
]


def get_boss_by_id(boss_id: str) -> BossInfo | None:
    return next((b for b in BOSS_LIST if b["id"] == boss_id), None)
