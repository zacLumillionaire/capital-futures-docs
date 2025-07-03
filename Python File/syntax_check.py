#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
語法檢查腳本
"""

import ast
import sys

def check_syntax(filename):
    """檢查Python文件語法"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # 嘗試解析語法
        ast.parse(source)
        print(f"✅ {filename}: 語法正確")
        return True
        
    except SyntaxError as e:
        print(f"❌ {filename}: 語法錯誤 - 第{e.lineno}行: {e.msg}")
        return False
    except Exception as e:
        print(f"❌ {filename}: 檢查失敗 - {e}")
        return False

def main():
    """主函數"""
    files_to_check = [
        "Python File/OrderTester.py",
        "Python File/order/future_order.py"
    ]
    
    print("🔧 開始語法檢查...")
    
    results = []
    for filename in files_to_check:
        results.append(check_syntax(filename))
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 檢查結果: {passed}/{total} 通過")
    
    if passed == total:
        print("🎉 所有文件語法正確！")
    else:
        print("⚠️ 部分文件有語法錯誤")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    print(f"結果: {'成功' if success else '失敗'}")
