# CAMEL AI 技术说明文档

本文档详细介绍 CAMEL AI 框架在 EcoLLM 项目中的应用，帮助理解其工作原理和实现细节。

---

## 1. CAMEL AI 框架概述

### 1.1 什么是 CAMEL AI？

CAMEL AI（Communicative Agents for "Mind" Exploration of Large Language Model Society）是一个开源的多智能体协作框架。其核心理念是通过**角色扮演**（Role-Playing）让多个 AI 智能体进行自主协作，完成复杂任务。

**官方定义**：CAMEL 是一个支持自主智能体协作的框架，通过为智能体分配不同角色和任务，使其能够进行多轮对话、协商和协作。

### 1.2 为什么选择 CAMEL AI？

在 EcoLLM 项目中，我们选择 CAMEL AI 而非直接调用 LLM API，原因如下：

| 直接调用 LLM API | 使用 CAMEL AI |
|-----------------|---------------|
| 每次调用独立，无上下文 | 内置对话记忆，保持上下文连贯 |
| 需要手动管理对话历史 | 自动管理对话历史 |
| 需要手动处理 system prompt | 通过 ChatAgent 封装 system prompt |
| 无角色扮演能力 | 支持角色扮演，可模拟专家行为 |

**核心优势**：CAMEL AI 的 `ChatAgent` 类提供了**记忆模块**，使得在处理同一个样本的多个 tool calls 时，生成的推理内容能够引用之前的操作，保持逻辑连贯性。

---

## 2. 核心组件：ChatAgent

### 2.1 ChatAgent 是什么？

`ChatAgent` 是 CAMEL AI 的核心类，代表一个具有特定角色和能力的智能体。它封装了：

- **System Message**：定义智能体的角色、能力和行为准则
- **Model**：底层的 LLM（如 DeepSeek-V3）
- **Memory**：对话记忆，存储历史消息

### 2.2 在 EcoLLM 中的使用

```python
from camel.agents import ChatAgent
from camel.messages import BaseMessage
from camel.models import OpenAIModel
from camel.configs.openai_config import ChatGPTConfig

# 1. 配置模型
config = ChatGPTConfig(
    temperature=1.0,  # DeepSeek 推荐：数据抽取/分析场景
    max_tokens=2048
)

# 2. 创建 ChatAgent
agent = ChatAgent(
    system_message=BaseMessage.make_assistant_message(
        role_name="Assistant",
        content="You are an LCA expert..."  # System Prompt
    ),
    model=OpenAIModel(
        model_type="deepseek-chat",
        model_config_dict=config.as_dict(),
        api_key=api_key,
        url="https://api.deepseek.com"
    )
)

# 3. 发送消息并获取响应
user_msg = BaseMessage.make_user_message(
    role_name="User",
    content="Generate reasoning for this action..."
)
response = agent.step(user_msg)
result = response.msg.content
```

### 2.3 记忆模块的工作原理

ChatAgent 的记忆模块是其核心特性：

```
┌─────────────────────────────────────────────────────────────┐
│                      ChatAgent Memory                        │
├─────────────────────────────────────────────────────────────┤
│  Turn 1: User → "Generate reasoning for search_document"    │
│          Agent → "I need to find material data..."          │
├─────────────────────────────────────────────────────────────┤
│  Turn 2: User → "Generate reasoning for record_process_flow"│
│          Agent → "Based on my search, I found Ti-6Al-4V..." │
│                  ↑ 能够引用 Turn 1 的内容                    │
├─────────────────────────────────────────────────────────────┤
│  Turn 3: User → "Generate reasoning for get_session_summary"│
│          Agent → "Now that I've recorded the material..."   │
│                  ↑ 能够引用 Turn 1 和 Turn 2 的内容          │
└─────────────────────────────────────────────────────────────┘
```

**关键操作**：
- `agent.step(msg)`：发送消息，记忆会自动更新
- `agent.clear_memory()`：清空记忆，用于处理新样本

---

## 3. 在 EcoLLM 中的三大应用

### 3.1 应用一：Name/Note 规范化

**脚本**：`improve_name_note_with_camel.py`

**目的**：将专家标注的非标准 LCI 数据规范化为可搜索的标准格式。

**System Prompt 设计**：
```
You are an LCA data standardizer. Refine user drafts into professional LCI records.

## Core Logic: Searchability + Context

LCI databases (like Ecoinvent) work by searching the **material/flow identity** first, 
then filtering by **characteristics**.

Your task: Split user's informal notes into this two-field structure:

### 1. Name Field (Identity for Searching)
- Purpose: Create a searchable, standardized flow name
- Strategy: Use standard industrial terminology (not abbreviations)
- Examples: "Ti64" → "Titanium alloy, Ti-6Al-4V"

### 2. Note Field (Context for Filtering)
- Purpose: Capture characteristics that matter for LCA analysis
- Examples: "Powder, gas atomized, Grade 23"
```

**执行流程**：
```
输入: {
  "name": "Ti6Al4V powder",
  "note": "gas atomized, 15-45μm",
  "category": "Raw Material",
  "value": "2.5 kg"
}
    ↓
构建 Prompt: "Improve this LCI record: name='Ti6Al4V powder', note='gas atomized, 15-45μm'..."
    ↓
调用 ChatAgent.step()
    ↓
输出: {
  "improved_name": "titanium alloy powder, Ti-6Al-4V",
  "improved_note": "gas atomized | particle size: 15-45 μm"
}
```

**特点**：每条记录独立处理，不需要记忆模块（每次调用前清空记忆）。

---

### 3.2 应用二：Reasoning 内容生成

**脚本**：`generate_short_reasoning.py` + `reasoning_helpers.py`

**目的**：为每个 tool call 生成自然的推理内容（`<think>` 标签内的内容）。

**System Prompt 设计**：
```
You are an LCA expert performing LCI data extraction from documents.

## Your Role
Generate first-person reasoning for short extraction tasks. You have access to FULL context.

## Key Principles
1. First-person perspective: Write as if you are performing the extraction
2. Natural thinking: Think out loud, vary your expression
3. Context-aware: Reference previous actions and search results
4. Honest: Express uncertainty or confidence naturally
```

**动态 Prompt 构建**（核心创新）：

与 Name/Note 规范化不同，Reasoning 生成使用**动态 Prompt**，根据当前上下文构建不同的提示词。

```python
def build_dynamic_prompt(previous_messages, current_tool_call, user_query):
    """
    动态构建 Prompt
    
    包含四个核心组件：
    1. 对话历史 (Conversation History)
    2. 当前动作 (Next Action)
    3. 文档证据 (Document Evidence) - 隐含在对话历史中
    4. 工具特定引导 (Tool-Specific Guidance)
    """
    
    # 1. 构建对话历史
    history_text = build_conversation_history(previous_messages)
    
    # 2. 描述下一个动作
    next_action_text = describe_next_action(current_tool_call)
    
    # 3. 检测场景，提供工具特定引导
    if 场景是 "搜索后记录":
        guidance = """
        Generate your internal reasoning that:
        1. Briefly comments on the search results you just received
        2. Explains what you're going to record based on these results
        """
    elif 场景是 "搜索后检查进度":
        guidance = """
        Generate your internal reasoning that:
        1. Briefly comments on the search results you just received
        2. Explains why you want to check the session summary now
        """
    # ... 其他场景
    
    # 4. 组装完整 Prompt
    return f"""
    ## Conversation So Far:
    {history_text}
    
    ## Next Action You Will Take:
    {next_action_text}
    
    ## Your Task:
    {guidance}
    
    **Remember**:
    - Write in first person ("I need to...", "I found...")
    - Be natural and concise (50-180 characters)
    - Reference previous actions if relevant
    """
```

**记忆模块的关键作用**：

```python
# 处理一个样本的多个 tool calls
def generate_reasoning_for_sample(sample):
    # 🔥 清空记忆（每个样本独立）
    self.reasoning_agent.clear_memory()
    
    for i, msg in enumerate(messages):
        if msg.get("role") == "assistant" and msg.get("tool_calls"):
            # 构建动态 Prompt
            prompt = build_dynamic_prompt(
                previous_messages=messages[:i],
                current_tool_call=msg["tool_calls"][0]
            )
            
            # 调用 ChatAgent（记忆会自动累积）
            user_msg = BaseMessage.make_user_message(role_name="User", content=prompt)
            response = self.reasoning_agent.step(user_msg)
            
            # 🔥 记忆保持：下一次调用时，Agent 能"记住"之前生成的推理
            msg["reasoning_content"] = response.msg.content
```

**生成效果示例**：

| Tool Call | 生成的 Reasoning |
|-----------|-----------------|
| `search_document(["titanium", "powder"])` | "I need to find the material input data for this SLM process. Let me search for titanium powder information." |
| `record_process_flow(name="Ti-6Al-4V powder", value=2.5, unit="kg")` | "The search results show Ti-6Al-4V powder consumption is 2.5 kg. I'll record this as a raw material input." |
| `get_session_summary()` | "Now that I've recorded the material input, let me check what other data I still need to extract." |

---

### 3.3 应用三：User Content 生成

**脚本**：`generate_short_reasoning.py`

**目的**：为每个训练样本生成自然的用户请求，替换原始的简单/格式化请求。

**场景区分**：

| 场景 | 用户意图 | 生成策略 |
|-----|---------|---------|
| **Extract** | 请求提取/记录数据 | "Could you help me extract the titanium alloy data..." |
| **QA** | 询问信息 | "Can you tell me about the argon consumption..." |

**Prompt 设计**（Extract 场景）：
```
Generate a natural user request for extracting titanium alloy powder data.

Guidelines:
- Request the assistant to extract/record data
- Natural and conversational
- Keep it simple and direct (15-30 words)

Output ONLY the final request, no thinking process.

Generate the request:
```

**Prompt 设计**（QA 场景）：
```
Generate a natural user request asking about argon, nitrogen, gas in a manufacturing process.

Guidelines:
- Ask about information
- Natural and conversational
- Keep it simple and direct (15-25 words)

Output ONLY the final request, no thinking process.

Generate the request:
```

**特点**：
- 每次生成后清空记忆（`agent.clear_memory()`），确保不受之前生成的影响
- 使用 `"Output ONLY the final request, no thinking process."` 防止 CoT 泄漏

---

## 4. 技术细节

### 4.1 与 DeepSeek API 的集成

CAMEL AI 通过 OpenAI 兼容接口与 DeepSeek 集成：

```python
# 配置环境变量
os.environ["OPENAI_API_KEY"] = api_key
os.environ["OPENAI_API_BASE_URL"] = "https://api.deepseek.com"

# 创建模型
model = OpenAIModel(
    model_type="deepseek-chat",
    model_config_dict=config.as_dict(),
    api_key=api_key,
    url="https://api.deepseek.com"
)
```

### 4.2 温度参数选择

根据 DeepSeek 官方推荐：

| 场景 | 温度 | 说明 |
|-----|------|------|
| 数据抽取/分析 | 1.0 | 需要一定的多样性，但保持准确性 |
| 代码生成 | 0.0 | 需要确定性输出 |
| 创意写作 | 1.3+ | 需要高度多样性 |

我们使用 `temperature=1.0`，在多样性和准确性之间取得平衡。

### 4.3 输出解析与回退机制

对于需要结构化输出的场景（如 Name/Note 规范化），我们实现了自动解析和回退：

```python
def parse_response(response_text):
    try:
        # 尝试解析 JSON
        result = json.loads(response_text)
        return result["improved_name"], result["improved_note"]
    except:
        # 回退：返回原始值
        return original_name, original_note
```

---

## 5. 设计原则：Less is More

在 Prompt 设计中，我们遵循 **Less is More** 原则：

### 5.1 避免过度约束

**❌ 过度约束的 Prompt**：
```
Generate a user request using ONLY these verbs: "extract", "record", "capture", "pull out".
DO NOT use: "find", "search", "look for", "get".
The request MUST start with "Please" or "Could you".
The request MUST be exactly 20-25 words.
```

**✅ 适度引导的 Prompt**：
```
Generate a natural user request for extracting titanium alloy data.

Guidelines:
- Request the assistant to extract/record data
- Natural and conversational
- Keep it simple and direct (15-30 words)
```

### 5.2 意图引导而非形式约束

**核心思想**：告诉 LLM "做什么"（意图），而不是"怎么做"（形式）。

| 约束类型 | 示例 | 效果 |
|---------|------|------|
| 形式约束 | "Use verbs like extract, record" | 限制多样性 |
| 意图引导 | "Request the assistant to extract/record data" | 保持多样性 |

---

## 6. 常见问题

### 6.1 为什么生成的内容有时包含思考过程？

**问题**：生成的 user content 有时会包含 "Hmm, I need to think about..." 这样的思考过程。

**原因**：LLM 的 Chain-of-Thought (CoT) 泄漏。

**解决方案**：在 Prompt 中明确要求：
```
Output ONLY the final request, no thinking process.
```

### 6.2 为什么需要在每个样本开始时清空记忆？

**原因**：样本之间应该是独立的。如果不清空记忆，前一个样本的对话历史会影响当前样本的生成。

```python
# 正确做法
for sample in samples:
    agent.clear_memory()  # 🔥 每个样本开始时清空
    for tool_call in sample["tool_calls"]:
        response = agent.step(...)  # 记忆在样本内累积
```

### 6.3 为什么 User Content 生成后要清空记忆？

**原因**：User Content 生成和 Reasoning 生成是独立的任务。如果不清空，User Content 的生成会影响后续 Reasoning 的生成。

```python
# 生成 User Content
user_content = generate_user_content(...)
agent.clear_memory()  # 🔥 清空，避免影响 Reasoning 生成

# 生成 Reasoning
for tool_call in tool_calls:
    reasoning = generate_reasoning(...)
```

---

## 7. 总结

CAMEL AI 在 EcoLLM 中的核心价值：

| 功能 | 实现方式 | 核心优势 |
|-----|---------|---------|
| Name/Note 规范化 | ChatAgent + 专门 System Prompt | 编码 LCI 数据库搜索逻辑 |
| Reasoning 生成 | ChatAgent + 动态 Prompt + 记忆模块 | 上下文感知，逻辑连贯 |
| User Content 生成 | ChatAgent + 场景区分 | 自然多样，场景适配 |

**核心创新**：
1. **动态 Prompt 构建**：根据对话历史和当前工具动态生成提示词
2. **记忆模块利用**：使生成的推理能够引用之前的操作
3. **场景感知生成**：区分 Extract 和 QA 场景，生成适配的内容
4. **Less is More 原则**：意图引导而非形式约束，保持生成多样性
