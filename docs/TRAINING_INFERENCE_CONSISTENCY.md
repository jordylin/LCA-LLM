# 训练-推理一致性设计

**创建时间**: 2025-11-17  
**版本**: v1.0

---

## 📋 问题背景

### 核心矛盾

```
工作台记录的数据 ≠ LLM实际能看到的数据

工作台Session Summary包含：
✅ record_process_flow      ← LLM会调用
✅ record_parameter          ← LLM会调用
❌ execute_calculation       ← LLM不会调用（后端自动执行）
❌ record_smart_skip         ← LLM不会调用（辅助标记）
❌ record_pivot_query        ← LLM不会调用（辅助标记）

但训练时LLM看到的Session Summary包含了这些！
```

### 为什么这是问题？

1. **训练-推理不一致**
   - 训练时：Session Summary包含calculation/smart_skip/pivot
   - 推理时：LLM自己生成的Session Summary不包含这些
   - 结果：LLM会困惑，不知道如何处理

2. **信息泄露**
   - LLM看到"已记录smart_skip"，但它自己不会记录
   - LLM可能学会依赖这些不可见的信息

3. **决策逻辑混乱**
   - LLM应该通过reasoning判断"数据已记录，跳过"
   - 但如果Session Summary显示"smart_skip已记录"，它会依赖这个标记

---

## 💡 解决方案：双视图Session Summary

### 核心设计

**LLM视图**（用于训练数据）：
- 只包含LLM会调用的工具结果
- 包含：`record_process_flow`, `record_parameter`
- 排除：`execute_calculation`, `record_smart_skip`, `record_pivot_query`

**工作台视图**（用于UI显示）：
- 包含所有统计信息
- 用于专家标注和数据分析

---

## 🔧 技术实现

### 1. 后端服务层

**文件**: `backend/services/tool_service.py`

**方法签名**：
```python
async def get_session_summary(
    self, 
    session_id: str, 
    format: str = "text",
    view: str = "llm"  # 🔥 新增参数
) -> Union[Dict[str, Any], str]:
```

**过滤逻辑**：
```python
if view == "llm":
    # LLM视图：只保留LLM会调用的工具（flow和parameter）
    visible_actions = [
        a for a in all_actions 
        if a.get("record_type") in ["flow", "parameter"]
    ]
else:
    # 工作台视图：包含所有actions
    visible_actions = all_actions
```

**文本格式输出**：
```python
def _format_summary_as_text(
    self, 
    flow_actions: List[dict], 
    parameter_actions: List[dict], 
    calculation_actions: List[dict], 
    view: str = "llm"
) -> str:
    if view == "llm":
        # LLM视图：只显示flow和parameter
        lines.append(f"Total Actions: {len(flow_actions) + len(parameter_actions)}")
        lines.append(f"Flows: {len(flow_actions)}, Parameters: {len(parameter_actions)}")
        # ⚠️ 不包含calculation统计
    else:
        # 工作台视图：包含calculation
        lines.append(f"Total Actions: {len(flow_actions) + len(parameter_actions) + len(calculation_actions)}")
        lines.append(f"Flows: {len(flow_actions)}, Parameters: {len(parameter_actions)}, Calculations: {len(calculation_actions)}")
```

### 2. API层

**文件**: `backend/app.py`

**Endpoint**：
```python
@app.get("/tools/session-summary/{session_id}")
async def tool_get_session_summary(
    session_id: str,
    format: str = Query("text", ...),
    view: str = Query("llm", ...)  # 🔥 新增参数，默认llm
):
    result = await tool_service.get_session_summary(
        session_id=session_id, 
        format=format, 
        view=view
    )
```

**默认行为**：
- 默认使用`view="llm"`，保证训练数据一致性
- 工作台显式指定`view="workbench"`

### 3. 导出脚本

**文件**: `scripts/export_training_data.py`

**修改**：
```python
def get_session_summary_text(self, session_id: str, before_action_id: str = None) -> str:
    """
    🔥 重要：只包含flow和parameter，不包含calculation
    """
    # 🔥 LLM视图：只统计flow和parameter
    flows = [a for a in actions if a.get("record_type") == "flow"]
    parameters = [a for a in actions if a.get("record_type") == "parameter"]
    
    summary_parts = []
    summary_parts.append(f"Total Actions: {len(flows) + len(parameters)}")
    summary_parts.append(f"Flows: {len(flows)}, Parameters: {len(parameters)}")
    # ⚠️ 不包含calculation统计
```

### 4. 工作台前端

**文件**: `scripts/expert_annotation_workbench.py`

**修改**：
```python
# 所有session summary调用都使用workbench视图
result = call_api(
    f"/tools/session-summary/{session_id}?format=json&view=workbench", 
    method="GET"
)
```

### 5. Record Summary Check

**文件**: `backend/app.py`

**修复**：
```python
@app.post("/actions/record-summary-check")
async def record_summary_check(request: dict):
    # ⚠️ 使用workbench视图，包含完整统计（用于snapshot）
    summary_result = await tool_service.get_session_summary(
        session_id=session_id, 
        format="json", 
        view="workbench"  # 🔥 必须指定workbench
    )
```

**重要**：
- `record_summary_check` 需要记录完整的统计信息（包含calculation）
- 但导出训练数据时，会将snapshot转换为LLM视图格式
- 这样既保证了工作台统计的完整性，又保证了训练数据的一致性

---

## 📊 对比示例

### LLM视图（训练数据）

```
Total Actions: 6
Flows: 6, Parameters: 0

Recorded Flows:
  - Ti6Al4V: 20.83 kg (Input/Raw Material)
  - Electricity: 147.26 kWh (Input/Energy)
  - Argon – Flooding: 3.03 kg (Input/Ancillary Material)
  - Argon – Build Phase: 25.94 kg (Input/Ancillary Material)
  - 20 Femoral Stems: 1.77 kg (Output/Product)
  - Ti6Al4V: 18.99 kg (Output/By-product)
```

⚠️ **不包含**：Calculations, Smart Skips, Pivots

### 工作台视图（UI显示）

```
Total Actions: 8
Flows: 6, Parameters: 0, Calculations: 2

Recorded Flows:
  - Ti6Al4V: 20.83 kg (Input/Raw Material)
  - ...

Recorded Calculations:
  - energy: 3420000 J
  - power_density: 0.95 W/mm²
```

✅ **包含完整统计**

---

## ✅ 验证要点

### 1. Session Summary内容

**LLM视图（默认）**：
```bash
curl "http://localhost:8000/tools/session-summary/{session_id}?format=text"
# 或
curl "http://localhost:8000/tools/session-summary/{session_id}?format=text&view=llm"
```

应该只包含：
- ✅ Flows
- ✅ Parameters
- ❌ Calculations
- ❌ Smart Skips
- ❌ Pivots

**工作台视图**：
```bash
curl "http://localhost:8000/tools/session-summary/{session_id}?format=json&view=workbench"
```

应该包含：
- ✅ Flows
- ✅ Parameters
- ✅ Calculations
- ✅ Smart Skips
- ✅ Pivots

### 2. 训练数据一致性

```
训练时LLM看到的Session Summary 
= 
推理时LLM自己生成的Session Summary
```

验证方法：
1. 导出训练数据
2. 检查Session Summary的tool响应
3. 确认不包含calculation/smart_skip/pivot

### 3. 工作台功能完整

工作台UI应该：
- ✅ 显示完整统计（包含所有action类型）
- ✅ 统计卡片显示Calculations, Smart Skips, Pivots
- ✅ 不影响训练数据的生成

---

## 🎯 设计原则

### 1. 训练-推理一致性

**核心原则**：训练数据只包含LLM能看到的信息

- ✅ LLM会调用的工具 → 包含在Session Summary中
- ❌ LLM不会调用的工具 → 不包含在Session Summary中

### 2. 信息可见性

**LLM可见**：
- `record_process_flow` - LLM主动调用
- `record_parameter` - LLM主动调用
- `search_document` - LLM主动调用
- `get_session_summary` - LLM主动调用

**LLM不可见**：
- `execute_calculation` - 后端自动执行，LLM不调用
- `record_smart_skip` - 工作台辅助标记，LLM不调用
- `record_pivot_query` - 工作台辅助标记，LLM不调用

### 3. Reasoning驱动

**Smart Skip场景**：
- ❌ 不依赖Session Summary中的smart_skip统计
- ✅ 通过reasoning表达"数据已记录，跳过"
- ✅ 直接进入下一个大类的搜索

**Calculation场景**：
- ❌ LLM不调用execute_calculation
- ✅ LLM调用record_parameter
- ✅ 后端自动执行计算并记录
- ✅ 计算结果不出现在LLM的Session Summary中

---

## 📁 修改文件清单

1. **`backend/services/tool_service.py`**
   - 添加`view`参数到`get_session_summary()`
   - 根据view过滤visible_actions
   - 修改`_format_summary_as_text()`，LLM视图不包含calculation

2. **`backend/app.py`**
   - 添加`view`参数到`/tools/session-summary/{session_id}` endpoint
   - 默认使用`view="llm"`
   - 修复`record_summary_check`，使用`view="workbench"`

3. **`scripts/export_training_data.py`**
   - 修改`get_session_summary_text()`，只包含flow和parameter
   - 修改snapshot转换逻辑，训练数据不包含calculation

4. **`scripts/expert_annotation_workbench.py`**
   - 所有session summary调用使用`view="workbench"`

5. **`docs/TRAINING_INFERENCE_CONSISTENCY.md`**（新建）
   - 完整的设计文档

---

## 🚀 影响分析

### 对训练数据的影响

**之前**：
```json
{
  "role": "tool",
  "content": "Total Actions: 8\nFlows: 6, Parameters: 0, Calculations: 2"
}
```

**现在**：
```json
{
  "role": "tool",
  "content": "Total Actions: 6\nFlows: 6, Parameters: 0"
}
```

✅ **更准确**：LLM推理时也只能看到flow和parameter

### 对工作台的影响

**之前**：
- 工作台看到的summary与训练数据一致
- 但包含了LLM不会生成的信息

**现在**：
- 工作台使用`view="workbench"`，看到完整统计
- 训练数据使用`view="llm"`，只包含LLM可见信息
- ✅ **两者分离，各司其职**

### 对LLM推理的影响

**之前**：
- LLM可能依赖calculation/smart_skip统计
- 推理时无法生成这些统计，导致困惑

**现在**：
- LLM只看到flow和parameter
- 推理时生成的summary与训练时一致
- ✅ **训练-推理完全一致**

---

## 📝 总结

### 核心价值

1. **训练-推理一致性**
   - 训练时看到的 = 推理时能生成的
   - 消除信息泄露

2. **决策逻辑清晰**
   - LLM通过reasoning判断，而非依赖辅助标记
   - 培养真正的推理能力

3. **架构优雅**
   - 双视图设计，清晰分离
   - 工作台功能不受影响

### 关键创新

- ✅ 首次明确区分"LLM可见"和"工作台可见"
- ✅ 通过view参数实现双视图
- ✅ 保证训练数据的纯净性

---

**文档状态**: ✅ 完成  
**实现状态**: ✅ 已完成所有代码修改  
**测试状态**: ⏳ 待验证
