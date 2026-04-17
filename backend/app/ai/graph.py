"""
LangGraph를 사용한 AI Agent 그래프 정의
"""
import logging
from typing import Literal, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage
from app.ai.state import AIState
from app.ai.nodes.llm_node import llm_node
from app.ai.nodes.tool_node import tool_node
from app.ai.nodes.output_node import output_node

logger = logging.getLogger(__name__)


def create_ai_graph(
    tools: list,
    tools_dict: dict[str, Any],
    char_service: Any,
    user_service: Any,
    data_service: Any
):
    """
    LangGraph 그래프 생성.

    Args:
        tools: LangChain Tool 리스트
        tools_dict: Tool 이름 → 함수 매핑
        char_service: CharacterService 인스턴스
        user_service: UserService 인스턴스
        data_service: 데이터 서비스 인스턴스

    Returns:
        컴파일된 그래프
    """

    # 그래프 생성
    graph_builder = StateGraph(AIState)

    # 노드 추가 (partial로 의존성 주입)
    from functools import partial

    llm_with_tools = partial(llm_node, tools=tools)
    tool_with_deps = partial(
        tool_node,
        tools_dict=tools_dict,
        char_service=char_service,
        user_service=user_service,
        data_service=data_service
    )

    graph_builder.add_node("llm", llm_with_tools)
    graph_builder.add_node("tools", tool_with_deps)
    graph_builder.add_node("output", output_node)

    # 진입점 설정
    graph_builder.set_entry_point("llm")

    # 조건부 엣지 정의 (Tool 호출 여부에 따라)
    def should_continue(state: AIState) -> Literal["tools", "output"]:
        """
        LLM 응답 후 Tool 호출 여부를 판단.
        Tool이 있으면 "tools"로, 없으면 "output"으로 이동.
        """
        logger.info(f"[should_continue] Message count: {len(state.messages)}")
        
        if not state.messages:
            logger.info("[should_continue] No messages, going to output")
            return "output"

        last_message = state.messages[-1]
        
        logger.info(f"[should_continue] Last message type: {type(last_message)}")
        logger.info(f"[should_continue] Last message class name: {last_message.__class__.__name__ if hasattr(last_message, '__class__') else 'unknown'}")

        # BaseMessage 객체인 경우
        if isinstance(last_message, BaseMessage):
            logger.info(f"[should_continue] Is BaseMessage: True")
            logger.info(f"[should_continue] Has tool_calls attr: {hasattr(last_message, 'tool_calls')}")
            if hasattr(last_message, "tool_calls"):
                logger.info(f"[should_continue] tool_calls value: {last_message.tool_calls}")
                if last_message.tool_calls:
                    tool_names = [tc.function.name for tc in last_message.tool_calls]
                    logger.info(f"[should_continue] ✓ Tool calls detected: {tool_names}")
                    return "tools"

        # LangChain 메시지 객체인 경우
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            logger.info(f"[should_continue] ✓ Tool calls detected (fallback): {[tc.function.name for tc in last_message.tool_calls]}")
            return "tools"

        # 딕셔너리인 경우
        if isinstance(last_message, dict):
            logger.info(f"[should_continue] Is dict: True")
            logger.info(f"[should_continue] Dict keys: {list(last_message.keys())}")
            if last_message.get("tool_calls"):
                logger.info(f"[should_continue] ✓ Tool calls in dict: {last_message.get('tool_calls')}")
                return "tools"

        logger.info("[should_continue] ✗ No tool calls detected, going to output")
        
        # 메시지 content 확인
        if hasattr(last_message, 'content'):
            logger.info(f"[should_continue] Message content (first 100): {str(last_message.content)[:100]}")
        
        return "output"

    # 엣지 정의
    graph_builder.add_conditional_edges("llm", should_continue)
    graph_builder.add_edge("tools", "llm")  # Tool 실행 후 다시 LLM (반복)
    graph_builder.add_edge("output", END)

    # 그래프 컴파일
    graph = graph_builder.compile()

    logger.info("AI Graph created successfully")

    return graph
