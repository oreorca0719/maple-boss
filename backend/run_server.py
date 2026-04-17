#!/usr/bin/env python
"""
백엔드 서버 실행 스크립트
"""
import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# 현재 디렉토리를 backend로 설정
backend_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(backend_dir)

# PYTHONPATH에 backend 디렉토리 추가
sys.path.insert(0, backend_dir)

# .env 파일 로드
env_file = Path(backend_dir) / ".env"
if env_file.exists():
    load_dotenv(env_file)
    print(f"[OK] Loaded .env from {env_file}")
else:
    print(f"[WARNING] .env file not found at {env_file}")

# uvicorn 실행
subprocess.run([
    sys.executable, "-m", "uvicorn",
    "app.main:app",
    "--host", "127.0.0.1",
    "--port", "8002",
    "--reload"
])
