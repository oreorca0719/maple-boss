"""
LLM Node 직접 테스트
"""
import asyncio
import sys
from dotenv import load_dotenv
from app.ai.state import AIState
from app.ai.nodes.llm_node import llm_node

# .env 로드
load_dotenv()

# UTF-8 출력 설정
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


async def test_llm_node():
    """LLM Node 테스트"""
    
    print("[TEST] LLM Node Direct Test")
    print("=" * 60)
    
    # 테스트 State 생성
    state = AIState(
        user_id="test_user_01",
        char_name=None,
        messages=[{
            "role": "user",
            "content": "지난주 보스 체크리스트를 이번주로 복제해줄 수 있어?"
        }],
        current_week="2026-W15"
    )
    
    try:
        print("Calling llm_node...")
        result = await llm_node(state, tools=[])
        
        if "messages" in result and result["messages"]:
            msg = result["messages"][0]
            content = msg.content if hasattr(msg, 'content') else str(msg)
            print(f"[SUCCESS] Response generated:")
            print(f"  {content[:200]}")
            
            # 응답 검증
            if "api_key" in content.lower() and "client option" in content.lower():
                print("[ISSUE] API Key 오류 여전히 존재")
            elif "죄송" in content and "오류" in content:
                print("[ISSUE] Error response from LLM")
            else:
                print("[PASS] Valid AI response received")
        else:
            print("[FAIL] No response generated")
            
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_llm_node())
