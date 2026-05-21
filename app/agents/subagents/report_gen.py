"""Postgres根因分析报告生成子代理.

负责整合分析结果，生成完整的RCA报告。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from deepagents import SubAgent
from langchain_core.tools import tool


# ============================================================================
# 报告生成工具
# ============================================================================


@tool
def format_markdown_report(
    title: str,
    summary: str,
    issues: list[dict[str, Any]] | None = None,
    recommendations: list[dict[str, Any]] | None = None,
    metrics: dict[str, Any] | None = None
) -> str:
    """生成Markdown格式的RCA报告.

    Args:
        title: 报告标题
        summary: 问题摘要
        issues: 识别的问题列表
        recommendations: 优化建议列表
        metrics: 性能指标

    Returns:
        Markdown格式的报告
    """
    report = []
    report.append(f"# {title}\n")
    report.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 摘要部分
    report.append("## 摘要\n")
    report.append(f"{summary}\n")

    # 问题部分
    if issues:
        report.append("## 识别的问题\n")
        for i, issue in enumerate(issues, 1):
            severity = issue.get('severity', 'UNKNOWN')
            desc = issue.get('description', 'N/A')
            report.append(f"### {i}. {issue.get('type', 'Unknown')} [{severity}]\n")
            report.append(f"{desc}\n")

    # 指标部分
    if metrics:
        report.append("## 性能指标\n")
        report.append("| 指标 | 值 | 状态 |\n")
        report.append("|------|-----|------|\n")
        for key, value in metrics.items():
            status = "✓" if isinstance(value, bool) and value else "✗" if isinstance(value, bool) else "●"
            if isinstance(value, dict):
                for sub_key, sub_val in value.items():
                    report.append(f"| {key}.{sub_key} | {sub_val} | {status} |\n")
            else:
                report.append(f"| {key} | {value} | {status} |\n")

    # 建议部分
    if recommendations:
        report.append("## 优化建议\n")
        for i, rec in enumerate(recommendations, 1):
            priority = rec.get('priority', 'MEDIUM')
            optimization = rec.get('optimization', 'N/A')
            reason = rec.get('reason', '')
            report.append(f"### {i}. {optimization} [{priority}]\n")
            report.append(f"**原因**: {reason}\n\n")
            if 'example' in rec:
                report.append(f"**示例**:\n```sql\n{rec['example']}\n```\n")

    return '\n'.join(report)


@tool
def format_html_report(
    title: str,
    summary: str,
    issues: list[dict[str, Any]] | None = None,
    recommendations: list[dict[str, Any]] | None = None
) -> str:
    """生成HTML格式的RCA报告.

    Args:
        title: 报告标题
        summary: 问题摘要
        issues: 识别的问题列表
        recommendations: 优化建议列表

    Returns:
        HTML格式的报告
    """
    html = []
    html.append("<!DOCTYPE html>")
    html.append("<html>")
    html.append("<head>")
    html.append("<meta charset='utf-8'>")
    html.append(f"<title>{title}</title>")
    html.append("<style>")
    html.append("""
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1000px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; }
        h1 { color: #333; border-bottom: 2px solid #0066cc; padding-bottom: 10px; }
        h2 { color: #0066cc; margin-top: 30px; }
        .summary { background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .issue { border-left: 4px solid #ff9800; padding: 10px; margin: 10px 0; background-color: #fff3e0; }
        .issue.HIGH { border-left-color: #f44336; background-color: #ffebee; }
        .recommendation { background-color: #f1f8e9; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .code { background-color: #f5f5f5; padding: 10px; border-radius: 3px; font-family: 'Courier New'; overflow-x: auto; }
        .timestamp { color: #999; font-size: 0.9em; }
    """)
    html.append("</style>")
    html.append("</head>")
    html.append("<body>")
    html.append("<div class='container'>")

    # 标题和时间
    html.append(f"<h1>{title}</h1>")
    html.append(f"<p class='timestamp'>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")

    # 摘要
    html.append("<div class='summary'>")
    html.append(f"<h2>摘要</h2>")
    html.append(f"<p>{summary}</p>")
    html.append("</div>")

    # 问题
    if issues:
        html.append("<h2>识别的问题</h2>")
        for issue in issues:
            severity = issue.get('severity', 'UNKNOWN')
            html.append(f"<div class='issue {severity}'>")
            html.append(f"<strong>{issue.get('type', 'Unknown')} [{severity}]</strong>")
            html.append(f"<p>{issue.get('description', 'N/A')}</p>")
            html.append("</div>")

    # 建议
    if recommendations:
        html.append("<h2>优化建议</h2>")
        for rec in recommendations:
            html.append("<div class='recommendation'>")
            html.append(f"<h3>{rec.get('optimization', 'N/A')} [{rec.get('priority', 'MEDIUM')}]</h3>")
            html.append(f"<p><strong>原因</strong>: {rec.get('reason', '')}</p>")
            if 'example' in rec:
                html.append(f"<p><strong>示例</strong>:</p>")
                html.append(f"<div class='code'>{rec['example']}</div>")
            html.append("</div>")

    html.append("</div>")
    html.append("</body>")
    html.append("</html>")

    return '\n'.join(html)


@tool
def create_action_plan(
    issues: list[dict[str, Any]],
    recommendations: list[dict[str, Any]]
) -> dict[str, Any]:
    """根据问题和建议生成行动计划.

    Args:
        issues: 识别的问题列表
        recommendations: 优化建议列表

    Returns:
        包含分阶段行动计划的字典
    """
    # 按优先级排序
    high_priority = [rec for rec in recommendations if rec.get('priority') == 'HIGH']
    medium_priority = [rec for rec in recommendations if rec.get('priority') == 'MEDIUM']
    low_priority = [rec for rec in recommendations if rec.get('priority') == 'LOW']

    action_plan = {
        'phase_1_urgent': {
            'phase': '紧急修复（立即执行）',
            'duration': '1-2小时',
            'actions': [
                {
                    'action': rec.get('optimization'),
                    'reason': rec.get('reason'),
                    'steps': [
                        '备份当前配置',
                        rec.get('example', '执行优化'),
                        '监控性能变化',
                        '确认改进效果'
                    ]
                }
                for rec in high_priority[:2]
            ]
        },
        'phase_2_short_term': {
            'phase': '短期优化（本周内）',
            'duration': '2-3天',
            'actions': [
                {
                    'action': rec.get('optimization'),
                    'reason': rec.get('reason'),
                    'steps': [
                        '分析影响范围',
                        '制定执行计划',
                        rec.get('example', '执行优化'),
                        '测试和验证'
                    ]
                }
                for rec in medium_priority[:3]
            ]
        },
        'phase_3_long_term': {
            'phase': '长期优化（1个月内）',
            'duration': '持续',
            'actions': [
                {
                    'action': rec.get('optimization'),
                    'reason': rec.get('reason'),
                    'steps': [
                        '进行详细分析',
                        '与开发团队讨论',
                        '制定实施计划',
                        '持续监控效果'
                    ]
                }
                for rec in low_priority[:2]
            ]
        },
        'monitoring': {
            'phase': '持续监控',
            'metrics_to_watch': [
                '缓存命中率 (应 > 95%)',
                '连接数利用率 (应 < 60%)',
                '顺序扫描比例 (应 < 30%)',
                '锁等待时间 (应尽可能短)',
                '查询执行时间'
            ],
            'check_frequency': '每小时',
            'alert_thresholds': {
                'slow_query_ms': 1000,
                'cache_hit_ratio_percent': 90,
                'connection_utilization_percent': 80
            }
        }
    }

    return action_plan


@tool
def summarize_findings(
    log_findings: dict[str, Any] | None = None,
    query_findings: dict[str, Any] | None = None,
    metrics_findings: dict[str, Any] | None = None
) -> dict[str, Any]:
    """汇总所有分析结果.

    Args:
        log_findings: 日志分析结果
        query_findings: 查询分析结果
        metrics_findings: 指标分析结果

    Returns:
        综合分析结果
    """
    root_causes = []
    severity_levels = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}

    # 从日志中提取根因
    if log_findings:
        if isinstance(log_findings, dict) and 'identified_issues' in log_findings:
            for issue in log_findings.get('identified_issues', []):
                root_causes.append({
                    'source': '日志分析',
                    'type': issue.get('type'),
                    'severity': issue.get('severity'),
                    'occurrences': issue.get('occurrences')
                })
                severity_levels[issue.get('severity', 'LOW')] += 1

    # 从查询分析中提取根因
    if query_findings:
        if isinstance(query_findings, dict) and 'issues' in query_findings:
            for issue in query_findings.get('issues', []):
                root_causes.append({
                    'source': '查询分析',
                    'type': issue.get('type'),
                    'severity': issue.get('severity')
                })
                severity_levels[issue.get('severity', 'LOW')] += 1

    # 从指标分析中提取根因
    if metrics_findings:
        if isinstance(metrics_findings, dict) and 'issues' in metrics_findings:
            for issue in metrics_findings.get('issues', []):
                root_causes.append({
                    'source': '指标分析',
                    'issue': issue
                })

    # 生成摘要
    summary = f"发现 {len(root_causes)} 个潜在问题：" + \
              f"严重 {severity_levels['HIGH']} 个，" + \
              f"中等 {severity_levels['MEDIUM']} 个，" + \
              f"轻微 {severity_levels['LOW']} 个"

    return {
        'root_causes': root_causes,
        'severity_summary': severity_levels,
        'total_issues': len(root_causes),
        'summary': summary,
        'impact_assessment': {
            'database_availability': '可能受影响' if severity_levels['HIGH'] > 0 else '正常',
            'query_performance': '严重受影响' if severity_levels['HIGH'] > 2 else '中等影响' if severity_levels['MEDIUM'] > 0 else '正常',
            'user_experience': '受影响' if severity_levels['HIGH'] > 0 or severity_levels['MEDIUM'] > 2 else '正常'
        }
    }


# ============================================================================
# 子代理定义
# ============================================================================


def create_report_gen_agent() -> SubAgent:
    """创建报告生成子代理.

    Returns:
        配置好的SubAgent实例
    """
    return SubAgent(
        name="report_gen",
        description="整合分析结果，生成RCA报告和行动计划",
        system_prompt="""你是一个Postgres根因分析报告专家。你的任务是：
1. 接收来自其他子代理的分析结果（日志、查询、指标）
2. 整合这些结果生成综合RCA报告
3. 创建优先级明确的行动计划
4. 生成易于理解的报告（Markdown/HTML）

报告应该包含：
- 问题摘要和影响评估
- 识别的根本原因
- 按优先级排列的优化建议
- 分阶段的行动计划
- 监控和验证方案

报告风格：
- 清晰易读
- 包含具体数据和证据
- 提供实施步骤
- 预期改进效果

目标是帮助DBA和开发人员快速理解问题和解决方案。""",
        tools=[
            summarize_findings,
            format_markdown_report,
            format_html_report,
            create_action_plan,
        ]
    )


# 导出子代理实例供 __init__.py 使用
report_gen_agent = create_report_gen_agent()
