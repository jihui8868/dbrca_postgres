"""主智能体装配模块.

负责组合:
- OpenAI Chat 模型 (通过 `langchain_openai.ChatOpenAI`)
- 子智能体列表
- skills 目录挂载
- 日志回调注入
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI

from app.agents.subagents import ALL_SUBAGENTS
from app.core.config import get_settings
from app.core.logging_config import setup_logging

settings = get_settings()


# 确保日志系统已初始化(进程内只执行一次)
setup_logging(log_level=settings.log.LOG_LEVEL, log_dir=settings.log.LOG_DIR)

_logger = logging.getLogger("agent.main")

MAIN_SYSTEM_PROMPT = """你是一个 Postgres 数据库故障定位和根因分析 (RCA) 系统的主控智能体。
你的任务是理解用户意图，协调多个专业化的子智能体进行系统分析，最终输出完整的RCA报告。

可用的子智能体:
- log_analyzer:     日志分析 —— 解析 Postgres 错误日志、识别错误模式、诊断常见问题
- query_analyzer:   查询分析 —— 解析 EXPLAIN ANALYZE、识别性能瓶颈、提供优化建议
- metrics_analyzer: 指标分析 —— 分析缓存、连接、IO、锁等系统指标、识别瓶颈
- report_gen:       报告生成 —— 整合分析结果、生成 RCA 报告、制定行动计划

工作流程:
1. 当用户报告数据库故障或性能问题时，收集症状和上下文信息
2. 根据问题类型，委派相应的分析子智能体:
   - 有错误日志 → 委派 log_analyzer
   - 有慢查询或执行计划 → 委派 query_analyzer
   - 需要系统性能分析 → 委派 metrics_analyzer
3. 等待各子智能体的分析结果，整合关键发现
4. 最后委派 report_gen 生成综合 RCA 报告和行动计划

重要原则:
- 充分收集信息后再开始分析（询问是否有日志、查询、性能指标等）
- 并行运行多个分析以加快诊断速度
- 在调用子智能体前说明分析理由
- 整合所有结果后生成完整的问题根因和解决方案
- 保持回答清晰准确，使用中文，包含具体数据和证据

目标: 帮助用户快速定位 Postgres 性能问题的根本原因，提供可操作的优化建议。
"""


def _build_model() -> ChatOpenAI:
    if not settings.llm.api_key:
        _logger.warning("未设置 api_key, 模型调用将失败")
    return ChatOpenAI(
        model=settings.llm.model,
        api_key=settings.llm.api_key or "sk-placeholder",
        base_url=settings.llm.base_url,
        # temperature=settings.llm.temperature,
        timeout=settings.llm.timeout,
    )


def build_main_agent(session_id: Optional[str] = None) -> Any:
    """构建主智能体.

    Returns:
        已编译的 LangGraph agent (CompiledStateGraph).
    """
    session_id = session_id or uuid.uuid4().hex[:8]

    subagent_names = [sa["name"] for sa in ALL_SUBAGENTS]
    tool_counts = {sa["name"]: len(sa.get("tools", [])) for sa in ALL_SUBAGENTS}
    _logger.info(
        f"构建主智能体  subagents={subagent_names}  "
        f"tools_per_agent={tool_counts}  session={session_id}"
    )

    agent = create_deep_agent(
        model=_build_model(),
        system_prompt=MAIN_SYSTEM_PROMPT,
        subagents=ALL_SUBAGENTS,
        skills=settings.skills.sources if hasattr(settings, "skills") else [],
        name="main-agent",
    )

    _logger.info(f"主智能体构建完成  session={session_id}")
    return agent
