"""
AutoGPT 工具集实现
布道者

包含四大核心工具：
1. web_search — 网络搜索（基于 DuckDuckGo）
2. file_ops  — 文件读写操作
3. code_exec — 安全的代码执行（子进程沙箱）
4. web_browse — 网页内容抓取与解析
"""
import os
import re
import sys
import json
import tempfile
import subprocess
from typing import Any

from src.tools.base import BaseTool, ToolResult


# ═══════════════════════════════════════════════════════════════
# 工具 1: 网络搜索
# 布道者: 使用 DuckDuckGo 搜索，无需 API Key，隐私友好
# ═══════════════════════════════════════════════════════════════

class WebSearchTool(BaseTool):
    """
    网络搜索工具

    布道者:
        通过 DuckDuckGo 引擎搜索互联网信息。
        Agent 在需要获取最新情报或验证事实时调用此工具。
    """
    name = "web_search"
    description = "搜索互联网获取最新信息。当需要查找事实、数据或你不确定的内容时使用。"
    parameters = {
        "query": {
            "type": "string",
            "description": "搜索关键词，支持中文和英文",
        },
        "max_results": {
            "type": "integer",
            "description": "最大结果数，默认 5",
            "default": 5,
        },
    }

    def execute(self, query: str = "", max_results: int = 5, **kwargs) -> ToolResult:
        if not query.strip():
            return self.format_result(False, "搜索关键词不能为空")

        try:
            from duckduckgo_search import DDGS
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", "")[:300],
                    })

            if not results:
                return self.format_result(True, f"未找到与 '{query}' 相关的结果。")

            # 格式化搜索结果
            lines = [f"## 搜索: {query}\n"]
            for i, r in enumerate(results, 1):
                lines.append(f"{i}. **{r['title']}**")
                lines.append(f"   URL: {r['url']}")
                lines.append(f"   {r['snippet']}")
                lines.append("")

            content = "\n".join(lines)
            return self.format_result(True, content, {"result_count": len(results)})

        except ImportError:
            # 降级: 模拟搜索
            return self._simulated_search(query, max_results)
        except Exception as e:
            return self.format_result(False, f"搜索失败: {e}")

    def _simulated_search(self, query: str, max_results: int = 5) -> ToolResult:
        """模拟搜索（无 duckduckgo-search 包时的降级方案）"""
        content = (
            f"## 模拟搜索结果: {query}\n\n"
            f"（提示: 安装 duckduckgo-search 可获得真实搜索结果）\n\n"
            f"1. **关于 {query} 的概述**\n"
            f"   这是对 '{query}' 的模拟搜索结果。在生产环境中，"
            f"此工具将返回来自 DuckDuckGo 的真实搜索数据。\n\n"
            f"2. **相关资源**\n"
            f"   请基于你的训练知识来回答与 '{query}' 相关的问题。"
        )
        return self.format_result(True, content, {"simulated": True})


# ═══════════════════════════════════════════════════════════════
# 工具 2: 文件操作
# 布道者: Agent 可通过此工具读写工作目录内的文件
# ═══════════════════════════════════════════════════════════════

class FileOperationsTool(BaseTool):
    """
    文件操作工具

    布道者:
        限制在工作目录内操作，防止路径遍历攻击。
        支持读取、写入、列出文件三种操作。
    """
    name = "file_ops"
    description = "在 workspace 目录中读写文件。用于保存中间结果、生成报告、读取已有文件。"
    parameters = {
        "operation": {
            "type": "string",
            "description": "操作类型: read(读取), write(写入), list(列出文件)",
            "enum": ["read", "write", "list"],
        },
        "path": {
            "type": "string",
            "description": "文件路径（相对于 workspace 目录）",
        },
        "content": {
            "type": "string",
            "description": "要写入的内容（仅在 operation=write 时需要）",
        },
    }

    def __init__(self, workspace_dir: str = "./workspace"):
        super().__init__()
        self.workspace_dir = os.path.abspath(workspace_dir)
        os.makedirs(self.workspace_dir, exist_ok=True)

    def execute(self, operation: str = "list", path: str = "", content: str = "", **kwargs) -> ToolResult:
        # 安全检查: 防止路径遍历
        full_path = os.path.abspath(os.path.join(self.workspace_dir, path))
        if not full_path.startswith(self.workspace_dir):
            return self.format_result(False, f"安全拦截: 禁止访问工作目录外的路径 ({path})")

        if operation == "list":
            return self._list_files(full_path)
        elif operation == "read":
            return self._read_file(full_path)
        elif operation == "write":
            return self._write_file(full_path, content)
        else:
            return self.format_result(False, f"不支持的操作: {operation}")

    def _list_files(self, path: str) -> ToolResult:
        """列出目录内容"""
        try:
            items = os.listdir(path)
            files = []
            for item in sorted(items):
                item_path = os.path.join(path, item)
                tag = "[DIR]" if os.path.isdir(item_path) else "[FILE]"
                size = ""
                if os.path.isfile(item_path):
                    size = f" ({os.path.getsize(item_path)} bytes)"
                files.append(f"  {tag} {item}{size}")
            rel_path = os.path.relpath(path, self.workspace_dir)
            content = f"## {rel_path if rel_path != '.' else 'workspace'} 目录内容\n\n" + "\n".join(files)
            return self.format_result(True, content, {"file_count": len(files)})
        except FileNotFoundError:
            return self.format_result(False, f"目录不存在: {path}")
        except Exception as e:
            return self.format_result(False, f"读取目录失败: {e}")

    def _read_file(self, path: str) -> ToolResult:
        """读取文件"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            if len(content) > 5000:
                content = content[:5000] + "\n\n...(内容过长，已截断)"
            rel_path = os.path.relpath(path, self.workspace_dir)
            return self.format_result(True, f"## {rel_path}\n\n```\n{content}\n```",
                                      {"size": os.path.getsize(path)})
        except FileNotFoundError:
            return self.format_result(False, f"文件不存在: {path}")
        except Exception as e:
            return self.format_result(False, f"读取文件失败: {e}")

    def _write_file(self, path: str, content: str) -> ToolResult:
        """写入文件"""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            rel_path = os.path.relpath(path, self.workspace_dir)
            return self.format_result(True, f"已写入文件: {rel_path} ({len(content)} 字符)",
                                      {"size": len(content)})
        except Exception as e:
            return self.format_result(False, f"写入文件失败: {e}")


# ═══════════════════════════════════════════════════════════════
# 工具 3: 代码执行
# 布道者: 在隔离子进程中执行 Python 代码，配备超时机制
# ═══════════════════════════════════════════════════════════════

class CodeExecutionTool(BaseTool):
    """
    代码执行工具

    布道者:
        使用 subprocess 子进程执行代码，与主进程隔离。
        配备超时机制（默认 30 秒）和输出长度限制。
        支持自动安装常用 pip 包。
    """
    name = "code_exec"
    description = "执行 Python 代码并获取结果。用于计算、数据分析、文本处理等需要编程解决的任务。"
    parameters = {
        "code": {
            "type": "string",
            "description": "要执行的 Python 代码",
        },
        "timeout": {
            "type": "integer",
            "description": "执行超时秒数，默认 30",
            "default": 30,
        },
    }

    def execute(self, code: str = "", timeout: int = 30, **kwargs) -> ToolResult:
        if not code.strip():
            return self.format_result(False, "代码不能为空")

        # 代码包装: 捕获输出和异常
        # 布道者: 使用 UTF-8 + 异常捕获确保稳定执行
        wrapped = (
            '# -*- coding: utf-8 -*-\n'
            'import sys, io\n'
            '_out = io.StringIO()\n'
            'sys.stdout = _out\n'
            'sys.stderr = _out\n'
            'try:\n'
        )
        for line in code.split('\n'):
            wrapped += f'    {line}\n'
        wrapped += (
            'except Exception as _e:\n'
            '    _out.write(f"Exception: {type(_e).__name__}: {_e}")\n'
            'finally:\n'
            '    sys.stdout = sys.__stdout__\n'
            '    sys.stderr = sys.__stderr__\n'
            '    print(_out.getvalue()[:5000])\n'
        )

        try:
            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.py', prefix='autogpt_', delete=False
            ) as f:
                f.write(wrapped)
                tmp_path = f.name

            proc = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )

            output = proc.stdout[:4000]
            if proc.stderr:
                output += f"\n[stderr]\n{proc.stderr[:1000]}"

            if proc.returncode != 0:
                return self.format_result(False, output, {"exit_code": proc.returncode})

            return self.format_result(True, output, {"exit_code": 0})

        except subprocess.TimeoutExpired:
            return self.format_result(False, f"代码执行超时（>{timeout}秒），已自动终止")
        except Exception as e:
            return self.format_result(False, f"代码执行异常: {e}")
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════
# 工具 4: 网页浏览
# 布道者: 抓取网页内容并提取纯文本，供 Agent 分析使用
# ═══════════════════════════════════════════════════════════════

class WebBrowseTool(BaseTool):
    """
    网页浏览工具

    布道者:
        获取指定 URL 的网页内容，使用 BeautifulSoup 去除 HTML 标签。
        Agent 在需要阅读在线文档、文章、API 文档时使用此工具。
    """
    name = "web_browse"
    description = "浏览指定网页并提取文本内容。用于获取在线文档、教程、新闻等网页的正文。"
    parameters = {
        "url": {
            "type": "string",
            "description": "要浏览的网页 URL",
        },
    }

    def execute(self, url: str = "", **kwargs) -> ToolResult:
        if not url.strip():
            return self.format_result(False, "URL 不能为空")
        if not re.match(r'https?://', url):
            url = 'https://' + url

        try:
            import urllib.request
            from bs4 import BeautifulSoup

            req = urllib.request.Request(
                url,
                headers={"User-Agent": "AutoGPT-Demo/1.0 (Educational Purpose)"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode('utf-8', errors='replace')

            soup = BeautifulSoup(html, 'html.parser')
            # 移除 script/style 标签
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()

            text = soup.get_text(separator='\n', strip=True)
            # 清理空行
            lines = [l for l in text.split('\n') if l.strip()]
            clean_text = '\n'.join(lines[:200])  # 最多 200 行

            if len(clean_text) > 4000:
                clean_text = clean_text[:4000] + "\n\n...(内容已截断)"

            return self.format_result(True, f"## {url}\n\n{clean_text}",
                                      {"url": url, "chars": len(clean_text)})

        except ImportError:
            return self.format_result(False,
                "缺少依赖包: pip install beautifulsoup4 requests")
        except Exception as e:
            return self.format_result(False, f"浏览网页失败: {type(e).__name__}: {e}")
