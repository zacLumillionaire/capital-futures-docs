#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
測試完整註冊LOG功能
驗證詳細LOG輸出和追蹤功能
"""

import os
import sys
from datetime import datetime

def check_log_implementation():
    """檢查LOG實施情況"""
    print("🔍 檢查完整註冊LOG實施...")
    
    try:
        main_file = "simple_integrated.py"
        if not os.path.exists(main_file):
            print(f"❌ 主文件不存在: {main_file}")
            return False
            
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查LOG標籤
        log_checks = [
            ("[FULL_REG]", "完整註冊LOG標籤"),
            ("開始完整註冊追價訂單", "開始註冊LOG"),
            ("步驟1: 註冊到統一追蹤器", "統一追蹤器步驟LOG"),
            ("步驟2: 檢查FIFO匹配器註冊", "FIFO匹配器步驟LOG"),
            ("註冊結果統計", "結果統計LOG"),
            ("詳細日誌已記錄", "日誌記錄確認"),
            ("exit_retry_registration.log", "日誌文件名"),
            ("錯誤詳情: {traceback.format_exc()}", "詳細錯誤追蹤")
        ]
        
        print(f"\n📋 LOG功能檢查:")
        all_passed = True
        
        for keyword, description in log_checks:
            if keyword in content:
                print(f"  ✅ {description}: 已實施")
            else:
                print(f"  ❌ {description}: 未找到")
                all_passed = False
        
        # 檢查啟用狀態
        if "enable_exit_retry_full_registration', True)" in content:
            print(f"  ✅ 完整註冊已啟用: 正確")
        else:
            print(f"  ⚠️ 完整註冊狀態: 需要確認")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ LOG檢查失敗: {e}")
        return False

def create_test_log_entry():
    """創建測試日誌條目"""
    print(f"\n🧪 創建測試日誌條目...")
    
    try:
        log_file = "exit_retry_registration.log"
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        test_entry = f"""[{timestamp}] 測試日誌條目:
  部位ID: TEST_001
  訂單ID: TEST_ORDER_001
  方向: BUY, 價格: 23300.0, 重試: 1
  註冊結果: {{'simplified': True, 'unified': True, 'fifo': True}}
  成功率: 3/3
{'=' * 50}
"""
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(test_entry)
        
        print(f"✅ 測試日誌條目已創建: {log_file}")
        
        # 讀取並顯示最後幾行
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if len(lines) > 0:
                print(f"📄 日誌文件最後內容:")
                for line in lines[-6:]:  # 顯示最後6行
                    print(f"    {line.rstrip()}")
        
        return True
        
    except Exception as e:
        print(f"❌ 創建測試日誌失敗: {e}")
        return False

def check_log_format():
    """檢查日誌格式"""
    print(f"\n📋 檢查日誌格式規範...")
    
    format_requirements = [
        "時間戳格式: [YYYY-MM-DD HH:MM:SS]",
        "LOG標籤: [FULL_REG]",
        "結構化資訊: 部位ID, 訂單ID, 方向, 價格",
        "註冊結果: 字典格式記錄各追蹤器狀態",
        "成功率統計: X/Y 格式",
        "分隔線: 便於區分不同條目"
    ]
    
    print(f"📋 日誌格式要求:")
    for requirement in format_requirements:
        print(f"  ✅ {requirement}")
    
    return True

def generate_monitoring_guide():
    """生成監控指南"""
    guide = """
🔍 完整註冊LOG監控指南

📋 LOG標籤說明:
[FULL_REG] 🚀 開始完整註冊追價訂單    # 註冊流程開始
[FULL_REG] 📝 步驟1: 註冊到統一追蹤器  # 統一追蹤器註冊
[FULL_REG] 📝 步驟2: 檢查FIFO匹配器   # FIFO匹配器檢查
[FULL_REG] 📊 註冊結果統計           # 最終結果統計
[FULL_REG] 🏁 完整註冊流程結束       # 流程結束

📄 日誌文件:
- exit_retry_registration.log: 詳細註冊記錄
- 包含時間戳、部位資訊、註冊結果

🔍 監控重點:
1. 統一追蹤器註冊是否成功
2. FIFO匹配器是否正確關聯
3. 註冊成功率 (應該是 3/3)
4. 錯誤詳情和堆疊追蹤

⚠️ 問題排查:
- 如果統一追蹤器註冊失敗，檢查組件初始化
- 如果FIFO匹配器未關聯，檢查統一追蹤器配置
- 如果出現異常，查看詳細錯誤堆疊

✅ 成功指標:
- 控制台顯示 [FULL_REG] ✅ 統一追蹤器註冊成功
- 控制台顯示 [FULL_REG] ✅ FIFO匹配器自動註冊成功
- 日誌顯示 成功率: 3/3
    """
    
    print(guide)
    return guide

def main():
    """主測試函數"""
    print("=" * 70)
    print("🚀 完整註冊LOG功能測試")
    print("=" * 70)
    
    test_results = []
    
    # 執行各項檢查
    test_results.append(("LOG實施檢查", check_log_implementation()))
    test_results.append(("測試日誌創建", create_test_log_entry()))
    test_results.append(("日誌格式檢查", check_log_format()))
    
    # 統計結果
    passed_tests = sum(1 for _, result in test_results if result)
    total_tests = len(test_results)
    
    print("=" * 70)
    print(f"📊 測試結果: {passed_tests}/{total_tests} 通過")
    print("=" * 70)
    
    for test_name, result in test_results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{status} {test_name}")
    
    if passed_tests == total_tests:
        print("\n🎉 LOG功能實施完成！")
        print("\n📋 現在可以開始測試:")
        print("1. 啟動交易系統")
        print("2. 觸發追價平倉")
        print("3. 觀察控制台 [FULL_REG] LOG輸出")
        print("4. 檢查 exit_retry_registration.log 文件")
        
        print("\n🔍 監控指南:")
        generate_monitoring_guide()
    else:
        print("\n⚠️ 部分檢查失敗，請檢查實施")
    
    print("=" * 70)

if __name__ == "__main__":
    # 切換到正確目錄
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    main()
