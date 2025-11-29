# LCA-LLM 专家标注工作台完整指南

## 概述

LCA-LLM专家标注工作台是一个专业的智能数据提取平台，专为LCA（生命周期评估）数据的高效标注和提取而设计。该系统实现了Expert Workbench Decision Logic Schema v1.3规范，提供完整的决策逻辑追踪、智能特征提取和专家决策记录功能。

## 系统架构

### 核心组件

```
┌─────────────────────────────────────────────────────────────────┐
│                    LCA-LLM Expert Workbench                    │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (Streamlit)     │  Backend (FastAPI)  │  Storage     │
│  ┌─────────────────────┐  │  ┌─────────────────┐ │  ┌─────────┐ │
│  │ 三栏式界面          │  │  │ 工具服务层       │ │  │ MongoDB │ │
│  │ - 会话管理          │  │  │ - PDF处理       │ │  │ - 决策链 │ │
│  │ - 智能搜索          │  │  │ - 向量搜索       │ │  │ - 特征   │ │
│  │ - 决策特征显示      │  │  │ - 特征计算       │ │  │ - 上下文 │ │
│  │ - 专家决策记录      │  │  │ - 会话管理       │ │  └─────────┘ │
│  └─────────────────────┘  │  └─────────────────┘ │             │
└─────────────────────────────────────────────────────────────────┘
```

### 三栏式布局

```
┌────────────────────┬──────────────────────┬──────────────────┐
│ [A] 会话与实时摘要  │ [B] 文档与智能搜索    │ [C] 统一提取工具  │
│                    │                      │                  │
│ - 会话状态管理      │ - 文档上传处理        │ - LCA范围定义     │
│ - 实时数据摘要      │ - 智能语义搜索        │ - 工艺流程记录    │
│ - 提取操作日志      │ - 决策特征展示        │ - 计算工具        │
│ - 决策链追踪       │ - 上下文管理         │ - 智能rationale   │
│                    │                      │ - 动作链追踪      │
└────────────────────┴──────────────────────┴──────────────────┘
```

## 核心功能

### 1. 智能决策特征系统

#### 自动特征计算
系统为每个文档块自动计算以下决策特征：

- **unit_hits**: 单位匹配数量（基于专业单位库unit.yml）
- **pattern_count**: 数值-单位对数量（支持复合单位如kg CO₂-eq/MJ）
- **quantitative_pattern_score**: 定量模式得分（0.0-1.0）
- **matched_examples**: 匹配的示例文本
- **contains_basis_tokens**: 是否包含基准标识符（per, basis, functional unit等）
- **is_table**: 表格类型检测（table_section, table_keyvalue等）

#### 颜色编码系统
- 🟢 **高质量**: 相似度≥0.75, Units>0, Pairs≥3, QPS≥0.15
- 🟡 **中等质量**: 相似度≥0.5, Pairs≥1, QPS≥0.02
- 🔴 **低质量**: 相似度<0.5, 无单位匹配
- ⚪ **无数据**: 空值或零值

#### 质量警告系统
- ⚠️ **Low evidence**: 无单位、无模式、QPS<0.02
- ⚠️ **Narrative**: 非表格、模式≤1、QPS<0.05
- ⚠️ **Sparse table**: 表格但模式<2

### 2. 专家决策追踪系统

#### 动作链机制
每个专家操作都会生成唯一的action_id（格式：ACT_0001, ACT_0002...），通过link_to字段形成完整的决策链：

```
ACT_0001 (select_best) → ACT_0002 (refine_same) → ACT_0003 (pivot_query)
     ↓                        ↓                        ↓
  初始选择              从同一块提取更多数据        改变搜索策略
```

#### 四种意图类型
1. **select_best**: 从搜索结果中选择最佳候选
2. **refine_same**: 从同一文档块提取更多数据
3. **pivot_query**: 改变搜索关键词和策略
4. **calculate**: 记录数学计算过程

#### link_to逻辑链条
系统支持四种依赖关系的自动建立：

1. **refine_same链接**: 链接到原始成功动作
   ```
   ACT_0001 (select_best) ← ACT_0003 (refine_same, link_to: ACT_0001)
   ```

2. **持续pivot链接**: 失败动作B链接到失败动作A
   ```
   ACT_0002 (pivot_query) ← ACT_0004 (pivot_query, link_to: ACT_0002)
   ```

3. **失败-成功闭环**: 成功动作链接到它解决的失败动作
   ```
   ACT_0002 (pivot_query) ← ACT_0003 (select_best, link_to: ACT_0002)
   ```

4. **计算结果链接**: 无上下文Flow记录链接到计算动作
   ```
   ACT_0003 (calculate) ← ACT_0004 (flow, no context, link_to: ACT_0003)
   ```

#### Pivot Query系统
专门用于捕获复杂负样本的智能系统：

- **独立记录**: 立即记录失败动作到MongoDB，不混合成功和失败数据
- **失败原因**: 专家必须填写为什么当前搜索结果不可用
- **清空重搜**: 记录失败后清空搜索结果，让专家手动开始新搜索
- **学习链条**: 通过link_to建立失败-成功的完整学习链

#### 智能Rationale系统
- **select_best**: 用户输入专家理由
- **refine_same**: 自动生成模板 + 可选备注
  ```
  模板: "Continuing extraction from the same high-value context (C47)."
  备注: "|| note: unit normalized from kWh to MJ"
  ```
- **pivot_query**: 专家填写失败原因，用于负样本学习

### 3. 上下文管理系统

#### 当前上下文显示
- 显示选中的文档块信息
- 提供Refine和Clear操作
- 实时显示决策特征

#### 搜索上下文记录
- 完整保存所有搜索候选
- 记录专家的选择过程
- 支持决策回溯分析

## 使用流程

### 启动系统

```bash
# 启动后端服务
cd /home/Research_work/24_yzlin/LCA-LLM
source lcaLLM/bin/activate
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000

# 启动前端界面
streamlit run scripts/expert_annotation_workbench.py --server.port 8504
```

访问地址：http://localhost:8504

### 完整工作流程

#### 第一阶段：文档准备与搜索

1. **文档上传**（栏目B）
   - 上传PDF文档
   - 点击"Process Document"
   - 等待文档处理完成

2. **智能搜索**（栏目B）
   - 输入搜索关键词
   - 执行语义搜索
   - 查看决策特征和质量评估

#### 第二阶段：专家决策与上下文设置

3. **候选评估**（栏目B）
   - 查看每个候选的决策特征：
     - Units, Pairs, QPS指标
     - 质量警告标识
     - 匹配示例展示
   - 展开查看完整内容

4. **设置上下文**（栏目B）
   - 点击"Set as Context"按钮
   - 输入专家选择理由
   - 确认设置为当前上下文

#### 第三阶段：数据提取与记录

5. **LCA范围定义**（栏目C）
   - 选择"LCA Scope"工具
   - 定义项目目标和边界
   - 记录功能单位和系统边界

6. **参数记录**（栏目C）
   - 选择"Parameter Recorder (For Calculations)"工具
   - 用途：从文档提取原始参数值（如功率、时间）
   - 填写参数数据：
     - 参数名称、数值、单位（标准单位库）
     - Intent和link_to自动检测
   - 点击"Record Parameter"

7. **工艺流程记录**（栏目C）
   - 选择"Process Flow"工具
   - 填写流程数据：
     - 流程类型（Input/Output）
     - LCI分类（12种标准分类，不含Process Parameter）
     - 物质名称、数值、单位
     - 可选：地点、CAS号、工艺名称
   - 点击"Record Process Flow"

7. **计算工具**（栏目C）
   - 选择"Calculation (Mathematical Operations)"工具
   - **Calculate & Verify工作流**：
     - 第一步：填写计算表达式和变量，点击"Calculate & Verify"
     - 第二步：验证计算结果，点击"Record Verified Calculation"
   - 支持功能：
     - 数学表达式：`power * time`, `sqrt(area)`
     - 变量定义：`power=10, time=5`
     - Start Over：重新定义计算
     - 安全执行：SafeCalculator防止代码注入

#### 第四阶段：会话管理与回顾

7. **Session Summary回顾**
   - 点击"Get Summary"查看当前会话数据
   - 系统显示：
     - 已记录的Parameters、Calculations、Flows、Scopes
     - 统计信息和完整性评估
   - 可通过"📝 Record Check"记录本次查看动作：
     - 用途：为LLM训练数据生成提供"回顾"样本
     - Rationale（可选）：记录查看summary的目的
     - 数据存储：MongoDB中记录为`summary_check`类型
     - **关键**：此动作**不分配action_id**，因为它是元动作而非数据记录

#### 第五阶段：高级操作

8. **Refine Same操作**
   - 在当前上下文中点击"Refine"
   - 系统自动生成rationale模板
   - 可选添加简短备注（≤80字）
   - 从同一文档块提取更多数据

9. **Pivot Query操作**
   - 点击"Pivot Query"按钮
   - 输入新的搜索关键词
   - 填写pivot原因
   - 执行新搜索策略

### 数据结构

#### MongoDB存储结构

```javascript
// lca_actions集合（统一存储）
{
  "_id": ObjectId,
  "session_id": "uuid",
  "action_id": "ACT_0001",  // 仅数据记录动作有action_id
  "link_to": "ACT_0000",  // 上一个动作的ID
  "record_type": "flow|scope|calculation|parameter|summary_check",
  "intent": "select_best|refine_same|pivot_query|calculate",
  "created_at": "2025-10-18T10:30:00",
  
  // 工艺流数据（仅flow类型）
  "flow_type": "Input|Output",
  "category": "Raw Material|Energy|...",  // 12种LCI分类，不含Process Parameter
  "name": "electricity",
  "value": 50.0,
  "unit": "kWh",
  "location": "China",
  "cas_number": "optional",
  "process_name": "optional",
  
  // 计算数据（仅calculation类型）
  "calculation_expression": "power * time",
  "calculation_result": 50.0,
  "calculation_unit": "kWh",
  
  // 决策逻辑数据
  "search_context": [
    {
      "chunk_id": "C47",
      "content": "...",
      "score": 0.85
    }
  ],
  "selected_chunk": {
    "chunk_id": "C47",
    "content": "...",
    "score": 0.85
  },
  "expert_decision": {
    "rationale": "Table format with clear value-unit pairs"
  }
}

// summary_check记录（特殊类型，无action_id）
{
  "_id": ObjectId,
  "session_id": "uuid",
  // ❌ 无action_id字段（元动作，不参与数据链）
  "record_type": "summary_check",
  "tool_name": "get_session_summary",
  "timestamp": "2025-11-07T10:30:00",
  "summary_snapshot": {
    "statistics": {
      "scope_count": 1,
      "flow_count": 3,
      "param_count": 2,
      "calc_count": 1,
      "total_actions": 7
    },
    "recorded_flows": [
      {"type": "Input", "category": "energy", "name": "electricity", "value": 100, "unit": "kWh", "action_id": "ACT_0001"},
      // ... 其他flows
    ],
    "recorded_parameters": [
      {"name": "power", "value": 10.5, "unit": "kW", "action_id": "ACT_0002"},
      // ... 其他parameters
    ],
    "recorded_calculations": [
      {"name": "energy", "expression": "power*time", "result": 52.5, "unit": "kWh", "action_id": "ACT_0003"},
      // ... 其他calculations
    ]
  },
  "expert_rationale": "Check if all material inputs are recorded"  // 可选字段
}
```

## 高级特性

### 1. 实时会话摘要（栏目A）

系统自动生成和更新会话摘要，包括：
- 已提取的数据统计
- 主要工艺流程概览
- 数据质量评估
- 提取进度跟踪

### 2. 智能单位识别

基于专业单位库（unit.yml）进行精确匹配：
- 支持1000+专业单位
- 智能过滤常见词汇
- 支持复合单位识别
- 自动单位标准化

### 3. 表格智能识别

自动识别和处理表格数据：
- 表格结构检测
- 数值-单位对提取
- 表格质量评估
- 稀疏表格警告

### 4. 决策链可视化

提供完整的专家决策追踪：
- 动作序列展示
- 意图类型标识
- 链接关系可视化
- 决策回溯支持

## 最佳实践

### 搜索策略

1. **关键词选择**
   - 使用具体的物质名称
   - 包含数量词汇
   - 避免过于宽泛的术语

2. **结果评估**
   - 优先选择🟢高质量候选
   - 注意⚠️质量警告
   - 查看匹配示例验证相关性

### 数据提取

1. **上下文设置**
   - 选择信息密度最高的块
   - 填写详细的选择理由
   - 确保决策特征支持选择

2. **Refine操作**
   - 充分利用高质量上下文
   - 添加有意义的备注
   - 保持数据一致性

3. **质量控制**
   - 验证数值和单位匹配
   - 检查LCI分类准确性
   - 确保工艺流逻辑合理

## 故障排除

### 常见问题

1. **搜索无结果**
   - 检查文档是否正确处理
   - 尝试不同关键词
   - 降低相似度阈值

2. **决策特征异常**
   - 确认单位库加载正常
   - 检查文本格式
   - 验证正则表达式匹配

3. **上下文丢失**
   - 检查session_state状态
   - 重新设置上下文
   - 确认浏览器会话有效

### 性能优化

1. **搜索优化**
   - 合理设置结果数量
   - 使用精确关键词
   - 避免过于频繁的搜索

2. **内存管理**
   - 定期清理会话数据
   - 避免处理过大文档
   - 监控系统资源使用

## 技术规范

### 系统要求

- **Python**: 3.8+
- **MongoDB**: 4.0+
- **内存**: 8GB+
- **存储**: 10GB+

### API接口

- **文档处理**: POST /tools/process-document
- **智能搜索**: POST /tools/search-document
- **数据记录**: POST /tools/record-process-flow
- **会话摘要**: GET /tools/session-summary/{session_id}

### 配置文件

- **MongoDB配置**: backend/config/mongodb_config.py
- **单位库**: resources/unit.yml
- **向量模型**: 自动下载HuggingFace模型

## 扩展开发

### 添加新的数据字段

1. 在后端API中添加字段处理逻辑
2. 更新前端显示组件
3. 修改MongoDB存储结构
4. 更新API响应格式

### 自定义LCI分类

1. 修改`backend/services/tool_service.py`中的分类列表
2. 更新前端选择器选项
3. 确保数据验证逻辑一致

### 集成新的搜索算法

1. 实现新的搜索服务类
2. 在工具服务层注册新算法
3. 更新前端搜索界面
4. 添加算法选择选项

---

*本文档基于Expert Workbench Decision Logic Schema v1.3规范编写，涵盖了系统的完整功能和使用方法。如有问题，请参考相关技术文档或联系开发团队。*