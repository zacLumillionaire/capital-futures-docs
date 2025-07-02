#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
實單下單問題診斷腳本
分析為什麼策略在實單模式下無法觸發下單
"""

import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def diagnose_strategy_order_manager():
    """診斷策略下單管理器初始化"""
    print("🔍 診斷策略下單管理器...")
    
    try:
        from OrderTester import StrategyOrderManager, TradingMode
        
        # 測試無下單框架的情況
        manager = StrategyOrderManager(None, TradingMode.LIVE)
        print(f"✅ StrategyOrderManager 創建成功")
        print(f"   - future_order_frame: {manager.future_order_frame}")
        print(f"   - order_executor: {manager.order_executor}")
        print(f"   - trading_mode: {manager.trading_mode}")
        
        # 測試建倉下單
        result = manager.place_entry_order('LONG', 23880, 1, 'FOK')
        print(f"   - 建倉測試結果: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ 策略下單管理器診斷失敗: {e}")
        return False

def diagnose_order_executor():
    """診斷OrderExecutor初始化"""
    print("\n🔍 診斷OrderExecutor...")
    
    try:
        from order.future_order import OrderExecutor
        
        # 模擬SKCOM物件
        mock_skcom = {
            'SKOrder': None,
            'SKCenter': None,
            'SKQuote': None
        }
        
        executor = OrderExecutor(mock_skcom)
        print(f"✅ OrderExecutor 創建成功")
        print(f"   - m_pSKOrder: {executor.m_pSKOrder}")
        print(f"   - m_pSKCenter: {executor.m_pSKCenter}")
        print(f"   - strategy_callback: {executor.strategy_callback}")
        
        # 測試策略下單
        result = executor.strategy_order('BUY', 23880, 1, 'FOK', 'MTX00', 0)
        print(f"   - 策略下單測試結果: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ OrderExecutor診斷失敗: {e}")
        return False

def diagnose_api_parameters():
    """診斷API參數設置"""
    print("\n🔍 診斷API參數設置...")
    
    try:
        # 檢查群益官方案例的參數設置
        print("📋 群益官方案例參數:")
        print("   - bstrFullAccount: 完整帳號 (如 F0200006363839)")
        print("   - bstrStockNo: 商品代碼 (如 MTX00)")
        print("   - sBuySell: 買賣別 (0=買進, 1=賣出)")
        print("   - sTradeType: 委託類型 (0=ROD, 1=IOC, 2=FOK)")
        print("   - sDayTrade: 當沖與否 (0=非當沖, 1=當沖)")
        print("   - bstrPrice: 委託價格 (字串格式)")
        print("   - nQty: 委託數量 (整數)")
        print("   - sNewClose: 倉別 (0=新倉, 1=平倉, 2=自動)")
        print("   - sReserved: 盤別 (0=盤中, 1=T盤預約)")
        
        # 檢查我們的參數設置
        print("\n📋 我們的參數設置:")
        order_params = {
            'account': 'F0200006363839',
            'product': 'MTX00',
            'direction': 'BUY',
            'price': 23880,
            'quantity': 1,
            'order_type': 'FOK',
            'day_trade': 1,
            'new_close': 0,
            'reserved': 0
        }
        
        for key, value in order_params.items():
            print(f"   - {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ API參數診斷失敗: {e}")
        return False

def diagnose_strategy_trigger():
    """診斷策略觸發流程"""
    print("\n🔍 診斷策略觸發流程...")
    
    try:
        print("📋 策略觸發檢查點:")
        print("1. 策略監控是否啟動？")
        print("2. 交易模式是否設為實單？")
        print("3. 突破信號是否正確檢測？")
        print("4. execute_entry_on_next_tick 是否被調用？")
        print("5. enter_position 是否被調用？")
        print("6. strategy_order_manager.place_entry_order 是否被調用？")
        print("7. OrderExecutor.strategy_order 是否被調用？")
        print("8. SendFutureOrderCLR API 是否被調用？")
        
        print("\n💡 建議檢查步驟:")
        print("1. 在策略LOG中查找 '🎯 執行進場!' 訊息")
        print("2. 在策略LOG中查找 '實單建倉:' 訊息")
        print("3. 在策略LOG中查找 '【策略下單】' 訊息")
        print("4. 在策略LOG中查找 '【API】準備調用SendFutureOrderCLR' 訊息")
        
        return True
        
    except Exception as e:
        print(f"❌ 策略觸發診斷失敗: {e}")
        return False

def diagnose_common_issues():
    """診斷常見問題"""
    print("\n🔍 診斷常見問題...")
    
    print("📋 可能的問題原因:")
    print("1. 策略下單管理器未正確初始化")
    print("   - future_order_frame 為 None")
    print("   - order_executor 為 None")
    
    print("2. 交易模式未正確切換")
    print("   - trading_mode 仍為 SIMULATION")
    print("   - 模式切換確認對話框被取消")
    
    print("3. API物件未正確初始化")
    print("   - m_pSKOrder 為 None")
    print("   - SKOrderLib 未初始化")
    print("   - 憑證未讀取")
    
    print("4. 策略觸發條件未滿足")
    print("   - 進場頻率限制")
    print("   - 突破信號未正確檢測")
    print("   - 等待進場狀態異常")
    
    print("5. 下單參數錯誤")
    print("   - 帳號格式錯誤")
    print("   - 商品代碼錯誤")
    print("   - 價格格式錯誤")
    
    return True

def main():
    """主診斷流程"""
    print("🚀 開始實單下單問題診斷...")
    print("=" * 50)
    
    # 執行各項診斷
    results = []
    results.append(diagnose_strategy_order_manager())
    results.append(diagnose_order_executor())
    results.append(diagnose_api_parameters())
    results.append(diagnose_strategy_trigger())
    results.append(diagnose_common_issues())
    
    print("\n" + "=" * 50)
    print("📊 診斷結果總結:")
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"✅ 成功診斷: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 所有診斷項目都通過，問題可能在於:")
        print("   1. 實際運行時的環境差異")
        print("   2. 策略觸發時機問題")
        print("   3. LOG輸出被過濾或遺漏")
    else:
        print("⚠️ 發現問題，請檢查失敗的診斷項目")
    
    print("\n💡 下一步建議:")
    print("1. 在OrderTester.py中添加更詳細的DEBUG LOG")
    print("2. 檢查策略面板的交易模式顯示")
    print("3. 手動測試OrderExecutor.strategy_order方法")
    print("4. 對比模擬模式和實單模式的執行差異")

if __name__ == "__main__":
    main()
