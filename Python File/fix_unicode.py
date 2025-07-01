#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復OrderTester.py中的Unicode字符
"""

import re

def fix_unicode_in_file(file_path):
    """修復檔案中的Unicode字符"""
    
    # Unicode字符對應表
    unicode_replacements = {
        '✅': '[OK]',
        '❌': '[ERROR]',
        '⚠️': '[WARN]',
        'ℹ️': '[INFO]',
        '🔍': '[SEARCH]',
        '🔄': '[LOADING]',
        '📡': '[TCP]',
        '⏹️': '[STOP]',
        '🏷️': '[TAG]',
        '📋': '[LIST]',
    }
    
    try:
        # 讀取檔案
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 記錄修改
        changes = []
        
        # 替換Unicode字符
        for unicode_char, replacement in unicode_replacements.items():
            if unicode_char in content:
                count = content.count(unicode_char)
                content = content.replace(unicode_char, replacement)
                changes.append(f"  {unicode_char} -> {replacement} ({count}次)")
        
        # 寫回檔案
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"修復完成: {file_path}")
        if changes:
            print("修改內容:")
            for change in changes:
                print(change)
        else:
            print("  沒有需要修復的Unicode字符")
        
        return True
        
    except Exception as e:
        print(f"修復失敗: {e}")
        return False

if __name__ == "__main__":
    print("開始修復OrderTester.py中的Unicode字符...")
    success = fix_unicode_in_file("OrderTester.py")
    
    if success:
        print("\n修復完成！現在可以重新啟動OrderTester.py測試")
    else:
        print("\n修復失敗！請檢查錯誤訊息")
    
    input("按Enter鍵結束...")
