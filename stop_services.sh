#!/bin/bash

# LCA-LLM服务停止脚本
# 用于停止所有运行中的服务

echo "=========================================="
echo "LCA-LLM 服务停止脚本"
echo "=========================================="
echo ""

# 停止后端
echo "1️⃣ 停止后端服务..."
if pkill -9 -f uvicorn 2>/dev/null; then
    echo "   ✅ 后端已停止"
else
    echo "   ℹ️  后端未运行"
fi

# 停止前端
echo ""
echo "2️⃣ 停止前端服务..."
if pkill -f "streamlit run scripts/expert_annotation_workbench.py" 2>/dev/null; then
    echo "   ✅ 前端已停止"
else
    echo "   ℹ️  前端未运行"
fi

echo ""
echo "=========================================="
echo "✅ 所有服务已停止"
echo "=========================================="
echo ""

