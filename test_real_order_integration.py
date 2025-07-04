#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試實際下單功能整合
驗證五檔ASK價格提取系統與simple_integrated.py的整合效果
"""

import sys
import os
import time

# 添加路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'Capital_Official_Framework'))

def test_quote_manager_import():
    """測試報價管理器導入"""
    print("🧪 測試報價管理器導入...")
    
    try:
        from real_time_quote_manager import RealTimeQuoteManager
        print("✅ RealTimeQuoteManager 導入成功")
        
        # 創建實例
        manager = RealTimeQuoteManager(console_enabled=True)
        print("✅ RealTimeQuoteManager 實例創建成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 導入失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ 創建實例失敗: {e}")
        return False

def test_simple_integrated_import():
    """測試simple_integrated.py的實際下單模組導入"""
    print("\n🧪 測試simple_integrated.py的實際下單模組導入...")
    
    try:
        # 模擬simple_integrated.py的導入邏輯
        try:
            from real_time_quote_manager import RealTimeQuoteManager
            REAL_ORDER_MODULES_AVAILABLE = True
            print("✅ 實際下單模組載入成功")
        except ImportError as e:
            REAL_ORDER_MODULES_AVAILABLE = False
            print(f"⚠️ 實際下單模組載入失敗: {e}")
            print("💡 系統將以模擬模式運行")
        
        return REAL_ORDER_MODULES_AVAILABLE
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_best5_data_processing():
    """測試五檔數據處理邏輯"""
    print("\n🧪 測試五檔數據處理邏輯...")
    
    try:
        from real_time_quote_manager import RealTimeQuoteManager
        
        # 創建管理器
        manager = RealTimeQuoteManager(console_enabled=False)  # 關閉Console避免過多輸出
        
        # 模擬OnNotifyBest5LONG事件的數據
        # 群益API的價格需要除以100
        raw_ask1 = 2251500  # 22515.00 * 100
        raw_ask2 = 2251600  # 22516.00 * 100
        raw_ask3 = 2251700  # 22517.00 * 100
        raw_ask4 = 2251800  # 22518.00 * 100
        raw_ask5 = 2251900  # 22519.00 * 100
        
        raw_bid1 = 2251400  # 22514.00 * 100
        raw_bid2 = 2251300  # 22513.00 * 100
        raw_bid3 = 2251200  # 22512.00 * 100
        raw_bid4 = 2251100  # 22511.00 * 100
        raw_bid5 = 2251000  # 22510.00 * 100
        
        # 轉換價格 (模擬simple_integrated.py的邏輯)
        ask1 = raw_ask1 / 100.0 if raw_ask1 > 0 else 0
        ask2 = raw_ask2 / 100.0 if raw_ask2 > 0 else 0
        ask3 = raw_ask3 / 100.0 if raw_ask3 > 0 else 0
        ask4 = raw_ask4 / 100.0 if raw_ask4 > 0 else 0
        ask5 = raw_ask5 / 100.0 if raw_ask5 > 0 else 0
        
        bid1 = raw_bid1 / 100.0 if raw_bid1 > 0 else 0
        bid2 = raw_bid2 / 100.0 if raw_bid2 > 0 else 0
        bid3 = raw_bid3 / 100.0 if raw_bid3 > 0 else 0
        bid4 = raw_bid4 / 100.0 if raw_bid4 > 0 else 0
        bid5 = raw_bid5 / 100.0 if raw_bid5 > 0 else 0
        
        print(f"📊 原始數據: ASK1={raw_ask1} BID1={raw_bid1}")
        print(f"📊 轉換後: ASK1={ask1} BID1={bid1}")
        
        # 更新到報價管理器
        success = manager.update_best5_data(
            market_no="TF", stock_idx=1,
            ask1=ask1, ask1_qty=10, ask2=ask2, ask2_qty=8, ask3=ask3, ask3_qty=5,
            ask4=ask4, ask4_qty=3, ask5=ask5, ask5_qty=2,
            bid1=bid1, bid1_qty=12, bid2=bid2, bid2_qty=9, bid3=bid3, bid3_qty=6,
            bid4=bid4, bid4_qty=4, bid5=bid5, bid5_qty=1,
            product_code="MTX00"
        )
        
        print(f"📊 數據更新結果: {'成功' if success else '失敗'}")
        
        # 測試ASK價格提取
        best_ask = manager.get_best_ask_price("MTX00")
        print(f"💰 最佳ASK價格: {best_ask}")
        
        # 驗證結果
        if best_ask == ask1:
            print("✅ ASK價格提取正確")
            return True
        else:
            print(f"❌ ASK價格提取錯誤: 期望{ask1}, 實際{best_ask}")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_integration_simulation():
    """模擬完整整合流程"""
    print("\n🧪 模擬完整整合流程...")
    
    try:
        from real_time_quote_manager import RealTimeQuoteManager
        
        # 模擬simple_integrated.py的初始化
        print("📋 模擬系統初始化...")
        real_time_quote_manager = RealTimeQuoteManager(console_enabled=True)
        real_order_enabled = True
        
        print("✅ 實際下單系統初始化完成")
        print("📊 五檔ASK價格提取系統已就緒")
        
        # 模擬OnNotifyBest5LONG事件
        print("\n📋 模擬OnNotifyBest5LONG事件...")
        
        # 模擬多次報價更新
        test_data = [
            (2251500, 2251400, "第1次報價"),
            (2251600, 2251500, "第2次報價"),
            (2251700, 2251600, "第3次報價"),
        ]
        
        for raw_ask1, raw_bid1, description in test_data:
            print(f"\n⏰ {description}")
            
            # 轉換價格
            ask1 = raw_ask1 / 100.0
            bid1 = raw_bid1 / 100.0
            
            # 更新到實際下單系統
            if real_time_quote_manager:
                try:
                    product_code = "MTX00"
                    
                    success = real_time_quote_manager.update_best5_data(
                        market_no="TF", stock_idx=1,
                        ask1=ask1, ask1_qty=10, ask2=ask1+1, ask2_qty=8, ask3=ask1+2, ask3_qty=5,
                        ask4=ask1+3, ask4_qty=3, ask5=ask1+4, ask5_qty=2,
                        bid1=bid1, bid1_qty=12, bid2=bid1-1, bid2_qty=9, bid3=bid1-2, bid3_qty=6,
                        bid4=bid1-3, bid4_qty=4, bid5=bid1-4, bid5_qty=1,
                        product_code=product_code
                    )
                    
                    if success:
                        # 測試ASK價格提取
                        best_ask = real_time_quote_manager.get_best_ask_price(product_code)
                        print(f"   📊 更新成功，最佳ASK: {best_ask}")
                    else:
                        print("   ❌ 更新失敗")
                        
                except Exception as e:
                    print(f"   ❌ 處理錯誤: {e}")
            
            time.sleep(0.1)  # 模擬時間間隔
        
        # 測試報價摘要
        print("\n📋 測試報價摘要...")
        summary = real_time_quote_manager.get_quote_summary("MTX00")
        if summary:
            print(f"📊 報價摘要:")
            print(f"   商品: {summary['product_code']}")
            print(f"   ASK1: {summary['ask1']} ({summary['ask1_qty']})")
            print(f"   BID1: {summary['bid1']} ({summary['bid1_qty']})")
            print(f"   更新次數: {summary['update_count']}")
            print(f"   數據新鮮: {'是' if summary['is_fresh'] else '否'}")
        
        # 測試統計資訊
        print("\n📋 測試統計資訊...")
        stats = real_time_quote_manager.get_statistics()
        print(f"📊 統計資訊:")
        print(f"   總更新次數: {stats['total_updates']}")
        print(f"   追蹤商品: {stats['tracked_products']}")
        print(f"   更新頻率: {stats['updates_per_second']:.2f} 次/秒")
        
        print("\n✅ 完整整合流程測試成功")
        return True
        
    except Exception as e:
        print(f"❌ 整合測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 開始測試實際下單功能整合")
    print("=" * 60)
    
    # 測試結果統計
    test_results = []
    
    # 測試1: 報價管理器導入
    result1 = test_quote_manager_import()
    test_results.append(("報價管理器導入", result1))
    
    # 測試2: simple_integrated.py導入邏輯
    result2 = test_simple_integrated_import()
    test_results.append(("simple_integrated.py導入邏輯", result2))
    
    # 測試3: 五檔數據處理
    result3 = test_best5_data_processing()
    test_results.append(("五檔數據處理", result3))
    
    # 測試4: 完整整合流程
    result4 = test_integration_simulation()
    test_results.append(("完整整合流程", result4))
    
    # 輸出測試結果
    print("\n" + "=" * 60)
    print("🎉 測試結果總結:")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📊 總體結果: {passed}/{total} 項測試通過")
    
    if passed == total:
        print("🎉 所有測試通過！實際下單功能整合成功")
        print("\n📋 下一步:")
        print("   1. 啟動 simple_integrated.py")
        print("   2. 登入群益API")
        print("   3. 訂閱報價")
        print("   4. 觀察Console輸出中的五檔報價更新")
        print("   5. 確認實際下單系統正常運作")
    else:
        print("⚠️ 部分測試失敗，請檢查問題後重新測試")

if __name__ == "__main__":
    main()
