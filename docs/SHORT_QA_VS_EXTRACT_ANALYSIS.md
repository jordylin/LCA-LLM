# Short QA vs Extract 场景分析与改进

**日期**: 2025-11-29  
**版本**: v1.0

---

## 📊 核心区别

### **Short Extract** (有 record)
```
User: "Can you help me extract the energy consumption data?"
→ 用户知道要"提取"数据
→ 用户不知道具体值和分类
→ 使用动词: extract, identify, record
```

### **Short QA** (无 record)
```
User: "What energy was used in this process?"
→ 用户只是"询问"信息
→ 更口语化、更自然
→ 使用动词: what, how much, can you tell me
```

---

## 🔧 改进方案总结

### 1️⃣ **`export_short_qa_data.py` 增强** ✅

#### **新增场景支持**

| 场景 | 支持状态 | 说明 |
|------|---------|------|
| **Calculation** | ✅ 已支持 | 跟踪 `parameter → calculation → flow` 链 |
| **Pivot Query** | ✅ 已支持 | 保留失败搜索 → 重新搜索 |
| **Smart Skip** | ✅ 已支持 | 搜索发现已记录 → 跳过 |
| **Link_to** | ✅ 已支持 | Flow 链接到 Calculation，答案标注"Based on calculation" |
| **Multiple Records** | ✅ 已支持 | 同一 chunk 多个数据，合并为连贯答案 |

#### **关键改进**

```python
# 🔥 NEW: 支持 calculation 链
calculation_chain = {}  # {action_id: calculation_result}

# 🔥 NEW: 处理 pivot（失败搜索）
if record_type == "pivot" or intent == "pivot_query":
    # 添加失败的搜索和响应

# 🔥 NEW: 处理 smart_skip
if intent == "smart_skip":
    # 添加搜索和跳过逻辑

# 🔥 NEW: 检查是否链接到 calculation
link_to = action.get("link_to")
is_calc_result = link_to in calculation_chain

# 🔥 NEW: 答案生成区分计算结果
if is_calculation_result:
    return f"Based on the calculation, the {name.lower()} is {value} {unit}."
```

---

### 2️⃣ **`generate_short_reasoning.py` v4.3** ✅

#### **User Content 生成改进**

##### **Extract 场景** (有 record)
```python
# 扫描所有 record_process_flow 和 define_lca_scope
recorded_names = set()
# ... 收集数据名称（去重）

# 使用 CAMEL AI 生成自然请求
prompt = f"""Generate a natural, conversational user request for {context}.

Requirements:
1. Natural and conversational tone
2. DO NOT mention specific values, categories, or technical classifications
3. Keep it simple and direct
4. Use question format or polite request format

Generate ONE natural request (15-30 words):"""
```

**示例输出**:
- ✅ "Can you help me extract the energy consumption data?"
- ✅ "Please identify the functional unit from this document."
- ❌ "Extract Process Energy: Electricity (147.26 kWh)" (过于具体)

##### **QA 场景** (无 record) - 🔥 NEW
```python
# 提取 search queries
topics = ["electricity", "power"]
topics_str = ", ".join(topics)

# 使用 CAMEL AI 生成自然问题
prompt = f"""Generate a natural, conversational question asking about {topics_str} in a manufacturing process.

Requirements:
1. Use question format ("What...", "How much...", "Can you tell me...")
2. Natural and conversational tone
3. DO NOT mention specific values or technical terms
4. Keep it simple and direct (15-25 words)
5. Focus on ASKING, not EXTRACTING

Generate ONE natural question:"""
```

**示例输出**:
- ✅ "What energy was used in this manufacturing process?"
- ✅ "How much electricity did the process consume?"
- ✅ "Can you tell me about the power consumption?"
- ❌ "Can you help me find information about electricity and power?" (模板化)

---

### 3️⃣ **Reasoning 生成** ✅

#### **统一使用 Full 版本的 `reasoning_helpers`**

```python
# 使用 Full 版本的动态 Prompt
prompt = build_dynamic_prompt(
    previous_messages=previous_messages,
    current_tool_call=tool_calls[0],
    user_query=user_query
)

# CAMEL AI 自动生成第一人称推理
response = self.reasoning_agent.step(user_msg)
reasoning = response.msg.content.strip()
```

**优势**:
- ✅ 完整上下文（不截断）
- ✅ CAMEL AI 自动记忆（同一 sample 内）
- ✅ 第一人称自然思维
- ✅ **对 QA 和 Extract 都适用**

---

## 📋 对比表

| 特性 | Short Extract | Short QA |
|------|--------------|----------|
| **User Content 动词** | extract, identify, record | what, how much, tell me |
| **User Content 语气** | 请求式 | 询问式 |
| **Tool Calls** | `search_document` + `record_*` | 仅 `search_document` |
| **Assistant Response** | Tool calls | 直接文本答案 |
| **Reasoning 生成** | ✅ CAMEL AI（Full helpers） | ✅ CAMEL AI（Full helpers） |
| **复杂场景支持** | ✅ Calculation, Pivot, Smart Skip | ✅ Calculation, Pivot, Smart Skip |

---

## 🎯 使用流程

### **导出 QA 数据**
```bash
python scripts/export_short_qa_data.py \
  --session-ids "session_001,session_002" \
  --output dataset/short_qa/doc1/qa_001_exported.json
```

### **生成 Reasoning**
```bash
python scripts/generate_short_reasoning.py \
  --input dataset/short_qa/doc1/qa_001_exported.json \
  --output dataset/short_qa/doc1/qa_001_complete.json \
  --api-key "sk-xxx"
```

### **批量处理**
```bash
python scripts/batch_process_short_qa.py \
  --output-dir dataset/short_qa/doc1 \
  --api-key "sk-xxx"
```

---

## ✅ 验证清单

- [x] `export_short_qa_data.py` 支持 calculation 场景
- [x] `export_short_qa_data.py` 支持 pivot 场景
- [x] `export_short_qa_data.py` 支持 smart_skip 场景
- [x] `export_short_qa_data.py` 支持 link_to 字段
- [x] `generate_short_reasoning.py` 区分 QA 和 Extract 的 user content
- [x] `generate_short_reasoning.py` QA 场景使用 CAMEL AI 生成自然问题
- [x] Reasoning 生成使用 Full 版本的 `reasoning_helpers`
- [x] 所有改进已提交到 Git

---

## 📝 示例对比

### **Extract 场景**
```json
{
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "Can you help me extract the energy consumption data?"},
    {"role": "assistant", "reasoning_content": "I need to search for energy-related data...", "tool_calls": [...]},
    {"role": "tool", "content": "<tool_response>..."},
    {"role": "assistant", "reasoning_content": "I found electricity data...", "tool_calls": [{"name": "record_process_flow", ...}]},
    {"role": "tool", "content": "Successfully recorded"}
  ]
}
```

### **QA 场景**
```json
{
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "What energy was used in this process?"},
    {"role": "assistant", "reasoning_content": "I need to search for energy-related data...", "tool_calls": [...]},
    {"role": "tool", "content": "<tool_response>..."},
    {"role": "assistant", "reasoning_content": "Based on the search results...", "content": "The process consumed 147.26 kWh of electricity."}
  ]
}
```

---

## 🚀 下一步

1. **测试 Full 场景数据**: 使用 `export_short_qa_data.py` 导出包含 calculation、pivot 的复杂场景
2. **验证 User Content 质量**: 检查 CAMEL AI 生成的 QA 问题是否自然
3. **批量生成数据集**: 使用 `batch_process_short_qa.py` 生成 100+ 样本
4. **训练模型**: 使用 QA 和 Extract 混合数据训练

---

**总结**: 
- ✅ `export_short_qa_data.py` 现在可以处理 Full 对话中的所有复杂场景
- ✅ `generate_short_reasoning.py` v4.3 区分 QA 和 Extract 的 user content 生成
- ✅ Reasoning 生成统一使用 Full 版本的 helpers，CAMEL AI 自动发挥
