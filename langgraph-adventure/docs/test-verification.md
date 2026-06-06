# 🧪 测试验证文档 · AI 地牢探险 (LangGraph)

> 本文档覆盖 `langgraph-adventure` 项目的全部测试场景，从单元测试到集成验证，
> 确保 LangGraph 状态图的每个节点、每条边、每种路由都能正确运行。

---

## 📋 目录

1. [测试环境准备](#1-测试环境准备)
2. [模块单元测试](#2-模块单元测试)
   - 2.1 adventure_data（游戏数据层）
   - 2.2 state（状态定义）
   - 2.3 tools（工具函数）
   - 2.4 nodes（节点函数）
   - 2.5 graph（图的组装与路由）
3. [集成测试：完整图流程](#3-集成测试完整图流程)
4. [Human-in-the-Loop 验证](#4-human-in-the-loop-验证)
5. [边界条件与异常情况](#5-边界条件与异常情况)
6. [验证清单 Checklist](#6-验证清单-checklist)
7. [运行测试](#7-运行测试)

---


## 0. 虚拟环境（已就绪）

本项目已在 `langgraph-adventure\.venv` 下创建了 Python 虚拟环境，所有依赖均已安装完毕。

| 组件 | 版本 | 状态 |
|------|------|------|
| Python | 3.14.5 | ✅ 就绪 |
| langgraph | 1.2.4 | ✅ 就绪 |
| langchain-core | 1.4.0 | ✅ 就绪 |
| langgraph-checkpoint | 4.1.1 | ✅ 就绪 |
| pytest | 9.0.3 | ✅ 就绪 |

**使用方式：**

```powershell
# 激活虚拟环境
.\langgraph-adventure\.venv\Scripts\Activate.ps1

# 或直接使用虚拟环境的 Python 执行
.\langgraph-adventure\.venv\Scripts\python.exe -m pytest tests/ -v
.\langgraph-adventure\.venv\Scripts\python.exe -m src.main
```

---
## 1. 测试环境准备

| 依赖 | 版本要求 | 用途 |
|------|---------|------|
| pytest | >=8.0 | 测试框架 |
| pytest-asyncio | >=0.24 | 异步测试支持（LangGraph 编译图是异步的） |
| langgraph | >=0.4.0 | 被测试模块 |
| langchain-core | >=0.3.0 | 消息类型 |

```bash
# 安装测试依赖
pip install pytest pytest-asyncio
pip install -r requirements.txt
```

**测试目录结构：**

```
langgraph-adventure/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # 共享 fixtures
│   ├── test_adventure_data.py   # 数据层测试
│   ├── test_state.py            # 状态定义测试
│   ├── test_tools.py            # 工具函数测试
│   ├── test_nodes.py            # 节点函数测试
│   ├── test_graph.py            # 图组装与路由测试
│   └── test_integration.py      # 端到端集成测试
```

---

## 2. 模块单元测试

### 2.1 adventure_data（游戏数据层）

| 测试ID | 测试项 | 验证点 | 预期结果 |
|--------|--------|--------|----------|
| DATA-01 | `get_room("entrance")` | 起始房间存在 | 返回 Room(name="地牢入口", room_type="start") |
| DATA-02 | `get_room("nonexistent")` | 不存在的房间 | 返回 None |
| DATA-03 | `get_monster("goblin")` | 怪物数据正确 | Monster(hp=20, attack=4) |
| DATA-04 | `get_monster("dragon")` | Boss 怪物数据正确 | Monster(hp=60, attack=12) |
| DATA-05 | `get_item("治疗药水")` | 物品数据正确 | Item(effect_type="heal", effect_value=15) |
| DATA-06 | `get_item("不存在的物品")` | 不存在的物品 | 返回 None |
| DATA-07 | `describe_inventory([...])` | 空背包 | 返回包含 "空空如也" 的字符串 |
| DATA-08 | `describe_inventory(["银剑"])` | 有物品的背包 | 返回包含 emoji + 描述的字符串 |
| DATA-09 | `Room.exits` 完整性 | 所有出口指向存在的房间 | ROOMS 中每个 exit 的 target_id 在 ROOMS 中存在 |
| DATA-10 | `Monster.random_taunt()` | 嘲讽台词 | 返回 taunts 列表中的某个字符串 |
| DATA-11 | `PUZZLES` 完整性 | 每个谜题有 question/answer/hint/reward | 无 None 字段 |
| DATA-12 | 所有房间可达性 | 从 entrance 出发可到达所有房间 | BFS 遍历覆盖全部 ROOMS 键 |

### 2.2 state（状态定义）

| 测试ID | 测试项 | 验证点 | 预期结果 |
|--------|--------|--------|----------|
| STATE-01 | GameState 字段完整性 | TypedDict 包含全部必需字段 | messages, current_room, player_hp 等 14 个字段存在 |
| STATE-02 | messages 字段的 Annotated 类型 | 使用 add_messages reducer | 通过 `__annotations__` 检查 |
| STATE-03 | 默认覆盖字段 | player_hp/combat_active 等 | 无 Annotated 包装，使用默认 reducer |
| STATE-04 | total=False 语义 | 部分字段可缺失 | 构造不完整 GameState 不报错 |
| STATE-05 | 初始状态构建 | 游戏初始值 | current_room="entrance", player_hp=30, inventory=[] |

### 2.3 tools（工具函数）

| 测试ID | 测试项 | 验证点 | 预期结果 |
|--------|--------|--------|----------|
| TOOL-01 | `roll_dice(sides=20, times=1)` | 基本掷骰 | 结果在 1-20 之间 |
| TOOL-02 | `roll_dice(sides=20, times=3)` | 多骰子 | 返回包含 "总和 = " 的字符串 |
| TOOL-03 | `roll_dice` 满值 (D20=20) | 大成功提示 | 返回包含 "大成功" |
| TOOL-04 | `roll_dice` 最低值 (D20=1) | 大失败提示 | 返回包含 "大失败" |
| TOOL-05 | `calculate_damage(dice_result=1)` | 攻击失误 | 返回 "造成 0 点伤害" |
| TOOL-06 | `calculate_damage(dice_result=20)` | 暴击 | 返回包含 "暴击" |
| TOOL-07 | `calculate_damage(has_advantage=True)` | 优势暴击 | crit_threshold 降为 15 |
| TOOL-08 | `use_item("治疗药水", ["治疗药水"])` | 使用存在的物品 | 返回 "恢复 15 点生命" |
| TOOL-09 | `use_item("不存在的物品", [])` | 使用不存在的物品 | 返回包含 "背包中没有" |
| TOOL-10 | `check_inventory([])` | 空背包 | 返回 "背包空空如也" |
| TOOL-11 | `check_inventory(["银剑", "治疗药水"])` | 有内容的背包 | 返回 emoji + 物品名列表 |
| TOOL-12 | ALL_TOOLS 列表完整 | 包含 4 个工具 | len(ALL_TOOLS) == 4 |

### 2.4 nodes（节点函数）

| 测试ID | 测试项 | 验证点 | 预期结果 |
|--------|--------|--------|----------|
| NODE-01 | `enter_room` 起始房间 | 展示入口信息 | 返回 messages 包含 "地牢入口" |
| NODE-02 | `enter_room` 未知房间 | 回退到 entrance | current_room="entrance" |
| NODE-03 | `pickup_items` 空房间 | 无物品可拿 | 返回 "这里已经没什么可拿的了" |
| NODE-04 | `pickup_items` 军械库 | 拾取银剑+治疗药水 | inventory 增加 2 件，消息包含 emoji |
| NODE-05 | `pickup_items` 重复拾取 | 已拾取过 | inventory 不重复，返回无内容消息 |
| NODE-06 | `initiate_combat` 地精巢穴 | 战斗初始化 | combat_active=True, monster_hp=20 |
| NODE-07 | `initiate_combat` 空房间 | 无怪物 | 返回空 dict |
| NODE-08 | `player_attack` 普通攻击 | 造成伤害 | monster_hp 减少，返回伤害消息 |
| NODE-09 | `player_attack` 击杀怪物 | 怪物 HP 归零 | combat_active=False, 掉落物品加入背包 |
| NODE-10 | `player_attack` 装备银剑 | 攻击力加成 | player_attack 包含 +8 武器加成 |
| NODE-11 | `flee_combat` 成功 | D20>=12 | combat_active=False, 未受伤 |
| NODE-12 | `flee_combat` 失败 | D20<12 受伤 | player_hp 减少，可能 game_over |
| NODE-13 | `solve_puzzle` 未解谜题 | 展示谜题 | pending_decision=True, 返回谜题文字 |
| NODE-14 | `solve_puzzle` 已解谜题 | 跳过 | 返回 "这道谜题你已经解过了" |
| NODE-15 | `check_puzzle_answer` 正确答案 | 光之谜题答 "太阳" | solved_puzzles 增加, 获得卷轴 |
| NODE-16 | `check_puzzle_answer` 错误答案 | 答错 | pending_decision=True, 返回失败消息 |
| NODE-17 | `check_puzzle_answer` 请求提示 | 输入 "提示" | 返回 hint 内容 |
| NODE-18 | `move_player` 有效方向 | entrance → 北 → corridor | current_room="corridor" |
| NODE-19 | `move_player` 无效方向 | entrance → 南 | 返回错误消息，current_room 不变 |
| NODE-20 | `move_player` 上锁房间 | 无钥匙进宝库 | 返回 "🔒 这扇门被锁住了" |
| NODE-21 | `move_player` 有钥匙进锁房间 | 持有生锈的钥匙 | 允许进入 treasure_room |
| NODE-22 | `game_over_screen` 胜利 | game_won=True | 返回 "🏆 恭喜你" |
| NODE-23 | `game_over_screen` 失败 | game_won=False | 返回 "💀 冒险结束" |

### 2.5 graph（图的组装与路由）

| 测试ID | 测试项 | 验证点 | 预期结果 |
|--------|--------|--------|----------|
| GRAPH-01 | `build_graph()` 返回编译后的图 | 非 None, 可 invoked | 返回 CompiledStateGraph |
| GRAPH-02 | 所有节点已注册 | 9 个节点 | enter_room, pickup_items, initiate_combat, player_attack, flee_combat, solve_puzzle, check_puzzle, move_player, game_over |
| GRAPH-03 | 条件边 route_from_room | 战斗房间 → initiate_combat | current_room="goblin_den" → "initiate_combat" |
| GRAPH-04 | route_from_room 谜题房间 | puzzle_chamber → solve_puzzle | current_room="puzzle_chamber" → "solve_puzzle" |
| GRAPH-05 | route_from_room 宝物房间 | armory → pickup_items | current_room="armory" → "pickup_items" |
| GRAPH-06 | route_from_room 已清理战斗 | monster_hp=0 跳过战斗 | combat_active=False → "enter_room" |
| GRAPH-07 | route_combat_input "攻击" | 中文输入 | 返回 "player_attack" |
| GRAPH-08 | route_combat_input "flee" | 英文输入 | 返回 "flee_combat" |
| GRAPH-09 | route_after_combat 胜利 | 怪物死亡 | 返回 "enter_room" |
| GRAPH-10 | route_after_combat 失败 | player_hp=0 | 返回 "game_over" |
| GRAPH-11 | _route_user_input 战斗状态 | combat_active=True 输入 "打" | 返回 "player_attack" |
| GRAPH-12 | _route_user_input 移动命令 | 输入 "北" | 返回 "move_player" |
| GRAPH-13 | _route_user_input 拾取命令 | 输入 "拿" | 返回 "pickup_items" |
| GRAPH-14 | MemorySaver checkpointer | 编译图含 checkpointer | 可以保存/恢复状态快照 |

---

## 3. 集成测试：完整图流程

以下测试覆盖主要的游戏流程路径。

| 测试ID | 测试场景 | 路径 | 关键验证点 |
|--------|----------|------|------------|
| INT-01 | 起点探索 | entrance → enter_room → wait_for_input | 展示入口信息，3 个方向可选 |
| INT-02 | 进入黑暗走廊 | entrance → 北 → corridor | 到达 corridor，显示走廊描述 |
| INT-03 | 触发地精战斗 | corridor → 北 → goblin_den → initiate_combat | combat_active=True, 展示战斗信息 |
| INT-04 | 击败地精 | 攻击 → player_attack 循环直到 monster_hp=0 | 获得 "生锈的钥匙"，combat_active=False |
| INT-05 | 谜题密室流程 | goblin_den → 东 → puzzle_chamber → solve_puzzle | pending_decision=True，展示谜题 |
| INT-06 | 解开谜题 | 输入 "太阳" → check_puzzle_answer | 获得 "古老卷轴"，solved_puzzles 包含 riddle_of_light |
| INT-07 | 龙穴 Boss 战 | puzzle_chamber → 北 → dragon_lair → initiate_combat | monster_hp=60, monster_name="远古火龙" |
| INT-08 | 屠龙成功 | 多次 player_attack 直到龙 HP=0 | 获得 "龙之心"+"传说之盾"，combat_active=False |
| INT-09 | 胜利通关 | dragon_lair → 北 → exit_room → game_over | game_won=True, 胜利消息 |
| INT-10 | 拾取军械库物品 | entrance → 东 → armory → pickup_items | inventory 包含 "银剑"+"治疗药水" |
| INT-11 | 钥匙开门 | 拾取钥匙 → entrance → 西 → treasure_room | 允许进入宝库（有生锈的钥匙） |
| INT-12 | 无钥匙被挡 | entrance → 西 （无生锈的钥匙） | 返回 "🔒 这扇门被锁住了" |
| INT-13 | 逃跑流程 | 战斗中 → 输入 "逃跑" → flee_combat | combat_active=False |
| INT-14 | 玩家死亡 | player_hp 归零 | game_over=True, game_won=False |
| INT-15 | 完整通关路径 | entrance→corridor→goblin_den(战斗)→puzzle_chamber(解谜)→dragon_lair(战斗)→exit_room | game_won=True, 获得所有关键物品 |

---

## 4. Human-in-the-Loop 验证

| 测试ID | 测试项 | 验证点 | 预期结果 |
|--------|--------|--------|----------|
| HITL-01 | interrupt 暂停 | wait_for_input 节点 | 图执行暂停，等待外部输入 |
| HITL-02 | resume 恢复 | 传入用户输入后 resume | 图继续执行到对应节点 |
| HITL-03 | 谜题等待输入 | solve_puzzle → pending_decision=True | 状态标记等待决策 |
| HITL-04 | 错误答案重试 | 答错后继续等待 | pending_decision 保持 True，可再次输入 |
| HITL-05 | 输入提示功能 | 在谜题中输入 "提示" | 返回提示内容但不消耗谜题 |
| HITL-06 | checkpoint 恢复 | 中断后从 checkpoint 恢复 | 状态完整保留（HP/背包/位置） |

---

## 5. 边界条件与异常情况

| 测试ID | 测试项 | 输入/场景 | 预期行为 |
|--------|--------|-----------|----------|
| EDGE-01 | 空状态图调用 | GameState 缺少 current_room | 回退到 entrance，不崩溃 |
| EDGE-02 | 无效房间 ID | current_room="不存在的房间" | get_room 返回 None，节点安全处理 |
| EDGE-03 | 空背包使用物品 | use_item("任意", []) | 返回友好的 "背包中没有" |
| EDGE-04 | player_hp 为负数 | flee 失败伤害超过剩余 HP | player_hp 被 max(0, ...) 钳制为 0 |
| EDGE-05 | monster_hp 为负数 | 伤害超过剩余怪物 HP | monster_hp 被 max(0, ...) 钳制为 0 |
| EDGE-06 | 重复解同一谜题 | 已解谜题再次触发 | 返回 "你已经解过了"，不重复奖励 |
| EDGE-07 | 重复拾取物品 | 在已清空的 treasure room 拾取 | 返回 "这里已经没什么可拿的了" |
| EDGE-08 | 空消息列表 | 路由函数处理 messages=[] | _route_user_input 返回 "enter_room" |
| EDGE-09 | 特殊字符输入 | 用户输入 "/quit" 等 | 不被识别为有效命令，回退到 enter_room |
| EDGE-10 | 英文方向输入 | "north"/"n" 而非 "北" | _move_wrapper 正确映射 |
| EDGE-11 | 无出口房间 | exit_room.exits={} | move_player 对所有方向返回错误 |
| EDGE-12 | 已死亡怪物房间 | 地精击杀后重新进入 | route_from_room 跳过战斗 → enter_room |

---

## 6. 验证清单 Checklist

### 6.1 安装与构建

- [ ] `pip install -r requirements.txt` 无报错
- [ ] `python -m src.main` 可启动游戏
- [ ] `import langgraph` 版本 >= 0.4.0
- [ ] `pytest` 可正常运行

### 6.2 状态管理

- [ ] GameState 初始化包含全部 14 个字段
- [ ] messages 使用 add_messages reducer（追加而非覆盖）
- [ ] 普通字段使用默认覆盖策略
- [ ] 状态在各节点间正确传递（HP、背包、位置不丢失）

### 6.3 节点功能

- [ ] enter_room：展示正确房间信息（名称、描述、物品、出口、玩家状态）
- [ ] pickup_items：拾取物品后背包正确更新
- [ ] initiate_combat：正确初始化战斗状态
- [ ] player_attack：攻击计算合理，击杀后掉落物品
- [ ] flee_combat：逃跑概率合理，失败有惩罚
- [ ] solve_puzzle / check_puzzle_answer：谜题展示→回答→奖励流程正确
- [ ] move_player：方向验证、钥匙检查正确
- [ ] game_over_screen：胜/负消息不同

### 6.4 路由逻辑

- [ ] 战斗房间自动触发 initiate_combat
- [ ] 谜题房间自动触发 solve_puzzle
- [ ] 宝物房间自动触发 pickup_items
- [ ] 已清理的战斗/谜题不重复触发
- [ ] 用户输入正确分发到对应处理节点
- [ ] 移动命令中英文均支持

### 6.5 工具函数

- [ ] roll_dice 结果在有效范围
- [ ] calculate_damage 暴击/失误逻辑正确
- [ ] use_item 物品识别准确
- [ ] check_inventory 格式化正确

### 6.6 游戏数据

- [ ] 所有房间出口指向有效房间
- [ ] 所有怪物数据完整（名称、HP、攻击、台词、掉落）
- [ ] 所有物品数据完整（名称、emoji、描述、效果类型、效果值）
- [ ] 所有谜题数据完整（问题、答案、提示、奖励）

### 6.7 Human-in-the-Loop

- [ ] 战斗中和谜题中正确等待用户输入
- [ ] interrupt/resume 状态保持完整
- [ ] MemorySaver checkpoint 可正常存档/读档

### 6.8 游戏完整性

- [ ] 可从 entrance 胜利通关到 exit_room
- [ ] 存在多条可探索路径
- [ ] 死亡后有清晰提示
- [ ] 所有物品可使用且效果符合描述

---

## 7. 运行测试

```powershell
# 进入项目目录
cd langgraph-adventure

# 创建 tests 目录（首次）
New-Item -ItemType Directory -Path tests -Force
New-Item -ItemType File -Path tests\__init__.py -Force

# 激活虚拟环境后运行
.\.venv\Scripts\Activate.ps1

# 运行全部测试
pytest tests/ -v

# 运行特定模块
pytest tests/test_tools.py -v
pytest tests/test_nodes.py -v

# 运行集成测试
pytest tests/test_integration.py -v

# 带覆盖率报告（需先 pip install pytest-cov）
pytest tests/ -v --cov=src --cov-report=term-missing
```

### conftest.py（共享 fixtures 示例）

```python
# tests/conftest.py
import pytest
from src.state import GameState

@pytest.fixture
def base_state() -> GameState:
    """基础游戏状态 fixture"""
    return GameState(
        messages=[],
        current_room="entrance",
        player_hp=30,
        max_hp=30,
        player_attack=5,
        inventory=[],
        combat_active=False,
        monster_hp=0,
        monster_attack=0,
        monster_name="",
        solved_puzzles=[],
        game_over=False,
        game_won=False,
        pending_decision=False,
    )

@pytest.fixture
def combat_state(base_state) -> GameState:
    """战斗中的状态 fixture"""
    state = dict(base_state)
    state.update(
        current_room="goblin_den",
        combat_active=True,
        monster_hp=20,
        monster_attack=4,
        monster_name="地精守卫",
    )
    return GameState(**state)
```

---

## 📊 测试覆盖矩阵

| 模块 | 单元测试数 | 集成测试数 | 覆盖目标 |
|------|-----------|-----------|----------|
| adventure_data.py | 12 | — | 100% |
| state.py | 5 | — | 100% |
| tools.py | 12 | — | 100% |
| nodes.py | 23 | — | ≥95% |
| graph.py | 14 | — | ≥90% |
| 集成测试 | — | 15 | 核心路径 100% |
| **总计** | **66** | **15** | — |

---

*文档版本: v1.0 | 更新日期: 2026-06-04 | 适用项目: langgraph-adventure*


