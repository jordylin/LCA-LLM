# LCA-LLM 数据集制作指南

**版本**: v4.3  
**更新**: 2025-11-19  
**DeepSeek API Key**: `sk-b9f348bb5ba4437faa5a7253d085fd44`

---

## 📋 目录

1. [快速开始](#快速开始)
2. [方法A：真实文献标注](#方法a真实文献标注)
3. [方法B：逆向生成文档](#方法b逆向生成文档)
4. [常见问题](#常见问题)

---

## 快速开始

### 系统要求

```bash
# Python 3.8+
pip install streamlit openai pymongo python-dotenv
```

### API配置

```bash
# 设置DeepSeek API Key
export DEEPSEEK_API_KEY="sk-b9f348bb5ba4437faa5a7253d085fd44"
```

### 启动工作台

```bash
cd /home/Research_work/24_yzlin/LCA-LLM
streamlit run scripts/expert_annotation_workbench.py
```

浏览器打开：`http://localhost:8504`

## 方法B：逆向生成文档

**适合**：快速扩展数据集  
**速度**：快（1个LCI数据 → 12个文档 ≈ 30分钟）

### 步骤1：准备LCI数据

#### 方法1：使用模板

```bash
cd /home/Research_work/24_yzlin/LCA-LLM

# 复制模板
cp dataset/lci_literature/template.json dataset/lci_literature/paper_001.json

# 编辑文件
nano dataset/lci_literature/paper_001.json
```

### 步骤2：生成文档

#### 单个文档测试

```bash
cd scripts
export DEEPSEEK_API_KEY="sk-b9f348bb5ba4437faa5a7253d085fd44"
python reverse_engineer_documents.py
```

输出：`dataset/documents/test_simple_batch_production_record.md`

#### 批量生成（推荐）

**方案 A：优化版本（推荐）⭐**

```bash
# 批量生成：10个文档/篇（6 Simple + 3 Medium + 1 Complex）
python scripts/batch_generate_optimized.py \
  --input-dir dataset/lci_literature \
  --file paper_003.json \
  --output-dir dataset/documents/phase3
```

输出（每篇文献）：
```
dataset/documents/phase3/
├── doc_1_simple_batch_production_record.md
├── doc_1_simple_process_certification.md
├── doc_1_simple_material_traceability.md
├── doc_1_simple_build_job_log.md
├── doc_1_simple_quality_inspection.md
├── doc_1_simple_process_parameter_sheet.md
├── doc_1_medium_batch_production_record.md
├── doc_1_medium_material_traceability.md
├── doc_1_medium_build_job_log.md
└── doc_1_complex_process_certification.md
```

**优点**：
- ✅ 每篇文献 10 个文档（避免过拟合）
- ✅ Simple 占 60%（基础能力训练）
- ✅ Medium 占 30%（语义理解训练）
- ✅ Complex 占 10%（推理计算训练）
- ✅ 鼓励多文献多样性

**方案 B：完整版本**

```bash
# 批量生成：3难度 × 9类型 = 27个文档
python scripts/batch_generate_all.py
```

**说明**：
- ✅ 自动读取 `dataset/lci_literature/` 下所有 `paper_*.json` 文件
- ✅ 优化版本：每个LCI数据生成 10 个文档
- ✅ 完整版本：每个LCI数据生成 27 个文档
- ✅ 如果有 6 个JSON文件（优化版本），生成 60 个文档

### 步骤3：导入工作台标注

1. 启动工作台：`streamlit run expert_annotation_workbench.py`
2. 上传生成的文档（Markdown转PDF或直接粘贴）
3. 按照方法A的步骤2-6进行标注和导出

---

## 常见问题

### Q1: 文献中缺少某些数据怎么办？

**答**：直接省略即可。

```json
// 示例：只有Raw Material, Process Energy, Product
{
  "inputs": [
    {"category": "Raw Material", "name": "Ti-6Al-4V powder", "value": 1.2, "unit": "kg"},
    {"category": "Process Energy", "name": "Electricity", "value": 120, "unit": "MJ"}
  ],
  "outputs": [
    {"category": "Product", "name": "Ti-6Al-4V part", "value": 1.0, "unit": "kg"}
  ]
}
```

**最小要求**：至少1个Input + 1个Output

---

### Q2: 如何批量处理多个文献？

**答**：创建多个JSON文件。

```bash
dataset/lci_literature/
├── paper_001.json  # SLM of Ti-6Al-4V
├── paper_002.json  # FDM of PLA
├── paper_003.json  # SLS of Nylon
└── paper_004.json  # DED of 316L
```

然后运行：
```bash
python scripts/batch_generate_all.py
```

自动处理所有文件！

---

### Q3: 生成的文档质量如何保证？

**答**：v1.5版本已添加质量约束。

**Logic Consistency约束**：
- ✅ LCI数据是绝对真理
- ✅ 禁止编造或矛盾的数值
- ✅ 防止数据幻觉

**Missing Data Protocol**：
- ✅ 缺失数据不编造
- ✅ 明确声明"未记录"或省略章节
- ✅ 支持负样本训练

**建议**：生成后人工抽查10-20%的文档。

---

### Q4: 三种难度有什么区别？

| 难度 | 数据呈现 | 训练目标 |
|-----|---------|---------|
| **Simple** | 表格集中，易于提取 | 视觉定位能力 |
| **Medium** | 数据分散在文本中 | 语义理解能力 |
| **Complex** | 只给参数，需要计算 | 推理计算能力 |

**示例（Complex）**：
```markdown
文档只写：
- Laser Power: 370 W
- Build Time: 14.5 h

模型需要计算：370W × 14.5h = 5.365 kWh
```

---

### Q5: 四种文档类型有什么区别？

| 类型 | 焦点 | 特点 |
|-----|------|------|
| **Batch Production Record** | 时间序列 | 批次追踪，时间戳 |
| **Process Certification** | 合规验证 | ISO/ASTM标准 |
| **Material Traceability** | 质量平衡 | 批号，回收率 |
| **Build Job Log** | 设备监控 | 传感器数据，报警 |

**建议**：均衡分布，每种类型生成相同数量的文档。

---

### Q6: 成本估算

**DeepSeek API成本**：
- 生成1个文档：约$0.01-0.02
- 生成1个推理：约$0.001-0.002

**60个文档的总成本**：
- 文档生成：$0.6-1.2
- 推理生成：$0.06-0.12
- **总计**：约$0.7-1.5

**非常便宜！** 🎉

---

### Q7: 为什么推荐 10 个文档而不是 27 个？

**答**：避免过拟合，鼓励文献多样性。

**问题**：27 个文档来自同一篇文献
- ⚠️  单篇文献占比过大
- ⚠️  LLM 可能记住特定文档内容
- ⚠️  泛化能力差

**解决方案**：10 个文档 + 多篇文献
- ✅ 6 篇文献 × 10 个文档 = 60 个样本
- ✅ 单篇文献占比 ~17%（合理）
- ✅ 文献多样性好
- ✅ 避免过拟合

**难度分布**：
- Simple 60%：基础能力（表格提取）
- Medium 30%：语义理解（文本提取）
- Complex 10%：推理计算（参数计算）

这符合**课程学习**（Curriculum Learning）原则：先简单 → 再中等 → 最后复杂

---

### Q8: 推荐的工作流程

**第1周**：准备 6 篇文献的 LCI 数据
- 从真实文献提取或手动创建
- 确保文献主题多样性（不同材料、工艺、产品）

**第2周**：批量生成文档
- 使用 `batch_generate_optimized.py`
- 每篇文献生成 10 个文档
- 总共 60 个文档

**第3周**：工作台标注
- 导入 60 个文档
- 生成 60 个 Full 对话
- 可选：生成 48-60 个 Short 对话

**第4周**：导出和微调
- 导出训练数据
- 生成推理内容
- 转换为 JSONL
- 开始第一轮微调测试

---

## 📊 完整工作流对比

| 步骤 | 方法A（真实文献） | 方法B（逆向生成） |
|-----|-----------------|-----------------|
| **准备** | 下载AM-LCA文献 | 准备LCI数据JSON |
| **生成** | - | 批量生成文档 |
| **标注** | 工作台标注 | 工作台标注 |
| **导出** | export_training_data.py | export_training_data.py |
| **推理** | generate_think_with_camel.py | generate_think_with_camel.py |
| **转换** | convert_json_to_jsonl.py | convert_json_to_jsonl.py |
| **时间** | 2-4小时/篇 | 30分钟/12篇 |
| **质量** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## 🚀 快速命令速查

### 工作台
```bash
streamlit run scripts/expert_annotation_workbench.py
```

### 逆向生成
```bash
cd scripts
export DEEPSEEK_API_KEY="sk-b9f348bb5ba4437faa5a7253d085fd44"

# 推荐：优化版本（10个文档/篇）
python batch_generate_optimized.py

# 或：完整版本（27个文档/篇）
python batch_generate_all.py
```

### 导出训练数据
```bash
cd scripts
python export_training_data.py
python generate_think_with_camel.py
python convert_json_to_jsonl.py
```

### 验证数据
```bash
head -n 3 ../dataset/training_data/training_data.jsonl | jq .
```

---

## 📚 相关文档

- `LCA_LLM_v4.3_GUIDE.md` - 完整系统指南
- `Expert_Workbench_Guide.md` - 工作台详细说明
- `REVERSE_GENERATION_FAQ.md` - 逆向生成完整FAQ
- `dataset/lci_literature/template.json` - LCI数据模板

---

## ✅ 检查清单

### 开始前
- [ ] Python 3.8+ 已安装
- [ ] 依赖包已安装（streamlit, openai, pymongo）
- [ ] DeepSeek API Key已设置
- [ ] MongoDB已启动（如果使用数据库）

### 方法A（真实文献）
- [ ] PDF文献已准备
- [ ] 工作台已启动
- [ ] 已完成Phase 1-4标注
- [ ] 已导出训练样本
- [ ] 已生成推理内容
- [ ] 已转换为JSONL

### 方法B（逆向生成）
- [ ] LCI数据JSON已创建
- [ ] 已批量生成文档
- [ ] 已导入工作台标注
- [ ] 已导出训练样本
- [ ] 已生成推理内容
- [ ] 已转换为JSONL

### 质量检查
- [ ] 训练数据格式正确
- [ ] 推理内容合理
- [ ] 无数据幻觉（数值一致）
- [ ] 负样本处理正确（缺失数据）

---

**现在可以开始制作数据集了！** 🎉
