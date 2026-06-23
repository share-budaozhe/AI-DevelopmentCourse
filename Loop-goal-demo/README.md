# Loop vs Goal — 理解"循环"与"目标"的区别与协作

> **学习计算机程序中两个最基础概念的独立性与协作关系。**

## 一句话

```
Loop = 引擎（怎么跑）
Goal = 终点（跑到哪停）
程序 = Loop 驱动 + Goal 判断
```

## 快速开始

```bash
# 运行全部 5 个演示
python loop_and_goal.py

# 运行 20 个单元测试
python loop_and_goal.py test
```

## 项目结构

```
├── loop_and_goal.py          # 主演示程序（包含所有代码、测试和文档注释）
├── README.md                 # 本文件
└── docs/
    ├── project_overview.md       # 项目说明 —— 设计理念、类比、对比表
    ├── technical_implementation.md  # 技术要点与实现 —— 6 大技术点详解
    └── testing.md               # 测试说明 —— 测试策略、用例详解、运行指南
```

## 五大演示示例

| 示例 | 内容 | 核心洞察 |
|------|------|---------|
| 例 1 — 猜数字 | `while True` + 条件 `break` | Loop 和 Goal 最直观的形态 |
| 例 2 — 同一 Goal 不同 Loop | 求和：while / for / 递归 / 公式 | **Goal 不变，Loop 可换** |
| 例 3 — 同一 Loop 不同 Goal | `count_up_until` + 4 种目标函数 | **Loop 不变，Goal 可换** |
| 例 4 — Goal 达不到 | 带 `step_limit` 的安全搜索 | Loop 需要安全阀 |
| 例 5 — 嵌套 Loop + 多层 Goal | 勾股数搜索 (3 层嵌套) | 复杂任务中的分层协作 |

## 核心对比

| 维度 | Loop（循环） | Goal（目标） |
|------|-------------|-------------|
| 角色 | 引擎 / 驱动器 | 终点 / 判断条件 |
| 回答的问题 | "怎么做？" | "做到什么程度停？" |
| 代码形态 | `while` / `for` / 递归 | `if` 条件 / 哨兵值 |
| 失败方式 | 死循环 | 永远达不到 |
| 可替换性 | 同一 Goal 可用不同 Loop | 同一 Loop 可追不同 Goal |

## 适用人群

- 编程初学者（理解循环和条件的关系）
- 教学场景（作为 Loop vs Goal 概念的教学材料）
- 自学者（通过 5 个递进示例建立直觉）
