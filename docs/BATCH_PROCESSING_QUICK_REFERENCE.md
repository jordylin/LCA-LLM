# 批量处理快速参考卡

**版本**: 1.0  
**更新日期**: 2025-11-23

---

## 🚀 一键命令

### 短对话数据集（推荐开始）

```bash
python scripts/batch_process_short_dialogues.py \
  --output-dir dataset/short/doc1 \
  --api-key "sk-b9f348bb5ba4437faa5a7253d085fd44"
```

**输出**：
- `short_001_complete.json`, `short_002_complete.json`, ...
- `session_id_mapping.json`
- `batch_process.log`

---

### 完整对话数据集

```bash
python scripts/batch_process_full_dialogues.py \
  --output-dir dataset/full/doc1 \
  --api-key "sk-b9f348bb5ba4437faa5a7253d085fd44"
```

**输出**：
- `training_full_001.jsonl`, `training_full_002.jsonl`, ...
- `session_id_mapping.json`
- `batch_process.log`

---

## 📋 处理特定 Sessions

### 短对话

```bash
python scripts/batch_process_short_dialogues.py \
  --output-dir dataset/short/doc1 \
  --session-ids "session_001,session_002,session_003" \
  --api-key "sk-xxx"
```

### 完整对话

```bash
python scripts/batch_process_full_dialogues.py \
  --output-dir dataset/full/doc1 \
  --session-ids "session_001,session_002,session_003" \
  --api-key "sk-xxx"
```

---

## 🔍 查看处理结果

### 统计文件数量

```bash
# 短对话
ls -1 dataset/short/doc1/short_*_complete.json | wc -l

# 完整对话
ls -1 dataset/full/doc1/training_full_*.jsonl | wc -l
```

### 查看 Session ID 映射

```bash
cat dataset/short/doc1/session_id_mapping.json | jq
```

### 查看处理日志

```bash
tail -f dataset/short/doc1/batch_process.log
```

---

## ✅ 验证数据质量

### 检查 User content

```bash
jq '.messages[] | select(.role=="user") | .content' dataset/short/doc1/short_001_complete.json
```

### 检查 Reasoning

```bash
jq '.messages[] | select(.role=="assistant") | .reasoning_content' dataset/short/doc1/short_001_complete.json
```

### 检查 Name/Note

```bash
jq '.messages[] | select(.tool_calls) | .tool_calls[].arguments | select(.name) | {name, note}' dataset/short/doc1/short_001_improved.json
```

### 确认无 task_type

```bash
grep "task_type" dataset/short/doc1/short_001_complete.json
# 应该没有输出
```

---

## 🔧 常用操作

### 合并多个 JSONL 文件

```bash
cat dataset/full/doc1/training_full_*.jsonl > dataset/training_all.jsonl
```

### 统计样本数量

```bash
# JSON 文件
jq 'length' dataset/short/doc1/short_001_complete.json

# JSONL 文件
wc -l dataset/full/doc1/training_full_001.jsonl
```

### 查看第一个样本

```bash
# JSON
jq '.[0]' dataset/short/doc1/short_001_complete.json

# JSONL
head -1 dataset/full/doc1/training_full_001.jsonl | jq
```

---

## 📊 文件结构

### 短对话数据集

```
dataset/short/doc1/
├── short_001_exported.json      # 导出
├── short_001_improved.json      # 改进
├── short_001_complete.json      # 完成 ⭐
├── short_002_exported.json
├── short_002_improved.json
├── short_002_complete.json      # 完成 ⭐
├── ...
├── session_id_mapping.json      # 映射表
└── batch_process.log            # 日志
```

**最终使用**：`short_*_complete.json`

---

### 完整对话数据集

```
dataset/full/doc1/
├── full_001_exported.json       # 导出
├── full_001_improved.json       # 改进
├── full_001_with_think.json     # 生成
├── training_full_001.jsonl      # 最终 ⭐
├── full_002_exported.json
├── full_002_improved.json
├── full_002_with_think.json
├── training_full_002.jsonl      # 最终 ⭐
├── ...
├── session_id_mapping.json      # 映射表
└── batch_process.log            # 日志
```

**最终使用**：`training_full_*.jsonl`

---

## 🎯 核心流程

### 短对话

```
export → improve → generate_short_reasoning
  ↓         ↓              ↓
JSON     JSON          JSON (最终)
```

### 完整对话

```
export → improve → generate_think → convert
  ↓         ↓            ↓             ↓
JSON     JSON         JSON         JSONL (最终)
```

---

## ⚡ 性能指标

| 操作 | 时间 | 备注 |
|------|------|------|
| 导出 1 个 session | ~1 秒 | 取决于 action 数量 |
| 改进 name/note | ~5-10 秒 | CAMEL AI 调用 |
| 生成 reasoning (短) | ~3-5 秒 | CAMEL AI 调用 |
| 生成 reasoning (完整) | ~10-30 秒 | 取决于对话长度 |
| 转换 JSONL | ~1 秒 | 纯文件操作 |

**估算**：
- 处理 100 个短对话：约 15-20 分钟
- 处理 50 个完整对话：约 30-60 分钟

---

## 💡 最佳实践

1. **使用批量处理脚本**（推荐）
   - 自动化流程
   - 文件命名不重复
   - 详细日志记录

2. **先处理短对话**
   - 快速构建大量样本
   - 验证流程正确性
   - 训练基础能力

3. **定期备份**
   - 备份 `session_id_mapping.json`
   - 备份最终文件（`*_complete.json` 或 `*.jsonl`）

4. **验证数据质量**
   - 检查 user content 不为空
   - 检查 reasoning 已生成
   - 检查 name/note 已改进

---

**详细文档**: `docs/EXPORT_TRAINING_DATA_GUIDE.md`
