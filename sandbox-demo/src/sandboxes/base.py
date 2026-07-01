"""
抽象沙箱基类 — 定义统一的沙箱接口

所有沙箱实现（subprocess / Docker / RestrictedPython）
都继承此基类，确保一致的 API 和可替换性。

核心接口:
    execute(code: str) -> SandboxResult    同步执行
    execute_async(code: str) -> SandboxResult  异步执行
    is_available() -> bool                  检查是否可用

设计原则:
    - 策略模式: 沙箱实现可插拔替换
    - 模板方法: execute() 封装了 pre/post 钩子
    - 防御深度: 每个沙箱内部实现多层安全检查
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime
import time


@dataclass
class SandboxResult:
    """沙箱执行结果"""
    success: bool                          # 是否成功执行
    stdout: str = ""                       # 标准输出
    stderr: str = ""                       # 标准错误
    exit_code: int = -1                    # 退出码
    execution_time_ms: float = 0.0         # 执行耗时（毫秒）
    error: Optional[str] = None            # 错误信息
    truncated: bool = False                # 输出是否被截断
    resources_used: Dict = field(default_factory=dict)  # 资源使用量
    audit_id: Optional[str] = None         # 审计日志 ID

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "stdout": self.stdout[:1000] + "..." if self.truncated else self.stdout,
            "stderr": self.stderr[:500],
            "exit_code": self.exit_code,
            "execution_time_ms": self.execution_time_ms,
            "error": self.error,
            "truncated": self.truncated,
            "resources_used": self.resources_used,
        }


@dataclass
class SandboxConfig:
    """沙箱通用配置"""
    timeout_seconds: int = 10              # CPU/墙上时钟超时
    memory_limit_mb: int = 256             # 内存限制
    max_processes: int = 32                # 最大子进程数
    max_output_chars: int = 10_000         # 输出最大字符数
    max_file_size_mb: int = 100            # 最大文件写入
    allow_network: bool = False            # 是否允许网络
    allow_subprocesses: bool = False       # 是否允许子进程
    allow_file_write: bool = False         # 是否允许文件写入
    environment_vars: Dict[str, str] = field(default_factory=dict)


class BaseSandbox(ABC):
    """
    沙箱抽象基类

    所有沙箱实现的统一入口，子类只需实现 _execute_impl() 方法。
    execute() 模板方法自动处理：
        1. 前置: 输入验证、策略检查
        2. 执行: 调用子类 _execute_impl()
        3. 后置: 结果截断、资源统计、审计记录
    """

    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self.audit_log: List[Dict] = []

    @abstractmethod
    def _execute_impl(self, code: str) -> SandboxResult:
        """子类实现的具体沙箱执行逻辑"""
        ...

    def execute(self, code: str) -> SandboxResult:
        """
        在沙箱中执行代码

        模板方法 —— 封装了 pre-execution 检查、执行计时、post-execution 处理
        """
        # ── 前置检查 ──
        validation_error = self._validate_input(code)
        if validation_error:
            return SandboxResult(success=False, error=validation_error,
                                 audit_id=self._audit("BLOCKED", validation_error))

        # ── 执行 ──
        start = time.perf_counter()
        try:
            result = self._execute_impl(code)
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return SandboxResult(
                success=False, error=f"沙箱执行异常: {e}",
                execution_time_ms=elapsed,
                audit_id=self._audit("CRASH", str(e)),
            )
        elapsed = (time.perf_counter() - start) * 1000

        # ── 后置处理 ──
        result.execution_time_ms = elapsed

        # 输出截断
        if len(result.stdout) > self.config.max_output_chars:
            result.stdout = result.stdout[:self.config.max_output_chars]
            result.truncated = True

        # 审计
        audit_id = self._audit(
            "SUCCESS" if result.success else "FAILED",
            result.error or "",
        )
        result.audit_id = audit_id

        return result

    def _validate_input(self, code: str) -> Optional[str]:
        """输入验证 —— 在代码进入沙箱前进行基础检查"""
        if not code or not code.strip():
            return "代码不能为空"
        if len(code) > 500_000:  # 500KB 上限
            return "代码过长，超过 500KB 上限"
        return None

    def _audit(self, action: str, detail: str) -> str:
        """记录审计日志"""
        import uuid
        entry = {
            "id": str(uuid.uuid4())[:8],
            "timestamp": datetime.now().isoformat(),
            "sandbox_type": self.__class__.__name__,
            "action": action,
            "detail": detail[:200],
        }
        self.audit_log.append(entry)
        return entry["id"]

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        """沙箱名称（用于展示）"""
        ...

    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        """检查该沙箱是否在当前环境中可用"""
        ...

    @classmethod
    @abstractmethod
    def isolation_level(cls) -> str:
        """隔离等级: process | container | language"""
        ...
