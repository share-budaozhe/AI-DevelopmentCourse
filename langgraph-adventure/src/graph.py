"""
═══════════════════════════════════════════════════════════════
  🏰 AI 地牢探险 — src/graph.py
  LangGraph 核心学习要点：Graph（图的组装与路由）
═══════════════════════════════════════════════════════════════
这是整个 LangGraph Demo 的灵魂所在——
展示如何把"节点"和"边"组装成一个有状态的计算图。

核心概念全在这里：
1. StateGraph — 有状态的图定义
2. add_node — 注册节点函数
3. add_edge — 固定边（无条件）
4. add_conditional_edges — 条件路由
5. SET_START / END — 图的入口和出口
6. interrupt — 人工介入（Human-in-the-Loop）
7. compile — 编译为可运行的应用
"""
from __future__ import annotations

from typing import Literal

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt

from state import GameState
from nodes import (
    enter_room,
    pickup_items,
    initiate_combat,
    player_attack,
    flee_combat,
    solve_puzzle,
    check_puzzle_answer,
    move_player,
    game_over_screen,
)
from adventure_data import get_room


# ═══════════════════════════════════════════════════════════════
# 条件路由函数
# ═══════════════════════════════════════════════════════════════

def route_from_room(state: GameState) -> Literal[
    "initiate_combat", "solve_puzzle", "pickup_items", "enter_room"
]:
    """🚦 房间路由：根据房间类型决定下一个节点。

    这是 **条件边** 的核心示例。
    LangGraph 调用这个函数，根据返回值选择下一条边。

    学习要点：
    - 函数签名 (state) -> str
    - 返回的字符串必须是已注册的节点名
    - 这是实现"分支逻辑"的标准方式
    """
    room_id = state.get("current_room", "")
    room = get_room(room_id)
    if not room:
        return "enter_room"

    room_type = room.room_type

    # 特殊检查：出口直接结束
    if room_type == "exit":
        return "enter_room"

    # 战斗房间
    if room_type in ("combat", "boss") and room.monster_id:
        # 怪物还在吗？（已被击杀则跳过战斗）
        monster_hp = state.get("monster_hp", 999)
        combat_active = state.get("combat_active", False)
        if monster_hp > 0 and not combat_active:
            return "initiate_combat"

    # 谜题房间
    if room_type == "puzzle" and room.puzzle_id:
        solved = state.get("solved_puzzles", [])
        if room.puzzle_id not in solved:
            return "solve_puzzle"

    # 宝物房间（有物品可拿）
    if room_type == "treasure" and room.items:
        current_inv = state.get("inventory", [])
        if any(item not in current_inv for item in room.items):
            return "pickup_items"

    return "enter_room"


def route_after_enter(state: GameState) -> Literal["END", "wait_for_input"]:
    """🚦 进入房间后的路由：判断是否需要等待玩家输入。

    学习要点：
    - 这是一种"元路由"——决定是否需要人机交互
    - route_to END 表示图运行结束（等待外部输入）
    """
    room = get_room(state.get("current_room", ""))
    if room and room.room_type == "exit":
        return "END"

    if state.get("game_over", False):
        return "END"

    return "wait_for_input"


def route_combat_input(state: GameState, user_input: str) -> Literal[
    "player_attack", "flee_combat", "use_item_combat"
]:
    """🚦 战斗输入路由：根据玩家输入决定战斗动作。

    学习要点：条件路由可以基于外部输入（Human-in-the-Loop）。
    """
    user_input = user_input.strip().lower()

    if user_input in ("攻击", "attack", "a", "打"):
        return "player_attack"
    elif user_input in ("逃跑", "flee", "f", "跑"):
        return "flee_combat"
    elif user_input in ("物品", "道具", "item", "i", "使用"):
        return "use_item_combat"
    else:
        # 默认攻击
        return "player_attack"


def route_after_combat(state: GameState) -> Literal["game_over", "enter_room"]:
    """🚦 战斗结束后的路由：检查是否游戏结束。"""
    if state.get("game_over", False):
        return "game_over"
    if state.get("player_hp", 0) <= 0:
        return "game_over"
    return "enter_room"


# ═══════════════════════════════════════════════════════════════
# Interrupt 节点（Human-in-the-Loop 的入口点）
# ═══════════════════════════════════════════════════════════════

def wait_for_input(state: GameState) -> dict:
    """⏸️  暂停节点 —— 等待玩家输入。

    这是 **Human-in-the-Loop** 的核心实现。
    调用 interrupt() 会暂停图执行，返回给外部调用者。
    当外部调用 graph.invoke(Command(resume=...), ...) 时，
    图从这一点恢复执行。

    学习要点：
    - interrupt() 是 LangGraph 的"断点"机制
    - 外部程序可以读取当前状态、展示给用户
    - 用户输入后通过 Command(resume=...) 恢复执行
    """
    user_input = interrupt("请选择你的动作：")

    # 返回用户输入供后续节点使用
    return {
        "messages": [("user", user_input)],
        "pending_decision": False,
    }


# ═══════════════════════════════════════════════════════════════
# 构建图
# ═══════════════════════════════════════════════════════════════

def build_adventure_graph() -> StateGraph:
    """🔧 构建地牢探险的 LangGraph 图。

    图结构如下：

    SET_START
       │
       ▼
    enter_room ──(条件: room type)──→ initiate_combat / solve_puzzle / pickup_items
       │                                    │              │               │
       │◄───────────────────────────────────┘              │               │
       │                                                  │               │
       ├──(条件: 需要输入?)──→ wait_for_input             │               │
       │                         │                         │               │
       │                    (外部输入)                      │               │
       │                         │                         │               │
       ├──(条件: 移动/查看/战斗...)──→ move_player / player_attack ...
       │
       ▼
      END
    """
    # ── 1. 创建 StateGraph ──
    #     指定状态类型和状态模式
    graph = StateGraph(GameState)

    # ── 2. 注册节点 ──
    #     每个节点对应一个处理函数
    graph.add_node("enter_room", enter_room)
    graph.add_node("pickup_items", pickup_items)
    graph.add_node("initiate_combat", initiate_combat)
    graph.add_node("player_attack", player_attack)
    graph.add_node("flee_combat", flee_combat)
    graph.add_node("solve_puzzle", solve_puzzle)
    graph.add_node("move_player", _move_wrapper)        # 需要用户输入的包装
    graph.add_node("game_over", game_over_screen)
    graph.add_node("wait_for_input", wait_for_input)     # interrupt 节点
    graph.add_node("check_puzzle", _puzzle_wrapper)       # 谜题答案检查

    # ── 3. 设置入口 ──
    graph.set_entry_point("enter_room")

    # ── 4. 添加条件边（房间路由）──
    graph.add_conditional_edges(
        "enter_room",
        route_from_room,
        {
            "initiate_combat": "initiate_combat",
            "solve_puzzle": "solve_puzzle",
            "pickup_items": "pickup_items",
            "enter_room": "enter_room",
        },
    )

    # ── 5. 战斗相关的边 ──
    graph.add_edge("initiate_combat", "enter_room")     # 战斗初始化后返回房间展示

    # player_attack / flee_combat 后：检查是否需要 game_over
    for node_name in ["player_attack", "flee_combat"]:
        graph.add_conditional_edges(
            node_name,
            route_after_combat,
            {"enter_room": "enter_room", "game_over": "game_over"},
        )

    # ── 6. 拾取物品后返回房间 ──
    graph.add_edge("pickup_items", "enter_room")

    # ── 7. 谜题 → 检查答案 → 返回房间 ──
    graph.add_edge("solve_puzzle", "enter_room")
    graph.add_edge("check_puzzle", "enter_room")

    # ── 8. 移动后返回房间 ──
    graph.add_edge("move_player", "enter_room")

    # ── 9. 游戏结束 → END ──
    graph.add_edge("game_over", END)

    # ── 10. 条件边：是否需要等待输入 ──
    graph.add_conditional_edges(
        "enter_room",
        route_after_enter,
        {"END": END, "wait_for_input": "wait_for_input"},
    )

    # ── 11. wait_for_input 后路由（根据用户输入分发）──
    #     这里使用一个特殊的条件路由
    #     注意：wait_for_input 本身包含 interrupt()
    #     resume 后的输入由外部调用者传入
    graph.add_conditional_edges(
        "wait_for_input",
        _route_user_input,
        {
            "move_player": "move_player",
            "player_attack": "player_attack",
            "flee_combat": "flee_combat",
            "check_puzzle": "check_puzzle",
            "enter_room": "enter_room",
            "pickup_items": "pickup_items",
            "game_over": "game_over",
        },
    )

    # ── 12. 编译图（带内存检查点）──
    memory = MemorySaver()
    compiled = graph.compile(checkpointer=memory)

    return compiled


# ═══════════════════════════════════════════════════════════════
# 包装器：处理用户输入
# ═══════════════════════════════════════════════════════════════

def _route_user_input(state: GameState) -> str:
    """根据用户最后一条消息路由到对应的处理节点。

    这是 Human-in-the-Loop 路由的核心——
    读取 state 中用户最后输入的消息，然后分发。
    """
    messages = state.get("messages", [])
    if not messages:
        return "enter_room"

    # 获取最后一条用户消息
    user_input = ""
    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type == "human":
            user_input = msg.content
            break
        elif isinstance(msg, tuple) and msg[0] == "user":
            user_input = msg[1]
            break

    user_input = user_input.strip()

    # 检查是否在战斗中
    if state.get("combat_active", False):
        cmd = user_input.lower()
        if cmd in ("逃跑", "flee", "f", "跑"):
            return "flee_combat"
        elif cmd in ("攻击", "attack", "a", "打", ""):
            return "player_attack"
        else:
            return "player_attack"  # 默认攻击

    # 检查是否在解谜中
    if state.get("pending_decision", False):
        return "check_puzzle"

    # 普通移动命令
    direction_map = {
        "北": "北", "north": "北", "n": "北",
        "南": "南", "south": "南", "s": "南",
        "东": "东", "east": "东", "e": "东",
        "西": "西", "west": "西", "w": "西",
    }

    cmd_lower = user_input.lower()
    room = get_room(state.get("current_room", ""))
    if room:
        for dir_name in room.exits:
            if cmd_lower in (dir_name, dir_name.lower()):
                return "move_player"
        # 检查英文简写
        mapped = direction_map.get(cmd_lower)
        if mapped and mapped in room.exits:
            return "move_player"

    # 拾取物品
    if cmd_lower in ("拿", "捡", "拾取", "take", "get", "拾"):
        return "pickup_items"

    # 默认：展示房间
    return "enter_room"


def _move_wrapper(state: GameState) -> dict:
    """🚶 移动包装器 —— 提取用户输入中的方向并移动。"""
    messages = state.get("messages", [])
    user_input = ""
    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type == "human":
            user_input = msg.content
            break
        elif isinstance(msg, tuple) and msg[0] == "user":
            user_input = msg[1]
            break

    # 解析方向
    direction_map = {
        "北": "北", "north": "北", "n": "北",
        "南": "南", "south": "南", "s": "南",
        "东": "东", "east": "东", "e": "东",
        "西": "西", "west": "西", "w": "西",
    }
    direction = direction_map.get(user_input.strip().lower(), user_input.strip())
    return move_player(state, direction)


def _puzzle_wrapper(state: GameState) -> dict:
    """🧩 谜题检查包装器 —— 提取用户输入中的答案。"""
    messages = state.get("messages", [])
    user_input = ""
    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type == "human":
            user_input = msg.content
            break
        elif isinstance(msg, tuple) and msg[0] == "user":
            user_input = msg[1]
            break
    return check_puzzle_answer(state, user_input)
