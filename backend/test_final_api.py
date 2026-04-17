#!/usr/bin/env python
"""Final API Test with Correct Endpoint"""
import asyncio
import httpx
import sys
import io

# UTF-8 출력 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def main():
    print("=" * 70)
    print("ChatUpstage API Integration - Final Test")
    print("=" * 70)
    
    url = "http://127.0.0.1:8002/api/v1/ai/chat"
    
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
            "name": "Test 4: 현재 주차 정보",
            "message": "지금 몇주차야?",
        }
    ]
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            for i, test in enumerate(test_cases, 1):
                print(f"\n[{i}] {test['name']}")
                print(f"    Request: {test['message']}")
                
                try:
                    response = await client.post(
                        url,
                        json={
                            "user_id": "test_user_01",
                            "message": test["message"]
                        }
                    )
                    
                    print(f"    Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        ai_response = data.get('response', '')
                        print(f"    [PASS] Response received")
                        print(f"    Preview: {ai_response[:150]}...")
                        
                    else:
                        print(f"    [FAIL] {response.text}")
                        
                except asyncio.TimeoutError:
                    print(f"    [TIMEOUT]")
                except Exception as e:
                    print(f"    [ERROR] {str(e)}")
        
        print("\n" + "=" * 70)
        print("All tests completed")
        
    except Exception as e:
        print(f"Fatal Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
