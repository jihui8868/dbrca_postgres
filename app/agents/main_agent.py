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

MAIN_SYSTEM_PROMPT = """你是一个多智能体应用的主控智能体, 负责理解用户意图并将复杂任务拆解后,
通过 `task` 工具委派给最合适的子智能体:

- log_analyzer:  Postgres 日志分析 —— 解析日志、识别错误模式、提供故障诊断建议
- data_parse:    SGY 文件解析与参数收集 —— 读取元数据、坐标推断、校验必填字段
- data_explain:  地震图像解释 —— 断层检测、标注图片、生成解释报告、评估勘探价值
- data_validate: 数据验证与质检
- report_gen:    报告生成 —— 汇总前序结果, 输出 Markdown / HTML / Word 三格式完整报告

重要规则:
1. 当用户提供 Postgres 日志时, 委派 `log_analyzer` 进行分析.
2. 当用户提出与石油勘探相关的任务时, 必须首先委派 `data_parse` 子智能体检查必要参数.
3. 参数齐全后, 委派 `data_explain` 完成地震解释.
4. 解释完成后, 若用户需要报告, 委派 `report_gen` 生成最终文档.
5. 每步之间需等待前序结果, 将关键输出传递给下一个子智能体.

请保持回答简洁, 默认使用中文. 在调用子智能体前先说明你的调度理由, 结果整合后返回给用户.
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
