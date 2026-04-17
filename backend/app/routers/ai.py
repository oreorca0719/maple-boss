"""
AI 챗봇 라우터 - LangGraph 기반 AI Agent
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.ai.service import AIService
from app.dependencies import get_ai_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])


class ChatRequest(BaseModel):
    """AI 챗봇 메시지 요청"""
    user_id: str
    message: str
    char_name: str | None = None


class ChatResponse(BaseModel):
    """AI 챗봇 응답"""
    response: str
    tools_used: list[str] = []


class StreamEvent(BaseModel):
    """스트리밍 이벤트"""
    event: str
    data: dict | str | None = None


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    svc: AIService = Depends(get_ai_service)
):
    """
    AI 챗봇과 대화.

    Args:
        request: ChatRequest
            - user_id: 사용자 ID
            - message: 사용자 메시지
            - char_name: 캐릭터 이름 (선택)
        svc: AIService

    Returns:
        ChatResponse: AI 응답 및 사용 도구 목록
    """
    try:
        if not request.message or not request.message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="메시지는 비어있을 수 없습니다"
            )

        logger.info(f"Chat request: user={request.user_id}, msg={request.message[:50]}")

        # AI 서비스 실행
        response = await svc.chat(
            user_id=request.user_id,
            message=request.message,
            char_name=request.char_name
        )

        return ChatResponse(response=response, tools_used=[])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 처리 중 오류 발생: {str(e)}"
        )


@router.post("/chat/stream")
async def chat_streaming(
    request: ChatRequest,
    svc: AIService = Depends(get_ai_service)
):
    """
    AI 챗봇 스트리밍 응답.

    Args:
        request: ChatRequest
        svc: AIService

    Yields:
        각 LangGraph 노드 실행 결과 (Server-Sent Events 형식)
    """
    import json
    from fastapi.responses import StreamingResponse

    async def event_generator():
        try:
            if not request.message or not request.message.strip():
                yield f"data: {json.dumps({'error': '메시지는 비어있을 수 없습니다'})}\n\n"
                return

            logger.info(f"Streaming request: user={request.user_id}")

            async for event in svc.chat_streaming(
                user_id=request.user_id,
                message=request.message,
                char_name=request.char_name
            ):
                # 각 노드 실행 결과를 JSON으로 인코딩
                yield f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"

        except Exception as e:
            logger.error(f"Error in chat streaming: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
