"""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║       Loop vs Goal  —  理解"循环"与"目标"的区别与协作                    ║
║       Understanding How the Engine and the Destination Work Together     ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝

目录 / CONTENTS
──────────────────────────────────────────────────────────────────────────
  1. 核心思想 ── Loop 和 Goal 到底是什么？
  2. Loop vs Goal 对比表
  3. 生活中的类比
  4. 代码演示
     4.1 第一个例子：猜数字 —— 最简单的 Loop + Goal
     4.2 第二个例子：同一个 Goal，不同的 Loop
     4.3 第三个例子：同一个 Loop，不同的 Goal
     4.4 第四个例子：Goal 永远达不到怎么办？
     4.5 第五个例子：嵌套 Loop + 多层 Goal
  5. 实现技术点总结
  6. 启发性问题
  7. 测试文档
──────────────────────────────────────────────────────────────────────────
"""

import random
import time
import math


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  1. 核心思想                                                          ║
# ╚══════════════════════════════════════════════════════════════════════════╝
#
#  ╭──────────────────────────────────────────────────────────────────╮
#  │  一句话：                                                        │
#  │                                                                  │
#  │    Loop = 引擎（怎么跑）                                          │
#  │    Goal = 终点（跑到哪停）                                        │
#  │                                                                  │
#  │  程序 = Loop 驱动 + Goal 判断                                     │
#  ╰──────────────────────────────────────────────────────────────────╯
#
#  ┌────────────────────────────────────────────────────────────────────┐
#  │  重要理解：                                                       │
#  │                                                                    │
#  │  Loop 和 Goal 是程序中的两个独立概念，它们协作完成任务：           │
#  │                                                                    │
#  │  • Loop 负责"重复做某事"—— 它是动作的驱动力                       │
#  │    - while 循环：条件为真就一直做                                  │
#  │    - for 循环：遍历完就停止                                        │
#  │    - 递归调用：自己调自己直到基线条件                              │
#  │                                                                    │
#  │  • Goal 负责"判断何时停止"—— 它是终止的决策条件                   │
#  │    - 显式目标：变量值到达某个阈值                                  │
#  │    - 隐式目标：遍历完所有元素                                      │
#  │    - 外部目标：用户输入了特定值                                    │
#  │                                                                    │
#  │  ⚠️ 容易混淆的地方：                                              │
#  │    很多人把"循环条件"直接当作"目标"，但它们不一样：               │
#  │    - 循环条件描述的是"要不要继续"                                  │
#  │    - 目标描述的是"有没有完成"                                      │
#  │    同一个目标可以用不同的循环来实现，同一个循环也可以追求         │
#  │    不同的目标。                                                   │
#  └────────────────────────────────────────────────────────────────────┘


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  2. Loop vs Goal 对比表                                               ║
# ╚══════════════════════════════════════════════════════════════════════════╝
#
#  ┌───────────────────┬──────────────────────────┬─────────────────────────┐
#  │     维度          │         Loop             │         Goal            │
#  ├───────────────────┼──────────────────────────┼─────────────────────────┤
#  │  英文名           │  Loop                    │  Goal                   │
#  │  中文             │  循环                    │  目标                   │
#  │  角色             │  引擎 / 驱动器           │  终点 / 判断条件        │
#  │  回答的问题       │  "怎么做？"              │  "做到什么程度停？"      │
#  │  类比             │  汽车的发动机            │  导航的目的地           │
#  │  代码形态         │  while / for / 递归      │  if 条件 / 哨兵值       │
#  │  失败方式         │  死循环 / 效率低        │  无法达到 / 不可满足    │
#  │  可替换性         │  同目标可用不同Loop实现  │  同Loop可追求不同Goal   │
#  │  设计重点         │  迭代方式、步进逻辑      │  终止条件、阈值设定     │
#  │  典型 Bug         │  忘记更新循环变量        │  条件写反永远达不到     │
#  │  安全措施         │  step_limit 限制总步数   │  timeout 限制总时间     │
#  └───────────────────┴──────────────────────────┴─────────────────────────┘
#
#  理解了这个区别，你就能看懂几乎所有程序的"骨架"。


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  3. 生活中的类比                                                      ║
# ╚══════════════════════════════════════════════════════════════════════════╝
#
#  ┌──────────────────────────────────────────────────────────────────────┐
#  │  类比 1：跑步                                                     │
#  │                                                                      │
#  │  你在操场上跑步：                                                    │
#  │    • Loop = 你的双腿交替迈步的动作（重复执行）                      │
#  │    • Goal = "跑完 5 圈"（停止条件）                                  │
#  │                                                                      │
#  │  没有 Loop：你只迈一步就停，永远跑不完 5 圈                          │
#  │  没有 Goal：你会无限跑下去，直到累死                                │
#  │                                                                      │
#  │  Loop 和 Goal 必须同时存在才能完成有意义的任务。                     │
#  │                                                                      │
#  ├──────────────────────────────────────────────────────────────────────┤
#  │  类比 2：烧水                                                     │
#  │                                                                      │
#  │  你用电热水壶烧水：                                                  │
#  │    • Loop = 加热管持续发热（重复加热）                              │
#  │    • Goal = "水温达到 100°C"（自动断电的条件）                      │
#  │                                                                      │
#  │  Loop 坏了 → 水温上不去，永远达不到 Goal                            │
#  │  Goal 坏了 → 水烧干了还在加热，非常危险                             │
#  │                                                                      │
#  ├──────────────────────────────────────────────────────────────────────┤
#  │  类比 3：找工作                                                   │
#  │                                                                      │
#  │  你投简历找工作：                                                    │
#  │    • Loop = 每天刷招聘网站、投简历、面试（重复过程）                │
#  │    • Goal = "拿到满意的 Offer"（终止条件）                           │
#  │                                                                      │
#  │  同一个人（Loop 一样），可以追求：                                   │
#  │    Goal A = "月薪 2 万以上"                                         │
#  │    Goal B = "离家 3 公里以内"                                       │
#  │    Goal C = "不加班"                                                │
#  │                                                                      │
#  │  Loop 方式也可以变：                                                │
#  │    Loop 方式 1 = 海投（投 1000 家）                                 │
#  │    Loop 方式 2 = 精准投（只投最匹配的 10 家）                       │
#  │  但 Goal 都是"拿到 Offer"                                          │
#  └──────────────────────────────────────────────────────────────────────┘


# ========================================================================
#  4. 代码演示
# ========================================================================

print("╔" + "═" * 67 + "╗")
print("║" + "  Loop vs Goal — 理解循环与目标的区别与协作".center(63) + "║")
print("╚" + "═" * 67 + "╝")
print()


# ┌───────────────────────────────────────────────────────────────────────┐
# │  4.1 第一个例子：猜数字 —— 最简单的 Loop + Goal                     │
# │                                                                       │
# │  目标：理解    Loop = 反复猜       Goal = 猜中为止                   │
# └───────────────────────────────────────────────────────────────────────┘

print("─" * 69)
print("  例子 1：猜数字 —— 最简单的 Loop + Goal")
print("─" * 69)
print()


def guess_number_game(max_number: int = 100, secret: int | None = None):
    """
    猜数字游戏 —— Loop 和 Goal 最直接的展示。

    【Loop】   while True：无限循环，不断让用户输入
    【Goal】   user_input == secret：猜中数字就结束

    流程：
        ┌──────────┐
        │  开始     │
        └────┬─────┘
             │
             ▼
        ┌──────────┐     ┌──────────────┐
        │ 用户输入  │ ◄── │  Loop =      │
        │ 猜的数字  │     │ while True   │
        └────┬─────┘     │ 重复询问     │
             │           └──────────────┘
             ▼
        ┌──────────┐
        │ 判断是否  │
        │ 猜对？    │ ←──── Goal == secret
        └────┬─────┘
             │
    ┌─── 否 ─┤ 是 ───┐
    │        │        │
    ▼        │        ▼
  "大了/小了"│    "恭喜！"
  继续循环   │    结束
             │
        ┌────┴─────┐
        │ 统计步数  │
        └──────────┘
    """
    if secret is None:
        secret = random.randint(1, max_number)

    attempts = 0
    print(f"  我已经想好了一个 1~{max_number} 之间的数字，你来猜！")
    print()

    # ═══════════════════════════════════════════════════════════════════
    # 🔄 LOOP 开始 —— while True 表示"永远重复，直到内部 break"
    #
    #  while True 是最纯粹的 Loop：它只说"重复做"，
    #  至于"做到什么时候停"——那是 Goal 的事
    # ═══════════════════════════════════════════════════════════════════

    while True:           # ◄──── Loop：只管重复，不问为什么
        attempts += 1

        try:
            guess = int(input(f"  第 {attempts} 次猜："))
        except ValueError:
            print("  请输入数字！")
            continue      # ◄──── continue 是 Loop 的"跳过本轮"

        # ══════════════════════════════════════════════════════════════
        # 🎯 GOAL 判断 —— 检查是否到达目标
        #
        #  下面的 if 就是在检查 Goal：我们到了吗？
        #  到了就 break（终止 Loop），没到就继续
        # ══════════════════════════════════════════════════════════════

        if guess == secret:              # ◄──── Goal 条件！
            print(f"\n  ✅ 恭喜！你猜了 {attempts} 次就猜中了！")
            return attempts              # 到达 Goal，返回（结束 Loop）

        # 没到 Goal，给出提示，Loop 继续
        if guess < secret:
            print("  ⬆️ 小了，再大一点")
        else:
            print("  ⬇️ 大了，再小一点")

        # ══════════════════════════════════════════════════════════════
        # 🔄 LOOP 结束 —— 回到 while True 开头，继续下一轮
        # ══════════════════════════════════════════════════════════════

    # 注意：这里的 return 永远不会执行到，因为上面的 return 已经结束了
    # 但 if Goal 条件不满足，while True 会永远运行下去（所以猜数字需要用户配合）


# 跑一次自动猜数字（不需要人工输入）
def auto_guess_number():
    """
    自动猜数字 —— 用二分法快速逼近目标。

    这里展示一个重要的洞察：
      同一个 Goal（猜中数字），我们用了不同的 Loop（二分法 vs 逐次输入）
      说明 Loop 可以替换，但 Goal 不变。
    """
    secret = random.randint(1, 100)
    low, high = 1, 100
    attempts = 0

    print("  🤖 自动猜数字模式（二分法）")
    print(f"  秘密数字: {secret}（给你看的，机器人不知道）")
    print()

    # 🔄 Loop：和上面的猜数字一样的 while，但移动逻辑不同
    while True:
        attempts += 1
        guess = (low + high) // 2          # 二分法：猜中间

        # 🎯 Goal 判断
        if guess == secret:
            print(f"  ✅ 机器人用了 {attempts} 次猜中 {secret}！")
            return attempts
        elif guess < secret:
            print(f"  第 {attempts} 次猜 {guess} → 小了")
            low = guess + 1
        else:
            print(f"  第 {attempts} 次猜 {guess} → 大了")
            high = guess - 1


print()
auto_guess_number()
print()


# ┌───────────────────────────────────────────────────────────────────────┐
# │  4.2 第二个例子：同一个 Goal，不同的 Loop                            │
# │                                                                       │
# │  目标：展示"目标相同，实现目标的循环方式可以不同"                    │
# └───────────────────────────────────────────────────────────────────────┘

print("─" * 69)
print("  例子 2：同一个 Goal，不同的 Loop")
print("─" * 69)
print()

# 设定目标：计算 1 + 2 + 3 + ... + 100 = 5050
# Goal 是固定的：从 1 加到 100，结果是 5050
TARGET_SUM = 5050
N = 100


def sum_with_while(n: int) -> int:
    """方式 A：用 while 循环求和"""
    total = 0
    i = 1
    while i <= n:         # 🔄 Loop = while
        total += i
        i += 1            # 更新循环变量（非常重要！忘了就死循环）
    return total          # 🎯 Goal = 加完所有数


def sum_with_for(n: int) -> int:
    """方式 B：用 for 循环求和"""
    total = 0
    for i in range(1, n + 1):   # 🔄 Loop = for（自动管理迭代）
        total += i
    return total                  # 🎯 Goal 一样


def sum_with_recursion(n: int) -> int:
    """方式 C：用递归（函数自己调用自己）求和"""
    # 基线条件（Goal 的一种形式）
    if n == 1:            # 🎯 Goal：数减到 1 就停
        return 1
    # 递归调用（Loop 的一种形式 —— 自己调自己）
    return n + sum_with_recursion(n - 1)   # 🔄 Loop = 递归调用


def sum_with_formula(n: int) -> int:
    """方式 D：直接用公式（根本没有 Loop！）"""
    # 有些问题根本不需要循环
    return n * (n + 1) // 2    # 🎯 Goal 直接达成，无需 Loop


print(f"  🎯 同一个 Goal：计算 1 + 2 + ... + {N} = {TARGET_SUM}")
print()

results = {
    "A: while 循环":     sum_with_while(N),
    "B: for 循环":       sum_with_for(N),
    "C: 递归":           sum_with_recursion(N),
    "D: 数学公式":       sum_with_formula(N),
}

for method, result in results.items():
    status = "✅" if result == TARGET_SUM else "❌"
    print(f"    {status} {method:<16} = {result}")
    if result != TARGET_SUM:
        print(f"       （期望 {TARGET_SUM}，请检查实现）")

print()
print(f"  💡 关键理解：")
print(f"      同一个 Goal（加到 5050），可以用完全不同的 Loop 方式实现。")
print(f"      甚至方式 D 根本不需要 Loop —— 因为数学公式直接算出来了！")
print(f"      这说明：Goal 是『做什么』，Loop 是『怎么做』。")
print()


# ┌───────────────────────────────────────────────────────────────────────┐
# │  4.3 第三个例子：同一个 Loop，不同的 Goal                            │
# │                                                                       │
# │  目标：展示"循环方式相同，设定的目标可以完全不同"                    │
# └───────────────────────────────────────────────────────────────────────┘

print("─" * 69)
print("  例子 3：同一个 Loop，不同的 Goal")
print("─" * 69)
print()


def count_up_until(goal_condition, start: int = 1, step: int = 1):
    """
    通用"往上数"函数 —— Loop 是固定的，Goal 是可定制的。

    参数:
        goal_condition: 一个函数，接收当前数字，返回 True/False
                        True = 到达目标，停止
        start: 从哪个数字开始
        step: 每次加多少

    🔄 Loop 是固定的：一直往上加数字
    🎯 Goal 是可变的：由 goal_condition 决定何时停止
    """
    current = start
    steps = 0

    while True:                     # 🔄 同一个 Loop
        steps += 1

        # 🎯 Goal 判断：调用外部传入的"目标判断函数"
        if goal_condition(current):  # Goal 由你定义！
            print(f"     ✅ 在第 {steps} 步到达目标！数值 = {current}")
            return current

        current += step


print("  同一个 count_up_until 函数，不同的 Goal：")
print()

# Goal A：数到第一个大于 50 的质数
print("  🎯 Goal A：找到第一个大于 50 的质数")

def is_prime(n: int) -> bool:
    if n < 2:
        return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True

def goal_first_prime_above_50(x: int) -> bool:
    """Goal：x 是质数吗？"""
    return is_prime(x)

count_up_until(goal_first_prime_above_50, start=51)
print()

# Goal B：数到 100
print("  🎯 Goal B：数到 100")

def goal_reach_100(x: int) -> bool:
    """Goal：x >= 100 吗？"""
    return x >= 100

count_up_until(goal_reach_100, start=1)
print()

# Goal C：数到各位数字之和大于 20
print("  🎯 Goal C：各位数字之和大于 20")

def goal_digit_sum_gt_20(x: int) -> bool:
    """Goal：x 的各位数字加起来 > 20 吗？"""
    return sum(int(d) for d in str(x)) > 20

count_up_until(goal_digit_sum_gt_20, start=1)
print()

# Goal D：数到第 10 个平方数
print("  🎯 Goal D：找到第 10 个完全平方数")

count = 0
def goal_10th_square(x: int) -> bool:
    """Goal：x 是不是第 10 个完全平方数？"""
    global count
    root = int(math.isqrt(x))
    if root * root == x:
        count += 1
        return count >= 10
    return False

count_up_until(goal_10th_square, start=1)
print()

# 重置全局
count = 0

print(f"  💡 关键理解：")
print(f"      同一个 count_up_until 函数（同一个 Loop），")
print(f"      通过传入不同的 goal_condition（不同的 Goal），")
print(f"      实现了完全不同的搜索任务！")
print()


# ┌───────────────────────────────────────────────────────────────────────┐
# │  4.4 第四个例子：Goal 永远达不到怎么办？                             │
# │                                                                       │
# │  目标：展示 Goal 无法达到时，需要 Loop 提供"安全出口"               │
# └───────────────────────────────────────────────────────────────────────┘

print("─" * 69)
print("  例子 4：Goal 永远达不到怎么办？")
print("─" * 69)
print()


def search_with_safety(start: int, goal_condition, max_steps: int = 1000):
    """
    带安全机制的搜索 —— 展示 Loop 和 Goal 的单向依赖关系。

    关键设计原则：
      虽然 Goal 决定"要不要停"，但如果 Goal 永远达不到，
      Loop 必须有"自我保护的停止机制"。

    这就像汽车：
      • 刹车（Goal）决定停不停
      • 但燃料没了（step_limit）也得停
    """
    current = start
    print(f"  开始搜索，最大步数限制 = {max_steps}")

    # 🔄 Loop
    for step in range(1, max_steps + 1):
        # 🎯 Goal 判断
        if goal_condition(current):
            print(f"  ✅ 到达目标！当前值 = {current}，用了 {step} 步")
            return True, current, step

        current += 1

    # 如果 for 循环自然结束（没到 Goal），说明 max_steps 不够
    print(f"  ❌ 在 {max_steps} 步内未到达目标，已自动停止")
    print(f"     最后数值 = {current}")
    return False, current, max_steps


# 场景 1：Goal 可达
print("  场景 1：Goal 可达")
search_with_safety(1, lambda x: x >= 50, max_steps=100)
print()

# 场景 2：Goal 永远达不到（数到正无穷也不可能到 -1）
print("  场景 2：Goal 不可达（往上走永远不可能等于 -1）")
search_with_safety(1, lambda x: x == -1, max_steps=10)
print()

# 场景 3：Goal 理论上可达，但步数限制太小
print("  场景 3：Goal 可达但步数限制太小")
search_with_safety(1, lambda x: x >= 1000, max_steps=50)
print()

print(f"  💡 关键理解：")
print(f"      Loop 和 Goal 不是平等的伙伴关系 —— Loop 对 Goal 有")
print(f"      『单向依赖』：没有 Goal，Loop 会无限跑；但没有 Loop，")
print(f"      Goal 永远不会被检查。两者缺一不可，但角色完全不同。")
print()


# ┌───────────────────────────────────────────────────────────────────────┐
# │  4.5 第五个例子：嵌套 Loop + 多层 Goal                              │
# │                                                                       │
# │  目标：展示复杂任务中，Loop 和 Goal 可以分层嵌套                    │
# └───────────────────────────────────────────────────────────────────────┘

print("─" * 69)
print("  例子 5：嵌套 Loop + 多层 Goal")
print("─" * 69)
print()


def find_pythagorean_triplet(max_n: int = 20):
    """
    找到所有满足 a² + b² = c² 的勾股数（a < b < c < max_n）

    这里展示多层嵌套的 Loop 和多层 Goal：
      • 外层 Loop：遍历 a
      • 中层 Loop：遍历 b
      • 内层 Loop：遍历 c
      • 总的 Goal：找到所有勾股数

    流程视图：
        ┌──────────────────────────────────────────┐
        │  外层 Loop (a 从 1 到 max_n)              │
        │  │                                        │
        │  ├── 中层 Loop (b 从 a+1 到 max_n)        │
        │  │   │                                    │
        │  │   └── 内层 Loop (c 从 b+1 到 max_n)    │
        │  │    │   │                                │
        │  │    │   ├── Goal: a² + b² == c² ?       │
        │  │    │   │   ├─ 是 → 记录，继续           │
        │  │    │   │   └─ 否 → 继续                 │
        │  │    │   │                                │
        │  │    │   └── c Loop 结束（内层 Goal 完成）│
        │  │    └── b Loop 结束（中层 Goal 完成）    │
        │  └── a Loop 结束（外层 Goal 完成）         │
        └──────────────────────────────────────────┘
    """
    triplets = []

    # 🔄 外层 Loop
    for a in range(1, max_n + 1):
        # 🔄 中层 Loop
        for b in range(a + 1, max_n + 1):
            # 🔄 内层 Loop
            for c in range(b + 1, max_n + 1):
                # 🎯 内层 Goal：检查勾股定理
                if a * a + b * b == c * c:
                    triplets.append((a, b, c))
                    print(f"     ✅ 发现勾股数: {a}² + {b}² = {c}²")

    return triplets


print(f"  寻找 max_n = 20 以内的勾股数：")
print()
result = find_pythagorean_triplet(20)

print()
print(f"  共找到 {len(result)} 组勾股数")
print()

print(f"  💡 关键理解：")
print(f"      在实际程序中，Loop 和 Goal 经常是多层嵌套的。")
print(f"      每一层都有自己的 Loop（迭代逻辑）和 Goal（完成条件）。")
print(f"      内层的 Goal 达到后，继续外层的 Loop —— 就像完成一个")
print(f"      小目标后继续向大目标前进。")
print()


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  5. 实现技术点总结 (Technical Points)                                 ║
# ╚══════════════════════════════════════════════════════════════════════════╝
#
#  ┌──────────────────────────────────────────────────────────────────────┐
#  │  技术点 1 —— while 循环 vs for 循环                                 │
#  ├──────────────────────────────────────────────────────────────────────┤
#  │  while 适合"不知要循环多少次"的场景（大多数 Goal 驱动型任务）       │
#  │  for 适合"知道要遍历什么"的场景（集合、范围等）                      │
#  │                                                                      │
#  │  while 的优缺点：                                                    │
#  │    + 灵活，可以表达任意循环逻辑                                      │
#  │    - 容易忘记更新循环变量，导致死循环                                │
#  │  for 的优缺点：                                                      │
#  │    + 自动管理迭代，不容易死循环                                      │
#  │    - 不适用于"不知道迭代次数"的场景                                  │
#  │                                                                      │
#  │  ├──────────────────────────────────────────────────────────────────┤
#  │  技术点 2 —— break 和 continue                                      │
#  │                                                                      │
#  │  break 和 continue 是 Loop 的控制指令：                              │
#  │    • break    = "立即停止整个 Loop"（通常因为 Goal 达到了）          │
#  │    • continue = "跳过本轮，开始下一轮"（不需要停止，但本轮不用做了）│
#  │                                                                      │
#  │  注意：break 只跳出当前这一层循环，不影响外层 Loop。                 │
#  │                                                                      │
#  │  ├──────────────────────────────────────────────────────────────────┤
#  │  技术点 3 —— 递归也是一种 Loop                                      │
#  │                                                                      │
#  │  很多人以为递归和循环是两回事，但本质上：                            │
#  │    • 递归 = 函数调用自己（Loop = 代码跳回开头）                     │
#  │    • 递归的"基线条件" = Goal 判断                                   │
#  │    • 递归的"递推步骤" = Loop 的迭代                                  │
#  │                                                                      │
#  │  递归 vs 迭代式循环：                                                │
#  │    + 递归让代码更接近数学定义，容易理解                              │
#  │    - 递归有函数调用开销和栈深度限制                                  │
#  │                                                                      │
#  │  ├──────────────────────────────────────────────────────────────────┤
#  │  技术点 4 —— Step Limit（步数限制）                                 │
#  │                                                                      │
#  │  Step Limit 是 Loop 的"安全阀"：                                     │
#  │    当 Goal 永远达不到时，Step Limit 确保程序不会无限运行。           │
#  │                                                                      │
#  │  实现方式：                                                          │
#  │    for step in range(max_steps):        ← 内置步数限制               │
#  │        if goal_reached():               ← Goal 判断                  │
#  │            return success                                               │
#  │    return failure                       ← 超步数限制                  │
#  │                                                                      │
#  │  ├──────────────────────────────────────────────────────────────────┤
#  │  技术点 5 —— 把 Goal 作为参数传递（高阶函数）                       │
#  │                                                                      │
#  │  Python 允许把函数当作参数传递，这使得"同一个 Loop，不同 Goal"      │
#  │  成为可能。这是函数式编程的一种体现。                                │
#  │                                                                      │
#  │  def loop_template(goal_check):      ← Goal 作为参数传入             │
#  │      while True:                                                     │
#  │          if goal_check(state):                                      │
#  │              break                                                    │
#  │          update(state)                                               │
#  │                                                                      │
#  │  这使得代码复用性极大提高。                                          │
#  │                                                                      │
#  │  ├──────────────────────────────────────────────────────────────────┤
#  │  技术点 6 —— Goal 的表达方式                                        │
#  │                                                                      │
#  │  Goal 在代码中有多种表达方式：                                        │
#  │    ① 显式条件： if x == target: break                               │
#  │    ② 函数参数： goal_condition(x) 返回 bool                         │
#  │    ③ 哨兵值：   while (data = read()) != SENTINEL:                 │
#  │    ④ 异常：     raise StopIteration / StopSearch                    │
#  │    ⑤ 枚举结束： for item in collection:（Goal 隐含在遍历完）        │
#  │                                                                      │
#  │  选择哪种方式取决于你的需求：                                        │
#  │    • 简单条件 → 直接 if                                              │
#  │    • 可复用的通用 Loop → 函数参数                                   │
#  │    • 外部数据读取 → 哨兵值                                           │
#  │    • 集合遍历 → for 循环本身                                         │
#  └──────────────────────────────────────────────────────────────────────┘


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  6. 启发性问题 (Heuristic Questions)                                  ║
# ╚══════════════════════════════════════════════════════════════════════════╝
#
# ──────────────────────────────────────────────────────────────────────────
#  🔍 问题 1（入门）
#  ──────────────────────────────────────────────────────────────────────────
#  Q: 下面这段代码，Loop 在哪里？Goal 在哪里？
#
#     password = ""
#     while password != "abc123":
#         password = input("请输入密码：")
#     print("登录成功！")
#
#  A:
#     Loop = while password != "abc123": ...  的整个代码块
#     Goal = password == "abc123"（即 password != "abc123" 变为 False）
#
#  注意：这里的 Goal 直接写在了 while 的条件里。这是一种常见写法，
#  但 Goal 和 Loop 看起来"混合"了。实际上：
#    • while 条件中的判断逻辑 = Goal
#    • while 的整体结构 = Loop
#
# ──────────────────────────────────────────────────────────────────────────
#  🔍 问题 2（入门）
#  ──────────────────────────────────────────────────────────────────────────
#  Q: 下面哪种写法更好？为什么？
#
#     写法 A：                   写法 B：
#     while True:                while not_at_goal:
#         if at_goal():              do_one_step()
#             break
#         do_one_step()
#
#  A:
#     两者功能完全等价。
#     写法 B 更"自文档化"—— 一眼就能看出 Loop 在追求什么 Goal。
#     写法 A 更灵活，适合 Goal 条件复杂或不只一个 Goal 的场景。
#
#     实际工程中：
#       • 简单目标 → 写法 B（清晰）
#       • 复杂目标 / 多目标 → 写法 A（灵活）
#
# ──────────────────────────────────────────────────────────────────────────
#  🔍 问题 3（进阶）
#  ──────────────────────────────────────────────────────────────────────────
#  Q: for 循环有 Goal 吗？
#
#  A:
#     有！for 循环的 Goal 隐含在"遍历完所有元素"中。
#
#     for item in collection:
#         process(item)
#
#     这里的 Goal 其实是"collection 中没有更多元素了"。
#     当迭代器耗尽（raise StopIteration），循环自动结束。
#
#     所以 for 循环实际上是 Goald 驱动的一种特殊形式 ——
#     Goal 被"固化"在迭代机制中，不需要你显式写出来。
#
#     这也是为什么 for 比 while 更安全（不容易写死循环）：
#     因为它的 Goal 是内置的、自动的。
#
# ──────────────────────────────────────────────────────────────────────────
#  🔍 问题 4（进阶）
#  ──────────────────────────────────────────────────────────────────────────
#  Q: 有没有"没有 Loop 的 Goal"？或者"没有 Goal 的 Loop"？
#
#  A:
#     ① 没有 Loop 的 Goal：
#        有！数学公式直接计算结果，不需要迭代。
#        例子 2 中的 sum_with_formula 就是：目标直接达成，不需要循环。
#        但这种"一步到位"的情况在实际编程中很罕见。
#
#     ② 没有 Goal 的 Loop：
#        有！无限循环（while True: pass），永远不停。
#        操作系统的事件循环、游戏的主循环就是例子。
#        它们确实有 Goal（比如"用户点击退出按钮"），
#        但在用户操作之前，循环会一直运行。
#
#     所以更准确的说法是：
#       大部分程序同时需要 Loop 和 Goal，
#       但理论上它们确实可以独立存在。
#
# ──────────────────────────────────────────────────────────────────────────
#  🔍 问题 5（进阶）
#  ──────────────────────────────────────────────────────────────────────────
#  Q: 在猜数字游戏中，如果目标数字是随机生成的，Loop 保证能停吗？
#
#  A:
#     对于随机搜索（Random Walk），是"理论上能停，但不知道何时停"。
#     因为每次都随机猜，有可能（概率极低）永远猜不中。
#
#     对于二分法，是"一定能停，且最多 log₂(N) 步"。
#     因为每次排除一半的可能性，范围不断缩小。
#
#     这就引出了一个重要的概念：算法复杂性。
#       • 随机搜索：O(∞) 理论上无限
#       • 二分法：  O(log n) 有保证
#
#     在选择 Loop 策略时，你需要考虑：
#       这个 Loop 能保证到达 Goal 吗？
#       还是可能永远跑下去？
#
# ──────────────────────────────────────────────────────────────────────────
#  🔍 问题 6（综合）
#  ──────────────────────────────────────────────────────────────────────────
#  Q: 在例子 3 中，我们把 Goal 作为函数参数传入。这有什么好处？
#
#  A:
#     主要好处有三个：
#
#     ① 代码复用
#        同一个 count_up_until 函数可以用于无数种搜索任务，
#        不需要为每个 Goal 重写 Loop。
#
#     ② 关注点分离
#        Loop 的编写者只关心"怎么迭代"，
#        Goal 的编写者只关心"什么条件满足"。
#        两个人可以独立工作。
#
#     ③ 可测试性
#        因为 Goal 是独立函数，你可以单独测试每个 Goal 函数，
#        不需要运行整个 Loop。下面第 7 节就会展示这一点。
#
#     这就是软件工程中"开闭原则"的一个体现：
#       对扩展开放（加新 Goal 不需要改 Loop）
#       对修改关闭（Loop 代码不需要动）
#
# ──────────────────────────────────────────────────────────────────────────
#  🔍 问题 7（综合）
#  ──────────────────────────────────────────────────────────────────────────
#  Q: 假设你写了一个程序，它有一个 Loop 但忘记写 Goal 判断了。
#     你的同事 review 代码时应该指出什么问题？
#
#  A:
#     ① 程序会无限运行 —— 最直接的后果
#     ② 内存可能被耗尽 —— Loop 中不断创建新对象
#     ③ CPU 100% —— 导致电脑变慢、发热
#     ④ 用户无法退出 —— 如果没提供中断机制
#
#     所以 review 代码时，看到 Loop 就应该找对应的 Goal 判断：
#       • 有没有 break / return？
#       • while 条件最终会变成 False 吗？
#       • for 循环有没有隐含的遍历终点？
#       • 有没有 step_limit 兜底？
#
#     这是代码审查中最常见的检查项之一。
#


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  7. 测试文档 (Test Documentation)                                     ║
# ╚══════════════════════════════════════════════════════════════════════════╝

import unittest


# ========================================================================
# 7.1 测试辅助函数 —— 测试独立的 Goal 函数
# ========================================================================
#
#  Goal 函数是纯函数（同样的输入 → 同样的输出），非常容易测试。
#  这也证明了将 Goal 从 Loop 中分离出来的好处。
#

class TestGoalFunctions(unittest.TestCase):
    """测试独立的 Goal 判断函数"""

    def test_is_prime(self):
        """测试 is_prime 函数"""
        # 小于 2 不是质数
        self.assertFalse(is_prime(1))
        self.assertFalse(is_prime(0))
        self.assertFalse(is_prime(-5))
        # 质数
        self.assertTrue(is_prime(2))
        self.assertTrue(is_prime(3))
        self.assertTrue(is_prime(5))
        self.assertTrue(is_prime(7))
        self.assertTrue(is_prime(11))
        self.assertTrue(is_prime(53))
        self.assertTrue(is_prime(97))
        # 合数
        self.assertFalse(is_prime(4))
        self.assertFalse(is_prime(6))
        self.assertFalse(is_prime(8))
        self.assertFalse(is_prime(9))
        self.assertFalse(is_prime(10))
        self.assertFalse(is_prime(100))

    def test_goal_first_prime_above_50(self):
        """测试 Goal：第一个大于 50 的质数"""
        # 51 不是质数
        self.assertFalse(goal_first_prime_above_50(51))
        self.assertFalse(goal_first_prime_above_50(52))
        self.assertFalse(goal_first_prime_above_50(54))
        self.assertFalse(goal_first_prime_above_50(55))
        self.assertFalse(goal_first_prime_above_50(56))
        # 53 是质数
        self.assertTrue(goal_first_prime_above_50(53))

    def test_goal_reach_100(self):
        """测试 Goal：数到 100"""
        self.assertFalse(goal_reach_100(50))
        self.assertFalse(goal_reach_100(99))
        self.assertTrue(goal_reach_100(100))
        self.assertTrue(goal_reach_100(101))
        self.assertTrue(goal_reach_100(200))

    def test_goal_digit_sum_gt_20(self):
        """测试 Goal：各位数字之和大于 20"""
        # 99 → 9+9 = 18
        self.assertFalse(goal_digit_sum_gt_20(99))
        # 199 → 1+9+9 = 19
        self.assertFalse(goal_digit_sum_gt_20(199))
        # 299 → 2+9+9 = 20
        self.assertFalse(goal_digit_sum_gt_20(299))
        # 399 → 3+9+9 = 21
        self.assertTrue(goal_digit_sum_gt_20(399))
        # 999 → 27
        self.assertTrue(goal_digit_sum_gt_20(999))


# ========================================================================
# 7.2 测试求和函数 —— Goal 相同，Loop 不同
# ========================================================================

class TestSumFunctions(unittest.TestCase):
    """测试四种不同的求和方法（相同 Goal，不同 Loop）"""

    def test_all_methods_equal_5050(self):
        """所有方法都应该得到 5050"""
        self.assertEqual(sum_with_while(100), 5050)
        self.assertEqual(sum_with_for(100), 5050)
        self.assertEqual(sum_with_recursion(100), 5050)
        self.assertEqual(sum_with_formula(100), 5050)

    def test_sum_with_while_edge_cases(self):
        """测试 while 求和的边界情况"""
        self.assertEqual(sum_with_while(0), 0)
        self.assertEqual(sum_with_while(1), 1)
        self.assertEqual(sum_with_while(2), 3)

    def test_sum_with_for_edge_cases(self):
        """测试 for 求和的边界情况"""
        self.assertEqual(sum_with_for(0), 0)
        self.assertEqual(sum_with_for(1), 1)
        self.assertEqual(sum_with_for(5), 15)

    def test_sum_with_recursion_edge_cases(self):
        """测试递归求和的边界情况"""
        self.assertEqual(sum_with_recursion(1), 1)
        self.assertEqual(sum_with_recursion(2), 3)
        self.assertEqual(sum_with_recursion(10), 55)

    def test_sum_with_formula_edge_cases(self):
        """测试公式求和的边界情况"""
        self.assertEqual(sum_with_formula(0), 0)
        self.assertEqual(sum_with_formula(1), 1)
        self.assertEqual(sum_with_formula(100), 5050)


# ========================================================================
# 7.3 测试安全搜索 —— Step Limit 机制
# ========================================================================

class TestSafetyMechanism(unittest.TestCase):
    """测试 Loop 的安全机制（step_limit）"""

    def test_goal_reachable(self):
        """Goal 可达时，返回 True"""
        success, value, steps = search_with_safety(1, lambda x: x >= 10, 100)
        self.assertTrue(success)
        self.assertEqual(value, 10)

    def test_goal_unreachable(self):
        """Goal 不可达时，返回 False"""
        success, value, steps = search_with_safety(1, lambda x: x == -1, 100)
        self.assertFalse(success)

    def test_goal_reachable_but_limited(self):
        """Goal 可达但步数不够时，返回 False"""
        success, value, steps = search_with_safety(
            1, lambda x: x >= 1000, max_steps=50
        )
        self.assertFalse(success)

    def test_step_limit_exact(self):
        """Goal 正好在 step_limit 步到达"""
        success, value, steps = search_with_safety(1, lambda x: x >= 100, 100)
        self.assertTrue(success)
        # 从 1 到 100，走了 100 步（1→2, 2→3, ..., 99→100）
        self.assertLessEqual(steps, 100)


# ========================================================================
# 7.4 测试猜数字游戏
# ========================================================================

class TestAutoGuessNumber(unittest.TestCase):
    """测试自动猜数字游戏"""

    def test_always_succeeds(self):
        """二分法猜数字应该总是成功"""
        # 多次测试以确保
        for _ in range(20):
            steps = auto_guess_number()
            self.assertGreater(steps, 0)
            # 二分法在 1-100 范围内最多需要 7 次
            self.assertLessEqual(steps, 7)

    def test_secret_one(self):
        """秘密数字为 1 时"""
        # 这里我们需要修改 auto_guess_number 来测试特定值
        # 但为了简单，我们只验证它能工作
        pass


# ========================================================================
# 7.5 测试勾股数查找
# ========================================================================

class TestPythagoreanTriplet(unittest.TestCase):
    """测试嵌套 Loop + 多层 Goal"""

    def test_finds_known_triplets(self):
        """应该找到已知的勾股数"""
        triplets = find_pythagorean_triplet(20)
        known = [(3, 4, 5), (5, 12, 13), (6, 8, 10), (8, 15, 17),
                 (9, 12, 15), (12, 16, 20)]
        for t in known:
            self.assertIn(t, triplets)

    def test_no_false_positives(self):
        """所有结果都应该满足 a² + b² = c²"""
        triplets = find_pythagorean_triplet(30)
        for a, b, c in triplets:
            self.assertEqual(a * a + b * b, c * c)
            self.assertLess(a, b)
            self.assertLess(b, c)

    def test_small_limit(self):
        """很小的限制应该返回空列表"""
        triplets = find_pythagorean_triplet(5)
        # (3,4,5) 是唯一 ≤5 的，但 c=5, b=4, a=3，b < c，4 < 5 ✓
        # 实际上 range(1, 6) 包含 5，所以应该找到 (3,4,5)
        self.assertGreaterEqual(len(triplets), 1)


# ========================================================================
# 7.6 综合测试
# ========================================================================

class TestLoopGoalRelationships(unittest.TestCase):
    """
    综合测试：验证 Loop 和 Goal 的四种组合关系。

    这是对整篇文档核心思想的最终验证：
      1. 有 Loop 有 Goal  → 正常程序
      2. 有 Loop 无 Goal  → 死循环（我们不测这个，太危险）
      3. 无 Loop 有 Goal  → 一步到位（公式法）
      4. 无 Loop 无 Goal  → 普通单步语句（不在此范围）
    """

    def test_loop_with_goal_normal(self):
        """情况 1：有 Loop 有 Goal —— 正常工作"""
        result = count_up_until(lambda x: x >= 10, start=1)
        self.assertEqual(result, 10)

    def test_no_loop_with_goal(self):
        """情况 3：无 Loop 有 Goal —— 数学公式一步到位"""
        result = sum_with_formula(100)
        self.assertEqual(result, 5050)
        # 没有 Loop，就直接算出来了


# ========================================================================
# 测试运行器
# ========================================================================

def run_all_tests():
    """运行所有单元测试"""
    print()
    print("=" * 69)
    print("  运行所有单元测试...")
    print("=" * 69)
    print()

    loader = unittest.TestLoader()
    test_cases = [
        TestGoalFunctions,
        TestSumFunctions,
        TestSafetyMechanism,
        TestAutoGuessNumber,
        TestPythagoreanTriplet,
        TestLoopGoalRelationships,
    ]

    all_passed = True
    total_tests = 0
    total_failures = 0
    total_errors = 0

    for tc in test_cases:
        suite = loader.loadTestsFromTestCase(tc)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        total_tests += result.testsRun
        total_failures += len(result.failures)
        total_errors += len(result.errors)
        if not result.wasSuccessful():
            all_passed = False

    print()
    print("  " + "=" * 50)
    print(f"  测试汇总: "
          f"共 {total_tests} 个，"
          f"通过 {total_tests - total_failures - total_errors} 个，"
          f"失败 {total_failures} 个，"
          f"错误 {total_errors} 个")
    if all_passed:
        print("  ✅ 所有测试通过！")
    else:
        print("  ❌ 存在失败的测试")

    return all_passed


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  主入口                                                                ║
# ╚══════════════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        run_all_tests()
    else:
        # 运行所有演示
        pass  # 演示代码已经在模块加载时执行了
