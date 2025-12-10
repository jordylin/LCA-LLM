#!/usr/bin/env python3
"""
转换训练数据格式，解决模型幻觉 tool_response 的问题

问题原因：
- 原格式中 observation 作为独立角色，模型学会了"预测"它
- 导致推理时模型会在 <think> 中幻觉 tool_response

解决方案：
- 将 observation 改为 human 角色，并用 <tool_response> 标签包装
- 这样模型就知道 tool_response 是输入，不是它应该生成的输出

转换规则：
- human -> human (不变)
- function_call -> assistant (Qwen3 官方格式)
- observation -> user (作为用户输入的工具返回)
- gpt -> assistant (不变)
- system -> system (不变)
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Any


def convert_message(msg: Dict[str, Any]) -> Dict[str, Any]:
    """转换单条消息的角色"""
    role = msg.get("from", "")
    value = msg.get("value", "")
    
    if role == "system":
        return {"from": "system", "value": value}
    
    elif role == "human":
        return {"from": "human", "value": value}
    
    elif role == "function_call":
        # function_call -> assistant
        # 保持 <think> 和工具调用格式不变
        return {"from": "gpt", "value": value}
    
    elif role == "observation":
        # observation -> human，用 <tool_response> 包装
        # 检查是否已经有 <tool_response> 标签
        if not value.strip().startswith("<tool_response>"):
            value = f"<tool_response>\n{value}\n</tool_response>"
        return {"from": "human", "value": value}
    
    elif role == "gpt":
        return {"from": "gpt", "value": value}
    
    else:
        # 未知角色，保持不变
        print(f"⚠️ 未知角色: {role}")
        return msg


def convert_conversation(conv: Dict[str, Any]) -> Dict[str, Any]:
    """转换单条对话"""
    messages = conv.get("conversations", [])
    converted_messages = []
    
    for msg in messages:
        converted_msg = convert_message(msg)
        converted_messages.append(converted_msg)
    
    return {"conversations": converted_messages}


def validate_conversation(conv: Dict[str, Any]) -> bool:
    """验证转换后的对话格式"""
    messages = conv.get("conversations", [])
    
    # 检查角色序列是否合理
    valid_roles = {"system", "human", "gpt"}
    for msg in messages:
        role = msg.get("from", "")
        if role not in valid_roles:
            print(f"❌ 无效角色: {role}")
            return False
    
    return True


def main():
    parser = argparse.ArgumentParser(description="转换训练数据格式")
    parser.add_argument("--input", "-i", required=True, help="输入文件路径")
    parser.add_argument("--output", "-o", required=True, help="输出文件路径")
    parser.add_argument("--validate", "-v", action="store_true", help="验证转换结果")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"❌ 输入文件不存在: {input_path}")
        return
    
    print(f"📖 读取输入文件: {input_path}")
    
    converted_data = []
    total_count = 0
    error_count = 0
    
    # 统计转换情况
    role_stats = {
        "human": 0,
        "function_call": 0,
        "observation": 0,
        "gpt": 0,
        "system": 0
    }
    
    with open(input_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                conv = json.loads(line)
                total_count += 1
                
                # 统计原始角色
                for msg in conv.get("conversations", []):
                    role = msg.get("from", "unknown")
                    if role in role_stats:
                        role_stats[role] += 1
                
                # 转换
                converted_conv = convert_conversation(conv)
                
                # 验证
                if args.validate and not validate_conversation(converted_conv):
                    print(f"⚠️ 第 {line_num} 行验证失败")
                    error_count += 1
                    continue
                
                converted_data.append(converted_conv)
                
            except json.JSONDecodeError as e:
                print(f"❌ 第 {line_num} 行 JSON 解析错误: {e}")
                error_count += 1
    
    print(f"\n📊 原始数据统计:")
    print(f"   总对话数: {total_count}")
    for role, count in role_stats.items():
        print(f"   {role}: {count} 条消息")
    
    print(f"\n📝 转换规则:")
    print(f"   human -> human (不变)")
    print(f"   function_call -> gpt (作为 assistant 输出)")
    print(f"   observation -> human (作为用户输入的工具返回)")
    print(f"   gpt -> gpt (不变)")
    print(f"   system -> system (不变)")
    
    # 写入输出文件
    print(f"\n💾 写入输出文件: {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        for conv in converted_data:
            f.write(json.dumps(conv, ensure_ascii=False) + "\n")
    
    print(f"\n✅ 转换完成!")
    print(f"   成功: {len(converted_data)} 条")
    print(f"   失败: {error_count} 条")
    
    # 显示转换后的示例
    if converted_data:
        print(f"\n📋 转换后示例 (第一条对话的前5条消息):")
        first_conv = converted_data[0]["conversations"][:5]
        for i, msg in enumerate(first_conv):
            role = msg.get("from", "")
            value = msg.get("value", "")[:100]
            print(f"   [{i}] {role}: {value}...")


if __name__ == "__main__":
    main()
