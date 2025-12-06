"""
批量生成文档 - 优化版本
每篇文献生成 10 个文档：6 Simple + 3 Medium + 1 Complex
"""
import os
import sys
import glob
import argparse
from reverse_engineer_documents import DocumentReverseEngineer, load_lci_from_literature

def batch_generate_optimized(
    input_dir: str = None,
    output_dir: str = None,
    specific_file: str = None
):
    """
    批量生成所有文献的文档（优化版本）
    
    每篇文献生成 10 个文档：
    - Simple: 4 个（40%）
    - Medium: 4 个（40%）
    - Complex: 2 个（20%）
    
    Args:
        input_dir: LCI数据目录（默认：dataset/lci_literature）
        output_dir: 输出目录（默认：dataset/generated_docs）
        specific_file: 指定特定的JSON文件（可选）
    """
    # 设置默认路径
    if input_dir is None:
        input_dir = "dataset/lci_literature"
    if output_dir is None:
        output_dir = "dataset/generated_docs"
    # 检查API Key
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ 错误: 未设置 DEEPSEEK_API_KEY")
        print("   请运行: export DEEPSEEK_API_KEY='your_key'")
        return
    
    # 初始化生成器
    engineer = DocumentReverseEngineer(api_key=api_key)
    
    # 查找JSON文件
    if specific_file:
        # 如果指定了特定文件
        if os.path.isabs(specific_file):
            json_files = [specific_file] if os.path.exists(specific_file) else []
        else:
            json_files = [os.path.join(input_dir, specific_file)] if os.path.exists(os.path.join(input_dir, specific_file)) else []
        
        if not json_files:
            print(f"❌ 错误: 找不到文件 {specific_file}")
            return
        print(f"📚 处理指定文件: {specific_file}")
    else:
        # 查找所有JSON文件
        json_files = glob.glob(os.path.join(input_dir, "paper_*.json"))
        
        if not json_files:
            print(f"❌ 错误: 在 {input_dir} 中没有找到 paper_*.json 文件")
            print(f"   请确保文件名格式为: paper_001.json, paper_002.json, ...")
            print(f"\n💡 提示: 使用 --file 参数指定特定文件")
            print(f"   例如: python batch_generate_optimized.py --file paper_002.json")
            return
        
        print(f"📚 找到 {len(json_files)} 个文献文件")
    print(f"\n📊 生成策略:")
    print(f"   - 每篇文献: 10 个文档")
    print(f"   - Simple: 4 个 (40%)")
    print(f"   - Medium: 4 个 (40%)")
    print(f"   - Complex: 2 个 (20%)")
    print(f"   - 预计总文档数: {len(json_files) * 10}")
    
    # 定义生成配置（v5.1: 工业真实性 + 文本丰富类型，训练检索能力；比例 4/4/2）
    # 格式: (difficulty, document_type)
    generation_config = [
        # Simple (4 个) - 工业操作/记录类文档
        ("simple", "batch_production_record"),      # 批次生产记录
        ("simple", "build_job_log"),                # 设备作业日志
        ("simple", "material_traceability"),        # 物料追溯
        ("simple", "quality_inspection"),           # 质量检验
        
        # Medium (4 个) - 工程分析与开发/可行性类文档
        ("medium", "technical_process_report"),         # 技术工艺报告
        ("medium", "process_development_report"),       # 工艺开发报告
        ("medium", "multi_build_analysis"),             # 多批次对比分析
        ("medium", "manufacturing_feasibility_study"),  # 制造可行性研究
        
        # Complex (2 个) - 研究/表征类长文档
        ("complex", "research_case_study"),             # 研究型案例分析
        ("complex", "process_characterization_study"),  # 工艺表征研究
    ]
    
    # 逐个处理
    total_docs = 0
    for json_file in sorted(json_files):
        print(f"\n{'='*70}")
        print(f"📖 处理: {os.path.basename(json_file)}")
        print(f"{'='*70}")
        
        # 提取文献ID（从 paper_XXX.json 中提取 XXX）
        import re
        match = re.search(r'paper_(\d+)', os.path.basename(json_file))
        paper_id = match.group(1) if match else "000"
        
        try:
            # 加载LCI数据
            lci_list = load_lci_from_literature(json_file)
            
            if not lci_list:
                print(f"⚠️  跳过: 没有找到LCI数据")
                continue
            
            print(f"✅ 找到 {len(lci_list)} 个LCI数据")
            
            generated_count = 0
            
            # 对每个LCI数据生成文档
            for i, lci_data in enumerate(lci_list):
                print(f"\n  📄 LCI数据 #{i+1}: {lci_data.get('process_name', 'Unknown')}")
                
                # 按照配置生成文档
                for difficulty, document_type in generation_config:
                    try:
                        # 生成文档
                        document_text = engineer.generate_document(
                            lci_data=lci_data,
                            difficulty=difficulty,
                            document_type=document_type
                        )
                        
                        # 难度代码映射
                        difficulty_code = {"simple": "S", "medium": "M", "complex": "C"}[difficulty]
                        
                        # 类型代码映射（取前3个字符的首字母）
                        type_words = document_type.split('_')
                        type_code = ''.join([w[0].upper() for w in type_words[:3]])
                        
                        # 新命名格式: paper_{文献ID}_{序号}_{难度代码}_{类型代码}.md
                        filename = f"paper_{paper_id}_{i+1:02d}_{difficulty_code}_{type_code}.md"
                        filepath = os.path.join(output_dir, filename)
                        
                        os.makedirs(output_dir, exist_ok=True)
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(document_text)
                        
                        generated_count += 1
                        print(f"    ✓ {difficulty.capitalize():8} | {document_type}")
                    except Exception as e:
                        print(f"    ✗ {difficulty.capitalize():8} | {document_type} - 失败: {e}")
            
            total_docs += generated_count
            
            print(f"\n  ✅ 本文件生成 {generated_count} 个文档")
            print(f"     - Simple: {sum(1 for d, _ in generation_config if d == 'simple')} 个")
            print(f"     - Medium: {sum(1 for d, _ in generation_config if d == 'medium')} 个")
            print(f"     - Complex: {sum(1 for d, _ in generation_config if d == 'complex')} 个")
            
        except Exception as e:
            print(f"❌ 处理失败: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\n{'='*70}")
    print(f"🎉 全部完成！")
    print(f"{'='*70}")
    print(f"📊 统计:")
    print(f"   - 处理文献数: {len(json_files)}")
    print(f"   - 总文档数: {total_docs}")
    print(f"   - 平均每篇: {total_docs / len(json_files):.1f} 个文档")
    print(f"\n📁 输出目录: {os.path.abspath(output_dir)}")
    print(f"{'='*70}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="批量生成文档 - 优化版本（每篇文献生成 10 个文档）"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default=None,
        help="LCI数据目录（默认：dataset/lci_literature）"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="输出目录（默认：dataset/generated_docs）"
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="指定特定的JSON文件（例如：paper_002.json）"
    )
    
    args = parser.parse_args()
    
    batch_generate_optimized(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        specific_file=args.file
    )
