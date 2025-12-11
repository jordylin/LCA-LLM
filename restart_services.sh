#!/bin/bash

# ============================================================================
# EcoLLM 服务启动脚本
# ============================================================================
# 
# 架构说明:
#   vLLM (8080) → Backend (8000) → Frontend (8501)
#   
# 启动顺序:
#   1. vLLM 服务 (GPU 推理引擎) - 需要单独启动: ./start_vllm.sh
#   2. 后端服务 (FastAPI + Qwen-Agent)
#   3. 前端服务 (Streamlit)
#
# 使用方法:
#   ./restart_services.sh          # 使用 LoRA 模型 (默认)
#   USE_BASE=1 ./restart_services.sh  # 使用基座模型 (对比测试)
#
# ============================================================================

set -e

cd /home/Research_work/24_yzlin/LCA-LLM

echo "=========================================="
echo "🌿 EcoLLM 服务启动脚本"
echo "=========================================="
echo ""

# 激活虚拟环境
source lcaLLM/bin/activate

# ============================================================================
# 配置
# ============================================================================
# 模型名称：与 start_vllm.sh 中的 --served-model-name 保持一致
VLLM_MODEL_NAME="qwen-lca"
echo "📦 模型: qwen-lca (LoRA 已合并到 vLLM 服务)"

# ============================================================================
# 1. 检查 vLLM 服务
# ============================================================================
echo ""
echo "1️⃣ 检查 vLLM 服务 (端口 8080)..."
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "   ✅ vLLM 已运行"
else
    echo "   ❌ vLLM 未运行！请先执行: ./start_vllm.sh"
    echo "   提示: vLLM 启动需要约 30-60 秒"
    exit 1
fi

# ============================================================================
# 2. 停止现有服务
# ============================================================================
echo ""
echo "2️⃣ 停止现有服务..."
pkill -9 -f "uvicorn backend.app" 2>/dev/null || echo "   后端未运行"
pkill -9 -f "streamlit run frontend/app.py" 2>/dev/null || echo "   前端未运行"
sleep 2

# ============================================================================
# 3. 启动后端
# ============================================================================
echo ""
echo "3️⃣ 启动后端 (端口 8000)..."
export LLM_SERVICE=qwen_agent
export VLLM_MODEL_NAME=$VLLM_MODEL_NAME
export VLLM_API_BASE=http://localhost:8080/v1

python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "   后端 PID: $BACKEND_PID"

# 等待后端启动
for i in {1..10}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "   ✅ 后端启动成功"
        break
    fi
    echo "   等待中... ($i/10)"
    sleep 1
done

if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ⚠️  后端可能未成功启动，请检查: tail -50 /tmp/backend.log"
fi

# ============================================================================
# 4. 启动前端
# ============================================================================
echo ""
echo "4️⃣ 启动前端 (端口 8501)..."
streamlit run frontend/app.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  --server.fileWatcherType none \
  > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   前端 PID: $FRONTEND_PID"

# 等待前端启动
for i in {1..10}; do
    if curl -s http://localhost:8501 > /dev/null 2>&1; then
        echo "   ✅ 前端启动成功"
        break
    fi
    sleep 1
done

# ============================================================================
# 完成
# ============================================================================
echo ""
echo "=========================================="
echo "✅ EcoLLM 服务启动完成"
echo "=========================================="
echo ""
echo "📊 访问地址:"
echo "   🌐 前端界面:  http://localhost:8501"
echo "   🔌 后端 API:  http://localhost:8000"
echo "   🤖 vLLM API:  http://localhost:8080"
echo ""
echo "📝 日志文件:"
echo "   tail -f /tmp/backend.log   # 后端日志"
echo "   tail -f /tmp/frontend.log  # 前端日志"
echo "   tail -f /tmp/vllm.log      # vLLM 日志"
echo ""
echo "🛑 停止服务: ./stop_services.sh"
echo ""

