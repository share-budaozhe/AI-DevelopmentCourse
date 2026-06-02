"""
═══════════════════════════════════════════════════════════════
  🏰 AI 地牢探险 — 游戏世界数据
═══════════════════════════════════════════════════════════════
定义所有房间、怪物、物品和谜题。
这是 LangGraph 状态机驱动的地牢世界"静态数据层"。
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


# ─────────────────────────────────────────────────────────────
# 怪物定义
# ─────────────────────────────────────────────────────────────
@dataclass
class Monster:
    """地牢中的怪物，拥有名称、生命值、攻击力和特殊台词。"""
    name: str
    hp: int
    attack: int
    emoji: str
    taunts: List[str]    # 嘲讽台词
    defeat_msg: str      # 被击败台词
    loot: List[str]      # 掉落物品名

    def random_taunt(self) -> str:
        return random.choice(self.taunts)


MONSTERS: Dict[str, Monster] = {
    "goblin": Monster(
        name="地精守卫",
        hp=20,
        attack=4,
        emoji="👹",
        taunts=["「嘎嘎！又一个送死的冒险者！」", "「你的装备看起来不错……我要了！」"],
        defeat_msg="「不……不可能……」地精化为一股黑烟消散了。",
        loot=["生锈的钥匙"],
    ),
    "skeleton": Monster(
        name="骷髅骑士",
        hp=35,
        attack=7,
        emoji="💀",
        taunts=["「咔咔咔……血肉……新鲜的……」", "「加入亡者的行列吧！」"],
        defeat_msg="骷髅散落成一地碎骨，头盔滚到了墙角。",
        loot=["银剑", "治疗药水"],
    ),
    "dragon": Monster(
        name="🔥 远古火龙",
        hp=60,
        attack=12,
        emoji="🐉",
        taunts=[
            "「渺小的凡人，你竟敢闯入我的巢穴？」",
            "「我已经三百年没吃过冒险者了……真怀念啊。」",
        ],
        defeat_msg="「这不……可能……」火龙轰然倒下，龙鳞散落一地。",
        loot=["龙之心", "传说之盾"],
    ),
}


# ─────────────────────────────────────────────────────────────
# 物品定义
# ─────────────────────────────────────────────────────────────
@dataclass
class Item:
    """可收集的物品，有名称、效果和描述。"""
    name: str
    emoji: str
    description: str
    effect_type: str    # "heal" | "weapon" | "key" | "artifact"
    effect_value: int = 0


ITEMS: Dict[str, Item] = {
    "生锈的钥匙": Item("生锈的钥匙", "🔑", "一把锈迹斑斑的铁钥匙，似乎能打开某扇门。", "key"),
    "治疗药水": Item("治疗药水", "🧪", "闪烁红光的药水，喝下可恢复15点生命。", "heal", 15),
    "银剑": Item("银剑", "⚔️", "锋利的银制长剑，攻击力+8。", "weapon", 8),
    "龙之心": Item("龙之心", "❤️‍🔥", "火龙的心脏，蕴含远古力量。恢复全部生命。", "heal", 999),
    "传说之盾": Item("传说之盾", "🛡️", "传说中勇士的盾牌，受到伤害减半。", "artifact", 50),
    "古老卷轴": Item("古老卷轴", "📜", "记录着开门咒语的卷轴：「说出光的名字」。", "key"),
}


# ─────────────────────────────────────────────────────────────
# 谜题定义
# ─────────────────────────────────────────────────────────────
@dataclass
class Puzzle:
    """需要玩家回答的谜题，用于 puzzle 类型房间。"""
    question: str
    answer: str
    hint: str
    success_msg: str
    fail_msg: str
    reward: List[str]  # 奖励物品名列表


PUZZLES: Dict[str, Puzzle] = {
    "riddle_of_light": Puzzle(
        question="""
🗝️  谜题之门的石板上刻着一行字：

    「我是白昼的使者，黑暗的敌人。
      没有我万物凋零，太多我万物成烬。
      我是什么？」""",
        answer="光",
        hint="想一想……太阳发出的东西。",
        success_msg="石板发出耀眼光芒，石门缓缓打开！",
        fail_msg="石板震动了一下，门纹丝不动。再试一次吧。",
        reward=["古老卷轴"],
    ),
}


# ─────────────────────────────────────────────────────────────
# 房间定义
# ─────────────────────────────────────────────────────────────
@dataclass
class Room:
    """地牢中的一个房间。type 决定 LangGraph 如何路由处理。"""
    name: str
    emoji: str
    description: str
    room_type: str               # "start" | "explore" | "combat" | "treasure" | "puzzle" | "boss" | "exit"
    exits: Dict[str, str]        # 方向 -> 目标房间ID
    monster_id: Optional[str] = None
    items: List[str] = field(default_factory=list)       # 初始存在的物品名
    puzzle_id: Optional[str] = None
    locked: bool = False          # 是否需要钥匙
    required_key: Optional[str] = None


ROOMS: Dict[str, Room] = {
    # ── 起始房间 ──
    "entrance": Room(
        name="地牢入口",
        emoji="🚪",
        description="""
你站在一座古老地牢的入口。石壁上爬满青苔，空气中弥漫着潮湿的霉味。
前方有三条路可选：
  → 北：一条黑暗的走廊
  → 东：隐隐传来打铁声
  → 西：一扇锁着的铁门""",
        room_type="start",
        exits={"北": "corridor", "东": "armory", "西": "treasure_room"},
    ),
    # ── 探索房间 ──
    "corridor": Room(
        name="黑暗走廊",
        emoji="🌑",
        description="""
走廊又长又暗，你的脚步声在石壁间回荡。墙上火把忽明忽暗。
你注意到地上有干涸的血迹……前方似乎有东西在移动。
  → 北：继续深入（通往地精巢穴）
  → 南：退回入口""",
        room_type="explore",
        exits={"北": "goblin_den", "南": "entrance"},
    ),
    # ── 战斗房间 ──
    "goblin_den": Room(
        name="地精巢穴",
        emoji="👹",
        description="一股恶臭扑面而来！角落里堆着骨头和破烂。两只地精正盯着你！",
        room_type="combat",
        monster_id="goblin",
        exits={"南": "corridor", "东": "puzzle_chamber"},
        items=[],
    ),
    # ── 宝物房间 ──
    "armory": Room(
        name="废弃军械库",
        emoji="⚔️",
        description="""
这是一个被遗忘的军械库。武器架上还挂着几件像样的装备。
角落里有一个宝箱！
  → 西：返回入口""",
        room_type="treasure",
        exits={"西": "entrance"},
        items=["银剑", "治疗药水"],
    ),
    # ── 谜题房间 ──
    "puzzle_chamber": Room(
        name="谜题密室",
        emoji="🧩",
        description="""
你走进一间圆形的石室。中央立着一道刻满符文的大门。
要过去就必须解开谜题。
  → 北：符文大门（需要解开谜题）
  → 西：返回地精巢穴""",
        room_type="puzzle",
        exits={"北": "dragon_lair", "西": "goblin_den"},
        puzzle_id="riddle_of_light",
    ),
    # ── Boss 房间 ──
    "dragon_lair": Room(
        name="龙穴",
        emoji="🐉",
        description="""
🔥 热浪灼人！巨大的洞窟中央盘踞着一条远古火龙，
金色的瞳孔死死盯住你。这是最终之战！
  → 北：龙身后的出口
  → 南：退回密室""",
        room_type="boss",
        monster_id="dragon",
        exits={"北": "exit_room", "南": "puzzle_chamber"},
    ),
    # ── 宝物房间（锁） ──
    "treasure_room": Room(
        name="封印宝库",
        emoji="💎",
        description="一扇厚重的铁门挡住去路，上面有一个钥匙孔。",
        room_type="treasure",
        exits={"东": "entrance"},
        items=["龙之心", "传说之盾", "治疗药水"],
        locked=True,
        required_key="生锈的钥匙",
    ),
    # ── 出口 ──
    "exit_room": Room(
        name="🏆 胜利之光",
        emoji="🌅",
        description="""
你冲出了地牢！阳光洒在脸上，新鲜的空气填满肺腑。
你成为了传说——屠龙勇士！
""",
        room_type="exit",
        exits={},
    ),
}


# ─────────────────────────────────────────────────────────────
# 辅助函数
# ─────────────────────────────────────────────────────────────
def get_room(room_id: str) -> Optional[Room]:
    """安全地获取房间对象。"""
    return ROOMS.get(room_id)


def get_monster(monster_id: str) -> Optional[Monster]:
    """安全地获取怪物对象。"""
    return MONSTERS.get(monster_id)


def get_item(item_name: str) -> Optional[Item]:
    """安全地获取物品对象。"""
    return ITEMS.get(item_name)


def describe_inventory(inventory: List[str]) -> str:
    """格式化显示玩家背包。"""
    if not inventory:
        return "  （空空如也）"
    lines = []
    for name in inventory:
        item = ITEMS.get(name)
        if item:
            lines.append(f"  {item.emoji} {item.name} — {item.description}")
    return "\n".join(lines)
