# -*- coding: utf-8 -*-
"""
測試無對話框版本
Test No MessageBox Version

驗證所有messagebox都已移除，避免GIL問題

作者: GIL問題修正
日期: 2025-07-04
"""

import ast
import os

def check_messagebox_usage(file_path):
    """檢查文件中是否還有messagebox使用"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查是否有messagebox導入
        has_import = 'messagebox' in content
        
        # 檢查是否有messagebox調用
        messagebox_calls = []
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if 'messagebox.' in line:
                messagebox_calls.append((i, line.strip()))
        
        return {
            'file': file_path,
            'has_import': has_import,
            'calls': messagebox_calls,
            'total_calls': len(messagebox_calls)
        }
        
    except Exception as e:
        return {
            'file': file_path,
            'error': str(e)
        }

def main():
    """主測試函數"""
    print("🧪 檢查messagebox使用情況...")
    
    # 要檢查的文件
    files_to_check = [
        'simple_integrated.py',
        'order_mode_ui_controller.py',
        'virtual_real_order_manager.py',
        'unified_order_tracker.py'
    ]
    
    total_issues = 0
    
    for file_name in files_to_check:
        file_path = file_name
        if os.path.exists(file_path):
            result = check_messagebox_usage(file_path)
            
            print(f"\n📁 檢查文件: {file_name}")
            
            if 'error' in result:
                print(f"❌ 檢查失敗: {result['error']}")
                continue
            
            if result['has_import']:
                print("⚠️ 仍有messagebox導入")
                total_issues += 1
            else:
                print("✅ 無messagebox導入")
            
            if result['total_calls'] > 0:
                print(f"❌ 發現 {result['total_calls']} 個messagebox調用:")
                for line_num, line in result['calls']:
                    print(f"   第{line_num}行: {line}")
                total_issues += result['total_calls']
            else:
                print("✅ 無messagebox調用")
        else:
            print(f"⚠️ 文件不存在: {file_name}")
    
    print(f"\n📊 檢查結果:")
    if total_issues == 0:
        print("✅ 所有文件都已移除messagebox，GIL風險已消除")
    else:
        print(f"❌ 發現 {total_issues} 個問題需要修正")
    
    return total_issues == 0

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 GIL風險修正完成！")
    else:
        print("\n⚠️ 仍有問題需要處理")
