# 技术要点与实现

> **文档版本**: v1.0  
> **对应代码**: `loop_and_goal.py`  
> **覆盖范围**: 六大技术点详解 + 代码实现分析

---

## 目录

- [1. while 循环 vs for 循环](#1-while-循环-vs-for-循环)
- [2. break 和 continue —— Loop 的控制指令](#2-break-和-continue--loop-的控制指令)
- [3. 递归也是一种 Loop](#3-递归也是一种-loop)
- [4. Step Limit —— Loop 的安全阀](#4-step-limit--loop-的安全阀)
- [5. 把 Goal 作为参数传递（高阶函数）](#5-把-goal-作为参数传递高阶函数)
- [6. Goal 的五种表达方式](#6-goal-的五种表达方式)
- [附录：代码结构总览](#附录代码结构总览)

---

## 1. while 循环 vs for 循环

### 1.1 核心区别

| 维度 | `while` 循环 | `for` 循环 |
|------|-------------|-----------|
| 迭代次数 | 未知（由条件决定） | 已知（由集合决定） |
| 适用场景 | Goal 驱动型任务 | 集合遍历型任务 |
| 循环变量 | 手动管理 | 自动管理 |
| 死循环风险 | 高（忘记更新变量） | 低（遍历完自动结束） |
| 灵活性 | 高（任意条件） | 中（限于可迭代对象） |

### 1.2 代码对比

```python
# ===== while 循环：适合"不知要循环多少次" =====
def sum_with_while(n: int) -> int:
    total = 0
    i = 1
    while i <= n:         # Loop：条件驱动
        total += i
        i += 1            # ⚠️ 必须手动更新，否则死循环
    return total          # Goal：加完所有数

# ===== for 循环：适合"知道要遍历什么" =====
def sum_with_for(n: int) -> int:
    total = 0
    for i in range(1, n + 1):   # Loop：集合驱动，自动迭代
        total += i
    return total                  # Goal：遍历完
```

### 1.3 选型指南

```
问题场景                         推荐
──────────────────────────────────────────────
"不断尝试直到成功"               → while（例：猜数字）
"处理集合中的每个元素"           → for（例：遍历列表）
"不知道要循环多少次"             → while（例：搜索）
"知道确切范围"                   → for（例：求和 1..100）
"条件会动态变化"                 → while（例：用户输入）
"条件固定不变"                   → for（例：固定次数）
```

---

## 2. break 和 continue —— Loop 的控制指令

### 2.1 概念

| 指令 | 作用 | 类比 |
|------|------|------|
| `break` | **立即终止**整个 Loop | 紧急刹车 |
| `continue` | **跳过本轮**，开始下一轮 | 跳过这一步 |

### 2.2 代码示例

```python
# break：到达 Goal 就停止
while True:
    guess = get_input()
    if guess == secret:    # 🎯 Goal 判断
        break              # 🛑 立即结束整个循环
    print("再试一次")

# continue：不合法的输入跳过本轮
while True:
    value = get_value()
    if value < 0:          # 非法值
        continue           # ⏭️ 跳过本轮，不执行后续代码
    process(value)
    if value == target:    # 🎯 Goal
        break
```

### 2.3 break 的"一层"规则

```python
# break 只跳出当前层，不影响外层
while outer_condition:           # 外层 Loop
    print("外层开始")
    while inner_condition:       # 内层 Loop
        if some_condition:
            break                # 🛑 只跳出内层，外层继续
        print("内层")
    print("外层结束")            # break 后会执行到这里！
```

> **技术要点**：如果需要跳出多层循环，可以使用"标志变量"或"异常"。

```python
# 方式 1：标志变量
found = False
for a in range(N):
    for b in range(N):
        if a * b == target:
            found = True
            break
    if found:
        break

# 方式 2：异常（适用于深度嵌套）
class FoundException(Exception):
    pass

try:
    for a in range(N):
        for b in range(N):
            if a * b == target:
                raise FoundException()
except FoundException:
    print("找到了！")
```

---

## 3. 递归也是一种 Loop

### 3.1 递归 vs 迭代式循环

很多人认为递归和循环是两回事，但本质上是**同一种模式的不同表达**：

```
┌─────────────────────────────────────────────────────┐
│  递归 = 函数调用自己                                 │
│  迭代 = 代码跳回开头（goto / while / for）          │
│                                                      │
│  两者关系：                                          │
│    • 递归的"基线条件" = 迭代的"Goal 判断"            │
│    • 递归的"递推步骤" = 迭代的"循环体"               │
│    • 递归的"函数栈"  = 迭代的"循环变量"              │
└─────────────────────────────────────────────────────┘
```

### 3.2 代码对比

```python
# ===== 递归方式 =====
def sum_with_recursion(n: int) -> int:
    if n == 1:             # 🎯 基线条件（Goal）
        return 1
    return n + sum_with_recursion(n - 1)  # 🔄 递归调用（Loop）

# ===== 等价的 while 方式 =====
def sum_with_while(n: int) -> int:
    total = 0
    while n > 0:           # 🔄 Loop
        total += n
        n -= 1
    return total           # 🎯 Goal 隐含在 while 条件中
```

### 3.3 递归的执行过程

以 `sum_with_recursion(5)` 为例：

```
调用栈（Call Stack）：
    ❮❯ sum_with_recursion(5)
        → 5 + sum_with_recursion(4)        # 递推：压栈
            → 4 + sum_with_recursion(3)    # 递推：压栈
                → 3 + sum_with_recursion(2)    # 递推：压栈
                    → 2 + sum_with_recursion(1)    # 递推：压栈
                        → return 1               # 🎯 基线条件到达
                    → return 2 + 1 = 3           # 回归：弹栈
                → return 3 + 3 = 6           # 回归：弹栈
            → return 4 + 6 = 10          # 回归：弹栈
        → return 5 + 10 = 15         # 回归：弹栈
```

### 3.4 递归的适用性

| 场景 | 是否推荐递归 | 原因 |
|------|------------|------|
| 树形遍历（文件系统、DOM） | ✅ 推荐 | 代码简洁，符合直觉 |
| 分治算法（快排、归并） | ✅ 推荐 | 自然表达"分而治之" |
| 简单线性迭代（求和） | ❌ 不推荐 | 有调用栈开销 |
| 深度未知的搜索 | ⚠️ 小心 | 可能栈溢出（Python 默认限制 ~1000 层） |

---

## 4. Step Limit —— Loop 的安全阀

### 4.1 为什么需要 Step Limit

Loop 可能因为以下原因永远停不下来：

1. **Goal 不可达**：条件永远无法满足（如 `x == -1` 但 x 只增不减）
2. **循环变量忘记更新**：`i = 1; while i < 10: print(i)` — i 永远是 1
3. **逻辑错误**：条件写反了，永远为 True
4. **外部因素**：等待的资源永远不会到达

Step Limit 是最后一道防线，就像"安全气囊"——平时用不上，关键时刻救命。

### 4.2 实现模式

```python
def safe_search(start, goal_check, max_steps=1000):
    """
    带步数限制的安全搜索。

    架构：
        for step in range(max_steps):   ← 内置步数限制（安全阀）
            if goal_check(state):        ← Goal 判断
                return success
            update(state)                ← 迭代逻辑
        return failure                   ← 超步数限制
    """
    current = start

    # for 循环在这里充当了双重角色：
    #   1. 🔄 驱动迭代（Loop 的功能）
    #   2. 🛡️ 提供步数限制（安全阀的功能）
    for step in range(1, max_steps + 1):
        if goal_check(current):          # 🎯 Goal 判断
            return True, current, step
        current += 1                     # 更新状态

    return False, current, max_steps     # ❌ 超步数限制
```

### 4.3 三种场景

| 场景 | 输入 | 结果 | 说明 |
|------|------|------|------|
| Goal 可达 | `goal: x>=50, steps=100` | ✅ 第 50 步到达 | 正常 |
| Goal 不可达 | `goal: x==-1, steps=100` | ❌ 100 步后失败 | 条件永远不满足 |
| 步数不够 | `goal: x>=1000, steps=50` | ❌ 50 步后失败 | 再多 950 步就行 |

### 4.4 工程实践中的其他"安全阀"

除了 `step_limit`，实际工程中还有：

| 安全阀 | 适用场景 | 代码实现 |
|--------|---------|---------|
| `max_retries` | 网络请求、重试操作 | `for i in range(max_retries)` |
| `timeout` | 耗时操作、外部调用 | `signal.alarm(timeout)` |
| `max_memory` | 数据处理 | 检查 `sys.getsizeof()` |
| `max_depth` | 搜索、递归 | `if depth > max_depth: return` |

---

## 5. 把 Goal 作为参数传递（高阶函数）

### 5.1 概念

Python 允许函数作为参数传递。利用这个特性，我们可以：

```python
def count_up_until(goal_condition, start=1):
    """
    通用"往上数"函数。

    goal_condition 是一个函数，接收当前值，返回 True/False。
    调用者通过传入不同的 goal_condition 来定制目标。

    参数:
        goal_condition: Callable[[int], bool] — Goal 判断函数
        start: int — 起始值
    """
    current = start
    while True:
        if goal_condition(current):  # 🎯 调用外部 Goal 判断
            return current
        current += 1                  # 🔄 迭代
```

### 5.2 四种不同的 Goal

```python
# Goal A：找到第一个大于 50 的质数
count_up_until(lambda x: is_prime(x) and x > 50)

# Goal B：数到 100
count_up_until(lambda x: x >= 100)

# Goal C：各位数字之和大于 20
count_up_until(lambda x: sum(int(d) for d in str(x)) > 20)

# Goal D：找到第 10 个完全平方数
square_count = 0
def tenth_square(x):
    global square_count
    if int(math.isqrt(x)) ** 2 == x:
        square_count += 1
        return square_count >= 10
    return False
count_up_until(tenth_square)
```

### 5.3 设计模式意义

这实际上是**策略模式（Strategy Pattern）**的体现：

```
┌──────────────────────┐
│  Context（上下文）    │
│  count_up_until      │ ← 算法框架（Loop）固定
│                      │
│  + strategy: Callable│ ← Goal 策略可替换
└──────────────────────┘
           │
           ▼
┌──────────────────────┐
│  Strategy（策略接口）  │
│  goal_condition(x)    │ ← bool 返回值
└──────────────────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
┌─────────┐ ┌─────────┐
│ 策略 A   │ │ 策略 B   │ ...
│ 找质数   │ │ 数到 100 │
└─────────┘ └─────────┘
```

### 5.4 三大好处

| 好处 | 说明 | 在项目中的体现 |
|------|------|--------------|
| **代码复用** | 同一个 Loop 函数可用于无数种任务 | `count_up_until` 服务 4 种不同 Goal |
| **关注点分离** | Loop 作者只管迭代，Goal 作者只管条件 | 可分工协作 |
| **可测试性** | Goal 函数是纯函数，可独立测试 | 见 `TestGoalFunctions` |

---

## 6. Goal 的五种表达方式

### 6.1 显式条件

```python
# Goal 直接在 if 语句中表达
if guess == secret:        # 🎯 最直接的 Goal 表达
    break
```

**适用**: 简单、明确的一次性条件  
**优点**: 直观，一眼能看懂  
**缺点**: 不可复用

### 6.2 函数参数（高阶函数）

```python
# Goal 作为函数参数传入
def count_up_until(goal_condition):
    while True:
        if goal_condition(current):  # 🎯 由调用者定义 Goal
            break
```

**适用**: 需要复用 Loop 逻辑的场景  
**优点**: 灵活、可测试、可复用  
**缺点**: 需要理解函数式编程概念

### 6.3 哨兵值（Sentinel）

```python
# 使用特殊值标记"结束"
SENTINEL = -1
while True:
    value = read_sensor()
    if value == SENTINEL:  # 🎯 哨兵值表示"没有更多数据"
        break
```

**适用**: 读取数据流、文件处理  
**优点**: 实现简单，不需要额外状态  
**缺点**: 需要确保哨兵值不会出现在正常数据中

### 6.4 异常（Exception）

```python
# 用异常机制表达 Goal 到达
class GoalReached(Exception):
    pass

def search():
    if found:
        raise GoalReached()  # 🎯 通过异常"跳出"多层循环
```

**适用**: 需要跳出多层嵌套循环  
**优点**: 可以跨越任意多层代码  
**缺点**: 异常不应用于正常流程控制（Python 社区惯例）

### 6.5 枚举结束（隐含 Goal）

```python
# for 循环的 Goal 隐含在"遍历完"中
for item in collection:     # 🎯 Goal = "没有更多元素"
    process(item)           # 当 StopIteration 被抛出时，循环自动结束
```

**适用**: 遍历已知集合  
**优点**: 安全、简洁、不会死循环  
**缺点**: 仅适用于可迭代对象

### 6.6 选型指南

```
Goal 复杂度                   推荐表达方式
──────────────────────────────────────────────
简单条件（==、>、<）           → 显式条件
需要复用 Loop 逻辑              → 函数参数
读取数据流                      → 哨兵值
跳出多层循环                    → 异常
遍历集合                        → 枚举结束（for）
```

---

## 附录：代码结构总览

### 文件模块图

```
loop_and_goal.py
│
├── 1. 核心思想（文档注释）
│
├── 2. Loop vs Goal 对比表（文档注释）
│
├── 3. 生活类比（文档注释）
│
├── 4. 代码演示
│   ├── guess_number_game()      — 例 1：猜数字
│   ├── auto_guess_number()      — 例 1b：自动猜数字
│   ├── sum_with_while()         — 例 2：while 求和
│   ├── sum_with_for()           — 例 2：for 求和
│   ├── sum_with_recursion()     — 例 2：递归求和
│   ├── sum_with_formula()       — 例 2：公式求和
│   ├── count_up_until()         — 例 3：通用 Loop
│   ├── is_prime()               — 例 3：质数判断（Goal A）
│   ├── search_with_safety()     — 例 4：安全搜索
│   └── find_pythagorean_triplet() — 例 5：勾股数
│
├── 5. 实现技术点（文档注释）
│
├── 6. 启发性问题（文档注释）
│
├── 7. 测试代码
│   ├── TestGoalFunctions        — 测试独立 Goal 函数
│   ├── TestSumFunctions         — 测试不同 Loop 的实现
│   ├── TestSafetyMechanism      — 测试安全机制
│   ├── TestAutoGuessNumber      — 测试猜数字
│   ├── TestPythagoreanTriplet   — 测试勾股数
│   └── TestLoopGoalRelationships — 综合测试
│
└── 主入口
    ├── __name__ == "__main__"
    └── run_all_tests()
```

### 函数依赖图

```
用户入口
    │
    ├── python loop_and_goal.py
    │   └── 模块级代码自动执行所有 print() 演示
    │
    └── python loop_and_goal.py test
        └── run_all_tests()
            ├── TestGoalFunctions
            │   └── 依赖: is_prime(), goal_*()
            ├── TestSumFunctions
            │   └── 依赖: sum_with_*()
            ├── TestSafetyMechanism
            │   └── 依赖: search_with_safety()
            ├── TestAutoGuessNumber
            │   └── 依赖: auto_guess_number()
            ├── TestPythagoreanTriplet
            │   └── 依赖: find_pythagorean_triplet()
            └── TestLoopGoalRelationships
                └── 依赖: count_up_until(), sum_with_formula()
```
