# Reasoning 生成改进总结

## 📅 更新时间

2025-11-25

---

## 🎯 改进目标

为训练数据生成高质量的 reasoning 内容，使其：
- **第一人称代入**：像真实的 LLM 思维过程
- **自然连贯**：自动引用前面的动作
- **符合流程**：解释"为什么"执行后续的 tool_call

---

## ✅ 已完成的改进

### 1. 启用 CAMEL AI 记忆机制

**改动**：
```python
def generate_think_for_messages(self, sample: Dict) -> Dict:
    # 🔥 每个 sample 开始时清空记忆
    self.agent.clear_memory()
    
    for i, msg in enumerate(messages):
        if msg.get("role") == "assistant":
            # Agent 自动记住这次对话
            response = self.agent.step(user_msg)
```

**效果**：
- ✅ 同一个 sample 内，Agent 自动记住前面生成的 reasoning
- ✅ 生成的 reasoning 自然引用前面的动作
- ✅ 每个 sample 独立，互不干扰

---

### 2. 动态构建 Prompt

**改动**：
```python
# 使用辅助函数动态构建 prompt
prompt = build_dynamic_prompt(
    previous_messages=previous_messages,
    current_tool_call=tool_calls[0],
    user_query=user_query
)
```

**效果**：
- ✅ 每个位置生成不同的 prompt
- ✅ Prompt 包含：前面的对话历史 + 后续要执行的 tool_call
- ✅ Agent 解释"为什么"执行这个 tool_call

---

### 3. 简化 System Prompt

**改动**：
```python
def _get_system_prompt(self) -> str:
    return """You are an LCA expert performing LCI data extraction.
    
## Key Principles
1. **First-person perspective**: Write as if you are performing the extraction
2. **Natural thinking**: Think out loud, don't follow templates
3. **Context-aware**: Reference previous actions when relevant
4. **Concise**: 50-180 characters
5. **Honest**: Express uncertainty or confidence naturally
"""
```

**效果**：
- ✅ 移除固定例子和格式要求
- ✅ 强调第一人称和自然思维
- ✅ 让 Agent 自由发挥

---

### 4. 完整信息提供

**改动**：
```python
# 🔥 显示全部 queries（不截断）
queries = args.get("queries", [])
return f"Search the document for: {', '.join(queries)}"

# 🔥 显示全部 chunks（不截断）
for result in results:
    chunk_id = result.get("chunk_id", "?")
    content_text = result.get("content", "")
    summaries.append(f"  - Chunk {chunk_id}: {content_text}")
```

**效果**：
- ✅ Agent 看到完整的 queries、chunks 等信息
- ✅ 生成更准确的 reasoning

---

### 5. 创建辅助函数模块

**新增文件**：`scripts/reasoning_helpers.py`

**包含函数**：
- `build_dynamic_prompt()`: 动态构建 Prompt
- `build_conversation_history()`: 构建对话历史
- `describe_next_action()`: 描述下一步动作
- `summarize_tool_response()`: 简化 Tool Response

**效果**：
- ✅ 代码模块化，易于维护
- ✅ 逻辑清晰，易于理解

---

## 📊 质量对比

### 改进前

```
"Searching for raw material data."
```

**问题**：
- ❌ 过于简单
- ❌ 缺乏上下文
- ❌ 不是第一人称

---

### 改进后

```
"I need to search for raw material inputs, starting with the metal powder feedstock used in the SLM process."
```

**优点**：
- ✅ 第一人称（"I need to..."）
- ✅ 说明了策略（starting with metal powder）
- ✅ 提供了上下文（SLM process）

---

## 🎬 实际效果

### 测试数据

- **文件**：`full_001_exported.json`
- **消息数**：53 条
- **Assistant 消息**：26 条

### 生成结果

- **成功率**：100%（26/26）
- **场景覆盖**：
  - search_document: 11 次
  - record_process_flow: 11 次
  - define_lca_scope: 1 次
  - get_session_summary: 2 次
  - Final Response: 1 次

### 质量评估

**连贯性**：
```
Message 1: "I need to find the functional unit first..."
Message 2: "Based on the functional unit I defined earlier..."  ← 自动引用
Message 3: "I also found process water in the same table..."    ← 自动引用
```

**第一人称**：
```
"I need to...", "I found...", "I have...", "I'll record..."
```

**自然度**：
```
"Perfect! Based on the functional unit I defined earlier, I can now record the main product output..."
"Great, I found the recovery table again. I'll record the 2.94 kg of powder..."
```

---

## 📁 文件清理

### 已删除

- ✅ `scripts/test_camel_memory.py`
- ✅ `scripts/test_camel_memory_detail.py`
- ✅ `scripts/test_reasoning_improvement.py`
- ✅ `dataset/full/doc1/full_001_improved.json`
- ✅ `dataset/full/doc1/full_001_with_think_test.json`
- ✅ `docs/REASONING_GENERATION_ANALYSIS.md`
- ✅ `docs/SMART_SKIP_REASONING_FIX_SUMMARY.md`

### 已归档

- ✅ `docs/REASONING_GENERATION_IMPROVEMENT_PLAN.md` → `docs/archive/`

### 新增文档

- ✅ `docs/REASONING_GENERATION_GUIDE.md` - 完整技术指南
- ✅ `docs/REASONING_GENERATION_README.md` - 快速开始
- ✅ `docs/REASONING_GENERATION_SUMMARY.md` - 改进总结（本文档）

---

## 🚀 使用方法

### 快速开始

```bash
python scripts/generate_think_with_camel.py \
  --input dataset/full/doc1/full_001_exported.json \
  --output dataset/full/doc1/full_001_with_think.json \
  --api-key "sk-your-api-key"
```

### 批量处理

```bash
python scripts/batch_process_full_dialogues.py \
  --input-dir dataset/full/doc1 \
  --output-dir dataset/full/doc1 \
  --api-key "sk-your-api-key"
```

---

## 📚 相关文档

1. **快速开始**：[REASONING_GENERATION_README.md](./REASONING_GENERATION_README.md)
2. **完整指南**：[REASONING_GENERATION_GUIDE.md](./REASONING_GENERATION_GUIDE.md)
3. **导出数据**：[EXPORT_TRAINING_DATA_GUIDE.md](./EXPORT_TRAINING_DATA_GUIDE.md)
4. **批量处理**：[BATCH_PROCESSING_GUIDE.md](./BATCH_PROCESSING_GUIDE.md)

---

## 🎉 总结

通过以下改进，实现了高质量的 reasoning 生成：

1. **CAMEL AI 记忆机制**：自动记住同一个 sample 内的对话历史
2. **动态 Prompt 构建**：根据当前位置动态生成不同的 prompt
3. **完整信息提供**：不截断 queries、chunks 等信息
4. **第一人称引导**：System Prompt 和 User Prompt 都强调第一人称
5. **自然思维流程**：不使用固定句式，让 Agent 自由发挥

**结果**：生成的 reasoning 自然、连贯、专业，符合 LLM 实际运行时的思维过程。

---

**版本**：v6.0  
**状态**：✅ 已完成，可投入生产使用
