#!/usr/bin/env python3
"""
短对话 Reasoning 生成器 (v4.5)

功能：
1. 为短对话数据集生成 reasoning_content（使用 CAMEL AI）
2. 生成自然的 user content（区分 QA 和 Extract 场景）
3. 使用 Full 版本的 reasoning_helpers（完整上下文）
4. 支持 final response 生成（区分 QA/Extract）
5. 支持 QA 格式转换（--convert-to-qa）

改进：
- v4.5: 修复 QA final response 生成，区分 QA/Extract prompt
- v4.4: 添加 --convert-to-qa 参数，支持输出时格式转换
- v4.3: 改进 QA 场景的 user content 生成，使用 CAMEL AI 生成自然问题
- v4.2: 使用 CAMEL AI 生成自然的 user content，扫描所有 record 操作

作者：AI Assistant
日期：2025-11-30
"""

import json
import sys
import os
from pathlib import Path
from typing import List, Dict
import argparse

# CAMEL AI imports
try:
    from camel.agents import ChatAgent
    from camel.messages import BaseMessage
    from camel.models import OpenAIModel
    from camel.configs.openai_config import ChatGPTConfig
except ImportError:
    print("❌ CAMEL AI 未安装。请运行: pip install camel-ai")
    sys.exit(1)

# 导入 Full 版本的辅助函数
from reasoning_helpers import (
    summarize_tool_response,
    describe_next_action,
    build_conversation_history,
    build_dynamic_prompt
)


class ShortReasoningGenerator:
    """短对话 Reasoning 生成器 v4.5（CAMEL AI 自然生成 + QA/Extract 区分）"""
    
    def __init__(self, model_name: str = "deepseek-chat", temperature: float = 1.0, api_key: str = None):
        """
        初始化生成器
        
        Args:
            model_name: 模型名称
            temperature: 温度参数
            api_key: DeepSeek API Key
        """
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("❌ 未提供 API Key。请通过 --api-key 参数或 DEEPSEEK_API_KEY 环境变量提供。")
        
        # 配置 CAMEL AI
        os.environ["OPENAI_API_KEY"] = self.api_key
        os.environ["OPENAI_API_BASE_URL"] = "https://api.deepseek.com"
        
        config = ChatGPTConfig(
            temperature=temperature,
            max_tokens=2048
        )
        
        model_config = {
            "model_type": model_name,
            "model_config_dict": config.as_dict(),
            "api_key": self.api_key,
            "url": "https://api.deepseek.com"
        }
        
        # 创建 reasoning 生成 agent（带记忆）
        self.reasoning_agent = ChatAgent(
            system_message=BaseMessage.make_assistant_message(
                role_name="Assistant",
                content=self._get_reasoning_system_prompt()
            ),
            model=OpenAIModel(**model_config)
        )
        
        print("\n" + "="*60)
        print("短对话 Reasoning 生成器 (v4.5)")
        print("="*60)
        print("\n功能：")
        print("  1. 使用 CAMEL AI 生成自然的 user content")
        print("  2. 区分 QA（询问）和 Extract（提取）场景")
        print("  3. 使用 Full 版本的 reasoning_helpers")
        print("  4. 支持 QA 格式转换（--convert-to-qa）")
        print("="*60 + "\n")
        print(f"🚀 初始化短对话 Reasoning Generator v4.5...")
        print(f"💬 使用模型: {model_name}")
        print(f"🌡️  温度: {temperature}")
        print(f"📊 使用 Full 版本的 reasoning_helpers（完整上下文）")
        print(f"✨ 使用 CAMEL AI 生成自然的 user content")
    
    def _get_reasoning_system_prompt(self) -> str:
        """获取 reasoning 生成的 system prompt（v4.0 - 简洁版，对齐 Full）"""
        return """You are an LCA expert performing LCI data extraction from documents.

## Your Role
Generate first-person reasoning for short extraction tasks. You have access to FULL context.

## LCI Categories (11 types)
**Input**: Raw Material, Process Energy, Post-processing Energy, Feedstock Energy, Gas, Cooling Media
**Output**: Product, Recovered Material, Waste, Emission
**Scope**: Functional Unit

## Key Principles
1. **First-person perspective**: Write as if you are performing the extraction
2. **Natural thinking**: Think out loud, vary your expression
3. **Context-aware**: Reference previous actions and search results
4. **Honest**: Express uncertainty or confidence naturally

## Energy Classification
- **Process Energy**: Printing/machine operation (e.g., SLM system)
- **Post-processing Energy**: Heat treatment, machining after printing
- **Feedstock Energy**: Powder production (e.g., atomization)

Generate only the reasoning content, no tags or labels."""
    
    def generate_user_content_from_search_queries(self, messages: List[Dict]) -> str:
        """
        使用 CAMEL AI 生成自然的 user content
        
        原则：
        1. 用户看到文档提到了某些数据（如 electricity, argon）
        2. 用户不知道具体分类（Process Energy vs Post-processing Energy）
        3. 用户不知道有几个（可能 argon 有 2 个，但用户只说"argon"）
        4. 用户的请求应该是泛化的、自然的
        
        Args:
            messages: messages 数组
            
        Returns:
            生成的 user content
        """
        # 🔥 扫描所有 record 操作，收集数据名称（去重）
        recorded_names = set()
        
        for msg in messages:
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                tool_calls = msg["tool_calls"]
                if isinstance(tool_calls, list):
                    for tool_call in tool_calls:
                        tool_name = tool_call.get("name")
                        args = tool_call.get("arguments", {})
                        
                        if tool_name == "record_process_flow":
                            name = args.get("name", "")
                            if name:
                                recorded_names.add(name.lower())
                        
                        elif tool_name == "define_lca_scope":
                            recorded_names.add("functional unit")
        
        # 根据记录的数据生成 user content
        if recorded_names:
            # 有 record 操作：让 CAMEL AI 生成自然的请求
            names_list = sorted(list(recorded_names))
            
            if "functional unit" in names_list:
                context = "identifying the functional unit"
            elif len(names_list) == 1:
                context = f"extracting {names_list[0]} data"
            else:
                names_str = ", ".join(names_list)
                context = f"extracting data about {names_str}"
            
            # 使用 CAMEL AI 生成自然的 user content
            prompt = f"""Generate a natural, conversational user request for {context}.

Requirements:
1. Natural and conversational tone
2. DO NOT mention specific values, categories, or technical classifications
3. Keep it simple and direct
4. Use question format or polite request format

Generate ONE natural request (15-30 words):"""
            
            try:
                user_msg = BaseMessage.make_user_message(role_name="User", content=prompt)
                response = self.reasoning_agent.step(user_msg)
                user_content = response.msg.content.strip().strip('"').strip("'")
                # 清空记忆（避免影响后续 reasoning 生成）
                self.reasoning_agent.clear_memory()
                return user_content
            except Exception as e:
                print(f"  ⚠️  生成 user content 失败: {e}")
                # 回退到简单模板
                if "functional unit" in names_list:
                    return "Can you help me identify the functional unit from this document?"
                elif len(names_list) == 1:
                    return f"Please help me extract the {names_list[0]} data."
                else:
                    names_str = " and ".join(names_list)
                    return f"Can you help me extract data about {names_str}?"
        
        else:
            # 没有 record（QA 场景）：基于 search queries，使用 CAMEL AI 生成自然问题
            first_search_queries = []
            for msg in messages:
                if msg.get("role") == "assistant" and msg.get("tool_calls"):
                    for tc in msg["tool_calls"]:
                        if tc.get("name") == "search_document":
                            # 支持 queries 或 query
                            args = tc.get("arguments", {})
                            queries = args.get("queries", [])
                            if not queries and args.get("query"):
                                queries = [args.get("query")]
                            if queries:
                                first_search_queries = queries
                                break
                    if first_search_queries:
                        break
            
            if not first_search_queries:
                return "Please help me find LCI data from this document."
            
            # 🔥 NEW: QA 场景使用 CAMEL AI 生成自然的问题
            # 将 search queries 转换为主题描述
            topics = []
            for q in first_search_queries[:3]:  # 最多 3 个
                if isinstance(q, str):
                    topics.append(q.lower())
            
            topics_str = ", ".join(topics)
            
            # 使用 CAMEL AI 生成自然的问题
            prompt = f"""Generate a natural, conversational question asking about {topics_str} in a manufacturing process.

Requirements:
1. Use question format 
2. Natural and conversational tone
3. DO NOT mention specific values or technical terms
4. Keep it simple and direct (15-25 words)
5. Focus on ASKING, not EXTRACTING

Generate ONE natural question:"""
            
            try:
                user_msg = BaseMessage.make_user_message(role_name="User", content=prompt)
                response = self.reasoning_agent.step(user_msg)
                user_content = response.msg.content.strip().strip('"').strip("'")
                # 清空记忆
                self.reasoning_agent.clear_memory()
                return user_content
            except Exception as e:
                print(f"  ⚠️  生成 QA user content 失败: {e}")
                # 回退到简单模板
                return f"What information can you find about {topics_str}?"
    
    def _extract_previous_actions(self, previous_messages: List[Dict]) -> List[str]:
        """
        从历史消息中提取已执行的动作（用于上下文连续性）
        
        Args:
            previous_messages: 当前位置之前的所有 messages
            
        Returns:
            动作描述列表
        """
        actions = []
        
        for msg in previous_messages:
            if msg.get("role") == "assistant":
                tool_calls = msg.get("tool_calls", [])
                if tool_calls:
                    for tc in tool_calls:
                        tool_name = tc.get("name")
                        args = tc.get("arguments", {})
                        
                        if tool_name == "search_document":
                            queries = args.get("queries", [])
                            actions.append(f"Searched for: {', '.join(queries)}")
                        elif tool_name == "record_process_flow":
                            category = args.get("category", "")
                            name = args.get("name", "")
                            actions.append(f"Recorded {category}: {name}")
                        elif tool_name == "define_lca_scope":
                            param = args.get("parameter_name", "")
                            actions.append(f"Defined scope: {param}")
                        elif tool_name == "record_parameter":
                            param = args.get("parameter_name", "")
                            actions.append(f"Recorded parameter: {param}")
                        elif tool_name == "execute_calculation":
                            actions.append("Executed calculation")
        
        return actions
    
    def convert_to_qa_format(self, sample: Dict) -> Dict:
        """
        将 Extract 格式转换为 QA 格式（删除 record tool calls）
        
        仅在输出时转换，不影响 CAMEL AI 的生成过程
        
        Args:
            sample: 包含 messages 的 sample
            
        Returns:
            转换后的 sample（QA 格式）
        """
        messages = sample.get("messages", [])
        converted_messages = []
        skip_next_tool = False
        
        for i, msg in enumerate(messages):
            if msg.get("role") == "assistant":
                tool_calls = msg.get("tool_calls", [])
                
                if tool_calls:
                    # 过滤掉 record 相关的 tool calls
                    filtered_calls = []
                    has_record = False
                    
                    for tc in tool_calls:
                        tool_name = tc.get("name")
                        if tool_name in ["record_process_flow", "define_lca_scope", "execute_calculation", "record_parameter"]:
                            has_record = True
                        else:
                            filtered_calls.append(tc)
                    
                    if filtered_calls:
                        # 保留非 record 的 tool calls
                        msg_copy = msg.copy()
                        msg_copy["tool_calls"] = filtered_calls
                        converted_messages.append(msg_copy)
                    elif has_record:
                        # 全是 record，跳过这条消息和下一条 tool response
                        skip_next_tool = True
                        continue
                else:
                    # 没有 tool calls 的 assistant 消息（最终回复）
                    converted_messages.append(msg.copy())
            
            elif msg.get("role") == "tool":
                if skip_next_tool:
                    skip_next_tool = False
                    continue
                else:
                    converted_messages.append(msg.copy())
            
            else:
                converted_messages.append(msg.copy())
        
        return {"messages": converted_messages}
    
    def generate_reasoning_for_sample(self, sample: Dict, is_qa_mode: bool = False) -> Dict:
        """
        为整个 sample 生成 reasoning（带记忆）
        
        Args:
            sample: 包含 messages 的 sample
            is_qa_mode: 是否是 QA 模式（用于区分 final response 的生成）
            
        Returns:
            填充了 reasoning_content 的 sample
        """
        messages = sample.get("messages", [])
        
        # 🔥 清空记忆（每个 sample 独立）
        self.reasoning_agent.clear_memory()
        
        # 遍历每个 assistant 消息
        for i, msg in enumerate(messages):
            if msg.get("role") != "assistant":
                continue
            
            tool_calls = msg.get("tool_calls", [])
            
            # 🔥 检测最终回复场景：assistant消息但没有tool_calls
            is_final_response = (not tool_calls) and (i > 0)
            
            if not tool_calls and not is_final_response:
                continue
            
            # 提取前面的对话历史
            previous_messages = messages[:i]
            
            # 🔥 处理最终回复（区分 QA/Extract）
            if is_final_response:
                try:
                    # 构建总结 prompt
                    from reasoning_helpers import build_conversation_history
                    history_text = build_conversation_history(previous_messages)
                    
                    # 🔥 使用 is_qa_mode 参数判断场景
                    if not is_qa_mode:
                        # Extract 场景：强调记录
                        prompt = f"""You have completed a short data extraction task. Generate:
1. **Reasoning** (internal thinking): Reflect on what you accomplished
2. **Response** (user-facing): A natural confirmation message

## Conversation So Far:
{history_text}

**Format**:
[Your internal reasoning] ||| [Your response to user]

**Remember**:
- Reasoning: First person, natural
- Response: Professional confirmation (mention "recorded" or "extracted")
- Must include "|||" separator

Generate your output:"""
                    else:
                        # QA 场景：强调回答
                        prompt = f"""You have answered a user's question about LCI data. Generate:
1. **Reasoning** (internal thinking): Explain how you found the answer
2. **Response** (user-facing): A direct, informative answer with specific data

## Conversation So Far:
{history_text}

**Format**:
[Your internal reasoning] ||| [Your answer to user]

**Remember**:
- Reasoning: First person, explain your search and findings
- Response: Direct answer with specific data (DO NOT mention "recording" or "extracting")
- Focus on providing information, not on the process
- Must include "|||" separator

Generate your output:"""
                    
                    user_msg = BaseMessage.make_user_message(
                        role_name="User",
                        content=prompt
                    )
                    
                    response = self.reasoning_agent.step(user_msg)
                    result = response.msg.content.strip()
                    result = result.replace("<think>", "").replace("</think>", "").strip()
                    
                    # 分割 reasoning 和 content
                    if "|||" in result:
                        parts = result.split("|||")
                        msg["reasoning_content"] = parts[0].strip()
                        msg["content"] = parts[1].strip() if len(parts) > 1 else "I have completed the data extraction."
                    else:
                        # 如果没有分隔符，使用默认值
                        msg["reasoning_content"] = result
                        msg["content"] = "I have completed the data extraction."
                    
                    print(f"  ✓ 生成 final response")
                    
                except Exception as e:
                    print(f"  ⚠️  生成 final response 失败: {e}")
                    msg["reasoning_content"] = "[生成失败]"
                    msg["content"] = "[生成失败]"
                continue
            
            # 🔥 使用 Full 版本的动态 Prompt（完整信息）
            # 提取 user query
            user_query = ""
            for prev_msg in previous_messages:
                if prev_msg.get("role") == "user":
                    user_query = prev_msg.get("content", "")
                    break
            
            # 使用 reasoning_helpers 的 build_dynamic_prompt
            prompt = build_dynamic_prompt(
                previous_messages=previous_messages,
                current_tool_call=tool_calls[0],
                user_query=user_query
            )
            
            # 生成 reasoning
            try:
                user_msg = BaseMessage.make_user_message(
                    role_name="User",
                    content=prompt
                )
                
                # 🔥 Agent 自动记住这次对话
                response = self.reasoning_agent.step(user_msg)
                reasoning = response.msg.content.strip()
                
                # 清理格式
                reasoning = reasoning.replace("<think>", "").replace("</think>", "").strip()
                
                # 填充 reasoning_content
                msg["reasoning_content"] = reasoning
                
                print(f"  ✓ 生成 reasoning: {reasoning[:80]}...")
                
            except Exception as e:
                print(f"  ⚠️  生成 final response 失败: {e}")
                msg["reasoning_content"] = "[生成失败]"
                msg["content"] = "[生成失败]"
                continue
        
        return sample
    
    def process_file(self, input_path: str, output_path: str, convert_to_qa: bool = False):
        """
        处理整个文件
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            convert_to_qa: 是否转换为 QA 格式（删除 record tool calls）
        """
        print(f"\n📂 读取输入文件: {input_path}")
        
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            data = [data]
        
        print(f"📊 共 {len(data)} 个样本")
        
        # 处理每个样本
        results = []
        for idx, sample in enumerate(data):
            print(f"\n{'='*60}")
            print(f"处理样本 {idx+1}/{len(data)}")
            print(f"{'='*60}")
            
            messages = sample.get("messages", [])
            
            # 1. 生成 user content（从第一次 search 的 queries 反推）
            print("\n📝 生成 user content...")
            user_content = self.generate_user_content_from_search_queries(messages)
            print(f"  ✓ User content: {user_content}")
            
            # 填充 user content
            for msg in messages:
                if msg.get("role") == "user" and msg.get("content") == "":
                    msg["content"] = user_content
                    break
            
            # 2. 生成 reasoning（带记忆）
            print("\n🧠 生成 reasoning...")
            # 🔥 传入 convert_to_qa 参数，用于区分 final response 生成
            sample = self.generate_reasoning_for_sample(sample, is_qa_mode=convert_to_qa)
            
            # 3. 🔥 如果需要，转换为 QA 格式（仅在输出时）
            if convert_to_qa:
                print("\n🔄 转换为 QA 格式（删除 record tool calls）...")
                sample = self.convert_to_qa_format(sample)
                print("  ✓ 已转换为 QA 格式")
            
            results.append(sample)
        
        # 保存结果
        print(f"\n💾 保存结果到: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 完成！")


def main():
    parser = argparse.ArgumentParser(description="短对话 Reasoning 生成器 v4.5（CAMEL AI 自然生成 + QA/Extract 区分 + QA 格式转换）")
    parser.add_argument("--input", required=True, help="输入文件路径")
    parser.add_argument("--output", required=True, help="输出文件路径")
    parser.add_argument("--api-key", help="DeepSeek API Key")
    parser.add_argument("--model", default="deepseek-chat", help="模型名称")
    parser.add_argument("--temperature", type=float, default=1.0, help="温度参数")
    parser.add_argument("--convert-to-qa", action="store_true", help="转换为 QA 格式（删除 record tool calls）")
    
    args = parser.parse_args()
    
    # 创建生成器
    generator = ShortReasoningGenerator(
        model_name=args.model,
        temperature=args.temperature,
        api_key=args.api_key
    )
    
    # 处理文件
    generator.process_file(args.input, args.output, convert_to_qa=args.convert_to_qa)


if __name__ == "__main__":
    main()
