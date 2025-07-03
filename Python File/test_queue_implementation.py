#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Queue實施驗證腳本
用於檢查Queue方案實施的每個步驟是否正確
"""

import os
import sys
import importlib.util
import ast
import re

def check_file_exists(file_path):
    """檢查文件是否存在"""
    if os.path.exists(file_path):
        print(f"✅ 文件存在: {file_path}")
        return True
    else:
        print(f"❌ 文件不存在: {file_path}")
        return False

def check_backup_files():
    """檢查備份文件是否存在"""
    print("\n🔍 檢查備份文件...")
    
    backup_files = [
        "OrderTester_pre_queue_backup.py",
        "order/future_order_pre_queue_backup.py"
    ]
    
    all_exist = True
    for file_path in backup_files:
        if not check_file_exists(file_path):
            all_exist = False
    
    if all_exist:
        print("✅ 所有備份文件已準備完成")
    else:
        print("❌ 請先創建備份文件")
    
    return all_exist

def check_syntax(file_path):
    """檢查Python文件語法"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        ast.parse(content)
        print(f"✅ 語法檢查通過: {file_path}")
        return True
    except SyntaxError as e:
        print(f"❌ 語法錯誤 {file_path}: {e}")
        return False
    except Exception as e:
        print(f"❌ 檢查失敗 {file_path}: {e}")
        return False

def check_step1_queue_initialization():
    """檢查步驟1: Queue初始化"""
    print("\n🔍 檢查步驟1: Queue初始化...")
    
    file_path = "OrderTester.py"
    if not check_file_exists(file_path):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查必要的導入
        imports_found = {
            'queue': 'import queue' in content,
            'threading': 'import threading' in content,
            'time': 'import time' in content
        }
        
        # 檢查Queue初始化
        queue_init_patterns = [
            r'self\.tick_data_queue\s*=\s*queue\.Queue',
            r'self\.strategy_queue\s*=\s*queue\.Queue',
            r'self\.log_queue\s*=\s*queue\.Queue'
        ]
        
        queues_found = {}
        for pattern in queue_init_patterns:
            queue_name = pattern.split('.')[1].split('\\')[0]
            queues_found[queue_name] = bool(re.search(pattern, content))
        
        # 報告結果
        print("📋 導入檢查:")
        for imp, found in imports_found.items():
            status = "✅" if found else "❌"
            print(f"  {status} {imp}")
        
        print("📋 Queue初始化檢查:")
        for queue, found in queues_found.items():
            status = "✅" if found else "❌"
            print(f"  {status} {queue}")
        
        all_good = all(imports_found.values()) and all(queues_found.values())
        
        if all_good:
            print("✅ 步驟1檢查通過")
        else:
            print("❌ 步驟1檢查失敗")
        
        return all_good
        
    except Exception as e:
        print(f"❌ 檢查步驟1失敗: {e}")
        return False

def check_step2_com_event_modification():
    """檢查步驟2: COM事件修改"""
    print("\n🔍 檢查步驟2: COM事件修改...")
    
    file_path = "order/future_order.py"
    if not check_file_exists(file_path):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查OnNotifyTicksLONG函數是否存在
        function_pattern = r'def OnNotifyTicksLONG\(self[^)]*\):'
        function_found = bool(re.search(function_pattern, content))
        
        # 檢查是否包含Queue操作
        queue_operations = [
            r'tick_data_queue\.put_nowait',
            r'tick_data\s*=\s*{',
            r'return 0'
        ]
        
        operations_found = {}
        for pattern in queue_operations:
            operations_found[pattern] = bool(re.search(pattern, content))
        
        # 檢查是否移除了UI操作 (不應該包含這些)
        ui_operations = [
            r'\.config\(',
            r'logging\.getLogger.*\.info',
            r'print\('
        ]
        
        ui_removed = {}
        for pattern in ui_operations:
            # 在OnNotifyTicksLONG函數內檢查
            ui_removed[pattern] = not bool(re.search(pattern, content))
        
        print("📋 函數檢查:")
        status = "✅" if function_found else "❌"
        print(f"  {status} OnNotifyTicksLONG函數存在")
        
        print("📋 Queue操作檢查:")
        for op, found in operations_found.items():
            status = "✅" if found else "❌"
            print(f"  {status} {op}")
        
        print("📋 UI操作移除檢查:")
        for op, removed in ui_removed.items():
            status = "✅" if removed else "⚠️"
            print(f"  {status} 已移除 {op}")
        
        all_good = function_found and all(operations_found.values())
        
        if all_good:
            print("✅ 步驟2檢查通過")
        else:
            print("❌ 步驟2檢查失敗")
        
        return all_good
        
    except Exception as e:
        print(f"❌ 檢查步驟2失敗: {e}")
        return False

def check_step3_queue_processing():
    """檢查步驟3: Queue處理機制"""
    print("\n🔍 檢查步驟3: Queue處理機制...")
    
    file_path = "OrderTester.py"
    if not check_file_exists(file_path):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查必要的函數
        required_functions = [
            r'def start_queue_processing\(self\):',
            r'def process_tick_queue\(self\):',
            r'def process_log_queue\(self\):',
            r'def add_log_to_queue\(self,'
        ]
        
        functions_found = {}
        for pattern in required_functions:
            func_name = pattern.split('def ')[1].split('(')[0]
            functions_found[func_name] = bool(re.search(pattern, content))
        
        # 檢查關鍵操作
        key_operations = [
            r'tick_data_queue\.get_nowait',
            r'strategy_queue\.put_nowait',
            r'log_queue\.put_nowait',
            r'root\.after\('
        ]
        
        operations_found = {}
        for pattern in key_operations:
            operations_found[pattern] = bool(re.search(pattern, content))
        
        print("📋 函數檢查:")
        for func, found in functions_found.items():
            status = "✅" if found else "❌"
            print(f"  {status} {func}")
        
        print("📋 關鍵操作檢查:")
        for op, found in operations_found.items():
            status = "✅" if found else "❌"
            print(f"  {status} {op}")
        
        all_good = all(functions_found.values()) and all(operations_found.values())
        
        if all_good:
            print("✅ 步驟3檢查通過")
        else:
            print("❌ 步驟3檢查失敗")
        
        return all_good
        
    except Exception as e:
        print(f"❌ 檢查步驟3失敗: {e}")
        return False

def check_step4_strategy_thread():
    """檢查步驟4: 策略執行緒"""
    print("\n🔍 檢查步驟4: 策略執行緒...")
    
    file_path = "OrderTester.py"
    if not check_file_exists(file_path):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查策略執行緒相關函數
        strategy_functions = [
            r'def start_strategy_thread\(self\):',
            r'def stop_strategy_thread\(self\):',
            r'def strategy_logic_thread\(self\):'
        ]
        
        functions_found = {}
        for pattern in strategy_functions:
            func_name = pattern.split('def ')[1].split('(')[0]
            functions_found[func_name] = bool(re.search(pattern, content))
        
        # 檢查執行緒操作
        thread_operations = [
            r'threading\.Thread',
            r'strategy_queue\.get\(',
            r'strategy_thread_running'
        ]
        
        operations_found = {}
        for pattern in thread_operations:
            operations_found[pattern] = bool(re.search(pattern, content))
        
        print("📋 策略執行緒函數檢查:")
        for func, found in functions_found.items():
            status = "✅" if found else "❌"
            print(f"  {status} {func}")
        
        print("📋 執行緒操作檢查:")
        for op, found in operations_found.items():
            status = "✅" if found else "❌"
            print(f"  {status} {op}")
        
        all_good = all(functions_found.values()) and all(operations_found.values())
        
        if all_good:
            print("✅ 步驟4檢查通過")
        else:
            print("❌ 步驟4檢查失敗")
        
        return all_good
        
    except Exception as e:
        print(f"❌ 檢查步驟4失敗: {e}")
        return False

def run_syntax_check():
    """運行語法檢查"""
    print("\n🔍 運行語法檢查...")
    
    files_to_check = [
        "OrderTester.py",
        "order/future_order.py"
    ]
    
    all_good = True
    for file_path in files_to_check:
        if check_file_exists(file_path):
            if not check_syntax(file_path):
                all_good = False
        else:
            all_good = False
    
    return all_good

def main():
    """主函數"""
    print("🚀 Queue實施驗證腳本")
    print("=" * 50)
    
    # 檢查備份文件
    if not check_backup_files():
        print("\n❌ 請先創建備份文件再繼續")
        return
    
    # 運行語法檢查
    if not run_syntax_check():
        print("\n❌ 語法檢查失敗，請修正錯誤")
        return
    
    # 檢查各個步驟
    steps = [
        ("步驟1: Queue初始化", check_step1_queue_initialization),
        ("步驟2: COM事件修改", check_step2_com_event_modification),
        ("步驟3: Queue處理機制", check_step3_queue_processing),
        ("步驟4: 策略執行緒", check_step4_strategy_thread)
    ]
    
    results = []
    for step_name, check_func in steps:
        try:
            result = check_func()
            results.append((step_name, result))
        except Exception as e:
            print(f"❌ {step_name} 檢查異常: {e}")
            results.append((step_name, False))
    
    # 總結報告
    print("\n" + "=" * 50)
    print("📊 檢查結果總結:")
    
    all_passed = True
    for step_name, passed in results:
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"  {status} {step_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 所有檢查通過！可以開始測試Queue機制")
        print("📝 建議：啟動程式並測試策略監控功能")
    else:
        print("⚠️ 部分檢查失敗，請檢查並修正問題")
        print("📝 建議：參考實施指南重新檢查相關步驟")

if __name__ == "__main__":
    main()
