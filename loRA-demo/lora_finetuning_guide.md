# LoRA 模型微调全流程指南

> 本教程涵盖 LoRA (Low-Rank Adaptation) 微调的理论基础、完整流程、代码实现、关键知识点、启发性问题以及测试部署方案。

---

## 目录

1. [LoRA 概述与原理](#1-lora-概述与原理)
2. [环境搭建与依赖](#2-环境搭建与依赖)
3. [数据准备](#3-数据准备)
4. [模型加载与 LoRA 配置](#4-模型加载与-lora-配置)
5. [训练流程](#5-训练流程)
6. [模型合并与保存](#6-模型合并与保存)
7. [推理与评估](#7-推理与评估)
8. [技术细节与关键知识点](#8-技术细节与关键知识点)
9. [启发性问题](#9-启发性问题)
10. [测试方案](#10-测试方案)
11. [部署方案](#11-部署方案)
12. [完整 Demo 代码](#12-完整-demo-代码)

---

## 1. LoRA 概述与原理

### 1.1 什么是 LoRA？

**LoRA（Low-Rank Adaptation）** 是 2021 年由微软研究者提出的一种高效微调方法（论文：*LoRA: Low-Rank Adaptation of Large Language Models*）。其核心思想是：**冻结预训练模型的全部权重，在原始模型旁插入少量可训练的低秩分解矩阵，仅更新这些参数来完成下游任务适配**。

### 1.2 核心数学原理

> **关键直觉**：预训练模型（如 GPT、LLaMA、BERT）学习到的权重矩阵通常具有很低的"固有秩"（intrinsic rank）—— 即权重变化可以被投影到低维子空间中表示。

对于预训练权重矩阵 $W_0 \in \mathbb{R}^{d \times k}$，微调时的权重更新量 $\Delta W$ 可以分解为两个低秩矩阵的乘积：

$$W = W_0 + \Delta W = W_0 + BA$$

其中：
- $B \in \mathbb{R}^{d \times r}$，$A \in \mathbb{R}^{r \times k}$
- **秩 $r \ll \min(d, k)$** （典型值：4、8、16、32）
- $W_0$ **冻结不更新**，仅训练 $B$ 和 $A$

**参数量节省**：
- 原始权重参数量：$d \times k$
- LoRA 参数量：$d \times r + r \times k = r(d + k)$
- **节省比例**：$1 - \frac{r(d+k)}{d \cdot k}$
- 例如 $d=4096, k=4096, r=8$：参数量从 16.7M 降至 65K，节省 **99.6%**

### 1.3 初始化与缩放

```
前向传播时：h = W₀x + (α / r) · BAx
```

- $A$ 初始化为高斯分布 $\mathcal{N}(0, \sigma^2)$
- $B$ 初始化为零矩阵，确保训练开始时 $\Delta W = 0$
- **缩放因子 $\alpha / r$**：$\alpha$ 是常数超参数，调整 $r$ 时无需大幅改变学习率

### 1.4 LoRA 的典型应用场景

| 场景 | 说明 |
|------|------|
| 指令微调 | 让基座模型遵循指令 |
| 领域适应 | 适配法律、医疗、金融等垂直领域 |
| 风格迁移 | 改变模型的输出风格 |
| 知识注入 | 让模型掌握私有/最新知识 |
| 多任务扩展 | 为每个任务保存独立的 LoRA 权重 |

---

## 2. 环境搭建与依赖

### 2.1 推荐环境

```bash
# Python 3.10+ 推荐
python >= 3.10
torch >= 2.0.0
transformers >= 4.30.0
peft >= 0.5.0        # HuggingFace PEFT 库（LoRA 核心）
datasets >= 2.10.0
accelerate >= 0.20.0
bitsandbytes >= 0.40.0  # 量化支持
trl >= 0.7.0          # RLHF/DPO 训练（可选）
wandb                 # 实验追踪（可选）
```

### 2.2 安装命令

```bash
# 基础环境
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install transformers datasets accelerate peft bitsandbytes

# 可选
pip install wandb tensorboard scikit-learn
pip install trl  # DPO/PPO 训练
```

### 2.3 硬件要求速查

| 模型规模 | 参数总量 | 全参微调显存 | LoRA 微调显存 | 最低 GPU |
|---------|---------|-------------|--------------|---------|
| LLaMA-7B | 7B | ~56 GB | ~16 GB | RTX 3090/4090 |
| LLaMA-13B | 13B | ~104 GB | ~24 GB | A10G/RTX 6000 |
| LLaMA-70B | 70B | ~560 GB | ~80 GB | 2×A100 |
| Qwen2.5-7B | 7B | ~56 GB | ~14 GB (4bit) | RTX 3090 |

---

## 3. 数据准备

### 3.1 数据格式

LoRA 微调常见的数据格式取决于训练方式：

#### SFT（监督微调）格式

```json
[
  {
    "instruction": "请解释什么是机器学习",
    "input": "",
    "output": "机器学习是人工智能的一个分支，它使计算机能够从数据中学习和改进，而无需进行明确的编程。其核心是通过算法分析数据模式，构建预测模型...",
    "history": []
  },
  {
    "instruction": "翻译以下句子成英文",
    "input": "今天天气真好",
    "output": "The weather is great today.",
    "history": []
  }
]
```

#### 对话格式（ShareGPT / ChatML）

```json
{
  "messages": [
    {"role": "system", "content": "你是一个有用的助手。"},
    {"role": "user", "content": "请解释相对论"},
    {"role": "assistant", "content": "相对论是爱因斯坦提出的物理学理论..."}
  ]
}
```

### 3.2 数据预处理流程

```
原始数据 → 清洗去重 → 格式化 → Tokenization → 打包/切割 → Dataset
```

**关键注意点**：
- **序列长度对齐**：根据模型最大长度（如 2048/4096）截断或打包
- **loss 掩码**：attention mask 仅对输出部分计算 loss，输入部分 mask 掉
- **数据混合**：通用数据与领域数据按比例混合以防止灾难性遗忘
- **质量 > 数量**：500 条高质量数据往往优于 50000 条噪声数据

### 3.3 数据预处理代码

```python
def preprocess_function(examples, tokenizer, max_length=2048):
    """将原始数据转换为模型输入格式"""
    prompts = []
    for instruction, inp, output in zip(
        examples["instruction"], examples["input"], examples["output"]
    ):
        if inp:
            prompt = f"指令: {instruction}\n输入: {inp}\n输出: "
        else:
            prompt = f"指令: {instruction}\n输出: "
        prompts.append(prompt)

    # Tokenize with labels
    model_inputs = tokenizer(
        prompts,
        max_length=max_length,
        truncation=True,
        padding=False,
    )

    labels = tokenizer(
        [p + o for p, o in zip(prompts, examples["output"])],
        max_length=max_length,
        truncation=True,
        padding=False,
    )

    model_inputs["labels"] = labels["input_ids"]
    return model_inputs
```

---

## 4. 模型加载与 LoRA 配置

### 4.1 加载基础模型

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "Qwen/Qwen2.5-7B-Instruct"

# 使用 4bit 量化加载（节省显存）
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    load_in_4bit=True,                # 4bit 量化
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,   # 双重量化进一步节省
)

tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token  # 设置 padding token
```

### 4.2 LoRA 配置详解

```python
from peft import LoraConfig, get_peft_model

lora_config = LoraConfig(
    # === 核心参数 ===
    r=8,                          # LoRA 秩（越小参数越少，但表达能力下降）
    lora_alpha=16,                # 缩放因子：ΔW = (alpha/r) * BA
    target_modules=[              # 应用 LoRA 的模块
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    lora_dropout=0.05,            # Dropout 防止过拟合
    bias="none",                  # 偏置处理方式

    # === 高级参数 ===
    task_type="CAUSAL_LM",        # 任务类型
    modules_to_save=None,         # 额外需要全量微调的模块
    init_lora_weights="pissa",    # 初始化策略（"default" | "gaussian" | "pissa" | "loftq"）
    use_rslora=True,              # 使用 Rank-Stabilized LoRA
    use_dora=False,               # 使用 DoRA（Weight-Decomposed LoRA）
)

# 应用 LoRA
model = get_peft_model(model, lora_config)

# 查看可训练参数
model.print_trainable_parameters()
# 输出示例: trainable params: 8.3M || all params: 6.7B || trainable%: 0.12
```

### 4.3 LoRA 参数选择指南

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| `r` | 8-16 | 通用任务 8，复杂任务 16，简单分类 4 |
| `lora_alpha` | 16-32 | 通常设为 r 的 2 倍，或从 16 开始调 |
| `target_modules` | 全连接层 | 对 LLM 通常所有线性层都加效果最好 |
| `lora_dropout` | 0.0-0.1 | 数据少时设 0.1，数据多时 0.0 |
| `bias` | "none" | "lora_only" 或 "all" 会大幅增加参数量 |

---

## 5. 训练流程

### 5.1 训练参数配置

```python
from transformers import TrainingArguments

training_args = TrainingArguments(
    # === 输出与日志 ===
    output_dir="./lora_output",
    logging_dir="./logs",
    logging_steps=10,
    report_to="tensorboard",       # 实验追踪

    # === 训练核心 ===
    num_train_epochs=3,            # 训练轮数
    per_device_train_batch_size=4, # 单卡 batch size
    gradient_accumulation_steps=8, # 梯度累积 = 有效 batch size=32
    learning_rate=2e-4,            # LoRA 常用 LR（比全量微调大 10-100 倍）
    warmup_ratio=0.03,             # 学习率预热
    lr_scheduler_type="cosine",    # 学习率调度

    # === 精度与优化 ===
    bf16=True,                     # bfloat16 混合精度
    optim="paged_adamw_8bit",      # 8bit 优化器省显存
    gradient_checkpointing=True,   # 梯度检查点（省显存换速度）

    # === 正则与避免过拟合 ===
    weight_decay=0.01,
    max_grad_norm=1.0,             # 梯度裁剪

    # === 保存策略 ===
    save_strategy="steps",
    save_steps=500,
    save_total_limit=3,            # 最多保留 3 个 checkpoint
    load_best_model_at_end=True,
    metric_for_best_model="loss",

    # === 分布式 ===
    ddp_find_unused_parameters=False,
    remove_unused_columns=False,
)
```

### 5.2 初始化 Trainer

```python
from transformers import Trainer
from datasets import load_dataset

dataset = load_dataset("json", data_files="data/train.json")
dataset = dataset.map(
    lambda x: preprocess_function(x, tokenizer),
    batched=True,
    remove_columns=dataset["train"].column_names,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset["train"],
    eval_dataset=dataset.get("validation"),
    tokenizer=tokenizer,
    data_collator=lambda data: {
        "input_ids": torch.stack([d["input_ids"] for d in data]),
        "attention_mask": torch.stack([d["attention_mask"] for d in data]),
        "labels": torch.stack([d["labels"] for d in data]),
    },
)

# 开始训练
trainer.train()
```

### 5.3 损失曲线解读

训练过程中应关注的信号：

```
Loss 曲线形态         →  含义
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
持续下降，最终收敛    →  正常训练
快速下降到接近 0      →  过拟合 / 数据泄露
震荡不收敛            →  学习率过大 / 数据有问题
loss 不降             →  学习率过小 / 模型未正确加载
验证 loss 上升        →  过拟合（需增加正则化/减少epoch）
验证 loss 先降后升    →  过拟合，应早停
```

---

## 6. 模型合并与保存

### 6.1 保存 LoRA 权重（适配器）

```python
# 仅保存 LoRA 权重（推荐，文件小）
model.save_pretrained("./lora_adapter")
tokenizer.save_pretrained("./lora_adapter")
# 生成文件：adapter_config.json + adapter_model.bin (~15MB)
```

### 6.2 合并权重到基础模型

```python
from peft import PeftModel

# 加载基础模型
base_model = AutoModelForCausalLM.from_pretrained(
    model_name, torch_dtype=torch.bfloat16, device_map="auto"
)

# 加载 LoRA 权重
lora_model = PeftModel.from_pretrained(base_model, "./lora_adapter")

# 合并权重
merged_model = lora_model.merge_and_unload()

# 保存完整模型
merged_model.save_pretrained("./merged_model")
tokenizer.save_pretrained("./merged_model")
```

### 6.3 合并原理

```
merge_and_unload 的实际操作：

W_new = W_0 + (alpha / r) * B @ A

其中 B @ A 是矩阵乘法，恢复为原始维度
合并后模型结构与原始模型完全一致，推理无额外开销
```

---

## 7. 推理与评估

### 7.1 使用 LoRA 适配器推理

```python
from peft import PeftModel

# 方式一：加载基础模型 + LoRA 适配器
base = AutoModelForCausalLM.from_pretrained(
    model_name, torch_dtype=torch.bfloat16, device_map="auto"
)
model = PeftModel.from_pretrained(base, "./lora_adapter")

# 推理
inputs = tokenizer("指令: 解释什么是注意力机制\n输出:", return_tensors="pt")
outputs = model.generate(
    **inputs,
    max_new_tokens=512,
    do_sample=True,
    temperature=0.7,
    top_p=0.9,
)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

### 7.2 使用合并后模型推理

```python
# 方式二：使用合并后模型（推理速度更快）
model = AutoModelForCausalLM.from_pretrained(
    "./merged_model", torch_dtype=torch.bfloat16, device_map="auto"
)
# 推理代码同上，与原始模型使用方式完全一致
```

### 7.3 评估指标

```python
from nltk.translate.bleu_score import sentence_bleu
from rouge_score import rouge_scorer

def evaluate_model(model, tokenizer, test_data):
    """评估微调后模型的质量"""

    # 1. ROUGE-L（摘要/生成类任务）
    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    rouge_scores = {"rouge1": 0, "rouge2": 0, "rougeL": 0}

    # 2. Perplexity（模型困惑度）
    total_loss = 0
    num_batches = 0

    for example in test_data:
        # 生成结果
        prompt = f"指令: {example['instruction']}\n输出:"
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        outputs = model.generate(**inputs, max_new_tokens=512)
        generated = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # 计算 ROUGE
        scores = scorer.score(example["output"], generated)
        for k in rouge_scores:
            rouge_scores[k] += scores[k].fmeasure

    for k in rouge_scores:
        rouge_scores[k] /= len(test_data)

    return rouge_scores

# 重要提醒：自动评估指标与人类判断存在差距，
# 建议结合人工抽查和 A/B 测试
```

---

## 8. 技术细节与关键知识点

### 8.1 LoRA 的设计哲学

```
为什么 LoRA 能工作？
─────────────────────────────────────────────

1. 低秩性假设（核心理论依据）
   预训练模型学到的特征空间维度非常高，但针对特定下游任务
   所需的"适应方向"实际上分布在低维子空间中。
   论文实验证明：即使 r=1 也能取得不错的效果。
   
2. 避免灾难性遗忘
   冻结原始权重确保预训练知识不被破坏，
   仅学习任务特定的"增量"。

3. 参数效率
   微调参数量通常只有原始模型的 0.01%-1%。
   可以将多个 LoRA 适配器动态切换，实现多任务复用同一基础模型。
```

### 8.2 LoRA 变体一览

| 变体 | 年份 | 改进点 | 适用场景 |
|------|------|--------|---------|
| **LoRA** | 2021 | 标准低秩分解 | 通用 |
| **AdaLoRA** | 2023 | 自适应分配秩（SVD 分解） | 需要自动调参 |
| **DoRA** | 2024 | 权重分解：magnitude + direction | 需要更强适应能力 |
| **LoRA+** | 2024 | A/B 矩阵不同学习率 | 加速收敛 |
| **PiSSA** | 2024 | 基于 SVD 的主成分初始化 | 更快收敛，更好效果 |
| **VeRA** | 2023 | 共享参数 + 可学习缩放 | 极致参数节省 |
| **Delta-LoRA** | 2024 | 参数增量放缩 | 提升微调稳定性 |

### 8.3 常见陷阱与解决方案

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| **训练 loss 不降** | LR 过小或模型冻结错误 | 检查 `requires_grad`，增大 LR |
| **生成重复内容** | LoRA 学习率太大导致过拟合 | 降低 r/lora_alpha，增加 dropout |
| **灾难性遗忘** | 微调数据太单一 | 加入 10-30% 通用数据混合训练 |
| **量化 + LoRA 兼容** | bnb 4bit + LoRA 训练 | 使用 `bnb_4bit_compute_dtype=bf16` |
| **OOM 错误** | 显存不足 | 减小 batch size / 开启 gradient checkpoint |
| **适配器不生效** | target_modules 写错 | 用 `model.print_model()` 确认模块名 |
| **merge 后效果下降** | 精度损失 | merge 时使用与训练一致的 dtype |

### 8.4 学习率策略详解

```
LoRA 的学习率通常比全量微调大 10~100 倍 ！

原因分析：
- 全量微调：更新 ~7B 参数，LR 通常 1e-5 ~ 5e-5
- LoRA 微调：仅更新 ~8M 参数（0.1%），LR 通常 1e-4 ~ 5e-4
- 因为更新的参数量少，每个参数需要"走更大的步"来达到相同的效果

学习率调度：
         Λ
  lr     |   /‾‾‾‾‾‾‾‾‾‾‾‾‾\    cosine 衰减
         |  /               \
         | /                 \________
         |/
         └───────────────────────────> step
            ^预热期^
```

### 8.5 梯度检查点（Gradient Checkpointing）

```
原理：在前向传播时丢弃中间激活值，反向传播时重新计算
效果：节省显存约 30-50%，但训练速度降低约 20%

适用场景：
- 大模型（7B+）单卡训练时必须开启
- 小模型（<1B）可以不开启
```

---

## 9. 启发性问题

> 这些问题旨在加深对 LoRA 及微调本质的理解，适合用于面试、讨论或自测。

### 🔥 基础理解

**Q1**: 为什么 LoRA 要固定原始权重而只更新低秩矩阵？为什么不直接微调全部参数？

<details>
<summary>思考引导</summary>
考虑以下几点：(1) 计算资源限制，(2) 模型泛化能力，(3) 灾难性遗忘，(4) 多任务部署。全量微调相当于让模型"重新学习"一个任务，风险在于破坏预训练学到的通用特征。
</details>

**Q2**: LoRA 的秩 r 值越大越好吗？r=64 一定比 r=8 效果好吗？

<details>
<summary>思考引导</summary>
不一定。r 越大参数量越多，但也可能引入噪声或导致过拟合。论文实验表明 r=1 在某些任务上与 r=64 性能相当。关键在于：预训练模型的权重变化确实具有很低的"固有秩"。
</details>

**Q3**: 为什么 LoRA 的初始化方案是 B=0, A ~ N(0, σ²)？如果改成 A=0, B~N 会怎样？

<details>
<summary>思考引导</summary>
如果 B~N, A=0，则前向传播时 BAx = 0，等价。但反向传播时梯度会如何传播？梯度通过 A 回传到 B，若 A=0 则梯度始终为 0，B 永远无法更新。所以必须把非零初始化放在靠近输入的一侧。
</details>

### 🚀 进阶理解

**Q4**: 假设你对一个 7B 模型做了 LoRA 微调（r=8），然后想部署到 8 个不同客户场景。对比全量微调和 LoRA 所需的存储空间。

<details>
<summary>思考引导</summary>
全量微调：8 × 7B = 56B 参数存储；LoRA：8 × ~15MB + 1 × 7B = ~7.05B。LoRA 同时加载多个适配器的显存开销只增加约 2-3%。
</details>

**Q5**: QLoRA 中的 4-bit NormalFloat (NF4) 量化为什么优于普通的 4-bit 整数量化？

<details>
<summary>思考引导</summary>
NF4 假设权重服从正态分布，利用分位数将量化级别"均匀"分配在概率密度高的区域，使得量化误差的期望值最小化。简单说：更重要的数值区域获得更高的精度。
</details>

**Q6**: LoRA 的缩放因子 α 和秩 r 之间有何关系？为什么调整 r 时需要相应调整 α？

<details>
<summary>思考引导</summary>
更新量 ΔW = (α/r)BA。当 r 增大时，BA 的表达能力增强但输出幅度也增大。α/r 起到归一化作用，使得不同 r 配置下 ΔW 的初始量级大致一致，避免每次调 r 都需要重调学习率。
</details>

### 💡 深度思考

**Q7**: 如果让 LoRA 的 A 和 B 矩阵也参与 SVD 分解，理论上会怎样？这是一个悖论吗？

<details>
<summary>思考引导</summary>
这就是"低秩分解的低秩分解"，假如 B 和 A 本身也做低秩分解，那么外层 LoRA 的秩实际上被内层限制了。这引出了"多重低秩堆叠"的问题——多个低秩变换的复合仍然是低秩变换。
</details>

**Q8**: DoRA（Weight-Decomposed LoRA）将权重分解为 magnitude 和 direction。这借鉴了哪个经典优化算法的思想？为什么分解后 LoRA 只需要学 direction？

<details>
<summary>思考引导</summary>
这与 LayerNorm 和 WeightNorm 的思想一脉相承。magnitude 控制"有多关注"，direction 控制"关注什么"。实验中 magnitude 的变化模式在不同任务间高度相似，可能是一个通用的"注意力调节"信号。
</details>

**Q9**: 在边缘设备（手机、IoT）上部署 LoRA 模型时，你会如何设计推理引擎以最小化额外的计算开销？

<details>
<summary>思考引导</summary>
核心思路：(1) merge 权重一次性推理，(2) 或者利用 BA 的低秩结构优化矩阵乘法（先算 A@x 再 B@(A@x)），(3) 考虑 LoRA 适配器的知识蒸馏到小模型，(4) 利用硬件特性（如 mobile NPU）加速低秩计算。
</details>

**Q10**: 当使用多个 LoRA 适配器进行组合时（如 Multi-LoRA），不同适配器之间的"干扰"可能来自哪里？如何缓解？

<details>
<summary>思考引导</summary>
干扰源：(1) 适配器间的梯度冲突（任务 A 和 B 需要不同的权重更新方向），(2) 激活值分布偏移，(3) 注意力头竞争。缓解方法：路由机制、正交约束、任务特定的 prompt prefix。
</details>

### 🧪 实践问题

**Q11**: 你在微调后发现模型在训练数据上 loss 很低，但在测试集上生成结果全是重复的。可能的原因是什么？

<details>
<summary>思考引导</summary>
典型的过拟合。检查：(1) 训练数据量是否太少，(2) r 是否过大，(3) lora_dropout 是否设为 0，(4) epoch 是否太多。过拟合的 LoRA 相当于记住了特定模式但丧失了泛化能力。
</details>

**Q12**: 如果 LoRA 训练时 loss 不断震荡且不收敛，你会怎么排查？

<details>
<summary>思考引导</summary>
系统性排查：(1) 确认模型不是全冻结的（检查 requires_grad），(2) 学习率从 1e-4 下调到 1e-5 试试，(3) 检查数据中是否存在冲突的 label（相同输入不同输出），(4) 减少 batch size 看是否有改善，(5) 用随机数据跑一遍排查代码 bug。
</details>

---

## 10. 测试方案

### 10.1 单元测试

```python
"""tests/test_lora.py"""
import unittest
import torch
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM

class TestLoRAConfig(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.model = AutoModelForCausalLM.from_pretrained(
            "Qwen/Qwen2.5-0.5B-Instruct",
            torch_dtype=torch.float32,
            device_map="cpu",
        )

    def test_lora_param_count(self):
        """验证 LoRA 参数量计算正确"""
        config = LoraConfig(r=8, lora_alpha=16, target_modules=["q_proj", "v_proj"])
        lora_model = get_peft_model(self.model, config)
        trainable = lora_model.get_nb_trainable_parameters()
        # 检查可训练参数比例 < 1%
        self.assertLess(trainable[0] / trainable[1], 0.01)

    def test_lora_output_shape(self):
        """验证 LoRA 输出 shape 与原始模型一致"""
        config = LoraConfig(r=8, target_modules=["q_proj", "v_proj"])
        lora_model = get_peft_model(self.model, config)
        inputs = torch.randint(0, 1000, (1, 128))
        with torch.no_grad():
            output = lora_model(input_ids=inputs)
        # logits shape: [batch, seq_len, vocab_size]
        self.assertEqual(output.logits.shape, (1, 128, lora_model.config.vocab_size))

    def test_merge_unload(self):
        """验证合并后模型输出与原模型一致"""
        config = LoraConfig(r=4, target_modules=["q_proj"])
        lora_model = get_peft_model(self.model, config)

        # 合并前
        inputs = torch.randint(0, 1000, (1, 64))
        with torch.no_grad():
            out_before = lora_model(input_ids=inputs).logits

        # 合并后
        merged = lora_model.merge_and_unload()
        with torch.no_grad():
            out_after = merged(input_ids=inputs).logits

        self.assertTrue(torch.allclose(out_before, out_after, atol=1e-4))

    def test_multiple_adapters(self):
        """验证多适配器切换功能"""
        config1 = LoraConfig(r=8, target_modules=["q_proj"])
        config2 = LoraConfig(r=16, target_modules=["q_proj", "v_proj"])

        model = get_peft_model(self.model, config1, adapter_name="adapter_a")
        model.add_adapter("adapter_b", config2)

        # 切换适配器
        model.set_adapter("adapter_a")
        params_a = sum(p.sum() for p in model.parameters() if p.requires_grad)
        model.set_adapter("adapter_b")
        params_b = sum(p.sum() for p in model.parameters() if p.requires_grad)

        # 不同适配器的参数量不同
        self.assertNotEqual(params_a.item(), params_b.item())


if __name__ == "__main__":
    unittest.main()
```

### 10.2 集成测试

```python
"""tests/test_integration.py"""
import subprocess
import tempfile
import os
import json


class TestLoRATraining:
    """端到端训练测试"""

    def test_training_completes(self):
        """验证训练流程完整运行"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试数据
            train_data = [
                {"instruction": "你好", "output": "你好！有什么可以帮助你的吗？"},
                {"instruction": "1+1等于几", "output": "1+1=2"},
            ]
            os.makedirs(f"{tmpdir}/data", exist_ok=True)
            with open(f"{tmpdir}/data/train.json", "w") as f:
                for item in train_data:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")

            # 运行训练脚本
            result = subprocess.run(
                [
                    "python", "lora_demo.py",
                    "--model_name", "Qwen/Qwen2.5-0.5B-Instruct",
                    "--data_path", f"{tmpdir}/data/train.json",
                    "--output_dir", f"{tmpdir}/output",
                    "--num_epochs", "1",
                    "--max_steps", "10",
                ],
                capture_output=True, text=True,
            )

            assert result.returncode == 0, f"Training failed: {result.stderr}"
            assert os.path.exists(f"{tmpdir}/output/final_model")
```

### 10.3 性能基准测试

```python
"""Benchmark LoRA vs Full Fine-tuning"""

import time
import torch
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM


def benchmark_memory_and_speed(model_name, use_lora=True, r=8):
    """对比 LoRA 与全量微调的内存和速度"""

    model = AutoModelForCausalLM.from_pretrained(
        model_name, torch_dtype=torch.bfloat16, device_map="auto"
    )

    if use_lora:
        config = LoraConfig(r=r, target_modules=["q_proj", "v_proj", "k_proj", "o_proj"])
        model = get_peft_model(model, config)
        model.print_trainable_parameters()

    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-4 if use_lora else 2e-5)

    # 测量显存
    memory_before = torch.cuda.memory_allocated()

    inputs = torch.randint(0, 1000, (1, 512)).to(model.device)

    # 测量速度
    start = time.time()
    for _ in range(10):
        outputs = model(input_ids=inputs, labels=inputs)
        outputs.loss.backward()
        optimizer.step()
        optimizer.zero_grad()
    elapsed = time.time() - start

    memory_after = torch.cuda.max_memory_allocated()
    memory_used = (memory_after - memory_before) / 1024**3

    return {
        "method": "LoRA" if use_lora else "Full FT",
        "time_per_step": f"{(elapsed/10)*1000:.1f} ms",
        "peak_memory": f"{memory_used:.2f} GB",
    }
```

### 10.4 模型评估清单

| 测试项 | 方法 | 通过标准 |
|--------|------|---------|
| **功能正确性** | 输入测试 prompt，检查输出格式 | 输出符合预期格式 |
| **语义质量** | 人工评分（1-5） | 平均 ≥ 3.5 |
| **幻觉率** | 检查生成内容的事实正确性 | 幻觉率 < 5% |
| **鲁棒性** | 输入有噪声/对抗性 prompt | 不崩溃，不输出有害内容 |
| **延迟** | 测量 p50/p95/p99 推理时间 | 满足业务 SLA |
| **吞吐量** | 每秒处理请求数 (QPS) | 满足业务需求 |
| **内存泄漏** | 长时间运行监控显存 | 显存稳定不增长 |
| **AB 对比** | 新旧模型盲测对比 | 新模型胜出率 > 50% |

---

## 11. 部署方案

### 11.1 方案一：vLLM 部署（推荐生产环境）

```python
# vllm_deploy.py
from vllm import LLM, SamplingParams
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

# vLLM 原生支持 LoRA（v0.4.0+）

def deploy_with_vllm():
    """使用 vLLM 部署 LoRA 模型，支持动态适配器切换"""

    llm = LLM(
        model="Qwen/Qwen2.5-7B-Instruct",
        enable_lora=True,                     # 启用 LoRA 支持
        max_loras=8,                          # 最大同时加载适配器数
        max_lora_rank=64,                     # 最大 LoRA 秩
        tensor_parallel_size=1,               # 张量并行数
        gpu_memory_utilization=0.9,           # GPU 显存利用率
        trust_remote_code=True,
    )

    # 动态加载多个 LoRA 适配器
    sampling_params = SamplingParams(
        temperature=0.7,
        top_p=0.9,
        max_tokens=1024,
    )

    # 不同请求可以使用不同适配器
    prompts = [
        ("<用户>请解释量子计算</用户>", "adapter_a"),  # 使用 adapter_a
        ("<用户>写一首诗</用户>", "adapter_b"),        # 使用 adapter_b
    ]

    outputs = llm.generate(
        [p[0] for p in prompts],
        sampling_params,
        lora_request=[p[1] for p in prompts],  # 指定每个 prompt 的适配器
    )

    for output in outputs:
        print(output.outputs[0].text)


def deploy_with_fastapi():
    """FastAPI 封装 LoRA 推理服务"""
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    import uvicorn

    app = FastAPI(title="LoRA Model Serving")

    class GenerationRequest(BaseModel):
        prompt: str
        max_tokens: int = 512
        temperature: float = 0.7
        lora_adapter: str = "default"

    class GenerationResponse(BaseModel):
        text: str
        usage: dict

    llm = LLM(
        model="Qwen/Qwen2.5-7B-Instruct",
        enable_lora=True,
        max_lora_rank=64,
    )

    @app.post("/v1/generate", response_model=GenerationResponse)
    async def generate(request: GenerationRequest):
        try:
            sampling_params = SamplingParams(
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
            outputs = llm.generate(
                [request.prompt],
                sampling_params,
                lora_request=[request.lora_adapter],
            )
            return GenerationResponse(
                text=outputs[0].outputs[0].text,
                usage={"total_tokens": len(outputs[0].outputs[0].token_ids)},
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # 启动: uvicorn vllm_deploy:app --host 0.0.0.0 --port 8000
    return app
```

### 11.2 方案二：TGI（Text Generation Inference）

```bash
# Docker 部署 LoRA（HuggingFace TGI）
docker run --gpus all -p 8080:80 \
  -v ~/.cache/huggingface:/data \
  ghcr.io/huggingface/text-generation-inference:latest \
  --model-id Qwen/Qwen2.5-7B-Instruct \
  --lora-adapters /path/to/lora/adapter_a \
  --max-lora-adapters 5
```

### 11.3 方案三：轻量级 ONNX Runtime 部署（边缘设备）

```python
# onnx_deploy.py
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM

def convert_to_onnx():
    """将 LoRA 合并模型转为 ONNX 格式"""

    model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-0.5B")
    lora_model = PeftModel.from_pretrained(model, "./lora_adapter")
    merged = lora_model.merge_and_unload()

    # 导出 ONNX
    dummy_input = torch.randint(0, 1000, (1, 128))
    torch.onnx.export(
        merged,
        dummy_input,
        "model.onnx",
        input_names=["input_ids"],
        output_names=["logits"],
        dynamic_axes={
            "input_ids": {0: "batch", 1: "sequence"},
            "logits": {0: "batch", 1: "sequence"},
        },
        opset_version=17,
    )
```

### 11.4 Docker 部署

```dockerfile
# Dockerfile
FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

WORKDIR /app

# 安装依赖
RUN pip install transformers peft accelerate vllm fastapi uvicorn

# 复制模型和代码
COPY ./merged_model /app/model
COPY ./app.py /app/app.py

# 暴露端口
EXPOSE 8000

# 启动服务
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 11.5 生产环境 Checklist

```
部署前检查清单
─────────────────────────────────────────────
□ 模型合并后的推理精度验证通过
□ 单次推理延迟满足 SLA（通常 < 2s）
□ 并发压力测试通过（目标 QPS）
□ 显存使用稳定，无内存泄漏
□ 模型输出安全性过滤（敏感词/有害内容）
□ 监控：prompt 级别延迟、错误率、token 使用量
□ 回滚方案：保留上一版本适配器
□ 多适配器路由逻辑正确
□ 日志记录：request_id, prompt, response, latency
□ 扩容策略：单 GPU 还是多 GPU 分片
```

---

## 12. 完整 Demo 代码

> 以下是与本指南配套的完整可运行脚本，见 `lora_demo.py`

### 文件结构

```
lora-finetuning-demo/
├── README.md
├── lora_finetuning_guide.md        # 本指南
├── lora_demo.py                    # 完整训练/推理脚本
├── test_deploy_guide.md            # 测试部署文档
├── tests/
│   ├── test_lora.py                # 单元测试
│   └── test_integration.py         # 集成测试
├── data/
│   └── sample_data.json            # 示例数据（可选）
└── requirements.txt                # 依赖清单
```

### 配套脚本

请参见 `lora_demo.py` 获取完整的端到端可运行实现，包括：
- 模型加载与 LoRA 配置
- 基于 PEFT 的训练循环
- 模型保存与合并
- 推理示例
- 评估函数

---

> **下一步**：运行 `python lora_demo.py --help` 查看命令行选项，或阅读 `lora_demo.py` 源码了解实现细节。

---

*本指南持续更新。如有问题或建议，欢迎讨论。*
