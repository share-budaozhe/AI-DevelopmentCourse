# ============================================================
# MCP Demo - 公共类型与协议常量
# ============================================================
# 说明：
#   MCP协议基于 JSON-RPC 2.0，所有消息都遵循此格式。
#   本文件定义了三种传输模式共享的类型和协议常量。

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ---------- JSON-RPC 2.0 基础消息 ----------

@dataclass
class JsonRpcRequest:
    """JSON-RPC 2.0 请求消息"""
    jsonrpc: str = "2.0"
    id: int | str | None = None
    method: str = ""
    params: dict[str, Any] | None = None


@dataclass
class JsonRpcNotification:
    """JSON-RPC 2.0 通知消息（无id，无需响应）"""
    jsonrpc: str = "2.0"
    method: str = ""
    params: dict[str, Any] | None = None


@dataclass
class JsonRpcSuccessResponse:
    """JSON-RPC 2.0 成功响应"""
    jsonrpc: str = "2.0"
    id: int | str | None = None
    result: Any = None


@dataclass
class JsonRpcErrorResponse:
    """JSON-RPC 2.0 错误响应"""
    jsonrpc: str = "2.0"
    id: int | str | None = None
    error: dict[str, Any] = field(default_factory=dict)


# ---------- MCP 协议常量 ----------

MCP_PROTOCOL_VERSION = "2024-11-05"


class MCP_METHODS:
    """MCP 预定义方法名"""
    # 生命周期
    INITIALIZE = "initialize"
    INITIALIZED = "notifications/initialized"
    PING = "ping"

    # 工具
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"

    # 资源
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"

    # 提示
    PROMPTS_LIST = "prompts/list"
    PROMPTS_GET = "prompts/get"
