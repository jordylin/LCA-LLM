#!/bin/bash

# vLLM 服务启动脚本
# 用于启动 vLLM OpenAI 兼容 API 服务器

set -e

cd /home/Research_work/24_yzlin/LCA-LLM

echo "=========================================="
echo "vLLM 服务启动脚本"
echo "=========================================="
echo ""

# 激活虚拟环境
source lcaLLM/bin/activate

# 模型路径配置
# 通过环境变量 USE_LORA 控制是否使用 LoRA
# USE_LORA=1  使用合并后的模型或 LoRA 适配器
# USE_LORA=0  使用原生模型（默认，用于测试基线效果）
USE_LORA=${USE_LORA:-0}

MERGED_MODEL="/home/Research_work/24_yzlin/LCA-LLM/models/Qwen3-8B-LCA-Merged"
BASE_MODEL="/home/Research_work/24_yzlin/LCA-LLM/models/Qwen3-8B"
LORA_PATH="/home/Research_work/24_yzlin/LCA-LLM/models/lca_lora"

if [ "$USE_LORA" = "1" ]; then
    # 使用 LoRA
    if [ -d "$MERGED_MODEL" ]; then
        MODEL_PATH="$MERGED_MODEL"
        echo "📦 使用合并后的模型: $MODEL_PATH"
        LORA_ARGS=""
    else
        MODEL_PATH="$BASE_MODEL"
        echo "📦 使用基座模型 + LoRA"
        echo "🔧 LoRA 适配器: $LORA_PATH"
        if [ -d "$LORA_PATH" ]; then
            LORA_ARGS="--enable-lora --lora-modules lca_lora=$LORA_PATH"
        else
            LORA_ARGS=""
            echo "⚠️ LoRA 路径不存在，使用原始模型"
        fi
    fi
else
    # 使用原生模型（测试基线）
    MODEL_PATH="$BASE_MODEL"
    echo "📦 使用原生模型（无 LoRA）: $MODEL_PATH"
    LORA_ARGS=""
fi

# 检查 GPU 显存
echo ""
echo "🔍 检查 GPU 状态..."
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader

# vLLM 服务端口
VLLM_PORT=8080

# 停止已有的 vLLM 服务
echo ""
echo "1️⃣ 停止现有 vLLM 服务..."
pkill -9 -f "vllm.entrypoints" 2>/dev/null || echo "   vLLM 未运行"
sleep 2

# 启动 vLLM
echo ""
echo "2️⃣ 启动 vLLM 服务 (端口 $VLLM_PORT)..."
echo "   模型: $MODEL_PATH"

# 启动命令
# --dtype auto: 自动选择数据类型
# --max-model-len: 最大上下文长度
# --gpu-memory-utilization: GPU 显存使用率
# --quantization: 量化方式（可选：awq, gptq, squeezellm, fp8）
python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_PATH" \
    --served-model-name qwen-lca \
    --host 0.0.0.0 \
    --port $VLLM_PORT \
    --max-model-len 8192 \
    --dtype auto \
    --gpu-memory-utilization 0.9 \
    --trust-remote-code \
    --enable-auto-tool-choice \
    --tool-call-parser hermes \
    $LORA_ARGS \
    > /tmp/vllm.log 2>&1 &

VLLM_PID=$!
echo "   vLLM PID: $VLLM_PID"

# 等待启动
echo ""
echo "3️⃣ 等待 vLLM 启动..."
for i in {1..30}; do
    if curl -s http://localhost:$VLLM_PORT/health > /dev/null 2>&1; then
        echo "   ✅ vLLM 启动成功！"
        break
    fi
    echo "   等待中... ($i/30)"
    sleep 2
done

# 检查是否成功
if curl -s http://localhost:$VLLM_PORT/health > /dev/null 2>&1; then
    echo ""
    echo "=========================================="
    echo "✅ vLLM 服务启动完成"
    echo "=========================================="
    echo ""
    echo "📊 API 地址: http://localhost:$VLLM_PORT"
    echo "📝 日志文件: /tmp/vllm.log"
    echo ""
    echo "🔧 测试命令:"
    echo "   curl http://localhost:$VLLM_PORT/v1/models"
    echo ""
    echo "🛑 停止命令:"
    echo "   pkill -9 -f 'vllm.entrypoints'"
else
    echo ""
    echo "❌ vLLM 启动失败，请检查日志:"
    echo "   tail -50 /tmp/vllm.log"
fi
