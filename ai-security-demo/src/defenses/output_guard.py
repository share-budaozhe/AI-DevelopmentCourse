"""
防御模块 2：Output Guard（输出审查器）

第二道防线——在 LLM 生成输出后、返回给用户前进行安全审查。

核心策略：
1. 敏感信息检测 —— PII、API Key、Token、内部 IP
2. 提示词泄露检测 —— 模型是否输出了系统提示词
3. 有害内容过滤 —— 暴力/色情/仇恨/违法行为
4. 格式验证 —— 检测异常输出格式
5. 输出改写 —— 对可疑内容进行安全化处理

设计原则：
- 输出审查不能完全依赖 LLM 自查
- 正则 + 规则引擎作为兜底
- 敏感数据一经发现立即替换
"""
import re
from typing import Dict, List, Tuple


class OutputGuard:
    """LLM 输出安全审查器"""

    # 敏感信息检测规则（正则 → 替换）
    PII_PATTERNS: List[Tuple[str, str, str]] = [
        # (名称, 正则, 替换为)
        ("中国大陆身份证号", r"\b[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b", "[身份证号已脱敏]"),
        ("中国大陆手机号",  r"\b1[3-9]\d{9}\b", "[手机号已脱敏]"),
        ("邮箱地址",        r"\b[\w.%+-]+@[\w.-]+\.[A-Za-z]{2,}\b", "[邮箱已脱敏]"),
        ("IP 地址",         r"\b(?:10\.|172\.(?:1[6-9]|2\d|3[01])\.|192\.168\.)\d{1,3}\.\d{1,3}\b", "[内网IP已脱敏]"),
        ("API Key 格式",    r"\b(sk-[A-Za-z0-9\-]{20,})\b", "[API_KEY已脱敏]"),
    ]

    # 危险内容模式
    DANGEROUS_CONTENT: List[str] = [
        r"(暴力|爆炸物|武器|暗杀|绑架).*(制作|制造|教程|步骤|方法)",
        r"(毒品|鸦片|海洛因|冰毒).*(制作|合成|配方)",
        r"(儿童|未成年人).*(色情|性行为|裸照)",
    ]

    # 提示词泄露标识
    PROMPT_LEAK_INDICATORS: List[str] = [
        r"(系统提示词|system prompt|系统指令).{0,30}[是为：:]",
        r"以下是.{0,10}(系统提示词|system prompt)",
        r"ORDER_DB|内部系统|internal",
    ]

    def review(self, output: str, user_input: str = "") -> Dict:
        """
        审查 LLM 输出

        返回:
            {
                "sanitized": bool,          # 是否被处理
                "safe_response": str,       # 安全化后的响应
                "leak_type": str|None,      # 泄露类型
                "reason": str,              # 理由
                "findings": List[str],      # 发现的问题
            }
        """
        findings = []
        safe = output

        # ── 1. 提示词泄露检测 ──
        for pattern in self.PROMPT_LEAK_INDICATORS:
            if re.search(pattern, safe, re.IGNORECASE):
                findings.append("提示词泄露")
                safe = self._leak_response("提示词内容")
                break

        # ── 2. 敏感信息脱敏 ──
        for name, pattern, replacement in self.PII_PATTERNS:
            matches = re.findall(pattern, safe)
            if matches:
                findings.append(f"检测到 {name}: {len(matches)} 处")
                safe = re.sub(pattern, replacement, safe)

        # ── 3. 危险内容检测 ──
        for pattern in self.DANGEROUS_CONTENT:
            if re.search(pattern, safe, re.IGNORECASE):
                findings.append("检测到危险内容")
                safe = "抱歉，我无法提供此类信息。如果你遇到安全问题，请联系相关部门。"
                break

        # ── 4. 代码块中的敏感内容 ──
        code_blocks = re.findall(r"```[\s\S]*?```", safe)
        for block in code_blocks:
            # 检查代码块中是否有明显的恶意代码
            if re.search(r"(os\.system|subprocess\.call|eval\(|exec\(|rm\s+-rf)", block):
                findings.append("代码块包含潜在恶意代码")
                safe = safe.replace(block, "```\n[代码块因安全原因已移除]\n```")

        if findings:
            return {
                "sanitized": True,
                "safe_response": safe,
                "leak_type": ", ".join(findings),
                "reason": f"输出审查发现 {len(findings)} 个问题，已进行安全处理",
                "findings": findings,
            }

        return {
            "sanitized": False,
            "safe_response": output,
            "leak_type": None,
            "reason": "通过输出审查",
            "findings": [],
        }

    def _leak_response(self, leak_type: str) -> str:
        """生成泄露拦截的回复"""
        return (
            f"（⚠️ 安全拦截：检测到输出中包含{leak_type}，已自动屏蔽。"
            f"此事件已记录到安全日志。）\n\n"
            f"抱歉，我无法提供此信息。有什么其他我可以帮助你的吗？"
        )
