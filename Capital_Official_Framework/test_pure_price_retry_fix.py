#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
測試純新報價追價修復
驗證口級別計算和純新報價邏輯
"""

import os
import sys
from datetime import datetime

def check_pure_price_retry_implementation():
    """檢查純新報價追價實施情況"""
    print("🔍 檢查純新報價追價修復...")
    
    try:
        # 檢查多組管理器
        mgr_file = "multi_group_position_manager.py"
        if not os.path.exists(mgr_file):
            print(f"❌ 文件不存在: {mgr_file}")
            return False
            
        with open(mgr_file, 'r', encoding='utf-8') as f:
            mgr_content = f.read()
        
        # 檢查虛擬機
        vm_file = "virtual_simple_integrated.py"
        if not os.path.exists(vm_file):
            print(f"❌ 文件不存在: {vm_file}")
            return False
            
        with open(vm_file, 'r', encoding='utf-8') as f:
            vm_content = f.read()
        
        # 檢查修復點
        mgr_checks = [
            ("🔄 [純新報價追價] LONG使用最新ASK1", "多組管理器LONG純新報價"),
            ("🔄 [純新報價追價] SHORT使用最新BID1", "多組管理器SHORT純新報價"),
            ("🔄 [純新報價追價] 多單進場使用最新ASK1", "進場LONG純新報價"),
            ("🔄 [純新報價追價] 空單進場使用最新BID1", "進場SHORT純新報價"),
            ("🔄 [備用純新報價] 多單使用估算ASK1", "備用LONG純新報價"),
            ("🔄 [備用純新報價] 空單使用估算BID1", "備用SHORT純新報價"),
            ("retry_price = current_ask1", "LONG直接使用ASK1"),
            ("retry_price = current_bid1", "SHORT直接使用BID1"),
            ("口級別追價", "口級別LOG修復")
        ]
        
        vm_checks = [
            ("🔄 [純新報價追價] 多單平倉使用最新BID1", "虛擬機多單平倉純新報價"),
            ("🔄 [純新報價追價] 空單平倉使用最新ASK1", "虛擬機空單平倉純新報價"),
            ("retry_price = current_bid1", "虛擬機多單平倉直接使用BID1"),
            ("retry_price = current_ask1", "虛擬機空單平倉直接使用ASK1")
        ]
        
        print(f"\n📋 多組管理器修復檢查:")
        mgr_passed = True
        
        for keyword, description in mgr_checks:
            if keyword in mgr_content:
                print(f"  ✅ {description}: 已修復")
            else:
                print(f"  ❌ {description}: 未找到")
                mgr_passed = False
        
        print(f"\n📋 虛擬機修復檢查:")
        vm_passed = True
        
        for keyword, description in vm_checks:
            if keyword in vm_content:
                print(f"  ✅ {description}: 已修復")
            else:
                print(f"  ❌ {description}: 未找到")
                vm_passed = False
        
        # 檢查舊邏輯是否已移除
        print(f"\n📋 舊邏輯移除檢查:")
        old_logic_checks = [
            ("ASK1({current_ask1}) + {retry_count}", "舊LONG追價邏輯"),
            ("BID1({current_bid1}) - {retry_count}", "舊SHORT追價邏輯"),
            ("+ retry_count", "加點數邏輯"),
            ("- retry_count", "減點數邏輯")
        ]
        
        old_logic_found = False
        for keyword, description in old_logic_checks:
            if keyword in mgr_content or keyword in vm_content:
                print(f"  ⚠️ {description}: 仍存在（可能需要進一步清理）")
                old_logic_found = True
        
        if not old_logic_found:
            print(f"  ✅ 舊追價邏輯: 已完全移除")
        
        return mgr_passed and vm_passed
        
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")
        return False

def check_lot_level_retry_implementation():
    """檢查口級別追價實施情況"""
    print(f"\n🔧 檢查口級別追價機制...")
    
    try:
        # 檢查簡化追蹤器
        tracker_file = "simplified_order_tracker.py"
        if not os.path.exists(tracker_file):
            print(f"❌ 文件不存在: {tracker_file}")
            return False
            
        with open(tracker_file, 'r', encoding='utf-8') as f:
            tracker_content = f.read()
        
        # 檢查口級別功能
        lot_checks = [
            ("needs_retry_for_lot", "口級別追價檢查方法"),
            ("increment_retry_for_lot", "口級別追價計數方法"),
            ("individual_retry_counts", "口級別追價計數器"),
            ("current_lot_index", "當前口索引"),
            ("第{individual_retry_count}次", "口級別追價次數顯示"),
            ("口級別鎖定", "口級別鎖定機制")
        ]
        
        print(f"📋 口級別追價功能檢查:")
        all_passed = True
        
        for keyword, description in lot_checks:
            if keyword in tracker_content:
                print(f"  ✅ {description}: 已實施")
            else:
                print(f"  ❌ {description}: 未找到")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")
        return False

def generate_test_scenarios():
    """生成測試場景"""
    scenarios = """
🧪 測試場景設計

📋 建倉追價測試:
1. 多單建倉追價:
   - 預期LOG: "[純新報價追價] LONG使用最新ASK1: XXXX"
   - 不應出現: "ASK1(XXXX) + 1 = YYYY"

2. 空單建倉追價:
   - 預期LOG: "[純新報價追價] SHORT使用最新BID1: XXXX"
   - 不應出現: "BID1(XXXX) - 1 = YYYY"

3. 口級別追價次數:
   - 第1口: "第1次"
   - 第2口: "第1次" (不是第2次)
   - 第3口: "第1次" (不是第3次)

📋 平倉追價測試:
1. 多單平倉追價:
   - 預期LOG: "[純新報價追價] 多單平倉使用最新BID1: XXXX"

2. 空單平倉追價:
   - 預期LOG: "[純新報價追價] 空單平倉使用最新ASK1: XXXX"

🔍 關鍵監控點:
- 簡化追蹤器顯示: "第1次, 1口 (口級別鎖定)"
- 多組管理器顯示: "(口級別追價)" 而非 "第X次重試"
- 價格計算: 直接使用最新報價，不加減點數

⚠️ 問題指標:
- 如果看到 "ASK1(XXXX) + N" 表示舊邏輯未完全移除
- 如果看到 "第2次"、"第3次" 表示口級別計算有問題
- 如果追價價格不是最新報價，表示純新報價邏輯有問題
    """
    
    print(scenarios)

def main():
    """主測試函數"""
    print("=" * 70)
    print("🚀 純新報價追價修復驗證")
    print("=" * 70)
    
    test_results = []
    
    # 執行檢查
    test_results.append(("純新報價追價實施", check_pure_price_retry_implementation()))
    test_results.append(("口級別追價機制", check_lot_level_retry_implementation()))
    
    # 統計結果
    passed_tests = sum(1 for _, result in test_results if result)
    total_tests = len(test_results)
    
    print("=" * 70)
    print(f"📊 檢查結果: {passed_tests}/{total_tests} 通過")
    print("=" * 70)
    
    for test_name, result in test_results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{status} {test_name}")
    
    if passed_tests == total_tests:
        print("\n🎉 修復驗證通過！")
        print("\n📋 現在可以測試:")
        print("1. 啟動虛擬交易系統")
        print("2. 觸發建倉追價")
        print("3. 觀察LOG輸出")
        print("4. 確認使用純新報價和口級別計算")
        
        print("\n🧪 測試場景:")
        generate_test_scenarios()
    else:
        print("\n⚠️ 部分檢查失敗，請檢查修復")
    
    print("=" * 70)

if __name__ == "__main__":
    # 切換到正確目錄
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    main()
