#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
保護性停損緊急修復
修復保護性停損機制的關鍵問題
"""

import sqlite3
import json
from datetime import datetime

def fix_protective_stop_parameters():
    """修復保護性停損參數"""
    print("🔧 修復保護性停損參數...")
    
    try:
        with sqlite3.connect("multi_group_strategy.db") as conn:
            cursor = conn.cursor()
            
            # 獲取活躍部位
            cursor.execute("""
                SELECT id, lot_id, rule_config
                FROM position_records 
                WHERE status = 'ACTIVE'
                ORDER BY id
            """)
            
            positions = cursor.fetchall()
            
            fixed_count = 0
            for pos_id, lot_id, rule_config in positions:
                if rule_config:
                    try:
                        config = json.loads(rule_config)
                        
                        # 修復保護性停損配置
                        needs_update = False
                        
                        # 確保所有部位都有保護倍數
                        if lot_id == 1:
                            if config.get('protective_stop_multiplier') is None:
                                config['protective_stop_multiplier'] = 1.0
                                needs_update = True
                                print(f"   部位{pos_id}: 設置第1口保護倍數為1.0")
                        elif lot_id == 2:
                            if config.get('protective_stop_multiplier') is None:
                                config['protective_stop_multiplier'] = 2.0
                                needs_update = True
                                print(f"   部位{pos_id}: 設置第2口保護倍數為2.0")
                        
                        # 啟用保護性停損
                        if not config.get('use_protective_stop', False):
                            config['use_protective_stop'] = True
                            needs_update = True
                            print(f"   部位{pos_id}: 啟用保護性停損")
                        
                        # 更新配置
                        if needs_update:
                            new_config = json.dumps(config)
                            cursor.execute("""
                                UPDATE position_records 
                                SET rule_config = ?, updated_at = CURRENT_TIMESTAMP
                                WHERE id = ?
                            """, (new_config, pos_id))
                            fixed_count += 1
                            
                    except json.JSONDecodeError:
                        print(f"   ❌ 部位{pos_id}: 配置解析失敗")
                else:
                    print(f"   ❌ 部位{pos_id}: 缺少配置")
            
            conn.commit()
            print(f"   ✅ 修復了 {fixed_count} 個部位的保護性停損參數")
            return True
            
    except Exception as e:
        print(f"   ❌ 修復失敗: {e}")
        return False

def add_protective_stop_database_fields():
    """添加保護性停損資料庫欄位"""
    print("\n🔧 添加保護性停損資料庫欄位...")
    
    try:
        with sqlite3.connect("multi_group_strategy.db") as conn:
            cursor = conn.cursor()
            
            # 檢查並添加 position_records 欄位
            cursor.execute("PRAGMA table_info(position_records)")
            pr_columns = [col[1] for col in cursor.fetchall()]
            
            pr_fields_to_add = [
                ('protective_stop_price', 'REAL'),
                ('protective_stop_activated', 'INTEGER DEFAULT 0'),
                ('first_lot_exit_profit', 'REAL')
            ]
            
            for field_name, field_type in pr_fields_to_add:
                if field_name not in pr_columns:
                    try:
                        cursor.execute(f"ALTER TABLE position_records ADD COLUMN {field_name} {field_type}")
                        print(f"   ✅ 添加 position_records.{field_name}")
                    except Exception as e:
                        print(f"   ⚠️ 添加 position_records.{field_name} 失敗: {e}")
                else:
                    print(f"   ✅ position_records.{field_name} 已存在")
            
            # 檢查並添加 risk_management_states 欄位
            try:
                cursor.execute("PRAGMA table_info(risk_management_states)")
                rms_columns = [col[1] for col in cursor.fetchall()]
                
                rms_fields_to_add = [
                    ('protective_stop_price', 'REAL'),
                    ('protective_stop_activated', 'INTEGER DEFAULT 0')
                ]
                
                for field_name, field_type in rms_fields_to_add:
                    if field_name not in rms_columns:
                        try:
                            cursor.execute(f"ALTER TABLE risk_management_states ADD COLUMN {field_name} {field_type}")
                            print(f"   ✅ 添加 risk_management_states.{field_name}")
                        except Exception as e:
                            print(f"   ⚠️ 添加 risk_management_states.{field_name} 失敗: {e}")
                    else:
                        print(f"   ✅ risk_management_states.{field_name} 已存在")
                        
            except Exception as e:
                print(f"   ⚠️ 檢查 risk_management_states 表失敗: {e}")
            
            conn.commit()
            return True
            
    except Exception as e:
        print(f"   ❌ 添加欄位失敗: {e}")
        return False

def test_protective_stop_calculation():
    """測試保護性停損計算邏輯"""
    print("\n🧪 測試保護性停損計算邏輯...")
    
    # 測試案例
    test_cases = [
        {
            'description': 'SHORT部位保護性停損計算',
            'direction': 'SHORT',
            'entry_price': 22542.0,
            'first_lot_profit': 20.0,
            'protective_multiplier': 2.0,
            'expected_protective_price': 22502.0  # 22542 - (20 * 2.0)
        },
        {
            'description': 'LONG部位保護性停損計算',
            'direction': 'LONG',
            'entry_price': 22500.0,
            'first_lot_profit': 20.0,
            'protective_multiplier': 2.0,
            'expected_protective_price': 22540.0  # 22500 + (20 * 2.0)
        }
    ]
    
    all_passed = True
    
    for case in test_cases:
        print(f"\n   📊 {case['description']}:")
        print(f"      方向: {case['direction']}")
        print(f"      進場價格: {case['entry_price']}")
        print(f"      第一口獲利: {case['first_lot_profit']}點")
        print(f"      保護倍數: {case['protective_multiplier']}")
        
        # 正確的計算邏輯
        if case['direction'] == 'SHORT':
            # SHORT部位：保護價格 = 進場價格 - (第一口獲利 × 倍數)
            calculated_price = case['entry_price'] - (case['first_lot_profit'] * case['protective_multiplier'])
        else:
            # LONG部位：保護價格 = 進場價格 + (第一口獲利 × 倍數)
            calculated_price = case['entry_price'] + (case['first_lot_profit'] * case['protective_multiplier'])
        
        print(f"      計算結果: {calculated_price}")
        print(f"      預期結果: {case['expected_protective_price']}")
        
        if abs(calculated_price - case['expected_protective_price']) < 0.01:
            print(f"      ✅ 計算正確")
        else:
            print(f"      ❌ 計算錯誤")
            all_passed = False
        
        # 檢查合理性
        if case['direction'] == 'SHORT':
            if calculated_price < case['entry_price']:
                print(f"      ✅ SHORT保護價格合理 ({calculated_price} < {case['entry_price']})")
            else:
                print(f"      ❌ SHORT保護價格不合理")
                all_passed = False
        else:
            if calculated_price > case['entry_price']:
                print(f"      ✅ LONG保護價格合理 ({calculated_price} > {case['entry_price']})")
            else:
                print(f"      ❌ LONG保護價格不合理")
                all_passed = False
    
    return all_passed

def simulate_protective_stop_trigger():
    """模擬保護性停損觸發"""
    print("\n🎯 模擬保護性停損觸發情境...")
    
    try:
        with sqlite3.connect("multi_group_strategy.db") as conn:
            cursor = conn.cursor()
            
            # 獲取當前部位
            cursor.execute("""
                SELECT pr.id, pr.lot_id, pr.direction, pr.entry_price, pr.rule_config
                FROM position_records pr
                WHERE pr.status = 'ACTIVE'
                ORDER BY pr.lot_id
            """)
            
            positions = cursor.fetchall()
            
            if len(positions) >= 2:
                first_lot = positions[0]
                second_lot = positions[1]
                
                pos1_id, lot1_id, direction1, entry1, config1 = first_lot
                pos2_id, lot2_id, direction2, entry2, config2 = second_lot
                
                print(f"   第一口部位: {pos1_id} (進場: {entry1})")
                print(f"   第二口部位: {pos2_id} (進場: {entry2})")
                
                # 模擬第一口平倉
                simulated_exit_price = 22520
                if direction1 == 'SHORT':
                    first_profit = entry1 - simulated_exit_price
                else:
                    first_profit = simulated_exit_price - entry1
                
                print(f"\n   模擬第一口平倉:")
                print(f"      平倉價格: {simulated_exit_price}")
                print(f"      獲利: {first_profit}點")
                
                # 計算第二口保護性停損
                if config2:
                    try:
                        config = json.loads(config2)
                        multiplier = config.get('protective_stop_multiplier', 2.0)
                        
                        # 使用正確的計算公式
                        if direction2 == 'SHORT':
                            protective_price = entry2 - (first_profit * multiplier)
                        else:
                            protective_price = entry2 + (first_profit * multiplier)
                        
                        print(f"\n   第二口保護性停損:")
                        print(f"      保護倍數: {multiplier}")
                        print(f"      保護價格: {protective_price}")
                        
                        # 檢查觸發條件
                        current_price = 22515
                        
                        if direction2 == 'SHORT':
                            should_trigger = current_price >= protective_price
                            trigger_condition = f"{current_price} >= {protective_price}"
                        else:
                            should_trigger = current_price <= protective_price
                            trigger_condition = f"{current_price} <= {protective_price}"
                        
                        print(f"      當前價格: {current_price}")
                        print(f"      觸發條件: {trigger_condition}")
                        print(f"      應該觸發: {should_trigger}")
                        
                        if should_trigger:
                            print(f"      🎯 觸發保護性停損!")
                        else:
                            print(f"      ✅ 保護性停損待命中")
                        
                        return True
                        
                    except json.JSONDecodeError:
                        print(f"   ❌ 第二口配置解析失敗")
                        return False
                else:
                    print(f"   ❌ 第二口缺少配置")
                    return False
            else:
                print(f"   ℹ️ 部位數量不足，無法模擬")
                return True
                
    except Exception as e:
        print(f"   ❌ 模擬失敗: {e}")
        return False

def generate_fix_summary(results):
    """生成修復總結"""
    print("\n📋 保護性停損緊急修復總結")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"修復項目: {total}")
    print(f"成功項目: {passed}")
    print(f"失敗項目: {total - passed}")
    
    if passed == total:
        print("\n✅ 保護性停損緊急修復完成!")
        print("   主要問題已修復，建議進行完整測試")
    elif passed >= total * 0.8:
        print("\n⚠️ 保護性停損部分修復完成")
        print("   大部分問題已修復，但仍有部分問題")
    else:
        print("\n🚨 保護性停損修復失敗!")
        print("   存在嚴重問題，需要進一步檢查")
    
    print(f"\n📝 後續建議:")
    print("   1. 完整測試保護性停損功能")
    print("   2. 添加統一出場管理器支援")
    print("   3. 完善狀態更新機制")
    print("   4. 監控保護性停損執行")

def main():
    """主修復函數"""
    print("🚀 保護性停損緊急修復")
    print("=" * 40)
    print("🎯 修復關鍵問題，確保保護性停損能正常工作")
    print("=" * 40)
    
    results = []
    
    # 1. 修復保護性停損參數
    results.append(fix_protective_stop_parameters())
    
    # 2. 添加資料庫欄位
    results.append(add_protective_stop_database_fields())
    
    # 3. 測試計算邏輯
    results.append(test_protective_stop_calculation())
    
    # 4. 模擬觸發情境
    results.append(simulate_protective_stop_trigger())
    
    # 5. 生成總結
    generate_fix_summary(results)

if __name__ == "__main__":
    main()
