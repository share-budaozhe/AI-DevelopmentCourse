"""
═══════════════════════════════════════════════════════════════
  🎯 Milvus 学习教程 — src/main.py（交互入口）
  7 个核心实验 + 文档导航 + 测试说明
═══════════════════════════════════════════════════════════════

运行方式：
    cd milvus-demo
    python -m src.main
"""
from __future__ import annotations

import sys
import os

# 确保 src 目录在路径中（必须在所有本地导入之前）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def show_banner():
    print(r"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🎯  Milvus 向量数据库学习教程 v1.0                        ║
║     从零掌握向量检索与 ANN 索引                                ║
║                                                              ║
║     7 个核心实验 | 完整文档 | 测试指南                         ║
║     支持 Milvus Lite（免 Docker）| Standalone | Zilliz Cloud  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")


def show_menu():
    print("""
  📋 实验菜单：
  ┌──────────────────────────────────────────────────────────┐
  │ [1] 连接与基础操作    → Connection & Schema              │
  │ [2] Collection 管理   → CRUD & 数据操作                  │
  │ [3] 索引类型对比      → FLAT/IVF/HNSW 对比               │
  │ [4] 向量搜索          → ANN Search & 相似度度量           │
  │ [5] 标量过滤          → Scalar Filter & 表达式语法        │
  │ [6] 分区管理          → Partition 隔离与优化              │
  │ [7] 进阶特性          → 别名/一致性/性能调优              │
  ├──────────────────────────────────────────────────────────┤
  │ [9] 运行全部实验（顺序执行）                               │
  │ [c] 连接配置指南 (Lite / Standalone / Zilliz)            │
  │ [d] 查看文档导航                                          │
  │ [r] 查看 README（运行说明）                                │
  │ [t] 查看测试说明                                          │
  │ [q] 退出                                                  │
  └──────────────────────────────────────────────────────────┘
""")


def run_experiment(choice: str):
    experiments = {
        "1": ("demo_connect", "连接与基础操作"),
        "2": ("demo_collections", "Collection 管理"),
        "3": ("demo_indexes", "索引类型对比"),
        "4": ("demo_search", "向量搜索"),
        "5": ("demo_filter", "标量过滤"),
        "6": ("demo_partition", "分区管理"),
        "7": ("demo_advanced", "进阶特性"),
    }

    if choice in experiments:
        mod_name, title = experiments[choice]
        print(f"\n{'='*60}")
        print(f"  🚀 实验 {choice}：{title}")
        print(f"{'='*60}")
        mod = __import__(mod_name)
        mod.run()
    elif choice == "9":
        for num in ["1", "2", "3", "4", "5", "6", "7"]:
            mod_name, title = experiments[num]
            print(f"\n{'#'*60}")
            print(f"  实验 {num}：{title}")
            mod = __import__(mod_name)
            mod.run()
        print(f"\n🎉 全部实验完成！")
    elif choice == "c":
        from config import print_connection_guide
        print_connection_guide()
    elif choice == "d":
        show_docs_nav()
    elif choice == "r":
        show_readme_guide()
    elif choice == "t":
        show_test_guide()
    else:
        print(f"  ⚠️ 无效选择: {choice}")


def show_docs_nav():
    docs = r"""
╔══════════════════════════════════════════════════════════════╗
║              📖 文档导航                                      ║
╚══════════════════════════════════════════════════════════════╝

  docs/ 目录下的学习文档：

  ┌──────────────────────────────────────┬────────────────────┐
  │ 01-overview.md                       │ 项目总览与核心概念  │
  │ 02-installation.md                   │ 安装部署指南       │
  │ 03-collections.md                    │ Collection 与 CRUD │
  │ 04-indexes.md                        │ 索引类型与原理     │
  │ 05-search.md                         │ 向量搜索深入       │
  │ 06-advanced.md                       │ 进阶特性与优化     │
  │ 07-faq.md                            │ 常见问题汇总       │
  ├──────────────────────────────────────┼────────────────────┤
  │ test-guide.md                        │ 测试说明与用例     │
  └──────────────────────────────────────┴────────────────────┘
"""
    print(docs)


def show_readme_guide():
    guide = r"""
╔══════════════════════════════════════════════════════════════╗
║              🚀 测试运行详细说明                              ║
╚══════════════════════════════════════════════════════════════╝

  1. 安装
  ────────────────────────────────────────
  pip install -r requirements.txt

  注意：Milvus Lite 是纯 Python 实现，无需 Docker！

  2. 运行（默认使用 Milvus Lite）
  ────────────────────────────────────────
  cd milvus-demo
  python -m src.main

  3. 如需 Milvus Standalone（Docker）
  ────────────────────────────────────────
  docker-compose up -d
  # .env 中取消注释 MILVUS_HOST=localhost
  python -m src.main

  4. 单独运行实验
  ────────────────────────────────────────
  python -m src.demo_connect
  python -m src.demo_collections
  python -m src.demo_indexes
  python -m src.demo_search
  python -m src.demo_filter
  python -m src.demo_partition
  python -m src.demo_advanced

  5. 学习路径
  ────────────────────────────────────────
  初学者：实验 1 → 2 → 3 → 4 → 5
  进阶者：实验 6 → 7
"""
    print(guide)


def show_test_guide():
    test = r"""
╔══════════════════════════════════════════════════════════════╗
║              🧪 测试说明                                      ║
╚══════════════════════════════════════════════════════════════╝

  测试场景覆盖：

  ┌──────────────────┬────────────────────────────────────┐
  │ 功能测试          │ 连接 → 创建集合 → 插入 → 索引      │
  │                   │ → 搜索 → 过滤 → 删除 → 清理         │
  ├──────────────────┼────────────────────────────────────┤
  │ 性能测试          │ 批量插入吞吐量 (条/秒)               │
  │                   │ 搜索延迟 (P50/P95/P99)             │
  │                   │ FLAT vs IVF 速度对比               │
  ├──────────────────┼────────────────────────────────────┤
  │ 边界测试          │ 空集合搜索                          │
  │                   │ 超大 limit 查询                     │
  │                   │ 重复主键插入                        │
  │                   │ 不存在的分区查询                     │
  ├──────────────────┼────────────────────────────────────┤
  │ 正确性测试        │ 搜索自己 → score ≈ 1.0 (COSINE)    │
  │                   │ 同类商品 → score 高于异类            │
  │                   │ 过滤后结果满足条件                   │
  └──────────────────┴────────────────────────────────────┘

  验证清单（运行所有实验后检查）：
  ✅ 连接成功
  ✅ Collection 创建成功，字段正确
  ✅ 数据插入数量正确
  ✅ 索引创建成功
  ✅ 搜索返回结果且按分数降序
  ✅ 标量过滤结果满足表达式条件
  ✅ 分区数据隔离正确
  ✅ 资源清理完整（无残留 Collection）
"""
    print(test)


def main():
    show_banner()

    while True:
        show_menu()
        try:
            choice = input("  👉 请输入选项: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n  👋 再见！")
            break

        if choice in ("q", "quit", "exit"):
            print("\n  👋 再见！\n")
            break

        run_experiment(choice)

        if choice not in ("c", "d", "r", "t", "q"):
            try:
                input("\n  按 Enter 返回菜单...")
            except (EOFError, KeyboardInterrupt):
                print()
                break


if __name__ == "__main__":
    main()
