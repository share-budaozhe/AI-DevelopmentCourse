"""
工具基类与注册中心
布道者

所有工具必须继承 BaseTool 并实现 execute() 方法。
ToolRegistry 提供统一的工具注册、发现和调用机制。
"""
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Type, Optional, List


class BaseTool(ABC):
    """
    工具基类

    布道者:
        每个工具包含三个核心属性:
        - name: 命令名（LLM 据此识别要调用哪个工具）
        - description: 功能描述（告诉 LLM 何时使用）
        - parameters: 参数 Schema（定义输入格式）

        execute() 方法返回统一的 ToolResult。
    """

    name: str = ""
    description: str = ""
    parameters: Dict[str, Any] = {}

    @abstractmethod
    def execute(self, **kwargs) -> 'ToolResult':
        """执行工具逻辑"""
        ...

    def to_schema(self) -> Dict[str, Any]:
        """导出 JSON Schema 供 LLM 理解工具能力"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }

    def format_result(self, success: bool, content: str, metadata: Dict = None) -> 'ToolResult':
        return ToolResult(
            tool_name=self.name,
            success=success,
            content=content,
            metadata=metadata or {},
        )


class ToolResult:
    """统一的工具执行结果"""
    def __init__(self, tool_name: str, success: bool, content: str, metadata: Dict = None):
        self.tool_name = tool_name
        self.success = success
        self.content = content
        self.metadata = metadata or {}

    def __str__(self) -> str:
        status = "成功" if self.success else "失败"
        return f"[{self.tool_name}] {status}: {self.content[:200]}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool": self.tool_name,
            "success": self.success,
            "content": self.content,
            "metadata": self.metadata,
        }


class ToolRegistry:
    """
    工具注册中心

    布道者:
        统一的工具管理模式。
        LLM 通过 get_commands_description() 了解可用命令，
        通过 execute(tool_name, params) 调用具体工具。
    """

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """注册一个工具"""
        if tool.name in self._tools:
            raise ValueError(f"工具 '{tool.name}' 已存在")
        self._tools[tool.name] = tool

    def register_all(self, tools: List[BaseTool]) -> None:
        """批量注册工具"""
        for tool in tools:
            self.register(tool)

    def get(self, name: str) -> Optional[BaseTool]:
        """获取指定工具"""
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        """列出所有已注册工具"""
        return list(self._tools.values())

    def get_tools_description(self) -> str:
        """生成工具能力描述（注入到 System Prompt）"""
        lines = []
        for tool in self._tools.values():
            params_desc = json.dumps(tool.parameters, ensure_ascii=False, indent=2)
            lines.append(f"- {tool.name}: {tool.description}\n  参数: {params_desc}")
        return "\n".join(lines)

    def get_commands_description(self) -> str:
        """生成命令列表描述（注入到 System Prompt）"""
        lines = []
        for tool in self._tools.values():
            lines.append(f"  {tool.name}: {tool.description}")
        return "\n".join(lines)

    def execute(self, tool_name: str, **params) -> ToolResult:
        """
        执行指定工具

        布道者:
            统一的调用入口，包含错误处理。
            LLM 只需输出 tool_name + params，Registry 负责分发。
        """
        if tool_name == "finish":
            return ToolResult("finish", True, params.get("summary", "任务完成"))

        tool = self._tools.get(tool_name)
        if not tool:
            return ToolResult(tool_name, False,
                              f"未知工具: {tool_name}。可用工具: {list(self._tools.keys())}")

        try:
            return tool.execute(**params)
        except Exception as e:
            return ToolResult(tool_name, False, f"工具执行异常: {type(e).__name__}: {e}")
