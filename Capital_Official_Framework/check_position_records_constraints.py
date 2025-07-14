#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查 position_records 表的約束情況
"""

import sqlite3

def check_position_records_table():
    """檢查 position_records 表結構"""
    try:
        conn = sqlite3.connect("multi_group_strategy.db")
        cursor = conn.cursor()
        
        # 獲取表結構
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='position_records'")
        result = cursor.fetchone()
        
        if result:
            table_sql = result[0]
            print("📋 position_records 表結構:")
            print(table_sql)
            
            # 檢查具體約束
            constraints_to_check = [
                "CHECK(direction IN ('LONG', 'SHORT'))",
                "CHECK(status IN ('ACTIVE', 'EXITED', 'FAILED'))",
                "CHECK(order_status IN ('PENDING', 'FILLED', 'CANCELLED', 'REJECTED') OR order_status IS NULL)",
                "CHECK(lot_id BETWEEN 1 AND 3)",
                "CHECK(exit_reason IN ('移動停利', '保護性停損', '初始停損', '手動出場', 'FOK失敗', '下單失敗') OR exit_reason IS NULL)",
                "CHECK(retry_count >= 0 AND retry_count <= 5)",
                "CHECK(max_slippage_points > 0)"
            ]
            
            print("\n🔍 約束檢查結果:")
            missing_constraints = []
            
            for constraint in constraints_to_check:
                if constraint in table_sql:
                    print(f"✅ {constraint}")
                else:
                    print(f"❌ {constraint}")
                    missing_constraints.append(constraint)
            
            if missing_constraints:
                print(f"\n⚠️ 缺少的約束: {len(missing_constraints)} 個")
                for constraint in missing_constraints:
                    print(f"  - {constraint}")
            else:
                print("\n✅ 所有約束都存在")
                
            return len(missing_constraints) == 0
        else:
            print("❌ 找不到 position_records 表")
            return False
            
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_position_records_table()
