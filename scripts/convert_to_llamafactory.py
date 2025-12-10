#!/usr/bin/env python3
"""
将 Qwen3 格式的训练数据转换为 LLaMA Factory 格式

输入格式 (Qwen3 原生):
{
    "messages": [
        {"role": "system", "content": "..."},
        {"role": "user", "content": "..."},
        {"role": "assistant", "reasoning_content": "...", "tool_calls": [{"name": "...", "arguments": {...}}]},
        {"role": "tool", "content": "..."},
        {"role": "assistant", "reasoning_content": "...", "content": "..."}
    ]
}

输出格式 (LLaMA Factory sharegpt):
{
    "conversations": [
        {"from": "system", "value": "..."},
        {"from": "human", "value": "..."},
        {"from": "function_call", "value": "<think>...</think>\n\n<tool_call>...</tool_call>"},
        {"from": "observation", "value": "..."},
        {"from": "gpt", "value": "<think>...</think>\n\n..."}
    ]
}
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Any


def convert_tool_calls_to_json(tool_calls: List[Dict]) -> str:
    """将 tool_calls 列表转换为 JSON 格式（LLaMA Factory 会自动添加 <tool_call> 标签）"""
    # LLaMA Factory 期望的是纯 JSON，它会自动用 tool_format 添加标签
    if len(tool_calls) == 1:
        # 单个 tool call
        tc = tool_calls[0]
        return json.dumps({"name": tc.get("name", ""), "arguments": tc.get("arguments", {})}, ensure_ascii=False)
    else:
        # 多个 tool calls（并行调用）
        calls = []
        for tc in tool_calls:
            calls.append({"name": tc.get("name", ""), "arguments": tc.get("arguments", {})})
        return json.dumps(calls, ensure_ascii=False)


def convert_message(msg: Dict[str, Any]) -> Dict[str, str]:
    """转换单条消息"""
    role = msg.get("role", "")
    content = msg.get("content", "")
    reasoning_content = msg.get("reasoning_content", "")
    tool_calls = msg.get("tool_calls", [])
    
    # 角色映射
    role_mapping = {
        "system": "system",
        "user": "user", 
        "assistant": "gpt",
        "tool": "observation"
    }
    
    # 处理 assistant 消息
    if role == "assistant":
        parts = []
        
        # 1. 添加 reasoning_content（如果有）
        if reasoning_content:
            parts.append(f"<think>\n{reasoning_content}\n</think>")
        
        # 2. 处理 tool_calls（如果有）
        if tool_calls:
            tool_json = convert_tool_calls_to_json(tool_calls)
            parts.append(tool_json)
            # 有 tool_calls 的 assistant 消息转换为 function_call
            new_role = "function_call"
        else:
            new_role = "gpt"
        
        # 3. 添加 content（如果有）
        if content:
            parts.append(content)
        
        # 合并所有部分
        new_value = "\n\n".join(parts) if parts else ""
        
        return {"from": new_role, "value": new_value}
    
    # 处理 tool 消息（工具返回结果）
    elif role == "tool":
        # 提取 tool_response 内容
        # 原始格式可能是 "<tool_response>...</tool_response>" 或纯文本
        if content.startswith("<tool_response>") and content.endswith("</tool_response>"):
            # 去掉外层标签，因为 LLaMA Factory 的 qwen3 template 会自动添加
            inner_content = content[len("<tool_response>"):-len("</tool_response>")].strip()
        else:
            inner_content = content
        
        return {"from": "observation", "value": inner_content}
    
    # 处理 user 消息
    elif role == "user":
        return {"from": "human", "value": content}
    
    # 处理 system 消息
    elif role == "system":
        return {"from": "system", "value": content}
    
    else:
        raise ValueError(f"Unknown role: {role}")


def convert_sample(sample: Dict[str, Any]) -> Dict[str, Any]:
    """转换单个样本
    
    特殊处理：如果 role=tool 的消息同时有 tool_calls，
    需要拆分成两条消息：observation + function_call
    """
    messages = sample.get("messages", [])
    conversations = []
    
    for msg in messages:
        role = msg.get("role", "")
        tool_calls = msg.get("tool_calls", [])
        
        # 特殊情况：tool 消息带有 tool_calls（数据生成 bug）
        # 需要拆分成：observation + function_call
        if role == "tool" and tool_calls:
            # 1. 先添加 observation（工具返回结果）
            content = msg.get("content", "")
            if content.startswith("<tool_response>") and content.endswith("</tool_response>"):
                inner_content = content[len("<tool_response>"):-len("</tool_response>")].strip()
            else:
                inner_content = content
            conversations.append({"from": "observation", "value": inner_content})
            
            # 2. 再添加 function_call（新的工具调用）
            # 这个 tool_calls 应该有对应的 reasoning，但原数据没有，我们用空的
            tool_json = convert_tool_calls_to_json(tool_calls)
            conversations.append({"from": "function_call", "value": tool_json})
        else:
            # 正常转换
            converted = convert_message(msg)
            conversations.append(converted)
    
    return {"conversations": conversations}


def validate_conversion(original: Dict, converted: Dict) -> List[str]:
    """验证转换结果 - 简化版，只检查关键内容是否保留"""
    issues = []
    
    orig_msgs = original.get("messages", [])
    conv_msgs = converted.get("conversations", [])
    
    # 收集原始数据中的所有关键内容
    orig_reasoning = []
    orig_tool_calls = []
    orig_contents = []
    
    for msg in orig_msgs:
        if msg.get("reasoning_content"):
            orig_reasoning.append(msg["reasoning_content"][:50])
        if msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                orig_tool_calls.append(tc.get("name", ""))
        if msg.get("content") and msg.get("role") == "assistant":
            orig_contents.append(msg["content"][:50])
    
    # 收集转换后的内容
    conv_text = " ".join(c.get("value", "") for c in conv_msgs)
    
    # 验证 reasoning 是否保留
    for r in orig_reasoning:
        if r[:30] not in conv_text:
            issues.append(f"reasoning 可能丢失: {r[:30]}...")
    
    # 验证 tool_calls 是否保留
    for tc_name in orig_tool_calls:
        if tc_name not in conv_text:
            issues.append(f"tool_call 丢失: {tc_name}")
    
    # 验证 content 是否保留
    for c in orig_contents:
        if c[:30] not in conv_text:
            issues.append(f"content 可能丢失: {c[:30]}...")
    
    return issues


def main():
    parser = argparse.ArgumentParser(description="转换数据格式为 LLaMA Factory 格式")
    parser.add_argument("--input", type=str, default="dataset/finetune_data_all.jsonl",
                        help="输入文件路径")
    parser.add_argument("--output", type=str, default="LLaMA-Factory/data/lca_data.jsonl",
                        help="输出文件路径")
    parser.add_argument("--validate", action="store_true", default=True,
                        help="验证转换结果")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    print(f"📂 输入文件: {input_path}")
    print(f"📂 输出文件: {output_path}")
    
    # 读取原始数据
    samples = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                samples.append(json.loads(line))
    
    print(f"📊 读取 {len(samples)} 个样本")
    
    # 转换数据
    converted_samples = []
    all_issues = []
    
    for i, sample in enumerate(samples):
        try:
            converted = convert_sample(sample)
            converted_samples.append(converted)
            
            # 验证
            if args.validate:
                issues = validate_conversion(sample, converted)
                if issues:
                    all_issues.append((i, issues))
        except Exception as e:
            print(f"❌ 样本 {i} 转换失败: {e}")
            raise
    
    # 报告验证结果
    if all_issues:
        print(f"\n⚠️  发现 {len(all_issues)} 个样本有问题:")
        for idx, issues in all_issues[:5]:  # 只显示前5个
            print(f"  样本 {idx}:")
            for issue in issues:
                print(f"    - {issue}")
        if len(all_issues) > 5:
            print(f"  ... 还有 {len(all_issues) - 5} 个样本有问题")
    else:
        print("✅ 所有样本验证通过")
    
    # 保存转换后的数据
    with open(output_path, 'w', encoding='utf-8') as f:
        for sample in converted_samples:
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')
    
    print(f"\n✅ 转换完成，保存到 {output_path}")
    
    # 打印统计信息
    total_conversations = sum(len(s["conversations"]) for s in converted_samples)
    role_counts = {}
    for s in converted_samples:
        for conv in s["conversations"]:
            role = conv["from"]
            role_counts[role] = role_counts.get(role, 0) + 1
    
    print(f"\n📊 统计信息:")
    print(f"  总样本数: {len(converted_samples)}")
    print(f"  总消息数: {total_conversations}")
    print(f"  角色分布:")
    for role, count in sorted(role_counts.items()):
        print(f"    {role}: {count}")
    
    # 打印一个样本示例
    print(f"\n📝 转换示例 (第一个样本的前3条消息):")
    if converted_samples:
        for conv in converted_samples[0]["conversations"][:3]:
            print(f"  [{conv['from']}]")
            value_preview = conv['value'][:200] + "..." if len(conv['value']) > 200 else conv['value']
            print(f"    {value_preview}")


if __name__ == "__main__":
    main()
