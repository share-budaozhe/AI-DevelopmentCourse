"""
subprocess 资源限制沙箱

通过启动独立的 Python 子进程，并在子进程内部设置 OS 级资源限制
（RLIMIT + signal）来实现隔离执行。

隔离等级: process 级
隔离机制:
    1. 独立进程空间 —— 崩溃不影响主进程
    2. RLIMIT 资源限制 —— CPU/内存/文件/进程数硬限制
    3. 超时 kill —— 防止死循环/阻塞
    4. stdin/stdout 管道 —— 隔离 I/O
    5. 安全策略预检查 —— AST 分析 + 导入/调用黑名单

优势:
    - 无需 Docker，纯 Python 实现
    - 比 Docker 轻量，启动快（~50ms）
    - 跨平台（Windows/Linux/macOS）
    - 资源限制精细（CPU time / 内存 / 文件大小 / 进程数）

局限:
    - 进程级隔离 < 容器级隔离
    - RLIMIT_AS 在 Linux 上有效，Windows 上部分功能不可用
    - 无法阻止内核漏洞级别的逃逸
"""
import os
import sys
import signal
import textwrap
import tempfile
import time
from typing import Optional

from src.sandboxes.base import BaseSandbox, SandboxConfig, SandboxResult
from src.policies.security_policy import CodeSecurityAnalyzer, SecurityLevel
from src.monitor.resource_monitor import ResourceMonitor, ResourceLimits


# ── 子进程中运行的代码包装模板 ─────────────────

EXECUTION_TEMPLATE = '''
import sys, os, json, signal, traceback, time

# ══ RLIMIT 资源限制 ══
HAS_RESOURCE = False
try:
    import resource
    HAS_RESOURCE = True
except ImportError:
    pass

if HAS_RESOURCE:
    # CPU 时间限制 (秒)
    resource.setrlimit(resource.RLIMIT_CPU, ({cpu_limit}, {cpu_limit}))
    # 地址空间限制 (字节) — 需留解释器开销 (~100MB)
    resource.setrlimit(resource.RLIMIT_AS, ({mem_bytes}, {mem_bytes}))
    # 数据段限制
    resource.setrlimit(resource.RLIMIT_DATA, ({data_bytes}, {data_bytes}))
    # 进程数限制
    resource.setrlimit(resource.RLIMIT_NPROC, ({proc_limit}, {proc_limit}))
    # 文件大小限制
    resource.setrlimit(resource.RLIMIT_FSIZE, ({fsize_bytes}, {fsize_bytes}))
    # 文件描述符限制
    resource.setrlimit(resource.RLIMIT_NOFILE, ({fd_limit}, {fd_limit}))

    # CPU 超时信号处理器 (Unix only)
    try:
        def _cpu_timeout_handler(signum, frame):
            print(json.dumps({"success": False, "error": "CPU_TIME_EXCEEDED: 代码执行超过时间限制"}))
            sys.exit(1)
        signal.signal(signal.SIGXCPU, _cpu_timeout_handler)
    except AttributeError:
        pass  # Windows 不支持 SIGXCPU

# ══ Wall-Clock 超时 (跨平台兼容：Unix SIGALRM / Windows threading.Timer) ══
_timed_out = [False]
try:
    def _wall_timeout_handler(signum, frame):
        _timed_out[0] = True
        print(json.dumps({"success": False, "error": "WALL_TIME_EXCEEDED: 代码执行超时"}))
        sys.exit(1)
    signal.signal(signal.SIGALRM, _wall_timeout_handler)
    signal.alarm({wall_timeout})
except AttributeError:
    # Windows: 使用 threading.Timer
    import threading
    def _win_timeout():
        _timed_out[0] = True
        print(json.dumps({"success": False, "error": "WALL_TIME_EXCEEDED: 代码执行超时"}))
        sys.exit(1)
    _timer = threading.Timer({wall_timeout}, _win_timeout)
    _timer.daemon = True
    _timer.start()

# ══ 禁止写入安全模块 (防止绕过) ══
FORBIDDEN = [
    "os", "subprocess", "shutil", "socket", "ctypes", "pickle",
    "requests", "urllib", "http", "importlib", "signal",
]
for mod_name in FORBIDDEN:
    if mod_name in sys.modules:
        pass  # 已导入的无法卸载
    sys.modules[mod_name] = type(sys)(mod_name)
    sys.modules[mod_name].__spec__ = None

# ══ 重定向 I/O ══
_real_stdout = sys.stdout  # 保留原始 stdout 引用
class _SandboxStdout:
    """限制输出长度的安全 stdout —— 同时写入 buffer 和 pipe"""
    def __init__(self, max_chars={max_output}):
        self.buffer = []
        self.count = 0
        self.max_chars = max_chars
    def write(self, s):
        if self.count < self.max_chars:
            self.buffer.append(s)
            self.count += len(s)
        _real_stdout.write(s)  # 同时写入 pipe，使父进程可读
    def flush(self):
        _real_stdout.flush()
    def getvalue(self):
        return "".join(self.buffer)

_stdout = _SandboxStdout()
sys.stdout = _stdout
sys.stderr = _stdout

# ══ 执行用户代码 ══
_exit_code = 0
_result = {"success": False, "error": "", "exit_code": -1}
try:
    exec_globals = {"__builtins__": __builtins__, "__name__": "__sandbox__"}
    exec("""{code}""", exec_globals)
    _result["success"] = True
    _result["exit_code"] = 0
except SystemExit as e:
    _result["exit_code"] = e.code if e.code else 0
    _result["success"] = _result["exit_code"] == 0
    _result["error"] = str(e) if e.code else ""
except Exception as e:
    _result["error"] = f"{type(e).__name__}: {e}"
    _result["tb"] = traceback.format_exc(limit=5)
    _result["exit_code"] = 1
finally:
    _result["stdout"] = _stdout.getvalue()
    print(json.dumps(_result, ensure_ascii=False, default=str)[:{max_output}])
'''


class SubprocessSandbox(BaseSandbox):
    """
    Subprocess 资源限制沙箱

    通过 subprocess 启动子进程，在子进程中设置 OS 资源限制后执行代码。
    这是最轻量、最快、无外部依赖的沙箱方案。
    """

    def __init__(self, config: Optional[SandboxConfig] = None, security_level: SecurityLevel = SecurityLevel.STANDARD):
        super().__init__(config)
        self.security_analyzer = CodeSecurityAnalyzer(level=security_level)
        self.security_level = security_level

    @classmethod
    def name(cls) -> str:
        return "Subprocess Resource Sandbox"

    @classmethod
    def is_available(cls) -> bool:
        """始终可用（纯 Python + subprocess）"""
        return True

    @classmethod
    def isolation_level(cls) -> str:
        return "process"

    def _execute_impl(self, code: str) -> SandboxResult:
        # 安全策略预检查
        analysis = self.security_analyzer.analyze(code)
        if not analysis["safe"]:
            findings_str = "; ".join(f["message"] for f in analysis["findings"][:3])
            return SandboxResult(
                success=False,
                error=f"安全策略检查未通过 (risk={analysis['risk_score']}): {findings_str}",
                exit_code=403,
            )

        # 构建子进程执行的代码
        interpreter_overhead_mb = 120
        mem_limit_bytes = max(1, self.config.memory_limit_mb - interpreter_overhead_mb) * 1024 * 1024

        # 安全地替换模板中的占位符（避免 format() 对代码中 {} 的干扰）
        wrapped_code = EXECUTION_TEMPLATE
        # 转义代码中的三引号
        escaped_code = code.replace('\\', '\\\\').replace('"""', '\\"\\"\\"')
        wrapped_code = wrapped_code.replace('{code}', escaped_code)
        wrapped_code = wrapped_code.replace('{cpu_limit}', str(self.config.timeout_seconds))
        wrapped_code = wrapped_code.replace('{wall_timeout}', str(self.config.timeout_seconds + 2))
        wrapped_code = wrapped_code.replace('{mem_bytes}', str(mem_limit_bytes + interpreter_overhead_mb * 1024 * 1024))
        wrapped_code = wrapped_code.replace('{data_bytes}', str(mem_limit_bytes))
        wrapped_code = wrapped_code.replace('{proc_limit}', str(self.config.max_processes if self.config.allow_subprocesses else 0))
        wrapped_code = wrapped_code.replace('{fsize_bytes}', str(self.config.max_file_size_mb * 1024 * 1024))
        wrapped_code = wrapped_code.replace('{fd_limit}', str(256))
        wrapped_code = wrapped_code.replace('{max_output}', str(self.config.max_output_chars))

        # 写入临时文件
        tmp_path = None
        try:
            fd, tmp_path = tempfile.mkstemp(suffix=".py", prefix="sandbox_")
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(wrapped_code)

            import subprocess
            # 启动子进程
            proc = subprocess.Popen(
                [sys.executable, "-S", tmp_path],  # -S 禁止 site-packages
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )

            # 等待 + 超时 kill
            try:
                stdout, _ = proc.communicate(timeout=self.config.timeout_seconds + 5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                return SandboxResult(
                    success=False,
                    error="WALL_TIME_EXCEEDED: 代码执行超时，进程已被强制终止",
                    exit_code=-9,
                )

            # 解析 JSON 结果
            import json
            try:
                last_line = stdout.strip().split('\n')[-1] if stdout.strip() else "{}"
                data = json.loads(last_line)
            except json.JSONDecodeError:
                return SandboxResult(
                    success=False,
                    stdout=stdout[:self.config.max_output_chars],
                    error=f"无法解析沙箱输出 (exit_code={proc.returncode})",
                    exit_code=proc.returncode,
                )

            return SandboxResult(
                success=data.get("success", False),
                stdout=data.get("stdout", ""),
                stderr=data.get("error", ""),
                exit_code=data.get("exit_code", proc.returncode),
                error=data.get("error") if not data.get("success") else None,
            )

        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
