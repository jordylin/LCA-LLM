# 仓库清理与多模型对比测试计划

## 目的

这份文档用于统一回答三个问题：

1. 当前仓库中哪些文件/目录应该保留，哪些可以清理或归档。
2. 整理完成后，如何安全地提交代码并 push 到 GitHub 备份。
3. 后续如果要加入别的基础小模型做对比测试，需要准备什么、按什么顺序做。

本文档基于当前仓库快照整理，不会直接触发删除操作。

---

## 一、当前仓库的基本判断

当前仓库不是一个“只有服务代码”的轻量仓库，而是混合了以下几类内容：

1. `LCA-LLM` 主框架代码
2. 前景数据提取工具链
3. 背景数据库匹配与 LCIA 计算扩展
4. 训练数据构建与导出脚本
5. 评测脚本与测试集
6. 一次性实验脚本、结果文件、缓存、日志、旧版文档

因此，清理时不能只看“前后端主服务”，还必须把“前景抽取 -> 背景匹配 -> LCIA 计算 -> 结果分析”这一整条链条纳入核心范围。

---

## 二、文件分层建议

下面按四类整理。

### A. 框架核心，绝不建议删除

这些文件构成了当前 LCA-LLM 的主要服务链路。

#### 后端主链

- [backend/app.py](/home/Research_work/24_yzlin/LCA-LLM/backend/app.py)
- [backend/services/tool_service.py](/home/Research_work/24_yzlin/LCA-LLM/backend/services/tool_service.py)
- [backend/services/llm_chat_service.py](/home/Research_work/24_yzlin/LCA-LLM/backend/services/llm_chat_service.py)
- [backend/services/qwen_agent_service_v2.py](/home/Research_work/24_yzlin/LCA-LLM/backend/services/qwen_agent_service_v2.py)
- [backend/services/qwen_agent_tools.py](/home/Research_work/24_yzlin/LCA-LLM/backend/services/qwen_agent_tools.py)
- [backend/services/session_manager.py](/home/Research_work/24_yzlin/LCA-LLM/backend/services/session_manager.py)
- [backend/services/pdf_processor.py](/home/Research_work/24_yzlin/LCA-LLM/backend/services/pdf_processor.py)
- [backend/services/table_aware_chunker.py](/home/Research_work/24_yzlin/LCA-LLM/backend/services/table_aware_chunker.py)
- [backend/services/vectorized_knowledge_base.py](/home/Research_work/24_yzlin/LCA-LLM/backend/services/vectorized_knowledge_base.py)
- [backend/services/mongodb_manager.py](/home/Research_work/24_yzlin/LCA-LLM/backend/services/mongodb_manager.py)
- [backend/services/knowledge_base.py](/home/Research_work/24_yzlin/LCA-LLM/backend/services/knowledge_base.py)
- [backend/services/vllm_service.py](/home/Research_work/24_yzlin/LCA-LLM/backend/services/vllm_service.py)
- [backend/services/local_qwen_service.py](/home/Research_work/24_yzlin/LCA-LLM/backend/services/local_qwen_service.py)
- [backend/api/unit_api.py](/home/Research_work/24_yzlin/LCA-LLM/backend/api/unit_api.py)
- [backend/utils/unit_processor.py](/home/Research_work/24_yzlin/LCA-LLM/backend/utils/unit_processor.py)

#### 前端主链

- [frontend/app.py](/home/Research_work/24_yzlin/LCA-LLM/frontend/app.py)
- [frontend/components/unit_selector.py](/home/Research_work/24_yzlin/LCA-LLM/frontend/components/unit_selector.py)

#### 运行与服务脚本

- [start_vllm.sh](/home/Research_work/24_yzlin/LCA-LLM/start_vllm.sh)
- [restart_services.sh](/home/Research_work/24_yzlin/LCA-LLM/restart_services.sh)
- [stop_services.sh](/home/Research_work/24_yzlin/LCA-LLM/stop_services.sh)
- [restart_workbench.sh](/home/Research_work/24_yzlin/LCA-LLM/restart_workbench.sh)
- [check_services.sh](/home/Research_work/24_yzlin/LCA-LLM/check_services.sh)

#### 资源与依赖说明

- [requirements.txt](/home/Research_work/24_yzlin/LCA-LLM/requirements.txt)
- `resources/`
- [README.md](/home/Research_work/24_yzlin/LCA-LLM/README.md)
- [docs/ARCHITECTURE_SUMMARY.md](/home/Research_work/24_yzlin/LCA-LLM/docs/ARCHITECTURE_SUMMARY.md)
- [docs/README.md](/home/Research_work/24_yzlin/LCA-LLM/docs/README.md)

---

### B. LCIA / 背景匹配扩展核心，建议保留

这是你特别强调的“前景数据与背景数据匹配，再做 LCIA 计算”的链路，属于框架的一部分，不应当误删。

#### 服务代码

- [backend/services/ecoinvent_matcher.py](/home/Research_work/24_yzlin/LCA-LLM/backend/services/ecoinvent_matcher.py)
- [backend/services/lcia_calculator.py](/home/Research_work/24_yzlin/LCA-LLM/backend/services/lcia_calculator.py)
- [backend/services/openlca_client.py](/home/Research_work/24_yzlin/LCA-LLM/backend/services/openlca_client.py)
- [backend/services/unit_compatibility.py](/home/Research_work/24_yzlin/LCA-LLM/backend/services/unit_compatibility.py)

#### 相关实验/核算/结果分析脚本

这些不一定是“在线服务主链”，但明显属于 LCIA 扩展路径的工作成果，建议至少先归档保留：

- [test_improved_workflow.py](/home/Research_work/24_yzlin/LCA-LLM/test_improved_workflow.py)
- [test_lcia_endpoint.py](/home/Research_work/24_yzlin/LCA-LLM/test_lcia_endpoint.py)
- [calculate_ipcc2021.py](/home/Research_work/24_yzlin/LCA-LLM/calculate_ipcc2021.py)
- [calculate_ipcc2021_gwp.py](/home/Research_work/24_yzlin/LCA-LLM/calculate_ipcc2021_gwp.py)
- [calculate_individual_flow_contributions.py](/home/Research_work/24_yzlin/LCA-LLM/calculate_individual_flow_contributions.py)
- [analyze_recipe_2016.py](/home/Research_work/24_yzlin/LCA-LLM/analyze_recipe_2016.py)
- [final_accurate_calculation.py](/home/Research_work/24_yzlin/LCA-LLM/final_accurate_calculation.py)
- [visualize_lcia_results_final.py](/home/Research_work/24_yzlin/LCA-LLM/visualize_lcia_results_final.py)
- [assess_ipc_capabilities.py](/home/Research_work/24_yzlin/LCA-LLM/assess_ipc_capabilities.py)
- [LCIA_CALCULATION_ANALYSIS.md](/home/Research_work/24_yzlin/LCA-LLM/LCIA_CALCULATION_ANALYSIS.md)
- `lcia_results/`

建议做法：

1. 不要立刻删
2. 若要精简主目录，可移动到 `archive/lcia_experiments/`
3. 只要论文、图表、分析还可能回查，就保留

---

### C. 训练、数据集、评测相关，建议保留

这些内容与“LoRA 微调效果是否好”直接相关，是后续多模型对比的基础资产。

#### 训练/导出脚本

- [scripts/prepare_finetune_data.py](/home/Research_work/24_yzlin/LCA-LLM/scripts/prepare_finetune_data.py)
- [scripts/export_training_data.py](/home/Research_work/24_yzlin/LCA-LLM/scripts/export_training_data.py)
- [scripts/export_short_qa_data.py](/home/Research_work/24_yzlin/LCA-LLM/scripts/export_short_qa_data.py)
- [scripts/validate_training_data.py](/home/Research_work/24_yzlin/LCA-LLM/scripts/validate_training_data.py)
- [scripts/reasoning_helpers.py](/home/Research_work/24_yzlin/LCA-LLM/scripts/reasoning_helpers.py)
- [scripts/reverse_engineer_documents.py](/home/Research_work/24_yzlin/LCA-LLM/scripts/reverse_engineer_documents.py)
- [scripts/train_config.yaml](/home/Research_work/24_yzlin/LCA-LLM/scripts/train_config.yaml)
- [scripts/train_config_a100.yaml](/home/Research_work/24_yzlin/LCA-LLM/scripts/train_config_a100.yaml)
- [scripts/train_config_cloud.yaml](/home/Research_work/24_yzlin/LCA-LLM/scripts/train_config_cloud.yaml)
- [scripts/train_config_cloud_v2.yaml](/home/Research_work/24_yzlin/LCA-LLM/scripts/train_config_cloud_v2.yaml)
- [merge_lora.py](/home/Research_work/24_yzlin/LCA-LLM/merge_lora.py)

#### 工作台

- [scripts/expert_workbench.sh](/home/Research_work/24_yzlin/LCA-LLM/scripts/expert_workbench.sh)
- [scripts/expert_annotation_workbench.py](/home/Research_work/24_yzlin/LCA-LLM/scripts/expert_annotation_workbench.py)
- [workbench.json](/home/Research_work/24_yzlin/LCA-LLM/workbench.json)

#### 评测与结果

- [run_baseline_evaluation.sh](/home/Research_work/24_yzlin/LCA-LLM/run_baseline_evaluation.sh)
- [run_evaluation_pipeline.sh](/home/Research_work/24_yzlin/LCA-LLM/run_evaluation_pipeline.sh)
- [scripts/extract_ground_truth.py](/home/Research_work/24_yzlin/LCA-LLM/scripts/extract_ground_truth.py)
- [scripts/calculate_metrics_final.py](/home/Research_work/24_yzlin/LCA-LLM/scripts/calculate_metrics_final.py)
- [scripts/run_full_evaluation.py](/home/Research_work/24_yzlin/LCA-LLM/scripts/run_full_evaluation.py)
- `test_data/`
- [BASELINE_TEST_GUIDE.md](/home/Research_work/24_yzlin/LCA-LLM/BASELINE_TEST_GUIDE.md)
- [EVALUATION_GUIDE.md](/home/Research_work/24_yzlin/LCA-LLM/EVALUATION_GUIDE.md)
- [BASELINE_COMPARISON_SUMMARY.md](/home/Research_work/24_yzlin/LCA-LLM/BASELINE_COMPARISON_SUMMARY.md)
- [docs/MODEL_COMPARISON_AUDIT.md](/home/Research_work/24_yzlin/LCA-LLM/docs/MODEL_COMPARISON_AUDIT.md)

说明：

当前评测链有历史残缺，特别是：

- `run_baseline_evaluation.sh` 引用了不存在的 `scripts/run_inference_agent_loop_final.py`
- 还引用了不存在的 `scripts/calculate_metrics_baseline.py`

所以这部分虽然要保留，但后续需要统一重构评测入口。

---

### D. 明显的缓存、日志、运行产物，建议清理

这些通常不应进 GitHub，也不应长期留在主工作树里。

#### 建议直接清理

- `context_files/`
- `logs/`
- `llamaboard_cache/`
- `backend/startup.log`
- `inference_log.txt`
- `chroma_db/`  如果不需要保留临时向量数据库
- `backend/__pycache__/`
- `scripts/__pycache__/`
- `.codex`
- `frontend/pages/`  如果确认为空且无计划使用
- `workspace/`  如果确认无实际用途

#### 建议加入或完善 `.gitignore`

当前 `.gitignore` 已覆盖：

- `lcaLLM/`
- `models/`
- `dataset/`
- `context_files/`
- `LLaMA-Factory/`
- `llamaboard_cache`
- `logs/`

建议继续确保以下内容不要进入 Git：

- `chroma_db/`
- `lcia_results/` 如果你决定不将实验图表纳入版本管理
- `*.xlsx` 中的大型导出物，除非确实需要
- `backend/startup.log`

---

### E. 旧版/重复/可疑文件，建议“先确认再动”

这类文件不要直接删，建议先做一次小范围核对。

#### 候选

- [oldREADME.md](/home/Research_work/24_yzlin/LCA-LLM/oldREADME.md)
- [backend/services/pdf_processor_backup.py](/home/Research_work/24_yzlin/LCA-LLM/backend/services/pdf_processor_backup.py)
- [backend/services/pdf_processor_enhanced.py](/home/Research_work/24_yzlin/LCA-LLM/backend/services/pdf_processor_enhanced.py)
- [backend/services/qwen_agent_service.py](/home/Research_work/24_yzlin/LCA-LLM/backend/services/qwen_agent_service.py)
- `docs/archive/`
- [VLLM_GUIDE.md](/home/Research_work/24_yzlin/LCA-LLM/VLLM_GUIDE.md)
- [QUICK_START_PDF.md](/home/Research_work/24_yzlin/LCA-LLM/QUICK_START_PDF.md)
- [frontend_api_check.md](/home/Research_work/24_yzlin/LCA-LLM/frontend_api_check.md)
- [git.md](/home/Research_work/24_yzlin/LCA-LLM/git.md)

#### 当前判断

- `pdf_processor_backup.py` 很像纯旧文件
- `pdf_processor_enhanced.py` 也很像旧分支实现，而且还依赖当前未找到的 `lci_extractor`
- `qwen_agent_service.py` 是旧版 agent 服务，但仍被 import，删除前要顺手清理 import
- `oldREADME.md` 大概率可删
- 其余文档更适合“归档”而不是粗暴删除

---

## 三、建议的整理顺序

建议按下面顺序做，不要一步到位大清扫。

### 第 1 步：只清缓存和运行产物

只动 D 类内容：

1. `context_files/`
2. `logs/`
3. `llamaboard_cache/`
4. `__pycache__/`
5. `.codex`
6. `backend/startup.log`
7. `inference_log.txt`
8. `chroma_db/`  如果不保留会话

### 第 2 步：把 LCIA 一次性分析脚本集中归档

将这些移到一个更清晰的位置，例如：

- `archive/lcia_experiments/`

而不是先删掉。

### 第 3 步：确认旧版实现是否仍被引用

重点检查：

1. `backend/services/pdf_processor_backup.py`
2. `backend/services/pdf_processor_enhanced.py`
3. `backend/services/qwen_agent_service.py`

确认无用后，再删。

### 第 4 步：最后再处理重复文档

例如：

1. `oldREADME.md`
2. `docs/archive/`
3. 若有重复的模型对比文档，只保留一份主版本

---

## 四、整理后如何提交并 push 到 GitHub

当前仓库已经配置了远端：

- `origin https://github.com/jordylin/LCA-LLM.git`

但在提交前，必须先意识到一个现实：

当前工作区已经是脏的，包含：

1. 修改过的文件
2. 已删除但未提交的旧文件
3. 新增但未跟踪的文件

所以，不建议直接执行 `git add . && git push`。

### 推荐提交流程

#### 1. 先查看状态

```bash
git status
```

#### 2. 先确认 `.gitignore`

确保以下大目录不要被误加入：

```bash
models/
lcaLLM/
dataset/
context_files/
LLaMA-Factory/
llamaboard_cache/
logs/
chroma_db/
```

如果决定不把图表和实验结果推上去，也可加入：

```bash
lcia_results/
```

#### 3. 如果你先做了清理，再检查状态

```bash
git status --short
```

#### 4. 建议分批提交，而不是一次全塞

例如：

```bash
git add README.md docs/ backend/ frontend/ scripts/ resources/ test_data/
git commit -m "整理仓库结构并保留LCA-LLM核心代码与评测资产"
```

如果你还做了缓存清理和归档：

```bash
git add .gitignore archive/ docs/
git commit -m "清理运行产物并归档LCIA实验文件"
```

#### 5. 推送到远端

```bash
git push origin main
```

如果当前分支不是 `main`，先看分支名：

```bash
git branch --show-current
```

然后：

```bash
git push origin <当前分支名>
```

#### 6. 如果是第一次把本地分支推到远端

```bash
git push -u origin <当前分支名>
```

### 建议的提交流水线

最稳的是三次提交：

1. `docs + 说明整理`
2. `缓存/日志清理`
3. `代码结构调整或归档`

这样之后回滚也更容易。

---

## 五、后续加入别的基础小模型做对比测试：总体策略

你的目标很明确：

> 通过加入别的更小基础模型作为对比组，突出 `Qwen3-8B + LoRA` 的效果更好。

这是合理的，但建议你把实验分成两类。

### 实验类型 A：基础模型对比

目标：

- `Qwen3-8B base`
- `Qwen2.5-3B-Instruct`
- `Llama-3.2-3B-Instruct`
- 其他小模型 baseline

这一类不需要重新训练 LoRA。

它回答的问题是：

> 只换基础模型，不做领域微调时，谁在这套 agent/tool-calling LCA 任务上更稳？

### 实验类型 B：微调后对比

目标：

- `Qwen3-8B + lca_lora`
- `小模型A + 它自己的 LoRA`
- `小模型B + 它自己的 LoRA`

这一类成本高很多。

它回答的问题是：

> 在相同训练数据下，Qwen3-8B + LoRA 是否依然优于更小模型 + LoRA？

### 推荐优先顺序

先做 A，再决定要不要做 B。

原因：

1. 成本低
2. 更容易快速得到有说服力的 baseline 对比
3. 更适合先突出 `Qwen3-8B + LoRA` 的优势

---

## 六、推荐的候选小模型

以下推荐优先基于“能否接入当前 vLLM + tool-calling 框架”，而不只是通用 benchmark。

### 1. 第一优先：Qwen2.5-3B-Instruct

推荐原因：

1. 与你当前 `Qwen3-8B + LoRA` 同属 Qwen 家族，迁移成本最低
2. Qwen2.5 官方模型卡强调其在结构化输出、JSON、表格理解方面有增强
3. vLLM 官方文档明确说明 `Qwen/Qwen2.5-*` 可以直接使用 `hermes` parser 开启 tool calling

适合用作：

- 最稳妥的小模型 baseline

官方来源：

- Qwen2.5-3B-Instruct 模型卡  
  https://huggingface.co/Qwen/Qwen2.5-3B-Instruct
- vLLM Tool Calling 文档中 Qwen Models 部分  
  https://docs.vllm.ai/en/stable/features/tool_calling/

我根据官方文档的判断是：

- 这是最应该优先尝试的对比小模型

### 2. 第二优先：Llama-3.2-3B-Instruct

推荐原因：

1. 官方模型卡明确提到它面向 agentic retrieval 和 summarization 场景
2. 参数规模小，适合作为“开放基础小模型”对比组
3. vLLM 官方文档明确支持 `Llama 3.2` 的 tool calling，但需要使用 `llama3_json` parser 和对应 chat template

适合用作：

- 跨家族 baseline

注意：

- 它不像 Qwen 那样能直接沿用你现在的 `hermes` 配置
- 你需要改 vLLM 启动参数

官方来源：

- Llama-3.2-3B-Instruct 模型卡  
  https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct
- vLLM Tool Calling 文档中 Llama Models 部分  
  https://docs.vllm.ai/en/stable/features/tool_calling/

### 3. 第三优先：Phi-4-mini-instruct

推荐原因：

1. 参数规模小
2. 官方资料强调 instruction following 和 function calling
3. 适合作为“强小模型”附加参考组

注意：

- 我目前更有把握它适合作为函数调用能力参考模型
- 但它接入你当前这套 `vLLM auto tool-choice + Qwen-style config` 的稳定性，不如前两者稳

官方来源：

- Phi-4-mini-instruct 模型卡  
  https://build.nvidia.com/microsoft/phi-4-mini-instruct/modelcard

### 当前最推荐的起步组合

建议先测这三个：

1. `Qwen3-8B base`
2. `Qwen2.5-3B-Instruct`
3. `Llama-3.2-3B-Instruct`

然后与：

4. `Qwen3-8B + lca_lora`

做对比。

这样最容易讲故事：

- 同家族缩小模型对比：Qwen3-8B vs Qwen2.5-3B
- 跨家族小模型对比：Llama-3.2-3B
- 最终突出：Qwen3-8B + LoRA 最优

---

## 七、为什么不建议一开始就找很多模型

因为你这个任务不是普通聊天 benchmark，而是：

1. 有 system prompt
2. 有工具调用
3. 有 JSON/tool schema
4. 有 retrieval
5. 有 LCA 领域术语

所以真正决定胜负的不只是“模型聪不聪明”，而是：

1. `Valid JSON Rate`
2. tool call 稳定性
3. 对术语和单位的理解
4. 是否容易幻觉

因此，不建议一开始就同时加五六个模型。更好的顺序是：

1. 先统一评测入口
2. 先重跑 `Qwen3-8B base`
3. 先重跑 `Qwen3-8B + LoRA`
4. 再加一个最稳妥的小模型
5. 再加第二个跨家族小模型

---

## 八、后续多模型对比：你需要准备什么

### 1. 固定测试集

建议固定：

- `test_data/`
- 同一批 `ground_truth`

不要在模型之间更换测试集。

### 2. 固定 prompt 和工具定义

所有模型都必须尽量保持：

1. 同一个 system prompt
2. 同一套工具 schema
3. 同一批后端 API
4. 同一批知识库与检索逻辑

否则就不是公平比较。

### 3. 固定采样参数

建议固定：

- `temperature`
- `max_tokens`
- `tool_choice`
- `top_p` 如果使用

### 4. 为每个模型保存独立结果目录

不要重复覆盖 `test_data/predictions_final.json`。

建议改成：

```text
results/
  qwen3_8b_base/
    predictions.json
    metrics.json
  qwen3_8b_lora/
    predictions.json
    metrics.json
  qwen2_5_3b_instruct/
    predictions.json
    metrics.json
  llama3_2_3b_instruct/
    predictions.json
    metrics.json
```

### 5. 先统一评测入口

当前仓库的评测问题是：

1. 历史结果在
2. 指标脚本部分在
3. 真正的一键推理入口有缺失

所以后续一定要先补一个统一评测脚本，而不是继续依赖旧的残缺脚本。

---

## 九、后续多模型对比：具体操作步骤

以下步骤是推荐执行顺序。

### Phase 1：先把当前框架清理稳定

1. 清理缓存/日志/运行产物
2. 整理或归档 LCIA 实验脚本
3. 保留核心服务代码、评测资产、训练脚本
4. 提交到 GitHub

### Phase 2：统一模型启动方式

你当前的 [start_vllm.sh](/home/Research_work/24_yzlin/LCA-LLM/start_vllm.sh) 是偏 Qwen 写法：

- `--served-model-name qwen-lca`
- `--tool-call-parser hermes`

这对 Qwen 友好，但对 Llama 不够通用。

建议后续改造成参数化脚本，至少支持：

1. `MODEL_PATH`
2. `SERVED_MODEL_NAME`
3. `TOOL_CALL_PARSER`
4. `CHAT_TEMPLATE`

#### Qwen 家族建议参数

根据 vLLM 官方文档，对 `Qwen/Qwen2.5-*`：

- `--tool-call-parser hermes`

来源：

- https://docs.vllm.ai/en/stable/features/tool_calling/

#### Llama 家族建议参数

根据 vLLM 官方文档，对 `Llama-3.2-*`：

- `--tool-call-parser llama3_json`
- `--chat-template examples/tool_chat_template_llama3.2_json.jinja`

来源：

- https://docs.vllm.ai/en/stable/features/tool_calling/

### Phase 3：先重跑两组锚点

先确保这两组结果可重现：

1. `Qwen3-8B base`
2. `Qwen3-8B + LoRA`

这是后面所有对比的参照物。

### Phase 4：加入第一个小模型 baseline

建议先加：

1. `Qwen2.5-3B-Instruct`

原因：

1. 家族相近
2. tool-calling 适配最直接
3. 最容易稳定跑通

### Phase 5：加入第二个跨家族 baseline

建议再加：

1. `Llama-3.2-3B-Instruct`

这样就能回答：

1. 同家族缩小参数后表现如何
2. 跨家族小模型表现如何

### Phase 6：统一输出指标表

建议每个模型都输出同一组指标：

1. `Field-level EM`
2. `Numerical Accuracy`
3. `Grounding Accuracy`
4. `Recall`
5. `Precision`
6. `F1 Score`
7. `Valid JSON Rate`
8. `failed_samples`

然后汇总成一张统一表格。

---

## 十、如果你后续想进一步强化论文论点

推荐的论证顺序如下：

1. `Qwen3-8B base` 不够稳定
2. `更小基础模型` 在同一 agent tool-calling 任务上更弱或更不稳定
3. `Qwen3-8B + LoRA` 在 JSON 有效率、Recall、F1、术语理解上整体最好

这样你的论点就不仅是：

> 微调有用

而会变成：

> 在这个特定的 LCA agentic workflow 中，基础模型越小越难稳定完成任务，而 `Qwen3-8B + LoRA` 在性能与稳定性之间给出了更优平衡。

---

## 十一、建议的下一步动作

建议按下面顺序推进：

1. 先做“保守清理”
2. 先整理 `.gitignore`
3. 先提交当前核心代码和文档到 GitHub
4. 再改造 `start_vllm.sh` 为多模型参数化版本
5. 再补统一评测入口
6. 先加 `Qwen2.5-3B-Instruct`
7. 再加 `Llama-3.2-3B-Instruct`

---

## 十二、总结

当前仓库的正确清理思路不是“尽量删”，而是：

1. 保住主框架
2. 保住前景到背景再到 LCIA 的扩展链条
3. 清掉缓存和运行产物
4. 把一次性分析脚本归档而不是直接删除
5. 统一评测入口后，再开展多模型对比

从后续实验角度看，最值得优先做的是：

1. `Qwen3-8B base`
2. `Qwen3-8B + LoRA`
3. `Qwen2.5-3B-Instruct`
4. `Llama-3.2-3B-Instruct`

这是目前最适合用来突出你现有 `Qwen3-8B + LoRA` 优势的一条路线。

---

## 参考来源

以下结论涉及外部官方资料：

1. vLLM Tool Calling 官方文档  
   https://docs.vllm.ai/en/stable/features/tool_calling/

2. Qwen2.5-3B-Instruct 官方模型卡  
   https://huggingface.co/Qwen/Qwen2.5-3B-Instruct

3. Llama-3.2-3B-Instruct 官方模型卡  
   https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct

4. Phi-4-mini-instruct 官方模型卡  
   https://build.nvidia.com/microsoft/phi-4-mini-instruct/modelcard

其中关于模型接入难度和优先级的排序，是基于以上官方资料并结合当前仓库结构做出的工程判断。
