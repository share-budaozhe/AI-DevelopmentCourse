// ============================================================
// MCP Demo - 公共类型与协议常量
// ============================================================
// 说明：
//   MCP协议基于 JSON-RPC 2.0，所有消息都遵循此格式。
//   本文件定义了三种传输模式共享的类型和协议常量。

// ---------- JSON-RPC 2.0 基础消息 ----------

/** JSON-RPC 2.0 请求消息 */
export interface JsonRpcRequest {
  jsonrpc: "2.0";
  id: number | string;
  method: string;
  params?: Record<string, unknown>;
}

/** JSON-RPC 2.0 通知消息（无id，无需响应） */
export interface JsonRpcNotification {
  jsonrpc: "2.0";
  method: string;
  params?: Record<string, unknown>;
}

/** JSON-RPC 2.0 成功响应 */
export interface JsonRpcSuccessResponse {
  jsonrpc: "2.0";
  id: number | string;
  result: unknown;
}

/** JSON-RPC 2.0 错误响应 */
export interface JsonRpcErrorResponse {
  jsonrpc: "2.0";
  id: number | string;
  error: {
    code: number;
    message: string;
    data?: unknown;
  };
}

/** JSON-RPC 2.0 消息联合类型 */
export type JsonRpcMessage =
  | JsonRpcRequest
  | JsonRpcNotification
  | JsonRpcSuccessResponse
  | JsonRpcErrorResponse;

// ---------- MCP 协议常量 ----------

/** MCP 协议版本 */
export const MCP_PROTOCOL_VERSION = "2024-11-05";

/** MCP 预定义方法名 */
export const MCP_METHODS = {
  // 生命周期
  INITIALIZE: "initialize",
  INITIALIZED: "notifications/initialized",
  PING: "ping",

  // 工具
  TOOLS_LIST: "tools/list",
  TOOLS_CALL: "tools/call",

  // 资源
  RESOURCES_LIST: "resources/list",
  RESOURCES_READ: "resources/read",

  // 提示
  PROMPTS_LIST: "prompts/list",
  PROMPTS_GET: "prompts/get",
} as const;
