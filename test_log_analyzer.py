#!/usr/bin/env python3
"""日志分析子代理测试脚本."""

from app.agents.subagents.log_analyzer import (
    parse_postgres_log,
    extract_errors,
    analyze_log_patterns,
    summarize_issues,
)

# 示例 Postgres 日志
SAMPLE_LOG = """2024-05-21 10:23:45.123 UTC [1234] ERROR: connection refused
2024-05-21 10:23:46.456 UTC [1235] INFO: database started
2024-05-21 10:24:00.789 UTC [1236] WARNING: slow query detected, duration: 15.234s
2024-05-21 10:24:15.012 UTC [1237] ERROR: out of memory
2024-05-21 10:24:30.345 UTC [1238] ERROR: connection timeout
2024-05-21 10:25:00.678 UTC [1239] FATAL: disk full, cannot write
2024-05-21 10:25:30.901 UTC [1240] ERROR: authentication failed for user 'admin'
2024-05-21 10:26:00.234 UTC [1241] ERROR: deadlock detected
2024-05-21 10:26:30.567 UTC [1242] ERROR: connection refused
2024-05-21 10:27:00.890 UTC [1243] WARNING: checkpoint starting
2024-05-21 10:27:30.123 UTC [1244] ERROR: permission denied for schema public
"""


def main():
    print("=" * 80)
    print("Postgres 日志分析子代理测试")
    print("=" * 80)

    # 1. 解析日志
    print("\n[1] 解析日志内容...")
    parsed = parse_postgres_log.invoke({"log_content": SAMPLE_LOG})
    print(f"  总条目数: {parsed['total_entries']}")
    print(f"  时间范围: {parsed['time_range']}")
    print(f"  严重级别分布: {parsed['severity_distribution']}")

    # 2. 提取错误
    print("\n[2] 提取ERROR级别错误...")
    errors = extract_errors.invoke({"log_content": SAMPLE_LOG, "severity": "ERROR"})
    print(f"  错误数量: {errors['error_count']}")
    print(f"  错误类型分布: {errors['error_type_distribution']}")
    print(f"  样本错误数: {len(errors['sample_errors'])}")

    # 3. 分析模式
    print("\n[3] 分析日志模式...")
    patterns = analyze_log_patterns.invoke({"log_content": SAMPLE_LOG})
    print(f"  检测到的模式: {patterns['detected_patterns']}")
    print(f"  前5大问题: {patterns['top_issues']}")

    # 4. 问题汇总
    print("\n[4] 汇总关键问题和建议...")
    summary = summarize_issues.invoke(
        {"log_content": SAMPLE_LOG, "error_threshold": 2}
    )
    print(f"  汇总:")
    for key, value in summary['summary'].items():
        print(f"    - {key}: {value}")

    print(f"\n  识别的问题:")
    for issue in summary['identified_issues']:
        print(f"    - {issue['type']}: {issue['occurrences']} 次 ({issue['severity']})")

    print(f"\n  建议:")
    for rec in summary['recommendations']:
        print(f"    - {rec['issue']}: {rec['action']}")

    print("\n" + "=" * 80)
    print("✓ 日志分析子代理测试完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
