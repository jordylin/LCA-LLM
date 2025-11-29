# Reasoning 生成改进方案

## 📋 文档概述

本文档详细说明了如何改进 `generate_think_with_camel.py` 中的 reasoning 生成机制，使 CAMEL AI 能够：
1. **代入 LLM 角色**：理解自己在对话流程中的位置
2. **承上启下**：基于前面的 tool_responses，解释后续的 tool_calls
3. **自然引用上下文**：通过记忆机制自动引用前面的动作
4. **生成真实推理**：符合实际流程，避免过拟合固定句式

---

## 🔑 核心理解：导出脚本是"模拟"

### **实际 LLM 运行时流程**
```
1. LLM 推理: "首先，我得先找 functional unit..."
2. LLM 调用: <tool call> search_document(...)
3. 系统返回: <tool response> Found 3 chunks...
4. LLM 推理: "我看到了X，我要记录Y..."
5. LLM 调用: <tool call> record_process_flow(...)
6. 系统返回: <tool response> Recorded successfully
7. 继续循环...
```

### **导出脚本的模拟（训练数据生成）**
```json
{
  "role": "assistant",
  "reasoning_content": "[需要生成] 首先，我得先找 functional unit...",
  "tool_calls": [{"name": "search_document", ...}]  ← 已经存在
}
↓
{
  "role": "tool",
  "content": "Found 3 chunks..."  ← 已经存在
}
↓
{
  "role": "assistant",
  "reasoning_content": "[需要生成] 我看到了X，我要记录Y...",
  "tool_calls": [{"name": "record_process_flow", ...}]  ← 已经存在
}
```

### **关键洞察**

1. **所有 tool_calls 和 tool_responses 已经存在**
   - 导出脚本已经生成了完整的对话流程
   - 我们只是填充 reasoning_content

2. **Reasoning 的作用是"承上启下"**
   - **承上**：基于前面的 tool_responses（"我看到了X"）
   - **启下**：解释后续的 tool_calls 的原因（"所以我要做Y"）

3. **Agent 需要"依赖后续信息"**
   - ✅ 必须告诉 Agent 后续会执行什么 tool_call
   - ✅ 但要求 Agent 解释"为什么"，而不是"做什么"
   - ✅ 这样 reasoning 才能和 tool_call 对得上

4. **"假装不知道"的真实含义**
   - 不是说 Agent 真的不知道后续的 tool_call
   - 而是说 Reasoning 的语气要像"决策"，而不是"陈述事实"
   - 例如："我要搜索..."（决策）vs "我搜索了..."（陈述）

---

## 🎯 核心问题

### 当前问题 1：Agent 记忆跨 sample 累积

**问题描述**：
```python
# 当前代码
def __init__(self, api_key: str):
    self.agent = ChatAgent(...)  # 创建一次 Agent

def generate_think_for_messages(self, sample: Dict):
    for msg in messages:
        response = self.agent.step(user_msg)  # ❌ Agent 记忆会累积
```

**后果**：
- Sample A 的对话会影响 Sample B 的生成
- Agent 会"记住"不该记住的内容

---

### 当前问题 2：Prompt 过于冗杂

**问题描述**：
```python
# 当前 prompt（Line 756-778）
prompt = f"""
Generate a TWO-PART reasoning for this Smart Skip scenario:
**Examples:**
- "Post-processing energy not found. Now searching for feedstock energy."
- "Feedstock energy already recorded. Moving to gas inputs."
...
"""
```

**后果**：
- 提供固定例子 → 过拟合
- 强制格式 → 不自然
- 过多指令 → 限制 Agent 发挥

---

### 当前问题 3：Agent 不知道后续的 tool_call

**问题描述**：
Agent 不知道后续会执行什么 tool_call，导致生成的 reasoning 和实际的 tool_call 对不上。

**示例**：
```python
# 当前代码：只看前面的内容
previous_messages = messages[:current_index]

prompt = f"""
## Conversation So Far:
{previous_messages}

## Task:
Generate your internal reasoning for the NEXT action.
"""
```

**问题**：
- Agent 不知道后续会调用什么工具
- 生成的 reasoning 可能和后续的 tool_call **对不上**
- 例如：Reasoning 说"我要搜索能源数据"，但后续 tool_call 是记录原料

**根本原因**：
- 导出脚本已经生成了完整的对话流程（tool_calls 已存在）
- 但我们没有告诉 Agent 后续会执行什么
- Reasoning 需要"承上启下"，必须和后续的 tool_call 对应

---

## 💡 改进方案总览

### 核心思路

1. **启用记忆机制**：让 Agent 记住同一个 sample 内前面生成的 reasoning
2. **动态构建 Prompt**：每次生成 reasoning 时，根据当前位置自动构建新的 prompt
3. **告诉 Agent 后续动作**：在 prompt 中包含后续的 tool_call，但要求 Agent 解释"为什么"
4. **简化 System Prompt**：移除固定例子和格式要求，让 Agent 自由发挥

---

## 📋 详细改进方案

### 改进 1：启用记忆机制 + 每个 sample 清空

#### 原理

CAMEL AI 的 `ChatAgent` 有内置记忆系统：
- `agent.chat_history`：保存所有对话历史
- `agent.memory`：`ChatHistoryMemory` 类型
- `agent.step()`：自动记住每次对话

#### 实现

```python
def generate_think_for_messages(self, sample: Dict) -> Dict:
    messages = sample.get("messages", [])
    
    # 🔥 关键改进：每个 sample 开始时清空记忆
    self.agent.clear_memory()
    
    for i, msg in enumerate(messages):
        if msg.get("role") == "assistant":
            # 构建 prompt
            prompt = self._build_prompt_from_messages(messages, i, ...)
            
            user_msg = BaseMessage.make_user_message(
                role_name="User",
                content=prompt
            )
            
            # 🔥 Agent 自动记住这次对话
            response = self.agent.step(user_msg)
            reasoning = response.msg.content.strip()
            
            msg["reasoning_content"] = reasoning
    
    return sample
```

#### 效果

- ✅ 每个 sample 独立，互不干扰
- ✅ 同一个 sample 内，Agent 记住前面的 reasoning
- ✅ 生成更连贯、更自然

---

### 改进 2：动态构建 Prompt + 告诉 Agent 后续动作

#### 核心概念：什么是"动态 Prompt"？

**不是**：
- ❌ 每次有新数据就手动修改 CAMEL AI 的 prompt
- ❌ 固定的 prompt 模板

**而是**：
- ✅ **每次生成 reasoning 时，根据当前位置自动构建一个新的 prompt**
- ✅ Prompt 的内容根据当前的 messages 数组动态生成
- ✅ 通过 `agent.step(dynamic_prompt)` 发送不同的 prompt

#### 完整流程

```python
def generate_think_for_messages(self, sample: Dict) -> Dict:
    messages = sample.get("messages", [])
    
    # Step 1: 清空记忆
    self.agent.clear_memory()
    
    # Step 2: 遍历每个 assistant 消息
    for i, msg in enumerate(messages):
        if msg.get("role") == "assistant":
            
            # Step 3: 🔥 为当前位置动态构建 prompt
            prompt = self._build_prompt_from_messages(messages, i, ...)
            
            # Step 4: 发送给 CAMEL AI
            user_msg = BaseMessage.make_user_message(
                role_name="User",
                content=prompt  # 🔥 动态生成的 prompt
            )
            
            # Step 5: Agent 生成 reasoning（自动记住这次对话）
            response = self.agent.step(user_msg)
            reasoning = response.msg.content.strip()
            
            # Step 6: 填充到 messages
            msg["reasoning_content"] = reasoning
    
    return sample
```

#### 关键：告诉 Agent 后续的 tool_call

**为什么要告诉 Agent 后续的 tool_call？**

因为：
1. ✅ 导出脚本已经生成了完整的对话流程（tool_calls 已存在）
2. ✅ Reasoning 需要"承上启下"，必须和后续的 tool_call 对应
3. ✅ 如果不告诉 Agent，生成的 reasoning 可能和实际的 tool_call 对不上

**Reasoning 的位置**：
```
┌─────────────────────────────────────────────┐
│ User: "Extract LCI data..."                 │
├─────────────────────────────────────────────┤
│ Tool Response: (process_document 结果)      │
├─────────────────────────────────────────────┤
│ Assistant:                                  │
│   <think> [REASONING] </think>  ← 当前位置  │
│   <tool_call> search_document(...) </tool>  │
├─────────────────────────────────────────────┤
│ Tool Response: Found 5 chunks...            │
├─────────────────────────────────────────────┤
│ Assistant:                                  │
│   <think> [REASONING] </think>  ← 当前位置  │
│   <tool_call> record_flow(...) </tool>      │
└─────────────────────────────────────────────┘
```

**关键设计**：
- ✅ 可以看到：`messages[0:current_index]`（前面所有内容）
- ✅ **必须看到**：`messages[current_index]` 的 `tool_calls`（后续要执行的动作）
- ❌ 不能看到：`messages[current_index+1:]`（更后面的内容）

**为什么必须看到当前的 tool_calls？**
- 因为 Reasoning 要解释"为什么执行这个 tool_call"
- 如果不知道要执行什么，就无法生成对应的 reasoning

#### 实现

```python
def _build_prompt_from_messages(
    self, 
    messages: List[Dict], 
    current_index: int,
    user_query: str,
    chunk_preview: str
) -> str:
    """
    为 messages[current_index] 生成 reasoning
    
    严格遵循时间顺序：只能看到前面的内容
    """
    
    current_msg = messages[current_index]
    
    # 🔥 关键：只提取前面的 messages
    previous_messages = messages[:current_index]
    
    # 构建对话历史
    history_lines = []
    
    for msg in previous_messages:
        role = msg.get("role")
        
        if role == "user":
            content = msg.get("content", "")[:300]
            history_lines.append(f"**User**: {content}")
        
        elif role == "tool":
            # Tool Response
            tool_name = msg.get("name", "unknown")
            content = msg.get("content", "")
            summary = self._summarize_tool_response(tool_name, content)
            history_lines.append(f"**Tool Response ({tool_name})**: {summary}")
        
        elif role == "assistant":
            # 前面的 Assistant 消息
            reasoning = msg.get("reasoning_content", "")
            tool_calls = msg.get("tool_calls", [])
            
            if reasoning:
                # 清理 placeholder
                reasoning_clean = re.sub(
                    r'\[SMART_SKIP_PLACEHOLDER:.*?\]', '', reasoning
                ).strip()
                if reasoning_clean:
                    history_lines.append(f"**Your Reasoning**: {reasoning_clean}")
            
            if tool_calls:
                for tc in tool_calls:
                    tool_desc = self._describe_tool_call(tc)
                    history_lines.append(f"**Your Action**: {tool_desc}")
    
    # 构建 prompt
    history_text = "\n".join(history_lines) if history_lines else "(No previous actions)"
    
    prompt = f"""You are an LLM agent performing LCI data extraction.

## Conversation So Far:
{history_text}

## Task:
Generate your internal reasoning for the NEXT action.

**Guidelines**:
- Explain your thought process and strategy
- Reference previous results if relevant
- Do NOT mention specific tool parameters (you haven't decided them yet)
- Keep it concise (50-180 characters)

Generate only the reasoning:"""
    
    return prompt
```

#### 效果

**示例 1：第一次搜索**

**Agent 看到的 Prompt**：
```
## Conversation So Far:
**User**: Extract LCI data from this document about 316L powder production.
**Tool Response (process_document)**: Document processed, session: sess_001

## Task:
Generate your internal reasoning for the NEXT action.
```

**Agent 生成**：
```
"Need to search for raw material data. Starting with powder and material-related terms."
```

**关键**：
- ✅ 没有提到具体的 queries（因为还没决定）
- ✅ 只说明策略（search for raw material data）

---

**示例 2：记录数据**

**Agent 看到的 Prompt**：
```
## Conversation So Far:
**User**: Extract LCI data from this document about 316L powder production.
**Tool Response (process_document)**: Document processed
**Your Reasoning**: Need to search for raw material data...
**Your Action**: search_document(queries=["powder", "material", "316L"])
**Tool Response (search_document)**: Found 1 chunk:
  Chunk 7: "316L: 4.11 kg"

## Task:
Generate your internal reasoning for the NEXT action.
```

**Agent 生成**：
```
"Found 316L steel with quantity 4.11 kg in chunk 7. Recording this as raw material input."
```

**关键**：
- ✅ 引用了前面的搜索结果（chunk 7）
- ✅ 说明要记录数据，但没有提到具体参数
- ✅ 符合时间顺序

---

### 改进 3：简化 Prompt，移除固定句式

#### 原理

**当前问题**：
```python
# 固定例子 → 过拟合
**Examples:**
- "Post-processing energy not found. Now searching for feedstock energy."
- "Feedstock energy already recorded. Moving to gas inputs."
```

**改进思路**：
- ❌ 不提供固定例子
- ✅ 只提供必要的上下文信息
- ✅ 让 Agent 自由发挥

#### 实现

**System Prompt（全局，一次性）**：
```python
def _get_system_prompt(self) -> str:
    return """You are an expert LCA assistant generating reasoning for LCI data extraction.

## Your Role
You are the LLM agent performing the extraction. Generate your internal thought process 
explaining WHY you chose each action.

## Key Principles
1. **Natural thinking**: Write as if thinking out loud, not following templates
2. **Context-aware**: Reference previous actions naturally when relevant
3. **Concise**: 50-180 characters, first-person perspective
4. **Honest**: Express uncertainty or confidence naturally

## LCI Categories (for reference)
- **Input**: Raw Material, Process Energy, Post-processing Energy, Feedstock Energy, Gas, Cooling Media
- **Output**: Product, Recovered Material, Waste, Emission
- **Scope**: Functional Unit

Generate only the reasoning content, no tags or labels.
"""
```

**User Prompt（每次调用，简洁）**：
```python
# 见"改进 2"的实现
```

#### 效果

**改进前**（固定句式）：
```
"Post-processing energy not found. Now searching for feedstock energy."
```

**改进后**（自然推理）：
```
"Post-processing energy not found in the search results. Now checking for feedstock 
energy inputs since I've already recorded process energy."
```

**优势**：
- ✅ 更自然、更多样
- ✅ 自动引用前面的动作（"I've already recorded process energy"）
- ✅ 避免过拟合

---

### 改进 4：辅助函数

#### `_summarize_tool_response`：简化 Tool Response

```python
def _summarize_tool_response(self, tool_name: str, content: str) -> str:
    """简化 tool response（显示完整信息）"""
    
    try:
        data = json.loads(content)
    except:
        return content[:500]  # 🔥 增加显示长度
    
    if tool_name == "search_document":
        chunks = data.get("chunks", [])
        if not chunks:
            return "No results found"
        
        summaries = []
        for chunk in chunks:  # 🔥 显示全部 chunks
            chunk_id = chunk.get("chunk_id", "?")
            preview = chunk.get("content", "")[:200]  # 🔥 增加预览长度
            summaries.append(f"Chunk {chunk_id}: {preview}")
        
        return f"Found {len(chunks)} chunks:\n  " + "\n  ".join(summaries)
    
    elif tool_name == "process_document":
        session_id = data.get("session_id", "unknown")
        return f"Document processed, session: {session_id}"
    
    elif tool_name == "record_process_flow":
        return "Data recorded successfully"
    
    elif tool_name == "get_session_summary":
        completeness = data.get("completeness_score", 0)
        missing = data.get("missing_categories", [])
        return f"Completeness: {completeness}%, Missing: {missing[:3]}"
    
    return str(data)[:200]
```

#### `_describe_tool_call`：描述 Tool Call

```python
def _describe_tool_call(self, tool_call: Dict) -> str:
    """描述 tool call（显示完整信息）"""
    
    tool_name = tool_call.get("name")
    args = tool_call.get("arguments", {})
    
    if tool_name == "search_document":
        queries = args.get("queries", [])
        return f"search_document(queries={queries})"  # 🔥 显示全部
    
    elif tool_name == "record_process_flow":
        category = args.get("category")
        name = args.get("name")
        value = args.get("value")
        unit = args.get("unit")
        return f"record_process_flow({category}: {name} = {value} {unit})"
    
    elif tool_name == "get_session_summary":
        return "get_session_summary()"
    
    return f"{tool_name}(...)"
```

---

## 🎬 动态 Prompt 示例

### 示例：同一个 sample 的不同位置，prompt 不同

#### **位置 1：第一次搜索（index=2）**

**messages[0:3]**：
```json
[
  {"role": "user", "content": "Extract LCI data..."},
  {"role": "tool", "name": "process_document", "content": "..."},
  {"role": "assistant", "tool_calls": [{"name": "search_document", "arguments": {"queries": ["functional", "unit"]}}]}
]
```

**动态生成的 Prompt 1**：
```
You are an LLM agent performing LCI data extraction.

## Conversation So Far:
**User**: Extract LCI data from this document about 316L powder production.
**Tool Response (process_document)**: Document processed, session: sess_001

## Next Action You Will Take:
You will search the document for: functional, unit

## Task:
Generate your internal reasoning explaining WHY you chose this action.

Generate only the reasoning:
```

**Agent 生成**：
```
"First, I need to establish the functional unit as the foundation of this LCA. Searching for product and unit definitions."
```

---

#### **位置 2：记录数据（index=4）**

**messages[0:5]**：
```json
[
  {"role": "user", "content": "Extract LCI data..."},
  {"role": "tool", "name": "process_document", "content": "..."},
  {"role": "assistant", "reasoning_content": "First, I need to...", "tool_calls": [...]},
  {"role": "tool", "name": "search_document", "content": "{\"chunks\": [...]}"},
  {"role": "assistant", "tool_calls": [{"name": "record_process_flow", "arguments": {...}}]}
]
```

**动态生成的 Prompt 2**：
```
You are an LLM agent performing LCI data extraction.

## Conversation So Far:
**User**: Extract LCI data from this document about 316L powder production.
**Tool Response (process_document)**: Document processed, session: sess_001
**Your Reasoning**: First, I need to establish the functional unit...
**Your Action**: search_document(queries=["functional", "unit"])
**Tool Response (search_document)**: Found 2 chunks:
  Chunk 5: "Functional unit: 1 kg of 316L powder"
  Chunk 7: "Product: 316L stainless steel powder"

## Next Action You Will Take:
You will record: Functional Unit - 1 kg of 316L powder (1.0 kg)

## Task:
Generate your internal reasoning explaining WHY you chose this action.

Generate only the reasoning:
```

**Agent 生成**：
```
"Found the functional unit definition in chunk 5: 1 kg of 316L powder. Recording this as the scope foundation for the LCA."
```

**关键观察**：
- ✅ Prompt 1 和 Prompt 2 **完全不同**
- ✅ Prompt 2 包含了 Prompt 1 生成的 reasoning（"First, I need to..."）
- ✅ 每次都是**自动生成**的，不需要手动修改
- ✅ Agent 通过记忆自然引用前面的内容

---

## 📊 改进效果对比

### 场景 1：第一次搜索

| 维度 | 改进前 | 改进后 |
|------|--------|--------|
| **Prompt** | 冗长，包含固定例子 | 简洁，只提供上下文 |
| **Reasoning** | "Searching for raw material data." | "Need to search for raw material data. Starting with powder and material-related terms to find 316L steel inputs." |
| **问题** | 过于简单，缺乏上下文 | ✅ 自然、详细、符合流程 |

---

### 场景 2：Smart Skip + Search

| 维度 | 改进前 | 改进后 |
|------|--------|--------|
| **Prompt** | 固定格式："[Why skip]. [Now searching for {category}]." | 只提供事实：Skipping X (reason), Searching for: keywords |
| **Reasoning** | "Post-processing energy not found. Now searching for feedstock energy." | "Post-processing energy not found in the search results. Now checking for feedstock energy inputs since I've already recorded process energy." |
| **问题** | 模仿例子，过拟合 | ✅ 自然引用前面的动作，更连贯 |

---

### 场景 3：连续记录（同一 chunk）

| 维度 | 改进前 | 改进后 |
|------|--------|--------|
| **上下文** | 不知道前面记录了什么 | ✅ 通过记忆知道前面的动作 |
| **Reasoning** | "Recording gas input data." | "This argon data is from the same chunk as the 316L I just recorded. Recording it as a gas input." |
| **问题** | 缺乏连贯性 | ✅ 自然引用，连贯性强 |

---

## 🔧 实施步骤

### Step 1: 修改 `generate_think_for_messages`

**位置**：Line 360-389

**改动**：
1. 添加 `self.agent.clear_memory()` 在循环开始前
2. 调用新的 `_build_prompt_from_messages` 方法

```python
def generate_think_for_messages(self, sample: Dict) -> Dict:
    messages = sample.get("messages", [])
    
    # 🔥 新增：清空记忆
    self.agent.clear_memory()
    
    # ... 其他代码保持不变 ...
    
    for i, msg in enumerate(messages):
        if msg.get("role") == "assistant":
            # 🔥 调用新的 prompt 构建方法
            prompt = self._build_prompt_from_messages(
                messages, i, user_query, chunk_preview
            )
            
            # ... 其他代码保持不变 ...
```

---

### Step 2: 重写 `_build_prompt_from_messages`

**位置**：Line 430-519

**改动**：
1. 移除所有场景检测逻辑
2. 移除固定句式和例子
3. 只提取 `messages[:current_index]` 的内容
4. 构建简洁的 prompt

```python
def _build_prompt_from_messages(
    self, 
    messages: List[Dict], 
    current_index: int,
    user_query: str,
    chunk_preview: str
) -> str:
    """见"改进 2"的完整实现"""
    # ... (见上文)
```

---

### Step 3: 添加辅助函数

**位置**：新增方法

**改动**：
1. 添加 `_summarize_tool_response`
2. 添加 `_describe_tool_call`

```python
# 见"改进 4"的完整实现
```

---

### Step 4: 更新 System Prompt

**位置**：Line 30-109（`__init__` 方法）

**改动**：
1. 简化 system prompt
2. 移除固定例子

```python
def __init__(self, api_key: str, model_name: str = "deepseek-chat"):
    # ... 其他代码 ...
    
    system_prompt = self._get_system_prompt()  # 使用新的 system prompt
    
    # ... 其他代码 ...
```

---

## ✅ 预期效果

### 代码层面
- ✅ 减少 200+ 行代码（移除场景检测和固定句式）
- ✅ 更清晰、更易维护
- ✅ 更容易扩展到新场景

### 生成质量
- ✅ 更自然、更多样
- ✅ 自动引用前面的动作
- ✅ 避免过拟合固定句式
- ✅ 符合时间顺序，不超前

### 训练数据
- ✅ 更真实的 reasoning
- ✅ 更好的上下文连贯性
- ✅ 更适合微调 LLM

---

## 🚀 下一步

1. **实现改进**：修改 `generate_think_with_camel.py`
2. **测试验证**：在 `full_001_with_think.json` 上测试
3. **批量生成**：使用 `batch_process_full_dialogues.py` 批量处理
4. **质量评估**：对比改进前后的 reasoning 质量

---

## 📝 附录：关键代码位置

| 功能 | 文件 | 行号 |
|------|------|------|
| `generate_think_for_messages` | `generate_think_with_camel.py` | 360-389 |
| `_build_prompt_from_messages` | `generate_think_with_camel.py` | 430-519 |
| System Prompt | `generate_think_with_camel.py` | 30-109 |
| Smart Skip 检测 | `generate_think_with_camel.py` | 140-182 |
| 关键词映射 | `generate_think_with_camel.py` | 729-746 |

---

**文档版本**：v1.0  
**创建时间**：2025-11-25  
**作者**：Cascade AI
