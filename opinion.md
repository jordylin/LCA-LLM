
---

## **评价：SEARCH_OPTIMIZATION_CORRECTED.md**

### **原方案的权重分配**

```python
最终分数 = 语义相似度 (0-1.0) + 覆盖率 (0-0.5) + 数据密度 (0-0.2)
```

---

### **📊 与保守方案的对比**

| 维度 | 原方案 | 保守方案 | 差异分析 |
|------|--------|---------|---------|
| **语义相似度** | 0-1.0 | 0-1.0 | ✅ 相同 |
| **覆盖率权重** | 0-0.5 | 0-0.25 | ❌ 原方案过高，风险大 |
| **数据密度阈值** | 15个数字 | 5个数字 | ❌ 原方案不符合LCA实际 |
| **数据密度权重** | 0-0.2 | 0-0.2 | ✅ 相同 |
| **表格标记权重** | 0-0.1 | 0-0.15 | ⚠️ 原方案略低 |
| **总分范围** | 0-1.7 | 0-1.6 | - |

---

### **🔍 详细评价**

#### **1. 覆盖率权重 0.5 的问题**

**原方案的风险场景**：

```python
搜索: ["process", "energy", "consumption", "manufacturing"]

Chunk A (关键词堆砌，无数据):
"The manufacturing process requires energy for consumption activities."
- 语义: 0.70
- 覆盖率: 4/4 = 100% → +0.5
- 数据密度: 0个数字 → 0
- 最终: 0.70 + 0.5 + 0 = 1.20 ❌

Chunk B (有实际数据):
"Electricity consumption: 147.26 kWh"
- 语义: 0.88
- 覆盖率: 2/4 = 50% → +0.25
- 数据密度: 2个数字 → +0.027 (按15个阈值)
- 最终: 0.88 + 0.25 + 0.027 = 1.157 ✅
```

**结果**: A (1.20) > B (1.157) ❌ **错误排序！**

**问题**：
- 覆盖率 +0.5 **过高**，足以让无数据的 chunk 超越有数据的 chunk
- 语义相似度差距 0.18 无法弥补覆盖率差距 0.25

---

**保守方案的改进**：

```python
Chunk A (关键词堆砌，无数据):
- 语义: 0.70
- 覆盖率: 4/4 = 100% → +0.25 (降低！)
- 数据密度: 0个数字 → 0
- 最终: 0.70 + 0.25 + 0 = 0.95 ✅

Chunk B (有实际数据):
- 语义: 0.88
- 覆盖率: 2/4 = 50% → +0.125
- 数据密度: 2个数字 → +0.08 (按5个阈值)
- 最终: 0.88 + 0.125 + 0.08 = 1.085 ✅
```

**结果**: B (1.085) > A (0.95) ✅ **排序正确！**

**改进效果**：
- ✅ 覆盖率权重降低到 0.25，减少了"关键词堆砌"的风险
- ✅ 数据密度阈值调整到 5 个，更符合 LCA 实际场景
- ✅ 语义相似度重新成为主导因素

---

#### **2. 数据密度阈值 15 的问题**

**原方案的问题**：

```python
典型 LCA chunk:
"Ti6Al4V powder: 20.83 kg, Electricity: 147.26 kWh, Argon: 28.97 kg"
- 数字: [20.83, 147.26, 28.97] = 3个
- 数据密度: 3 / 15 = 0.2 → +0.04 ❌ 只有满分的 20%
```

**保守方案的改进**：

```python
- 数字: 3个
- 数据密度: 3 / 5 = 0.6 → +0.12 ✅ 达到满分的 60%
```

**改进效果**：
- ✅ 阈值从 15 降低到 5，更符合 LCA 数据的实际特点
- ✅ 3 个数字的 chunk 能获得合理的数据密度加成

---

#### **3. 表格标记权重 0.1 的问题**

**原方案**：
```python
if pipe_count >= 3:
    boost += 0.1
```

**保守方案的改进**：
```python
if pipe_count >= 10:
    boost += 0.15  # 复杂表格
elif pipe_count >= 3:
    boost += 0.1   # 简单表格
```

**改进效果**：
- ✅ 区分简单表格和复杂表格
- ✅ 复杂表格（多行数据）获得更高权重
- ✅ 提升结构化数据的排名

---

### **📝 原方案的核心问题总结**

| 问题 | 原方案 | 保守方案 | 改进效果 |
|------|--------|---------|---------|
| **覆盖率过高** | 0.5 | 0.25 | ✅ 降低"关键词堆砌"风险 |
| **数据密度阈值不合理** | 15个 | 5个 | ✅ 适配LCA实际场景 |
| **表格权重略低** | 0.1 | 0.15 | ✅ 提升结构化数据排名 |
| **总分范围** | 0-1.7 | 0-1.6 | ✅ 更平衡 |

---

## **新方案：保守版搜索排序优化（v5.0）**

### **🎯 核心设计原则**

1. **语义相似度为主导**（0-1.0）
2. **覆盖率为辅助**（0-0.25，避免压倒语义）
3. **数据密度为关键特征**（0-0.2，适配LCA场景）
4. **表格标记为结构化加成**（0-0.15，区分简单/复杂表格）

---

### **📊 权重分配**

```python
最终分数 = 语义相似度 (0-1.0)      # 基础，Qdrant提供
         + 覆盖率 (0-0.25)         # 辅助，避免风险
         + 数据密度 (0-0.2)        # 关键，LCA特征
         + 表格标记 (0-0.15)       # 加成，结构化数据

总分范围: 0-1.6
```

**权重占比**：
- 语义相似度: 62.5%（主导）
- 覆盖率: 15.6%（辅助）
- 数据密度: 12.5%（重要）
- 表格标记: 9.4%（加成）

---

### **💻 完整实现代码**

```python
def _calculate_coverage_boost(self, content: str, queries: List[str]) -> float:
    """
    计算覆盖率提升分数（保守版）
    
    核心逻辑:
    - 统计 chunk 中出现了多少个**不同的**关键词
    - 使用 set() 去重，避免词频干扰
    - 权重设置为 0.25（而非 0.5），降低风险
    
    Args:
        content: chunk 内容
        queries: 搜索关键词列表
        
    Returns:
        覆盖率提升分数 (0-0.25)
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
    
    # 覆盖率提升分数 (0-0.25)
    # 100% 覆盖 = +0.25
    # 75% 覆盖 = +0.19
    # 50% 覆盖 = +0.125
    # 25% 覆盖 = +0.06
    coverage_boost = coverage_rate * 0.25
    
    return coverage_boost


def _calculate_data_density_boost(self, content: str) -> float:
    """
    计算数据密度提升分数（优化版）
    
    核心逻辑:
    - LCA 数据通常包含 3-5 个关键数字
    - 阈值调整为 5 个数字（而非 15 个）
    
    Args:
        content: chunk 内容
        
    Returns:
        数据密度提升分数 (0-0.2)
    """
    import re
    
    # 提取数字（包括小数）
    numbers = re.findall(r'\d+\.?\d*', content)
    
    # 5 个数字达到满分
    # 3 个数字 = +0.12
    # 5 个数字 = +0.2
    # 10+ 个数字 = +0.2（封顶）
    data_boost = min(len(numbers) / 5.0, 1.0) * 0.2
    
    return data_boost


def _calculate_table_boost(self, content: str) -> float:
    """
    计算表格标记提升分数（优化版）
    
    核心逻辑:
    - 区分简单表格（少行）和复杂表格（多行）
    - 复杂表格通常包含更多数据，权重更高
    
    Args:
        content: chunk 内容
        
    Returns:
        表格标记提升分数 (0-0.15)
    """
    pipe_count = content.count('|')
    
    if pipe_count >= 10:
        # 复杂表格（多行数据）
        # 例如: 3行数据 + 表头 = 至少 12 个 |
        return 0.15
    elif pipe_count >= 3:
        # 简单表格（少行数据）
        # 例如: 1行数据 + 表头 = 至少 6 个 |
        return 0.1
    else:
        # 非表格
        return 0.0


def _calculate_enhanced_boost(self, content: str, queries: List[str]) -> float:
    """
    增强版排序算法（保守版 v5.0）
    
    组成:
    1. 覆盖率提升 (0-0.25) ← 降低权重，减少风险
    2. 数据密度提升 (0-0.2) ← 调整阈值，适配LCA
    3. 表格标记提升 (0-0.15) ← 区分简单/复杂表格
    
    总提升范围: 0-0.6
    
    Args:
        content: chunk 内容
        queries: 搜索关键词列表
        
    Returns:
        总提升分数 (0-0.6)
    """
    boost = 0.0
    
    # 1. 覆盖率提升（最多 +0.25）
    coverage_boost = self._calculate_coverage_boost(content, queries)
    boost += coverage_boost
    
    # 2. 数据密度提升（最多 +0.2）
    data_boost = self._calculate_data_density_boost(content)
    boost += data_boost
    
    # 3. 表格标记提升（最多 +0.15）
    table_boost = self._calculate_table_boost(content)
    boost += table_boost
    
    return boost


def _process_search_results(self, results, query, extract_mode):
    """
    处理搜索结果，根据模式进行智能提取（v5.0）
    
    改进:
    1. 支持单查询和批量查询
    2. 使用增强版排序算法
    3. 按提升后的分数重新排序
    
    Args:
        results: 搜索结果列表
        query: 查询词（字符串或列表）
        extract_mode: 提取模式（"chunks", "sentences", "key_points"）
        
    Returns:
        处理后的结果列表（已排序）
    """
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
        
        # 根据提取模式处理内容
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
    
    # 按提升后的分数排序
    processed.sort(key=lambda x: x.get("_boosted_score", 0), reverse=True)
    
    return processed
```

---

### **📈 效果对比（保守方案 vs 原方案）**

#### **场景 1: 关键词选择不当（宽泛词）**

**搜索**: `["process", "energy", "consumption", "manufacturing"]`

| Chunk | 内容摘要 | 覆盖率 | 数字 | 原方案 | 保守方案 | 排名变化 |
|-------|---------|--------|------|--------|---------|---------|
| A | "manufacturing process requires energy consumption" (无数据) | 100% | 0 | 0.70+0.5+0=**1.20** | 0.70+0.25+0=**0.95** | 🥇→🥉 |
| B | "Electricity consumption: 147.26 kWh" (有数据) | 50% | 2 | 0.88+0.25+0.027=**1.157** | 0.88+0.125+0.08=**1.085** | 🥈→🥇 |
| C | "Process Energy: 147.26 kWh during build" (完整数据) | 25% | 2 | 0.92+0.125+0.027=**1.072** | 0.92+0.06+0.08=**1.06** | 🥉→🥈 |

**原方案排序**: A > B > C ❌ **错误！无数据的排第一**  
**保守方案排序**: B > C > A ✅ **正确！有数据的排前面**

---

#### **场景 2: 精准关键词**

**搜索**: `["Ti6Al4V", "powder", "kg"]`

| Chunk | 内容摘要 | 覆盖率 | 数字 | 原方案 | 保守方案 | 排名变化 |
|-------|---------|--------|------|--------|---------|---------|
| A | "Ti6Al4V powder: 20.83 kg" (完整数据) | 100% | 2 | 0.92+0.5+0.027=**1.447** | 0.92+0.25+0.08=**1.25** | 🥇→🥇 |
| B | "Ti6Al4V powder was used" (无数据) | 67% | 0 | 0.85+0.33+0=**1.18** | 0.85+0.17+0=**1.02** | 🥈→🥈 |
| C | "Material: 20.83 kg" (部分数据) | 33% | 2 | 0.75+0.17+0.027=**0.947** | 0.75+0.08+0.08=**0.91** | 🥉→🥉 |

**原方案排序**: A > B > C ✅ **正确**  
**保守方案排序**: A > B > C ✅ **正确**

**结论**: 精准关键词下，两种方案都能正确排序，但保守方案更稳健。

---

#### **场景 3: 表格数据**

**搜索**: `["material", "value", "unit"]`

| Chunk | 内容摘要 | 覆盖率 | 数字 | 表格 | 原方案 | 保守方案 | 排名变化 |
|-------|---------|--------|------|------|--------|---------|---------|
| A | 表格（3行数据） | 100% | 6 | 复杂 | 0.88+0.5+0.08+0.1=**1.56** | 0.88+0.25+0.2+0.15=**1.48** | 🥇→🥇 |
| B | 表格标题行 | 100% | 0 | 简单 | 0.60+0.5+0+0.1=**1.20** | 0.60+0.25+0+0.1=**0.95** | 🥈→🥉 |
| C | "Material: Ti6Al4V, Value: 20.83, Unit: kg" | 100% | 2 | 无 | 0.85+0.5+0.027+0=**1.377** | 0.85+0.25+0.08+0=**1.18** | 🥉→🥈 |

**原方案排序**: A > C > B ⚠️ **勉强正确，但 B 分数过高**  
**保守方案排序**: A > C > B ✅ **正确，且 B 的分数更合理**

---

### **🎯 保守方案的核心优势**

#### **1. 降低"关键词堆砌"风险**
```
覆盖率权重: 0.5 → 0.25（降低 50%）
```
- ✅ 无数据但覆盖率高的 chunk 不会轻易超越有数据的 chunk
- ✅ 语义相似度重新成为主导因素

---

#### **2. 适配 LCA 实际场景**
```
数据密度阈值: 15 → 5（降低 67%）
```
- ✅ 3 个数字的 chunk 能获得 +0.12（而非 +0.04）
- ✅ 更符合 LCA 数据的实际特点

---

#### **3. 提升结构化数据排名**
```
表格权重: 0.1 → 0.15（提升 50%）
复杂表格: 新增额外加成
```
- ✅ 多行表格（真实数据）排名更高
- ✅ 表格标题行（无数据）排名降低

---

#### **4. 更平衡的权重分配**
```
语义: 62.5%（主导）
覆盖率: 15.6%（辅助）
数据密度: 12.5%（重要）
表格: 9.4%（加成）
```
- ✅ 语义相似度仍然是主导因素
- ✅ 覆盖率只是辅助，不会压倒语义
- ✅ 各因素权重更合理

---

### **📋 实施建议**

#### **阶段 1: 实施保守方案**
1. 修改 `_calculate_coverage_boost`：权重 0.5 → 0.25
2. 修改 `_calculate_data_density_boost`：阈值 15 → 5
3. 修改 `_calculate_table_boost`：区分简单/复杂表格

#### **阶段 2: 测试验证**
1. 使用真实的 LCA 文档测试
2. 尝试不同的关键词组合（精准词、宽泛词、常见词）
3. 观察排序结果是否合理

#### **阶段 3: 根据效果调整**
- 如果覆盖率效果不明显：权重 0.25 → 0.3
- 如果仍有"关键词堆砌"问题：权重 0.25 → 0.2
- 如果数据密度不够敏感：阈值 5 → 3

---

## **总结**

### **原方案的问题**
❌ 覆盖率权重 0.5 过高，风险大  
❌ 数据密度阈值 15 不符合 LCA 实际  
❌ 表格权重 0.1 略低

### **保守方案的改进**
✅ 覆盖率权重 0.25，平衡效果和风险  
✅ 数据密度阈值 5，适配 LCA 场景  
✅ 表格权重 0.15，区分简单/复杂表格  
✅ 语义相似度仍为主导（62.5%）

### **最终权重**
```
最终分数 = 语义相似度 (0-1.0) + 覆盖率 (0-0.25) + 数据密度 (0-0.2) + 表格 (0-0.15)
总分范围: 0-1.6
```
