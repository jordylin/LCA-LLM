# LLM Tools Reference Manual
## LCA-LLM 2.0 工具调用参考手册

**目标受众**: LLM (Language Model Agent)  
**版本**: 2.1  
**最后更新**: 2025-11-12 (新增批量搜索功能)

---

## 📋 目录

1. [概述](#概述)
2. [核心工作流](#核心工作流)
3. [可用工具列表](#可用工具列表)
4. [工具详细说明](#工具详细说明)
5. [数据结构](#数据结构)
6. [Session Summary - 你的工作记忆](#session-summary---你的工作记忆)
7. [完整工作流示例](#完整工作流示例)
8. [错误处理](#错误处理)

---

## 概述

### 你的任务
作为LLM Agent，你的任务是从文献中提取LCA（生命周期评估）数据，并构建完整的LCI（生命周期清单）。

### 系统架构
- **文档检索**: 系统会为你提供相关的文档片段（chunks）
- **工具调用**: 你通过调用REST API工具来记录LCA数据
- **工作记忆**: 通过`get_session_summary`查询你已记录的所有数据
- **决策追踪**: 每个动作都会生成`action_id`，用于建立数据链

### 核心理念
你是一个**专家LCA分析师**，需要：
1. 从文档中提取原始参数
2. 执行必要的计算
3. 记录最终的LCI流数据
4. 保持完整的决策追踪链

---

## 核心工作流

### 三工具架构

```
┌─────────────────────────────────────────────────┐
│  Phase 1: 参数提取 (Parameter Extraction)        │
├─────────────────────────────────────────────────┤
│  Tool: record_parameter                         │
│  输入: 文档chunk                                  │
│  输出: action_id (如 ACT_0001)                   │
│  数据: parameter_name, value, unit              │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  Phase 2: 数学计算 (Mathematical Calculation)   │
├─────────────────────────────────────────────────┤
│  Tool: record_calculation                       │
│  输入: expression, variables                     │
│  输出: action_id (如 ACT_0003)                   │
│  依赖: data_dependencies = [ACT_0001, ACT_0002] │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  Phase 3: LCI记录 (Process Flow Recording)      │
├─────────────────────────────────────────────────┤
│  Tool: record_process_flow                      │
│  输入: name, value, unit, category, io_type     │
│  输出: action_id (如 ACT_0004)                   │
│  链接: link_to = ACT_0003 (自动)                │
└─────────────────────────────────────────────────┘
```

---

## 可用工具列表

| 工具名称 | 端点 | 用途 | 是否需要文档上下文 |
|---------|------|------|------------------|
| `record_parameter` | `/tools/record-parameter` | 从文档中提取原始参数值 | ✅ 是 |
| `record_calculation` | `/tools/record-calculation` | 记录数学计算过程 | ❌ 否 |
| `record_process_flow` | `/tools/record-flow` | 记录最终LCI流数据 | 可选 |
| `record_scope` | `/tools/record-scope` | 定义LCA范围 | ✅ 是 |
| `pivot_query` | `/tools/pivot-query` | 切换搜索方向 | ❌ 否 |
| `get_session_summary` | `/tools/session-summary` | 查询工作记忆 | ❌ 否 |
| `execute_calculation` | `/tools/execute-calculation` | 执行数学运算 | ❌ 否 |
| `search_document` | `/tools/search-document` | 文档搜索（支持批量） | ❌ 否 |

---

## 工具详细说明

### 1. `record_parameter` - 参数提取工具

**用途**: 从文档片段中提取原始参数值（如功率、时间、质量等）

**何时使用**:
- 文档中明确提到了某个量化参数
- 这个参数后续会用于计算
- 你需要追溯参数的来源

**API端点**: `POST /tools/record-parameter`

**请求参数**:
```json
{
  "session_id": "string (必填)",
  "parameter_name": "string (必填, 描述性名称, 如 'motor_power')",
  "parameter_value": "float (必填, 如 10.5)",
  "parameter_unit": "string (可选, 如 'kW')",
  "intent": "select_best | refine_same (必填)",
  "link_to": "string (可选, action_id)",
  "search_query": "string (可选)",
  "search_context": [
    {
      "chunk_id": "string",
      "content": "string",
      "score": "float"
    }
  ],
  "selected_chunk": {
    "chunk_id": "string (必填)",
    "content": "string (必填)",
    "score": "float"
  }
}
```

**响应**:
```json
{
  "success": true,
  "message": "Parameter recorded with action_id: ACT_0001",
  "data": {
    "new_action_id": "ACT_0001",
    "parameter_name": "motor_power",
    "parameter_value": 10.5,
    "parameter_unit": "kW"
  }
}
```

**MongoDB存储结构**:
```json
{
  "_id": "ObjectId(...)",
  "action_id": "ACT_0001",
  "session_id": "session_123",
  "record_type": "parameter",
  "intent": "select_best",
  "link_to": null,
  "timestamp": "2025-10-30T10:30:00Z",
  
  "parameter_name": "motor_power",
  "parameter_value": 10.5,
  "parameter_unit": "kW",
  
  "search_query": "motor power consumption",
  "search_context": [...],
  "selected_chunk": {
    "chunk_id": "CHUNK_047",
    "content": "The motor consumes 10.5 kW during operation...",
    "score": 0.95
  }
}
```

**关键决策字段**:
- `intent`:
  - `select_best`: 从多个候选chunk中首次选择最佳的一个
  - `refine_same`: 从**同一个信息丰富的chunk**中继续提取**不同的参数**（第2个、第3个...）
- `link_to`: 如果是`refine_same`，应链接到上一个从同一chunk提取的参数的action_id

**重要**：`refine_same`不是"重新选择更好的chunk"，而是"继续从同一个chunk提取更多参数"

**示例调用**:

**场景1：首次从某个chunk提取参数**
```python
# 从CHUNK_047首次提取电机功率
response1 = call_tool(
    "record_parameter",
    {
        "session_id": "session_123",
        "parameter_name": "motor_power",
        "parameter_value": 10.5,
        "parameter_unit": "kW",
        "intent": "select_best",  # ← 首次提取
        "selected_chunk": {
            "chunk_id": "CHUNK_047",
            "content": "The motor consumes 10.5 kW during 5-hour operation...",
            "score": 0.95
        }
    }
)
# 得到: ACT_0001
```

**场景2：从同一个chunk继续提取其他参数**
```python
# 从同一个CHUNK_047继续提取运行时间
response2 = call_tool(
    "record_parameter",
    {
        "session_id": "session_123",
        "parameter_name": "operation_time",
        "parameter_value": 5.0,
        "parameter_unit": "h",
        "intent": "refine_same",  # ← 继续从同一chunk提取
        "link_to": "ACT_0001",    # ← 链接到上一个从此chunk提取的参数
        "selected_chunk": {
            "chunk_id": "CHUNK_047",  # ← 同一个chunk
            "content": "The motor consumes 10.5 kW during 5-hour operation...",
            "score": 0.95
        }
    }
)
# 得到: ACT_0002
```

---

### 2. `record_calculation` - 计算记录工具

**用途**: 记录纯数学计算过程，**不需要文档上下文**

**何时使用**:
- 需要对已提取的参数进行数学运算
- 需要建立参数之间的计算关系
- 需要记录计算逻辑供后续审计

**API端点**: `POST /tools/record-calculation`

**请求参数**:
```json
{
  "session_id": "string (必填)",
  "calculation_expression": "string (必填, 如 'motor_power * operation_time')",
  "calculation_result": "float (必填)",
  "calculation_unit": "string (可选, 如 'kWh')",
  "data_dependencies": ["string (action_id数组, 如 ['ACT_0001', 'ACT_0002'])"],
  "expert_decision": {
    "rationale": "string (必填, 纯自然语言, 不需要包含 'Depends on:')"
  }
}
```

**响应**:
```json
{
  "success": true,
  "message": "Calculation recorded with action_id: ACT_0003",
  "data": {
    "new_action_id": "ACT_0003",
    "calculation_result": 52.5,
    "calculation_unit": "kWh"
  }
}
```

**MongoDB存储结构**:
```json
{
  "_id": "ObjectId(...)",
  "action_id": "ACT_0003",
  "session_id": "session_123",
  "record_type": "calculation",
  "intent": "calculate",
  "link_to": null,
  "timestamp": "2025-10-30T10:35:00Z",
  
  "calculation_expression": "motor_power * operation_time",
  "calculation_result": 52.5,
  "calculation_unit": "kWh",
  "data_dependencies": ["ACT_0001", "ACT_0002"],
  
  "expert_decision": {
    "rationale": "Calculate total energy consumption for the production cycle"
  }
}
```

**关键字段**:
- `data_dependencies`: **结构化字段**，明确列出依赖的parameter action_ids
  - 这是100%可靠的依赖关系
  - 不要在rationale中写"Depends on: ACT_XXX"
  - rationale应该是纯自然语言
- `calculation_expression`: 数学表达式（可以是符号或实际值）
- `rationale`: 解释为什么要做这个计算

**示例调用**:
```python
# 场景：计算能耗 = 功率 × 时间
response = call_tool(
    "record_calculation",
    {
        "session_id": "session_123",
        "calculation_expression": "motor_power * operation_time",
        "calculation_result": 52.5,
        "calculation_unit": "kWh",
        "data_dependencies": ["ACT_0001", "ACT_0002"],
        "expert_decision": {
            "rationale": "Calculate total energy consumption for one production cycle"
        }
    }
)
# 得到: ACT_0003
```

**重要**: 在调用此工具前，你应该：
1. 从`session_summary`查询已记录的parameters
2. 找到需要的参数的`action_id`
3. 将这些`action_id`填入`data_dependencies`

---

### 3. `record_process_flow` - LCI流记录工具

**用途**: 记录最终的LCI（生命周期清单）流数据

**何时使用**:
- 已经得到了最终的量化结果
- 需要记录输入或输出流
- 需要标准化的LCI分类

**API端点**: `POST /tools/record-flow`

**请求参数**:
```json
{
  "session_id": "string (必填)",
  "name": "string (必填, 流名称)",
  "value": "float (必填)",
  "unit": "string (必填)",
  "io_type": "Input | Output (必填)",
  "category": "string (必填, 见下方分类列表)",
  "intent": "select_best | refine_same | calculate (可选)",
  "link_to": "string (可选, action_id)",
  "search_query": "string (可选)",
  "search_context": [],
  "selected_chunk": {}
}
```

**标准LCI分类** (category字段):

**Input类型**:
- `raw_material` - 原材料
- `energy` - 能源
- `water` - 水资源
- `land_use` - 土地使用
- `intermediate_product` - 中间产品
- `auxiliary_material` - 辅助材料

**Output类型**:
- `product` - 产品
- `co_product` - 联产品
- `emission_to_air` - 大气排放
- `emission_to_water` - 水体排放
- `emission_to_soil` - 土壤排放
- `waste` - 废物

**响应**:
```json
{
  "success": true,
  "message": "Process flow recorded with action_id: ACT_0004",
  "data": {
    "new_action_id": "ACT_0004",
    "name": "Electricity",
    "value": 52.5,
    "unit": "kWh",
    "category": "energy"
  }
}
```

**MongoDB存储结构**:
```json
{
  "_id": "ObjectId(...)",
  "action_id": "ACT_0004",
  "session_id": "session_123",
  "record_type": "flow",
  "intent": "calculate",
  "link_to": "ACT_0003",
  "timestamp": "2025-10-30T10:40:00Z",
  
  "name": "Electricity",
  "value": 52.5,
  "unit": "kWh",
  "io_type": "Input",
  "category": "energy",
  
  "search_query": null,
  "search_context": [],
  "selected_chunk": null,
  
  "expert_decision": {
    "rationale": "Energy input for motor operation"
  }
}
```

**link_to自动规则**:
系统会自动设置`link_to`：
- 如果上一个动作是`calculation` (ACT_0003)
- 并且当前flow**没有**文档上下文
- 系统会自动设置 `link_to = ACT_0003`

**示例调用**:
```python
# 场景：记录能源输入（来自计算）
response = call_tool(
    "record_process_flow",
    {
        "session_id": "session_123",
        "name": "Electricity",
        "value": 52.5,
        "unit": "kWh",
        "io_type": "Input",
        "category": "energy",
        "intent": "calculate",
        "expert_decision": {
            "rationale": "Energy consumption calculated from motor power and operation time"
        }
    }
)
# 得到: ACT_0004
# link_to会自动设置为ACT_0003
```

---

### 4. `record_scope` - LCA范围定义工具

**用途**: 定义LCA研究的范围（功能单位、系统边界等）

**API端点**: `POST /tools/record-scope`

**请求参数**:
```json
{
  "session_id": "string (必填)",
  "scope_type": "Function Unit | System Boundary | Time Horizon | Geographic Scope | Technology Level | Data Quality | Allocation Method | Impact Categories | Cut-off Criteria | Assumptions (必填)",
  "content": "string (必填)",
  "intent": "select_best | refine_same (必填)",
  "link_to": "string (可选)",
  "search_query": "string (可选)",
  "search_context": [],
  "selected_chunk": {
    "chunk_id": "string (必填)",
    "content": "string (必填)",
    "score": "float"
  }
}
```

**示例调用**:
```python
response = call_tool(
    "record_scope",
    {
        "session_id": "session_123",
        "scope_type": "Function Unit",
        "content": "1 kg of printed ABS component",
        "intent": "select_best",
        "selected_chunk": {
            "chunk_id": "CHUNK_001",
            "content": "The functional unit is defined as 1 kg of printed component...",
            "score": 0.98
        }
    }
)
```

---

### 5. `pivot_query` - 查询切换工具

**用途**: 当前搜索结果不满意时，切换搜索方向

**API端点**: `POST /tools/pivot-query`

**请求参数**:
```json
{
  "session_id": "string (必填)",
  "pivot_reason": "string (必填, 为什么要pivot)",
  "new_query": "string (可选, 新的搜索查询)",
  "link_to": "string (可选, 上一个动作的action_id)"
}
```

**示例调用**:
```python
response = call_tool(
    "pivot_query",
    {
        "session_id": "session_123",
        "pivot_reason": "Current results focus on material properties, but I need energy consumption data",
        "new_query": "energy consumption 3D printing",
        "link_to": "ACT_0005"
    }
)
```

---

### 6. `get_session_summary` - 工作记忆查询工具 ⭐

**用途**: 查询你在当前session中已记录的所有数据（你的"工作记忆"）

**API端点**: `GET /tools/session-summary/{session_id}?format=text`

**⚠️ 重要**:
- **必须使用** `format=text` (默认值)，为LLM优化的简洁文本格式
- **节省约80% tokens** 相比JSON格式
- 这是 **"P → S → C"工作流** 的必经步骤

**这是你最重要的工具之一！** 在执行计算前，你**必须**调用此工具来：
1. 查询已记录的parameters
2. 获取parameter的`action_id` (用于data_dependencies)
3. 查看已有的calculations
4. 检查LCI数据完整性
5. 避免重复记录

**Text格式响应示例** (默认):
```
=== Recorded Parameters ===
ACT_0001: motor_power = 10.5 kW
ACT_0002: operation_time = 5.0 h

=== Recorded Calculations ===
ACT_0003: energy = motor_power * operation_time = 52.5 kWh
  └─ Dependencies: ACT_0001 (motor_power), ACT_0002 (operation_time)

=== Recorded Flows ===
Input/energy: Electricity = 52.5 kWh (ACT_0004)

=== Statistics ===
Total: 4 actions | Parameters: 2 | Calculations: 1 | Flows: 1
```

**为什么使用Text格式?**
- ✅ **极简**: 只显示action_id和关键值
- ✅ **快速扫描**: 一眼找到需要的action_id
- ✅ **Token友好**: 显著降低推理成本
- ✅ **人类可读**: 便于调试和理解

**完整JSON格式**: 见后续章节 [Session Summary详解](#session-summary---你的工作记忆)

---

### 7. `execute_calculation` - 计算执行工具

**用途**: 执行实际的数学计算（辅助工具）

**API端点**: `POST /tools/execute-calculation`

**请求参数**:
```json
{
  "expression": "string (必填, 如 '10.5 * 5')",
  "unit": "string (可选)"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "expression": "10.5 * 5",
    "result": 52.5,
    "unit": "kWh"
  }
}
```

**注意**: 此工具只执行计算，**不记录**到数据库。记录需要使用`record_calculation`。

---

### 8. `search_document` - 文档搜索工具 🆕

**用途**: 在已处理的文档中进行语义搜索，**支持单查询和批量查询**

**API端点**: `POST /tools/search-document`

**核心特性**:
- **单查询模式**: 搜索单个具体概念
- **批量查询模式**: 一次搜索多个同义词或相关术语，自动去重
- **智能去重**: 基于chunk_id去除重复结果

**请求参数**:
```json
{
  "session_id": "string (必填)",
  
  // 单查询模式（与queries二选一）
  "query": "string (可选, 如 'energy consumption')",
  "max_results": "integer (可选, 默认5)",
  
  // 批量查询模式（与query二选一）
  "queries": ["string (可选, 如 ['electricity', 'energy', 'power'])"],
  "max_results_per_query": "integer (可选, 默认3)",
  "max_total_results": "integer (可选, 默认10)",
  "deduplicate": "boolean (可选, 默认true)",
  
  // 通用参数
  "extract_mode": "string (可选, 'chunks'|'sentences'|'key_points', 默认'chunks')",
  "min_similarity": "float (可选, 默认0.3)"
}
```

**响应（单查询）**:
```json
{
  "success": true,
  "message": "Found 3 results",
  "query": "energy consumption",
  "results": [
    {
      "rank": 1,
      "content": "...",
      "similarity_score": 0.85,
      "metadata": {"chunk_id": "CHUNK_047"}
    }
  ]
}
```

**响应（批量查询）**:
```json
{
  "success": true,
  "message": "Batch search completed: 3 queries, 8 results (2 deduplicated)",
  "queries": ["electricity", "energy", "power"],
  "total_results": 8,
  "results_breakdown": {
    "electricity": 3,
    "energy": 3,
    "power": 2
  },
  "results": [...]
}
```

**使用场景**:

**单查询**: 具体概念
```json
{
  "session_id": "session_123",
  "query": "total energy consumption",
  "max_results": 5
}
```

**批量查询**: 同义词搜索
```json
{
  "session_id": "session_123",
  "queries": ["electricity", "energy", "power"],
  "max_results_per_query": 3,
  "deduplicate": true
}
```

**重要提示**:
- 批量搜索会在MongoDB中记录为`search_query: ["term1", "term2"]`（列表格式）
- 单查询会记录为`search_query: "term"`（字符串格式）
- 使用批量搜索可以一次性捕捉多种表述，提高搜索效率

---

## 数据结构

### action_id 生成规则

每个动作都会生成唯一的`action_id`：
- 格式: `ACT_XXXX` (XXXX是4位数字，从0001开始)
- 在同一个session内递增
- 用于建立数据追踪链

### intent 决策类型

| Intent | 含义 | 何时使用 |
|--------|------|---------|
| `select_best` | 从多个候选chunk中选择最佳 | 首次从某个chunk提取数据 |
| `refine_same` | 从**同一个chunk**继续提取 | 同一个信息丰富的chunk中提取第2、3...个参数 |
| `pivot_query` | 切换搜索方向 | 当前搜索结果不相关，需要换个查询 |
| `calculate` | 执行计算 | 进行数学运算（无需chunk上下文） |

### link_to 链接机制

`link_to`用于建立**动作序列**链：

```
# 场景：从同一个黄金chunk中提取多个参数
ACT_0001 (parameter: printer_power = 2.5 kW)
    从 CHUNK_047 首次提取
    link_to = null

ACT_0002 (parameter: printing_time = 8.0 h)
    从 CHUNK_047 继续提取 (refine_same)
    link_to = ACT_0001  ← 表示"继续从同一chunk提取"

ACT_0003 (parameter: material_input = 1.2 kg)
    从 CHUNK_047 继续提取 (refine_same)
    link_to = ACT_0002  ← 链式关系

ACT_0004 (calculation: power * time = 20.0 kWh)
    data_dependencies = [ACT_0001, ACT_0002]  ← 数据依赖
    link_to = null

ACT_0005 (flow: Electricity, 20.0 kWh)
    link_to = ACT_0004  ← 自动链接到上一个calculation
```

**关键区别**:
- `link_to`: 动作序列（"这个动作是上一个动作的延续"或"来自同一来源"）
- `data_dependencies`: 数据依赖（"这个计算用到了哪些参数"，与chunk无关）

**重要说明**:
- `refine_same` + `link_to`: 表示从**同一个chunk**连续提取多个**不同参数**
- 不是"修正旧值"，而是"继续提取新参数"

---

## Session Summary - 你的工作记忆

### 概述

`get_session_summary`返回的是你在当前session中的**完整工作记忆**：
- 你定义的LCA范围
- 你提取的所有parameters
- 你执行的所有calculations
- 你记录的所有LCI flows
- 完整的决策链

### 完整响应结构

```json
{
  "success": true,
  "data": {
    "session_id": "session_123",
    "created_at": "2025-10-30T10:00:00Z",
    
    // ========== 1. LCA范围定义 ==========
    "lca_scope": {
      "Function Unit": {
        "content": "1 kg of printed ABS component",
        "action_id": "ACT_0001",
        "selected_chunk": {...}
      },
      "System Boundary": {
        "content": "Cradle-to-gate: material production to part manufacturing",
        "action_id": "ACT_0002",
        "selected_chunk": {...}
      }
      // ... 其他scope类型
    },
    
    // ========== 2. 工艺流数据（按分类） ==========
    "process_flows": {
      "inputs": {
        "raw_material": [
          {
            "action_id": "ACT_0010",
            "name": "ABS plastic",
            "value": 1.2,
            "unit": "kg",
            "intent": "select_best",
            "link_to": null,
            "selected_chunk": {...},
            "timestamp": "2025-10-30T10:15:00Z"
          }
        ],
        "energy": [
          {
            "action_id": "ACT_0015",
            "name": "Electricity",
            "value": 52.5,
            "unit": "kWh",
            "intent": "calculate",
            "link_to": "ACT_0014",
            "selected_chunk": null,
            "timestamp": "2025-10-30T10:40:00Z"
          }
        ]
        // ... 其他输入分类
      },
      "outputs": {
        "product": [...],
        "emission_to_air": [...],
        "waste": [...]
        // ... 其他输出分类
      }
    },
    
    // ========== 3. 决策链分析 ==========
    "decision_chain": {
      "total_actions": 15,
      "actions_by_intent": {
        "select_best": 5,
        "refine_same": 3,
        "pivot_query": 2,
        "calculate": 1
      },
      "actions_by_type": {
        "scope": 2,
        "parameter": 3,
        "calculation": 1,
        "flow": 7,
        "pivot": 2
      },
      "link_relationships": 8,
      "action_sequence": [
        {
          "action_id": "ACT_0014",
          "record_type": "calculation",
          "intent": "calculate",
          "timestamp": "2025-10-30T10:35:00Z"
        },
        {
          "action_id": "ACT_0015",
          "record_type": "flow",
          "intent": "calculate",
          "link_to": "ACT_0014",
          "timestamp": "2025-10-30T10:40:00Z"
        }
        // ... 最近10个动作
      ]
    },
    
    // ========== 4. 参数分析（关键！） ==========
    "parameter_analysis": {
      "total_parameters": 3,
      "parameters": [
        {
          "action_id": "ACT_0005",
          "parameter_name": "motor_power",
          "parameter_value": 10.5,
          "parameter_unit": "kW",
          "intent": "select_best",
          "link_to": null,
          "timestamp": "2025-10-30T10:20:00Z"
        },
        {
          "action_id": "ACT_0006",
          "parameter_name": "operation_time",
          "parameter_value": 5.0,
          "parameter_unit": "h",
          "intent": "select_best",
          "link_to": null,
          "timestamp": "2025-10-30T10:25:00Z"
        },
        {
          "action_id": "ACT_0007",
          "parameter_name": "efficiency",
          "parameter_value": 0.85,
          "parameter_unit": "-",
          "intent": "select_best",
          "link_to": null,
          "timestamp": "2025-10-30T10:28:00Z"
        }
      ],
      "linked_parameters": 0
    },
    
    // ========== 5. 计算分析（关键！） ==========
    "calculation_analysis": {
      "total_calculations": 1,
      "calculations": [
        {
          "action_id": "ACT_0014",
          "calculation_expression": "motor_power * operation_time",
          "calculation_result": 52.5,
          "calculation_unit": "kWh",
          "data_dependencies": ["ACT_0005", "ACT_0006"],
          "expert_rationale": "Calculate total energy consumption",
          "timestamp": "2025-10-30T10:35:00Z"
        }
      ],
      "linked_calculations": 1
    },
    
    // ========== 6. Pivot分析 ==========
    "pivot_analysis": {
      "total_pivots": 2,
      "pivot_reasons": [
        "Need more specific energy data",
        "Switch from material to emissions"
      ],
      "success_after_pivot": 1,
      "continuous_pivots": 0
    },
    
    // ========== 7. 统计信息 ==========
    "statistics": {
      "total_scopes_defined": 2,
      "total_flows_recorded": 7,
      "total_parameters": 3,
      "total_calculations": 1,
      "flows_by_type": {
        "Input": 4,
        "Output": 3
      },
      "flows_by_category": {
        "raw_material": 1,
        "energy": 1,
        "water": 1,
        "auxiliary_material": 1,
        "product": 1,
        "emission_to_air": 1,
        "waste": 1
      }
    },
    
    // ========== 8. 完整性评估 ==========
    "completeness_assessment": {
      "has_functional_unit": true,
      "has_system_boundary": true,
      "has_inputs": true,
      "has_outputs": true,
      "min_flows_met": false,
      "data_quality_score": 0.75,
      "missing_scope_items": ["Time Horizon", "Geographic Scope"],
      "coverage": {
        "scope_coverage": 0.2,
        "input_categories": 4,
        "output_categories": 3
      }
    }
  }
}
```

### Text格式详解 (LLM专用)

**Text格式** (format=text) 是为LLM推理优化的极简格式：

```
=== Recorded Parameters ===
ACT_0001: motor_power = 10.5 kW
ACT_0002: operation_time = 5.0 h
ACT_0003: efficiency = 0.85 

=== Recorded Calculations ===
ACT_0004: energy_total = motor_power * operation_time = 52.5 kWh
  └─ Dependencies: ACT_0001 (motor_power), ACT_0002 (operation_time)

ACT_0005: energy_actual = energy_total * efficiency = 44.625 kWh
  └─ Dependencies: ACT_0004 (energy_total), ACT_0003 (efficiency)

=== Recorded Flows ===
Input/raw_material: ABS plastic = 1.2 kg (ACT_0006)
Input/energy: Electricity = 44.625 kWh (ACT_0007)
Output/product: Printed component = 1.0 kg (ACT_0008)

=== Recorded Scopes ===
Function Unit: 1 kg of printed ABS component (ACT_0009)
System Boundary: Cradle-to-gate analysis (ACT_0010)

=== Statistics ===
Total actions: 10
Flows: 3 | Parameters: 3 | Calculations: 2 | Scopes: 2
```

**关键特点**:
- 每行一个数据点
- action_id始终在最前
- Dependencies清晰标注父action_id和参数名
- 分类清晰 (Parameters / Calculations / Flows / Scopes)
- 无冗余JSON结构

---

### 如何使用Session Summary

#### 场景1: 执行计算前查询参数 (Text格式)

```python
# 1. 查询session summary (使用默认的text格式)
summary_text = call_tool("get_session_summary", {"session_id": "session_123"})

# 2. 从text中解析出需要的action_id
# Text格式示例:
# === Recorded Parameters ===
# ACT_0005: motor_power = 10.5 kW
# ACT_0006: operation_time = 5.0 h

# LLM可以直接从文本中识别action_id
# 例如: "我需要使用motor_power (ACT_0005) 和 operation_time (ACT_0006)"

# 3. 记录计算
call_tool("record_calculation", {
    "session_id": "session_123",
    "calculation_expression": "motor_power * operation_time",
    "calculation_result": 52.5,
    "calculation_unit": "kWh",
    "data_dependencies": ["ACT_0005", "ACT_0006"],  # 从text中获取
    "expert_decision": {
        "rationale": "Calculate total energy consumption"
    }
})
```

#### 场景1 (备选): 使用JSON格式 (仅当需要程序化处理时)

```python
# 1. 查询session summary (显式请求JSON格式)
summary = call_tool("get_session_summary", {"session_id": "session_123", "format": "json"})

# 2. 从parameter_analysis中找到需要的参数
parameters = summary["data"]["parameter_analysis"]["parameters"]

motor_power_id = None
operation_time_id = None

for param in parameters:
    if param["parameter_name"] == "motor_power":
        motor_power_id = param["action_id"]  # ACT_0005
        motor_power_value = param["parameter_value"]  # 10.5
    elif param["parameter_name"] == "operation_time":
        operation_time_id = param["action_id"]  # ACT_0006
        operation_time_value = param["parameter_value"]  # 5.0

# 3. 记录计算，明确data_dependencies
call_tool("record_calculation", {
    "session_id": "session_123",
    "calculation_expression": "motor_power * operation_time",
    "calculation_result": 52.5,
    "calculation_unit": "kWh",
    "data_dependencies": [motor_power_id, operation_time_id],
    "expert_decision": {
        "rationale": "Calculate total energy consumption"
    }
})
```

#### 场景2: 检查数据完整性

```python
summary = call_tool("get_session_summary", {"session_id": "session_123"})

completeness = summary["data"]["completeness_assessment"]

if not completeness["has_functional_unit"]:
    # 需要先定义功能单位
    call_tool("record_scope", {...})

if completeness["min_flows_met"]:
    # 数据已足够，可以结束
    pass
else:
    # 继续提取数据
    pass
```

#### 场景3: 避免重复记录

```python
summary = call_tool("get_session_summary", {"session_id": "session_123"})

# 检查是否已记录过某个参数
existing_params = [p["parameter_name"] for p in summary["data"]["parameter_analysis"]["parameters"]]

if "motor_power" not in existing_params:
    # 尚未记录，可以记录
    call_tool("record_parameter", {...})
else:
    # 已存在，可能需要refine或直接使用
    pass
```

---

## 完整工作流示例

### 示例任务
从文献中提取3D打印的LCA数据，包括材料、能耗和废物。

### Step 1: 定义LCA范围

```python
# 1.1 记录功能单位
response1 = call_tool("record_scope", {
    "session_id": "print_lca_001",
    "scope_type": "Function Unit",
    "content": "1 kg of printed ABS component",
    "intent": "select_best",
    "selected_chunk": {
        "chunk_id": "CHUNK_001",
        "content": "...functional unit is 1 kg of printed part...",
        "score": 0.98
    }
})
# 得到: ACT_0001

# 1.2 记录系统边界
response2 = call_tool("record_scope", {
    "session_id": "print_lca_001",
    "scope_type": "System Boundary",
    "content": "Cradle-to-gate: material production to part manufacturing",
    "intent": "select_best",
    "selected_chunk": {
        "chunk_id": "CHUNK_002",
        "content": "...system boundary includes material extraction...",
        "score": 0.95
    }
})
# 得到: ACT_0002
```

### Step 2: 提取参数

```python
# 2.1 提取打印机功率
response3 = call_tool("record_parameter", {
    "session_id": "print_lca_001",
    "parameter_name": "printer_power",
    "parameter_value": 2.5,
    "parameter_unit": "kW",
    "intent": "select_best",
    "selected_chunk": {
        "chunk_id": "CHUNK_015",
        "content": "The 3D printer consumes 2.5 kW during operation...",
        "score": 0.92
    }
})
# 得到: ACT_0003

# 2.2 提取打印时间
response4 = call_tool("record_parameter", {
    "session_id": "print_lca_001",
    "parameter_name": "printing_time",
    "parameter_value": 8.0,
    "parameter_unit": "h",
    "intent": "select_best",
    "selected_chunk": {
        "chunk_id": "CHUNK_016",
        "content": "Printing time for 1 kg component is approximately 8 hours...",
        "score": 0.89
    }
})
# 得到: ACT_0004

# 2.3 提取材料用量
response5 = call_tool("record_parameter", {
    "session_id": "print_lca_001",
    "parameter_name": "material_input",
    "parameter_value": 1.2,
    "parameter_unit": "kg",
    "intent": "select_best",
    "selected_chunk": {
        "chunk_id": "CHUNK_020",
        "content": "Material input is 1.2 kg ABS for 1 kg finished part...",
        "score": 0.94
    }
})
# 得到: ACT_0005
```

### Step 3: 执行计算

```python
# 3.1 首先查询session summary，获取参数action_ids
summary = call_tool("get_session_summary", {"session_id": "print_lca_001"})
parameters = summary["data"]["parameter_analysis"]["parameters"]

# 3.2 找到需要的参数
printer_power_id = None
printing_time_id = None

for param in parameters:
    if param["parameter_name"] == "printer_power":
        printer_power_id = param["action_id"]  # ACT_0003
        printer_power_value = param["parameter_value"]  # 2.5
    elif param["parameter_name"] == "printing_time":
        printing_time_id = param["action_id"]  # ACT_0004
        printing_time_value = param["parameter_value"]  # 8.0

# 3.3 记录计算
response6 = call_tool("record_calculation", {
    "session_id": "print_lca_001",
    "calculation_expression": "printer_power * printing_time",
    "calculation_result": 20.0,
    "calculation_unit": "kWh",
    "data_dependencies": [printer_power_id, printing_time_id],
    "expert_decision": {
        "rationale": "Calculate total electricity consumption for printing 1 kg component"
    }
})
# 得到: ACT_0006
```

### Step 4: 记录LCI流

```python
# 4.1 记录材料输入（直接从参数）
response7 = call_tool("record_process_flow", {
    "session_id": "print_lca_001",
    "name": "ABS plastic",
    "value": 1.2,
    "unit": "kg",
    "io_type": "Input",
    "category": "raw_material",
    "intent": "select_best",
    "selected_chunk": {
        "chunk_id": "CHUNK_020",
        "content": "...",
        "score": 0.94
    }
})
# 得到: ACT_0007

# 4.2 记录能源输入（来自计算）
response8 = call_tool("record_process_flow", {
    "session_id": "print_lca_001",
    "name": "Electricity",
    "value": 20.0,
    "unit": "kWh",
    "io_type": "Input",
    "category": "energy",
    "intent": "calculate",
    "expert_decision": {
        "rationale": "Energy consumption from calculation"
    }
})
# 得到: ACT_0008
# link_to会自动设置为ACT_0006

# 4.3 记录产品输出
response9 = call_tool("record_process_flow", {
    "session_id": "print_lca_001",
    "name": "Printed ABS component",
    "value": 1.0,
    "unit": "kg",
    "io_type": "Output",
    "category": "product",
    "intent": "select_best",
    "selected_chunk": {
        "chunk_id": "CHUNK_001",
        "content": "...",
        "score": 0.98
    }
})
# 得到: ACT_0009

# 4.4 记录废物输出
response10 = call_tool("record_process_flow", {
    "session_id": "print_lca_001",
    "name": "Support material waste",
    "value": 0.2,
    "unit": "kg",
    "io_type": "Output",
    "category": "waste",
    "intent": "select_best",
    "selected_chunk": {
        "chunk_id": "CHUNK_025",
        "content": "Approximately 0.2 kg support material is removed and discarded...",
        "score": 0.87
    }
})
# 得到: ACT_0010
```

### Step 5: 检查完整性

```python
# 5.1 再次查询session summary
summary = call_tool("get_session_summary", {"session_id": "print_lca_001"})

# 5.2 检查完整性
completeness = summary["data"]["completeness_assessment"]

print(f"Has Functional Unit: {completeness['has_functional_unit']}")  # True
print(f"Has System Boundary: {completeness['has_system_boundary']}")  # True
print(f"Has Inputs: {completeness['has_inputs']}")  # True
print(f"Has Outputs: {completeness['has_outputs']}")  # True
print(f"Data Quality Score: {completeness['data_quality_score']}")  # 0.85

# 5.3 查看数据链
decision_chain = summary["data"]["decision_chain"]
print(f"Total Actions: {decision_chain['total_actions']}")  # 10
print(f"Link Relationships: {decision_chain['link_relationships']}")  # 1 (ACT_0008 -> ACT_0006)

# 5.4 查看完整的parameter和calculation链
parameters = summary["data"]["parameter_analysis"]["parameters"]
calculations = summary["data"]["calculation_analysis"]["calculations"]

print("Parameters:")
for param in parameters:
    print(f"  {param['action_id']}: {param['parameter_name']} = {param['parameter_value']} {param['parameter_unit']}")

print("\nCalculations:")
for calc in calculations:
    print(f"  {calc['action_id']}: {calc['calculation_expression']} = {calc['calculation_result']} {calc['calculation_unit']}")
    print(f"    Dependencies: {calc['data_dependencies']}")
```

### 完整的数据链

```
ACT_0001: Scope (Function Unit)
ACT_0002: Scope (System Boundary)

ACT_0003: Parameter (printer_power = 2.5 kW)
ACT_0004: Parameter (printing_time = 8.0 h)
ACT_0005: Parameter (material_input = 1.2 kg)

ACT_0006: Calculation (printer_power * printing_time = 20.0 kWh)
           data_dependencies = [ACT_0003, ACT_0004]

ACT_0007: Flow (Input/raw_material: ABS plastic, 1.2 kg)
ACT_0008: Flow (Input/energy: Electricity, 20.0 kWh)
           link_to = ACT_0006
ACT_0009: Flow (Output/product: Printed ABS component, 1.0 kg)
ACT_0010: Flow (Output/waste: Support material waste, 0.2 kg)
```

---

## 错误处理

### 常见错误及解决方案

#### 1. Missing Required Field

**错误**:
```json
{
  "success": false,
  "error": "Missing required field: parameter_name"
}
```

**原因**: 请求缺少必填字段

**解决**: 检查API文档，确保所有必填字段都提供了

---

#### 2. Invalid Category

**错误**:
```json
{
  "success": false,
  "error": "Invalid category for Input type"
}
```

**原因**: LCI分类不正确（如Input类型使用了emission_to_air）

**解决**: 查看标准LCI分类列表，选择正确的category

---

#### 3. Session Not Found

**错误**:
```json
{
  "success": false,
  "error": "Session not found"
}
```

**原因**: session_id不存在

**解决**: 
- 首次调用会自动创建session
- 确保session_id拼写正确
- 检查session是否已过期（长时间未活动）

---

#### 4. Invalid Calculation Expression

**错误**:
```json
{
  "success": false,
  "error": "Cannot evaluate expression"
}
```

**原因**: 计算表达式语法错误

**解决**: 
- 使用标准Python语法
- 支持: `+`, `-`, `*`, `/`, `**`, `()`, `sqrt()`, `log()`, `exp()`
- 示例: `10.5 * 5`, `sqrt(16)`, `(a + b) / 2`

---

#### 5. Data Dependencies Not Found

**警告**: 此错误不会阻止记录，但会影响数据完整性

**问题**: `data_dependencies`中的action_id不存在或不是parameter类型

**解决**:
1. 调用`get_session_summary`查询现有parameters
2. 确保引用的action_id确实存在
3. 确保引用的action是parameter类型（不是flow或calculation）

---

## 最佳实践

### 1. 始终查询后再计算

❌ **错误做法**:
```python
# 盲目假设参数存在
call_tool("record_calculation", {
    "data_dependencies": ["ACT_0001", "ACT_0002"],  # 可能不存在
    ...
})
```

✅ **正确做法**:
```python
# 先查询session summary
summary = call_tool("get_session_summary", {"session_id": "..."})
params = summary["data"]["parameter_analysis"]["parameters"]

# 找到正确的action_ids
power_id = [p["action_id"] for p in params if p["parameter_name"] == "power"][0]
time_id = [p["action_id"] for p in params if p["parameter_name"] == "time"][0]

# 使用正确的依赖
call_tool("record_calculation", {
    "data_dependencies": [power_id, time_id],
    ...
})
```

---

### 2. 使用描述性参数名

❌ **不好**:
```python
call_tool("record_parameter", {
    "parameter_name": "power",  # 太模糊
    ...
})
```

✅ **更好**:
```python
call_tool("record_parameter", {
    "parameter_name": "extruder_heater_power",  # 清晰明确
    ...
})
```

---

### 3. 保持rationale纯净

❌ **不要这样**:
```python
call_tool("record_calculation", {
    "expert_decision": {
        "rationale": "Calculate energy. Depends on: ACT_0001, ACT_0002"  # 不要手写依赖
    }
})
```

✅ **应该这样**:
```python
call_tool("record_calculation", {
    "data_dependencies": ["ACT_0001", "ACT_0002"],  # 依赖用结构化字段
    "expert_decision": {
        "rationale": "Calculate total energy consumption for one production cycle"  # 纯自然语言
    }
})
```

---

### 4. 定期检查完整性

```python
# 每完成一个阶段，检查一次
summary = call_tool("get_session_summary", {"session_id": "..."})
completeness = summary["data"]["completeness_assessment"]

if completeness["data_quality_score"] < 0.7:
    # 数据质量不足，需要补充
    missing = completeness["missing_scope_items"]
    print(f"Missing: {missing}")
```

---

### 5. 合理使用pivot

当搜索结果不满意时，及时pivot：

```python
# 发现搜索结果不相关
call_tool("pivot_query", {
    "session_id": "...",
    "pivot_reason": "Current results focus on material properties, but I need energy consumption data",
    "new_query": "3D printing energy consumption per kg"
})
```

---

### 6. 使用批量搜索提高效率 🆕

**何时使用批量搜索**:
- 搜索同义词或相关术语
- 需要覆盖多种表述方式
- 一次性查找多个相关参数

❌ **低效做法**（多次单查询）:
```python
# 分别搜索3次
results1 = call_tool("search_document", {
    "session_id": "...",
    "query": "electricity"
})
results2 = call_tool("search_document", {
    "session_id": "...",
    "query": "energy"
})
results3 = call_tool("search_document", {
    "session_id": "...",
    "query": "power"
})
# 需要手动合并和去重
```

✅ **高效做法**（批量搜索）:
```python
# 一次搜索，自动去重
results = call_tool("search_document", {
    "session_id": "...",
    "queries": ["electricity", "energy", "power"],
    "max_results_per_query": 3,
    "deduplicate": true
})
# 自动合并并去重
```

**批量搜索应用场景**:
```python
# 场景1: 同义词搜索
{
    "queries": ["electricity", "energy", "power"],
    "max_results_per_query": 3
}

# 场景2: 多方面参数
{
    "queries": ["temperature", "pressure", "time"],
    "max_results_per_query": 2
}

# 场景3: 不同表述
{
    "queries": ["CO2 emission", "carbon dioxide", "greenhouse gas"],
    "max_results_per_query": 3
}
```

---

## 总结

作为LLM Agent，你需要：

1. **理解三工具架构**:
   - Parameter → Calculation → Process Flow
   - 清晰的数据链追踪

2. **掌握核心工具**:
   - `record_parameter`: 提取原始参数
   - `record_calculation`: 记录计算过程
   - `record_process_flow`: 记录LCI流
   - `get_session_summary`: 查询工作记忆
   - `search_document`: 文档搜索（支持批量）🆕

3. **建立可靠的数据链**:
   - 使用`data_dependencies`明确计算依赖
   - 使用`link_to`建立动作序列
   - 保持rationale纯净

4. **保持数据完整性**:
   - 定期查询session summary
   - 检查completeness assessment
   - 避免重复记录

5. **遵循最佳实践**:
   - 查询后再计算
   - 使用描述性名称
   - 及时pivot
   - 记录清晰的rationale
   - **使用批量搜索提高效率**🆕

6. **高效搜索策略** 🆕:
   - 同义词 → 批量搜索
   - 具体概念 → 单查询
   - 自动去重，节省时间

---

**现在，你已经准备好使用这些工具来完成LCA数据提取任务了！** 🚀

如有疑问，请查阅本手册或联系开发团队。

