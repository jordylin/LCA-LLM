"""
LoRA 模型合并脚本
将 LoRA 适配器合并到基座模型，生成完整的模型文件

用法：
    python merge_lora.py

输出：
    合并后的模型保存到 models/Qwen3-8B-LCA-Merged/
"""

import os
import torch
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# 路径配置
BASE_MODEL_PATH = "/home/Research_work/24_yzlin/LCA-LLM/models/Qwen3-8B"
LORA_PATH = "/home/Research_work/24_yzlin/LCA-LLM/models/lca_lora"
OUTPUT_PATH = "/home/Research_work/24_yzlin/LCA-LLM/models/Qwen3-8B-LCA-Merged"


def main():
    print("=" * 60)
    print("LoRA 模型合并脚本")
    print("=" * 60)
    print()
    
    # 检查路径
    if not Path(BASE_MODEL_PATH).exists():
        print(f"❌ 基座模型不存在: {BASE_MODEL_PATH}")
        return
        
    if not Path(LORA_PATH).exists():
        print(f"❌ LoRA 适配器不存在: {LORA_PATH}")
        return
        
    print(f"📦 基座模型: {BASE_MODEL_PATH}")
    print(f"🔧 LoRA 适配器: {LORA_PATH}")
    print(f"📁 输出路径: {OUTPUT_PATH}")
    print()
    
    # 检查 GPU
    if torch.cuda.is_available():
        print(f"🖥️ GPU: {torch.cuda.get_device_name(0)}")
        print(f"   显存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    else:
        print("⚠️ 未检测到 GPU，将使用 CPU（可能较慢）")
    print()
    
    # 加载 tokenizer
    print("1️⃣ 加载 Tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        BASE_MODEL_PATH,
        trust_remote_code=True
    )
    print("   ✅ Tokenizer 加载完成")
    
    # 加载基座模型（使用 float16 以节省显存）
    print()
    print("2️⃣ 加载基座模型...")
    print("   这可能需要几分钟...")
    
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_PATH,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True
    )
    print("   ✅ 基座模型加载完成")
    
    # 加载 LoRA 适配器
    print()
    print("3️⃣ 加载 LoRA 适配器...")
    model = PeftModel.from_pretrained(model, LORA_PATH)
    print("   ✅ LoRA 适配器加载完成")
    
    # 合并模型
    print()
    print("4️⃣ 合并模型...")
    model = model.merge_and_unload()
    print("   ✅ 模型合并完成")
    
    # 保存合并后的模型
    print()
    print("5️⃣ 保存合并后的模型...")
    print(f"   保存到: {OUTPUT_PATH}")
    
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    
    model.save_pretrained(OUTPUT_PATH, safe_serialization=True)
    tokenizer.save_pretrained(OUTPUT_PATH)
    
    print("   ✅ 模型保存完成")
    
    # 验证
    print()
    print("6️⃣ 验证保存的文件...")
    saved_files = list(Path(OUTPUT_PATH).glob("*"))
    print(f"   保存了 {len(saved_files)} 个文件:")
    for f in saved_files[:10]:
        size = f.stat().st_size / 1024**2
        print(f"   - {f.name} ({size:.1f} MB)")
    if len(saved_files) > 10:
        print(f"   ... 还有 {len(saved_files) - 10} 个文件")
        
    print()
    print("=" * 60)
    print("✅ 合并完成！")
    print("=" * 60)
    print()
    print("下一步：")
    print(f"  1. 启动 vLLM: ./start_vllm.sh")
    print(f"  2. 启动后端: LLM_SERVICE=vllm ./restart_services.sh")


if __name__ == "__main__":
    main()
