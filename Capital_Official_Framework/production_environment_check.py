#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生產環境檢查工具
檢查正式機和虛擬測試機的實際狀態，確認修復是否在實際環境中生效
"""

import os
import sys
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

# 添加當前目錄到路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

class ProductionEnvironmentCheck:
    """生產環境檢查器"""
    
    def __init__(self):
        # 實際環境的資料庫路徑
        self.production_db = "multi_group_strategy.db"  # 正式機資料庫
        self.virtual_db = "test_virtual_strategy.db"    # 虛擬測試機資料庫
        
        print("🔍 生產環境檢查工具")
        print("=" * 50)
        print("🎯 檢查目標:")
        print("  1. 正式機資料庫狀態")
        print("  2. 虛擬測試機資料庫狀態") 
        print("  3. 累積獲利計算邏輯驗證")
        print("  4. 重複觸發防護機制狀態")
        print("=" * 50)
    
    def check_database_exists(self, db_path: str) -> bool:
        """檢查資料庫是否存在"""
        exists = os.path.exists(db_path)
        status = "✅ 存在" if exists else "❌ 不存在"
        print(f"📁 {db_path}: {status}")
        return exists
    
    def check_database_schema(self, db_path: str) -> Dict:
        """檢查資料庫表結構"""
        if not os.path.exists(db_path):
            return {"error": "資料庫文件不存在"}
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 檢查關鍵表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            schema_info = {
                "tables": tables,
                "position_records_exists": "position_records" in tables,
                "strategy_groups_exists": "strategy_groups" in tables,
                "risk_management_states_exists": "risk_management_states" in tables
            }
            
            # 檢查position_records表結構
            if "position_records" in tables:
                cursor.execute("PRAGMA table_info(position_records)")
                columns = [row[1] for row in cursor.fetchall()]
                schema_info["position_records_columns"] = columns
                schema_info["has_realized_pnl"] = "realized_pnl" in columns
                schema_info["has_direction"] = "direction" in columns
                schema_info["has_entry_time"] = "entry_time" in columns
            
            conn.close()
            return schema_info
            
        except Exception as e:
            return {"error": str(e)}
    
    def check_position_data(self, db_path: str) -> Dict:
        """檢查部位數據"""
        if not os.path.exists(db_path):
            return {"error": "資料庫文件不存在"}
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 檢查是否有部位記錄
            cursor.execute("SELECT COUNT(*) FROM position_records")
            total_positions = cursor.fetchone()[0]
            
            # 檢查已平倉部位
            cursor.execute("SELECT COUNT(*) FROM position_records WHERE status = 'EXITED'")
            exited_positions = cursor.fetchone()[0]
            
            # 檢查活躍部位
            cursor.execute("SELECT COUNT(*) FROM position_records WHERE status = 'ACTIVE'")
            active_positions = cursor.fetchone()[0]
            
            # 檢查有獲利記錄的部位
            cursor.execute("SELECT COUNT(*) FROM position_records WHERE realized_pnl IS NOT NULL AND realized_pnl != 0")
            profit_positions = cursor.fetchone()[0]
            
            # 獲取最近的部位記錄
            cursor.execute('''
                SELECT id, group_id, lot_id, status, realized_pnl, entry_price 
                FROM position_records 
                ORDER BY id DESC 
                LIMIT 5
            ''')
            recent_positions = cursor.fetchall()
            
            conn.close()
            
            return {
                "total_positions": total_positions,
                "exited_positions": exited_positions,
                "active_positions": active_positions,
                "profit_positions": profit_positions,
                "recent_positions": recent_positions
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def test_cumulative_profit_logic(self, db_path: str) -> Dict:
        """測試累積獲利計算邏輯"""
        if not os.path.exists(db_path):
            return {"error": "資料庫文件不存在"}
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 檢查是否有策略組（修復：使用正確的欄位名稱）
            cursor.execute("SELECT id, group_id, date, direction FROM strategy_groups LIMIT 5")
            groups = cursor.fetchall()

            results = {}

            for db_id, logical_group_id, date_str, direction in groups:
                # 測試修復後的查詢邏輯（使用logical_group_id作為查詢條件）
                cursor.execute('''
                    SELECT id, realized_pnl, lot_id
                    FROM position_records
                    WHERE group_id = ?
                      AND status = 'EXITED'
                      AND realized_pnl IS NOT NULL
                    ORDER BY id
                ''', (logical_group_id,))

                profit_records = cursor.fetchall()
                cumulative_profit = sum(row[1] for row in profit_records if row[1] is not None)

                # 檢查活躍部位
                cursor.execute('''
                    SELECT COUNT(*)
                    FROM position_records
                    WHERE group_id = ? AND status = 'ACTIVE'
                ''', (logical_group_id,))

                active_count = cursor.fetchone()[0]

                group_display_name = f"組{logical_group_id}({direction})"
                results[f"group_{logical_group_id}"] = {
                    "group_name": group_display_name,
                    "date": date_str,
                    "direction": direction,
                    "profit_records": profit_records,
                    "cumulative_profit": cumulative_profit,
                    "active_positions": active_count,
                    "should_trigger_protection": cumulative_profit > 0 and active_count > 0
                }
            
            conn.close()
            return results
            
        except Exception as e:
            return {"error": str(e)}
    
    def check_environment(self, env_name: str, db_path: str):
        """檢查單個環境"""
        print(f"\n🔍 檢查{env_name}")
        print("-" * 40)
        
        # 1. 檢查資料庫文件
        db_exists = self.check_database_exists(db_path)
        
        if not db_exists:
            print(f"❌ {env_name}資料庫不存在，無法進行進一步檢查")
            return False
        
        # 2. 檢查資料庫結構
        print(f"\n📋 {env_name}資料庫結構:")
        schema = self.check_database_schema(db_path)
        
        if "error" in schema:
            print(f"❌ 結構檢查失敗: {schema['error']}")
            return False
        
        print(f"  表數量: {len(schema['tables'])}")
        print(f"  position_records表: {'✅ 存在' if schema['position_records_exists'] else '❌ 不存在'}")
        print(f"  realized_pnl欄位: {'✅ 存在' if schema.get('has_realized_pnl', False) else '❌ 不存在'}")
        print(f"  direction欄位: {'✅ 存在' if schema.get('has_direction', False) else '❌ 不存在'}")
        print(f"  entry_time欄位: {'✅ 存在' if schema.get('has_entry_time', False) else '❌ 不存在'}")
        
        # 3. 檢查部位數據
        print(f"\n📊 {env_name}部位數據:")
        position_data = self.check_position_data(db_path)
        
        if "error" in position_data:
            print(f"❌ 數據檢查失敗: {position_data['error']}")
            return False
        
        print(f"  總部位數: {position_data['total_positions']}")
        print(f"  已平倉部位: {position_data['exited_positions']}")
        print(f"  活躍部位: {position_data['active_positions']}")
        print(f"  有獲利記錄: {position_data['profit_positions']}")
        
        if position_data['recent_positions']:
            print(f"  最近部位:")
            for pos in position_data['recent_positions']:
                print(f"    部位{pos[0]} (組{pos[1]}_口{pos[2]}): {pos[3]}, 獲利={pos[4]}")
        
        # 4. 測試累積獲利邏輯
        print(f"\n🧮 {env_name}累積獲利邏輯測試:")
        profit_logic = self.test_cumulative_profit_logic(db_path)
        
        if "error" in profit_logic:
            print(f"❌ 邏輯測試失敗: {profit_logic['error']}")
            return False
        
        if not profit_logic:
            print("  📝 沒有策略組數據可供測試")
            return True
        
        for group_key, group_data in profit_logic.items():
            print(f"  策略組 {group_data['group_name']}:")
            print(f"    累積獲利: {group_data['cumulative_profit']:.1f} 點")
            print(f"    活躍部位: {group_data['active_positions']} 個")
            print(f"    應觸發保護: {'✅ 是' if group_data['should_trigger_protection'] else '❌ 否'}")
        
        return True
    
    def run_production_check(self):
        """運行生產環境檢查"""
        print("🚀 開始生產環境檢查")
        
        start_time = datetime.now()
        
        # 檢查正式機
        production_ok = self.check_environment("正式機", self.production_db)
        
        # 檢查虛擬測試機
        virtual_ok = self.check_environment("虛擬測試機", self.virtual_db)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 生成總結報告
        print("\n" + "=" * 50)
        print("📊 生產環境檢查總結")
        print("=" * 50)
        print(f"檢查時間: {duration:.2f} 秒")
        print(f"正式機狀態: {'✅ 正常' if production_ok else '❌ 異常'}")
        print(f"虛擬測試機狀態: {'✅ 正常' if virtual_ok else '❌ 異常'}")
        
        print(f"\n🔧 修復狀態評估:")
        if production_ok and virtual_ok:
            print("✅ 兩個環境都正常，修復可能已生效")
            print("💡 建議: 可以進行實際交易測試")
        elif production_ok or virtual_ok:
            print("⚠️ 部分環境正常，需要進一步檢查")
            print("💡 建議: 檢查異常環境的配置和數據")
        else:
            print("❌ 兩個環境都有問題，需要修復")
            print("💡 建議: 檢查資料庫文件和表結構")
        
        print(f"\n📋 下一步建議:")
        print("1. 如果環境檢查正常，運行實際交易測試")
        print("2. 如果環境檢查異常，先修復環境問題")
        print("3. 監控實際交易中的保護性停損觸發情況")
        print("4. 觀察是否還有重複平倉現象")
        
        return production_ok and virtual_ok

if __name__ == "__main__":
    checker = ProductionEnvironmentCheck()
    success = checker.run_production_check()
    
    if success:
        print("\n🎉 生產環境檢查通過！可以進行實際測試")
    else:
        print("\n⚠️ 生產環境檢查發現問題，需要先修復環境")
    
    exit(0 if success else 1)
