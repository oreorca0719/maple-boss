#!/usr/bin/env python
"""Verbose API test"""
import asyncio
import httpx
import sys
import io

# UTF-8 출력 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def main():
    print("API Test - Verbose Output")
    print("=" * 60)
    
    url = "http://127.0.0.1:8002/ai/chat"
    payload = {
        "user_id": "test_user_01",
        "message": "지난주 보스 체크리스트를 이번주로 복제해줄 수 있어?"
    }
    
    print(f"URL: {url}")
    print(f"Payload: {payload}")
    print("Connecting...")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print("Client created, sending request...")
            
            response = await client.post(url, json=payload)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Text: {response.text[:500]}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"\nAI Response:")
                print(data.get('response', 'No response'))
            else:
                print(f"\nError Response:")
                print(response.text)
                
    except asyncio.TimeoutError:
        print("TimeoutError: Request timed out")
    except httpx.ConnectError as e:
        print(f"ConnectError: {str(e)}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
