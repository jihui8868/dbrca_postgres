"""子代理注册和聚合模块.

所有子代理在此聚合，作为一个统一的列表供主代理使用。
"""

from __future__ import annotations

from app.agents.subagents.log_analyzer import log_analyzer_agent
from app.agents.subagents.query_analyzer import query_analyzer_agent
from app.agents.subagents.metrics_analyzer import metrics_analyzer_agent
from app.agents.subagents.report_gen import report_gen_agent

# 所有子代理列表 - 供 create_deep_agent() 使用
ALL_SUBAGENTS = [
    log_analyzer_agent,
    query_analyzer_agent,
    metrics_analyzer_agent,
    report_gen_agent,
]

__all__ = [
    "ALL_SUBAGENTS",
    "log_analyzer_agent",
    "query_analyzer_agent",
    "metrics_analyzer_agent",
    "report_gen_agent",
]
