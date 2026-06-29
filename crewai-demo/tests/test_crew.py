"""
CrewAI Demo 测试套件

包含：
- Unit Tests: Agent 和 Task 的创建与配置验证
- Tool Tests: 自定义工具的功能测试
- Integration Tests: 完整流程测试（需要 API Key）
"""
import os
import sys
import json
import pytest

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.config import get_crewai_config
from src.tools.tools import (
    RequirementAnalyzerTool,
    TechStackRecommenderTool,
    CodeReviewTool,
    DeployCheckTool,
    SearchSimulatorTool,
)


# ═══════════════════════════════════════════════
# 工具单元测试
# ═══════════════════════════════════════════════

class TestRequirementAnalyzerTool:
    """需求分析工具测试"""

    def test_basic_requirement(self):
        tool = RequirementAnalyzerTool()
        result = tool._run("用户登录功能，支持手机号和邮箱登录")
        data = json.loads(result)
        assert "功能点" in data
        assert "非功能需求" in data
        assert len(data["功能点"]) > 0

    def test_empty_requirement(self):
        tool = RequirementAnalyzerTool()
        result = tool._run("")
        data = json.loads(result)
        assert "功能点" in data
        assert len(data["功能点"]) > 0  # 应返回默认示例


class TestTechStackRecommenderTool:
    """技术栈推荐工具测试"""

    def test_web_project(self):
        tool = TechStackRecommenderTool()
        result = tool._run("web")
        data = json.loads(result)
        assert "前端" in data
        assert "后端" in data
        assert "React" in data["前端"]

    def test_ai_project(self):
        tool = TechStackRecommenderTool()
        result = tool._run("ai")
        data = json.loads(result)
        assert "框架" in data
        assert "LangChain" in data["框架"] or "CrewAI" in data["框架"]

    def test_unknown_type_returns_default(self):
        tool = TechStackRecommenderTool()
        result = tool._run("unknown_type")
        data = json.loads(result)
        assert "前端" in data  # 返回 web 默认值


class TestCodeReviewTool:
    """代码审查工具测试"""

    def test_print_statement_warning(self):
        tool = CodeReviewTool()
        result = tool._run('print("hello world")')
        data = json.loads(result)
        assert data["总问题数"] >= 1
        issues = [i["描述"] for i in data["审查结果"]]
        assert any("logging" in desc for desc in issues)

    def test_hardcoded_secret(self):
        tool = CodeReviewTool()
        result = tool._run('password = "admin123"')
        data = json.loads(result)
        issues = [i["描述"] for i in data["审查结果"]]
        assert any("硬编码" in desc for desc in issues)

    def test_eval_detection(self):
        tool = CodeReviewTool()
        result = tool._run('eval("2 + 2")')
        data = json.loads(result)
        issues = [i["描述"] for i in data["审查结果"]]
        assert any("注入" in desc for desc in issues)

    def test_clean_code(self):
        tool = CodeReviewTool()
        result = tool._run(
            'def calculate(x: int, y: int) -> int:\n'
            '    """Add two numbers."""\n'
            '    return x + y\n'
        )
        data = json.loads(result)
        assert data["总问题数"] == 0


class TestDeployCheckTool:
    """部署检查工具测试"""

    def test_checklist_structure(self):
        tool = DeployCheckTool()
        result = tool._run("生产环境")
        data = json.loads(result)
        assert "检查清单" in data
        assert len(data["检查清单"]) == 8
        for item in data["检查清单"]:
            assert "检查项" in item
            assert "状态" in item
            assert "建议" in item


class TestSearchSimulatorTool:
    """搜索模拟工具测试"""

    def test_exact_match(self):
        tool = SearchSimulatorTool()
        result = tool._run("微服务")
        data = json.loads(result)
        assert "微服务" in data["关键词"]

    def test_partial_match(self):
        tool = SearchSimulatorTool()
        result = tool._run("Docker 容器化")
        data = json.loads(result)
        assert data["关键词"] in ["Docker", "Docker 容器化"]

    def test_no_match(self):
        tool = SearchSimulatorTool()
        # 使用与知识库完全无交集的查询词，验证返回模拟结果
        result = tool._run("区块链技术在供应链中的应用")
        data = json.loads(result)
        assert "模拟" in data["内容"]


# ═══════════════════════════════════════════════
# Agent 创建测试 —— Mock Agent 构造函数避免 Pydantic 验证
# ═══════════════════════════════════════════════

class TestAgentCreation:
    """Agent 创建测试 —— 验证工厂函数正确调用 CrewAI Agent"""

    @pytest.fixture
    def mock_llm(self):
        """使用模型名字符串作为 LLM（CrewAI 接受字符串作为 model name）"""
        return "gpt-4o"

    def test_create_product_manager(self, mocker, mock_llm):
        mock_agent_class = mocker.patch("src.agents.product_manager.Agent", return_value=mocker.MagicMock())
        from src.agents.product_manager import create_product_manager
        agent = create_product_manager(llm=mock_llm)
        assert mock_agent_class.called
        call_kwargs = mock_agent_class.call_args.kwargs
        assert call_kwargs["role"] == "产品经理"
        assert call_kwargs["allow_delegation"] is False
        assert len(call_kwargs["tools"]) >= 1

    def test_create_architect(self, mocker, mock_llm):
        mock_agent_class = mocker.patch("src.agents.architect.Agent", return_value=mocker.MagicMock())
        from src.agents.architect import create_architect
        agent = create_architect(llm=mock_llm)
        call_kwargs = mock_agent_class.call_args.kwargs
        assert call_kwargs["role"] == "系统架构师"
        assert call_kwargs["allow_delegation"] is True
        assert len(call_kwargs["tools"]) >= 2

    def test_create_developer(self, mocker, mock_llm):
        mock_agent_class = mocker.patch("src.agents.developer.Agent", return_value=mocker.MagicMock())
        from src.agents.developer import create_developer
        agent = create_developer(llm=mock_llm)
        call_kwargs = mock_agent_class.call_args.kwargs
        assert call_kwargs["role"] == "高级开发工程师"
        assert len(call_kwargs["tools"]) >= 1

    def test_create_tester(self, mocker, mock_llm):
        mock_agent_class = mocker.patch("src.agents.tester.Agent", return_value=mocker.MagicMock())
        from src.agents.tester import create_tester
        agent = create_tester(llm=mock_llm)
        call_kwargs = mock_agent_class.call_args.kwargs
        assert call_kwargs["role"] == "测试工程师"
        assert len(call_kwargs["tools"]) >= 1

    def test_create_devops(self, mocker, mock_llm):
        mock_agent_class = mocker.patch("src.agents.devops.Agent", return_value=mocker.MagicMock())
        from src.agents.devops import create_devops
        agent = create_devops(llm=mock_llm)
        call_kwargs = mock_agent_class.call_args.kwargs
        assert call_kwargs["role"] == "DevOps 运维工程师"
        assert len(call_kwargs["tools"]) >= 2


# ═══════════════════════════════════════════════
# Task 创建测试 —— Mock Task 构造函数
# ═══════════════════════════════════════════════

class TestTaskCreation:
    """Task 创建测试 —— 验证工厂函数正确调用 CrewAI Task"""

    def test_create_requirement_task(self, mocker):
        mock_agent = mocker.MagicMock()
        mock_task_class = mocker.patch("src.tasks.tasks.Task", return_value=mocker.MagicMock())
        from src.tasks.tasks import create_requirement_task
        task = create_requirement_task(mock_agent, "测试需求")
        assert mock_task_class.called
        call_kwargs = mock_task_class.call_args.kwargs
        assert "测试需求" in call_kwargs["description"]
        assert call_kwargs["agent"] == mock_agent
        assert call_kwargs["async_execution"] is False

    def test_create_architecture_task(self, mocker):
        mock_agent = mocker.MagicMock()
        mock_task_class = mocker.patch("src.tasks.tasks.Task", return_value=mocker.MagicMock())
        from src.tasks.tasks import create_architecture_task
        task = create_architecture_task(mock_agent, "测试项目")
        call_kwargs = mock_task_class.call_args.kwargs
        assert "测试项目" in call_kwargs["description"]

    def test_create_development_task(self, mocker):
        mock_agent = mocker.MagicMock()
        mock_task_class = mocker.patch("src.tasks.tasks.Task", return_value=mocker.MagicMock())
        from src.tasks.tasks import create_development_task
        task = create_development_task(mock_agent, "测试项目")
        call_kwargs = mock_task_class.call_args.kwargs
        assert "测试项目" in call_kwargs["description"]

    def test_create_testing_task(self, mocker):
        mock_agent = mocker.MagicMock()
        mock_task_class = mocker.patch("src.tasks.tasks.Task", return_value=mocker.MagicMock())
        from src.tasks.tasks import create_testing_task
        task = create_testing_task(mock_agent, "测试项目")
        call_kwargs = mock_task_class.call_args.kwargs
        assert "测试项目" in call_kwargs["description"]

    def test_create_deployment_task(self, mocker):
        mock_agent = mocker.MagicMock()
        mock_task_class = mocker.patch("src.tasks.tasks.Task", return_value=mocker.MagicMock())
        from src.tasks.tasks import create_deployment_task
        task = create_deployment_task(mock_agent, "测试项目")
        call_kwargs = mock_task_class.call_args.kwargs
        assert "测试项目" in call_kwargs["description"]


# ═══════════════════════════════════════════════
# 配置模块测试
# ═══════════════════════════════════════════════

class TestConfig:
    """配置模块测试"""

    def test_get_crewai_config_defaults(self):
        config = get_crewai_config()
        assert "process" in config
        assert "verbose" in config
        assert "memory" in config
        assert config["process"] in ("sequential", "hierarchical")


# ═══════════════════════════════════════════════
# 集成测试（需要 API Key）
# ═══════════════════════════════════════════════

@pytest.mark.integration
class TestIntegration:
    """集成测试 —— 需要配置 API Key"""

    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY") and not os.getenv("DEEPSEEK_API_KEY"),
        reason="未配置 API Key，跳过集成测试",
    )
    def test_build_crew(self):
        """测试 Crew 构建"""
        from src.crew import build_crew
        crew = build_crew("测试项目：一个简单的 Todo 应用", verbose=False)
        assert crew is not None
        assert len(crew.agents) == 5
        assert len(crew.tasks) == 5

    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY") and not os.getenv("DEEPSEEK_API_KEY"),
        reason="未配置 API Key，跳过集成测试",
    )
    def test_run_software_team_basic(self):
        """测试完整流程执行（使用简单的课题以减少 Token 消耗）"""
        from src.crew import run_software_team
        result = run_software_team(
            "构建一个简单的待办事项 (Todo) Web 应用，支持增删改查",
            verbose=False,
        )
        assert result is not None
        assert "result" in result
        assert len(result["result"]) > 0
        assert result["topic"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
