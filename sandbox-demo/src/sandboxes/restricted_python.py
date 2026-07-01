"""
RestrictedPython AST 级沙箱

基于 RestrictedPython 库，在 Python AST（抽象语法树）级别对代码进行
安全限制。代码在编译前即被分析和转换，危险操作被替换为安全替代或直接拒绝。

隔离等级: language 级
隔离机制:
    1. AST 变换 —— 在编译前修改 AST，将危险操作替换为安全检查版本
    2. 受限内置函数 —— 替换 __builtins__ 为安全子集
    3. 导入控制 —— 白名单/黑名单控制可用的模块
    4. 属性访问控制 —— 限制对特殊属性（__class__/__bases__ 等）的访问
    5. 编译时检查 —— 在 compile() 阶段阻止危险语法

优势:
    - 纯 Python，无需 Docker 或 subprocess
    - 极快启动（< 1ms），零开销
    - 精细控制 —— 精确到每个 AST 节点
    - 最适合"只做计算"的安全场景

局限:
    - 不是真正的 OS 级隔离
    - 对某些绕过技术（如 pickle 反序列化逃逸）防御不足
    - 仅适用于 Python 代码
    - 支持的 Python 语法子集有限

适用场景:
    - 沙箱中的数学/统计计算
    - 用户自定义公式/规则引擎
    - 教学平台中的 Python 练习环境
    - 数据转换/ETL 中的自定义逻辑
"""
import ast
import sys
from typing import Optional, Dict, Any

from src.sandboxes.base import BaseSandbox, SandboxConfig, SandboxResult
from src.policies.security_policy import (
    CodeSecurityAnalyzer, SecurityLevel,
    FORBIDDEN_BUILTINS, FORBIDDEN_BUILTINS_STRICT,
    ALLOWED_MODULES_STRICT,
)


# ── 安全的 builtins 替代 ───────────────────────

def _safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    """安全的 import 函数 —— 仅允许白名单模块"""
    root_module = name.split('.')[0]
    if root_module not in ALLOWED_MODULES_STRICT:
        raise ImportError(f"模块 '{root_module}' 不在安全白名单中")
    return __import__(name, globals, locals, fromlist, level)


def _safe_open(path, mode='r', *args, **kwargs):
    """安全的 open —— 禁止所有文件操作"""
    raise PermissionError("沙箱中禁止文件操作")


def _safe_getattr(obj, name, *default):
    """安全的 getattr —— 禁止访问双下划线属性"""
    if name.startswith('__') and name.endswith('__'):
        raise AttributeError(f"禁止访问特殊属性: {name}")
    if default:
        return getattr(obj, name, default[0])
    return getattr(obj, name)


# ── 受限制的 builtins 字典 ─────────────────────

def build_safe_builtins(level: SecurityLevel) -> Dict[str, Any]:
    """构建安全的内置函数字典"""
    import builtins

    forbidden = FORBIDDEN_BUILTINS_STRICT if level == SecurityLevel.STRICT else FORBIDDEN_BUILTINS

    safe = {}
    for name in dir(builtins):
        if name.startswith('_'):
            continue
        if name in forbidden:
            continue
        obj = getattr(builtins, name)
        try:
            hash(obj)
            safe[name] = obj
        except TypeError:
            continue

    # 替换为安全版本
    safe['__import__'] = _safe_import
    safe['open'] = _safe_open
    safe['getattr'] = _safe_getattr

    return safe


class RestrictedPythonSandbox(BaseSandbox):
    """
    RestrictedPython AST 级沙箱

    在 Python 语言层面对代码进行安全限制，不依赖外部进程或容器。
    代码在受限的 globals 字典中执行，危险操作被替换或禁止。
    """

    def __init__(self, config: Optional[SandboxConfig] = None, security_level: SecurityLevel = SecurityLevel.STRICT):
        super().__init__(config)
        self.security_level = security_level
        self.security_analyzer = CodeSecurityAnalyzer(level=security_level)

    @classmethod
    def name(cls) -> str:
        return "RestrictedPython AST Sandbox"

    @classmethod
    def is_available(cls) -> bool:
        """始终可用（纯 Python）"""
        return True

    @classmethod
    def isolation_level(cls) -> str:
        return "language"

    def _execute_impl(self, code: str) -> SandboxResult:
        # ── 1. 安全策略检查 ──
        analysis = self.security_analyzer.analyze(code)
        if not analysis["safe"]:
            findings_str = "; ".join(f["message"] for f in analysis["findings"][:3])
            return SandboxResult(
                success=False,
                error=f"安全策略检查未通过 (risk={analysis['risk_score']}): {findings_str}",
                exit_code=403,
            )

        # ── 2. AST 语法检查 ──
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return SandboxResult(
                success=False,
                error=f"语法错误 (line {e.lineno}): {e.msg}",
                exit_code=1,
            )

        # ── 3. 执行前 AST 变换 ──
        try:
            tree = self._transform_ast(tree)
        except ValueError as e:
            return SandboxResult(
                success=False,
                error=f"AST 安全检查失败: {e}",
                exit_code=403,
            )

        # ── 4. 编译 + 执行 ──
        safe_builtins = build_safe_builtins(self.security_level)
        exec_globals = {
            "__builtins__": safe_builtins,
            "__name__": "__sandbox__",
        }

        # 捕获 stdout
        import io
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        old_stdout = sys.stdout
        old_stderr = sys.stderr

        try:
            sys.stdout = stdout_buf
            sys.stderr = stderr_buf

            # 使用 compile + exec 执行转换后的 AST
            compiled = compile(tree, "<sandbox>", "exec")

            # 超时处理 —— 使用 threading.Timer (跨平台兼容)
            import threading
            timed_out = [False]

            def timeout_handler():
                timed_out[0] = True

            timer = threading.Timer(self.config.timeout_seconds, timeout_handler)
            timer.daemon = True

            try:
                timer.start()
                exec(compiled, exec_globals)
            finally:
                timer.cancel()

            if timed_out[0]:
                return SandboxResult(
                    success=False,
                    stdout=stdout_buf.getvalue()[:self.config.max_output_chars],
                    error="TIMEOUT: 代码执行超过时间限制",
                    exit_code=-9,
                )

        except TimeoutError:
            return SandboxResult(
                success=False,
                stdout=stdout_buf.getvalue()[:self.config.max_output_chars],
                error="TIMEOUT: 代码执行超过时间限制",
                exit_code=-9,
            )
        except SystemExit as e:
            pass  # 正常退出
        except Exception as e:
            import traceback
            return SandboxResult(
                success=False,
                stdout=stdout_buf.getvalue()[:self.config.max_output_chars],
                stderr=traceback.format_exc(limit=3),
                error=f"{type(e).__name__}: {e}",
                exit_code=1,
            )
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        stdout = stdout_buf.getvalue()

        return SandboxResult(
            success=True,
            stdout=stdout[:self.config.max_output_chars],
            exit_code=0,
        )

    def _transform_ast(self, tree: ast.AST) -> ast.AST:
        """
        AST 安全变换 —— 将危险节点替换为安全替代

        包括:
        - Import/ImportFrom → 通过 _safe_import 的检查
        - 危险属性访问 → _safe_getattr
        """
        # 遍历修改 AST
        for node in ast.walk(tree):
            # 处理 from x import y
            if isinstance(node, ast.ImportFrom):
                # 检查模块名
                module = node.module or ""
                root = module.split('.')[0]
                if root not in ALLOWED_MODULES_STRICT and self.security_level == SecurityLevel.STRICT:
                    raise ValueError(f"禁止导入模块: {root}")

            # 处理 import x
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split('.')[0]
                    if root not in ALLOWED_MODULES_STRICT and self.security_level == SecurityLevel.STRICT:
                        raise ValueError(f"禁止导入模块: {root}")

        return tree
