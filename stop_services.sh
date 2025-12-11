#!/bin/bash

# ============================================================================
# EcoLLM 服务停止脚本
# ============================================================================
#
# 使用方法:
#   ./stop_services.sh        # 停止后端和前端 (保留 vLLM)
#   ./stop_services.sh --all  # 停止所有服务 (包括 vLLM)
#
# ============================================================================

echo "=========================================="
echo "🌿 EcoLLM 服务停止脚本"
echo "=========================================="
echo ""

# 停止前端
echo "1️⃣ 停止前端服务 (8501)..."
if pkill -9 -f "streamlit run frontend/app.py" 2>/dev/null; then
    echo "   ✅ 前端已停止"
else
    echo "   ℹ️  前端未运行"
fi

# 停止后端
echo ""
echo "2️⃣ 停止后端服务 (8000)..."
if pkill -9 -f "uvicorn backend.app" 2>/dev/null; then
    echo "   ✅ 后端已停止"
else
    echo "   ℹ️  后端未运行"
fi

# 如果指定 --all，停止 vLLM
if [ "$1" = "--all" ]; then
    echo ""
    echo "3️⃣ 停止 vLLM 服务 (8080)..."
    if pkill -9 -f "vllm.entrypoints" 2>/dev/null; then
        echo "   ✅ vLLM 已停止"
    else
        echo "   ℹ️  vLLM 未运行"
    fi
fi

echo ""
echo "=========================================="
echo "✅ 服务已停止"
echo "=========================================="
echo ""

# 显示当前状态
echo "📊 当前服务状态:"
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "   🤖 vLLM (8080):   运行中"
else
    echo "   🤖 vLLM (8080):   已停止"
fi
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   🔌 后端 (8000):   运行中"
else
    echo "   🔌 后端 (8000):   已停止"
fi
if curl -s http://localhost:8501 > /dev/null 2>&1; then
    echo "   🌐 前端 (8501):   运行中"
else
    echo "   🌐 前端 (8501):   已停止"
fi
echo ""

if [ "$1" != "--all" ]; then
    echo "💡 提示: 使用 ./stop_services.sh --all 可同时停止 vLLM"
    echo ""
fi

