#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
驗證日期範圍設定
"""

import sys
import os
from datetime import datetime, date

def verify_date_range_settings():
    """驗證日期範圍設定"""
    print("🗓️ 驗證 mdd_gui.py 日期範圍設定")
    print("=" * 60)
    print(f"開始時間: {datetime.now()}")
    
    results = {}
    
    # 測試1：檢查 mdd_gui.py 中的日期設定
    print("\n🔍 測試1：檢查 mdd_gui.py 中的日期設定")
    try:
        with open('experiment_analysis/mdd_gui.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = []
        checks.append(('開始日期設定', '"start_date": "2024-11-04"' in content))
        checks.append(('結束日期設定', '"end_date": "2025-06-28"' in content))
        checks.append(('GUI日期顯示', '2024-11-04 至 2025-06-28' in content))
        checks.append(('日期範圍說明', '約 7.8 個月' in content))
        checks.append(('日誌輸出日期', '回測日期範圍: 2024-11-04 至 2025-06-28' in content))
        
        all_passed = all(check[1] for check in checks)
        if all_passed:
            print("✅ mdd_gui.py 日期設定正確")
            results['date_settings'] = True
        else:
            print("❌ mdd_gui.py 日期設定有問題:")
            for name, passed in checks:
                print(f"  - {name}: {'✅' if passed else '❌'}")
            results['date_settings'] = False
            
    except Exception as e:
        print(f"❌ 日期設定檢查失敗: {e}")
        results['date_settings'] = False
    
    # 測試2：計算實際日期範圍
    print("\n🔍 測試2：計算實際日期範圍")
    try:
        start_date = date(2024, 11, 4)
        end_date = date(2025, 6, 28)
        
        # 計算天數差異
        date_diff = (end_date - start_date).days
        
        # 計算月數差異（近似）
        months_diff = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        months_diff += (end_date.day - start_date.day) / 30  # 近似計算
        
        print(f"✅ 日期範圍分析:")
        print(f"  - 開始日期: {start_date}")
        print(f"  - 結束日期: {end_date}")
        print(f"  - 總天數: {date_diff} 天")
        print(f"  - 約 {months_diff:.1f} 個月")
        print(f"  - 約 {date_diff/7:.1f} 週")
        
        # 檢查是否涵蓋足夠的交易日
        if date_diff >= 200:  # 至少200天
            print("✅ 日期範圍足夠進行可靠的回測分析")
            results['date_range_analysis'] = True
        else:
            print("❌ 日期範圍可能不足以進行可靠的回測分析")
            results['date_range_analysis'] = False
            
    except Exception as e:
        print(f"❌ 日期範圍分析失敗: {e}")
        results['date_range_analysis'] = False
    
    # 測試3：檢查 GUI 界面元素
    print("\n🔍 測試3：檢查 GUI 界面元素")
    try:
        checks = []
        checks.append(('日期範圍標題', '📅 回測日期範圍' in content))
        checks.append(('固定日期標籤', '固定日期範圍:' in content))
        checks.append(('日期範圍樣式', 'date-range-display' in content))
        checks.append(('日期說明文字', '此日期範圍已針對策略驗證進行最佳化' in content))
        
        all_passed = all(check[1] for check in checks)
        if all_passed:
            print("✅ GUI 界面元素正確")
            results['gui_elements'] = True
        else:
            print("❌ GUI 界面元素有問題:")
            for name, passed in checks:
                print(f"  - {name}: {'✅' if passed else '❌'}")
            results['gui_elements'] = False
            
    except Exception as e:
        print(f"❌ GUI 界面元素檢查失敗: {e}")
        results['gui_elements'] = False
    
    # 測試4：檢查 CSS 樣式
    print("\n🔍 測試4：檢查 CSS 樣式")
    try:
        checks = []
        checks.append(('日期顯示樣式', '.date-range-display' in content))
        checks.append(('日期信息樣式', '.date-info' in content))
        checks.append(('背景顏色設定', '#e8f4fd' in content))
        checks.append(('邊框設定', '#bee5eb' in content))
        
        all_passed = all(check[1] for check in checks)
        if all_passed:
            print("✅ CSS 樣式設定正確")
            results['css_styles'] = True
        else:
            print("❌ CSS 樣式設定有問題:")
            for name, passed in checks:
                print(f"  - {name}: {'✅' if passed else '❌'}")
            results['css_styles'] = False
            
    except Exception as e:
        print(f"❌ CSS 樣式檢查失敗: {e}")
        results['css_styles'] = False
    
    # 測試5：檢查日誌輸出
    print("\n🔍 測試5：檢查日誌輸出")
    try:
        checks = []
        checks.append(('日期範圍日誌', '回測日期範圍: 2024-11-04 至 2025-06-28' in content))
        checks.append(('進場方式日誌', '進場方式:' in content))
        checks.append(('時間戳格式', 'datetime.now().strftime' in content))
        
        all_passed = all(check[1] for check in checks)
        if all_passed:
            print("✅ 日誌輸出設定正確")
            results['log_output'] = True
        else:
            print("❌ 日誌輸出設定有問題:")
            for name, passed in checks:
                print(f"  - {name}: {'✅' if passed else '❌'}")
            results['log_output'] = False
            
    except Exception as e:
        print(f"❌ 日誌輸出檢查失敗: {e}")
        results['log_output'] = False
    
    # 總結
    print(f"\n📊 驗證總結:")
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, passed in results.items():
        status = '✅ 通過' if passed else '❌ 失敗'
        print(f"  - {test_name}: {status}")
    
    print(f"\n整體結果: {passed_tests}/{total_tests} 測試通過")
    
    if passed_tests == total_tests:
        print("🎉 日期範圍設定完全正確！")
        print("\n📋 設定詳情:")
        print("  ✅ 回測日期範圍: 2024-11-04 至 2025-06-28")
        print("  ✅ 總計約 236 天 (7.8 個月)")
        print("  ✅ 涵蓋完整交易週期，確保回測可靠性")
        print("  ✅ GUI 界面清楚顯示固定日期範圍")
        print("  ✅ 日誌輸出包含日期範圍信息")
        print("\n🚀 現在 mdd_gui.py 將使用正確的日期範圍進行大量實驗回測！")
    else:
        print("⚠️ 部分設定需要進一步檢查")
    
    print(f"\n結束時間: {datetime.now()}")
    return passed_tests == total_tests

if __name__ == "__main__":
    verify_date_range_settings()
