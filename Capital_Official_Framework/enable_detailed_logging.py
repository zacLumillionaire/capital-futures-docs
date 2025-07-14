#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
啟用詳細日誌診斷腳本
用於診斷AsyncUpdater失敗原因
"""

import sqlite3
import os

def enable_async_detailed_logging():
    """啟用AsyncUpdater詳細日誌的代碼片段"""
    print("🔍 AsyncUpdater詳細日誌啟用代碼:")
    print("=" * 60)
    print("在 simple_integrated.py 的Console中執行以下代碼:")
    print()
    print("# 1. 啟用AsyncUpdater詳細日誌")
    print("if hasattr(self, 'async_updater') and self.async_updater:")
    print("    self.async_updater.enable_task_completion_logs = True")
    print("    print('✅ 已啟用AsyncUpdater任務完成日誌')")
    print("else:")
    print("    print('❌ AsyncUpdater不存在')")
    print()
    print("# 2. 檢查當前統計")
    print("if hasattr(self, 'async_updater') and self.async_updater:")
    print("    stats = self.async_updater.stats")
    print("    print(f'📊 當前統計: 總任務:{stats[\"total_tasks\"]}, 完成:{stats[\"completed_tasks\"]}, 失敗:{stats[\"failed_tasks\"]}')")
    print("    print(f'📊 隊列大小: {self.async_updater.update_queue.qsize()}')")
    print()
    print("# 3. 檢查工作線程狀態")
    print("if hasattr(self, 'async_updater') and self.async_updater:")
    print("    if hasattr(self.async_updater, 'worker_thread'):")
    print("        thread = self.async_updater.worker_thread")
    print("        print(f'🧵 工作線程狀態: {\"活躍\" if thread and thread.is_alive() else \"非活躍\"}')")
    print()

def check_database_constraints():
    """檢查數據庫約束"""
    print("\n🔍 數據庫約束檢查:")
    print("=" * 60)
    
    db_path = "multi_group_strategy.db"
    
    if not os.path.exists(db_path):
        print("❌ 資料庫檔案不存在")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. 檢查風險管理狀態表結構
        print("📋 1. 風險管理狀態表結構:")
        cursor.execute("PRAGMA table_info(risk_management_states)")
        columns = cursor.fetchall()
        
        for col in columns:
            col_id, name, type_name, not_null, default, pk = col
            constraints = []
            if not_null:
                constraints.append("NOT NULL")
            if pk:
                constraints.append("PRIMARY KEY")
            if default:
                constraints.append(f"DEFAULT {default}")
            
            constraint_str = f" ({', '.join(constraints)})" if constraints else ""
            print(f"   - {name}: {type_name}{constraint_str}")
        
        # 2. 檢查表的完整約束
        print("\n📋 2. 表的完整約束定義:")
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='risk_management_states'")
        table_sql = cursor.fetchone()
        if table_sql:
            print("   CREATE TABLE 語句:")
            print(f"   {table_sql[0]}")
        
        # 3. 檢查索引
        print("\n📋 3. 相關索引:")
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='risk_management_states'")
        indexes = cursor.fetchall()
        
        if indexes:
            for idx_name, idx_sql in indexes:
                print(f"   - {idx_name}: {idx_sql}")
        else:
            print("   - 無自定義索引")
        
        # 4. 檢查當前數據
        print("\n📋 4. 當前風險管理狀態數據:")
        cursor.execute("SELECT COUNT(*) FROM risk_management_states")
        count = cursor.fetchone()[0]
        print(f"   - 總記錄數: {count}")
        
        if count > 0:
            cursor.execute("""
                SELECT position_id, peak_price, update_reason, last_update_time 
                FROM risk_management_states 
                ORDER BY position_id DESC 
                LIMIT 5
            """)
            recent_records = cursor.fetchall()
            print("   - 最近5條記錄:")
            for record in recent_records:
                print(f"     部位{record[0]}: 峰值={record[1]}, 原因='{record[2]}', 時間={record[3]}")
        
        # 5. 檢查可能的約束衝突
        print("\n📋 5. 檢查可能的約束問題:")
        
        # 檢查重複的position_id
        cursor.execute("""
            SELECT position_id, COUNT(*) as count 
            FROM risk_management_states 
            GROUP BY position_id 
            HAVING COUNT(*) > 1
        """)
        duplicates = cursor.fetchall()
        
        if duplicates:
            print("   ⚠️ 發現重複的position_id:")
            for pos_id, count in duplicates:
                print(f"     部位{pos_id}: {count}條記錄")
        else:
            print("   ✅ 無重複的position_id")
        
        # 6. 檢查update_reason的值
        print("\n📋 6. update_reason值分析:")
        cursor.execute("""
            SELECT update_reason, COUNT(*) as count 
            FROM risk_management_states 
            GROUP BY update_reason 
            ORDER BY count DESC
        """)
        reasons = cursor.fetchall()
        
        if reasons:
            print("   當前使用的update_reason值:")
            for reason, count in reasons:
                print(f"     '{reason}': {count}次")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 數據庫檢查失敗: {e}")

def check_peak_update_logic():
    """檢查峰值更新邏輯的代碼片段"""
    print("\n🔍 峰值更新邏輯檢查:")
    print("=" * 60)
    print("在 simple_integrated.py 的Console中執行以下代碼來檢查峰值更新邏輯:")
    print()
    print("# 1. 檢查風險管理引擎的峰值更新設置")
    print("if hasattr(self, 'multi_group_risk_engine'):")
    print("    engine = self.multi_group_risk_engine")
    print("    print(f'🔧 異步峰值更新啟用: {getattr(engine, \"enable_async_peak_update\", \"未設置\")}')")
    print("    print(f'🔧 異步更新器連接: {\"是\" if getattr(engine, \"async_updater\", None) else \"否\"}')")
    print()
    print("# 2. 檢查最近的峰值更新任務")
    print("if hasattr(self, 'async_updater') and self.async_updater:")
    print("    cache = self.async_updater.memory_cache.get('risk_states', {})")
    print("    print(f'📊 內存中的風險狀態數量: {len(cache)}')")
    print("    if cache:")
    print("        latest_positions = list(cache.keys())[-3:]  # 最近3個部位")
    print("        for pos_id in latest_positions:")
    print("            state = cache[pos_id]")
    print("            print(f'   部位{pos_id}: 峰值={state.get(\"peak_price\")}, 原因={state.get(\"update_reason\")}')")
    print()
    print("# 3. 手動測試峰值更新")
    print("# 注意：只在確實需要時執行，避免產生錯誤數據")
    print("# test_position_id = 146  # 替換為實際的部位ID")
    print("# test_peak_price = 22573.0  # 替換為實際的峰值價格")
    print("# try:")
    print("#     success = self.multi_group_db_manager.update_risk_management_state(")
    print("#         position_id=test_position_id,")
    print("#         peak_price=test_peak_price,")
    print("#         update_time='12:30:00',")
    print("#         update_reason='價格更新'")
    print("#     )")
    print("#     print(f'手動峰值更新測試: {\"成功\" if success else \"失敗\"}')")
    print("# except Exception as e:")
    print("#     print(f'手動峰值更新失敗: {e}')")

def analyze_peak_update_frequency():
    """分析峰值更新頻率"""
    print("\n🔍 峰值更新頻率分析:")
    print("=" * 60)
    print("在 simple_integrated.py 的Console中執行以下代碼:")
    print()
    print("# 檢查峰值更新的觸發頻率")
    print("import time")
    print("start_time = time.time()")
    print("if hasattr(self, 'async_updater') and self.async_updater:")
    print("    initial_stats = self.async_updater.stats.copy()")
    print("    print(f'📊 開始監控 - 當前任務數: {initial_stats[\"total_tasks\"]}')")
    print("    print('等待30秒後再次檢查...')")
    print("    ")
    print("    # 30秒後執行:")
    print("    # current_stats = self.async_updater.stats")
    print("    # new_tasks = current_stats['total_tasks'] - initial_stats['total_tasks']")
    print("    # elapsed = time.time() - start_time")
    print("    # print(f'📊 {elapsed:.1f}秒內新增任務: {new_tasks}個')")
    print("    # print(f'📊 平均任務頻率: {new_tasks/elapsed:.2f}個/秒')")

def main():
    """主函數"""
    print("🔍 AsyncUpdater詳細診斷工具")
    print("=" * 60)
    
    # 1. 啟用詳細日誌的指令
    enable_async_detailed_logging()
    
    # 2. 檢查數據庫約束
    check_database_constraints()
    
    # 3. 峰值更新邏輯檢查
    check_peak_update_logic()
    
    # 4. 峰值更新頻率分析
    analyze_peak_update_frequency()
    
    print("\n💡 診斷建議:")
    print("1. 先執行上述代碼片段啟用詳細日誌")
    print("2. 觀察Console輸出中的具體錯誤信息")
    print("3. 檢查峰值更新是否在非創高時也被觸發")
    print("4. 確認update_reason值是否符合數據庫約束")
    print("5. 監控峰值更新的觸發頻率是否異常")

if __name__ == "__main__":
    main()
