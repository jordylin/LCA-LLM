# LCA-LLM

LCA-LLM is a domain-focused framework for using language models in Life Cycle Assessment workflows. It combines document understanding, tool-based LCI extraction, expert traceability, background matching, and downstream LCIA calculation support.

## What this repository is for

This project is built around one end-to-end idea:

1. Read LCA-related PDF documents.
2. Extract foreground LCI data through a tool-calling workflow.
3. Store each action and record with traceability.
4. Match extracted foreground flows to background database entries.
5. Support downstream LCIA calculation and result analysis.

The repository also includes training, evaluation, and LoRA fine-tuning assets for making the model more reliable in this workflow.

## Core workflow

### 1. Document ingestion and retrieval

- Upload a PDF document.
- Parse text and tables into chunks.
- Build a session-level temporary vector index for semantic search.

Relevant modules:

- `backend/services/pdf_processor.py`
- `backend/services/table_aware_chunker.py`
- `backend/services/session_manager.py`
- `backend/services/knowledge_base.py`

### 2. Tool-based LCI extraction

- The model interacts through a constrained tool set instead of free-form extraction.
- Main tools include document search, scope definition, parameter recording, calculation, flow recording, and session summary.
- All recorded actions are stored for traceability and later training-data construction.

Relevant modules:

- `backend/services/tool_service.py`
- `backend/services/qwen_agent_tools.py`
- `backend/services/llm_chat_service.py`
- `backend/services/qwen_agent_service_v2.py`

### 3. Background matching and LCIA support

- Extracted foreground flows can be matched to background entries such as ecoinvent-style flows and processes.
- The repository contains code for flow matching, unit compatibility checks, LCIA preparation, and openLCA IPC integration.

Relevant modules:

- `backend/services/ecoinvent_matcher.py`
- `backend/services/unit_compatibility.py`
- `backend/services/lcia_calculator.py`
- `backend/services/openlca_client.py`

### 4. Training and evaluation

- The repository includes scripts for dataset preparation, export, validation, and fine-tuning configuration.
- It also contains baseline-vs-fine-tuned evaluation artifacts and test data used for comparison.

Relevant paths:

- `scripts/`
- `test_data/`
- `docs/`

## Architecture

The current runtime architecture is:

- `Streamlit frontend` on port `8501`
- `FastAPI backend` on port `8000`
- `vLLM inference server` on port `8080`
- `MongoDB` for persistent structured records and background data
- `ChromaDB` for temporary session-level document retrieval

Typical runtime flow:

1. A document is uploaded from the frontend.
2. The backend creates a session and indexes the document.
3. The LLM runs through a tool-calling loop to search, extract, calculate, and record LCI data.
4. Recorded flows can then be matched to background data and used for LCIA-related processing.

## Repository layout

- `backend/`
  FastAPI application, service layer, chat logic, tools, matching, and LCIA support.

- `frontend/`
  Streamlit interface for document upload, chat, extraction, matching, and LCIA-related interaction.

- `scripts/`
  Data preparation, export, validation, evaluation, and training configuration scripts.

- `resources/`
  Unit definitions and domain keyword resources.

- `test_data/`
  Evaluation samples, predictions, ground truth, and stored metric outputs.

- `docs/`
  Architecture notes, training/export guides, and comparison planning documents.

## Running the system

### Start the inference server

```bash
./start_vllm.sh
```

By default this starts the LoRA-enabled model path if available.

### Start backend and frontend

```bash
./restart_services.sh
```

### Stop services

```bash
./stop_services.sh
```

## Model modes

The repository currently centers on `Qwen3-8B` and its `lca_lora` adapter.

Common usage patterns:

- `LoRA-enabled serving`: default path through `start_vllm.sh`
- `Base-model comparison`: serve the base model without LoRA for baseline testing

Related files:

- `start_vllm.sh`
- `merge_lora.py`
- `run_baseline_evaluation.sh`

## Current status

What is already in place:

- Document parsing and retrieval
- Tool-based foreground LCI extraction
- Action-traceable storage in MongoDB
- Background flow matching support
- LCIA-related service code and analysis scripts
- LoRA fine-tuning assets and baseline comparison artifacts

What still needs consolidation:

- A single fully unified multi-model evaluation pipeline
- Cleaner organization of archived analysis scripts and generated outputs
- More systematic comparison of additional smaller base models

## Documentation

Useful starting points:

- `docs/ARCHITECTURE_SUMMARY.md`
- `docs/EVALUATION_GUIDE.md`
- `docs/FINETUNE_GUIDE.md`
- `docs/REPO_CLEANUP_AND_MODEL_COMPARISON_PLAN.md`

## Notes

- Large directories such as `models/`, `dataset/`, `lcaLLM/`, and runtime caches are intentionally excluded from Git tracking.
- Some historical evaluation artifacts remain in the repository even though parts of the original evaluation pipeline need cleanup or reconstruction.
