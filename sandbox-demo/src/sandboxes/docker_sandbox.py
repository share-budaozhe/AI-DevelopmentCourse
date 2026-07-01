"""
Docker 容器沙箱

通过 Docker SDK 在隔离容器中执行代码，提供最强的隔离级别。
适用于对安全性要求极高的场景（如 AI Agent 执行 LLM 生成的代码）。

隔离等级: container 级
隔离机制:
    1. 独立容器 —— 完整的内核命名空间隔离 (PID/NET/MNT/IPC/UTS/USER)
    2. Cgroup 资源限制 —— CPU quota / Memory limit / PIDs limit / Blk I/O
    3. Linux Capabilities —— cap_drop=ALL + no-new-privileges
    4. 只读根文件系统 —— 禁止写入系统目录
    5. 网络隔离 —— 默认 network_mode=none
    6. Ulimit —— nproc / nofile / fsize
    7. 临时文件系统 —— tmpfs /tmp
    8. Auto-remove —— 执行后自动销毁容器

优势:
    - 最强的进程/网络/文件系统隔离
    - 不可变的执行环境
    - 容器即焚 (throwaway container)
    - 适合执行不受信任的第三方代码

局限:
    - 需要 Docker 环境
    - 启动较慢 (~500ms - 2s)
    - 镜像需要预先 pull
    - 资源开销较大
"""
import json
import textwrap
import time
from typing import Optional

from src.sandboxes.base import BaseSandbox, SandboxConfig, SandboxResult
from src.policies.security_policy import CodeSecurityAnalyzer, SecurityLevel


DOCKER_SANDBOX_IMAGE = "python:3.11-slim"

CONTAINER_SCRIPT_TEMPLATE = '''
import json, sys, traceback, signal, resource, os

# ══ Python 级 RLIMIT (容器内第二道防线) ══
limits = [
    (resource.RLIMIT_CPU, ({cpu_limit}, {cpu_limit})),
    (resource.RLIMIT_AS, ({mem_bytes}, {mem_bytes})),
    (resource.RLIMIT_DATA, ({data_bytes}, {data_bytes})),
    (resource.RLIMIT_NPROC, ({proc_limit}, {proc_limit})),
    (resource.RLIMIT_FSIZE, ({fsize_bytes}, {fsize_bytes})),
    (resource.RLIMIT_NOFILE, ({fd_limit}, {fd_limit})),
]
for r, (soft, hard) in limits:
    try:
        resource.setrlimit(r, (soft, hard))
    except (ValueError, resource.error):
        pass

def _timeout_handler(signum, frame):
    print(json.dumps({{"success": False, "error": "CPU_TIME_EXCEEDED"}}))
    sys.exit(1)
signal.signal(signal.SIGXCPU, _timeout_handler)
signal.alarm({wall_timeout})

# ══ 安全 stdout ══
class _LimitedStdout:
    def __init__(self, limit={max_output}):
        self.limit = limit
        self.buf = []
        self.n = 0
    def write(self, s):
        if self.n < self.limit:
            self.buf.append(s)
            self.n += len(s)
    def flush(self): pass
    def getvalue(self): return "".join(self.buf)

_out = _LimitedStdout()
sys.stdout = _out
sys.stderr = _out

# ══ 执行 ══
_result = {{"success": False, "error": "", "stdout": "", "exit_code": -1}}
try:
    exec_globals = {{"__builtins__": __builtins__, "__name__": "__sandbox__"}}
    exec("""{code}""", exec_globals)
    _result["success"] = True
    _result["exit_code"] = 0
except SystemExit as e:
    _result["exit_code"] = e.code or 0
    _result["success"] = _result["exit_code"] == 0
except Exception as e:
    _result["error"] = f"{{type(e).__name__}}: {{e}}"
    _result["exit_code"] = 1
finally:
    _result["stdout"] = _out.getvalue()
    print(json.dumps(_result, ensure_ascii=False, default=str))
'''


class DockerSandbox(BaseSandbox):
    """
    Docker 容器隔离沙箱

    使用 Docker SDK 在全新容器中执行代码，容器执行完毕后自动销毁。
    """

    def __init__(self, config: Optional[SandboxConfig] = None,
                 image: str = DOCKER_SANDBOX_IMAGE,
                 security_level: SecurityLevel = SecurityLevel.STANDARD):
        super().__init__(config)
        self.image = image
        self.security_analyzer = CodeSecurityAnalyzer(level=security_level)
        self._docker_client = None

    @classmethod
    def name(cls) -> str:
        return "Docker Container Sandbox"

    @classmethod
    def is_available(cls) -> bool:
        """检查 Docker 是否可用"""
        try:
            import docker
            client = docker.from_env()
            client.ping()
            return True
        except Exception:
            return False

    @classmethod
    def isolation_level(cls) -> str:
        return "container"

    @property
    def docker_client(self):
        if self._docker_client is None:
            import docker
            self._docker_client = docker.from_env()
        return self._docker_client

    def _execute_impl(self, code: str) -> SandboxResult:
        # 安全策略检查
        analysis = self.security_analyzer.analyze(code)
        if not analysis["safe"]:
            findings_str = "; ".join(f["message"] for f in analysis["findings"][:3])
            return SandboxResult(
                success=False,
                error=f"安全策略检查未通过 (risk={analysis['risk_score']}): {findings_str}",
                exit_code=403,
            )

        import docker

        interpreter_overhead_mb = 120
        mem_limit_bytes = max(1, self.config.memory_limit_mb) * 1024 * 1024

        wrapped_code = CONTAINER_SCRIPT_TEMPLATE.format(
            code=code.replace("\\", "\\\\").replace('"""', '\\"\\"\\"'),
            cpu_limit=self.config.timeout_seconds,
            wall_timeout=self.config.timeout_seconds + 2,
            mem_bytes=mem_limit_bytes,
            data_bytes=max(1, self.config.memory_limit_mb - interpreter_overhead_mb) * 1024 * 1024,
            proc_limit=self.config.max_processes if self.config.allow_subprocesses else 0,
            fsize_bytes=self.config.max_file_size_mb * 1024 * 1024,
            fd_limit=256,
            max_output=self.config.max_output_chars,
        )

        try:
            container = self.docker_client.containers.run(
                image=self.image,
                command=["python", "-c", wrapped_code],
                detach=True,
                # ── Cgroup 资源限制 ──
                mem_limit=f"{self.config.memory_limit_mb}m",
                memswap_limit=f"{self.config.memory_limit_mb * 2}m",
                cpu_quota=int(self.config.timeout_seconds * 10000),
                cpu_period=100000,
                pids_limit=self.config.max_processes if self.config.allow_subprocesses else 1,
                # ── 安全加固 ──
                network_mode="none" if not self.config.allow_network else "bridge",
                read_only=True,
                security_opt=["no-new-privileges:true"],
                cap_drop=["ALL"],
                # ── Ulimits ──
                ulimits=[
                    docker.types.Ulimit(name='nproc', soft=1, hard=self.config.max_processes),
                    docker.types.Ulimit(name='nofile', soft=64, hard=256),
                    docker.types.Ulimit(name='fsize', soft=self.config.max_file_size_mb * 1048576,
                                        hard=self.config.max_file_size_mb * 1048576),
                ],
                # ── 临时文件系统 ──
                tmpfs={"/tmp": "size=64M,noexec,nosuid"},
                # ── 环境变量 ──
                environment={"PYTHONDONTWRITEBYTECODE": "1"},
                auto_remove=True,
            )

            # 等待完成（含超时）
            try:
                result = container.wait(timeout=self.config.timeout_seconds + 10)
                exit_code = result.get("StatusCode", -1) if isinstance(result, dict) else -1
            except Exception:
                container.kill()
                return SandboxResult(
                    success=False,
                    error="CONTAINER_TIMEOUT: 容器执行超时，已强制终止",
                    exit_code=-9,
                )

            # 读取日志
            output = container.logs(stdout=True, stderr=True).decode("utf-8", errors="replace")
            try:
                last_line = output.strip().split('\n')[-1] if output.strip() else "{}"
                data = json.loads(last_line)
            except json.JSONDecodeError:
                return SandboxResult(
                    success=False,
                    stdout=output[:self.config.max_output_chars],
                    error=f"无法解析容器输出 (exit_code={exit_code})",
                    exit_code=exit_code,
                )

            return SandboxResult(
                success=data.get("success", False),
                stdout=data.get("stdout", ""),
                stderr=data.get("error", ""),
                exit_code=data.get("exit_code", exit_code),
                error=data.get("error") if not data.get("success") else None,
            )

        except docker.errors.ImageNotFound:
            return SandboxResult(
                success=False,
                error=f"Docker 镜像 '{self.image}' 未找到，请先执行: docker pull {self.image}",
            )
        except docker.errors.DockerException as e:
            return SandboxResult(
                success=False,
                error=f"Docker 错误: {e}",
            )
