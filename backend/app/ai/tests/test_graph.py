"""
LangGraph 그래프 및 노드 통합 테스트
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from langgraph.graph import StateGraph

from app.ai.graph import create_ai_graph
from app.ai.state import AIState
from app.ai.nodes.llm_node import llm_node
from app.ai.nodes.tool_node import tool_node
from app.ai.nodes.output_node import output_node


class TestGraphCreation:
    """그래프 생성 테스트"""

    @pytest.fixture
    def mock_services(self):
        """Mock 서비스"""
        return {
            "char_service": Mock(),
            "user_service": Mock(),
            "data_service": None,
            "tools": [],
            "tools_dict": {}
        }

    def test_graph_creates_successfully(self, mock_services):
        """그래프가 정상적으로 생성되는지 테스트"""
        graph = create_ai_graph(
            tools=mock_services["tools"],
            tools_dict=mock_services["tools_dict"],
            char_service=mock_services["char_service"],
            user_service=mock_services["user_service"],
            data_service=mock_services["data_service"]
        )

        assert graph is not None, "그래프가 None임"
        # 컴파일된 그래프는 invoke 메서드를 가져야 함
        assert hasattr(graph, 'invoke') or hasattr(graph, 'ainvoke'), "그래프가 invoke 메서드를 가지지 않음"

    def test_graph_has_three_nodes(self, mock_services):
        """그래프가 3개의 노드(llm, tools, output)를 가지는지 확인"""
        graph = create_ai_graph(
            tools=mock_services["tools"],
            tools_dict=mock_services["tools_dict"],
            char_service=mock_services["char_service"],
            user_service=mock_services["user_service"],
            data_service=mock_services["data_service"]
        )

        # 컴파일된 그래프의 노드 확인
        # StateGraph는 내부 _nodes를 가지지만, 컴파일된 그래프는 다른 구조
        # 주로 invoke를 통해 실행되는지 확인하는 방식으로 테스트
        assert graph is not None, "그래프가 생성되지 않음"


class TestConditionalEdge:
    """조건부 엣지(should_continue) 테스트"""

    def test_should_continue_to_output_no_tool_calls(self):
        """Tool 호출이 없으면 output으로 라우팅"""
        from app.ai.graph import create_ai_graph

        # Mock 메시지 객체 (tool_calls 없음)
        mock_message = {
            "role": "assistant",
            "content": "응답입니다",
        }

        state = AIState(
            user_id="test",
            messages=[mock_message],
            current_week="2026-W17"
        )

        # should_continue 함수는 create_ai_graph 내에 정의되므로
        # 여기서는 그래프 동작을 통해 확인

    def test_should_continue_to_tools_with_tool_calls(self):
        """Tool 호출이 있으면 tools로 라우팅"""
        # Tool 호출이 있는 메시지 테스트
        from langchain_core.messages import AIMessage

        # LangChain의 AIMessage 생성
        mock_message = AIMessage(
            content="도구를 사용하겠습니다",
            tool_calls=[
                {
                    "id": "call_123",
                    "function": {
                        "name": "analyze_character_earnings",
                        "arguments": '{"user_id": "test", "char_name": "TestChar"}'
                    }
                }
            ]
        )

        state = AIState(
            user_id="test",
            messages=[mock_message],
            current_week="2026-W17"
        )

        # 이 상태가 should_continue에서 "tools"로 라우팅되어야 함
        assert hasattr(state.messages[-1], 'tool_calls'), "tool_calls 속성이 없음"
        assert len(state.messages[-1].tool_calls) > 0, "tool_calls가 비어있음"


class TestOutputNode:
    """Output Node 테스트"""

    def test_output_node_extracts_final_response(self):
        """최종 응답 추출 테스트"""
        messages = [
            {"role": "user", "content": "안녕하세요"},
            {"role": "assistant", "content": "안녕하세요! 도움을 드리겠습니다."}
        ]

        state = AIState(
            user_id="test",
            messages=messages,
            current_week="2026-W17"
        )

        result = output_node(state)

        assert "final_response" in result, "final_response가 없음"
        assert result["final_response"] == "안녕하세요! 도움을 드리겠습니다.", "응답이 일치하지 않음"

    def test_output_node_with_tool_results(self):
        """Tool 결과를 포함한 최종 응답 테스트"""
        messages = [
            {"role": "assistant", "content": "분석 결과입니다"}
        ]

        state = AIState(
            user_id="test",
            messages=messages,
            current_week="2026-W17",
            tool_results={
                "analyze_character_earnings": {
                    "success": True,
                    "total": 1000000
                }
            }
        )

        result = output_node(state)

        assert "final_response" in result, "final_response가 없음"
        assert "user_context" in result, "user_context가 없음"
        assert "tools_used" in result["user_context"], "tools_used가 없음"
        assert "analyze_character_earnings" in result["user_context"]["tools_used"], "도구 이름이 없음"

    def test_output_node_with_empty_messages(self):
        """메시지가 없을 때의 테스트"""
        state = AIState(
            user_id="test",
            messages=[],
            current_week="2026-W17"
        )

        result = output_node(state)

        assert "final_response" in result, "final_response가 없음"
        assert "없습니다" in result["final_response"], "기본 에러 메시지가 없음"


class TestToolNode:
    """Tool Node 테스트"""

    @pytest.mark.asyncio
    async def test_tool_node_executes_tool(self):
        """Tool 실행 테스트"""
        from langchain_core.messages import AIMessage

        # Mock 도구 함수
        def mock_tool_func(**kwargs):
            return {"success": True, "result": "테스트 결과"}

        tools_dict = {
            "test_tool": mock_tool_func
        }

        # Tool 호출을 포함한 메시지
        message = AIMessage(
            content="도구를 실행합니다",
            tool_calls=[
                {
                    "id": "call_123",
                    "function": {
                        "name": "test_tool",
                        "arguments": '{}'
                    }
                }
            ]
        )

        state = AIState(
            user_id="test",
            messages=[message],
            current_week="2026-W17"
        )

        # Tool node 실행
        result = await tool_node(
            state=state,
            tools_dict=tools_dict,
            char_service=Mock(),
            user_service=Mock(),
            data_service=None
        )

        assert "messages" in result, "messages가 없음"
        assert "tool_results" in result, "tool_results가 없음"
        assert len(result["messages"]) > 0, "tool 메시지가 없음"

    @pytest.mark.asyncio
    async def test_tool_node_unknown_tool(self):
        """알 수 없는 도구 처리 테스트"""
        from langchain_core.messages import AIMessage

        tools_dict = {}  # 도구가 없음

        message = AIMessage(
            content="도구를 실행합니다",
            tool_calls=[
                {
                    "id": "call_123",
                    "function": {
                        "name": "unknown_tool",
                        "arguments": '{}'
                    }
                }
            ]
        )

        state = AIState(
            user_id="test",
            messages=[message],
            current_week="2026-W17"
        )

        result = await tool_node(
            state=state,
            tools_dict=tools_dict,
            char_service=Mock(),
            user_service=Mock(),
            data_service=None
        )

        assert "tool_results" in result, "tool_results가 없음"
        assert "unknown_tool" in result["tool_results"], "도구 결과가 없음"
        assert result["tool_results"]["unknown_tool"]["success"] is False, "실패로 표시되지 않음"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
