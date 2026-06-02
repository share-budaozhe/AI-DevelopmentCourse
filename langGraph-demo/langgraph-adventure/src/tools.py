"""
═══════════════════════════════════════════════════════════════
  🏰 AI 地牢探险 — src/tools.py
  LangGraph 学习要点：Tool 集成（工具调用）
═══════════════════════════════════════════════════════════════
LangGraph 中，工具是"外部能力"的封装。Agent 节点可以
调用工具来执行计算、获取数据或执行副作用操作。

在本 demo 中，工具模拟了 RPG 游戏的动作：
- roll_dice：战斗中的随机骰子
- calculate_damage：伤害计算
- use_item：使用物品
- check_inventory：查看背包

核心概念：
1. @tool 装饰器 — 定义可被 LLM 调用的工具
2. ToolNode — 将工具列表转为可执行图节点
3. tools_condition — 条件路由：判断是否需要调用工具
"""
from __future__ import annotations

import random
from typing import List

from langchain_core.tools import tool


@tool
def roll_dice(sides: int = 20, times: int = 1) -> str:
    """🎲 掷骰子，返回结果。

    Args:
        sides: 骰子面数（默认D20）
        times: 掷几次

    Returns:
        掷骰结果描述字符串
    """
    results = [random.randint(1, sides) for _ in range(times)]
    total = sum(results)

    if times == 1:
        if results[0] == sides:
            return f"🎲 D{sides}: **{results[0]}** —— 满值！大成功！🌟"
        elif results[0] == 1:
            return f"🎲 D{sides}: **{results[0]}** —— 大失败！💥"
        elif results[0] >= sides * 0.8:
            return f"🎲 D{sides}: **{results[0]}** —— 不错的一掷！"
        else:
            return f"🎲 D{sides}: **{results[0]}**"
    else:
        details = ", ".join(str(r) for r in results)
        return f"🎲 {times}D{sides}: [{details}] 总和 = **{total}**"


@tool
def calculate_damage(base_attack: int, dice_result: int, has_advantage: bool = False) -> str:
    """⚔️ 计算战斗伤害。

    Args:
        base_attack: 基础攻击力
        dice_result: 骰子结果（攻击判定）
        has_advantage: 是否有优势（暴击概率翻倍）

    Returns:
        伤害计算结果描述
    """
    if dice_result == 1:
        return "💥 攻击失误！武器从手中滑落，造成 0 点伤害。"

    crit_threshold = 15 if has_advantage else 19
    is_crit = dice_result >= crit_threshold

    if is_crit:
        damage = base_attack * 2 + random.randint(1, 6)
        return f"💥 **暴击！** 造成 {damage} 点伤害！（基础 {base_attack} x2 + {damage - base_attack * 2}）"
    else:
        damage = base_attack + random.randint(-2, 3)
        damage = max(1, damage)
        return f"⚔️ 造成 {damage} 点伤害。"


@tool
def use_item(item_name: str, inventory: List[str]) -> str:
    """🧪 使用背包中的物品。

    Args:
        item_name: 要使用的物品名
        inventory: 当前背包列表

    Returns:
        使用结果描述
    """
    if item_name not in inventory:
        available = ", ".join(inventory) if inventory else "空"
        return f"❌ 背包中没有「{item_name}」。当前背包: {available}"

    # 模拟物品效果（实际效果由 nodes 中的逻辑计算）
    effect_map = {
        "治疗药水": ("恢复 15 点生命", "🧪"),
        "龙之心": ("恢复全部生命", "❤️‍🔥"),
        "银剑": ("装备银剑，攻击力+8", "⚔️"),
        "传说之盾": ("装备传说之盾，伤害减半", "🛡️"),
        "生锈的钥匙": ("使用钥匙开门", "🔑"),
        "古老卷轴": ("阅读卷轴上的咒语", "📜"),
    }

    info = effect_map.get(item_name, ("使用了物品", "📦"))
    return f"{info[1]} {info[0]}：**{item_name}**"


@tool
def check_inventory(inventory: List[str]) -> str:
    """🎒 查看背包内容。

    Args:
        inventory: 当前背包列表

    Returns:
        格式化的背包内容
    """
    if not inventory:
        return "🎒 背包空空如也。"
    items_str = "\n".join(f"  • {name}" for name in inventory)
    return f"🎒 背包 ({len(inventory)}件):\n{items_str}"


# 将所有工具收集为列表，供 LangGraph ToolNode 使用
ALL_TOOLS = [roll_dice, calculate_damage, use_item, check_inventory]
