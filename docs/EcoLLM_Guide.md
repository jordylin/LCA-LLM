# EcoLLM 数据集构建指南

**更新日期**: 2025-11-22  
**版本**: 1.1 (新增关键词建议器)
**适用项目**: LCA-LLM (Additive Manufacturing LCI Extraction)

---

## 📋 目录

1. [系统概述](#系统概述)
2. [LCI分类体系](#lci分类体系)
3. [数据标注流程](#数据标注流程)
4. [文档生成器](#文档生成器)
5. [训练数据导出](#训练数据导出)
6. [Batch Search关键词](#batch-search关键词)
7. [工作台使用指南](#工作台使用指南)
8. [关键词建议器使用](#关键词建议器使用)

---

## 系统概述

### 核心目标

构建高质量SFT数据集，训练LLM从增材制造文献中系统化提取LCI（Life Cycle Inventory）数据。

### 数据生产流程

```
┌────────────────────────────────────────┐
│ 来源1: 真实文献                         │
│ - 人工标注PDF文献                       │
│ - 工作台辅助提取                        │
└────────────────────────────────────────┘
                ↓
┌────────────────────────────────────────┐
│ 来源2: 逆向生成文档 (v3.1.2)            │
│ - 从LCI数据生成多样化文档               │
│ - 9种文档类型 × 3难度 = 27种            │
│ - 再导入工作台标注                      │
└────────────────────────────────────────┘
                ↓
┌────────────────────────────────────────┐
│ 导出训练样本                            │
│ - export_training_data.py               │
│ - 生成messages格式                      │
└────────────────────────────────────────┘
                ↓
┌────────────────────────────────────────┐
│ 生成推理内容                            │
│ - generate_think_with_camel.py          │
│ - CAMEL AI生成<think>                   │
└────────────────────────────────────────┘
                ↓
┌────────────────────────────────────────┐
│ 转换为JSONL                             │
│ - convert_json_to_jsonl.py              │
│ - OpenAI格式，用于SFT                   │
└────────────────────────────────────────┘
```

---

## LCI分类体系

### 11个核心类别

#### Phase 1: Function Unit (锚点) ⭐ 新增
```
Function Unit - 功能单位定义（确定归一化基准）
              - 位置：文档开头或Methods章节
              - 类型：文本描述（非表格）
              - 策略：通过Product反推（同一物理对象，两种记录方式）
              - 搜索优先级：
                1️⃣ 优先：生产描述语句
                   * "We manufactured 10 Ti-6Al-4V parts..."
                   * "A batch of 15 specimens was fabricated..."
                2️⃣ 备选：如果找不到明确生产描述，使用Product相关内容
              - 关键词：manufactured, part, product, kg, fabricated, printed
              - 记录方式：
                * Phase 1：记录文本描述（定义层）- 功能单位
                * Phase 2：记录数值+单位（计算层）- 产品输出流
```

#### Phase 2: Input Flows (6个) ⭐ 标准LCA顺序：先输入
```
Raw Material          - 原材料（powder, filament等）
Process Energy        - 机器能耗（printing, laser等）
Post-processing Energy - 后处理能耗（heat treatment, machining等）
Feedstock Energy      - 原料生产能耗（atomization等）
Gas                   - 保护气体（argon, nitrogen等）
Cooling Media         - 冷却介质（water, coolant等）
```

#### Phase 3: Output Flows (4个)
```
Product               - 制造的产品输出量（使用Phase 1搜索结果）
                      - 位置：Materials/Results章节，可能在表格或文本中
                      - 示例："Ti-6Al-4V part, 2.5 kg"
Recovered Material    - 回收材料（recovered powder等）
Waste                 - 废料（support structures, scrap等）
Emission              - 排放（VOC, particulate等）
```

#### Phase 4: Validation (验证)
```
- 检查Function Unit已定义
- 检查关键Input Flows（Raw Material, Energy）
- 检查Product已记录
- 验证质量平衡和归一化
```

### Energy分类详解

| 类别 | 定义 | 典型来源 |
|-----|------|---------|
| **Process Energy** | 打印机运行能耗 | SLM laser, FDM heater, machine power |
| **Post-processing Energy** | 后续处理能耗 | Heat treatment, CNC machining, polishing |
| **Feedstock Energy** | 原料制备能耗 | Powder atomization (SEC × powder mass) |

**注意**：Feedstock Energy不包括Primary Material的Embodied Energy（上游背景数据）。

---

## 数据标注流程

### 4-Phase工作流程

```
Phase 1: Product (Anchor)
  ↓ 确定功能单位基准
Phase 2: Input Flows
  Raw Material → Process Energy → Post-processing Energy 
  → Feedstock Energy → Gas → Cooling Media
  ↓ 系统化收集输入
Phase 3: Output Flows
  Recovered Material → Waste → Emission
  ↓ 完整性检查
Phase 4: Validation
  检查关键类别 → 确认归一化 → 生成Summary
```

### Phase 1: Product First策略

**为什么Product优先？**
1. Product的单位隐含功能单位（kg, piece, m³）
2. 有了基准才能判断Input是否已归一化
3. 符合文献逻辑（先说"制造了什么"）

**示例**：
```
Product: "Ti-6Al-4V part, 2.5 kg"
→ 推断功能单位: "1 kg of Ti-6Al-4V part"
→ 所有Input/Output数据需归一化到此单位
```

---

## 文档生成器

### 逆向生成系统 (v3.1.2)

**核心思路**：
```
真实文献 → 提取LCI数据 → 生成多样化文档 → 工作台标注 → 训练数据
```

**优势**：
- ✅ 可扩展：1个LCI → 27个文档（3难度×9类型）
- ✅ 多样性：不同风格、长度、难度
- ✅ 成本效益：相比人工撰写降低90%+成本

### 难度等级

#### Simple（简单）
- 数据集中在表格
- 一眼就能看到所有LCI数据
- 适合快速提取训练

#### Medium（中等）
- 数据分散在多个章节/小表格
- 需要读多个section收集完整
- 训练多步骤搜索能力

#### Complex（复杂）
- 只给参数，不给结果
- 需要计算得出LCI数据
- 训练推理和计算能力

**Complex示例**：
```markdown
**Argon Consumption Parameters:**
- Per-component volume: 54 L
- Components: 33 pieces
- Chamber filling: 700 L
- Density: 1.784 g/L

→ 读者需计算: (54×33 + 700) × 1.784 = 3.08 kg
```

### 文档类型（9种）

#### Tier 1 - 短文档（1500-2500词）
1. **Batch Production Record** - 批次生产记录
2. **Build Job Log** - 设备作业日志
3. **Material Traceability** - 物料追溯报告
4. **Quality Inspection** - 质量检验报告

#### Tier 2 - 中文档（3000-4500词）
5. **Technical Process Report** - 技术工艺报告
6. **Environmental Assessment** - 环境评估总结
7. **Multi-Build Analysis** - 多批次对比分析

#### Tier 3 - 长文档（5000-7000词）
8. **Research Case Study** - 研究案例分析
9. **Sustainability Report** - 可持续性报告章节

### 使用流程

#### 步骤1：准备LCI数据

创建JSON文件：`dataset/lci_literature/paper_001.json`

```json
{
  "papers": [
    {
      "title": "SLM of Ti-6Al-4V: Process Optimization",
      "lci_data": {
        "process_name": "Selective Laser Melting of Ti-6Al-4V",
        "functional_unit": "1 kg of Ti-6Al-4V part",
        "inputs": [
          {
            "category": "Raw Material",
            "name": "Ti-6Al-4V powder",
            "value": 1.2,
            "unit": "kg"
          },
          {
            "category": "Process Energy",
            "name": "Electricity",
            "value": 120,
            "unit": "MJ"
          },
          {
            "category": "Post-processing Energy",
            "name": "Heat treatment",
            "value": 1.5,
            "unit": "MJ"
          },
          {
            "category": "Feedstock Energy",
            "name": "Atomization energy",
            "value": 28.5,
            "unit": "MJ"
          },
          {
            "category": "Gas",
            "name": "Argon",
            "value": 0.5,
            "unit": "kg"
          }
        ],
        "outputs": [
          {
            "category": "Product",
            "name": "Ti-6Al-4V part",
            "value": 1.0,
            "unit": "kg"
          },
          {
            "category": "Recovered Material",
            "name": "Recovered powder",
            "value": 0.15,
            "unit": "kg"
          },
          {
            "category": "Waste",
            "name": "Support structures",
            "value": 0.05,
            "unit": "kg"
          }
        ]
      }
    }
  ]
}
```

#### 步骤2：生成文档

```bash
# 设置API Key
export DEEPSEEK_API_KEY="your_key"

# 生成单个文档（测试）
python scripts/reverse_engineer_documents.py \
  --input dataset/lci_literature/paper_001.json \
  --difficulty complex \
  --document-type research_case_study

# 批量生成（27个文档）
python scripts/batch_generate_all.py
```

**输出示例**：
```
dataset/documents/
├── test_simple_batch_production_record.md
├── test_simple_build_job_log.md
├── test_medium_technical_process_report.md
├── test_complex_research_case_study.md
└── ... (共27个文档)
```

#### 步骤3：转换PDF（可选）

```bash
# 单个文档
python scripts/md_to_pdf.py dataset/documents/test_complex_research_case_study.md

# 批量转换
for file in dataset/documents/*.md; do 
  python scripts/md_to_pdf.py "$file"
done
```

#### 步骤4：导入工作台标注

1. 启动工作台：`streamlit run scripts/expert_annotation_workbench.py`
2. 上传生成的PDF或粘贴Markdown内容
3. 按照正常流程标注（参考下文"工作台使用指南"）

---

## 训练数据导出

### 完整工作流

```
工作台标注 → 导出样本 → 生成推理 → 转换JSONL
```

### 步骤1：导出训练样本

```bash
cd scripts
python export_training_data.py
```

**输出格式**（JSON）：
```json
{
  "session_id": "paper_001_session_1",
  "messages": [
    {
      "role": "user",
      "content": "Please extract LCI data from the document."
    },
    {
      "role": "assistant",
      "tool_calls": [
        {
          "function": {
            "name": "search_document",
            "arguments": "{\"queries\": [\"product\", \"part\"]}"
          }
        }
      ]
    },
    {
      "role": "tool",
      "content": "Search results..."
    },
    {
      "role": "assistant",
      "tool_calls": [
        {
          "function": {
            "name": "record_process_flow",
            "arguments": "{...}"
          }
        }
      ]
    }
  ]
}
```

### 步骤2：生成推理内容

```bash
cd scripts
python generate_think_with_camel.py
```

**功能**：
- 使用CAMEL AI（DeepSeek）生成`<think>`推理内容
- 第一人称视角（"I need to...", "I should..."）
- 展示LLM的决策过程

**生成效果**：
```json
{
  "role": "assistant",
  "reasoning_content": "I'll start by searching for the product to establish the functional unit.",
  "tool_calls": [...]
}
```

### 步骤3：转换为JSONL

```bash
cd scripts
python convert_json_to_jsonl.py
```

**转换操作**：
1. 移除`metadata`字段
2. 只保留`messages`字段
3. 每行一个JSON对象（JSONL格式）

**最终训练数据**：
```jsonl
{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "reasoning_content": "...", "tool_calls": [...]}]}
{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "reasoning_content": "...", "tool_calls": [...]}]}
```

**用途**：
- 直接上传到OpenAI/Qwen/DeepSeek进行SFT训练
- 训练LLM学习：推理过程、工具调用、系统化流程

---

## Batch Search关键词

### 设计原则

- 覆盖不同表达方式（专业术语+通用词汇）
- 适应不同文献风格
- 支持批量搜索（一次返回所有相关chunk）
- **两层体系**：核心词（高频必选）+ 扩展词（低频随机）

### 关键词体系架构

#### **核心词库（Core Keywords）**
- **作用**：高频基础词汇，每次搜索**必须包含**
- **数量**：每个类别 3-5 个
- **目的**：保证LLM学会核心概念的搜索策略

#### **扩展词库（Extended Keywords）**
- **作用**：专业/长尾词汇，随机抽样使用
- **数量**：每个类别 5-10 个
- **目的**：增强泛化能力，覆盖不同工艺和场景

#### **使用策略**
```python
# 每次搜索：核心词（全部）+ 扩展词（随机1-2个）
# 总数控制：5-8 个关键词
# 示例：
queries = ["electricity", "kWh", "SEC"]  # 核心词（必选）
         + random.sample(["laser power", "machine power"], k=1)  # 扩展词（随机）
```

---

### SLM工艺关键词表（Phase 1）

**适用场景**：Selective Laser Melting / Powder Bed Fusion

```python
# ============================================
# Phase 1: Product (Anchor)
# ============================================

PRODUCT_CORE = [
    "product", "part", "component"
]

PRODUCT_EXTENDED = [
    "output", "yield", "manufactured", "fabricated", "specimen"
]

# ============================================
# Phase 2: Input Flows
# ============================================

# --- Raw Material ---
RAW_MATERIAL_CORE = [
    "powder", "material", "feedstock"
]

RAW_MATERIAL_EXTENDED = [
    # SLM特定金属
    "Ti6Al4V", "Ti-6Al-4V", "AlSi10Mg", "316L", 
    "stainless steel", "aluminum alloy",
    # 颗粒特性
    "particle size", "virgin powder"
]

# --- Process Energy ---
PROCESS_ENERGY_CORE = [
    "electricity", "kWh", "energy consumption"
]

PROCESS_ENERGY_EXTENDED = [
    "power consumption", "MJ", "SEC", "specific energy consumption",
    "machine power", "printing energy", "build energy",
    "laser power", "heater power", "bed power"
]

# --- Post-processing Energy ---
POST_PROCESSING_ENERGY_CORE = [
    "heat treatment", "machining", "post-processing"
]

POST_PROCESSING_ENERGY_EXTENDED = [
    # 热处理（SLM常见）
    "annealing", "stress relief", "furnace",
    "solution treatment", "aging",
    # 机加工
    "CNC", "milling", "grinding", "cutting", "drilling",
    # 表面处理
    "surface finishing", "polishing", "blasting",
    # 高端工艺（Phase 2/3）
    "HIP", "hot isostatic pressing", "wire EDM", "EDM"
]

# --- Feedstock Energy ---
FEEDSTOCK_ENERGY_CORE = [
    "atomization", "powder production"
]

FEEDSTOCK_ENERGY_EXTENDED = [
    "atomization energy", "powder manufacturing",
    "feedstock production", "feedstock energy",
    "gas atomization", "water atomization", "plasma atomization"
]

# --- Gas ---
GAS_CORE = [
    "argon", "nitrogen", "gas"
]

GAS_EXTENDED = [
    "inert gas", "shielding gas", "Ar", "N2",
    "gas consumption", "gas flow rate",
    "purge gas", "protective atmosphere",
    "compressed air"  # Phase 2/3: SLS工艺
]

# --- Cooling Media ---
COOLING_MEDIA_CORE = [
    "water", "coolant"
]

COOLING_MEDIA_EXTENDED = [
    "cooling water", "cutting fluid", "cooling liquid",
    "lubricant", "machining fluid", "coolant flow"
]

# ============================================
# Phase 3: Output Flows
# ============================================

# --- Recovered Material ---
RECOVERED_MATERIAL_CORE = [
    "recovered powder", "recycled powder"
]

RECOVERED_MATERIAL_EXTENDED = [
    "sieved powder", "reused powder",
    "unmelted powder", "loose powder",
    "surplus powder", "excess powder"
]

# --- Waste ---
WASTE_CORE = [
    "waste", "scrap", "support"
]

WASTE_EXTENDED = [
    "support structure", "failed print", "rejected part",
    "machining waste", "trimmings", "offcuts",
    "powder waste", "contaminated powder",
    "condensate", "filter"  # Phase 2/3: 金属打印特有
]

# --- Emission ---
EMISSION_CORE = [
    "emission", "particulate"
]

EMISSION_EXTENDED = [
    "VOC", "volatile organic compound",
    "particle", "fume", "smoke",
    "wastewater", "effluent", "off-gas",
    "air emission", "dust"
]
```

---

### 未来工艺扩展（Phase 2/3）

**仅作记录，阶段1不使用**

```python
# FDM工艺特定
RAW_MATERIAL_EXTENDED += ["filament", "PLA", "ABS", "nylon", "PEEK"]

# SLA工艺特定
RAW_MATERIAL_EXTENDED += ["resin", "photopolymer"]
POST_PROCESSING_ENERGY_EXTENDED += ["curing", "UV curing", "post-curing"]

# Binder Jetting工艺特定
RAW_MATERIAL_EXTENDED += ["binder"]
POST_PROCESSING_ENERGY_EXTENDED += ["sintering", "debinding"]

# WAAM/DED工艺特定
RAW_MATERIAL_EXTENDED += ["wire"]
```

---

### 使用策略

#### **策略1：核心+扩展抽样（推荐）**

```python
import random

# 示例：搜索 Process Energy
core = PROCESS_ENERGY_CORE  # ["electricity", "kWh", "energy consumption"]
extended = PROCESS_ENERGY_EXTENDED  # 8个扩展词

# 自动生成查询（5-8个关键词）
queries = core + random.sample(extended, k=random.randint(1, 2))

# 结果示例：
# ["electricity", "kWh", "energy consumption", "laser power", "SEC"]
```

**优点**：
- ✅ 核心词保证学习基础概念
- ✅ 随机扩展词增加多样性
- ✅ 避免"咒语化"过拟合

#### **策略2：手动调整**

工作台支持**人工编辑**关键词：
- 可以删除自动建议的某些词
- 可以添加临时词汇（如文献特有术语）
- 可以调整顺序

#### **策略3：批量搜索**

```python
# 一次搜索多个类别（提高效率）
queries = PRODUCT_CORE + RAW_MATERIAL_CORE + PROCESS_ENERGY_CORE
# 返回所有相关chunk，避免重复搜索
```

#### **策略4：Extract Fully**

```
找到一个表格后 → 提取所有相关数据
避免重复搜索 → 检查Session Summary确认
```

---

## 工作台使用指南

### 启动工作台

```bash
streamlit run scripts/expert_annotation_workbench.py
```

### 界面布局

```
┌─────────────────────────────────────────┐
│ 📄 Document Upload                       │
│ - 上传PDF或粘贴文本                      │
│ - 自动分块处理                           │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ 🤖 LLM Assistant (Optional)              │
│ - 辅助快速提取                           │
│ - 支持批量搜索                           │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ ✍️ Manual Annotation                     │
│ - Process Flow Recorder                  │
│ - Parameter Recorder                     │
│ - 10个LCI分类                            │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ 📊 Session Summary                       │
│ - 查看已记录数据                         │
│ - 检查完整性                             │
└─────────────────────────────────────────┘
```

### 标注流程

#### 1. Function Unit First（Phase 1）⭐ 新增

**策略核心**：通过Product反推Function Unit（同一物理对象，分两次记录）

**操作流程**：
1. 💡 → "Function Unit" → Generate → Apply → ✅Batch → Search
2. 搜索关键词：`["manufactured", "part", "product", "kg", "fabricated", "printed"]`
3. 查看搜索结果，按优先级选择：
   - **优先选择**：明确的生产描述语句
     * "We manufactured 10 parts..."
     * "Results are reported per kg..."
   - **备选方案**：如果找不到生产描述，使用Product相关内容
4. 记录功能单位定义（文本描述）

**位置**：文档开头（Introduction/Methods）章节
**类型**：文本描述（非表格）

**⚠️ 重要提示**：
- Phase 1只记录**文本描述**（定义层）
- Phase 2会再次记录**数值+单位**（计算层）- 作为Product输出流
- 这是同一物理对象的两种不同记录方式，服务于不同目的

**真实文献示例**：

**场景A：典型AM文献（生产描述）**
```
找到文本："We manufactured 10 Ti-6Al-4V parts using SLM. 
           Each part weighed approximately 250 g."

记录：
- Function Unit: "1 Ti-6Al-4V part (250 g)"
或推断为: "1 kg of Ti-6Al-4V part"
```

**场景B：材料测试文献**
```
找到文本："A total of 15 tensile specimens were fabricated according to ASTM E8. 
           Each specimen weighed 50 g."

记录：
- Function Unit: "1 tensile specimen (50 g)"
或推断为: "1 kg of specimen"
```

**场景C：批量生产**
```
找到文本："Five batches of components were printed with optimized parameters. 
           Each batch contained 20 parts."

记录：
- Function Unit: "1 batch (20 parts)"
或: "1 part"
```

**场景D：应用案例**
```
找到文本："A complex bracket was built for the aerospace application. 
           The final component mass was 1.2 kg."

记录：
- Function Unit: "1 bracket (1.2 kg)"
或推断为: "1 kg of bracket"
```

**注意**：
- Function Unit是文本描述，不是数值
- 如果文献未明确定义，可从Product输出或归一化基准推断
- 这是所有LCI数据归一化的基准

---

#### 2. Product Output（Phase 2）

**操作**：
1. 💡 → "Product" → Generate → Apply → ✅Batch → Search
2. 搜索关键词：`["product", "part", "component", "output", ...]`
3. 找到产品输出量（通常在Materials/Results章节，可能在表格或文本中）
4. 记录为Output Flow → Product

**位置**：文档后面（Materials/Results章节）
**类型**：表格或文本

**示例**：
```
找到："Ti-6Al-4V part, 2.5 kg"

记录：
- Flow Type: Output
- Category: Product
- Name: Ti-6Al-4V part
- Quantity: 2.5
- Unit: kg
```

---

#### 3. Input Flows（Phase 3）

**标注顺序**：
1. Raw Material
2. Process Energy
3. Post-processing Energy
4. Feedstock Energy
5. Gas
6. Cooling Media

**Energy分类技巧**：

| 数据示例 | 分类 | 理由 |
|---------|------|------|
| "SLM laser power: 200W" | Process Energy | 机器运行 |
| "Heat treatment: 850°C, 2h" | Post-processing Energy | 后处理 |
| "Atomization: 23.76 MJ/kg" | Feedstock Energy | 粉末制备 |

---

#### 4. Output Flows（Phase 4）

**标注顺序**：
1. Recovered Material
2. Waste
3. Emission

**Recovered Material vs Waste**：
- Recovered Material：可直接重用（如sieved powder）
- Waste：无法再利用（如contaminated powder）

---

#### 5. Validation（Phase 5）

**完整性检查**：
- [ ] Function Unit已定义 ✅
- [ ] Product已记录 ✅
- [ ] 至少有Raw Material ✅
- [ ] 至少有Process Energy或Post-processing Energy ✅
- [ ] 至少有Waste或Emission ✅

**归一化检查**：
- 所有数据单位是否一致？
- 是否归一化到功能单位？
- 计算场景是否正确？

---

### 标注技巧

#### 技巧1：Extract Fully原则

```
找到一个表格 → 一次性提取所有相关数据
避免重复搜索同一个chunk
在Session Summary中确认已提取
```

#### 技巧2：处理计算场景

**场景**：能耗需要计算（如"Power × Time"）

**操作**：
1. 使用Parameter Recorder记录参数：
   - Power: 3 kW
   - Time: 2 h
2. 工作台自动生成calculation动作
3. 最终记录为Process Flow：6 kWh

#### 技巧3：处理归一化数据

**场景**：文献已提供归一化数据

**示例**：
```
"Energy consumption: 120 MJ/kg"
```

**操作**：
- 直接记录为Process Energy
- 在Validation阶段确认与功能单位一致

#### 技巧4：处理分散数据

**场景**：能耗数据分散在不同章节

**策略**：
- Process Energy在"Manufacturing"章节 → 搜索"machine power"
- Post-processing Energy在"Post-processing"章节 → 搜索"heat treatment"
- 分别提取，分类清晰

---

## 常见问题

### Q1: 为什么Energy要拆分为3个子类？

**A**: 复杂场景中，能耗数据分散在不同章节：
- Process Energy：通常在"Manufacturing"章节
- Post-processing Energy：独立的"Post-processing"章节
- Feedstock Energy：在"Materials"或"Powder Production"章节

单一"Energy"关键词无法有效覆盖所有场景。

---

### Q2: Feedstock Energy vs Embodied Energy？

**A**: 
- **Feedstock Energy**：粉末/丝材制备能耗（如atomization），属于工艺系统边界内
- **Embodied Energy**：金属从矿石到铸锭的能耗，属于上游背景数据（不包括）

---

### Q3: 如何判断数据是否已归一化？

**A**: 
1. 检查Product的输出量（如2.5 kg）
2. 检查Input数据的单位
3. 如果Input已经是"per kg"单位，则已归一化
4. 如果Input是绝对值，需要除以Product输出量

**示例**：
```
Product: 2.5 kg
Raw Material: 3 kg (绝对值)
→ 归一化: 3/2.5 = 1.2 kg per kg
```

---

### Q4: 如何选择Batch Search关键词？

**A**: 
- 包含专业术语（如"SEC", "atomization"）
- 包含通用词汇（如"energy", "powder"）
- 考虑不同表达方式（如"Ti6Al4V" vs "Ti-6Al-4V"）
- 参考本文档第6章的关键词表

---

### Q5: 文档生成器的质量如何保证？

**A**: 
- ✅ 生成后需人工审核
- ✅ 检查LCI数据一致性
- ✅ 验证计算场景正确性
- ✅ 确认无LCA术语泄露
- ✅ 检查表格前后有空行（PDF转换需要）

---

## 快速参考

### 关键脚本

| 脚本 | 功能 | 位置 |
|-----|------|------|
| `expert_annotation_workbench.py` | 工作台主程序 | `scripts/` |
| `reverse_engineer_documents.py` | 文档生成器 | `scripts/` |
| `batch_generate_all.py` | 批量生成文档 | `scripts/` |
| `export_training_data.py` | 导出训练样本 | `scripts/` |
| `generate_think_with_camel.py` | 生成推理内容 | `scripts/` |
| `convert_json_to_jsonl.py` | 转换JSONL | `scripts/` |
| `md_to_pdf.py` | Markdown转PDF | `scripts/` |

### 文件结构

```
LCA-LLM/
├── dataset/
│   ├── lci_literature/          # 输入LCI数据（JSON）
│   ├── documents/               # 生成的文档（MD/PDF）
│   └── training_data/           # 导出的训练数据
├── scripts/                     # 所有Python脚本
├── docs/                        # 文档
│   ├── EcoLLM_Guide.md         # 本文档
│   └── PROMPT_DESIGN_GUIDE.md  # Prompt设计说明
└── workbench_data/             # 工作台数据库
```

---

## 数据扩展策略

### 第1阶段：真实文献
- 从5-10篇真实文献中人工标注
- 建立基础数据集（50-100个样本）
- 验证标注流程和质量

### 第2阶段：文档生成
- 每个LCI数据生成27个文档（3难度×9类型）
- 扩展到300-500个训练样本
- 覆盖多种难度和文档风格

### 第3阶段：持续迭代
- 继续真实文献标注
- 优化文档生成质量
- 目标：1000+高质量训练样本

---

## 关键词建议器使用

### 概述

**功能**：基于两层关键词体系，自动生成搜索关键词
**位置**：工作台Search部分，搜索框旁边的💡按钮
**版本**：1.0 (2025-11-22)

---

### 两层关键词体系

#### 核心词（Core Keywords）
- **特点**：高频基础词汇，每次**必须包含**
- **数量**：每个类别2-3个
- **示例**：`["electricity", "kWh", "energy consumption"]`

#### 扩展词（Extended Keywords）
- **特点**：专业/长尾词汇，**随机抽样**使用
- **数量**：每个类别5-17个
- **示例**：`["laser power", "SEC", "machine power", "bed power", ...]`

#### 生成策略
```
每次生成 = 核心词（全部）+ 扩展词（随机1-2个）
总数控制：5-8个关键词
```

**目的**：
- ✅ 核心词保证LLM学会基础概念
- ✅ 扩展词随机抽样避免"咒语化"过拟合
- ✅ 每次生成的关键词组合不完全相同（数据多样性）

---

### 使用流程（Parent Node搜索）

#### Step 1: 打开建议对话框
点击搜索框旁边的**💡按钮**

#### Step 2: 选择LCI类别
从10个类别中选择（如"Process Energy"）

#### Step 3: 生成关键词
点击"**Generate**"按钮

**示例输出**：
```
Core (Required):
- electricity
- kWh  
- energy consumption

Extended (Sampled):
- laser power
- SEC

Full Keywords:
electricity, kWh, energy consumption, laser power, SEC
```

#### Step 4: 编辑（可选）
在文本框中编辑关键词：
- 删除不需要的词
- 添加文献特有术语
- 调整顺序

#### Step 5: 应用
点击"**Apply**"按钮 → 关键词自动填充到搜索框

#### Step 6: 执行搜索
1. ✅ **勾选"Batch"复选框**（必须！）
2. 点击"**Search**"按钮

---

### Parent Node vs Child Node 搜索策略

#### **Parent Node搜索（第一次broad search）**

**使用工具**：💡 关键词建议器

**目标**：找到相关的chunk/段落/表格

**示例场景**：搜索Process Energy
```
生成关键词：["electricity", "kWh", "energy consumption", "laser power", "SEC"]
勾选Batch → Search
结果：返回5-10个相关chunk，包含各种能耗数据
```

**优势**：
- ✅ 一次搜索覆盖多个关键词
- ✅ 避免遗漏相关数据
- ✅ 关键词多样化（训练数据质量）

---

#### **Child Node搜索（后续细化搜索）**

**使用工具**：手动输入关键词

**目标**：在已找到的内容中，进一步精准定位

**示例场景1：细化能耗组成**
```
Parent搜索找到："Total energy: 150 kWh (laser: 100 kWh, heater: 30 kWh, other: 20 kWh)"
Child搜索：手动输入 "laser power" 或 "heater power"
目的：精准定位到laser或heater的具体数据
```

**示例场景2：同一chunk多次提取**
```
Parent搜索找到一个大表格，包含多个LCI类别的数据
Child搜索1：手动输入 "powder" → 提取Raw Material数据
Child搜索2：手动输入 "argon" → 提取Gas数据
Child搜索3：手动输入 "waste" → 提取Waste数据
```

**操作方式**：
1. **不点💡按钮**
2. 直接在搜索框输入具体关键词（如"laser power"）
3. **可以不勾选Batch**（单关键词搜索）
4. 点击"Search"

---

### 使用场景对比

| 场景 | 工具 | 关键词数量 | Batch模式 | 示例 |
|-----|------|----------|---------|------|
| **第一次搜索** | 💡建议器 | 5-8个 | ✅必须 | `["electricity", "kWh", "energy consumption", "laser power", "SEC"]` |
| **细化搜索** | 手动输入 | 1-2个 | ❌可选 | `"laser power"` 或 `"laser power, heater power"` |
| **Extract Fully** | 手动输入 | 1个 | ❌ | 找到表格后，用`"Table 3"`定位 |
| **跨类别搜索** | 💡建议器+手动编辑 | 8-12个 | ✅必须 | Product + Raw Material核心词 |

---

### 最佳实践

#### ✅ 推荐做法

**1. Parent Node搜索：用建议器**
```
每次搜索新的LCI类别时：
- 点击💡按钮
- 选择类别
- 生成关键词
- 勾选Batch
- 搜索
```

**2. Child Node搜索：手动输入**
```
找到相关内容后，需要细化时：
- 直接在搜索框输入具体关键词
- 可以不勾选Batch（单关键词即可）
- 搜索
```

**3. 保持多样性**
```
不要连续3个文档使用完全相同的关键词组合
每次用建议器重新生成（扩展词会随机变化）
```

**4. Extract Fully原则**
```
找到一个表格/段落后 → 一次性提取所有相关数据
避免重复搜索同一个chunk
在Session Summary中确认已提取
```

---

#### ❌ 避免做法

**1. 不用建议器，每次手动输入所有关键词**
```
❌ 效率低，且关键词组合固定（容易过拟合）
✅ 用建议器自动生成，节省时间且保证多样性
```

**2. Child Node搜索时仍用建议器生成大量关键词**
```
❌ 已经找到了相关chunk，不需要broad search
✅ 直接手动输入1-2个精准关键词
```

**3. 不勾选Batch就用建议器生成的关键词**
```
❌ 整个字符串会被当作单个查询（效果很差）
✅ 建议器生成的关键词必须勾选Batch
```

**4. 删除所有核心词，只保留扩展词**
```
❌ 核心词是保证LLM学习基础概念的关键
✅ 至少保留2个核心词
```

---

### 实际标注流程示例

#### 示例：标注一篇SLM文献

**Step 1: Function Unit (Definition)** ⭐ 新增
```
操作：💡 → 选择"Function Unit" → Generate → Apply → ✅Batch → Search
关键词：["manufactured", "part", "product", "kg", "fabricated", "printed"]
结果示例（优先选择生产描述）：
  ✅ 优先："We manufactured 10 Ti-6Al-4V parts using SLM..."
  ✅ 优先："Results are reported per kg of deposited material..."
  ⚠️ 备选：如果找不到，使用Product相关内容
动作：记录Function Unit文本描述（定义层）
注意：这是"定义"，数值稍后在Phase 2记录
```

**Step 2: Product Output (Quantitative)**
```
策略：使用Phase 1的搜索结果（避免重复搜索）
操作：从Phase 1找到的内容中提取数值
结果：找到 "10 parts" 或 "2.5 kg"
动作：记录为Output Flow → Product（数值+单位）
注意：这是"计算层"，与Function Unit是同一物理对象
示例：
  - Function Unit (Phase 1): "1 Ti-6Al-4V part (250 g)"
  - Product (Phase 2): Value=2.5, Unit=kg (总共10个parts)
```

**Step 3: Raw Material (Parent Node)**
```
操作：💡 → 选择"Raw Material" → Generate → Apply → ✅Batch → Search
关键词：["powder", "material", "feedstock", "Ti-6Al-4V", "particle size"]
结果：找到 "Ti-6Al-4V powder, 3.2 kg, particle size: 15-45 μm"
动作：记录为Input Flow → Raw Material
```

**Step 4: Process Energy (Parent Node)**
```
操作：💡 → 选择"Process Energy" → Generate → Apply → ✅Batch → Search
关键词：["electricity", "kWh", "energy consumption", "laser power", "SEC"]
结果：找到一个表格，包含多项能耗数据
```

**Step 5: Process Energy - Laser (Child Node)**
```
操作：手动输入 "laser power" → Search（不勾选Batch）
结果：精准定位到 "Laser power: 200 W, build time: 8 h"
动作：记录参数 → 自动计算 → 记录为Process Energy: 1.6 kWh
```

**Step 6: Process Energy - Heater (Child Node)**
```
操作：手动输入 "heater" → Search
结果：精准定位到 "Bed heater: 1.5 kW, build time: 8 h"
动作：记录参数 → 自动计算 → 记录为Process Energy: 12 kWh
```

**Step 7: Gas (Parent Node)**
```
操作：💡 → 选择"Gas" → Generate → Apply → ✅Batch → Search
关键词：["argon", "nitrogen", "gas", "inert gas", "Ar"]
结果：找到 "Argon consumption: 0.5 L/min, build time: 8 h"
动作：记录参数 → 自动计算 → 记录为Gas: 240 L
```

**Step 8: 继续其他类别...**

---

### 关键词统计（供参考）

#### Parent Node搜索（推荐使用建议器）

| LCI类别 | 核心词数 | 扩展词数 | 典型生成数 | 核心词示例 |
|---------|---------|---------|-----------|----------|
| Function Unit ⭐ | 4 | 6 | 6 | manufactured, part, product, kg |
| Product | 3 | 5 | 5 | product, part, component |
| Raw Material | 3 | 8 | 5 |
| Process Energy | 3 | 10 | 5-6 |
| Post-processing Energy | 3 | 17 | 5-6 |
| Feedstock Energy | 2 | 7 | 4-5 |
| Gas | 3 | 9 | 5 |
| Cooling Media | 2 | 6 | 4 |
| Recovered Material | 2 | 6 | 4 |
| Waste | 3 | 10 | 5 |
| Emission | 2 | 10 | 4-5 |

#### Child Node搜索（手动输入）

**常用精准关键词**（示例）：

**Process Energy细化**：
- `"laser power"`
- `"heater power"`
- `"bed power"`
- `"machine power"`

**Post-processing细化**：
- `"heat treatment"`
- `"machining"`
- `"CNC"`
- `"polishing"`

**Gas细化**：
- `"argon"`
- `"nitrogen"`
- `"build chamber"`
- `"flooding"`

---

### 常见问题

#### Q1: 什么时候用建议器，什么时候手动输入？

**A**: 
- **Parent Node（第一次broad search）**：用建议器
- **Child Node（后续细化搜索）**：手动输入

#### Q2: 建议器生成的关键词可以编辑吗？

**A**: ✅ 可以！点击"Apply"之前可以在文本框中编辑。

#### Q3: 每次生成的关键词为什么不一样？

**A**: 核心词固定，但扩展词是随机抽样的。这是为了：
- 避免训练数据中关键词组合完全相同
- 增加数据多样性
- 防止LLM过拟合到固定"咒语"

#### Q4: Child Node搜索时也要勾选Batch吗？

**A**: 
- 如果只搜索1个关键词（如"laser power"）：**不需要**勾选Batch
- 如果搜索2-3个关键词（如"laser power, heater power"）：**可以**勾选Batch

#### Q5: 可以跨类别搜索吗（如同时搜索Product + Raw Material）？

**A**: 可以！方法：
1. 用建议器生成Product关键词
2. 点击"Apply"
3. 在搜索框中手动添加Raw Material关键词（用逗号分隔）
4. 勾选Batch → Search

---

### 快速参考卡

```
┌─────────────────────────────────────────────────────────┐
│ 🎯 关键词建议器速查                                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Parent Node搜索（第一次broad search）                    │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│ 1. 点击💡按钮                                            │
│ 2. 选择LCI类别                                           │
│ 3. 点击"Generate"                                        │
│ 4. （可选）编辑关键词                                     │
│ 5. 点击"Apply"                                           │
│ 6. ✅ 勾选"Batch"                                        │
│ 7. 点击"Search"                                          │
│                                                          │
│ Child Node搜索（后续细化搜索）                           │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│ 1. 直接在搜索框输入精准关键词                            │
│ 2. 点击"Search"（可以不勾选Batch）                       │
│                                                          │
│ 记住：                                                   │
│ - Parent用建议器 → 5-8个关键词 → 必须Batch               │
│ - Child用手动 → 1-2个关键词 → 可选Batch                 │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

**最后更新**: 2025-11-22  
**维护者**: LCA-LLM Team  
**相关文档**: 
- `PROMPT_DESIGN_GUIDE.md`（文档生成器Prompt设计详解）
- `KEYWORD_QUICK_REFERENCE.md`（关键词建议器快速参考）
