#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復移動停利狀態同步問題
解決 position_records 和 risk_management_states 表狀態不一致的問題
"""

import sqlite3
from datetime import datetime

def check_state_sync():
    """檢查狀態同步情況"""
    print("🔍 檢查移動停利狀態同步...")
    
    with sqlite3.connect("multi_group_strategy.db") as conn:
        cursor = conn.cursor()
        
        # 檢查兩個表的狀態
        cursor.execute("""
            SELECT pr.id, pr.trailing_activated as pr_activated, pr.peak_price as pr_peak,
                   rms.trailing_activated as rms_activated, rms.peak_price as rms_peak
            FROM position_records pr
            LEFT JOIN risk_management_states rms ON pr.id = rms.position_id
            WHERE pr.status = 'ACTIVE'
            ORDER BY pr.id
        """)
        
        positions = cursor.fetchall()
        
        print(f"檢查 {len(positions)} 個活躍部位的狀態同步:")
        
        sync_issues = []
        for pos_id, pr_activated, pr_peak, rms_activated, rms_peak in positions:
            print(f"\n📊 部位 {pos_id}:")
            print(f"   position_records: 啟動={pr_activated}, 峰值={pr_peak}")
            print(f"   risk_management_states: 啟動={rms_activated}, 峰值={rms_peak}")
            
            # 檢查狀態不一致
            if pr_activated != rms_activated:
                sync_issues.append({
                    'position_id': pos_id,
                    'issue': 'trailing_activated不一致',
                    'pr_value': pr_activated,
                    'rms_value': rms_activated
                })
                print(f"   ❌ trailing_activated 不一致: PR={pr_activated}, RMS={rms_activated}")
            
            # 檢查峰值不一致
            if pr_peak != rms_peak:
                sync_issues.append({
                    'position_id': pos_id,
                    'issue': 'peak_price不一致',
                    'pr_value': pr_peak,
                    'rms_value': rms_peak
                })
                print(f"   ❌ peak_price 不一致: PR={pr_peak}, RMS={rms_peak}")
            
            if pr_activated == rms_activated and pr_peak == rms_peak:
                print(f"   ✅ 狀態同步正常")
        
        return sync_issues

def fix_state_sync(sync_issues):
    """修復狀態同步問題"""
    if not sync_issues:
        print("\n✅ 所有狀態都同步，無需修復")
        return
    
    print(f"\n🔧 修復 {len(sync_issues)} 個狀態同步問題...")
    
    with sqlite3.connect("multi_group_strategy.db") as conn:
        cursor = conn.cursor()
        
        # 以 risk_management_states 為準（因為它是實際的風險管理狀態）
        for issue in sync_issues:
            pos_id = issue['position_id']
            
            # 獲取 risk_management_states 的最新狀態
            cursor.execute("""
                SELECT trailing_activated, peak_price, last_update_time
                FROM risk_management_states
                WHERE position_id = ?
            """, (pos_id,))
            
            rms_data = cursor.fetchone()
            if rms_data:
                rms_activated, rms_peak, last_update = rms_data
                
                # 更新 position_records 以匹配 risk_management_states
                cursor.execute("""
                    UPDATE position_records
                    SET trailing_activated = ?,
                        peak_price = ?,
                        last_price_update_time = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (rms_activated, rms_peak, last_update, pos_id))
                
                print(f"   ✅ 部位 {pos_id}: 同步為 啟動={rms_activated}, 峰值={rms_peak}")
        
        conn.commit()
        print(f"🎉 狀態同步修復完成!")

def verify_trailing_stop_logic():
    """驗證移動停利邏輯"""
    print("\n🧪 驗證移動停利邏輯...")
    
    with sqlite3.connect("multi_group_strategy.db") as conn:
        cursor = conn.cursor()
        
        # 獲取已啟動移動停利的部位
        cursor.execute("""
            SELECT pr.id, pr.lot_id, pr.direction, pr.entry_price, 
                   pr.trailing_activation_points, pr.trailing_pullback_ratio,
                   rms.peak_price, rms.trailing_activated
            FROM position_records pr
            JOIN risk_management_states rms ON pr.id = rms.position_id
            WHERE pr.status = 'ACTIVE' AND rms.trailing_activated = 1
            ORDER BY pr.id
        """)
        
        activated_positions = cursor.fetchall()
        
        print(f"檢查 {len(activated_positions)} 個已啟動移動停利的部位:")
        
        # 模擬當前價格進行平倉條件檢查
        current_price = 22513  # 從日誌中看到的最新價格
        
        for pos_data in activated_positions:
            pos_id, lot_id, direction, entry_price, activation_points, pullback_ratio, peak_price, trailing_activated = pos_data
            
            print(f"\n📊 部位 {pos_id} (第{lot_id}口, {direction}):")
            print(f"   進場價格: {entry_price}")
            print(f"   峰值價格: {peak_price}")
            print(f"   當前價格: {current_price}")
            print(f"   回撤比例: {pullback_ratio}")
            
            # 計算移動停利價格
            if direction == 'SHORT':
                # SHORT部位：移停價格 = 峰值價格 + (峰值價格 - 進場價格) * 回撤比例
                profit_points = entry_price - peak_price
                pullback_points = profit_points * pullback_ratio
                trailing_stop_price = peak_price + pullback_points
                
                print(f"   獲利點數: {profit_points}")
                print(f"   回撤點數: {pullback_points}")
                print(f"   移停價格: {trailing_stop_price}")
                
                # 檢查是否應該平倉
                should_exit = current_price >= trailing_stop_price
                print(f"   應該平倉: {'✅ 是' if should_exit else '❌ 否'} ({current_price} >= {trailing_stop_price})")
                
                if should_exit:
                    print(f"   🎯 觸發平倉條件！")
            
            elif direction == 'LONG':
                # LONG部位：移停價格 = 峰值價格 - (峰值價格 - 進場價格) * 回撤比例
                profit_points = peak_price - entry_price
                pullback_points = profit_points * pullback_ratio
                trailing_stop_price = peak_price - pullback_points
                
                print(f"   獲利點數: {profit_points}")
                print(f"   回撤點數: {pullback_points}")
                print(f"   移停價格: {trailing_stop_price}")
                
                # 檢查是否應該平倉
                should_exit = current_price <= trailing_stop_price
                print(f"   應該平倉: {'✅ 是' if should_exit else '❌ 否'} ({current_price} <= {trailing_stop_price})")
                
                if should_exit:
                    print(f"   🎯 觸發平倉條件！")

def check_exit_mechanism():
    """檢查平倉機制"""
    print("\n🔍 檢查平倉機制...")
    
    # 檢查是否有平倉記錄
    with sqlite3.connect("multi_group_strategy.db") as conn:
        cursor = conn.cursor()
        
        # 檢查最近的平倉記錄
        cursor.execute("""
            SELECT id, exit_reason, exit_price, exit_time, pnl
            FROM position_records
            WHERE exit_reason IS NOT NULL
            ORDER BY exit_time DESC
            LIMIT 5
        """)
        
        exit_records = cursor.fetchall()
        
        print(f"最近的平倉記錄: {len(exit_records)} 筆")
        for record in exit_records:
            pos_id, exit_reason, exit_price, exit_time, pnl = record
            print(f"   部位 {pos_id}: {exit_reason} @{exit_price} 損益:{pnl} 時間:{exit_time}")
        
        # 檢查移動停利平倉記錄
        cursor.execute("""
            SELECT COUNT(*) FROM position_records
            WHERE exit_reason = '移動停利'
        """)
        
        trailing_exits = cursor.fetchone()[0]
        print(f"\n移動停利平倉記錄: {trailing_exits} 筆")
        
        if trailing_exits == 0:
            print("❌ 沒有移動停利平倉記錄，平倉機制可能有問題")
        else:
            print("✅ 有移動停利平倉記錄")

def generate_fix_summary():
    """生成修復總結"""
    print("\n📋 移動停利狀態同步修復總結")
    print("=" * 50)
    
    print("🔍 發現的問題:")
    print("   1. position_records 和 risk_management_states 狀態不同步")
    print("   2. 移動停利啟動了但 position_records 表未更新")
    print("   3. 風險引擎計數器顯示錯誤")
    
    print("\n🔧 執行的修復:")
    print("   1. 檢查並修復狀態同步問題")
    print("   2. 以 risk_management_states 為準同步狀態")
    print("   3. 驗證移動停利邏輯和平倉條件")
    
    print("\n📝 建議後續行動:")
    print("   1. 重啟交易系統或重新載入風險管理模組")
    print("   2. 觀察移動停利計數器是否正確顯示")
    print("   3. 監控平倉機制是否正常執行")
    print("   4. 檢查平倉執行器的連接和配置")

def main():
    """主修復函數"""
    print("🚀 修復移動停利狀態同步問題")
    print("=" * 50)
    
    # 1. 檢查狀態同步
    sync_issues = check_state_sync()
    
    # 2. 修復狀態同步
    fix_state_sync(sync_issues)
    
    # 3. 驗證移動停利邏輯
    verify_trailing_stop_logic()
    
    # 4. 檢查平倉機制
    check_exit_mechanism()
    
    # 5. 生成修復總結
    generate_fix_summary()

if __name__ == "__main__":
    main()
