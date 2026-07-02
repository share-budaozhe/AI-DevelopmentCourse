"""
AutoGPT Demo 统一配置模块
布道者

集中管理所有 Agent 配置：LLM 参数、Prompt 模板、工具开关、记忆策略。
"""
import os
from dataclasses import dataclass, field
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()


# ═══════════════════════════════════════════════════════════════
# Agent 核心配置
# ═══════════════════════════════════════════════════════════════

@dataclass
class AgentConfig:
    """
    AutoGPT Agent 配置

    布道者:
        每个配置项都经过精心设计，以确保 Agent 在自主性与安全性之间取得平衡。
        max_iterations 控制单次任务的最大循环次数，
        temperature 控制 LLM 输出的确定性程度。
    """
    name: str = "AutoGPT-Demo"
    description: str = "一个自主 AI Agent，能够分解复杂任务并逐步执行"
    max_iterations: int = 10        # 单次任务最大循环次数
    max_tokens: int = 4096          # 每次 LLM 调用的最大 Token 数
    temperature: float = 0.5        # LLM 温度（0=确定, 1=随机）
    model: str = "gpt-4o"           # LLM 模型名

    # 工具开关
    allow_search: bool = True       # 网络搜索
    allow_file_ops: bool = True     # 文件读写
    allow_code_execution: bool = True  # 代码执行
    allow_web_browse: bool = True   # 网页浏览

    # 记忆配置
    memory_backend: str = "local"   # local / chroma
    chroma_persist_dir: str = "./workspace/chroma_db"
    short_term_memory_size: int = 20  # 保留最近 N 轮对话

    # 工作目录
    workspace_dir: str = "./workspace"


def get_config() -> AgentConfig:
    """从环境变量加载配置, 布道者推荐使用环境变量管理敏感信息"""
    return AgentConfig(
        name=os.getenv("AGENT_NAME", "AutoGPT-Demo"),
        max_iterations=int(os.getenv("AGENT_MAX_ITERATIONS", "10")),
        max_tokens=int(os.getenv("AGENT_MAX_TOKENS", "4096")),
        temperature=float(os.getenv("AGENT_TEMPERATURE", "0.5")),
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        allow_code_execution=os.getenv("AGENT_ALLOW_CODE_EXECUTION", "true").lower() == "true",
        allow_file_ops=os.getenv("AGENT_ALLOW_FILE_OPERATIONS", "true").lower() == "true",
        chroma_persist_dir=os.getenv("CHROMA_PERSIST_DIR", "./workspace/chroma_db"),
        workspace_dir=os.getenv("WORKSPACE_DIR", "./workspace"),
    )


# ═══════════════════════════════════════════════════════════════
# Prompt 模板 —— Agent 自主推理的核心引擎
# 布道者: 以下 Prompt 参考了 AutoGPT 原版设计，经过中文化适配
# ═══════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """你是一个名为 {name} 的自主 AI Agent。

## 你的身份
{description}

## 核心能力
1. **任务分解**：将复杂目标拆解为可执行的子任务
2. **工具使用**：你可以调用以下工具来完成任务:
   {tools_description}
3. **自我评估**：每次行动后评估结果，判断是否需要调整计划

## 行为规范
- 始终以目标为导向，避免偏离主题
- 遇到错误时，尝试分析原因并寻找替代方案
- 优先使用工具获取信息，而非依赖知识猜测
- 对于不确定的信息，应搜索验证
- 完成任务后使用 finish 命令提交最终成果

## 当前上下文
- 工作目录: {workspace_dir}
- 当前时间: {current_time}

## 输出格式要求
每次行动必须输出以下格式：

THOUGHT: <你对当前情况的思考和分析>
ACTION: <要执行的命令名>
ARGUMENTS: <命令参数，JSON 格式>

可用的命令:
{commands_description}

重要: 请始终保持中文输出，执行精确，不要编造结果。
"""

NEXT_ACTION_PROMPT = """## 你的目标
{goal}

## 当前进度
已完成步骤 ({completed_count}/{total_count}):
{completed_steps}

## 上一步结果
行动: {last_action}
思考: {last_thought}
结果: {last_result}

## 下一步
分析当前状态，决定下一步行动。使用标准格式输出。
"""

SUMMARY_PROMPT = """## 任务总结

请用中文总结以下任务的执行过程：

### 原始目标
{goal}

### 执行记录
{execution_log}

### 总结要求
1. 概括任务完成情况
2. 列出关键发现或产出
3. 指出遇到的问题及解决方案
4. 评估成果质量

请输出一个结构化的总结报告。
"""
