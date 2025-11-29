"""
逆向工程：从LCI数据生成工艺文档 v3.1.2

v3.1.2修复（表格PDF转换问题）：
- 强制要求表格前后空行（TABLE FORMATTING）
- 修复Pandoc表格识别问题

v3.1.1修复（术语泄露+格式问题）：
- 禁止LCA/LCI术语泄露（FORBIDDEN TERMINOLOGY）
- 禁止markdown代码块包裹（OUTPUT FORMAT）
- 强化Complex的Batch Record：Raw Sensor不显示计算结果

v3.1改进（特征引导+专家建议版）：
- 用"风格特征"代替"具体例子"，避免模板化
- Base Prompt通用化（适配短中长文档）
- 9种文档类型：短(1500-2500词) + 中(3000-4500词) + 长(5000-7000词)
- 增加对比数据标记规则（避免混淆LCI真实数据）
- Complex长文档局部聚合（保持可追溯性）
- Batch Record的Raw Sensor Dumps（更自然的参数化）

支持的难度级别：
- simple: 清晰集中（易于快速提取）
- medium: 分散叙述（需读多个section）
- complex: 参数呈现（需计算得结果）

文档类型体系：
【Tier 1 - 短文档 1500-2500词】
- batch_production_record: 批次生产记录
- build_job_log: 设备作业日志
- material_traceability: 物料追溯报告
- quality_inspection: 质量检验报告

【Tier 2 - 中文档 3000-4500词】
- technical_process_report: 技术工艺报告
- environmental_assessment: 环境评估总结
- multi_build_analysis: 多批次对比分析

【Tier 3 - 长文档 5000-7000词】
- research_case_study: 研究案例分析
- sustainability_report: 可持续性报告章节
"""

import json
import os
from typing import List, Dict
from openai import OpenAI

class DocumentReverseEngineer:
    """
    从LCI数据逆向生成工艺文档
    """
    
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        """
        初始化
        
        Args:
            api_key: DeepSeek API key
            base_url: API base URL
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
    
    def generate_document(
        self, 
        lci_data: Dict, 
        difficulty: str = "simple",
        document_type: str = "batch_production_record"
    ) -> str:
        """
        生成工艺文档
        
        Args:
            lci_data: LCI数据字典
                {
                    "process_name": "Ti6Al4V Femoral Stem Production",
                    "inputs": [
                        {"category": "Raw Material", "name": "Ti6Al4V Powder", "value": 20.83, "unit": "kg", "is_parent": True},
                        {"category": "Process Energy", "name": "Electricity - EOS M290", "value": 147.26, "unit": "kWh", "is_parent": True},
                        {"category": "Post-processing Energy", "name": "Heat treatment energy", "value": 2.5, "unit": "kWh", "is_parent": True},
                        {"category": "Feedstock Energy", "name": "Atomization energy", "value": 495, "unit": "MJ", "is_parent": True},
                        {"category": "Gas", "name": "Argon", "value": 10.5, "unit": "kg", "is_parent": True},
                        ...
                    ],
                    "outputs": [
                        {"category": "Product", "name": "Femoral Stems", "value": 1.77, "unit": "kg", "quantity": 20, "is_parent": True},
                        {"category": "Recovered Material", "name": "Recovered Ti6Al4V powder", "value": 3.2, "unit": "kg", "is_parent": True},
                        {"category": "Waste", "name": "Support structures", "value": 0.8, "unit": "kg", "is_parent": True},
                        ...
                    ],
                    "parameters": [
                        {"name": "Build Time", "value": 14.5, "unit": "h"},
                        {"name": "Laser Power", "value": 370, "unit": "W"},
                        ...
                    ]
                }
            difficulty: 难度等级 ("simple", "medium", "complex")
            document_type: 文档类型
                - "batch_production_record": 批量生产记录
                - "process_certification": 工艺认证报告
                - "material_traceability": 材料追溯报告
                - "build_job_log": 构建作业日志
        
        Returns:
            生成的文档文本（Markdown格式）
        """
        
        # 构建prompt
        prompt = self._build_prompt(lci_data, difficulty, document_type)
        
        # 调用LLM生成
        response = self.client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {"role": "system", "content": self._get_system_prompt(difficulty, document_type)},
                {"role": "user", "content": prompt}
            ],
            temperature=1.3,  # 高温度以最大化多样性和创造性
            max_tokens=32000   # DeepSeek Reasoner支持更大的输出
        )
        
        document_text = response.choices[0].message.content
        return document_text
    
    def _get_system_prompt(self, difficulty: str, document_type: str) -> str:
        """
        获取系统提示词（v3.1: 特征引导+专家建议版）
        
        设计原则：
        - 用"风格特征"代替"具体例子"（避免模板化）
        - Base层通用化（适配所有长度）
        - Document Type用"typical characteristics"描述
        - 让Deepseek自由创作，而非套模板
        
        v3.1新增：
        - 对比数据标记规则
        - Complex长文档局部聚合
        - Batch Record的Raw Sensor Dumps
        """
        
        # ============================================================
        # Base Prompt: 通用原则（适配所有文档类型和长度）
        # ============================================================
        base_prompt = """You are creating documentation for an additive manufacturing process based on provided inventory data.

**GROUND TRUTH**: The inventory data (materials, energy, products, waste, gas) must be accurately reflected with exact values.

**AUTHENTICITY**: Create documentation that reads like real-world documents in this domain, not artificial data showcases. Add contextual details appropriate to the document type.

**FORBIDDEN TERMINOLOGY**: Avoid using professional terms or concepts related to life cycle assessment. These terms would not appear in authentic operational/technical documents.

**COMPARATIVE DATA (Optional)**: For longer documents, you may include contextual comparisons (e.g., "Last year: ~X", "Industry benchmark: ~Y") to enhance realism. Clearly mark these as historical/reference data, distinct from the current reporting period data which must exactly match the JSON.

**COMPLETENESS**: If a data category is missing, either state it was not recorded or naturally omit it (as happens in real documents).

**OUTPUT FORMAT**: Output ONLY the document content in plain Markdown format. Do NOT wrap the output in markdown code blocks (```markdown). Start directly with the document title.

**TABLE FORMATTING**: When including tables, ALWAYS add a blank line before and after the table. This is required for proper PDF conversion.

"""
        
        # ============================================================
        # Difficulty Instructions: 数据呈现方式
        # ============================================================
        difficulty_instructions = {
            "simple": """
**DATA PRESENTATION**: Clear and consolidated
Make it easy for readers to extract complete LCI data quickly. Use summary tables as appropriate for this document type.
""",
            "medium": """
**DATA PRESENTATION**: Distributed narrative
Embed LCI data naturally throughout the document. Readers should need to read multiple sections to collect the complete picture. Small focused tables for single aspects are fine, but avoid large summary tables showing all LCI categories together.
""",
            "complex": """
**DATA PRESENTATION**: Parameter-based (for calculable items)
Present underlying parameters rather than final totals when marked [CALCULABLE]. Readers must calculate to derive LCI values.

**For long documents (>4000 words)**: While distributing parameters throughout the document, keep calculation-related parameters within the same logical section or chapter to maintain reasoning traceability.

For [DIRECT] items, show final values normally.
"""}
        
        # ============================================================
        # Document Type Instructions: 特征描述（v3.1）
        # ============================================================
        document_type_instructions = {
            # ========== Tier 1: 短文档 (1500-2500 words) ==========
            "batch_production_record": """
**DOCUMENT TYPE**: Batch Production Record (1500-2500 words)

**Typical for**: Factory production logging and traceability
**Audience**: Production supervisors, quality control, operations team
**Typical characteristics**:
- Operational and factual focus
- Chronological flow with timestamped entries
- Traceability elements (batch IDs, operator names, equipment IDs, lot numbers)
- Matter-of-fact tone, concise operational language
- Mix of log entries and brief procedural notes

**For Complex difficulty**: Present energy/resource data as raw measurements rather than calculated totals, requiring readers to perform the calculation.
""",
            
            "build_job_log": """
**DOCUMENT TYPE**: Build Job Log (1500-2200 words)

**Typical for**: Equipment operation logging for maintenance and process control
**Audience**: Machine operators, maintenance team, process engineers
**Typical characteristics**:
- Technical log format with timestamped events
- Equipment status and sensor readings
- Operational data and alarm records
- Can be telegraphic in style
- Focus on factual equipment performance data
""",
            
            "material_traceability": """
**DOCUMENT TYPE**: Material Traceability Report (1800-2500 words)

**Typical for**: Material flow tracking for quality assurance and compliance
**Audience**: Quality assurance, supply chain, regulatory compliance
**Typical characteristics**:
- Material flow tracking from receiving to disposition
- Emphasis on lot numbers, weighing records, chain of custody
- Mass balance and material accounting focus
- Professional QA documentation style
- Traceability through material transformations
""",
            
            "quality_inspection": """
**DOCUMENT TYPE**: Quality Inspection Report (1500-2500 words)

**Typical for**: Quality verification and compliance documentation
**Audience**: Quality control, customer audits, certification bodies
**Typical characteristics**:
- Inspection procedures and test results
- Pass/fail criteria and conformance statements
- Measurement data and dimensional verification
- Reference to quality standards and specifications
- Formal inspection documentation style
""",
            
            # ========== Tier 2: 中文档 (3000-4500 words) ==========
            "technical_process_report": """
**DOCUMENT TYPE**: Technical Process Report (3000-4500 words)

**Typical for**: Process engineering documentation and technical analysis
**Audience**: Process engineers, technical managers, R&D team
**Typical characteristics**:
- Technical and analytical focus
- Structured sections (Introduction, Process Description, Results, Analysis, Conclusions)
- Process parameter discussions and technical rationale
- Engineering terminology and technical depth
- Balance of narrative explanation and technical data
- Professional technical documentation style
""",
            
            "environmental_assessment": """
**DOCUMENT TYPE**: Environmental Assessment Summary (3500-4500 words)

**Typical for**: Environmental impact evaluation and sustainability reporting
**Audience**: Environmental managers, sustainability teams, regulatory bodies
**Typical characteristics**:
- Environmental performance focus
- Resource consumption and waste generation analysis
- Comparison to benchmarks or previous periods
- Interpretation of environmental significance
- Recommendations for improvement
- Professional environmental reporting style
""",
            
            "multi_build_analysis": """
**DOCUMENT TYPE**: Multi-Build Comparative Analysis (3500-4500 words)

**Typical for**: Process optimization and production performance analysis
**Audience**: Production management, process engineers, continuous improvement teams
**Typical characteristics**:
- Comparative analysis across multiple production runs
- Trend identification and variance analysis
- Performance metrics and efficiency discussions
- Root cause analysis of variations
- Data-driven insights and recommendations
- Analytical technical writing style
""",
            
            # ========== Tier 3: 长文档 (5000-7000 words) ==========
            "research_case_study": """
**DOCUMENT TYPE**: Research Case Study (5000-7000 words)

**Typical for**: Academic or industry research documentation
**Audience**: Researchers, academics, industry experts, technical professionals
**Typical characteristics**:
- Comprehensive scholarly structure (Abstract, Introduction/Background, Methodology, Results, Discussion, Conclusions)
- Context-setting with broader field perspective (general references to research areas, not specific citations)
- Detailed methodology description
- In-depth results presentation and interpretation
- Critical analysis and discussion of findings
- Implications and future work considerations
- Formal academic/technical writing tone
""",
            
            "sustainability_report": """
**DOCUMENT TYPE**: Annual Sustainability Report Chapter (5000-7000 words)

**Typical for**: Corporate sustainability and ESG reporting
**Audience**: Stakeholders, investors, sustainability analysts, general public
**Typical characteristics**:
- Comprehensive coverage of sustainability dimensions (environmental, economic, operational)
- Executive summary and key highlights
- Year-over-year comparisons and trend analysis
- Contextualization within organizational goals and industry standards
- Narrative storytelling combined with data presentation
- Forward-looking commitments and improvement plans
- Professional corporate reporting style with stakeholder focus
""",
            
            # ========== 新增文档类型（v5.0）：文本丰富，训练检索能力 ==========
            "process_development_report": """
**DOCUMENT TYPE**: Process Development Report (3500-5000 words)

**Typical for**: Process engineering and manufacturing development
**Audience**: Process engineers, R&D team, manufacturing managers, technical leadership
**Typical characteristics**:
- Narrative of process development journey from concept to production
- Description of parameter optimization and troubleshooting activities
- Evolution of process understanding over development cycles
- Technical rationale for design choices and parameter selection
- Discussion of challenges encountered and solutions implemented
- Lessons learned and best practices identified
- Balance of technical narrative and supporting data
- Professional engineering documentation style
- Focus on the "how" and "why" of process development
""",
            
            "manufacturing_feasibility_study": """
**DOCUMENT TYPE**: Manufacturing Feasibility Study (4000-5500 words)

**Typical for**: New process evaluation and technology adoption decisions
**Audience**: Management, engineering team, operations planning, strategic decision-makers
**Typical characteristics**:
- Comprehensive feasibility assessment from multiple perspectives
- Technical requirements and resource analysis
- Infrastructure and operational considerations
- Risk identification and mitigation strategies
- Practical implementation considerations
- Cost implications (without detailed financial analysis)
- Recommendations and decision support
- Professional consulting/advisory documentation style
- Balance of technical depth and business perspective
""",
            
            "process_characterization_study": """
**DOCUMENT TYPE**: Process Characterization Study (4000-6000 words)

**Typical for**: Process understanding and optimization research
**Audience**: Process engineers, researchers, technical specialists, R&D teams
**Typical characteristics**:
- Systematic investigation of process behavior and patterns
- Analysis of input-output relationships and dependencies
- Identification of key process variables and their effects
- Empirical observations and pattern recognition
- Technical insights and process understanding development
- Discussion of process sensitivities and control strategies
- Balance of analytical narrative and experimental observations
- Technical research documentation style
- Focus on building process knowledge and understanding
"""}
        
        
        # ============================================================
        # 组装最终Prompt
        # ============================================================
        final_prompt = base_prompt + \
                      difficulty_instructions.get(difficulty, difficulty_instructions["simple"]) + \
                      document_type_instructions.get(document_type, document_type_instructions["batch_production_record"])
        
        return final_prompt
    
    def _build_prompt(self, lci_data: Dict, difficulty: str, document_type: str) -> str:
        """构建用户prompt（v1.5: 支持relations）"""
        
        # 提取数据
        process_name = lci_data.get("process_name", "AM Process")
        inputs = lci_data.get("inputs", [])
        outputs = lci_data.get("outputs", [])
        parameters = lci_data.get("parameters", [])
        relations = lci_data.get("relations", [])
        
        # 构建清晰的数据列表
        data_items = []
        
        # 构建relations映射（flow名称 -> relation信息）
        relations_map = {}
        if relations:
            for rel in relations:
                flow_key = rel.get("flow", "")
                relations_map[flow_key] = rel
        
        for inp in inputs:
            flow_key = f"{inp['category']}: {inp['name']}"
            relation = relations_map.get(flow_key)
            
            if relation:
                # 有relation的flow，标注为CALCULABLE并包含计算说明
                calc_desc = relation.get("calculation", "")
                params_used = relation.get("parameters_used", [])
                data_items.append(f"[CALCULABLE] {inp['name']} ({inp['category']}): {inp['value']} {inp['unit']}")
                if difficulty == "complex":
                    data_items.append(f"  → Calculation: {calc_desc}")
                    data_items.append(f"  → Uses parameters: {', '.join(params_used)}")
            elif inp.get("child_nodes"):
                # 旧版child_nodes格式兼容
                child_str = ", ".join([f"{c['name']}: {c['value']} {c['unit']}" for c in inp['child_nodes']])
                data_items.append(f"[CALCULABLE] {inp['name']} ({inp['category']}): parameters are {child_str}, final value is {inp['value']} {inp['unit']}")
            else:
                # 标注为直接陈述的flow
                data_items.append(f"[DIRECT] {inp['name']} ({inp['category']}): {inp['value']} {inp['unit']}")
        
        for out in outputs:
            qty = f", {out['quantity']} units" if "quantity" in out else ""
            flow_key = f"{out['category']}: {out['name']}"
            relation = relations_map.get(flow_key)
            
            if relation:
                # 有relation的flow
                calc_desc = relation.get("calculation", "")
                params_used = relation.get("parameters_used", [])
                data_items.append(f"[CALCULABLE] {out['name']} ({out['category']}): {out['value']} {out['unit']}{qty}")
                if difficulty == "complex":
                    data_items.append(f"  → Calculation: {calc_desc}")
                    data_items.append(f"  → Uses parameters: {', '.join(params_used)}")
            elif out.get("child_nodes"):
                # 旧版child_nodes格式兼容
                child_str = ", ".join([f"{c['name']}: {c['value']} {c['unit']}" for c in out['child_nodes']])
                data_items.append(f"[CALCULABLE] {out['name']} ({out['category']}): parameters are {child_str}, final value is {out['value']} {out['unit']}{qty}")
            else:
                data_items.append(f"[DIRECT] {out['name']} ({out['category']}): {out['value']} {out['unit']}{qty}")
        
        if parameters:
            for param in parameters:
                data_items.append(f"[CONTEXT] {param['name']}: {param['value']} {param['unit']}")
        
        # 构建prompt说明
        notes = [
            "- [DIRECT] = state the final value directly",
            "- [CALCULABLE] = flow calculated from parameters",
            "- [CONTEXT] = additional process parameters for context"
        ]
        
        if difficulty == "complex" and relations:
            notes.append("\n**For Complex documents**: Present the underlying parameters for [CALCULABLE] flows rather than the final calculated value.")
        elif difficulty == "medium" and relations:
            notes.append("\n**Tip for Medium documents**:")
            notes.append("- You may mention how flows were calculated in narrative form")
            notes.append("- Example: 'Based on 2.23 MJ/kg consumption and 4.11 kg material, the process required 2.55 kWh...'")
        
        prompt = f"""Process: {process_name}

Data to document:
{chr(10).join('- ' + item for item in data_items)}

Note: 
{chr(10).join(notes)}

Write a formal {document_type.replace('_', ' ')} using tables and narrative paragraphs. Start with a clear document title using # heading. Use proper Markdown formatting (headings, bold text, tables, horizontal rules). Return only the Markdown document.
"""
        
        return prompt
    
    def batch_generate(
        self,
        lci_data_list: List[Dict],
        output_dir: str = "dataset/documents"
    ):
        """
        批量生成文档
        
        Args:
            lci_data_list: LCI数据列表
            output_dir: 输出目录
        """
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 难度和文档类型组合（v2.0: Tier 1文档类型）
        difficulty_levels = ["simple", "medium", "complex"]
        document_types = [
            "batch_production_record",
            "material_traceability",
            "build_job_log"
        ]
        
        generated_count = 0
        
        for i, lci_data in enumerate(lci_data_list):
            # 为每个LCI数据生成不同难度和类型的文档
            for difficulty in difficulty_levels:
                for doc_type in document_types:
                    try:
                        print(f"🔄 生成文档 {generated_count + 1}: {lci_data['process_name']} - {difficulty} - {doc_type}")
                        
                        document_text = self.generate_document(
                            lci_data=lci_data,
                            difficulty=difficulty,
                            document_type=doc_type
                        )
                        
                        # 保存文档
                        filename = f"doc_{i+1}_{difficulty}_{doc_type}.md"
                        filepath = os.path.join(output_dir, filename)
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(document_text)
                        
                        # 保存元数据
                        metadata = {
                            "source_lci": lci_data,
                            "difficulty": difficulty,
                            "document_type": doc_type,
                            "filename": filename
                        }
                        
                        metadata_file = filepath.replace('.md', '_metadata.json')
                        with open(metadata_file, 'w', encoding='utf-8') as f:
                            json.dump(metadata, f, indent=2, ensure_ascii=False)
                        
                        generated_count += 1
                        print(f"✅ 已保存: {filepath}")
                        
                    except Exception as e:
                        print(f"❌ 生成失败: {e}")
        
        print(f"\n🎉 批量生成完成！共生成 {generated_count} 个文档")


def load_lci_from_literature(literature_file: str) -> List[Dict]:
    """
    从文献中提取LCI数据
    
    Args:
        literature_file: 文献文件路径（JSON格式）
            格式示例：
            {
                "papers": [
                    {
                        "title": "...",
                        "lci_data": {
                            "process_name": "...",
                            "inputs": [...],
                            "outputs": [...],
                            "parameters": [...]
                        }
                    }
                ]
            }
    
    Returns:
        LCI数据列表
    """
    with open(literature_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    lci_list = []
    for paper in data.get("papers", []):
        lci_data = paper.get("lci_data")
        if lci_data:
            lci_list.append(lci_data)
    
    return lci_list


# ============================================================
# 示例使用
# ============================================================

if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='从LCI数据生成工艺文档')
    parser.add_argument('--input', type=str, required=True, help='输入的JSON文件路径')
    parser.add_argument('--difficulty', type=str, default='simple', choices=['simple', 'medium', 'complex'], help='难度级别')
    parser.add_argument('--document-type', type=str, default='batch_production_record', help='文档类型')
    args = parser.parse_args()
    
    # 检查API Key
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ 错误: 未设置 DEEPSEEK_API_KEY")
        print("   请运行: export DEEPSEEK_API_KEY='your_key'")
        sys.exit(1)
    
    # 从文件加载LCI数据
    print(f"📖 从文件加载LCI数据: {args.input}")
    lci_list = load_lci_from_literature(args.input)
    
    if len(lci_list) == 0:
        print("❌ 错误: 没有找到LCI数据")
        print(f"   请确保 {args.input} 文件存在且格式正确")
        sys.exit(1)
    
    print(f"✅ 找到 {len(lci_list)} 个LCI数据，使用第一个")
    lci_to_use = lci_list[0]
    
    # 初始化生成器
    engineer = DocumentReverseEngineer(api_key=api_key)
    
    # 生成单个文档示例
    print("🚀 生成示例文档...")
    doc = engineer.generate_document(
        lci_data=lci_to_use,
        difficulty=args.difficulty,
        document_type=args.document_type
    )
    
    # 保存到文件
    output_dir = "dataset/documents"
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, f"test_{args.difficulty}_{args.document_type}.md")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(doc)
    
    print("\n" + "="*60)
    print(f"✅ 文档已保存到: {output_file}")
    print("\n文档内容预览（前500字符）:")
    print(doc[:500] + "...")
    print(f"\n📊 文档总长度: {len(doc)} 字符")
    
    # 批量生成
    # engineer.batch_generate([example_lci])
