"""
CAMEL AI Name/Note 改进脚本 - 两阶段处理

阶段1: 改进 name 和 note 字段
阶段2: 生成推理内容

作者：AI Assistant
日期：2025-11-22
"""

import os
import sys
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import argparse
from pathlib import Path

# CAMEL AI imports
try:
    from camel.agents import ChatAgent
    from camel.messages import BaseMessage
except ImportError:
    print("❌ CAMEL AI 未安装。请运行: pip install camel-ai")
    sys.exit(1)


class NameNoteImprover:
    """使用 CAMEL AI 改进 name 和 note 字段"""
    
    def __init__(self, api_key: str, model_name: str = "deepseek-chat"):
        """
        初始化改进器
        
        Args:
            api_key: DeepSeek API Key
            model_name: 模型名称
        """
        self.api_key = api_key
        self.model_name = model_name
        
        # 配置 CAMEL AI
        os.environ["OPENAI_API_KEY"] = api_key
        os.environ["OPENAI_API_BASE_URL"] = "https://api.deepseek.com"
        
        from camel.models import OpenAIModel
        from camel.configs.openai_config import ChatGPTConfig
        
        config = ChatGPTConfig(
            temperature=1.0,  # DeepSeek 推荐：数据抽取/分析场景
            max_tokens=300
        )
        
        self.agent = ChatAgent(
            system_message=self._get_improvement_system_prompt(),
            model=OpenAIModel(
                model_type=model_name,
                model_config_dict=config.as_dict(),
                api_key=api_key,
                url="https://api.deepseek.com"
            )
        )
    
    def _get_improvement_system_prompt(self) -> str:
        """获取 Name/Note 改进的系统提示词 (v3 - Guided, Not Constrained)"""
        return """You are an LCA data standardizer. Refine user drafts into professional LCI records.

## Core Logic: Searchability + Context

LCI databases (like Ecoinvent) work by searching the **material/flow identity** first, then filtering by **characteristics**.

Your task: Split user's informal notes into this two-field structure:

### 1. Name Field (Identity for Searching)
- **Purpose**: Create a searchable, standardized flow name
- **Strategy**: 
  * Use standard industrial terminology (not abbreviations)
  * Focus on WHAT the flow is (material, energy, service, waste)
  * Common format: `[Subject], [Type]` when applicable
  
- **Examples**:
  * "Ti64" → "Titanium alloy, Ti-6Al-4V"
  * "Power" → "Electricity"
  * "Waste supports" → "Waste metal, Ti-6Al-4V"

### 2. Note Field (Context for Filtering)
- **Purpose**: Capture characteristics that matter for LCA analysis
- **Strategy**:
  * Extract key information from source text
  * Include details that affect environmental impact
  * No need to repeat what's already in Name
  
- **Examples**:
  * "Powder, gas atomized, Grade 23"
  * "Low voltage, from grid mix"
  * "Support structures, to sanitary landfill"

## Key Principles
- Don't invent information not in the source
- Standard terms over brand names or abbreviations
- Clarity over brevity (use as many words as needed)
- For waste flows: Keep "Waste" or "Scrap" prefix in Name (to distinguish from inputs/products)

## Output Format
Return ONLY a JSON object with two fields:
{
  "improved_name": "...",
  "improved_note": "..."
}

**Important**: Do NOT include any other fields like "改进说明" or "explanation".
"""
    
    def improve_functional_unit(self, description: str, selected_chunk: Dict[str, Any]) -> str:
        """
        改进 Functional Unit 描述
        
        Args:
            description: 原始 FU 描述
            selected_chunk: 来源文本块
            
        Returns:
            改进后的描述
        """
        try:
            # 构建用户消息
            user_msg = f"""Refine this Functional Unit description to be more precise and professional:

Original: "{description}"

Source context:
{selected_chunk.get('content', '')[:500]}

Return ONLY the improved description (one clear sentence), start directly with the content, no JSON, no explanation."""
            
            # 调用 CAMEL AI
            response = self.agent.step(user_msg)
            improved = response.msg.content.strip()
            
            # 清理可能的引号
            improved = improved.strip('"').strip("'")
            
            return improved if improved else description
            
        except Exception as e:
            print(f"    ⚠️ FU 改进失败: {str(e)}")
            return description
    
    def improve_flow(self, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        改进单个 flow 的 name 和 note
        
        Args:
            flow_data: 包含 name, note, selected_chunk, category, flow_type 的字典
            
        Returns:
            改进后的数据，包含 improved_name, improved_note, 改进说明
        """
        # 构建提示词
        prompt = f"""Please improve the following LCI flow record:

**Current Record**:
- Name: "{flow_data.get('name', '')}"
- Note: "{flow_data.get('note', '')}"
- Category: {flow_data.get('category', 'Unknown')}
- Flow Type: {flow_data.get('flow_type', 'Unknown')}

**Source Data** (selected_chunk):
```
{flow_data.get('selected_chunk', {}).get('content', '')[:500]}
```

Provide improved name and note following the principles above."""

        try:
            user_msg = BaseMessage.make_user_message(
                role_name="User",
                content=prompt
            )
            
            response = self.agent.step(user_msg)
            content = response.msg.content
            
            # 解析 JSON 响应
            # 尝试提取 JSON 块
            import re
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析
                json_str = content
            
            result = json.loads(json_str)
            return result
            
        except Exception as e:
            print(f"⚠️ 改进失败: {str(e)}")
            # 返回原始数据（仅清理空格）
            return {
                "improved_name": flow_data.get('name', '').strip(),
                "improved_note": flow_data.get('note', '')
            }
    
    def process_training_data(self, input_file: str, output_file: str):
        """
        处理训练数据文件，改进所有 flow 记录的 name 和 note
        
        Args:
            input_file: 输入 JSON 文件路径
            output_file: 输出 JSON 文件路径
        """
        print(f"📖 读取训练数据: {input_file}")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        total_samples = len(data)
        print(f"📊 总样本数: {total_samples}")
        
        improved_count = 0
        
        for sample_idx, sample in enumerate(data, 1):
            print(f"\n处理样本 {sample_idx}/{total_samples}")
            
            messages = sample.get('messages', [])
            
            for msg_idx, msg in enumerate(messages):
                if msg.get('role') != 'assistant':
                    continue
                
                tool_calls = msg.get('tool_calls', [])
                for tool_call in tool_calls:
                    tool_name = tool_call.get('name')
                    
                    # 处理 Functional Unit
                    if tool_name == 'define_lca_scope':
                        args = tool_call.get('arguments', {})
                        if args.get('parameter_name') == 'Function Unit':
                            old_desc = args.get('description', '')
                            if old_desc:
                                print(f"  🎯 改进 Functional Unit: {old_desc[:50]}...")
                                improved_desc = self.improve_functional_unit(old_desc, args.get('selected_chunk', {}))
                                args['description'] = improved_desc
                                improved_count += 1
                                if old_desc != improved_desc:
                                    print(f"    ✅ {old_desc} → {improved_desc}")
                                else:
                                    print(f"    ✅ (unchanged)")
                        continue
                    
                    # 处理 Process Flow
                    if tool_name != 'record_process_flow':
                        continue
                    
                    args = tool_call.get('arguments', {})
                    
                    # 跳过 Product 类型（不改进产品名称）
                    if args.get('category') == 'Product':
                        print(f"  ⏭️  跳过 Product: {args.get('name', '')} (保持原样)")
                        continue
                    
                    # 准备改进数据
                    flow_data = {
                        'name': args.get('name', ''),
                        'note': args.get('note', ''),
                        'selected_chunk': args.get('selected_chunk', {}),
                        'category': args.get('category', ''),
                        'flow_type': args.get('flow_type', '')
                    }
                    
                    print(f"  🔧 改进 flow: {flow_data['name']}")
                    
                    # 调用 CAMEL AI 改进
                    improved = self.improve_flow(flow_data)
                    
                    # 更新数据（直接修改原始数据）
                    old_name = args['name']
                    old_note = args.get('note', '')
                    
                    args['name'] = improved['improved_name']
                    args['note'] = improved['improved_note']
                    
                    improved_count += 1
                    
                    # 显示改进信息
                    if old_name != improved['improved_name']:
                        print(f"    ✅ Name: {old_name} → {improved['improved_name']}")
                    else:
                        print(f"    ✅ Name: {improved['improved_name']} (unchanged)")
                    
                    if old_note != improved['improved_note']:
                        print(f"    📝 Note: {old_note} → {improved['improved_note']}")
                    elif improved['improved_note']:
                        print(f"    📝 Note: {improved['improved_note']} (unchanged)")
        
        # 保存改进后的数据
        print(f"\n💾 保存改进后的数据: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 完成！共改进 {improved_count} 个 flow 记录")


def main():
    parser = argparse.ArgumentParser(description='使用 CAMEL AI 改进训练数据的 name 和 note 字段')
    parser.add_argument('--input', required=True, help='输入 JSON 文件路径')
    parser.add_argument('--output', help='输出 JSON 文件路径（可选，默认覆盖输入文件）')
    parser.add_argument('--api-key', help='DeepSeek API Key（可选，默认从环境变量读取）')
    parser.add_argument('--model', default='deepseek-chat', help='模型名称（默认: deepseek-chat）')
    
    args = parser.parse_args()
    
    # 获取 API Key
    api_key = args.api_key or os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        print("❌ 错误: 未提供 API Key")
        print("请通过 --api-key 参数或 DEEPSEEK_API_KEY 环境变量提供")
        sys.exit(1)
    
    # 确定输出文件（默认覆盖输入文件）
    output_file = args.output if args.output else args.input
    
    if not args.output:
        print(f"⚠️  未指定 --output，将直接修改输入文件: {args.input}")
        confirm = input("确认继续？(y/N): ")
        if confirm.lower() != 'y':
            print("已取消")
            sys.exit(0)
    
    # 创建改进器
    improver = NameNoteImprover(api_key=api_key, model_name=args.model)
    
    # 处理数据
    improver.process_training_data(args.input, output_file)


if __name__ == '__main__':
    main()
