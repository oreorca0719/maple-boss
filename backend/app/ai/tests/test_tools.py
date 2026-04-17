"""
AI Tool 함수 단위 테스트
"""
import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta

from app.ai.tools.character_tools import (
    replicate_checklist_from_last_week,
    analyze_character_earnings,
    get_character_checklist,
    compute_last_week
)
from app.ai.tools.earnings_tools import (
    analyze_user_earnings,
    get_top_earning_bosses
)


class TestCharacterTools:
    """Character Tools 테스트"""

    def test_compute_last_week(self):
        """compute_last_week 함수 테스트"""
        # 현재가 2026-W17이면 이전주는 2026-W16
        result = compute_last_week("2026-W17")
        assert result == "2026-W16", "이전주 계산이 잘못됨"

        # 연도 변경 케이스
        result = compute_last_week("2026-W01")
        assert result == "2025-W52", "연도 변경 케이스 실패"

    def test_replicate_checklist_from_last_week(self):
        """지난주 체크리스트 복제 테스트"""
        # Mock CharacterService
        mock_char_service = Mock()
        mock_char_service.get_weekly_checklist.return_value = [
            {"boss_name": "루시드", "is_cleared": False, "earnings": 0},
            {"boss_name": "윌", "is_cleared": False, "earnings": 0},
        ]

        result = replicate_checklist_from_last_week(
            user_id="test_user",
            char_name="TestChar",
            current_week="2026-W17",
            char_service=mock_char_service
        )

        assert result["success"] is True, "결과가 실패임"
        assert len(result["checklist"]) == 2, "체크리스트 길이가 맞지 않음"
        # 복제된 아이템은 is_cleared=True여야 함
        assert result["checklist"][0]["is_cleared"] is True, "복제된 아이템이 체크되지 않음"

    def test_replicate_checklist_empty_last_week(self):
        """지난주 체크리스트가 없을 때 테스트"""
        mock_char_service = Mock()
        mock_char_service.get_weekly_checklist.return_value = []

        result = replicate_checklist_from_last_week(
            user_id="test_user",
            char_name="TestChar",
            current_week="2026-W17",
            char_service=mock_char_service
        )

        assert result["success"] is False, "실패여야 함"
        assert "오류" in result.get("error", "").lower(), "오류 메시지 없음"

    def test_analyze_character_earnings(self):
        """캐릭터 수익 분석 테스트"""
        mock_char_service = Mock()
        mock_char_service.get_weekly_checklist.side_effect = [
            [{"boss_name": "루시드", "earnings": 1000000}],  # 4주 전
            [{"boss_name": "루시드", "earnings": 1200000}],  # 3주 전
            [{"boss_name": "루시드", "earnings": 1100000}],  # 2주 전
            [{"boss_name": "루시드", "earnings": 1300000}],  # 1주 전
        ]

        result = analyze_character_earnings(
            user_id="test_user",
            char_name="TestChar",
            char_service=mock_char_service
        )

        assert result["success"] is True, "분석 실패"
        assert "earnings_trend" in result, "수익 추이가 없음"
        assert len(result["earnings_trend"]) == 4, "4주 데이터가 없음"

    def test_get_character_checklist(self):
        """캐릭터 체크리스트 조회 테스트"""
        mock_checklist = [
            {"boss_name": "루시드", "is_cleared": True},
            {"boss_name": "윌", "is_cleared": False},
            {"boss_name": "더러운 레지스탕스", "is_cleared": True},
        ]

        mock_char_service = Mock()
        mock_char_service.get_weekly_checklist.return_value = mock_checklist

        result = get_character_checklist(
            user_id="test_user",
            char_name="TestChar",
            weekly_key="2026-W17",
            char_service=mock_char_service
        )

        assert result["success"] is True, "조회 실패"
        assert len(result["checklist"]) == 3, "체크리스트 길이가 맞지 않음"
        assert result["checklist"][0]["is_cleared"] is True, "클리어 상태 불일치"


class TestEarningsTools:
    """Earnings Tools 테스트"""

    def test_analyze_user_earnings_weekly(self):
        """사용자 주간 수익 분석 테스트"""
        # Mock 데이터
        mock_user_service = Mock()
        mock_char_service = Mock()

        # 캐릭터 목록 반환
        mock_user_service.get_characters.return_value = ["Char1", "Char2"]

        # 캐릭터별 주간 체크리스트 반환
        def mock_checklist(user_id, char_name, week):
            if char_name == "Char1":
                return [{"boss_name": "루시드", "earnings": 1000000}]
            else:
                return [{"boss_name": "윌", "earnings": 800000}]

        mock_char_service.get_weekly_checklist.side_effect = mock_checklist

        result = analyze_user_earnings(
            user_id="test_user",
            period="weekly",
            user_service=mock_user_service,
            char_service=mock_char_service
        )

        assert result["success"] is True, "분석 실패"
        assert "total_earnings" in result, "총 수익이 없음"

    def test_get_top_earning_bosses(self):
        """상위 보스 조회 테스트"""
        mock_char_service = Mock()
        mock_data_service = Mock()

        # 주간 보스별 수익 데이터
        earnings_data = {
            "루시드": 1000000,
            "윌": 900000,
            "더러운 레지스탕스": 700000,
            "카이": 600000,
            "검은 마법사": 500000,
            "보로스": 400000,
        }

        mock_data_service.get_boss_earnings.return_value = earnings_data

        result = get_top_earning_bosses(
            user_id="test_user",
            weeks=1,
            char_service=mock_char_service,
            data_service=mock_data_service
        )

        assert result["success"] is True, "조회 실패"
        assert "top_bosses" in result, "상위 보스 목록이 없음"
        assert len(result["top_bosses"]) <= 5, "상위 5개 보스 이상이 반환됨"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
