"""
资源监控模块 — 实时追踪沙箱内代码的资源使用

提供三个维度的监控:
    1. 内存  — RSS / VMS
    2. CPU   — 用户态 / 内核态时间
    3. I/O   — 文件描述符 / 磁盘读写

监控策略:
    - 采样间隔可配（默认 100ms）
    - 超过阈值可触发回调（如发送告警）
    - 支持异步采样（不阻塞主进程）

注意:
    某些指标（如 RLIMIT_AS）在 Windows 上不可用，会优雅降级。
"""
import os
import time
import threading
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field

try:
    import resource
    HAS_RESOURCE = True
except ImportError:
    HAS_RESOURCE = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


@dataclass
class ResourceLimits:
    """资源限制定义"""
    max_memory_mb: int = 256
    max_cpu_seconds: int = 10
    max_processes: int = 32
    max_file_size_mb: int = 100
    max_open_files: int = 256
    max_output_chars: int = 10_000


@dataclass
class ResourceSnapshot:
    """资源使用快照"""
    timestamp: float = 0.0
    memory_rss_mb: float = 0.0
    memory_vms_mb: float = 0.0
    cpu_user_seconds: float = 0.0
    cpu_system_seconds: float = 0.0
    open_fds: int = 0
    threads: int = 0


@dataclass
class ResourceReport:
    """资源使用报告"""
    peak_memory_mb: float = 0.0
    avg_memory_mb: float = 0.0
    total_cpu_seconds: float = 0.0
    peak_open_fds: int = 0
    peak_threads: int = 0
    snapshots: List[ResourceSnapshot] = field(default_factory=list)
    limit_exceeded: bool = False
    exceeded_resource: Optional[str] = None


class ResourceMonitor:
    """
    资源使用监控器

    用法:
        monitor = ResourceMonitor(limits, pid=child_process.pid)
        monitor.start()
        # ... 执行代码 ...
        monitor.stop()
        report = monitor.get_report()
    """

    def __init__(self, limits: ResourceLimits, pid: Optional[int] = None):
        self.limits = limits
        self.pid = pid or os.getpid()
        self._running = False
        self._snapshots: List[ResourceSnapshot] = []
        self._thread: Optional[threading.Thread] = None
        self._on_limit_exceeded: Optional[Callable] = None

    def set_limit_callback(self, callback: Callable[[str, float, float], None]):
        """
        设置超限回调

        回调签名: callback(resource_name: str, current_value: float, limit: float)
        """
        self._on_limit_exceeded = callback

    def start(self, interval_seconds: float = 0.1):
        """启动后台监控线程"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval_seconds,),
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> ResourceReport:
        """停止监控并返回报告"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        return self.get_report()

    def _monitor_loop(self, interval: float):
        """后台采样循环"""
        while self._running:
            snapshot = self._take_snapshot()
            self._snapshots.append(snapshot)
            self._check_limits(snapshot)
            time.sleep(interval)

    def _take_snapshot(self) -> ResourceSnapshot:
        """采集一次资源快照"""
        snap = ResourceSnapshot(timestamp=time.time())

        if HAS_PSUTIL:
            try:
                proc = psutil.Process(self.pid)
                mem = proc.memory_info()
                snap.memory_rss_mb = mem.rss / (1024 * 1024)
                snap.memory_vms_mb = mem.vms / (1024 * 1024)
                cpu = proc.cpu_times()
                snap.cpu_user_seconds = cpu.user
                snap.cpu_system_seconds = cpu.system
                snap.open_fds = proc.num_fds() if hasattr(proc, 'num_fds') else 0
                snap.threads = proc.num_threads()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        elif HAS_RESOURCE:
            try:
                usage = resource.getrusage(resource.RUSAGE_SELF)
                snap.memory_rss_mb = usage.ru_maxrss / 1024
                snap.cpu_user_seconds = usage.ru_utime
                snap.cpu_system_seconds = usage.ru_stime
            except Exception:
                pass

        return snap

    def _check_limits(self, snapshot: ResourceSnapshot):
        """检查是否超出限制"""
        checks = [
            ("memory", snapshot.memory_rss_mb, self.limits.max_memory_mb),
            ("cpu", snapshot.cpu_user_seconds + snapshot.cpu_system_seconds,
             self.limits.max_cpu_seconds),
            ("open_fds", snapshot.open_fds, self.limits.max_open_files),
            ("threads", snapshot.threads, self.limits.max_processes),
        ]

        for name, current, limit in checks:
            if current > limit:
                if self._on_limit_exceeded:
                    self._on_limit_exceeded(name, current, limit)
                break

    def get_report(self) -> ResourceReport:
        """生成资源使用报告"""
        if not self._snapshots:
            return ResourceReport()

        mem_values = [s.memory_rss_mb for s in self._snapshots]
        cpu_total = (
            self._snapshots[-1].cpu_user_seconds
            + self._snapshots[-1].cpu_system_seconds
        )
        fd_values = [s.open_fds for s in self._snapshots]
        thread_values = [s.threads for s in self._snapshots]

        report = ResourceReport(
            peak_memory_mb=max(mem_values) if mem_values else 0,
            avg_memory_mb=sum(mem_values) / len(mem_values) if mem_values else 0,
            total_cpu_seconds=cpu_total,
            peak_open_fds=max(fd_values) if fd_values else 0,
            peak_threads=max(thread_values) if thread_values else 0,
            snapshots=self._snapshots,
        )

        # 检查是否超限
        checks = [
            ("memory", report.peak_memory_mb, self.limits.max_memory_mb),
            ("cpu", report.total_cpu_seconds, self.limits.max_cpu_seconds),
            ("open_fds", report.peak_open_fds, self.limits.max_open_files),
        ]
        for name, current, limit in checks:
            if current > limit:
                report.limit_exceeded = True
                report.exceeded_resource = name
                break

        return report

    def get_current_snapshot(self) -> ResourceSnapshot:
        """获取当前即时快照"""
        return self._take_snapshot()
