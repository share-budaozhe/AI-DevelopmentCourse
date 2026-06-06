# 💬 LlamaIndex 学习 — 查询引擎全解析

## 什么是查询引擎？

QueryEngine 是 LlamaIndex 的「端到端问答接口」。
你只需要调用 `query("你的问题")`，它自动完成：
检索 → 合成 → 生成答案。

## 前置：配置 LLM

查询引擎需要 LLM。项目支持三种方案：

```python
from config import auto_setup

mode = auto_setup()  # 自动检测 .env 配置
# mode = "deepseek"  → 使用 DeepSeek LLM
# mode = "openai"    → 使用 OpenAI LLM
# mode = "mock"      → 仅演示结构（不调用 LLM）
```

**推荐 DeepSeek**：
```bash
# .env
DEEPSEEK_API_KEY=sk-your-key
USE_LOCAL_EMBEDDING=true  # 嵌入用本地模型，免费
```

## 基础用法

```python
from llama_index.core import VectorStoreIndex
from config import auto_setup

auto_setup()  # 自动配置 LLM + Embedding

index = VectorStoreIndex.from_documents(documents)

# 创建查询引擎
query_engine = index.as_query_engine()

# 查询
response = query_engine.query("什么是 LlamaIndex？")

# 结果
print(response.response)         # 文本答案
print(response.source_nodes)     # 参考来源
```

## 响应合成模式（Response Mode）

这是 QueryEngine 最重要的配置项，决定「检索到的内容如何组织并送给 LLM」。

### compact（默认、推荐）
将所有检索片段打包成一条消息，一次性发送。

```
检索结果 → [片段1] [片段2] [片段3] → 打包 → LLM → 答案
```

- ✅ 速度快，token 省（DeepSeek 只需一次调用）
- ✅ 适合 3-5 个片段
- ❌ 片段太多时可能超长

### refine
逐条处理，每次用新片段修正上一步的答案。

```
[片段1] → LLM → 初版答案
[片段2] + 初版答案 → LLM → 修正答案
[片段3] + 修正答案 → LLM → 最终答案
```

- ✅ 深度融合信息
- ❌ 多次 LLM 调用（DeepSeek 需要 N 次，成本 N 倍）

### tree_summarize
构建树，自底向上总结。

```
[片段1][片段2] → LLM → 摘要A
[片段3][片段4] → LLM → 摘要B
[摘要A][摘要B] → LLM → 最终答案
```

- ✅ 适合 10+ 个片段
- ❌ LLM 调用次数最多

## 自定义提示模板

```python
from llama_index.core import PromptTemplate

qa_template = PromptTemplate(
    "你是一个资深工程师。请用中文回答，要简洁专业。\n"
    "参考资料：\n"
    "{context_str}\n"
    "问题：{query_str}\n"
    "答案："
)

query_engine = index.as_query_engine(
    text_qa_template=qa_template,
)
```

## 检查信息来源

```python
response = query_engine.query("什么是 RAG？")

# 文本答案
print(response.response)

# 查看来源（RAG 可溯源的体现）
for node in response.source_nodes:
    print(f"来源: {node.metadata.get('file_name', '未知')}")
    print(f"相关度: {node.score:.3f}")
    print(f"内容: {node.text[:100]}...")
```

## 查询引擎配置清单

```python
query_engine = index.as_query_engine(
    similarity_top_k=5,            # 检索多少节点
    response_mode="compact",       # 合成模式
    text_qa_template=custom_tpl,   # 自定义提示
    node_postprocessors=[...],     # 后处理器
    streaming=False,               # 是否流式输出
)
```

## 💡 实战提示

- DeepSeek 使用 `deepseek-chat` 模型，128K 上下文窗口，单次查询成本极低
- 建议从 `compact` 模式开始，token 效率最高
- 如果答案不完整，尝试增加 `similarity_top_k` 或改用 `refine` 模式
- 始终检查 `response.source_nodes` 验证答案依据
