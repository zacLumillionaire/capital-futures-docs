#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新程式碼審查資料夾腳本
自動生成於: 2025-07-16 22:35:09
更新於: 2025-07-16 22:45:00 - 添加排除功能
"""

import os
import shutil
from pathlib import Path

def should_exclude_file(file_path):
    """檢查檔案是否應該被排除"""
    file_name = os.path.basename(file_path)

    # 排除 test 開頭的檔案
    if file_name.lower().startswith('test'):
        return True, f"排除 test 開頭檔案: {file_name}"

    # 排除 json 檔案
    if file_name.lower().endswith('.json'):
        return True, f"排除 JSON 檔案: {file_name}"

    return False, ""

def update_review_folder():
    """更新程式碼審查資料夾"""
    
    # 檔案清單
    source_files = ['Capital_Official_Framework\\async_db_updater.py', 'Capital_Official_Framework\\async_failure_diagnostic.py', 'Capital_Official_Framework\\check_database_and_cleanup.py', 'Capital_Official_Framework\\check_database_status.py', 'Capital_Official_Framework\\check_log_fix.py', 'Capital_Official_Framework\\check_position_records_constraints.py', 'Capital_Official_Framework\\check_table_schema.py', 'Capital_Official_Framework\\cleanup_test_positions.py', 'Capital_Official_Framework\\cumulative_profit_protection_manager.py', 'Capital_Official_Framework\\drawdown_monitor.py', 'Capital_Official_Framework\\exit_mechanism_config.py', 'Capital_Official_Framework\\exit_mechanism_database_extension.py', 'Capital_Official_Framework\\exit_mechanism_manager.py', 'Capital_Official_Framework\\exit_order_tracker.py', 'Capital_Official_Framework\\fifo_order_matcher.py', 'Capital_Official_Framework\\final_fixed_verification.db', 'Capital_Official_Framework\\final_fixed_verification.py', 'Capital_Official_Framework\\ghost_loop_fix_verification_test.py', 'Capital_Official_Framework\\initial_stop_loss_manager.py', 'Capital_Official_Framework\\multi_group_config.py', 'Capital_Official_Framework\\multi_group_console_logger.py', 'Capital_Official_Framework\\multi_group_database.py', 'Capital_Official_Framework\\multi_group_position_manager.py', 'Capital_Official_Framework\\multi_group_strategy.db', 'Capital_Official_Framework\\multi_group_strategy_backup_20250707_132600.db', 'Capital_Official_Framework\\multi_group_ui_panel.py', 'Capital_Official_Framework\\optimized_risk_manager.py', 'Capital_Official_Framework\\order_mode_config.json', 'Capital_Official_Framework\\order_mode_ui_controller.py', 'Capital_Official_Framework\\order_service\\Global.py', 'Capital_Official_Framework\\peak_price_tracker.py', 'Capital_Official_Framework\\position_manager_id_verifier.py', 'Capital_Official_Framework\\quick_async_check.py', 'Capital_Official_Framework\\quick_db_check.py', 'Capital_Official_Framework\\real_time_quote_manager.py', 'Capital_Official_Framework\\risk_management_engine.py', 'Capital_Official_Framework\\simple_integrated.py', 'Capital_Official_Framework\\simple_table_check.py', 'Capital_Official_Framework\\simple_test.db', 'Capital_Official_Framework\\simple_test_data_source.db', 'Capital_Official_Framework\\simple_validation_test.db', 'Capital_Official_Framework\\simplified_order_tracker.py', 'Capital_Official_Framework\\stop_loss_executor.py', 'Capital_Official_Framework\\stop_loss_monitor.py', 'Capital_Official_Framework\\stop_loss_state_manager.py', 'Capital_Official_Framework\\strategy_trading.db', 'Capital_Official_Framework\\system_health_monitor.py', 'Capital_Official_Framework\\system_maintenance_manager.py', 'Capital_Official_Framework\\test_api_fix_verification.py', 'Capital_Official_Framework\\test_async_performance.db', 'Capital_Official_Framework\\test_cache.db', 'Capital_Official_Framework\\test_callback_fix.db', 'Capital_Official_Framework\\test_concurrent.db', 'Capital_Official_Framework\\test_config.db', 'Capital_Official_Framework\\test_connection_fix.db', 'Capital_Official_Framework\\test_data_inconsistency.db', 'Capital_Official_Framework\\test_distributed_perf.db', 'Capital_Official_Framework\\test_final_fix_verification.py', 'Capital_Official_Framework\\test_fix_verification.db', 'Capital_Official_Framework\\test_fix_verification.py', 'Capital_Official_Framework\\test_get_group_positions.db', 'Capital_Official_Framework\\test_gil_fix_verification.py', 'Capital_Official_Framework\\test_group_fix.db', 'Capital_Official_Framework\\test_integration.db', 'Capital_Official_Framework\\test_log_freq.db', 'Capital_Official_Framework\\test_optimized_risk.db', 'Capital_Official_Framework\\test_simple_fix_verification.py', 'Capital_Official_Framework\\test_stop_loss_fix.db', 'Capital_Official_Framework\\test_stop_loss_flow.db', 'Capital_Official_Framework\\test_task2_data_flow.db', 'Capital_Official_Framework\\test_task3_simplification.db', 'Capital_Official_Framework\\test_task4_async_consistency.db', 'Capital_Official_Framework\\test_task5_end_to_end.db', 'Capital_Official_Framework\\test_task5_end_to_end_verification.py', 'Capital_Official_Framework\\test_temp.db', 'Capital_Official_Framework\\test_trailing_calc.db', 'Capital_Official_Framework\\test_trailing_integration.db', 'Capital_Official_Framework\\test_trailing_retry.db', 'Capital_Official_Framework\\test_unified_perf.db', 'Capital_Official_Framework\\test_unified_risk.db', 'Capital_Official_Framework\\test_verification.db', 'Capital_Official_Framework\\test_virtual_strategy.db', 'Capital_Official_Framework\\total_lot_manager.py', 'Capital_Official_Framework\\total_lot_tracker.py', 'Capital_Official_Framework\\trailing_stop_activator.py', 'Capital_Official_Framework\\trailing_stop_calculator.py', 'Capital_Official_Framework\\ultimate_fix_verification.db', 'Capital_Official_Framework\\ultimate_fix_verification.py', 'Capital_Official_Framework\\unified_exit_manager.py', 'Capital_Official_Framework\\unified_order_tracker.py', 'Capital_Official_Framework\\user_config.py', 'Capital_Official_Framework\\virtual_real_order_manager.py', 'Capital_Official_Framework\\virtual_simple_integrated.py', 'Capital_Official_Framework\\保護性停損檢查報告_20250714_233946.json', 'Capital_Official_Framework\\保護性停損檢查報告_20250715_001240.json', 'Capital_Official_Framework\\保護性停損檢查報告_20250715_001333.json', 'Capital_Official_Framework\\保護性停損檢查報告_20250715_065924.json', 'Capital_Official_Framework\\保護性停損檢測報告_20250715_004001.json', 'Capital_Official_Framework\\全流程檢測工具.py', 'Capital_Official_Framework\\多角度資料庫診斷工具.py', 'Capital_Official_Framework\\快速診斷.py', 'Capital_Official_Framework\\移動停利問題診斷.json', 'Capital_Official_Framework\\移動停利平倉診斷工具.py', 'Capital_Official_Framework\\移動停利平倉關鍵問題診斷.py', 'Capital_Official_Framework\\移動停利平倉風險報告_20250714_231753.json', 'Capital_Official_Framework\\移動停利診斷報告_20250714_225457.json', 'Capital_Official_Framework\\簡單診斷.py', 'Capital_Official_Framework\\虛擬報價機\\Global.py', 'Capital_Official_Framework\\虛擬報價機\\README.md', 'Capital_Official_Framework\\虛擬報價機\\__init__.py', 'Capital_Official_Framework\\虛擬報價機\\__pycache__\\Global.cpython-311.pyc', 'Capital_Official_Framework\\虛擬報價機\\__pycache__\\__init__.cpython-311.pyc', 'Capital_Official_Framework\\虛擬報價機\\__pycache__\\config_manager.cpython-311.pyc', 'Capital_Official_Framework\\虛擬報價機\\__pycache__\\event_dispatcher.cpython-311.pyc', 'Capital_Official_Framework\\虛擬報價機\\__pycache__\\order_simulator.cpython-311.pyc', 'Capital_Official_Framework\\虛擬報價機\\__pycache__\\quote_engine.cpython-311.pyc', 'Capital_Official_Framework\\虛擬報價機\\__pycache__\\simple_virtual_quote.cpython-311.pyc', 'Capital_Official_Framework\\虛擬報價機\\config.json', 'Capital_Official_Framework\\虛擬報價機\\config_backups\\config_backup_20250716_025515.json', 'Capital_Official_Framework\\虛擬報價機\\config_backups\\config_backup_20250716_025522.json', 'Capital_Official_Framework\\虛擬報價機\\config_backups\\config_backup_20250716_104314.json', 'Capital_Official_Framework\\虛擬報價機\\config_entry_chase.json', 'Capital_Official_Framework\\虛擬報價機\\config_entry_test.json', 'Capital_Official_Framework\\虛擬報價機\\config_manager.py', 'Capital_Official_Framework\\虛擬報價機\\config_stop_chase.json', 'Capital_Official_Framework\\虛擬報價機\\config_stop_loss.json', 'Capital_Official_Framework\\虛擬報價機\\config_stress_test.json', 'Capital_Official_Framework\\虛擬報價機\\config_trailing_stop.json', 'Capital_Official_Framework\\虛擬報價機\\event_dispatcher.py', 'Capital_Official_Framework\\虛擬報價機\\order_simulator.py', 'Capital_Official_Framework\\虛擬報價機\\quick_switch.bat', 'Capital_Official_Framework\\虛擬報價機\\quote_engine.py', 'Capital_Official_Framework\\虛擬報價機\\simple_virtual_quote.py', 'Capital_Official_Framework\\虛擬報價機\\switch_config.py', 'Capital_Official_Framework\\虛擬報價機\\test_simple.py', 'Capital_Official_Framework\\虛擬報價機\\test_virtual_quote_machine.py', 'Capital_Official_Framework\\虛擬報價機\\使用說明.md', 'Capital_Official_Framework\\虛擬報價機\\配置使用說明.md', 'Capital_Official_Framework\\診斷移動停利問題.py', 'Capital_Official_Framework\\診斷部位150.py', 'check_database_rules.py', 'check_database_status.py', 'id_consistency_verifier.py', '實時診斷代碼片段.py', '平倉問題診斷工具.py', '簡化診斷.py']
    
    target_base_dir = Path(__file__).parent
    print(f"📁 更新目標資料夾: {target_base_dir}")
    print("🚫 排除規則: test開頭檔案 + JSON檔案")

    copied_count = 0
    failed_count = 0
    skipped_count = 0
    excluded_count = 0

    for source_path in source_files:
        try:
            source_file = Path("../..") / source_path

            # 檢查檔案是否應該被排除
            should_exclude, exclude_reason = should_exclude_file(source_path)
            if should_exclude:
                print(f"🚫 {exclude_reason}")
                excluded_count += 1
                continue

            if not source_file.exists():
                print(f"⚠️ 來源檔案不存在: {source_path}")
                skipped_count += 1
                continue

            # 計算相對路徑
            if source_path.startswith("Capital_Official_Framework"):
                relative_path = source_path[len("Capital_Official_Framework"):].lstrip(os.sep)
            else:
                relative_path = os.path.join("root_files", os.path.basename(source_path))

            target_path = target_base_dir / relative_path
            target_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy2(source_file, target_path)
            print(f"✅ 已更新: {relative_path}")
            copied_count += 1

        except Exception as e:
            print(f"❌ 更新失敗 {source_path}: {e}")
            failed_count += 1

    print(f"\n📊 更新完成統計:")
    print(f"   ✅ 成功複製: {copied_count} 個檔案")
    print(f"   🚫 排除檔案: {excluded_count} 個檔案")
    print(f"   ⚠️ 跳過檔案: {skipped_count} 個檔案")
    print(f"   ❌ 失敗檔案: {failed_count} 個檔案")

if __name__ == "__main__":
    update_review_folder()
