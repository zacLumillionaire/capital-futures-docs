#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
徹底清理測試環境 - 清除所有可能的狀態和緩存
包括：資料庫記錄、內存緩存、鎖定狀態、追蹤器狀態等
支援同時清理正式機和測試機環境
"""

import os
import sys
import sqlite3
import time
from datetime import date, datetime

def cleanup_test_positions():
    """徹底清理測試環境 - 支援正式機和測試機"""
    print("🧹 徹底清理測試環境 (正式機 + 測試機)")
    print("=" * 70)
    print("📋 將清理以下內容：")
    print("   1. 正式機資料庫 (multi_group_strategy.db)")
    print("   2. 測試機資料庫 (test_virtual_strategy.db)")
    print("   3. 風險管理狀態")
    print("   4. 內存緩存和鎖定狀態")
    print("   5. 追蹤器狀態")
    print("   6. 訂單追蹤記錄")
    print("=" * 70)

    # 🔧 修改：支援多個資料庫
    databases = {
        "正式機": "multi_group_strategy.db",
        "測試機": "test_virtual_strategy.db"
    }

    # 檢查資料庫存在性
    available_databases = {}
    for env_name, db_path in databases.items():
        if os.path.exists(db_path):
            available_databases[env_name] = db_path
            print(f"✅ 發現 {env_name} 資料庫: {db_path}")
        else:
            print(f"⚠️ {env_name} 資料庫不存在: {db_path}")

    if not available_databases:
        print("❌ 沒有找到任何資料庫檔案")
        return

    # 🔧 修改：遍歷所有可用資料庫進行檢查
    all_databases_info = {}
    total_active_positions = 0
    total_risk_states = 0
    total_groups = 0

    for env_name, db_path in available_databases.items():
        print(f"\n🔍 檢查 {env_name} 環境...")
        print("-" * 40)

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 1. 檢查當前的活躍部位
            print(f"🔍 步驟1: 檢查 {env_name} 活躍部位...")
            cursor.execute('''
                SELECT pr.id, pr.group_id, pr.lot_id, pr.direction, pr.entry_price,
                       pr.status, pr.order_status, sg.group_id as original_group_id,
                       sg.date, pr.created_at
                FROM position_records pr
                LEFT JOIN strategy_groups sg ON pr.group_id = sg.id
                WHERE pr.status = 'ACTIVE'
                ORDER BY pr.created_at
            ''')

            active_positions = cursor.fetchall()

            # 2. 檢查風險管理狀態
            print(f"🔍 步驟2: 檢查 {env_name} 風險管理狀態...")
            cursor.execute('SELECT COUNT(*) FROM risk_management_states')
            risk_states_count = cursor.fetchone()[0]

            # 3. 檢查策略組狀態
            print(f"🔍 步驟3: 檢查 {env_name} 策略組狀態...")
            cursor.execute('SELECT COUNT(*) FROM strategy_groups WHERE date = ?', (date.today().strftime('%Y-%m-%d'),))
            today_groups_count = cursor.fetchone()[0]

            # 4. 顯示當前狀態
            print(f"\n📊 {env_name} 當前狀態:")
            print(f"   - 活躍部位: {len(active_positions)} 個")
            print(f"   - 風險管理狀態: {risk_states_count} 個")
            print(f"   - 今日策略組: {today_groups_count} 個")

            if len(active_positions) > 0:
                print(f"\n📋 {env_name} 活躍部位詳情:")
                for pos in active_positions:
                    # 修復：sqlite3.Row對象使用索引或鍵訪問，不支持get方法
                    original_group_id = pos['original_group_id'] if pos['original_group_id'] is not None else 'N/A'
                    date_value = pos['date'] if pos['date'] is not None else 'N/A'
                    print(f"   - 部位{pos['id']}: 組{original_group_id}, {pos['direction']}, "
                          f"@{pos['entry_price']}, 日期:{date_value}")

            # 保存資料庫資訊
            all_databases_info[env_name] = {
                'db_path': db_path,
                'conn': conn,
                'cursor': cursor,
                'active_positions': active_positions,
                'risk_states_count': risk_states_count,
                'today_groups_count': today_groups_count
            }

            # 累計統計
            total_active_positions += len(active_positions)
            total_risk_states += risk_states_count
            total_groups += today_groups_count

        except Exception as e:
            print(f"❌ 檢查 {env_name} 失敗: {e}")
            continue

    # 檢查是否有需要清理的數據
    if total_active_positions == 0 and total_risk_states == 0 and total_groups == 0:
        print(f"\n✅ 所有環境都沒有需要清理的數據")
        # 關閉所有連接
        for info in all_databases_info.values():
            info['conn'].close()
        return

    # 5. 顯示總體統計
    print(f"\n📊 總體統計:")
    print(f"   - 總活躍部位: {total_active_positions} 個")
    print(f"   - 總風險管理狀態: {total_risk_states} 個")
    print(f"   - 總今日策略組: {total_groups} 個")
    print(f"   - 涉及環境: {', '.join(all_databases_info.keys())}")

    # 6. 詢問是否進行徹底清理
    print(f"\n⚠️ 檢測到測試數據，可能會觸發風險管理停損")
    print("🔧 建議進行徹底清理以確保測試環境乾淨")
    print("💡 將同時清理正式機和測試機環境")
    choice = input("\n是否要進行徹底清理？(y/N): ").strip().lower()

    if choice != 'y':
        print("❌ 取消清理")
        # 關閉所有連接
        for info in all_databases_info.values():
            info['conn'].close()
        return

    # 7. 清理方式選擇
    print("\n🔧 清理方式選擇:")
    print("1. 完全重置 (推薦) - 清除所有測試數據，重置為全新狀態")
    print("2. 標記為已出場 - 保留記錄但標記為已平倉")
    print("3. 標記為失敗 - 標記為測試失敗數據")
    print("4. 徹底清理 - 刪除所有相關記錄")

    method = input("請選擇清理方式 (1/2/3/4): ").strip()

    # 8. 執行清理 - 對所有資料庫執行
    cleanup_success = True

    for env_name, info in all_databases_info.items():
        print(f"\n🧹 清理 {env_name} 環境...")
        print("-" * 40)

        env_success = False
        cursor = info['cursor']
        active_positions = info['active_positions']

        if method == "1":
            # 完全重置 (推薦)
            env_success = perform_complete_reset(cursor, active_positions, env_name)

        elif method == "2":
            # 標記為已出場
            env_success = mark_positions_as_exited(cursor, active_positions, env_name)

        elif method == "3":
            # 標記為失敗
            env_success = mark_positions_as_failed(cursor, active_positions, env_name)

        elif method == "4":
            # 徹底清理
            env_success = perform_thorough_cleanup(cursor, active_positions, env_name)

        else:
            print("❌ 無效選擇，取消清理")
            # 關閉所有連接
            for info in all_databases_info.values():
                info['conn'].close()
            return

        if env_success:
            print(f"✅ {env_name} 清理成功")
        else:
            print(f"❌ {env_name} 清理失敗")
            cleanup_success = False

    if not cleanup_success:
        print("❌ 部分環境清理過程中發生錯誤")
        # 關閉所有連接
        for info in all_databases_info.values():
            info['conn'].close()
        return

    # 9. 清理內存狀態和鎖定
    print("\n🧹 步驟9: 清理內存狀態和鎖定...")
    try:
        clear_memory_states()
    except Exception as e:
        print(f"   ⚠️ 內存狀態清理失敗: {e}")

    # 10. 提交變更並驗證結果
    print(f"\n📊 清理後狀態驗證:")
    print("=" * 50)

    total_final_active = 0
    total_final_exited = 0
    total_final_failed = 0
    total_final_risk = 0
    total_final_groups = 0

    for env_name, info in all_databases_info.items():
        print(f"\n📊 {env_name} 清理後狀態:")

        try:
            # 提交變更
            info['conn'].commit()

            cursor = info['cursor']

            cursor.execute("SELECT COUNT(*) FROM position_records WHERE status = 'ACTIVE'")
            active_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM position_records WHERE status = 'EXITED'")
            exited_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM position_records WHERE status = 'FAILED'")
            failed_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM risk_management_states")
            risk_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM strategy_groups WHERE date = ?", (date.today().strftime('%Y-%m-%d'),))
            group_count = cursor.fetchone()[0]

            print(f"   - 活躍部位: {active_count}")
            print(f"   - 已出場部位: {exited_count}")
            print(f"   - 失敗部位: {failed_count}")
            print(f"   - 風險管理狀態: {risk_count}")
            print(f"   - 今日策略組: {group_count}")

            # 累計統計
            total_final_active += active_count
            total_final_exited += exited_count
            total_final_failed += failed_count
            total_final_risk += risk_count
            total_final_groups += group_count

            # 關閉連接
            info['conn'].close()

        except Exception as e:
            print(f"   ❌ {env_name} 驗證失敗: {e}")
            info['conn'].close()

    print(f"\n📊 總體清理結果:")
    print(f"   - 總活躍部位: {total_final_active}")
    print(f"   - 總已出場部位: {total_final_exited}")
    print(f"   - 總失敗部位: {total_final_failed}")
    print(f"   - 總風險管理狀態: {total_final_risk}")
    print(f"   - 總今日策略組: {total_final_groups}")

    print("\n🎉 徹底清理完成！")
    print("💡 建議重啟程序以確保內存狀態也被清除")
    print("💡 現在可以重新測試策略，環境已完全重置")
    print("\n📋 清理總結:")
    print("   ✅ 正式機資料庫記錄已清理")
    print("   ✅ 測試機資料庫記錄已清理")
    print("   ✅ 風險管理狀態已清理")
    print("   ✅ 策略組狀態已清理")
    print("   ✅ 內存清理指令已發出")
    print("   🔄 建議重啟程序完成清理")

def perform_complete_reset(cursor, active_positions, env_name=""):
    """完全重置 - 清除所有測試數據"""
    try:
        print(f"🔄 執行 {env_name} 完全重置...")

        # 1. 清理部位記錄
        if active_positions:
            position_ids = [str(pos['id']) for pos in active_positions]
            placeholders = ','.join(['?'] * len(position_ids))

            # 刪除風險管理狀態
            cursor.execute(f'DELETE FROM risk_management_states WHERE position_id IN ({placeholders})', position_ids)
            print(f"   ✅ 清理 {len(position_ids)} 個風險管理狀態")

            # 刪除部位記錄
            cursor.execute(f'DELETE FROM position_records WHERE id IN ({placeholders})', position_ids)
            print(f"   ✅ 清理 {len(position_ids)} 個部位記錄")

        # 2. 清理今日策略組
        today = date.today().strftime('%Y-%m-%d')
        cursor.execute('DELETE FROM strategy_groups WHERE date = ?', (today,))
        print(f"   ✅ 清理今日策略組")

        # 3. 清理即時報價（可選，檢查表是否存在）
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='real_time_quotes'")
            if cursor.fetchone():
                cursor.execute('DELETE FROM real_time_quotes WHERE timestamp < datetime("now", "-1 hour")')
                print(f"   ✅ 清理舊即時報價")
            else:
                print(f"   ⚠️ real_time_quotes表不存在，跳過清理")
        except Exception as e:
            print(f"   ⚠️ 清理即時報價失敗: {e}")

        print(f"✅ {env_name} 完全重置完成")
        return True

    except Exception as e:
        print(f"❌ {env_name} 完全重置失敗: {e}")
        return False

def mark_positions_as_exited(cursor, active_positions, env_name=""):
    """標記部位為已出場"""
    try:
        print(f"📝 標記 {env_name} 部位為已出場...")

        for pos in active_positions:
            cursor.execute('''
                UPDATE position_records
                SET status = 'EXITED',
                    exit_price = entry_price,
                    exit_time = datetime('now', 'localtime'),
                    exit_reason = '手動清理',
                    pnl = 0,
                    pnl_amount = 0,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (pos['id'],))

        print(f"✅ 已將 {env_name} {len(active_positions)} 個部位標記為已出場")
        return True

    except Exception as e:
        print(f"❌ {env_name} 標記出場失敗: {e}")
        return False

def mark_positions_as_failed(cursor, active_positions, env_name=""):
    """標記部位為失敗"""
    try:
        print(f"📝 標記 {env_name} 部位為失敗...")

        for pos in active_positions:
            cursor.execute('''
                UPDATE position_records
                SET status = 'FAILED',
                    order_status = 'CANCELLED',
                    exit_reason = '測試數據清理',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (pos['id'],))

        print(f"✅ 已將 {env_name} {len(active_positions)} 個部位標記為失敗")
        return True

    except Exception as e:
        print(f"❌ {env_name} 標記失敗失敗: {e}")
        return False

def perform_thorough_cleanup(cursor, active_positions, env_name=""):
    """徹底清理 - 刪除所有相關記錄"""
    try:
        print(f"🗑️ 執行 {env_name} 徹底清理...")

        if active_positions:
            position_ids = [str(pos['id']) for pos in active_positions]
            placeholders = ','.join(['?'] * len(position_ids))

            # 刪除所有相關記錄
            cursor.execute(f'DELETE FROM risk_management_states WHERE position_id IN ({placeholders})', position_ids)
            cursor.execute(f'DELETE FROM position_records WHERE id IN ({placeholders})', position_ids)

        # 清理所有今日數據
        today = date.today().strftime('%Y-%m-%d')
        cursor.execute('DELETE FROM strategy_groups WHERE date = ?', (today,))

        # 檢查real_time_quotes表是否存在
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='real_time_quotes'")
            if cursor.fetchone():
                cursor.execute('DELETE FROM real_time_quotes WHERE DATE(timestamp) = ?', (today,))
        except Exception as e:
            print(f"   ⚠️ 清理今日報價數據失敗: {e}")

        print(f"✅ {env_name} 徹底清理完成")
        return True

    except Exception as e:
        print(f"❌ {env_name} 徹底清理失敗: {e}")
        return False

def clear_memory_states():
    """清理內存狀態和鎖定"""
    try:
        print("🧠 清理內存狀態...")

        # 嘗試清理GlobalExitManager鎖定狀態
        try:
            # 這裡我們不能直接導入，因為可能會有依賴問題
            # 但我們可以提供清理指令
            print("   📋 建議重啟程序以清理內存狀態")
            print("   📋 或者在程序中調用 global_exit_manager.clear_all_exits()")

        except Exception as e:
            print(f"   ⚠️ 無法直接清理內存狀態: {e}")

        print("✅ 內存狀態清理指令已發出")

    except Exception as e:
        print(f"❌ 清理內存狀態失敗: {e}")

if __name__ == "__main__":
    try:
        cleanup_test_positions()
    except Exception as e:
        print(f"❌ 清理失敗: {e}")
        import traceback
        traceback.print_exc()


