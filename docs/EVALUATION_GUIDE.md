# EcoLLM 完整评估指南

## 🎯 评估目标

在测试集上运行微调后的模型，计算以下指标：
- Field-level Exact Match (EM)
- Numerical Accuracy
- Grounding Accuracy  
- Valid JSON Rate

---

## 🏗️ 系统架构理解

### 当前架构

```
┌─────────────────────────────────────────────────────────┐
│                    EcoLLM 系统                           │
├─────────────────────────────────────────────────────────┤
│  1. vLLM 推理服务 (端口 8080)                           │
│     - 加载微调后的模型 (lca_lora)                        │
│     - 提供 OpenAI 兼容的 API                            │
│                                                          │
│  2. FastAPI 后端 (端口 8000)                            │
│     - 上传 PDF → 创建 Session → ChromaDB               │
│     - 提供工具 API (search_document, record_*, etc.)   │
│     - LLM 服务层调用 vLLM                               │
│                                                          │
│  3. 数据存储                                             │
│     - MongoDB: 存储 action records                       │
│     - ChromaDB: 临时文档向量库                          │
└─────────────────────────────────────────────────────────┘
```

### 评估流程

```
测试文档 (PDF)
    │
    ├─→ 上传到 FastAPI (/upload-pdf)
    │       │
    │       └─→ 创建 Session + ChromaDB 向量库
    │
    ├─→ 用户请求 ("Extract LCI data")
    │       │
    │       └─→ LLM 服务 (vLLM + 微调模型)
    │               │
    │               ├─→ 生成 tool_calls
    │               │
    │               └─→ 调用工具 (search_document, record_process_flow)
    │                       │
    │                       └─→ 存储到 MongoDB
    │
    └─→ 收集预测结果 (从 MongoDB 或工具响应)
            │
            └─→ 对比 Ground Truth → 计算指标
```

---

## 🚀 评估步骤

### Step 1: 准备环境

#### 1.1 启动 vLLM 服务

```bash
# 使用微调后的模型
./start_vllm.sh

# 或手动启动
python -m vllm.entrypoints.openai.api_server \
    --model models/lca_lora \
    --served-model-name lca_lora \
    --max-model-len 25000 \
    --dtype bfloat16 \
    --port 8080
```

**验证 vLLM 是否启动成功：**
```bash
curl http://localhost:8080/v1/models
```

#### 1.2 启动 FastAPI 后端

```bash
# 设置环境变量使用 vLLM
export LLM_SERVICE=vllm
export VLLM_API_BASE=http://localhost:8080/v1
export VLLM_MODEL_NAME=lca_lora

# 启动后端
cd backend
python app.py
```

**验证后端是否启动成功：**
```bash
curl http://localhost:8000/sessions/stats
```

---

### Step 2: 准备测试数据

你已经完成了这一步：
- ✅ 测试数据：`test_data/` (11 个对话)
- ✅ Ground Truth：`test_data/ground_truth.json` (16 条记录)

---

### Step 3: 运行评估

#### 方案 A：完整的端到端评估（推荐）

这需要实现一个聊天接口，让模型完整地运行 Agent 流程。

**问题**：当前 FastAPI 后端没有直接的 `/chat` 端点。

**解决方案**：
1. 添加 `/chat` 端点到 `app.py`
2. 或者使用现有的工具 API 手动模拟 Agent 流程

#### 方案 B：简化评估（快速验证）

直接使用测试数据中的 tool_calls 作为"预测"，验证评估流程是否正确。

```bash
python scripts/run_full_evaluation.py \
    --backend-url http://localhost:8000 \
    --test-dir test_data \
    --output-dir test_results
```

---

## 🔧 关键问题和解决方案

### 问题 1：如何让模型真正推理？

**当前状态**：
- ✅ vLLM 可以加载微调后的模型
- ✅ FastAPI 提供了工具 API
- ❌ 缺少一个端点让模型"自主运行"整个对话

**解决方案选项**：

#### 选项 1：添加 `/chat` 端点（推荐）

在 `app.py` 中添加：

```python
@app.post("/chat")
async def chat(request: ChatRequest):
    """
    聊天接口，支持完整的 Agent 对话
    
    Request:
        session_id: str
        message: str
        
    Response:
        assistant_message: str
        tool_calls: List[Dict]
        records: List[Dict]  # 提取的记录
    """
    # 1. 调用 LLM 服务生成响应
    response = await llm_chat_service.chat(
        session_id=request.session_id,
        user_message=request.message
    )
    
    # 2. 如果有 tool_calls，执行工具
    if response.get('tool_calls'):
        for tool_call in response['tool_calls']:
            tool_result = await execute_tool(tool_call)
            # 继续对话...
    
    # 3. 返回结果
    return response
```

#### 选项 2：使用 Qwen-Agent 的 Assistant API

如果你使用 `QwenAgentServiceV2`，可以直接调用 `assistant.run()`：

```python
# 在 qwen_agent_service_v2.py 中
async def run_dialogue(self, session_id: str, user_message: str):
    """运行完整对话"""
    messages = [{'role': 'user', 'content': user_message}]
    
    # Qwen-Agent 会自动处理工具调用
    responses = []
    for response in self.assistant.run(messages):
        responses.append(response)
    
    return responses
```

#### 选项 3：手动模拟 Agent 循环（临时方案）

```python
async def simulate_agent(session_id: str, user_message: str):
    """手动模拟 Agent 工具调用循环"""
    
    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_message}
    ]
    
    max_turns = 20
    records = []
    
    for turn in range(max_turns):
        # 1. 调用 LLM
        response = await vllm_service.chat_completion(messages)
        
        # 2. 解析 tool_calls
        tool_calls = response.get('tool_calls', [])
        
        if not tool_calls:
            # 没有工具调用，对话结束
            break
        
        # 3. 执行工具
        for tc in tool_calls:
            tool_result = await execute_tool(session_id, tc)
            
            # 如果是 record_process_flow，保存记录
            if tc['name'] == 'record_process_flow':
                records.append(tc['arguments'])
            
            # 添加工具响应到消息历史
            messages.append({
                'role': 'tool',
                'content': json.dumps(tool_result)
            })
        
        # 4. 继续下一轮
        messages.append({
            'role': 'assistant',
            'tool_calls': tool_calls
        })
    
    return records
```

---

### 问题 2：测试文档格式

**当前状态**：
- 测试数据中有 `text_full_001.jsonl`（JSONL 格式）
- 但系统需要 PDF 文件

**解决方案**：

1. **如果你有原始 PDF**：直接使用
2. **如果只有 JSONL**：需要将文档内容转换为 PDF 或直接注入到 ChromaDB

```python
# 方案：直接创建临时知识库（跳过 PDF 上传）
async def create_test_session(document_chunks: List[str]):
    """从文档片段创建测试 session"""
    session_id = str(uuid.uuid4())
    
    # 创建临时知识库
    temp_kb = TemporaryKnowledgeBase(f"session_{session_id}")
    
    # 添加文档片段
    documents = [
        Document(page_content=chunk, metadata={'chunk_id': str(i)})
        for i, chunk in enumerate(document_chunks)
    ]
    temp_kb.add_documents(documents)
    
    # 保存到 session
    session_manager.create_session_with_kb(session_id, temp_kb)
    
    return session_id
```

---

## 📊 评估指标计算

评估脚本已经实现了指标计算逻辑：

```python
# scripts/run_full_evaluation.py 中的 calculate_metrics()

1. Field-level EM
   - 对比文本字段（flow_name, category, unit）
   - 使用归一化（小写 + 去标点）
   - 计算召回率

2. Numerical Accuracy
   - 对比数值字段（value）
   - 允许 1% 相对误差
   - 需要先匹配对应的记录

3. Grounding Accuracy
   - 条件概率：给定数值正确，引用是否正确
   - 对比 chunk_id

4. Valid JSON Rate
   - 检查预测结果的结构完整性
```

---

## 🎯 下一步行动

### 立即可做的（验证评估流程）

```bash
# 1. 提取 Ground Truth（已完成）
python scripts/extract_ground_truth.py

# 2. 运行简化评估（验证流程）
python scripts/run_full_evaluation.py
```

### 需要实现的（真正评估）

**选择一个方案实现**：

#### 方案 1：添加 /chat 端点（最完整）
- 修改 `backend/app.py`
- 添加聊天接口
- 实现工具调用循环

#### 方案 2：使用 Qwen-Agent API（如果已配置）
- 确保 `LLM_SERVICE=qwen_agent`
- 使用 `assistant.run()` 方法

#### 方案 3：编写独立推理脚本（最灵活）
- 直接调用 vLLM API
- 手动实现 Agent 循环
- 不依赖 FastAPI 后端

---

## 💡 推荐方案

**我推荐方案 3**：编写独立推理脚本

**原因**：
1. ✅ 不需要修改现有代码
2. ✅ 完全控制推理流程
3. ✅ 可以详细记录每一步
4. ✅ 便于调试和分析

**实现**：创建 `scripts/run_inference_standalone.py`

---

## 📝 总结

**当前状态**：
- ✅ 测试数据准备完成
- ✅ Ground Truth 提取完成
- ✅ 评估指标计算逻辑完成
- ⚠️ 缺少真正的模型推理部分

**需要做的**：
1. 选择一个推理方案（推荐方案 3）
2. 实现推理脚本
3. 运行完整评估
4. 分析结果，撰写 3.3 小节

**预计时间**：
- 实现推理脚本：2-3 小时
- 运行评估：30 分钟
- 分析结果：1 小时
- 总计：4-5 小时
