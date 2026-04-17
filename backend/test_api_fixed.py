#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API 테스트 스크립트
"""
import requests
import json
import time
import sys

# UTF-8 출력 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8002"

def test_health_check():
    """헬스 체크 테스트"""
    print("\n" + "=" * 60)
    print("[TEST 1] Health Check")
    print("=" * 60)
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_checklist_replication():
    """보스 체크리스트 복제 테스트 (허용된 요청)"""
    print("\n" + "=" * 60)
    print("[TEST 2] 지난주 보스 체크리스트 복제 (허용된 요청)")
    print("=" * 60)
    try:
        payload = {
            "user_id": "test_user_001",
            "message": "지난주 보스 체크리스트를 이번주에 복제해줘",
            "char_name": "TestCharacter"
        }
        print(f"Request: {json.dumps(payload, ensure_ascii=False)}")
        response = requests.post(
            f"{BASE_URL}/api/v1/ai/chat",
            json=payload,
            timeout=30
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            resp_text = data.get('response', 'No response')
            print(f"AI Response: {resp_text[:300]}")
            # 허용된 요청이므로 유효한 응답을 받아야 함
            return len(resp_text) > 0
        else:
            print(f"Error Response: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_earnings_analysis():
    """수익 분석 테스트 (허용된 요청)"""
    print("\n" + "=" * 60)
    print("[TEST 3] 수익 분석 요청 (허용된 요청)")
    print("=" * 60)
    try:
        payload = {
            "user_id": "test_user_001",
            "message": "내 이번 주 수익이 얼마야?",
            "char_name": "TestCharacter"
        }
        print(f"Request: {json.dumps(payload, ensure_ascii=False)}")
        response = requests.post(
            f"{BASE_URL}/api/v1/ai/chat",
            json=payload,
            timeout=30
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            resp_text = data.get('response', 'No response')
            print(f"AI Response: {resp_text[:300]}")
            # 허용된 요청이므로 유효한 응답을 받아야 함
            return len(resp_text) > 0
        else:
            print(f"Error Response: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_weather_request():
    """날씨 요청 테스트 (거절되어야 함)"""
    print("\n" + "=" * 60)
    print("[TEST 4] 게임 외 주제 요청 - 날씨 (거절되어야 함)")
    print("=" * 60)
    try:
        payload = {
            "user_id": "test_user_001",
            "message": "오늘 날씨가 어떻게 돼?",
            "char_name": "TestCharacter"
        }
        print(f"Request: {json.dumps(payload, ensure_ascii=False)}")
        response = requests.post(
            f"{BASE_URL}/api/v1/ai/chat",
            json=payload,
            timeout=30
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            response_text = data.get('response', 'No response')
            print(f"AI Response: {response_text[:300]}")
            # 거절 메시지 확인
            if "죄송" in response_text or "도와드릴" in response_text:
                print("[PASSED] Correctly rejected!")
                return True
            else:
                print("[WARNING] Unexpected response")
                return False
        else:
            print(f"Error Response: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_boss_guide_request():
    """보스 공략 요청 테스트 (거절되어야 함)"""
    print("\n" + "=" * 60)
    print("[TEST 5] 게임 플레이 팁 요청 - 보스 공략 (거절되어야 함)")
    print("=" * 60)
    try:
        payload = {
            "user_id": "test_user_001",
            "message": "루시드 보스 공략 알려줄래?",
            "char_name": "TestCharacter"
        }
        print(f"Request: {json.dumps(payload, ensure_ascii=False)}")
        response = requests.post(
            f"{BASE_URL}/api/v1/ai/chat",
            json=payload,
            timeout=30
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            response_text = data.get('response', 'No response')
            print(f"AI Response: {response_text[:300]}")
            # 거절 메시지 확인
            if "죄송" in response_text or "도와드릴" in response_text:
                print("[PASSED] Correctly rejected!")
                return True
            else:
                print("[WARNING] Unexpected response")
                return False
        else:
            print(f"Error Response: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_empty_message():
    """빈 메시지 테스트 (400 Bad Request 예상)"""
    print("\n" + "=" * 60)
    print("[TEST 6] 빈 메시지 요청 (400 Bad Request 예상)")
    print("=" * 60)
    try:
        payload = {
            "user_id": "test_user_001",
            "message": "",
            "char_name": "TestCharacter"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/ai/chat",
            json=payload,
            timeout=5
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 400:
            print("[PASSED] Correctly returned 400 error!")
            return True
        else:
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    """메인 테스트 함수"""
    print("\n" + "=" * 60)
    print("AI Chat API Test")
    print("=" * 60)
    
    # 백엔드 연결 확인을 위해 잠시 대기
    print("\nWaiting for backend connection...")
    time.sleep(2)
    
    results = {
        "Health Check": test_health_check(),
        "Checklist Replication": test_checklist_replication(),
        "Earnings Analysis": test_earnings_analysis(),
        "Weather Request (should reject)": test_weather_request(),
        "Boss Guide Request (should reject)": test_boss_guide_request(),
        "Empty Message (400 expected)": test_empty_message(),
    }
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {test_name}")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")


if __name__ == "__main__":
    main()
