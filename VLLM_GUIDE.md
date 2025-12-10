# vLLM + Qwen-Agent 使用指南

## 架构说明

```
┌─────────────────────────────────────────────────────────┐
│                    前端 (Streamlit)                      │
│                    http://localhost:8501                 │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    后端 (FastAPI)                        │
│                    http://localhost:8000                 │
│  ┌─────────────────────────────────────────────────┐    │
│  │              LLMChatService                      │    │
│  │         (工具调用管理、对话流程)                   │    │
│  └─────────────────────────────────────────────────┘    │
│                           │                              │
│                           ▼                              │
│  ┌─────────────────────────────────────────────────┐    │
│  │    VLLMService / LocalQwenService               │    │
│  │         (LLM 推理引擎)                           │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    vLLM 服务器                           │
│                    http://localhost:8080                 │
│         (OpenAI 兼容 API，高性能推理)                     │
└─────────────────────────────────────────────────────────┘
```

## 快速开始

### 方式一：使用原生模型测试（推荐先测试基线效果）

```bash
# 终端 1：启动 vLLM（原生模型）
./start_vllm.sh

# 终端 2：启动后端（使用 vLLM）
LLM_SERVICE=vllm ./restart_services.sh

# 终端 3：查看日志
tail -f /tmp/vllm.log      # vLLM 日志
tail -f /tmp/backend.log   # 后端日志
```

### 方式二：使用 LoRA 微调模型

```bash
# 先合并模型（只需执行一次）
python merge_lora.py

# 启动 vLLM（使用合并后的模型）
USE_LORA=1 ./start_vllm.sh

# 启动后端
LLM_SERVICE=vllm ./restart_services.sh
```

## 环境变量说明

### vLLM 启动 (`start_vllm.sh`)

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `USE_LORA` | `0` | 是否使用 LoRA。`0`=原生模型，`1`=LoRA 模型 |

### 后端启动 (`restart_services.sh`)

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LLM_SERVICE` | `local` | LLM 服务类型。`vllm`/`qwen_agent`/`local` |
| `VLLM_API_BASE` | `http://localhost:8080/v1` | vLLM API 地址 |

## 验证是否生效

### 1. 检查 vLLM 是否启动

```bash
# 查看可用模型
curl http://localhost:8080/v1/models

# 预期输出：
# {"object":"list","data":[{"id":"qwen-lca",...}]}
```

### 2. 检查后端是否连接 vLLM

```bash
# 查看后端日志
grep "LLM 服务" /tmp/backend.log

# 预期输出：
# 🚀 使用 vLLM 服务
```

### 3. 测试推理

```bash
# 直接测试 vLLM
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-lca",
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 100
  }'
```

### 4. 查看流式输出

在后端日志中可以看到实时的推理过程：
```bash
tail -f /tmp/backend.log
```

## 常见问题

### Q: vLLM 启动失败，显存不足

vLLM 默认使用 90% 显存。如果显存不足，可以调整：

```bash
# 编辑 start_vllm.sh，修改 --gpu-memory-utilization
--gpu-memory-utilization 0.7  # 使用 70% 显存
```

或者减少上下文长度：
```bash
--max-model-len 8192  # 从 16384 减少到 8192
```

### Q: 如何切换回原来的 LocalQwenService？

```bash
# 不设置 LLM_SERVICE 或设置为 local
./restart_services.sh
# 或
LLM_SERVICE=local ./restart_services.sh
```

### Q: 如何知道用的是原生模型还是 LoRA 模型？

查看 vLLM 启动日志：
```bash
head -20 /tmp/vllm.log
```

会显示：
- `📦 使用原生模型（无 LoRA）` - 原生模型
- `📦 使用合并后的模型` - LoRA 合并后的模型

### Q: 合并模型后想删除怎么办？

```bash
# 删除合并后的模型（原始模型和 LoRA 不受影响）
rm -rf models/Qwen3-8B-LCA-Merged/
```

## 性能对比

| 服务 | 首字延迟 | 吞吐量 | 显存占用 | 流式输出 |
|------|----------|--------|----------|----------|
| LocalQwenService (4-bit) | 10-20s | 低 | ~6GB | ❌ |
| vLLM (fp16) | 2-5s | 高 | ~16GB | ✅ |
| vLLM (8-bit) | 3-6s | 中 | ~10GB | ✅ |

## 下一步

1. **测试原生模型效果**：先用原生 Qwen3-8B 测试，建立基线
2. **对比 LoRA 效果**：如果原生效果不错，再测试 LoRA 版本
3. **调整 System Prompt**：根据测试结果优化提示词
4. **考虑重新训练**：如果 LoRA 效果不好，考虑调整训练数据
