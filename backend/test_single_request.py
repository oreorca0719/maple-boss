#!/usr/bin/env python
"""Single Request Test"""
import asyncio
import httpx
import sys
import io

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def main():
    url = "http://127.0.0.1:8002/api/v1/ai/chat"
    
    message = "이번주 수익이 어떻게 되는지 분석해줄 수 있어?"
    
    print(f"Request: {message}")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                json={
                    "user_id": "test_user_01",
                    "message": message
                }
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response:\n{data.get('response', '')}")
            else:
                print(f"Error: {response.text}")
                
    except Exception as e:
        print(f"Error: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
