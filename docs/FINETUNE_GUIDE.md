# Qwen3-8B 微调指南（新手版）

## 概述

本指南帮助你使用 LoRA 方法微调 Qwen3-8B 模型，用于 LCI 数据提取任务。

### 你的数据

| 数据类型 | 数量 | 用途 |
|----------|------|------|
| Full | 53 | 完整对话，训练全流程 |
| Short Extract | 61 | 短对话，训练数据提取 |
| Short QA | 61 | 短对话，训练问答能力 |
| **总计** | **175** | 训练集 163 + 验证集 12 |

### 验证集分布（分层采样）
- Full: 3 样本
- Short: 9 样本（extract + qa）

---

## 第一步：环境准备

### 1.1 安装依赖

```bash
# 激活虚拟环境
source lcaLLM/bin/activate

# 安装微调所需的库
pip install transformers>=4.40.0
pip install peft>=0.10.0          # LoRA 支持
pip install trl>=0.8.0            # SFT Trainer
pip install datasets>=2.18.0
pip install accelerate>=0.28.0
pip install bitsandbytes>=0.43.0  # 量化支持（可选，节省显存）
pip install wandb                  # 训练监控（推荐）
```

### 1.2 检查 GPU

```bash
nvidia-smi
# 确保有足够显存（建议 24GB+，如 RTX 3090/4090 或 A100）
```

---

## 第二步：数据已准备好

数据文件已生成：
- `dataset/finetune_data.train.jsonl` - 训练集 (157 样本)
- `dataset/finetune_data.eval.jsonl` - 验证集 (18 样本)

### 数据格式

```json
{"messages": [
  {"role": "system", "content": "You are an expert LCA assistant..."},
  {"role": "user", "content": "I need help pulling the LCI data..."},
  {"role": "assistant", "reasoning_content": "I need to find...", "tool_calls": [...]},
  {"role": "tool", "content": "<tool_response>...</tool_response>"},
  {"role": "assistant", "reasoning_content": "Great, I found...", "content": "I have recorded..."}
]}
```

---

## 第三步：开始微调

### 3.1 创建微调脚本

```bash
# 创建微调脚本
cat > scripts/finetune_qwen3.py << 'EOF'
#!/usr/bin/env python3
"""
Qwen3-8B LoRA 微调脚本
"""

import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    BitsAndBytesConfig,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer, DataCollatorForCompletionOnlyLM
import json

# ==================== 配置 ====================
MODEL_PATH = "models/Qwen3-8B"  # 本地模型路径
TRAIN_FILE = "dataset/finetune_data.train.jsonl"
EVAL_FILE = "dataset/finetune_data.eval.jsonl"
OUTPUT_DIR = "outputs/qwen3-8b-lca-lora"

# LoRA 配置
LORA_R = 64           # LoRA 秩（越大越强，但越慢）
LORA_ALPHA = 128      # LoRA alpha
LORA_DROPOUT = 0.05

# 训练配置
EPOCHS = 3
BATCH_SIZE = 1        # 根据显存调整
GRADIENT_ACCUMULATION = 8  # 有效 batch size = 1 * 8 = 8
LEARNING_RATE = 2e-4
MAX_SEQ_LENGTH = 32768  # Qwen3-8B 支持 32K

# ==================== 加载数据 ====================
def load_jsonl(file_path):
    data = []
    with open(file_path, 'r') as f:
        for line in f:
            data.append(json.loads(line))
    return data

# ==================== 主函数 ====================
def main():
    print("=" * 60)
    print("Qwen3-8B LoRA 微调")
    print("=" * 60)
    
    # 1. 加载 tokenizer
    print("\n📦 加载 tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    
    # 2. 加载模型（4-bit 量化节省显存）
    print("\n📦 加载模型（4-bit 量化）...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
    )
    model = prepare_model_for_kbit_training(model)
    
    # 3. 配置 LoRA
    print("\n🔧 配置 LoRA...")
    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", 
                       "gate_proj", "up_proj", "down_proj"],
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    # 4. 加载数据集
    print("\n📂 加载数据集...")
    dataset = load_dataset('json', data_files={
        'train': TRAIN_FILE,
        'eval': EVAL_FILE
    })
    print(f"   训练集: {len(dataset['train'])} 样本")
    print(f"   验证集: {len(dataset['eval'])} 样本")
    
    # 5. 格式化函数
    def format_messages(example):
        """将 messages 转换为模型输入格式"""
        messages = example['messages']
        
        # 使用 Qwen 的 chat template
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False
        )
        return {"text": text}
    
    dataset = dataset.map(format_messages, remove_columns=['messages'])
    
    # 6. 训练参数
    print("\n⚙️  配置训练参数...")
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION,
        learning_rate=LEARNING_RATE,
        weight_decay=0.01,
        warmup_ratio=0.1,
        lr_scheduler_type="cosine",
        logging_steps=10,
        eval_strategy="steps",
        eval_steps=50,
        save_strategy="steps",
        save_steps=100,
        save_total_limit=3,
        bf16=True,
        gradient_checkpointing=True,
        report_to="wandb",  # 或 "none" 如果不用 wandb
        run_name="qwen3-8b-lca-lora",
    )
    
    # 7. 创建 Trainer
    print("\n🚀 开始训练...")
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset['train'],
        eval_dataset=dataset['eval'],
        tokenizer=tokenizer,
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LENGTH,
        packing=False,
    )
    
    # 8. 训练
    trainer.train()
    
    # 9. 保存
    print("\n💾 保存模型...")
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    
    print("\n✅ 训练完成！")
    print(f"   模型保存在: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
EOF
```

### 3.2 运行微调

```bash
# 激活环境
source lcaLLM/bin/activate

# 登录 wandb（可选，用于监控训练）
wandb login

# 开始微调
python scripts/finetune_qwen3.py
```

---

## 第四步：监控训练

### 4.1 关键指标

| 指标 | 含义 | 期望趋势 |
|------|------|----------|
| `train_loss` | 训练损失 | 持续下降 |
| `eval_loss` | 验证损失 | 下降后趋于稳定 |
| `learning_rate` | 学习率 | 先升后降（warmup + cosine） |

### 4.2 正常训练曲线

```
Epoch 1: train_loss 2.5 → 1.8, eval_loss 2.3 → 1.9
Epoch 2: train_loss 1.8 → 1.2, eval_loss 1.9 → 1.5
Epoch 3: train_loss 1.2 → 0.8, eval_loss 1.5 → 1.4
```

### 4.3 异常情况

| 现象 | 可能原因 | 解决方案 |
|------|----------|----------|
| loss 不下降 | 学习率太小 | 增大 `LEARNING_RATE` |
| loss 震荡剧烈 | 学习率太大 | 减小 `LEARNING_RATE` |
| eval_loss 上升 | 过拟合 | 减少 epochs 或增大 dropout |
| OOM 错误 | 显存不足 | 减小 `BATCH_SIZE` 或 `MAX_SEQ_LENGTH` |

---

## 第五步：测试微调模型

### 5.1 加载微调后的模型

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# 加载基础模型
base_model = AutoModelForCausalLM.from_pretrained(
    "models/Qwen3-8B",
    device_map="auto",
    torch_dtype=torch.bfloat16,
)

# 加载 LoRA 权重
model = PeftModel.from_pretrained(base_model, "outputs/qwen3-8b-lca-lora")
tokenizer = AutoTokenizer.from_pretrained("outputs/qwen3-8b-lca-lora")

# 测试
messages = [
    {"role": "system", "content": "You are an expert LCA assistant..."},
    {"role": "user", "content": "Extract the material inputs from this document."}
]
inputs = tokenizer.apply_chat_template(messages, return_tensors="pt")
outputs = model.generate(inputs, max_new_tokens=512)
print(tokenizer.decode(outputs[0]))
```

### 5.2 合并权重（可选）

如果想把 LoRA 权重合并到基础模型：

```python
merged_model = model.merge_and_unload()
merged_model.save_pretrained("outputs/qwen3-8b-lca-merged")
```

---

## 常见问题

### Q1: 训练需要多长时间？

- **175 样本 + 3 epochs**：约 1-2 小时（RTX 3090）
- 主要取决于 `MAX_SEQ_LENGTH` 和 GPU 性能

### Q2: 显存不够怎么办？

1. 减小 `BATCH_SIZE` 到 1
2. 减小 `MAX_SEQ_LENGTH` 到 16384
3. 使用 `gradient_checkpointing=True`（已启用）
4. 使用 4-bit 量化（已启用）

### Q3: 效果不好怎么办？

1. **检查数据质量**：确保 reasoning 和 tool_calls 正确
2. **增加数据量**：更多样本通常效果更好
3. **调整超参数**：尝试不同的 `LORA_R`、`LEARNING_RATE`
4. **增加 epochs**：但注意过拟合

### Q4: 如何评估效果？

1. **定性评估**：手动测试几个样本，看输出是否合理
2. **定量评估**：计算 tool_calls 的准确率、数值提取的准确率

---

## 方案二：使用 LLaMA Factory（推荐新手）⭐

LLaMA Factory 提供可视化界面，更适合新手。

### 1. 安装 LLaMA Factory

```bash
# 克隆仓库
git clone --depth 1 https://github.com/hiyouga/LLaMA-Factory.git
cd LLaMA-Factory

# 创建虚拟环境
conda create -n llama_factory python=3.10 -y
conda activate llama_factory

# 安装依赖
pip install -e ".[torch,metrics]"
```

### 2. 准备数据集配置

在 `LLaMA-Factory/data/` 目录下创建数据集描述文件：

```bash
# 复制数据文件到 LLaMA-Factory
cp /home/Research_work/24_yzlin/LCA-LLM/dataset/finetune_data.train.jsonl LLaMA-Factory/data/lca_train.json
cp /home/Research_work/24_yzlin/LCA-LLM/dataset/finetune_data.eval.jsonl LLaMA-Factory/data/lca_eval.json
```

编辑 `LLaMA-Factory/data/dataset_info.json`，添加：

```json
{
  "lca_train": {
    "file_name": "lca_train.json",
    "formatting": "sharegpt",
    "columns": {
      "messages": "messages"
    },
    "tags": {
      "role_tag": "role",
      "content_tag": "content",
      "user_tag": "user",
      "assistant_tag": "assistant",
      "system_tag": "system"
    }
  },
  "lca_eval": {
    "file_name": "lca_eval.json",
    "formatting": "sharegpt",
    "columns": {
      "messages": "messages"
    },
    "tags": {
      "role_tag": "role",
      "content_tag": "content",
      "user_tag": "user",
      "assistant_tag": "assistant",
      "system_tag": "system"
    }
  }
}
```

### 3. 启动 Web UI

```bash
cd LLaMA-Factory
llamafactory-cli webui
```

浏览器打开 `http://localhost:7860`

### 4. Web UI 配置

在界面中设置：

| 配置项 | 推荐值 |
|--------|--------|
| **Model** | |
| Model name | `/home/Research_work/24_yzlin/LCA-LLM/models/Qwen3-8B` |
| Finetuning method | `lora` |
| Quantization bit | `4` (节省显存) |
| **Data** | |
| Dataset | `lca_train` |
| **Train** | |
| Learning rate | `2e-4` |
| Epochs | `3.0` |
| Max length | `32768` |
| Batch size | `1` |
| Gradient accumulation | `8` |
| LoRA rank | `64` |
| LoRA alpha | `128` |

### 5. 开始训练

点击 **Start** 按钮开始训练。

训练过程中可以在界面上实时查看：
- Loss 曲线
- 学习率变化
- 训练进度

### 6. 导出模型

训练完成后，在 **Export** 标签页导出模型：
- 选择输出目录
- 点击 **Export** 导出 LoRA 权重

---

## 下一步

1. ✅ 运行微调脚本
2. ✅ 监控 wandb 上的训练曲线
3. ✅ 测试微调后的模型
4. 🔄 根据效果调整数据或超参数
