#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════
  🏰 AI 地牢探险 — main.py （游戏入口）
  LangGraph Demo：用状态图驱动的文字冒险游戏
═══════════════════════════════════════════════════════════════

运行方式：
    python -m src.main

游戏命令：
    移动：北 / 南 / 东 / 西 （或 n/s/e/w / north/south/east/west）
    战斗：攻击 / 逃跑
    交互：拿 / 捡 （拾取物品）
    其他：背包 / 状态 / 帮助 / 退出

═══════════════════════════════════════════════════════════════
  学习要点：main.py 展示如何与编译后的 LangGraph 应用交互
───────────────────────────────────────────────────────────────
1. 初始化状态 → graph.invoke(state, config)
2. Human-in-the-Loop → graph.invoke(Command(resume=...), config)
3. 检查点 → config["configurable"]["thread_id"] 保持状态
4. 流式输出 → graph.stream() 可选
═══════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import sys
import os
import uuid

# 确保 src 目录在路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.types import Command

from state import GameState
from graph import build_adventure_graph


# ═══════════════════════════════════════════════════════════════
# 初始游戏状态
# ═══════════════════════════════════════════════════════════════
INITIAL_STATE: GameState = {
    "messages": [],
    "current_room": "entrance",
    "player_hp": 30,
    "max_hp": 30,
    "player_attack": 5,
    "inventory": [],
    "combat_active": False,
    "monster_hp": 0,
    "monster_attack": 0,
    "monster_name": "",
    "solved_puzzles": [],
    "game_over": False,
    "game_won": False,
    "pending_decision": False,
}


# ═══════════════════════════════════════════════════════════════
# 消息显示工具
# ═══════════════════════════════════════════════════════════════
def print_message(msg) -> None:
    """将 LangGraph 消息格式化打印到终端。"""
    if hasattr(msg, "content") and hasattr(msg, "type"):
        if msg.type == "ai":
            print(msg.content)
        elif msg.type == "human":
            print(f"\n🧑 冒险者: {msg.content}")
    elif isinstance(msg, tuple):
        role, content = msg[0], msg[1]
        if role == "ai":
            print(content)
        elif role == "user":
            print(f"\n🧑 冒险者: {content}")


def print_banner() -> None:
    """打印游戏标题画面。"""
    banner = """
╔══════════════════════════════════════════════════════╗
║                                                      ║
║   🏰  AI 地牢探险 · Dragon's Lair                   ║
║                                                      ║
║   一个由 LangGraph 状态图驱动的交互式文字冒险        ║
║                                                      ║
║   在这座古老的地牢中，你将面对：                    ║
║     👹 地精守卫                                     ║
║     💀 骷髅骑士                                     ║
║     🐉 远古火龙                                     ║
║                                                      ║
║   你的目标：击败火龙，逃出生天！                    ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
"""
    print(banner)


def print_help() -> None:
    """打印帮助信息。"""
    help_text = """
🎮 可用命令：
  ┌──────────────────────────────────────────────────┐
  │ 移动    │ 北 / 南 / 东 / 西                      │
  │         │ n / s / e / w                          │
  │         │ north / south / east / west             │
  ├──────────────────────────────────────────────────┤
  │ 战斗    │ 攻击 / a / attack                      │
  │         │ 逃跑 / f / flee                        │
  ├──────────────────────────────────────────────────┤
  │ 交互    │ 拿 / 捡 / take                         │
  │         │ 提示（解谜时）                         │
  ├──────────────────────────────────────────────────┤
  │ 系统    │ 背包 / inventory                       │
  │         │ 状态 / status                          │
  │         │ 帮助 / help / ?                        │
  │         │ 退出 / quit / exit                     │
  └──────────────────────────────────────────────────┘
"""
    print(help_text)


# ═══════════════════════════════════════════════════════════════
# 游戏主循环
# ═══════════════════════════════════════════════════════════════

def run_game() -> None:
    """🏰 游戏主循环 —— 展示 LangGraph 的人机交互模式。

    流程：
    1. 初始化图
    2. invoke(initial_state) → 图运行到 interrupt() 暂停
    3. 显示暂停位置的输出
    4. 等待用户输入
    5. invoke(Command(resume=user_input)) → 恢复执行
    6. 重复 3-5 直到游戏结束

    这是 Human-in-the-Loop 的经典模式：
    - interrupt() 暂停 → 外部展示 → 用户输入 → resume 继续
    """
    print_banner()
    print_help()
    print("\n" + "=" * 50)
    print("  游戏开始！你站在地牢入口……")
    print("=" * 50 + "\n")

    # ── 构建图 ──
    app = build_adventure_graph()

    # ── 配置检查点 ──
    #     每个游戏会话使用独立的 thread_id
    #     这是 LangGraph 持久化的关键
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # ── 启动游戏：首次 invoke ──
    current_state = app.invoke(INITIAL_STATE, config)

    # 显示初始房间
    for msg in current_state.get("messages", []):
        print_message(msg)

    # ── 主循环：Human-in-the-Loop ──
    while True:
        # 检查游戏是否结束
        if current_state.get("game_over", False):
            print("\n🌟 感谢游玩！再见，冒险者。")
            break

        # 获取玩家输入
        try:
            user_input = input("\n🎯 你想做什么？> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n👋 冒险中断，再见！")
            break

        # 处理系统命令
        cmd = user_input.lower()
        if cmd in ("退出", "quit", "exit", "q"):
            print("👋 再见，冒险者！")
            break
        elif cmd in ("帮助", "help", "?"):
            print_help()
            continue
        elif cmd in ("背包", "inventory", "i", "inv"):
            inv = current_state.get("inventory", [])
            if inv:
                print("🎒 你的背包:")
                for name in inv:
                    from adventure_data import get_item
                    item = get_item(name)
                    if item:
                        print(f"  {item.emoji} {name} — {item.description}")
            else:
                print("🎒 背包空空如也。")
            continue
        elif cmd in ("状态", "status"):
            hp = current_state.get("player_hp", 0)
            max_hp = current_state.get("max_hp", 30)
            atk = current_state.get("player_attack", 5)
            room_id = current_state.get("current_room", "")
            from adventure_data import get_room
            room = get_room(room_id)
            room_name = room.name if room else "未知"
            print(f"  ❤️  生命: {hp}/{max_hp}")
            print(f"  ⚔️  攻击: {atk}")
            print(f"  📍 位置: {room_name}")
            continue

        # ── 恢复图执行：传递用户输入 ──
        try:
            current_state = app.invoke(
                Command(resume=user_input),
                config,
            )
        except Exception as e:
            print(f"⚠️ 出了点问题: {e}")
            continue

        # 显示新增的消息
        for msg in current_state.get("messages", []):
            print_message(msg)


if __name__ == "__main__":
    run_game()
