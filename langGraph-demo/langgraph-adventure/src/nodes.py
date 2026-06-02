"""
═══════════════════════════════════════════════════════════════
  🏰 AI 地牢探险 — src/nodes.py
  LangGraph 学习要点：Node（节点函数）与图计算
═══════════════════════════════════════════════════════════════
每个节点是一个纯函数，签名统一为：
    def node_name(state: GameState) -> dict:
        ...
        return {"field": new_value, ...}

核心概念：
1. 节点是图中的"处理单元"
2. 接收完整 state，返回 partial state update
3. 返回的 dict 会与当前状态合并（按 reducer 策略）
4. 节点不直接调用下一个节点——由图的边（edge）决定路由
"""
from __future__ import annotations

import random
from typing import Dict, Any

from adventure_data import (
    ROOMS, MONSTERS, ITEMS, PUZZLES,
    get_room, get_monster, get_item, describe_inventory,
)
from state import GameState


# ═══════════════════════════════════════════════════════════════
# 辅助：格式化房间信息为可读文本
# ═══════════════════════════════════════════════════════════════
def _format_room(room_id: str, state: GameState) -> str:
    """将房间数据 + 玩家状态格式化为人类可读的文本。"""
    room = get_room(room_id)
    if not room:
        return f"⚠️ 未知区域: {room_id}"

    lines = [
        f"\n{'='*50}",
        f"  {room.emoji}  {room.name}",
        f"{'='*50}",
        room.description,
        "",
    ]

    # 物品
    if room.items:
        items_str = "\n".join(f"    • {get_item(n).emoji} {n}" for n in room.items if get_item(n))
        lines.append(f"📦 地上的物品:\n{items_str}")
        lines.append("")

    # 出口
    if room.exits:
        exits_str = "  |  ".join(f"{dir_} → {get_room(rid).name}" for dir_, rid in room.exits.items() if get_room(rid))
        lines.append(f"🚶 可走的方向: {exits_str}")
        lines.append("")

    # 玩家状态栏
    hp_bar = "█" * (state.get("player_hp", 0) // 5) + "░" * ((state.get("max_hp", 30) - state.get("player_hp", 0)) // 5)
    lines.append(f"❤️  生命: [{hp_bar}] {state.get('player_hp', 0)}/{state.get('max_hp', 30)}")
    lines.append(f"⚔️  攻击: {state.get('player_attack', 5)}")
    lines.append(f"🎒 背包: {describe_inventory(state.get('inventory', []))}")
    lines.append("")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# 节点函数
# ═══════════════════════════════════════════════════════════════

def enter_room(state: GameState) -> dict:
    """🏠 进入房间节点 —— 展示当前房间信息，等待玩家选择动作。

    这是游戏的主循环入口。每到达一个新房间都会经过这个节点。
    它不修改状态，只是展示信息。

    思考：为什么这个节点不直接调用下一个节点？
    → 因为 LangGraph 的边（edge）负责流程控制，节点只负责"计算"。
    """
    room_id = state.get("current_room", "entrance")
    room = get_room(room_id)
    if not room:
        return {"current_room": "entrance"}

    room_text = _format_room(room_id, state)
    return {"messages": [("ai", room_text)]}


def pickup_items(state: GameState) -> dict:
    """📦 拾取物品节点 —— 自动收集当前房间的所有物品。

    学习要点：这个节点展示了如何读取和修改 state。
    - 读取 state["current_room"] 找到房间
    - 读取 state["inventory"] 获取背包
    - 返回更新后的 inventory（追加新物品）
    """
    room_id = state.get("current_room", "")
    room = get_room(room_id)
    if not room or not room.items:
        return {}

    current_inv = state.get("inventory", [])
    new_items = [name for name in room.items if name not in current_inv]

    if not new_items:
        return {"messages": [("ai", "这里已经没什么可拿的了。")]}

    # 更新背包（追加新物品）
    updated_inv = current_inv + new_items
    items_str = "、".join(f"{get_item(n).emoji}{n}" for n in new_items if get_item(n))
    return {
        "inventory": updated_inv,
        "messages": [("ai", f"🎒 你拾取了: {items_str}")],
    }


def initiate_combat(state: GameState) -> dict:
    """⚔️ 战斗初始化节点 —— 检测到怪物时进入战斗状态。

    学习要点：条件触发 —— 节点根据 state 决定是否激活。
    这里设置 combat_active=True 和怪物的初始状态。
    """
    room_id = state.get("current_room", "")
    room = get_room(room_id)
    if not room or not room.monster_id:
        return {"combat_active": False}

    monster = get_monster(room.monster_id)
    if not monster:
        return {"combat_active": False}

    taunt = monster.random_taunt()
    return {
        "combat_active": True,
        "monster_hp": monster.hp,
        "monster_attack": monster.attack,
        "monster_name": monster.name,
        "messages": [
            ("ai", f"\n⚔️ 战斗开始！{monster.emoji} **{monster.name}** 出现了！"),
            ("ai", f'{taunt}\n  ❤️ 怪物生命: {monster.hp}  |  ⚔️ 怪物攻击: {monster.attack}'),
        ],
    }


def player_attack(state: GameState) -> dict:
    """⚔️ 玩家攻击节点 —— 执行一次玩家攻击回合。

    战斗流程：
    1. 掷 D20 判定命中
    2. 根据判定计算伤害
    3. 检查怪物是否被击败
    4. 如果击败，掉落物品、结束战斗

    学习要点：节点中的业务逻辑如何组织。
    每个回合是一个独立的节点执行，由循环边控制。
    """
    player_atk = state.get("player_attack", 5)
    monster_hp = state.get("monster_hp", 0)
    monster_atk = state.get("monster_attack", 0)
    monster_name = state.get("monster_name", "怪物")

    # 1. 攻击判定
    dice = random.randint(1, 20)
    if dice == 1:
        # 大失败
        return {
            "messages": [("ai", f"💥 **攻击失误！** 你挥空了。D20={dice}")],
        }

    # 2. 伤害计算
    if dice >= 18:
        damage = player_atk * 2 + random.randint(1, 6)
        msg = f"💥 **暴击！** D20={dice}，造成 {damage} 点伤害！"
    else:
        damage = player_atk + random.randint(-2, 3)
        damage = max(1, damage)
        msg = f"⚔️ D20={dice}，造成 {damage} 点伤害。"

    monster_hp -= damage

    # 3. 检查击杀
    if monster_hp <= 0:
        monster_hp = 0
        room = get_room(state.get("current_room", ""))
        monster = get_monster(room.monster_id) if room else None
        defeat_msg = monster.defeat_msg if monster else "怪物被击败了！"

        # 掉落物品
        loot = monster.loot if monster else []
        current_inv = state.get("inventory", [])
        new_loot = [l for l in loot if l not in current_inv]
        updated_inv = current_inv + new_loot

        loot_str = "、".join(f"{get_item(l).emoji}{l}" for l in new_loot if get_item(l)) if new_loot else "无"

        return {
            "monster_hp": 0,
            "combat_active": False,
            "inventory": updated_inv,
            "messages": [
                ("ai", f"{msg}\n💀 {defeat_msg}"),
                ("ai", f"🎁 掉落物品: {loot_str}"),
            ],
        }

    # 4. 怪物存活，触发怪物反击
    counter_damage = monster_atk + random.randint(-1, 2)
    counter_damage = max(1, counter_damage)

    # 检查是否有传说之盾（伤害减半）
    if "传说之盾" in state.get("inventory", []):
        counter_damage = max(1, counter_damage // 2)
        shield_msg = "（🛡️ 传说之盾减半！）"
    else:
        shield_msg = ""

    player_hp = state.get("player_hp", 30) - counter_damage

    if player_hp <= 0:
        player_hp = 0
        return {
            "monster_hp": monster_hp,
            "player_hp": 0,
            "game_over": True,
            "combat_active": False,
            "messages": [
                ("ai", f"{msg}\n💢 {monster_name} 反击造成 {counter_damage} 点伤害！{shield_msg}"),
                ("ai", "💀 **你被击败了……游戏结束。** "),
            ],
        }

    return {
        "monster_hp": monster_hp,
        "player_hp": player_hp,
        "messages": [
            ("ai", f"{msg}"),
            ("ai", f"💢 {monster_name} 反击造成 {counter_damage} 点伤害！{shield_msg}"),
            ("ai", f"  ❤️ 你的生命: {player_hp}/{state.get('max_hp', 30)}  |  👹 怪物: {monster_hp}"),
        ],
    }


def flee_combat(state: GameState) -> dict:
    """🏃 逃跑节点 —— 尝试逃离战斗。

    学习要点：不是所有节点都修改核心状态。
    这个节点只是改变 combat_active 标记 + 添加消息。
    """
    dice = random.randint(1, 20)
    if dice >= 10:
        return {
            "combat_active": False,
            "messages": [("ai", f"🏃 你成功逃脱了！（D20={dice}）")],
        }
    else:
        # 逃跑失败，受到惩罚
        damage = random.randint(3, 8)
        player_hp = max(0, state.get("player_hp", 30) - damage)
        if player_hp <= 0:
            return {
                "player_hp": 0,
                "game_over": True,
                "combat_active": False,
                "messages": [("ai", f"💀 逃跑失败！{state.get('monster_name', '怪物')} 趁机造成 {damage} 点伤害，你倒下了……")],
            }
        return {
            "player_hp": player_hp,
            "combat_active": False,
            "messages": [("ai", f"🏃 逃跑失败！（D20={dice}）受到 {damage} 点伤害。当前生命: {player_hp}")],
        }


def solve_puzzle(state: GameState) -> dict:
    """🧩 谜题节点 —— 展示谜题并等待玩家回答。

    学习要点：human-in-the-loop 模式。
    这个节点展示谜题，设置 pending_decision=True，
    然后等待外部输入（玩家答案）再继续。
    """
    room_id = state.get("current_room", "")
    room = get_room(room_id)
    if not room or not room.puzzle_id:
        return {}

    puzzle = PUZZLES.get(room.puzzle_id)
    if not puzzle:
        return {}

    solved = state.get("solved_puzzles", [])
    if room.puzzle_id in solved:
        return {"messages": [("ai", "这道谜题你已经解过了。")]}

    return {
        "pending_decision": True,
        "messages": [
            ("ai", puzzle.question),
            ("ai", f"（提示：输入你的答案。如果需要提示，说「提示」）"),
        ],
    }


def check_puzzle_answer(state: GameState, user_input: str) -> dict:
    """🧩 检查谜题答案 —— 由 interrupt 恢复后调用。

    学习要点：这是 interrupt → 外部输入 → resume 的标准流程。
    """
    room_id = state.get("current_room", "")
    room = get_room(room_id)
    if not room or not room.puzzle_id:
        return {}

    puzzle = PUZZLES.get(room.puzzle_id)
    if not puzzle:
        return {}

    user_input = user_input.strip()

    # 请求提示
    if user_input in ("提示", "hint"):
        return {
            "messages": [("ai", f"💡 提示：{puzzle.hint}")],
            "pending_decision": True,  # 继续等待
        }

    # 检查答案
    if user_input == puzzle.answer:
        solved = list(state.get("solved_puzzles", []))
        solved.append(room.puzzle_id)

        # 奖励
        current_inv = state.get("inventory", [])
        new_items = [l for l in puzzle.reward if l not in current_inv]
        updated_inv = current_inv + new_items

        reward_str = "、".join(f"{get_item(i).emoji}{i}" for i in new_items if get_item(i))

        return {
            "solved_puzzles": solved,
            "inventory": updated_inv,
            "pending_decision": False,
            "messages": [
                ("ai", f"✅ {puzzle.success_msg}"),
                ("ai", f"🎁 获得奖励: {reward_str}"),
            ],
        }
    else:
        return {
            "messages": [("ai", f"❌ {puzzle.fail_msg}")],
            "pending_decision": True,  # 继续等待
        }


def move_player(state: GameState, direction: str) -> dict:
    """🚶 移动节点 —— 处理玩家移动请求。

    学习要点：节点中调用辅助函数，保持代码清晰。
    移动时检查：
    1. 方向是否存在
    2. 目标房间是否上锁
    3. 是否有对应钥匙
    """
    room_id = state.get("current_room", "")
    room = get_room(room_id)
    if not room:
        return {}

    # 检查方向是否存在
    if direction not in room.exits:
        return {
            "messages": [("ai", f"❌ 这里没有通往「{direction}」方向的路。可用方向: {', '.join(room.exits.keys())}")],
        }

    target_id = room.exits[direction]
    target = get_room(target_id)
    if not target:
        return {}

    # 检查目标房间是否上锁
    if target.locked:
        required_key = target.required_key
        inventory = state.get("inventory", [])
        if required_key and required_key not in inventory:
            return {
                "messages": [("ai", f"🔒 这扇门被锁住了！需要 **{required_key}** 才能打开。")],
            }

    return {
        "current_room": target_id,
        "combat_active": False,
        "pending_decision": False,
    }


def game_over_screen(state: GameState) -> dict:
    """💀 游戏结束节点 —— 展示结束画面。"""
    if state.get("game_won", False):
        msg = f"""
{'='*50}
  🏆  恭喜你！你成功逃出了地牢！
  屠龙勇士的传说将永远流传……
{'='*50}
"""
    else:
        msg = f"""
{'='*50}
  💀  冒险结束
  你的故事到此为止……但另一个冒险者
  或许能继承你的意志，继续前行。
{'='*50}
"""
    return {"messages": [("ai", msg)], "game_over": True}
