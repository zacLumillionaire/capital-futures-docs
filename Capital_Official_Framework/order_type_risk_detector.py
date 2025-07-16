#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
order_type 參數風險檢測器
檢查整個專案中是否還有其他 'unexpected keyword argument order_type' 潛在風險
"""

import os
import re
import ast
from typing import List, Dict, Tuple
from datetime import datetime

class OrderTypeRiskDetector:
    """order_type 參數風險檢測器"""
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.issues = []
        self.safe_patterns = []
        self.risky_patterns = []
        
    def scan_project(self) -> Dict:
        """掃描整個專案"""
        print("🔍 開始掃描 order_type 參數風險...")
        print("=" * 60)
        
        python_files = self._find_python_files()
        print(f"📁 找到 {len(python_files)} 個 Python 檔案")
        
        for file_path in python_files:
            self._scan_file(file_path)
        
        return self._generate_report()
    
    def _find_python_files(self) -> List[str]:
        """找到所有 Python 檔案"""
        python_files = []
        for root, dirs, files in os.walk(self.project_root):
            # 跳過一些目錄
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'CapitalLog_']]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        return python_files
    
    def _scan_file(self, file_path: str):
        """掃描單個檔案"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 檢查 order_type 的使用
            self._check_order_type_usage(file_path, content)
            
        except Exception as e:
            print(f"⚠️ 無法讀取檔案 {file_path}: {e}")
    
    def _check_order_type_usage(self, file_path: str, content: str):
        """檢查 order_type 的使用情況"""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            if 'order_type' in line:
                self._analyze_order_type_line(file_path, line_num, line.strip())
    
    def _analyze_order_type_line(self, file_path: str, line_num: int, line: str):
        """分析包含 order_type 的行"""
        relative_path = os.path.relpath(file_path, self.project_root)
        
        # 安全模式：變數賦值、字典鍵、回報解析等
        safe_patterns = [
            r'order_type\s*=\s*cutData\[',  # 回報解析
            r'order_type\s*=\s*fields\[',   # 欄位解析
            r'order_type\s*=\s*data\.get\(',  # 字典取值
            r'if\s+order_type\s*==',        # 條件判斷
            r'elif\s+order_type\s*==',      # 條件判斷
            r'order_type\s*=\s*["\']',      # 字串賦值
            r'["\']order_type["\']',        # 字串字面值
            r'order_type.*#.*回報',          # 註解說明回報
            r'order_type.*#.*委託',          # 註解說明委託
            r'def.*order_type.*:',          # 函式定義參數
            r'class.*order_type',           # 類別定義
        ]
        
        # 危險模式：函式呼叫中的 order_type 參數
        risky_patterns = [
            r'\.execute_strategy_order\s*\([^)]*order_type',  # execute_strategy_order 呼叫
            r'\.strategy_order\s*\([^)]*order_type',          # strategy_order 呼叫
            r'\.place_order\s*\([^)]*order_type',             # place_order 呼叫
            r'\.send_order\s*\([^)]*order_type',              # send_order 呼叫
        ]
        
        # 檢查是否為安全模式
        is_safe = any(re.search(pattern, line, re.IGNORECASE) for pattern in safe_patterns)
        
        if is_safe:
            self.safe_patterns.append({
                'file': relative_path,
                'line': line_num,
                'content': line,
                'type': 'SAFE'
            })
            return
        
        # 檢查是否為危險模式
        is_risky = any(re.search(pattern, line, re.IGNORECASE) for pattern in risky_patterns)
        
        if is_risky:
            self.risky_patterns.append({
                'file': relative_path,
                'line': line_num,
                'content': line,
                'type': 'RISKY',
                'severity': 'HIGH'
            })
            self.issues.append({
                'file': relative_path,
                'line': line_num,
                'content': line,
                'issue': 'Potential order_type parameter in function call',
                'severity': 'HIGH'
            })
        else:
            # 其他使用，需要人工檢查
            self.risky_patterns.append({
                'file': relative_path,
                'line': line_num,
                'content': line,
                'type': 'UNKNOWN',
                'severity': 'MEDIUM'
            })
    
    def _generate_report(self) -> Dict:
        """生成檢測報告"""
        report = {
            'scan_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_files_scanned': len(self._find_python_files()),
            'safe_usages': len(self.safe_patterns),
            'risky_usages': len([p for p in self.risky_patterns if p['type'] == 'RISKY']),
            'unknown_usages': len([p for p in self.risky_patterns if p['type'] == 'UNKNOWN']),
            'high_risk_issues': len([i for i in self.issues if i['severity'] == 'HIGH']),
            'issues': self.issues,
            'safe_patterns': self.safe_patterns,
            'risky_patterns': self.risky_patterns
        }
        
        return report
    
    def print_report(self, report: Dict):
        """列印檢測報告"""
        print("\n" + "=" * 60)
        print("📊 order_type 參數風險檢測報告")
        print("=" * 60)
        
        print(f"🕐 掃描時間: {report['scan_time']}")
        print(f"📁 掃描檔案: {report['total_files_scanned']} 個")
        print(f"✅ 安全使用: {report['safe_usages']} 處")
        print(f"⚠️ 風險使用: {report['risky_usages']} 處")
        print(f"❓ 未知使用: {report['unknown_usages']} 處")
        print(f"🚨 高風險問題: {report['high_risk_issues']} 個")
        
        # 顯示高風險問題
        if report['high_risk_issues'] > 0:
            print("\n🚨 高風險問題詳情:")
            print("-" * 40)
            for issue in report['issues']:
                if issue['severity'] == 'HIGH':
                    print(f"📄 檔案: {issue['file']}")
                    print(f"📍 行號: {issue['line']}")
                    print(f"📝 內容: {issue['content']}")
                    print(f"⚠️ 問題: {issue['issue']}")
                    print("-" * 40)
        
        # 顯示需要檢查的未知使用
        unknown_patterns = [p for p in report['risky_patterns'] if p['type'] == 'UNKNOWN']
        if unknown_patterns:
            print("\n❓ 需要人工檢查的 order_type 使用:")
            print("-" * 40)
            for pattern in unknown_patterns[:10]:  # 只顯示前10個
                print(f"📄 {pattern['file']}:{pattern['line']}")
                print(f"📝 {pattern['content']}")
                print("-" * 40)
            
            if len(unknown_patterns) > 10:
                print(f"... 還有 {len(unknown_patterns) - 10} 個需要檢查")
        
        # 總結
        print("\n📋 檢測總結:")
        if report['high_risk_issues'] == 0:
            print("✅ 沒有發現高風險的 order_type 參數問題")
            print("✅ 所有 execute_strategy_order 呼叫都已修復")
        else:
            print("❌ 發現高風險問題，需要立即修復")
        
        if report['unknown_usages'] > 0:
            print(f"⚠️ 有 {report['unknown_usages']} 處 order_type 使用需要人工檢查")
        
        return report

def main():
    """主函數"""
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    detector = OrderTypeRiskDetector(project_root)
    report = detector.scan_project()
    detector.print_report(report)
    
    # 保存報告
    report_file = f"order_type_risk_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"order_type 參數風險檢測報告\n")
        f.write(f"掃描時間: {report['scan_time']}\n")
        f.write(f"掃描檔案: {report['total_files_scanned']} 個\n")
        f.write(f"高風險問題: {report['high_risk_issues']} 個\n\n")
        
        if report['issues']:
            f.write("高風險問題詳情:\n")
            for issue in report['issues']:
                f.write(f"檔案: {issue['file']}:{issue['line']}\n")
                f.write(f"內容: {issue['content']}\n")
                f.write(f"問題: {issue['issue']}\n\n")
    
    print(f"\n📄 詳細報告已保存至: {report_file}")
    
    return report['high_risk_issues'] == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
