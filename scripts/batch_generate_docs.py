#!/usr/bin/env python3
"""
批量生成文档
从LCI数据生成不同难度和类型的工艺文档
"""

import json
import os
import sys
from reverse_engineer_documents import DocumentReverseEngineer, load_lci_from_literature

def main():
    # 设置API key
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ 错误: 未设置 DEEPSEEK_API_KEY 环境变量")
        print("   请运行: export DEEPSEEK_API_KEY='your_key'")
        sys.exit(1)
    
    # 加载LCI数据
    lci_file = "dataset/lci_literature/paper_001.json"
    
    if not os.path.exists(lci_file):
        print(f"❌ 文件不存在: {lci_file}")
        print("\n请先创建LCI数据文件，参考格式：")
        print("""
{
  "papers": [
    {
      "title": "论文标题",
      "authors": "作者",
      "year": 2023,
      "lci_data": {
        "process_name": "工艺名称",
        "inputs": [...],
        "outputs": [...],
        "parameters": [...]
      }
    }
  ]
}
        """)
        sys.exit(1)
    
    print(f"📖 加载LCI数据: {lci_file}")
    lci_list = load_lci_from_literature(lci_file)
    print(f"✅ 找到 {len(lci_list)} 个LCI数据")
    
    if len(lci_list) == 0:
        print("❌ 没有找到LCI数据")
        sys.exit(1)
    
    # 初始化生成器
    engineer = DocumentReverseEngineer(api_key=api_key)
    
    # 批量生成
    output_dir = "dataset/documents"
    print(f"\n🚀 开始批量生成文档到: {output_dir}")
    print(f"   每个LCI数据将生成 12 个文档（3难度 × 4类型）")
    print(f"   预计生成 {len(lci_list) * 12} 个文档")
    print(f"   文档长度目标: 1500-2500词，更丰富的内容和多样性\n")
    
    engineer.batch_generate(lci_list, output_dir=output_dir)
    
    print("\n✅ 批量生成完成！")
    print(f"\n📁 生成的文档位于: {output_dir}")
    print(f"   - 每个文档都有对应的 _metadata.json 文件")
    print(f"   - 可以使用 ls -lh {output_dir} 查看")

if __name__ == "__main__":
    main()
