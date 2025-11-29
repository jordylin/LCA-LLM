"""
阶段1批量生成脚本 - 快速验证（MVP）

目标: 生成200个全流程文档
配比:
- Simple: 100样本 (50%)
- Medium: 60样本 (30%)
- Complex: 40样本 (20%)

文档类型分布:
- Tier 1（短文档）: 40%
- Tier 2（中文档）: 35%
- Tier 3（长文档）: 25%
"""
import os
import glob
import random
from reverse_engineer_documents import DocumentReverseEngineer, load_lci_from_literature

# 阶段1配置
PHASE1_CONFIG = {
    "samples_per_paper": 27,  # 每篇文献生成27个样本（3难度 × 9类型）
    "difficulty_distribution": {
        "simple": 0.50,   # 50%
        "medium": 0.30,   # 30%
        "complex": 0.20   # 20%
    },
    "tier_distribution": {
        "tier1": 0.40,   # 40% 短文档
        "tier2": 0.35,   # 35% 中文档
        "tier3": 0.25    # 25% 长文档
    },
    "document_types": {
        "tier1": [
            "batch_production_record",
            "build_job_log",
            "material_traceability",
            "quality_inspection"
        ],
        "tier2": [
            "technical_process_report",
            "environmental_assessment",
            "multi_build_analysis"
        ],
        "tier3": [
            "research_case_study",
            "sustainability_report"
        ]
    }
}

def generate_sampling_plan_per_paper(total_samples: int = 27) -> list:
    """
    为单篇文献生成采样计划（按难度比例）
    
    Args:
        total_samples: 总样本数（默认27）
    
    Returns:
        采样计划列表，每项包含 (difficulty, document_type)
    """
    plan = []
    
    # 收集所有文档类型
    all_doc_types = []
    for tier_types in PHASE1_CONFIG["document_types"].values():
        all_doc_types.extend(tier_types)
    
    # 按比例计算每个难度的数量
    simple_count = int(total_samples * PHASE1_CONFIG["difficulty_distribution"]["simple"])
    medium_count = int(total_samples * PHASE1_CONFIG["difficulty_distribution"]["medium"])
    complex_count = total_samples - simple_count - medium_count  # 确保总数正确
    
    print(f"\n📊 每篇文献生成 {total_samples} 个样本:")
    print(f"  Simple: {simple_count} 个 ({simple_count/total_samples*100:.0f}%)")
    print(f"  Medium: {medium_count} 个 ({medium_count/total_samples*100:.0f}%)")
    print(f"  Complex: {complex_count} 个 ({complex_count/total_samples*100:.0f}%)")
    
    # 为每个难度随机选择文档类型
    for difficulty, count in [("simple", simple_count), ("medium", medium_count), ("complex", complex_count)]:
        for _ in range(count):
            # 随机选择文档类型
            doc_type = random.choice(all_doc_types)
            plan.append({
                "difficulty": difficulty,
                "document_type": doc_type
            })
    
    # 打乱顺序
    random.shuffle(plan)
    
    return plan

def batch_generate_phase1(
    input_dir: str = "dataset/lci_literature",
    output_dir: str = "dataset/documents/phase1"
):
    """
    阶段1批量生成
    
    Args:
        input_dir: LCI数据目录
        output_dir: 输出目录
    """
    print("="*60)
    print("🚀 阶段1批量生成 - 快速验证（MVP）")
    print("="*60)
    
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
        return
    
    print(f"\n📚 找到 {len(json_files)} 个文献文件")
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成采样计划（每篇文献27个样本）
    plan = generate_sampling_plan_per_paper()
    
    # 逐个处理文献
    total_generated = 0
    
    for paper_idx, json_file in enumerate(sorted(json_files), 1):
        print(f"\n{'='*60}")
        print(f"📖 [{paper_idx}/{len(json_files)}] 处理: {os.path.basename(json_file)}")
        print(f"{'='*60}")
        
        # 加载LCI数据
        lci_list = load_lci_from_literature(json_file)
        
        if not lci_list:
            print(f"⚠️  跳过: 没有找到LCI数据")
            continue
        
        print(f"✅ 找到 {len(lci_list)} 个LCI数据，使用第一个")
        lci_data = lci_list[0]
        
        # 为该文献生成27个文档
        paper_name = os.path.splitext(os.path.basename(json_file))[0]
        generated_count = 0
        
        for i, item in enumerate(plan, 1):
            difficulty = item["difficulty"]
            document_type = item["document_type"]
            
            print(f"  [{i}/{len(plan)}] 生成: {difficulty} - {document_type}", end="")
            
            try:
                # 生成文档
                content = engineer.generate_document(
                    lci_data=lci_data,
                    difficulty=difficulty,
                    document_type=document_type
                )
                
                # 保存文档
                output_file = os.path.join(
                    output_dir,
                    f"{paper_name}_{i:02d}_{difficulty}_{document_type}.md"
                )
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                generated_count += 1
                print(" ✅")
                
            except Exception as e:
                print(f" ❌ 失败: {e}")
                continue
        
        total_generated += generated_count
        print(f"\n✅ 本文献生成 {generated_count}/{len(plan)} 个文档")
    
    # 统计
    print(f"\n{'='*60}")
    print(f"🎉 批量生成完成！")
    print(f"{'='*60}")
    print(f"✅ 总共生成: {total_generated} 个文档")
    print(f"📁 输出目录: {os.path.abspath(output_dir)}")
    print(f"📊 平均每篇文献: {total_generated/len(json_files):.0f} 个文档")
    
    print(f"\n💡 下一步:")
    print(f"  1. 检查生成的文档质量")
    print(f"  2. 如果质量OK，继续处理更多文献")
    print(f"  3. 运行 export_qa_training_data.py 生成QA数据")
    print(f"  4. 运行 export_training_data.py 导出训练样本")
    print(f"{'='*60}")

if __name__ == "__main__":
    batch_generate_phase1()
