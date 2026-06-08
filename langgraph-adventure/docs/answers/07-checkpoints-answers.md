# 07 · 检查点与持久化 — 启发式问题答案

---

### Q1: 如果 `MemorySaver` 在程序重启后数据丢失，在什么场景下这反而是有利的？

**答案**：

**有利场景**：

1. **无状态微服务**：每次请求都应该是独立的，不希望残留状态影响下次
2. **敏感数据处理**：处理完即毁，不落盘，符合数据安全要求
3. **测试环境**：每次测试都从干净状态开始，避免状态污染
4. **原型开发**：快速迭代时不想被旧检查点的 bug 困扰
5. **临时会话**：如一次性咨询、匿名聊天

```python
# 匿名客服：每次对话从零开始
config = {"configurable": {"thread_id": str(uuid.uuid4())}}
# 关闭浏览器 = 对话消失，不留痕迹
```

还有一个额外好处：**性能**。MemorySaver 比磁盘 I/O 快几个数量级，适合对延迟敏感的场景。

---

### Q2: `thread_id` 冲突会怎样？如果两个用户意外使用了相同的 `thread_id`，会发生什么？

**答案**：

**结论：第二个用户会"继承"第一个用户的状态。**

```python
# 用户A 玩到一半
config_a = {"configurable": {"thread_id": "game-1"}}
state_a = app.invoke(start, config_a)  # HP=30, room=entrance
# ...战斗后 HP=10, room=goblin_den...

# 用户B 不小心用了相同 thread_id
config_b = {"configurable": {"thread_id": "game-1"}}  # 冲突！
state_b = app.invoke(Command(resume="北"), config_b)
# HP=10, room=dragon_lair  ← 继承了用户A的状态！
```

**防护措施**：
- 使用 UUID 作为 thread_id
- 在 thread_id 中编码用户标识：`f"user-{user_id}-{session_id}"`
- 服务端维护 thread_id → user 的映射表

---

### Q3: 检查点会保存**完整**的状态还是**增量**？如果 state 中有大对象，会有什么性能影响？

**答案**：

**当前行为**：LangGraph 保存**完整快照**（每个检查点包含完整 state）。

这意味着：
```python
state = {
    "messages": [...1000条消息...],      # 大列表
    "chat_history": "...长篇对话...",     # 大字符串
    "document": "...整个PDF内容...",      # 大文本
    "player_hp": 10,                      # 小整数
}
# 每个检查点都存完整副本！
```

**性能影响**：
- 检查点大小 = state 大小 × 步数（线性增长）
- 对于长对话 Agent（100+ 步），内存/磁盘可能很快耗尽
- 恢复较慢（需要反序列化整个 state）

**优化策略**：
- 用外部存储管理大对象（数据库/对象存储），state 只存引用
- 限制 messages 长度（只保留最近 N 条）
- 选择合适的 checkpointer（PostgreSQL 可处理大状态）
- 定期清理旧检查点（手动 or 自动化）

---

### Q4: 如果你想让用户"回到上一轮战斗前"，应该用什么 API？如何实现一个"撤销"功能？

**答案**：

```python
def undo_last_step(config):
    """回溯到上一个检查点"""
    # 1. 获取历史
    history = list(app.get_state_history(config))

    # 2. 跳过当前状态，取上一个
    if len(history) < 2:
        return None

    previous = history[1]  # history[0] 是当前状态
    previous_state = previous.values

    # 3. 用 update 恢复到上一个状态
    app.update_state(config, previous_state)

    return previous_state
```

实现"回到战斗前"功能：

```python
def go_back_before_combat(config):
    """回溯到最近的非战斗状态"""
    history = list(app.get_state_history(config))

    for snapshot in history:
        state = snapshot.values
        if not state.get("combat_active") and not state.get("game_over"):
            # 找到了战斗前的状态
            app.update_state(config, state)
            # 还需要跳转到对应的节点
            next_node = snapshot.next[0] if snapshot.next else "enter_room"
            return app.invoke(Command(goto=next_node), config)

    return None
```

**更优雅的做法**：在关键节点手动创建"标签"检查点：
```python
# 在 initiate_combat 前标记
app.update_state(config, values={"_checkpoint_label": "before_goblin_fight"})

# 撤销时找到这个标签
for snapshot in app.get_state_history(config):
    if snapshot.values.get("_checkpoint_label") == "before_goblin_fight":
        app.update_state(config, snapshot.values)
        break
```

---

### Q5: 在生产环境中，你会选择 `SqliteSaver` 还是 `PostgresSaver`？考虑并发、性能和运维。

**答案**：

| 维度 | SqliteSaver | PostgresSaver |
|------|------------|---------------|
| **并发** | 单写者（写锁） | 高并发读写 |
| **性能** | 小数据量极快 | 大数据量稳定 |
| **部署** | 零配置，文件级 | 需要数据库服务 |
| **运维** | 备份 = 复制文件 | 需要 DBA 或托管 |
| **扩展** | 单机 | 水平扩展 |
| **状态大小** | < 1GB 可接受 | 数十 GB 无压力 |

**选择建议**：

```python
# SqliteSaver：适合
- 单用户/低并发应用
- 桌面或边缘设备（离线可用）
- 原型和 MVP 阶段
- 测试环境

# PostgresSaver：适合
- 多用户 SaaS 服务
- 生产环境关键任务
- 需要高可用和灾难恢复
- 长对话 Agent（状态大）
```

**一个常见的演进路径**：
```
开发阶段：MemorySaver
  ↓
MVP/测试：SqliteSaver（本地持久化）
  ↓
生产环境：PostgresSaver（云托管 RDS/Aurora）
```

在生产中，建议使用**托管数据库**（AWS RDS、GCP Cloud SQL、Azure Database），把运维负担交给云服务商。
