
> 说明：  
> - 所有 `"TEMPLATE_..."` 和 `0.0` 位置请替换为真实数值和文本。  
> - `relations` 是可选的；若暂时不需要参数化关系，可以先省略整个数组。

---

## 二、简短使用说明（怎么填，怎么帮助文档生成）

### 1. 顶层 `papers` 列表

- **`title` / `authors` / `year` / `doi` / `journal`**
  - 主要是方便你自己管理数据和溯源，目前生成器只用到 `lci_data`，但这些字段对后续评估和扩展很有用。
- **`notes`**
  - 可写系统边界、是否包含某些阶段等，便于你以后回顾。

### 2. `lci_data` 核心字段

这些字段是当前文档生成器真正会用到的：

- **`process_name`**
  - 用作文档主线的工艺名称（文中标题、引言会频繁提到）。
- **`functional_unit`**
  - 描述“1 个什么”的功能单位，有助于 DeepSeek 在文中保持量纲一致。
- **`description`**
  - 一两句话的自然语言场景说明：工艺背景、设备类型、边界（如是否含后处理）。
  - 有助于模型生成更贴近具体场景的引言和方法部分。

### 3. `inputs` / `outputs`

- 每一项代表一个流（物料、能耗、气体、冷却介质、产物、废弃物等）。
- **推荐字段**：
  - `id`：短 ID，方便在 `relations` 里引用。
  - `category`：语义类别（Raw Material / Energy / Gas / Cooling Media / Product / Waste …）。  
    - 主要是帮助 prompt 理解语义，不一定会逐字映射到文中。
  - `name`：尽量接近论文原文的流名称。
  - `value` / `unit`：数值与单位。
  - `location`：可选，用于以后做 Ecoinvent 匹配。
  - `note`：注明来源（“Table 3”, “Fig. 2”, “Section 3.4”）或特殊说明。

这些结构让生成器在不同文档类型/难度下，有足够信息将数据“合理地嵌入”到叙述和表格中。

### 4. `parameters`

- 用于记录“底层参数”，例如：
  - 时间、功率、速率、强度值（kWh/kg）、温度、压力等。
- 对 `complex` 难度特别重要：
  - 生成器可以用这些参数来写“过程参数”、“实验条件”、“测量结果”，并**隐式支撑**能耗/物料的计算，而不是只给一个现成总量。

### 5. `relations`（可选，但推荐用于复杂样本）

- 用来显式告诉生成器：某个 flow 是由哪些参数计算出来的。
- 字段含义：
  - `flow`：用 `category: name` 形式指向某个 input/output，比如 `"Process Energy: Electricity for SLM build"`。
  - `relation_type`：通常填 `"calculation"`。
  - `calculation`：自然语言或简单表达式（给给人/模型一个大致关系）。
  - `parameters_used`：引用 `parameters` 里的 `id` 列表。
  - `note`：可放原文中对该计算关系的描述。

---
