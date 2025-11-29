"""
批量生成所有文献的文档
"""
import os
import glob
from reverse_engineer_documents import DocumentReverseEngineer, load_lci_from_literature

def batch_generate_all_papers(
    input_dir: str = "../dataset/lci_literature",
    output_dir: str = "../dataset/generated_docs"
):
    """
    批量生成所有文献的文档
    
    Args:
        input_dir: LCI数据目录
        output_dir: 输出目录
    """
    # 检查API Key
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ 错误: 未设置 DEEPSEEK_API_KEY")
        print("   请运行: export DEEPSEEK_API_KEY='your_key'")
        return
    
    # 初始化生成器
    engineer = DocumentReverseEngineer(api_key=api_key)
    
    # 查找所有JSON文件
    json_files = glob.glob(os.path.join(input_dir, "paper_*.json"))
    
    if not json_files:
        print(f"❌ 错误: 在 {input_dir} 中没有找到 paper_*.json 文件")
        print(f"   请确保文件名格式为: paper_001.json, paper_002.json, ...")
        return
    
    print(f"📚 找到 {len(json_files)} 个文献文件")
    
    # 逐个处理
    total_docs = 0
    for json_file in sorted(json_files):
        print(f"\n{'='*60}")
        print(f"📖 处理: {os.path.basename(json_file)}")
        print(f"{'='*60}")
        
        try:
            # 加载LCI数据
            lci_list = load_lci_from_literature(json_file)
            
            if not lci_list:
                print(f"⚠️  跳过: 没有找到LCI数据")
                continue
            
            print(f"✅ 找到 {len(lci_list)} 个LCI数据")
            
            difficulty_levels = ["simple", "medium", "complex"]
            document_types = [
                # Tier 1: 短文档
                "batch_production_record",
                "build_job_log",
                "material_traceability",
                "quality_inspection",
                # Tier 2: 中文档
                "technical_process_report",
                "environmental_assessment",
                "multi_build_analysis",
                # Tier 3: 长文档
                "research_case_study",
                "sustainability_report"
            ]
            
            generated_count = 0
            
            for i, lci_data in enumerate(lci_list):
                for difficulty in difficulty_levels:
                    for document_type in document_types:
                        engineer.batch_generate(
                            lci_data_list=[lci_data],
                            output_dir=output_dir,
                            difficulty=difficulty,
                            document_type=document_type
                        )
                        generated_count += 1
            
            total_docs += generated_count
            
            print(f"✅ 本文件生成 {generated_count} 个文档")
            
        except Exception as e:
            print(f"❌ 处理失败: {e}")
            continue
    
    print(f"\n{'='*60}")
    print(f"🎉 全部完成！共生成 {total_docs} 个文档")
    print(f"📁 输出目录: {os.path.abspath(output_dir)}")
    print(f"{'='*60}")

if __name__ == "__main__":
    batch_generate_all_papers()
