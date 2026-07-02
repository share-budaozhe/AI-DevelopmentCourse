"""
AutoGPT 自主 Agent 核心引擎
布道者

这是整个 Demo 的核心——实现了 AutoGPT 的自主任务分解与执行循环。

核心流程:
    1. 初始化阶段:    加载配置、注册工具、初始化记忆
    2. 规划阶段:      将大目标分解为子任务列表
    3. 执行循环:      对每个子任务: 思考→行动→观察→调整
    4. 总结阶段:      汇总执行结果，生成最终交付物
    5. 记忆持久化:    将经验存入长期记忆

参考论文:
    - "AutoGPT: Autonomous Task Execution with Language Models"
    - ReAct (Reasoning + Acting) 模式
    - Plan-and-Solve 策略
"""
import os
import re
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any, List

from src.config import AgentConfig, SYSTEM_PROMPT, NEXT_ACTION_PROMPT, SUMMARY_PROMPT
from src.tools.base import ToolRegistry, ToolResult
from src.tools.tools import WebSearchTool, FileOperationsTool, CodeExecutionTool, WebBrowseTool
from src.memory.memory import ShortTermMemory, LongTermMemory, WorkingMemory


class AutoGPTAgent:
    """
    自主 AI Agent

    布道者:
        这是 AutoGPT 的核心实现。Agent 接收一个目标（Goal），
        自主完成以下步骤:
        1. 规划 — 分析目标，拆解为可执行的子任务
        2. 执行 — 逐个完成子任务，通过 思考→行动→观察 循环推进
        3. 总结 — 汇总所有发现，生成最终答案

        Agent 在每一步都会:
        - 感知当前状态（工作记忆 + 短期记忆）
        - 参考历史经验（长期记忆）
        - 决定下一步行动（LLM 推理 或 规则引擎）
        - 执行工具调用并观察结果
        - 更新记忆，进入下一轮循环
    """

    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig()
        self.registry = ToolRegistry()
        self.short_memory = ShortTermMemory(max_size=self.config.short_term_memory_size)
        self.long_memory = LongTermMemory(persist_dir=self.config.chroma_persist_dir)
        self.working = WorkingMemory()
        self._setup_tools()
        self._iteration = 0
        self._llm = None  # 延迟初始化

    def _setup_tools(self):
        """
        注册可用工具

        布道者:
            根据配置选择性注册工具。
            关闭的工具不会被注册，LLM 也无法调用——这是最小权限原则的体现。
        """
        tools = []
        if self.config.allow_search:
            tools.append(WebSearchTool())
        if self.config.allow_file_ops:
            tools.append(FileOperationsTool(workspace_dir=self.config.workspace_dir))
        if self.config.allow_code_execution:
            tools.append(CodeExecutionTool())
        if self.config.allow_web_browse:
            tools.append(WebBrowseTool())
        self.registry.register_all(tools)

    def _get_llm(self):
        """延迟初始化 LLM 连接"""
        if self._llm is None:
            from langchain_openai import ChatOpenAI
            self._llm = ChatOpenAI(
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            )
        return self._llm

    # ═══════════════════════════════════════════════
    # 公共入口: 执行目标任务
    # 布道者: run() 是外部调用的唯一入口
    # ═══════════════════════════════════════════════

    def run(self, goal: str, use_live_llm: bool = False) -> Dict[str, Any]:
        """
        执行目标任务

        参数:
            goal:        用户提出的目标（如"调研 Python 异步编程的最佳实践"）
            use_live_llm: 是否调用真实 LLM（默认 False，使用模拟推理）

        返回:
            包含执行摘要、结果、记忆日志的字典
        """
        # 重置状态
        self._iteration = 0
        self.working.set_goal(goal)
        self.short_memory.clear()

        print(f"\n{'='*60}")
        print(f"  🤖 {self.config.name} 已启动")
        print(f"  目标: {goal}")
        print(f"  模式: {'🟢 真实 LLM' if use_live_llm else '🟡 模拟推理'}")
        print(f"  工具: {len(self.registry.list_tools())} 个已注册")
        print(f"{'='*60}\n")

        # ── 阶段 1: 规划 ──
        print("📋 [阶段 1/4] 规划: 分解目标为子任务...")
        self._plan_phase(goal, use_live_llm)
        self._print_plan()

        # ── 阶段 2: 执行 ──
        print("\n⚡ [阶段 2/4] 执行: 逐个子任务推进...")
        self._execution_phase(use_live_llm)

        # ── 阶段 3: 总结 ──
        print("\n📊 [阶段 3/4] 总结: 汇总执行结果...")
        summary = self._summary_phase(use_live_llm)

        # ── 阶段 4: 持久化 ──
        print("\n💾 [阶段 4/4] 持久化: 存储经验到长期记忆...")
        self._persist_memory(goal, summary)

        result = {
            "goal": goal,
            "summary": summary,
            "plan": self.working.plan,
            "execution_log": self.working.execution_log,
            "iterations": self._iteration,
            "mode": "live" if use_live_llm else "simulated",
        }

        print(f"\n{'='*60}")
        print(f"  ✅ 任务完成！共 {self._iteration} 次迭代")
        print(f"{'='*60}\n")
        return result

    # ═══════════════════════════════════════════════
    # 阶段 1: 任务规划
    # 布道者: 使用 LLM 或内置规则将大目标分解为可管理的子任务
    # ═══════════════════════════════════════════════

    def _plan_phase(self, goal: str, use_live_llm: bool):
        """
        规划阶段

        布道者:
            让 LLM 分析目标，结合可用工具，生成一个结构化的任务计划。
            每个子任务应该独立、可验证、有明确的完成标准。
        """
        if use_live_llm:
            plan = self._plan_with_llm(goal)
        else:
            plan = self._plan_with_rules(goal)

        self.working.set_plan(plan)
        self.short_memory.add_system(f"已制定计划，共 {len(plan)} 个子任务")
        for i, task in enumerate(plan):
            self.short_memory.add_system(f"  子任务 {i+1}: {task.get('title', 'N/A')}")

    def _plan_with_llm(self, goal: str) -> List[Dict[str, Any]]:
        """使用真实 LLM 进行任务规划"""
        prompt = f"""你是一个任务规划专家。请将以下目标分解为 3-5 个具体的子任务。

目标: {goal}

可用工具:
{self.registry.get_tools_description()}

要求:
1. 每个子任务独立且可执行
2. 命名可用的工具
3. 按逻辑顺序排列

请以 JSON 格式输出:
[{{"title": "子任务名称", "description": "详细描述", "tool": "建议使用的工具", "criteria": "完成标准"}}]
"""
        try:
            llm = self._get_llm()
            response = llm.invoke(prompt)
            # 尝试解析 JSON
            text = response.content if hasattr(response, 'content') else str(response)
            json_match = re.search(r'\[[\s\S]*\]', text)
            if json_match:
                return json.loads(json_match.group(0))
            return self._plan_with_rules(goal)
        except Exception:
            return self._plan_with_rules(goal)

    def _plan_with_rules(self, goal: str) -> List[Dict[str, Any]]:
        """
        基于规则的智能规划

        布道者:
            当 LLM 不可用时，使用模式匹配 + 关键词分析来生成合理的计划。
            这确保了 Demo 在没有 API Key 的情况下也能展示完整的执行流程。
        """
        goal_lower = goal.lower()

        # 调研/分析类任务
        if any(kw in goal_lower for kw in ['调研', '研究', '分析', '了解', '学习', 'research', 'analyze']):
            topic = self._extract_topic(goal)
            return [
                {"title": f"搜索与收集: {topic}", "description": f"搜索 '{topic}' 的相关资料，收集多源信息",
                 "tool": "web_search", "criteria": "至少找到 3 个有效来源"},
                {"title": "信息整理与分类", "description": "对收集到的信息进行分类、去重和结构化整理",
                 "tool": "code_exec", "criteria": "生成结构化的信息表格"},
                {"title": "深度分析与洞察", "description": "基于整理后的信息进行深度分析，提炼关键观点",
                 "tool": "code_exec", "criteria": "输出 3-5 条关键洞察"},
                {"title": "报告生成", "description": "将分析和发现汇总为一份结构化的研究报告",
                 "tool": "file_ops", "criteria": "生成完整报告文件"},
            ]
        # 开发/编码类任务
        elif any(kw in goal_lower for kw in ['开发', '编写', '实现', '构建', '代码', 'develop', 'code', 'build']):
            feature = self._extract_topic(goal)
            return [
                {"title": f"需求分析与设计", "description": f"分析 '{feature}' 的需求，设计技术方案",
                 "tool": "web_search", "criteria": "明确功能边界和技术选型"},
                {"title": "核心代码实现", "description": f"实现 '{feature}' 的核心功能代码",
                 "tool": "code_exec", "criteria": "代码可运行且通过测试"},
                {"title": "测试验证", "description": "编写和执行测试用例，验证功能正确性",
                 "tool": "code_exec", "criteria": "所有测试用例通过"},
                {"title": "文档与交付", "description": "编写使用文档，生成最终交付物",
                 "tool": "file_ops", "criteria": "生成完整文档"},
            ]
        # 数据/计算类任务
        elif any(kw in goal_lower for kw in ['计算', '数据', '统计', '计算', 'data', 'statistics']):
            topic = self._extract_topic(goal)
            return [
                {"title": "数据获取", "description": f"搜索和整理 '{topic}' 相关数据",
                 "tool": "web_search", "criteria": "获取足够数据样本"},
                {"title": "数据处理与分析", "description": "使用 Python 进行数据清洗、计算和分析",
                 "tool": "code_exec", "criteria": "输出统计分析结果"},
                {"title": "结果可视化与报告", "description": "生成分析报告和可视化图表",
                 "tool": "file_ops", "criteria": "生成完整分析报告"},
            ]
        # 默认: 通用三步流程
        else:
            topic = goal[:50]
            return [
                {"title": f"信息收集", "description": f"搜索 '{topic}' 相关信息",
                 "tool": "web_search", "criteria": "找到相关信息"},
                {"title": "分析处理", "description": "分析收集到的信息",
                 "tool": "code_exec", "criteria": "完成分析"},
                {"title": "结果汇总", "description": "汇总结果",
                 "tool": "file_ops", "criteria": "生成报告"},
            ]

    def _extract_topic(self, goal: str) -> str:
        """从目标中提取核心主题"""
        # 移除常见的引导词
        for word in ['帮我', '请', '能不能', '可以', '我想', '调研', '研究', '分析', '开发', '编写', '构建']:
            goal = goal.replace(word, '')
        return goal.strip()[:50] or goal[:50]

    def _print_plan(self):
        """打印任务计划"""
        print("  📋 任务计划:")
        for i, task in enumerate(self.working.plan):
            print(f"    {i+1}. [{task.get('tool', 'N/A')}] {task.get('title', 'N/A')}")
            print(f"       {task.get('description', '')[:80]}")
            print(f"       标准: {task.get('criteria', '完成')}")

    # ═══════════════════════════════════════════════
    # 阶段 2: 自主执行循环
    # 布道者: AutoGPT 的核心——思考→行动→观察循环
    # ═══════════════════════════════════════════════

    def _execution_phase(self, use_live_llm: bool):
        """
        执行阶段

        布道者:
            这是 Agent 自主性的核心体现。
            对每个子任务，进入 思考→行动→观察 循环:
            - THOUGHT:  分析当前状态，推理下一步应做什么
            - ACTION:   调用工具执行具体操作
            - OBSERVE:  观察工具返回结果，评估是否完成

            循环终止条件:
            - 子任务完成
            - 达到最大迭代次数
            - Agent 主动调用 finish 命令
        """
        for i, task in enumerate(self.working.plan):
            if self.working.aborted:
                break

            self.working.current_task_index = i
            print(f"\n  ┌─ 子任务 {i+1}/{len(self.working.plan)}: {task['title']}")
            print(f"  │  工具: {task['tool']}  |  标准: {task['criteria']}")

            # 子任务执行循环
            for attempt in range(self.config.max_iterations):
                self._iteration += 1

                # ── THOUGHT ──
                thought = self._think(task, use_live_llm)

                # ── ACTION ──
                print(f"  │  💭 {thought[:80]}...")
                action_name, action_params = self._decide_action(task, thought, use_live_llm)

                # ── OBSERVE ──
                result = self._act(action_name, action_params)
                success_icon = "✅" if result.success else "❌"
                print(f"  │  {success_icon} [{action_name}] {str(result)[:100]}...")

                self.working.log_action(thought, action_name, str(result))
                self.short_memory.add_agent(
                    f"THOUGHT: {thought}\nACTION: {action_name}\nRESULT: {str(result)}",
                    {"iteration": self._iteration},
                )

                # 检查是否完成
                if action_name == "finish" or self._is_subtask_complete(task, result):
                    print(f"  └─ ✅ 子任务完成")
                    break
            else:
                print(f"  └─ ⚠️  达到最大迭代次数 ({self.config.max_iterations})")

    def _think(self, task: Dict[str, Any], use_live_llm: bool) -> str:
        """
        思考步骤

        布道者:
            Agent 在每次行动前先思考——分析当前状态、参考历史记忆、
            推理下一步最佳行动。这是 ReAct 模式的 Reasoning 部分。
        """
        context = {
            "task_title": task["title"],
            "task_desc": task["description"],
            "task_tool": task["tool"],
            "criteria": task["criteria"],
            "progress": self.working.get_progress(),
            "recent_memory": self.short_memory.get_context_for_llm(5),
            "available_tools": [t.name for t in self.registry.list_tools()],
        }

        if use_live_llm:
            return self._think_with_llm(context)
        else:
            return self._think_simulated(task, context)

    def _think_with_llm(self, context: Dict) -> str:
        """使用 LLM 进行深度推理"""
        try:
            prompt = NEXT_ACTION_PROMPT.format(
                goal=self.working.goal,
                completed_count=self.working.current_task_index,
                total_count=len(self.working.plan),
                completed_steps=json.dumps(self.working.execution_log[-3:], ensure_ascii=False),
                last_action=context.get("task_desc", ""),
                last_thought="",
                last_result=context.get("recent_memory", ""),
            )
            llm = self._get_llm()
            response = llm.invoke(prompt)
            text = response.content if hasattr(response, 'content') else str(response)
            return text[:500]
        except Exception:
            return self._think_simulated(None, context)

    def _think_simulated(self, task: Dict, context: Dict) -> str:
        """
        模拟推理

        布道者:
            Demo 模式的智能推理引擎。
            虽然不调用 LLM，但通过规则引擎模拟了真实的思考过程。
            在生产环境中，这里会被替换为 LLM 的推理输出。
        """
        task_tool = task.get("tool", "web_search")
        task_idx = self.working.current_task_index
        log_size = len(self.working.execution_log)

        # 根据执行历史和任务类型生成合理的思考
        if log_size == 0:
            return f"开始执行子任务: {task['title']}。我需要先使用 {task_tool} 获取基础信息。"

        last_result = self.working.execution_log[-1] if self.working.execution_log else {}
        last_success = "成功" if "成功" in str(last_result) else "需要重试"

        if task_tool == "web_search":
            if log_size == 1:
                return "已获取初步搜索结果，现在需要整理和分析这些信息。"
            elif log_size == 2:
                return "信息已整理完毕，接下来进行深度分析和洞察提炼。"
            else:
                return "分析已完成，准备生成最终报告。"

        elif task_tool == "code_exec":
            if log_size == 1:
                return f"已通过搜索了解需求，现在编写 {task['title']} 的核心实现代码。"
            elif log_size == 2:
                return "代码已编写完成，现在进行测试验证。"
            else:
                return "功能已验证通过，准备整理文档交付。"

        elif task_tool == "file_ops":
            return "汇总前面的分析结果，生成结构化的报告文件。"

        if self.working.current_task_index >= len(self.working.plan) - 1:
            return "已接近任务尾声，整理最终成果并准备提交。"

        return f"继续推进子任务，当前进度 {task_idx+1}/{len(self.working.plan)}。"

    def _decide_action(self, task: Dict, thought: str, use_live_llm: bool) -> tuple:
        """
        决策步骤

        布道者:
            将思考转化为具体行动。
            在 LLM 模式下，从输出中解析命令和参数。
            在模拟模式下，根据任务类型和进度做最优决策。
        """
        if use_live_llm and "ACTION:" in thought:
            return self._parse_action_from_thought(thought)

        # 规则决策
        task_tool = task.get("tool", "web_search")
        progress = self.working.get_progress()
        log_size = len(self.working.execution_log)

        # 搜索类工具
        if task_tool == "web_search":
            if log_size == 0:
                return ("web_search", {"query": self.working.goal, "max_results": 5})
            else:
                return ("file_ops", {"operation": "write", "path": f"research_{datetime.now():%Y%m%d}.md",
                                     "content": self._gen_research_report()})

        # 代码类工具
        elif task_tool == "code_exec":
            if log_size == 0:
                return ("web_search", {"query": f"{task['title']} 实现方案", "max_results": 3})
            elif log_size <= 2:
                return ("code_exec", {"code": self._gen_demo_code(task)})
            else:
                return ("file_ops", {"operation": "write", "path": "output.md",
                                     "content": self._gen_code_report(task)})

        # 文件类工具
        elif task_tool == "file_ops":
            return ("file_ops", {"operation": "write", "path": f"report_{datetime.now():%Y%m%d}.md",
                                 "content": self._gen_final_report()})

        # 默认: 如果还有子任务，推进
        if progress["completed_tasks"] < progress["total_tasks"] - 1:
            return ("web_search", {"query": task.get("title", self.working.goal), "max_results": 3})
        else:
            return ("finish", {"summary": self._gen_final_report()})

    def _parse_action_from_thought(self, thought: str) -> tuple:
        """从 LLM 输出中解析 ACTION 和 ARGUMENTS"""
        action_match = re.search(r'ACTION:\s*(\w+)', thought)
        args_match = re.search(r'ARGUMENTS:\s*({.*})', thought, re.DOTALL)
        action = action_match.group(1) if action_match else "web_search"
        try:
            arguments = json.loads(args_match.group(1)) if args_match else {}
        except json.JSONDecodeError:
            arguments = {"query": self.working.goal}
        return (action, arguments)

    def _act(self, action_name: str, params: Dict) -> ToolResult:
        """执行工具调用"""
        return self.registry.execute(action_name, **params)

    def _is_subtask_complete(self, task: Dict, result: ToolResult) -> bool:
        """判断子任务是否完成"""
        if not result.success and "失败" in result.content:
            return False
        criteria = task.get("criteria", "")
        if "报告" in criteria and "file_ops" in str(task.get("tool")):
            return "已写入" in result.content or "已写入文件" in str(result)
        if "运行" in criteria or "通过" in criteria:
            return result.success
        return result.success and len(self.working.execution_log) >= 3

    # ═══════════════════════════════════════════════
    # 阶段 3: 总结
    # ═══════════════════════════════════════════════

    def _summary_phase(self, use_live_llm: bool) -> str:
        """汇总执行结果"""
        log_summary = "\n".join([
            f"[步骤 {e['step']}] {e['action']}: {e['result'][:100]}"
            for e in self.working.execution_log
        ])
        if use_live_llm:
            return self._summarize_with_llm(log_summary)
        return self._summarize_simple(log_summary)

    def _summarize_with_llm(self, log: str) -> str:
        try:
            prompt = SUMMARY_PROMPT.format(goal=self.working.goal, execution_log=log)
            llm = self._get_llm()
            response = llm.invoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception:
            return self._summarize_simple(log)

    def _summarize_simple(self, log: str) -> str:
        success_count = sum(1 for e in self.working.execution_log if "成功" in str(e))
        return (
            f"## 任务总结\n\n"
            f"**目标**: {self.working.goal}\n\n"
            f"**执行概况**: 共 {len(self.working.plan)} 个子任务，"
            f"{self._iteration} 次迭代\n"
            f"**成功操作**: {success_count}/{len(self.working.execution_log)}\n\n"
            f"**关键产出**:\n"
            f"- 任务计划已分解为 {len(self.working.plan)} 步\n"
            f"- 已完成所有子任务\n"
            f"- 生成最终报告文件\n\n"
            f"(ℹ️ 使用 --live 参数可获得 LLM 驱动的详细总结)"
        )

    # ═══════════════════════════════════════════════
    # 阶段 4: 记忆持久化
    # ═══════════════════════════════════════════════

    def _persist_memory(self, goal: str, summary: str):
        self.long_memory.store(
            content=f"任务: {goal}\n\n{summary}",
            metadata={"goal": goal, "timestamp": datetime.now().isoformat(),
                       "iterations": self._iteration, "success": True},
        )
        # 同时保存检查点
        checkpoint_path = os.path.join(self.config.workspace_dir, f"checkpoint_{hash(goal) % 10000}.json")
        self.working.save_checkpoint(checkpoint_path)

    # ═══════════════════════════════════════════════
    # 模拟内容生成（Demo 用）
    # ═══════════════════════════════════════════════

    def _gen_research_report(self) -> str:
        goal = self.working.goal
        return (
            f"# 调研报告: {goal}\n\n"
            f"## 摘要\n本文档是针对 '{goal}' 的系统性调研结果。\n\n"
            f"## 关键发现\n"
            f"1. **现状**: 通过 web_search 获取了相关领域的最新信息\n"
            f"2. **趋势**: 识别了 3 个主要发展趋势\n"
            f"3. **建议**: 基于分析提供了 5 条行动建议\n\n"
            f"## 数据来源\n"
            f"- DuckDuckGo 搜索: 获取 {5} 条结果\n"
            f"- 代码分析: 通过 Python 脚本进行数据处理\n\n"
            f"## 结论\n综合以上分析，建议优先关注领域内的最新进展，"
            f"结合实际需求制定实施计划。\n\n"
            f"---\n*生成时间: {datetime.now()}*\n"
            f"*生成者: AutoGPT Demo Agent*"
        )

    def _gen_demo_code(self, task: Dict) -> str:
        title = task.get("title", "example")
        return (
            f"# 任务: {title}\n"
            f"print('正在执行: {title}')\n\n"
            f"# 数据处理示例\n"
            f"data = {{'task': '{title}', 'status': 'completed', 'items': [1,2,3,4,5]}}\n"
            f"print(f'处理结果: {{data}}')\n"
            f"print(f'数据摘要: 共 {{len(data)}} 个字段')\n"
        )

    def _gen_code_report(self, task: Dict) -> str:
        return (
            f"# 代码实现报告\n\n"
            f"## 任务: {task['title']}\n"
            f"## 实现状态: ✅ 完成\n\n"
            f"### 代码输出\n```\n"
            f">>> 正在执行: {task['title']}\n"
            f">>> 处理结果: 共 3 个字段\n"
            f"```\n\n"
            f"### 验证结果\n- 代码可运行 ✅\n- 输出符合预期 ✅\n"
        )

    def _gen_final_report(self) -> str:
        plan_summary = "\n".join([
            f"{i+1}. {t['title']} - {t['criteria']}"
            for i, t in enumerate(self.working.plan)
        ])
        return (
            f"# AutoGPT 执行报告\n\n"
            f"## 目标\n{self.working.goal}\n\n"
            f"## 任务计划\n{plan_summary}\n\n"
            f"## 执行统计\n"
            f"- 总迭代次数: {self._iteration}\n"
            f"- 操作步骤: {len(self.working.execution_log)}\n"
            f"- 执行时间: {datetime.now()}\n\n"
            f"## 结论\n所有子任务已完成，成果已保存到 workspace 目录。\n\n"
            f"---\n*AutoGPT Demo Agent — 布道者*"
        )
