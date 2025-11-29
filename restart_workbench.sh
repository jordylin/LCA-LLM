#!/bin/bash
# 快速重启工作台

echo "🔄 重启工作台..."

# 停止旧的工作台
pkill -9 -f 'streamlit run scripts/expert_annotation_workbench.py'
sleep 1

# 启动新的工作台
cd /home/Research_work/24_yzlin/LCA-LLM
nohup streamlit run scripts/expert_annotation_workbench.py \
  --server.port 8504 \
  --server.address 0.0.0.0 \
  --server.fileWatcherType none \
  > /tmp/streamlit_8504.log 2>&1 &

WORKBENCH_PID=$!
sleep 2

# 检查是否启动成功
if ps -p $WORKBENCH_PID > /dev/null; then
    echo "✅ 工作台已重启 (PID: $WORKBENCH_PID)"
    echo "📊 访问地址: http://localhost:8504"
    echo "📝 日志文件: /tmp/streamlit_8504.log"
    echo ""
    echo "💡 请刷新浏览器 (Ctrl+Shift+R) 并测试 Smart Skip"
else
    echo "❌ 工作台启动失败，请查看日志:"
    echo "   tail -50 /tmp/streamlit_8504.log"
fi
