"""
LangGraph 실행 테스트
"""
import asyncio
import sys
from dotenv import load_dotenv
from app.ai.service import AIService
from app.services.character_service import CharacterService
from app.services.user_service import UserService

# .env 로드
load_dotenv()

# UTF-8 출력 설정
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


async def test_graph():
    """AIService를 통한 그래프 실행 테스트"""
    
    print("[TEST] LangGraph Execution Test")
    print("=" * 60)
    
    try:
        # 더미 서비스 초기화
        char_service = CharacterService(None)
        user_service = UserService(None)
        
        # AIService 초기화
        ai_service = AIService(
            char_service=char_service,
            user_service=user_service,
            data_service=None
        )
        
        print("AIService initialized")
        
        # 채팅 테스트
        message = "지난주 보스 체크리스트를 이번주로 복제해줄 수 있어?"
        print(f"Sending: {message}")
        
        response = await ai_service.chat(
            user_id="test_user_01",
            message=message
        )
        
        print(f"[SUCCESS] Response received:")
        print(f"  {response[:300]}")
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_graph())
