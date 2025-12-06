#!/usr/bin/env python3
"""
短对话 Reasoning 生成器 (v5.0)

功能：
1. 为短对话数据集生成 reasoning_content（使用 CAMEL AI）
2. 生成自然的 user content（区分 QA 和 Extract 场景）
3. 使用 Full 版本的 reasoning_helpers（完整上下文）
4. 支持 final response 生成（区分 QA/Extract）
5. 支持 QA 格式转换（--convert-to-qa）
6. 🔥 支持 not_found / smart_skip / pivot 等特殊场景

改进：
- v5.0: 补充 not_found / smart_skip / pivot 场景处理，对齐 Full 版本
- v4.7: 简化 prompt，删除具体动词列表，只保留意图引导（Less is More）
- v4.6: 明确区分 Extract/QA 的 user content 动词（extract vs ask）
- v4.5: 修复 QA final response 生成，区分 QA/Extract prompt
- v4.4: 添加 --convert-to-qa 参数，支持输出时格式转换
- v4.3: 改进 QA 场景的 user content 生成，使用 CAMEL AI 生成自然问题
- v4.2: 使用 CAMEL AI 生成自然的 user content，扫描所有 record 操作

作者：AI Assistant
日期：2025-12-04
"""

import json
import sys
import os
import re
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
    """短对话 Reasoning 生成器 v4.7（CAMEL AI 自然生成 + QA/Extract 区分）"""
    
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
        print("短对话 Reasoning 生成器 (v5.0)")
        print("="*60)
        print("\n功能：")
        print("  1. 使用 CAMEL AI 生成自然的 user content")
        print("  2. 区分 QA（询问）和 Extract（提取）场景")
        print("  3. 使用 Full 版本的 reasoning_helpers")
        print("  4. 支持 QA 格式转换（--convert-to-qa）")
        print("  5. 🔥 支持 not_found / smart_skip / pivot 场景")
        print("="*60 + "\n")
        print(f"🚀 初始化短对话 Reasoning Generator v5.0...")
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
    
    def generate_user_content_from_search_queries(self, messages: List[Dict], is_qa_mode: bool = False) -> str:
        """
        使用 CAMEL AI 基于对话行为模式生成自然的 user content
        
        方案 A：让 LLM 看到整个对话的行为序列，自己推断用户意图
        """
        # 🔥 构建行为摘要（精简版）
        action_summary = []
        has_record = False
        
        for msg in messages:
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    tool_name = tc.get("name")
                    args = tc.get("arguments", {})
                    
                    if tool_name == "search_document":
                        queries = args.get("queries", [])
                        action_summary.append(f"Search: {', '.join(queries)}")
                    elif tool_name == "record_process_flow":
                        has_record = True
                        category = args.get("category", "unknown")
                        action_summary.append(f"Record: {category}")
                    elif tool_name == "define_lca_scope":
                        has_record = True
                        action_summary.append("Record: Functional Unit")
                    elif tool_name == "execute_calculation":
                        action_summary.append("Calculate")
        
        if not action_summary:
            return "What LCI data can you find in this document?"
        
        actions_text = "\n".join(f"- {a}" for a in action_summary)
        
        # 根据模式选择 prompt
        if has_record and not is_qa_mode:
            # Extract 模式
            prompt = f"""Based on these assistant actions, generate a natural user request that would trigger them:

{actions_text}

Guidelines:
- User wants to EXTRACT/RECORD data (not just ask questions)
- Natural and conversational (10-20 words)
- Do NOT mention specific values or exact names from the actions

Output ONLY the user request:"""
        else:
            # QA 模式
            prompt = f"""Based on these assistant actions, generate a natural user question that would trigger them:

{actions_text}

Guidelines:
- User wants to ASK about information (not extract/record)
- Natural and conversational (10-20 words)
- Do NOT mention specific values or exact names from the actions

Output ONLY the user question:"""
        
        try:
            user_msg = BaseMessage.make_user_message(role_name="User", content=prompt)
            response = self.reasoning_agent.step(user_msg)
            user_content = response.msg.content.strip().strip('"').strip("'")
            self.reasoning_agent.clear_memory()
            return user_content
        except Exception as e:
            print(f"  ⚠️  生成 user content 失败: {e}")
            # 回退模板
            if has_record and not is_qa_mode:
                return "Can you help me extract the relevant LCI data from this document?"
            else:
                return "What can you tell me about the process data in this document?"
    
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
    
    def _detect_not_found_scenario(self, previous_messages: List[Dict], user_query: str) -> bool:
        """
        检测是否为 not_found 场景：搜索结果中没有用户要的数据
        
        Args:
            previous_messages: 当前位置之前的所有 messages
            user_query: 用户的原始请求
            
        Returns:
            是否为 not_found 场景
        """
        if not previous_messages:
            return False
        
        # 找到最后一个 tool response
        last_tool_msg = None
        last_search_queries = []
        
        for i in range(len(previous_messages) - 1, -1, -1):
            msg = previous_messages[i]
            if msg.get("role") == "tool":
                last_tool_msg = msg
                # 找到对应的 search_document 调用
                if i > 0 and previous_messages[i-1].get("role") == "assistant":
                    tool_calls = previous_messages[i-1].get("tool_calls", [])
                    if tool_calls and tool_calls[0].get("name") == "search_document":
                        args = tool_calls[0].get("arguments", {})
                        last_search_queries = args.get("queries", args.get("query", []))
                        if isinstance(last_search_queries, str):
                            last_search_queries = [last_search_queries]
                break
        
        if not last_tool_msg or not last_search_queries:
            return False
        
        # 检查搜索结果是否包含用户要的数据
        tool_content = last_tool_msg.get("content", "")
        
        # 提取用户请求中的关键词（简单启发式）
        user_keywords = []
        for kw in ["emission", "particulate", "dust", "waste", "gas", "energy", "material", "product"]:
            if kw.lower() in user_query.lower():
                user_keywords.append(kw)
        
        # 如果搜索的是 emission/particulate/dust，但结果中没有这些词
        search_for_emissions = any(q.lower() in ["emission", "particulate", "dust", "voc", "volatile"] 
                                   for q in last_search_queries)
        
        if search_for_emissions:
            # 检查结果中是否真的有 emission 数据
            has_emission_data = any(kw in tool_content.lower() 
                                    for kw in ["emission", "particulate", "dust", "voc", "co2", "nox"])
            if not has_emission_data:
                return True
        
        return False
    
    def _extract_search_results_from_tool_message(self, tool_msg: Dict) -> List[Dict]:
        """
        从 tool 消息中提取搜索结果
        
        Args:
            tool_msg: tool role 的消息
            
        Returns:
            搜索结果列表
        """
        content = tool_msg.get("content", "")
        
        # 提取 <tool_response> 标签内的 JSON
        match = re.search(r'<tool_response>\s*(\{.*?\})\s*</tool_response>', content, re.DOTALL)
        if match:
            try:
                response_data = json.loads(match.group(1))
                return response_data.get("results", [])
            except:
                pass
        
        return []

    def generate_reasoning_for_sample(self, sample: Dict, is_qa_mode: bool = False) -> Dict:
        """
        为整个 sample 生成 reasoning（带记忆）
        
        v5.0: 支持 not_found / smart_skip / pivot 等特殊场景
        
        Args:
            sample: 包含 messages 的 sample
            is_qa_mode: 是否是 QA 模式（用于区分 final response 的生成）
            
        Returns:
            填充了 reasoning_content 的 sample
        """
        messages = sample.get("messages", [])
        
        # 🔥 清空记忆（每个 sample 独立）
        self.reasoning_agent.clear_memory()
        
        # 提取 user query（用于后续场景检测）
        user_query = ""
        for msg in messages:
            if msg.get("role") == "user":
                user_query = msg.get("content", "")
                break
        
        # 遍历每个 assistant 消息
        for i, msg in enumerate(messages):
            if msg.get("role") != "assistant":
                continue
            
            tool_calls = msg.get("tool_calls", [])
            existing_reasoning = msg.get("reasoning_content", "")
            
            # 🔥 检测 Smart Skip 场景：reasoning_content 包含 SMART_SKIP_PLACEHOLDER
            has_smart_skip_placeholder = "SMART_SKIP_PLACEHOLDER" in existing_reasoning
            
            # 🔥 区分两种 Smart Skip 场景：
            # 1. 纯 Smart Skip：有 placeholder，没有 tool_calls
            # 2. Smart Skip + Search：有 placeholder，有 search_document tool_call
            is_smart_skip_pure = has_smart_skip_placeholder and (not tool_calls or len(tool_calls) == 0)
            is_smart_skip_with_search = (has_smart_skip_placeholder and 
                                         tool_calls and len(tool_calls) > 0 and 
                                         tool_calls[0].get("name") == "search_document")
            
            # 🔥 检测最终回复场景：assistant消息但没有tool_calls
            is_final_response = (not tool_calls) and (i > 0) and (not is_smart_skip_pure)
            
            # 🔥 修复：允许 smart skip 消息（即使没有 tool_calls）
            if not tool_calls and not is_final_response and not is_smart_skip_pure:
                continue
            
            # 提取前面的对话历史
            previous_messages = messages[:i]
            
            # 🔥 检测是否为 Pivot 场景：search_document 后紧接着另一个 search_document
            is_pivot_scenario = False
            prev_search_results = []
            current_tool = tool_calls[0].get("name") if tool_calls else None
            
            if current_tool == "search_document" and i >= 2 and not is_smart_skip_with_search:
                prev_msg = messages[i-1]
                prev_prev_msg = messages[i-2]
                if (prev_msg.get("role") == "tool" and 
                    prev_prev_msg.get("role") == "assistant" and
                    prev_prev_msg.get("tool_calls", [{}])[0].get("name") == "search_document"):
                    is_pivot_scenario = True
                    prev_search_results = self._extract_search_results_from_tool_message(prev_msg)
            
            # 🔥 检测 not_found 场景（用于 final response）
            is_not_found = False
            if is_final_response:
                is_not_found = self._detect_not_found_scenario(previous_messages, user_query)
            
            # 构建 prompt
            from reasoning_helpers import build_conversation_history
            history_text = build_conversation_history(previous_messages)
            
            # ==================== 场景分支处理 ====================
            
            if is_smart_skip_with_search:
                # 🔥 Smart Skip + Search 场景
                match = re.search(r'\[SMART_SKIP_PLACEHOLDER: (.*?) - (.*?)\]', existing_reasoning)
                if match:
                    skip_category = match.group(1)
                    skip_reason = match.group(2)
                else:
                    skip_category = "Unknown"
                    skip_reason = "already_recorded"
                
                next_search_queries = tool_calls[0].get("arguments", {}).get("queries", [])
                reason_text = "not found in the document" if skip_reason == "not_found" else "already recorded earlier"
                
                prompt = f"""You are an LCA expert performing LCI data extraction.

## Conversation So Far:
{history_text}

## Your Decision:
1. Skip recording {skip_category} ({reason_text})
2. Then search for: {', '.join(next_search_queries)}

## Your Task:
Generate your reasoning explaining:
1. Why you're skipping {skip_category}
2. Why you're moving on to search for the next category

**Remember**:
- Write in first person
- Be concise and natural
- Combine both decisions in one reasoning

Generate only the reasoning:"""
                
                try:
                    user_msg = BaseMessage.make_user_message(role_name="User", content=prompt)
                    response = self.reasoning_agent.step(user_msg)
                    reasoning = response.msg.content.strip().replace("<think>", "").replace("</think>", "").strip()
                    msg["reasoning_content"] = reasoning
                    print(f"  ✓ 生成 smart_skip+search reasoning: {reasoning[:80]}...")
                except Exception as e:
                    print(f"  ⚠️  生成 smart_skip+search reasoning 失败: {e}")
                    msg["reasoning_content"] = f"Skipping {skip_category} and moving to next search."
                continue
            
            elif is_smart_skip_pure:
                # 🔥 纯 Smart Skip 场景（这也是一个 final response，因为没有后续 tool_calls）
                match = re.search(r'\[SMART_SKIP_PLACEHOLDER: (.*?) - (.*?)\]', existing_reasoning)
                if match:
                    skip_category = match.group(1)
                    skip_reason = match.group(2)
                else:
                    skip_category = "Unknown"
                    skip_reason = "already_recorded"
                
                reason_text = "not found in the document" if skip_reason == "not_found" else "already recorded earlier"
                is_not_found_skip = (skip_reason == "not_found")
                
                # 🔥 修复：smart_skip_pure 也需要生成 content（用户可见的回复）
                prompt = f"""You are an LCA expert performing LCI data extraction.

## Conversation So Far:
{history_text}

## Your Decision:
Skip recording {skip_category} ({reason_text})

## Your Task:
Generate TWO parts separated by "|||":
1. **Reasoning** (internal thinking): Explain why you're skipping this category
2. **Response** (user-facing): Tell the user what you found (or didn't find)

**Format**:
[Your internal reasoning] ||| [Your response to user]

**Remember**:
- Reasoning: First person, explain the skip reason
- Response: Be honest about what was/wasn't found
- Must include "|||" separator

Generate your output:"""
                
                try:
                    user_msg = BaseMessage.make_user_message(role_name="User", content=prompt)
                    response = self.reasoning_agent.step(user_msg)
                    result = response.msg.content.strip().replace("<think>", "").replace("</think>", "").strip()
                    
                    # 🔥 分割 reasoning 和 content
                    if "|||" in result:
                        parts = result.split("|||")
                        msg["reasoning_content"] = parts[0].strip()
                        msg["content"] = parts[1].strip() if len(parts) > 1 else ""
                    else:
                        msg["reasoning_content"] = result
                        # 默认 content
                        if is_not_found_skip:
                            msg["content"] = f"I searched the document but couldn't find any {skip_category.lower()} data."
                        else:
                            msg["content"] = f"The {skip_category.lower()} data was already recorded earlier."
                    
                    # 确保 content 不为空
                    if not msg.get("content"):
                        if is_not_found_skip:
                            msg["content"] = f"I searched the document but couldn't find any {skip_category.lower()} data."
                        else:
                            msg["content"] = f"The {skip_category.lower()} data was already recorded earlier."
                    
                    # 🔥 移除空的 tool_calls（smart_skip_pure 是纯文本回复）
                    if "tool_calls" in msg and (not msg["tool_calls"] or len(msg["tool_calls"]) == 0):
                        del msg["tool_calls"]
                    
                    print(f"  ✓ 生成 smart_skip reasoning + content: {msg['reasoning_content'][:60]}...")
                except Exception as e:
                    print(f"  ⚠️  生成 smart_skip reasoning 失败: {e}")
                    msg["reasoning_content"] = f"Skipping {skip_category} as it was {reason_text}."
                    if is_not_found_skip:
                        msg["content"] = f"I searched the document but couldn't find any {skip_category.lower()} data."
                    else:
                        msg["content"] = f"The {skip_category.lower()} data was already recorded earlier."
                    # 🔥 同样移除空的 tool_calls
                    if "tool_calls" in msg and (not msg["tool_calls"] or len(msg["tool_calls"]) == 0):
                        del msg["tool_calls"]
                continue
            
            elif is_final_response:
                # 🔥 最终回复场景（区分 QA/Extract 和 not_found）
                try:
                    if is_not_found:
                        # 🔥 not_found 场景：诚实告知用户没找到
                        if is_qa_mode:
                            prompt = f"""You searched for data but didn't find what the user asked for. Generate:
1. **Reasoning** (internal thinking): Explain what you searched for and why you couldn't find it
2. **Response** (user-facing): Honestly tell the user the data wasn't found

## Conversation So Far:
{history_text}

## User's Original Question:
{user_query}

**Format**:
[Your internal reasoning] ||| [Your response to user]

**Remember**:
- Reasoning: First person, explain your search attempts
- Response: Be honest that the specific data wasn't found in the document
- DO NOT claim you found or recorded data that doesn't exist
- Must include "|||" separator

Generate your output:"""
                        else:
                            prompt = f"""You searched for data but didn't find what the user asked for. Generate:
1. **Reasoning** (internal thinking): Explain what you searched for and why you couldn't find it
2. **Response** (user-facing): Honestly tell the user the data wasn't found

## Conversation So Far:
{history_text}

## User's Original Request:
{user_query}

**Format**:
[Your internal reasoning] ||| [Your response to user]

**Remember**:
- Reasoning: First person, explain your search attempts
- Response: Be honest that the specific data wasn't found in the document
- DO NOT claim you found or recorded data that doesn't exist
- Must include "|||" separator

Generate your output:"""
                    
                    elif is_qa_mode:
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
                    else:
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
                    
                    user_msg = BaseMessage.make_user_message(role_name="User", content=prompt)
                    response = self.reasoning_agent.step(user_msg)
                    result = response.msg.content.strip().replace("<think>", "").replace("</think>", "").strip()
                    
                    # 分割 reasoning 和 content
                    if "|||" in result:
                        parts = result.split("|||")
                        msg["reasoning_content"] = parts[0].strip()
                        msg["content"] = parts[1].strip() if len(parts) > 1 else "I have completed the task."
                    else:
                        msg["reasoning_content"] = result
                        if is_not_found:
                            msg["content"] = "I searched the document but couldn't find the specific data you requested."
                        else:
                            msg["content"] = "I have completed the data extraction."
                    
                    # 🔥 移除空的 tool_calls（final_response 是纯文本回复）
                    if "tool_calls" in msg and (not msg["tool_calls"] or len(msg["tool_calls"]) == 0):
                        del msg["tool_calls"]
                    
                    scenario_type = "not_found" if is_not_found else ("QA" if is_qa_mode else "Extract")
                    print(f"  ✓ 生成 final response ({scenario_type})")
                    
                except Exception as e:
                    print(f"  ⚠️  生成 final response 失败: {e}")
                    msg["reasoning_content"] = "[生成失败]"
                    msg["content"] = "[生成失败]"
                    # 🔥 同样移除空的 tool_calls
                    if "tool_calls" in msg and (not msg["tool_calls"] or len(msg["tool_calls"]) == 0):
                        del msg["tool_calls"]
                continue
            
            elif is_pivot_scenario:
                # 🔥 Pivot 场景：解释为什么上次搜索结果不行，需要换关键词
                new_queries = tool_calls[0].get("arguments", {}).get("queries", [])
                
                prompt = f"""You are an LCA expert performing LCI data extraction.

## Conversation So Far:
{history_text}

## Your Decision:
The previous search didn't give you what you needed, so you're trying new keywords: {', '.join(new_queries)}

## Your Task:
Generate your reasoning explaining:
1. What was missing or insufficient in the previous search results
2. Why you chose these new keywords

**Remember**:
- Write in first person
- Be concise and natural
- Reference the previous search results

Generate only the reasoning:"""
                
                try:
                    user_msg = BaseMessage.make_user_message(role_name="User", content=prompt)
                    response = self.reasoning_agent.step(user_msg)
                    reasoning = response.msg.content.strip().replace("<think>", "").replace("</think>", "").strip()
                    msg["reasoning_content"] = reasoning
                    print(f"  ✓ 生成 pivot reasoning: {reasoning[:80]}...")
                except Exception as e:
                    print(f"  ⚠️  生成 pivot reasoning 失败: {e}")
                    msg["reasoning_content"] = "Previous search didn't find what I needed, trying different keywords."
                continue
            
            else:
                # 🔥 通用场景：使用 build_dynamic_prompt
                prompt = build_dynamic_prompt(
                    previous_messages=previous_messages,
                    current_tool_call=tool_calls[0],
                    user_query=user_query
                )
                
                try:
                    user_msg = BaseMessage.make_user_message(role_name="User", content=prompt)
                    response = self.reasoning_agent.step(user_msg)
                    reasoning = response.msg.content.strip().replace("<think>", "").replace("</think>", "").strip()
                    msg["reasoning_content"] = reasoning
                    print(f"  ✓ 生成 reasoning: {reasoning[:80]}...")
                except Exception as e:
                    print(f"  ⚠️  生成 reasoning 失败: {e}")
                    msg["reasoning_content"] = "[生成失败]"
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
            # 🔥 传入 convert_to_qa 参数，用于区分 Extract/QA
            user_content = self.generate_user_content_from_search_queries(messages, is_qa_mode=convert_to_qa)
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
    parser = argparse.ArgumentParser(description="短对话 Reasoning 生成器 v5.0（支持 not_found/smart_skip/pivot 场景）")
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
