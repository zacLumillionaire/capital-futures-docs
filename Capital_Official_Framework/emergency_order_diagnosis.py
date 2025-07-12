# -*- coding: utf-8 -*-
"""
緊急下單問題診斷工具
用於分析"3口買單變成2口賣單"的問題
"""

import sys
import os
import sqlite3
from datetime import datetime, date

def diagnose_order_direction_issue():
    """診斷下單方向問題"""
    print("🔍 緊急下單問題診斷")
    print("=" * 50)
    
    try:
        # 1. 檢查資料庫中的訂單記錄
        print("\n📋 1. 檢查資料庫訂單記錄")
        print("-" * 30)
        
        db_path = "multi_group_strategy.db"
        if not os.path.exists(db_path):
            print(f"❌ 資料庫檔案不存在: {db_path}")
            return False
            
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 查詢今天的策略組
        today = date.today().isoformat()
        cursor.execute("""
            SELECT * FROM strategy_groups 
            WHERE date = ? 
            ORDER BY created_at DESC
        """, (today,))
        
        groups = cursor.fetchall()
        print(f"📊 今天的策略組數量: {len(groups)}")
        
        for group in groups:
            print(f"  組{group['group_id']}: {group['direction']} 狀態:{group['status']}")
            
            # 查詢該組的部位記錄
            cursor.execute("""
                SELECT * FROM position_records 
                WHERE group_id = ? 
                ORDER BY created_at
            """, (group['id'],))
            
            positions = cursor.fetchall()
            print(f"    部位數量: {len(positions)}")
            
            for pos in positions:
                print(f"      部位{pos['id']}: {pos['direction']} @{pos['entry_price']} 狀態:{pos['status']} 訂單狀態:{pos['order_status']}")
        
        # 2. 檢查方向轉換邏輯
        print("\n🔄 2. 測試方向轉換邏輯")
        print("-" * 30)
        
        test_directions = ["LONG", "SHORT", "BUY", "SELL"]
        
        for direction in test_directions:
            # 測試API到策略方向轉換
            if direction in ["BUY", "SELL"]:
                strategy_direction = "LONG" if direction == "BUY" else "SHORT"
                print(f"  API方向 {direction} → 策略方向 {strategy_direction}")
            
            # 測試平倉方向轉換
            if direction in ["LONG", "SHORT"]:
                exit_direction = "SELL" if direction == "LONG" else "BUY"
                print(f"  部位方向 {direction} → 平倉方向 {exit_direction}")
        
        # 3. 檢查追價邏輯
        print("\n🔄 3. 測試追價邏輯")
        print("-" * 30)
        
        # 模擬市價
        current_ask1 = 22440
        current_bid1 = 22439
        
        for direction in ["LONG", "SHORT"]:
            for retry_count in range(1, 4):
                if direction == "LONG":
                    retry_price = current_ask1 + retry_count
                    print(f"  {direction} 第{retry_count}次追價: ASK1({current_ask1}) + {retry_count} = {retry_price}")
                else:
                    retry_price = current_bid1 - retry_count
                    print(f"  {direction} 第{retry_count}次追價: BID1({current_bid1}) - {retry_count} = {retry_price}")
        
        # 4. 檢查平倉追價邏輯
        print("\n🔄 4. 測試平倉追價邏輯")
        print("-" * 30)
        
        for original_direction in ["LONG", "SHORT"]:
            for retry_count in range(1, 4):
                if original_direction == "LONG":
                    # 多單平倉 = 賣出，使用BID1-retry_count
                    exit_direction = "SELL"
                    retry_price = current_bid1 - retry_count
                    print(f"  {original_direction}部位平倉({exit_direction}) 第{retry_count}次追價: BID1({current_bid1}) - {retry_count} = {retry_price}")
                else:
                    # 空單平倉 = 買進，使用ASK1+retry_count
                    exit_direction = "BUY"
                    retry_price = current_ask1 + retry_count
                    print(f"  {original_direction}部位平倉({exit_direction}) 第{retry_count}次追價: ASK1({current_ask1}) + {retry_count} = {retry_price}")
        
        conn.close()
        
        # 5. 提供診斷建議
        print("\n💡 5. 診斷建議")
        print("-" * 30)
        
        print("🔍 可能的問題原因:")
        print("  1. 平倉訂單被誤認為新倉建倉")
        print("  2. 簡化追蹤器的方向匹配邏輯錯誤")
        print("  3. 追價機制使用了錯誤的方向")
        print("  4. FIFO匹配時方向轉換出錯")
        
        print("\n🔧 建議檢查:")
        print("  1. 檢查期貨商LOG中的實際下單方向")
        print("  2. 確認new_close參數是否正確設置")
        print("  3. 檢查簡化追蹤器的回報處理邏輯")
        print("  4. 驗證追價機制的方向計算")
        
        print("\n📋 下次交易時請觀察:")
        print("  1. [ORDER_MGR] 下單LOG中的方向")
        print("  2. [SIMPLIFIED_TRACKER] 回報處理LOG")
        print("  3. [追價] 相關的LOG訊息")
        print("  4. 期貨商系統中的實際委託記錄")
        
        return True
        
    except Exception as e:
        print(f"❌ 診斷失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_database_constraints():
    """檢查資料庫約束問題"""
    print("\n🔍 檢查資料庫約束")
    print("-" * 30)
    
    try:
        db_path = "multi_group_strategy.db"
        if not os.path.exists(db_path):
            print(f"❌ 資料庫檔案不存在: {db_path}")
            return False
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 檢查風險管理狀態表的約束
        cursor.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='risk_management_states'
        """)
        
        result = cursor.fetchone()
        if result:
            table_sql = result[0]
            print("📋 風險管理狀態表約束:")
            
            if "CHECK(update_reason IN" in table_sql:
                # 提取約束內容
                start = table_sql.find("CHECK(update_reason IN")
                end = table_sql.find(")", start) + 1
                constraint = table_sql[start:end]
                print(f"  {constraint}")
                
                # 檢查支援的值
                if "成交初始化" in constraint:
                    print("  ✅ 支援 '成交初始化'")
                else:
                    print("  ❌ 不支援 '成交初始化'")
                    
                if "簡化追蹤成交確認" in constraint:
                    print("  ✅ 支援 '簡化追蹤成交確認'")
                else:
                    print("  ❌ 不支援 '簡化追蹤成交確認'")
            else:
                print("  ⚠️ 未找到 update_reason 約束")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 檢查約束失敗: {e}")
        return False

if __name__ == "__main__":
    print("🚨 緊急下單問題診斷工具")
    print("用於分析'3口買單變成2口賣單'的問題")
    print("=" * 60)
    
    # 執行診斷
    success1 = diagnose_order_direction_issue()
    success2 = check_database_constraints()
    
    if success1 and success2:
        print("\n✅ 診斷完成")
        print("\n📋 下一步建議:")
        print("1. 運行此診斷工具查看結果")
        print("2. 在下次交易時密切觀察LOG")
        print("3. 對比期貨商系統的實際委託記錄")
        print("4. 如果問題持續，可以暫時禁用追價機制")
    else:
        print("\n❌ 診斷過程中出現錯誤")
