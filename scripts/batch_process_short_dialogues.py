#!/usr/bin/env python3
"""
短对话数据集批量处理脚本

功能：
1. 批量处理短对话数据（search → record）
2. 执行流程：export → improve name/note → generate reasoning
3. 每个 session 一个文件
4. 清晰的文件命名（short_001, short_002, ...）
5. 保持 JSON 格式（不转 JSONL）

使用示例：
    # 处理所有 sessions
    python scripts/batch_process_short_dialogues.py \
      --output-dir dataset/short/doc1 \
      --api-key "sk-xxx"
    
    # 处理特定 sessions
    python scripts/batch_process_short_dialogues.py \
      --output-dir dataset/short/doc1 \
      --session-ids "session_001,session_002" \
      --api-key "sk-xxx"

作者：AI Assistant
日期：2025-11-23
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class ShortDialogueBatchProcessor:
    """短对话数据集批量处理器"""
    
    def __init__(self, output_dir: str = "dataset/short/doc1"):
        """
        初始化处理器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.output_dir / "batch_process.log"
        
        # Session ID 映射文件
        self.id_mapping_file = self.output_dir / "session_id_mapping.json"
        self.id_mapping = self._load_id_mapping()
    
    def _load_id_mapping(self) -> Dict[str, str]:
        """加载 session ID 映射"""
        if self.id_mapping_file.exists():
            with open(self.id_mapping_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_id_mapping(self):
        """保存 session ID 映射"""
        with open(self.id_mapping_file, 'w', encoding='utf-8') as f:
            json.dump(self.id_mapping, f, ensure_ascii=False, indent=2)
    
    def _get_short_name(self, session_id: str, index: int) -> str:
        """
        获取简短名称（支持增量命名，不会重复）
        
        Args:
            session_id: 完整的 session ID
            index: 当前循环的序号（仅用于参考）
            
        Returns:
            简短名称（如 'short_001'）
        """
        # 如果已经有映射，直接返回
        if session_id in self.id_mapping:
            return self.id_mapping[session_id]
        
        # 找到当前最大的序号
        existing_numbers = []
        for name in self.id_mapping.values():
            if name.startswith("short_"):
                try:
                    num = int(name.split("_")[1])
                    existing_numbers.append(num)
                except (ValueError, IndexError):
                    pass
        
        # 新序号 = 最大序号 + 1
        next_number = max(existing_numbers) + 1 if existing_numbers else 1
        short_name = f"short_{next_number:03d}"
        
        self.id_mapping[session_id] = short_name
        self._save_id_mapping()
        
        return short_name
    
    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] [{level}] {message}"
        print(log_msg)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_msg + "\n")
    
    def get_all_session_ids(self) -> List[str]:
        """获取所有 session IDs"""
        try:
            from pymongo import MongoClient
            
            client = MongoClient("mongodb://localhost:27017/")
            db = client["lci_database"]
            all_session_ids = db.lca_actions.distinct("session_id")
            client.close()
            
            return sorted(all_session_ids)
        
        except Exception as e:
            self.log(f"获取 session IDs 失败: {e}", "ERROR")
            return []
    
    def export_session(self, session_id: str, short_name: str) -> bool:
        """
        导出单个 session
        
        Args:
            session_id: 完整的 session ID
            short_name: 简短名称
            
        Returns:
            是否成功
        """
        output_file = self.output_dir / f"{short_name}_exported.json"
        
        cmd = [
            "python", "scripts/export_training_data.py",
            "--session-id", session_id,
            "--output", str(output_file),
            "--format", "json"
        ]
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                self.log(f"✅ 导出成功: {short_name}", "SUCCESS")
                return True
            else:
                self.log(f"❌ 导出失败: {short_name}\n{result.stderr}", "ERROR")
                return False
        
        except Exception as e:
            self.log(f"❌ 导出异常: {short_name}\n{e}", "ERROR")
            return False
    
    def improve_name_note(self, short_name: str, api_key: Optional[str] = None) -> bool:
        """
        改进 name 和 note
        
        Args:
            short_name: 简短名称
            api_key: DeepSeek API Key
            
        Returns:
            是否成功
        """
        input_file = self.output_dir / f"{short_name}_exported.json"
        
        if not input_file.exists():
            self.log(f"⚠️  输入文件不存在: {input_file}", "WARNING")
            return False
        
        output_file = self.output_dir / f"{short_name}_improved.json"
        
        cmd = [
            "python", "scripts/improve_name_note_with_camel.py",
            "--input", str(input_file),
            "--output", str(output_file)
        ]
        
        if api_key:
            cmd.extend(["--api-key", api_key])
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                self.log(f"✅ 改进成功: {short_name}", "SUCCESS")
                return True
            else:
                self.log(f"❌ 改进失败: {short_name}\n{result.stderr}", "ERROR")
                return False
        
        except Exception as e:
            self.log(f"❌ 改进异常: {short_name}\n{e}", "ERROR")
            return False
    
    def generate_reasoning(self, short_name: str, api_key: Optional[str] = None) -> bool:
        """
        生成 user content 和 reasoning
        
        Args:
            short_name: 简短名称
            api_key: DeepSeek API Key
            
        Returns:
            是否成功
        """
        # 优先使用 improved，如果不存在则使用 exported
        improved_file = self.output_dir / f"{short_name}_improved.json"
        exported_file = self.output_dir / f"{short_name}_exported.json"
        
        if improved_file.exists():
            input_file = improved_file
        elif exported_file.exists():
            input_file = exported_file
        else:
            self.log(f"⚠️  输入文件不存在: {short_name}", "WARNING")
            return False
        
        output_file = self.output_dir / f"{short_name}_complete.json"
        
        cmd = [
            "python", "scripts/generate_short_reasoning.py",
            "--input", str(input_file),
            "--output", str(output_file)
        ]
        
        if api_key:
            cmd.extend(["--api-key", api_key])
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                self.log(f"✅ 生成成功: {short_name}", "SUCCESS")
                return True
            else:
                self.log(f"❌ 生成失败: {short_name}\n{result.stderr}", "ERROR")
                return False
        
        except Exception as e:
            self.log(f"❌ 生成异常: {short_name}\n{e}", "ERROR")
            return False
    
    def process_session(self, session_id: str, index: int, api_key: Optional[str] = None) -> Dict[str, str]:
        """
        处理单个 session（完整流程）
        
        Args:
            session_id: 完整的 session ID
            index: 序号
            api_key: DeepSeek API Key
            
        Returns:
            处理结果 {"short_name": str, "status": str}
        """
        short_name = self._get_short_name(session_id, index)
        
        # Step 1: 导出
        if not self.export_session(session_id, short_name):
            return {"short_name": short_name, "status": "export_failed"}
        
        # Step 2: 改进 name/note
        if not self.improve_name_note(short_name, api_key):
            return {"short_name": short_name, "status": "improve_failed"}
        
        # Step 3: 生成 reasoning
        if not self.generate_reasoning(short_name, api_key):
            return {"short_name": short_name, "status": "generate_failed"}
        
        return {"short_name": short_name, "status": "success"}
    
    def batch_process(self, session_ids: Optional[List[str]] = None, api_key: Optional[str] = None):
        """
        批量处理所有 sessions
        
        Args:
            session_ids: session ID 列表，如果为 None 则处理所有
            api_key: DeepSeek API Key
        """
        if session_ids is None:
            session_ids = self.get_all_session_ids()
        
        self.log(f"开始批量处理 {len(session_ids)} 个 sessions", "INFO")
        
        results = []
        for i, session_id in enumerate(session_ids, 1):
            self.log(f"\n[{i}/{len(session_ids)}] 处理 session: {session_id[:30]}...", "INFO")
            result = self.process_session(session_id, i, api_key)
            results.append(result)
        
        # 统计结果
        success_count = sum(1 for r in results if r["status"] == "success")
        
        self.log(f"\n批量处理完成: {success_count}/{len(session_ids)} 成功", "INFO")
        
        return results
    
    def print_summary(self):
        """打印处理摘要"""
        print("\n" + "="*60)
        print("📊 短对话数据集处理摘要")
        print("="*60)
        
        exported_files = list(self.output_dir.glob("short_*_exported.json"))
        improved_files = list(self.output_dir.glob("short_*_improved.json"))
        complete_files = list(self.output_dir.glob("short_*_complete.json"))
        
        print(f"\n📁 输出目录: {self.output_dir}")
        print(f"  ✅ 已导出: {len(exported_files)} 个文件")
        print(f"  ✅ 已改进: {len(improved_files)} 个文件")
        print(f"  ✅ 已完成: {len(complete_files)} 个文件")
        
        print(f"\n🔗 Session ID 映射: {self.id_mapping_file}")
        print(f"  总计: {len(self.id_mapping)} 个映射")
        
        print(f"\n📝 日志文件: {self.log_file}")
        print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="批量处理短对话数据集",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 处理所有 sessions
  python scripts/batch_process_short_dialogues.py \\
    --output-dir dataset/short/doc1 \\
    --api-key "sk-xxx"
  
  # 处理特定 sessions
  python scripts/batch_process_short_dialogues.py \\
    --output-dir dataset/short/doc1 \\
    --session-ids "session_001,session_002" \\
    --api-key "sk-xxx"
        """
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="dataset/short/doc1",
        help="输出目录（默认: dataset/short/doc1）"
    )
    
    parser.add_argument(
        "--session-ids",
        type=str,
        help="指定 session IDs（逗号分隔），如果不指定则处理所有"
    )
    
    parser.add_argument(
        "--api-key",
        type=str,
        help="DeepSeek API Key"
    )
    
    args = parser.parse_args()
    
    processor = ShortDialogueBatchProcessor(output_dir=args.output_dir)
    
    session_ids = None
    if args.session_ids:
        session_ids = [s.strip() for s in args.session_ids.split(",")]
    
    processor.batch_process(session_ids, api_key=args.api_key)
    processor.print_summary()


if __name__ == "__main__":
    main()
