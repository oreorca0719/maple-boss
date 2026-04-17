#!/usr/bin/env python
"""Debug API response"""
import asyncio
import httpx
import sys
import io

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def main():
    url = "http://127.0.0.1:8002/api/v1/ai/chat"
    
    message = "안녕"
    
    print(f"Request: {message}")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                json={
                    "user_id": "test_user_01",
                    "message": message
                }
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            print(f"Response Text (raw):\n{response.text}")
            
            print("\n" + "=" * 60)
            
            # Try to parse JSON
            try:
                data = response.json()
                print(f"Parsed JSON: {data}")
            except Exception as e:
                print(f"JSON Parse Error: {str(e)}")
                
    except Exception as e:
        print(f"Request Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
