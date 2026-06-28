"""
═══════════════════════════════════════════════════════════════
  🚀 本地推理服务 — LoRA 微调模型部署
═══════════════════════════════════════════════════════════════

提供与 Ollama API 兼容的 HTTP 接口，无需 Ollama。
API 兼容: /api/generate  /api/chat

用法:
    python serve.py
    python serve.py --model ./merged_model --port 11435
"""

import os
import sys
import json
import time
import argparse
import logging
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Flask 应用 ──
try:
    from flask import Flask, request, jsonify, Response, stream_with_context
except ImportError:
    logger.error("请先安装 Flask: pip install flask")
    sys.exit(1)

app = Flask(__name__)

model = None
tokenizer = None
device = "cuda" if torch.cuda.is_available() else "cpu"


def load_model(model_path: str):
    """加载合并后的模型"""
    global model, tokenizer

    logger.info(f"加载模型: {model_path}")
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        device_map="auto",
        trust_remote_code=True,
        local_files_only=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        trust_remote_code=True,
        local_files_only=True,
    )
    logger.info(f"模型加载完成 ✅ 设备: {device}")
    return model, tokenizer


def generate_response(prompt: str, stream: bool = False, **kwargs):
    """生成回复"""
    temperature = kwargs.get("temperature", 0.7)
    top_p = kwargs.get("top_p", 0.9)
    max_tokens = kwargs.get("max_tokens", 1024)

    # 使用训练时的 prompt 格式
    full_prompt = f"指令: {prompt}\n输出:"

    inputs = tokenizer(full_prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            do_sample=temperature > 0,
            temperature=temperature if temperature > 0 else 1.0,
            top_p=top_p,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    response_text = tokenizer.decode(
        outputs[0][len(inputs.input_ids[0]):],
        skip_special_tokens=True,
    )

    if stream:
        # 模拟流式输出
        def generate():
            for char in response_text:
                yield json.dumps({"response": char, "done": False}) + "\n"
                time.sleep(0.01)
            yield json.dumps({"response": "", "done": True}) + "\n"
        return generate()
    else:
        return response_text


def chat_response(messages: list, stream: bool = False, **kwargs):
    """聊天回复"""
    temperature = kwargs.get("temperature", 0.7)
    top_p = kwargs.get("top_p", 0.9)
    max_tokens = kwargs.get("max_tokens", 1024)

    # 构建 Qwen 格式的对话
    prompt_parts = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if role == "system":
            prompt_parts.append(f"<|im_start|>system\n{content}<|im_end|>\n")
        elif role == "user":
            prompt_parts.append(f"<|im_start|>user\n{content}<|im_end|>\n")
        elif role == "assistant":
            prompt_parts.append(f"<|im_start|>assistant\n{content}<|im_end|>\n")

    full_prompt = "".join(prompt_parts) + "<|im_start|>assistant\n"

    inputs = tokenizer(full_prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            do_sample=temperature > 0,
            temperature=temperature if temperature > 0 else 1.0,
            top_p=top_p,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    response_text = tokenizer.decode(
        outputs[0][len(inputs.input_ids[0]):],
        skip_special_tokens=True,
    ).strip()

    if stream:
        def generate():
            for char in response_text:
                yield json.dumps({"message": {"content": char}, "done": False}) + "\n"
                time.sleep(0.01)
            yield json.dumps({"message": {"content": ""}, "done": True}) + "\n"
        return generate()
    else:
        return response_text


# ── API 路由 ──

@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.json
    prompt = data.get("prompt", "")
    stream = data.get("stream", False)

    kwargs = {k: v for k, v in data.items() if k not in ("prompt", "stream")}

    t_start = time.time()
    try:
        result = generate_response(prompt, stream=stream, **kwargs)
        if stream:
            return Response(stream_with_context(result()), mimetype="application/x-ndjson")
        return jsonify({
            "model": "lora-finetuned",
            "response": result,
            "done": True,
            "total_duration": int((time.time() - t_start) * 1e9),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.json
    messages = data.get("messages", [])
    stream = data.get("stream", False)

    kwargs = {k: v for k, v in data.items() if k not in ("messages", "stream")}

    t_start = time.time()
    try:
        result = chat_response(messages, stream=stream, **kwargs)
        if stream:
            return Response(stream_with_context(result()), mimetype="application/x-ndjson")
        return jsonify({
            "model": "lora-finetuned",
            "message": {"role": "assistant", "content": result},
            "done": True,
            "total_duration": int((time.time() - t_start) * 1e9),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/tags", methods=["GET"])
def api_tags():
    return jsonify({"models": [{"name": "lora-finetuned", "model": "lora-finetuned"}]})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model": "lora-finetuned", "device": device})


# ── 命令行接口（也可用于直接测试）──

def interactive():
    """交互式对话"""
    print("\n" + "=" * 50)
    print("  LoRA 微调模型 -- 交互式对话")
    print("  输入 'quit' 退出, 输入 'chat' 进入聊天模式")
    print("=" * 50 + "\n")

    mode = "instruct"  # instruct 或 chat

    while True:
        try:
            user_input = input(f"[{mode}] 你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("再见！")
            break
        if user_input.lower() == "chat":
            mode = "chat"
            print("切换到聊天模式")
            continue
        if user_input.lower() == "instruct":
            mode = "instruct"
            print("切换到指令模式")
            continue

        t_start = time.time()
        if mode == "chat":
            response = chat_response([
                {"role": "user", "content": user_input}
            ])
        else:
            response = generate_response(user_input)

        elapsed = time.time() - t_start
        print(f"[{mode}] 助手: {response}")
        print(f"(生成耗时: {elapsed:.1f}s)\n")


def main():
    parser = argparse.ArgumentParser(description="LoRA 微调模型推理服务")
    parser.add_argument("--model", type=str, default="./merged_model",
                        help="合并后模型目录")
    parser.add_argument("--port", type=int, default=11435,
                        help="服务端口 (默认 11435)")
    parser.add_argument("--host", type=str, default="127.0.0.1",
                        help="监听地址")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="交互式对话模式（不启动服务）")
    args = parser.parse_args()

    # 加载模型
    if not os.path.exists(args.model):
        logger.error(f"模型不存在: {args.model}")
        logger.info("请先运行: python merge_for_deploy.py")
        sys.exit(1)

    load_model(args.model)

    if args.interactive:
        interactive()
    else:
        logger.info(f"启动推理服务: http://{args.host}:{args.port}")
        logger.info("接口: /api/generate  /api/chat  /api/tags  /health")
        app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
