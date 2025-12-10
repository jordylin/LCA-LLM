#!/bin/bash
# 启动 LLaMA Factory Web UI
cd /home/Research_work/24_yzlin/LCA-LLM
source lcaLLM/bin/activate
DISABLE_VERSION_CHECK=1 llamafactory-cli webui
