# LoRA 微调测试与部署指南

> 本文档详细说明 LoRA 模型微调后的测试验证策略和生产部署方案，涵盖从 checkpoint 验证到线上服务的完整流程。

---

## 一、测试总览

### 1.1 测试金字塔

```
         ╱╲
        ╱  ╲               A/B 测试 & 人工评估
       ╱    ╲              ──────────────
      ╱ E2E  ╲             端到端集成测试
     ╱────────╲            ──────────────
    ╱   集成   ╲           模块集成 & 训练管道测试
   ╱────────────╲          ──────────────
  ╱    单元      ╲         LoRA 配置、参数计算、数据预处理
 ╱────────────────╲        ──────────────
╱      静态检查     ╲      代码风格、类型标注、配置文件 schema
╱────────────────────╲
```

### 1.2 测试分类

| 测试层级 | 关注点 | 频率 | 工具 |
|---------|--------|------|------|
| **单元测试** | LoRA 配置、参数计算、矩阵维度 | 每次提交 | pytest, unittest |
| **集成测试** | 训练管道、数据加载、模型保存/加载 | 每次提交 | pytest |
| **质量评估** | 生成质量、语义一致性、幻觉率 | 每次训练 | ROUGE/BLEU + 人工 |
| **性能测试** | 推理延迟、吞吐量、显存峰值 | 部署前 | 自定义 benchmark |
| **压力测试** | 并发请求、长序列、持续运行 | 部署前 | locust, k6 |
| **安全测试** | 对抗攻击、敏感词、越狱 | 定期 | 红队测试框架 |
| **A/B 测试** | 新旧模型对比 | 上线前 | 在线实验平台 |

---

## 二、单元测试

### 2.1 测试目录结构

```
tests/
├── __init__.py
├── conftest.py                     # pytest 共享 fixture
├── test_lora_config.py             # LoRA 配置测试
├── test_model_loading.py           # 模型加载测试
├── test_data_preprocessing.py      # 数据预处理测试
├── test_training.py                # 训练流程测试
├── test_inference.py               # 推理测试
├── test_model_save_load.py         # 模型保存/加载测试
├── test_merge.py                   # 权重合并测试
└── fixtures/
    ├── sample_data.json            # 测试用数据
    └── expected_outputs.json       # 预期输出
```

### 2.2 测试 Fixture 配置（conftest.py）

```python
"""tests/conftest.py - 共享 pytest fixture"""

import pytest
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model


@pytest.fixture(scope="session")
def tiny_model():
    """使用最小模型进行测试（快速）"""
    model = AutoModelForCausalLM.from_pretrained(
        "Qwen/Qwen2.5-0.5B-Instruct",
        torch_dtype=torch.float32,
        device_map="cpu",
    )
    return model


@pytest.fixture(scope="session")
def tokenizer():
    """Tokenizer fixture"""
    tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-0.5B-Instruct")
    tokenizer.pad_token = tokenizer.eos_token
    return tokenizer


@pytest.fixture
def lora_model(tiny_model):
    """应用 LoRA 后的模型"""
    config = LoraConfig(
        r=8,
        lora_alpha=16,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.0,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(tiny_model, config)
    return model


@pytest.fixture
def sample_batch():
    """标准测试输入"""
    return torch.randint(0, 1000, (2, 128))


@pytest.fixture
def sample_training_data():
    """训练用样本数据"""
    return [
        {"instruction": "你好", "output": "你好！有什么可以帮助你的吗？"},
        {"instruction": "1+1等于几", "output": "1+1=2"},
        {"instruction": "解释机器学习", "output": "机器学习是AI的一个分支。"},
    ]
```

### 2.3 核心测试用例

<details>
<summary>展开完整测试代码</summary>

```python
"""tests/test_lora_config.py"""

import torch
from peft import LoraConfig, get_peft_model
from peft.utils import transpose


class TestLoraConfig:

    def test_lora_param_count(self, tiny_model):
        """验证 LoRA 参数量计算是否正确"""
        config = LoraConfig(r=8, lora_alpha=16,
                            target_modules=["q_proj", "v_proj"])
        model = get_peft_model(tiny_model, config)

        trainable, total = model.get_nb_trainable_parameters()
        ratio = trainable / total

        # LoRA 可训练参数应远小于总参数
        assert ratio < 0.01, f"LoRA 参数比例过高: {ratio:.4f}"

    def test_lora_rank_effect(self, tiny_model):
        """验证不同 r 值产生的参数数量差异"""
        configs = [
            (4, "r=4"),
            (8, "r=8"),
            (16, "r=16"),
        ]
        param_counts = []

        for r, name in configs:
            config = LoraConfig(r=r, lora_alpha=16,
                                target_modules=["q_proj", "v_proj"])
            model = get_peft_model(tiny_model, config)
            trainable, _ = model.get_nb_trainable_parameters()
            param_counts.append((name, trainable))

        # 验证 r 与参数量的线性关系
        counts = [c for _, c in param_counts]
        assert counts[0] * 2 == counts[1], f"r=4 到 r=8 参数应翻倍"
        assert counts[0] * 4 == counts[2], f"r=4 到 r=16 参数应翻 4 倍"

    def test_lora_forward_shape(self, lora_model, sample_batch):
        """验证模型输出 shape 正确"""
        with torch.no_grad():
            output = lora_model(input_ids=sample_batch)

        expected_shape = (
            sample_batch.shape[0],       # batch
            sample_batch.shape[1],       # seq_len
            lora_model.config.vocab_size, # vocab
        )
        assert output.logits.shape == expected_shape, \
            f"预期 {expected_shape}, 实际 {output.logits.shape}"

    def test_lora_gradient_flow(self, lora_model, sample_batch):
        """验证 LoRA 参数接收梯度但原始参数不接收"""
        # 前向
        output = lora_model(input_ids=sample_batch, labels=sample_batch)
        loss = output.loss
        loss.backward()

        # 检查 LoRA 参数有梯度
        lora_has_grad = False
        original_has_grad = False

        for name, param in lora_model.named_parameters():
            if "lora_" in name and param.requires_grad:
                if param.grad is not None:
                    lora_has_grad = True
            elif "lora_" not in name and param.requires_grad is False:
                if param.grad is not None:
                    original_has_grad = True

        assert lora_has_grad, "LoRA 参数应有梯度"
        assert not original_has_grad, "原始参数不应有梯度"


"""tests/test_model_save_load.py"""

import os
import tempfile
import torch
from peft import PeftModel


class TestModelSaveLoad:

    def test_save_and_load_adapter(self, lora_model, tokenizer):
        """验证 LoRA 适配器的保存和加载"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 保存
            lora_model.save_pretrained(tmpdir)
            tokenizer.save_pretrained(tmpdir)

            # 检查文件存在
            assert os.path.exists(f"{tmpdir}/adapter_config.json")
            assert os.path.exists(f"{tmpdir}/adapter_model.bin")

            # 重新加载
            loaded = PeftModel.from_pretrained(lora_model.model, tmpdir)

            # 验证输出一致
            inputs = torch.randint(0, 100, (1, 32))
            with torch.no_grad():
                out1 = lora_model(input_ids=inputs).logits
                out2 = loaded(input_ids=inputs).logits

            assert torch.allclose(out1, out2, atol=1e-5), \
                "保存前后的模型输出应一致"

    def test_merge_and_unload(self, lora_model):
        """验证权重合并正确性"""
        inputs = torch.randint(0, 100, (1, 32))

        # 合并前
        with torch.no_grad():
            before = lora_model(input_ids=inputs).logits

        # 合并后
        merged = lora_model.merge_and_unload()
        with torch.no_grad():
            after = merged(input_ids=inputs).logits

        # 合并前后输出应一致（因为还未训练，BA=0）
        assert torch.allclose(before, after, atol=1e-4), \
            "未训练时合并前后输出应一致"

    def test_multiple_adapter_switching(self, tiny_model):
        """验证多适配器切换功能"""
        config_a = LoraConfig(r=8, target_modules=["q_proj", "v_proj"])
        config_b = LoraConfig(r=16, target_modules=["q_proj", "v_proj", "k_proj"])

        model = get_peft_model(tiny_model, config_a, adapter_name="adapter_a")
        model.add_adapter("adapter_b", config_b)

        inputs = torch.randint(0, 100, (1, 32))

        # 切换适配器
        model.set_adapter("adapter_a")
        out_a = model(input_ids=inputs).logits

        model.set_adapter("adapter_b")
        out_b = model(input_ids=inputs).logits

        # 不同适配器应产生不同输出
        assert not torch.allclose(out_a, out_b, atol=1e-5), \
            "不同 LoRA 配置应产生不同输出"


"""tests/test_data_preprocessing.py"""


class TestDataPreprocessing:

    def test_preprocess_format(self, tokenizer):
        """验证预处理函数输出格式"""
        from lora_demo import preprocess_function

        data = {
            "instruction": ["什么是机器学习？"],
            "output": ["机器学习是AI的一个分支。"],
        }

        result = preprocess_function(data, tokenizer, max_length=512)

        # 检查必需字段
        assert "input_ids" in result
        assert "labels" in result
        assert "attention_mask" in result

        # 检查长度一致
        assert len(result["input_ids"][0]) == len(result["labels"][0])

        # 检查标签掩码：输入部分应为 -100
        labels = result["labels"][0]
        assert -100 in labels, "labels 应包含 -100 掩码"

    def test_max_length_truncation(self, tokenizer):
        """验证超长序列截断"""
        from lora_demo import preprocess_function

        long_text = "机器学习" * 1000  # 超长序列
        data = {
            "instruction": [long_text],
            "output": [f"{long_text}总结"],
        }

        result = preprocess_function(data, tokenizer, max_length=128)

        # 检查截断
        assert len(result["input_ids"][0]) <= 128, \
            f"序列长度 {len(result['input_ids'][0])} 超过限制 128"
        assert len(result["labels"][0]) <= 128

    def test_empty_output_handling(self, tokenizer):
        """验证空输出处理"""
        from lora_demo import preprocess_function

        data = {
            "instruction": ["测试"],
            "output": [""],  # 空输出
        }

        # 不应抛出异常
        result = preprocess_function(data, tokenizer)

        # labels 应该全部被 -100 掩盖（因为没有输出）
        labels = result["labels"][0]
        assert all(l == -100 for l in labels), \
            "空输出时所有 labels 应为 -100"
```
</details>

### 2.4 运行测试

```bash
# 运行所有单元测试
cd lora-finetuning-demo
pytest tests/ -v

# 运行特定测试
pytest tests/test_lora_config.py -v -k "test_lora_param_count"

# 带覆盖率报告
pytest tests/ --cov=. --cov-report=html

# 快速模式（跳过慢测试）
pytest tests/ -v -m "not slow"
```

---

## 三、质量评估

### 3.1 自动评估指标

```python
"""evaluation/evaluator.py"""
from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np
from rouge_score import rouge_scorer
from bert_score import BERTScorer
import nltk
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction


@dataclass
class EvaluationResult:
    """评估结果"""
    rouge1: float
    rouge2: float
    rougeL: float
    bleu: float
    bert_score: float
    perplexity: float
    response_length: float
    repetition_rate: float


class ModelEvaluator:
    """
    模型质量评估器

    用法:
        evaluator = ModelEvaluator()
        result = evaluator.evaluate(model, tokenizer, test_data)
    """

    def __init__(self):
        self.rouge = rouge_scorer.RougeScorer(
            ["rouge1", "rouge2", "rougeL"],
            use_stemmer=True,
        )
        self.bert_scorer = BERTScorer(
            model_type="bert-base-chinese",
            lang="zh",
            rescale_with_baseline=True,
        )
        self.smooth_fn = SmoothingFunction().method1

    def evaluate(
        self,
        model,
        tokenizer,
        test_data: List[Dict],
        max_samples: int = 100,
    ) -> EvaluationResult:
        """对测试数据执行全面评估"""
        predictions = []
        references = []

        for i, item in enumerate(test_data[:max_samples]):
            prompt = f"指令: {item['instruction']}\n输出:"
            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
            outputs = model.generate(**inputs, max_new_tokens=256)
            pred = tokenizer.decode(outputs[0], skip_special_tokens=True)
            # 提取输出部分
            pred = pred.split("输出:")[-1].strip()

            predictions.append(pred)
            references.append(item["output"])

        # 计算各项指标
        return EvaluationResult(
            rouge1=self._calc_rouge("rouge1", predictions, references),
            rouge2=self._calc_rouge("rouge2", predictions, references),
            rougeL=self._calc_rouge("rougeL", predictions, references),
            bleu=self._calc_bleu(predictions, references),
            bert_score=self._calc_bert_score(predictions, references),
            perplexity=self._calc_perplexity(model, tokenizer, test_data[:max_samples]),
            response_length=np.mean([len(p) for p in predictions]),
            repetition_rate=self._calc_repetition_rate(predictions),
        )

    def _calc_rouge(self, metric: str, preds: List[str], refs: List[str]) -> float:
        scores = []
        for p, r in zip(preds, refs):
            scores.append(getattr(self.rouge.score(r, p), metric).fmeasure)
        return float(np.mean(scores))

    def _calc_bleu(self, preds: List[str], refs: List[str]) -> float:
        scores = []
        for p, r in zip(preds, refs):
            scores.append(sentence_bleu(
                [r.split()], p.split(),
                smoothing_function=self.smooth_fn,
            ))
        return float(np.mean(scores))

    def _calc_bert_score(self, preds: List[str], refs: List[str]) -> float:
        P, R, F1 = self.bert_scorer.score(preds, refs)
        return float(F1.mean().item())

    def _calc_perplexity(self, model, tokenizer, data: List[Dict]) -> float:
        losses = []
        for item in data:
            text = f"指令: {item['instruction']}\n输出: {item['output']}"
            inputs = tokenizer(text, return_tensors="pt").to(model.device)
            with torch.no_grad():
                outputs = model(**inputs, labels=inputs["input_ids"])
            losses.append(outputs.loss.item())
        return float(np.exp(np.mean(losses)))

    def _calc_repetition_rate(self, texts: List[str]) -> float:
        """计算生成文本的重复率（n-gram 重复比例）"""
        rates = []
        for text in texts:
            words = text.split()
            if len(words) < 4:
                continue
            # 计算重复 bigram 比例
            bigrams = set()
            repeats = 0
            for i in range(len(words) - 1):
                bg = f"{words[i]}_{words[i+1]}"
                if bg in bigrams:
                    repeats += 1
                bigrams.add(bg)
            rates.append(repeats / max(1, len(words) - 1))
        return float(np.mean(rates)) if rates else 0.0
```

### 3.2 评估报告示例

```
═══════════════════════════════════════
  LoRA 微调评估报告
═══════════════════════════════════════

模型: Qwen2.5-7B-Instruct + LoRA(r=8,alpha=16)
数据: 500 条指令数据, 3 epoch

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
自动指标
─────────────────────────────────────
ROUGE-1:      0.4523  ↑
ROUGE-2:      0.3217  ↑
ROUGE-L:      0.4189  ↑
BLEU:         0.2834  ↑
BERTScore:    0.8912  ↑
Perplexity:   3.2415  ↓
重复率:       0.0231  ↓
平均生成长度:  184.5  tokens
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

人工评估 (n=50)
─────────────────────────────────────
流畅度:       4.2/5  ★★★★
相关性:       4.5/5  ★★★★☆
有用性:       4.1/5  ★★★★
无害性:       4.8/5  ★★★★☆
翻车率:       2%     ✓
─────────────────────────────────────

性能指标
─────────────────────────────────────
推理延迟:     0.85s  (p50)
              1.23s  (p95)
              2.01s  (p99)
吞吐量:       45.2   req/s
显存峰值:     14.8   GB
─────────────────────────────────────

结论: ✅ 通过
═══════════════════════════════════════
```

### 3.3 人工评估模板

```markdown
## 人工评估记录

| # | Prompt | 参考输出 | 模型输出 | 流畅度(1-5) | 正确性(1-5) | 有用性(1-5) | 备注 |
|---|--------|---------|---------|-----------|-----------|-----------|------|
| 1 | 什么是机器学习？ | ... | ... | 5 | 5 | 5 | 优秀 |
| 2 | 写一首诗 | ... | ... | 4 | 4 | 3 | 略显平淡 |
| 3 | 解释量子计算 | ... | ... | 3 | 2 | 3 | 有一点幻觉 |

总体评价：
- 优点：流畅度高，格式规范
- 不足：部分领域知识仍需加强
- 建议：增加更多领域数据
```

---

## 四、性能测试

### 4.1 基准测试脚本

```python
"""benchmarks/benchmark.py"""

import time
import torch
import numpy as np
from dataclasses import dataclass
from typing import List


@dataclass
class BenchmarkResult:
    """性能基准测试结果"""
    model_name: str
    batch_size: int
    input_length: int
    output_length: int
    latency_p50: float  # ms
    latency_p95: float
    latency_p99: float
    throughput: float    # tokens/s
    peak_memory: float   # GB
    gpu_utilization: float  # %


def run_benchmark(
    model,
    tokenizer,
    input_lengths: List[int] = [128, 512, 1024, 2048],
    output_lengths: List[int] = [64, 128, 256, 512],
    num_runs: int = 10,
    warmup_runs: int = 3,
) -> List[BenchmarkResult]:
    """
    运行性能基准测试

    测试不同输入/输出长度组合下的性能指标
    """
    results = []

    for in_len in input_lengths:
        for out_len in output_lengths:
            # 无需输出超过输入太多
            if out_len > in_len * 2:
                continue

            latencies = []

            # 构造测试输入
            input_ids = torch.randint(0, 1000, (1, in_len)).to(model.device)

            # Warmup
            for _ in range(warmup_runs):
                _ = model.generate(
                    input_ids,
                    max_new_tokens=min(out_len, 32),
                    do_sample=False,
                )

            # 清空 CUDA 缓存
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats()

            # 正式测试
            for _ in range(num_runs):
                start = time.time()
                outputs = model.generate(
                    input_ids,
                    max_new_tokens=out_len,
                    do_sample=False,
                )
                end = time.time()

                latencies.append((end - start) * 1000)  # ms

            # 统计
            latencies = sorted(latencies)
            peak_mem = torch.cuda.max_memory_allocated() / 1024**3

            # 吞吐量: 生成的 token 数 / 总时间
            generated_tokens = num_runs * out_len
            total_time = sum(latencies) / 1000
            throughput = generated_tokens / total_time

            results.append(BenchmarkResult(
                model_name=model.config._name_or_path,
                batch_size=1,
                input_length=in_len,
                output_length=out_len,
                latency_p50=np.median(latencies),
                latency_p95=np.percentile(latencies, 95),
                latency_p99=np.percentile(latencies, 99),
                throughput=throughput,
                peak_memory=peak_mem,
                gpu_utilization=0.0,  # 需要 nvidia-smi 采集
            ))

    return results
```

### 4.2 并发压力测试

```bash
# 使用 locust 进行压测
# locustfile.py 见下方

pip install locust
locust -f benchmarks/locustfile.py --host=http://localhost:8000
```

```python
"""benchmarks/locustfile.py"""
from locust import HttpUser, task, between
import json


class LoRAModelUser(HttpUser):
    """LoRA 模型推理压测"""
    wait_time = between(0.5, 2.0)

    @task(3)
    def short_generation(self):
        """短文本生成"""
        payload = {
            "prompt": "什么是机器学习？",
            "max_tokens": 128,
            "temperature": 0.7,
        }
        with self.client.post(
            "/v1/generate",
            json=payload,
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Status: {response.status_code}")

    @task(1)
    def long_generation(self):
        """长文本生成"""
        payload = {
            "prompt": "请详细解释深度学习中的Transformer架构，包括自注意力机制、多头注意力、位置编码等核心概念的原理和实现。" * 3,
            "max_tokens": 512,
            "temperature": 0.7,
        }
        with self.client.post(
            "/v1/generate",
            json=payload,
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Status: {response.status_code}")
```

### 4.3 压力测试通过标准

| 指标 | 目标值 | 警告线 | 不可接受 |
|------|--------|--------|---------|
| P50 延迟 | < 1.0s | 1.0-2.0s | > 2.0s |
| P95 延迟 | < 2.0s | 2.0-4.0s | > 4.0s |
| P99 延迟 | < 5.0s | 5.0-10.0s | > 10.0s |
| 吞吐量 | > 30 req/s | 15-30 req/s | < 15 req/s |
| 错误率 | < 0.1% | 0.1-1.0% | > 1.0% |
| 显存 | < 80% 总显存 | 80-90% | > 90% |

---

## 五、部署指南

### 5.1 部署方案对比

| 方案 | 适用场景 | 延迟 | 吞吐量 | 多适配器 | 复杂度 |
|------|---------|------|--------|---------|-------|
| **vLLM** | 生产环境，高并发 | 低 | 高 | ✅ 原生支持 | 低 |
| **TGI** | HF 生态 | 中 | 中 | ✅ | 低 |
| **FastAPI + Transformers** | 小规模，快速原型 | 中高 | 低 | ❌ 需手动 | 低 |
| **ONNX Runtime** | 边缘设备 | 低 | 高 | ❌ | 高 |
| **TensorRT-LLM** | 极致性能 | 极低 | 极高 | ✅ | 高 |
| **llama.cpp** | CPU/边缘 | 中 | 中 | ❌ | 低 |

### 5.2 vLLM 部署（推荐）

```python
# deploy/vllm_server.py
"""
vLLM + LoRA 部署服务

启动：
    python deploy/vllm_server.py
    # 或
    vllm serve Qwen/Qwen2.5-7B-Instruct \
        --enable-lora \
        --lora-modules adapter_a=./lora_a adapter_b=./lora_b \
        --max-lora-rank=64 \
        --port 8000
"""

from vllm import LLM, SamplingParams
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

app = FastAPI(title="LoRA Model Serving API")

# ── 初始化 ──
MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"
LORA_ADAPTERS = {
    "default": "./lora_output/final_model",
}

llm = LLM(
    model=MODEL_NAME,
    enable_lora=True,
    max_loras=8,
    max_lora_rank=64,
    tensor_parallel_size=1,      # 单卡为 1
    gpu_memory_utilization=0.9,
    trust_remote_code=True,
    max_model_len=8192,
)


# ── API Schema ──

class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    repetition_penalty: float = 1.05
    lora_adapter: str = "default"
    stream: bool = False


class GenerateResponse(BaseModel):
    text: str
    usage: dict


# ── API 端点 ──

@app.post("/v1/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    try:
        params = SamplingParams(
            temperature=request.temperature,
            top_p=request.top_p,
            top_k=request.top_k,
            max_tokens=request.max_tokens,
            repetition_penalty=request.repetition_penalty,
        )

        adapter = request.lora_adapter
        outputs = llm.generate(
            [request.prompt],
            params,
            lora_request=adapter if adapter != "default" else None,
        )

        generated_text = outputs[0].outputs[0].text
        total_tokens = len(outputs[0].outputs[0].token_ids)

        return GenerateResponse(
            text=generated_text,
            usage={
                "prompt_tokens": len(outputs[0].prompt_token_ids),
                "completion_tokens": total_tokens,
                "total_tokens": len(outputs[0].prompt_token_ids) + total_tokens,
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/chat/completions")
async def chat_completions(request: dict):
    """兼容 OpenAI API 格式"""
    from vllm.entrypoints.openai.api_server import (
        build_openai_chat_completions_request
    )
    # 此处需适配 OpenAI 格式
    # 生产环境建议使用 vllm serve 直接提供 OpenAI 兼容 API
    raise HTTPException(status_code=501, detail="请使用 vllm serve 启动以支持 OpenAI 格式")


@app.get("/v1/adapters")
async def list_adapters():
    """列出可用适配器"""
    return {"adapters": list(LORA_ADAPTERS.keys())}


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 5.3 Docker 部署

```dockerfile
# Dockerfile.vllm
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

WORKDIR /app

# Python 环境
RUN apt-get update && apt-get install -y python3 python3-pip

# 安装 vLLM
RUN pip install vllm fastapi uvicorn

# 复制 LoRA 适配器
COPY ./lora_adapter /app/lora_adapter
COPY ./deploy/vllm_server.py /app/server.py

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  lora-server:
    build:
      context: .
      dockerfile: Dockerfile.vllm
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - CUDA_VISIBLE_DEVICES=0
    ports:
      - "8000:8000"
    volumes:
      - ~/.cache/huggingface:/root/.cache/huggingface
      - ./lora_output:/app/lora_output
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

### 5.4 Kubernetes 部署

```yaml
# deploy/k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lora-inference
  labels:
    app: lora-inference
spec:
  replicas: 2
  selector:
    matchLabels:
      app: lora-inference
  template:
    metadata:
      labels:
        app: lora-inference
    spec:
      containers:
      - name: vllm
        image: vllm/lora-server:latest
        ports:
        - containerPort: 8000
        resources:
          limits:
            nvidia.com/gpu: 1
            memory: "64Gi"
            cpu: "16"
          requests:
            nvidia.com/gpu: 1
            memory: "48Gi"
            cpu: "8"
        env:
        - name: CUDA_VISIBLE_DEVICES
          value: "0"
        volumeMounts:
        - name: model-cache
          mountPath: /root/.cache
        - name: lora-adapters
          mountPath: /app/lora_output
      volumes:
      - name: model-cache
        persistentVolumeClaim:
          claimName: huggingface-cache
      - name: lora-adapters
        persistentVolumeClaim:
          claimName: lora-adapters
      tolerations:
      - key: "nvidia.com/gpu"
        operator: "Exists"
        effect: "NoSchedule"
---
apiVersion: v1
kind: Service
metadata:
  name: lora-inference-service
spec:
  selector:
    app: lora-inference
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: lora-inference-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: lora-inference
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 5.5 生产部署 Checklist

```
□ [模型准备]
   ✓ LoRA 适配器训练完成并通过评估
   ✓ 已选择部署方式（vLLM/TGI/自建）
   ✓ 模型已转换为部署格式（可选：awq/gptq 量化）

□ [服务配置]
   ✓ 推理服务启动参数已确定
   ✓ 最大并发数已压测
   ✓ 超时时间已设置（通常 30s-60s）
   ✓ 请求队列大小已配置

□ [监控告警]
   ✓ 服务指标接入 Prometheus/Grafana
   ✓ 关键指标告警规则已设置
     - 延迟升高
     - 错误率升高
     - 显存过高
     - QPS 陡降
   ✓ 业务指标监控
     - 每日调用量
     - Token 消耗量
     - 用户满意度

□ [安全]
   ✓ 输入/输出内容安全过滤
   ✓ API 鉴权机制
   ✓ 速率限制（Rate Limiting）
   ✓ 请求日志记录（审计）

□ [容灾]
   ✓ 多副本部署
   ✓ 优雅关闭（Graceful Shutdown）
   ✓ 自动扩缩容配置
   ✓ 降级方案（降级到基础模型）
   ✓ 回滚方案

□ [持续集成]
   ✓ 训练 pipeline 自动化
   ✓ 模型评估自动化
   ✓ 部署 pipeline 自动化
   ✓ 模型版本管理
```

---

## 六、监控与运维

### 6.1 关键监控指标

```python
# deploy/monitoring.py
import time
import psutil
import torch
from prometheus_client import Counter, Histogram, Gauge, start_http_server


# ── 定义指标 ──

REQUEST_COUNT = Counter(
    "lora_requests_total",
    "Total number of inference requests",
    ["adapter", "status"],
)

REQUEST_LATENCY = Histogram(
    "lora_request_duration_seconds",
    "Request latency in seconds",
    ["adapter"],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0),
)

TOKENS_PER_REQUEST = Histogram(
    "lora_tokens_per_request",
    "Number of tokens generated per request",
    ["adapter"],
    buckets=(16, 64, 128, 256, 512, 1024, 2048),
)

GPU_MEMORY_USAGE = Gauge(
    "lora_gpu_memory_bytes",
    "GPU memory usage in bytes",
    ["device", "type"],  # type: allocated, reserved, cached
)

GPU_UTILIZATION = Gauge(
    "lora_gpu_utilization_percent",
    "GPU utilization percentage",
    ["device"],
)

ACTIVE_REQUESTS = Gauge(
    "lora_active_requests",
    "Number of active requests being processed",
)


def start_monitoring(port: int = 8001):
    """启动 Prometheus 监控端点"""
    start_http_server(port)
```

### 6.2 日志规范

```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "level": "INFO",
  "service": "lora-inference",
  "request_id": "req_a1b2c3d4",
  "adapter": "medical_v1",
  "prompt_length": 128,
  "response_length": 256,
  "latency_ms": 850,
  "temperature": 0.7,
  "top_p": 0.9,
  "gpu_memory_gb": 14.2,
  "status": "success"
}
```

---

## 七、快速参考

```bash
# ── 本地测试 ──
# 运行单元测试
pytest tests/ -v

# 运行质量评估
python evaluation/evaluator.py

# 运行性能测试
python benchmarks/benchmark.py

# ── 构建部署 ──
# 构建 Docker 镜像
docker build -f Dockerfile.vllm -t lora-server:latest .

# 启动服务
docker-compose up -d

# ── 测试 API ──
# 健康检查
curl http://localhost:8000/health

# 推理请求
curl -X POST http://localhost:8000/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "什么是机器学习？", "max_tokens": 256}'

# ── 压测 ──
locust -f benchmarks/locustfile.py --host=http://localhost:8000

# ── 监控 ──
# 启动 Prometheus 指标端点（默认集成）
# 访问 http://localhost:8001/metrics
```

---

## 八、常见问题

### Q1: 训练后的模型推理结果与训练前一样

**可能原因**：
- LoRA 权重未正确加载
- 训练时 `requires_grad` 设置错误
- 学习率太小，几乎没有更新

**排查步骤**：
1. 检查 `model.print_trainable_parameters()` 输出，确认可训练参数 > 0
2. 对比训练前后的 loss 值
3. 手动检查 LoRA 权重是否有变化：`model.base_model.model.model.layers[0].self_attn.q_proj.lora_A.default.weight`

### Q2: 部署后显存持续增长

**可能原因**：内存泄漏

**解决方案**：
1. 确保关闭了 `torch.no_grad()`（推理时）
2. 避免在 request handler 中创建模型
3. 使用 `torch.cuda.empty_cache()` 定期清理
4. 检查是否在每个请求中调用了 `tokenizer` 的返回值未释放

### Q3: vLLM 启用 LoRA 时报错 `ValueError: LoRA not supported`

**确认**：
- vLLM 版本 >= 0.4.0
- 启动时添加了 `--enable-lora` 参数
- 模型架构支持 LoRA（Qwen、LLaMA 系列均支持）

### Q4: 合并模型后效果下降

**可能原因**：精度损失

**解决方案**：
- 合并时使用 `dtype=torch.bfloat16`（与训练一致）
- 使用 `merge( safe_merge=True )` 做安全合并
- 考虑不合并，直接用 PeftModel 推理

---

> **相关文件**：
> - `lora_finetuning_guide.md` - 理论和流程完整指南
> - `lora_demo.py` - 完整可运行训练脚本
> - `tests/` - 单元测试和集成测试
> - `benchmarks/` - 性能基准测试
> - `deploy/` - 部署配置
