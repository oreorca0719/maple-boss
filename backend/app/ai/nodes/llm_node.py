"""
LLM 호출 노드 (Upstage OpenAI 호환 API 사용)
"""
import asyncio
import logging
import json
from typing import Any
from openai import AsyncOpenAI
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage, ToolMessage
from app.ai.state import AIState
from app.config import get_settings

logger = logging.getLogger(__name__)

# 내부 주입 파라미터 (API 스키마에서 제외)
INTERNAL_PARAMS = {'char_service', 'user_service', 'data_service'}


def convert_langchain_tools_to_openai_format(tools: list) -> list:
    """LangChain Tool을 OpenAI 함수 정의 포맷으로 변환"""
    openai_tools = []
    
    for tool in tools:
        openai_tool = {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
        
        # Tool의 args_schema가 있으면 파라미터 추출
        if hasattr(tool, 'args_schema') and tool.args_schema:
            schema = tool.args_schema
            if hasattr(schema, 'model_fields'):
                # Pydantic model
                for field_name, field_info in schema.model_fields.items():
                    # 내부 서비스 파라미터는 제외
                    if field_name in INTERNAL_PARAMS:
                        logger.info(f"[llm_node] Excluding internal param: {field_name} from {tool.name}")
                        continue
                    
                    openai_tool["function"]["parameters"]["properties"][field_name] = {
                        "type": "string",
                        "description": field_info.description or ""
                    }
                    if field_info.is_required():
                        openai_tool["function"]["parameters"]["required"].append(field_name)
        
        openai_tools.append(openai_tool)
    
    return openai_tools


async def llm_node(state: AIState, tools: list) -> dict[str, Any]:
    """
    LLM을 호출하는 노드 (Upstage OpenAI 호환 API 사용).
    AIMessage의 tool_calls를 dict 형태로 변환하여 API 호출.
    
    === 핵심 규칙 ===
    1. Tool에서 반환된 데이터만 사용
    2. 존재하지 않는 데이터는 절대 생성하지 않음
    3. 데이터가 없으면 "데이터 없음" 명시
    """

    try:
        # 설정에서 API 키 가져오기
        settings = get_settings()
        api_key = settings.upstage_api_key
        
        logger.info(f"[llm_node] API Key from settings: {api_key[:10] if api_key else 'EMPTY'}...")
        
        if not api_key or api_key == "":
            logger.error("[llm_node] UPSTAGE_API_KEY is not configured or empty")
            return {
                "messages": [AIMessage(content="죄송합니다. AI 시스템이 제대로 구성되지 않았습니다.")]
            }

        # AsyncOpenAI 클라이언트 초기화 (Upstage base_url)
        logger.info("[llm_node] Initializing Upstage OpenAI client...")
        
        client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.upstage.ai/v1"
        )

        logger.info("[llm_node] Client initialized")

        # 시스템 프롬프트 - 매우 엄격한 지침
        system_prompt = """당신은 메이플스토리 주간 보스 관리 AI 어시스턴트입니다.

=== 당신의 역할 (ONLY) ===
1. 보스 체크리스트 조회 및 관리
2. Tool에서 반환된 데이터를 기반으로 한 수익 분석
3. 현재 주차 정보 안내

=== 절대 지키는 규칙 (CRITICAL) ===
✓ Tool 결과 데이터만 사용 (절대 추측/예상 데이터 금지)
✓ 과거 주차 데이터는 Tool 결과가 있을 때만 표시
✓ 역사 데이터(W13, W14, W15 등)가 없으면 절대 생성하지 말 것
✓ 데이터가 없으면 명시적으로 "정보 없음" 또는 "조회 불가" 표시
✓ 게임 공략, 팁, 아이템, 스킬 정보는 제공하지 말 것

=== 응답 포맷 (엄격히 준수) ===
1. 현재 주차 체크리스트 → Tool 결과만 표시
2. 총 수익 → Tool에서 받은 수치만 표시
3. 과거 수익 비교 → Tool 결과가 있을 때만 표시
4. 없으면: "현재 {current_week} 주차 데이터만 조회 가능합니다. 이전 주차 데이터는 저장되지 않습니다."

=== 금지 사항 ===
✗ 과거 주차의 가상의 수익 수치 생성
✗ 예상 수익이나 평균값 계산
✗ 게임 공략 팁, 패턴 분석, 난이도 공략법
✗ 존재하지 않는 통계 데이터 제공

=== 사용자 정보 ===
- 사용자 ID: {user_id}
- 현재 주차: {current_week}
- 캐릭터: {char_name}

=== 응답 스타일 ===
- 한국어로 친근하게
- 수익은 "메소" 단위로만 표시
- 확실한 데이터만 표시"""

        system_message = system_prompt.format(
            user_id=state.user_id,
            current_week=state.current_week,
            char_name=state.char_name or "정보 없음"
        )

        # 메시지 변환
        messages = [{"role": "system", "content": system_message}]
        
        for msg in state.messages:
            if isinstance(msg, BaseMessage):
                if isinstance(msg, AIMessage):
                    # AIMessage를 dict로 변환 (tool_calls 포함)
                    msg_dict = {"role": "assistant", "content": msg.content}
                    # tool_calls가 있으면 포함
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        msg_dict["tool_calls"] = [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            }
                            for tc in msg.tool_calls
                        ]
                        logger.info(f"[llm_node] AIMessage contains {len(msg.tool_calls)} tool_calls")
                    messages.append(msg_dict)
                elif isinstance(msg, HumanMessage):
                    messages.append({"role": "user", "content": msg.content})
                elif isinstance(msg, ToolMessage):
                    messages.append({
                        "role": "tool", 
                        "content": msg.content, 
                        "tool_call_id": getattr(msg, 'tool_call_id', '')
                    })
            elif isinstance(msg, dict):
                # dict 메시지는 그대로 통과 (이미 올바른 형식)
                messages.append(msg)

        logger.info(f"[llm_node] Messages prepared: {len(messages)} messages")
        logger.info(f"[llm_node] Message structure: {[m.get('role') for m in messages]}")

        # Tools를 OpenAI 포맷으로 변환
        openai_tools = convert_langchain_tools_to_openai_format(tools) if tools else []
        
        logger.info(f"[llm_node] Converted {len(openai_tools)} tools to OpenAI format")
        if openai_tools:
            for tool in openai_tools:
                logger.info(f"[llm_node] Tool: {tool['function']['name']}")

        # API 호출 (tool_choice="auto" 활성화)
        call_kwargs = {
            "model": "solar-pro3",
            "messages": messages,
            "temperature": 0.3,  # 낮춰서 hallucination 줄이기
            "timeout": 60.0
        }
        
        if openai_tools:
            call_kwargs["tools"] = openai_tools
            call_kwargs["tool_choice"] = "auto"
            logger.info(f"[llm_node] Tools enabled: {len(openai_tools)} tools")
        
        logger.info("[llm_node] Calling Upstage API...")
        logger.info(f"[llm_node] Message count: {len(messages)}")
        
        response = await client.chat.completions.create(**call_kwargs)

        logger.info(f"[llm_node] Response received")
        
        response_message = response.choices[0].message
        
        # 응답을 AIMessage로 변환
        ai_message = AIMessage(content=response_message.content or "")
        
        # Tool calls가 있으면 메타데이터에 저장
        if hasattr(response_message, 'tool_calls') and response_message.tool_calls:
            logger.info(f"[llm_node] Tool calls detected: {[tc.function.name for tc in response_message.tool_calls]}")
            ai_message.tool_calls = response_message.tool_calls
        else:
            logger.info("[llm_node] No tool calls in response")
        
        return {
            "messages": [ai_message]
        }

    except Exception as e:
        logger.error(f"[llm_node] Error: {str(e)}", exc_info=True)
        return {
            "messages": [AIMessage(content=f"죄송합니다. AI 처리 중 오류가 발생했습니다: {str(e)}")]
        }
