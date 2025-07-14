#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復現有部位移動停利參數
解決移動停利啟動條件檢查失敗的問題
"""

import sqlite3
from datetime import datetime

def check_current_positions():
    """檢查當前部位狀態"""
    print("🔍 檢查當前部位狀態...")
    
    with sqlite3.connect("multi_group_strategy.db") as conn:
        cursor = conn.cursor()
        
        # 檢查活躍部位
        cursor.execute("""
            SELECT id, group_id, lot_id, direction, entry_price, 
                   trailing_activation_points, trailing_pullback_ratio, 
                   trailing_activated, status
            FROM position_records 
            WHERE status = 'ACTIVE'
            ORDER BY id
        """)
        
        positions = cursor.fetchall()
        
        print(f"找到 {len(positions)} 個活躍部位:")
        
        need_fix = []
        for pos in positions:
            pos_id, group_id, lot_id, direction, entry_price, \
            activation_points, pullback_ratio, trailing_activated, status = pos
            
            print(f"\n📊 部位 {pos_id} (組{group_id}, 第{lot_id}口, {direction}):")
            print(f"   進場價格: {entry_price}")
            print(f"   啟動點數: {activation_points}")
            print(f"   回撤比例: {pullback_ratio}")
            print(f"   已啟動: {trailing_activated}")
            print(f"   狀態: {status}")
            
            if activation_points is None:
                need_fix.append((pos_id, lot_id))
                print(f"   ❌ 需要修復: 啟動點數為 None")
            else:
                print(f"   ✅ 參數正常")
        
        return need_fix

def fix_trailing_stop_parameters(positions_to_fix):
    """修復移動停利參數"""
    if not positions_to_fix:
        print("\n✅ 所有部位參數都正常，無需修復")
        return
    
    print(f"\n🔧 開始修復 {len(positions_to_fix)} 個部位的移動停利參數...")
    
    with sqlite3.connect("multi_group_strategy.db") as conn:
        cursor = conn.cursor()
        
        fixed_count = 0
        
        for pos_id, lot_id in positions_to_fix:
            # 根據口數設置移動停利參數
            if lot_id == 1:
                activation_points = 15.0
                pullback_ratio = 0.2
                description = "第1口: 15點啟動, 20%回撤"
            elif lot_id == 2:
                activation_points = 40.0
                pullback_ratio = 0.2
                description = "第2口: 40點啟動, 20%回撤"
            elif lot_id == 3:
                activation_points = 65.0
                pullback_ratio = 0.2
                description = "第3口: 65點啟動, 20%回撤"
            else:
                activation_points = 15.0
                pullback_ratio = 0.2
                description = f"第{lot_id}口: 預設15點啟動, 20%回撤"
            
            try:
                cursor.execute("""
                    UPDATE position_records 
                    SET trailing_activation_points = ?, 
                        trailing_pullback_ratio = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (activation_points, pullback_ratio, pos_id))
                
                print(f"   ✅ 部位 {pos_id}: {description}")
                fixed_count += 1
                
            except Exception as e:
                print(f"   ❌ 部位 {pos_id} 修復失敗: {e}")
        
        conn.commit()
        print(f"\n🎉 修復完成! 成功修復 {fixed_count} 個部位")

def verify_fix():
    """驗證修復結果"""
    print("\n🔍 驗證修復結果...")
    
    with sqlite3.connect("multi_group_strategy.db") as conn:
        cursor = conn.cursor()
        
        # 檢查修復後的狀態
        cursor.execute("""
            SELECT id, lot_id, trailing_activation_points, trailing_pullback_ratio
            FROM position_records 
            WHERE status = 'ACTIVE'
            ORDER BY id
        """)
        
        positions = cursor.fetchall()
        
        all_fixed = True
        for pos_id, lot_id, activation_points, pullback_ratio in positions:
            if activation_points is None:
                print(f"   ❌ 部位 {pos_id}: 仍然缺少啟動點數")
                all_fixed = False
            else:
                print(f"   ✅ 部位 {pos_id} (第{lot_id}口): {activation_points}點啟動, {pullback_ratio}回撤")
        
        if all_fixed:
            print(f"\n🎉 所有部位參數修復成功!")
        else:
            print(f"\n⚠️ 部分部位仍有問題，請檢查")
        
        return all_fixed

def test_trailing_stop_activation():
    """測試移動停利啟動條件"""
    print("\n🧪 測試移動停利啟動條件...")
    
    with sqlite3.connect("multi_group_strategy.db") as conn:
        cursor = conn.cursor()
        
        # 獲取活躍部位進行測試
        cursor.execute("""
            SELECT id, lot_id, direction, entry_price, trailing_activation_points
            FROM position_records 
            WHERE status = 'ACTIVE' AND trailing_activation_points IS NOT NULL
            ORDER BY id
        """)
        
        positions = cursor.fetchall()
        
        # 模擬當前價格 (從日誌中看到的價格)
        test_prices = {
            'SHORT': 22502  # SHORT部位，當前價格22502
        }
        
        for pos_id, lot_id, direction, entry_price, activation_points in positions:
            if direction in test_prices:
                current_price = test_prices[direction]
                
                # 計算獲利
                if direction == 'SHORT':
                    profit = entry_price - current_price
                else:
                    profit = current_price - entry_price
                
                should_activate = profit >= activation_points
                
                print(f"   📊 部位 {pos_id} (第{lot_id}口, {direction}):")
                print(f"      進場價格: {entry_price}")
                print(f"      當前價格: {current_price}")
                print(f"      當前獲利: {profit}點")
                print(f"      啟動點數: {activation_points}點")
                print(f"      應該啟動: {'✅ 是' if should_activate else '❌ 否'}")
                
                if should_activate:
                    print(f"      🎯 符合啟動條件，應該啟動移動停利")

def main():
    """主修復函數"""
    print("🚀 修復現有部位移動停利參數")
    print("=" * 50)
    
    # 1. 檢查當前狀態
    positions_to_fix = check_current_positions()
    
    # 2. 執行修復
    fix_trailing_stop_parameters(positions_to_fix)
    
    # 3. 驗證修復結果
    success = verify_fix()
    
    # 4. 測試啟動條件
    if success:
        test_trailing_stop_activation()
    
    print(f"\n📋 修復總結:")
    if success:
        print("   ✅ 移動停利參數修復成功")
        print("   ✅ 所有部位都有正確的啟動點數和回撤比例")
        print("   🚀 移動停利機制現在應該能正常工作")
        print("\n📝 下一步:")
        print("   1. 重啟交易系統或重新載入風險管理模組")
        print("   2. 觀察移動停利啟動和平倉是否正常")
        print("   3. 檢查風險引擎計數器是否正確更新")
    else:
        print("   ❌ 修復過程中遇到問題")
        print("   📝 建議檢查資料庫結構和權限")

if __name__ == "__main__":
    main()
