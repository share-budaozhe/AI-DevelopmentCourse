# ─────────────────────────────────────────────────────────────
#  🏰 AI 地牢探险 — src/state.py
#   LangGraph 核心：状态定义 (TypedDict + Annotated)
# ─────────────────────────────────────────────────────────────
"""
═══════════════════════════════════════════════════════════════
  学习要点：LangGraph 的 State（状态管理）
═══════════════════════════════════════════════════════════════
LangGraph 用 TypedDict 定义图的状态。状态是图
中所有节点共享的"记忆"。每个节点读取状态、
做出决策、然后返回状态的更新部分。

关键概念：
1. TypedDict — 类型安全的状态字典
2. Annotated — 定义 reducer（合并策略）
3. add_messages — 内置的 messages reducer（追加而非覆盖）
4. 普通字段 — 默认覆盖策略（用新值替换旧值）
"""
from __future__ import annotations

import operator
from typing import Annotated, List, Optional, TypedDict

from langgraph.graph.message import add_messages


class GameState(TypedDict, total=False):
    """
    🎮 游戏全局状态 —— LangGraph 状态定义
    
    这个 TypedDict 定义了整个游戏图的状态结构。
    所有节点函数都接收和返回这个状态（或部分更新）。
    
    字段说明：
    ┌─────────────────────┬──────────────────────────────────┐
    │ messages            │ 对话历史，使用 add_messages      │
    │                     │ reducer 自动追加，不会覆盖      │
    ├─────────────────────┼──────────────────────────────────┤
    │ current_room        │ 当前所在房间ID                    │
    │ player_hp / max_hp  │ 玩家生命值 / 最大生命值           │
    │ player_attack       │ 玩家基础攻击力                    │
    │ inventory           │ 背包（物品名列表）                │
    │ combat_active       │ 是否处于战斗状态                  │
    │ monster_hp          │ 当前怪物生命值                    │
    │ solved_puzzles      │ 已解谜题ID集合                    │
    │ game_over           │ 游戏是否结束                      │
    │ game_won            │ 是否胜利                          │
    │ pending_decision    │ 等待玩家决策的标志                │
    └─────────────────────┴──────────────────────────────────┘
    """
    # ═══════════════════════════════════════════════════════
    # messages 使用 add_messages reducer：
    # 这是 LangGraph 的内置合并策略——新消息会追加到列表，
    # 而不会覆盖旧的。这对构建对话历史至关重要。
    # ═══════════════════════════════════════════════════════
    messages: Annotated[list, add_messages]

    # ═══════════════════════════════════════════════════════
    # 以下字段使用默认覆盖策略：
    # 节点返回的新值会完全替换旧值。
    # ═══════════════════════════════════════════════════════
    current_room: str
    player_hp: int
    max_hp: int
    player_attack: int
    inventory: List[str]
    combat_active: bool
    monster_hp: int
    monster_attack: int
    monster_name: str
    solved_puzzles: List[str]
    game_over: bool
    game_won: bool
    pending_decision: Annotated[bool, operator.or_]
