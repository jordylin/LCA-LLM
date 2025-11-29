"""
JSON to JSONL 转换脚本

功能：
将填充好<think>内容的JSON文件转换为JSONL格式，用于模型训练

作者：AI Assistant
日期：2025-11-16
"""

import json
import argparse
from pathlib import Path


def convert_json_to_jsonl(input_path: str, output_path: str):
    """
    将JSON数组转换为JSONL格式
    
    Args:
        input_path: 输入JSON文件路径
        output_path: 输出JSONL文件路径
    """
    print(f"📖 读取 JSON 文件: {input_path}")
    
    # 读取JSON文件
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        print("❌ 错误: JSON文件必须是一个数组")
        return
    
    print(f"找到 {len(data)} 个样本")
    
    # 确保输出目录存在
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 写入JSONL文件（只保留messages字段，移除metadata）
    with open(output_file, 'w', encoding='utf-8') as f:
        for sample in data:
            # 只保留messages，移除metadata等辅助字段
            clean_sample = {"messages": sample["messages"]}
            f.write(json.dumps(clean_sample, ensure_ascii=False) + '\n')
    
    print(f"✅ 成功转换为 JSONL 格式: {output_path}")
    print(f"   (已移除 metadata 字段，仅保留 messages)")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="将JSON数组转换为JSONL格式"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="输入JSON文件路径"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="输出JSONL文件路径"
    )
    
    args = parser.parse_args()
    
    convert_json_to_jsonl(args.input, args.output)


if __name__ == "__main__":
    main()
