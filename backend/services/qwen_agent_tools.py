"""
Qwen-Agent 工具定义
将我们的 LCA 工具注册为 Qwen-Agent 的 BaseTool

这些工具会被 Qwen-Agent 的 Assistant 自动调用和管理
"""

import logging
import json
import asyncio
from typing import Dict, Any, List, Union

# 解决嵌套事件循环问题
try:
    import nest_asyncio
    nest_asyncio.apply()
    NEST_ASYNCIO_AVAILABLE = True
except ImportError:
    NEST_ASYNCIO_AVAILABLE = False

logger = logging.getLogger(__name__)


def run_async(coro):
    """安全地运行异步函数"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果事件循环已在运行，创建新任务
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result(timeout=60)
        else:
            return loop.run_until_complete(coro)
    except Exception as e:
        logger.error(f"run_async 失败: {e}")
        # 尝试直接运行
        return asyncio.run(coro)

# 尝试导入 qwen-agent
try:
    from qwen_agent.tools.base import BaseTool, register_tool
    QWEN_AGENT_AVAILABLE = True
except ImportError:
    QWEN_AGENT_AVAILABLE = False
    logger.warning("qwen-agent 未安装")
    # 创建占位符
    class BaseTool:
        pass
    def register_tool(name):
        def decorator(cls):
            return cls
        return decorator


# 全局 tool_service 引用，由 QwenAgentServiceV2 设置
_tool_service = None
_current_session_id = None


def set_tool_service(tool_service, session_id: str = None):
    """设置工具服务引用"""
    global _tool_service, _current_session_id
    _tool_service = tool_service
    _current_session_id = session_id
    logger.info(f"✅ Qwen-Agent 工具服务已设置，session_id: {session_id}")


def get_tool_service():
    """获取工具服务"""
    return _tool_service


def get_session_id():
    """获取当前会话 ID"""
    return _current_session_id


@register_tool('search_document')
class SearchDocumentTool(BaseTool):
    """搜索文档工具"""
    
    description = "Search uploaded PDF document content. Use this to find specific information in the document."
    parameters = [
        {
            "name": "query",
            "type": "string",
            "description": "Search query, e.g., 'energy consumption', 'material input', 'CO2 emission'",
            "required": True
        },
        {
            "name": "max_results",
            "type": "integer",
            "description": "Maximum number of results to return (default: 5)",
            "required": False
        }
    ]
    
    def call(self, params: Union[str, dict], **kwargs) -> str:
        """执行文档搜索"""
        try:
            if isinstance(params, str):
                params = json.loads(params)
                
            query = params.get("query", "")
            max_results = params.get("max_results", 5)
            session_id = get_session_id()
            
            if not session_id:
                return json.dumps({"error": "No document session available"})
                
            tool_service = get_tool_service()
            if not tool_service:
                return json.dumps({"error": "Tool service not initialized"})
            
            # 调用实际的搜索方法
            result = run_async(
                tool_service.search_document(
                    session_id=session_id,
                    query=query,
                    max_results=max_results
                )
            )
            
            logger.info(f"🔍 search_document 执行完成，找到 {len(result.get('results', []))} 个结果")
            return json.dumps(result, ensure_ascii=False, default=str)
            
        except Exception as e:
            logger.error(f"search_document 执行失败: {e}")
            return json.dumps({"error": str(e)})


@register_tool('record_process_flow')
class RecordProcessFlowTool(BaseTool):
    """记录 LCI 流程数据工具"""
    
    description = "Record LCI (Life Cycle Inventory) flow data including inputs and outputs with quantities and units."
    parameters = [
        {
            "name": "flow_type",
            "type": "string",
            "description": "Flow type: 'Input' or 'Output'",
            "required": True
        },
        {
            "name": "category",
            "type": "string",
            "description": "Category: Raw Material, Process Energy, Post-processing Energy, Feedstock Energy, Gas, Cooling Media, Product, Recovered Material, Waste, Emission",
            "required": True
        },
        {
            "name": "name",
            "type": "string",
            "description": "Name of the flow, e.g., 'Electricity', 'Steel', 'CO2'",
            "required": True
        },
        {
            "name": "value",
            "type": "number",
            "description": "Quantity value",
            "required": True
        },
        {
            "name": "unit",
            "type": "string",
            "description": "Unit of measurement, e.g., 'kWh', 'kg', 'MJ'",
            "required": True
        },
        {
            "name": "selected_chunk",
            "type": "string",
            "description": "Source text from document for traceability",
            "required": False
        },
        {
            "name": "note",
            "type": "string",
            "description": "Additional notes",
            "required": False
        }
    ]
    
    def call(self, params: Union[str, dict], **kwargs) -> str:
        """执行记录"""
        try:
            if isinstance(params, str):
                params = json.loads(params)
                
            session_id = get_session_id()
            if not session_id:
                return json.dumps({"error": "No document session available"})
                
            tool_service = get_tool_service()
            if not tool_service:
                return json.dumps({"error": "Tool service not initialized"})
            
            # 🔥 参数名映射（兼容 LLM 可能使用的不同参数名）
            if "flow_name" in params:
                params["name"] = params.pop("flow_name")
            if "quantity" in params:
                params["value"] = params.pop("quantity")
            if "amount" in params:
                params["value"] = params.pop("amount")
            if "notes" in params:
                params["note"] = params.pop("notes")
            
            # 添加 session_id
            params["session_id"] = session_id
            
            # 调用实际的记录方法
            result = run_async(
                tool_service.record_process_flow(**params)
            )
            
            logger.info(f"📝 record_process_flow 执行完成: {params.get('name')}")
            return json.dumps(result, ensure_ascii=False, default=str)
            
        except Exception as e:
            logger.error(f"record_process_flow 执行失败: {e}")
            return json.dumps({"error": str(e)})


@register_tool('record_parameter')
class RecordParameterTool(BaseTool):
    """记录中间参数工具"""
    
    description = "Record intermediate parameters for calculations, such as efficiency values, conversion factors, etc."
    parameters = [
        {
            "name": "parameter_name",
            "type": "string",
            "description": "Name of the parameter",
            "required": True
        },
        {
            "name": "value",
            "type": "number",
            "description": "Parameter value",
            "required": True
        },
        {
            "name": "unit",
            "type": "string",
            "description": "Unit of measurement",
            "required": True
        },
        {
            "name": "selected_chunk",
            "type": "string",
            "description": "Source text from document",
            "required": False
        },
        {
            "name": "notes",
            "type": "string",
            "description": "Additional notes",
            "required": False
        }
    ]
    
    def call(self, params: Union[str, dict], **kwargs) -> str:
        """执行记录"""
        try:
            if isinstance(params, str):
                params = json.loads(params)
                
            session_id = get_session_id()
            if not session_id:
                return json.dumps({"error": "No document session available"})
                
            tool_service = get_tool_service()
            if not tool_service:
                return json.dumps({"error": "Tool service not initialized"})
            
            params["session_id"] = session_id
            
            result = run_async(
                tool_service.record_parameter(**params)
            )
            
            logger.info(f"📝 record_parameter 执行完成: {params.get('parameter_name')}")
            return json.dumps(result, ensure_ascii=False, default=str)
            
        except Exception as e:
            logger.error(f"record_parameter 执行失败: {e}")
            return json.dumps({"error": str(e)})


@register_tool('define_lca_scope')
class DefineLCAScopeTool(BaseTool):
    """定义 LCA 范围工具"""
    
    description = "Define LCA scope parameters: Functional Unit, System Boundary, or Geographical Scope"
    parameters = [
        {
            "name": "parameter_name",
            "type": "string",
            "description": "Parameter type: 'Functional Unit', 'System Boundary', or 'Geographical Scope'",
            "required": True
        },
        {
            "name": "value",
            "type": "string",
            "description": "Parameter value, e.g., '1 kg product', 'cradle-to-gate', 'China'",
            "required": True
        },
        {
            "name": "selected_chunk",
            "type": "string",
            "description": "Source text from document",
            "required": False
        },
        {
            "name": "notes",
            "type": "string",
            "description": "Additional notes",
            "required": False
        }
    ]
    
    def call(self, params: Union[str, dict], **kwargs) -> str:
        """执行定义"""
        try:
            if isinstance(params, str):
                params = json.loads(params)
                
            session_id = get_session_id()
            if not session_id:
                return json.dumps({"error": "No document session available"})
                
            tool_service = get_tool_service()
            if not tool_service:
                return json.dumps({"error": "Tool service not initialized"})
            
            params["session_id"] = session_id
            
            result = run_async(
                tool_service.define_lca_scope(**params)
            )
            
            logger.info(f"📝 define_lca_scope 执行完成: {params.get('parameter_name')}")
            return json.dumps(result, ensure_ascii=False, default=str)
            
        except Exception as e:
            logger.error(f"define_lca_scope 执行失败: {e}")
            return json.dumps({"error": str(e)})


@register_tool('get_session_summary')
class GetSessionSummaryTool(BaseTool):
    """获取会话摘要工具"""
    
    description = "Get a summary of all recorded data in the current session, including LCI flows and parameters."
    parameters = []
    
    def call(self, params: Union[str, dict] = None, **kwargs) -> str:
        """获取摘要"""
        try:
            session_id = get_session_id()
            if not session_id:
                return json.dumps({"error": "No document session available"})
                
            tool_service = get_tool_service()
            if not tool_service:
                return json.dumps({"error": "Tool service not initialized"})
            
            result = run_async(
                tool_service.get_session_summary(session_id=session_id)
            )
            
            logger.info(f"📊 get_session_summary 执行完成")
            return json.dumps(result, ensure_ascii=False, default=str)
            
        except Exception as e:
            logger.error(f"get_session_summary 执行失败: {e}")
            return json.dumps({"error": str(e)})


@register_tool('execute_calculation')
class ExecuteCalculationTool(BaseTool):
    """执行计算工具"""
    
    description = "Execute calculations on recorded parameters using formulas."
    parameters = [
        {
            "name": "formula",
            "type": "string",
            "description": "Calculation formula, e.g., 'energy_per_part = total_energy / num_parts'",
            "required": True
        },
        {
            "name": "result_name",
            "type": "string",
            "description": "Name for the calculation result",
            "required": True
        },
        {
            "name": "result_unit",
            "type": "string",
            "description": "Unit for the result",
            "required": True
        }
    ]
    
    def call(self, params: Union[str, dict], **kwargs) -> str:
        """执行计算"""
        try:
            if isinstance(params, str):
                params = json.loads(params)
                
            session_id = get_session_id()
            if not session_id:
                return json.dumps({"error": "No document session available"})
                
            tool_service = get_tool_service()
            if not tool_service:
                return json.dumps({"error": "Tool service not initialized"})
            
            params["session_id"] = session_id
            
            result = run_async(
                tool_service.execute_calculation(**params)
            )
            
            logger.info(f"🔢 execute_calculation 执行完成: {params.get('result_name')}")
            return json.dumps(result, ensure_ascii=False, default=str)
            
        except Exception as e:
            logger.error(f"execute_calculation 执行失败: {e}")
            return json.dumps({"error": str(e)})


# 获取所有工具类列表
def get_lca_tools() -> List[type]:
    """获取所有 LCA 工具类"""
    if not QWEN_AGENT_AVAILABLE:
        return []
    return [
        SearchDocumentTool,
        RecordProcessFlowTool,
        RecordParameterTool,
        DefineLCAScopeTool,
        GetSessionSummaryTool,
        ExecuteCalculationTool,
    ]


def get_lca_tool_names() -> List[str]:
    """获取所有 LCA 工具名称"""
    return [
        'search_document',
        'record_process_flow',
        'record_parameter',
        'define_lca_scope',
        'get_session_summary',
        'execute_calculation',
    ]
