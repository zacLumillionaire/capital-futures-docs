#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
診斷移動停利問題 - 檢查為什麼移動停利沒有觸發
"""

import sqlite3
import json
from datetime import datetime

def diagnose_trailing_stop_issue():
    """診斷移動停利問題"""
    print("🔍 診斷移動停利問題")
    print("=" * 60)
    
    # 檢查測試機資料庫
    db_path = "test_virtual_strategy.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. 先檢查資料庫結構
        print("\n🔍 檢查資料庫結構:")
        cursor.execute("PRAGMA table_info(position_records)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        print(f"position_records 表的欄位: {column_names}")

        # 檢查策略組表
        cursor.execute("PRAGMA table_info(strategy_groups)")
        strategy_columns = cursor.fetchall()
        strategy_column_names = [col[1] for col in strategy_columns]
        print(f"strategy_groups 表的欄位: {strategy_column_names}")

        # 2. 檢查部位記錄 (使用實際存在的欄位)
        print("\n📊 檢查部位記錄:")

        # 構建動態查詢，只選擇存在的欄位
        base_fields = ['id', 'direction', 'entry_price', 'status', 'entry_time', 'rule_config']
        available_fields = [field for field in base_fields if field in column_names]

        # 添加 group_id 相關欄位
        if 'group_id' in column_names:
            available_fields.append('group_id')
        if 'group_db_id' in column_names:
            available_fields.append('group_db_id')

        query = f"SELECT {', '.join(available_fields)} FROM position_records WHERE status = 'ACTIVE' ORDER BY id DESC LIMIT 5"
        cursor.execute(query)
        
        positions = cursor.fetchall()
        if not positions:
            print("❌ 沒有找到活躍部位")
            return

        # 獲取策略組的區間數據
        cursor.execute("SELECT id, range_high, range_low FROM strategy_groups ORDER BY id DESC LIMIT 10")
        strategy_groups = {row[0]: {'range_high': row[1], 'range_low': row[2]} for row in cursor.fetchall()}

        for pos in positions:
            # 動態解析部位數據
            pos_dict = dict(zip(available_fields, pos))
            pos_id = pos_dict.get('id')
            direction = pos_dict.get('direction')
            entry_price = pos_dict.get('entry_price')
            status = pos_dict.get('status')
            entry_time = pos_dict.get('entry_time')
            rule_config = pos_dict.get('rule_config')
            group_id = pos_dict.get('group_id') or pos_dict.get('group_db_id')

            print(f"\n部位 {pos_id}:")
            print(f"  方向: {direction}")
            print(f"  進場價: {entry_price}")
            print(f"  狀態: {status}")
            print(f"  進場時間: {entry_time}")
            print(f"  組別ID: {group_id}")

            # 從策略組獲取區間數據
            if group_id and group_id in strategy_groups:
                range_high = strategy_groups[group_id]['range_high']
                range_low = strategy_groups[group_id]['range_low']
                print(f"  區間: {range_low} - {range_high}")

            # 解析規則配置
            if rule_config:
                try:
                    rule = json.loads(rule_config)
                    print(f"  規則配置: {rule}")
                except:
                    print(f"  規則配置: {rule_config}")

            # 計算啟動點位
            if entry_price and direction:
                if direction == 'LONG':
                    activation_price = entry_price + 15
                    print(f"  📈 LONG啟動點位: {activation_price}")
                elif direction == 'SHORT':
                    activation_price = entry_price - 15
                    print(f"  📉 SHORT啟動點位: {activation_price}")
        
        # 2. 檢查風險管理狀態
        print("\n🛡️ 檢查風險管理狀態:")
        cursor.execute("""
            SELECT position_id, peak_price, trailing_activated,
                   last_update_time, update_category, update_message
            FROM risk_management_states
            WHERE position_id IN (
                SELECT id FROM position_records WHERE status = 'ACTIVE'
            )
            ORDER BY position_id DESC
        """)
        
        risk_states = cursor.fetchall()
        if risk_states:
            for state in risk_states:
                pos_id, peak_price, trailing_activated, last_update, category, message = state
                print(f"\n風險狀態 - 部位 {pos_id}:")
                print(f"  峰值價格: {peak_price}")
                print(f"  移動停利已啟動: {trailing_activated}")
                print(f"  最後更新: {last_update}")
                print(f"  更新類別: {category}")
                print(f"  更新訊息: {message}")
        else:
            print("❌ 沒有找到風險管理狀態記錄")
        
        # 3. 檢查最近的價格
        print("\n💰 模擬價格檢查:")
        test_prices = [21487.0, 21502.0, 21507.0, 21525.0, 21549.0, 21540.0]

        for pos in positions:
            # 重新解析部位數據
            pos_dict = dict(zip(available_fields, pos))
            pos_id = pos_dict.get('id')
            direction = pos_dict.get('direction')
            entry_price = pos_dict.get('entry_price')

            if entry_price and direction:
                print(f"\n部位 {pos_id} ({direction} @{entry_price}):")

                if direction == 'LONG':
                    activation_price = entry_price + 15
                    for price in test_prices:
                        if price >= activation_price:
                            print(f"  🎯 價格 {price} >= 啟動點 {activation_price} - 應該啟動移動停利!")
                        else:
                            print(f"  ⏳ 價格 {price} < 啟動點 {activation_price} - 尚未達到啟動條件")

                elif direction == 'SHORT':
                    activation_price = entry_price - 15
                    for price in test_prices:
                        if price <= activation_price:
                            print(f"  🎯 價格 {price} <= 啟動點 {activation_price} - 應該啟動移動停利!")
                        else:
                            print(f"  ⏳ 價格 {price} > 啟動點 {activation_price} - 尚未達到啟動條件")
        
        conn.close()
        
        # 4. 檢查可能的問題
        print("\n🚨 可能的問題:")
        print("1. OptimizedRiskManager 的緩存可能被資料庫同步覆蓋")
        print("2. 異步更新延遲導致監控失效")
        print("3. 價格更新沒有正確觸發 _check_activation_trigger")
        print("4. 去重機制可能阻止了觸發")
        
        print("\n🔧 建議解決方案:")
        print("1. 檢查 OptimizedRiskManager 的 activation_cache 和 trailing_cache")
        print("2. 確認 update_price 方法被正確調用")
        print("3. 檢查 _sync_with_database 是否覆蓋了內存數據")
        print("4. 驗證去重機制的參數設置")
        
    except Exception as e:
        print(f"❌ 診斷失敗: {e}")

def check_optimized_risk_manager_state():
    """檢查 OptimizedRiskManager 的內存狀態"""
    print("\n🧠 檢查 OptimizedRiskManager 內存狀態:")
    print("=" * 60)
    
    try:
        # 這需要在實際運行的系統中執行
        print("💡 此檢查需要在運行中的系統中執行")
        print("建議在虛擬測試機中添加以下調試代碼:")
        
        debug_code = '''
# 在 virtual_simple_integrated.py 中添加調試方法
def debug_optimized_risk_manager(self):
    """調試優化風險管理器狀態"""
    if hasattr(self, 'optimized_risk_manager') and self.optimized_risk_manager:
        print("\\n🧠 OptimizedRiskManager 內存狀態:")
        print(f"  position_cache: {self.optimized_risk_manager.position_cache}")
        print(f"  activation_cache: {self.optimized_risk_manager.activation_cache}")
        print(f"  trailing_cache: {self.optimized_risk_manager.trailing_cache}")
        print(f"  stop_loss_cache: {self.optimized_risk_manager.stop_loss_cache}")
        
        # 手動觸發價格更新測試
        test_price = 21507.0
        result = self.optimized_risk_manager.update_price(test_price)
        print(f"  手動價格更新結果: {result}")
'''
        
        print(debug_code)
        
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")

if __name__ == "__main__":
    diagnose_trailing_stop_issue()
    check_optimized_risk_manager_state()
