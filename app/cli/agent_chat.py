"""RCA分析交互式CLI.

提供REPL和一次性输入模式用于与主代理交互。
"""

from __future__ import annotations

import uuid
from typing import Optional

from app.agents.main_agent import build_main_agent


def repl(session_id: Optional[str] = None, debug: bool = False) -> None:
    """交互式REPL模式.

    Args:
        session_id: 会话ID，如果为None则生成新的
        debug: 是否显示调试信息
    """
    session_id = session_id or uuid.uuid4().hex[:8]
    print(f"\n{'='*80}")
    print(f"Postgres RCA 分析系统 - 交互模式")
    print(f"{'='*80}")
    print(f"会话ID: {session_id}")
    print(f"输入 'help' 查看帮助，输入 'quit' 或 'exit' 退出\n")

    agent = build_main_agent(session_id)

    while True:
        try:
            user_input = input("RCA> ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit']:
                print("\n感谢使用RCA分析系统，再见！")
                break

            if user_input.lower() == 'help':
                print_help()
                continue

            # 调用主代理
            print("\n分析中...\n")

            result = agent.invoke(
                {"messages": [{"role": "user", "content": user_input}]},
                {"configurable": {"thread_id": session_id, "debug": debug}}
            )

            # 显示结果
            if result and 'messages' in result and result['messages']:
                last_message = result['messages'][-1]
                if hasattr(last_message, 'content'):
                    print(f"\n{'─'*80}")
                    print(last_message.content)
                    print(f"{'─'*80}\n")

        except KeyboardInterrupt:
            print("\n\n中断了分析，输入 'quit' 退出或继续输入新命令\n")
        except Exception as e:
            print(f"\n错误: {str(e)}\n")
            if debug:
                import traceback
                traceback.print_exc()


def run_once(
    session_id: Optional[str] = None,
    debug: bool = False,
    user_input: str = ""
) -> None:
    """一次性输入模式（非交互）.

    Args:
        session_id: 会话ID，如果为None则生成新的
        debug: 是否显示调试信息
        user_input: 用户输入的命令
    """
    session_id = session_id or uuid.uuid4().hex[:8]

    print(f"\n{'='*80}")
    print(f"Postgres RCA 分析系统 - 单次分析")
    print(f"{'='*80}")
    print(f"会话ID: {session_id}\n")

    if not user_input:
        print("错误: 未指定输入内容")
        return

    print(f"输入: {user_input}\n")
    print("分析中...\n")

    agent = build_main_agent(session_id)

    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]},
            {"configurable": {"thread_id": session_id, "debug": debug}}
        )

        if result and 'messages' in result and result['messages']:
            last_message = result['messages'][-1]
            if hasattr(last_message, 'content'):
                print(f"\n{'─'*80}")
                print(last_message.content)
                print(f"{'─'*80}\n")

    except Exception as e:
        print(f"\n错误: {str(e)}\n")
        if debug:
            import traceback
            traceback.print_exc()


def print_help() -> None:
    """打印帮助信息."""
    help_text = """
RCA分析系统 - 使用帮助
══════════════════════════════════════════════════════════════════════════════

支持的命令:

1. 日志分析
   示例: "分析这个Postgres日志: [日志内容]"

2. 查询性能分析
   示例: "分析这个查询: SELECT * FROM users WHERE id = 1"

3. 性能指标分析
   示例: "分析数据库指标，缓存命中率90%，连接数50"

4. 生成RCA报告
   示例: "生成完整的RCA分析报告"

5. 系统命令
   help    - 显示此帮助信息
   quit    - 退出应用
   exit    - 退出应用

用法示例
──────────────────────────────────────────────────────────────────────────────

场景1: 分析错误日志
  RCA> 这是我的Postgres日志：2024-05-21 10:23:45 ERROR: connection refused

场景2: 分析慢查询
  RCA> 分析这个查询的性能：SELECT * FROM orders WHERE customer_id NOT IN (...)

场景3: 系统诊断
  RCA> 我们的缓存命中率是85%，连接数占用65%，有什么建议吗？

提示:
  - 提供尽可能多的上下文信息（日志、查询、性能指标）
  - 系统会根据内容自动选择合适的分析方式
  - 每个会话独立，会话结束时分析结果保留在内存中

更多信息请访问: app/agents/subagents/README.md
══════════════════════════════════════════════════════════════════════════════
    """
    print(help_text)
