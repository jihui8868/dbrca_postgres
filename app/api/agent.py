"""多智能体API端点.

提供直接调用主代理的REST接口，支持流式响应。
"""

from __future__ import annotations

import uuid
import logging
from datetime import datetime
from typing import Optional, Any, AsyncGenerator

from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Query
from pydantic import BaseModel, Field

from app.agents.main_agent import build_main_agent

_logger = logging.getLogger("api.agent")

# 创建API路由
agent_router = APIRouter(prefix="/api/agent", tags=["Agent"])


# ============================================================================
# 数据模型
# ============================================================================


class AgentQueryRequest(BaseModel):
    """代理查询请求."""

    query: str = Field(..., min_length=1, max_length=5000, description="用户查询内容")
    session_id: Optional[str] = Field(None, description="会话ID，如果为None则生成新的")
    debug: bool = Field(False, description="是否输出调试信息")


class AgentQueryResponse(BaseModel):
    """代理查询响应."""

    session_id: str
    query: str
    response: str
    timestamp: datetime
    processing_time_ms: float


class StreamMessage(BaseModel):
    """流式消息."""

    type: str  # "start", "thinking", "response", "end", "error"
    content: str
    timestamp: datetime


class AgentHealthResponse(BaseModel):
    """代理健康检查响应."""

    status: str
    session_count: int
    agent_status: dict[str, str]
    timestamp: datetime


# ============================================================================
# 全局状态
# ============================================================================

# 活跃会话
_active_sessions: dict[str, dict[str, Any]] = {}


# ============================================================================
# API端点
# ============================================================================


@agent_router.post("/query", response_model=AgentQueryResponse)
async def query_agent(req: AgentQueryRequest) -> AgentQueryResponse:
    """同步查询代理.

    接收用户查询，调用主代理进行分析，返回完整结果。
    """
    session_id = req.session_id or uuid.uuid4().hex[:16]
    start_time = datetime.utcnow()

    try:
        _logger.info(f"处理代理查询: session={session_id}, query={req.query[:50]}...")

        # 构建主代理
        agent = build_main_agent(session_id)

        # 调用代理
        result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": req.query
                    }
                ]
            },
            {
                "configurable": {
                    "thread_id": session_id,
                    "debug": req.debug
                }
            }
        )

        # 提取响应
        response_text = ""
        if result and "messages" in result:
            messages = result["messages"]
            if messages:
                last_msg = messages[-1]
                if hasattr(last_msg, "content"):
                    response_text = last_msg.content
                elif isinstance(last_msg, dict) and "content" in last_msg:
                    response_text = last_msg["content"]

        # 计算处理时间
        end_time = datetime.utcnow()
        processing_time_ms = (end_time - start_time).total_seconds() * 1000

        # 记录会话
        _active_sessions[session_id] = {
            "created_at": start_time,
            "last_query": req.query,
            "last_response": response_text,
            "query_count": _active_sessions.get(session_id, {}).get("query_count", 0) + 1
        }

        _logger.info(f"代理查询完成: session={session_id}, time={processing_time_ms:.0f}ms")

        return AgentQueryResponse(
            session_id=session_id,
            query=req.query,
            response=response_text,
            timestamp=end_time,
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        _logger.error(f"代理查询失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"代理查询失败: {str(e)}"
        )


@agent_router.get("/stream/{session_id}")
async def stream_query(
    session_id: str,
    query: str = Query(..., min_length=1)
) -> AsyncGenerator[StreamMessage, None]:
    """流式查询代理.

    实时流式返回代理的分析过程和结果。
    """
    try:
        _logger.info(f"开始流式查询: session={session_id}, query={query[:50]}...")

        # 初始化消息
        yield StreamMessage(
            type="start",
            content=f"开始分析...",
            timestamp=datetime.utcnow()
        )

        # 构建主代理
        agent = build_main_agent(session_id)

        # 调用代理（实际应用中可能需要异步处理）
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
                    "debug": True  # 流式模式启用调试
                }
            }
        )

        # 发送思考过程（如果有）
        if result and "messages" in result:
            messages = result["messages"]
            for i, msg in enumerate(messages[:-1]):  # 除了最后一条
                if hasattr(msg, "content"):
                    content = msg.content
                elif isinstance(msg, dict) and "content" in msg:
                    content = msg["content"]
                else:
                    continue

                yield StreamMessage(
                    type="thinking",
                    content=content[:500],  # 截断长消息
                    timestamp=datetime.utcnow()
                )

        # 发送最终响应
        if result and "messages" in result:
            messages = result["messages"]
            if messages:
                last_msg = messages[-1]
                response_content = ""
                if hasattr(last_msg, "content"):
                    response_content = last_msg.content
                elif isinstance(last_msg, dict) and "content" in last_msg:
                    response_content = last_msg["content"]

                yield StreamMessage(
                    type="response",
                    content=response_content,
                    timestamp=datetime.utcnow()
                )

        # 发送完成消息
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()

        yield StreamMessage(
            type="end",
            content=f"分析完成（耗时 {processing_time:.1f}s）",
            timestamp=end_time
        )

    except Exception as e:
        _logger.error(f"流式查询失败: {str(e)}", exc_info=True)
        yield StreamMessage(
            type="error",
            content=f"错误: {str(e)}",
            timestamp=datetime.utcnow()
        )


class AnalyzeRequest(BaseModel):
    """分析请求模型."""
    query: str = Field(..., min_length=1)
    log_content: Optional[str] = None
    explain_plan: Optional[str] = None
    metrics: Optional[dict[str, Any]] = None


@agent_router.post("/analyze")
async def analyze_issue(req: AnalyzeRequest) -> AgentQueryResponse:
    """智能问题分析.

    综合日志、查询计划和性能指标进行根因分析。
    """
    session_id = uuid.uuid4().hex[:16]
    start_time = datetime.utcnow()

    try:
        # 构建综合查询
        full_query = f"请分析以下问题: {req.query}\n"

        if req.log_content:
            full_query += f"\n日志内容:\n{req.log_content[:1000]}\n"

        if req.explain_plan:
            full_query += f"\n执行计划:\n{req.explain_plan[:500]}\n"

        if req.metrics:
            full_query += f"\n性能指标:\n"
            for key, value in list(req.metrics.items())[:5]:  # 只显示前5个指标
                full_query += f"- {key}: {value}\n"

        full_query += "\n请进行全面的根因分析，提供具体的优化建议。"

        # 调用代理
        agent = build_main_agent(session_id)

        result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": full_query
                    }
                ]
            },
            {
                "configurable": {
                    "thread_id": session_id,
                    "debug": False
                }
            }
        )

        # 提取响应
        response_text = ""
        if result and "messages" in result:
            messages = result["messages"]
            if messages:
                last_msg = messages[-1]
                if hasattr(last_msg, "content"):
                    response_text = last_msg.content

        end_time = datetime.utcnow()
        processing_time_ms = (end_time - start_time).total_seconds() * 1000

        _logger.info(f"问题分析完成: session={session_id}, time={processing_time_ms:.0f}ms")

        return AgentQueryResponse(
            session_id=session_id,
            query=req.query,
            response=response_text,
            timestamp=end_time,
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        _logger.error(f"问题分析失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"问题分析失败: {str(e)}"
        )


@agent_router.post("/diagnose")
async def diagnose_database(
    db_host: str = Query(..., description="数据库主机"),
    issue_description: str = Query(..., description="问题描述"),
    background_tasks: BackgroundTasks = None
) -> dict[str, Any]:
    """数据库诊断分析.

    对数据库问题进行诊断并生成完整的RCA报告。
    """
    session_id = uuid.uuid4().hex[:16]
    start_time = datetime.utcnow()

    try:
        _logger.info(f"开始数据库诊断: session={session_id}, host={db_host}")

        query = f"""请对以下数据库问题进行诊断：

数据库: {db_host}
问题描述: {issue_description}

请执行以下分析步骤:
1. 首先判断问题的严重程度
2. 分析可能的根本原因
3. 列出相关的日志信息（如果有）
4. 建议的解决方案
5. 预防措施

请提供详细的诊断报告。"""

        # 调用主代理
        agent = build_main_agent(session_id)

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
                    "debug": False
                }
            }
        )

        # 提取响应
        diagnosis = ""
        if result and "messages" in result:
            messages = result["messages"]
            if messages:
                last_msg = messages[-1]
                if hasattr(last_msg, "content"):
                    diagnosis = last_msg.content

        end_time = datetime.utcnow()
        processing_time_ms = (end_time - start_time).total_seconds() * 1000

        _active_sessions[session_id] = {
            "created_at": start_time,
            "db_host": db_host,
            "issue": issue_description,
            "status": "completed"
        }

        _logger.info(f"数据库诊断完成: session={session_id}")

        return {
            "session_id": session_id,
            "db_host": db_host,
            "issue": issue_description,
            "diagnosis": diagnosis,
            "processing_time_ms": processing_time_ms,
            "timestamp": end_time
        }

    except Exception as e:
        _logger.error(f"数据库诊断失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"数据库诊断失败: {str(e)}"
        )


@agent_router.get("/sessions")
async def list_sessions() -> dict[str, Any]:
    """列出所有活跃会话."""
    return {
        "total_sessions": len(_active_sessions),
        "sessions": [
            {
                "session_id": sid,
                "created_at": info.get("created_at"),
                "query_count": info.get("query_count", 1),
                "last_updated": info.get("last_updated", info.get("created_at"))
            }
            for sid, info in _active_sessions.items()
        ]
    }


@agent_router.get("/sessions/{session_id}")
async def get_session(session_id: str) -> dict[str, Any]:
    """获取会话信息."""
    if session_id not in _active_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话 {session_id} 不存在"
        )

    info = _active_sessions[session_id]
    return {
        "session_id": session_id,
        "created_at": info.get("created_at"),
        "query_count": info.get("query_count", 1),
        "last_query": info.get("last_query"),
        "last_response": info.get("last_response", "")[:500]  # 截断长响应
    }


@agent_router.delete("/sessions/{session_id}")
async def delete_session(session_id: str) -> dict[str, str]:
    """删除会话."""
    if session_id not in _active_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话 {session_id} 不存在"
        )

    del _active_sessions[session_id]
    _logger.info(f"会话已删除: {session_id}")

    return {"message": f"会话 {session_id} 已删除"}


@agent_router.get("/health", response_model=AgentHealthResponse)
async def health_check() -> AgentHealthResponse:
    """代理健康检查."""
    return AgentHealthResponse(
        status="healthy",
        session_count=len(_active_sessions),
        agent_status={
            "log_analyzer": "ready",
            "query_analyzer": "ready",
            "metrics_analyzer": "ready",
            "report_gen": "ready"
        },
        timestamp=datetime.utcnow()
    )


__all__ = ["agent_router"]
