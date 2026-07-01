# 🛡️ 安全沙箱应用 Demo

展示三种主流代码执行沙箱技术的实际应用和对比。

**Subprocess 资源限制沙箱 | Docker 容器沙箱 | RestrictedPython AST 沙箱**

## 快速开始

```bash
cd sandbox-demo
pip install -r requirements.txt

# 无需外部依赖即可运行大部分功能
python main.py                  # 交互模式
python main.py --demo           # 完整演示（三种沙箱）
python main.py --compare        # 沙箱技术对比
python main.py --sandbox subprocess  # 使用指定沙箱
python main.py --policy-check "import os"  # 安全策略检查
```

## 运行模式

| 命令 | 说明 |
|------|------|
| `python main.py` | 🌟 交互模式：选择沙箱 → 输入代码 → 查看结果 |
| `python main.py --demo` | 📖 完整演示：对 6 个测试用例在三沙箱上运行 |
| `python main.py --compare` | 🔍 技术对比表 + 可用状态检查 |
| `python main.py --sandbox subprocess` | 🎯 使用 subprocess 沙箱交互执行 |
| `python main.py --policy-check "代码"` | 🔒 安全策略分析（仅检查不执行） |
| `python main.py --code "print(1+1)" --sandbox restricted` | ⚡ 直接执行（非交互） |
| `python main.py --timeout 5 --memory 128` | ⚙️ 自定义超时和内存限制 |

## 三种沙箱技术

```
┌────────────────────────────────────────────────────┐
│  Subprocess Sandbox     Docker Sandbox    RestrictedPython  │
│  ─────────────────     ──────────────    ────────────────  │
│  隔离等级: 进程级      隔离等级: 容器级    隔离等级: 语言级   │
│  启动速度: ~50ms       启动速度: ~1s       启动速度: < 1ms   │
│  外部依赖: 无 ✅        外部依赖: Docker    外部依赖: 无 ✅   │
│  跨平台: ✅            跨平台: ⚠️          跨平台: ✅        │
│                                                         │
│  RLIMIT 资源限制      Cgroup + Namespace    AST 变换 + 受限   │
│  subprocess 子进程     Capabilities 安全层   builtins 替换   │
└────────────────────────────────────────────────────┘
```

## 安全策略架构

```
代码输入 → AST 静态分析 → 策略检查 → 沙箱执行 → 资源监控 → 审计日志
              │               │            │           │           │
         语法检查         导入黑名单    OS RLIMIT   内存/CPU    完整记录
         节点检查         调用检测     超时 kill     文件描述符   可追溯
```

## 安全等级

| 等级 | 说明 | 导入策略 | 适用场景 |
|------|------|---------|---------|
| **STRICT** | 纯计算模式 | 白名单（~20 安全模块） | 教学/考试平台 |
| **STANDARD** | 标准沙箱 | 黑名单（禁止危险模块） | Agent 代码执行 |
| **RELAXED** | 开发模式 | 仅过滤明确危险 | 可信用户环境 |

## 测试用例覆盖

| 测试 | Subprocess | Docker | RestrictedPython |
|------|:--:|:--:|:--:|
| 安全代码（斐波那契） | ✅ 通过 | ✅ 通过 | ✅ 通过 |
| 危险导入（os.system） | ✅ 拦截 | ✅ 拦截 | ✅ 拦截 |
| eval() 调用 | ✅ 拦截 | ✅ 拦截 | ✅ 拦截 |
| Shell 命令注入 | ✅ 拦截 | ✅ 拦截 | ✅ 拦截 |
| 死循环 | ✅ 超时 kill | ✅ 超时 kill | ✅ 超时 |
| 内存炸弹 | ✅ RLIMIT | ✅ Cgroup | ⚠️ |

## 项目结构

```
sandbox-demo/
├── main.py                          # 🚀 主入口 (交互式 CLI)
├── requirements.txt
├── README.md
├── src/
│   ├── sandboxes/                   # 🛡️ 三种沙箱实现
│   │   ├── base.py                  #   抽象基类 (模板方法)
│   │   ├── subprocess_sandbox.py    #   Subprocess + RLIMIT
│   │   ├── docker_sandbox.py        #   Docker + Cgroup
│   │   └── restricted_python.py     #   AST 变换 + 受限 builtins
│   ├── policies/                    # 🔒 安全策略
│   │   └── security_policy.py       #   AST 分析 / 导入控制 / 注入检测
│   └── monitor/                     # 📊 资源监控
│       └── resource_monitor.py      #   内存/CPU/FD/线程 实时采样
├── tests/
│   └── test_sandbox.py              # 🧪 45+ 测试用例
└── docs/
    ├── 项目说明.md                   # 项目背景、目标、沙箱选择决策树
    ├── 沙箱技术对比.md               # 三种技术详细对比 + 性能基准
    └── 安全策略设计.md               # 策略体系、威胁模型、安全检查清单
```

## 测试

```bash
# 安装依赖
pip install pytest

# 运行全部测试（无需 Docker）
pytest tests/ -v

# 排除需要 Docker 的测试
pytest tests/ -v -k "not Docker"

# 仅运行安全策略测试
pytest tests/test_sandbox.py::TestSecurityPolicy -v
```

## 适用场景

- 🎓 **教学演示**：三种沙箱技术的可运行对比
- 🤖 **AI Agent 安全**：为 LLM 生成的代码提供执行沙箱
- 🏗️ **代码平台**：多租户 SaaS 平台的代码隔离方案选型参考
- 📐 **安全架构**：从威胁模型到安全策略的完整参考实现
- 🔬 **安全研究**：沙箱逃逸测试和加固研究的基础设施

## 许可

本项目仅供学习、研究和交流目的使用。
