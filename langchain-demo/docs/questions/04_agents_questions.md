# Demo 04 启发性问题 -- Agents

## 基础理解

1. Agent 和普通的 Chain 有什么本质区别?
   什么场景应该用 Agent，什么场景用 Chain 就够了?

2. ReAct (Reasoning + Acting) 和 Function Calling 有什么区别?
   LangChain 的 `create_react_agent` 底层是如何与 OpenAI 的 Function Calling
   结合的?

3. Tool 的 docstring 是如何被 Agent 使用的?
   Agent 是怎样"看到"可用工具列表的?

## 深入思考

4. 如果 Agent 连续调用同一个工具 10 次还没有得到满意结果，会发生什么?
   如何设置最大迭代次数和超时?

5. 在 ReAct 循环中，LLM 的推理步骤 (Thought) 和行动步骤 (Action)
   是否共享同一个 context window? 这会导致什么问题?

6. Agent 的"幻觉"有什么特殊的表现形式?
   比如 Agent 可能"假装"调用了一个不存在的工具，为什么会这样?

## 实战挑战

7. 设计一个工具，让 Agent 可以执行 SQL 查询并返回结果。
   需要考虑: 安全问题、错误处理、大型结果集的截断。

8. 如果多个工具的功能有重叠 (比如 calculator 和 wolfram_alpha 都能计算)，
   Agent 如何选择? 如何引导 Agent 优先使用某个工具?

9. 如何让 Agent 在调用工具出错时自动重试，而不是直接给出错误答案?
   这与 LLM 层面的 retry 有什么不同?
