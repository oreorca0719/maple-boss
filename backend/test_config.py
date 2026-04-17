#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
설정 로드 테스트
"""
from pathlib import Path
import os

print("Current working directory:", os.getcwd())
print("\n.env 파일 위치:")
env_path = Path(__file__).parent / ".env"
print(f"Expected: {env_path}")
print(f"Exists: {env_path.exists()}")

if env_path.exists():
    print(f"\n.env 파일 내용:")
    with open(env_path) as f:
        content = f.read()
        # API 키는 숨기기
        for line in content.split('\n'):
            if 'UPSTAGE_API_KEY' in line:
                parts = line.split('=')
                print(f"{parts[0]}={parts[1][:10]}..." if len(parts) > 1 else line)
            else:
                print(line)

print("\n\nSettings 로드 테스트:")
try:
    from app.config import get_settings
    settings = get_settings()
    
    print(f"upstage_api_key: {settings.upstage_api_key[:10] + '...' if settings.upstage_api_key else 'NOT SET'}")
    print(f"nexon_api_key: {settings.nexon_api_key[:10] + '...' if settings.nexon_api_key else 'NOT SET'}")
    print(f"app_env: {settings.app_env}")
    
    # 환경 변수 직접 확인
    print(f"\nos.getenv('UPSTAGE_API_KEY'): {os.getenv('UPSTAGE_API_KEY')[:10] + '...' if os.getenv('UPSTAGE_API_KEY') else 'NOT SET'}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
