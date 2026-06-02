# ============================================================
# MCP Demo - 共享工具定义
# ============================================================
# 说明：
#   本文档定义了所有传输模式公用的 MCP 工具。
#   每个工具包含 name, description, inputSchema 三要素，
#   以及对应的 handler 实现函数。

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import mcp.types as types

# ---------- 工具定义 ----------

DEMO_TOOLS = [
    types.Tool(
        name="add",
        description="两个数相加 —— 演示基本的工具调用",
        inputSchema={
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "第一个加数"},
                "b": {"type": "number", "description": "第二个加数"},
            },
            "required": ["a", "b"],
        },
    ),
    types.Tool(
        name="greet",
        description="发送问候 —— 演示字符串参数工具",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "要问候的名字"},
                "language": {
                    "type": "string",
                    "enum": ["zh", "en", "ja"],
                    "description": "语言：zh=中文, en=英文, ja=日文",
                },
            },
            "required": ["name"],
        },
    ),
    types.Tool(
        name="get_time",
        description="获取当前服务器时间 —— 演示无必需参数工具",
        inputSchema={
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "时区，如 Asia/Shanghai, America/New_York，默认 UTC",
                },
            },
        },
    ),
]

# ---------- 工具处理器 ----------

def handle_add(args: dict[str, Any]) -> list[types.TextContent]:
    """加法处理器"""
    a = args.get("a", 0)
    b = args.get("b", 0)
    return [types.TextContent(type="text", text=f"{a} + {b} = {a + b}")]


def handle_greet(args: dict[str, Any]) -> list[types.TextContent]:
    """问候处理器"""
    greetings = {
        "zh": "你好",
        "en": "Hello",
        "ja": "こんにちは",
    }
    language = args.get("language", "zh") or "zh"
    word = greetings.get(language, greetings["zh"])
    name = args.get("name", "")
    return [types.TextContent(type="text", text=f"{word}，{name}！")]


def handle_get_time(args: dict[str, Any]) -> list[types.TextContent]:
    """时间处理器"""
    now = datetime.now(timezone.utc)
    tz = args.get("timezone", "UTC") or "UTC"
    try:
        # 简单格式化（不使用 zoneinfo 以保持兼容性）
        if tz == "UTC":
            formatted = now.strftime("%Y-%m-%d %H:%M:%S UTC")
        else:
            # 简单标记：真实项目应使用 zoneinfo / pytz
            formatted = f"{now.strftime('%Y-%m-%d %H:%M:%S')} ({tz})"
        return [types.TextContent(type="text", text=f"当前时间 ({tz}): {formatted}")]
    except Exception:
        return [
            types.TextContent(
                type="text",
                text=f"无效时区: {tz}。当前 UTC 时间: {now.isoformat()}",
            )
        ]


# ---------- 工具调度器 ----------

def dispatch_tool(name: str, args: dict[str, Any]) -> list[types.TextContent]:
    """根据工具名分发到对应处理器"""
    if name == "add":
        return handle_add(args)
    elif name == "greet":
        return handle_greet(args)
    elif name == "get_time":
        return handle_get_time(args)
    else:
        raise ValueError(f"未知工具: {name}")
