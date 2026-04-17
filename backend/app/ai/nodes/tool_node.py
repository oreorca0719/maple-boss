"""
Tool 실행 노드
Upstage Function Calling 포맷에 맞춘 메시지 구성
"""
import json
import logging
from typing import Any
from app.ai.state import AIState

logger = logging.getLogger(__name__)


async def tool_node(
    state: AIState,
    tools_dict: dict[str, Any],
    char_service: Any,
    user_service: Any,
    data_service: Any
) -> dict[str, Any]:
    """
    LLM이 호출한 Tool을 실제로 실행하는 노드.
    Tool 결과만 반환 (Assistant 메시지는 state에 AIMessage로 이미 존재).
    llm_node에서 AIMessage를 dict로 변환할 때 tool_calls도 함께 변환됨.
    """

    try:
        last_message = state.messages[-1]

        # Tool 호출이 없으면 빈 결과 반환
        if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
            logger.warning("No tool calls found in last message")
            return {
                "messages": [],
                "tool_results": {}
            }

        tool_results = {}
        tool_messages = []

        # 각 Tool 호출 처리
        for tool_call in last_message.tool_calls:
            tool_name = tool_call.function.name
            tool_call_id = tool_call.id
            
            logger.info(f"[tool_node] Processing tool: {tool_name}, id: {tool_call_id}")

            try:
                args = json.loads(tool_call.function.arguments)
                logger.info(f"[tool_node] Tool args: {args}")

                logger.info(f"Executing tool: {tool_name} with args: {args}")

                # Tool 함수 가져오기
                if tool_name not in tools_dict:
                    result = {
                        "success": False,
                        "error": f"알 수 없는 도구: {tool_name}"
                    }
                else:
                    tool_obj = tools_dict[tool_name]
                    
                    # LangChain StructuredTool의 경우 .invoke() 사용
                    # Tool 객체는 invoke 메서드를 통해 실행
                    try:
                        # Tool 객체에 service 파라미터 추가
                        input_with_services = args.copy()
                        
                        if tool_name == "replicate_checklist_from_last_week":
                            input_with_services["char_service"] = char_service
                        elif tool_name == "analyze_character_earnings":
                            input_with_services["char_service"] = char_service
                        elif tool_name == "get_character_checklist":
                            input_with_services["char_service"] = char_service
                        elif tool_name == "analyze_user_earnings":
                            input_with_services["user_service"] = user_service
                            input_with_services["char_service"] = char_service
                        elif tool_name == "get_top_earning_bosses":
                            input_with_services["char_service"] = char_service
                            input_with_services["data_service"] = data_service
                        
                        logger.info(f"[tool_node] Invoking tool with input: {input_with_services}")
                        
                        # StructuredTool의 invoke 메서드 호출
                        result = tool_obj.invoke(input_with_services)
                        
                        logger.info(f"[tool_node] Tool result: {result}")
                        
                    except Exception as e:
                        logger.error(f"[tool_node] Tool invoke failed: {str(e)}", exc_info=True)
                        result = {
                            "success": False,
                            "error": f"Tool 실행 오류: {str(e)}"
                        }

                logger.info(f"Tool result: {result}")

                # Tool 결과 저장
                tool_results[tool_name] = result

                # Tool 결과 메시지 추가
                # 메시지 형식: {"role": "tool", "tool_call_id": "...", "content": "..."}
                tool_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": json.dumps(result, ensure_ascii=False)
                })
                logger.info(f"[tool_node] Tool result message added for {tool_name}")

            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error for tool {tool_name}: {str(e)}")
                error_result = {
                    "success": False,
                    "error": f"Tool 파라미터 파싱 오류: {str(e)}"
                }
                tool_results[tool_name] = error_result
                tool_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": json.dumps(error_result, ensure_ascii=False)
                })

            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {str(e)}", exc_info=True)
                error_result = {
                    "success": False,
                    "error": f"Tool 실행 오류: {str(e)}"
                }
                tool_results[tool_name] = error_result
                tool_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": json.dumps(error_result, ensure_ascii=False)
                })

        return {
            "messages": tool_messages,
            "tool_results": tool_results
        }

    except Exception as e:
        logger.error(f"Error in tool_node: {str(e)}", exc_info=True)
        return {
            "messages": [],
            "tool_results": {
                "error": {
                    "success": False,
                    "error": f"Tool 노드 처리 오류: {str(e)}"
                }
            }
        }
