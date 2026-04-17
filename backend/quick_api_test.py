#!/usr/bin/env python
"""Quick API test"""
import asyncio
import httpx
import json

async def main():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("Testing ChatUpstage API...")
        print("=" * 60)
        
        test_message = "지난주 보스 체크리스트를 이번주로 복제해줄 수 있어?"
        
        try:
            print(f"Sending: {test_message}")
            response = await client.post(
                "http://127.0.0.1:8002/ai/chat",
                json={
                    "user_id": "test_user_01",
                    "message": test_message
                }
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {data.get('response', 'No response')[:300]}")
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
