#!/usr/bin/env python3
"""
测试微调后的 LoRA 模型效果

用法:
    python scripts/test_finetuned_model.py

对比:
    - 基座模型 (Qwen3-8B)
    - 微调模型 (Qwen3-8B + LoRA)
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.local_qwen_service import LocalQwenService


async def test_model(use_lora: bool = True):
    """测试模型"""
    
    mode = "微调后 (LoRA)" if use_lora else "基座模型"
    print(f"\n{'='*60}")
    print(f"测试模式: {mode}")
    print(f"{'='*60}\n")
    
    # 初始化服务
    service = LocalQwenService(use_lora=use_lora)
    await service.initialize()
    
    # 测试用例 1: LCA 工具调用
    print("📝 测试 1: LCA 数据提取任务")
    print("-" * 40)
    
    messages = [
        {
            "role": "system",
            "content": "MODE: document_based\nPDF_SESSION_ID: test-session-123"
        },
        {
            "role": "user",
            "content": "Please help me extract the electricity consumption data from this LCA document."
        }
    ]
    
    # 定义可用工具
    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_document",
                "description": "Search for information in the uploaded document",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "queries": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of search queries"
                        }
                    },
                    "required": ["queries"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "record_process_flow",
                "description": "Record LCI inventory data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "flow_type": {"type": "string", "enum": ["input", "output"]},
                        "category": {"type": "string"},
                        "name": {"type": "string"},
                        "value": {"type": "number"},
                        "unit": {"type": "string"}
                    },
                    "required": ["flow_type", "category", "name", "value", "unit"]
                }
            }
        }
    ]
    
    result = await service.chat_completion(messages, tools=tools)
    
    if result["success"]:
        print(f"💭 思考过程: {result.get('thinking', '无')[:200]}...")
        print(f"\n📤 响应内容: {result['message']['content'][:300]}...")
        if result['message'].get('tool_calls'):
            print(f"\n🔧 工具调用: {result['message']['tool_calls']}")
    else:
        print(f"❌ 错误: {result.get('error')}")
    
    # 测试用例 2: 简单问答
    print("\n\n📝 测试 2: LCA 知识问答")
    print("-" * 40)
    
    messages2 = [
        {
            "role": "user",
            "content": "What is a functional unit in Life Cycle Assessment?"
        }
    ]
    
    result2 = await service.chat_completion(messages2)
    
    if result2["success"]:
        print(f"💭 思考过程: {result2.get('thinking', '无')[:200]}...")
        print(f"\n📤 响应: {result2['message']['content'][:500]}...")
    
    # 清理
    service.cleanup()
    print(f"\n✅ {mode} 测试完成")


async def compare_models():
    """对比基座模型和微调模型"""
    
    print("\n" + "="*70)
    print("🔬 模型对比测试: 基座 vs 微调")
    print("="*70)
    
    # 检查 LoRA 路径是否存在
    lora_path = "/home/Research_work/24_yzlin/LCA-LLM/models/lca_lora"
    if not os.path.exists(lora_path):
        print(f"\n⚠️ LoRA 适配器不存在: {lora_path}")
        print("请先从云服务器下载 LoRA 适配器到该路径")
        print("\n下载步骤:")
        print("1. 在云服务器上: cd /root/LLaMA-Factory/saves/Qwen3-8B/lora && tar -czvf lca_lora.tar.gz lca_lora/")
        print("2. 下载 lca_lora.tar.gz 到本地")
        print("3. 解压到: /home/Research_work/24_yzlin/LCA-LLM/models/lca_lora/")
        return
    
    # 测试微调模型
    await test_model(use_lora=True)
    
    # 可选: 测试基座模型进行对比
    # await test_model(use_lora=False)


if __name__ == "__main__":
    asyncio.run(compare_models())
