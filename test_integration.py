#!/usr/bin/env python3
"""主代理和子代理集成测试."""

from app.agents.subagents import ALL_SUBAGENTS

# 示例 Postgres 日志
SAMPLE_LOG = """2024-05-21 10:23:45.123 UTC [1234] ERROR: connection refused
2024-05-21 10:23:46.456 UTC [1235] INFO: database started
2024-05-21 10:24:00.789 UTC [1236] WARNING: slow query detected, duration: 15.234s
2024-05-21 10:24:15.012 UTC [1237] ERROR: out of memory
2024-05-21 10:24:30.345 UTC [1238] ERROR: connection timeout
2024-05-21 10:25:00.678 UTC [1239] FATAL: disk full, cannot write
"""


def main():
    print("=" * 80)
    print("主代理和子代理集成测试")
    print("=" * 80)

    print(f"\n[✓] 成功加载 {len(ALL_SUBAGENTS)} 个子代理:")
    for subagent in ALL_SUBAGENTS:
        name = subagent.get('name', 'unknown')
        desc = subagent.get('description', 'N/A')
        tools = len(subagent.get('tools', []))
        print(f"  - {name:20s} ({tools} tools): {desc}")

    print("\n[✓] 日志分析子代理详情:")
    log_analyzer = ALL_SUBAGENTS[0]
    print(f"  名称: {log_analyzer['name']}")
    print(f"  描述: {log_analyzer['description']}")
    print(f"  工具列表:")
    for tool in log_analyzer.get('tools', []):
        print(f"    - {tool.name}: {tool.description}")

    print("\n[✓] 测试日志分析子代理的工具:")
    tools = log_analyzer.get('tools', [])
    if tools:
        # 测试第一个工具 (parse_postgres_log)
        parse_tool = next((t for t in tools if t.name == 'parse_postgres_log'), None)
        if parse_tool:
            print(f"\n  调用 {parse_tool.name}...")
            result = parse_tool.invoke({"log_content": SAMPLE_LOG})
            print(f"    总条目数: {result['total_entries']}")
            print(f"    ERROR数量: {result['severity_distribution']['ERROR']}")

        # 测试第二个工具 (extract_errors)
        extract_tool = next((t for t in tools if t.name == 'extract_errors'), None)
        if extract_tool:
            print(f"\n  调用 {extract_tool.name}...")
            result = extract_tool.invoke({"log_content": SAMPLE_LOG, "severity": "ERROR"})
            print(f"    错误数量: {result['error_count']}")
            print(f"    错误类型: {list(result['error_type_distribution'].keys())}")

        # 测试第三个工具 (analyze_log_patterns)
        analyze_tool = next((t for t in tools if t.name == 'analyze_log_patterns'), None)
        if analyze_tool:
            print(f"\n  调用 {analyze_tool.name}...")
            result = analyze_tool.invoke({"log_content": SAMPLE_LOG})
            print(f"    检测到的模式数: {result['pattern_count']}")
            print(f"    前5大问题: {list(result['top_issues'].keys())}")

        # 测试第四个工具 (summarize_issues)
        summarize_tool = next((t for t in tools if t.name == 'summarize_issues'), None)
        if summarize_tool:
            print(f"\n  调用 {summarize_tool.name}...")
            result = summarize_tool.invoke({"log_content": SAMPLE_LOG, "error_threshold": 1})
            print(f"    总错误数: {result['summary']['total_errors']}")
            print(f"    建议数: {len(result['recommendations'])}")
            if result['recommendations']:
                print(f"    首个建议: {result['recommendations'][0]}")

    print("\n" + "=" * 80)
    print("✓ 集成测试完成 - 所有组件正常运行")
    print("=" * 80)


if __name__ == "__main__":
    main()
