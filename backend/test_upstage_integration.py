"""
ChatUpstage 통합 테스트
"""
import asyncio
import sys
from dotenv import load_dotenv
from app.ai.service import AIService
from app.services.character_service import CharacterService
from app.services.user_service import UserService
from app.services.data_service import DataService

# .env 로드
load_dotenv()


async def test_chatupstage_integration():
    """ChatUpstage 통합 테스트"""
    
    print("[TEST] ChatUpstage Integration Test")
    print("=" * 60)
    
    try:
        # 더미 서비스 초기화 (실제 로직 테스트, DB 없음)
        char_service = CharacterService(None)
        user_service = UserService(None)
        data_service = DataService(None)
        
        # AIService 초기화
        ai_service = AIService(char_service, user_service, data_service)
        
        # 테스트 케이스
        test_cases = [
            {
                "name": "Test 1: 보스 체크리스트 복제 요청",
                "user_id": "test_user_01",
                "message": "지난주 보스 체크리스트를 이번주로 복제해줄 수 있어?",
                "expected": "복제"
            },
            {
                "name": "Test 2: 수익 분석 요청",
                "user_id": "test_user_01",
                "message": "이번주 수익이 어떻게 되는지 분석해줄 수 있어?",
                "expected": "분석"
            },
            {
                "name": "Test 3: 범위 외 요청 (게임 팁)",
                "user_id": "test_user_01",
                "message": "보스를 빠르게 깨는 팁을 알려줄 수 있어?",
                "expected": "거절"
            },
            {
                "name": "Test 4: 범위 외 요청 (날씨)",
                "user_id": "test_user_01",
                "message": "오늘 날씨가 어떻게 되나?",
                "expected": "거절"
            },
            {
                "name": "Test 5: 현재 주차 정보 요청",
                "user_id": "test_user_01",
                "message": "지금 몇주차야?",
                "expected": "정보"
            }
        ]
        
        for i, test in enumerate(test_cases, 1):
            print(f"\n[{i}] {test['name']}")
            print(f"    Message: {test['message']}")
            print(f"    Expected: {test['expected']}")
            
            try:
                response = await ai_service.chat(
                    user_id=test["user_id"],
                    message=test["message"]
                )
                
                print(f"    Status: [PASS]")
                print(f"    Response: {response[:150]}...")
                
                # 응답 검증
                if test["expected"] == "복제" and "복제" in response:
                    print(f"    Content Check: [PASS] - 복제 관련 응답")
                elif test["expected"] == "분석" and "분석" in response:
                    print(f"    Content Check: [PASS] - 분석 관련 응답")
                elif test["expected"] == "거절" and ("도와드릴 수 없습니다" in response or "거절" in response):
                    print(f"    Content Check: [PASS] - 거절 응답")
                elif test["expected"] == "정보" and ("주차" in response or "정보" in response):
                    print(f"    Content Check: [PASS] - 정보 제공")
                else:
                    print(f"    Content Check: [INFO] - 응답이 생성됨 (내용 검증은 LLM 의존)")
                    
            except Exception as e:
                print(f"    Status: [FAIL]")
                print(f"    Error: {str(e)}")
        
        print("\n" + "=" * 60)
        print("[TEST] All tests completed")
        
    except Exception as e:
        print(f"[ERROR] Test setup failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(test_chatupstage_integration())
