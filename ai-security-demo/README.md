# 🛡️ AI 安全攻防 Demo

基于 OWASP Top 10 for LLM Applications 的 AI 安全攻防演示项目。

**5 类攻击 × 30+ Payload × 3 层防御 = 完整的 AI 安全学习平台。**

## 快速开始

```bash
# 1. 进入项目目录
cd ai-security-demo

# 2. (可选) 安装 Rich 终端美化
pip install rich

# 3. 运行（无需 API Key，纯模拟环境）
python main.py                  # 交互模式
python main.py --demo           # 完整演示（攻击+防御）
python main.py --attack all     # 运行全部攻击演示
python main.py --defense        # 防御机制详解
python main.py --compare        # 脆弱版 vs 加固版对比
python main.py --list           # 列出所有攻击 Payload
```

## 运行模式

| 命令 | 说明 |
|------|------|
| `python main.py` | 🌟 交互模式：浏览菜单，按需探索 |
| `python main.py --demo` | 📖 完整演示：OWASP 概览 → 攻击演示 → 防御详解 |
| `python main.py --attack prompt-injection` | 🎯 运行指定攻击类型的演示 |
| `python main.py --attack all` | 🔄 运行全部 5 类攻击演示 |
| `python main.py --defense` | 🛡️ 查看三层防御体系 |
| `python main.py --compare` | ⚖️ 脆弱版 vs 加固版逐项对比 |
| `python main.py --list` | 📋 列出所有攻击 Payload |

## 攻击类型

| # | 攻击类型 | OWASP | 严重度 | Payload 数 |
|---|---------|-------|--------|-----------|
| 1 | Prompt Injection（提示词注入） | LLM01 | 🔴 严重 | 12 |
| 2 | Jailbreak（越狱攻击） | LLM01 | 🔴 严重 | 8 |
| 3 | Tool & Function Abuse（工具调用滥用） | LLM08 | 🔴 严重 | 8 |
| 4 | Data Leakage（敏感数据泄露） | LLM06 | 🟠 高 | 9 |
| 5 | Adversarial Prompt（对抗性提示词） | LLM01/02 | 🟠 高 | 9 |

详细说明见 [docs/攻击类型详解.md](docs/攻击类型详解.md)

## 防御体系

```
Layer 1: Input Filter     →  用户输入到达 LLM 之前的安全检查
Layer 2: Output Guard     →  LLM 输出返回给用户之前的安全审查
Layer 3: Tool Sandbox     →  Agent 调用外部工具之前的安全审批
```

详细说明见 [docs/防御策略与安全设计.md](docs/防御策略与安全设计.md)

## 项目结构

```
ai-security-demo/
├── main.py                          # 🚀 主入口（交互式 CLI）
├── requirements.txt
├── README.md
├── src/
│   ├── config.py                    # ⚙️ 系统提示词（脆弱版/加固版）
│   ├── attacks/                     # 🔓 攻击模块
│   │   ├── prompt_injection.py      #   LLM01: 提示词注入
│   │   ├── jailbreak.py             #   LLM01: 越狱攻击
│   │   ├── data_leakage.py          #   LLM06: 数据泄露
│   │   ├── tool_abuse.py            #   LLM08: 工具滥用
│   │   └── adversarial.py           #   LLM01/02: 对抗性提示词
│   ├── defenses/                    # 🛡️ 防御模块
│   │   ├── input_filter.py          #   输入过滤器
│   │   ├── output_guard.py          #   输出审查器
│   │   └── sandbox.py               #   工具执行沙箱
│   └── vulnerable_app/              # 🎯 攻击靶场
│       └── simulator.py             #   脆弱版/加固版 LLM 应用模拟器
├── tests/
│   └── test_security.py             # 🧪 完整测试套件
└── docs/
    ├── 项目说明.md                   # 项目背景、目标、适用场景
    ├── 攻击类型详解.md               # 5 类攻击的深度解析
    └── 防御策略与安全设计.md          # 纵深防御与安全检查清单
```

## 测试

```bash
# 安装测试依赖
pip install pytest

# 运行全部测试（无需 API Key）
pytest tests/ -v
```

## 安全声明

> ⚠️ **重要声明**
>
> 本项目的所有攻击 Payload 仅用于**安全研究**和**教育**目的。
> 所有演示在**模拟环境**中运行，不调用真实 LLM API。
> 请勿将本项目技术用于未经授权的安全测试。
>
> 如果需要对生产系统进行安全评估，请：
> 1. 获得正式书面授权
> 2. 在隔离的测试环境中进行
> 3. 遵守适用的法律法规

## 适用场景

- 🎓 **安全培训**：开发团队 AI 安全意识培训的动手实验
- 🔍 **安全评估**：LLM 应用安全评估时的攻击面参考
- 📐 **安全设计**：从架构阶段引入纵深防御思维
- 📚 **教学案例**：高校信息安全课程的 AI 安全模块

## 许可

本项目仅供学习、研究和交流目的使用。
