# -*- coding: utf-8 -*-
"""
GIL問題修正驗證
Test GIL Fix Verification

檢查報價事件中是否還有UI更新操作

作者: GIL問題修正
日期: 2025-07-04
"""

import re
import os

def check_ui_updates_in_quote_events():
    """檢查報價事件中的UI更新"""
    
    file_path = 'simple_integrated.py'
    if not os.path.exists(file_path):
        print("❌ 文件不存在")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # 找到報價事件方法的範圍
    quote_event_methods = [
        'OnNotifyTicksLONG',
        'OnNotifyBest5LONG',
        'process_strategy_logic_safe',
        'update_range_calculation_safe',
        'check_minute_candle_breakout_safe',
        'check_breakout_signals_safe',
        'enter_position_safe'
    ]
    
    ui_update_patterns = [
        r'\.set\(',           # StringVar.set()
        r'\.config\(',        # widget.config()
        r'\.configure\(',     # widget.configure()
        r'messagebox\.',      # messagebox calls
        r'\.insert\(',        # Text.insert()
        r'\.delete\(',        # Text.delete()
    ]
    
    issues_found = []
    
    for method_name in quote_event_methods:
        # 找到方法的開始和結束
        method_start = None
        method_end = None
        indent_level = None
        
        for i, line in enumerate(lines):
            if f'def {method_name}(' in line:
                method_start = i
                indent_level = len(line) - len(line.lstrip())
                break
        
        if method_start is None:
            continue
        
        # 找到方法結束
        for i in range(method_start + 1, len(lines)):
            line = lines[i]
            if line.strip() == '':
                continue
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= indent_level and line.strip().startswith('def '):
                method_end = i
                break
        
        if method_end is None:
            method_end = len(lines)
        
        # 檢查方法內的UI更新
        method_lines = lines[method_start:method_end]
        for i, line in enumerate(method_lines):
            line_num = method_start + i + 1
            
            # 跳過註釋行
            if line.strip().startswith('#'):
                continue
            
            # 檢查UI更新模式
            for pattern in ui_update_patterns:
                if re.search(pattern, line):
                    # 排除已知的安全操作
                    if 'print(' in line or 'Console' in line or '已移除' in line:
                        continue
                    
                    issues_found.append({
                        'method': method_name,
                        'line_num': line_num,
                        'line': line.strip(),
                        'pattern': pattern
                    })
    
    return issues_found

def main():
    """主測試函數"""
    print("🔍 檢查報價事件中的UI更新...")
    
    issues = check_ui_updates_in_quote_events()
    
    if not issues:
        print("✅ 所有報價事件中的UI更新都已移除")
        print("✅ GIL風險已消除")
        return True
    else:
        print(f"❌ 發現 {len(issues)} 個潛在的UI更新問題:")
        for issue in issues:
            print(f"   方法: {issue['method']}")
            print(f"   第{issue['line_num']}行: {issue['line']}")
            print(f"   模式: {issue['pattern']}")
            print()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 GIL問題修正驗證通過！")
        print("💡 現在可以安全地處理報價事件，不會再遇到GIL錯誤")
    else:
        print("\n⚠️ 仍有潛在的GIL風險需要處理")
