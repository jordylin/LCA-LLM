# Short Reasoning v4.0 改进说明

**版本**: v4.0  
**日期**: 2025-11-29  
**状态**: ✅ 已完成

---

## 📋 改进概览

Short 对话的 CAMEL AI 从 v3.0 升级到 v4.0，核心目标：**使用完整信息，提升 Reasoning 质量**。

---

## 🔍 v3.0 vs v4.0 对比

### 1. 辅助函数

| 特性 | v3.0 | v4.0 |
|------|------|------|
| **动态 Prompt** | ❌ 自己实现的简化版 `_build_short_dynamic_prompt()` | ✅ 使用 Full 版本的 `build_dynamic_prompt()` |
| **辅助函数** | ❌ 不使用 `reasoning_helpers.py` | ✅ 导入并使用所有辅助函数 |
| **历史信息** | ❌ 简化（只显示 "Found X chunks"） | ✅ 完整（显示 chunk 内容摘要） |
| **Queries 显示** | ❌ 只显示前 3 个 | ✅ 完整显示所有 queries |
| **Previous Actions** | ❌ 简化显示 | ✅ 提取并传递完整动作列表 |

### 2. System Prompt

**v3.0**:
```python
## Key Principles
2. **Concise**: 30-100 characters (shorter than full dialogues)

## LCI Categories
**Input**: Raw Material, Process Energy, Post-processing Energy, Feedstock Energy, Gas, Cooling Media
**Output**: Product, Recovered Material, Waste, Emission
```

**v4.0**:
```python
## Key Principles
2. **Natural length**: 50-180 characters (quality over brevity)
5. **Classification clarity**: Explain WHY you chose a specific LCI category

## LCI Categories (Critical!)
**Input**: 
- Raw Material: Powder, filament, billet (NOT energy!)
- Process Energy: Electricity for PRINTING/MACHINE operation
- Post-processing Energy: Heat treatment, machining, finishing
- Feedstock Energy: Powder production, atomization, material prep
- Gas: Argon, nitrogen, shielding gas (NOT energy!)
- Cooling Media: Water, coolant, cutting fluid

## Key Classification Rules
⚠️ **Argon/Nitrogen = Gas, NOT Energy!**
⚠️ **Process Energy = Machine operation, NOT post-processing**
⚠️ **Feedstock Energy = Material preparation, NOT process**
```

### 3. 动态 Prompt 构建

**v3.0 简化版**:
```python
def _build_short_dynamic_prompt(self, previous_messages, current_tool_call):
    # 只显示前 3 个 queries
    history.append(f"**Your Previous Action**: Search for: {', '.join(queries[:3])}")
    
    # Tool response 只显示数量
    history.append(f"**Tool Response**: Found {num_results} chunks")
    
    # 简化的 Prompt
    prompt = f"""You are an LCA expert performing LCI data extraction.

## Conversation So Far:
{history_text}

## Next Action You Will Take:
{action_desc}

## Your Task:
Generate your internal reasoning explaining WHY you chose this action.

**Remember**:
- Be concise (30-100 characters)
"""
```

**v4.0 完整版**:
```python
# 使用 Full 版本的 reasoning_helpers
prompt = build_dynamic_prompt(
    previous_messages=previous_messages,
    current_tool_call=tool_calls[0],
    user_query=user_query
)

# 添加短对话特定的引导（强调分类逻辑）
if tool_calls[0].get("name") == "record_process_flow":
    category = tool_calls[0].get("arguments", {}).get("category", "")
    prompt += f"\n\n**Critical**: Explain why you classified this as '{category}' (not other categories)."
    prompt += "\nExample: 'Argon' → Gas (NOT Process Energy, even though consumed during process)"
```

**Full 版本的 `build_dynamic_prompt()` 提供**:
- ✅ 完整的对话历史（包含 tool response 内容）
- ✅ 所有 queries（不截断）
- ✅ Previous actions 提取
- ✅ 场景检测（search→search, search→record, search→summary）
- ✅ 自动引导（根据场景调整 prompt）

---

## 🎯 核心改进点

### 1. **完整信息提供**

**v3.0 问题**:
```python
# 只显示前 3 个 queries
queries = tc_args.get("queries", [])
history.append(f"**Your Previous Action**: Search for: {', '.join(queries[:3])}")

# Tool response 只显示数量
num_results = len(data.get("results", []))
history.append(f"**Tool Response**: Found {num_results} chunks")
```

**v4.0 改进**:
```python
# 使用 reasoning_helpers.describe_next_action()
# 显示所有 queries
queries = args.get("queries", [])
return f"Search the document for: {', '.join(queries)}"

# 使用 reasoning_helpers.summarize_tool_response()
# 显示 chunk 内容摘要
summaries = []
for result in results:
    chunk_id = result.get("chunk_id", "?")
    content_text = result.get("content", "")
    summaries.append(f"  - Chunk {chunk_id}: {content_text}")
return f"Found {len(results)} chunks:\n" + "\n".join(summaries)
```

### 2. **字符限制放宽**

**v3.0**: 30-100 字符（过于严格）  
**v4.0**: 50-180 字符（质量优先）

**原因**:
- 短对话不用担心 tokens（对话轮次少）
- 更长的 reasoning 可以包含更多细节
- 可以解释分类逻辑（"为什么是 Gas 而不是 Energy"）

### 3. **LCI 分类规则强化**

**v3.0**: 只列出分类，没有警告  
**v4.0**: 添加关键分类规则和警告

```python
## Key Classification Rules
⚠️ **Argon/Nitrogen = Gas, NOT Energy!**
⚠️ **Process Energy = Machine operation, NOT post-processing**
⚠️ **Feedstock Energy = Material preparation, NOT process**
```

### 4. **record_process_flow 特别引导**

**v4.0 新增**:
```python
# 添加短对话特定的引导（强调分类逻辑）
if tool_calls[0].get("name") == "record_process_flow":
    category = tool_calls[0].get("arguments", {}).get("category", "")
    prompt += f"\n\n**Critical**: Explain why you classified this as '{category}' (not other categories)."
    prompt += "\nExample: 'Argon' → Gas (NOT Process Energy, even though consumed during process)"
```

**效果**: 强制 Agent 解释分类逻辑，避免机械化的 "Found X, so I'll record it"

---

## 📊 预期效果对比

### v3.0 典型输出

```json
{
  "reasoning_content": "I found electricity consumption data, so I'll record it as Process Energy."
}
```

**问题**:
- ❌ 过于简单
- ❌ 没有解释为什么选择 Process Energy
- ❌ 机械化

### v4.0 预期输出

```json
{
  "reasoning_content": "Found electricity consumption (147.26 kWh) in Table 3.2 for SLM process. This is Process Energy since it's for machine operation during printing, not post-processing."
}
```

**改进**:
- ✅ 包含具体数值和来源
- ✅ 解释分类逻辑（Process Energy vs Post-processing Energy）
- ✅ 自然、有细节

---

## 🚀 使用方法

**v4.0 使用方式与 v3.0 完全相同**:

```bash
python scripts/generate_short_reasoning.py \
  --input dataset/short/doc2/short_001_exported.json \
  --output dataset/short/doc2/short_001_improved.json \
  --api-key "sk-xxx"
```

**或使用批量处理**:

```bash
python scripts/batch_process_short_dialogues.py \
  --output-dir dataset/short/doc2 \
  --api-key "sk-xxx"
```

---

## ✅ 验证清单

测试 v4.0 时，检查以下方面：

1. **Reasoning 长度**: 50-180 字符（不再过短）
2. **分类解释**: record_process_flow 时解释为什么选择该 category
3. **完整信息**: 引用具体的 chunk 内容、数值
4. **自然度**: 不再是机械化的 "Found X, so I'll record it"
5. **准确性**: Argon 被正确分类为 Gas（不是 Energy）

---

## 📝 总结

**v4.0 核心理念**: **完整信息 + Less is More**

**核心改进**:
- ✅ 使用 Full 版本的 `reasoning_helpers`（完整上下文）
- ✅ 完整显示历史信息（不截断 queries、tool response）
- ✅ 提取并传递 Previous Actions（上下文连续性）
- ✅ 放宽字符限制：30-100 → 50-180（质量优先）
- ✅ System Prompt 简化对齐 Full 版本（Less is More）

**预期结果**: 短对话的 Reasoning 质量显著提升，接近 Full 对话的水平。
