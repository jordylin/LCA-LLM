"""
Qwen-Agent 服务 V2
真正使用 Qwen-Agent 框架，通过 vLLM API 进行推理

架构：
┌─────────────────────────────────────────┐
│           QwenAgentServiceV2            │
│  ┌─────────────────────────────────┐    │
│  │     Qwen-Agent Assistant        │    │
│  │   (对话管理、工具调用解析)        │    │
│  └─────────────────────────────────┘    │
│                   │                      │
│                   ▼                      │
│  ┌─────────────────────────────────┐    │
│  │     vLLM API (OpenAI 兼容)       │    │
│  │   (高性能推理引擎)               │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘

使用方式：
1. 先启动 vLLM: ./start_vllm.sh
2. 设置环境变量: LLM_SERVICE=qwen_agent
3. 启动后端: ./restart_services.sh
"""

import logging
import json
import re
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# 尝试导入 qwen-agent
try:
    from qwen_agent.agents import Assistant
    from qwen_agent.llm import get_chat_model
    from qwen_agent.tools.base import BaseTool, register_tool
    QWEN_AGENT_AVAILABLE = True
except ImportError:
    QWEN_AGENT_AVAILABLE = False
    logger.warning("qwen-agent 未安装，将使用简化模式")

# 导入我们的 LCA 工具
from backend.services.qwen_agent_tools import (
    set_tool_service, 
    get_lca_tool_names,
    QWEN_AGENT_AVAILABLE as TOOLS_AVAILABLE
)


class QwenAgentServiceV2:
    """
    基于 Qwen-Agent 框架的 LLM 服务
    
    通过 vLLM API 进行推理，使用 Qwen-Agent 管理对话和工具调用
    """
    
    def __init__(
        self,
        api_base: str = "http://localhost:8080/v1",
        api_key: str = "EMPTY",
        model_name: str = "qwen-lca",
        session_manager = None
    ):
        """
        初始化服务
        
        Args:
            api_base: vLLM API 地址
            api_key: API 密钥
            model_name: 模型名称
            session_manager: 会话管理器
        """
        self.api_base = api_base
        self.api_key = api_key
        self.model_name = model_name
        self.session_manager = session_manager
        
        self.llm = None
        self.assistant = None
        self.is_initialized = False
        
        # PDF 处理器引用
        self.pdf_processor = None
        
        # 工具执行器（由 LLMChatService 设置）
        self.tool_executor = None
        
        logger.info(f"QwenAgentServiceV2 初始化，API: {self.api_base}")
        
    def set_pdf_processor(self, pdf_processor):
        """设置 PDF 处理器"""
        self.pdf_processor = pdf_processor
        
    def set_tool_executor(self, executor):
        """设置工具执行器"""
        self.tool_executor = executor
        
    def set_tool_service(self, tool_service):
        """设置工具服务（供 Qwen-Agent 工具使用）"""
        self._tool_service = tool_service
        logger.info("✅ QwenAgentServiceV2 已设置 tool_service")
        
    async def initialize(self):
        """异步初始化"""
        if self.is_initialized:
            return
            
        logger.info("🚀 初始化 Qwen-Agent 服务...")
        
        if not QWEN_AGENT_AVAILABLE:
            logger.warning("⚠️ qwen-agent 不可用，使用简化模式")
            self.is_initialized = True
            return
            
        try:
            # 配置 LLM（使用 vLLM API）
            llm_cfg = {
                'model': self.model_name,
                'model_server': self.api_base,
                'api_key': self.api_key,
                'generate_cfg': {
                    'max_input_tokens': 16000,
                    'max_retries': 3,
                }
            }
            
            # 创建 LLM 实例
            self.llm = get_chat_model(llm_cfg)
            
            # 系统提示词
            system_prompt = self._build_system_prompt()
            
            # 🔥 创建 Assistant，配置 LCA 工具
            # Qwen-Agent 会自动管理工具调用流程
            tool_names = get_lca_tool_names()
            logger.info(f"📦 配置 Qwen-Agent 工具: {tool_names}")
            
            self.assistant = Assistant(
                llm=llm_cfg,
                system_message=system_prompt,
                name='LCA-Assistant',
                description='LCA data extraction assistant',
                function_list=tool_names  # 注册我们的 LCA 工具
            )
            
            logger.info("✅ Qwen-Agent 初始化成功")
            self.is_initialized = True
            
        except Exception as e:
            logger.error(f"❌ Qwen-Agent 初始化失败: {e}")
            # 降级到简化模式
            self.is_initialized = True
            
    def _build_system_prompt(self, pdf_session_id: str = None) -> str:
        """构建系统提示词"""
        
        prompt = """You are an expert LCA (Life Cycle Assessment) assistant for Additive Manufacturing.

## Your Core Task
Extract quantitative LCI (Life Cycle Inventory) data from documents and record them using the provided tools.

## Available Tools
You have access to these tools:
- **search_document**: Search for specific information in the uploaded document
- **define_lca_scope**: Record the Functional Unit of the LCA study
- **record_process_flow**: Record LCI flow data (inputs/outputs with quantities)
- **record_parameter**: Record intermediate parameters for calculations
- **execute_calculation**: Perform calculations on recorded parameters
- **get_session_summary**: View all recorded data in the current session

## Strategic Workflow
1. **Understand** the user's request
2. **Search** the document for relevant data using keywords
3. **Extract** quantitative values (numbers with units)
4. **Record** data using appropriate tools
5. **Summarize** findings for the user

## LCI Categories
**Inputs:** Raw Material, Process Energy, Post-processing Energy, Feedstock Energy, Gas, Cooling Media
**Outputs:** Product, Recovered Material, Waste, Emission

## Key Guidelines
- Always search the document first before asking the user for information
- Use exact values from documents (no estimation)
- Provide selected_chunk for traceability
- Be proactive - don't wait for user to specify every detail
- After recording data, summarize what was recorded"""

        if pdf_session_id:
            prompt += f"\n\n## Current Session\nPDF_SESSION_ID: {pdf_session_id}"
            
        return prompt
        
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        聊天补全接口
        
        使用 Qwen-Agent 的 Assistant 进行对话
        """
        if not self.is_initialized:
            await self.initialize()
            
        try:
            if QWEN_AGENT_AVAILABLE and self.assistant:
                return await self._qwen_agent_chat(messages, tools, max_tokens, temperature)
            else:
                return await self._simple_chat(messages, tools, max_tokens, temperature)
                
        except Exception as e:
            logger.error(f"Chat completion 失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def stream_chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ):
        """
        流式聊天补全接口
        
        直接使用 vLLM API 进行流式输出，同时保留工具调用能力
        
        Yields:
            Dict with type: "content", "tool_call", "final"
        """
        if not self.is_initialized:
            await self.initialize()
        
        from openai import AsyncOpenAI
        
        try:
            # 创建 OpenAI 客户端
            client = AsyncOpenAI(
                base_url=self.api_base,
                api_key=self.api_key
            )
            
            # 格式化消息：将 system 和首条 assistant 注入到 user 消息
            formatted_messages = self._format_messages_for_stream(messages)
            
            # 格式化工具
            openai_tools = None
            if tools:
                openai_tools = []
                for tool in tools:
                    if "function" in tool:
                        openai_tools.append({
                            "type": "function",
                            "function": tool["function"]
                        })
            
            logger.info(f"🌊 开始流式调用 vLLM，消息数: {len(formatted_messages)}")
            
            # 🔥 动态计算 max_tokens，避免超过模型上下文限制
            # vLLM 启动时设置了 --max-model-len 8192
            # 需要留出足够空间给输入 tokens
            effective_max_tokens = min(max_tokens, 4096)  # 限制最大输出为 4096
            
            # 流式调用
            stream = await client.chat.completions.create(
                model=self.model_name,
                messages=formatted_messages,
                tools=openai_tools,
                max_tokens=effective_max_tokens,
                temperature=temperature,
                stream=True,
                extra_body={
                    "chat_template_kwargs": {
                        "enable_thinking": True
                    }
                }
            )
            
            full_content = ""
            tool_calls = []
            current_tool_call = None
            
            async for chunk in stream:
                if chunk.choices:
                    delta = chunk.choices[0].delta
                    
                    # 处理内容
                    if delta.content:
                        full_content += delta.content
                        yield {
                            "type": "content",
                            "content": delta.content
                        }
                    
                    # 处理工具调用
                    if delta.tool_calls:
                        for tc in delta.tool_calls:
                            if tc.index is not None:
                                # 新的工具调用
                                if tc.function and tc.function.name:
                                    current_tool_call = {
                                        "tool_name": tc.function.name,
                                        "arguments": ""
                                    }
                                    tool_calls.append(current_tool_call)
                                
                                # 累积参数
                                if tc.function and tc.function.arguments and current_tool_call:
                                    current_tool_call["arguments"] += tc.function.arguments
            
            # 解析工具调用参数
            parsed_tool_calls = []
            for tc in tool_calls:
                try:
                    params = json.loads(tc["arguments"]) if tc["arguments"] else {}
                    parsed_tool_calls.append({
                        "tool_name": tc["tool_name"],
                        "parameters": params
                    })
                    yield {
                        "type": "tool_call",
                        "tool_call": parsed_tool_calls[-1]
                    }
                except json.JSONDecodeError:
                    logger.warning(f"无法解析工具参数: {tc['arguments']}")
            
            # 最终结果
            yield {
                "type": "final",
                "success": True,
                "message": {
                    "role": "assistant",
                    "content": full_content,
                    "tool_calls": parsed_tool_calls if parsed_tool_calls else None
                }
            }
            
        except Exception as e:
            logger.error(f"流式聊天失败: {e}", exc_info=True)
            yield {
                "type": "error",
                "error": str(e)
            }
    
    def _format_messages_for_stream(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """格式化消息用于流式输出"""
        formatted = []
        system_context = ""
        welcome_context = ""
        first_non_system_handled = False
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                system_context = content
            elif role == "tool":
                formatted.append({
                    "role": "user",
                    "content": f"[Tool Response]\n{content}"
                })
            elif role == "assistant" and not first_non_system_handled:
                welcome_context = content
                first_non_system_handled = True
            else:
                formatted.append({
                    "role": role,
                    "content": content
                })
                if role != "system":
                    first_non_system_handled = True
        
        # 将上下文注入到第一条 user 消息
        if formatted and (system_context or welcome_context):
            for i, msg in enumerate(formatted):
                if msg["role"] == "user":
                    context_prefix = ""
                    if system_context:
                        context_prefix += f"[System Context]\n{system_context}\n\n"
                    if welcome_context:
                        context_prefix += f"[Document Status]\n{welcome_context}\n\n"
                    
                    formatted[i]["content"] = context_prefix + "[User Query]\n" + msg["content"]
                    break
        
        return formatted
            
    async def _qwen_agent_chat(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """
        使用 Qwen-Agent 的 Assistant.run() 进行对话
        
        🔥 真正的 Qwen-Agent 集成：
        - Qwen-Agent 自动解析工具调用
        - Qwen-Agent 自动执行工具（通过我们注册的 BaseTool）
        - Qwen-Agent 自动循环直到任务完成
        """
        
        # 从消息中提取 pdf_session_id
        pdf_session_id = None
        for msg in messages:
            if msg.get("role") == "system":
                content = msg.get("content", "")
                if "PDF_SESSION_ID:" in content:
                    import re as re_module
                    match = re_module.search(r'PDF_SESSION_ID:\s*(\S+)', content)
                    if match:
                        pdf_session_id = match.group(1)
                        break
        
        # 🔥 设置工具服务（让 BaseTool 可以访问）
        if hasattr(self, '_tool_service') and self._tool_service:
            set_tool_service(self._tool_service, pdf_session_id)
            logger.info(f"🔧 已设置工具服务，pdf_session_id: {pdf_session_id}")
        
        # 🔥 格式化消息：将 system 消息和首条 assistant 消息作为上下文注入到第一条 user 消息
        qwen_messages = []
        system_context = ""
        welcome_context = ""
        first_non_system_handled = False
        user_messages_collected = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                # 收集 system 消息作为上下文
                system_context = content
            elif role == "tool":
                # 工具响应转换为 user 消息
                qwen_messages.append({
                    "role": "user",
                    "content": f"[Tool Response]\n{content}"
                })
            elif role == "assistant" and not first_non_system_handled:
                # 首条 assistant 消息（欢迎语）作为上下文
                welcome_context = content
                first_non_system_handled = True
            else:
                if role == "user":
                    user_messages_collected.append(content)
                qwen_messages.append({
                    "role": role,
                    "content": content
                })
                if role != "system":
                    first_non_system_handled = True
        
        # 🔥 将上下文注入到第一条 user 消息
        if qwen_messages and (system_context or welcome_context):
            for i, msg in enumerate(qwen_messages):
                if msg["role"] == "user":
                    context_prefix = ""
                    if system_context:
                        context_prefix += f"[System Context]\n{system_context}\n\n"
                    if welcome_context:
                        context_prefix += f"[Document Status]\n{welcome_context}\n\n"
                    
                    qwen_messages[i]["content"] = context_prefix + "[User Query]\n" + msg["content"]
                    logger.info(f"🔧 已将上下文注入到第一条 user 消息，pdf_session_id: {pdf_session_id}")
                    break
        
        if not qwen_messages:
            return {
                "success": False,
                "error": "No user messages to process"
            }
        
        try:
            # 🔥 调用 Qwen-Agent 的 Assistant.run()
            # 这会自动处理工具调用和多轮对话
            logger.info(f"🚀 调用 Qwen-Agent Assistant.run()，消息数: {len(qwen_messages)}")
            
            responses = []
            for response in self.assistant.run(messages=qwen_messages):
                responses.append(response)
                logger.debug(f"Qwen-Agent 响应: {response}")
            
            # 解析最后一个响应
            if responses:
                last_response = responses[-1]
                
                # 提取内容
                content = ""
                thinking = ""
                tool_results = []
                
                for item in last_response:
                    if isinstance(item, dict):
                        item_role = item.get('role', '')
                        item_content = item.get('content', '')
                        
                        if item_role == 'assistant':
                            content = item_content
                        elif item_role == 'function':
                            # 工具调用结果
                            tool_results.append({
                                "tool_name": item.get('name', ''),
                                "result": item_content
                            })
                    elif hasattr(item, 'content'):
                        content = item.content
                    elif hasattr(item, 'role') and item.role == 'assistant':
                        content = getattr(item, 'content', str(item))
                
                # 解析 thinking
                think_match = re.search(r'<think>(.*?)</think>', content, re.DOTALL)
                if think_match:
                    thinking = think_match.group(1).strip()
                    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
                
                result = {
                    "success": True,
                    "message": {
                        "role": "assistant",
                        "content": content,
                        "thinking": thinking
                    }
                }
                
                if tool_results:
                    result["tool_results"] = tool_results
                    logger.info(f"🔧 Qwen-Agent 执行了 {len(tool_results)} 个工具")
                
                return result
            else:
                return {
                    "success": False,
                    "error": "No response from Qwen-Agent"
                }
                
        except Exception as e:
            logger.error(f"Qwen-Agent Assistant.run() 失败: {e}", exc_info=True)
            # 降级到简化模式
            logger.info("⚠️ 降级到简化模式")
            return await self._simple_chat(messages, tools, max_tokens, temperature)
            
    async def _simple_chat(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """简化模式：直接调用 vLLM API"""
        
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(
            base_url=self.api_base,
            api_key=self.api_key
        )
        
        # 格式化消息
        formatted_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "tool":
                formatted_messages.append({
                    "role": "user",
                    "content": f"<tool_response>\n{content}\n</tool_response>"
                })
            else:
                formatted_messages.append({
                    "role": role,
                    "content": content
                })
                
        # 🔥 修复：确保消息以 user 开头（vLLM 要求）
        if formatted_messages:
            first_non_system_idx = None
            for i, msg in enumerate(formatted_messages):
                if msg["role"] != "system":
                    first_non_system_idx = i
                    break
                    
            if first_non_system_idx is not None:
                first_msg = formatted_messages[first_non_system_idx]
                if first_msg["role"] == "assistant":
                    logger.info("🔧 将首条 assistant 消息转换为 system 消息")
                    formatted_messages[first_non_system_idx] = {
                        "role": "system",
                        "content": f"[Document Context]\n{first_msg['content']}"
                    }
                
        # 格式化工具
        openai_tools = None
        if tools:
            openai_tools = []
            for tool in tools:
                if "function" in tool:
                    openai_tools.append({
                        "type": "function",
                        "function": tool["function"]
                    })
                    
        # 调用 API
        response = await client.chat.completions.create(
            model=self.model_name,
            messages=formatted_messages,
            tools=openai_tools,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        choice = response.choices[0]
        content = choice.message.content or ""
        
        # 解析 thinking
        thinking = ""
        think_match = re.search(r'<think>(.*?)</think>', content, re.DOTALL)
        if think_match:
            thinking = think_match.group(1).strip()
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
            
        result = {
            "success": True,
            "message": {
                "role": "assistant",
                "content": content,
                "thinking": thinking
            }
        }
        
        # 解析工具调用
        if choice.message.tool_calls:
            tool_calls = []
            for tc in choice.message.tool_calls:
                tool_calls.append({
                    "tool_name": tc.function.name,
                    "parameters": json.loads(tc.function.arguments)
                })
            result["message"]["tool_calls"] = tool_calls
            
        return result
        
    async def simple_generate(self, prompt: str, max_tokens: int = 512) -> str:
        """简单文本生成"""
        messages = [{"role": "user", "content": prompt}]
        result = await self.chat_completion(messages, max_tokens=max_tokens)
        if result.get("success"):
            return result["message"]["content"]
        return ""
