#!/usr/bin/env python3
"""
本地Qwen3-8B LLM服务
提供本地化的大语言模型推理能力，支持工具调用
"""

import logging
import json
import torch
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig
import re

logger = logging.getLogger(__name__)


def extract_title_from_first_chunk(first_chunk_content: str) -> Optional[str]:
    """
    从第一个 chunk 中提取标题（极简版）
    
    规则：
    1. 只检查第一行
    2. 长度 20-250 字符
    3. 不以句号/逗号/分号结尾
    4. 不匹配排除模式
    
    返回：标题 或 None
    """
    if not first_chunk_content:
        return None
    
    lines = [line.strip() for line in first_chunk_content.split('\n') if line.strip()]
    if not lines:
        return None
    
    first_line = lines[0]
    
    # 检查 1：长度
    if not (20 <= len(first_line) <= 250):
        return None
    
    # 检查 2：结尾（不能是句子结尾）
    # 允许冒号结尾（常见于带副标题的学术论文）
    if first_line.endswith(('.', '。', ',', '，', ';', '；')):
        return None
    
    # 特殊处理：如果以冒号结尾，保留（这是常见的标题格式）
    # 例如："Title: Subtitle" 或 "Main Title:"
    
    # 检查 3：排除明显不是标题的模式
    exclude_patterns = [
        r'^\d{4}$',                    # 单独的年份
        r'^(abstract|摘要)$',          # 单独的"Abstract"
        r'^(page|第.*?页)',            # 页码
        r'^(author|作者|by)\s*:',     # 作者标记
    ]
    
    if any(re.search(pattern, first_line, re.IGNORECASE) for pattern in exclude_patterns):
        return None
    
    return first_line

class LocalQwenService:
    """本地Qwen3-8B服务"""
    
    def __init__(self, model_path: str = None, device: str = "auto", session_manager=None):
        """
        初始化本地Qwen服务
        
        Args:
            model_path: 模型路径，默认使用项目内的Qwen3-8B
            device: 计算设备，auto/cuda/cpu
            session_manager: 会话管理器（用于获取文档信息）
        """
        self.model_path = model_path or "/home/Research_work/24_yzlin/LCA-LLM/models/Qwen3-8B"
        self.device = self._setup_device(device)
        self.session_manager = session_manager  # ✅ 保存 session_manager
        self.tokenizer = None
        self.model = None
        self.generation_config = None
        self.is_initialized = False
        
        logger.info(f"LocalQwenService初始化，模型路径: {self.model_path}, 设备: {self.device}")
    
    def _setup_device(self, device: str) -> str:
        """设置计算设备"""
        if device == "auto":
            if torch.cuda.is_available():
                device = "cuda"
                logger.info(f"检测到CUDA，使用GPU: {torch.cuda.get_device_name()}")
            else:
                device = "cpu"
                logger.info("未检测到CUDA，使用CPU")
        return device
    
    async def initialize(self):
        """异步初始化模型"""
        if self.is_initialized:
            return
            
        try:
            logger.info("开始加载Qwen3-8B模型...")
            
            # 加载tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True
            )
            logger.info("Tokenizer加载完成")
            
            # 加载模型
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
                trust_remote_code=True
            )
            
            if self.device == "cpu":
                self.model = self.model.to(self.device)
            
            logger.info("模型加载完成")
            
            # 设置生成配置
            self.generation_config = GenerationConfig.from_pretrained(
                self.model_path,
                trust_remote_code=True
            )
            
            # 调整生成参数
            self.generation_config.max_new_tokens = 2048
            self.generation_config.temperature = 0.7
            self.generation_config.top_p = 0.8
            self.generation_config.do_sample = True
            self.generation_config.repetition_penalty = 1.05
            
            self.is_initialized = True
            logger.info("Qwen3-8B服务初始化完成")
            
        except Exception as e:
            logger.error(f"初始化Qwen3-8B服务失败: {str(e)}")
            raise
    
    async def chat_completion(self, 
                            messages: List[Dict[str, str]], 
                            tools: List[Dict[str, Any]] = None,
                            max_tokens: int = 2048,
                            temperature: float = 0.7) -> Dict[str, Any]:
        """
        聊天补全接口
        
        Args:
            messages: 对话历史，格式为[{"role": "user/assistant", "content": "..."}]
            tools: 可用工具列表
            max_tokens: 最大生成token数
            temperature: 温度参数
            
        Returns:
            Dict[str, Any]: 生成结果
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # 构建输入prompt
            prompt = self._build_chat_prompt(messages, tools)
            
            # Tokenize
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=4096)
            inputs = inputs.to(self.device)
            
            # 更新生成配置
            self.generation_config.max_new_tokens = max_tokens
            self.generation_config.temperature = temperature
            
            # 生成响应
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    generation_config=self.generation_config,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # 解码响应
            response = self.tokenizer.decode(
                outputs[0][inputs.input_ids.shape[1]:], 
                skip_special_tokens=True
            )
            
            logger.info(f"📝 LLM 原始响应（前200字符）: {response[:200]}")
            
            # 🔥 解析思考过程（<think> 标签）
            import re
            thinking_content = ""
            actual_response = response.strip()
            
            # 检查是否包含 <think> 标签（处理多个标签和格式错误）
            think_pattern = r'<think>(.*?)</think>'
            think_match = re.search(think_pattern, response, re.DOTALL)
            
            if think_match:
                thinking_content = think_match.group(1).strip()
                # 移除所有 <think>...</think> 标签对
                actual_response = re.sub(think_pattern, '', response, flags=re.DOTALL).strip()
                # 移除孤立的 </think> 标签（格式错误的情况）
                actual_response = re.sub(r'</think>', '', actual_response, flags=re.IGNORECASE).strip()
                logger.info(f"💭 检测到思考过程，长度: {len(thinking_content)} 字符")
            
            # 解析工具调用（使用清理后的响应）
            tool_calls = self._parse_tool_calls(actual_response) if tools else None
            
            # 🔥 进一步清理：如果有工具调用，从响应中移除 <tool_call> 标签
            clean_content = actual_response
            if tool_calls:
                clean_content = re.sub(r'<tool_call>.*?</tool_call>', '', actual_response, flags=re.DOTALL).strip()
                logger.info(f"🧹 清理工具调用标签后，content 长度: {len(clean_content)} (原始: {len(actual_response)})")
                logger.info(f"🧹 清理后的 content（前200字符）: {clean_content[:200]}")
            
            result = {
                "success": True,
                "message": {
                    "role": "assistant",
                    "content": clean_content  # 使用清理后的内容
                },
                "thinking": thinking_content,  # 🔥 新增：思考过程
                "usage": {
                    "prompt_tokens": inputs.input_ids.shape[1],
                    "completion_tokens": outputs.shape[1] - inputs.input_ids.shape[1],
                    "total_tokens": outputs.shape[1]
                }
            }
            
            if tool_calls:
                result["message"]["tool_calls"] = tool_calls
            
            return result
            
        except Exception as e:
            logger.error(f"聊天补全失败: {str(e)}")
            return {
                "success": False,
                "error": f"生成响应时出错: {str(e)}"
            }
    
    def _build_chat_prompt(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]] = None) -> str:
        """构建聊天prompt"""
        
        # 🔥 提取 pdf_session_id（从简化的 system message 中）
        pdf_session_id = None
        mode = "standalone"
        for msg in messages:
            if msg.get("role") == "system":
                content = msg.get("content", "")
                # 新格式：MODE: document_based\nPDF_SESSION_ID: xxx
                if "PDF_SESSION_ID:" in content:
                    match = re.search(r"PDF_SESSION_ID:\s*([a-f0-9-]+)", content)
                    if match:
                        pdf_session_id = match.group(1)
                        mode = "document_based"
                        logger.info(f"📝 提取到 pdf_session_id: {pdf_session_id}")
                elif "MODE: standalone" in content:
                    mode = "standalone"
                    logger.info(f"📝 检测到 standalone 模式")
                break
        
        system_prompt = """You are an LCA (Life Cycle Assessment) specialist assistant with access to document analysis tools.

Use tools to extract and record data from documents.

**AVAILABLE TOOLS**:
• search_document(query) - Search for one keyword
• search_document(queries) - Batch search for multiple related keywords (saves tokens)
• record_parameter(parameter_name, parameter_value, selected_chunk, parameter_unit) - Record raw parameter values
• record_calculation(expression, result, unit, data_dependencies) - Record calculations
• record_process_flow(flow_type, category, name, value, unit, selected_chunk, link_to) - Record LCI inventory data
• get_session_summary() - View all recorded data
• execute_calculation(expression, variables) - Verify calculations
• record_pivot_failure(failed_query) - Record failed searches

**IMPORTANT**:
- Extract exact values from documents (no estimation)
- Provide selected_chunk when recording data from documents
- Session ID is automatically injected"""
        
        # 🔥 动态注入文档上下文（如果有 PDF）
        if pdf_session_id:
            # 获取文档信息
            document_name = "Unknown Document"
            document_title = None
            
            if self.session_manager:
                session_data = self.session_manager.get_session(pdf_session_id)
                if session_data:
                    # 1. 获取文档名称
                    document_name = session_data.original_filename
                    
                    # 2. 尝试提取标题（保守策略）
                    if hasattr(session_data, 'documents') and session_data.documents:
                        first_chunk = session_data.documents[0].page_content
                        document_title = extract_title_from_first_chunk(first_chunk)
                        
                        # 日志输出提取结果
                        if document_title:
                            logger.info(f"✅ 成功提取文档标题: {document_title[:50]}...")
                        else:
                            logger.info(f"⚠️ 无法提取文档标题（保守策略），仅使用文档名称")
            
            # 构建文档上下文
            system_prompt += f"""

**DOCUMENT CONTEXT**: 
A PDF document has been uploaded and is ready for analysis.
- Document Name: "{document_name}"
"""
            
            # 只有在成功提取标题时才添加
            if document_title:
                system_prompt += f"""- Document Title: "{document_title}"
"""
            
            system_prompt += f"""- Document ID: {pdf_session_id[:8]}...
"""
            
            # 🔥 动态注入 chunk 0 和 chunk 1 的内容（用于快速定位 Functional Unit）
            if self.session_manager:
                session_data = self.session_manager.get_session(pdf_session_id)
                if session_data and hasattr(session_data, 'documents') and session_data.documents:
                    # 获取 chunk 0（完整内容，与训练时一致）
                    if len(session_data.documents) > 0:
                        chunk_0_content = session_data.documents[0].page_content  # 🔥 完整内容
                        system_prompt += f"""
**CHUNK 0 PREVIEW** (Executive Summary / Introduction):
"{chunk_0_content}"
"""
                    
                    # 获取 chunk 1（完整内容，与训练时一致）
                    if len(session_data.documents) > 1:
                        chunk_1_content = session_data.documents[1].page_content  # 🔥 完整内容
                        system_prompt += f"""
**CHUNK 1 PREVIEW**:
"{chunk_1_content}"
"""
            
            system_prompt += f"""
**AUTOMATIC SESSION INJECTION**: 
When you call document-related tools (search_document, record_parameter, record_calculation, record_process_flow, get_session_summary, define_lca_scope, record_pivot_failure), the system will AUTOMATICALLY inject the session_id for you.

You do NOT need to ask the user for session_id. Just call the tools directly with other required parameters (e.g., "query" for search_document)."""
        
        if tools:
            system_prompt += "\n\n# Tools\n\nYou may call one or more functions to assist with the user query.\n\nYou are provided with function signatures within <tools></tools> XML tags:\n<tools>"
            for tool in tools:
                system_prompt += f"\n{json.dumps(tool, ensure_ascii=False)}"
            system_prompt += "\n</tools>\n\nFor each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:\n<tool_call>\n{\"name\": <function-name>, \"arguments\": <args-json-object>}\n</tool_call>"
        
        # 构建完整prompt
        prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
        
        # 🔥 调试：打印 System Prompt 关键部分以验证
        if "GENERAL WORKFLOW LOGIC" in system_prompt:
            print(f"\n✅ 使用简化版 System Prompt (包含 GENERAL WORKFLOW LOGIC)\n", flush=True)
        else:
            print(f"\n⚠️ 使用旧版 System Prompt\n", flush=True)
        
        # 🔥 按照官方 chat_template.md 格式构建消息
        i = 0
        while i < len(messages):
            msg = messages[i]
            role = msg["role"]
            content = msg.get("content", "")
            
            # Skip system messages as we already have our own system prompt
            if role == "system":
                i += 1
                continue
            
            # 🔥 处理 tool role：按照官方格式包装为 <tool_response>
            if role == "tool":
                # 收集连续的 tool 消息
                tool_responses = []
                while i < len(messages) and messages[i]["role"] == "tool":
                    tool_responses.append(messages[i]["content"])
                    i += 1
                
                # 包装为官方格式：role=user + <tool_response> 标签
                prompt += "<|im_start|>user\n"
                for tool_content in tool_responses:
                    prompt += f"<tool_response>\n{tool_content}\n</tool_response>"
                    if len(tool_responses) > 1:  # 多个 tool response 之间换行
                        prompt += "\n"
                prompt += "<|im_end|>\n"
            else:
                # 其他角色（user, assistant）正常处理
                prompt += f"<|im_start|>{role}\n{content}<|im_end|>\n"
                i += 1
        
        prompt += "<|im_start|>assistant\n"
        
        return prompt
    
    def _parse_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """解析工具调用（匹配官方格式）"""
        tool_calls = []
        
        # 使用正则表达式查找工具调用
        pattern = r'<tool_call>\s*(\{.*?\})\s*</tool_call>'
        matches = re.findall(pattern, response, re.DOTALL)
        
        for match in matches:
            try:
                tool_call_data = json.loads(match)
                
                # 转换官方格式 {"name": "xxx", "arguments": {...}} 
                # 到我们的内部格式 {"tool_name": "xxx", "parameters": {...}}
                if "name" in tool_call_data:
                    converted_call = {
                        "tool_name": tool_call_data["name"],
                        "parameters": tool_call_data.get("arguments", {})
                    }
                    tool_calls.append(converted_call)
                    logger.info(f"解析到工具调用: {converted_call['tool_name']}")
                else:
                    # 兼容旧格式
                    tool_calls.append(tool_call_data)
                    
            except json.JSONDecodeError as e:
                logger.warning(f"解析工具调用失败: {match}, 错误: {e}")
                continue
        
        return tool_calls
    
    async def simple_generate(self, prompt: str, max_tokens: int = 512) -> str:
        """
        简单文本生成接口
        
        Args:
            prompt: 输入提示
            max_tokens: 最大生成token数
            
        Returns:
            str: 生成的文本
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
            inputs = inputs.to(self.device)
            
            self.generation_config.max_new_tokens = max_tokens
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    generation_config=self.generation_config,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            response = self.tokenizer.decode(
                outputs[0][inputs.input_ids.shape[1]:], 
                skip_special_tokens=True
            )
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"文本生成失败: {str(e)}")
            return f"生成失败: {str(e)}"
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "model_name": "Qwen3-8B",
            "model_path": self.model_path,
            "device": self.device,
            "is_initialized": self.is_initialized,
            "supports_tools": True,
            "max_context_length": 4096
        }
    
    def cleanup(self):
        """清理资源"""
        if self.model:
            del self.model
        if self.tokenizer:
            del self.tokenizer
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        self.is_initialized = False
        logger.info("Qwen3-8B服务资源清理完成")
    
    def cleanup(self):
        """清理资源"""
        if self.model:
            del self.model
        if self.tokenizer:
            del self.tokenizer
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        self.is_initialized = False
        logger.info("Qwen3-8B服务资源清理完成")
