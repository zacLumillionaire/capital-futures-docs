#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平倉問題診斷工具
專門診斷異步更新與同步查詢的時序問題，以及口級別追價機制的影響
"""

import sys
import os
import time
import sqlite3
from datetime import datetime, date
from typing import Dict, List, Optional, Any

# 添加框架路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'Capital_Official_Framework'))

def print_header(title: str):
    """打印診斷標題"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def print_section(title: str):
    """打印診斷小節"""
    print(f"\n🎯 {title}")
    print("-" * 40)

class PlatformDiagnostics:
    """平倉問題診斷器"""

    def __init__(self):
        # 檢查可能的資料庫文件
        possible_dbs = [
            "Capital_Official_Framework/multi_group_strategy.db",
            "Capital_Official_Framework/trading_data.db",
            "Capital_Official_Framework/strategy_trading.db"
        ]

        self.db_path = None
        for db_path in possible_dbs:
            if os.path.exists(db_path):
                self.db_path = db_path
                break

        self.console_enabled = True

    def diagnose_database_status(self):
        """診斷1：資料庫狀態檢查"""
        print_header("資料庫狀態診斷")

        try:
            # 檢查資料庫文件
            if not self.db_path:
                print("❌ 找不到任何資料庫文件")
                print("檢查的路徑:")
                for db_path in ["Capital_Official_Framework/multi_group_strategy.db",
                              "Capital_Official_Framework/trading_data.db",
                              "Capital_Official_Framework/strategy_trading.db"]:
                    exists = os.path.exists(db_path)
                    print(f"  - {db_path}: {'存在' if exists else '不存在'}")
                return False

            print(f"✅ 資料庫文件存在: {self.db_path}")

            # 檢查資料庫連接
            with sqlite3.connect(self.db_path, timeout=5.0) as conn:
                cursor = conn.cursor()

                # 檢查問題部位記錄
                print_section("檢查問題部位記錄")
                problem_positions = [133, 134, 135]

                for position_id in problem_positions:
                    cursor.execute('''
                        SELECT id, status, group_id, direction, entry_price,
                               created_at, exit_price, exit_time
                        FROM position_records
                        WHERE id = ?
                    ''', (position_id,))

                    row = cursor.fetchone()
                    if row:
                        print(f"📊 部位{position_id}:")
                        print(f"  - 狀態: {row[1]}")
                        print(f"  - 組ID: {row[2]}")
                        print(f"  - 方向: {row[3]}")
                        print(f"  - 進場價: {row[4]}")
                        print(f"  - 建立時間: {row[5]}")
                        print(f"  - 出場價: {row[6] if row[6] else '未平倉'}")
                        print(f"  - 出場時間: {row[7] if row[7] else '未平倉'}")
                    else:
                        print(f"❌ 部位{position_id}: 記錄不存在")

                # 檢查策略組記錄
                print_section("檢查策略組記錄")
                today = date.today().isoformat()

                cursor.execute('''
                    SELECT id, group_id, date, direction, range_high, range_low
                    FROM strategy_groups
                    WHERE date = ?
                    ORDER BY id DESC
                ''', (today,))

                groups = cursor.fetchall()
                if groups:
                    print(f"📊 今日策略組記錄 ({len(groups)}個):")
                    for group in groups[:5]:  # 只顯示前5個
                        print(f"  - 組{group[1]}: 方向={group[3]}, 高={group[4]}, 低={group[5]}")
                else:
                    print(f"❌ 今日({today})無策略組記錄")

                # 檢查JOIN查詢
                print_section("檢查JOIN查詢邏輯")
                for position_id in problem_positions:
                    cursor.execute('''
                        SELECT pr.id, pr.status, pr.group_id,
                               sg.range_high, sg.range_low, sg.direction as group_direction
                        FROM position_records pr
                        JOIN (
                            SELECT * FROM strategy_groups
                            WHERE date = ?
                            ORDER BY id DESC
                        ) sg ON pr.group_id = sg.group_id
                        WHERE pr.id = ? AND pr.status = 'ACTIVE'
                    ''', (today, position_id))

                    row = cursor.fetchone()
                    if row:
                        print(f"✅ 部位{position_id}: JOIN查詢成功")
                        print(f"  - 狀態: {row[1]}, 組方向: {row[5]}")
                    else:
                        print(f"❌ 部位{position_id}: JOIN查詢失敗")

                        # 分步診斷
                        cursor.execute('SELECT status, group_id FROM position_records WHERE id = ?', (position_id,))
                        pos_info = cursor.fetchone()
                        if pos_info:
                            print(f"  - 部位狀態: {pos_info[0]} (需要ACTIVE)")
                            print(f"  - 部位組ID: {pos_info[1]}")

                            cursor.execute('SELECT COUNT(*) FROM strategy_groups WHERE group_id = ? AND date = ?',
                                         (pos_info[1], today))
                            group_count = cursor.fetchone()[0]
                            print(f"  - 對應策略組: {group_count}個")

                return True

        except sqlite3.Error as e:
            print(f"❌ 資料庫錯誤: {e}")
            return False
        except Exception as e:
            print(f"❌ 診斷錯誤: {e}")
            return False

    def diagnose_async_updater_status(self):
        """診斷2：異步更新器狀態檢查"""
        print_header("異步更新器狀態診斷")

        try:
            # 嘗試導入相關模組
            try:
                from multi_group_position_manager import AsyncDatabaseUpdater
                print("✅ AsyncDatabaseUpdater 模組導入成功")

                # 檢查是否有實例在運行
                # 注意：這需要在實際系統運行時才能檢查
                print("⚠️ 需要在實際系統運行時檢查異步更新器狀態")
                print("建議在 simple_integrated.py 中添加診斷代碼")

            except ImportError as e:
                print(f"❌ AsyncDatabaseUpdater 導入失敗: {e}")

            # 檢查相關文件
            async_files = [
                "Capital_Official_Framework/multi_group_position_manager.py",
                "Capital_Official_Framework/optimized_risk_manager.py",
                "Capital_Official_Framework/simplified_order_tracker.py"
            ]

            print_section("檢查相關文件")
            for file_path in async_files:
                if os.path.exists(file_path):
                    print(f"✅ {file_path}")
                else:
                    print(f"❌ {file_path} 不存在")

            return True

        except Exception as e:
            print(f"❌ 異步更新器診斷錯誤: {e}")
            return False

    def diagnose_lot_level_mechanism(self):
        """診斷3：口級別追價機制檢查"""
        print_header("口級別追價機制診斷")

        try:
            # 檢查SimplifiedOrderTracker
            print_section("檢查SimplifiedOrderTracker")
            try:
                from simplified_order_tracker import SimplifiedOrderTracker, ExitGroup, GlobalExitManager
                print("✅ SimplifiedOrderTracker 模組導入成功")

                # 檢查ExitGroup類
                print("✅ ExitGroup 類導入成功")

                # 檢查GlobalExitManager
                manager = GlobalExitManager()
                print(f"✅ GlobalExitManager 創建成功")
                print(f"  - 鎖定超時: {manager.exit_timeout}秒")
                print(f"  - 當前鎖定數量: {len(manager.exit_locks)}")

            except ImportError as e:
                print(f"❌ SimplifiedOrderTracker 導入失敗: {e}")
                return False

            # 檢查StopLossExecutor整合
            print_section("檢查StopLossExecutor整合")
            try:
                from stop_loss_executor import StopLossExecutor
                print("✅ StopLossExecutor 模組導入成功")

                # 檢查是否有simplified_tracker屬性
                print("⚠️ 需要在實際系統運行時檢查 simplified_tracker 整合")

            except ImportError as e:
                print(f"❌ StopLossExecutor 導入失敗: {e}")

            return True

        except Exception as e:
            print(f"❌ 口級別機制診斷錯誤: {e}")
            return False

    def diagnose_cache_status(self):
        """診斷4：緩存狀態檢查"""
        print_header("緩存狀態診斷")

        try:
            # 檢查OptimizedRiskManager
            print_section("檢查OptimizedRiskManager")
            try:
                from optimized_risk_manager import OptimizedRiskManager
                print("✅ OptimizedRiskManager 模組導入成功")
                print("⚠️ 需要在實際系統運行時檢查緩存狀態:")
                print("  - position_cache 中的部位")
                print("  - stop_loss_cache 中的停損價格")
                print("  - trailing_cache 中的移動停利狀態")

            except ImportError as e:
                print(f"❌ OptimizedRiskManager 導入失敗: {e}")

            return True

        except Exception as e:
            print(f"❌ 緩存狀態診斷錯誤: {e}")
            return False

    def run_full_diagnosis(self):
        """運行完整診斷"""
        print_header("平倉問題完整診斷開始")
        print(f"診斷時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        results = {}

        # 診斷1：資料庫狀態
        results['database'] = self.diagnose_database_status()

        # 診斷2：異步更新器狀態
        results['async_updater'] = self.diagnose_async_updater_status()

        # 診斷3：口級別機制
        results['lot_level'] = self.diagnose_lot_level_mechanism()

        # 診斷4：緩存狀態
        results['cache'] = self.diagnose_cache_status()

        # 總結
        print_header("診斷結果總結")

        success_count = sum(1 for result in results.values() if result)
        total_count = len(results)

        print(f"📊 診斷完成: {success_count}/{total_count} 項通過")

        for category, result in results.items():
            status = "✅ 通過" if result else "❌ 失敗"
            print(f"  - {category}: {status}")

        if success_count == total_count:
            print("\n🎉 所有基礎檢查通過，問題可能在運行時狀態")
            print("建議運行實時診斷工具")
        else:
            print(f"\n⚠️ 發現 {total_count - success_count} 個基礎問題")
            print("建議先修復基礎問題再進行實時診斷")

        return results

def main():
    """主函數"""
    print("🔍 平倉問題診斷工具")
    print("專門診斷異步更新與口級別追價機制問題")

    diagnostics = PlatformDiagnostics()
    results = diagnostics.run_full_diagnosis()

    print(f"\n{'='*60}")
    print("📋 下一步建議:")
    print("1. 如果基礎檢查通過，請運行實時診斷工具")
    print("2. 在 simple_integrated.py 運行時添加診斷代碼")
    print("3. 檢查具體的緩存和異步更新器狀態")
    print("4. 分析LOG中的時序問題")

if __name__ == "__main__":
    main()