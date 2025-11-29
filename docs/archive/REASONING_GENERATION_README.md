# Reasoning 生成 - 快速开始

## 📋 概述

使用 CAMEL AI 为训练数据生成高质量的 reasoning 内容。

**版本**：v6.0  
**更新时间**：2025-11-25

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install camel-ai
```

### 2. 准备 API Key

获取 DeepSeek API Key：https://platform.deepseek.com/

### 3. 生成 Reasoning

```bash
# 单个文件
python scripts/generate_think_with_camel.py \
  --input dataset/full/doc1/full_001_exported.json \
  --output dataset/full/doc1/full_001_with_think.json \
  --api-key "sk-your-api-key"

# 批量处理
python scripts/batch_process_full_dialogues.py \
  --input-dir dataset/full/doc1 \
  --output-dir dataset/full/doc1 \
  --api-key "sk-your-api-key"
```

---

## 📊 输入输出格式

### 输入（`full_xxx_exported.json`）

```json
[
  {
    "messages": [
      {"role": "system", "content": "..."},
      {"role": "user", "content": ""},
      {
        "role": "assistant",
        "reasoning_content": "",  // ← 空的，需要生成
        "tool_calls": [{"name": "search_document", "arguments": {...}}]
      },
      {"role": "tool", "content": "..."},
      ...
    ]
  }
]
```

### 输出（`full_xxx_with_think.json`）

```json
[
  {
    "messages": [
      {"role": "system", "content": "..."},
      {"role": "user", "content": "Please help me extract the LCI data..."},
      {
        "role": "assistant",
        "reasoning_content": "I need to find the functional unit first...",  // ← 已生成
        "tool_calls": [{"name": "search_document", "arguments": {...}}]
      },
      {"role": "tool", "content": "..."},
      ...
    ]
  }
]
```

---

## ✨ 核心特性

### 1. 第一人称代入

```
✅ "I need to find the functional unit first..."
✅ "I found the base material quantity in the table..."
❌ "The functional unit should be found first..."
```

### 2. 自动记忆

Agent 自动记住同一个 sample 内前面的对话：

```
Message 1: "I need to find the functional unit first..."
Message 2: "Based on the functional unit I defined earlier..."  ← 自动引用
Message 3: "I also found process water in the same table..."    ← 自动引用
```

### 3. 动态 Prompt

每个位置生成不同的 prompt：

```
Position 1: 
  - 对话历史：User + process_document
  - 下一步动作：search_document(functional, unit)
  - 生成："I need to find the functional unit first..."

Position 2:
  - 对话历史：User + process_document + search + tool_response
  - 下一步动作：define_lca_scope(...)
  - 生成："I found the product description. Now I need to define..."
```

### 4. 完整信息

不截断 queries、chunks 等信息，Agent 看到完整内容。

---

## 📖 详细文档

- **完整指南**：[REASONING_GENERATION_GUIDE.md](./REASONING_GENERATION_GUIDE.md)
  - 技术架构
  - 执行流程
  - Prompt 结构
  - 实际示例
  - 故障排查

---

## 🎯 质量示例

### 好的 Reasoning

```json
{
  "reasoning_content": "I need to find the functional unit first. I'll search for the product, its quantity, and the manufacturing process to establish the study's basis.",
  "tool_calls": [{
    "name": "search_document",
    "arguments": {"queries": ["manufactured", "part", "product", "kg", "316L", "SLM"]}
  }]
}
```

**特点**：
- ✅ 第一人称（"I need to..."）
- ✅ 说明了为什么（establish the study's basis）
- ✅ 符合工作流程（functional unit first）

---

### 连贯的 Reasoning

```json
// Message 1
{
  "reasoning_content": "I have the functional unit. Now I need to find the raw material inputs, starting with the metal powder feedstock used in the SLM process.",
  "tool_calls": [{"name": "search_document", "arguments": {"queries": ["powder", "material", "316L"]}}]
}

// Message 2
{
  "reasoning_content": "I found the base material quantity in the table. I need to record this 4.11 kg of stainless steel as a raw material input for the LCI.",
  "tool_calls": [{"name": "record_process_flow", "arguments": {...}}]
}
```

**特点**：
- ✅ 引用了前面的动作（"I have the functional unit"）
- ✅ 引用了搜索结果（"found in the table"）
- ✅ 通过 Agent 记忆自动实现

---

## ⚙️ 配置选项

### 命令行参数

```bash
python scripts/generate_think_with_camel.py \
  --input <输入文件路径> \
  --output <输出文件路径> \
  --api-key <DeepSeek API Key> \
  [--model deepseek-chat]  # 可选，默认 deepseek-chat
```

### Python API

```python
from generate_think_with_camel import ThinkGenerator

# 创建生成器
generator = ThinkGenerator(
    api_key="sk-your-api-key",
    model_name="deepseek-chat"  # 可选
)

# 处理单个 sample
result = generator.generate_think_for_messages(sample)
```

---

## 📈 性能

- **速度**：2-3 秒/条 reasoning
- **Token 消耗**：200-500 tokens/条
- **成功率**：>99%
- **质量一致性**：高

---

## 🔧 常见问题

### Q: Reasoning 不连贯怎么办？

**A**: 检查以下几点：
1. 确保每个 sample 开始时清空了记忆
2. 确保 `previous_messages` 正确传递
3. 查看生成的 prompt 是否包含完整的对话历史

### Q: 如何提高生成质量？

**A**: 
1. 使用 `deepseek-chat` 模型（已优化）
2. 确保输入数据格式正确
3. 检查 tool_calls 和 tool_responses 是否完整

### Q: API 调用失败怎么办？

**A**:
1. 检查 API Key 是否正确
2. 检查网络连接
3. 查看错误日志
4. 尝试重新运行

---

## 📚 相关文档

- [REASONING_GENERATION_GUIDE.md](./REASONING_GENERATION_GUIDE.md) - 完整技术指南
- [EXPORT_TRAINING_DATA_GUIDE.md](./EXPORT_TRAINING_DATA_GUIDE.md) - 导出训练数据
- [BATCH_PROCESSING_GUIDE.md](./BATCH_PROCESSING_GUIDE.md) - 批量处理

---

## 🎉 总结

使用 CAMEL AI 生成 reasoning 的核心优势：

1. **第一人称代入**：生成的 reasoning 像真实的 LLM 思维过程
2. **自动记忆**：无需手动提取上下文，Agent 自动记住
3. **动态 Prompt**：每个位置生成不同的 prompt，保证准确性
4. **高质量**：自然、连贯、专业

**开始使用**：
```bash
python scripts/generate_think_with_camel.py \
  --input your_exported.json \
  --output your_with_think.json \
  --api-key "sk-xxx"
```
