"""
防御模块 1：Input Filter（输入过滤器）

第一道防线——在用户输入到达 LLM 之前进行检测和过滤。

核心策略：
1. 关键词/模式检测 —— 识别常见攻击特征
2. 语义分析 —— 检测意图（注入、越狱、数据提取）
3. 规范化 + 重检测 —— Unicode 标准化后再次检测
4. Rate Limiting —— 限制请求频率
5. 长度限制 —— 防止超长/过载式攻击

设计原则：
- 宁可误拦（false positive）不可漏放（false negative）
- 误拦的用户可以通过正常渠道申诉
- 所有拦截事件记录到安全日志
"""
import re
import unicodedata
from typing import Dict, List


class InputFilter:
    """LLM 输入安全过滤器"""

    # 高危模式 —— 匹配任一即拦截
    CRITICAL_PATTERNS: List[str] = [
        # 指令覆盖
        r"(忽略|忘记|无视|覆盖).{0,10}(所有|全部|一切).{0,10}(指令|规则|限制|约束)",
        r"(ignore|forget|disregard|override).{0,10}(all|previous|above).{0,10}(instruction|rule|constraint)",
        r"(你现在是|you are now|you're now).{0,20}(不需要|不必|无需).{0,10}(遵守|遵循|服从)",
        # ADMIN 前缀劫持
        r"(^|\n)\s*ADMIN\s*[:：]",
        r"(^|\n)\s*\[系统消息\]",
        r"(^|\n)\s*---\s*SYSTEM\s*OVERRIDE\s*---",
        # 提示词提取
        r"(显示|输出|告诉我|打印|重复|复述|返回).{0,15}(提示词|prompt|系统指令|system message)",
        r"(what|show|print|repeat).{0,10}(your|the).{0,10}(system prompt|instructions)",
        # 代码/命令注入
        r"(import\s+(os|subprocess|sys|shutil|requests)\b)",
        r"(rm\s+-rf|DROP\s+TABLE|DELETE\s+FROM|shutdown\s)",
        r"(eval\s*[\(（]|exec\s*[\(（])",
        # 解码类攻击
        r"(base64|解码|decrypt|解密).{0,20}(执行|运行|命令|攻击)",
    ]

    # 中危模式 —— 组合出现时拦截
    WARNING_PATTERNS: List[str] = [
        r"DAN\s*(模式|mode)?",
        r"进入开发者模式",
        r"角色扮演",
        r"你不再是一?个?\w*助手",
        r"filter\s*=\s*0",
        r"(sudo|root|admin).*(权限|access)",
        r"(SELECT|INSERT|UPDATE|DELETE)\s.*\bFROM\b",
        r"(密码|password|token|api.?key|secret)",
        r"(系统配置|内部|internal|config)",
        r"紧急.*模式",
    ]

    # 可疑 Unicode 字符范围
    SUSPICIOUS_UNICODE = [
        (0x200B, 0x200F),   # 零宽字符
        (0x2028, 0x202E),   # 行分隔符/方向覆盖
        (0x2060, 0x2064),   # 单词连接符/不可见字符
        (0xFE00, 0xFE0F),   # 变体选择器
        (0xFFF0, 0xFFFF),   # 特殊区域
    ]

    def check(self, text: str) -> Dict:
        """
        检查用户输入，返回判定结果

        返回:
            {
                "blocked": bool,           # 是否拦截
                "attack_type": str|None,   # 攻击类型
                "reason": str,             # 判定理由
                "matches": List[str],      # 匹配到的模式
            }
        """
        matches = []
        original = text

        # Step 1: Unicode 规范化（NFKC：兼容性分解 + 组合）
        text = unicodedata.normalize("NFKC", text)

        # Step 2: 检测可疑 Unicode 字符
        for char in text:
            cp = ord(char)
            for low, high in self.SUSPICIOUS_UNICODE:
                if low <= cp <= high:
                    return {
                        "blocked": True,
                        "attack_type": "Unicode 混淆攻击",
                        "reason": f"检测到可疑 Unicode 字符 U+{cp:04X}",
                        "matches": [f"U+{cp:04X}"],
                    }

        # Step 3: 检查高危模式（匹配任一即拦截）
        for pattern in self.CRITICAL_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                matched_text = match.group(0)[:80]
                return {
                    "blocked": True,
                    "attack_type": self._classify(pattern),
                    "reason": f"匹配高危安全规则：'{matched_text}'",
                    "matches": [matched_text],
                }

        # Step 4: 检查中危模式（出现 ≥2 个才拦截）
        for pattern in self.WARNING_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                matches.append(match.group(0)[:80])

        if len(matches) >= 2:
            return {
                "blocked": True,
                "attack_type": "多重可疑模式",
                "reason": f"同时检测到 {len(matches)} 个可疑特征",
                "matches": matches,
            }

        if len(matches) == 1:
            return {
                "blocked": True,
                "attack_type": self._classify(matches[0]),
                "reason": f"检测到可疑输入特征：'{matches[0]}'",
                "matches": matches,
            }

        # Step 5: 长度检查（防止上下文过载攻击）
        if len(original) > 10000:
            return {
                "blocked": True,
                "attack_type": "上下文过载",
                "reason": f"输入过长（{len(original)} 字符），超过安全限制",
                "matches": [],
            }

        return {"blocked": False, "attack_type": None, "reason": "通过安全检查", "matches": []}

    def _classify(self, text: str) -> str:
        """根据匹配文本分类攻击类型"""
        if any(kw in text.lower() for kw in ["忽略", "忘记", "ignore", "forget", "覆盖", "override"]):
            return "Prompt Injection - 指令覆盖"
        if "ADMIN" in text or "系统消息" in text:
            return "Prompt Injection - 身份伪造"
        if any(kw in text.lower() for kw in ["提示词", "prompt", "系统指令", "system message"]):
            return "提示词提取攻击"
        if any(kw in text.lower() for kw in ["import", "eval", "exec", "rm ", "drop"]):
            return "代码/命令注入攻击"
        if any(kw in text.lower() for kw in ["dan", "开发者模式", "角色扮演"]):
            return "Jailbreak 越狱攻击"
        if any(kw in text.lower() for kw in ["密码", "password", "token", "secret"]):
            return "敏感信息探测"
        return "可疑输入"
