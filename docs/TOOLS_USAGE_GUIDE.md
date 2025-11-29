# 🛠️ LCA-LLM核心工具使用指南

## 📋 目录
1. [工具概述](#工具概述)
2. [Phase 1 核心工具](#phase-1-核心工具)
   - [define_lca_scope - LCA范围定义](#define_lca_scope---lca范围定义工具)
   - [record_process_flow - 工艺流记录](#record_process_flow---工艺流记录工具)
   - [get_session_summary - 会话总结](#get_session_summary---会话总结工具)
3. [文档处理工具](#文档处理工具)
   - [process_document - 文档处理](#process_document---文档处理工具)
   - [search_document - 文档搜索](#search_document---文档搜索工具)
4. [数据库查询工具](#数据库查询工具)
   - [search_lci_database - LCI数据库搜索](#search_lci_database---lci数据库搜索工具)
5. [系统构建工具](#系统构建工具)
   - [build_lca_system - LCA系统构建](#build_lca_system---lca系统构建工具)
6. [使用流程示例](#使用流程示例)
7. [最佳实践](#最佳实践)
8. [常见问题](#常见问题)

---

## 🎯 工具概述

LCA-LLM系统提供七个核心工具，支持完整的LCA文档分析和数据提取工作流程：

> **🔧 重要更新说明**: `process_document` 工具已经过重要修正，现在仅作为纯文档预处理器使用，不再进行LCI数据的自动提取。这确保了第一阶段微调目标的正确性，即训练LLM学会通过工具调用来完成LCI数据提取。

| 工具名称 | 主要功能 | 输入 | 输出 | 使用场景 |
|---------|----------|------|------|----------|
| `define_lca_scope` | 📋 LCA范围定义 | 黄金三要素参数 | 范围定义记录 | 设定LCA分析基准 |
| `record_process_flow` | 🔄 工艺流记录 | LCI流数据 | 流记录ID | 记录输入输出数据 |
| `get_session_summary` | 📊 会话总结 | 会话ID | 结构化总结 | 获取分析状态 |
| `process_document` | 📄 PDF文档预处理 | PDF文件 | 会话ID + 全文 | 文档预处理与索引 |
| `search_document` | 🔍 文档内容搜索 | 查询词 | 相关文档片段 | 查找特定信息 |
| `search_lci_database` | 🗃️ LCI数据库查询 | 查询词 | 环境数据 | 获取标准LCA数据 |
| `build_lca_system` | 🏗️ LCA系统构建 | 系统描述 | pyLCA代码 | 生成计算代码 |

---

## 🎯 Phase 1 核心工具

Phase 1阶段的三个核心工具专门设计用于从生产工艺文档中提取结构化LCI数据，实现"初级LCI分析师"的功能。

### 🎯 define_lca_scope - LCA范围定义工具

#### 功能描述
基于"黄金三要素"原则，从生产工艺文档中提取核心LCA范围信息。

#### 黄金三要素
- **Functional Unit**: 生产什么产品，多少数量
- **System Boundary**: 包含哪些工艺步骤，从哪到哪  
- **Geographical Scope**: 生产地点、区域信息

#### 使用示例
```bash
curl -X POST http://localhost:8000/tools/define-lca-scope \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "pet_production_001",
    "parameter_name": "Functional Unit",
    "description": "生产1000公斤PET颗粒",
    "value": 1000.0,
    "unit": "kg"
  }'
```

### 🔄 record_process_flow - 工艺流记录工具

#### 功能描述
原子化地记录每一条工艺流数据，使用完备的LCI分类体系。

#### LCI分类体系
**输入流**: Raw Material, Ancillary Material, Energy, Water, Transport Service, Resource from Nature
**输出流**: Product, By-product, Waste for Treatment, Emission to Air, Emission to Water, Emission to Soil

#### 使用示例
```bash
curl -X POST http://localhost:8000/tools/record-process-flow \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "pet_production_001",
    "flow_type": "Input",
    "category": "Raw Material",
    "name": "精对苯二甲酸 (PTA)",
    "value": 850.0,
    "unit": "kg",
    "cas_number": "100-21-0",
    "process_name": "PET聚合反应"
  }'
```

### 📊 get_session_summary - 会话总结工具

#### 功能描述
赋予LLM"工作记忆"和"状态自省"能力，提供会话数据的结构化总结和完整性评估。

#### 使用示例
```bash
curl -X POST http://localhost:8000/tools/get-session-summary \
  -H "Content-Type: application/json" \
  -d '{"session_id": "pet_production_001"}'
```

---

## 📄 文档处理工具

### 📄 process_document - 文档处理工具

### 功能描述
**修正版 - 纯文档预处理器**

专门用于PDF文档的基础预处理工作，生成会话ID、提取完整文本并创建向量化索引。

**重要说明**: 本工具不进行LCI数据的自动提取和分析，而是为后续的LLM工具调用提供基础数据。

### 核心特性
- **PDF文档解析**: 提取完整的文本内容，不进行内容分析
- **智能分块**: 600字符分块，150字符重叠，保持语义连贯
- **向量化索引**: 为search_document工具创建ChromaDB索引
- **会话管理**: 生成唯一session_id用于后续工具调用
- **临时知识库**: 为每个会话创建独立的搜索空间
- **全文返回**: 返回完整文档文本供浏览和分析
- **自动清理**: 临时文件自动删除，防止存储泄露

### 参数说明

#### 必需参数
- `file_content` (string): PDF文件的base64编码内容
- `filename` (string): 文件名称

#### 可选参数
- `search_focus` (string): 保留参数，但在当前版本中不使用
  - 注意: 此参数为向后兼容保留，实际不影响处理流程

### 返回结果
```json
{
  "success": true,
  "session_id": "uuid-string-for-this-session",
  "message": "文档处理成功，共创建50个文本分块",
  "data": {
    "filename": "steel_production_lca.pdf",
    "total_pages": 10,
    "total_chunks": 50,
    "full_text": "这里是提取出的文档全部纯文本内容..."
  }
}
```

### 使用示例

#### API调用方式
```bash
curl -X POST "http://localhost:8000/tools/process-document" \
     -H "Content-Type: application/json" \
     -d '{
       "file_content": "JVBERi0xLjQ...",  # base64编码的PDF
       "filename": "steel_production_lca.pdf",
       "search_focus": "钢铁生产工艺"
     }'
```

#### Python代码示例
```python
import base64
import requests

# 读取PDF文件
with open("example.pdf", "rb") as f:
    file_content = base64.b64encode(f.read()).decode()

# 调用工具
response = requests.post(
    "http://localhost:8000/tools/process-document",
    json={
        "file_content": file_content,
        "filename": "example.pdf",
        "search_focus": "材料成分分析"
    }
)

result = response.json()
session_id = result["session_id"]  # 保存会话ID供后续使用
full_text = result["data"]["full_text"]  # 获取完整文档文本
```

### 处理流程
1. **会话创建** → 生成唯一session_id
2. **文件解码** → 将base64内容解码为PDF文件
3. **PDF解析** → 提取纯文本内容，不进行内容分析
4. **文档分块** → 智能分割，保持语义完整性
5. **向量化** → 生成语义向量，建立搜索索引
6. **知识库创建** → 建立临时ChromaDB知识库供search_document使用
7. **文本整合** → 将所有分块内容合并为完整文本
8. **结果返回** → 返回session_id和完整文档文本

---

## 🔍 search_document - 文档搜索工具

### 功能描述
在已处理的PDF文档中进行智能语义搜索，支持多种信息提取模式。**支持单查询和批量查询两种模式**。

### 核心特性
- **语义搜索**: 基于向量相似度的智能匹配
- **批量搜索**: 一次调用搜索多个相关关键词，自动去重
- **多提取模式**: chunks/sentences/key_points三种粒度
- **相似度过滤**: 可配置相似度阈值，确保结果质量
- **置信度评估**: 为每个结果提供可信度评分
- **上下文保持**: 保留完整文档片段便于深度分析

### 参数说明

#### 必需参数
- `session_id` (string): 文档处理会话ID（由process_document返回）

#### 单查询模式参数
- `query` (string): 单个搜索查询（与queries二选一）
- `max_results` (integer): 最大返回结果数 (默认: 5, 范围: 1-10)

#### 批量查询模式参数
- `queries` (array of strings): 多个相关关键词（与query二选一）
- `max_results_per_query` (integer): 每个查询的最大结果数 (默认: 3)
- `max_total_results` (integer): 总结果数上限 (默认: 10)
- `deduplicate` (boolean): 是否去重（基于chunk_id）(默认: true)

#### 通用可选参数
- `extract_mode` (string): 信息提取模式 (默认: "chunks")
- `min_similarity` (float): 最小相似度阈值 (默认: 0.3, 范围: 0-1)

### 提取模式详解

#### 1. chunks模式 (完整分块)
- **用途**: 需要详细上下文的查询
- **返回**: 完整的600字符文档分块
- **适用**: 深度分析、方法学理解、详细技术描述

#### 2. sentences模式 (精准句子)
- **用途**: 需要精确引用的查询
- **返回**: 最相关的1-2个句子
- **适用**: 数据引用、关键参数、具体数值

#### 3. key_points模式 (结构化要点)
- **用途**: 需要结构化总结的查询
- **返回**: 关键要点列表
- **适用**: 快速概览、要点提取、结构化信息

### 返回结果
```json
{
  "success": true,
  "message": "找到 3 个相关结果",
  "query": "能源消耗",
  "results": [
    {
      "rank": 1,
      "content": "提取的精准内容（根据extract_mode处理）",
      "full_content": "完整原文分块内容",
      "similarity_score": 0.85,
      "confidence": 0.78,
      "extract_type": "sentences",
      "metadata": {
        "page": 3,
        "chunk_id": "chunk_15"
      }
    }
  ],
  "document_info": {
    "filename": "example.pdf",
    "total_chunks": 50
  }
}
```

### 使用示例

#### 单查询模式：查找技术参数
```bash
curl -X POST "http://localhost:8000/tools/search-document" \
     -H "Content-Type: application/json" \
     -d '{
       "session_id": "your-session-id",
       "query": "能源消耗数据",
       "extract_mode": "sentences",
       "max_results": 3
     }'
```

#### 批量查询模式：搜索同义词
```bash
curl -X POST "http://localhost:8000/tools/search-document" \
     -H "Content-Type: application/json" \
     -d '{
       "session_id": "your-session-id",
       "queries": ["electricity", "energy", "power"],
       "max_results_per_query": 3,
       "max_total_results": 10,
       "extract_mode": "sentences",
       "deduplicate": true
     }'
```

#### 单查询模式：获取方法学概述
```bash
curl -X POST "http://localhost:8000/tools/search-document" \
     -H "Content-Type: application/json" \
     -d '{
       "session_id": "your-session-id",
       "query": "LCA方法学",
       "extract_mode": "key_points",
       "max_results": 5
     }'
```

### 搜索策略优化

#### 查询词选择
- **具体 > 抽象**: "电力消耗kWh" > "能源"
- **技术术语**: 使用LCA专业词汇
- **多语言**: 支持中英文混合查询
- **同义词**: 尝试不同表达方式

#### 批量搜索使用场景
- **同义词搜索**: `["electricity", "energy", "power"]` - 搜索能源相关的所有表述
- **多方面参数**: `["temperature", "pressure", "time"]` - 一次性查找多个工艺参数
- **不同单位**: `["kg", "kilogram", "weight"]` - 捕捉不同的单位表达
- **中英文混合**: `["材料", "material", "substance"]` - 多语言全面搜索

#### 模式选择指南
```python
# 查询类型 → 推荐模式
query_strategies = {
    "具体数值": "sentences",      # "碳排放系数是多少"
    "技术细节": "chunks",         # "生产工艺流程"
    "方法概述": "key_points",     # "研究采用了什么方法"
    "参数列表": "key_points",     # "主要技术参数"
    "精确引用": "sentences"       # "功能单位定义"
}

# 单查询 vs 批量查询
search_mode_guide = {
    "单查询": "具体概念，如'total energy consumption'",
    "批量查询": "同义词、相关术语，如['electricity', 'energy', 'power']"
}
```

---

## 🗄️ search_lci_database - LCI数据库搜索工具

### 功能描述
直接搜索生命周期清单(LCI)数据库，获取标准化的环境数据、排放因子和材料属性。

### 核心特性
- **标准LCI数据**: 基于EcoInvent等权威数据库
- **向量化搜索**: 使用Qwen3-Embedding-0.6B模型，1024维语义向量
- **混合搜索**: 语义搜索 + 关键词搜索双重保障
- **地理定位**: 支持特定地区的环境数据
- **质量过滤**: 可配置相似度阈值，确保数据相关性

### 参数说明

#### 必需参数
- `query` (string): 搜索查询

#### 可选参数
- `max_results` (integer): 最大返回结果数 (默认: 5, 范围: 1-10)
- `similarity_threshold` (float): 相似度阈值 (默认: 0.3, 范围: 0.1-0.9)

### 返回结果
```json
{
  "success": true,
  "message": "Found 4 LCI database entries for 'steel production'",
  "query": "steel production",
  "results": [
    {
      "rank": 1,
      "name": "Steel production, electric arc furnace",
      "description": "电弧炉钢铁生产工艺",
      "category": "Materials/Metals",
      "unit": "kg",
      "similarity_score": 0.92,
      "environmental_data": {
        "carbon_footprint": "1.85 kg CO2-eq/kg",
        "energy_consumption": "3.2 MJ/kg",
        "water_usage": "15.6 L/kg"
      },
      "metadata": {
        "database": "ecoinvent_3.8",
        "geography": "GLO",
        "technology_level": "current"
      }
    }
  ],
  "total_results": 4,
  "search_parameters": {
    "max_results": 5,
    "similarity_threshold": 0.3
  }
}
```

### 使用示例

#### 查找标准排放因子
```bash
curl -X POST "http://localhost:8000/tools/search-lci-database" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "electricity production carbon footprint",
       "max_results": 3,
       "similarity_threshold": 0.4
     }'
```

#### 获取材料属性数据
```bash
curl -X POST "http://localhost:8000/tools/search-lci-database" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "plastic PET production",
       "max_results": 5,
       "similarity_threshold": 0.3
     }'
```

### 搜索类别指南

#### 材料类查询
- **金属**: "steel production", "aluminum manufacturing", "copper mining"
- **塑料**: "PET plastic", "polyethylene production", "polystyrene"
- **建材**: "concrete production", "cement manufacturing", "glass"

#### 能源类查询
- **电力**: "electricity production", "grid electricity", "renewable energy"
- **燃料**: "natural gas", "diesel fuel", "gasoline combustion"
- **热能**: "steam production", "heating natural gas"

#### 运输类查询
- **货运**: "truck transport", "rail freight", "ship transport"
- **客运**: "passenger car", "bus transport", "air transport"

#### 废物处理
- **回收**: "recycling plastic", "metal recycling", "paper recycling"
- **处置**: "landfill", "incineration", "wastewater treatment"

---

## 🔄 使用流程示例

### 完整工作流程示例

#### 1. 文档上传与处理
```python
import base64
import requests

# 步骤1: 处理PDF文档
with open("lca_study.pdf", "rb") as f:
    file_content = base64.b64encode(f.read()).decode()

process_response = requests.post(
    "http://localhost:8000/tools/process-document",
    json={
        "file_content": file_content,
        "filename": "lca_study.pdf",
        "search_focus": "材料消耗和能源使用"
    }
)

result_data = process_response.json()
session_id = result_data["session_id"]
full_text = result_data["data"]["full_text"]
print(f"✅ 文档处理完成，会话ID: {session_id}")
```

#### 2. 文档信息检索
```python
# 步骤2: 搜索文档中的技术参数
doc_search = requests.post(
    "http://localhost:8000/tools/search-document",
    json={
        "session_id": session_id,
        "query": "生产工艺技术参数",
        "extract_mode": "key_points",
        "max_results": 5
    }
)

doc_results = doc_search.json()["data"]["results"]
print(f"✅ 找到 {len(doc_results)} 个文档结果")

# 打印文档搜索结果
for result in doc_results:
    print(f"📄 [{result['rank']}] {result['content']}")
    print(f"   相似度: {result['similarity_score']:.3f}")
```

#### 3. 标准数据查询
```python
# 步骤3: 查询相关的LCI标准数据
lci_search = requests.post(
    "http://localhost:8000/tools/search-lci-database",
    json={
        "query": "steel production energy consumption",
        "max_results": 3,
        "similarity_threshold": 0.4
    }
)

lci_results = lci_search.json()["data"]["results"]
print(f"✅ 找到 {len(lci_results)} 个LCI数据")

# 打印LCI搜索结果
for result in lci_results:
    print(f"🗄️ {result['name']}")
    print(f"   类别: {result['category']}")
    print(f"   碳足迹: {result['environmental_data']['carbon_footprint']}")
    print(f"   相似度: {result['similarity_score']:.3f}")
```

#### 4. 数据对比分析
```python
# 步骤4: 对比文档数据与标准数据
print("\n📊 数据对比分析:")
print("文档中的信息:")
for result in doc_results[:3]:
    print(f"  - {result['content'][:100]}...")

print("\n标准LCI数据:")
for result in lci_results:
    print(f"  - {result['name']}: {result['environmental_data']['carbon_footprint']}")
```

### LLM工具调用示例

#### 在AI对话中的应用
```python
# LLM会根据用户问题自动选择和调用工具
user_query = "这个文档中提到的钢铁生产数据与标准数据相比如何？"

# LLM自动执行的工具调用序列:
# 1. search_document(query="钢铁生产数据", extract_mode="sentences")
# 2. search_lci_database(query="steel production")
# 3. 分析和对比两组数据
# 4. 生成专业分析报告
```

---

## 💡 最佳实践

### 1. 文档处理优化

#### 文件准备
- **格式要求**: 确保PDF可读，避免扫描版或加密文件
- **文件大小**: 建议小于50MB，大文件会影响处理速度
- **内容质量**: 结构清晰的文档处理效果更好

#### search_focus策略
```python
# 根据文档类型选择合适的搜索重点
focus_strategies = {
    "LCA研究报告": "LCA方法学 系统边界 影响评估",
    "技术规范": "技术参数 工艺流程 设备规格",
    "环境数据": "排放因子 能源消耗 材料用量",
    "产品手册": "产品规格 材料成分 性能参数"
}
```

### 2. 搜索查询优化

#### 文档搜索技巧
```python
# 有效的查询策略
query_tips = {
    "具体化": "电力消耗量kWh" > "能源使用",
    "术语化": "GWP全球变暖潜值" > "温室气体",
    "结构化": "原材料 + 用量 + 单位",
    "分层查询": "先概述后细节"
}

# 查询示例
queries = {
    "技术参数": "生产温度 压力 时间 产率",
    "环境数据": "CO2排放 能耗 水耗 废物",
    "方法学": "LCA方法 系统边界 功能单位",
    "结果分析": "环境影响 敏感性分析 不确定性"
}
```

#### LCI数据库查询技巧
```python
# 标准术语使用
standard_terms = {
    "材料": "production", "manufacturing", "processing",
    "能源": "electricity", "natural gas", "fuel oil",
    "运输": "transport", "freight", "logistics",
    "废物": "waste treatment", "recycling", "disposal"
}

# 地理修饰词
geography = {
    "全球": "GLO", "global", "worldwide",
    "欧洲": "Europe", "EU", "European",
    "中国": "China", "CN", "Chinese",
    "美国": "US", "USA", "United States"
}
```

### 3. 结果质量控制

#### 相似度阈值设置
```python
threshold_guide = {
    0.1: "最宽松，可能包含不相关结果",
    0.3: "平衡设置，推荐日常使用",
    0.5: "较严格，确保高相关性",
    0.7: "很严格，只返回最匹配结果",
    0.9: "极严格，可能错过有用信息"
}
```

#### 结果验证
```python
def validate_results(results):
    """验证搜索结果质量"""
    quality_indicators = {
        "similarity_score": 0.3,  # 最低相似度
        "confidence": 0.5,        # 最低置信度
        "content_length": 20      # 最短内容长度
    }
    
    valid_results = []
    for result in results:
        if (result.get("similarity_score", 0) >= quality_indicators["similarity_score"] and
            result.get("confidence", 0) >= quality_indicators["confidence"] and
            len(result.get("content", "")) >= quality_indicators["content_length"]):
            valid_results.append(result)
    
    return valid_results
```

### 4. 性能优化建议

#### 批量查询策略
```python
# 避免频繁单次查询，使用批量策略
def batch_search_strategy(session_id, queries):
    """批量搜索策略"""
    results = {}
    
    # 按查询类型分组
    specific_queries = [q for q in queries if len(q.split()) <= 3]
    general_queries = [q for q in queries if len(q.split()) > 3]
    
    # 先执行具体查询
    for query in specific_queries:
        results[query] = search_document(session_id, query, extract_mode="sentences")
    
    # 再执行概括查询
    for query in general_queries:
        results[query] = search_document(session_id, query, extract_mode="key_points")
    
    return results
```

#### 缓存策略
```python
# 对于重复查询，实现结果缓存
cache_strategy = {
    "常用术语": "预计算并缓存常见LCA术语搜索结果",
    "标准数据": "缓存经常查询的排放因子和材料数据",
    "文档摘要": "缓存文档的关键信息摘要"
}
```

---

## ❓ 常见问题

### Q1: 为什么search_document返回空结果？

**可能原因**:
1. **会话不存在**: session_id无效或已过期
2. **相似度阈值过高**: 降低min_similarity参数
3. **查询词不匹配**: 尝试不同的关键词组合
4. **文档未处理**: 确保先调用process_document

**解决方案**:
```python
# 检查会话状态
response = requests.get(f"http://localhost:8000/session/{session_id}/status")
if not response.json().get("exists"):
    print("❌ 会话不存在，请重新上传文档")

# 降低相似度阈值
search_result = search_document(
    session_id, 
    query, 
    min_similarity=0.1  # 降低阈值
)
```

### Q2: LCI数据库搜索结果不准确？

**常见问题**:
1. **查询词过于宽泛**: 使用更具体的术语
2. **语言混用**: 优先使用英文术语
3. **术语不标准**: 参考EcoInvent术语表

**改进策略**:
```python
# 术语标准化
def standardize_query(query):
    """标准化LCI查询术语"""
    mappings = {
        "钢铁": "steel",
        "塑料": "plastic",
        "电力": "electricity",
        "运输": "transport"
    }
    
    for cn, en in mappings.items():
        query = query.replace(cn, en)
    
    return query
```

### Q3: 工具调用超时怎么办？

**超时原因**:
1. **文档过大**: PDF文件超过推荐大小
2. **网络延迟**: 网络连接不稳定
3. **服务负载**: 后端服务繁忙

**解决方案**:
```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 配置重试策略
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

# 使用session进行请求
response = session.post(url, json=data, timeout=60)
```

### Q4: 如何提高搜索结果的相关性？

**优化技巧**:
```python
# 1. 分层查询策略
def hierarchical_search(session_id, topic):
    """分层搜索策略"""
    # 第一层：概况查询
    overview = search_document(
        session_id, 
        f"{topic} 概述 方法",
        extract_mode="key_points"
    )
    
    # 第二层：具体数据查询
    details = search_document(
        session_id,
        f"{topic} 数据 参数 数值",
        extract_mode="sentences"
    )
    
    return {"overview": overview, "details": details}

# 2. 多关键词组合
def multi_keyword_search(session_id, keywords):
    """多关键词组合搜索"""
    results = []
    
    # 单独查询每个关键词
    for keyword in keywords:
        result = search_document(session_id, keyword)
        results.extend(result["results"])
    
    # 组合查询
    combined_query = " ".join(keywords)
    combined_result = search_document(session_id, combined_query)
    results.extend(combined_result["results"])
    
    # 去重和排序
    unique_results = remove_duplicates(results)
    return sorted(unique_results, key=lambda x: x["similarity_score"], reverse=True)
```

### Q5: 如何处理多语言文档？

**处理策略**:
```python
# 多语言查询策略
def multilingual_search(session_id, topic):
    """多语言搜索策略"""
    # 中英文关键词映射
    bilingual_terms = {
        "材料": ["材料", "material", "substance"],
        "工艺": ["工艺", "process", "procedure"],
        "能源": ["能源", "energy", "power"],
        "排放": ["排放", "emission", "discharge"]
    }
    
    all_results = []
    for cn_term, terms in bilingual_terms.items():
        if topic in cn_term:
            for term in terms:
                results = search_document(session_id, term)
                all_results.extend(results["results"])
    
    return deduplicate_results(all_results)
```

---

## 📝 总结

这三个核心工具构成了LCA-LLM系统的基础功能：

1. **process_document**: 文档入口，建立搜索基础
2. **search_document**: 文档分析，获取具体信息
3. **search_lci_database**: 标准数据，提供对比基准

通过合理组合使用这些工具，可以实现从文档上传到深度分析的完整LCA工作流程。建议根据具体需求选择合适的参数配置，并遵循最佳实践以获得最佳效果。

---

*📅 文档更新日期: 2025-11-12*  
*🔧 文档版本: v1.1 - 新增批量搜索功能*  
*👥 维护团队: LCA-LLM开发组*
