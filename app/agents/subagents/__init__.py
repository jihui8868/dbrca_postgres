"""子代理注册和聚合模块.

所有子代理在此聚合，作为一个统一的列表供主代理使用。
"""

from __future__ import annotations

from app.agents.subagents.log_analyzer import log_analyzer_agent

# 所有子代理列表 - 供 create_deep_agent() 使用
ALL_SUBAGENTS = [
    log_analyzer_agent,
    # 后续可在此添加更多子代理:
    # - data_parse_agent: 数据解析和参数收集
    # - data_explain_agent: 地震图像解释
    # - data_validate_agent: 数据验证和质检
    # - report_gen_agent: 报告生成
]

__all__ = [
    "ALL_SUBAGENTS",
    "log_analyzer_agent",
]
