# Tool Ecosystem Principles
## LCA-LLM工具生态系统设计原理与协作机制

**文档类型**: 学术写作辅助文档  
**目标受众**: 研究人员、论文作者  
**版本**: 1.0  
**更新日期**: 2025-11-27

---

## 目录

1. [设计哲学](#1-设计哲学)
2. [双层知识库架构](#2-双层知识库架构)
3. [核心工具及其设计原理](#3-核心工具及其设计原理)
4. [工具协作机制](#4-工具协作机制)
5. [关键技术决策](#5-关键技术决策)
6. [ReAct工作流程](#6-react工作流程)

---

## 1. 设计哲学

### 1.1 核心理念

EcoLLM的工具生态系统遵循**"分离关注点"**（Separation of Concerns）和**"最小权限原则"**（Principle of Least Privilege）的设计哲学：

1. **文档处理与数据提取分离**：`process_document`工具仅负责PDF预处理和索引构建，不进行LCI数据的自动提取，确保LLM通过主动调用工具学习提取逻辑。

2. **临时与永久知识分离**：文献内容存储在会话级临时知识库，标准LCA数据存储在永久向量化数据库，避免污染背景数据库。

3. **检索与推理分离**：工具提供信息检索能力，但决策权完全交给LLM Agent，促进模型学习专家级推理模式。

### 1.2 设计目标

- **可解释性**：每个工具调用都有明确的意图（intent）和文档上下文（selected_chunk），建立完整的数据溯源链。
- **可训练性**：工具调用序列可导出为训练数据，支持模型微调学习工具使用模式。
- **可扩展性**：模块化架构支持新工具的快速集成，无需修改核心框架。

---

## 2. 双层知识库架构

### 2.1 架构设计动机

LCA数据提取任务涉及两类截然不同的知识源：

1. **前景文献（Foreground Literature）**：用户上传的特定工艺PDF文档，内容动态、会话专属、需要实时索引。
2. **背景数据库（Background Database）**：ecoinvent等标准LCI数据，内容静态、全局共享、需要持久存储。

传统单一知识库方案存在以下问题：
- 无法区分前景与背景数据
- 会话间数据污染
- 索引更新代价高昂

**双层架构**通过物理隔离解决上述问题。

### 2.2 临时知识库（Temporary Knowledge Base）

> **技术实现细节**见 `TECHNOLOGY_STACK_GUIDE.md` §4.2.1

**设计原理**：

1. **会话隔离**：每个session创建独立的ChromaDB实例和临时目录，确保多用户并发安全。

2. **轻量级向量化**：
   - 使用通用文本嵌入模型（384维）
   - 平衡检索精度与索引速度
   - 不需要与背景数据库模型一致（因为不跨库检索）

3. **自动清理机制**：
   - 析构函数触发资源释放
   - 三次重试确保目录删除
   - 防止临时文件累积导致存储泄露

**实现要点**：
- 每个会话创建独立的向量存储实例
- 使用临时目录存储索引文件
- 会话结束时自动清理资源
- 支持并发多用户访问

### 2.3 永久LCI数据库（Permanent LCI Database）

> **技术实现细节**见 `TECHNOLOGY_STACK_GUIDE.md` §4.2.2

**设计原理**：

1. **混合检索策略**：
   - 向量搜索：捕捉语义相似性（如"electricity" ≈ "power consumption"）
   - 关键词搜索：确保术语精准匹配（如"steel production"）
   - 两者结合提升召回率和准确率

2. **专业领域优化**：
   - 使用针对专业术语优化的嵌入模型
   - 高维向量（1024维）提升语义表征能力
   - 与主LLM模型同源，确保语义空间对齐

3. **延迟加载优化**：
   - 嵌入模型仅在首次搜索时加载（节省内存）
   - MongoDB连接池复用（降低连接开销）

**实现要点**：
- 向量搜索与关键词搜索并行执行
- 结果按UUID去重，避免重复
- 按相似度排序，返回top-k结果
- 支持可配置的相似度阈值过滤

### 2.4 双层架构的协作模式

```
┌─────────────────────────────────────────────────────────┐
│  用户上传PDF → process_document                          │
│  ├─ 创建临时知识库（Session-specific ChromaDB）          │
│  ├─ 使用all-MiniLM-L6-v2向量化（384维）                  │
│  └─ 返回session_id + full_text                          │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│  LLM推理 → search_document（前景检索）                    │
│  ├─ 查询临时知识库                                        │
│  ├─ 语义搜索 + 智能排序                                   │
│  └─ 返回相关文档片段                                      │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│  LLM推理 → search_lci_database（背景检索）                │
│  ├─ 查询永久LCI数据库                                     │
│  ├─ 混合搜索（Qwen3-embedding + 关键词）                  │
│  └─ 返回标准LCA数据                                       │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│  LLM决策 → record_process_flow（数据记录）                │
│  ├─ 结合前景与背景信息                                    │
│  ├─ 记录提取的LCI数据                                     │
│  └─ 建立数据溯源链                                        │
└─────────────────────────────────────────────────────────┘
```

---

## 3. 核心工具及其设计原理

### 3.1 process_document - PDF预处理工具

#### 设计动机

第一阶段微调目标是训练LLM学习**通过工具调用**完成LCI数据提取。如果`process_document`自动提取数据，会导致：
- LLM绕过工具调用直接获取数据
- 训练数据失去工具使用序列
- 模型无法学习提取决策逻辑

因此，该工具被设计为**纯文档预处理器**。

#### 工作原理

**输入**：
- PDF文件的base64编码内容
- 文件名

**处理流程**：

1. **会话创建**：
   ```python
   session_id = self.session_manager.create_session(filename)
   ```
   生成唯一session_id，用于后续所有工具调用。

2. **PDF解析**：
   - 使用`TableAwareChunker`进行表格感知分块
   - 识别表格区域并序列化为Markdown格式
   - 保持语义完整性（600字符块，150字符重叠）

3. **向量化索引**：
   ```python
   temp_kb = TemporaryKnowledgeBase(collection_name=f"session_{session_id}")
   temp_kb.add_documents(documents)
   ```
   为每个chunk生成384维语义向量，建立搜索索引。

4. **元数据存储**：
   ```python
   session_data.metadata = {
       "filename": filename,
       "total_pages": page_count,
       "total_chunks": chunk_count,
       "processing_timestamp": timestamp
   }
   ```

**输出**：
- `session_id`：会话标识符
- `full_text`：完整文档文本（供LLM浏览）
- 元数据：页数、分块数等统计信息

**关键设计点**：
- ✅ **不提取LCI数据**：确保LLM必须主动调用`search_document`
- ✅ **返回全文**：允许LLM理解文档整体结构
- ✅ **建立索引**：为后续语义搜索提供基础设施

### 3.2 search_document - 文档语义搜索工具

#### 设计动机

LLM需要从数百页PDF中定位特定信息（如"能源消耗"、"原材料用量"），人工遍历不现实。语义搜索通过向量相似度快速定位相关片段。

#### 工作原理

**支持两种模式**：

1. **单查询模式**：搜索单个具体概念
   ```json
   {"query": "total energy consumption", "max_results": 5}
   ```

2. **批量查询模式**：搜索同义词或相关术语
   ```json
   {"queries": ["electricity", "energy", "power"], "deduplicate": true}
   ```

**智能排序机制**（保守版Boosting）：

基础相似度分数可能无法准确反映chunk对LCI提取的价值。系统引入三层增强机制：

1. **覆盖率提升（Coverage Boost）**：权重0.15
   ```python
   # 统计chunk中出现了多少个不同的查询关键词（语义匹配，阈值0.35）
   matched_keywords = sum(1 for kw in query_keywords if kw in chunk_content)
   coverage = matched_keywords / len(query_keywords)
   boost += coverage * 0.15
   ```
   **理由**：包含更多查询关键词的chunk更可能是信息丰富的"黄金段落"。

2. **数据密度提升（Data Density Boost）**：权重0.12
   ```python
   # 提取有意义的数字（仅排除年份1900-2100，不排除页码）
   # 理由：chunking时页码已被清除，且LCI数据常在1-999范围内
   relevant_numbers = [num for num in numbers if not is_year(num)]
   density = min(len(relevant_numbers) / 5.0, 1.0)
   boost += density * 0.12
   ```
   **理由**：LCI数据高度定量化，数字密集的chunk更可能包含关键参数。

3. **表格标记提升（Table Boost）**：权重0.18
   ```python
   pipe_count = content.count('|')
   if pipe_count >= 3:
       boost += 0.18  # 有表格
   ```
   **理由**：LCI数据常以表格形式呈现，Markdown表格标记是强信号。

**最终排序**：
```python
final_score = similarity_score + coverage_boost + density_boost + table_boost
# 范围：[0, 1.45]，其中1.0来自相似度，0.45来自增强
```

**输出格式**：
```json
{
  "success": true,
  "query": "energy consumption",
  "results": [
    {"chunk_id": "0", "content": "extracted content..."},
    {"chunk_id": "5", "content": "another relevant chunk..."}
  ]
}
```

**批量搜索三阶段处理流程**：
```
阶段 1: 收集所有候选结果（不截断）
- 每个 query 独立搜索，过滤 similarity < min_similarity
- 不限制每个 query 的结果数量

阶段 2: 智能去重（保留最高相似度）
- 基于 chunk_id 去重
- 同一 chunk 被多个 query 命中时，保留最高相似度

阶段 3: 计算 boost，排序，截断
- 计算 coverage + density + table boost
- 按 boosted_score 排序
- 取 Top N（用户可配置 max_results）
```

**关键设计点**：
- ✅ **智能去重**：批量搜索时基于chunk_id去重，保留最高相似度
- ✅ **保守增强**：Boosting权重总和≤0.45，避免过度干扰原始相似度
- ✅ **模式适配**：支持chunks/sentences/key_points三种提取粒度
- ✅ **延迟截断**：排序后再截断，确保保留最优结果

### 3.3 search_lci_database - 背景数据库检索工具

#### 设计动机

文献中提取的前景数据（如"电力消耗52.5 kWh"）需要与背景数据库中的标准排放因子（如"China electricity mix: 0.85 kg CO2-eq/kWh"）关联，才能完成环境影响评估。

#### 工作原理

**混合检索策略**：

1. **向量搜索**（主路径）：
   ```python
   query_embedding = embedding_model.encode(query)  # 1024维向量
   similarities = [
       cosine_similarity(query_embedding, flow_embedding)
       for flow in vectorized_flows
   ]
   # 过滤：similarity >= 0.3（可配置阈值）
   ```
   **优势**：捕捉语义相似性，如"steel production" ≈ "iron smelting"

2. **关键词搜索**（辅助路径）：
   ```python
   # MongoDB全文索引
   text_results = flows_collection.find({"$text": {"$search": query}})
   
   # 类别匹配
   category_results = flows_collection.find({"categories": {"$regex": query}})
   
   # 产品匹配
   product_results = flows_collection.find({"reference_product": {"$regex": query}})
   ```
   **优势**：确保术语精准匹配，避免语义漂移

3. **结果合并与去重**：
   ```python
   merged = {}
   for result in vector_results:
       merged[result['uuid']] = result
   for result in keyword_results:
       if result['uuid'] not in merged:
           merged[result['uuid']] = result
   ```

**相似度阈值机制**：

默认阈值0.3是经验平衡点：
- 阈值过低（<0.2）：引入噪声数据
- 阈值过高（>0.5）：漏掉相关结果
- 0.3：平衡准确率（Precision）和召回率（Recall）

**输出示例**：
```json
{
  "success": true,
  "query": "steel production",
  "results": [
    {
      "name": "Steel, electric arc furnace",
      "category": "Materials/Metals",
      "unit": "kg",
      "similarity_score": 0.92,
      "carbon_footprint": "1.85 kg CO2-eq/kg"
    }
  ]
}
```

### 3.4 build_lca_system - LCA系统构建工具

#### 设计动机

从零编写pyLCA代码需要深厚的编程和LCA知识。该工具结合前景文献和背景数据库信息，自动生成可执行的LCA建模代码。

#### 工作原理

**输入**：
- `system_description`：如"光伏板生产系统"
- `functional_unit`：如"1 kWp"
- `impact_categories`：如["GWP", "AP", "EP"]

**处理流程**：

1. **上下文收集**：
   ```python
   pdf_context = temp_kb.query(instruction)  # 从文献提取工艺信息
   lci_data = permanent_lci_db.search_flows(instruction)  # 获取背景数据
   ```

2. **代码生成**（调用LLM Service）：
   ```python
   code_context = {
       "pdf_context": pdf_context,
       "lci_data": lci_data,
       "parameters": {
           "system_description": system_description,
           "functional_unit": functional_unit,
           "impact_categories": impact_categories
       }
   }
   generated_code = llm_service.generate_pylca_code(code_context)
   ```

3. **代码验证与返回**：
   - 语法检查（Python AST解析）
   - 依赖检查（brightway2/pyLCA库调用）
   - 返回可执行代码字符串

**输出**：
```json
{
  "success": true,
  "generated_code": "import brightway2 as bw\n...",
  "code_length": 1250,
  "system_info": {...}
}
```

---

## 4. 工具协作机制

### 4.1 典型工作流序列

**场景：从PDF提取钢铁生产工艺的LCI数据**

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: 文档预处理                                            │
├─────────────────────────────────────────────────────────────┤
│ Tool: process_document                                      │
│ Input: PDF file (base64)                                    │
│ Output: session_id, full_text                               │
│ Purpose: 建立检索基础设施，不提取数据                          │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 2: 搜索能源消耗信息                                       │
├─────────────────────────────────────────────────────────────┤
│ Tool: search_document                                        │
│ Input: query="energy consumption"                           │
│ Output: chunks mentioning "electricity 52.5 kWh"            │
│ Purpose: 定位前景数据                                         │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 3: 查询标准排放因子                                       │
├─────────────────────────────────────────────────────────────┤
│ Tool: search_lci_database                                    │
│ Input: query="China electricity mix"                        │
│ Output: carbon_footprint="0.85 kg CO2-eq/kWh"               │
│ Purpose: 获取背景数据                                         │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 4: 记录LCI流数据                                         │
├─────────────────────────────────────────────────────────────┤
│ Tool: record_process_flow                                    │
│ Input: name="Electricity", value=52.5, unit="kWh"           │
│ Output: action_id="ACT_0001"                                 │
│ Purpose: 结构化存储提取结果，建立溯源链                         │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 5: 构建LCA系统                                           │
├─────────────────────────────────────────────────────────────┤
│ Tool: build_lca_system                                       │
│ Input: system_description, functional_unit                   │
│ Output: executable pyLCA code                                │
│ Purpose: 自动化建模，生成影响评估代码                           │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 数据流转机制

**前景数据流**：
```
PDF文档 
  → [process_document] → 
临时知识库（ChromaDB） 
  → [search_document] → 
LLM推理 
  → [record_flow] → 
MongoDB（结构化存储）
```

**背景数据流**：
```
EcoInvent数据库（预向量化） 
  → [search_lci_database] → 
LLM推理（与前景数据结合） 
  → [build_lca_system] → 
pyLCA代码
```

**溯源链流**：
```
每个工具调用生成action_id 
  → MongoDB记录：
     - tool_name
     - intent (select_best/refine_same/calculate)
     - selected_chunk (数据来源)
     - timestamp
  → 导出训练数据时保留完整决策链
```

### 4.3 会话状态管理

**SessionManager职责**：
- 创建唯一session_id
- 存储临时知识库引用
- 管理会话生命周期（自动清理）

**状态共享机制**：
```python
session_data = {
    "session_id": "uuid-xxx",
    "knowledge_base": TemporaryKnowledgeBase(...),  # 共享检索接口
    "documents": [Document(...)],  # 原始chunks
    "metadata": {...},  # 文档元信息
    "generated_code": "...",  # 最终生成的代码
}
```

所有工具通过`session_id`访问共享状态，避免数据重复传递。

---

## 5. 关键技术决策

### 5.1 为什么使用两种不同的嵌入模型？

**临时知识库**：通用文本嵌入模型（384维）
- 优化目标：通用文本语义理解
- 训练数据：大规模通用语料
- 适用场景：文献文本检索
- 性能特点：快速索引，低内存占用

**永久LCI数据库**：专业领域嵌入模型（1024维）
- 优化目标：专业领域知识建模
- 训练数据：包含中文专业语料
- 适用场景：LCA术语和流程检索
- 性能特点：高精度召回，语义对齐

**核心理由**：
1. 两个知识库**不需要跨库检索**，无需向量空间对齐
2. 临时库优先考虑速度和内存效率（文献数量大）
3. 永久库优先考虑精度和专业性（术语匹配要求高）
4. 专业模型与主LLM同源，减少检索-生成语义gap

> **具体模型选择与性能对比**见 `TECHNOLOGY_STACK_GUIDE.md` §4.2

### 5.2 为什么采用保守的Boosting策略？

**问题**：过度Boosting可能干扰原始语义相似度。

**解决方案**：限制增强权重总和≤0.45

| 增强类型 | 权重 | 阈值/条件 |
|---------|------|----------|
| 覆盖率提升 | 0.15 | 关键词语义匹配度（阈值0.35） |
| 数据密度提升 | 0.12 | 5个有效数字为满分（仅过滤年份） |
| 表格标记提升 | 0.18 | pipe_count ≥ 3 |
| **总和** | **≤0.45** | 原始相似度仍占主导 |

**效果**：
- 在不破坏语义排序的前提下，提升信息丰富chunk的排名
- 避免"数据密集但语义无关"的chunk干扰结果

### 5.3 为什么需要批量搜索模式？

**场景**：搜索"能源消耗"，文献中可能使用：
- "electricity consumption"
- "energy usage"
- "power input"
- "electrical demand"

**单查询模式**：需要4次API调用，重复计算相似度。

**批量查询模式**：
```python
queries = ["electricity", "energy", "power"]
# 一次调用，自动去重，合并结果
```

**优势**：
- 提升召回率（Coverage）
- 减少API调用次数（降低推理成本）
- 自动去重相同chunk（避免冗余展示）

### 5.4 为什么选择600字符分块+150字符重叠？

**分块大小权衡**：

| 大小 | 优势 | 劣势 |
|-----|------|------|
| <300字符 | 精准定位 | 语义碎片化，上下文丢失 |
| 300-600字符 | **平衡点** | 适中 |
| >1000字符 | 完整上下文 | 相似度计算噪声大 |

**重叠策略**：
- 150字符重叠（25%）确保跨块信息不被割裂
- 例如："...功率为2.5 kW，运行时间8小时..."
  - 无重叠：Chunk 1可能在"运行时间8..."处截断
  - 有重叠：Chunk 2包含完整的"功率为2.5 kW，运行时间8小时"

**表格感知分块**：
- 检测表格边界，避免在表格中间切分
- 将完整表格序列化为Markdown格式保留在单个chunk
- LCI数据常以表格形式呈现，完整性至关重要

> **表格解析技术细节**见 `TECHNOLOGY_STACK_GUIDE.md` §5.2

---

## 6. ReAct工作流程

### 6.1 ReAct模式概述

EcoLLM采用**ReAct（Reasoning + Acting）**模式，结合推理（Thought）和行动（Action）：

```
Observation → Thought → Action → Observation → ...
```

**与传统Prompt Engineering的区别**：

| 维度 | 传统Prompt | ReAct with Tools |
|-----|-----------|------------------|
| 信息获取 | 一次性输入全部文档 | 主动调用search_document |
| 推理过程 | 黑盒 | 显式<think>标签记录 |
| 可解释性 | 低 | 高（完整工具调用链） |
| Token效率 | 低（重复传递长文档） | 高（按需检索） |

### 6.2 Prompt Engineering策略

**System Prompt结构**：

```markdown
# Role Definition
You are an expert LCA analyst specialized in extracting life cycle inventory data from academic literature.

# Available Tools
1. search_document: Semantic search in uploaded PDF
   - When to use: Looking for specific technical parameters
   - Example: {"query": "energy consumption", "max_results": 5}

2. search_lci_database: Query background LCI database
   - When to use: Need standard emission factors
   - Example: {"query": "China electricity mix"}

3. record_process_flow: Record extracted LCI data
   - When to use: Found quantified flow data with unit
   - Example: {"name": "Electricity", "value": 52.5, "unit": "kWh"}

# Workflow Guidelines
1. Start with search_document to locate foreground data
2. Use search_lci_database to find background references
3. Combine both sources to make informed decisions
4. Always record data with record_process_flow
5. Document your reasoning in <think> tags

# Output Format
<think>
I need to find energy consumption data. Let me search the document first.
</think>

<action>
{
  "tool": "search_document",
  "parameters": {"query": "energy consumption", "max_results": 5}
}
</action>
```

**关键设计点**：
- 明确角色定位（Expert LCA Analyst）
- 列举工具及使用场景（When to use）
- 提供具体示例（降低调用错误率）
- 规定输出格式（<think>和<action>标签）

### 6.3 Tool Calling机制

**调用流程**：

1. **LLM生成工具调用请求**：
   ```json
   {
     "tool": "search_document",
     "parameters": {
       "session_id": "uuid-xxx",
       "query": "electricity consumption",
       "max_results": 5
     }
   }
   ```

2. **后端执行工具**：
   ```python
   result = await tool_service.search_document(**parameters)
   ```

3. **返回结果注入对话历史**：
   ```json
   {
     "role": "tool",
     "name": "search_document",
     "content": "{\"success\": true, \"results\": [...]}"
   }
   ```

4. **LLM基于结果继续推理**：
   ```markdown
   <think>
   The search returned 3 chunks. Chunk 0 mentions "electricity consumption: 52.5 kWh per cycle". This is the data I need.
   </think>
   
   <action>
   {
     "tool": "record_process_flow",
     "parameters": {
       "name": "Electricity",
       "value": 52.5,
       "unit": "kWh",
       "selected_chunk": {"chunk_id": "0", "content": "..."}
     }
   }
   </action>
   ```

**错误处理**：
- 工具调用失败时返回错误信息（而非中断对话）
- LLM可根据错误信息调整策略（如降低相似度阈值）
- 记录失败调用用于后续分析和优化

### 6.4 训练数据生成

工具调用序列可导出为**STAO格式**（State-Thought-Action-Observation）训练数据：

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Extract LCI data from this document."
    },
    {
      "role": "assistant",
      "content": "<think>I should search for energy data first.</think>\n<action>{\"tool\": \"search_document\", ...}</action>"
    },
    {
      "role": "tool",
      "name": "search_document",
      "content": "{\"success\": true, \"results\": [...]}"
    },
    {
      "role": "assistant",
      "content": "<think>Found relevant data, recording it.</think>\n<action>{\"tool\": \"record_process_flow\", ...}</action>"
    }
  ]
}
```

**微调目标**：
- 学习何时调用何种工具
- 学习如何构造工具参数
- 学习如何基于工具返回结果做出决策

---

## 7. 与学术论文Methodology部分的对应关系

根据你的论文框架，各部分可对应如下：

### 2.1 Agent design: ReAct workflow for LCI extraction

**对应本文档**：
- §6 ReAct工作流程
- §6.3 Tool Calling机制
- §6.2 Prompt Engineering策略

**撰写建议**：
- 强调ReAct模式的优势（显式推理 + 主动检索）
- 用流程图展示Observation-Thought-Action循环
- 举例说明工具调用序列

### 2.1.1 Tool ecosystem

**对应本文档**：
- §3 核心工具及其设计原理
- §2 双层知识库架构
- §4 工具协作机制

**撰写建议**：
- 用表格对比前景检索（临时知识库）与背景检索（永久数据库）
- 解释工具设计的动机（如为何process_document不自动提取）
- 强调双层架构的隔离性和扩展性

### 2.1.2 ReAct loop: observation-thought-action

**对应本文档**：
- §6.1 ReAct模式概述
- §6.4 训练数据生成（STAO格式）

**撰写建议**：
- 与传统RAG（Retrieval-Augmented Generation）对比
- 展示\<think\>标签在可解释性中的作用
- 说明如何将对话序列转换为训练数据

### 2.1.3 Prompt engineering for tool calling

**对应本文档**：
- §6.2 Prompt Engineering策略
- §6.3 Tool Calling机制

**撰写建议**：
- 展示System Prompt的关键组成部分
- 说明如何通过Few-shot Examples降低调用错误率
- 讨论错误处理和自我修正机制

### 2.5 Technology Stack and Implementation

**对应本文档**：
- §2.2 临时知识库（技术栈：ChromaDB + all-MiniLM）
- §2.3 永久LCI数据库（技术栈：MongoDB + Qwen3-embedding）
- §5 关键技术决策

**撰写建议**：
- 用技术栈图展示各组件及其连接
- 说明模型选择的理由（如为何用两种嵌入模型）
- 提及性能优化（如延迟加载、连接池复用）

---

## 8. 关键数字与实验数据（供论文引用）

| 指标 | 数值 | 说明 |
|-----|------|------|
| **嵌入模型维度** | 384维（临时）/ 1024维（永久） | 平衡效率与精度 |
| **默认分块大小** | 600字符 | 保持语义完整性 |
| **分块重叠** | 150字符 | 避免信息割裂 |
| **默认相似度阈值** | 0.3 | 平衡准确率与召回率 |
| **Boosting权重总和** | ≤0.45 | 保守增强策略（Coverage 0.15 + Density 0.12 + Table 0.18） |
| **批量搜索处理** | 三阶段 | 收集→去重（保留最高相似度）→排序截断 |
| **会话隔离** | 独立临时目录 | 确保多用户并发安全 |

---

## 9. 总结

EcoLLM的工具生态系统通过以下关键设计实现高效、可解释、可训练的LCI数据提取：

1. **双层知识库架构**：物理隔离前景与背景数据，优化检索效率
2. **保守增强检索**：在不破坏语义的前提下提升数据密集chunk排名
3. **ReAct工作流**：显式推理过程，建立完整溯源链
4. **模块化工具设计**：每个工具职责单一，协作机制清晰

这些设计决策共同支撑了第一阶段微调目标：**训练LLM学会通过工具调用完成专家级LCI数据提取**。

---

**文档维护**: 如有技术更新或新增工具，请同步更新本文档对应章节。

**引用建议**: 
```bibtex
@misc{ecollm_tool_ecosystem_2025,
  title={Tool Ecosystem Principles: Design and Collaboration Mechanisms in EcoLLM},
  author={LCA-LLM Research Team},
  year={2025},
  note={Internal Technical Documentation}
}
```
