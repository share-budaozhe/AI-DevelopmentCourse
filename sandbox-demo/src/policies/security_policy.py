"""
安全策略模块 — 定义代码执行的安全边界

策略引擎采用多层检查架构:
    1. AST 静态分析    — 编译时检测危险语法结构
    2. 导入白名单/黑名单 — 控制可用的模块
    3. 内置函数控制     — 禁用/替换危险内置函数
    4. 模式匹配        — 检测 shell 注入/路径遍历等

安全等级:
    STRICT  — 纯计算，无 I/O，无导入，无副作用
    STANDARD — 允许安全的内置模块，有限 I/O
    RELAXED — 允许大部分操作，仅阻止明确的危险操作
"""
import ast
import re
import sys
from enum import Enum
from typing import Set, List, Dict, Optional


class SecurityLevel(Enum):
    STRICT = "strict"       # 纯计算沙箱（数学/字符串操作）
    STANDARD = "standard"   # 标准沙箱（允许安全模块）
    RELAXED = "relaxed"     # 宽松沙箱（仅阻止明确危险）


# ── 危险模块黑名单 ──────────────────────────────

FORBIDDEN_MODULES_STRICT: Set[str] = {
    # 所有 I/O 和系统模块
    "os", "sys", "subprocess", "shutil", "pathlib",
    "socket", "requests", "urllib", "http", "ftp",
    "pickle", "marshal", "shelve",
    "ctypes", "cffi", "multiprocessing", "threading",
    "importlib", "pkgutil", "inspect",
    "signal", "atexit",
    "builtins", "__builtins__",
}

FORBIDDEN_MODULES_STANDARD: Set[str] = {
    "os", "subprocess", "shutil",
    "socket", "requests", "urllib.request",
    "pickle", "marshal",
    "ctypes", "cffi", "multiprocessing",
    "signal",
}

# 安全白名单（STRICT 模式仅允许的模块）
ALLOWED_MODULES_STRICT: Set[str] = {
    "math", "cmath", "decimal", "fractions",
    "random", "statistics",
    "json",
    "datetime", "calendar",
    "collections", "itertools", "functools",
    "re", "string", "textwrap",
    "typing", "dataclasses",
    "hashlib", "base64",
}


# ── 危险内置函数 ───────────────────────────────

FORBIDDEN_BUILTINS: Set[str] = {
    "eval", "exec", "compile", "__import__",
    "open", "input",
    "globals", "locals", "vars",
    "getattr", "setattr", "delattr",
    "breakpoint",
    "memoryview",
    "help",
}

# STRICT 模式额外禁止
FORBIDDEN_BUILTINS_STRICT: Set[str] = FORBIDDEN_BUILTINS | {
    "print", "format",
    "id", "hash",
    "object", "type", "isinstance", "issubclass",
    "super", "staticmethod", "classmethod",
    "enumerate", "zip", "map", "filter", "sorted",
    "reversed", "all", "any",
}


# ── 危险 AST 节点类型 ──────────────────────────

FORBIDDEN_AST_NODES: Set[str] = set()
# STANDARD 级别只禁止 AST 级别危险的语法（不禁止 import）

FORBIDDEN_AST_NODES_STRICT: Set[str] = {
    "Import",      # import x
    "ImportFrom",  # from x import y
    "Global",      # global x
    "Nonlocal",    # nonlocal x
    "ClassDef",    # class X:
    "AsyncFunctionDef",  # async def
    "Await",       # await
    "Yield",       # yield
    "YieldFrom",   # yield from
}

# 危险函数调用（AST 级别的 Call 匹配）
DANGEROUS_CALL_PATTERNS: List[str] = [
    r"eval\s*\(",
    r"exec\s*\(",
    r"compile\s*\(",
    r"__import__\s*\(",
    r"open\s*\(",
    r"os\.system\s*\(",
    r"os\.popen\s*\(",
    r"subprocess\.",
    r"os\.remove\s*\(",
    r"os\.unlink\s*\(",
    r"os\.rmdir\s*\(",
    r"shutil\.rmtree",
    r"os\.chmod\s*\(",
    r"os\.chown\s*\(",
    r"requests\.(get|post|put|delete|patch)\s*\(",
    r"socket\.",
]


class CodeSecurityAnalyzer:
    """
    代码安全分析器 — 多层检查流水线
    """

    def __init__(self, level: SecurityLevel = SecurityLevel.STANDARD):
        self.level = level

    def analyze(self, code: str) -> Dict:
        """
        分析代码安全性

        返回:
            {
                "safe": bool,
                "findings": List[Dict],    # 每项: {level, type, line, message}
                "risk_score": int,         # 0-100
            }
        """
        findings = []
        risk_score = 0

        # ── 1. AST 静态分析 ──
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {
                "safe": False,
                "findings": [{"level": "CRITICAL", "type": "SyntaxError",
                              "line": e.lineno, "message": str(e)}],
                "risk_score": 100,
            }

        # 遍历 AST 节点
        ast_findings = self._check_ast(tree)
        findings.extend(ast_findings)
        risk_score += sum(20 if f["level"] == "CRITICAL" else
                          10 if f["level"] == "HIGH" else 5
                          for f in ast_findings)

        # ── 2. 导入检查 ──
        import_findings = self._check_imports(code)
        findings.extend(import_findings)
        risk_score += sum(25 if f["level"] == "CRITICAL" else
                          10 if f["level"] == "HIGH" else 5
                          for f in import_findings)

        # ── 3. 危险函数调用检查 ──
        call_findings = self._check_dangerous_calls(code)
        findings.extend(call_findings)
        risk_score += sum(30 if f["level"] == "CRITICAL" else 15
                          for f in call_findings)

        # ── 4. Shell 注入/路径遍历 ──
        injection_findings = self._check_injection_patterns(code)
        findings.extend(injection_findings)
        risk_score += sum(25 for _ in injection_findings)

        risk_score = min(risk_score, 100)
        safe = risk_score == 0

        return {
            "safe": safe,
            "findings": findings,
            "risk_score": risk_score,
        }

    # ── AST 检查 ───────────────────────────────

    def _check_ast(self, tree: ast.AST) -> List[Dict]:
        findings = []
        forbidden = (FORBIDDEN_AST_NODES_STRICT if self.level == SecurityLevel.STRICT
                     else FORBIDDEN_AST_NODES if self.level == SecurityLevel.STANDARD
                     else set())

        for node in ast.walk(tree):
            node_type = type(node).__name__
            if node_type in forbidden:
                findings.append({
                    "level": "CRITICAL" if node_type in ("Import", "ImportFrom") else "HIGH",
                    "type": f"ForbiddenAST:{node_type}",
                    "line": getattr(node, "lineno", 0),
                    "message": f"禁止使用的语法结构: {node_type}",
                })
        return findings

    # ── 导入检查 ───────────────────────────────

    def _check_imports(self, code: str) -> List[Dict]:
        findings = []
        import_re = re.compile(
            r'(?:from\s+(\S+)\s+import|import\s+(\S+))',
            re.MULTILINE,
        )
        for match in import_re.finditer(code):
            module = (match.group(1) or match.group(2)).split('.')[0]
            if self.level == SecurityLevel.STRICT:
                if module not in ALLOWED_MODULES_STRICT:
                    findings.append({
                        "level": "CRITICAL",
                        "type": "ForbiddenImport",
                        "line": 0,
                        "message": f"STRICT 模式禁止导入模块: {module}",
                    })
            elif module in (FORBIDDEN_MODULES_STRICT if self.level == SecurityLevel.STRICT
                            else FORBIDDEN_MODULES_STANDARD):
                findings.append({
                    "level": "CRITICAL",
                    "type": "ForbiddenImport",
                    "line": 0,
                    "message": f"禁止导入危险模块: {module}",
                })
        return findings

    # ── 危险调用检查 ───────────────────────────

    def _check_dangerous_calls(self, code: str) -> List[Dict]:
        findings = []
        for pattern in DANGEROUS_CALL_PATTERNS:
            for match in re.finditer(pattern, code, re.IGNORECASE):
                findings.append({
                    "level": "CRITICAL",
                    "type": "DangerousCall",
                    "line": code[:match.start()].count('\n') + 1,
                    "message": f"检测到危险函数调用: {match.group(0)[:50]}",
                })
        return findings

    # ── 注入模式检查 ───────────────────────────

    def _check_injection_patterns(self, code: str) -> List[Dict]:
        findings = []
        injection_patterns = [
            (r"rm\s+-rf\s+/", "Shell: 递归根目录删除"),
            (r">\s*/dev/\w+", "Shell: 设备文件重定向"),
            (r"curl\s+.*\|\s*(ba)?sh", "Shell: 远程脚本管道执行"),
            (r"wget\s+.*-O\s*-", "Shell: wget 下载到管道"),
            (r"\.\.\/\.\.\/", "Path: 路径遍历"),
            (r"chr\(\s*\d+\s*\)\s*\.\s*join", "Obfuscation: chr join 混淆"),
            (r"base64\..*decode", "Obfuscation: base64 解码"),
        ]
        for pattern, desc in injection_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                findings.append({
                    "level": "CRITICAL",
                    "type": "InjectionPattern",
                    "line": 0,
                    "message": f"检测到攻击模式: {desc}",
                })
        return findings
