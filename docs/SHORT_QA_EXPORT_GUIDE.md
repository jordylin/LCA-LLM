# 短对话 QA 场景导出指南

## 📋 概述

**QA 场景** vs **Extract 场景**：

| 特性 | QA 场景 | Extract 场景 |
|------|---------|-------------|
| **用户意图** | 查询数据值 | 提取并记录数据 |
| **User content** | `"How much electricity was used?"` | `"Please extract the electricity data."` |
| **Tool calls** | 只有 `search_document` | `search_document` + `record_process_flow` |
| **Assistant response** | 直接回答数值 | 确认已记录 |
| **数据库** | 不写入 | 写入 |

---

## 🎯 QA 场景的特点

### 工作台操作
1. 用户通过工作台进行数据提取
2. 只提取 1-2 种数据（不是完整的 LCI 流程）
3. 最开始也会记录 chunk0, 1（preview）

### 训练数据转换
- **MongoDB 中**：`search_document` → `record_process_flow`（有 tool call 和 response）
- **训练数据中**：`search_document` → 直接回答（删除 record tool call，将数据放在 assistant content 中）

**转换示例**：

```json
// MongoDB 中的数据
{
  "role": "assistant",
  "tool_calls": [
    {"name": "search_document", ...},
    {"name": "record_process_flow", "arguments": {"value": 147.26, "unit": "kWh", ...}}
  ]
}

// 训练数据中的数据
{
  "role": "assistant",
  "tool_calls": [
    {"name": "search_document", ...}
  ]
},
{
  "role": "assistant",
  "content": "The process consumed 147.26 kWh of electricity."
}
```

---

## 🚀 使用方法

### 方法 1：批量处理所有 sessions

```bash
python scripts/batch_process_short_qa.py \
  --output-dir dataset/short_qa/doc1 \
  --api-key "sk-xxx"
```

**说明**：
- 自动从 MongoDB 获取所有 sessions
- 导出 → 生成 reasoning → 保存
- 每个 session 一个文件（`qa_001_complete.json`, `qa_002_complete.json`, ...）

---

### 方法 2：处理特定 sessions

```bash
python scripts/batch_process_short_qa.py \
  --output-dir dataset/short_qa/doc1 \
  --session-ids "session_001,session_002,session_003" \
  --api-key "sk-xxx"
```

**说明**：
- 只处理指定的 sessions
- 适合增量处理新数据

---

### 方法 3：分步处理（调试用）

#### Step 1: 导出数据

```bash
python scripts/export_short_qa_data.py \
  --session-ids "ae98c9c9-ee9e-40b1-99a9-b582f1dfc981" \
  --output dataset/short_qa/doc1/qa_001_exported.json
```

#### Step 2: 生成 reasoning

```bash
python scripts/generate_short_reasoning.py \
  --input dataset/short_qa/doc1/qa_001_exported.json \
  --output dataset/short_qa/doc1/qa_001_complete.json \
  --api-key "sk-xxx"
```

---

## 📊 输出文件结构

```
dataset/short_qa/doc1/
├── qa_001_exported.json      # 导出的原始数据（无 reasoning）
├── qa_001_complete.json      # 完整数据（含 reasoning 和 user content）
├── qa_002_exported.json
├── qa_002_complete.json
├── ...
├── session_id_mapping.json   # Session ID 映射
└── batch_process.log         # 处理日志
```

---

## 📝 数据格式示例

### qa_001_exported.json（导出后）

```json
[
  {
    "messages": [
      {
        "role": "system",
        "content": "You are an expert LCA assistant...\n\n**CHUNK 0 PREVIEW**:..."
      },
      {
        "role": "user",
        "content": ""  // 待 CAMEL AI 生成
      },
      {
        "role": "assistant",
        "reasoning_content": "",  // 待 CAMEL AI 生成
        "tool_calls": [
          {
            "name": "search_document",
            "arguments": {
              "session_id": "ae98c9c9...",
              "queries": ["electricity", "kWh", "energy"]
            }
          }
        ]
      },
      {
        "role": "tool",
        "content": "<tool_response>...</tool_response>"
      },
      {
        "role": "assistant",
        "reasoning_content": "",  // 待 CAMEL AI 生成
        "content": "The process consumed 147.26 kWh of electricity."
      }
    ]
  }
]
```

### qa_001_complete.json（生成 reasoning 后）

```json
[
  {
    "messages": [
      {
        "role": "system",
        "content": "You are an expert LCA assistant..."
      },
      {
        "role": "user",
        "content": "How much electricity was used in this process?"  // ✅ CAMEL AI 生成
      },
      {
        "role": "assistant",
        "reasoning_content": "The user wants to know the electricity consumption. I'll search for it.",  // ✅ CAMEL AI 生成
        "tool_calls": [
          {
            "name": "search_document",
            "arguments": {
              "session_id": "ae98c9c9...",
              "queries": ["electricity", "kWh", "energy"]
            }
          }
        ]
      },
      {
        "role": "tool",
        "content": "<tool_response>...</tool_response>"
      },
      {
        "role": "assistant",
        "reasoning_content": "I found the electricity data in the search results.",  // ✅ CAMEL AI 生成
        "content": "The process consumed 147.26 kWh of electricity."
      }
    ]
  }
]
```

---

## 🔍 关键特性

### 1. 自动转换 record → 答案

**MongoDB 中的 record_process_flow**：
```json
{
  "record_type": "flow",
  "name": "Electricity",
  "value": 147.26,
  "unit": "kWh",
  "category": "Process Energy",
  "flow_type": "Input"
}
```

**训练数据中的答案**：
```
"The process consumed 147.26 kWh of electricity."
```

### 2. CAMEL AI 生成自然的 user content

**原则**：
- 用户看到文档提到了某些数据（如 electricity, argon）
- 用户不知道具体分类（Process Energy vs Post-processing Energy）
- 用户不知道有几个（可能 argon 有 2 个，但用户只说"argon"）
- 用户的请求应该是泛化的、自然的

**生成示例**：
- ✅ `"How much electricity was used in this process?"`
- ✅ `"Can you tell me about the argon consumption?"`
- ❌ `"Please record the Electricity (Process Energy) data."`（太具体）

### 3. 保留 search_document

- ✅ 保留所有 `search_document` tool calls 和 responses
- ✅ 保留 chunk preview（chunk 0 和 1）
- ❌ 删除所有 `record_*` tool calls

---

## 🎯 适用场景

1. **快速查询**：用户只想知道某个数据的值
2. **部分提取**：用户只提取 1-2 种数据，不是完整的 LCI 流程
3. **探索性分析**：用户在决定是否记录数据之前先查看

---

## 📚 相关文档

- **Extract 场景**：`docs/BATCH_PROCESSING_GUIDE.md`
- **Reasoning 生成**：`docs/SHORT_REASONING_V4_IMPROVEMENTS.md`
- **Full 对话**：`docs/REASONING_GENERATION_GUIDE.md`

---

## ✅ 总结

**QA 场景导出流程**：
1. ✅ 从 MongoDB 导出 session（包含 search 和 record 操作）
2. ✅ 转换：删除 record tool calls，将数据转为直接回答
3. ✅ 使用 CAMEL AI 生成自然的 user content 和 reasoning
4. ✅ 保存为训练数据格式

**关键优势**：
- ✅ 直接从 MongoDB 导出新数据（不依赖旧数据）
- ✅ 自动转换为 QA 格式
- ✅ CAMEL AI 生成自然的对话
- ✅ 与 Extract 场景互补，丰富训练数据
