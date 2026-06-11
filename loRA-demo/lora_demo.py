#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
======================================================================
LoRA 模型微调全流程 Demo
======================================================================

本脚本演示了 LoRA（Low-Rank Adaptation）微调一个语言模型的完整流程：

  1. 环境检查与配置
  2. 加载基础模型与 Tokenizer（支持 4bit 量化）
  3. 配置 PEFT LoRA
  4. 准备示例数据（内置 + 可外部加载）
  5. 训练（使用 HuggingFace Trainer）
  6. 保存适配器 & 合并权重
  7. 推理测试
  8. 基础评估

用法：
    # 使用内置示例数据快速运行
    python lora_demo.py --quick

    # 使用自己的数据
    python lora_demo.py \
        --model_name Qwen/Qwen2.5-0.5B-Instruct \
        --data_path ./data/train.json \
        --output_dir ./output \
        --num_epochs 3 \
        --lora_r 8

    # 仅推理（使用已有适配器）
    python lora_demo.py --infer_only --adapter_path ./lora_adapter

依赖：
    torch>=2.0.0, transformers>=4.30.0, peft>=0.5.0,
    datasets>=2.10.0, accelerate>=0.20.0

作者：LoRA Demo
日期：2024
======================================================================
"""

import argparse
import json
import logging
import math
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import torch
from datasets import Dataset, load_dataset
from peft import (
    LoraConfig,
    PeftConfig,
    PeftModel,
    get_peft_model,
    prepare_model_for_kbit_training,
    TaskType,
)
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    HfArgumentParser,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq,
    BitsAndBytesConfig,
    GenerationConfig,
)
try:
    from torch.utils.tensorboard import SummaryWriter
    _HAS_TENSORBOARD = True
except ImportError:
    _HAS_TENSORBOARD = False
    SummaryWriter = None


# ─────────────────────────────────────────────────────────────────────
# 1. 日志配置
# ─────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────
# 2. 参数配置
# ─────────────────────────────────────────────────────────────────────

@dataclass
class ModelArguments:
    """模型相关参数"""
    model_name: str = field(
        default="Qwen/Qwen2.5-0.5B-Instruct",
        metadata={"help": "预训练模型名称或路径"}
    )
    use_4bit: bool = field(
        default=True,
        metadata={"help": "是否使用 4bit 量化加载"}
    )
    bnb_4bit_compute_dtype: str = field(
        default="bfloat16",
        metadata={"help": "4bit 计算精度: float16 | bfloat16 | float32"}
    )
    bnb_4bit_quant_type: str = field(
        default="nf4",
        metadata={"help": "4bit 量化类型: fp4 | nf4"}
    )
    use_double_quant: bool = field(
        default=True,
        metadata={"help": "是否使用双重量化"}
    )


@dataclass
class LoraArguments:
    """LoRA 相关参数"""
    lora_r: int = field(
        default=8,
        metadata={"help": "LoRA 秩 (rank)"}
    )
    lora_alpha: int = field(
        default=16,
        metadata={"help": "LoRA 缩放因子 alpha"}
    )
    lora_dropout: float = field(
        default=0.05,
        metadata={"help": "LoRA dropout 概率"}
    )
    target_modules: Optional[List[str]] = field(
        default=None,
        metadata={"help": "应用 LoRA 的目标模块, 默认 auto-detect"}
    )
    use_rslora: bool = field(
        default=True,
        metadata={"help": "是否使用 Rank-Stabilized LoRA"}
    )
    use_dora: bool = field(
        default=False,
        metadata={"help": "是否使用 DoRA (Weight-Decomposed LoRA)"}
    )


@dataclass
class DataArguments:
    """数据相关参数"""
    data_path: Optional[str] = field(
        default=None,
        metadata={"help": "训练数据路径 (JSONL 格式)"}
    )
    max_length: int = field(
        default=512,
        metadata={"help": "最大序列长度"}
    )
    val_split: float = field(
        default=0.1,
        metadata={"help": "验证集比例"}
    )


@dataclass
class TrainingConfig:
    """训练参数"""
    output_dir: str = field(
        default="./lora_output",
        metadata={"help": "输出目录"}
    )
    num_epochs: int = field(
        default=3,
        metadata={"help": "训练轮数"}
    )
    batch_size: int = field(
        default=4,
        metadata={"help": "每个设备的 batch size"}
    )
    gradient_accumulation_steps: int = field(
        default=4,
        metadata={"help": "梯度累积步数"}
    )
    learning_rate: float = field(
        default=2e-4,
        metadata={"help": "学习率"}
    )
    max_grad_norm: float = field(
        default=1.0,
        metadata={"help": "梯度裁剪最大值"}
    )
    warmup_ratio: float = field(
        default=0.03,
        metadata={"help": "学习率预热比例"}
    )
    logging_steps: int = field(
        default=10,
        metadata={"help": "日志记录间隔"}
    )
    save_steps: int = field(
        default=200,
        metadata={"help": "保存检查点间隔"}
    )
    save_total_limit: int = field(
        default=3,
        metadata={"help": "最多保留的检查点数"}
    )
    max_steps: int = field(
        default=-1,
        metadata={"help": "最大训练步数 (-1 表示由 epoch 决定)"}
    )
    inference_mode: bool = field(
        default=False,
        metadata={"help": "仅推理模式"}
    )
    adapter_path: Optional[str] = field(
        default=None,
        metadata={"help": "推理时使用的 LoRA 适配器路径"}
    )


# ─────────────────────────────────────────────────────────────────────
# 3. 示例数据生成
# ─────────────────────────────────────────────────────────────────────

def generate_sample_data(num_samples: int = 50) -> List[Dict]:
    """
    生成示例微调数据（指令问答格式）。
    实际使用时请替换为真实数据。
    """
    samples = [
        {"instruction": "什么是机器学习？", "output": "机器学习是人工智能的一个分支，通过从数据中学习模式和规律来做出预测或决策，而无需进行明确的编程。"},
        {"instruction": "1+1等于几？", "output": "1+1=2。这是基本的加法运算。"},
        {"instruction": "请用Python写一个斐波那契数列函数", "output": "def fibonacci(n):\\n    if n <= 1:\\n        return n\\n    return fibonacci(n-1) + fibonacci(n-2)\\n\\n# 或者使用迭代:\\ndef fibonacci_iter(n):\\n    a, b = 0, 1\\n    for _ in range(n):\\n        a, b = b, a + b\\n    return a"},
        {"instruction": "解释什么是注意力机制", "output": "注意力机制是一种让模型在处理序列时动态分配'注意力'权重的方法。它允许模型关注输入中最重要的部分，而不是平等对待所有位置。自注意力（Self-Attention）是 Transformer 架构的核心。"},
        {"instruction": "写一首关于秋天的短诗", "output": "秋风起，叶飘零，\\n远山如黛草枯荣。\\n一壶清茶半卷书，\\n坐看云起又几重。"},
        {"instruction": "告诉我太阳系有几大行星", "output": "太阳系有八大行星，按照距离太阳由近到远依次是：水星、金星、地球、火星、木星、土星、天王星和海王星。"},
        {"instruction": "翻译'Hello World'成中文", "output": "Hello World 翻译成中文是：'你好，世界'。在编程中常作为入门程序的第一个示例。"},
        {"instruction": "什么是BP神经网络？", "output": "BP（Back Propagation）神经网络是一种通过误差反向传播算法训练的多层前馈神经网络。它包含输入层、隐藏层和输出层，通过计算输出与真实值的误差，将误差从输出层反向传播到各隐藏层，逐层调整权重。"},
        {"instruction": "Git中如何撤销最近一次commit？", "output": "如果还没有推送到远程：\\n- git reset --soft HEAD~1  # 保留更改\\n- git reset --hard HEAD~1  # 丢弃更改\\n如果已经推送：\\n- git revert HEAD  # 创建一个新的撤销commit"},
        {"instruction": "什么是深度学习中的过拟合？", "output": "过拟合（Overfitting）是指模型在训练数据上表现很好，但在未见过的测试数据上表现差的现象。原因通常是模型过于复杂或训练数据太少。常见的解决方法包括：增加数据量、降低模型复杂度、使用正则化（L1/L2）、Dropout、早停（Early Stopping）等。"},
        {"instruction": "请解释Python装饰器", "output": "Python装饰器是一种高阶函数，它接受一个函数作为参数，并返回一个新的函数来增强原函数的功能。使用 @ 语法糖可以让代码更简洁。常见的应用包括：日志记录、性能计时、权限检查、缓存等。"},
        {"instruction": "什么是Transformer架构？", "output": "Transformer 是一种基于自注意力机制（Self-Attention）的深度学习架构，由 Vaswani 等人在 2017 年提出。它由编码器（Encoder）和解码器（Decoder）组成，每个部分包含多个注意力层和前馈网络层。其核心优势是能够并行处理序列数据，并捕获长距离依赖关系。BERT、GPT 等模型都基于 Transformer 架构。"},
        {"instruction": "如何优化SQL查询性能？", "output": "优化SQL查询的常用方法：1. 合理使用索引 2. 避免 SELECT * 3. 使用 EXPLAIN 分析执行计划 4. 优化 JOIN 顺序 5. 使用 LIMIT 限制结果集 6. 避免在 WHERE 中对列使用函数 7. 考虑分区表 8. 定期更新统计信息。"},
        {"instruction": "简述TCP三次握手", "output": "TCP三次握手是建立可靠连接的过程：第一次：客户端发送 SYN 包（SYN=1, seq=x）；第二次：服务器回复 SYN+ACK 包（SYN=1, ACK=1, seq=y, ack=x+1）；第三次：客户端发送 ACK 包（ACK=1, seq=x+1, ack=y+1）。至此连接建立完成。"},
        {"instruction": "排序算法中时间复杂度和空间复杂度分别指什么？", "output": "时间复杂度是算法执行时间随输入规模增长的变化趋势，用大O表示法表示。空间复杂度是算法执行过程中所需的额外存储空间。例如：快速排序平均时间复杂度 O(n log n)，最坏 O(n²)，空间复杂度 O(log n)；归并排序时间复杂度 O(n log n)，空间复杂度 O(n)。"},
    ]

    # 如果样本数不足，循环补充
    result = []
    for i in range(num_samples):
        result.append(samples[i % len(samples)].copy())
        # 添加一点点随机变化，使数据看起来更真实
        if i >= len(samples):
            result[-1]["instruction"] += f"（示例{i}）"

    return result


# ─────────────────────────────────────────────────────────────────────
# 4. 数据预处理
# ─────────────────────────────────────────────────────────────────────

def preprocess_function(
    examples: Dict[str, List],
    tokenizer: AutoTokenizer,
    max_length: int = 512,
) -> Dict[str, List]:
    """
    将指令数据转换为模型训练格式。

    核心逻辑：
    - 使用 '指令: ...\\n输出:' 作为 prompt 前缀
    - loss 只在输出部分计算
    - 将 labels 中对应输入部分的 token 设为 -100（忽略）
    """
    # 构建 prompt 和完整文本
    prompts = []
    full_texts = []

    for instruction, output in zip(examples["instruction"], examples["output"]):
        prompt = f"指令: {instruction}\n输出:"
        full_text = prompt + output
        prompts.append(prompt)
        full_texts.append(full_text)

    # Tokenize
    model_inputs = tokenizer(
        full_texts,
        max_length=max_length,
        truncation=True,
        padding=False,
        return_tensors=None,
    )

    # Tokenize prompts 以计算 labels mask
    prompt_tokens = tokenizer(
        prompts,
        max_length=max_length,
        truncation=True,
        padding=False,
        return_tensors=None,
    )

    labels = model_inputs["input_ids"].copy()

    # 将输入部分的标签设为 -100（不参与 loss 计算）
    for i, (label, prompt_ids) in enumerate(zip(labels, prompt_tokens["input_ids"])):
        # 将 prompt 部分设为 -100
        label[:len(prompt_ids)] = [-100] * len(prompt_ids)

    model_inputs["labels"] = labels
    return model_inputs


def load_and_prepare_data(
    data_path: Optional[str],
    tokenizer: AutoTokenizer,
    max_length: int = 512,
    val_split: float = 0.1,
):
    """
    加载并准备训练数据。

    如果 data_path 为 None，则使用内置示例数据。
    支持 JSONL 格式（每行一个 JSON 对象）。
    """
    if data_path and os.path.exists(data_path):
        logger.info(f"从 {data_path} 加载数据...")
        dataset = load_dataset("json", data_files=data_path, split="train")
    else:
        if data_path:
            logger.warning(f"数据文件 {data_path} 不存在，使用内置示例数据")
        logger.info("使用内置示例数据...")
        sample_data = generate_sample_data(50)
        dataset = Dataset.from_list(sample_data)

    logger.info(f"原始数据量: {len(dataset)}")

    # 预处理
    dataset = dataset.map(
        lambda x: preprocess_function(x, tokenizer, max_length),
        batched=True,
        remove_columns=dataset.column_names,
    )

    # 分割训练/验证集
    if val_split > 0:
        split = dataset.train_test_split(test_size=val_split, seed=42)
        train_dataset = split["train"]
        eval_dataset = split["test"]
        logger.info(f"训练集: {len(train_dataset)}, 验证集: {len(eval_dataset)}")
    else:
        train_dataset = dataset
        eval_dataset = None
        logger.info(f"训练集: {len(train_dataset)}")

    return train_dataset, eval_dataset


# ─────────────────────────────────────────────────────────────────────
# 5. 模型加载
# ─────────────────────────────────────────────────────────────────────

def create_bnb_config(args: ModelArguments) -> BitsAndBytesConfig:
    """创建 4bit 量化配置"""
    compute_dtype_map = {
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
        "float32": torch.float32,
    }

    return BitsAndBytesConfig(
        load_in_4bit=args.use_4bit,
        bnb_4bit_compute_dtype=compute_dtype_map.get(
            args.bnb_4bit_compute_dtype, torch.bfloat16
        ),
        bnb_4bit_quant_type=args.bnb_4bit_quant_type,
        bnb_4bit_use_double_quant=args.use_double_quant,
    )


def load_model_and_tokenizer(
    model_args: ModelArguments,
    lora_args: Optional[LoraArguments] = None,
):
    """
    加载基础模型和 Tokenizer。
    支持普通加载和 4bit 量化加载。
    """
    logger.info(f"加载模型: {model_args.model_name}")

    # 量化配置
    bnb_config = create_bnb_config(model_args) if model_args.use_4bit else None

    # 加载模型
    model = AutoModelForCausalLM.from_pretrained(
        model_args.model_name,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.bfloat16 if model_args.bnb_4bit_compute_dtype == "bfloat16"
                     else torch.float16,
        trust_remote_code=True,
        use_cache=False,  # gradient checkpointing 需要
    )

    # 加载 Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        model_args.model_name,
        trust_remote_code=True,
        padding_side="right",
    )

    # 设置 padding token
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # 为 kbit 训练准备模型
    if model_args.use_4bit:
        model = prepare_model_for_kbit_training(model)

    # 启用梯度检查点
    model.gradient_checkpointing_enable()

    # 统计模型信息
    total_params = sum(p.numel() for p in model.parameters())
    logger.info(f"模型总参数量: {total_params / 1e9:.2f}B")

    return model, tokenizer


def get_target_modules(model_name: str) -> List[str]:
    """
    根据模型名称自动推断 LoRA 目标模块。

    注意：具体模块名请通过 model.named_modules() 确认。
    """
    model_name_lower = model_name.lower()

    # LLaMA 系列
    if "llama" in model_name_lower or "qwen" in model_name_lower:
        return ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    # ChatGLM
    elif "chatglm" in model_name_lower:
        return ["query_key_value", "dense", "dense_h_to_4h", "dense_4h_to_h"]
    # BLOOM
    elif "bloom" in model_name_lower:
        return ["query_key_value", "dense", "dense_h_to_4h", "dense_4h_to_h"]
    # GPT / OPT
    elif "gpt" in model_name_lower or "opt" in model_name_lower:
        return ["q_proj", "v_proj"]
    # 默认
    else:
        return ["q_proj", "k_proj", "v_proj", "o_proj"]


def setup_lora(
    model: AutoModelForCausalLM,
    lora_args: LoraArguments,
    model_name: str,
):
    """配置并应用 LoRA"""

    target_modules = lora_args.target_modules or get_target_modules(model_name)
    logger.info(f"LoRA 目标模块: {target_modules}")

    lora_config = LoraConfig(
        r=lora_args.lora_r,
        lora_alpha=lora_args.lora_alpha,
        target_modules=target_modules,
        lora_dropout=lora_args.lora_dropout,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
        use_rslora=lora_args.use_rslora,
        use_dora=lora_args.use_dora,
    )

    logger.info(f"LoRA 配置:\n"
                f"  r={lora_args.lora_r}, "
                f"alpha={lora_args.lora_alpha}, "
                f"dropout={lora_args.lora_dropout}\n"
                f"  rslora={lora_args.use_rslora}, "
                f"dora={lora_args.use_dora}")

    # 应用 LoRA
    model = get_peft_model(model, lora_config)

    # 打印可训练参数
    trainable_params, all_params = model.get_nb_trainable_parameters()
    logger.info(f"可训练参数: {trainable_params:,} / {all_params:,} "
                f"({100 * trainable_params / all_params:.3f}%)")

    return model


# ─────────────────────────────────────────────────────────────────────
# 6. 训练
# ─────────────────────────────────────────────────────────────────────

def train(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    train_dataset: Dataset,
    eval_dataset: Optional[Dataset],
    training_config: TrainingConfig,
):
    """执行 LoRA 微调训练"""

    logger.info("开始训练...")
    logger.info(f"训练参数:\n"
                f"  epochs={training_config.num_epochs}, "
                f"batch={training_config.batch_size}, "
                f"lr={training_config.learning_rate}\n"
                f"  gradient_accumulation={training_config.gradient_accumulation_steps}")

    # 计算训练步数（用于 warmup）
    total_steps = (
        training_config.max_steps
        if training_config.max_steps > 0
        else math.ceil(len(train_dataset) / (
            training_config.batch_size * training_config.gradient_accumulation_steps
        )) * training_config.num_epochs
    )

    training_args = TrainingArguments(
        output_dir=training_config.output_dir,
        logging_dir=os.path.join(training_config.output_dir, "logs"),

        # 训练核心
        num_train_epochs=training_config.num_epochs,
        max_steps=training_config.max_steps,
        per_device_train_batch_size=training_config.batch_size,
        per_device_eval_batch_size=training_config.batch_size,
        gradient_accumulation_steps=training_config.gradient_accumulation_steps,
        learning_rate=training_config.learning_rate,
        warmup_ratio=training_config.warmup_ratio,
        lr_scheduler_type="cosine",

        # 精度与优化
        bf16=torch.cuda.is_bf16_supported(),
        fp16=not torch.cuda.is_bf16_supported(),
        optim="adamw_torch",
        gradient_checkpointing=True,

        # 正则化
        weight_decay=0.01,
        max_grad_norm=training_config.max_grad_norm,

        # 日志与保存
        logging_steps=training_config.logging_steps,
        save_strategy="steps" if training_config.save_steps > 0 else "epoch",
        save_steps=training_config.save_steps if training_config.save_steps > 0 else None,
        save_total_limit=training_config.save_total_limit,
        report_to="tensorboard" if _HAS_TENSORBOARD else "none",
        load_best_model_at_end=eval_dataset is not None,
        metric_for_best_model="eval_loss" if eval_dataset else None,

        # 评估策略必须与保存策略一致（load_best_model_at_end 要求）
        eval_strategy="steps" if training_config.save_steps > 0 else "epoch",
        eval_steps=training_config.save_steps if training_config.save_steps > 0 else None,

        # 分布式
        ddp_find_unused_parameters=False,
        remove_unused_columns=False,
        dataloader_pin_memory=False,
    )

    # 数据整理器
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
        padding="longest",
        pad_to_multiple_of=8,
    )

    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        tokenizer=tokenizer,
        data_collator=data_collator,
    )

    # 开始训练
    train_result = trainer.train()

    # 保存最终模型
    final_output = os.path.join(training_config.output_dir, "final_model")
    trainer.save_model(final_output)
    tokenizer.save_pretrained(final_output)
    logger.info(f"模型已保存到: {final_output}")

    # 保存训练指标
    metrics = train_result.metrics
    trainer.log_metrics("train", metrics)
    trainer.save_metrics("train", metrics)

    if eval_dataset:
        eval_metrics = trainer.evaluate()
        trainer.log_metrics("eval", eval_metrics)
        trainer.save_metrics("eval", eval_metrics)

    return model, trainer


# ─────────────────────────────────────────────────────────────────────
# 7. 推理
# ─────────────────────────────────────────────────────────────────────

def run_inference(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    prompt: str,
    max_new_tokens: int = 256,
    temperature: float = 0.7,
    top_p: float = 0.9,
    top_k: int = 50,
    repetition_penalty: float = 1.05,
) -> str:
    """执行单次推理"""
    formatted_prompt = f"指令: {prompt}\n输出:"

    inputs = tokenizer(
        formatted_prompt,
        return_tensors="pt",
        truncation=True,
        max_length=1024,
    ).to(model.device)

    # 配置生成参数
    gen_config = GenerationConfig(
        max_new_tokens=max_new_tokens,
        do_sample=temperature > 0,
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        repetition_penalty=repetition_penalty,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.pad_token_id,
    )

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            generation_config=gen_config,
        )

    response = tokenizer.decode(
        outputs[0][inputs["input_ids"].shape[1]:],
        skip_special_tokens=True,
    )

    return response.strip()


def run_batch_inference(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    test_prompts: List[str],
):
    """批量运行推理测试"""
    logger.info("\n" + "=" * 60)
    logger.info("推理测试结果")
    logger.info("=" * 60)

    for i, prompt in enumerate(test_prompts):
        start_time = time.time()
        response = run_inference(model, tokenizer, prompt)

        elapsed = time.time() - start_time
        logger.info(f"\n--- Prompt {i+1} ---")
        logger.info(f"输入: {prompt}")
        logger.info(f"输出: {response}")
        logger.info(f"耗时: {elapsed:.2f}s")

    logger.info("=" * 60)


# ─────────────────────────────────────────────────────────────────────
# 8. 基础评估
# ─────────────────────────────────────────────────────────────────────

def evaluate_perplexity(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    eval_data: Dataset,
    max_samples: int = 50,
) -> float:
    """
    计算模型在验证集上的困惑度 (Perplexity)。

    Perplexity 衡量模型对数据的"不确定度"：值越低越好。
    公式: PPL = exp(loss)
    """
    model.eval()
    total_loss = 0.0
    num_batches = 0

    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer, model=model, padding="longest"
    )

    indices = torch.randperm(len(eval_data))[:max_samples]
    batch_size = 8

    with torch.no_grad():
        for i in range(0, len(indices), batch_size):
            batch_indices = indices[i:i+batch_size].tolist()
            batch = data_collator([eval_data[j] for j in batch_indices])
            batch = {k: v.to(model.device) for k, v in batch.items()}

            outputs = model(**batch)
            loss = outputs.loss
            total_loss += loss.item()
            num_batches += 1

    avg_loss = total_loss / max(1, num_batches)
    perplexity = math.exp(avg_loss)
    logger.info(f"验证集 Perplexity: {perplexity:.4f} (avg_loss={avg_loss:.4f})")

    return perplexity


# ─────────────────────────────────────────────────────────────────────
# 9. 主流程
# ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="LoRA 模型微调全流程 Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 快速运行
  python lora_demo.py --quick

  # 使用自己的数据训练
  python lora_demo.py --data_path ./data/train.json --num_epochs 3

  # 仅推理
  python lora_demo.py --infer_only --adapter_path ./lora_output/final_model

  # 指定模型和 LoRA 参数
  python lora_demo.py --model_name Qwen/Qwen2.5-7B-Instruct --lora_r 16 --lora_alpha 32
        """
    )

    # 快速运行
    parser.add_argument("--quick", action="store_true",
                        help="使用默认参数快速运行（内置示例数据）")

    # 模型参数
    parser.add_argument("--model_name", type=str,
                        default="Qwen/Qwen2.5-0.5B-Instruct",
                        help="模型名称或路径")
    parser.add_argument("--no_quant", action="store_true",
                        help="不使用 4bit 量化")

    # LoRA 参数
    parser.add_argument("--lora_r", type=int, default=8,
                        help="LoRA 秩")
    parser.add_argument("--lora_alpha", type=int, default=16,
                        help="LoRA alpha")
    parser.add_argument("--lora_dropout", type=float, default=0.05,
                        help="LoRA dropout")
    parser.add_argument("--no_rslora", action="store_true",
                        help="不使用 Rank-Stabilized LoRA")
    parser.add_argument("--dora", action="store_true",
                        help="使用 DoRA")

    # 数据参数
    parser.add_argument("--data_path", type=str, default=None,
                        help="训练数据路径 (JSONL)")
    parser.add_argument("--max_length", type=int, default=512,
                        help="最大序列长度")

    # 训练参数
    parser.add_argument("--output_dir", type=str, default="./lora_output",
                        help="输出目录")
    parser.add_argument("--num_epochs", type=int, default=3,
                        help="训练轮数")
    parser.add_argument("--batch_size", type=int, default=4,
                        help="每个设备的 batch size")
    parser.add_argument("--learning_rate", type=float, default=2e-4,
                        help="学习率")
    parser.add_argument("--max_steps", type=int, default=-1,
                        help="最大训练步数")
    parser.add_argument("--save_steps", type=int, default=0,
                        help="保存间隔步数 (0=按epoch保存)")

    # 推理参数
    parser.add_argument("--infer_only", action="store_true",
                        help="仅推理模式")
    parser.add_argument("--adapter_path", type=str, default=None,
                        help="LoRA 适配器路径（推理模式使用）")

    parser.add_argument("--eval_only", action="store_true",
                        help="仅评估模式")

    args = parser.parse_args()

    # ── 快速模式 ──
    if args.quick:
        logger.info("=" * 60)
        logger.info("LoRA 微调 Demo - 快速模式")
        logger.info("=" * 60)
        args.model_name = "Qwen/Qwen2.5-0.5B-Instruct"
        args.output_dir = "./lora_output_quick"
        args.num_epochs = 2
        args.batch_size = 2
        args.gradient_accumulation_steps = 2
    else:
        args.gradient_accumulation_steps = 4

    # ── 运行流程 ──
    try:
        # 检查 CUDA
        if not torch.cuda.is_available():
            logger.warning("⚠ CUDA 不可用，将使用 CPU 训练（速度会非常慢）")

        logger.info(f"设备: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
        logger.info(f"可用 GPU 数: {torch.cuda.device_count() if torch.cuda.is_available() else 0}")

        # 准备参数对象
        model_args = ModelArguments(
            model_name=args.model_name,
            use_4bit=not args.no_quant and torch.cuda.is_available(),
        )

        lora_args = LoraArguments(
            lora_r=args.lora_r,
            lora_alpha=args.lora_alpha,
            lora_dropout=args.lora_dropout,
            use_rslora=not args.no_rslora,
            use_dora=args.dora,
        )

        training_config = TrainingConfig(
            output_dir=args.output_dir,
            num_epochs=args.num_epochs,
            batch_size=args.batch_size,
            gradient_accumulation_steps=args.gradient_accumulation_steps,
            learning_rate=args.learning_rate,
            max_steps=args.max_steps,
            save_steps=args.save_steps,
            inference_mode=args.infer_only,
            adapter_path=args.adapter_path,
        )

        # ── 推理模式 ──
        if args.infer_only:
            adapter_path = args.adapter_path or os.path.join(args.output_dir, "final_model")
            if not os.path.exists(adapter_path):
                logger.error(f"适配器不存在: {adapter_path}")
                sys.exit(1)

            logger.info(f"推理模式: 加载适配器 {adapter_path}")
            base_model, tokenizer = load_model_and_tokenizer(model_args)
            model = PeftModel.from_pretrained(base_model, adapter_path)
            model = model.merge_and_unload()

            test_prompts = [
                "什么是机器学习？",
                "请用Python写一个排序算法",
                "解释什么是注意力机制",
                "TCP三次握手是什么？",
            ]
            run_batch_inference(model, tokenizer, test_prompts)
            return

        # ── 加载模型 ──
        model, tokenizer = load_model_and_tokenizer(model_args)

        # ── 配置 LoRA ──
        model = setup_lora(model, lora_args, args.model_name)

        # ── 加载数据 ──
        train_dataset, eval_dataset = load_and_prepare_data(
            args.data_path, tokenizer, args.max_length
        )

        # ── 训练 ──
        model, trainer = train(model, tokenizer, train_dataset, eval_dataset, training_config)

        # ── 评估 ──
        if eval_dataset:
            train_dataset_for_eval, eval_dataset_for_eval = load_and_prepare_data(
                args.data_path, tokenizer, args.max_length, val_split=0.1
            )
            # 这里用 trainer 已经做了 eval，不再重复

        # ── 合并权重并测试推理 ──
        logger.info("\n合并 LoRA 权重到基础模型...")
        merged_model = model.merge_and_unload()
        logger.info("权重合并完成")

        test_prompts = [
            "什么是机器学习？",
            "1+1等于几？",
            "请用Python写一个斐波那契数列函数",
        ]
        run_batch_inference(merged_model, tokenizer, test_prompts)

        logger.info("\n✅ Demo 运行完成！")
        logger.info(f"模型已保存到: {args.output_dir}")
        logger.info(f"运行 tensorboard: tensorboard --logdir {os.path.join(args.output_dir, 'logs')}")

    except KeyboardInterrupt:
        logger.info("\n\n⏹ 训练被用户中断")
    except Exception as e:
        logger.error(f"❌ 发生错误: {e}", exc_info=True)
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────
# 10. 入口
# ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()
