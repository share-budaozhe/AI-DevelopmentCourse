"""
防御模块 3：Tool Execution Sandbox（工具执行沙箱）

第三道防线——当一个 LLM Agent 需要调用外部工具时，
所有工具调用都必须经过沙箱的审批和参数校验。

核心策略：
1. 最小权限 —— 每个工具只暴露必要的操作
2. 参数白名单 —— 对工具参数进行严格类型和范围校验
3. 调用审批（Human-in-the-loop）—— 高风险操作需人工确认
4. 审计日志 —— 记录所有工具调用
5. 速率限制 —— 防止工具调用滥用
"""
import hashlib
import json
from typing import Dict, Callable, List, Optional, Any


class ActionRisk:
    """风险等级定义"""
    LOW = "low"           # 只读、无副作用（如搜索、查询）
    MEDIUM = "medium"     # 有轻微副作用（如发邮件、创建记录）
    HIGH = "high"         # 有重要副作用（如修改数据、发起退款）
    CRITICAL = "critical" # 不可逆操作（如删除账户、执行命令）


class SandboxRule:
    """沙箱规则定义"""

    def __init__(
        self,
        tool_name: str,
        max_calls_per_session: int = 10,
        max_calls_per_minute: int = 3,
        require_approval: bool = False,
        allowed_params: dict = None,
        blocked_values: List[str] = None,
    ):
        self.tool_name = tool_name
        self.max_calls_per_session = max_calls_per_session
        self.max_calls_per_minute = max_calls_per_minute
        self.require_approval = require_approval
        self.allowed_params = allowed_params or {}
        self.blocked_values = blocked_values or []


class ToolSandbox:
    """工具执行沙箱"""

    def __init__(self):
        self.rules: Dict[str, SandboxRule] = {}
        self.call_history: List[Dict] = []
        self.audit_log: List[Dict] = []
        self._setup_default_rules()

    def _setup_default_rules(self):
        """配置默认沙箱规则"""
        # 只读工具：宽松
        self.rules["search_knowledge"] = SandboxRule(
            tool_name="search_knowledge",
            max_calls_per_session=50,
            max_calls_per_minute=10,
            require_approval=False,
        )
        self.rules["query_order"] = SandboxRule(
            tool_name="query_order",
            max_calls_per_session=20,
            max_calls_per_minute=5,
            require_approval=False,
        )

        # 中等风险：需验证
        self.rules["send_email"] = SandboxRule(
            tool_name="send_email",
            max_calls_per_session=10,
            max_calls_per_minute=3,
            require_approval=True,  # 发邮件需要审批
            blocked_values=["admin@", "root@", "/etc/passwd"],
        )

        # 高风险：严格限制
        self.rules["refund_order"] = SandboxRule(
            tool_name="refund_order",
            max_calls_per_session=3,
            max_calls_per_minute=1,
            require_approval=True,  # 必须人工审批
            allowed_params={
                "order_id": {"type": "str", "pattern": r"^#[A-Z0-9]{4,10}$"},
                "amount": {"type": "float", "min": 0, "max": 100000},
                "reason": {"type": "str", "max_length": 500},
            },
        )

        # 关键风险：禁止自动执行
        self.rules["execute_command"] = SandboxRule(
            tool_name="execute_command",
            max_calls_per_session=0,  # 完全禁止
            max_calls_per_minute=0,
            require_approval=True,
        )
        self.rules["delete_user"] = SandboxRule(
            tool_name="delete_user",
            max_calls_per_session=0,
            max_calls_per_minute=0,
            require_approval=True,
        )

    def check(self, tool_name: str, params: dict, session_id: str) -> Dict[str, Any]:
        """
        检查工具调用是否允许

        返回:
            {
                "allowed": bool,
                "reason": str,
                "need_approval": bool，
                "sanitized_params": dict,  # 清洗后的参数
            }
        """
        rule = self.rules.get(tool_name)
        if not rule:
            # 未注册的工具——默认禁止
            self._log(tool_name, params, session_id, "DENIED", "工具未在沙箱注册")
            return {
                "allowed": False,
                "reason": f"工具 '{tool_name}' 未在白名单中，禁止调用",
                "need_approval": False,
                "sanitized_params": params,
            }

        # 检查调用频率
        if rule.max_calls_per_session == 0:
            self._log(tool_name, params, session_id, "DENIED", "该工具被禁止直接调用")
            return {
                "allowed": False,
                "reason": f"工具 '{tool_name}' 禁止程序化调用，需走人工审批通道",
                "need_approval": True,
                "sanitized_params": params,
            }

        session_calls = sum(
            1 for c in self.call_history
            if c["tool"] == tool_name and c["session"] == session_id
        )
        if session_calls >= rule.max_calls_per_session:
            self._log(tool_name, params, session_id, "DENIED", "调用次数超限")
            return {
                "allowed": False,
                "reason": f"工具 '{tool_name}' 本会话调用次数已达上限 ({rule.max_calls_per_session})",
                "need_approval": False,
                "sanitized_params": params,
            }

        # 参数白名单校验
        for pname, prule in rule.allowed_params.items():
            if pname in params:
                value = params[pname]
                if prule["type"] == "float":
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        self._log(tool_name, params, session_id, "DENIED", f"参数 {pname} 类型错误")
                        return {"allowed": False, "reason": f"参数 {pname} 必须是数字", "need_approval": False, "sanitized_params": params}
                    if "min" in prule and value < prule["min"]:
                        return {"allowed": False, "reason": f"参数 {pname} 低于最小值 {prule['min']}", "need_approval": False, "sanitized_params": params}
                    if "max" in prule and value > prule["max"]:
                        return {"allowed": False, "reason": f"参数 {pname} 超出最大值 {prule['max']}", "need_approval": False, "sanitized_params": params}
                    params[pname] = value  # cast 回
                elif prule["type"] == "str":
                    value = str(value)
                    if "pattern" in prule and not re.match(prule["pattern"], value):
                        self._log(tool_name, params, session_id, "DENIED", f"参数 {pname} 格式不符")
                        return {"allowed": False, "reason": f"参数 {pname} 格式不符合要求", "need_approval": False, "sanitized_params": params}

        # 检查禁止值
        for pname, pvalue in params.items():
            str_value = str(pvalue)
            for blocked in rule.blocked_values:
                if blocked.lower() in str_value.lower():
                    self._log(tool_name, params, session_id, "DENIED", f"参数包含禁止值 '{blocked}'")
                    return {"allowed": False, "reason": f"参数包含被禁止的值", "need_approval": False, "sanitized_params": params}

        # 记录调用
        self.call_history.append({"tool": tool_name, "session": session_id})
        self._log(tool_name, params, session_id, "ALLOWED" if not rule.require_approval else "PENDING_APPROVAL", "")

        return {
            "allowed": True,
            "reason": "通过沙箱检查" + ("，需人工确认" if rule.require_approval else ""),
            "need_approval": rule.require_approval,
            "sanitized_params": params,
        }

    def _log(self, tool: str, params: dict, session: str, action: str, detail: str):
        self.audit_log.append({
            "timestamp": "2024-01-01T00:00:00Z",  # Demo 固定时间
            "tool": tool,
            "params_hash": hashlib.md5(json.dumps(params).encode()).hexdigest()[:8],
            "session": session[:8],
            "action": action,
            "detail": detail,
        })

    def get_audit_report(self) -> List[Dict]:
        """获取审计报告"""
        return self.audit_log


import re  # noqa: E402 (用于参数校验中的正则)
