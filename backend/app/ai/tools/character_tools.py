"""
캐릭터 관련 LangChain Tools
"""
from langchain.tools import tool
import logging
from datetime import datetime, date as date_type

logger = logging.getLogger(__name__)


def compute_last_week(weekly_key: str) -> str:
    """주차를 1주 이전으로 계산 (YYYY-Www → YYYY-Www-1)"""
    year = int(weekly_key.split("-W")[0])
    week = int(weekly_key.split("-W")[1])

    if week == 1:
        return f"{year - 1}-W52"
    return f"{year}-W{week - 1:02d}"


@tool
def replicate_checklist_from_last_week(
    user_id: str,
    char_name: str,
    current_week: str,
    char_service
) -> dict:
    """
    저번 주와 동일한 보스를 이번 주에 자동으로 체크.

    Args:
        user_id: 사용자 ID
        char_name: 캐릭터 이름
        current_week: 현재 주차 (YYYY-Www)
        char_service: CharacterService 인스턴스

    Returns:
        체크리스트 복제 결과
    """
    try:
        from app.models.character import BossChecklist, BossEntry

        # 저번 주 계산
        last_week = compute_last_week(current_week)

        logger.info(f"Replicating checklist: user={user_id}, char={char_name}, {last_week} → {current_week}")

        # 저번 주 체크리스트 조회
        last_checklist = char_service.get_checklist(user_id, last_week, char_name)
        if not last_checklist:
            return {
                "success": False,
                "error": f"{last_week}에 {char_name} 데이터가 없습니다",
                "char_name": char_name
            }

        # 이번 주 체크리스트 생성 (모든 보스 is_cleared=True)
        new_bosses = [
            BossEntry(
                boss_name=b.boss_name,
                difficulty=b.difficulty,
                crystal_price=b.crystal_price,
                party_size=b.party_size,
                is_cleared=True,
                is_monthly=b.is_monthly
            )
            for b in last_checklist.bosses
        ]

        this_week_checklist = BossChecklist(
            user_id=user_id,
            char_name=char_name,
            weekly_key=current_week,
            bosses=new_bosses
        )

        # 저장 (수익 자동 계산)
        saved, week_total, month_total = char_service.save_checklist(this_week_checklist)

        logger.info(f"Checklist replicated: week_total={week_total}, month_total={month_total}")

        return {
            "success": True,
            "message": f"{char_name} 캐릭터에 저번 주 보스 {len(saved.bosses)}개를 자동 체크했습니다",
            "char_name": char_name,
            "total_earnings": saved.total_earnings,
            "week_total": week_total,
            "month_total": month_total,
            "bosses_count": len(saved.bosses),
            "weekly_key": current_week
        }

    except Exception as e:
        logger.error(f"Error replicating checklist: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"체크리스트 복제 중 오류: {str(e)}",
            "char_name": char_name
        }


@tool
def analyze_character_earnings(
    user_id: str,
    char_name: str,
    char_service
) -> dict:
    """
    특정 캐릭터의 수익 분석.

    Args:
        user_id: 사용자 ID
        char_name: 캐릭터 이름
        char_service: CharacterService 인스턴스

    Returns:
        캐릭터 수익 분석
    """
    try:
        history = char_service.get_weekly_earnings_history(user_id, weeks=4)

        # 해당 캐릭터의 데이터만 필터링
        char_earnings = []
        for week_data in history:
            checklists = char_service.list_checklists_by_week(
                user_id,
                week_data.get("weekly_key", "")
            )
            for checklist in checklists:
                if checklist.char_name == char_name:
                    char_earnings.append(checklist.total_earnings)

        if not char_earnings:
            return {
                "success": False,
                "error": f"{char_name}의 수익 데이터가 없습니다",
                "char_name": char_name
            }

        avg = sum(char_earnings) / len(char_earnings)
        latest = char_earnings[-1] if char_earnings else 0

        return {
            "success": True,
            "char_name": char_name,
            "average_earnings": int(avg),
            "latest_earnings": int(latest),
            "weeks_data": len(char_earnings),
            "trend": "상승" if latest > avg else "하강" if latest < avg else "유지",
            "recommendation": "더 높은 난이도 보스를 도전해보세요" if latest < avg else "현재 보스 구성이 좋습니다"
        }

    except Exception as e:
        logger.error(f"Error analyzing character earnings: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"수익 분석 중 오류: {str(e)}",
            "char_name": char_name
        }


@tool
def get_character_checklist(
    user_id: str,
    char_name: str,
    weekly_key: str,
    char_service
) -> dict:
    """
    특정 주차의 캐릭터 체크리스트 조회.

    Args:
        user_id: 사용자 ID
        char_name: 캐릭터 이름
        weekly_key: 주차 (YYYY-Www)
        char_service: CharacterService 인스턴스

    Returns:
        체크리스트 정보
    """
    try:
        checklist = char_service.get_checklist(user_id, weekly_key, char_name)

        if not checklist:
            return {
                "success": False,
                "error": f"{weekly_key}의 {char_name} 체크리스트가 없습니다",
                "char_name": char_name,
                "weekly_key": weekly_key
            }

        bosses_info = [
            {
                "name": b.boss_name,
                "difficulty": b.difficulty,
                "earnings": b.earnings,
                "cleared": b.is_cleared,
                "is_monthly": b.is_monthly
            }
            for b in checklist.bosses
        ]

        return {
            "success": True,
            "char_name": char_name,
            "weekly_key": weekly_key,
            "total_bosses": len(checklist.bosses),
            "cleared_bosses": sum(1 for b in checklist.bosses if b.is_cleared),
            "total_earnings": checklist.total_earnings,
            "bosses": bosses_info
        }

    except Exception as e:
        logger.error(f"Error getting checklist: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"체크리스트 조회 중 오류: {str(e)}",
            "char_name": char_name
        }
