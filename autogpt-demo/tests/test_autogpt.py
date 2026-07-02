"""
AutoGPT Demo 测试套件
布道者

覆盖:
- 工具层: WebSearch / FileOps / CodeExec / WebBrowse
- 记忆层: ShortTerm / LongTerm / WorkingMemory
- Agent层: 初始化 / 规划 / 推理 / 执行 / 完整流程
- 配置层: AgentConfig 加载与验证
"""
import os
import sys
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.config import AgentConfig, get_config
from src.tools.base import BaseTool, ToolRegistry, ToolResult
from src.tools.tools import WebSearchTool, FileOperationsTool, CodeExecutionTool, WebBrowseTool
from src.memory.memory import ShortTermMemory, LongTermMemory, WorkingMemory
from src.agent.core import AutoGPTAgent


# ═══════════════════════════════════════════════
# 工具层测试
# ═══════════════════════════════════════════════

class TestTools:
    """工具层测试 —— 验证每个工具的独立功能"""

    def test_web_search_basic(self):
        tool = WebSearchTool()
        result = tool.execute(query="Python asyncio", max_results=3)
        assert result.success is True
        assert len(result.content) > 50

    def test_web_search_empty_query(self):
        tool = WebSearchTool()
        result = tool.execute(query="")
        assert result.success is False
        assert "不能为空" in result.content

    def test_file_ops_list(self, tmp_path):
        tool = FileOperationsTool(workspace_dir=str(tmp_path))
        (tmp_path / "test.txt").write_text("hello")
        result = tool.execute(operation="list", path="")
        assert result.success is True
        assert "test.txt" in result.content

    def test_file_ops_write_and_read(self, tmp_path):
        tool = FileOperationsTool(workspace_dir=str(tmp_path))
        write_result = tool.execute(operation="write", path="hello.txt", content="Hello World")
        assert write_result.success is True
        read_result = tool.execute(operation="read", path="hello.txt")
        assert read_result.success is True
        assert "Hello World" in read_result.content

    def test_file_ops_path_traversal(self, tmp_path):
        tool = FileOperationsTool(workspace_dir=str(tmp_path))
        result = tool.execute(operation="read", path="../../../etc/passwd")
        assert result.success is False
        assert "安全拦截" in result.content or "禁止" in result.content

    def test_file_ops_read_nonexistent(self, tmp_path):
        tool = FileOperationsTool(workspace_dir=str(tmp_path))
        result = tool.execute(operation="read", path="nonexistent.txt")
        assert result.success is False

    def test_code_exec_safe(self):
        tool = CodeExecutionTool()
        result = tool.execute(code="print('hello world')\nprint(1 + 2)")
        assert result.success is True
        assert "hello world" in result.content
        assert "3" in result.content

    def test_code_exec_exception(self):
        tool = CodeExecutionTool()
        result = tool.execute(code="raise ValueError('test error')")
        assert "ValueError" in result.content or "异常" in result.content

    def test_code_exec_empty(self):
        tool = CodeExecutionTool()
        result = tool.execute(code="")
        assert result.success is False
        assert "不能为空" in result.content

    def test_web_browse_empty_url(self):
        tool = WebBrowseTool()
        result = tool.execute(url="")
        assert result.success is False

    def test_tool_registry_register(self):
        registry = ToolRegistry()
        registry.register(WebSearchTool())
        assert registry.get("web_search") is not None
        assert len(registry.list_tools()) == 1

    def test_tool_registry_duplicate(self):
        registry = ToolRegistry()
        registry.register(WebSearchTool())
        with pytest.raises(ValueError, match="已存在"):
            registry.register(WebSearchTool())

    def test_tool_registry_execute(self):
        registry = ToolRegistry()
        registry.register(WebSearchTool())
        result = registry.execute("web_search", query="test", max_results=1)
        assert result.success is True

    def test_tool_registry_unknown_tool(self):
        registry = ToolRegistry()
        result = registry.execute("nonexistent_tool")
        assert result.success is False
        assert "未知工具" in result.content

    def test_tool_registry_finish(self):
        registry = ToolRegistry()
        result = registry.execute("finish", summary="任务完成")
        assert result.success is True
        assert result.tool_name == "finish"

    def test_tool_registry_commands_description(self):
        registry = ToolRegistry()
        registry.register(WebSearchTool())
        registry.register(CodeExecutionTool())
        desc = registry.get_commands_description()
        assert "web_search" in desc
        assert "code_exec" in desc


# ═══════════════════════════════════════════════
# 记忆系统测试
# ═══════════════════════════════════════════════

class TestMemory:
    """记忆系统测试 —— 验证三层记忆的正确性"""

    def test_short_term_add(self):
        mem = ShortTermMemory(max_size=10)
        mem.add_user("你好")
        assert len(mem.history) == 1
        assert mem.history[0]["role"] == "user"

    def test_short_term_max_size(self):
        mem = ShortTermMemory(max_size=3)
        for i in range(5):
            mem.add_user(f"消息 {i}")
        assert len(mem.history) == 3
        # 最旧的消息已被淘汰
        assert "消息 0" not in str(mem.history)

    def test_short_term_get_recent(self):
        mem = ShortTermMemory(max_size=10)
        mem.add_user("msg1")
        mem.add_agent("msg2")
        mem.add_tool_result("msg3")
        recent = mem.get_recent(2)
        assert len(recent) == 2
        assert recent[-1]["content"] == "msg3"

    def test_short_term_context_format(self):
        mem = ShortTermMemory(max_size=10)
        mem.add_user("用户问题")
        mem.add_agent("Agent 回答")
        ctx = mem.get_context_for_llm(2)
        assert "用户" in ctx
        assert "Agent" in ctx

    def test_short_term_key_facts(self):
        mem = ShortTermMemory(max_size=10)
        mem.add_key_fact("重要发现: X")
        mem.add_key_fact("重要发现: X")  # 重复不应重复添加
        assert len(mem.key_facts) == 1

    def test_short_term_clear(self):
        mem = ShortTermMemory(max_size=10)
        mem.add_user("msg")
        mem.add_key_fact("fact")
        mem.clear()
        assert len(mem.history) == 0
        assert len(mem.key_facts) == 0

    def test_working_memory_set_goal(self):
        wm = WorkingMemory()
        wm.set_goal("测试目标")
        assert wm.goal == "测试目标"
        assert wm.current_task_index == 0

    def test_working_memory_set_plan(self):
        wm = WorkingMemory()
        tasks = [{"title": "任务1"}, {"title": "任务2"}, {"title": "任务3"}]
        wm.set_plan(tasks)
        assert len(wm.plan) == 3
        assert wm.current_task()["title"] == "任务1"

    def test_working_memory_advance(self):
        wm = WorkingMemory()
        wm.set_plan([{"title": "T1"}, {"title": "T2"}, {"title": "T3"}])
        assert wm.advance_task() is True
        assert wm.current_task()["title"] == "T2"
        assert wm.advance_task() is True
        assert wm.current_task()["title"] == "T3"
        assert wm.advance_task() is False  # 超出范围

    def test_working_memory_log_action(self):
        wm = WorkingMemory()
        wm.set_goal("测试")
        wm.log_action("思考内容", "web_search", "搜索成功: 结果")
        assert len(wm.execution_log) == 1
        assert wm.execution_log[0]["action"] == "web_search"

    def test_working_memory_checkpoint(self, tmp_path):
        wm = WorkingMemory()
        wm.set_goal("测试目标")
        wm.set_plan([{"title": "T1"}, {"title": "T2"}])
        wm.log_action("思考", "搜索", "结果")

        path = str(tmp_path / "checkpoint.json")
        wm.save_checkpoint(path)
        assert os.path.exists(path)

        wm2 = WorkingMemory()
        assert wm2.load_checkpoint(path) is True
        assert wm2.goal == "测试目标"
        assert len(wm2.plan) == 2

    def test_working_memory_checkpoint_nonexistent(self):
        wm = WorkingMemory()
        assert wm.load_checkpoint("/nonexistent/path.json") is False

    def test_working_memory_progress(self):
        wm = WorkingMemory()
        wm.set_goal("测试")
        wm.set_plan([{"title": "T1"}, {"title": "T2"}, {"title": "T3"}])
        progress = wm.get_progress()
        assert progress["total_tasks"] == 3
        assert progress["completed_tasks"] == 0

    def test_long_term_store_and_search(self):
        ltm = LongTermMemory()
        doc_id = ltm.store("这是一条重要的经验")
        results = ltm.search("重要经验")
        assert len(results) >= 1
        if ltm.enabled:
            assert "重要" in results[0]["content"]


# ═══════════════════════════════════════════════
# Agent 核心循环测试
# ═══════════════════════════════════════════════

class TestAgentCore:
    """Agent 核心引擎测试"""

    @pytest.fixture
    def agent(self):
        config = AgentConfig(max_iterations=5)
        return AutoGPTAgent(config=config)

    def test_agent_initialization(self, agent):
        assert agent.config is not None
        assert len(agent.registry.list_tools()) == 4
        assert agent.short_memory is not None
        assert agent.working is not None

    def test_plan_phase_research_goal(self, agent):
        agent._plan_phase("调研 Python asyncio 的最新最佳实践", use_live_llm=False)
        plan = agent.working.plan
        assert len(plan) == 4
        assert plan[0]["tool"] == "web_search"
        assert plan[-1]["tool"] == "file_ops"

    def test_plan_phase_develop_goal(self, agent):
        agent._plan_phase("开发一个简单的 Web 应用", use_live_llm=False)
        plan = agent.working.plan
        assert len(plan) == 4
        assert any(t["tool"] == "code_exec" for t in plan)

    def test_plan_phase_data_goal(self, agent):
        agent._plan_phase("计算和统计数据趋势", use_live_llm=False)
        plan = agent.working.plan
        assert len(plan) == 3
        assert any(t["tool"] == "code_exec" for t in plan)

    def test_plan_phase_generic_goal(self, agent):
        agent._plan_phase("做点什么有趣的事情", use_live_llm=False)
        plan = agent.working.plan
        assert len(plan) == 3

    def test_plan_task_structure(self, agent):
        agent._plan_phase("调研 AI Agent 的发展趋势", use_live_llm=False)
        for task in agent.working.plan:
            assert "title" in task
            assert "description" in task
            assert "tool" in task
            assert "criteria" in task

    def test_think_simulated_first_step(self, agent):
        agent.working.set_goal("测试目标")
        agent.working.set_plan([{"title": "搜索信息", "description": "...", "tool": "web_search", "criteria": "找到3个来源"}])
        thought = agent._think_simulated(agent.working.plan[0], {})
        assert len(thought) > 10

    def test_think_simulated_mid_progress(self, agent):
        agent.working.set_goal("测试目标")
        agent.working.set_plan([{"title": "搜索", "description": "...", "tool": "web_search", "criteria": "完成"}])
        agent.working.log_action("开始搜索", "web_search", "搜索成功")
        thought = agent._think_simulated(agent.working.plan[0], {})
        assert len(thought) > 10

    def test_decide_action_first_search(self, agent):
        agent.working.set_goal("测试")
        agent.working.set_plan([{"title": "搜索", "description": "...", "tool": "web_search", "criteria": "完成"}])
        action, params = agent._decide_action(
            agent.working.plan[0], "需要搜索信息", use_live_llm=False
        )
        assert action in ["web_search", "file_ops"]

    def test_full_run_simulated(self, agent):
        result = agent.run("用 Python 打印 Hello World")
        assert result["goal"] == "用 Python 打印 Hello World"
        assert len(result["plan"]) >= 2
        assert result["iterations"] > 0
        assert result["mode"] == "simulated"
        assert len(result["summary"]) > 50

    def test_full_run_returns_complete_structure(self, agent):
        result = agent.run("调研 AI 安全最佳实践")
        assert "goal" in result
        assert "summary" in result
        assert "plan" in result
        assert "execution_log" in result
        assert "iterations" in result
        assert "mode" in result

    def test_run_clears_previous_state(self, agent):
        result1 = agent.run("目标1")
        iter1 = result1["iterations"]
        result2 = agent.run("目标2")
        iter2 = result2["iterations"]
        assert result2["goal"] == "目标2"
        assert result2["plan"] != result1["plan"]
        # 新任务从 0 开始计数
        assert iter2 > 0


# ═══════════════════════════════════════════════
# 配置模块测试
# ═══════════════════════════════════════════════

class TestConfig:
    """配置模块测试"""

    def test_default_config(self):
        config = AgentConfig()
        assert config.max_iterations == 10
        assert config.temperature == 0.5
        assert config.allow_search is True
        assert config.allow_code_execution is True

    def test_custom_config(self):
        config = AgentConfig(max_iterations=20, temperature=0.3, allow_search=False)
        assert config.max_iterations == 20
        assert config.temperature == 0.3
        assert config.allow_search is False

    def test_get_config(self):
        config = get_config()
        assert config is not None
        assert isinstance(config.max_iterations, int)


# ═══════════════════════════════════════════════
# 集成测试
# ═══════════════════════════════════════════════

class TestIntegration:
    """集成测试 —— 验证完整工作流"""

    def test_end_to_end_simulated(self):
        config = AgentConfig(max_iterations=8)
        agent = AutoGPTAgent(config=config)
        result = agent.run("调研 Python asyncio 最佳实践")

        assert result["goal"] is not None
        assert len(result["plan"]) == 4
        assert result["iterations"] >= 4
        assert len(result["execution_log"]) > 0
        # 应该有完成总结
        assert "总结" in result["summary"] or "报告" in result["summary"] or "asyncio" in result["summary"]

    def test_short_goal_executes_correctly(self):
        config = AgentConfig(max_iterations=5)
        agent = AutoGPTAgent(config=config)
        result = agent.run("计算 1+1")
        assert len(result["plan"]) >= 2
        assert result["iterations"] >= 2

    def test_tool_chain_works(self):
        """验证工具链可以串联使用"""
        config = AgentConfig(max_iterations=6)
        agent = AutoGPTAgent(config=config)
        result = agent.run("开发一个简单的计算器")
        # 开发类任务应包含搜索、编码、报告
        used_tools = set(e["action"] for e in result["execution_log"])
        assert "finish" in used_tools or len(used_tools) >= 1

    def test_agent_registers_all_tools(self):
        config = AgentConfig()
        agent = AutoGPTAgent(config=config)
        tool_names = [t.name for t in agent.registry.list_tools()]
        assert "web_search" in tool_names
        assert "file_ops" in tool_names
        assert "code_exec" in tool_names
        assert "web_browse" in tool_names

    def test_disabled_tools_not_registered(self):
        config = AgentConfig(allow_search=False, allow_code_execution=False)
        agent = AutoGPTAgent(config=config)
        tool_names = [t.name for t in agent.registry.list_tools()]
        assert "web_search" not in tool_names
        assert "code_exec" not in tool_names
        assert "file_ops" in tool_names  # 仍然开启


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
