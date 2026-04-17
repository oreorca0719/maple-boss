"""
수익 분석 관련 LangChain Tools
"""
from langchain.tools import tool
import logging

logger = logging.getLogger(__name__)


@tool
def analyze_user_earnings(
    user_id: str,
    period: str,
    user_service,
    char_service
) -> dict:
    """
    사용자의 전체 수익 분석.

    Args:
        user_id: 사용자 ID
        period: 분석 기간 ("weekly" 또는 "monthly")
        user_service: UserService 인스턴스
        char_service: CharacterService 인스턴스

    Returns:
        수익 분석 결과
    """
    try:
        user = user_service.get(user_id)
        if not user:
            return {
                "success": False,
                "error": "사용자를 찾을 수 없습니다",
                "period": period
            }

        logger.info(f"Analyzing earnings for user={user_id}, period={period}")

        if period == "weekly":
            current_earnings = user.weekly_earnings
            history = char_service.get_weekly_earnings_history(user_id, weeks=8)
            earnings_list = [h.get("total_earnings", 0) for h in history]

        elif period == "monthly":
            current_earnings = user.monthly_earnings
            # 월간 데이터는 좀 더 복잡 - 현재는 간단히
            earnings_list = [user.monthly_earnings]

        else:
            return {
                "success": False,
                "error": "기간은 'weekly' 또는 'monthly'여야 합니다",
                "period": period
            }

        if not earnings_list:
            return {
                "success": False,
                "error": f"수익 데이터가 없습니다",
                "period": period
            }

        avg = sum(earnings_list) / len(earnings_list)
        latest = earnings_list[-1] if earnings_list else 0
        trend = "상승" if latest > avg else "하강" if latest < avg else "유지"

        return {
            "success": True,
            "period": period,
            "current_earnings": current_earnings,
            "average_earnings": int(avg),
            "latest_earnings": int(latest),
            "data_points": len(earnings_list),
            "trend": trend,
            "recommendation": "더 높은 난이도 보스를 시도해보세요" if latest < avg else "현재 수익이 양호합니다"
        }

    except Exception as e:
        logger.error(f"Error analyzing earnings: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"수익 분석 중 오류: {str(e)}",
            "period": period
        }


@tool
def get_top_earning_bosses(
    user_id: str,
    weeks: int,
    char_service,
    data_service
) -> dict:
    """
    최근 N주간 가장 많은 수익을 주는 보스 목록.

    Args:
        user_id: 사용자 ID
        weeks: 조회 주 수 (기본 4주)
        char_service: CharacterService 인스턴스
        data_service: 보스 데이터 서비스

    Returns:
        상위 수익 보스 목록
    """
    try:
        from collections import defaultdict

        boss_earnings = defaultdict(int)
        boss_count = defaultdict(int)

        # 최근 N주 데이터 수집
        history = char_service.get_weekly_earnings_history(user_id, weeks=weeks)

        for week_data in history:
            weekly_key = week_data.get("weekly_key", "")
            checklists = char_service.list_checklists_by_week(user_id, weekly_key)

            for checklist in checklists:
                for boss in checklist.bosses:
                    if boss.is_cleared:
                        boss_earnings[boss.boss_name] += boss.earnings
                        boss_count[boss.boss_name] += 1

        if not boss_earnings:
            return {
                "success": False,
                "error": "클리어한 보스 데이터가 없습니다",
                "weeks": weeks
            }

        # 상위 5개 보스
        sorted_bosses = sorted(
            boss_earnings.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        top_bosses = [
            {
                "name": boss_name,
                "total_earnings": total,
                "clear_count": boss_count[boss_name],
                "average_per_clear": total // boss_count[boss_name]
            }
            for boss_name, total in sorted_bosses
        ]

        return {
            "success": True,
            "weeks": weeks,
            "total_bosses_cleared": sum(boss_count.values()),
            "top_bosses": top_bosses,
            "recommendation": f"'{sorted_bosses[0][0]}'가 가장 많은 수익을 제공합니다"
        }

    except Exception as e:
        logger.error(f"Error getting top bosses: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"보스 분석 중 오류: {str(e)}",
            "weeks": weeks
        }
