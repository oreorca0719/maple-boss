#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LLM 직접 테스트
"""
import os
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Set encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Load .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

async def test_llm():
    """LLM 직접 호출 테스트"""
    print("Testing LLM connection...")
    
    api_key = os.getenv("UPSTAGE_API_KEY")
    if not api_key:
        print("ERROR: UPSTAGE_API_KEY not set")
        return False
    
    print(f"API Key (first 10 chars): {api_key[:10]}...")
    
    # LLM 초기화
    llm = ChatOpenAI(
        model="solar-pro3",
        api_key=api_key,
        base_url="https://api.upstage.ai/v1",
        temperature=0.7,
        timeout=10
    )
    
    # 간단한 메시지로 테스트
    message = [{"role": "user", "content": "안녕하세요"}]
    
    try:
        print("\nSending test message to LLM...")
        response = await llm.ainvoke(message)
        print(f"\nResponse type: {type(response)}")
        print(f"Response content (100 chars): {response.content[:100]}")
        print("\n[SUCCESS] LLM is working!")
        print(f"Full response length: {len(response.content)} characters")
        return True
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_llm())
    print(f"\nTest result: {'PASSED' if result else 'FAILED'}")
