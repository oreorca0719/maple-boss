"""
ChatUpstage API 통합 테스트 (HTTP 기반)
"""
import asyncio
import httpx
import json
from dotenv import load_dotenv

# .env 로드
load_dotenv()

BASE_URL = "http://127.0.0.1:8002"


async def test_api():
    """API 엔드포인트 테스트"""
    
    print("[TEST] ChatUpstage API Integration Test")
    print("=" * 60)
    
    # 테스트 케이스
    test_cases = [
        {
            "name": "Test 1: 보스 체크리스트 복제 요청",
            "message": "지난주 보스 체크리스트를 이번주로 복제해줄 수 있어?",
        },
        {
            "name": "Test 2: 수익 분석 요청",
            "message": "이번주 수익이 어떻게 되는지 분석해줄 수 있어?",
        },
        {
            "name": "Test 3: 범위 외 요청 (게임 팁)",
            "message": "보스를 빠르게 깨는 팁을 알려줄 수 있어?",
        },
        {
            "name": "Test 4: 범위 외 요청 (날씨)",
            "message": "오늘 날씨가 어떻게 되나?",
        },
        {
            "name": "Test 5: 현재 주차 정보 요청",
            "message": "지금 몇주차야?",
        }
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, test in enumerate(test_cases, 1):
            print(f"\n[{i}] {test['name']}")
            print(f"    Message: {test['message']}")
            
            try:
                # API 호출
                response = await client.post(
                    f"{BASE_URL}/api/chat",
                    json={
                        "user_id": "test_user_01",
                        "message": test["message"]
                    }
                )
                
                print(f"    Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    ai_response = data.get("response", "")
                    
                    print(f"    Status: [PASS]")
                    print(f"    Response: {ai_response[:200]}...")
                    
                    # 응답 타입 체크
                    if "api_key client option must be set" in ai_response:
                        print(f"    ISSUE: API Key 문제 여전히 존재")
                    else:
                        print(f"    AI Response Generated: [OK]")
                        
                else:
                    print(f"    Status: [FAIL]")
                    print(f"    Response: {response.text[:200]}")
                    
            except httpx.ConnectError:
                print(f"    Status: [FAIL] - 서버에 연결할 수 없음")
                print(f"    Ensure backend server is running on {BASE_URL}")
                break
            except Exception as e:
                print(f"    Status: [FAIL]")
                print(f"    Error: {str(e)}")
        
        print("\n" + "=" * 60)
        print("[TEST] All API tests completed")


if __name__ == "__main__":
    asyncio.run(test_api())
