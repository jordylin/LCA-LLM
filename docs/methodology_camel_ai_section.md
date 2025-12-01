# 2.2.3 Data Cleaning and Reasoning Data Generation

## 中文草稿

### 2.2.3 数据清洗与推理数据生成

训练数据构建的最后阶段面临两个挑战：标注质量不一致和推理内容缺失。我们引入 CAMEL AI 框架解决这两个问题。CAMEL AI 是一个支持多智能体协作的角色扮演框架，其核心组件 ChatAgent 提供了系统提示词封装和对话记忆功能，使我们能够通过精心设计的提示词引导 LLM 执行特定任务，并在多轮交互中保持上下文连贯。

**数据清洗：LCI 流名称与注释的规范化**

专家标注的 LCI 数据普遍存在格式不一致问题：大小写混乱、拼写变体、缩写不统一等。这些差异不仅影响模型学习——同一物质的不同表述被视为不同 token 序列——更会影响后续与 ecoinvent 等背景数据库的自动匹配。

我们基于 LCI 数据库的检索逻辑设计了两字段规范化方案。数据库检索通常先按物质身份（identity）搜索，再按特征属性（characteristics）过滤，因此我们将标注拆分为 Name 和 Note 两个字段。Name 字段承载物质身份，规范化为标准工业术语，避免缩写和口语化表达，如将 "Ti6Al4V powder" 转换为 "titanium alloy powder, Ti-6Al-4V"；Note 字段承载特征属性，采用结构化键值对格式便于过滤，如 "gas atomized | particle size: 15-45 μm | purity: 99.9%"。

实现上，我们为 ChatAgent 设计了专门的系统提示词，该提示词编码了 LCI 数据库的搜索逻辑和命名规范。对每条待处理记录，我们构建包含原始 name、note、category 和 value 的上下文提示词，调用 DeepSeek-V3 生成规范化结果。为确保输出可解析，我们要求模型以 JSON 格式返回，并实现了自动解析与回退机制：若 JSON 解析失败，则保留原始值以保证流水线稳定性。

**推理数据生成：动态提示词与记忆模块**

构建 SFT 数据集的推理内容（`<think>` 标签）面临一个根本性权衡：完全自由的自然语言表达使模型难以从多样化措辞中提取共同的决策模式，导致欠拟合；固定的句子模板则使模型学习表面的 token 关联而非深层语义逻辑，限制分布外泛化能力。我们的方案是动态提示词构建结合记忆模块。

动态提示词根据当前上下文构建，包含四个核心组件。（1）对话历史：遍历当前工具调用之前的所有消息，提取并格式化已执行的动作及对应的工具响应，使生成的推理能够引用之前的操作，如 "Based on my previous search for material inputs..."。（2）当前动作：描述即将执行的工具及其参数，为推理提供明确目标。（3）文档证据：在 search_document 调用后提取返回的文档片段，使推理能够引用具体的文本证据支撑决策。（4）工具特定引导：根据不同工具的语义提供差异化的决策指导——record_process_flow 强调数据准确性和来源追溯，get_session_summary 强调完整性检查的时机选择，define_lca_scope 强调功能单位作为 LCA 分析锚点的重要性。

记忆模块是保证推理连贯性的关键。我们利用 ChatAgent 内置的对话记忆功能，采用"样本间独立、样本内连续"的策略：处理每个新样本时首先清空记忆确保样本间独立性，而在处理该样本内的多个工具调用时保持记忆连续性。这使生成的推理内容能够形成逻辑链条，如 "Now that I have recorded the material inputs, I should search for energy consumption data to complete the inventory."

**场景感知的内容生成**

训练数据包含两种场景：Extract（提取记录数据）和 QA（询问信息）。场景区分对模型训练至关重要——若不加区分，模型在推理时无法判断应直接回答问题还是先记录数据再回答。我们为两种场景生成差异化的用户请求和最终响应。

用户请求生成首先扫描对话中所有 record_process_flow 调用，提取已记录的 LCI 流名称作为上下文。然后构建场景感知的提示词引导生成：Extract 场景使用动作导向表达，如 "Could you help me extract the titanium alloy data from this document?"；QA 场景使用信息寻求表达，如 "Can you tell me about the argon consumption in this process?"。提示词设计遵循"意图引导而非形式约束"原则——我们只指定用户意图（提取数据 vs 询问信息），让模型自由选择具体措辞，避免过度约束导致的表达单一化。

最终响应同样采用场景感知策略：Extract 场景确认数据已记录，QA 场景直接提供信息而不提及记录过程。此外，QA 场景在输出阶段执行格式转换：移除所有 record_process_flow、define_lca_scope、execute_calculation 和 record_parameter 工具调用及其对应响应，仅保留 search_document 调用，确保训练数据呈现纯粹的问答模式。

上述步骤整合为端到端的自动化流水线，接收工作台导出的原始标注数据，依次执行规范化、推理生成、内容生成，输出可直接用于 SFT 训练的完整数据集，支持批量处理大规模标注数据。

---

## English Version (For Manuscript)

### 2.2.3 Data Cleaning and Reasoning Data Generation

The final stage of training data construction addresses two challenges: annotation quality inconsistency and missing reasoning content. We leverage CAMEL AI, a role-playing framework for multi-agent cooperation, to tackle both issues. Its core component, ChatAgent, provides system prompt encapsulation and conversation memory, enabling us to guide LLMs through carefully designed prompts while maintaining context coherence across multiple interactions.

**Data Cleaning: LCI Flow Name and Note Standardization**

Expert-annotated LCI data commonly exhibits formatting inconsistencies: mixed capitalization, spelling variations, and non-standard abbreviations. These differences impair model learning—different representations of the same substance are treated as distinct token sequences—and affect downstream matching with background databases like ecoinvent.

We design a two-field standardization scheme based on LCI database retrieval logic. Since databases typically search by material identity first, then filter by characteristics, we split annotations into Name and Note fields. The Name field carries material identity, standardized to industrial terminology while avoiding abbreviations and colloquial expressions (e.g., "Ti6Al4V powder" → "titanium alloy powder, Ti-6Al-4V"); the Note field carries characteristics in structured key-value format for filtering (e.g., "gas atomized | particle size: 15-45 μm | purity: 99.9%").

At the implementation level, we design specialized system prompts for ChatAgent that encode LCI database search logic and naming conventions. For each record, we construct context prompts containing the original name, note, category, and value, invoking DeepSeek-V3 to generate standardized results. To ensure parseability, we require JSON-formatted output and implement automatic parsing with fallback mechanisms: if JSON parsing fails, original values are preserved to maintain pipeline stability.

**Reasoning Data Generation: Dynamic Prompts with Memory Module**

Constructing reasoning content (`<think>` tags) for SFT datasets faces a fundamental trade-off: completely free-form natural language expressions make it difficult for models to extract common decision-making patterns from diverse phrasings, leading to underfitting; fixed sentence templates cause models to learn surface-level token associations rather than deep semantic logic, limiting out-of-distribution generalization. Our solution combines dynamic prompt construction with a memory module.

Dynamic prompts are constructed based on current context, containing four core components. (1) Conversation history: traverses all messages preceding the current tool call, extracting and formatting executed actions and corresponding tool responses, enabling generated reasoning to reference previous operations such as "Based on my previous search for material inputs...". (2) Current action: describes the tool to be executed and its parameters, providing a clear target for reasoning. (3) Document evidence: extracts returned document chunks after search_document calls, enabling reasoning to reference specific textual evidence supporting decisions. (4) Tool-specific guidance: provides differentiated decision guidance based on different tool semantics—record_process_flow emphasizes data accuracy and provenance tracking, get_session_summary emphasizes timing of completeness checks, define_lca_scope emphasizes the importance of functional unit as the anchor for LCA analysis.

The memory module is key to ensuring reasoning coherence. We leverage ChatAgent's built-in conversation memory with an "inter-sample independence, intra-sample continuity" strategy: clearing memory before each new sample ensures independence between samples, while maintaining memory continuity when processing multiple tool calls within that sample. This enables generated reasoning to form logical chains, such as "Now that I have recorded the material inputs, I should search for energy consumption data to complete the inventory."

**Scenario-Aware Content Generation**

Training data encompasses two scenarios: Extract (data extraction and recording) and QA (information inquiry). Scenario differentiation is crucial for model training—without it, the model cannot determine during inference whether to directly answer questions or first record data before responding. We generate differentiated user requests and final responses for each scenario.

User request generation first scans all record_process_flow calls in the conversation, extracting recorded LCI flow names as context. Scenario-aware prompts then guide generation: Extract uses action-oriented expressions like "Could you help me extract the titanium alloy data from this document?"; QA uses information-seeking expressions like "Can you tell me about the argon consumption in this process?". Prompt design follows the principle of "intent guidance rather than form constraint"—we specify only user intent (data extraction vs. information inquiry), allowing the model to freely choose specific phrasings, avoiding expression homogenization from over-constraint.

Final responses similarly adopt scenario-aware strategies: Extract confirms data recording, while QA directly provides information without mentioning the recording process. Additionally, QA scenarios perform format conversion at output: removing all record_process_flow, define_lca_scope, execute_calculation, and record_parameter tool calls along with their corresponding responses, retaining only search_document calls, ensuring training data presents a pure question-answering pattern.

These steps are integrated into an end-to-end automated pipeline that receives raw annotation data exported from the workbench, sequentially executes standardization, reasoning generation, and content generation, outputting complete datasets ready for SFT training with support for batch processing of large-scale annotation data.
