# 训练数据导出指南

**版本**: 7.1  
**更新日期**: 2025-11-30

---

## 📋 核心流程

```
工作台标注 → 导出 → 改进 name/note → 生成 reasoning (带全局观) → (转换 JSONL)
     ↓           ↓            ↓                  ↓                      ↓
   手动操作    脚本自动     CAMEL AI         CAMEL AI (全局观)      仅完整对话
```

### ✨ v7.1 最终优化（QA 完全复用 Extract 流程）

**核心改进**：
- 🔥 **完全复用 Extract 流程**：使用相同的脚本，仅在输出时转换格式
- 🔥 **Improve 步骤有用**：CAMEL AI 生成时看到 improved 后的完整对话
- 🔥 **质量一致**：与 Extract 使用相同的生成逻辑（动态 prompt + 记忆模块）

**最终的 QA 处理流程**：
```
1. 导出 (export_training_data.py) - 保留 record
2. 改进 (improve_name_note_with_camel.py) - 提升数据质量
3. 生成 + 转换 (generate_short_reasoning.py --convert-to-qa) - 生成 reasoning，输出时转换格式
```

**关键优势**：
- ✅ **完全复用**：与 Extract 使用相同的 `generate_short_reasoning.py`
- ✅ **Improve 有用**：CAMEL AI 生成时看到 improved 数据，不会被删除
- ✅ **质量一致**：动态 prompt + 记忆模块，与 Extract 相同
- ✅ **仅在输出时转换**：不影响 CAMEL AI 的生成过程

### 三种数据集对比

| 特性 | 完整对话 | 短对话 Extract | 短对话 QA |
|------|---------|----------------|----------|
| **描述** | 完整的 LCI 提取流程（Phase 1-4） | 单个操作（search → record） | 纯查询（search → answer） |
| **工作台操作** | FU → Input → Output → Validation | 随机查询 + 单次记录 | 随机查询（不记录） |
| **样本长度** | 10-30 轮对话 | 1-3 轮对话 | 1-2 轮对话 |
| **输出格式** | JSONL | JSON | JSON |
| **导出脚本** | `export_training_data.py` | `export_training_data.py` | `export_training_data.py` |
| **推荐用途** | 高级训练、流程理解 | 初期训练、记录能力 | 初期训练、查询能力 |
| **数据量需求** | 50-100 个会话 | 300-500 个样本 | 300-500 个样本 |

---

## 🚀 快速开始：批量处理（推荐）⭐⭐⭐

### 方式 1: 短对话 Extract 数据集（推荐开始）

**使用场景**：
- 快速构建大量训练样本
- 训练基础记录能力（search → record）
- 每个样本 < 1 分钟

**批量处理脚本**：
```bash
python scripts/batch_process_short_dialogues.py \
  --output-dir dataset/short_extract/doc3 \
  --api-key "sk-b9f348bb5ba4437faa5a7253d085fd44"
```

**执行流程**：
```
1. 自动从 MongoDB 获取所有 sessions
2. 对每个 session 执行：
   - 导出 (export_training_data.py)
   - 改进 name/note (improve_name_note_with_camel.py)
   - 生成 reasoning (generate_short_reasoning.py)
3. 生成文件命名映射表
```

**输出文件**：
```
dataset/short_extract/doc3/
├── extract_001_exported.json    # 导出阶段
├── extract_001_improved.json    # 改进阶段
├── extract_001_complete.json    # 完成阶段（最终使用）
├── extract_002_exported.json
├── extract_002_improved.json
├── extract_002_complete.json
├── ...
├── session_id_mapping.json      # Session ID 映射表
└── batch_process.log            # 处理日志
```

**文件命名特点**：
- ✅ 自动增量命名（extract_001, extract_002, ...）
- ✅ **不会重复**：即使多次运行，新 session 会继续递增
- ✅ Session ID 映射表：可追溯原始 session

**处理特定 sessions**：
```bash
python scripts/batch_process_short_dialogues.py \
  --output-dir dataset/short_extract/doc3 \
  --session-ids "session_001,session_002,session_003" \
  --api-key "sk-b9f348bb5ba4437faa5a7253d085fd44"
```

---

### 方式 2: 短对话 QA 数据集（新增）⭐

**使用场景**：
- 训练纯查询能力（不记录数据）
- 训练 LLM 直接回答问题
- 支持复杂场景（calculation、pivot、smart_skip）

**批量处理脚本**：
```bash
python scripts/batch_process_short_qa.py \
  --output-dir dataset/short_qa/doc3 \
  --api-key "sk-b9f348bb5ba4437faa5a7253d085fd44"
```

**执行流程（v3.0 最终版）**：
```
1. 自动从 MongoDB 获取所有 sessions
2. 对每个 session 执行：
   - 导出 (export_training_data.py) - 保留 record
   - 改进 (improve_name_note_with_camel.py) - 提升 name/note 质量
   - 生成 + 转换 (generate_short_reasoning.py --convert-to-qa) - 生成 reasoning，输出时转换
3. 生成文件命名映射表
```

**输出文件**：
```
dataset/short_qa/doc3/
├── qa_001_exported.json         # 导出阶段（保留 record）
├── qa_001_improved.json         # 改进阶段（高质量 name/note）
├── qa_001_complete.json         # 完成阶段（最终使用，QA 格式）
├── qa_002_exported.json
├── qa_002_improved.json
├── qa_002_complete.json
├── ...
├── session_id_mapping.json      # Session ID 映射表
└── batch_process.log            # 处理日志
```

**关键特性（v3.0）**：
- ✅ **完全复用 Extract**：使用相同的 `generate_short_reasoning.py`
- ✅ **Improve 有用**：CAMEL AI 生成时看到 improved 数据
- ✅ **质量一致**：动态 prompt + 记忆模块，与 Extract 相同
- ✅ **仅在输出时转换**：`--convert-to-qa` 参数控制
- ✅ **支持复杂场景**：calculation、pivot、smart_skip 等
- ✅ **自然问题生成**：基于 search queries，不是 record 元数据

**与 Extract 的区别**：

| 特性 | Extract | QA |
|------|---------|----|
| **工具调用** | 保留 `record_*` | 删除 `record_*` |
| **Assistant 回答** | 确认记录 | 直接提供数据 |
| **User Content** | "帮我提取..." | "...是多少？" |
| **训练目标** | 记录能力 | 查询能力 |

**示例对比**：

**Extract 场景**：
```json
{
  "role": "assistant",
  "tool_calls": [{"name": "record_process_flow", ...}],
  "reasoning_content": "I found the energy data, I'll record it."
}
```

**QA 场景**：
```json
{
  "role": "assistant",
  "content": "The process energy consumption is 64.92 kWh.",
  "reasoning_content": "I found the energy data in the table."
}
```

---

### 方式 3: 完整对话数据集

**使用场景**：
- 训练完整的 LCI 提取流程
- 学习 Phase 1-4 的顺序
- 高级训练阶段

**批量处理脚本**：
```bash
python scripts/batch_process_full_dialogues.py \
  --output-dir dataset/full/doc3 \
  --api-key "sk-b9f348bb5ba4437faa5a7253d085fd44"
```

**执行流程**：
```
1. 自动从 MongoDB 获取所有 sessions
2. 对每个 session 执行：
   - 导出 (export_training_data.py)
   - 改进 name/note (improve_name_note_with_camel.py) ⭐
   - 生成 reasoning (generate_think_with_camel.py)
   - 转换为 JSONL (convert_json_to_jsonl.py)
3. 生成文件命名映射表
```

**输出文件**：
```
dataset/full/doc3/
├── full_001_exported.json       # 导出阶段
├── full_001_improved.json       # 改进阶段
├── full_001_with_think.json     # 生成 reasoning
├── training_full_001.jsonl      # 最终训练文件
├── full_002_exported.json
├── full_002_improved.json
├── full_002_with_think.json
├── training_full_002.jsonl
├── ...
├── session_id_mapping.json      # Session ID 映射表
└── batch_process.log            # 处理日志
```

**文件命名特点**：
- ✅ 自动增量命名（full_001, full_002, ...）
- ✅ **不会重复**：即使多次运行，新 session 会继续递增
- ✅ Session ID 映射表：可追溯原始 session

---

## 🔧 单个 Session 处理（手动）

### 短对话 Extract 数据集

**步骤 1: 导出**
```bash
python scripts/export_training_data.py \
  --session-id <session_id> \
  --output dataset/extract_001_exported.json
```

**步骤 2: 改进 name/note**
```bash
python scripts/improve_name_note_with_camel.py \
  --input dataset/extract_001_exported.json \
  --output dataset/extract_001_improved.json \
  --api-key "sk-b9f348bb5ba4437faa5a7253d085fd44"
```

**步骤 3: 生成 reasoning**
```bash
python scripts/generate_short_reasoning.py \
  --input dataset/extract_001_improved.json \
  --output dataset/extract_001_complete.json \
  --api-key "sk-b9f348bb5ba4437faa5a7253d085fd44"
```

**最终文件**：`dataset/extract_001_complete.json`（JSON 格式）

---

### 短对话 QA 数据集

**步骤 1: 导出（使用通用脚本，保留 record）**
```bash
python scripts/export_training_data.py \
  --session-id <session_id> \
  --output dataset/qa_001_exported.json
```

**步骤 2: 改进 name/note（提升数据质量）**
```bash
python scripts/improve_name_note_with_camel.py \
  --input dataset/qa_001_exported.json \
  --output dataset/qa_001_improved.json \
  --api-key "sk-b9f348bb5ba4437faa5a7253d085fd44"
```

**步骤 3: 生成 reasoning + QA 转换（使用 generate_short_reasoning.py --convert-to-qa）**
```bash
python scripts/generate_short_reasoning.py \
  --input dataset/qa_001_improved.json \
  --output dataset/qa_001_complete.json \
  --api-key "sk-b9f348bb5ba4437faa5a7253d085fd44" \
  --convert-to-qa  # 🔥 关键参数：在输出时转换为 QA 格式
```

**最终文件**：`dataset/qa_001_complete.json`（JSON 格式）

**核心优势（v3.0）**：
- ✅ **完全复用 Extract**：使用相同的 `generate_short_reasoning.py`
- ✅ **Improve 有用**：CAMEL AI 生成时看到 improved 数据
- ✅ **质量一致**：动态 prompt + 记忆模块，与 Extract 相同
- ✅ **仅在输出时转换**：不影响 CAMEL AI 的生成过程

---

### 完整对话数据集

**步骤 1: 导出**
```bash
python scripts/export_training_data.py \
  --session-id <session_id> \
  --output dataset/full_001_exported.json
```

**步骤 2: 改进 name/note** ⭐
```bash
python scripts/improve_name_note_with_camel.py \
  --input dataset/full_001_exported.json \
  --output dataset/full_001_improved.json \
  --api-key "sk-b9f348bb5ba4437faa5a7253d085fd44"
```

**步骤 3: 生成 reasoning**
```bash
python scripts/generate_think_with_camel.py \
  --input dataset/full_001_improved.json \
  --output dataset/full_001_with_think.json \
  --api-key "sk-b9f348bb5ba4437faa5a7253d085fd44"
```

**步骤 4: 转换为 JSONL**
```bash
python scripts/convert_json_to_jsonl.py \
  --input dataset/full_001_with_think.json \
  --output dataset/training_full_001.jsonl
```

**最终文件**：`dataset/training_full_001.jsonl`（JSONL 格式）

---

## 📚 脚本详解

### 1. export_training_data.py（通用导出）

**功能**：从 MongoDB 导出 session 数据为训练样本

**基本用法**：
```bash
python scripts/export_training_data.py \
  --session-id <session_id> \
  --output <output_file> \
  --format json
```

**常用参数**：
- `--session-id <id>`：导出指定 session
- `--all`：导出所有 sessions
- `--output <file>`：输出文件路径
- `--format <fmt>`：输出格式（json 或 jsonl）

**特点**：
- ✅ 同时支持完整对话和短对话
- ✅ 自动添加 LLM 最终回复（闭环对话）
- ✅ 已移除 `task_type` 字段（避免训练污染）

---

### 2. improve_name_note_with_camel.py（改进 name/note）⭐

**功能**：使用 CAMEL AI 改进 `name` 和 `note` 字段

**基本用法**：
```bash
python scripts/improve_name_note_with_camel.py \
  --input <input_file> \
  --output <output_file> \
  --api-key "sk-b9f348bb5ba4437faa5a7253d085fd44"
```

**改进内容**：

**Name 字段**：
- 去除尾随/前导空格
- 添加材料规格（如 "316L"）
- 使用标准 LCA 术语
- 保持简洁（2-5 词）

**Note 字段**：
- 添加工艺上下文（如 "SLM machine", "Atomization"）
- 添加关键限定词（如 "99.9% purity", "recycled"）
- 区分同名流（如 "for cooling" vs "for cleaning"）
- 保持简洁（3-8 词）

**示例**：
```
原始:
  name: "Stainless Steel "  (有尾随空格)
  note: ""

改进后:
  name: "316L Stainless Steel Powder"
  note: "X2CrNiMo1712, atomized"
```

**重要性**：
- ✅ **完整对话和短对话都需要**
- ✅ 提高数据质量
- ✅ 标准化术语

---

### 3. generate_short_reasoning.py（短对话专用）⭐ v4.4 更新

**功能**：为短对话生成 user content、reasoning 和最终回复（支持 Extract 和 QA）

**Extract 场景用法**：
```bash
python scripts/generate_short_reasoning.py \
  --input <improved_file> \
  --output <complete_file> \
  --api-key "sk-b9f348bb5ba4437faa5a7253d085fd44"
```

**QA 场景用法**（🔥 新增 --convert-to-qa）：
```bash
python scripts/generate_short_reasoning.py \
  --input <improved_file> \
  --output <complete_file> \
  --api-key "sk-b9f348bb5ba4437faa5a7253d085fd44" \
  --convert-to-qa  # 在输出时转换为 QA 格式
```

**v4.4 新特性**：

**1. QA 格式转换（--convert-to-qa）**：
- ✅ **生成时保留 record**：CAMEL AI 看到 improved 后的完整对话
- ✅ **输出时删除 record**：仅在保存时转换为 QA 格式
- ✅ **Improve 有用**：不会被删除，CAMEL AI 能看到
- ✅ **质量一致**：与 Extract 使用相同的生成逻辑

**2. 自动识别场景**：
- **Extract 场景**（有 `record_*` 工具调用）：
  - ✅ 扫描所有 `record_*` 操作
  - ✅ 生成提取类 user content："帮我提取..."
  - ✅ Reasoning 关注记录过程
  
- **QA 场景**（基于 search queries）：
  - ✅ 基于 search queries 生成问句
  - ✅ 使用 CAMEL AI 生成自然问题："...是多少？"
  - ✅ Reasoning 关注查找和回答

**3. 自然的 User Content 生成**：
- **Extract 示例**：
  ```
  "Could you help me extract the energy data?"
  "Please extract the material flows from this document."
  ```
  
- **QA 示例**：
  ```
  "What's the process energy consumption?"
  "How much argon gas is used?"
  ```

**4. 使用 Full 版本 reasoning_helpers**：
- ✅ 与完整对话使用相同的辅助函数
- ✅ 支持动态 Prompt 构建
- ✅ 支持完整上下文感知

**关键特点**：
- ✅ **单一脚本**：同时处理 QA 和 Extract
- ✅ **完全复用**：QA 使用相同的生成逻辑
- ✅ **仅在输出时转换**：不影响 CAMEL AI 的生成过程
- ✅ **Improve 有用**：CAMEL AI 生成时看到 improved 数据

---

### 4. generate_think_with_camel.py（完整对话专用）

**功能**：为完整对话生成 reasoning

**基本用法**：
```bash
python scripts/generate_think_with_camel.py \
  --input <input_file> \
  --output <output_file> \
  --api-key "sk-b9f348bb5ba4437faa5a7253d085fd44"
```

**常用参数**：
- `--num-candidates 3`：每个样本生成 3 个候选
- `--model deepseek-chat`：使用标准模型
- `--model deepseek-reasoner`：使用 R1 推理模型（更高质量）

---

### 5. convert_json_to_jsonl.py（格式转换）

**功能**：将 JSON 转换为 JSONL（仅完整对话需要）

**基本用法**：
```bash
python scripts/convert_json_to_jsonl.py \
  --input <input_file> \
  --output <output_file>
```

**特点**：
- 自动移除 metadata 字段
- 每行一个样本
- 仅保留 messages 字段

---

## ❓ 常见问题

### Q1: 文件命名会重复吗？

**A**: **不会重复！**

批量处理脚本使用智能命名策略：
- ✅ 读取 `session_id_mapping.json` 中的现有映射
- ✅ 找到当前最大序号
- ✅ 新 session 使用 `最大序号 + 1`
- ✅ 即使多次运行，也会继续递增

**示例**：
```
第一次运行：short_001, short_002, short_003
第二次运行：short_004, short_005, short_006  (继续递增)
```

---

### Q2: 完整对话需要 improve_name_note 吗？

**A**: **需要！**

**原因**：
- ✅ 完整对话和短对话都需要改进 name/note
- ✅ 提高数据质量和一致性
- ✅ 标准化 LCA 术语

**正确流程**：
```
完整对话：export → improve → generate_think → convert
短对话 Extract：export → improve → generate_short_reasoning
短对话 QA：export → improve → generate_short_reasoning --convert-to-qa
```

---

### Q3: 如何验证数据质量？

**A**: **检查以下内容**

**1. User content 不为空**：
```bash
jq '.messages[] | select(.role=="user") | .content' dataset/short_001_complete.json
```

**2. Reasoning 已生成**：
```bash
jq '.messages[] | select(.role=="assistant") | .reasoning_content' dataset/short_001_complete.json
```

**3. Name/Note 已改进**：
```bash
jq '.messages[] | select(.tool_calls) | .tool_calls[].arguments | select(.name) | {name, note}' dataset/short_001_improved.json
```

**4. 无 task_type 字段**：
```bash
grep "task_type" dataset/short_001_complete.json
# 应该没有输出
```

---

### Q4: QA 和 Extract 场景如何选择？

**A**: **现在两者都使用相同的导出和改进流程！**

**共同流程（前两步）**：
```bash
# 步骤 1: 导出（保留 record）
python scripts/export_training_data.py \
  --session-id <session_id> \
  --output dataset/extract_001_exported.json

# 步骤 2: 改进 name/note
python scripts/improve_name_note_with_camel.py \
  --input dataset/data_001_exported.json \
  --output dataset/data_001_improved.json \
  --api-key "sk-xxx"
```

**区别在第三步**：

**Extract 场景**（训练记录能力）：
```bash
# 步骤 3: 生成 reasoning（保留 record）
python scripts/generate_short_reasoning.py \
  --input dataset/extract_001_improved.json \
  --output dataset/extract_001_complete.json \
  --api-key "sk-xxx"
```
- ✅ 保留 `record_*` 工具调用
- ✅ 生成提取类 user content："帮我提取..."
- ✅ 训练记录能力

**QA 场景**（训练查询能力）：
```bash
# 步骤 3: 生成 reasoning + QA 转换（使用 generate_short_reasoning.py --convert-to-qa）
python scripts/generate_short_reasoning.py \
  --input dataset/qa_001_improved.json \
  --output dataset/qa_001_complete.json \
  --api-key "sk-xxx" \
  --convert-to-qa  # 🔥 在输出时转换为 QA 格式
```
- ✅ 删除 `record_*` 工具调用（仅在输出时）
- ✅ 生成问句类 user content："...是多少？"
- ✅ CAMEL AI 生成时看到 improved 数据
- ✅ 训练查询能力

**关键改进（v3.0）**：
- ✅ **前两步完全相同**：都使用 `export_training_data.py` + `improve_name_note_with_camel.py`
- ✅ **第三步使用相同脚本**：都使用 `generate_short_reasoning.py`，QA 加 `--convert-to-qa`
- ✅ **Improve 有用**：CAMEL AI 生成时看到 improved 数据，不会被删除
- ✅ **质量一致**：与 Extract 使用相同的生成逻辑

---

### Q5: 如何追溯原始 session？

**A**: **查看 session_id_mapping.json**

```bash
cat dataset/short/doc1/session_id_mapping.json
```

输出示例：
```json
{
  "e4883977-3071-4dd3-a457-170588933cc6": "short_001",
  "f5994088-4182-5ee5-b1f6-281699044dd7": "short_002"
}
```

---

## 📈 推荐数据集规模

### 初期训练（验证可行性）
- 短对话 Extract：100-200 个样本
- 短对话 QA：100-200 个样本
- 完整对话：5-10 个会话
- 目的：验证训练流程

### 正式训练（达到可用水平）
- 短对话 Extract：300-500 个样本
- 短对话 QA：300-500 个样本
- 完整对话：50-100 个会话
- 目的：训练出能实际使用的 LLM

### 高级训练（达到专家水平）
- 短对话 Extract：1000+ 个样本
- 短对话 QA：1000+ 个样本
- 完整对话：200+ 个会话
- 目的：训练出接近人类专家的 LLM

**建议比例**：
- Extract : QA = 1:1（平衡记录和查询能力）
- 短对话 : 完整对话 = 10:1（先打基础，再学流程）

---

## 🎯 工作流顺序（重要）

**标准 LCA 顺序**：
```
Phase 1: Function Unit (定义基准)
  ↓
Phase 2: Input Flows (Raw Material → Energy → Gas → Cooling Media)
  ↓
Phase 3: Output Flows (Product → Recovered Material → Waste → Emission)
  ↓
Phase 4: Validation (验证完整性)
```

**注意**：
- 正确顺序：FU → Input → Output → Validation
- 反推策略：Product 虽然在 Phase 3，但可以使用 Phase 1 的搜索结果
- 标注时灵活性：实际标注时可根据文档结构调整

---

## 🔗 相关文档

- **工作台使用**: `docs/Expert_Workbench_Guide.md`
- **工作流详解**: `docs/EcoLLM_Guide.md`
- **Prompt 设计**: `docs/PROMPT_DESIGN_GUIDE.md`

---

**维护者**: LCA-LLM Team  
**更新时间**: 2025-11-23
