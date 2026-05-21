"""WebSocket API for实时多智能体交互.

提供WebSocket接口用于实时流式交互。
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.agents.main_agent import build_main_agent

_logger = logging.getLogger("api.websocket")

ws_router = APIRouter()

# 活跃连接管理
_connections: dict[str, list[WebSocket]] = {}


@ws_router.websocket("/ws/analyze/{session_id}")
async def websocket_analyze(websocket: WebSocket, session_id: str):
    """WebSocket端点用于实时代理交互.

    支持实时问题分析和流式响应。
    """
    await websocket.accept()
    _logger.info(f"WebSocket连接建立: session={session_id}")

    # 添加到连接列表
    if session_id not in _connections:
        _connections[session_id] = []
    _connections[session_id].append(websocket)

    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                query = message.get("query", "")
                debug = message.get("debug", False)

                if not query:
                    await websocket.send_json({
                        "type": "error",
                        "content": "查询内容不能为空",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    continue

                _logger.info(f"处理WebSocket查询: session={session_id}, query={query[:50]}...")

                # 发送处理中消息
                await websocket.send_json({
                    "type": "start",
                    "content": "开始分析...",
                    "timestamp": datetime.utcnow().isoformat()
                })

                # 构建并调用代理
                agent = build_main_agent(session_id)

                start_time = datetime.utcnow()
                result = agent.invoke(
                    {
                        "messages": [
                            {
                                "role": "user",
                                "content": query
                            }
                        ]
                    },
                    {
                        "configurable": {
                            "thread_id": session_id,
                            "debug": debug
                        }
                    }
                )

                # 发送中间步骤
                if result and "messages" in result:
                    messages = result["messages"]

                    # 发送中间消息
                    for msg in messages[:-1]:
                        content = ""
                        if hasattr(msg, "content"):
                            content = msg.content
                        elif isinstance(msg, dict) and "content" in msg:
                            content = msg["content"]

                        if content:
                            await websocket.send_json({
                                "type": "thinking",
                                "content": content[:1000],
                                "timestamp": datetime.utcnow().isoformat()
                            })

                    # 发送最终响应
                    if messages:
                        last_msg = messages[-1]
                        response_content = ""
                        if hasattr(last_msg, "content"):
                            response_content = last_msg.content
                        elif isinstance(last_msg, dict) and "content" in last_msg:
                            response_content = last_msg["content"]

                        if response_content:
                            await websocket.send_json({
                                "type": "response",
                                "content": response_content,
                                "timestamp": datetime.utcnow().isoformat()
                            })

                # 发送完成消息
                end_time = datetime.utcnow()
                processing_time = (end_time - start_time).total_seconds()

                await websocket.send_json({
                    "type": "end",
                    "content": f"分析完成（耗时 {processing_time:.1f}s）",
                    "processing_time_ms": processing_time * 1000,
                    "timestamp": end_time.isoformat()
                })

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "content": "无效的JSON格式",
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                _logger.error(f"处理WebSocket消息失败: {str(e)}", exc_info=True)
                await websocket.send_json({
                    "type": "error",
                    "content": f"处理失败: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat()
                })

    except WebSocketDisconnect:
        _logger.info(f"WebSocket连接断开: session={session_id}")
        _connections[session_id].remove(websocket)
        if not _connections[session_id]:
            del _connections[session_id]

    except Exception as e:
        _logger.error(f"WebSocket错误: {str(e)}", exc_info=True)
        try:
            await websocket.close(code=status.WS_1011_SERVER_ERROR)
        except Exception:
            pass


@ws_router.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """WebSocket聊天端点.

    支持多轮对话，保持会话状态。
    """
    await websocket.accept()
    _logger.info(f"WebSocket聊天连接: session={session_id}")

    if session_id not in _connections:
        _connections[session_id] = []
    _connections[session_id].append(websocket)

    # 初始化会话消息历史
    messages = []

    try:
        while True:
            data = await websocket.receive_text()

            try:
                payload = json.loads(data)
                user_query = payload.get("query", "")

                if not user_query:
                    await websocket.send_json({
                        "type": "error",
                        "content": "查询内容不能为空"
                    })
                    continue

                # 添加用户消息到历史
                messages.append({
                    "role": "user",
                    "content": user_query
                })

                _logger.info(f"处理聊天: session={session_id}, msg_count={len(messages)}")

                # 调用代理
                agent = build_main_agent(session_id)

                start_time = datetime.utcnow()
                result = agent.invoke(
                    {"messages": messages},
                    {
                        "configurable": {
                            "thread_id": session_id,
                            "debug": False
                        }
                    }
                )

                # 提取助手响应
                assistant_response = ""
                if result and "messages" in result:
                    result_messages = result["messages"]
                    if result_messages:
                        last_msg = result_messages[-1]
                        if hasattr(last_msg, "content"):
                            assistant_response = last_msg.content
                        elif isinstance(last_msg, dict):
                            assistant_response = last_msg.get("content", "")

                # 添加助手消息到历史
                messages.append({
                    "role": "assistant",
                    "content": assistant_response
                })

                end_time = datetime.utcnow()
                processing_time = (end_time - start_time).total_seconds()

                # 发送响应
                await websocket.send_json({
                    "type": "response",
                    "content": assistant_response,
                    "processing_time_ms": processing_time * 1000,
                    "message_count": len(messages),
                    "timestamp": end_time.isoformat()
                })

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "content": "无效的JSON格式"
                })
            except Exception as e:
                _logger.error(f"处理聊天消息失败: {str(e)}", exc_info=True)
                await websocket.send_json({
                    "type": "error",
                    "content": f"处理失败: {str(e)}"
                })

    except WebSocketDisconnect:
        _logger.info(f"聊天连接断开: session={session_id}")
        _connections[session_id].remove(websocket)
        if not _connections[session_id]:
            del _connections[session_id]

    except Exception as e:
        _logger.error(f"WebSocket聊天错误: {str(e)}", exc_info=True)
        try:
            await websocket.close(code=status.WS_1011_SERVER_ERROR)
        except Exception:
            pass


__all__ = ["ws_router"]
