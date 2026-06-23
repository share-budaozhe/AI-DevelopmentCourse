"""
=============================================================================
  GoalDemo — 基于循环（Loop）的目标搜索综合教学演示
  A Comprehensive Educational Demo of Goal-Oriented Looping in Python
=============================================================================

目录 / Table of Contents
─────────────────────────────────────────────────────────────────────────────
  1. 实现原理 (Implementation Principle)
  2. 流程 (Workflow)
  3. 实现技术点 (Technical Points)
  4. 代码实现 (Code Implementation)
  5. 启发性问题 (Heuristic Questions)
  6. 测试文档 (Test Documentation)
─────────────────────────────────────────────────────────────────────────────


╔═══════════════════════════════════════════════════════════════════════════╗
║  1. 实现原理 (Implementation Principle)                                ║
╚═══════════════════════════════════════════════════════════════════════════╝

  核心思想 —— 使用循环（Loop）不断向目标（Goal）逼近。

  现实类比：
  ┌─────────────────────────────────────────────────────────────────────┐
  │  你在森林里迷路了，手机有信号但没地图。朋友在营地等你。              │
  │  每一步你都可以：                                                     │
  │    ① 看看自己现在在哪里（获取当前位置）                              │
  │    ② 判断营地（目标）在哪个方向（计算方向）                          │
  │    ③ 朝那个方向走一步（执行动作）                                    │
  │    ④ 重复直到到达营地（循环）                                        │
  │    ⑤ 到了就停下来（终止条件）                                        │
  └─────────────────────────────────────────────────────────────────────┘

  将这个类比抽象为计算机程序，就是：
    while not at_goal(current_position):
        direction = calculate_direction(current_position, goal)
        current_position = move(current_position, direction)

  这就是 Loop（循环驱动） + GoalDemo（目标演示）的核心：用循环结构驱动
  一个系统不断逼近目标的通用范式。

  本演示中，我们实现三种目标搜索算法：
    1. 随机搜索 (Random Walk)    — 盲目尝试，适合探索
    2. 贪心搜索 (Greedy Search)  — 每次都往目标走最近的一步
    3. A* 搜索 (A* Search)       — 智能寻路，绕过障碍


╔═══════════════════════════════════════════════════════════════════════════╗
║  2. 流程 (Workflow)                                                    ║
╚═══════════════════════════════════════════════════════════════════════════╝

  通用目标搜索流程（适用于所有算法）：

  ┌─────────────────────────────────────────────────────────────┐
  │                     GoalDemo 通用流程                        │
  │                                                             │
  │    Start ──► 初始化环境 & 目标                               │
  │      │                                                      │
  │      ▼                                                      │
  │   ┌──────────────────────┐                                  │
  │   │  while 循环入口       │ ◄────  🔄 Loop 核心              │
  │   │  (检查是否到达目标)   │                                  │
  │   └────────┬─────────────┘                                  │
  │            │ 未到达                                           │
  │            ▼                                                  │
  │   ┌──────────────────────┐                                  │
  │   │  感知当前状态         │  ← 获取 agent 当前位置            │
  │   └────────┬─────────────┘                                  │
  │            ▼                                                  │
  │   ┌──────────────────────┐                                  │
  │   │  选择动作             │  ← 根据算法决定下一步             │
  │   └────────┬─────────────┘                                  │
  │            ▼                                                  │
  │   ┌──────────────────────┐                                  │
  │   │  执行动作             │  ← 移动 agent                    │
  │   └────────┬─────────────┘                                  │
  │            │                                                  │
  │            ▼                                                  │
  │   ┌──────────────────────┐                                  │
  │   │  更新状态 & 记录轨迹   │  ← 记录步数、路径                │
  │   └────────┬─────────────┘                                  │
  │            │                                                  │
  │            └──────────────────► 回到 while 入口 🔄            │
  │                                                             │
  │   到达目标 ──► 输出结果 & 可视化                               │
  │                                                             │
  └─────────────────────────────────────────────────────────────┘

  三种算法的流程差异：

  随机搜索 (Random Walk)
    ├─ 动作选择：从上下左右中随机选一个
    ├─ 特点：可能很慢，但保证探索所有可能路径
    └─ 适合：对地图完全未知时的探索

  贪心搜索 (Greedy Search)
    ├─ 动作选择：计算哪个方向离目标最近，走那个方向
    ├─ 特点：目标明确，但不一定能绕过障碍物
    └─ 适合：无障碍物或障碍物很少的开阔环境

  A* 搜索 (A* Search)
    ├─ 动作选择：使用 f = g + h 评估每个候选节点
    │   ├─ g: 从起点到当前点的实际代价
    │   └─ h: 从当前点到目标的估计代价（启发式）
    ├─ 特点：总能找到最短路径，能绕过障碍物
    └─ 适合：有障碍物的复杂环境


╔═══════════════════════════════════════════════════════════════════════════╗
║  3. 实现技术点 (Technical Points)                                      ║
╚═══════════════════════════════════════════════════════════════════════════╝

  技术点 1 —— while 循环结构
  ────────────────────────────────────────────
  核心循环 while not at_goal(): 是 GoalDemo 的发动机。
  每次迭代 = 一步。我们通过 step_limit 防止死循环。

  技术点 2 —— 曼哈顿距离 (Manhattan Distance)
  ────────────────────────────────────────────
  h = |x1 - x2| + |y1 - y2|
  用于贪心搜索和 A* 的启发式评估。
  在网格环境中，曼哈顿距离是可采纳的（admissible），
  即它永远不会高估到目标的实际距离。

  技术点 3 —— 优先级队列 (Priority Queue)
  ────────────────────────────────────────────
  A* 使用 heapq 来管理 open set。
  每次从队列中取出 f 值最小的节点。
  这是 A* 高效的关键数据结构。

  技术点 4 —— 回溯路径重建
  ────────────────────────────────────────────
  使用 came_from 字典记录每个节点是从哪个节点来的。
  找到目标后，从目标回溯到起点重建完整路径。

  技术点 5 —— 边界检查与障碍物检测
  ────────────────────────────────────────────
  二维网格需要边界保护。
  障碍物用集合存储，O(1) 查询。

  技术点 6 —— 步数限制 (Step Limit)
  ────────────────────────────────────────────
  任何循环都可能"跑飞"。step_limit 是安全网，
  防止无限循环消耗资源。
"""

import heapq
import random


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  4. 代码实现 (Code Implementation)                                    ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

# ========================================================================
# 4.1 网格世界环境 (GridWorld Environment)
# ========================================================================

class GridWorld:
    """
    二维网格世界 —— agent 在其中移动寻找目标。

    网格坐标：(row, col)，从 (0, 0) 开始。
    0 = 空地，1 = 障碍物。

    示例 5×5 网格：
        S . . . .
        . . X . .
        . . X . .
        . . X . .
        . . . . G

    S = 起点, G = 目标, X = 障碍物, . = 空地
    """

    # 四个移动方向：(行偏移, 列偏移)
    DIRECTIONS = [
        (-1, 0),   # 上
        (1, 0),    # 下
        (0, -1),   # 左
        (0, 1),    # 右
    ]
    DIRECTION_NAMES = {
        (-1, 0): "↑ 上",
        (1, 0):  "↓ 下",
        (0, -1): "← 左",
        (0, 1):  "→ 右",
    }

    def __init__(self, width: int, height: int,
                 obstacles: list[tuple[int, int]] | None = None):
        """
        初始化网格世界。

        参数:
            width: 网格宽度（列数）
            height: 网格高度（行数）
            obstacles: 障碍物坐标列表 [(row, col), ...]
        """
        self.width = width
        self.height = height
        self.obstacles = set(obstacles or [])   # 集合，O(1) 查询

    def is_walkable(self, pos: tuple[int, int]) -> bool:
        """检查某个位置是否可以行走（在边界内且不是障碍物）"""
        row, col = pos
        return (
            0 <= row < self.height
            and 0 <= col < self.width
            and pos not in self.obstacles
        )

    def get_neighbors(self, pos: tuple[int, int]) -> list[tuple[int, int]]:
        """获取某个位置的所有可通行邻居"""
        neighbors = []
        for dr, dc in self.DIRECTIONS:
            neighbor = (pos[0] + dr, pos[1] + dc)
            if self.is_walkable(neighbor):
                neighbors.append(neighbor)
        return neighbors

    def visualize(self, agent_pos: tuple[int, int],
                  goal_pos: tuple[int, int],
                  path: list[tuple[int, int]] | None = None) -> str:
        """
        将网格世界可视化为字符串。

        图例:
            S = 起点 (agent)
            G = 目标
            X = 障碍物
            · = 空地
            * = 路径
        """
        path_set = set(path or [])
        lines = []
        lines.append(f"  网格 {self.width}×{self.height}  "
                     f"(障碍物: {len(self.obstacles)} 个)")
        lines.append("")

        # 列号标头
        header = "     " + " ".join(f"{c:>2}" for c in range(self.width))
        lines.append(header)
        lines.append("    " + "---" * self.width)

        for r in range(self.height):
            row_str = f" {r:>2} |"
            for c in range(self.width):
                pos = (r, c)
                if pos == agent_pos:
                    row_str += " S "   # Agent
                elif pos == goal_pos:
                    row_str += " G "   # 目标
                elif pos in self.obstacles:
                    row_str += " X "   # 障碍物
                elif path_set and pos in path_set:
                    row_str += " * "   # 路径
                else:
                    row_str += " · "   # 空地
            lines.append(row_str)

        lines.append("    " + "---" * self.width)
        return "\n".join(lines)


# ========================================================================
# 4.2 辅助函数 (Helper Functions)
# ========================================================================

def manhattan_distance(a: tuple[int, int],
                       b: tuple[int, int]) -> int:
    """曼哈顿距离 = |行差| + |列差|"""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


# ========================================================================
# 4.3 算法 1 —— 随机搜索 (Random Walk)
# ========================================================================

def random_walk_search(
    world: GridWorld,
    start: tuple[int, int],
    goal: tuple[int, int],
    step_limit: int = 10000,
) -> dict:
    """
    随机搜索算法。

    Loop 原理：
      while not at_goal:
          从可走方向中随机选一个 → 移动 → 步数+1

    优点：实现简单，无需地图先验知识
    缺点：效率极低，可能永远找不到（理论上无限）

    返回包含以下键的字典:
        success:      是否找到目标
        steps:        总步数
        path:         走过的路径 (列表)
        explored:     探索过的位置数
        algorithm:    算法名称
    """
    current = start
    path = [current]
    visited = {current}

    # 🔄 ===== Loop 核心 =====
    for step in range(1, step_limit + 1):
        # ① 获取可通行的邻居
        neighbors = world.get_neighbors(current)

        if not neighbors:
            # 被困住了，无法继续
            break

        # ② 随机选择一个方向
        next_pos = random.choice(neighbors)

        # ③ 执行移动
        current = next_pos
        path.append(current)
        visited.add(current)

        # ④ 检查是否到达目标
        if current == goal:
            return {
                "success": True,
                "steps": step,
                "path": path,
                "explored": len(visited),
                "algorithm": "Random Walk (随机搜索)",
            }
    # ===== Loop 结束 =====

    return {
        "success": False,
        "steps": len(path) - 1,
        "path": path,
        "explored": len(visited),
        "algorithm": "Random Walk (随机搜索)",
    }


# ========================================================================
# 4.4 算法 2 —— 贪心搜索 (Greedy / Best-First Search)
# ========================================================================

def greedy_search(
    world: GridWorld,
    start: tuple[int, int],
    goal: tuple[int, int],
    step_limit: int = 10000,
) -> dict:
    """
    贪心最佳优先搜索。

    Loop 原理：
      while not at_goal:
          计算所有邻居到目标的曼哈顿距离
          选距离最小的方向移动

    优点：目标明确，效率较高
    缺点：可能被障碍物"欺骗"，走入死胡同

    返回包含以下键的字典:
        success:      是否找到目标
        steps:        总步数
        path:         走过的路径
        explored:     探索过的位置数
        algorithm:    算法名称
    """
    current = start
    path = [current]
    visited = {current}

    # 🔄 ===== Loop 核心 =====
    for step in range(1, step_limit + 1):
        if current == goal:
            return {
                "success": True,
                "steps": step - 1,
                "path": path,
                "explored": len(visited),
                "algorithm": "Greedy Search (贪心搜索)",
            }

        # ① 获取可通行的邻居
        neighbors = world.get_neighbors(current)

        if not neighbors:
            break  # 无路可走

        # ② 计算每个邻居到目标的曼哈顿距离，选最近的
        #    未访问过的邻居优先
        candidates = []
        for n in neighbors:
            dist = manhattan_distance(n, goal)
            unvisited_priority = 0 if n not in visited else 1
            candidates.append((unvisited_priority, dist, n))

        # 排序：首先选未访问的，其次选距离近的
        candidates.sort(key=lambda x: (x[0], x[1]))
        next_pos = candidates[0][2]

        # ③ 执行移动
        current = next_pos
        path.append(current)
        visited.add(current)
    # ===== Loop 结束 =====

    return {
        "success": False,
        "steps": len(path) - 1,
        "path": path,
        "explored": len(visited),
        "algorithm": "Greedy Search (贪心搜索)",
    }


# ========================================================================
# 4.5 算法 3 —— A* 搜索 (A* Search)
# ========================================================================

def astar_search(
    world: GridWorld,
    start: tuple[int, int],
    goal: tuple[int, int],
    step_limit: int = 10000,
) -> dict:
    """
    A* 搜索算法 —— 启发式路径搜索，保证最短路径。

    核心公式：  f(n) = g(n) + h(n)

    其中:
        g(n) = 从起点到当前点 n 的实际代价（步数）
        h(n) = 从当前点 n 到目标的估计代价（曼哈顿距离）
        f(n) = 总估计代价

    Loop 原理：
      while open_set 不为空:
          从 open_set 取出 f 值最小的节点
          如果是目标 → 重建路径并返回
          否则，检查所有邻居并更新代价

    优点：保证最短路径，能绕过障碍物
    缺点：在超大网格中可能消耗较多内存

    返回包含以下键的字典:
        success:      是否找到目标
        steps:        最短路径长度
        path:         最短路径坐标列表
        explored:     探索过的位置数
        algorithm:    算法名称
    """
    # open_set: 待探索的节点，用 (f_score, counter, pos) 存储
    # heapq 自动按 f_score 排序
    counter = 0
    open_set = []
    heapq.heappush(open_set, (0, counter, start))

    # g_score: 从起点到每个节点的已知最短距离
    g_score = {start: 0}

    # came_from: 记录路径（哪个节点 -> 哪个节点），用于回溯
    came_from = {}

    # 记录所有访问过的节点
    explored = {start}

    # 🔄 ===== Loop 核心 =====
    while open_set:
        # ① 从优先级队列中取出 f 值最小的节点
        current_f, _, current = heapq.heappop(open_set)

        # ② 到达目标？回溯重建路径！
        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()  # 从起点到目标的顺序

            return {
                "success": True,
                "steps": g_score[goal],
                "path": path,
                "explored": len(explored),
                "algorithm": "A* Search (A* 搜索)",
            }

        # ③ 检查所有邻居
        for neighbor in world.get_neighbors(current):
            # 到邻居的 tentative g_score
            tentative_g = g_score[current] + 1

            # 如果找到了更好的路径，更新
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                g_score[neighbor] = tentative_g
                f_score = tentative_g + manhattan_distance(neighbor, goal)

                came_from[neighbor] = current
                explored.add(neighbor)

                counter += 1
                heapq.heappush(open_set, (f_score, counter, neighbor))
    # ===== Loop 结束 =====

    return {
        "success": False,
        "steps": -1,
        "path": [],
        "explored": len(explored),
        "algorithm": "A* Search (A* 搜索)",
    }


# ========================================================================
# 4.6 结果展示 (Result Display)
# ========================================================================

def print_result(result: dict):
    """友好地打印搜索结果"""
    icon = "✅" if result["success"] else "❌"
    print(f"  {icon} 算法: {result['algorithm']}")
    print(f"     {'✓ 找到目标!' if result['success'] else '✗ 未找到目标'}")
    print(f"     步数:      {result['steps']}")
    print(f"     探索位置数: {result['explored']}")
    if result["path"]:
        print(f"     路径长度:   {len(result['path'])}")
        # 显示路径的前5个和后5个点
        path = result["path"]
        if len(path) > 10:
            print(f"     路径(首尾): {path[:5]} ... {path[-5:]}")
        else:
            print(f"     路径:       {path}")
    print()


def run_all_algorithms(world: GridWorld, start: tuple[int, int],
                       goal: tuple[int, int], step_limit: int = 50000):
    """在同一个世界上运行所有三种算法并对比结果"""
    print("=" * 65)
    print("  GoalDemo — 目标搜索算法对比演示")
    print("=" * 65)
    print()
    print(world.visualize(None, goal))
    print(f"\n  起点: {start}")
    print(f"  目标: {goal}")
    print()

    algorithms = [
        ("Random Walk", random_walk_search),
        ("Greedy", greedy_search),
        ("A*", astar_search),
    ]

    results = []
    for name, func in algorithms:
        print(f"  ┌{'─'*50}┐")
        print(f"  │ 正在运行: {name}...")
        print(f"  └{'─'*50}┘")
        result = func(world, start, goal, step_limit)
        print_result(result)
        results.append(result)

    # 对比表
    print("  " + "=" * 50)
    print("  算法对比总结:")
    print("  " + "=" * 50)
    print(f"  {'算法':<20} {'结果':<8} {'步数':<8} {'探索数':<8}")
    print(f"  {'─'*44}")
    for r in results:
        status = "✓ 到达" if r["success"] else "✗ 失败"
        steps = str(r["steps"]) if r["steps"] >= 0 else "N/A"
        print(f"  {r['algorithm']:<20} {status:<8} {steps:<8} {r['explored']:<8}")

    return results


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  5. 启发性问题 (Heuristic Questions)                                    ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
#
#   以下问题用于帮助理解 Loop 和 GoalDemo 的核心概念。
#   每个问题都附有提示和简要答案。
#
# ──────────────────────────────────────────────────────────────────────────
#   问题 1（基础）:
#   Q: 为什么所有搜索算法都使用 while 循环而不是 for 循环？
#   A:
#      while 循环在"条件不满足时持续执行"，这正是目标搜索的语义——
#      "只要没到目标就继续走"。for 循环要求预先知道迭代次数，
#      而搜索算法不知道需要多少步才能到达目标。
#      try:
#          while not at_goal:
#              keep_searching()
#      except OutOfSteps:
#          give_up()
#
# ──────────────────────────────────────────────────────────────────────────
#   问题 2（基础）:
#   Q: 如果没有 step_limit 会发生什么？
#   A:
#      - 如果算法总能到达目标 → 最终正常结束，不影响
#      - 如果算法有 bug 或永远无法到达目标 → 无限循环，
#        程序"卡死"，CPU 100%，必须手动终止
#      step_limit 就像"安全气囊"——平时用不上，但关键时刻救命
#
# ──────────────────────────────────────────────────────────────────────────
#   问题 3（进阶）:
#   Q: 贪心搜索（Greedy）明明每次都往目标方向走，为什么可能失败？
#   A:
#      贪心搜索只关注"局部最优"——它只看下一步哪个方向离目标最近。
#      如果目标被一堵墙挡住：
#        贪心会一直走向墙（因为墙离目标"直线距离"最近）
#        撞墙后才绕路，可能绕到更远的方向
#      就像开车只用指南针不看地图——方向对了，但前面有条河
#
# ──────────────────────────────────────────────────────────────────────────
#   问题 4（进阶）:
#   Q: A* 的 f = g + h 中，g 和 h 各自起什么作用？
#   A:
#      g（已走代价）：保证算法不会"绕远路"，因为走过的步数会被记录
#      h（估计代价）：引导算法朝目标方向搜索，避免盲目乱走
#
#      极端情况：
#      - 如果 h = 0（没有启发式）→ A* 退化为 Dijkstra 算法，
#        向所有方向均匀扩散
#      - 如果 g = 0（忽略已走代价）→ A* 退化为贪心搜索，
#        可能被障碍物欺骗
#
#      A* 的精妙就在于 g 和 h 的平衡！
#
# ──────────────────────────────────────────────────────────────────────────
#   问题 5（进阶）:
#   Q: 为什么 A* 用 heapq（优先级队列）而不是普通列表？
#   A:
#      普通列表找最小值：O(n) —— 每步都要扫描整个列表
#      堆顶取最小值：    O(1) —— 直接拿到
#      堆插入：          O(log n)
#
#      在 10000 步的搜索中：
#        普通列表 ≈ 10000 × 10000/2 ≈ 5000 万次比较
#        堆 ≈ 10000 × log₂(10000) ≈ 13 万次比较
#      差了近 400 倍！这就是数据结构选择的力量。
#
# ──────────────────────────────────────────────────────────────────────────
#   问题 6（综合）:
#   Q: Loop 在目标搜索之外还能用在哪些地方？
#   A:
#      这种"循环逼近目标"的模式无处不在：
#      - 梯度下降：while loss > threshold: parameters -= gradient
#      - 游戏 AI：while player_alive: make_decision()
#      - 自动导航：while not at_destination: recalculate_route()
#      - 强化学习：while not solved: agent.interact(environment)
#      - 编译器优化：while code_changed: apply_optimizations()
#
#      Loop + Goal 是计算机科学中最基础也最强大的模式之一。
#
# ──────────────────────────────────────────────────────────────────────────
#   问题 7（反思）:
#   Q: 如果地图非常大（比如 10000×10000），哪种算法最合适？
#   A:
#      - 如果有全局地图且需要最短路径 → A*（但注意内存）
#      - 如果地图基本开阔 → 贪心（极快）
#      - 如果完全不知道地图 → 随机搜索（总是可选，但慢）
#      - 实际工程中常用分层策略：
#        先使用粗略 A* 规划大方向
#        到达子目标后，再用贪心或局部搜索微调
#        就像你旅行时：
#          先用地图规划"北京→上海"的高铁（宏观 A*）
#          到了上海再导航到具体酒店（局部贪心）
#


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  6. 测试文档 (Test Documentation)                                      ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
#
#   测试策略：
#     ┌──────────────────────────────────────────────────────────────┐
#     │  我们对每个算法测试 4 个维度：                                │
#     │    ① 无障碍物时是否能找到目标                                │
#     │    ② 有障碍物时是否能绕过障碍找到目标                        │
#     │    ③ 无路可走时是否正确报告失败                              │
#     │    ④ 路径是否合法（每步都是相邻格子，不穿过障碍物）          │
#     └──────────────────────────────────────────────────────────────┘
#

import unittest


class TestGridWorld(unittest.TestCase):
    """测试网格世界的核心功能"""

    def test_walkable_empty_cell(self):
        """空地应该可以行走"""
        world = GridWorld(5, 5)
        self.assertTrue(world.is_walkable((2, 3)))

    def test_obstacle_not_walkable(self):
        """障碍物应该不可行走"""
        world = GridWorld(5, 5, obstacles=[(2, 3)])
        self.assertFalse(world.is_walkable((2, 3)))

    def test_out_of_bounds_not_walkable(self):
        """边界外的位置应该不可行走"""
        world = GridWorld(5, 5)
        self.assertFalse(world.is_walkable((-1, 0)))
        self.assertFalse(world.is_walkable((0, 5)))
        self.assertFalse(world.is_walkable((5, 0)))

    def test_get_neighbors_center(self):
        """中心位置的邻居应该有 4 个"""
        world = GridWorld(5, 5)
        neighbors = world.get_neighbors((2, 2))
        self.assertEqual(len(neighbors), 4)

    def test_get_neighbors_corner(self):
        """角落位置的邻居应该有 2 个"""
        world = GridWorld(5, 5)
        neighbors = world.get_neighbors((0, 0))
        self.assertEqual(len(neighbors), 2)

    def test_obstacle_not_in_neighbors(self):
        """障碍物不应出现在邻居列表中"""
        world = GridWorld(5, 5, obstacles=[(1, 2)])
        neighbors = world.get_neighbors((1, 1))
        self.assertNotIn((1, 2), neighbors)


class TestRandomWalk(unittest.TestCase):
    """测试随机搜索算法"""

    def test_no_obstacle_reaches_goal(self):
        """无障碍物时，随机搜索应能找到目标（大概率）"""
        random.seed(42)  # 固定随机种子以保证可重复
        world = GridWorld(5, 5)
        result = random_walk_search(world, (0, 0), (4, 4), step_limit=50000)
        self.assertTrue(result["success"])

    def test_path_starts_at_start(self):
        """路径应以起点开始"""
        random.seed(42)
        world = GridWorld(5, 5)
        result = random_walk_search(world, (0, 0), (4, 4), step_limit=50000)
        self.assertEqual(result["path"][0], (0, 0))

    def test_path_ends_at_goal_when_successful(self):
        """成功时路径应在目标结束"""
        random.seed(42)
        world = GridWorld(5, 5)
        result = random_walk_search(world, (0, 0), (4, 4), step_limit=50000)
        if result["success"]:
            self.assertEqual(result["path"][-1], (4, 4))

    def test_path_is_continuous(self):
        """路径中每相邻两步必须相邻（不能跳跃）"""
        random.seed(42)
        world = GridWorld(5, 5)
        result = random_walk_search(world, (0, 0), (4, 4), step_limit=50000)
        path = result["path"]
        for i in range(len(path) - 1):
            dr = abs(path[i][0] - path[i + 1][0])
            dc = abs(path[i][1] - path[i + 1][1])
            self.assertTrue((dr == 1 and dc == 0) or (dr == 0 and dc == 1),
                            f"路径不连续: {path[i]} -> {path[i + 1]}")


class TestGreedySearch(unittest.TestCase):
    """测试贪心搜索算法"""

    def test_no_obstacle_reaches_goal(self):
        """无障碍物时，贪心搜索应能到达目标"""
        world = GridWorld(5, 5)
        result = greedy_search(world, (0, 0), (4, 4))
        self.assertTrue(result["success"])

    def test_with_obstacles_reaches_goal(self):
        """有障碍物但可绕行时，贪心搜索应能到达目标"""
        world = GridWorld(5, 5, obstacles=[(2, 2), (2, 3)])
        result = greedy_search(world, (0, 0), (4, 4), step_limit=50000)
        self.assertTrue(result["success"])

    def test_path_does_not_cross_obstacles(self):
        """路径不应穿过障碍物"""
        obstacles = [(2, 2), (2, 3)]
        world = GridWorld(5, 5, obstacles=obstacles)
        result = greedy_search(world, (0, 0), (4, 4), step_limit=50000)
        for pos in result["path"]:
            self.assertNotIn(pos, obstacles)

    def test_fails_when_blocked(self):
        """被障碍物完全包围时应报告失败"""
        # 创建一个"迷宫"——起点被完全包围
        obstacles = [
            (1, 0), (0, 1), (1, 1),
        ]
        world = GridWorld(3, 3, obstacles=obstacles)
        result = greedy_search(world, (0, 0), (2, 2), step_limit=1000)
        self.assertFalse(result["success"])


class TestAStar(unittest.TestCase):
    """测试 A* 搜索算法"""

    def test_no_obstacle_finds_shortest_path(self):
        """无障碍物时，A* 应该找到曼哈顿距离长度的最短路径"""
        world = GridWorld(5, 5)
        start, goal = (0, 0), (4, 4)
        result = astar_search(world, start, goal)
        self.assertTrue(result["success"])
        expected_min = manhattan_distance(start, goal)
        self.assertEqual(result["steps"], expected_min,
                         f"A* 应找到最短路径 ({expected_min} 步)，"
                         f"实际 {result['steps']} 步")

    def test_with_obstacles_finds_shortest_path(self):
        """有障碍物时，A* 应能找到绕过障碍物的最短路径"""
        world = GridWorld(5, 5, obstacles=[(2, 0), (2, 1), (2, 2)])
        result = astar_search(world, (0, 0), (4, 4))
        self.assertTrue(result["success"])
        self.assertGreaterEqual(result["steps"],
                                manhattan_distance((0, 0), (4, 4)))

    def test_path_does_not_cross_obstacles(self):
        """A* 路径不应穿过障碍物"""
        obstacles = [(2, 2), (2, 3)]
        world = GridWorld(5, 5, obstacles=obstacles)
        result = astar_search(world, (0, 0), (4, 4))
        for pos in result["path"]:
            self.assertNotIn(pos, obstacles)

    def test_path_is_continuous(self):
        """A* 路径必须是连续的"""
        world = GridWorld(5, 5, obstacles=[(2, 2)])
        result = astar_search(world, (0, 0), (4, 4))
        path = result["path"]
        for i in range(len(path) - 1):
            dr = abs(path[i][0] - path[i + 1][0])
            dc = abs(path[i][1] - path[i + 1][1])
            self.assertTrue((dr == 1 and dc == 0) or (dr == 0 and dc == 1))

    def test_fails_when_impossible(self):
        """目标完全不可达时应报告失败"""
        # 用一堵墙把左右完全隔开
        obstacles = [(r, 2) for r in range(5)]   # 一整列障碍物
        world = GridWorld(5, 5, obstacles=obstacles)
        result = astar_search(world, (0, 0), (0, 4))
        self.assertFalse(result["success"])

    def test_start_is_goal(self):
        """起点就是目标时，步数应为 0"""
        world = GridWorld(5, 5)
        result = astar_search(world, (3, 3), (3, 3))
        self.assertTrue(result["success"])
        self.assertEqual(result["steps"], 0)
        self.assertEqual(len(result["path"]), 1)

    def test_empty_path_no_success(self):
        """失败时路径应为空"""
        obstacles = [(r, 2) for r in range(5)]
        world = GridWorld(5, 5, obstacles=obstacles)
        result = astar_search(world, (0, 0), (0, 4))
        self.assertEqual(result["path"], [])


class TestManhattanDistance(unittest.TestCase):
    """测试曼哈顿距离函数"""

    def test_same_point(self):
        """同一点的距离应为 0"""
        self.assertEqual(manhattan_distance((3, 3), (3, 3)), 0)

    def test_horizontal(self):
        """水平方向的距离"""
        self.assertEqual(manhattan_distance((0, 0), (0, 5)), 5)

    def test_vertical(self):
        """垂直方向的距离"""
        self.assertEqual(manhattan_distance((0, 0), (5, 0)), 5)

    def test_diagonal(self):
        """对角方向 = 水平+垂直"""
        self.assertEqual(manhattan_distance((0, 0), (3, 4)), 7)

    def test_negative_coordinates_not_supported(self):
        """曼哈顿距离始终为非负数"""
        d = manhattan_distance((0, 0), (-3, -4))
        self.assertEqual(d, 7)

    def test_commutative(self):
        """曼哈顿距离满足交换律：d(a,b) == d(b,a)"""
        self.assertEqual(
            manhattan_distance((1, 5), (4, 2)),
            manhattan_distance((4, 2), (1, 5)),
        )


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  主函数 (Main)                                                         ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

def demo_simple():
    """
    一个简单直观的演示 —— 5×5 网格，少量障碍物。

    网格布局:
        S . . . .
        . . X . .
        . . X . .
        . . . . .
        . . . . G
    """
    print("=" * 65)
    print("  GoalDemo — 简单演示 (Simple Demo)")
    print("=" * 65)
    print()

    world = GridWorld(5, 5, obstacles=[(1, 2), (2, 2)])
    start = (0, 0)
    goal = (4, 4)

    print(world.visualize(start, goal))
    print()
    run_all_algorithms(world, start, goal, step_limit=100000)


def demo_maze():
    """
    迷宫演示 —— 更复杂的障碍物布局。

    网格布局:
        S . X . .
        . . X . .
        . . . . X
        X . . X .
        . . . . G
    """
    print("=" * 65)
    print("  GoalDemo — 迷宫演示 (Maze Demo)")
    print("=" * 65)
    print()

    world = GridWorld(5, 5, obstacles=[
        (0, 2),
        (1, 2),
        (2, 4),
        (3, 0), (3, 3),
    ])
    start = (0, 0)
    goal = (4, 4)

    print(world.visualize(start, goal))
    print()
    run_all_algorithms(world, start, goal, step_limit=100000)


def run_tests():
    """运行所有单元测试"""
    print("=" * 65)
    print("  GoalDemo — 单元测试 (Unit Tests)")
    print("=" * 65)
    print()

    loader = unittest.TestLoader()
    test_cases = [
        TestGridWorld,
        TestManhattanDistance,
        TestRandomWalk,
        TestGreedySearch,
        TestAStar,
    ]

    all_results = []
    for tc in test_cases:
        suite = loader.loadTestsFromTestCase(tc)
        runner = unittest.TextTestRunner(verbosity=2)
        print()
        result = runner.run(suite)
        all_results.append(result)

    # 汇总
    print()
    print("  " + "=" * 50)
    print("  测试汇总:")
    total = sum(r.testsRun for r in all_results)
    failures = sum(len(r.failures) for r in all_results)
    errors = sum(len(r.errors) for r in all_results)
    print(f"  共 {total} 个测试，"
          f"通过 {total - failures - errors} 个，"
          f"失败 {failures} 个，"
          f"错误 {errors} 个")
    print()

    # 非零退出码让 CI/脚本能检测到失败
    if failures > 0 or errors > 0:
        return False
    return True


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # python goal_demo.py test  — 运行测试
        ok = run_tests()
        sys.exit(0 if ok else 1)
    elif len(sys.argv) > 1 and sys.argv[1] == "maze":
        # python goal_demo.py maze  — 迷宫演示
        demo_maze()
    else:
        # python goal_demo.py       — 简单演示
        demo_simple()
