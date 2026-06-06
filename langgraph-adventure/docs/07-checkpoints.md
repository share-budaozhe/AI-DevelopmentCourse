# 07 · 检查点与持久化：图不会"失忆"

## 🧠 一句话总结

Checkpoint 是 LangGraph 的"存档系统"——每次图执行后自动保存状态快照，支持时光回溯和断点续传。

---

## 💾 在我们的 Demo 中

打开 `src/graph.py`，`build_adventure_graph()` 的最后：

```python
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
compiled = graph.compile(checkpointer=memory)
```

而在 `src/main.py` 中：

```python
thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": thread_id}}

# 每次 invoke 都用同一个 thread_id
current_state = app.invoke(INITIAL_STATE, config)
# ... 用户交互 ...
current_state = app.invoke(Command(resume=user_input), config)
```

---

## 🔑 检查点的核心概念

### 1. Thread ID —— 存档槽位

```python
config = {"configurable": {"thread_id": "game-slot-1"}}
```

每一个 `thread_id` 就是一个独立的"存档槽"。不同的 thread_id 之间状态完全隔离。

就像 RPG 游戏的多个存档位。

### 2. 自动保存

每次图执行（无论成功还是中断），LangGraph 自动保存状态快照。你不需要手动调用 `save()`。

### 3. 时光回溯

```python
# 回到上一个检查点
previous_state = app.get_state(config).values

# 查看所有历史状态
history = list(app.get_state_history(config))
for snapshot in history:
    print(snapshot.values["current_room"])
```

---

## 🎮 在我们的游戏中的应用

**存档功能**（目前未实现，但很容易加）：

```python
# 保存：只需记住 thread_id
save_slot = thread_id  # "abc123"

# 读取：用同一个 thread_id 继续
config = {"configurable": {"thread_id": save_slot}}
current_state = app.get_state(config).values
print(f"你上次在: {current_state['current_room']}")
```

**死亡后重试**：

```python
# 查看历史，找到死亡前的状态
history = list(app.get_state_history(config))
last_alive = None
for snapshot in history:
    if not snapshot.values.get("game_over"):
        last_alive = snapshot
        break

# 从那个状态恢复
if last_alive:
    app.invoke(Command(goto=last_alive.next[0]), config)  # 跳回
```

---

## 📊 不同的 Checkpointer 实现

| 实现 | 存储位置 | 适用场景 |
|------|---------|---------|
| `MemorySaver` | 内存 | 开发/测试（重启丢失） |
| `SqliteSaver` | SQLite 文件 | 本地持久化 |
| `PostgresSaver` | PostgreSQL | 生产环境 |

```python
# SQLite 持久化
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

conn = sqlite3.connect("adventure_saves.db", check_same_thread=False)
memory = SqliteSaver(conn)
compiled = graph.compile(checkpointer=memory)
```

---

## ⌛ 检查点的内部结构

每个检查点保存：

```
Checkpoint:
├── values: GameState          # 完整的当前状态
├── next: ("enter_room",)      # 下一步要执行的节点
├── metadata:
│   ├── source: "loop"         # 触发来源
│   ├── step: 12               # 执行步数
│   └── writes: {...}          # 本次写入
└── parent_checkpoint_id       # 父检查点（形成链）
```

---

## 🧠 高级话题：Channel 和 Pregel

LangGraph 的持久化底层基于 **Pregel** 模型（Google 的图计算框架）：

- 每个状态字段都是一个 **Channel**
- 每次节点写入，数据流入 Channel
- Reducer 决定多个写入如何合并
- Checkpoint 保存所有 Channel 的当前快照

这保证了并发场景下的一致性。

---

## 💭 启发式问题

1. 如果 `MemorySaver` 在程序重启后数据丢失，在什么场景下这反而是有利的？
2. `thread_id` 冲突会怎样？如果两个用户意外使用了相同的 `thread_id`，会发生什么？
3. 检查点会保存**完整**的状态还是**增量**？如果 state 中有大对象（如整个网页内容），会有什么性能影响？
4. 如果你想让用户"回到上一轮战斗前"，应该用什么 API？如何实现一个"撤销"功能？
5. 在生产环境中，你会选择 `SqliteSaver` 还是 `PostgresSaver`？考虑并发、性能和运维。

---

👉 返回：[01 · LangGraph 概览](./01-overview.md)

💭 答案：[07-检查点-答案](./answers/07-checkpoints-answers.md)
