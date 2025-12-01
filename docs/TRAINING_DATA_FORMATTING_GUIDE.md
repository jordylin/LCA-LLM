# 2.2.3 Training Data Formatting 技术说明文档

本文档详细介绍训练数据格式化流程，帮助理解从专家标注到 SFT 训练样本的转换逻辑。

---

## 1. 概述

### 1.1 这个阶段做什么？

专家在工作台完成标注后，数据以结构化记录的形式存储在 MongoDB 中。这些记录包含：
- 工具调用（search_document, record_process_flow 等）
- 工具响应（搜索结果、记录确认等）
- 元数据（session_id, action_id, timestamp 等）

但这些记录**不能直接用于 SFT 训练**，需要转换为 Chat Template 格式——即 LLM 训练所需的多轮对话格式。

### 1.2 为什么需要这个阶段？

| MongoDB 记录 | Chat Template 格式 |
|-------------|-------------------|
| 扁平化的动作序列 | 多轮对话结构 |
| 无 System Prompt | 包含完整 System Prompt |
| 无文档上下文 | 注入 Chunk Preview |
| 记录独立存储 | 按对话轮次组织 |

**核心目标**：确保训练数据格式与推理时的输入格式完全一致，避免 train-inference mismatch。

---

## 2. Chat Template 格式

### 2.1 格式结构

```json
{
  "messages": [
    {"role": "system", "content": "<system_prompt>"},
    {"role": "user", "content": "<user_request>"},
    {"role": "assistant", "content": "<response>", "tool_calls": [...]},
    {"role": "tool", "name": "<tool_name>", "content": "<tool_response>"},
    {"role": "assistant", "content": "<response>", "tool_calls": [...]},
    ...
    {"role": "assistant", "content": "<final_response>"}
  ]
}
```

### 2.2 消息类型

| Role | 说明 | 内容来源 |
|------|------|---------|
| system | 系统提示词 | 脚本生成（含文档上下文） |
| user | 用户请求 | 后续由 CAMEL AI 生成 |
| assistant | 助手响应 | 工具调用或文本回复 |
| tool | 工具响应 | MongoDB 记录重建 |

---

## 3. System Prompt 设计

### 3.1 设计原则

System Prompt 是训练数据的关键组成部分，直接影响模型学习的行为模式。我们遵循以下原则：

1. **Less is More**：极简、聚焦、指令式
2. **Train-Inference Consistency**：与推理时的 prompt 保持一致
3. **Tool-Centric**：以工具使用为核心组织内容

### 3.2 Prompt 结构

```
## Core Task
Extract quantitative LCI data from documents or answer specific questions.

## Tools
- search_document: Search text segments containing data via keywords
- define_lca_scope: Record Functional Unit
- record_process_flow: Record LCI flows (quantitative values)
- record_parameter: Record intermediate parameters for calculation
- execute_calculation: Calculate derived values
- get_session_summary: Check recorded data

## Strategic Workflow
1. Anchor (Functional Unit): Identify the study basis
2. Inputs: Extract Material, Energy, Gas, Cooling
3. Outputs: Extract Waste, Emissions, Product
4. Validation: Check completeness

## LCI Categories (11 types)
**Input**: Raw Material, Process Energy, Post-processing Energy, Feedstock Energy, Gas, Cooling Media
**Output**: Product, Recovered Material, Waste, Emission
**Scope**: Functional Unit

## Key Guidelines
1. Batch Search: Combine related keywords in one search
2. Calc vs Record: Explicit data → record; Needs calculation → parameter + calc + record
3. Energy Classification: Process / Post-processing / Feedstock
4. Note Field: Use for context and qualifiers
5. Missing Data: Skip if not found. Do not hallucinate.
```

### 3.3 文档上下文注入

为了让模型"看到"文档，我们在 System Prompt 中注入文档上下文：

```
**DOCUMENT CONTEXT**: 
A PDF document has been uploaded and is ready for analysis.
- Document Name: "SLM_Ti64_LCA_Study.pdf"
- Document ID: a1b2c3d4...

**CHUNK 0 PREVIEW** (Executive Summary / Introduction):
"This study presents a comprehensive life cycle assessment of selective laser melting..."

**CHUNK 1 PREVIEW**:
"The functional unit is defined as the production of one Ti-6Al-4V impeller..."
```

**设计考量**：
- Chunk 0 通常是摘要/引言，提供研究概览
- Chunk 1 通常包含方法论或关键数据
- Preview 帮助模型理解文档主题，指导后续搜索策略

---

## 4. 工具调用序列重建

### 4.1 从 MongoDB 记录到对话轮次

MongoDB 中的记录是扁平化的：

```
action_001: search_document(["titanium", "powder"])
action_002: tool_response(search_document, [...chunks...])
action_003: record_process_flow(name="Ti-6Al-4V powder", value=2.5, unit="kg")
action_004: tool_response(record_process_flow, "Recorded successfully")
```

需要重建为对话轮次：

```json
[
  {"role": "assistant", "tool_calls": [{"name": "search_document", "arguments": {"query": ["titanium", "powder"]}}]},
  {"role": "tool", "name": "search_document", "content": "[...chunks...]"},
  {"role": "assistant", "tool_calls": [{"name": "record_process_flow", "arguments": {"name": "Ti-6Al-4V powder", "value": 2.5, "unit": "kg"}}]},
  {"role": "tool", "name": "record_process_flow", "content": "Recorded successfully"}
]
```

### 4.2 Session Summary 状态还原

`get_session_summary` 工具返回当前会话已记录的数据。在重建时，需要根据调用时间点还原当时的状态：

```python
def get_session_summary_text(session_id, before_action_id):
    """
    获取 action_id 之前的所有记录，模拟当时的 summary 状态
    """
    query = {
        "session_id": session_id,
        "action_id": {"$lt": before_action_id}  # 只获取之前的记录
    }
    actions = db.lca_actions.find(query).sort("action_id", 1)
    # 构建 summary 文本...
```

**这确保了**：训练数据中的 summary 响应与推理时模型实际看到的一致。

---

## 5. 实现细节

### 5.1 核心脚本

`scripts/export_training_data.py`：主导出脚本

**关键类**：`TrainingDataExporter`

**主要方法**：
- `get_system_prompt()`: 获取基础 System Prompt
- `get_system_prompt_with_chunks()`: 注入文档上下文
- `get_session_summary_text()`: 还原 summary 状态
- `export_session()`: 导出单个会话
- `export_all()`: 批量导出

### 5.2 输出格式

导出为 JSONL 文件，每行一个样本：

```jsonl
{"session_id": "xxx", "messages": [...], "metadata": {...}}
{"session_id": "yyy", "messages": [...], "metadata": {...}}
```

### 5.3 质量保证

1. **格式验证**：检查每个样本的 messages 结构
2. **工具调用验证**：确保 tool_calls 和 tool responses 配对
3. **Session ID 一致性**：确保同一会话的记录完整

---

## 6. 与前后阶段的衔接

```
┌─────────────────────────────────────────────────────────────────┐
│  2.2.2 Semi-automatic Annotation                                │
│  ├── 专家在工作台标注                                            │
│  └── 数据存储到 MongoDB                                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  2.2.3 Training Data Formatting  ← 本阶段                       │
│  ├── 从 MongoDB 导出记录                                         │
│  ├── 转换为 Chat Template 格式                                   │
│  ├── 注入 System Prompt + 文档上下文                             │
│  └── 输出 JSONL 文件                                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  2.2.4 Data Cleaning and Reasoning Generation                   │
│  ├── Name/Note 规范化                                            │
│  ├── 推理内容生成                                                │
│  └── 场景感知内容生成                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

# 手稿草稿

## 中文草稿

### 2.2.3 训练数据格式化

专家标注完成后，数据以结构化记录的形式存储在数据库中。每条记录包含动作类型（如 search_document、record_process_flow）、参数、执行结果和时间戳，按 action_id 顺序排列。然而，这种扁平化的记录结构与 LLM 训练所需的格式存在根本差异：SFT 训练要求数据以 Chat Template 格式组织，即包含 system、user、assistant、tool 四种角色的多轮对话结构。更重要的是，训练数据的格式必须与推理时的输入格式完全一致——如果训练时模型看到的是某种消息结构，推理时却接收到不同的结构，会导致严重的性能下降。因此，格式转换不仅是数据组织方式的改变，更是确保训练-推理一致性的关键步骤。

**Chat Template 格式与 System Prompt 设计**

Chat Template 格式将对话组织为消息序列，包含四种角色：system（系统提示词）、user（用户请求）、assistant（助手响应，可包含工具调用）、tool（工具响应）。其中，System Prompt 的设计尤为关键，它定义了模型的角色、可用工具和行为准则。我们遵循"Less is More"原则设计 System Prompt：以工具使用为核心，明确定义六种工具的功能和使用场景；提供战略性工作流程指导（锚定功能单位 → 提取输入 → 提取输出 → 验证完整性）；列出 11 种 LCI 类别的分类标准；给出关键操作指南（如批量搜索、计算与直接记录的选择、能源分类等）。

**文档上下文注入**

为使模型能够"感知"待分析的文档，我们在 System Prompt 中注入文档上下文。具体而言，我们提取文档的前两个 chunk 作为预览：Chunk 0 通常是摘要或引言，提供研究概览；Chunk 1 通常包含方法论或关键数据定义。这种设计使模型在开始交互前就能了解文档主题和结构，从而制定更有效的搜索策略。文档上下文还包含文档名称和会话标识符，确保工具调用的可追溯性。

**工具调用序列重建**

数据库中的记录是按时间顺序排列的扁平化动作序列，需要重建为符合 Chat Template 规范的对话轮次结构。这一转换涉及三个层面的处理。

首先是消息角色映射。数据库中每条工具调用记录需要拆分为两条消息：一条 assistant 消息包含 tool_calls 字段，描述模型决定调用哪个工具及其参数；紧随其后的一条 tool 消息包含工具执行结果。例如，一条 search_document 记录会转换为：assistant 消息携带 `{"name": "search_document", "arguments": {"query": ["titanium", "powder"]}}`，tool 消息携带搜索返回的文档片段。这种一一对应的结构确保模型能够学习"决策-反馈"的完整循环。

其次是工具响应内容的重建。不同工具的响应需要按照推理时的实际格式重建。search_document 的响应需要包含匹配的文档片段及其元数据；record_process_flow 的响应需要确认记录成功并回显记录的数据；execute_calculation 的响应需要包含计算过程和结果。特别地，get_session_summary 工具的响应需要根据调用时间点动态还原——只包含该 action_id 之前已记录的数据，而非会话的最终状态。这确保训练数据中的 summary 响应与推理时模型实际看到的一致，避免信息泄漏。

最后是对话边界的确定。一个完整的训练样本从 system 消息开始，包含一条 user 消息（用户请求），随后是多轮 assistant-tool 交互，最终以一条不包含工具调用的 assistant 消息（最终回复）结束。对话边界的正确划分确保每个样本都是一个完整的任务执行过程。

转换后的数据以 JSONL 格式输出，每行一个完整的对话样本，供后续的数据清洗和推理生成阶段处理。

---

## English Version (For Manuscript)

### 2.2.3 Training Data Formatting

After expert annotation, data is stored in the database as structured records. Each record contains the action type (e.g., search_document, record_process_flow), parameters, execution results, and timestamps, arranged in action_id order. However, this flattened record structure fundamentally differs from the format required for LLM training: SFT training requires data organized in Chat Template format—a multi-turn dialogue structure containing four roles: system, user, assistant, and tool. More critically, training data format must exactly match the input format during inference—if the model sees one message structure during training but receives a different structure during inference, severe performance degradation occurs. Therefore, format conversion is not merely a change in data organization but a crucial step in ensuring train-inference consistency.

**Chat Template Format and System Prompt Design**

The Chat Template format organizes conversations as message sequences containing four roles: system (system prompt), user (user request), assistant (assistant response, may include tool calls), and tool (tool response). The System Prompt design is particularly critical as it defines the model's role, available tools, and behavioral guidelines. We follow the "Less is More" principle in designing the System Prompt: centering on tool usage, clearly defining the functions and usage scenarios of six tools; providing strategic workflow guidance (anchor functional unit → extract inputs → extract outputs → validate completeness); listing classification criteria for 11 LCI categories; and offering key operational guidelines (such as batch searching, choosing between calculation and direct recording, energy classification, etc.).

**Document Context Injection**

To enable the model to "perceive" the document under analysis, we inject document context into the System Prompt. Specifically, we extract the first two chunks of the document as previews: Chunk 0 is typically the abstract or introduction, providing a research overview; Chunk 1 usually contains methodology or key data definitions. This design allows the model to understand the document's topic and structure before interaction begins, enabling more effective search strategies. The document context also includes the document name and session identifier, ensuring traceability of tool calls.

**Tool Call Sequence Reconstruction**

Records in the database are flattened action sequences arranged in chronological order that need to be reconstructed into dialogue turn structures conforming to Chat Template specifications. This conversion involves three levels of processing.

First is message role mapping. Each tool call record in the database needs to be split into two messages: an assistant message containing the tool_calls field, describing which tool the model decided to call and its parameters; immediately followed by a tool message containing the tool execution result. For example, a search_document record converts to: an assistant message carrying `{"name": "search_document", "arguments": {"query": ["titanium", "powder"]}}`, and a tool message carrying the returned document chunks. This one-to-one correspondence ensures the model learns the complete "decision-feedback" cycle.

Second is tool response content reconstruction. Responses from different tools need to be reconstructed according to their actual format during inference. search_document responses need to include matched document chunks with metadata; record_process_flow responses need to confirm successful recording and echo the recorded data; execute_calculation responses need to include the calculation process and results. Notably, get_session_summary tool responses need to be dynamically restored based on the call timestamp—including only data recorded before that action_id, not the session's final state. This ensures summary responses in training data match what the model actually sees during inference, avoiding information leakage.

Third is dialogue boundary determination. A complete training sample starts with a system message, contains one user message (user request), followed by multiple assistant-tool interaction turns, and ends with an assistant message without tool calls (final response). Correct dialogue boundary delineation ensures each sample represents a complete task execution process.

The converted data is output in JSONL format, with each line containing a complete dialogue sample, ready for subsequent data cleaning and reasoning generation stages.
