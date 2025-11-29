# Reasoning 生成指南

## 📋 文档概述

本文档说明如何使用 CAMEL AI 为训练数据生成高质量的 reasoning 内容。

**更新时间**：2025-11-25  
**版本**：v6.0

---

## 🎯 核心目标

为导出的训练数据（`full_xxx_exported.json`）中的每个 `assistant` 消息生成 `reasoning_content`，使其：

1. **第一人称代入**：使用 "I need to...", "I found..." 等第一人称表达
2. **自然连贯**：通过记忆机制自动引用前面的动作
3. **符合流程**：reasoning 解释"为什么"执行后续的 tool_call
4. **简洁专业**：50-180 字符，专注于数据提取决策

---

## 🔧 技术架构

### 核心组件

```
generate_think_with_camel.py
├── ThinkGenerator (主类)
│   ├── CAMEL AI ChatAgent (带记忆)
│   ├── DeepSeek API (deepseek-chat)
│   └── System Prompt (第一人称引导)
│
└── reasoning_helpers.py (辅助函数)
    ├── build_dynamic_prompt() (动态构建 prompt)
    ├── build_conversation_history() (构建对话历史)
    ├── describe_next_action() (描述下一步动作)
    └── summarize_tool_response() (简化 tool response)
```

### 关键特性

1. **记忆机制**：
   - 每个 sample 开始时清空记忆（`agent.clear_memory()`）
   - 同一个 sample 内，Agent 自动记住前面生成的 reasoning
   - 实现自然的上下文引用

2. **动态 Prompt**：
   - 每次生成 reasoning 时，根据当前位置动态构建新的 prompt
   - Prompt 包含：前面的对话历史 + 后续要执行的 tool_call
   - Agent 解释"为什么"执行这个 tool_call

3. **完整信息**：
   - 不截断 queries、chunks 等信息
   - Agent 看到完整的上下文

---

## 🚀 执行流程

### 1. 初始化

```python
generator = ThinkGenerator(api_key="sk-xxx")
```

**内部操作**：
- 创建 CAMEL AI `ChatAgent`
- 配置 DeepSeek API
- 加载 System Prompt

### 2. 处理单个 Sample

```python
result = generator.generate_think_for_messages(sample)
```

**执行步骤**：

#### Step 1: 清空记忆
```python
self.agent.clear_memory()
```
- 确保每个 sample 独立
- 避免跨 sample 的信息污染

#### Step 2: 填充 User Content（如果为空）
```python
if messages[1].get("content") == "":
    messages[1]["content"] = self._generate_user_content_for_full_dialogue()
```
- 生成简单的用户请求（如 "Please help me extract the LCI data from this document."）

#### Step 3: 遍历每个 Assistant 消息

```python
for i, msg in enumerate(messages):
    if msg.get("role") == "assistant":
        # 提取前面的对话历史
        previous_messages = messages[:i]
        
        # 获取当前的 tool_call
        tool_calls = msg.get("tool_calls", [])
        
        # 动态构建 prompt
        if tool_calls:
            prompt = build_dynamic_prompt(
                previous_messages=previous_messages,
                current_tool_call=tool_calls[0],
                user_query=user_query
            )
        else:
            # Smart Skip Pure 或 Final Response
            prompt = build_special_prompt(...)
        
        # 发送给 CAMEL AI
        response = self.agent.step(user_msg)
        
        # 填充 reasoning_content
        msg["reasoning_content"] = response.msg.content.strip()
```

---

## 📝 Prompt 结构

### System Prompt（全局）

```
You are an LCA expert performing LCI data extraction from documents.

## Your Role
You are actively extracting data. Generate your internal reasoning explaining WHY you choose each action.

## LCI Categories (11 types)
**Input**: Raw Material, Process Energy, Post-processing Energy, Feedstock Energy, Gas, Cooling Media
**Output**: Product, Recovered Material, Waste, Emission
**Scope**: Functional Unit

## Standard Workflow
1. **Functional Unit First**: Search for product, quantity, process to establish the study basis
2. **Input Flows**: Extract materials, energy, gas, cooling media
3. **Output Flows**: Extract product, recovered materials, waste, emissions
4. **Validation** (optional): Check completeness

## Key Principles
1. **First-person perspective**: Write as if you are performing the extraction ("I need to...", "I found...")
2. **Natural thinking**: Think out loud, don't follow templates
3. **Context-aware**: Reference previous actions when relevant
4. **Concise**: 50-180 characters
5. **Honest**: Express uncertainty or confidence naturally

Generate only the reasoning content, no tags or labels.
```

### User Prompt（动态生成）

#### 场景 1：有 tool_calls（普通场景）

```
You are an LCA expert performing LCI data extraction.

## Conversation So Far:
**User**: Extract LCI data from this document about 316L powder production.
**Tool Response (process_document)**: Document processed, session: sess_001

## Next Action You Will Take:
Search the document for: functional, unit

## Your Task:
Generate your internal reasoning explaining WHY you chose this action.

**Remember**:
- Write in first person ("I need to...", "I found...")
- Be natural and concise (50-180 characters)
- Reference previous actions if relevant
- Focus on your thought process, not the action details

Generate only the reasoning:
```

#### 场景 2：Smart Skip Pure（无 tool_calls）

```
You are an LCA expert performing LCI data extraction.

## Conversation So Far:
[对话历史...]

## Your Decision:
Skip recording Post-processing Energy (not found in the document)

## Your Task:
Generate your reasoning explaining why you're skipping this category.

**Remember**:
- Write in first person ("I found...", "I already recorded...")
- Be concise (50-150 characters)
- Explain the skip reason naturally

Generate only the reasoning:
```

#### 场景 3：Final Response（无 tool_calls）

```
You are an LCA expert performing LCI data extraction.

## Conversation So Far:
[对话历史...]

## Your Task:
Generate your final summary explaining what you have accomplished.

**Remember**:
- Write in first person ("I have extracted...", "I recorded...")
- Be concise (50-180 characters)
- Summarize the key data extracted

Generate only the reasoning:
```

---

## 🎬 实际示例

### 示例 1：第一次搜索（Functional Unit）

**输入**：
```json
{
  "role": "assistant",
  "reasoning_content": "",
  "tool_calls": [{
    "name": "search_document",
    "arguments": {
      "queries": ["manufactured", "part", "product", "kg", "316L", "SLM"]
    }
  }]
}
```

**动态生成的 Prompt**：
```
## Conversation So Far:
**User**: Extract LCI data from this document about 316L powder production.
**Tool Response (process_document)**: Document processed, session: sess_001

## Next Action You Will Take:
Search the document for: manufactured, part, product, kg, 316L, SLM

## Your Task:
Generate your internal reasoning explaining WHY you chose this action.
```

**生成的 Reasoning**：
```
"I need to find the functional unit first. I'll search for the product, its quantity, and the manufacturing process to establish the study's basis."
```

**特点**：
- ✅ 第一人称（"I need to..."）
- ✅ 说明了为什么（establish the study's basis）
- ✅ 符合工作流程（functional unit first）

---

### 示例 2：记录数据（引用前面的动作）

**输入**：
```json
{
  "role": "assistant",
  "reasoning_content": "",
  "tool_calls": [{
    "name": "record_process_flow",
    "arguments": {
      "category": "Raw Material",
      "name": "Stainless Steel",
      "value": 4.11,
      "unit": "kg"
    }
  }]
}
```

**动态生成的 Prompt**：
```
## Conversation So Far:
**User**: Extract LCI data...
**Tool Response (process_document)**: Document processed...
**Your Previous Reasoning**: I need to find the functional unit first...
**Your Previous Action**: Search the document for: manufactured, part, product...
**Tool Response (search_document)**: Found 10 chunks:
  - Chunk 6: [完整内容...]
  - Chunk 10: [完整内容...]
  ...
**Your Previous Reasoning**: I have the functional unit. Now I need to find the raw material inputs...
**Your Previous Action**: Search the document for: powder, material, feedstock...
**Tool Response (search_document)**: Found 10 chunks:
  - Chunk 6: [完整内容...]
  ...

## Next Action You Will Take:
Record Input flow - Raw Material: Stainless Steel (4.11 kg)

## Your Task:
Generate your internal reasoning explaining WHY you chose this action.
```

**生成的 Reasoning**：
```
"I found the base material quantity in the table. I need to record this 4.11 kg of stainless steel as a raw material input for the LCI."
```

**特点**：
- ✅ 引用了搜索结果（"found in the table"）
- ✅ 通过 Agent 记忆自动实现（不需要手动提取）
- ✅ 说明了要记录什么

---

### 示例 3：Final Response

**输入**：
```json
{
  "role": "assistant",
  "reasoning_content": "",
  "content": ""
}
```

**动态生成的 Prompt**：
```
## Conversation So Far:
[完整的对话历史，包括所有 reasoning 和 tool responses]

## Your Task:
Generate your final summary explaining what you have accomplished.
```

**生成的 Reasoning**：
```
"I have successfully extracted comprehensive LCI data including functional unit, material inputs, energy consumption, product output, recovered materials, and waste streams."
```

**特点**：
- ✅ 第一人称（"I have successfully extracted"）
- ✅ 总结了所有提取的内容
- ✅ 简洁、专业

---

## 📊 场景覆盖

| 场景 | Prompt 类型 | 示例 Reasoning |
|------|------------|----------------|
| **search_document** | 动态 Prompt（有 tool_call） | "I need to find the functional unit first..." |
| **record_process_flow** | 动态 Prompt（有 tool_call） | "I found the base material quantity in the table..." |
| **define_lca_scope** | 动态 Prompt（有 tool_call） | "I found the product description. Now I need to define the functional unit..." |
| **get_session_summary** | 动态 Prompt（有 tool_call） | "I didn't find any emissions data. Let me check my progress..." |
| **Smart Skip Pure** | 特殊 Prompt（无 tool_call） | "Post-processing energy not found in the search results..." |
| **Final Response** | 特殊 Prompt（无 tool_call） | "I have successfully extracted comprehensive LCI data..." |

---

## 🔍 辅助函数说明

### `build_dynamic_prompt()`

**功能**：动态构建 Prompt

**输入**：
- `previous_messages`: 当前位置之前的所有 messages
- `current_tool_call`: 当前要执行的 tool_call
- `user_query`: 用户的初始请求（可选）

**输出**：完整的 prompt 字符串

**内部逻辑**：
1. 调用 `build_conversation_history()` 构建对话历史
2. 调用 `describe_next_action()` 描述下一步动作
3. 组装成完整的 prompt

---

### `build_conversation_history()`

**功能**：构建对话历史摘要

**处理逻辑**：
- **User 消息**：显示前 200 字符
- **Tool Response**：调用 `summarize_tool_response()` 简化
- **Assistant 消息**：显示 reasoning + tool_call 描述

**示例输出**：
```
**User**: Extract LCI data from this document...
**Tool Response (process_document)**: Document processed, session: sess_001
**Your Previous Reasoning**: I need to find the functional unit first...
**Your Previous Action**: Search the document for: manufactured, part, product...
**Tool Response (search_document)**: Found 10 chunks:
  - Chunk 6: [完整内容]
  - Chunk 10: [完整内容]
  ...
```

---

### `summarize_tool_response()`

**功能**：格式化 Tool Response，使其易读（不是截断内容）

**处理逻辑**：
- `search_document`: 
  - 原始格式：`{"success": true, "results": [{"chunk_id": 6, "content": "..."}]}`
  - 格式化后：`"Found 10 chunks:\n  - Chunk 6: [完整内容]\n  - Chunk 10: [完整内容]"`
  - ✅ 显示所有 chunks 的**完整内容**（不截断）
  
- `process_document`: 
  - 只显示 session_id（其他字段不重要）
  
- `record_process_flow`: 
  - 只显示 action_id（其他字段不重要）
  
- `get_session_summary`: 
  - 显示 completeness 和 missing categories

**关键说明**：
- ✅ "格式化"是指去掉 JSON 格式，转成易读的文本
- ✅ "不截断"是指保留所有重要信息（如 chunk 完整内容）
- ❌ 不是"截断内容"或"缩短内容"

---

### `describe_next_action()`

**功能**：描述下一个要执行的动作

**示例**：
- `search_document`: "Search the document for: powder, material, 316L"
- `record_process_flow`: "Record Input flow - Raw Material: Stainless Steel (4.11 kg)"
- `define_lca_scope`: "Define LCA scope parameter: Function Unit (Production of 33 316L...)"

---

## ⚙️ 使用方法

### 命令行

```bash
# 处理单个文件
python scripts/generate_think_with_camel.py \
  --input dataset/full/doc1/full_001_exported.json \
  --output dataset/full/doc1/full_001_with_think.json \
  --api-key "sk-xxx"

# 批量处理
python scripts/batch_process_full_dialogues.py \
  --input-dir dataset/full/doc1 \
  --output-dir dataset/full/doc1 \
  --api-key "sk-xxx"
```

### Python API

```python
from generate_think_with_camel import ThinkGenerator

# 创建生成器
generator = ThinkGenerator(api_key="sk-xxx")

# 处理单个 sample
with open("full_001_exported.json") as f:
    data = json.load(f)

result = generator.generate_think_for_messages(data[0])

# 保存结果
with open("full_001_with_think.json", "w") as f:
    json.dump([result], f, ensure_ascii=False, indent=2)
```

---

## 🎯 质量标准

### 好的 Reasoning

✅ **第一人称**：
```
"I need to find the functional unit first..."
"I found the base material quantity in the table..."
```

✅ **自然引用**：
```
"Based on the functional unit I defined earlier..."
"I also found process water in the same table..."
```

✅ **说明原因**：
```
"I need to search for raw material inputs, starting with the metal powder feedstock..."
"This is clearly a cooling media input that I need to record for the LCI."
```

### 不好的 Reasoning

❌ **第三人称或被动语态**：
```
"The functional unit should be found first..."
"The data will be recorded..."
```

❌ **固定句式**：
```
"Searching for raw material data."
"Recording the data."
```

❌ **缺乏上下文**：
```
"Recording gas input data." (没有说明为什么或从哪里找到的)
```

---

## 📈 性能指标

- **生成速度**：约 2-3 秒/条 reasoning（使用 deepseek-chat）
- **Token 消耗**：约 200-500 tokens/条（input + output）
- **成功率**：>99%（DeepSeek API 稳定）
- **质量一致性**：高（通过记忆机制和动态 Prompt 保证）

---

## 🔧 故障排查

### 问题 1：Reasoning 不连贯

**原因**：Agent 记忆未清空或未正确传递 `previous_messages`

**解决**：
- 确保每个 sample 开始时调用 `self.agent.clear_memory()`
- 检查 `previous_messages = messages[:i]` 是否正确

### 问题 2：Reasoning 过于简单

**原因**：Prompt 中缺少足够的上下文

**解决**：
- 检查 `build_conversation_history()` 是否正确提取了前面的内容
- 确保 `summarize_tool_response()` 显示完整信息（不截断）

### 问题 3：API 调用失败

**原因**：API Key 错误或网络问题

**解决**：
- 检查 API Key 是否正确
- 检查网络连接
- 查看错误日志

---

## 📚 相关文档

- `REASONING_GENERATION_IMPROVEMENT_PLAN.md`：改进方案详细说明
- `EXPORT_TRAINING_DATA_GUIDE.md`：导出训练数据指南
- `BATCH_PROCESSING_GUIDE.md`：批量处理指南

---

## 🎉 总结

本系统通过以下机制实现高质量的 reasoning 生成：

1. **CAMEL AI 记忆机制**：自动记住同一个 sample 内的对话历史
2. **动态 Prompt 构建**：根据当前位置动态生成不同的 prompt
3. **完整信息提供**：不截断 queries、chunks 等信息
4. **第一人称引导**：System Prompt 和 User Prompt 都强调第一人称
5. **自然思维流程**：不使用固定句式，让 Agent 自由发挥

**结果**：生成的 reasoning 自然、连贯、专业，符合 LLM 实际运行时的思维过程。
