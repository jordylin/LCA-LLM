question：你前面提到的“LLM "中间人" 翻译 (LLM-based Query Rewriting) —— 最智能”，具体要怎么实现？我就记录在MongoDB数据库里面了，还能通过LLM进行改进吗？因为当前的流程就是通过脚本读取已记录的数据进行匹配的

answer：这一策略完全可行，且非常适合您当前的架构。虽然数据已经“死”在 MongoDB 里了，但数据中保留的\*\*上下文（Context）\*\*是“活”的。

您提到“数据已在 MongoDB 中”，这实际上是一个优势。EcoLLM 的 `lca_actions` 集合中保存了 `selected_chunk`（原始文档片段）和 `rationale`（推理过程）。我们可以利用这些“沉睡”的上下文信息，在脚本读取数据和进行匹配之间，插入一个 **LLM Rewriter** 环节。

以下是具体实现的三个步骤，不需要重跑提取流程，只需修改匹配脚本：

### 第一步：确认 MongoDB 中的“宝藏”

在您的 MongoDB `lca_actions` 集合中，一条典型的记录应该包含以下关键信息（基于 `README.md` 的 Experts Workbench 描述）：

```json
{
  "action_id": "ACT_0005",
  "tool_name": "record_process_flow",
  "name": "Waste solid",           // <--- 模糊的名称 (当前痛点)
  "process_name": "316L SLM",    // <--- 关键上下文 1
  "selected_chunk": {            // <--- 关键上下文 2 (这是金矿)
    "content": "...generated 0.42kg of solid waste during the laser sintering of 316L powder..."
  }
}
```

**核心思路**：不仅读取 `name`，还要读取 `process_name` 和 `selected_chunk`，把它们喂给 LLM，问它：“基于这段文字，'Waste solid' 在 Ecoinvent 数据库里应该叫什么？”

### 第二步：设计“中间人”重写 Prompt

我们需要一个极简的 Prompt，让 8B 模型充当“翻译官”。

**Prompt 模板：**

```python
REWRITE_PROMPT = """
Task: Translate a user-extracted flow name into a precise Ecoinvent database search term based on the context.

Context from Document: "{chunk_content}"
Process Name: "{process_name}"
User Extracted Name: "{user_name}"

Instruction:
1. Identify the material composition (e.g., steel, plastic, wood) and state (e.g., scrap, waste, liquid).
2. Output ONLY the specific technical term for searching Ecoinvent.

Example:
Context: "Aluminum milling generated scraps." -> Search Term: "Aluminium scrap"
Context: "Disposal of polyethylene packaging." -> Search Term: "Waste polyethylene"

Target Search Term:
"""
```

### 第三步：Python 脚本实现 (集成到 `ecoinvent_matcher.py`)

您可以在现有的匹配脚本中插入 `rewrite_flow_name` 函数。

```python
# 伪代码：集成到您的匹配脚本中

def rewrite_flow_name(action_record, llm_service):
    """
    使用 LLM 将模糊的名称转换为精确的搜索词
    """
    # 1. 准备上下文
    chunk_content = action_record.get("selected_chunk", {}).get("content", "")
    process_name = action_record.get("process_name", "")
    user_name = action_record.get("name", "")
    
    # 2. 如果没有上下文，直接返回原名（兜底）
    if not chunk_content:
        return f"{user_name} {process_name}"

    # 3. 调用 LLM (Qwen3-8B)
    # 使用 format 填充上面定义的 REWRITE_PROMPT
    prompt = REWRITE_PROMPT.format(
        chunk_content=chunk_content[:500], # 截取前500字符防溢出
        process_name=process_name,
        user_name=user_name
    )
    
    # 假设 llm_service.predict 是您的推理接口
    # temperature 设置低一点(0.1)，我们需要精准翻译
    search_term = llm_service.predict(prompt, temperature=0.1)
    
    # 清洗一下输出（去掉换行或引号）
    return search_term.strip().replace('"', '')

# --- 主循环逻辑 ---

def process_matching_batch(session_id):
    # 1. 从 MongoDB 读取记录
    actions = db.lca_actions.find({"session_id": session_id, "tool_name": "record_process_flow"})
    
    for action in actions:
        original_name = action['name']
        
        # [NEW] 2. LLM 中间人重写
        # 只有当名字很模糊时才重写 (可选逻辑)，或者全部重写
        enhanced_search_term = rewrite_flow_name(action, llm_service)
        print(f"重写: '{original_name}' -> '{enhanced_search_term}'")
        
        # 3. 使用新词进行向量搜索 (调用现有的 search 工具)
        # 注意：这里用 enhanced_search_term 去搜 Ecoinvent
        matches = ecoinvent_vector_db.search(enhanced_search_term)
        
        # 4. (可选) 将优化后的搜索词回写到 MongoDB，方便复盘
        db.lca_actions.update_one(
            {"_id": action['_id']}, 
            {"$set": {"enhanced_search_term": enhanced_search_term}}
        )
        
        # 5. 后续逻辑：保存 Top-K 匹配结果...
```

### 为什么这样做有效？

1.  **不需要重新运行提取流程**：您不需要让 LLM 重新读 PDF。利用 MongoDB 里存好的 `selected_chunk`，这是“事后诸葛亮”式的优化，成本极低。
2.  **利用了 8B 模型的强项**：让 8B 模型从头做整个 LCA 很难，但让它做“名称翻译”这种短文本任务（Summarization/Translation），效果通常极好。
3.  **可追溯**：您可以在 MongoDB 新增一个字段 `enhanced_search_term`，这样就能对比：LLM 原本提了什么（Waste solid），脚本把它改成了什么（316L waste），最后匹配到了什么。

### 进阶建议：Batching (批处理)

如果您的数据量很大（例如几百条 flow），一条条调 LLM 会慢。您可以把 5-10 条记录打包成一个 Prompt 发给 LLM：

```markdown
Here is a list of flows extracted from a document about "316L Additive Manufacturing".
Please provide specific Ecoinvent search terms for each.

1. "Waste solid" (Context: "...316L powder waste...")
2. "Electricity" (Context: "...grid mix...")
...

Output format: JSON
```

这样速度会快很多，且能保持 Token 效率。