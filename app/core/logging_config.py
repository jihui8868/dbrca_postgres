"""日志系统初始化.

调用 setup_logging() 一次即可完成全局配置:
- 控制台: 彩色, INFO 及以上
- 文件:   logs/app_YYYY-MM-DD.log, 每天轮转, 保留 30 天, DEBUG 及以上
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import sys
from pathlib import Path


# ANSI 颜色码
_COLORS = {
    "DEBUG":    "\033[36m",   # cyan
    "INFO":     "\033[32m",   # green
    "WARNING":  "\033[33m",   # yellow
    "ERROR":    "\033[31m",   # red
    "CRITICAL": "\033[35m",   # magenta
    "RESET":    "\033[0m",
}


class _ColorFormatter(logging.Formatter):
    """控制台彩色格式化器."""

    _FMT = "%(asctime)s %(levelcolor)s%(levelname)-8s%(reset)s %(name)-24s %(message)s"

    def format(self, record: logging.LogRecord) -> str:
        record.levelcolor = _COLORS.get(record.levelname, "")
        record.reset = _COLORS["RESET"]
        formatter = logging.Formatter(self._FMT, datefmt="%H:%M:%S")
        return formatter.format(record)


class _PlainFormatter(logging.Formatter):
    """文件纯文本格式化器."""

    _FMT = "%(asctime)s  %(levelname)-8s  %(name)-24s  %(message)s"

    def __init__(self) -> None:
        super().__init__(self._FMT, datefmt="%Y-%m-%d %H:%M:%S")


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    app_name: str = "earthquake",
) -> None:
    """配置全局日志. 幂等 —— 重复调用不会追加重复 handler."""

    root = logging.getLogger()
    if root.handlers:
        return  # 已初始化

    level = getattr(logging, log_level.upper(), logging.INFO)
    root.setLevel(logging.DEBUG)  # root 放到最低, 由 handler 控制实际输出级别

    # ── 控制台 handler ────────────────────────────────────────────────────────
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(_ColorFormatter())
    root.addHandler(console)

    # ── 文件 handler (按天轮转) ───────────────────────────────────────────────
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_path / f"{app_name}.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(_PlainFormatter())
    file_handler.suffix = "%Y-%m-%d"
    root.addHandler(file_handler)

    # 静默过于啰嗦的三方库
    for noisy in ("httpx", "httpcore", "urllib3", "pymilvus", "openai"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
