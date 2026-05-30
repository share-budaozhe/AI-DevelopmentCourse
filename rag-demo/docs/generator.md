# Generator — 答案生成模块

## 文件位置

[src/generator.py](../src/generator.py)

## 在 RAG 中的角色

`Generator` 是 RAG 流水线的**终结点**，也是 RAG 中 "**G**"（Generation）的体现。它接收检索到的文档上下文，生成最终回答。本模块支持三种工作模式：

```
                      ┌──────────────┐
  检索结果 ─────────→ │  Generator   │ ─────────→ 最终回答
  用户查询 ─────────→ │              │
                      │  自动检测:    │
                      │  DEEPSEEK_API_KEY? → DeepSeek API
                      │  OPENAI_API_KEY?  → OpenAI API
                      │  都没有           → 本地模式
                      └──────────────┘
```

---

## 类结构

```
Generator
├── provider: dict | None    # 检测到的 LLM 后端配置（或 None = 本地模式）
├── mode_label: str          # 当前模式标签（如 "LLM (DeepSeek)"）
├── use_llm: bool            # 是否使用 LLM
│
├── _detect_provider() → dict | None   # 自动检测可用后端
├── generate(query, results, context) → str  # 主入口
├── _generate_llm(query, context) → str      # LLM 模式
└── _generate_local(query, results, context) → str  # 本地模式
```

---

## 后端自动检测机制（第 55-60 行）

```python
def _detect_provider(self) -> dict | None:
    for name in ["deepseek", "openai"]:
        cfg = PROVIDERS[name]
        if os.environ.get(cfg["env_key"]):
            return cfg
    return None
```

### 知识点：后端优先级与配置

```python
PROVIDERS = {
    "deepseek": {
        "env_key": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
        "label": "LLM (DeepSeek)",
    },
    "openai": {
        "env_key": "OPENAI_API_KEY",
        "base_url": None,          # None → 使用 OpenAI SDK 默认地址
        "model": "gpt-4o-mini",
        "label": "LLM (OpenAI)",
    },
}
```

**检测优先级**：DeepSeek > OpenAI > 本地

**为什么 DeepSeek 优先级更高？**
1. **成本**：DeepSeek API 价格远低于 OpenAI（约 1/10 ~ 1/20）
2. **中文能力**：DeepSeek 对中文的理解和生成质量通常优于 GPT-4o-mini
3. **可用性**：在国内无需代理即可访问

**检测逻辑**：遍历 provider 列表，检查对应的环境变量是否存在。这是一个**优雅的降级**（Graceful Degradation）策略——系统在任何配置下都能工作，只是质量不同。

```python
# 设置方式
# PowerShell:
$env:DEEPSEEK_API_KEY="sk-..."

# Bash:
export DEEPSEEK_API_KEY="sk-..."

# 或写入 .env 文件后通过 python-dotenv 加载
```

---

## LLM 模式：`_generate_llm()`（第 84-103 行）

```python
def _generate_llm(self, query: str, context: str) -> str:
    from openai import OpenAI

    cfg = self.provider
    kwargs = {"api_key": os.environ[cfg["env_key"]]}
    if cfg["base_url"]:
        kwargs["base_url"] = cfg["base_url"]

    client = OpenAI(**kwargs)
    user_content = USER_PROMPT_TMPL.format(context=context, query=query)

    response = client.chat.completions.create(
        model=cfg["model"],
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        max_tokens=2048,
    )
    return response.choices[0].message.content
```

### 知识点 1：OpenAI SDK 兼容协议

这是一个关键的工程实践——**OpenAI SDK 并非只能调用 OpenAI**。

```python
# 调用 OpenAI
client = OpenAI(api_key="sk-...")                    # base_url 默认为 api.openai.com

# 调用 DeepSeek（兼容 OpenAI 协议）
client = OpenAI(
    api_key="sk-...",
    base_url="https://api.deepseek.com"              # ← 只需改这一行！
)
```

DeepSeek、Mistral、Together AI、Ollama 等大量 LLM 服务都兼容 OpenAI 的 API 协议，所以用同一个 SDK 就能调用它们。这种设计被称为**协议标准化**，降低了切换 LLM 后端的成本。

### 知识点 2：Prompt 工程 —— System Prompt 设计

```python
SYSTEM_PROMPT = """你是一个知识助手，请严格基于提供的参考文档来回答问题。

要求：
1. 只能使用参考文档中的信息来回答，禁止编造文档中没有的内容。
2. 充分利用所有提供的参考文档，提取关键信息组织成完整、详实的回答。
3. 使用结构化格式：先给出总结段落，再分点展开细节，每点标注来源文档。
4. 如果参考文档不足以回答问题，明确说明"根据现有资料无法回答"。
5. 回答字数不少于150字，确保覆盖问题的各个维度。"""
```

**这个 System Prompt 的设计是 RAG 的精华所在**：

| 约束 | 目的 | 防止的问题 |
|---|---|---|
| **只用参考文档** | 将 LLM 的知识限定在知识库内 | 幻觉（编造事实） |
| **禁止编造** | 显式禁止 LLM 调用自身训练记忆 | LLM 用自己知识"补全"缺失信息 |
| **标注来源** | 要求注明引用出处 | 用户无法验证信息真实性 |
| **明确说"无法回答"** | 设定无结果的期望行为 | LLM 强行编造答案 |
| **不少于 150 字** | 保证回答的充分性 | LLM 偷懒只写一两句 |

### 知识点 3：Prompt 工程 —— User Prompt 模板

```python
USER_PROMPT_TMPL = """以下是参考文档：

{context}

问题：{query}

请按照要求给出详细回答。"""
```

`{context}` 由 `Retriever.format_context()` 填充，`{query}` 是用户原始问题。这种方式让系统能**动态注入**检索到的知识。

### 知识点 4：`max_tokens=2048`

限制 LLM 最大输出长度。防止模型"跑偏"后无限制输出、浪费 token 和响应时间。

---

## 本地模式：`_generate_local()`（第 105-129 行）

```python
def _generate_local(self, query, results, context):
    if not results:
        return "（未找到相关文档）"

    lines = [
        "=" * 60,
        f"📝 问题: {query}",
        "=" * 60,
        "",
        f"🔍 检索到 {len(results)} 个相关文档片段：",
        "",
    ]
    for i, r in enumerate(results, 1):
        lines.append(f"--- 片段 {i} (来源: {r.source}, 相关度: {r.score:.4f}) ---")
        lines.append(r.text)
        lines.append("")

    lines.extend([
        "-" * 60,
        "💡 提示: 设置 DEEPSEEK_API_KEY 或 OPENAI_API_KEY 可启用 LLM 智能回答。",
        '   $env:DEEPSEEK_API_KEY="sk-..." (PowerShell)',
    ])
    return "\n".join(lines)
```

**本地模式的本质**：不做任何生成，直接把检索结果原样展示给用户。这相当于一个**纯检索系统**（只有 R，没有 G）。

```
LLM 模式：      检索 → LLM 总结提炼   → 一段通顺的答案
本地模式：      检索 → 片段直接展示   → 原始文档片段列表
```

---

## 错误处理与降级（第 74-82 行）

```python
def generate(self, query, results, context):
    if self.provider:
        try:
            return self._generate_llm(query, context)
        except Exception as e:
            return (
                f"⚠ LLM 调用失败: {e}\n\n"
                f"{self._generate_local(query, results, context)}"
            )
    else:
        return self._generate_local(query, results, context)
```

**优雅降级（Graceful Degradation）**：

```
检测到 API Key？
  ├── 是 → 调用 LLM
  │        ├── 成功 → 返回 LLM 答案
  │        └── 失败 → 显示错误 + 降级到本地模式  ← 关键！
  └── 否 → 本地模式
```

即使 API 挂了（网络超时、欠费、密钥过期），系统仍然能返回检索结果给用户，而非直接崩溃——这就是**韧性（Resilience）**设计。

---

## RAG 全链路数据流

```
用户输入 "什么是监督学习？"
        │
        ▼
┌──────────────────┐
│   Retriever      │
│   .retrieve()    │
│                  │
│  embed_query()   │  查询 → TF-IDF 向量
│  store.search()  │  向量 → Top-5 相似文档
│  min_score 过滤  │  筛除不相关
│                  │
│  返回: List[SearchResult]  (5条结果)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Retriever      │
│ .format_context()│
│                  │
│  拼接为:          │
│  【文档1】...     │
│  【文档2】...     │
│  返回: str (上下文)│
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Generator      │
│   .generate()    │
│                  │
│  LLM 模式:        │
│  ┌─────────────┐ │
│  │ System:      │ │
│  │  只用文档回答  │ │
│  │ User:        │ │
│  │  上下文 + 问题 │ │
│  │ model:       │ │
│  │  GPT/DeepSeek│ │
│  └─────────────┘ │
│        │         │
│        ▼         │
│  结构化回答       │
│  (附来源标注)     │
│                  │
│  本地模式:        │
│  纯展示检索结果   │
└──────────────────┘
         │
         ▼
    控制台输出
```

---

## 知识扩展：RAG 的 Prompt 进阶技术

### 1. 引用溯源（Citation）

更强的 System Prompt 可以要求 LLM 用特定格式引用：

```
要求：在回答中每句话后面标注来源编号，如 [1]、[2]。
```

### 2. 思维链（Chain of Thought）

```
要求：先分析每篇参考文档与问题的相关性，再综合所有信息给出回答。
```

### 3. 自我反思（Self-Reflection）

```
要求：回答完后再检查一遍，回答是否严格基于参考文档，是否有编造的内容。
```

### 4. Few-shot 示例

在 System Prompt 中给出 1-2 个示例问答，让 LLM 更清晰理解期望的回答格式和质量。

### 5. RAG 幻觉的根源分析

即使加了"只用参考文档"的约束，LLM 仍可能产生幻觉：

| 原因 | 解释 |
|---|---|
| **上下文污染** | 检索回来的文档包含错误信息，LLM 照单全收 |
| **长上下文的注意力衰减** | 文档太多时 LLM 对中间部分"失焦" |
| **训练偏置** | LLM 训练时就学到的"常识"压倒检索结果 |
| **模棱两可的表述** | 文档表述模糊，LLM 自行"创造性解读" |

这也是为什么 RAG 系统的质量不仅取决于 LLM，更多取决于**检索质量**和**文档质量**。
