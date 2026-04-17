#!/usr/bin/env python
"""Tool Calling 테스트"""
import asyncio
import httpx
import sys
import io

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def main():
    print("Tool Calling Test")
    print("=" * 60)
    
    url = "http://127.0.0.1:8002/api/v1/ai/chat"
    
    message = "히특 캐릭터의 2026-W16 주간 보스 체크리스트를 보여줘"
    
    print(f"Request: {message}")
    print("Waiting for response...")
    
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(
                url,
                json={
                    "user_id": "test_user_01",
                    "message": message
                }
            )
            
            print(f"\nStatus: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get('response', '')
                print(f"\n[AI Response]:\n{ai_response}")
                
                # Tool이 호출되었는지 판단
                if "스우" in ai_response or "데몬" in ai_response or "오류" in ai_response or "sorry" in ai_response.lower():
                    print("\n[ANALYSIS] Tool calling 미작동 (데이터 생성 또는 오류)")
                else:
                    print("\n[ANALYSIS] 정상 응답")
            else:
                print(f"Error: {response.text}")
                
    except asyncio.TimeoutError:
        print("Timeout - 요청이 너무 오래 걸렸습니다")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
