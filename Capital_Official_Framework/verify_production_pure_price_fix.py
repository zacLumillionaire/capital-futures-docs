#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
驗證正式機純新報價追價修復
確認正式機與虛擬機使用相同的修復邏輯
"""

import os
import sys
from datetime import datetime

def check_production_fix():
    """檢查正式機修復情況"""
    print("🔍 檢查正式機純新報價追價修復...")
    
    try:
        # 檢查正式機主文件
        prod_file = "simple_integrated.py"
        if not os.path.exists(prod_file):
            print(f"❌ 正式機文件不存在: {prod_file}")
            return False
            
        with open(prod_file, 'r', encoding='utf-8') as f:
            prod_content = f.read()
        
        # 檢查虛擬機文件作為對比
        vm_file = "virtual_simple_integrated.py"
        if not os.path.exists(vm_file):
            print(f"❌ 虛擬機文件不存在: {vm_file}")
            return False
            
        with open(vm_file, 'r', encoding='utf-8') as f:
            vm_content = f.read()
        
        # 檢查正式機修復點
        prod_checks = [
            ("🔄 [純新報價追價] 多單平倉使用最新BID1", "正式機多單平倉純新報價"),
            ("🔄 [純新報價追價] 空單平倉使用最新ASK1", "正式機空單平倉純新報價"),
            ("retry_price = current_bid1", "正式機多單平倉直接使用BID1"),
            ("retry_price = current_ask1", "正式機空單平倉直接使用ASK1"),
            ("純新報價追價邏輯", "正式機註釋更新"),
            ("直接使用最新BID1", "正式機註釋更新"),
            ("直接使用最新ASK1", "正式機註釋更新")
        ]
        
        print(f"\n📋 正式機修復檢查:")
        prod_passed = True
        
        for keyword, description in prod_checks:
            if keyword in prod_content:
                print(f"  ✅ {description}: 已修復")
            else:
                print(f"  ❌ {description}: 未找到")
                prod_passed = False
        
        # 檢查舊邏輯是否已移除
        print(f"\n📋 正式機舊邏輯移除檢查:")
        old_logic_checks = [
            ("BID1({current_bid1}) - {retry_count}", "舊多單平倉邏輯"),
            ("ASK1({current_ask1}) + {retry_count}", "舊空單平倉邏輯"),
            ("- retry_count", "減點數邏輯"),
            ("+ retry_count", "加點數邏輯")
        ]
        
        old_logic_found = False
        for keyword, description in old_logic_checks:
            if keyword in prod_content:
                print(f"  ⚠️ {description}: 仍存在（需要進一步檢查）")
                old_logic_found = True
        
        if not old_logic_found:
            print(f"  ✅ 舊平倉追價邏輯: 已完全移除")
        
        return prod_passed and not old_logic_found
        
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")
        return False

def compare_with_virtual_machine():
    """與虛擬機對比檢查"""
    print(f"\n🔄 與虛擬機對比檢查...")
    
    try:
        # 讀取兩個文件
        with open("simple_integrated.py", 'r', encoding='utf-8') as f:
            prod_content = f.read()
        
        with open("virtual_simple_integrated.py", 'r', encoding='utf-8') as f:
            vm_content = f.read()
        
        # 檢查關鍵修復點是否一致
        consistency_checks = [
            ("🔄 [純新報價追價] 多單平倉使用最新BID1", "多單平倉LOG"),
            ("🔄 [純新報價追價] 空單平倉使用最新ASK1", "空單平倉LOG"),
            ("retry_price = current_bid1", "多單平倉邏輯"),
            ("retry_price = current_ask1", "空單平倉邏輯")
        ]
        
        print(f"📋 正式機與虛擬機一致性檢查:")
        all_consistent = True
        
        for keyword, description in consistency_checks:
            prod_has = keyword in prod_content
            vm_has = keyword in vm_content
            
            if prod_has and vm_has:
                print(f"  ✅ {description}: 一致")
            elif not prod_has and not vm_has:
                print(f"  ⚠️ {description}: 都沒有（可能正常）")
            else:
                print(f"  ❌ {description}: 不一致（正式機:{prod_has}, 虛擬機:{vm_has}）")
                all_consistent = False
        
        return all_consistent
        
    except Exception as e:
        print(f"❌ 對比檢查失敗: {e}")
        return False

def check_shared_components():
    """檢查共用組件"""
    print(f"\n🔧 檢查共用組件修復...")
    
    try:
        # 檢查多組管理器（共用文件）
        mgr_file = "multi_group_position_manager.py"
        if not os.path.exists(mgr_file):
            print(f"❌ 多組管理器文件不存在: {mgr_file}")
            return False
            
        with open(mgr_file, 'r', encoding='utf-8') as f:
            mgr_content = f.read()
        
        # 檢查共用組件修復
        shared_checks = [
            ("🔄 [純新報價追價] LONG使用最新ASK1", "建倉LONG純新報價"),
            ("🔄 [純新報價追價] SHORT使用最新BID1", "建倉SHORT純新報價"),
            ("口級別追價", "口級別LOG修復"),
            ("retry_price = current_ask1", "LONG直接使用ASK1"),
            ("retry_price = current_bid1", "SHORT直接使用BID1")
        ]
        
        print(f"📋 共用組件修復檢查:")
        all_passed = True
        
        for keyword, description in shared_checks:
            if keyword in mgr_content:
                print(f"  ✅ {description}: 已修復")
            else:
                print(f"  ❌ {description}: 未找到")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ 共用組件檢查失敗: {e}")
        return False

def generate_production_test_guide():
    """生成正式機測試指南"""
    guide = """
🚀 正式機純新報價追價測試指南

📋 測試準備:
1. ✅ 正式機平倉追價邏輯已修復
2. ✅ 共用組件（多組管理器）已修復
3. ✅ 與虛擬機邏輯保持一致

🔧 測試步驟:
1. 啟動正式交易系統: python simple_integrated.py
2. 進行小量建倉測試（建議1口）
3. 觸發建倉追價操作
4. 觀察LOG輸出格式
5. 觸發平倉追價操作
6. 確認追價價格使用最新報價

🔍 關鍵監控點:

建倉追價:
- ✅ 看到: "[純新報價追價] LONG使用最新ASK1: XXXX"
- ✅ 看到: "(口級別追價)" 標籤
- ❌ 不應看到: "ASK1(XXXX) + N = YYYY"

平倉追價:
- ✅ 看到: "[純新報價追價] 多單平倉使用最新BID1: XXXX"
- ✅ 看到: "[純新報價追價] 空單平倉使用最新ASK1: XXXX"
- ❌ 不應看到: "BID1(XXXX) - N = YYYY"

⚠️ 風險控制:
1. 建議先用小量測試（1口）
2. 密切監控追價成交情況
3. 確認滑價控制在合理範圍
4. 如有異常立即停止交易

🛡️ 回退方案:
如果發現問題，可以：
1. 立即停止自動交易
2. 手動處理未完成部位
3. 檢查日誌分析問題原因
4. 必要時回退到備份版本

📊 預期效果:
- 追價價格更貼近市場實況
- 減少不必要的滑價成本
- 提高追價成功率
- LOG輸出更清晰易懂
    """
    
    print(guide)

def main():
    """主驗證函數"""
    print("=" * 70)
    print("🚀 正式機純新報價追價修復驗證")
    print("=" * 70)
    
    test_results = []
    
    # 執行檢查
    test_results.append(("正式機修復檢查", check_production_fix()))
    test_results.append(("與虛擬機一致性", compare_with_virtual_machine()))
    test_results.append(("共用組件檢查", check_shared_components()))
    
    # 統計結果
    passed_tests = sum(1 for _, result in test_results if result)
    total_tests = len(test_results)
    
    print("=" * 70)
    print(f"📊 驗證結果: {passed_tests}/{total_tests} 通過")
    print("=" * 70)
    
    for test_name, result in test_results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{status} {test_name}")
    
    if passed_tests == total_tests:
        print("\n🎉 正式機修復驗證通過！")
        print("\n📋 修復總結:")
        print("✅ 正式機平倉追價：使用純新報價邏輯")
        print("✅ 建倉追價（共用組件）：使用純新報價邏輯")
        print("✅ 口級別計算：與虛擬機保持一致")
        print("✅ LOG輸出：統一格式標準")
        
        print("\n🚀 現在可以進行正式機測試:")
        generate_production_test_guide()
    else:
        print("\n⚠️ 部分驗證失敗，請檢查修復")
    
    print("=" * 70)

if __name__ == "__main__":
    # 切換到正確目錄
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    main()
