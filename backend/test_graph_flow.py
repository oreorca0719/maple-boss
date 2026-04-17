#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Graph 실행 흐름 테스트
"""
import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Set encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Load .env
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Set up Django/DB (if needed)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

async def test_graph():
    """Graph 실행 테스트"""
    print("Testing AI Service Graph Flow...")
    
    try:
        from app.ai.service import AIService
        from app.services.character_service import CharacterService
        from app.services.user_service import UserService
        
        # Services 초기화 (더미로)
        char_service = CharacterService()
        user_service = UserService()
        data_service = None
        
        # AI Service 초기화
        ai_service = AIService(
            char_service=char_service,
            user_service=user_service,
            data_service=data_service
        )
        
        print(f"\n[Step 1] AI Service initialized")
        print(f"Tools available: {[t.name for t in ai_service.tools]}")
        
        # 테스트 메시지
        test_message = "지난주 보스 체크리스트를 이번주에 복제해줘"
        user_id = "test_user"
        char_name = "TestChar"
        
        print(f"\n[Step 2] Calling chat()...")
        print(f"Message: {test_message}")
        print(f"User: {user_id}, Char: {char_name}")
        
        # Chat 실행
        response = await ai_service.chat(
            user_id=user_id,
            message=test_message,
            char_name=char_name
        )
        
        print(f"\n[Step 3] Response received")
        print(f"Response type: {type(response)}")
        print(f"Response (first 200 chars): {response[:200]}")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_graph())
    print(f"\nTest result: {'PASSED' if result else 'FAILED'}")
