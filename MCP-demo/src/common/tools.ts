// ============================================================
// MCP Demo - 共享工具定义
// ============================================================
// 说明：
//   本文档定义了所有传输模式公用的 MCP 工具。
//   每个工具包含 name, description, inputSchema 三要素，
//   以及对应的 handler 实现函数。

import type { ToolDefinition } from "./types.js";

// ---------- 工具定义 ----------

export interface DemoInput {
  a: number;
  b: number;
}

export const DEMO_TOOLS: ToolDefinition[] = [
  {
    name: "add",
    description: "两个数相加 —— 演示基本的工具调用",
    inputSchema: {
      type: "object",
      properties: {
        a: { type: "number", description: "第一个加数" },
        b: { type: "number", description: "第二个加数" },
      },
      required: ["a", "b"],
    },
  },
  {
    name: "greet",
    description: "发送问候 —— 演示字符串参数工具",
    inputSchema: {
      type: "object",
      properties: {
        name: { type: "string", description: "要问候的名字" },
        language: {
          type: "string",
          enum: ["zh", "en", "ja"],
          description: "语言：zh=中文, en=英文, ja=日文",
        },
      },
      required: ["name"],
    },
  },
  {
    name: "get_time",
    description: "获取当前服务器时间 —— 演示无必需参数工具",
    inputSchema: {
      type: "object",
      properties: {
        timezone: {
          type: "string",
          description: "时区，如 Asia/Shanghai, America/New_York，默认 UTC",
        },
      },
    },
  },
];

// ---------- 工具处理器 ----------

/** 加法处理器 */
export function handleAdd(args: { a: number; b: number }) {
  const { a, b } = args;
  return {
    content: [
      {
        type: "text" as const,
        text: `${a} + ${b} = ${a + b}`,
      },
    ],
  };
}

/** 问候处理器 */
export function handleGreet(args: { name: string; language?: string }) {
  const greetings: Record<string, string> = {
    zh: "你好",
    en: "Hello",
    ja: "こんにちは",
  };
  const word = greetings[args.language ?? "zh"] ?? greetings.zh;
  return {
    content: [
      {
        type: "text" as const,
        text: `${word}，${args.name}！`,
      },
    ],
  };
}

/** 时间处理器 */
export function handleGetTime(args: { timezone?: string }) {
  const now = new Date();
  const tz = args.timezone ?? "UTC";
  try {
    const formatted = now.toLocaleString("zh-CN", { timeZone: tz });
    return {
      content: [
        {
          type: "text" as const,
          text: `当前时间 (${tz}): ${formatted}`,
        },
      ],
    };
  } catch {
    return {
      content: [
        {
          type: "text" as const,
          text: `无效时区: ${tz}。当前 UTC 时间: ${now.toISOString()}`,
        },
      ],
    };
  }
}

// ---------- 工具调度器 ----------

export function dispatchTool(name: string, args: Record<string, unknown>) {
  switch (name) {
    case "add":
      return handleAdd(args as unknown as { a: number; b: number });
    case "greet":
      return handleGreet(args as unknown as { name: string; language?: string });
    case "get_time":
      return handleGetTime(args as unknown as { timezone?: string });
    default:
      throw new Error(`未知工具: ${name}`);
  }
}
