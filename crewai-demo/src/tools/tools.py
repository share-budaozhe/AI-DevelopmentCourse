"""
CrewAI 自定义工具集

为 Agent 提供实用的外部能力：Web 搜索模拟、需求分析、代码审查、部署检查等。

CrewAI 的工具基于 LangChain BaseTool，每个工具包含：
- name: 工具名称
- description: 功能描述（Agent 据此判断何时调用）
- _run(): 实际执行逻辑
"""
import json
from crewai.tools import BaseTool


class RequirementAnalyzerTool(BaseTool):
    """
    需求分析工具 —— 对输入的产品需求进行结构化分析
    """
    name: str = "requirement_analyzer"
    description: str = (
        "对产品需求进行结构化分析，输出功能点列表、优先级、依赖关系。"
        "输入：需求文本字符串。输出：JSON 格式的结构化分析结果。"
    )

    def _run(self, requirement: str) -> str:
        # 将需求文本拆分为句子，过滤空句，取前 5 个
        raw_sentences = requirement.replace("\n", "。").split("。")
        sentences = [s.strip() for s in raw_sentences if s.strip()][:5]

        if sentences:
            features = [
                {"名称": f.split("：")[0] if "：" in f else f[:20],
                 "优先级": "P0" if i == 0 else ("P1" if i == 1 else "P2"),
                 "依赖": [] if i == 0 else ["功能点1"]}
                for i, f in enumerate(sentences)
            ]
        else:
            features = [
                {"名称": "用户管理", "优先级": "P0", "依赖": []},
                {"名称": "数据展示", "优先级": "P1", "依赖": ["用户管理"]},
                {"名称": "报表导出", "优先级": "P2", "依赖": ["数据展示"]},
            ]

        analysis = {
            "功能点": features,
            "非功能需求": ["性能：响应时间 < 500ms", "安全：RBAC 权限控制"],
            "技术约束": ["需兼容主流浏览器", "需支持移动端适配"],
        }
        return json.dumps(analysis, ensure_ascii=False, indent=2)


class TechStackRecommenderTool(BaseTool):
    """
    技术栈推荐工具 —— 根据项目需求推荐合适的技术栈
    """
    name: str = "tech_stack_recommender"
    description: str = (
        "根据项目类型和需求，推荐合适的技术栈组合。"
        "输入：项目类型（web/mobile/ai/data）。输出：推荐的技术栈 JSON。"
    )

    def _run(self, project_type: str) -> str:
        project_type = project_type.strip().lower()
        recommendations = {
            "web": {
                "前端": "React 18 + TypeScript + TailwindCSS",
                "后端": "FastAPI (Python) 或 NestJS (Node.js)",
                "数据库": "PostgreSQL + Redis",
                "部署": "Docker + Nginx + 云服务器",
            },
            "mobile": {
                "前端": "React Native 或 Flutter",
                "后端": "Go (Gin) 或 Python (FastAPI)",
                "数据库": "SQLite (本地) + 云端 PostgreSQL",
                "部署": "应用商店分发 + 云端 API",
            },
            "ai": {
                "框架": "LangChain / CrewAI / LangGraph",
                "模型": "OpenAI GPT-4o / Claude Sonnet / DeepSeek",
                "向量库": "Milvus / ChromaDB",
                "部署": "GPU 服务器 + Docker + FastAPI",
            },
            "data": {
                "采集": "Apache Kafka + Flink",
                "存储": "ClickHouse + S3 对象存储",
                "计算": "Spark / DBT",
                "展示": "Grafana / Superset",
            },
        }
        result = recommendations.get(project_type, recommendations["web"])
        return json.dumps(result, ensure_ascii=False, indent=2)


class CodeReviewTool(BaseTool):
    """
    代码审查工具 —— 对代码进行基础质量检查
    """
    name: str = "code_reviewer"
    description: str = (
        "对代码片段进行基础质量审查，检查代码规范、安全问题、性能隐患。"
        "输入：代码字符串。输出：审查意见 JSON。"
    )

    def _run(self, code: str) -> str:
        issues = []
        # 基础规则检查
        if "print(" in code:
            issues.append({"级别": "建议", "类型": "日志规范", "描述": "生产代码建议使用 logging 而非 print"})
        if "password" in code.lower() or "secret" in code.lower():
            issues.append({"级别": "严重", "类型": "安全", "描述": "检测到硬编码凭据风险，应使用环境变量"})
        if "except:" in code and "Exception" not in code:
            issues.append({"级别": "警告", "类型": "异常处理", "描述": "裸 except 应指定具体异常类型"})
        if "eval(" in code or "exec(" in code:
            issues.append({"级别": "严重", "类型": "安全", "描述": "eval/exec 存在代码注入风险"})
        if "TODO" in code or "FIXME" in code:
            issues.append({"级别": "提示", "类型": "代码质量", "描述": "存在未完成的 TODO/FIXME 标记"})

        if not issues:
            issues.append({"级别": "通过", "类型": "综合", "描述": "未发现明显问题，代码质量良好"})

        return json.dumps({"审查结果": issues, "总问题数": len([i for i in issues if i["级别"] != "通过"])}, ensure_ascii=False, indent=2)


class DeployCheckTool(BaseTool):
    """
    部署检查工具 —— 验证部署就绪条件
    """
    name: str = "deploy_checker"
    description: str = (
        "检查部署前的必要条件是否满足，输出检查清单结果。"
        "输入：部署环境描述。输出：检查清单 JSON。"
    )

    def _run(self, env_description: str) -> str:
        checklist = [
            {"检查项": "Dockerfile 是否存在", "状态": "待确认", "建议": "确保根目录有 Dockerfile"},
            {"检查项": "环境变量配置", "状态": "待确认", "建议": "检查 .env 文件是否包含所有必要变量"},
            {"检查项": "数据库迁移脚本", "状态": "待确认", "建议": "确认 migration 脚本已准备"},
            {"检查项": "健康检查端点", "状态": "待确认", "建议": "实现 /health 端点供监控使用"},
            {"检查项": "日志配置", "状态": "待确认", "建议": "配置结构化日志（JSON 格式）"},
            {"检查项": "资源限制", "状态": "待确认", "建议": "设置 CPU/内存 limits"},
            {"检查项": "监控告警", "状态": "待确认", "建议": "配置 Prometheus metrics + Grafana"},
            {"检查项": "回滚方案", "状态": "待确认", "建议": "保留上一版本镜像，支持快速回滚"},
        ]
        return json.dumps({"环境": env_description, "检查清单": checklist}, ensure_ascii=False, indent=2)


class SearchSimulatorTool(BaseTool):
    """
    搜索模拟工具 —— 模拟知识库检索（Demo 中用于替代真实搜索 API）
    """
    name: str = "knowledge_search"
    description: str = (
        "从内部知识库检索技术信息。输入：搜索关键词。输出：相关知识条目。"
    )

    def _run(self, query: str) -> str:
        knowledge_base = {
            "微服务": "微服务架构将应用拆分为小型独立服务，每个服务运行在独立进程中，通过轻量级 API 通信。优势：独立部署、技术异构、可扩展性强。挑战：分布式复杂性、数据一致性、运维成本。",
            "API设计": "RESTful API 设计原则：资源导向 URL、正确使用 HTTP 方法（GET/POST/PUT/DELETE）、状态码语义化、版本控制（/v1/）、分页支持、HATEOAS 超媒体驱动。",
            "数据库选型": "关系型（OLTP: PostgreSQL/MySQL；OLAP: ClickHouse）、文档型（MongoDB）、键值型（Redis）、图数据库（Neo4j）、时序数据库（TimescaleDB）、向量数据库（Milvus/ChromaDB）。",
            "Docker": "Docker 通过容器化技术实现环境一致性。核心概念：Dockerfile（构建）、Image（镜像）、Container（容器）、Docker Compose（编排）、Registry（仓库）。常用命令：docker build/run/compose up。",
            "CI/CD": "持续集成/持续部署流水线：代码提交 → 自动构建 → 单元测试 → 集成测试 → 镜像打包 → 部署到环境。工具：GitHub Actions、GitLab CI、Jenkins。",
            "认证授权": "认证（你是谁）vs 授权（你能做什么）。JWT：无状态令牌，适合分布式系统。OAuth2.0：第三方授权标准。RBAC：基于角色的权限控制。SSO：单点登录。",
        }
        query_lower = query.lower()
        for key, value in knowledge_base.items():
            if key.lower() in query_lower or any(w in query_lower for w in key):
                return json.dumps({"关键词": key, "内容": value}, ensure_ascii=False, indent=2)
        return json.dumps({"关键词": query, "内容": f"关于'{query}'的模拟知识：这是一个演示环境中的模拟检索结果。在生产环境中，这里将返回真实的知识库或搜索引擎结果。"}, ensure_ascii=False, indent=2)
