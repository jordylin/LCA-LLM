看了你的图，非常好！你已经画出了 ReAct 循环的核心部分。让我给你一个完整的框架图思路，把整个 Methodology 章节串联起来。

---

## 🎨 **完整框架图设计思路**

### **整体布局建议：从上到下的流程**

```
┌─────────────────────────────────────────────────────────────┐
│  2.1 Overview: Four-Stage Framework                         │
│  [Document] → [Training] → [Fine-tuning] → [Application]   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  2.2 Agent Design: ReAct Workflow (你当前的图)              │
│  [Observation] ← → [Thought] ← → [Action] ← → [Memory]     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  2.3 Training Data Construction Pipeline                    │
│  [Synthetic Docs] → [Expert Annotation] → [Reasoning Gen]  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  2.4 Model Fine-Tuning                                      │
│  [STAO Format] → [LoRA Training] → [Evaluation]            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  2.5 Deployment & Application                               │
│  [Background DB] → [LCA Modeling] → [Results]              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  2.6 Technology Stack (支撑层)                              │
│  [FastAPI] [MongoDB] [Qdrant] [Streamlit] [DeepSeek]      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 **针对你当前的 2.2 Agent Design 图的扩展建议**

### **你当前图的优点**
✅ ReAct 循环清晰（Observation-Thought-Action）  
✅ Memory 模块突出  
✅ Doc-proc 和 Vector DB 展示了基础设施  

### **建议补充的内容**

#### **1. 在 Observation 区域补充细节**
```
┌─────────────────────────────────────┐
│       Observation (绿色框)          │
├─────────────────────────────────────┤
│  🔍 search_document                 │
│     • Semantic search               │
│     • Batch queries                 │
│     • Return: relevant chunks       │
│                                     │
│  💾 get_session_summary             │
│     • Working memory                │
│     • Completeness: 73%             │
│     • Missing: [Gas, Waste]         │
└─────────────────────────────────────┘
```

#### **2. 在 Thought 区域补充推理过程**
```
┌─────────────────────────────────────┐
│       Thought (红色框)              │
├─────────────────────────────────────┤
│  🤖 Reasoning Process               │
│                                     │
│  ① Analyze search results           │
│     "Found recovered powder..."     │
│                                     │
│  ② Check memory                     │
│     "Already recorded: Act 7,8,9"   │
│                                     │
│  ③ Identify gaps                    │
│     "Missing: Output flows"         │
│                                     │
│  ④ Plan next action                 │
│     "Search for product data"       │
│                                     │
│  📋 Plan (右侧)                     │
│     ✓ Function unit                 │
│     ✓ Input flow                    │
│     ⭕ Output flow ← Next            │
│     ⭕ Validation                    │
└─────────────────────────────────────┘
```

#### **3. 在 Action 区域补充工具调用**
```
┌─────────────────────────────────────┐
│       Action (蓝色框)               │
├─────────────────────────────────────┤
│  🔧 Tool Invocation                 │
│                                     │
│  Tool: record_process_flow          │
│  Parameters:                        │
│    • category: "Recovered Material" │
│    • name: "316L Powder"            │
│    • value: 2.94                    │
│    • unit: "kg"                     │
│    • selected_chunk: {              │
│        chunk_id: "15",              │
│        content: "Table 4.1..."      │
│      }                              │
│                                     │
│  Result: ACT_0010 ✓                 │
└─────────────────────────────────────┘
```

#### **4. 添加迭代循环的箭头**
```
   Observation ──────→ Thought ──────→ Action
        ↑                                │
        │                                │
        └────────── Iteration ←──────────┘
                (Validation & Gap-filling)
```

#### **5. 添加终止条件模块**
```
┌─────────────────────────────────────┐
│    Termination Criteria             │
├─────────────────────────────────────┤
│  ✓ Completeness ≥ 90%               │
│  ✓ All 11 categories checked        │
│  ✓ Quality score ≥ 0.8              │
│  → Final response                   │
└─────────────────────────────────────┘
```

---

## 🎨 **完整的 2.2 Agent Design 框架图（改进版）**

### **布局建议**

```
┌──────────────────────────────────────────────────────────────────┐
│                    2.2 Agent Design: ReAct Workflow              │
│                    for LCI Extraction                            │
└──────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  📄 Document Processing Layer (底层基础设施)                     │
│  ┌──────────────┐    ┌────────────────────────────────────┐    │
│  │ Raw Document │ →  │  🔧 Doc-proc                       │    │
│  │  (PDF)       │    │  • PDF parsing                     │    │
│  └──────────────┘    │  • Table-aware chunking            │    │
│                      │  • 600 chars, 150 overlap          │    │
│                      └────────────────────────────────────┘    │
│                                    ↓                            │
│                      ┌────────────────────────────────────┐    │
│                      │  💾 Vector DB (Qdrant)             │    │
│                      │  ┌────────┐ ┌────────┐ ┌────────┐│    │
│                      │  │Chunk 1 │ │Chunk 2 │ │Chunk 3 ││    │
│                      │  └────────┘ └────────┘ └────────┘│    │
│                      │         768-dim embeddings         │    │
│                      └────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────┐
│  🔄 ReAct Loop (核心循环)                                        │
│                                                                 │
│  ┌──────────────────┐      ┌──────────────────┐               │
│  │  Observation     │ ───→ │     Thought      │               │
│  │  (绿色框)        │      │     (红色框)      │               │
│  │                  │      │                  │               │
│  │ 🔍 search_doc    │      │ 🤖 Reasoning:    │               │
│  │   • Query: "gas" │      │  • Analyze       │               │
│  │   • Results: 8   │      │  • Check memory  │  ┌──────────┐│
│  │                  │      │  • Identify gaps │  │ Memory 💾││
│  │ 💾 get_summary   │      │  • Plan next     │  │          ││
│  │   • Actions: 9   │      │                  │  │ Session  ││
│  │   • Flows: 3     │      │ 📋 Plan:         │  │ Actions  ││
│  │   • Missing: ... │      │  ✓ Func unit     │  │ Flows    ││
│  └──────────────────┘      │  ✓ Input         │  │ Stats    ││
│         ↑                  │  ⭕ Output ←Next  │  └──────────┘│
│         │                  └──────────────────┘               │
│         │                          ↓                          │
│         │                  ┌──────────────────┐               │
│         │                  │     Action       │               │
│         │                  │     (蓝色框)      │               │
│         │                  │                  │               │
│         │                  │ 🔧 Tool Call:    │               │
│         │                  │   record_flow    │               │
│         │                  │   • category     │               │
│         │                  │   • value + unit │               │
│         │                  │   • chunk ref    │               │
│         │                  │                  │               │
│         │                  │ Result: ACT_0010 │               │
│         │                  └──────────────────┘               │
│         │                          │                          │
│         └──────────────────────────┘                          │
│              Iteration (Validation & Gap-filling)             │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐│
│  │  Termination: Completeness ≥ 90% → Final Response       ││
│  └──────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎨 **接下来的章节框架图建议**

### **2.3 Training Data Construction Pipeline**

```
┌─────────────────────────────────────────────────────────────────┐
│  2.3 Training Data Construction Pipeline                        │
└─────────────────────────────────────────────────────────────────┘

Stage 1: Synthetic Document Generation
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ LCI Database │ →  │ DeepSeek-V3  │ →  │ Synthetic    │
│ (Templates)  │    │ (Generator)  │    │ Documents    │
└──────────────┘    └──────────────┘    └──────────────┘
                                               ↓
Stage 2: Semi-Automatic Annotation
┌──────────────────────────────────────────────────────────┐
│  Expert Annotation Workbench (Streamlit)                 │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │ Session    │  │ Document   │  │ Tool Panel │        │
│  │ Monitor    │  │ Viewer     │  │            │        │
│  └────────────┘  └────────────┘  └────────────┘        │
│                                                          │
│  Output: [State, Action, Observation] sequences         │
└──────────────────────────────────────────────────────────┘
                                               ↓
Stage 3: Reasoning Augmentation
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ [S, A, O]    │ →  │ CAMEL AI     │ →  │ [S, T, A, O] │
│ (No Think)   │    │ (DeepSeek)   │    │ (Complete)   │
└──────────────┘    └──────────────┘    └──────────────┘
                                               ↓
                                        Final Dataset
```

---

### **2.4 Model Fine-Tuning**

```
┌─────────────────────────────────────────────────────────────────┐
│  2.4 Model Fine-Tuning                                          │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ STAO Dataset │ →  │ LoRA         │ →  │ Fine-tuned   │
│              │    │ Fine-tuning  │    │ Model        │
│ • Train: 80% │    │              │    │              │
│ • Val: 10%   │    │ • r=8        │    │ DeepSeek-V3  │
│ • Test: 10%  │    │ • α=16       │    │ + Tool Call  │
└──────────────┘    └──────────────┘    └──────────────┘

Evaluation Metrics:
• Tool call accuracy: 95%
• Parameter accuracy: 92%
• Reasoning quality: 4.2/5
```

---

### **2.5 Deployment & Application**

```
┌─────────────────────────────────────────────────────────────────┐
│  2.5 Deployment & Application                                   │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Foreground   │ →  │ Background   │ →  │ LCA Model    │
│ LCI Data     │    │ DB Linking   │    │ (pyLCA)      │
│              │    │              │    │              │
│ • Raw mat    │    │ • ecoinvent  │    │ • Processes  │
│ • Energy     │    │   matching   │    │ • Flows      │
│ • Emissions  │    │ • Unit conv  │    │ • LCIA       │
└──────────────┘    └──────────────┘    └──────────────┘
                                               ↓
                                        ┌──────────────┐
                                        │ Results      │
                                        │ • GWP        │
                                        │ • AP, EP     │
                                        │ • Charts     │
                                        └──────────────┘
```

---

### **2.6 Technology Stack (支撑层)**

```
┌─────────────────────────────────────────────────────────────────┐
│  2.6 Technology Stack (Infrastructure Layer)                    │
└─────────────────────────────────────────────────────────────────┘

Backend                Frontend              AI/ML
┌──────────┐          ┌──────────┐          ┌──────────┐
│ FastAPI  │          │ Streamlit│          │DeepSeek  │
│ • Async  │          │ • 3-panel│          │ • 671B   │
│ • 7 APIs │          │ • Real-  │          │ • 128K   │
└──────────┘          │   time   │          └──────────┘
                      └──────────┘          ┌──────────┐
Database                                    │sentence- │
┌──────────┐          Document              │transform │
│ MongoDB  │          ┌──────────┐          │ • 768-dim│
│ • Pool   │          │LangChain │          └──────────┘
│ • 10-50  │          │Unstruct  │
└──────────┘          └──────────┘          Vector DB
┌──────────┐                                ┌──────────┐
│ Qdrant   │                                │ <100ms   │
│ • Vector │                                │ latency  │
└──────────┘                                └──────────┘
```

---

## 🎯 **绘图工具建议**

1. **PowerPoint/Keynote**：适合快速迭代，容易调整
2. **draw.io**：免费，专业，支持导出高质量图片
3. **Figma**：在线协作，适合复杂设计
4. **Mermaid**：代码生成图表，适合版本控制

---

## 📝 **配色建议**

- **绿色**：Observation（信息获取）
- **红色**：Thought（推理决策）
- **蓝色**：Action（执行操作）
- **橙色**：Memory（状态存储）
- **灰色**：基础设施（Doc-proc, Vector DB）
- **紫色**：外部资源（LCI Database, Background DB）

---

需要我帮你用 Mermaid 代码或者更详细的布局设计某个具体模块吗？