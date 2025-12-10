#!/bin/bash

# LCA-LLM服务重启脚本
# 用于快速重启后端和前端服务

set -e

cd /home/Research_work/24_yzlin/LCA-LLM

echo "=========================================="
echo "LCA-LLM 服务重启脚本"
echo "=========================================="
echo ""

# 激活虚拟环境
source lcaLLM/bin/activate

# 1. 停止所有服务
echo "1️⃣ 停止现有服务..."
pkill -9 -f uvicorn 2>/dev/null || echo "   后端未运行"
pkill -9 -f "streamlit run frontend/app.py" 2>/dev/null || echo "   前端(8501)未运行"
pkill -9 -f "streamlit run scripts/expert_annotation_workbench.py" 2>/dev/null || echo "   工作台(8504)未运行"
sleep 2

# 2. 启动后端
echo ""
echo "2️⃣ 启动后端 (端口 8000)..."
# 🔥 LLM 服务选择：
#   LLM_SERVICE=vllm       使用 vLLM（需要先运行 ./start_vllm.sh）
#   LLM_SERVICE=qwen_agent 使用 Qwen-Agent
#   LLM_SERVICE=local      使用 LocalQwenService（默认）
export LLM_SERVICE=${LLM_SERVICE:-local}
export VLLM_API_BASE=${VLLM_API_BASE:-http://localhost:8080/v1}
echo "   LLM 服务: $LLM_SERVICE"
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "   后端 PID: $BACKEND_PID"
sleep 3

# 3. 检查后端是否成功启动
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✅ 后端启动成功"
else
    echo "   ⚠️  后端可能未成功启动，请检查 /tmp/backend.log"
fi

# 4. 启动前端（8501端口 - AI Chat界面）
echo ""
echo "3️⃣ 启动前端 (端口 8501, 文件监视已禁用)..."
streamlit run frontend/app.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  --server.fileWatcherType none \
  > /tmp/streamlit_8501.log 2>&1 &
STREAMLIT_PID=$!
echo "   前端 PID: $STREAMLIT_PID"
sleep 3

# 5. 检查前端是否成功启动
if curl -s http://localhost:8501 > /dev/null 2>&1; then
    echo "   ✅ 前端启动成功"
else
    echo "   ⚠️  前端可能未成功启动，请检查 /tmp/streamlit_8501.log"
fi

# 6. 启动专家工作台（8504端口）
echo ""
echo "4️⃣ 启动专家工作台 (端口 8504, 文件监视已禁用)..."
streamlit run scripts/expert_annotation_workbench.py \
  --server.port 8504 \
  --server.address 0.0.0.0 \
  --server.fileWatcherType none \
  > /tmp/streamlit_8504.log 2>&1 &
WORKBENCH_PID=$!
echo "   工作台 PID: $WORKBENCH_PID"
sleep 3

# 7. 检查工作台是否成功启动
if curl -s http://localhost:8504 > /dev/null 2>&1; then
    echo "   ✅ 专家工作台启动成功"
else
    echo "   ⚠️  专家工作台可能未成功启动，请检查 /tmp/streamlit_8504.log"
fi

echo ""
echo "=========================================="
echo "✅ 服务启动完成"
echo "=========================================="
echo ""
echo "📊 访问地址:"
echo "   后端 API:      http://localhost:8000"
echo "   前端(AI Chat):  http://localhost:8501"
echo "   专家工作台:     http://localhost:8504"
echo ""
echo "📝 日志文件:"
echo "   后端:     /tmp/backend.log"
echo "   前端:     /tmp/streamlit_8501.log"
echo "   工作台:   /tmp/streamlit_8504.log"
echo ""
echo "🔧 查看日志命令:"
echo "   tail -f /tmp/backend.log        # 后端日志"
echo "   tail -f /tmp/streamlit_8501.log # 前端日志"
echo "   tail -f /tmp/streamlit_8504.log # 工作台日志"
echo ""
echo "🛑 停止服务命令:"
echo "   pkill -9 -f uvicorn"
echo "   pkill -9 -f 'streamlit run frontend/app.py'"
echo "   pkill -9 -f 'streamlit run scripts/expert_annotation_workbench.py'"
echo ""

