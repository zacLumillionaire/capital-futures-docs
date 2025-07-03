"""
GIL錯誤檢測器 - 系統性檢查所有可能的GIL錯誤源頭
=================================================

這個工具會掃描整個代碼庫，找出所有可能導致GIL錯誤的代碼模式，
包括：
1. COM事件中的直接UI操作
2. 日誌處理器中的UI操作
3. 背景線程中的tkinter調用
4. 未保護的UI更新操作

使用方法：
python gil_error_detector.py

作者: GIL錯誤調試工具
日期: 2025-07-03
"""

import os
import re
import ast
import logging
from pathlib import Path
from typing import List, Dict, Tuple

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class GILErrorDetector:
    """GIL錯誤檢測器"""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.issues = []
        
        # 危險的UI操作模式
        self.dangerous_ui_patterns = [
            r'\.config\s*\(',
            r'\.configure\s*\(',
            r'\.insert\s*\(',
            r'\.delete\s*\(',
            r'\.pack\s*\(',
            r'\.grid\s*\(',
            r'\.place\s*\(',
            r'\.see\s*\(',
            r'\["text"\]\s*=',
            r'\.text\s*=',
            r'\.update\s*\(',
            r'\.update_idletasks\s*\(',
        ]
        
        # COM事件模式
        self.com_event_patterns = [
            r'def\s+On\w+\s*\(',
            r'def\s+OnNotify\w+\s*\(',
            r'def\s+OnAsync\w+\s*\(',
            r'def\s+OnConnection\s*\(',
            r'def\s+OnReply\w+\s*\(',
        ]
        
        # 日誌處理器模式
        self.log_handler_patterns = [
            r'class\s+\w*Handler\s*\(',
            r'def\s+emit\s*\(',
            r'logging\.Handler',
        ]
    
    def scan_all_files(self):
        """掃描所有Python文件"""
        logger.info("🔍 開始掃描所有Python文件...")
        
        python_files = list(self.root_path.rglob("*.py"))
        logger.info(f"📁 找到 {len(python_files)} 個Python文件")
        
        for file_path in python_files:
            try:
                self.scan_file(file_path)
            except Exception as e:
                logger.error(f"❌ 掃描文件失敗 {file_path}: {e}")
        
        self.generate_report()
    
    def scan_file(self, file_path: Path):
        """掃描單個文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # 檢查COM事件中的UI操作
            self.check_com_events_ui_operations(file_path, content, lines)
            
            # 檢查日誌處理器中的UI操作
            self.check_log_handlers_ui_operations(file_path, content, lines)
            
            # 檢查未保護的UI操作
            self.check_unprotected_ui_operations(file_path, content, lines)
            
            # 檢查特定的危險模式
            self.check_specific_dangerous_patterns(file_path, content, lines)
            
        except Exception as e:
            logger.error(f"❌ 讀取文件失敗 {file_path}: {e}")
    
    def check_com_events_ui_operations(self, file_path: Path, content: str, lines: List[str]):
        """檢查COM事件中的UI操作"""
        in_com_event = False
        com_event_start = 0
        
        for i, line in enumerate(lines):
            # 檢查是否進入COM事件函數
            for pattern in self.com_event_patterns:
                if re.search(pattern, line):
                    in_com_event = True
                    com_event_start = i
                    break
            
            # 檢查是否離開函數（簡單的縮進檢查）
            if in_com_event and line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                if i > com_event_start + 1:  # 不是函數定義行
                    in_com_event = False
            
            # 在COM事件中檢查UI操作
            if in_com_event:
                for ui_pattern in self.dangerous_ui_patterns:
                    if re.search(ui_pattern, line):
                        self.issues.append({
                            'type': 'COM_EVENT_UI_OPERATION',
                            'severity': 'CRITICAL',
                            'file': str(file_path),
                            'line': i + 1,
                            'content': line.strip(),
                            'description': f'COM事件中的危險UI操作: {ui_pattern}'
                        })
    
    def check_log_handlers_ui_operations(self, file_path: Path, content: str, lines: List[str]):
        """檢查日誌處理器中的UI操作"""
        in_handler_class = False
        in_emit_method = False
        
        for i, line in enumerate(lines):
            # 檢查是否在Handler類中
            if re.search(r'class\s+\w*Handler\s*\(', line):
                in_handler_class = True
            elif line.strip() and not line.startswith(' ') and not line.startswith('\t') and 'class' in line:
                in_handler_class = False
            
            # 檢查是否在emit方法中
            if in_handler_class and re.search(r'def\s+emit\s*\(', line):
                in_emit_method = True
            elif in_emit_method and line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                if 'def' in line:
                    in_emit_method = False
            
            # 在emit方法中檢查UI操作
            if in_emit_method:
                for ui_pattern in self.dangerous_ui_patterns:
                    if re.search(ui_pattern, line):
                        self.issues.append({
                            'type': 'LOG_HANDLER_UI_OPERATION',
                            'severity': 'CRITICAL',
                            'file': str(file_path),
                            'line': i + 1,
                            'content': line.strip(),
                            'description': f'日誌處理器emit方法中的危險UI操作: {ui_pattern}'
                        })
    
    def check_unprotected_ui_operations(self, file_path: Path, content: str, lines: List[str]):
        """檢查未保護的UI操作"""
        for i, line in enumerate(lines):
            # 跳過註釋行
            if line.strip().startswith('#'):
                continue
            
            # 檢查UI操作但沒有線程安全保護
            for ui_pattern in self.dangerous_ui_patterns:
                if re.search(ui_pattern, line):
                    # 檢查前後幾行是否有線程安全保護
                    context_start = max(0, i - 3)
                    context_end = min(len(lines), i + 4)
                    context = '\n'.join(lines[context_start:context_end])
                    
                    # 檢查是否有保護措施
                    has_protection = any([
                        'threading.current_thread' in context,
                        'main_thread' in context,
                        'after_idle' in context,
                        'put_.*_message' in context,
                        'Queue' in context,
                        'queue' in context,
                    ])
                    
                    if not has_protection:
                        self.issues.append({
                            'type': 'UNPROTECTED_UI_OPERATION',
                            'severity': 'HIGH',
                            'file': str(file_path),
                            'line': i + 1,
                            'content': line.strip(),
                            'description': f'可能未保護的UI操作: {ui_pattern}'
                        })
    
    def check_specific_dangerous_patterns(self, file_path: Path, content: str, lines: List[str]):
        """檢查特定的危險模式"""
        dangerous_patterns = [
            # TreeView操作
            (r'TreeView.*\.insert\s*\(', 'TreeView插入操作'),
            (r'TreeView.*\.delete\s*\(', 'TreeView刪除操作'),
            
            # Text控件操作
            (r'Text.*\.insert\s*\(', 'Text控件插入操作'),
            (r'text_.*\.insert\s*\(', 'Text控件插入操作'),
            
            # Label配置
            (r'Label.*\.config\s*\(', 'Label配置操作'),
            (r'label_.*\.config\s*\(', 'Label配置操作'),
            
            # Listbox操作
            (r'Listbox.*\.insert\s*\(', 'Listbox插入操作'),
            (r'listbox.*\.insert\s*\(', 'Listbox插入操作'),
            
            # 直接屬性設置
            (r'\w+\["text"\]\s*=', '直接設置text屬性'),
        ]
        
        for i, line in enumerate(lines):
            for pattern, description in dangerous_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    self.issues.append({
                        'type': 'SPECIFIC_DANGEROUS_PATTERN',
                        'severity': 'HIGH',
                        'file': str(file_path),
                        'line': i + 1,
                        'content': line.strip(),
                        'description': description
                    })
    
    def generate_report(self):
        """生成檢測報告"""
        logger.info("\n" + "="*80)
        logger.info("🔍 GIL錯誤檢測報告")
        logger.info("="*80)
        
        if not self.issues:
            logger.info("✅ 未發現潛在的GIL錯誤問題！")
            return
        
        # 按嚴重程度分組
        critical_issues = [issue for issue in self.issues if issue['severity'] == 'CRITICAL']
        high_issues = [issue for issue in self.issues if issue['severity'] == 'HIGH']
        
        logger.info(f"📊 總計發現 {len(self.issues)} 個潛在問題")
        logger.info(f"   🚨 嚴重問題: {len(critical_issues)}")
        logger.info(f"   ⚠️ 高風險問題: {len(high_issues)}")
        
        # 顯示嚴重問題
        if critical_issues:
            logger.info("\n🚨 嚴重問題 (可能直接導致GIL錯誤):")
            logger.info("-" * 60)
            for issue in critical_issues:
                logger.info(f"📁 文件: {issue['file']}")
                logger.info(f"📍 行號: {issue['line']}")
                logger.info(f"🔍 類型: {issue['type']}")
                logger.info(f"📝 描述: {issue['description']}")
                logger.info(f"💻 代碼: {issue['content']}")
                logger.info("-" * 60)
        
        # 顯示高風險問題
        if high_issues:
            logger.info("\n⚠️ 高風險問題 (需要檢查):")
            logger.info("-" * 60)
            for issue in high_issues[:10]:  # 只顯示前10個
                logger.info(f"📁 {issue['file']}:{issue['line']} - {issue['description']}")
                logger.info(f"💻 {issue['content']}")
                logger.info("-" * 30)
            
            if len(high_issues) > 10:
                logger.info(f"... 還有 {len(high_issues) - 10} 個高風險問題")
        
        # 生成修復建議
        self.generate_fix_suggestions()
    
    def generate_fix_suggestions(self):
        """生成修復建議"""
        logger.info("\n🔧 修復建議:")
        logger.info("-" * 40)
        
        critical_issues = [issue for issue in self.issues if issue['severity'] == 'CRITICAL']
        
        if critical_issues:
            logger.info("1. 立即修復所有嚴重問題:")
            for issue in critical_issues:
                logger.info(f"   📁 {issue['file']}:{issue['line']}")
                
                if 'COM_EVENT' in issue['type']:
                    logger.info("   🔧 建議: 將UI操作改為Queue模式或after_idle")
                elif 'LOG_HANDLER' in issue['type']:
                    logger.info("   🔧 建議: 在emit方法中避免直接UI操作")
        
        logger.info("\n2. 通用修復模式:")
        logger.info("   ✅ COM事件: 使用put_*_message()放入Queue")
        logger.info("   ✅ UI操作: 檢查threading.current_thread()")
        logger.info("   ✅ 日誌處理器: 避免在emit中操作UI")
        logger.info("   ✅ 背景線程: 使用root.after_idle()安排UI更新")

def main():
    """主函數"""
    detector = GILErrorDetector()
    detector.scan_all_files()

if __name__ == "__main__":
    main()
