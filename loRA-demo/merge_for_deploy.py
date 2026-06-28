"""
═══════════════════════════════════════════════════════════════
  🔧 LoRA 权重合并 — 导出完整模型用于 Ollama 部署
═══════════════════════════════════════════════════════════════

将 final_model 中的 LoRA adapter 与基础模型合并，
输出可直接转换为 GGUF 的完整 HuggingFace 模型。

用法:
    python merge_for_deploy.py
    python merge_for_deploy.py --adapter_path ./lora_output/final_model --output ./merged_model
"""

import os
import sys
import argparse
import logging
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="合并 LoRA adapter 到基础模型")
    parser.add_argument("--base_model", type=str,
                        default="Qwen/Qwen2.5-0.5B-Instruct",
                        help="基础模型名称或路径")
    parser.add_argument("--adapter_path", type=str,
                        default="./lora_output/final_model",
                        help="LoRA adapter 目录")
    parser.add_argument("--output", type=str,
                        default="./merged_model",
                        help="合并后模型输出目录")
    args = parser.parse_args()

    if not os.path.exists(args.adapter_path):
        logger.error(f"Adapter 不存在: {args.adapter_path}")
        sys.exit(1)

    # 如果是 HuggingFace ID（含 /），自动映射到本地缓存路径
    base_path = args.base_model
    if "/" in base_path and not os.path.exists(base_path):
        # Qwen/Qwen2.5-0.5B-Instruct → 本地缓存
        org, name = base_path.split("/")
        base_path = os.path.join(
            os.path.expanduser("~/.cache/huggingface/hub"),
            f"models--{org}--{name}"
        )
        # 自动找最新 snapshot
        snapshots_dir = os.path.join(base_path, "snapshots")
        if os.path.isdir(snapshots_dir):
            snapshots = sorted(os.listdir(snapshots_dir))
            base_path = os.path.join(snapshots_dir, snapshots[-1])
        logger.info(f"本地缓存路径: {base_path}")

    # ── 1. 加载基础模型（offline 模式，不联网）──
    logger.info(f"加载基础模型: {base_path}")
    base_model = AutoModelForCausalLM.from_pretrained(
        base_path,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
        local_files_only=True,
    )

    # ── 2. 加载 LoRA adapter ──
    logger.info(f"加载 LoRA adapter: {args.adapter_path}")
    model = PeftModel.from_pretrained(base_model, args.adapter_path)

    # ── 3. 合并权重 ──
    logger.info("合并 LoRA 权重到基础模型...")
    merged_model = model.merge_and_unload()
    logger.info("合并完成 ✅")

    # ── 4. 保存完整模型 ──
    os.makedirs(args.output, exist_ok=True)
    merged_model.save_pretrained(args.output, safe_serialization=True)
    logger.info(f"模型权重已保存: {args.output}")

    # ── 5. 保存 tokenizer ──
    tokenizer = AutoTokenizer.from_pretrained(
        base_path, trust_remote_code=True, local_files_only=True
    )
    tokenizer.save_pretrained(args.output)
    logger.info(f"Tokenizer 已保存: {args.output}")

    # ── 6. 检查输出 ──
    logger.info("\n输出文件列表:")
    for f in sorted(os.listdir(args.output)):
        fpath = os.path.join(args.output, f)
        if os.path.isfile(fpath):
            size_mb = os.path.getsize(fpath) / (1024 * 1024)
            logger.info(f"  {f}  ({size_mb:.1f} MB)")

    logger.info("\n✅ 合并完成！下一步:")
    logger.info("  1. cd merged_model")
    logger.info("  2. 用 llama.cpp 转换: python convert-hf-to-gguf.py ./merged_model --outtype f16")
    logger.info("  3. 创建 Ollama Modelfile 并导入: ollama create my-lora-model -f Modelfile")


if __name__ == "__main__":
    main()
