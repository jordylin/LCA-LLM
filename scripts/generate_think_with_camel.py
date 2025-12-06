"""
CAMEL AI 推理生成脚本 - 为导出数据补充 reasoning 内容

功能：
1. 从 JSON 文件读取导出的训练数据（messages 格式）
2. 使用 CAMEL AI + DeepSeek API 生成高质量推理过程
3. 通过记忆机制和动态 Prompt 实现自然、连贯的 reasoning
4. 输出到新的 JSON 文件

核心特性：
- 第一人称代入
- 自动记忆前面的对话（同一个 sample 内）
- 动态构建 Prompt（根据当前位置）
- 完整信息提供（不截断 queries、chunks）

作者：AI Assistant
版本：v6.0
日期：2025-11-25
"""

import os
import sys
import json
import re
from typing import List, Dict, Any
import argparse
from pathlib import Path

# CAMEL AI imports
try:
    from camel.agents import ChatAgent
    from camel.messages import BaseMessage
except ImportError:
    print("❌ CAMEL AI 未安装。请运行: pip install camel-ai")
    sys.exit(1)

# 导入辅助函数
from reasoning_helpers import (
    summarize_tool_response,
    describe_next_action,
    build_conversation_history,
    build_dynamic_prompt
)


class ThinkGenerator:
    """使用 CAMEL AI 生成推理过程"""
    
    def __init__(self, api_key: str, model_name: str = "deepseek-chat"):
        """
        初始化生成器
        
        Args:
            api_key: DeepSeek API Key
            model_name: 模型名称（支持 deepseek-chat, deepseek-reasoner）
        """
        self.api_key = api_key
        self.model_name = model_name
        
        # 配置 CAMEL AI 使用 DeepSeek
        os.environ["OPENAI_API_KEY"] = api_key
        os.environ["OPENAI_API_BASE_URL"] = "https://api.deepseek.com"
        
        # 创建 CAMEL Agent with DeepSeek model
        from camel.models import OpenAIModel
        from camel.configs.openai_config import ChatGPTConfig
        
        # 根据模型类型调整参数
        if "reasoner" in model_name.lower() or "r1" in model_name.lower():
            # R1 推理模型：更高温度，更多 tokens
            config = ChatGPTConfig(
                temperature=1.0,  # DeepSeek 推荐：数据抽取/分析场景
                max_tokens=1000  # R1 需要更多空间进行推理
            )
            print(f"🧠 使用推理模型: {model_name}")
        else:
            # Chat 模型：标准配置
            config = ChatGPTConfig(
                temperature=1.0,  # DeepSeek 推荐：数据抽取/分析场景
                max_tokens=500
            )
            print(f"💬 使用对话模型: {model_name}")
        
        self.agent = ChatAgent(
            system_message=self._get_system_prompt(),
            model=OpenAIModel(
                model_type=model_name,
                model_config_dict=config.as_dict(),
                api_key=api_key,
                url="https://api.deepseek.com"
            )
        )
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词 (v6.0 - 第一人称代入)"""
        return """You are an LCA expert performing LCI data extraction from documents.

## Your Role
You are actively extracting data. Generate your internal reasoning explaining WHY you choose each action.

## LCI Categories (11 types)
**Input**: Raw Material, Process Energy, Post-processing Energy, Feedstock Energy, Gas, Cooling Media
**Output**: Product, Recovered Material, Waste, Emission
**Scope**: Functional Unit

## Standard Workflow
1. **Functional Unit First**: Search for product, quantity, process to establish the study basis
2. **Input Flows**: Extract materials, energy, gas, cooling media
3. **Output Flows**: Extract product, recovered materials, waste, emissions
4. **Validation** (optional): Check completeness

## Key Principles
1. **First-person perspective**: Write as if you are performing the extraction
2. **Natural thinking**: Think out loud, don't follow templates
3. **Context-aware**: Reference previous actions when relevant
4. **Concise**: Keep reasoning brief and focused
5. **Honest**: Express uncertainty or confidence naturally

## Energy Classification
- **Process Energy**: Printing/machine operation (e.g., SLM system)
- **Post-processing Energy**: Heat treatment, machining after printing
- **Feedstock Energy**: Powder production (e.g., atomization)

Generate only the reasoning content, no tags or labels.
"""
    
    def _extract_chunk_preview_from_system(self, messages: List[Dict]) -> str:
        """
        从 system message 中提取 chunk preview（如果有）
        
        Args:
            messages: messages数组
            
        Returns:
            chunk preview 文本，如果没有则返回空字符串
        """
        for msg in messages:
            if msg.get("role") == "system":
                content = msg.get("content", "")
                # 检查是否包含 CHUNK 0 PREVIEW
                if "**CHUNK 0 PREVIEW**" in content:
                    # 提取 chunk 0 的前 200 字符（简化版）
                    try:
                        chunk_0_start = content.find("**CHUNK 0 PREVIEW**")
                        chunk_0_end = content.find("**CHUNK 1 PREVIEW**", chunk_0_start)
                        if chunk_0_end == -1:
                            chunk_0_end = content.find("**AUTOMATIC SESSION INJECTION**", chunk_0_start)
                        
                        if chunk_0_end > chunk_0_start:
                            chunk_0_text = content[chunk_0_start:chunk_0_end].strip()
                            # 提取引号内的内容
                            if '"' in chunk_0_text:
                                chunk_0_content = chunk_0_text.split('"')[1]
                                # 只取前 200 字符（避免太长）
                                return chunk_0_content[:200] + "..." if len(chunk_0_content) > 200 else chunk_0_content
                    except:
                        pass
                break
        return ""
    
    def extract_context_from_messages(self, messages: List[Dict]) -> tuple:
        """
        从messages数组中提取上下文信息
        
        Args:
            messages: messages数组
            
        Returns:
            (user_query, search_results, tool_name, tool_args) 或 None
        """
        user_query = ""
        search_results = []
        tool_name = ""
        tool_args = {}
        
        for i, msg in enumerate(messages):
            role = msg.get("role")
            
            # 提取用户问题
            if role == "user":
                user_query = msg.get("content", "")
            
            # 提取搜索结果
            elif role == "tool" and i > 0:
                prev_msg = messages[i-1]
                if prev_msg.get("role") == "assistant":
                    tool_calls = prev_msg.get("tool_calls", [])
                    if tool_calls and tool_calls[0].get("name") == "search_document":
                        # 这是搜索结果
                        content = msg.get("content", "")
                        try:
                            # 解析<tool_response>标签内的JSON
                            if "<tool_response>" in content:
                                json_str = content.split("<tool_response>")[1].split("</tool_response>")[0].strip()
                                response_data = json.loads(json_str)
                                search_results = response_data.get("results", [])
                        except:
                            pass
            
            # 提取工具调用信息（record_*）
            elif role == "assistant":
                tool_calls = msg.get("tool_calls", [])
                if tool_calls:
                    first_call = tool_calls[0]
                    if first_call.get("name") != "search_document":  # 不是搜索，是记录
                        tool_name = first_call.get("name", "")
                        tool_args = first_call.get("arguments", {})
        
        return user_query, search_results, tool_name, tool_args
    
    def _generate_user_content_for_full_dialogue(self) -> str:
        """
        使用 CAMEL AI 生成多样化的 user content
        
        Full 数据的任务通常是提取完整的 LCI 数据，但表达方式应该多样化
        
        Returns:
            生成的 user content
        """
        prompt = """Generate a natural user request for extracting LCI (Life Cycle Inventory) data from a document.

Requirements:
- Keep it simple and natural (like a real user would ask)
- Focus on extracting LCI data from the document
- DO NOT be too specific (e.g., don't list "functional unit, materials, energy, gas, waste")
- Vary the phrasing naturally

Generate ONE natural user request (output ONLY the request, no explanation):"""

        try:
            response = self.agent.step(BaseMessage.make_user_message(
                role_name="User",
                content=prompt
            ))
            
            user_content = response.msg.content.strip()
            
            # 移除可能的引号
            if user_content.startswith('"') and user_content.endswith('"'):
                user_content = user_content[1:-1]
            if user_content.startswith("'") and user_content.endswith("'"):
                user_content = user_content[1:-1]
            
            # 确保不为空
            if not user_content or len(user_content) < 10:
                # 回退到简单的默认值
                return "Please help me extract the LCI data from this document."
            
            return user_content
            
        except Exception as e:
            print(f"  ⚠️  生成 user content 失败，使用默认值: {e}")
            return "Please help me extract the LCI data from this document."
    
    def generate_think_for_messages(
        self,
        sample: Dict
    ) -> Dict:
        """
        为messages格式的样本生成reasoning_content
        
        Args:
            sample: 包含messages数组的样本
            
        Returns:
            更新后的样本（填充了reasoning_content）
        """
        messages = sample.get("messages", [])
        
        # 🔥 关键改进：每个 sample 开始时清空记忆
        self.agent.clear_memory()
        print(f"  🧹 已清空 Agent 记忆（开始新 sample）")
        
        # 🔥 检查最后一条消息是否是 tool response，如果是，自动添加 final assistant 消息
        if messages and messages[-1].get("role") == "tool":
            print(f"  📝 检测到最后一条是 tool response，自动添加 final assistant 消息")
            messages.append({
                "role": "assistant",
                "reasoning_content": "",  # 占位符，后面会填充
                "content": ""  # 占位符，后面会填充
            })
        
        # 🔥 填充空的 user content（如果第二条消息是 user 且内容为空）
        if len(messages) >= 2 and messages[1].get("role") == "user":
            if not messages[1].get("content") or messages[1].get("content").strip() == "":
                messages[1]["content"] = self._generate_user_content_for_full_dialogue()
                print(f"  ✏️  已生成 user content")
        
        # 🔥 提取 system prompt 中的 chunk preview（如果有）
        chunk_preview = self._extract_chunk_preview_from_system(messages)
        
        # 提取上下文信息
        user_query, search_results, tool_name, tool_args = self.extract_context_from_messages(messages)
        
        # 为每个assistant消息生成reasoning_content
        for i, msg in enumerate(messages):
            if msg.get("role") == "assistant":
                tool_calls = msg.get("tool_calls", [])
                
                # 🔥 检测 Smart Skip 场景：reasoning_content 包含 SMART_SKIP_PLACEHOLDER
                existing_reasoning = msg.get("reasoning_content", "")
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
                
                current_tool = tool_calls[0].get("name") if tool_calls else None
                
                # 提取之前的历史（LLM能看到的上下文）
                previous_messages = messages[:i]  # 当前消息之前的所有消息
                previous_actions = self._extract_previous_actions(previous_messages)
                
                # 🔥 检测是否为Pivot场景：search_document后紧接着另一个search_document（但不是 Smart Skip）
                is_pivot_scenario = False
                if current_tool == "search_document" and i >= 2 and not is_smart_skip_with_search:
                    # 检查前两条消息是否为：assistant(search) + tool(response)
                    prev_msg = messages[i-1]
                    prev_prev_msg = messages[i-2]
                    if (prev_msg.get("role") == "tool" and 
                        prev_prev_msg.get("role") == "assistant" and
                        prev_prev_msg.get("tool_calls", [{}])[0].get("name") == "search_document"):
                        is_pivot_scenario = True
                        # 提取上一次搜索的结果
                        prev_search_results = self._extract_search_results_from_tool_message(prev_msg)
                
                # 构建state和action用于生成
                if is_smart_skip_with_search:
                    # 🔥 Smart Skip + Search 场景：评估前一个搜索结果 → 跳过 → 搜索下一个类别
                    match = re.search(r'\[SMART_SKIP_PLACEHOLDER: (.*?) - (.*?)\]', existing_reasoning)
                    if match:
                        skip_category = match.group(1)
                        skip_reason = match.group(2)
                    else:
                        skip_category = "Unknown"
                        skip_reason = "already_recorded"
                    
                    # 提取前一个搜索的结果（导致 skip 的搜索）
                    prev_msg = messages[i-1] if i > 0 else None
                    prev_search_results = []
                    if prev_msg and prev_msg.get("role") == "tool":
                        prev_search_results = self._extract_search_results_from_tool_message(prev_msg)
                    
                    # 提取当前的搜索查询（下一个类别）
                    next_search_keywords = tool_calls[0].get("arguments", {}).get("queries", [])
                    
                    state = {
                        "user_query": user_query,
                        "previous_actions": previous_actions,
                        "skip_category": skip_category,
                        "skip_reason": skip_reason,
                        "prev_search_results": prev_search_results,
                        "next_search_query": next_search_keywords,  # 保持数组格式
                        "chunk_preview": chunk_preview
                    }
                    action = {
                        "tool": "smart_skip_with_search",
                        "parameters": {
                            "skip_category": skip_category,
                            "skip_reason": skip_reason,
                            "queries": next_search_keywords  # 🔥 改为 "queries"，传数组
                        }
                    }
                    
                elif is_smart_skip_pure:
                    # 🔥 Smart Skip场景：解析placeholder提取category和skip_reason
                    match = re.search(r'\[SMART_SKIP_PLACEHOLDER: (.*?) - (.*?)\]', existing_reasoning)
                    if match:
                        category = match.group(1)
                        skip_reason = match.group(2)
                    else:
                        category = "Unknown"
                        skip_reason = "already_recorded"
                    
                    # 提取上一次tool response（搜索结果）
                    prev_msg = messages[i-1] if i > 0 else None
                    search_results = []
                    if prev_msg and prev_msg.get("role") == "tool":
                        search_results = self._extract_search_results_from_tool_message(prev_msg)
                    
                    state = {
                        "user_query": user_query,
                        "previous_actions": previous_actions,
                        "is_smart_skip": True,
                        "category": category,
                        "skip_reason": skip_reason,
                        "search_results": search_results,
                        "chunk_preview": chunk_preview
                    }
                    action = {"tool": "smart_skip", "parameters": {"category": category, "skip_reason": skip_reason}}
                    
                elif is_final_response:
                    # 🔥 最终回复场景：生成总结性回复
                    # 检查任务类型
                    task_type = msg.get("task_type", "FULL_EXTRACTION")
                    
                    # 提取上一次tool response
                    prev_msg = messages[i-1] if i > 0 else None
                    session_summary_text = ""
                    if prev_msg and prev_msg.get("role") == "tool":
                        session_summary_text = self._extract_session_summary_from_tool_message(prev_msg)
                    
                    state = {
                        "user_query": user_query,
                        "previous_actions": previous_actions,
                        "session_summary": session_summary_text,
                        "is_final": True,
                        "task_type": task_type,  # 传递任务类型
                        "chunk_preview": chunk_preview  # 🔥 传递 chunk preview
                    }
                    action = {"tool": "final_response", "parameters": {"task_type": task_type}}
                    
                elif current_tool == "search_document":
                    if is_pivot_scenario:
                        # Pivot场景：解释为什么上次搜索的结果不行，需要换关键词
                        state = {
                            "user_query": user_query, 
                            "previous_actions": previous_actions,
                            "previous_search_results": prev_search_results,
                            "is_pivot": True,
                            "chunk_preview": chunk_preview  # 🔥 传递 chunk preview
                        }
                    else:
                        # 正常搜索场景
                        state = {
                            "user_query": user_query, 
                            "previous_actions": previous_actions,
                            "is_pivot": False,
                            "chunk_preview": chunk_preview  # 🔥 传递 chunk preview
                        }
                    action = {"tool": "search_document", "parameters": tool_calls[0].get("arguments", {})}
                elif current_tool == "get_session_summary":
                    # Session summary推理
                    state = {
                        "user_query": user_query,
                        "previous_actions": previous_actions,
                        "chunk_preview": chunk_preview  # 🔥 传递 chunk preview
                    }
                    action = {"tool": current_tool, "parameters": tool_calls[0].get("arguments", {})}
                else:
                    # 记录推理 - 使用当前消息的tool_calls参数
                    current_tool_args = tool_calls[0].get("arguments", {}) if tool_calls else {}
                    state = {
                        "user_query": user_query, 
                        "search_results": search_results,
                        "previous_actions": previous_actions,
                        "chunk_preview": chunk_preview  # 🔥 传递 chunk preview
                    }
                    action = {"tool": current_tool, "parameters": current_tool_args}
                
                # 🔥 关键改进：使用动态 Prompt 构建
                # 所有场景都使用新的动态构建方式
                if tool_calls and len(tool_calls) > 0:
                    # 有 tool_calls：使用辅助函数动态构建 prompt
                    prompt = build_dynamic_prompt(
                        previous_messages=previous_messages,
                        current_tool_call=tool_calls[0],
                        user_query=user_query
                    )
                else:
                    # 没有 tool_calls（final response, smart_skip_pure）
                    # 构建简化的 prompt
                    history_text = build_conversation_history(previous_messages)
                    
                    if is_final_response:
                        prompt = f"""You are an LCA expert performing LCI data extraction.

## Conversation So Far:
{history_text}

## Your Task:
Generate TWO parts separated by "|||":
1. **Reasoning** (internal thinking): Reflect on what you accomplished
2. **Response** (user-facing): A natural confirmation message

**Format**:
[Your internal reasoning] ||| [Your response to user]

**Remember**:
- Reasoning: First person and detailed
- Response: Professional, concise and natural
- Must include "|||" separator

Generate your output:"""
                    
                    elif is_smart_skip_pure:
                        skip_category = state.get("category", "Unknown")
                        skip_reason = state.get("skip_reason", "already_recorded")
                        
                        reason_text = "not found in the document" if skip_reason == "not_found" else "already recorded earlier"
                        
                        prompt = f"""You are an LCA expert performing LCI data extraction.

## Conversation So Far:
{history_text}

## Your Decision:
Skip recording {skip_category} ({reason_text})

## Your Task:
Generate your reasoning explaining why you're skipping this category.

**Remember**:
- Write in first person
- Be concise and natural
- Explain the skip reason clearly

Generate only the reasoning:"""
                    
                    else:
                        # 不应该到达这里：所有无 tool_calls 的场景都已覆盖
                        raise ValueError(f"Unexpected scenario: no tool_calls, not final_response, not smart_skip_pure")
                
                try:
                    user_msg = BaseMessage.make_user_message(
                        role_name="User",
                        content=prompt
                    )
                    # 🔥 Agent 自动记住这次对话
                    response = self.agent.step(user_msg)
                    result_content = response.msg.content.strip()
                    result_content = result_content.replace("<think>", "").replace("</think>", "").strip()
                    
                    # 🔥 特殊处理：final_response需要分割thinking和content
                    if is_final_response:
                        if "|||" in result_content:
                            parts = result_content.split("|||")
                            if len(parts) >= 2:
                                msg["reasoning_content"] = parts[0].strip()
                                msg["content"] = parts[1].strip()
                            else:
                                msg["reasoning_content"] = result_content
                                msg["content"] = "I have completed the LCI data extraction."
                        else:
                            # 如果没有分隔符，reasoning作为thinking，生成默认content
                            msg["reasoning_content"] = result_content
                            msg["content"] = "I have completed the LCI data extraction."
                    else:
                        # 普通场景：只填充reasoning_content
                        msg["reasoning_content"] = result_content
                    
                except Exception as e:
                    msg["reasoning_content"] = f"[生成失败: {str(e)}]"
                    if is_final_response:
                        msg["content"] = f"[生成失败: {str(e)}]"
        
        return sample
    
    def _extract_previous_actions(self, previous_messages: list) -> list:
        """
        从之前的messages中提取已执行的动作
        
        Args:
            previous_messages: 当前消息之前的所有消息
            
        Returns:
            已执行动作的列表，每个动作包含工具名和关键参数
        """
        actions = []
        for msg in previous_messages:
            if msg.get("role") == "assistant":
                tool_calls = msg.get("tool_calls", [])
                for call in tool_calls:
                    tool_name = call.get("name")
                    args = call.get("arguments", {})
                    
                    # 提取关键信息
                    if tool_name == "record_process_flow":
                        actions.append({
                            "tool": tool_name,
                            "name": args.get("name"),
                            "value": args.get("value"),
                            "unit": args.get("unit")
                        })
                    elif tool_name == "record_parameter":
                        actions.append({
                            "tool": tool_name,
                            "parameter_name": args.get("parameter_name"),
                            "parameter_value": args.get("parameter_value")
                        })
                    elif tool_name == "execute_calculation":
                        actions.append({
                            "tool": tool_name,
                            "expression": args.get("expression")
                        })
                    elif tool_name == "search_document":
                        actions.append({
                            "tool": tool_name,
                            "query": args.get("query")
                        })
        
        return actions
    
    def _extract_search_results_from_tool_message(self, tool_msg: Dict) -> list:
        """
        从tool消息中提取搜索结果
        
        Args:
            tool_msg: tool role的消息
            
        Returns:
            搜索结果列表
        """
        content = tool_msg.get("content", "")
        
        # 提取<tool_response>标签内的JSON
        match = re.search(r'<tool_response>\s*(\{.*?\})\s*</tool_response>', content, re.DOTALL)
        if match:
            try:
                response_data = json.loads(match.group(1))
                return response_data.get("results", [])
            except:
                pass
        
        return []
    
    def _extract_session_summary_from_tool_message(self, tool_msg: Dict) -> str:
        """
        从tool消息中提取session summary文本
        
        Args:
            tool_msg: tool role的消息
            
        Returns:
            session summary文本
        """
        content = tool_msg.get("content", "")
        
        # 提取<tool_response>标签内的JSON
        match = re.search(r'<tool_response>\s*(\{.*?\})\s*</tool_response>', content, re.DOTALL)
        if match:
            try:
                response_data = json.loads(match.group(1))
                # 提取session_summary字段
                return response_data.get("session_summary", "")
            except:
                pass
        
        return ""
    
    def process_json_file(
        self,
        input_path: str,
        output_path: str
    ) -> None:
        """
        处理JSON文件（数组格式），为每个样本生成reasoning_content
        
        Args:
            input_path: 输入JSON文件路径
            output_path: 输出JSON文件路径
        """
        input_file = Path(input_path)
        output_file = Path(output_path)
        
        if not input_file.exists():
            print(f"❌ 输入文件不存在: {input_path}")
            return
        
        print(f"📖 读取输入文件: {input_path}")
        print(f"📝 输出文件: {output_path}")
        print("-" * 60)
        
        # 读取JSON数组
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print("❌ 错误：输入文件必须是JSON数组")
            return
        
        print(f"找到 {len(data)} 个样本\n")
        
        processed = 0
        failed = 0
        
        for i, sample in enumerate(data, 1):
            try:
                metadata = sample.get("metadata", {})
                action_id = metadata.get("action_id", f"sample_{i}")
                record_type = metadata.get("record_type", "unknown")
                
                print(f"处理样本 {i}/{len(data)} (action_id: {action_id}, type: {record_type})")
                
                # 生成reasoning_content
                updated_sample = self.generate_think_for_messages(sample)
                data[i-1] = updated_sample
                
                print(f"  ✅ 生成完成")
                processed += 1
                
            except Exception as e:
                print(f"  ❌ 处理失败: {e}")
                failed += 1
        
        # 写入输出文件
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print("\n" + "=" * 60)
        print(f"✅ 处理完成!")
        print(f"   成功: {processed} 个样本")
        print(f"   失败: {failed} 个样本")
        print(f"   输出: {output_path}")
        print("=" * 60)
    
    def process_jsonl_file(
        self,
        input_path: str,
        output_path: str
    ) -> None:
        """
        处理 JSONL 文件（旧格式兼容，不推荐使用）
        
        Args:
            input_path: 输入 JSONL 文件路径
            output_path: 输出 JSONL 文件路径
        """
        input_file = Path(input_path)
        output_file = Path(output_path)
        
        if not input_file.exists():
            print(f"❌ 输入文件不存在: {input_path}")
            return
        
        print(f"📖 读取输入文件: {input_path}")
        print(f"📝 输出文件: {output_path}")
        print("-" * 60)
        
        processed = 0
        failed = 0
        
        with open(input_file, 'r', encoding='utf-8') as f_in, \
             open(output_file, 'w', encoding='utf-8') as f_out:
            
            for line_num, line in enumerate(f_in, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    # 解析 JSON
                    data = json.loads(line)
                    
                    state = data.get("state", {})
                    action = data.get("action", {})
                    observation = data.get("observation", {})
                    
                    print(f"\n处理样本 {line_num}:")
                    print(f"  Tool: {action.get('tool', 'unknown')}")
                    
                    # 生成推理内容
                    think_candidates = self.generate_think_candidates(
                        state, action, observation, num_candidates=1
                    )
                    
                    # 直接填充reasoning_content
                    data["reasoning_content"] = think_candidates[0] if think_candidates else ""
                    
                    # 写入输出文件
                    f_out.write(json.dumps(data, ensure_ascii=False) + "\n")
                    
                    print(f"  ✅ 生成完成")
                    
                    processed += 1
                    
                except Exception as e:
                    print(f"  ❌ 处理失败: {e}")
                    failed += 1
        
        print("\n" + "=" * 60)
        print(f"✅ 处理完成!")
        print(f"   成功: {processed} 个样本")
        print(f"   失败: {failed} 个样本")
        print(f"   输出: {output_path}")
        print("=" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="使用 CAMEL AI 为训练数据生成 <think> 内容"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="输入 JSONL 文件路径"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="输出 JSONL 文件路径"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=os.getenv("DEEPSEEK_API_KEY"),
        help="DeepSeek API Key（或设置环境变量 DEEPSEEK_API_KEY）"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="deepseek-chat",
        choices=["deepseek-chat", "deepseek-reasoner"],
        help="使用的模型（默认: deepseek-chat）"
    )
    args = parser.parse_args()
    
    # 检查 API Key
    if not args.api_key:
        print("❌ 错误: 未提供 DeepSeek API Key")
        print("   方式1: --api-key YOUR_KEY")
        print("   方式2: export DEEPSEEK_API_KEY=YOUR_KEY")
        sys.exit(1)
    
    # 初始化生成器
    print("🚀 初始化 CAMEL AI Think Generator...")
    generator = ThinkGenerator(api_key=args.api_key, model_name=args.model)
    
    # 检测输入文件格式
    input_path = Path(args.input)
    if input_path.suffix == '.json':
        # JSON数组格式
        print("📋 检测到JSON格式，使用JSON处理模式\n")
        generator.process_json_file(
            input_path=args.input,
            output_path=args.output
        )
    elif input_path.suffix == '.jsonl':
        # JSONL格式（旧格式兼容）
        print("📋 检测到JSONL格式，使用JSONL处理模式\n")
        generator.process_jsonl_file(
            input_path=args.input,
            output_path=args.output
        )
    else:
        print(f"❌ 错误：不支持的文件格式 {input_path.suffix}")
        print("   支持的格式：.json（推荐）或 .jsonl")
        sys.exit(1)


if __name__ == "__main__":
    main()
