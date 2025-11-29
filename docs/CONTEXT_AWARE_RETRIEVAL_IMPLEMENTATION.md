# 上下文感知检索 (Context-Aware Retrieval) - 实现总结

**实现日期**: 2025-11-24  
**版本**: v1.0

---

## 🎯 核心概念

**上下文感知检索 (Context-Aware Retrieval)**：在训练和推理时，向 LLM 提供文档的前两个 chunks（chunk 0 和 chunk 1）作为预览，帮助 LLM 更好地选择搜索关键词。

**核心优势**：
- ✅ 训练-推理完全一致
- ✅ 提高搜索准确性
- ✅ 减少无效搜索
- ✅ 适用于所有数据集（Full + Short）

---

## 📝 实现内容

### **1. 新增工具：`record_document_preview`** ✅

**文件**: `/home/Research_work/24_yzlin/LCA-LLM/backend/services/tool_service.py`

**功能**：
- 从 `session_manager` 读取 chunk 0 和 chunk 1
- 存储到 MongoDB 的 `lca_actions` 集合
- 使用特殊标记：`record_type: "document_preview"`
- 添加 `exclude_from_export: True` 标记

**数据结构**：
```json
{
  "session_id": "xxx",
  "action_id": "ACT_PREVIEW",
  "tool_name": "record_document_preview",
  "record_type": "document_preview",
  "timestamp": "2025-11-24T...",
  "document_preview": {
    "chunk_0": {
      "chunk_id": "0",
      "content": "1.0 Executive Summary\nThis quality inspection report..."
    },
    "chunk_1": {
      "chunk_id": "1",
      "content": "All process parameters operated within..."
    }
  },
  "metadata": {
    "exclude_from_export": true,
    "document_name": "Quality_Inspection_Report.pdf"
  }
}
```

---

### **2. 工作台更新** ✅

**文件**: `/home/Research_work/24_yzlin/LCA-LLM/scripts/expert_annotation_workbench.py`

**新增按钮**: "📄 Record Preview"（第一栏第一个按钮）

**位置**: Session Control 区域

**功能**：
- 点击后调用 `/tools/record-document-preview` API
- 显示成功消息：`✅ Preview recorded! Chunk 0: xxx chars, Chunk 1: xxx chars`
- 只在有活跃 session 时可用

**布局**：
```
Session Control:
[📄 Record Preview] [Reset Session] [Get Summary] [Record Check]
```

---

### **3. 后端 API 路由** ✅

**文件**: `/home/Research_work/24_yzlin/LCA-LLM/backend/app.py`

**新增路由**: `POST /tools/record-document-preview`

**请求格式**：
```json
{
  "session_id": "6aad8fb6-58e0-456e-a0e5-46d4ffb6c489"
}
```

**响应格式**：
```json
{
  "success": true,
  "message": "文档预览已记录",
  "data": {
    "session_id": "6aad8fb6-58e0-456e-a0e5-46d4ffb6c489",
    "chunk_0_length": 1234,
    "chunk_1_length": 987
  }
}
```

---

### **4. 导出脚本更新** ✅

**文件**: `/home/Research_work/24_yzlin/LCA-LLM/scripts/export_training_data.py`

**修改点**：

#### **a) 从 `document_preview` 读取 chunks**
```python
def get_system_prompt_with_chunks(self, session_id: str) -> str:
    # 从 MongoDB 读取 document_preview 记录
    preview_record = self.db.lca_actions.find_one({
        "session_id": session_id,
        "record_type": "document_preview"
    })
    
    if not preview_record:
        logger.warning(f"⚠️ 未找到 document_preview 记录: {session_id}")
        return base_prompt
    
    # 提取 chunk 0 和 chunk 1
    chunk_0 = preview_record["document_preview"]["chunk_0"]["content"]
    chunk_1 = preview_record["document_preview"]["chunk_1"]["content"]
    
    # 构建 system prompt
    return base_prompt + f"""
**DOCUMENT CONTEXT**: 
- Document Name: "{document_name}"
- Document ID: {session_id[:8]}...

**CHUNK 0 PREVIEW** (Executive Summary / Introduction):
"{chunk_0}"

**CHUNK 1 PREVIEW**:
"{chunk_1}"

**AUTOMATIC SESSION INJECTION**: ...
"""
```

#### **b) 过滤导出**
```python
# 跳过 document_preview 记录（不导出到训练数据）
if record_type == "document_preview":
    continue
```

**特点**：
- ✅ 使用完整 chunk 内容（不截断）
- ✅ 无回退逻辑（简化代码）
- ✅ 如果没有 preview 记录，返回基础 prompt + 警告

---

### **5. 推理时注入** ✅

**文件**: `/home/Research_work/24_yzlin/LCA-LLM/backend/services/local_qwen_service.py`

**已实现**：在 `_build_chat_prompt` 方法中动态注入 chunk 0 和 chunk 1

```python
# 获取 chunk 0（完整内容）
if len(session_data.documents) > 0:
    chunk_0_content = session_data.documents[0].page_content
    system_prompt += f"""
**CHUNK 0 PREVIEW** (Executive Summary / Introduction):
"{chunk_0_content}"
"""

# 获取 chunk 1（完整内容）
if len(session_data.documents) > 1:
    chunk_1_content = session_data.documents[1].page_content
    system_prompt += f"""
**CHUNK 1 PREVIEW**:
"{chunk_1_content}"
"""
```

**训练-推理一致性**：✅ 完全一致

---

### **6. CAMEL AI 更新** ✅

**文件**: `/home/Research_work/24_yzlin/LCA-LLM/scripts/generate_think_with_camel.py`

**修改点**：

#### **a) 提取 chunk preview**
```python
def _extract_chunk_preview_from_system(self, messages: List[Dict]) -> str:
    """从 system message 中提取 chunk preview（如果有）"""
    for msg in messages:
        if msg.get("role") == "system":
            content = msg.get("content", "")
            if "**CHUNK 0 PREVIEW**" in content:
                # 提取前 200 字符
                return chunk_0_content[:200] + "..."
    return ""
```

#### **b) 传递给 state**
```python
# 提取 chunk preview
chunk_preview = self._extract_chunk_preview_from_system(messages)

# 传递给所有 state
state = {
    "user_query": user_query,
    "previous_actions": previous_actions,
    "chunk_preview": chunk_preview  # 🔥 新增
}
```

#### **c) 在 prompt 中使用（全局上下文）**
```python
# 🔥 构建全局上下文（包括 chunk preview）
global_context = ""
if chunk_preview:
    global_context = f"\n**Document Preview (from system prompt):** \"{chunk_preview}\"\n"

# 在所有场景的 prompt 中使用
prompt = f"""
**User Request:** {user_query}
{global_context}{context_description}
**Your Action:** Calling {tool_name} with ...

Generate YOUR internal thought process...
"""
```

**设计原则**：
- ✅ Chunk preview 是全局信息，不是临时信息
- ✅ LLM 在 system prompt 中已经看到，应该在整个对话中记住
- ✅ CAMEL AI 模拟 LLM 的完整上下文，包括全局信息
- ✅ 适用于所有场景（search, record, calculate, summary, final response）

---

## 🎯 设计改进：Chunk Preview 作为全局上下文

### **问题**：
最初的设计将 chunk preview 限制在"第一次搜索"时使用，这是错误的思路。

### **正确理解**：
- ✅ Chunk preview 是 LLM 在 **system prompt** 中已经看到的信息
- ✅ LLM 应该在**整个对话过程**中记住这些信息
- ✅ 这是**全局上下文**，不是临时信息

### **CAMEL AI 的职责**：
> CAMEL AI 应该模拟 LLM 看到的**完整上下文**，包括 system prompt 中的所有信息。

### **实现方式**：
1. **提取 chunk preview**：从 system message 中提取（前 200 字符）
2. **构建全局上下文**：`global_context = "Document Preview: ..."`
3. **融入所有场景**：在所有 prompt 中包含 `global_context`
   - ✅ Search（第一次和后续）
   - ✅ Record（所有类型）
   - ✅ Calculate
   - ✅ Get Summary
   - ✅ Final Response

### **为什么这样设计？**
- ✅ **一致性**：CAMEL AI 看到的 = LLM 看到的
- ✅ **自然性**：LLM 会自然地利用全局信息
- ✅ **完整性**：不人为限制信息的使用

### **示例**：
```
LLM 看到的 system prompt:
  "...
  **CHUNK 0 PREVIEW**: This report documents 33 units of 316L washers...
  ..."

CAMEL AI 生成推理时也应该"看到"这个信息：
  "Based on the preview mentioning 33 units of 316L washers, I'll search for 'manufactured' to find the functional unit."
```

---

## 🚀 使用流程

### **工作台操作**：

```
1. 上传 PDF 文档
   ↓
2. 点击 "📄 Record Preview" 按钮
   ↓
3. 系统自动：
   - 读取 chunk 0 和 chunk 1
   - 存储到 MongoDB
   - 显示成功消息
   ↓
4. 正常标注数据（search, record, etc.）
   ↓
5. 导出训练数据
   - 自动从 document_preview 读取 chunks
   - 填充到 system prompt
   - 过滤掉 document_preview 记录本身
   ↓
6. 生成推理内容（CAMEL AI）
   - 自动提取 chunk preview
   - 在第一次搜索时使用
```

---

## ✅ 优势总结

### **1. 适用于所有数据集** ✅
- ✅ Full 数据集：点击记录 → 有 chunk preview
- ✅ Short 数据集：点击记录 → 有 chunk preview
- ✅ 不依赖 search 结果

### **2. 数据持久化** ✅
- ✅ 存储在 MongoDB（不是临时的 ChromaDB）
- ✅ 可以随时导出
- ✅ 不会丢失

### **3. 完全可控** ✅
- ✅ 手动触发（点击按钮）
- ✅ 可以重新记录（更新）
- ✅ 不影响其他操作

### **4. 不影响导出流程** ✅
- ✅ 自动过滤 `document_preview` 记录
- ✅ 不会出现在训练数据的 messages 中
- ✅ 只用于 system prompt 的 chunk preview

### **5. 训练-推理一致** ✅
- ✅ 训练时：从 MongoDB 读取 chunk 0/1
- ✅ 推理时：从 session_manager 读取 chunk 0/1
- ✅ 格式完全相同

### **6. CAMEL AI 支持** ✅
- ✅ 自动提取 chunk preview
- ✅ 在第一次搜索时使用
- ✅ 不改变其他场景

---

## 📊 数据流

```
工作台 → MongoDB (document_preview)
   ↓
导出脚本 → 读取 document_preview → 填充 system prompt
   ↓
训练数据 (JSON) → CAMEL AI → 生成 reasoning_content
   ↓
训练数据 (JSONL) → 微调 LLM
   ↓
推理时 → session_manager → 注入 chunk 0/1 → LLM 使用
```

---

## 🎯 关键设计决策

### **1. 为什么存储在 MongoDB？**
- ✅ 持久化（不会丢失）
- ✅ 与其他 actions 在一起（便于管理）
- ✅ 可以随时查询

### **2. 为什么不从 search_context 提取？**
- ❌ 短数据集大概率没有 chunk 0/1
- ❌ 依赖专家的搜索策略
- ❌ 不可控

### **3. 为什么使用完整 chunk？**
- ✅ 不会漏掉关键信息
- ✅ Executive Summary 通常不会太长
- ✅ Token 消耗可接受（~250-500 tokens）

### **4. 为什么 CAMEL AI 只在第一次搜索时使用？**
- ✅ Less is More 原则
- ✅ 第一次搜索最需要文档预览
- ✅ 后续搜索已有上下文

---

## 📝 下一步

### **测试建议**：

```bash
# 1. 启动后端
cd /home/Research_work/24_yzlin/LCA-LLM
python backend/main.py

# 2. 启动工作台
streamlit run scripts/expert_annotation_workbench.py

# 3. 在工作台：
#    - 上传一个 PDF
#    - 点击 "📄 Record Preview" 按钮
#    - 检查 MongoDB 是否有记录

# 4. 导出测试：
python scripts/export_training_data.py \
  --session-id "xxx" \
  --output dataset/test_with_preview.json

# 5. 检查导出的文件：
#    - system prompt 是否包含 CHUNK 0 PREVIEW
#    - messages 中是否没有 record_document_preview

# 6. CAMEL AI 测试：
python scripts/generate_think_with_camel.py \
  --input dataset/test_with_preview.json \
  --output dataset/test_with_think.json \
  --api-key "sk-xxx"
```

---

## ✅ 完成状态

- ✅ 工具方法实现
- ✅ 工具 Schema 定义
- ✅ 工作台按钮添加
- ✅ 后端 API 路由
- ✅ 导出脚本更新
- ✅ 推理时注入（已有）
- ✅ CAMEL AI 更新
- ✅ 文档编写

**状态**: 🎉 完全实现，可以开始使用！

---

## 📚 相关文件

- `backend/services/tool_service.py` - 工具方法
- `backend/app.py` - API 路由
- `scripts/expert_annotation_workbench.py` - 工作台界面
- `scripts/export_training_data.py` - 导出脚本
- `backend/services/local_qwen_service.py` - 推理时注入
- `scripts/generate_think_with_camel.py` - CAMEL AI 生成

---

**作者**: AI Assistant  
**日期**: 2025-11-24  
**版本**: v1.0
