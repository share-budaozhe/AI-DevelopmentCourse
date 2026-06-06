"""
═══════════════════════════════════════════════════════════════
  🔧 Milvus 学习教程 — src/config.py
  Milvus 连接配置中心

  支持三种连接方式：
  - Milvus Lite（嵌入式，免 Docker，推荐学习）
  - Milvus Standalone（Docker 单机）
  - Zilliz Cloud（托管服务）
═══════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv
from pymilvus import connections, utility

load_dotenv(Path(__file__).parent.parent / ".env")


def connect_lite(db_path: str | None = None) -> str:
    """🔌 连接 Milvus Lite（嵌入式，无需外部服务）。

    Milvus Lite 将整个 Milvus 数据库嵌入到你的 Python 进程中，
    数据存储为本地文件。适合学习和开发。

    Args:
        db_path: 数据库文件路径，默认为 ./milvus_data.db
    Returns:
        连接别名
    """
    if db_path is None:
        db_path = str(Path(__file__).parent.parent / "milvus_data.db")

    connections.connect(
        alias="default",
        uri=db_path,
    )
    print(f"[config] ✅ 已连接 Milvus Lite → {db_path}")
    return "default"


def connect_standalone(host: str = "localhost", port: str = "19530") -> str:
    """🔌 连接 Milvus Standalone（Docker 部署）。

    Args:
        host: Milvus 服务器地址
        port: Milvus 端口
    Returns:
        连接别名
    """
    connections.connect(
        alias="default",
        host=host,
        port=port,
    )
    print(f"[config] ✅ 已连接 Milvus Standalone → {host}:{port}")
    return "default"


def connect_zilliz(uri: str, token: str) -> str:
    """🔌 连接 Zilliz Cloud（全托管）。

    Args:
        uri: Zilliz Cloud 实例地址
        token: API Token
    Returns:
        连接别名
    """
    connections.connect(
        alias="default",
        uri=uri,
        token=token,
    )
    print(f"[config] ✅ 已连接 Zilliz Cloud → {uri}")
    return "default"


def auto_connect() -> str:
    """自动检测环境并选择合适的连接方式。

    优先级：环境变量 > Milvus Lite（默认）
    """
    milvus_uri = os.getenv("MILVUS_URI")
    milvus_token = os.getenv("MILVUS_TOKEN")
    milvus_host = os.getenv("MILVUS_HOST")

    if milvus_uri and milvus_token:
        return connect_zilliz(milvus_uri, milvus_token)
    elif milvus_host:
        port = os.getenv("MILVUS_PORT", "19530")
        return connect_standalone(milvus_host, port)
    else:
        return connect_lite()


def get_connection_info() -> dict:
    """获取当前连接信息。"""
    try:
        alias = "default"
        if not connections.has_connection(alias):
            return {"status": "not_connected"}

        # Milvus Lite 的连接类型检查
        return {
            "status": "connected",
            "alias": alias,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def disconnect():
    """断开连接。"""
    try:
        connections.disconnect("default")
        print("[config] 🔌 已断开连接")
    except Exception:
        pass


def print_connection_guide():
    """打印连接配置指南。"""
    guide = """
╔══════════════════════════════════════════════════════════════╗
║              🔌 Milvus 连接配置指南                          ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  方案 1：Milvus Lite（默认，推荐学习）                        ║
║  ─────────────────────────────────────                       ║
║  无需任何配置，pip install milvus-lite 即可                   ║
║  数据存储在本地 milvus_data.db 文件                          ║
║  注意：仅供开发测试，不能用于生产                             ║
║                                                              ║
║  方案 2：Milvus Standalone（Docker）                          ║
║  ─────────────────────────────────────                       ║
║  docker-compose up -d                                         ║
║  .env 中取消注释 MILVUS_HOST=localhost                         ║
║                                                              ║
║  方案 3：Zilliz Cloud（托管）                                 ║
║  ───────────────────────────────                             ║
║  注册 https://cloud.zilliz.com                                ║
║  .env 中设置 MILVUS_URI 和 MILVUS_TOKEN                       ║
║                                                              ║
║  对比：                                                       ║
║  ┌────────────┬──────────┬──────────┬────────────┐           ║
║  │ 方案        │ 安装难度 │ 性能     │ 适用场景    │           ║
║  ├────────────┼──────────┼──────────┼────────────┤           ║
║  │ Lite       │ ⭐ 最简单 │ 低       │ 学习/开发  │           ║
║  │ Standalone │ ⭐⭐ Docker│ 中       │ 项目开发   │           ║
║  │ Zilliz     │ ⭐ 注册   │ 高       │ 生产环境   │           ║
║  └────────────┴──────────┴──────────┴────────────┘           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(guide)


if __name__ == "__main__":
    print_connection_guide()
    auto_connect()
    disconnect()
