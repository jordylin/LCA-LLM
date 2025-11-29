# 搜索排序优化方案（修正版）

## 🎯 核心理解

### 你的真实需求

**Batch Search 场景**:
```python
queries = ["electricity", "kWh", "energy", "consumption"]
```

**期望排序逻辑**:
- ✅ Chunk 中出现的**不同关键词种类**越多 → 权重越高
- ❌ **不是**某个词出现的次数（避免 'kg', 'kWh' 这种常见词干扰）

**示例**:

**Chunk A** (覆盖率高):
```
"The electricity consumption was 64.92 kWh. Energy efficiency improved."
```
- 匹配: ✅ electricity, ✅ kWh, ✅ energy, ✅ consumption
- **覆盖率: 4/4 = 100%** ✅ 排名最高

**Chunk B** (覆盖率中):
```
"The electricity usage was 64.92 kWh."
```
- 匹配: ✅ electricity, ✅ kWh
- **覆盖率: 2/4 = 50%** ⚠️ 排名中等

**Chunk C** (覆盖率低):
```
"The process uses energy resources."
```
- 匹配: ✅ energy
- **覆盖率: 1/4 = 25%** ❌ 排名较低

---

## 🔍 Batch Search 的语义相似度机制

### 当前实现（Line 302-303）

```python
for q in queries:
    search_results = session_data.knowledge_base.search(q, top_k=max_results_per_query * 2)
```

**工作原理**:
1. **逐个查询**: 对每个关键词单独进行 embedding 搜索
2. **独立排序**: 每个关键词返回自己的 top_k 结果
3. **合并去重**: 将所有结果合并，去除重复的 chunk

**问题**:
- ❌ 每个词的语义相似度是**独立计算**的
- ❌ 无法体现"多个词同时出现"的优势
- ❌ 一个 chunk 可能因为匹配了某一个词而被选中，但其他词都不匹配

**示例**:

搜索 `["electricity", "kWh", "energy"]`

```
Query "electricity":
  - Chunk A: 0.9 (包含 electricity, kWh, energy) ✅
  - Chunk B: 0.85 (只包含 electricity) ⚠️
  
Query "kWh":
  - Chunk A: 0.88 (包含 electricity, kWh, energy) ✅
  - Chunk C: 0.82 (只包含 kWh) ⚠️
  
Query "energy":
  - Chunk A: 0.87 (包含 electricity, kWh, energy) ✅
  - Chunk D: 0.80 (只包含 energy) ⚠️

合并结果:
  - Chunk A: 出现3次（被3个查询都选中）✅
  - Chunk B, C, D: 各出现1次 ⚠️
```

**当前问题**: 
- Chunk A 会被选中3次，但去重后只保留1次
- 无法体现 Chunk A 的"覆盖率优势"

---

## ✅ 正确的优化方案

### 方案核心

**不使用词频，只使用覆盖率**:

```python
覆盖率分数 = (chunk中匹配的不同关键词数量) / (总关键词数量)

最终分数 = 语义相似度 (0-1.0) + 覆盖率提升 (0-0.5) + 数据密度 (0-0.2)
```

### 算法实现

```python
def _calculate_coverage_boost(self, content: str, queries: List[str]) -> float:
    """
    计算覆盖率提升分数
    
    核心逻辑:
    - 只统计 chunk 中出现了多少个**不同的**关键词
    - 不考虑每个词出现的次数
    - 避免常见词（如 'kg', 'kWh'）的干扰
    
    Args:
        content: chunk 内容
        queries: 搜索关键词列表
        
    Returns:
        覆盖率提升分数 (0-0.5)
    """
    if not queries:
        return 0.0
    
    content_lower = content.lower()
    matched_keywords = set()  # 使用 set 去重
    
    for query in queries:
        query_lower = query.lower().strip()
        if not query_lower:
            continue
        
        # 只检查是否出现，不统计次数
        if query_lower in content_lower:
            matched_keywords.add(query_lower)
    
    # 计算覆盖率
    coverage_rate = len(matched_keywords) / len(queries)
    
    # 覆盖率提升分数 (0-0.5)
    # 100% 覆盖 = +0.5
    # 50% 覆盖 = +0.25
    # 0% 覆盖 = 0
    coverage_boost = coverage_rate * 0.5
    
    return coverage_boost
```

### 完整的排序算法

```python
def _calculate_enhanced_boost(self, content: str, queries: List[str]) -> float:
    """
    增强版排序算法（修正版）
    
    组成:
    1. 覆盖率提升 (0-0.5) ← 核心！
    2. 数据密度提升 (0-0.2)
    3. 表格标记提升 (0-0.1)
    
    总提升范围: 0-0.8
    """
    import re
    
    boost = 0.0
    
    # 1. 覆盖率提升（最多 +0.5）
    coverage_boost = self._calculate_coverage_boost(content, queries)
    boost += coverage_boost
    
    # 2. 数据密度提升（最多 +0.2）
    numbers = re.findall(r'\d+\.?\d*', content)
    data_boost = min(len(numbers) / 15.0, 0.2)
    boost += data_boost
    
    # 3. 表格标记提升（最多 +0.1）
    pipe_count = content.count('|')
    if pipe_count >= 3:
        boost += 0.1
    
    return boost

def _process_search_results(self, results, query, extract_mode):
    """处理搜索结果，根据模式进行智能提取"""
    processed = []
    
    # 解析查询词（支持单查询和批量查询）
    if isinstance(query, str):
        # 单查询：按空格或 | 分割
        queries = [q.strip() for q in query.replace('|', ' ').split() if q.strip()]
    elif isinstance(query, list):
        # 批量查询：已经是列表
        queries = query
    else:
        queries = []
    
    for result in results:
        content = result.get("content", "")
        similarity = result.get("similarity_score", 0)
        
        # 计算增强提升分数
        enhanced_boost = self._calculate_enhanced_boost(content, queries)
        boosted_score = similarity + enhanced_boost
        
        # 临时存储用于排序（不会返回给前端）
        result["_boosted_score"] = boosted_score
        
        # ... 其余处理逻辑保持不变
        if extract_mode == "sentences":
            extracted = self._extract_relevant_sentences(content, query)
            processed.append({
                **result,
                "extracted_content": extracted["content"],
                "confidence": extracted["confidence"],
                "extract_type": "sentences"
            })
        elif extract_mode == "key_points":
            extracted = self._extract_key_points(content, query)
            processed.append({
                **result,
                "extracted_content": extracted["content"],
                "confidence": extracted["confidence"],
                "extract_type": "key_points"
            })
        else:  # chunks (默认)
            processed.append({
                **result,
                "extracted_content": content,
                "confidence": similarity,
                "extract_type": "chunk"
            })
    
    return processed
```

---

## 📊 效果对比

### 场景: Batch Search

**搜索**: `["electricity", "kWh", "energy", "consumption"]`

| Chunk | 内容摘要 | 匹配词 | 覆盖率 | 语义 | 旧算法 | 新算法 | 排名 |
|-------|---------|--------|--------|------|--------|--------|------|
| A | "electricity consumption 64.92 kWh, energy..." | 4/4 | 100% | 0.85 | 0.85 | **1.35** | 🥇 |
| B | "electricity usage 64.92 kWh" | 2/4 | 50% | 0.82 | 0.82 | **1.07** | 🥈 |
| C | "energy resources" | 1/4 | 25% | 0.78 | 0.78 | **0.91** | 🥉 |
| D | "manufacturing process" | 0/4 | 0% | 0.75 | 0.75 | **0.75** | ❌ |

**新算法优势**:
- ✅ Chunk A（覆盖率100%）排名最高
- ✅ 覆盖率越高，排名越靠前
- ✅ 不受常见词频率干扰

---

## 🔧 进一步优化：改进 Batch Search 的语义相似度

### 当前问题

**逐个查询的缺陷**:
```python
for q in queries:
    search_results = knowledge_base.search(q, top_k=3)
```

- ❌ 每个词独立搜索，无法体现"组合匹配"
- ❌ 一个 chunk 可能被多次选中，但去重后只保留一次

### 改进方案：组合查询

```python
def search_document_batch_optimized(self, session_id: str, queries: List[str], ...):
    """
    优化的批量搜索
    
    改进:
    1. 将多个关键词组合成一个查询
    2. 使用覆盖率重新排序
    """
    # 方法1: 组合查询（推荐）
    combined_query = " ".join(queries)
    search_results = knowledge_base.search(combined_query, top_k=max_total_results * 2)
    
    # 方法2: 逐个查询 + 覆盖率排序（当前方案）
    # ... 保持现有逻辑
    
    # 使用覆盖率重新排序
    for result in search_results:
        content = result.get("content", "")
        similarity = result.get("similarity_score", 0)
        
        # 计算覆盖率提升
        coverage_boost = self._calculate_coverage_boost(content, queries)
        result["_boosted_score"] = similarity + coverage_boost
    
    # 按提升后的分数排序
    search_results.sort(key=lambda x: x.get("_boosted_score", 0), reverse=True)
    
    return search_results[:max_total_results]
```

**对比**:

| 方法 | 优势 | 劣势 |
|------|------|------|
| **逐个查询** | 确保每个词都被考虑 | 可能遗漏组合匹配 |
| **组合查询** | 更好的语义理解 | 可能忽略某些单词 |
| **混合方案** | 兼顾两者 | 计算量较大 |

**推荐**: 使用**组合查询 + 覆盖率排序**

---

## 💻 完整实施代码

```python
# 修改 backend/services/tool_service.py

def _calculate_coverage_boost(self, content: str, queries: List[str]) -> float:
    """
    计算覆盖率提升分数（修正版）
    
    核心逻辑:
    - 只统计 chunk 中出现了多少个**不同的**关键词
    - 不考虑每个词出现的次数
    - 避免常见词（如 'kg', 'kWh'）的干扰
    """
    if not queries:
        return 0.0
    
    content_lower = content.lower()
    matched_keywords = set()  # 使用 set 去重
    
    for query in queries:
        query_lower = query.lower().strip()
        if not query_lower:
            continue
        
        # 只检查是否出现，不统计次数
        if query_lower in content_lower:
            matched_keywords.add(query_lower)
    
    # 计算覆盖率
    coverage_rate = len(matched_keywords) / len(queries)
    
    # 覆盖率提升分数 (0-0.5)
    coverage_boost = coverage_rate * 0.5
    
    return coverage_boost

def _calculate_enhanced_boost(self, content: str, queries: List[str]) -> float:
    """
    增强版排序算法（修正版）
    
    组成:
    1. 覆盖率提升 (0-0.5) ← 核心！
    2. 数据密度提升 (0-0.2)
    3. 表格标记提升 (0-0.1)
    
    总提升范围: 0-0.8
    """
    import re
    
    boost = 0.0
    
    # 1. 覆盖率提升（最多 +0.5）
    coverage_boost = self._calculate_coverage_boost(content, queries)
    boost += coverage_boost
    
    # 2. 数据密度提升（最多 +0.2）
    numbers = re.findall(r'\d+\.?\d*', content)
    data_boost = min(len(numbers) / 15.0, 0.2)
    boost += data_boost
    
    # 3. 表格标记提升（最多 +0.1）
    pipe_count = content.count('|')
    if pipe_count >= 3:
        boost += 0.1
    
    return boost

def _process_search_results(self, results, query, extract_mode):
    """处理搜索结果，根据模式进行智能提取"""
    processed = []
    
    # 解析查询词（支持单查询和批量查询）
    if isinstance(query, str):
        # 单查询：按空格或 | 分割
        queries = [q.strip() for q in query.replace('|', ' ').split() if q.strip()]
    elif isinstance(query, list):
        # 批量查询：已经是列表
        queries = query
    else:
        queries = []
    
    for result in results:
        content = result.get("content", "")
        similarity = result.get("similarity_score", 0)
        
        # 计算增强提升分数
        enhanced_boost = self._calculate_enhanced_boost(content, queries)
        boosted_score = similarity + enhanced_boost
        
        # 临时存储用于排序（不会返回给前端）
        result["_boosted_score"] = boosted_score
        
        if extract_mode == "sentences":
            extracted = self._extract_relevant_sentences(content, query)
            processed.append({
                **result,
                "extracted_content": extracted["content"],
                "confidence": extracted["confidence"],
                "extract_type": "sentences"
            })
        elif extract_mode == "key_points":
            extracted = self._extract_key_points(content, query)
            processed.append({
                **result,
                "extracted_content": extracted["content"],
                "confidence": extracted["confidence"],
                "extract_type": "key_points"
            })
        else:  # chunks (默认)
            processed.append({
                **result,
                "extracted_content": content,
                "confidence": similarity,
                "extract_type": "chunk"
            })
    
    return processed
```

---

## 📝 总结

### 核心修正

1. **不使用词频** ❌
   - 避免 'kg', 'kWh' 等常见词干扰
   
2. **只使用覆盖率** ✅
   - 统计 chunk 中出现了多少个**不同的**关键词
   - 覆盖率 = 匹配词数 / 总词数

3. **权重分配**
   ```
   最终分数 = 语义相似度 (0-1.0) + 覆盖率 (0-0.5) + 数据密度 (0-0.3)
   ```

### Batch Search 的语义相似度

**当前机制**: 逐个查询 → 合并去重
- ⚠️ 无法体现"组合匹配"优势

**改进方向**: 组合查询 + 覆盖率排序
- ✅ 更好的语义理解
- ✅ 覆盖率提升排名

---

**这样理解对吗？我现在可以实施修正后的方案。**
