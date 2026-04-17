#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
빠른 테스트
"""
import requests
import time

print("헬스 체크 중...")
try:
    r = requests.get('http://127.0.0.1:8002/health', timeout=5)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")
except Exception as e:
    print(f"Error: {e}")

print("\nAI 요청 중...")
try:
    r = requests.post(
        'http://127.0.0.1:8002/api/v1/ai/chat',
        json={
            'user_id': 'test_user',
            'message': '안녕하세요',
            'char_name': 'TestChar'
        },
        timeout=30
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        response = data.get('response', 'No response')
        print(f"Response (first 200 chars): {response[:200]}")
    else:
        print(f"Error: {r.text}")
except Exception as e:
    print(f"Error: {e}")

print("\nTest completed!")
