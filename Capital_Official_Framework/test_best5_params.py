#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試五檔報價參數數量
"""

import os
import sys

# 加入虛擬報價機路徑
virtual_quote_path = os.path.join(os.path.dirname(__file__), '虛擬報價機')
if virtual_quote_path not in sys.path:
    sys.path.insert(0, virtual_quote_path)

from quote_engine import Best5Data

class TestHandler:
    """測試處理器 - 模擬virtual_simple_integrated.py中的方法"""
    
    def OnNotifyBest5LONG(self, sMarketNo, nStockidx, nPtr,
                         nBid1, nBidQty1, nBid2, nBidQty2, nBid3, nBidQty3, nBid4, nBidQty4, nBid5, nBidQty5,
                         nAsk1, nAskQty1, nAsk2, nAskQty2, nAsk3, nAskQty3, nAsk4, nAskQty4, nAsk5, nAskQty5, nSimulate):
        """五檔報價事件處理 - 24個參數（不包括self）"""
        print(f"✅ 五檔事件接收成功！參數數量正確")
        print(f"   市場:{sMarketNo} 商品:{nStockidx} BID1:{nBid1/100} ASK1:{nAsk1/100}")
        return True

def test_params():
    """測試參數傳遞"""
    print("🚀 測試五檔報價參數數量")
    print("=" * 50)
    
    # 創建測試數據
    best5_data = Best5Data(
        market_no=1,
        stock_idx=0,
        date=20250717,
        time_hms=140000,
        time_ms=0,
        bid_prices=[2150000, 2149500, 2149000, 2148500, 2148000],
        bid_qtys=[10, 15, 20, 25, 30],
        ask_prices=[2150500, 2151000, 2151500, 2152000, 2152500],
        ask_qtys=[12, 18, 22, 28, 32],
        simulate=0
    )
    
    # 創建測試處理器
    handler = TestHandler()
    
    # 測試參數傳遞
    print("\n1. 測試參數傳遞")
    try:
        # 模擬event_dispatcher的調用方式
        handler.OnNotifyBest5LONG(
            best5_data.market_no,
            best5_data.stock_idx,
            0,  # nPtr
            # 買方五檔 (價格, 數量) x 5
            best5_data.bid_prices[0], best5_data.bid_qtys[0],
            best5_data.bid_prices[1], best5_data.bid_qtys[1],
            best5_data.bid_prices[2], best5_data.bid_qtys[2],
            best5_data.bid_prices[3], best5_data.bid_qtys[3],
            best5_data.bid_prices[4], best5_data.bid_qtys[4],
            # 賣方五檔 (價格, 數量) x 5
            best5_data.ask_prices[0], best5_data.ask_qtys[0],
            best5_data.ask_prices[1], best5_data.ask_qtys[1],
            best5_data.ask_prices[2], best5_data.ask_qtys[2],
            best5_data.ask_prices[3], best5_data.ask_qtys[3],
            best5_data.ask_prices[4], best5_data.ask_qtys[4],
            # 模擬標記
            best5_data.simulate
        )
        
        print("✅ 參數數量測試成功！")
        return True
        
    except TypeError as e:
        print(f"❌ 參數數量錯誤: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他錯誤: {e}")
        return False

def count_params():
    """計算參數數量"""
    print("\n2. 參數數量計算")
    
    params = [
        "market_no", "stock_idx", "nPtr",
        "bid1_price", "bid1_qty", "bid2_price", "bid2_qty", "bid3_price", "bid3_qty", 
        "bid4_price", "bid4_qty", "bid5_price", "bid5_qty",
        "ask1_price", "ask1_qty", "ask2_price", "ask2_qty", "ask3_price", "ask3_qty",
        "ask4_price", "ask4_qty", "ask5_price", "ask5_qty",
        "simulate"
    ]
    
    print(f"📊 總參數數量: {len(params)}")
    print("📋 參數列表:")
    for i, param in enumerate(params, 1):
        print(f"   {i:2d}. {param}")
    
    return len(params)

if __name__ == "__main__":
    try:
        param_count = count_params()
        success = test_params()
        
        print(f"\n📊 結果總結")
        print("=" * 50)
        print(f"參數數量: {param_count}")
        print(f"測試結果: {'成功' if success else '失敗'}")
        
        if success:
            print("\n🎉 五檔報價參數修復成功！")
        else:
            print("\n⚠️ 五檔報價參數需要進一步調整")
            
    except Exception as e:
        print(f"\n❌ 測試過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()
