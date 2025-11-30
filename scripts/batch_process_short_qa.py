#!/usr/bin/env python3
"""
短对话 QA 场景批量处理脚本

功能：
1. 批量导出 QA 场景的短对话数据
2. 使用 CAMEL AI 生成 user content 和 reasoning
3. 每个 session 一个文件
4. 清晰的文件命名（qa_001, qa_002, ...）

使用示例：
    # 处理所有 sessions
    python scripts/batch_process_short_qa.py \
      --output-dir dataset/short_qa/doc1 \
      --api-key "sk-xxx"
    
    # 处理特定 sessions
    python scripts/batch_process_short_qa.py \
      --output-dir dataset/short_qa/doc1 \
      --session-ids "session_001,session_002" \
      --api-key "sk-xxx"

作者：AI Assistant
版本：v1.0
日期：2025-11-29
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class ShortQABatchProcessor:
    """短对话 QA 场景批量处理器"""
    
    def __init__(self, output_dir: str = "dataset/short_qa/doc1"):
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
    
    def _get_qa_name(self, session_id: str, index: int) -> str:
        """
        获取 QA 简短名称
        
        Args:
            session_id: 完整的 session ID
            index: 当前循环的序号
            
        Returns:
            简短名称（如 'qa_001'）
        """
        # 如果已经有映射，直接返回
        if session_id in self.id_mapping:
            return self.id_mapping[session_id]
        
        # 找到下一个可用的编号
        existing_numbers = set()
        for mapped_name in self.id_mapping.values():
            if mapped_name.startswith("qa_"):
                try:
                    num = int(mapped_name.split("_")[1])
                    existing_numbers.add(num)
                except:
                    pass
        
        # 从 1 开始找第一个未使用的编号
        next_num = 1
        while next_num in existing_numbers:
            next_num += 1
        
        qa_name = f"qa_{next_num:03d}"
        self.id_mapping[session_id] = qa_name
        self._save_id_mapping()
        
        return qa_name
    
    def _log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"
        print(log_message)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + "\n")
    
    def export_session(self, session_id: str, qa_name: str) -> bool:
        """
        导出单个 session
        
        Args:
            session_id: Session ID
            qa_name: QA 简短名称
            
        Returns:
            是否成功
        """
        output_file = self.output_dir / f"{qa_name}_exported.json"
        
        cmd = [
            "python", "scripts/export_short_qa_data.py",
            "--session-ids", session_id,
            "--output", str(output_file)
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            self._log(f"✅ 导出成功: {qa_name}", "SUCCESS")
            return True
        except subprocess.CalledProcessError as e:
            self._log(f"❌ 导出失败: {qa_name}\n{e.stderr}", "ERROR")
            return False
    
    def generate_reasoning(self, qa_name: str, api_key: str) -> bool:
        """
        生成 reasoning 和 user content
        
        Args:
            qa_name: QA 简短名称
            api_key: DeepSeek API Key
            
        Returns:
            是否成功
        """
        input_file = self.output_dir / f"{qa_name}_exported.json"
        output_file = self.output_dir / f"{qa_name}_complete.json"
        
        cmd = [
            "python", "scripts/generate_short_reasoning.py",
            "--input", str(input_file),
            "--output", str(output_file),
            "--api-key", api_key
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            self._log(f"✅ 生成成功: {qa_name}", "SUCCESS")
            return True
        except subprocess.CalledProcessError as e:
            self._log(f"❌ 生成失败: {qa_name}\n{e.stderr}", "ERROR")
            return False
    
    def process_sessions(self, session_ids: List[str], api_key: str):
        """
        批量处理 sessions
        
        Args:
            session_ids: Session ID 列表
            api_key: DeepSeek API Key
        """
        self._log(f"开始批量处理 {len(session_ids)} 个 sessions")
        
        success_count = 0
        
        for i, session_id in enumerate(session_ids, 1):
            qa_name = self._get_qa_name(session_id, i)
            
            self._log(f"\n[{i}/{len(session_ids)}] 处理 session: {session_id[:16]}...")
            
            # 1. 导出
            if not self.export_session(session_id, qa_name):
                continue
            
            # 2. 生成 reasoning
            if not self.generate_reasoning(qa_name, api_key):
                continue
            
            success_count += 1
        
        # 打印摘要
        self._log(f"\n批量处理完成: {success_count}/{len(session_ids)} 成功")
        
        print("\n" + "=" * 60)
        print("📊 短对话 QA 数据集处理摘要")
        print("=" * 60)
        print(f"\n📁 输出目录: {self.output_dir}")
        print(f"  ✅ 已导出: {success_count} 个文件")
        print(f"  ✅ 已完成: {success_count} 个文件")
        print(f"\n🔗 Session ID 映射: {self.id_mapping_file}")
        print(f"  总计: {len(self.id_mapping)} 个映射")
        print(f"\n📝 日志文件: {self.log_file}")
        print("=" * 60)
    
    def get_all_sessions(self) -> List[str]:
        """
        从 MongoDB 获取所有 sessions
        
        Returns:
            Session ID 列表
        """
        # 添加项目根目录到路径
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from backend.services.mongodb_manager import mongodb_manager
        
        mongodb_manager.initialize()
        db = mongodb_manager.get_database()
        
        # 🔥 修复：从 lca_actions 集合获取所有不同的 session_id
        session_ids = db.lca_actions.distinct("session_id")
        return session_ids


def main():
    parser = argparse.ArgumentParser(description="短对话 QA 场景批量处理器")
    parser.add_argument("--output-dir", default="dataset/short_qa/doc1", help="输出目录")
    parser.add_argument("--session-ids", help="Session IDs（逗号分隔），留空则处理所有")
    parser.add_argument("--api-key", required=True, help="DeepSeek API Key")
    
    args = parser.parse_args()
    
    # 创建处理器
    processor = ShortQABatchProcessor(output_dir=args.output_dir)
    
    # 获取 session IDs
    if args.session_ids:
        session_ids = [s.strip() for s in args.session_ids.split(",")]
    else:
        session_ids = processor.get_all_sessions()
        print(f"📊 从 MongoDB 获取到 {len(session_ids)} 个 sessions")
    
    # 处理 sessions
    processor.process_sessions(session_ids, args.api_key)


if __name__ == "__main__":
    main()
