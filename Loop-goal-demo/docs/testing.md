# 测试说明

> **文档版本**: v1.0  
> **对应代码**: `loop_and_goal.py`  
> **测试框架**: Python `unittest`  
> **测试总数**: 20 个

---

## 目录

- [1. 测试策略](#1-测试策略)
- [2. 测试结构](#2-测试结构)
- [3. 测试用例详解](#3-测试用例详解)
- [4. 运行测试](#4-运行测试)
- [5. 测试结果解读](#5-测试结果解读)
- [6. 覆盖分析](#6-覆盖分析)
- [7. 扩展测试](#7-扩展测试)

---

## 1. 测试策略

本项目的测试遵循"**分层验证**"策略，从最底层的独立函数开始，逐层向上验证：

```
测试金字塔（Testing Pyramid）
        ┌──────────┐
        │ 综合测试  │ ← 验证跨组件协作（例：Loop + Goal 组合）
       ┌┴──────────┴┐
      ┌┴────────────┴┐
      │ 算法级测试    │ ← 验证完整功能（例：猜数字、勾股数）
     ┌┴──────────────┴┐
    ┌┴────────────────┴┐
    │ 模块级测试        │ ← 验证模块行为（例：安全机制）
   ┌┴──────────────────┴┐
  ┌┴────────────────────┴┐
  │ 单元测试              │ ← 验证独立函数（例：is_prime、求和函数）
  └──────────────────────┘
```

### 1.1 测试原则

| 原则 | 说明 | 在项目中的体现 |
|------|------|--------------|
| **独立性** | 每个测试不依赖其他测试 | 每个测试用例独立创建数据 |
| **确定性** | 固定随机种子确保可重复 | `auto_guess_number` 被多次调用验证 |
| **边界覆盖** | 测试正常值、边界值、异常值 | 每个函数都有边界测试 |
| **单一断言** | 每个测试方法只验证一件事 | 测试方法名精确描述验证内容 |
| **自文档化** | 测试名称说明测试意图 | 中文测试方法名 + docstring |

### 1.2 测试维度

每个测试类覆盖以下四个维度：

```
维度 1：功能正确性（Does it work?）
    → 正常输入下是否返回正确结果

维度 2：边界条件（Edge cases?）
    → 最小输入、最大输入、空输入

维度 3：失败处理（Does it fail properly?）
    → 不可达目标是否返回 False

维度 4：不变性约束（Invariants?）
    → 路径是否连续、结果是否满足数学性质
```

---

## 2. 测试结构

```
TestGoalFunctions                  ← 底层：独立 Goal 函数
├── test_is_prime                     验证质数判定
├── test_goal_first_prime_above_50    验证"大于50的质数"
├── test_goal_reach_100               验证"数到100"
└── test_goal_digit_sum_gt_20         验证"数字和>20"

TestSumFunctions                   ← 底层：不同 Loop 实现同一 Goal
├── test_all_methods_equal_5050       所有求和方法结果一致
├── test_sum_with_while_edge_cases    while 边界
├── test_sum_with_for_edge_cases      for 边界
├── test_sum_with_recursion_edge_cases  递归边界
└── test_sum_with_formula_edge_cases  公式边界

TestSafetyMechanism                ← 中层：安全机制
├── test_goal_reachable              Goal 可达
├── test_goal_unreachable            Goal 不可达
├── test_goal_reachable_but_limited  Goal 可达但步数不够
└── test_step_limit_exact            Goal 正好在步数限制处

TestAutoGuessNumber                ← 中层：完整算法
├── test_always_succeeds             二分法总能在 ≤7 步内猜中
└── test_secret_one                  秘密数字为 1 的特殊情况

TestPythagoreanTriplet             ← 中层：嵌套 Loop + 多层 Goal
├── test_finds_known_triplets        包含已知勾股数
├── test_no_false_positives          所有结果满足 a²+b²=c²
└── test_small_limit                 小范围的空结果

TestLoopGoalRelationships          ← 顶层：综合验证
├── test_loop_with_goal_normal       有 Loop 有 Goal → 正常工作
└── test_no_loop_with_goal           无 Loop 有 Goal → 一步到位
```

---

## 3. 测试用例详解

### 3.1 TestGoalFunctions（4 个测试）

验证独立 Goal 判断函数的正确性。这些函数是纯函数（同样的输入永远产生同样的输出），最容易测试。

#### `test_is_prime`

| 输入 | 期望 | 说明 |
|------|------|------|
| `is_prime(1)` | `False` | 1 不是质数 |
| `is_prime(2)` | `True` | 最小的质数 |
| `is_prime(3)` | `True` | 质数 |
| `is_prime(4)` | `False` | 合数（2×2） |
| `is_prime(53)` | `True` | 质数 |
| `is_prime(100)` | `False` | 合数 |

#### `test_goal_first_prime_above_50`

| 输入 | 期望 | 说明 |
|------|------|------|
| `goal_first_prime_above_50(51)` | `False` | 51 = 3×17，合数 |
| `goal_first_prime_above_50(53)` | `True` | 53 是质数 |

#### `test_goal_reach_100`

| 输入 | 期望 |
|------|------|
| `goal_reach_100(50)` | `False` |
| `goal_reach_100(99)` | `False` |
| `goal_reach_100(100)` | `True` |
| `goal_reach_100(101)` | `True` |

#### `test_goal_digit_sum_gt_20`

| 输入 | 各位和 | 期望 |
|------|--------|------|
| 99 | 18 | `False` |
| 199 | 19 | `False` |
| 299 | 20 | `False`（等于 20，不大于） |
| 399 | 21 | `True` |

### 3.2 TestSumFunctions（5 个测试）

验证"同一 Goal，四种不同 Loop"的实现是否都正确。

#### `test_all_methods_equal_5050`

```
输入: n = 100
期望: 所有方法都返回 5050
验证: sum_with_while(100) == 5050
      sum_with_for(100)   == 5050
      sum_with_recursion(100)  == 5050
      sum_with_formula(100)   == 5050
```

#### 边界测试

| 方法 | n=0 | n=1 | n=2 |
|------|-----|-----|-----|
| while | 0 | 1 | 3 |
| for | 0 | 1 | 3 |
| 递归 | — | 1 | 3 |
| 公式 | 0 | 1 | 3 |

> 注意：`sum_with_recursion(0)` 没有定义基线条件，所以边界测试跳过。这**本身就是一个设计选择**——递归函数选择 n=1 而不是 n=0 作为基线。

### 3.3 TestSafetyMechanism（4 个测试）

验证 `search_with_safety` 在三种场景下的行为，以及边界的精确性。

| 测试 | 输入 | 期望结果 | 期望值 | 期望步数 |
|------|------|---------|-------|---------|
| `test_goal_reachable` | `goal: x>=10, max=100` | `True` | 10 | 10 |
| `test_goal_unreachable` | `goal: x==-1, max=100` | `False` | 101 | 100 |
| `test_goal_reachable_but_limited` | `goal: x>=1000, max=50` | `False` | 51 | 50 |
| `test_step_limit_exact` | `goal: x>=100, max=100` | `True` | 100 | ≤100 |

### 3.4 TestAutoGuessNumber（2 个测试）

#### `test_always_succeeds`

- 随机种子变化 20 次
- 每次都验证：
  - 步数 > 0（确实进行了搜索）
  - 步数 ≤ 7（二分法在 1-100 范围内保证 ≤ log₂(100) ≈ 7）

```
验证依据：
  二分法时间复杂度为 O(log₂N)
  对于 N=100，log₂(100) ≈ 6.64，取整为 7
  所以任何情况下都不需要超过 7 次猜测
```

### 3.5 TestPythagoreanTriplet（3 个测试）

#### `test_finds_known_triplets`

验证输出包含以下已知勾股数：

```
(3, 4, 5)      → 3² + 4² = 9 + 16 = 25 = 5²
(5, 12, 13)    → 5² + 12² = 25 + 144 = 169 = 13²
(6, 8, 10)     → 6² + 8² = 36 + 64 = 100 = 10²
(8, 15, 17)    → 8² + 15² = 64 + 225 = 289 = 17²
(9, 12, 15)    → 9² + 12² = 81 + 144 = 225 = 15²
(12, 16, 20)   → 12² + 16² = 144 + 256 = 400 = 20²
```

#### `test_no_false_positives`

对 `max_n=30` 的所有结果，逐一验证：

```
assert a² + b² == c²      ← 勾股定理成立
assert a < b < c           ← 有序性保证（无重复排列）
```

#### `test_small_limit`

```
find_pythagorean_triplet(5) 应该包含至少 1 组
因为 (3, 4, 5) 中的 5 在 range(1, 6) 范围内
```

### 3.6 TestLoopGoalRelationships（2 个测试）

这是对本项目核心论点的最终验证。

#### `test_loop_with_goal_normal`

验证"有 Loop 有 Goal → 正常工作"：

```python
count_up_until(lambda x: x >= 10, start=1)
# Loop: while True 不断 +1
# Goal: x >= 10
# 结果: 10
```

#### `test_no_loop_with_goal`

验证"无 Loop 有 Goal → 一步到位"：

```python
sum_with_formula(100)
# Loop: 无（直接公式计算）
# Goal: 1+2+...+100 = 5050
# 结果: 5050
```

---

## 4. 运行测试

### 4.1 完整运行

```bash
cd /path/to/project

# 方式 1：通过脚本入口
python loop_and_goal.py test

# 方式 2：通过 unittest 命令行
python -m unittest loop_and_goal.TestGoalFunctions
python -m unittest loop_and_goal.TestSumFunctions
python -m unittest loop_and_goal.TestSafetyMechanism
# ...

# 方式 3：运行所有测试
python -m unittest discover -p "*.py"
```

### 4.2 运行单个测试类

```bash
# 只测试 Goal 函数
python -m unittest loop_and_goal.TestGoalFunctions

# 只测试安全机制
python -m unittest loop_and_goal.TestSafetyMechanism
```

### 4.3 运行单个测试方法

```bash
python -m unittest loop_and_goal.TestGoalFunctions.test_is_prime
```

### 4.4 测试参数

| 参数 | 说明 |
|------|------|
| `-v` 或 `--verbose` | 详细输出，显示每个测试的名称和结果 |
| `-q` 或 `--quiet` | 简洁输出，只显示汇总 |
| `-f` 或 `--failfast` | 遇到第一个失败就停止 |

```bash
python -m unittest loop_and_goal.TestGoalFunctions -v
```

### 4.5 预期输出

```
test_goal_digit_sum_gt_20 (loop_and_goal.TestGoalFunctions)
测试 Goal：各位数字之和大于 20 ... ok
test_goal_first_prime_above_50 (loop_and_goal.TestGoalFunctions)
测试 Goal：第一个大于 50 的质数 ... ok
test_goal_reach_100 (loop_and_goal.TestGoalFunctions)
测试 Goal：数到 100 ... ok
test_is_prime (loop_and_goal.TestGoalFunctions)
测试 is_prime 函数 ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.000s

OK
```

---

## 5. 测试结果解读

### 5.1 成功结果

```
Ran 20 tests in 0.001s

OK
```

| 指标 | 含义 |
|------|------|
| `Ran 20 tests` | 执行了 20 个测试方法 |
| `in 0.001s` | 总耗时不到 1 毫秒 |
| `OK` | 全部通过，0 失败 0 错误 |

### 5.2 失败结果

```
FAIL: test_all_methods_equal_5050 (loop_and_goal.TestSumFunctions)
所有方法都应该得到 5050
----------------------------------------------------------------------
Traceback (most recent call last):
  File "loop_and_goal.py", line XXX, in test_all_methods_equal_5050
    self.assertEqual(sum_with_while(100), 5050)
AssertionError: 4950 != 5050

----------------------------------------------------------------------
Ran 5 tests in 0.001s

FAILED (failures=1)
```

解读：
- **FAIL** = 断言失败（`assertEqual` 没通过）
- **Traceback** 显示具体位置和预期值
- `4950 != 5050` — 说明 `sum_with_while` 少加了 100（可能 `while i < n` 而不是 `while i <= n`）

### 5.3 常见失败原因

| 症状 | 可能的原因 |
|------|-----------|
| `AssertionError: False != True` | Goal 条件写反了 |
| `AssertionError: X != Y` | 算法逻辑错误 |
| `RecursionError: maximum recursion depth exceeded` | 递归基线条件不对 |
| `TypeError: ...` | 函数参数类型不对 |
| `AttributeError: ...` | 函数名拼写错误 |

---

## 6. 覆盖分析

### 6.1 函数覆盖

| 函数 | 被测试覆盖 | 测试位置 |
|------|-----------|---------|
| `is_prime` | ✅ | `TestGoalFunctions.test_is_prime` |
| `goal_first_prime_above_50` | ✅ | `TestGoalFunctions.test_goal_first_prime_above_50` |
| `goal_reach_100` | ✅ | `TestGoalFunctions.test_goal_reach_100` |
| `goal_digit_sum_gt_20` | ✅ | `TestGoalFunctions.test_goal_digit_sum_gt_20` |
| `sum_with_while` | ✅ | `TestSumFunctions` |
| `sum_with_for` | ✅ | `TestSumFunctions` |
| `sum_with_recursion` | ✅ | `TestSumFunctions` |
| `sum_with_formula` | ✅ | `TestSumFunctions` |
| `search_with_safety` | ✅ | `TestSafetyMechanism` |
| `auto_guess_number` | ✅ | `TestAutoGuessNumber` |
| `find_pythagorean_triplet` | ✅ | `TestPythagoreanTriplet` |
| `count_up_until` | ✅ | `TestLoopGoalRelationships` |

### 6.2 逻辑覆盖

| 逻辑分支 | 覆盖情况 |
|---------|---------|
| is_prime: n < 2 | ✅ (test_is_prime) |
| is_prime: 合数 | ✅ (test_is_prime) |
| is_prime: 质数 | ✅ (test_is_prime) |
| search_with_safety: Goal 可达 | ✅ (test_goal_reachable) |
| search_with_safety: Goal 不可达 | ✅ (test_goal_unreachable) |
| search_with_safety: 超步数限制 | ✅ (test_goal_reachable_but_limited) |
| find_pythagorean: 找到 | ✅ (test_finds_known_triplets) |
| find_pythagorean: 不满足 | ✅ (test_no_false_positives) |
| find_pythagorean: 空结果 | ✅ (test_small_limit) |
| auto_guess_number: 二分法 | ✅ (test_always_succeeds, 20 轮) |

---

## 7. 扩展测试

### 7.1 如何添加新测试

```python
import unittest
from loop_and_goal import count_up_until

class TestCustomGoal(unittest.TestCase):
    """测试自定义 Goal"""

    def test_find_first_palindrome_above_100(self):
        """验证：找到第一个大于 100 的回文数"""

        def is_palindrome(x: int) -> bool:
            s = str(x)
            return s == s[::-1]

        def goal(x: int) -> bool:
            return x > 100 and is_palindrome(x)

        result = count_up_until(goal, start=101)
        self.assertEqual(result, 101)  # 101 本身就是回文数

    def test_goal_never_reached_with_custom_limit(self):
        """验证：不可达目标加上自定义步数限制"""

        # 这里复用了 count_up_until，但它没有 step_limit
        # 所以我们需要对 while True 做特殊处理
        # 在实际工程中，应该给 count_up_until 也加上 step_limit 参数
        pass
```

### 7.2 建议增加的测试

| 测试 | 说明 | 优先级 |
|------|------|--------|
| `count_up_until` 添加 `max_steps` 参数 | 当前版本缺乏步数限制 | 🟡 中 |
| 测试 `guess_number_game`（用户输入版） | 当前只测试了自动版 | 🟢 低 |
| 大数值性能测试 | 测试 `sum_with_recursion(10000)` 是否会栈溢出 | 🟡 中 |
| 随机搜索统计测试 | 验证 Random Walk 的期望步数在合理范围 | 🟢 低 |

### 7.3 集成到 CI

```yaml
# .github/workflows/test.yml
name: Run Loop vs Goal Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.10"

    - name: Run tests
      run: |
        python loop_and_goal.py test
        python -m unittest discover -v
```
