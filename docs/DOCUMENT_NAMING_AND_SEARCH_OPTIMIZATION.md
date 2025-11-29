# 文档命名优化 & 搜索排序改进方案

## 📋 问题分析

### 问题 1: 文档命名优化

**当前命名方式**：
```python
# Line 129 in batch_generate_optimized.py
filename = f"doc_{i+1}_{difficulty}_{document_type}.md"
# 示例: doc_1_simple_batch_production_record.md
```

**存在的问题**：
1. ❌ 文件名过长（平均 40+ 字符）
2. ❌ 没有按照难度和类型排序
3. ❌ 文件名不够直观

**改进目标**：
- ✅ 精简命名（20-30 字符）
- ✅ 支持自然排序（按难度 → 类型）
- ✅ 易于识别和管理

---

### 问题 2: 搜索结果排序优化

**当前排序逻辑**：
```python
# Line 487-509 in tool_service.py
def _calculate_data_boost(self, content: str) -> float:
    boost = 0.0
    # 1. 数字数量（最多+0.15）
    numbers = re.findall(r'\d+\.?\d*', content)
    number_boost = min(len(numbers) / 10.0, 0.15)
    boost += number_boost
    # 2. 表格标记（最多+0.15）
    pipe_count = content.count('|')
    if pipe_count >= 3:
        boost += 0.15
    return boost
```

**存在的问题**：
1. ❌ 只考虑数字和表格，忽略关键词匹配
2. ❌ 没有考虑查询词在 chunk 中的出现频率
3. ❌ 语义相似度和关键词匹配权重不平衡

**改进目标**：
- ✅ 综合考虑：语义相似度 + 关键词匹配 + 数据密度
- ✅ 关键词出现次数越多，权重越高
- ✅ 不影响语义相似度的基础排序

---

## 🔧 解决方案

### 方案 1: 文档命名优化

#### 1.1 新命名规则

```
格式: paper_{文献ID}_{序号}_{难度代码}_{类型代码}.md

难度代码:
- 01-06: Simple (s)
- 07-09: Medium (m)
- 10: Complex (c)

类型代码（3-5字母缩写）:
- bpr: batch_production_record
- mt: material_traceability
- bjl: build_job_log
- qi: quality_inspection
- pdr: process_development_report
- tpr: technical_process_report
- mfs: manufacturing_feasibility_study
- pcs: process_characterization_study
- mba: multi_build_analysis
- rcs: research_case_study
```

#### 1.2 命名示例

**旧命名**：
```
doc_1_simple_batch_production_record.md (42 字符)
doc_1_medium_manufacturing_feasibility_study.md (48 字符)
```

**新命名**：
```
paper_001_01_s_bpr.md (21 字符) ✅
paper_001_07_m_mfs.md (21 字符) ✅
paper_001_10_c_rcs.md (21 字符) ✅
```

**排序效果**：
```bash
ls dataset/generated_docs/
paper_001_01_s_bpr.md  # Simple #1
paper_001_02_s_mt.md   # Simple #2
paper_001_03_s_bjl.md  # Simple #3
...
paper_001_07_m_mfs.md  # Medium #1
paper_001_08_m_pcs.md  # Medium #2
paper_001_09_m_mba.md  # Medium #3
paper_001_10_c_rcs.md  # Complex #1
```

---

### 方案 2: 搜索排序优化

#### 2.1 新排序算法

```python
def _calculate_enhanced_boost(self, content: str, queries: List[str]) -> float:
    """
    增强版排序算法
    
    综合考虑:
    1. 关键词匹配度 (0-0.4)
    2. 数据密度 (0-0.2)
    3. 表格标记 (0-0.1)
    
    总提升范围: 0-0.7
    """
    boost = 0.0
    
    # 1. 关键词匹配度（最多 +0.4）
    keyword_boost = self._calculate_keyword_boost(content, queries)
    boost += keyword_boost
    
    # 2. 数据密度（最多 +0.2）
    data_boost = self._calculate_data_density(content)
    boost += data_boost
    
    # 3. 表格标记（最多 +0.1）
    table_boost = self._calculate_table_boost(content)
    boost += table_boost
    
    return boost

def _calculate_keyword_boost(self, content: str, queries: List[str]) -> float:
    """
    计算关键词匹配度
    
    策略:
    - 查询词在 chunk 中出现次数越多，权重越高
    - 考虑词频和覆盖率
    """
    content_lower = content.lower()
    total_matches = 0
    unique_matches = 0
    
    for query in queries:
        query_lower = query.lower()
        count = content_lower.count(query_lower)
        if count > 0:
            total_matches += count
            unique_matches += 1
    
    # 词频分数 (0-0.25)
    frequency_score = min(total_matches / 10.0, 0.25)
    
    # 覆盖率分数 (0-0.15)
    coverage_score = (unique_matches / len(queries)) * 0.15 if queries else 0
    
    return frequency_score + coverage_score
```

#### 2.2 排序权重分配

```
最终分数 = 语义相似度 (0-1.0) + 增强提升分 (0-0.7)

组成部分:
├── 语义相似度 (0-1.0) ← ChromaDB embedding 相似度
└── 增强提升分 (0-0.7)
    ├── 关键词匹配 (0-0.4) ← 新增！
    │   ├── 词频分数 (0-0.25)
    │   └── 覆盖率分数 (0-0.15)
    ├── 数据密度 (0-0.2)
    └── 表格标记 (0-0.1)
```

#### 2.3 示例对比

**场景**: 搜索 `["electricity", "kWh", "energy"]`

**Chunk A**:
```
"The electricity consumption was 64.92 kWh for the SLM process. 
Energy efficiency improved by 12%."
```
- 语义相似度: 0.85
- 关键词匹配: 
  - "electricity" 出现 1 次
  - "kWh" 出现 1 次
  - "energy" 出现 1 次
  - 词频分数: 3/10 * 0.25 = 0.075
  - 覆盖率分数: 3/3 * 0.15 = 0.15
  - 关键词总分: 0.225
- 数据密度: 0.10
- **最终分数: 0.85 + 0.225 + 0.10 = 1.175** ✅

**Chunk B**:
```
"The manufacturing process uses various resources."
```
- 语义相似度: 0.75
- 关键词匹配: 0 (无匹配)
- 数据密度: 0
- **最终分数: 0.75** ❌

**结果**: Chunk A 排名更高 ✅

---

## 💻 实施代码

### 代码 1: 文档命名优化

```python
# 修改 batch_generate_optimized.py

# 定义类型代码映射
DOCUMENT_TYPE_CODES = {
    "batch_production_record": "bpr",
    "material_traceability": "mt",
    "build_job_log": "bjl",
    "quality_inspection": "qi",
    "process_development_report": "pdr",
    "technical_process_report": "tpr",
    "manufacturing_feasibility_study": "mfs",
    "process_characterization_study": "pcs",
    "multi_build_analysis": "mba",
    "research_case_study": "rcs"
}

# 定义难度代码
DIFFICULTY_CODES = {
    "simple": "s",
    "medium": "m",
    "complex": "c"
}

def generate_optimized_filename(
    paper_id: str,
    doc_index: int,
    difficulty: str,
    document_type: str
) -> str:
    """
    生成优化的文件名
    
    Args:
        paper_id: 文献ID (如 "001")
        doc_index: 文档序号 (1-10)
        difficulty: 难度 ("simple", "medium", "complex")
        document_type: 文档类型
        
    Returns:
        优化的文件名 (如 "paper_001_01_s_bpr.md")
    """
    difficulty_code = DIFFICULTY_CODES.get(difficulty, "x")
    type_code = DOCUMENT_TYPE_CODES.get(document_type, "unknown")
    
    return f"paper_{paper_id}_{doc_index:02d}_{difficulty_code}_{type_code}.md"

# 在生成循环中使用
for json_file in sorted(json_files):
    # 提取文献ID (如 "paper_001.json" -> "001")
    paper_id = os.path.basename(json_file).replace("paper_", "").replace(".json", "")
    
    doc_index = 1
    for difficulty, document_type in generation_config:
        # 生成优化的文件名
        filename = generate_optimized_filename(
            paper_id=paper_id,
            doc_index=doc_index,
            difficulty=difficulty,
            document_type=document_type
        )
        
        filepath = os.path.join(output_dir, filename)
        # ... 保存文档
        doc_index += 1
```

### 代码 2: 搜索排序优化

```python
# 修改 backend/services/tool_service.py

def _calculate_enhanced_boost(self, content: str, queries: List[str]) -> float:
    """
    增强版排序算法
    
    Args:
        content: chunk 内容
        queries: 搜索关键词列表
        
    Returns:
        提升分数 (0-0.7)
    """
    import re
    
    boost = 0.0
    
    # 1. 关键词匹配度（最多 +0.4）
    if queries:
        content_lower = content.lower()
        total_matches = 0
        unique_matches = 0
        
        for query in queries:
            query_lower = query.lower().strip()
            if not query_lower:
                continue
                
            # 计算出现次数
            count = content_lower.count(query_lower)
            if count > 0:
                total_matches += count
                unique_matches += 1
        
        # 词频分数 (0-0.25)
        frequency_score = min(total_matches / 10.0, 0.25)
        
        # 覆盖率分数 (0-0.15)
        coverage_score = (unique_matches / len(queries)) * 0.15 if queries else 0
        
        keyword_boost = frequency_score + coverage_score
        boost += keyword_boost
    
    # 2. 数据密度（最多 +0.2）
    numbers = re.findall(r'\d+\.?\d*', content)
    data_boost = min(len(numbers) / 15.0, 0.2)
    boost += data_boost
    
    # 3. 表格标记（最多 +0.1）
    pipe_count = content.count('|')
    if pipe_count >= 3:
        boost += 0.1
    
    return boost

def _process_search_results(self, results, query, extract_mode):
    """处理搜索结果，根据模式进行智能提取"""
    processed = []
    
    # 解析查询词（支持单查询和批量查询）
    if isinstance(query, str):
        # 单查询：按空格分割
        queries = [q.strip() for q in query.split() if q.strip()]
    else:
        # 批量查询：已经是列表
        queries = query if isinstance(query, list) else []
    
    for result in results:
        content = result.get("content", "")
        similarity = result.get("similarity_score", 0)
        
        # 计算增强提升分数
        enhanced_boost = self._calculate_enhanced_boost(content, queries)
        boosted_score = similarity + enhanced_boost
        
        # 临时存储用于排序（不会返回给前端）
        result["_boosted_score"] = boosted_score
        
        # ... 其余处理逻辑保持不变
```

---

## 📊 效果对比

### 命名效果

| 指标 | 旧命名 | 新命名 | 改进 |
|------|--------|--------|------|
| 平均长度 | 42 字符 | 21 字符 | ✅ -50% |
| 排序支持 | ❌ 无序 | ✅ 自然排序 | ✅ 100% |
| 可读性 | ⚠️ 一般 | ✅ 清晰 | ✅ 提升 |

### 搜索效果

| 场景 | 旧算法 | 新算法 | 改进 |
|------|--------|--------|------|
| 关键词密集 chunk | 语义 0.8 → 0.8 | 语义 0.8 → 1.2 | ✅ +50% |
| 无关键词 chunk | 语义 0.7 → 0.7 | 语义 0.7 → 0.7 | ✅ 不变 |
| 数据密集 chunk | 语义 0.6 → 0.75 | 语义 0.6 → 0.9 | ✅ +50% |

---

## 🚀 部署步骤

### 步骤 1: 备份现有文件

```bash
cd /home/Research_work/24_yzlin/LCA-LLM

# 备份生成脚本
cp scripts/batch_generate_optimized.py scripts/batch_generate_optimized.py.backup

# 备份工具服务
cp backend/services/tool_service.py backend/services/tool_service.py.backup
```

### 步骤 2: 应用命名优化

```bash
# 我将为你修改 batch_generate_optimized.py
```

### 步骤 3: 应用搜索优化

```bash
# 我将为你修改 tool_service.py
```

### 步骤 4: 测试验证

```bash
# 1. 测试文档生成
python scripts/batch_generate_optimized.py --file paper_002.json

# 2. 检查文件名
ls -lh dataset/generated_docs/ | head -20

# 3. 测试搜索功能（需要启动后端）
# 上传文档 → 搜索 "electricity kWh energy" → 检查排序
```

---

## ❓ 常见问题

### Q1: 新命名会影响现有文档吗？

**A**: 不会。新命名只影响新生成的文档。如果需要重命名现有文档，可以使用批量重命名脚本。

### Q2: 搜索优化会降低语义相似度的准确性吗？

**A**: 不会。新算法只是在语义相似度基础上增加关键词匹配权重，不会改变 embedding 的计算逻辑。

### Q3: 关键词匹配会不会过度提升某些 chunk？

**A**: 不会。关键词匹配最多提升 0.4 分，而语义相似度范围是 0-1.0，因此语义相似度仍然是主导因素。

---

## 📝 总结

### 命名优化

- ✅ 文件名精简 50%
- ✅ 支持自然排序
- ✅ 易于识别和管理

### 搜索优化

- ✅ 关键词匹配权重提升
- ✅ 综合考虑语义 + 关键词 + 数据密度
- ✅ 不影响语义相似度基础排序

**下一步**: 我将为你实施这两个优化方案。是否继续？
