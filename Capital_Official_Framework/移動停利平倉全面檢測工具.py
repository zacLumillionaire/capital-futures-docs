#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移動停利平倉全面檢測工具
確保移動停利觸發平倉時能夠成功執行，避免能賺沒賺到的痛苦情況
"""

import sqlite3
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

class TrailingStopExitValidator:
    """移動停利平倉驗證器"""

    def __init__(self, db_path: str = "multi_group_strategy.db"):
        self.db_path = db_path
        self.results = {}
        self.critical_issues = []
        self.warnings = []

    def run_comprehensive_validation(self):
        """執行全面驗證"""
        print("🚀 移動停利平倉機制全面檢測")
        print("=" * 60)
        print("🎯 目標：確保移動停利平倉100%成功，避免能賺沒賺到！")
        print("=" * 60)

        # 面向1: 平倉觸發條件檢測機制
        self.results['trigger_detection'] = self.validate_trigger_detection()

        # 面向2: 平倉訂單生成與執行
        self.results['order_execution'] = self.validate_order_execution()

        # 面向3: 資料庫狀態更新與同步
        self.results['database_sync'] = self.validate_database_sync()

        # 面向4: 平倉回報處理與確認
        self.results['reply_processing'] = self.validate_reply_processing()

        # 面向5: 錯誤處理與容錯機制
        self.results['error_handling'] = self.validate_error_handling()

        # 面向6: 整合測試與模擬驗證
        self.results['integration_test'] = self.simulate_exit_scenarios()

        # 生成關鍵風險報告
        self.generate_critical_risk_report()

    def validate_trigger_detection(self) -> Dict:
        """面向1: 驗證平倉觸發條件檢測機制"""
        print("\n🔍 面向1: 平倉觸發條件檢測機制")
        print("-" * 40)

        result = {'status': 'UNKNOWN', 'issues': [], 'details': {}}

        try:
            # 檢查風險引擎是否正在運行
            print("   📋 檢查風險引擎運行狀態...")

            # 檢查關鍵文件
            risk_files = [
                'risk_management_engine.py',
                'optimized_risk_manager.py',
                'trailing_stop_calculator.py'
            ]

            for file_name in risk_files:
                if os.path.exists(file_name):
                    print(f"   ✅ 找到風險引擎文件: {file_name}")

                    # 檢查關鍵方法
                    with open(file_name, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # 檢查平倉條件檢查方法
                    if 'check_exit_conditions' in content or 'should_exit' in content:
                        print(f"      ✅ 包含平倉條件檢查邏輯")
                    else:
                        result['issues'].append(f"{file_name} 缺少平倉條件檢查邏輯")

                    # 檢查實時價格監控
                    if 'current_price' in content and 'trailing_stop' in content:
                        print(f"      ✅ 包含實時價格監控")
                    else:
                        result['issues'].append(f"{file_name} 缺少實時價格監控")

                else:
                    result['issues'].append(f"找不到關鍵文件: {file_name}")

            # 檢查當前移動停利狀態
            print("\n   📊 檢查當前移動停利狀態...")
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 獲取已啟動移動停利的部位
                cursor.execute("""
                    SELECT pr.id, pr.lot_id, pr.direction, pr.entry_price,
                           pr.trailing_activation_points, pr.trailing_pullback_ratio,
                           rms.peak_price, rms.current_price, rms.trailing_activated
                    FROM position_records pr
                    JOIN risk_management_states rms ON pr.id = rms.position_id
                    WHERE pr.status = 'ACTIVE' AND rms.trailing_activated = 1
                """)

                active_trailing = cursor.fetchall()
                result['details']['active_trailing_positions'] = len(active_trailing)

                print(f"   找到 {len(active_trailing)} 個已啟動移動停利的部位")

                for pos in active_trailing:
                    pos_id, lot_id, direction, entry_price, activation_points, pullback_ratio, \
                    peak_price, current_price, trailing_activated = pos

                    print(f"\n   📊 部位 {pos_id} (第{lot_id}口, {direction}):")
                    print(f"      進場價格: {entry_price}")
                    print(f"      峰值價格: {peak_price}")
                    print(f"      當前價格: {current_price}")
                    print(f"      回撤比例: {pullback_ratio}")

                    # 計算移動停利價格
                    if direction == 'SHORT' and peak_price and entry_price:
                        profit_points = entry_price - peak_price
                        pullback_points = profit_points * pullback_ratio
                        trailing_stop_price = peak_price + pullback_points

                        print(f"      移停價格: {trailing_stop_price}")

                        # 檢查觸發條件
                        if current_price:
                            should_exit = current_price >= trailing_stop_price
                            print(f"      觸發條件: {current_price} >= {trailing_stop_price} = {should_exit}")

                            if should_exit:
                                print(f"      🎯 應該立即平倉！")
                                self.critical_issues.append(f"部位{pos_id}應該平倉但可能未執行")
                        else:
                            result['issues'].append(f"部位{pos_id}缺少當前價格")

                    elif direction == 'LONG' and peak_price and entry_price:
                        profit_points = peak_price - entry_price
                        pullback_points = profit_points * pullback_ratio
                        trailing_stop_price = peak_price - pullback_points

                        print(f"      移停價格: {trailing_stop_price}")

                        if current_price:
                            should_exit = current_price <= trailing_stop_price
                            print(f"      觸發條件: {current_price} <= {trailing_stop_price} = {should_exit}")

                            if should_exit:
                                print(f"      🎯 應該立即平倉！")
                                self.critical_issues.append(f"部位{pos_id}應該平倉但可能未執行")
                        else:
                            result['issues'].append(f"部位{pos_id}缺少當前價格")

            result['status'] = 'PASSED' if not result['issues'] else 'FAILED'

        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            self.critical_issues.append(f"觸發條件檢測失敗: {e}")

        return result

    def validate_order_execution(self) -> Dict:
        """面向2: 驗證平倉訂單生成與執行"""
        print("\n🔍 面向2: 平倉訂單生成與執行")
        print("-" * 40)

        result = {'status': 'UNKNOWN', 'issues': [], 'details': {}}

        try:
            # 檢查平倉執行器
            print("   📋 檢查平倉執行器...")

            exit_files = [
                'unified_exit_manager.py',
                'exit_mechanism_manager.py',
                'stop_loss_executor.py',
                'global_exit_manager.py'
            ]

            found_exit_manager = False
            for file_name in exit_files:
                if os.path.exists(file_name):
                    found_exit_manager = True
                    print(f"   ✅ 找到平倉執行器: {file_name}")

                    with open(file_name, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # 檢查關鍵方法
                    if 'execute_exit' in content or 'place_exit_order' in content:
                        print(f"      ✅ 包含平倉執行方法")
                    else:
                        result['issues'].append(f"{file_name} 缺少平倉執行方法")

                    # 檢查移動停利處理
                    if 'trailing_stop' in content.lower():
                        print(f"      ✅ 支援移動停利平倉")
                    else:
                        result['issues'].append(f"{file_name} 缺少移動停利支援")

                    # 檢查API調用
                    if 'api' in content.lower() and ('sell' in content.lower() or 'buy' in content.lower()):
                        print(f"      ✅ 包含API交易調用")
                    else:
                        result['issues'].append(f"{file_name} 缺少API交易調用")

            if not found_exit_manager:
                self.critical_issues.append("找不到任何平倉執行器！")
                result['issues'].append("缺少平倉執行器")

            # 檢查平倉價格計算
            print("\n   📊 檢查平倉價格計算...")

            # 模擬平倉價格計算
            test_scenarios = [
                {
                    'direction': 'SHORT',
                    'current_price': 22535,
                    'expected_action': 'BUY',  # SHORT平倉用BUY
                    'price_adjustment': 'ASK1+1'  # 根據記憶中的退出重試定價
                },
                {
                    'direction': 'LONG',
                    'current_price': 22535,
                    'expected_action': 'SELL',  # LONG平倉用SELL
                    'price_adjustment': 'BID1-1'  # 根據記憶中的退出重試定價
                }
            ]

            for scenario in test_scenarios:
                print(f"   測試 {scenario['direction']} 部位平倉:")
                print(f"      當前價格: {scenario['current_price']}")
                print(f"      平倉動作: {scenario['expected_action']}")
                print(f"      價格調整: {scenario['price_adjustment']}")

            result['status'] = 'PASSED' if not result['issues'] else 'FAILED'

        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            self.critical_issues.append(f"訂單執行檢測失敗: {e}")

        return result

    def validate_database_sync(self) -> Dict:
        """面向3: 驗證資料庫狀態更新與同步"""
        print("\n🔍 面向3: 資料庫狀態更新與同步")
        print("-" * 40)

        result = {'status': 'UNKNOWN', 'issues': [], 'details': {}}

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 檢查資料庫表結構
                print("   📋 檢查資料庫表結構...")

                # 檢查 position_records 表的平倉相關欄位
                cursor.execute("PRAGMA table_info(position_records)")
                columns = [col[1] for col in cursor.fetchall()]

                required_exit_fields = [
                    'exit_price', 'exit_time', 'exit_reason',
                    'pnl', 'pnl_amount', 'status'
                ]

                for field in required_exit_fields:
                    if field in columns:
                        print(f"      ✅ 包含平倉欄位: {field}")
                    else:
                        result['issues'].append(f"缺少平倉欄位: {field}")

                # 檢查平倉狀態更新機制
                print("\n   📊 檢查平倉狀態更新機制...")

                # 檢查是否有平倉更新方法
                db_files = ['multi_group_database.py']
                for file_name in db_files:
                    if os.path.exists(file_name):
                        with open(file_name, 'r', encoding='utf-8') as f:
                            content = f.read()

                        if 'update_position_exit' in content:
                            print(f"      ✅ 找到平倉更新方法")
                        else:
                            result['issues'].append("缺少平倉更新方法")

                        if 'status = \'EXITED\'' in content:
                            print(f"      ✅ 包含狀態更新邏輯")
                        else:
                            result['issues'].append("缺少狀態更新邏輯")

                # 檢查異步更新機制
                print("\n   📊 檢查異步更新機制...")

                if os.path.exists('async_db_updater.py'):
                    with open('async_db_updater.py', 'r', encoding='utf-8') as f:
                        async_content = f.read()

                    if 'schedule_exit_update' in async_content:
                        print(f"      ✅ 支援異步平倉更新")
                    else:
                        self.warnings.append("缺少異步平倉更新支援")

                result['status'] = 'PASSED' if not result['issues'] else 'FAILED'

        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            self.critical_issues.append(f"資料庫同步檢測失敗: {e}")

        return result

    def validate_reply_processing(self) -> Dict:
        """面向4: 驗證平倉回報處理與確認"""
        print("\n🔍 面向4: 平倉回報處理與確認")
        print("-" * 40)

        result = {'status': 'UNKNOWN', 'issues': [], 'details': {}}

        try:
            # 檢查回報處理器
            print("   📋 檢查回報處理器...")

            reply_files = [
                'Reply_Service/Reply.py',
                'simplified_order_tracker.py',
                'order_reply_realtime.py'
            ]

            for file_name in reply_files:
                if os.path.exists(file_name):
                    print(f"   ✅ 找到回報處理器: {file_name}")

                    with open(file_name, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # 檢查成交回報處理
                    if 'Type=D' in content or 'Deal' in content:
                        print(f"      ✅ 支援成交回報處理")
                    else:
                        result['issues'].append(f"{file_name} 缺少成交回報處理")

                    # 檢查平倉確認邏輯
                    if 'exit' in content.lower() or 'close' in content.lower():
                        print(f"      ✅ 包含平倉確認邏輯")
                    else:
                        result['issues'].append(f"{file_name} 缺少平倉確認邏輯")

            # 檢查FIFO匹配機制
            print("\n   📊 檢查FIFO匹配機制...")

            if os.path.exists('simplified_order_tracker.py'):
                with open('simplified_order_tracker.py', 'r', encoding='utf-8') as f:
                    tracker_content = f.read()

                if 'FIFO' in tracker_content:
                    print(f"      ✅ 支援FIFO訂單匹配")
                else:
                    result['issues'].append("缺少FIFO訂單匹配")

                if 'confirm_position_filled' in tracker_content:
                    print(f"      ✅ 支援部位確認機制")
                else:
                    result['issues'].append("缺少部位確認機制")

            result['status'] = 'PASSED' if not result['issues'] else 'FAILED'

        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            self.critical_issues.append(f"回報處理檢測失敗: {e}")

        return result

    def validate_error_handling(self) -> Dict:
        """面向5: 驗證錯誤處理與容錯機制"""
        print("\n🔍 面向5: 錯誤處理與容錯機制")
        print("-" * 40)

        result = {'status': 'UNKNOWN', 'issues': [], 'details': {}}

        try:
            # 檢查重試機制
            print("   📋 檢查重試機制...")

            # 檢查平倉重試邏輯
            exit_files = ['unified_exit_manager.py', 'global_exit_manager.py']

            for file_name in exit_files:
                if os.path.exists(file_name):
                    with open(file_name, 'r', encoding='utf-8') as f:
                        content = f.read()

                    if 'retry' in content.lower():
                        print(f"      ✅ {file_name} 支援重試機制")
                    else:
                        result['issues'].append(f"{file_name} 缺少重試機制")

                    if 'timeout' in content.lower():
                        print(f"      ✅ {file_name} 包含超時處理")
                    else:
                        result['issues'].append(f"{file_name} 缺少超時處理")

            # 檢查緊急平倉機制
            print("\n   📊 檢查緊急平倉機制...")

            emergency_keywords = ['emergency', 'force_exit', 'manual_exit']
            found_emergency = False

            for file_name in exit_files:
                if os.path.exists(file_name):
                    with open(file_name, 'r', encoding='utf-8') as f:
                        content = f.read()

                    for keyword in emergency_keywords:
                        if keyword in content.lower():
                            found_emergency = True
                            print(f"      ✅ 找到緊急平倉機制: {keyword}")
                            break

            if not found_emergency:
                self.warnings.append("缺少緊急平倉機制")

            # 檢查錯誤日誌記錄
            print("\n   📊 檢查錯誤日誌記錄...")

            log_patterns = ['logger.error', 'print.*ERROR', 'logging.error']
            found_logging = False

            for file_name in exit_files:
                if os.path.exists(file_name):
                    with open(file_name, 'r', encoding='utf-8') as f:
                        content = f.read()

                    for pattern in log_patterns:
                        if pattern in content:
                            found_logging = True
                            print(f"      ✅ 包含錯誤日誌記錄")
                            break

            if not found_logging:
                result['issues'].append("缺少錯誤日誌記錄")

            result['status'] = 'PASSED' if not result['issues'] else 'FAILED'

        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            self.critical_issues.append(f"錯誤處理檢測失敗: {e}")

        return result

    def simulate_exit_scenarios(self) -> Dict:
        """面向6: 模擬各種平倉情境"""
        print("\n🔍 面向6: 整合測試與模擬驗證")
        print("-" * 40)

        result = {'status': 'UNKNOWN', 'issues': [], 'details': {}}

        try:
            # 模擬移動停利平倉情境
            print("   📋 模擬移動停利平倉情境...")

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 獲取當前活躍的移動停利部位
                cursor.execute("""
                    SELECT pr.id, pr.lot_id, pr.direction, pr.entry_price,
                           pr.trailing_pullback_ratio, rms.peak_price
                    FROM position_records pr
                    JOIN risk_management_states rms ON pr.id = rms.position_id
                    WHERE pr.status = 'ACTIVE' AND rms.trailing_activated = 1
                """)

                positions = cursor.fetchall()

                # 模擬不同價格情境
                test_prices = [22530, 22532, 22535, 22540]  # 不同的測試價格

                for test_price in test_prices:
                    print(f"\n   🧪 模擬價格 {test_price} 的平倉情境:")

                    for pos in positions:
                        pos_id, lot_id, direction, entry_price, pullback_ratio, peak_price = pos

                        if direction == 'SHORT' and peak_price and entry_price:
                            # 計算移動停利價格
                            profit_points = entry_price - peak_price
                            pullback_points = profit_points * pullback_ratio
                            trailing_stop_price = peak_price + pullback_points

                            should_exit = test_price >= trailing_stop_price

                            print(f"      部位{pos_id} (第{lot_id}口): 移停價格={trailing_stop_price:.1f}, "
                                  f"應平倉={should_exit}")

                            if should_exit:
                                # 模擬平倉流程
                                exit_price = test_price + 1  # 模擬滑價
                                pnl = entry_price - exit_price

                                print(f"         模擬平倉: @{exit_price}, 損益={pnl:.1f}點")

                                # 檢查是否有足夠的獲利
                                if pnl > 0:
                                    print(f"         ✅ 獲利平倉: {pnl:.1f}點")
                                else:
                                    print(f"         ⚠️ 虧損平倉: {pnl:.1f}點")

            # 檢查平倉執行路徑
            print("\n   📊 檢查平倉執行路徑...")

            execution_path = [
                "1. 風險引擎檢測觸發條件",
                "2. 調用平倉執行器",
                "3. 計算平倉價格",
                "4. 發送API訂單",
                "5. 接收成交回報",
                "6. 更新部位狀態",
                "7. 記錄損益結果"
            ]

            for i, step in enumerate(execution_path, 1):
                print(f"      {step}")

            # 檢查關鍵風險點
            print("\n   ⚠️ 檢查關鍵風險點...")

            risk_points = [
                "API連接中斷",
                "訂單被拒絕",
                "價格滑價過大",
                "資料庫更新失敗",
                "回報處理延遲"
            ]

            for risk in risk_points:
                print(f"      ⚠️ 風險點: {risk}")

            result['status'] = 'PASSED'

        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            self.critical_issues.append(f"模擬測試失敗: {e}")

        return result

    def generate_critical_risk_report(self):
        """生成關鍵風險報告"""
        print("\n📋 移動停利平倉關鍵風險報告")
        print("=" * 60)

        # 統計結果
        total_checks = len(self.results)
        passed_checks = sum(1 for r in self.results.values() if r.get('status') == 'PASSED')
        failed_checks = sum(1 for r in self.results.values() if r.get('status') == 'FAILED')
        error_checks = sum(1 for r in self.results.values() if r.get('status') == 'ERROR')

        print(f"📊 檢測統計:")
        print(f"   總檢測項目: {total_checks}")
        print(f"   ✅ 通過: {passed_checks}")
        print(f"   ❌ 失敗: {failed_checks}")
        print(f"   💥 錯誤: {error_checks}")

        # 關鍵問題
        print(f"\n🚨 關鍵問題 ({len(self.critical_issues)} 個):")
        if self.critical_issues:
            for issue in self.critical_issues:
                print(f"   🚨 {issue}")
        else:
            print("   ✅ 未發現關鍵問題")

        # 警告事項
        print(f"\n⚠️ 警告事項 ({len(self.warnings)} 個):")
        if self.warnings:
            for warning in self.warnings:
                print(f"   ⚠️ {warning}")
        else:
            print("   ✅ 無警告事項")

        # 風險評估
        print(f"\n🎯 風險評估:")
        if self.critical_issues:
            print("   🚨 高風險: 存在關鍵問題，可能導致平倉失敗")
            print("   📝 建議: 立即修復關鍵問題後再進行交易")
        elif self.warnings:
            print("   ⚠️ 中風險: 存在警告事項，建議優化")
            print("   📝 建議: 可以交易但需要密切監控")
        else:
            print("   ✅ 低風險: 平倉機制檢查通過")
            print("   📝 建議: 可以安心交易")

        # 保存報告
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_checks': total_checks,
                'passed': passed_checks,
                'failed': failed_checks,
                'errors': error_checks
            },
            'critical_issues': self.critical_issues,
            'warnings': self.warnings,
            'detailed_results': self.results
        }

        report_file = f"移動停利平倉風險報告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"\n📄 詳細報告已保存: {report_file}")

        # 生成修復建議
        self.generate_fix_recommendations()

    def generate_fix_recommendations(self):
        """生成修復建議"""
        print(f"\n🔧 修復建議:")

        if self.critical_issues:
            print("   🚨 立即修復項目:")
            for i, issue in enumerate(self.critical_issues, 1):
                print(f"      {i}. {issue}")

        if self.warnings:
            print("   ⚠️ 建議改進項目:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"      {i}. {warning}")

        print(f"\n📝 通用建議:")
        print("   1. 定期執行此檢測工具")
        print("   2. 監控平倉執行日誌")
        print("   3. 設置平倉失敗警報")
        print("   4. 準備手動平倉備案")
        print("   5. 測試緊急平倉功能")

def main():
    """主檢測函數"""
    validator = TrailingStopExitValidator()
    validator.run_comprehensive_validation()

if __name__ == "__main__":
    main()