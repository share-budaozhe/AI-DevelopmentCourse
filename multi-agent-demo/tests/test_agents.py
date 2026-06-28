"""
Agent 单元测试 —— 验证各 Agent 能正常初始化和执行基本逻辑

运行: pytest tests/ -v
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from src.tools.tools import (
    shared_context, search_knowledge_base,
    read_shared_context, write_shared_context, calculate
)
from src.config import get_llm


# ──────────────────────────────────────────────
# 工具函数测试
# ──────────────────────────────────────────────

class TestTools:
    """工具层单元测试"""

    def setup_method(self):
        # 每个测试前重置共享上下文
        shared_context["topic"] = ""
        shared_context["research_notes"] = ""
        shared_context["analysis_result"] = ""
        shared_context["draft_content"] = ""
        shared_context["review_feedback"] = ""
        shared_context["final_output"] = ""
        shared_context["status"] = "initialized"

    def test_search_knowledge_base(self):
        """测试知识库检索"""
        result = search_knowledge_base.invoke({"query": "人工智能"})
        assert "人工智能" in result
        assert len(result) > 20

    def test_search_knowledge_base_no_match(self):
        """测试知识库无匹配"""
        result = search_knowledge_base.invoke({"query": "不存在的关键词xyz"})
        assert "未找到" in result

    def test_read_write_shared_context(self):
        """测试共享上下文读写"""
        write_result = write_shared_context.invoke({"field": "topic", "value": "测试话题"})
        assert "成功" in write_result

        read_result = read_shared_context.invoke({"field": "topic"})
        assert read_result == "测试话题"

    def test_read_nonexistent_field(self):
        """测试读取不存在的字段"""
        result = read_shared_context.invoke({"field": "nonexistent"})
        assert "不存在" in result

    def test_write_invalid_field(self):
        """测试写入无效字段"""
        result = write_shared_context.invoke({"field": "invalid", "value": "test"})
        assert "不存在" in result

    def test_calculate_addition(self):
        """测试数学计算：加法"""
        result = calculate.invoke({"expression": "2 + 3"})
        assert "5" in result

    def test_calculate_complex(self):
        """测试数学计算：复杂表达式"""
        result = calculate.invoke({"expression": "(1 + 2) * 3 - 4 / 2"})
        assert "7" in result

    def test_calculate_error(self):
        """测试数学计算：错误表达式"""
        result = calculate.invoke({"expression": "1/0"})
        assert "错误" in result

    def test_shared_context_status(self):
        """测试状态流转"""
        write_shared_context.invoke({"field": "status", "value": "researching"})
        assert read_shared_context.invoke({"field": "status"}) == "researching"

        write_shared_context.invoke({"field": "status", "value": "completed"})
        assert read_shared_context.invoke({"field": "status"}) == "completed"


# ──────────────────────────────────────────────
# 配置测试
# ──────────────────────────────────────────────

class TestConfig:
    """配置模块测试"""

    def test_get_llm_default(self):
        """测试获取默认 LLM 实例"""
        llm = get_llm()
        assert llm is not None
        # 验证必要属性
        assert hasattr(llm, "invoke")

    def test_get_llm_with_params(self):
        """测试带参数获取 LLM"""
        llm = get_llm(temperature=0.5)
        assert llm is not None


# ──────────────────────────────────────────────
# 工作流测试
# ──────────────────────────────────────────────

class TestWorkflow:
    """工作流核心逻辑测试"""

    def test_workflow_graph_creation(self):
        """测试工作流图创建"""
        from src.workflow.collaboration_graph import build_collaboration_graph
        graph = build_collaboration_graph()
        assert graph is not None
        # 验证有正确的节点
        assert hasattr(graph, "invoke")

    def test_workflow_state_structure(self):
        """测试状态结构"""
        from src.workflow.collaboration_graph import AgentState
        state: AgentState = {
            "topic": "test",
            "writing_style": "技术博客",
            "research_output": "",
            "analysis_output": "",
            "draft_output": "",
            "review_output": "",
            "final_output": "",
            "status": "started",
            "error": "",
        }
        assert state["topic"] == "test"
        assert state["writing_style"] == "技术博客"


# ──────────────────────────────────────────────
# 集成测试（需要 API Key，标记为可选）
# ──────────────────────────────────────────────

@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") and not os.getenv("DEEPSEEK_API_KEY"),
    reason="需要配置 API Key 才能运行"
)
class TestIntegration:
    """集成测试（需要真实 LLM API）"""

    @pytest.mark.skip(reason="耗时长，按需启用")
    def test_full_workflow(self):
        """测试完整工作流"""
        from src.workflow.collaboration_graph import run_collaboration
        result = run_collaboration("什么是人工智能", "科普文章")
        assert result["status"] in ("completed", "error")
        if result["status"] == "completed":
            assert len(result.get("final_output", "")) > 0

    def test_single_agent_research(self):
        """测试单个研究 Agent"""
        from src.agents.research_agent import research
        output = research("人工智能")
        assert output is not None
        assert len(output) > 0
