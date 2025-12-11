"""
LCIA 计算服务

完整流程：
1. 从 lca_actions 拉取 session 数据
2. 与 ecoinvent flows/processes 匹配
3. 选择 LCIA 方法
4. 生成 olca-ipc 调用参数
5. 通过 IPC 调用 openLCA 计算
6. 返回 LCIA 结果
"""

import logging
from typing import Dict, Any, List, Optional
from .mongodb_manager import mongodb_manager
from .ecoinvent_matcher import get_ecoinvent_matcher
from .openlca_client import get_openlca_client

logger = logging.getLogger(__name__)


class LCIACalculator:
    """LCIA 计算器"""
    
    def __init__(self):
        self.db = None
        self.matcher = None
        self.olca_client = None
        
    def _ensure_initialized(self):
        """确保初始化"""
        if self.db is None:
            self.db = mongodb_manager.get_database()
        if self.matcher is None:
            self.matcher = get_ecoinvent_matcher()
            # 设置 matcher 的 db 连接
            if self.matcher.db is None:
                self.matcher.db = self.db
            self.matcher._ensure_initialized()
        if self.olca_client is None:
            self.olca_client = get_openlca_client()
    
    def get_all_sessions(self) -> Dict[str, Any]:
        """
        获取所有有 LCI 数据的 session 列表
        
        Returns:
            session 列表
        """
        self._ensure_initialized()
        
        try:
            # 获取所有唯一的 session_id
            sessions = self.db.lca_actions.distinct("session_id")
            
            result = []
            for sid in sessions:
                # 获取每个 session 的流数量
                flow_count = self.db.lca_actions.count_documents({
                    "session_id": sid,
                    "record_type": "flow"
                })
                
                # 获取 scope 信息
                scope = self.db.lca_actions.find_one({
                    "session_id": sid,
                    "record_type": "scope"
                })
                
                result.append({
                    "session_id": sid,
                    "flow_count": flow_count,
                    "functional_unit": scope.get("description", "N/A") if scope else "N/A"
                })
            
            return {
                "success": True,
                "sessions": result,
                "total": len(result)
            }
            
        except Exception as e:
            logger.error(f"获取 session 列表失败: {e}")
            return {"success": False, "error": str(e)}
    
    def get_session_lci_data(self, session_id: str) -> Dict[str, Any]:
        """
        获取会话的 LCI 数据
        
        Args:
            session_id: 会话 ID
            
        Returns:
            LCI 数据，包括 scope 和 flows
        """
        self._ensure_initialized()
        
        try:
            # 获取 scope 定义
            scope = self.db.lca_actions.find_one({
                "session_id": session_id,
                "record_type": "scope"
            })
            
            # 获取所有 flows
            flows = list(self.db.lca_actions.find({
                "session_id": session_id,
                "record_type": "flow"
            }))
            
            # 按类别分组
            inputs = []
            outputs = []
            
            for flow in flows:
                flow_data = {
                    "action_id": flow.get("action_id"),
                    "name": flow.get("name"),
                    "value": flow.get("value"),
                    "unit": flow.get("unit"),
                    "category": flow.get("category"),
                    "flow_type": flow.get("flow_type"),
                    "ecoinvent_match": flow.get("ecoinvent_match"),
                }
                
                # 根据类别判断输入/输出
                category = flow.get("category", "")
                if category in ["Raw Material", "Process Energy", "Post-processing Energy", 
                               "Feedstock Energy", "Gas", "Cooling Media"]:
                    inputs.append(flow_data)
                else:
                    outputs.append(flow_data)
            
            return {
                "success": True,
                "session_id": session_id,
                "scope": {
                    "functional_unit": scope.get("description") if scope else None,
                    "value": scope.get("value") if scope else None,
                    "unit": scope.get("unit") if scope else None,
                } if scope else None,
                "inputs": inputs,
                "outputs": outputs,
                "total_flows": len(flows)
            }
            
        except Exception as e:
            logger.error(f"获取 LCI 数据失败: {e}")
            return {"success": False, "error": str(e)}
    
    def get_lcia_methods(self, limit: int = 50) -> Dict[str, Any]:
        """
        获取可用的 LCIA 方法列表
        
        Returns:
            LCIA 方法列表
        """
        self._ensure_initialized()
        
        try:
            methods = list(self.db.lcia_methods.find(
                {},
                {"uuid": 1, "name": 1, "category": 1, "impact_categories_count": 1, "_id": 0}
            ).limit(limit))
            
            return {
                "success": True,
                "methods": methods,
                "total": len(methods)
            }
            
        except Exception as e:
            logger.error(f"获取 LCIA 方法失败: {e}")
            return {"success": False, "error": str(e)}
    
    def get_lcia_method_details(self, method_uuid: str) -> Dict[str, Any]:
        """
        获取 LCIA 方法详情，包括影响类别
        
        Args:
            method_uuid: LCIA 方法 UUID
            
        Returns:
            方法详情
        """
        self._ensure_initialized()
        
        try:
            method = self.db.lcia_methods.find_one(
                {"uuid": method_uuid},
                {"embedding_vector": 0}
            )
            
            if not method:
                return {"success": False, "error": "未找到该 LCIA 方法"}
            
            return {
                "success": True,
                "method": {
                    "uuid": method.get("uuid"),
                    "name": method.get("name"),
                    "category": method.get("category"),
                    "impact_categories": method.get("impactCategories", []),
                }
            }
            
        except Exception as e:
            logger.error(f"获取 LCIA 方法详情失败: {e}")
            return {"success": False, "error": str(e)}
    
    def match_all_flows(self, session_id: str, use_llm_rewrite: bool = False) -> Dict[str, Any]:
        """
        批量匹配会话中所有流
        
        Args:
            session_id: 会话 ID
            use_llm_rewrite: 是否使用 LLM 辅助重写流名称以提高匹配精度
            
        Returns:
            匹配结果
        """
        self._ensure_initialized()
        return self.matcher.batch_match_session(session_id, use_llm_rewrite=use_llm_rewrite)
    
    def prepare_lcia_calculation(self, 
                                  session_id: str,
                                  lcia_method_uuid: str,
                                  flow_mappings: List[Dict] = None) -> Dict[str, Any]:
        """
        准备 LCIA 计算参数
        
        Args:
            session_id: 会话 ID
            lcia_method_uuid: LCIA 方法 UUID
            flow_mappings: 流映射列表 [{action_id, ecoinvent_uuid}, ...]
            
        Returns:
            准备好的计算参数
        """
        self._ensure_initialized()
        
        try:
            # 获取 LCI 数据
            lci_data = self.get_session_lci_data(session_id)
            if not lci_data.get("success"):
                return lci_data
            
            # 获取 LCIA 方法
            method = self.db.lcia_methods.find_one({"uuid": lcia_method_uuid})
            if not method:
                return {"success": False, "error": "未找到 LCIA 方法"}
            
            # 构建计算参数
            exchanges = []
            all_flows = lci_data.get("inputs", []) + lci_data.get("outputs", [])
            
            for flow in all_flows:
                ecoinvent_uuid = None
                
                # 检查是否有预设映射
                if flow_mappings:
                    for mapping in flow_mappings:
                        if mapping.get("action_id") == flow.get("action_id"):
                            ecoinvent_uuid = mapping.get("ecoinvent_uuid")
                            break
                
                # 如果没有映射，使用已确认的匹配
                if not ecoinvent_uuid and flow.get("ecoinvent_match"):
                    ecoinvent_uuid = flow["ecoinvent_match"].get("uuid")
                
                if ecoinvent_uuid:
                    exchanges.append({
                        "flow_uuid": ecoinvent_uuid,
                        "amount": flow.get("value", 0),
                        "unit": flow.get("unit"),
                        "is_input": flow.get("category") in [
                            "Raw Material", "Process Energy", "Post-processing Energy",
                            "Feedstock Energy", "Gas", "Cooling Media"
                        ]
                    })
            
            return {
                "success": True,
                "session_id": session_id,
                "lcia_method": {
                    "uuid": method.get("uuid"),
                    "name": method.get("name"),
                },
                "exchanges": exchanges,
                "total_mapped": len(exchanges),
                "total_flows": len(all_flows),
                "ready_for_calculation": len(exchanges) > 0
            }
            
        except Exception as e:
            logger.error(f"准备 LCIA 计算失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _create_process_in_openlca(self, 
                                    session_id: str,
                                    exchanges: List[Dict],
                                    functional_unit: Dict) -> Dict[str, Any]:
        """
        在 openLCA 中创建临时 Process
        
        Args:
            session_id: 会话 ID
            exchanges: 交换列表（包含 flow_uuid, amount, unit, is_input）
            functional_unit: 功能单位信息
            
        Returns:
            创建结果，包含 process_id
        """
        try:
            import uuid
            
            # 构建 openLCA Process JSON-LD 格式
            process_id = str(uuid.uuid4())
            fu_desc = functional_unit.get("description", "1 unit")
            
            # 构建 exchanges
            olca_exchanges = []
            for i, ex in enumerate(exchanges):
                olca_exchange = {
                    "@type": "Exchange",
                    "internalId": i + 1,
                    "flow": {"@type": "Flow", "@id": ex.get("flow_uuid")},
                    "amount": ex.get("amount", 0),
                    "isInput": ex.get("is_input", True),
                    "isQuantitativeReference": False,
                }
                olca_exchanges.append(olca_exchange)
            
            # 添加一个参考产品流（功能单位）
            # 注意：这需要一个已存在的产品流，或者创建一个新的
            ref_exchange = {
                "@type": "Exchange",
                "internalId": len(olca_exchanges) + 1,
                "amount": functional_unit.get("value", 1),
                "isInput": False,
                "isQuantitativeReference": True,
            }
            olca_exchanges.append(ref_exchange)
            
            process_data = {
                "@type": "Process",
                "@id": process_id,
                "name": f"LCA-LLM Process - {session_id[:8]}",
                "description": f"Auto-generated process from LCA-LLM session. FU: {fu_desc}",
                "processType": "UNIT_PROCESS",
                "exchanges": olca_exchanges,
            }
            
            # 导入到 openLCA
            result = self.olca_client.import_process(process_data)
            
            if result.get("success"):
                return {
                    "success": True,
                    "process_id": process_id,
                    "exchanges_count": len(exchanges)
                }
            else:
                return {
                    "success": False,
                    "error": f"导入 Process 失败: {result.get('error')}"
                }
                
        except Exception as e:
            logger.error(f"创建 openLCA Process 失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _parse_impact_results(self, raw_result: Dict) -> List[Dict]:
        """
        解析 openLCA 计算结果
        
        Args:
            raw_result: openLCA 返回的原始结果
            
        Returns:
            格式化的影响结果列表
        """
        try:
            impact_results = []
            
            # openLCA 返回的结果格式可能因版本而异
            # 常见格式: {"impactResults": [{"impactCategory": {...}, "value": ...}, ...]}
            for ir in raw_result.get("impactResults", []):
                category = ir.get("impactCategory", {})
                impact_results.append({
                    "category": category.get("name", "Unknown"),
                    "value": ir.get("value", 0),
                    "unit": category.get("refUnit", ""),
                    "uuid": category.get("@id", ""),
                })
            
            return impact_results
            
        except Exception as e:
            logger.warning(f"解析影响结果失败: {e}")
            return []
    
    def calculate_lcia(self,
                       session_id: str,
                       lcia_method_uuid: str,
                       flow_mappings: List[Dict] = None) -> Dict[str, Any]:
        """
        执行 LCIA 计算
        
        通过 openLCA IPC 调用计算
        
        Args:
            session_id: 会话 ID
            lcia_method_uuid: LCIA 方法 UUID
            flow_mappings: 流映射
            
        Returns:
            LCIA 计算结果
        """
        self._ensure_initialized()
        
        try:
            # 准备计算参数
            prep = self.prepare_lcia_calculation(session_id, lcia_method_uuid, flow_mappings)
            if not prep.get("success"):
                return prep
            
            if not prep.get("ready_for_calculation"):
                return {
                    "success": False,
                    "error": "没有可用于计算的流映射，请先完成 ecoinvent 匹配"
                }
            
            # 检查 openLCA 连接
            olca_test = self.olca_client.test_connection()
            if not olca_test.get("success"):
                return {
                    "success": False,
                    "error": f"openLCA 连接失败: {olca_test.get('error')}"
                }
            
            # 执行 openLCA IPC 计算
            # 步骤 1: 创建临时 Process（包含所有 exchanges）
            process_result = self._create_process_in_openlca(
                session_id=session_id,
                exchanges=prep.get("exchanges", []),
                functional_unit=lci_data.get("functional_unit", {})
            )
            
            if not process_result.get("success"):
                return process_result
            
            process_id = process_result.get("process_id")
            
            # 步骤 2: 创建 Product System
            ps_result = self.olca_client.create_product_system(
                process_id=process_id,
                name=f"LCA-LLM Session {session_id[:8]}"
            )
            
            if not ps_result.get("success"):
                return {
                    "success": False,
                    "error": f"创建 Product System 失败: {ps_result.get('error')}"
                }
            
            product_system_id = ps_result.get("product_system", {}).get("@id")
            
            # 步骤 3: 执行 LCIA 计算
            calc_result = self.olca_client.calculate(
                product_system_id=product_system_id,
                impact_method_id=lcia_method_uuid
            )
            
            if not calc_result.get("success"):
                return {
                    "success": False,
                    "error": f"LCIA 计算失败: {calc_result.get('error')}"
                }
            
            # 解析计算结果
            raw_result = calc_result.get("result", {})
            
            return {
                "success": True,
                "session_id": session_id,
                "lcia_method": prep.get("lcia_method"),
                "results": {
                    "status": "completed",
                    "impact_results": self._parse_impact_results(raw_result),
                    "exchanges_count": prep.get("total_mapped"),
                    "process_id": process_id,
                    "product_system_id": product_system_id,
                },
                "raw_result": raw_result
            }
            
        except Exception as e:
            logger.error(f"LCIA 计算失败: {e}")
            return {"success": False, "error": str(e)}


# 全局实例
_calculator_instance = None

def get_lcia_calculator() -> LCIACalculator:
    """获取全局计算器实例"""
    global _calculator_instance
    if _calculator_instance is None:
        _calculator_instance = LCIACalculator()
    return _calculator_instance
