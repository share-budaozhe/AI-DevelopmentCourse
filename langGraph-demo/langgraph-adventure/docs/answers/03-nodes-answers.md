# 03 · 节点与边 — 启发式问题答案

---

### Q1: 为什么节点不应该调用下一个节点？如果在 `enter_room` 里直接调用 `initiate_combat()`，会出现什么问题？

**答案**：

如果在节点内部直接调用另一个节点：

```python
# ❌ 坏做法
def enter_room(state: GameState) -> dict:
    # ... 展示房间 ...
    return initiate_combat(state)  # 直接调用下一个节点！
```

会导致以下问题：

1. **图结构失效**：编译时定义的边被绕过，图的可视化和追踪变得不准确
2. **检查点丢失**：只能记录 `enter_room` 的入口和出口，`initiate_combat` 的中间状态丢失
3. **不可测试**：无法单独测试 `initiate_combat`，它被耦合在 `enter_room` 里
4. **路由逻辑混乱**：条件边变成死代码
5. **interrupt() 不安全**：在嵌套调用中的 interrupt 行为不可预测

**正确做法**：让图通过边来决定下一步，节点只负责自己的计算。

---

### Q2: 条件路由函数必须是**纯函数**吗？如果 `route_from_room()` 内部修改了 state，会发生什么？

**答案**：

LangGraph 的**设计合约**要求路由函数是纯函数。如果路由函数修改了 state：

```python
# ❌ 路由函数偷偷改状态
def route_from_room(state: GameState) -> str:
    state["player_hp"] = 999  # 侧效应！
    return "enter_room"
```

后果：
- 路由函数中的修改**可能被忽略**（LangGraph 不保证写入）
- 修改**可能进入下一轮**（取决于实现细节），导致非确定性 bug
- 检查点记录的状态与预期不符
- 调试时很难追踪是谁改了 `player_hp`

---

### Q3: 你能想到哪些场景适合用固定边，哪些适合用条件边？

**固定边**适用于：
- 初始化后一定展示（`initiate_combat → enter_room`）
- 清理工作（`game_over → END`）
- 数据管道中的确定性步骤（`extract → transform → load`）

**条件边**适用于：
- 用户输入分发（`"北" → move / "攻击" → attack`）
- 权限检查（管理员 → 管理面板 / 普通用户 → 主页）
- 内容审核（通过 → 发布 / 不通过 → 打回）
- 异常处理（成功 → 继续 / 失败 → 重试或告警）

---

### Q4: 如果图中有 20 个节点和 50 条边，你会如何测试这张图的正确性？

**答案**：

分层测试策略：

1. **单元测试**：每个节点函数单独测试
```python
def test_enter_room():
    state = {"current_room": "entrance", ...}
    result = enter_room(state)
    assert "地牢入口" in result["messages"][0][1]
```

2. **路由测试**：每个路由函数单独测试
```python
def test_route_from_room_combat():
    state = {"current_room": "goblin_den", "combat_active": False, ...}
    assert route_from_room(state) == "initiate_combat"
```

3. **集成测试**：测试关键路径
```python
def test_full_combat_flow():
    app = build_adventure_graph()
    result = app.invoke(INITIAL_STATE, config)
    # 移动 → 进战斗 → 攻击 → 击杀 → 回到探索
    assert not result.get("combat_active")
```

4. **状态快照对比**：对已知输入，验证每个检查点的状态快照

5. **边界测试**：HP=0, HP=1, 空背包, 所有谜题已解等

---

### Q5: 假如你想加一个"中毒"机制（每走一步扣 1 HP），应该在哪里加？加节点还是改路由？

**答案**：

两种方案：

**方案 A：新增节点（推荐）**
```python
def poison_tick(state: GameState) -> dict:
    if "毒药" in state.get("inventory", []):  # 中毒标记
        hp = max(0, state.get("player_hp", 0) - 1)
        return {"player_hp": hp, "messages": [("ai", "🟢 毒素侵蚀……生命-1")]}
    return {}

# 在移动后插入
graph.add_edge("move_player", "poison_tick")
graph.add_conditional_edges("poison_tick", route_after_combat, {...})
```

优点：职责清晰，可独立测试，可选启用。

**方案 B：在路由中判断**
```python
def route_with_poison(state):
    if hp <= 0:
        return "game_over"
    return "enter_room"
```

但路由不修改 state，所以扣血逻辑还是要放节点里。所以**节点 + 路由配合**是最佳实践。
