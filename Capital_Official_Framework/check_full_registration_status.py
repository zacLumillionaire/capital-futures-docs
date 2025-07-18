#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
檢查完整註冊功能狀態
快速確認系統配置和準備情況
"""

import os
import sys
from datetime import datetime

def check_main_file_status():
    """檢查主文件狀態"""
    print("🔍 檢查主文件配置...")
    
    try:
        main_file = "simple_integrated.py"
        if not os.path.exists(main_file):
            print(f"❌ 主文件不存在: {main_file}")
            return False
            
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查關鍵配置
        status_checks = [
            ("enable_exit_retry_full_registration', True)", "✅ 完整註冊已啟用"),
            ("enable_exit_retry_full_registration', False)", "❌ 完整註冊已禁用"),
            ("[FULL_REG]", "✅ LOG標籤已配置"),
            ("_register_exit_retry_order_full", "✅ 完整註冊方法已實施"),
            ("exit_retry_registration.log", "✅ 日誌文件已配置")
        ]
        
        print(f"📋 配置狀態:")
        enabled = False
        
        for check, message in status_checks:
            if check in content:
                if "True)" in check:
                    enabled = True
                print(f"  {message}")
                break
        
        if not enabled and "False)" in content:
            print(f"  ❌ 完整註冊已禁用")
        
        return enabled
        
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")
        return False

def check_log_files():
    """檢查日誌文件"""
    print(f"\n📄 檢查日誌文件...")
    
    log_files = [
        "exit_retry_registration.log",
        "exit_callback_errors.log", 
        "exit_retry_failures.log"
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            try:
                size = os.path.getsize(log_file)
                mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
                print(f"  ✅ {log_file}: {size} bytes, 修改時間: {mtime}")
                
                # 顯示最後幾行
                if size > 0:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        if len(lines) > 0:
                            print(f"    📝 最後內容: {lines[-1].strip()}")
                            
            except Exception as e:
                print(f"  ⚠️ {log_file}: 讀取失敗 - {e}")
        else:
            print(f"  ➖ {log_file}: 不存在（正常，會在使用時創建）")

def check_system_readiness():
    """檢查系統準備情況"""
    print(f"\n🔧 檢查系統準備情況...")
    
    # 檢查相關文件
    required_files = [
        ("simple_integrated.py", "主應用文件"),
        ("unified_order_tracker.py", "統一追蹤器"),
        ("fifo_order_matcher.py", "FIFO匹配器"),
        ("simplified_order_tracker.py", "簡化追蹤器"),
        ("exit_retry_registration_controller.py", "註冊控制器")
    ]
    
    print(f"📋 必要文件檢查:")
    all_ready = True
    
    for filename, description in required_files:
        if os.path.exists(filename):
            print(f"  ✅ {description}: {filename}")
        else:
            print(f"  ❌ {description}: {filename} (缺失)")
            all_ready = False
    
    return all_ready

def generate_test_instructions():
    """生成測試說明"""
    instructions = """
🚀 完整註冊功能測試說明

📋 測試準備:
1. ✅ 完整註冊功能已啟用
2. ✅ 詳細LOG已配置
3. ✅ 日誌文件已準備

🔧 測試步驟:
1. 啟動交易系統 (python simple_integrated.py)
2. 觀察啟動LOG中的註冊狀態提示
3. 觸發需要追價的平倉操作
4. 觀察控制台 [FULL_REG] LOG輸出
5. 檢查 exit_retry_registration.log 文件

🔍 關鍵監控點:
- 系統啟動時顯示: "🔧 完整註冊模式：啟用"
- 追價時顯示: "[FULL_REG] 🚀 開始完整註冊追價訂單"
- 成功時顯示: "[FULL_REG] ✅ 統一追蹤器註冊成功"
- 成功時顯示: "[FULL_REG] ✅ FIFO匹配器自動註冊成功"
- 結果顯示: "[FULL_REG] 📊 註冊結果統計: 成功率: 3/3"

⚠️ 問題排查:
- 如果看到 "❌ 統一追蹤器不可用"，檢查組件初始化
- 如果看到 "⚠️ FIFO匹配器不可用"，檢查統一追蹤器配置
- 如果出現異常，查看詳細錯誤堆疊

🛡️ 安全保障:
- 基本平倉功能（簡化追蹤器）不受影響
- 可隨時使用控制器禁用完整註冊
- 所有操作都有詳細LOG記錄
    """
    
    print(instructions)

def main():
    """主檢查函數"""
    print("=" * 60)
    print("🔍 完整註冊功能狀態檢查")
    print("=" * 60)
    
    # 執行檢查
    main_status = check_main_file_status()
    check_log_files()
    system_ready = check_system_readiness()
    
    print("=" * 60)
    print("📊 檢查結果:")
    
    if main_status:
        print("✅ 完整註冊功能：已啟用")
    else:
        print("❌ 完整註冊功能：未啟用")
    
    if system_ready:
        print("✅ 系統文件：準備就緒")
    else:
        print("⚠️ 系統文件：部分缺失")
    
    if main_status and system_ready:
        print("\n🎉 系統準備完成，可以開始測試！")
        generate_test_instructions()
    else:
        print("\n⚠️ 系統未完全準備，請檢查配置")
    
    print("=" * 60)

if __name__ == "__main__":
    # 切換到正確目錄
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    main()
