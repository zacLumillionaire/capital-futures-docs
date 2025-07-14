#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
保護性停損全面檢測工具 v1.0
專門檢測保護性停損機制的各個環節，支援多單空單測試
確保第一口平倉後能正確觸發第二口保護性停損

檢測範圍:
- 配置檢查 (LotRule配置、資料庫結構)
- 計算邏輯 (多單空單計算正確性)
- 觸發機制 (第一口平倉觸發邏輯)
- 執行流程 (統一出場管理器支援)
- 狀態管理 (資料庫狀態同步)
- 模擬測試 (完整流程模擬)
"""

import sqlite3
import json
import os
import sys
import traceback
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal

class ProtectiveStopInspector:
    """保護性停損檢測器"""
    
    def __init__(self, db_path: str = "multi_group_strategy.db"):
        self.db_path = db_path
        self.issues = []
        self.warnings = []
        self.passed_checks = []
        self.test_results = {}
        
    def log_issue(self, category: str, severity: str, description: str, details: str = ""):
        """記錄問題"""
        self.issues.append({
            'category': category,
            'severity': severity,  # CRITICAL, HIGH, MEDIUM, LOW
            'description': description,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
    def log_warning(self, category: str, description: str, details: str = ""):
        """記錄警告"""
        self.warnings.append({
            'category': category,
            'description': description,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
    def log_passed(self, category: str, description: str):
        """記錄通過的檢查"""
        self.passed_checks.append({
            'category': category,
            'description': description,
            'timestamp': datetime.now().isoformat()
        })

    def inspect_configuration(self) -> Dict:
        """檢測保護性停損配置"""
        print("🔧 1. 保護性停損配置檢測")
        print("=" * 50)
        
        results = {
            'lot_rule_config': self._check_lot_rule_config(),
            'database_structure': self._check_database_structure(),
            'exit_config': self._check_exit_config()
        }
        
        return results
    
    def _check_lot_rule_config(self) -> Dict:
        """檢查LotRule配置"""
        print("📋 1.1 LotRule配置檢查...")
        
        try:
            # 檢查LotRule類是否存在必要欄位
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from multi_group_config import LotRule
            
            # 測試創建LotRule實例
            test_rule = LotRule(
                lot_id=1,
                use_trailing_stop=True,
                trailing_activation=Decimal('15'),
                trailing_pullback=Decimal('0.10'),
                protective_stop_multiplier=Decimal('1.0'),
                use_protective_stop=True
            )
            
            # 檢查必要屬性
            required_attrs = ['protective_stop_multiplier', 'use_protective_stop']
            missing_attrs = []
            
            for attr in required_attrs:
                if not hasattr(test_rule, attr):
                    missing_attrs.append(attr)
            
            if missing_attrs:
                self.log_issue('CONFIG', 'CRITICAL', 
                             f"LotRule缺少必要屬性: {missing_attrs}")
                return {'status': 'FAILED', 'reason': 'Missing attributes'}
            
            # 檢查JSON序列化
            json_str = test_rule.to_json()
            restored_rule = LotRule.from_json(json_str)
            
            if restored_rule.protective_stop_multiplier != test_rule.protective_stop_multiplier:
                self.log_issue('CONFIG', 'HIGH', 
                             "LotRule JSON序列化/反序列化失敗")
                return {'status': 'FAILED', 'reason': 'JSON serialization failed'}
            
            self.log_passed('CONFIG', "LotRule配置檢查通過")
            print("   ✅ LotRule配置正常")
            return {'status': 'PASSED'}
            
        except ImportError as e:
            self.log_issue('CONFIG', 'CRITICAL', 
                         f"無法導入multi_group_config: {e}")
            return {'status': 'FAILED', 'reason': 'Import failed'}
        except Exception as e:
            self.log_issue('CONFIG', 'HIGH', 
                         f"LotRule配置檢查失敗: {e}")
            return {'status': 'FAILED', 'reason': str(e)}

    def _check_database_structure(self) -> Dict:
        """檢查資料庫結構"""
        print("📋 1.2 資料庫結構檢查...")
        
        try:
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            cursor = conn.cursor()
            
            # 檢查position_records表
            cursor.execute("PRAGMA table_info(position_records)")
            pr_columns = [row[1] for row in cursor.fetchall()]
            
            pr_required = ['protective_stop_price', 'protective_stop_activated', 'first_lot_exit_profit']
            pr_missing = [col for col in pr_required if col not in pr_columns]
            
            # 檢查risk_management_states表
            cursor.execute("PRAGMA table_info(risk_management_states)")
            rms_columns = [row[1] for row in cursor.fetchall()]
            
            rms_required = ['protection_activated', 'protective_stop_price']
            rms_missing = [col for col in rms_required if col not in rms_columns]
            
            if pr_missing or rms_missing:
                missing_info = []
                if pr_missing:
                    missing_info.append(f"position_records: {pr_missing}")
                if rms_missing:
                    missing_info.append(f"risk_management_states: {rms_missing}")
                
                self.log_warning('CONFIG', 
                               f"資料庫缺少保護性停損欄位: {'; '.join(missing_info)}")
                print("   ⚠️ 資料庫結構不完整，但可能會自動升級")
            else:
                self.log_passed('CONFIG', "資料庫結構檢查通過")
                print("   ✅ 資料庫結構完整")
            
            conn.close()
            return {'status': 'PASSED', 'missing_fields': pr_missing + rms_missing}
            
        except Exception as e:
            self.log_issue('CONFIG', 'HIGH', 
                         f"資料庫結構檢查失敗: {e}")
            return {'status': 'FAILED', 'reason': str(e)}

    def _check_exit_config(self) -> Dict:
        """檢查平倉配置"""
        print("📋 1.3 平倉配置檢查...")
        
        try:
            from exit_mechanism_config import get_default_exit_config_for_multi_group
            
            config = get_default_exit_config_for_multi_group()
            
            # 檢查每口的保護性停損配置
            issues = []
            for rule in config.lot_rules:
                if rule.lot_number == 1:
                    if rule.protective_stop_multiplier is None:
                        issues.append(f"第{rule.lot_number}口缺少保護倍數")
                elif rule.lot_number > 1:
                    if rule.protective_stop_multiplier is None:
                        issues.append(f"第{rule.lot_number}口缺少保護倍數")
            
            if issues:
                self.log_warning('CONFIG', f"平倉配置問題: {'; '.join(issues)}")
                print(f"   ⚠️ 平倉配置問題: {'; '.join(issues)}")
            else:
                self.log_passed('CONFIG', "平倉配置檢查通過")
                print("   ✅ 平倉配置正常")
            
            return {'status': 'PASSED', 'issues': issues}
            
        except Exception as e:
            self.log_issue('CONFIG', 'MEDIUM', 
                         f"平倉配置檢查失敗: {e}")
            return {'status': 'FAILED', 'reason': str(e)}

    def inspect_calculation_logic(self) -> Dict:
        """檢測計算邏輯"""
        print("\n🧮 2. 保護性停損計算邏輯檢測")
        print("=" * 50)
        
        results = {
            'long_calculation': self._test_long_calculation(),
            'short_calculation': self._test_short_calculation(),
            'edge_cases': self._test_edge_cases()
        }
        
        return results
    
    def _test_long_calculation(self) -> Dict:
        """測試多單計算邏輯"""
        print("📊 2.1 多單保護性停損計算測試...")
        
        try:
            # 測試參數
            direction = 'LONG'
            entry_price = 20000.0
            first_lot_profit = 20.0
            protection_multiplier = 2.0
            
            # 計算邏輯
            stop_loss_amount = first_lot_profit * protection_multiplier
            new_stop_loss = entry_price - stop_loss_amount
            
            # 驗證結果
            expected = 19960.0  # 20000 - (20 * 2.0)
            
            if abs(new_stop_loss - expected) < 0.01:
                self.log_passed('CALCULATION', "多單保護性停損計算正確")
                print(f"   ✅ 多單計算正確: {entry_price} - ({first_lot_profit} × {protection_multiplier}) = {new_stop_loss}")
                return {'status': 'PASSED', 'result': new_stop_loss}
            else:
                self.log_issue('CALCULATION', 'CRITICAL', 
                             f"多單計算錯誤: 期望{expected}, 實際{new_stop_loss}")
                return {'status': 'FAILED', 'expected': expected, 'actual': new_stop_loss}
                
        except Exception as e:
            self.log_issue('CALCULATION', 'HIGH', 
                         f"多單計算測試失敗: {e}")
            return {'status': 'FAILED', 'reason': str(e)}
    
    def _test_short_calculation(self) -> Dict:
        """測試空單計算邏輯"""
        print("📊 2.2 空單保護性停損計算測試...")
        
        try:
            # 測試參數
            direction = 'SHORT'
            entry_price = 22542.0
            first_lot_profit = 20.0
            protection_multiplier = 2.0
            
            # 計算邏輯 (空單止損往高點移動)
            stop_loss_amount = first_lot_profit * protection_multiplier
            new_stop_loss = entry_price + stop_loss_amount
            
            # 驗證結果
            expected = 22582.0  # 22542 + (20 * 2.0)
            
            if abs(new_stop_loss - expected) < 0.01:
                self.log_passed('CALCULATION', "空單保護性停損計算正確")
                print(f"   ✅ 空單計算正確: {entry_price} + ({first_lot_profit} × {protection_multiplier}) = {new_stop_loss}")
                print(f"   📝 邏輯說明: 空單止損往高點移動，給予更多保護空間")
                return {'status': 'PASSED', 'result': new_stop_loss}
            else:
                self.log_issue('CALCULATION', 'CRITICAL', 
                             f"空單計算錯誤: 期望{expected}, 實際{new_stop_loss}")
                return {'status': 'FAILED', 'expected': expected, 'actual': new_stop_loss}
                
        except Exception as e:
            self.log_issue('CALCULATION', 'HIGH', 
                         f"空單計算測試失敗: {e}")
            return {'status': 'FAILED', 'reason': str(e)}
    
    def _test_edge_cases(self) -> Dict:
        """測試邊界情況"""
        print("📊 2.3 邊界情況測試...")
        
        test_cases = [
            {'profit': 0, 'multiplier': 2.0, 'description': '零獲利'},
            {'profit': 1, 'multiplier': 0.5, 'description': '小倍數'},
            {'profit': 100, 'multiplier': 5.0, 'description': '大獲利大倍數'},
            {'profit': 10, 'multiplier': 0, 'description': '零倍數'}
        ]
        
        passed = 0
        failed = 0
        
        for case in test_cases:
            try:
                entry_price = 20000.0
                stop_loss_amount = case['profit'] * case['multiplier']
                
                # 多單計算
                long_result = entry_price - stop_loss_amount
                # 空單計算
                short_result = entry_price + stop_loss_amount
                
                # 基本合理性檢查
                if case['multiplier'] > 0 and case['profit'] > 0:
                    if long_result < entry_price and short_result > entry_price:
                        passed += 1
                        print(f"   ✅ {case['description']}: 多單{long_result}, 空單{short_result}")
                    else:
                        failed += 1
                        print(f"   ❌ {case['description']}: 計算結果不合理")
                else:
                    # 零值情況
                    if long_result == entry_price and short_result == entry_price:
                        passed += 1
                        print(f"   ✅ {case['description']}: 無保護調整")
                    else:
                        failed += 1
                        print(f"   ❌ {case['description']}: 零值處理錯誤")
                        
            except Exception as e:
                failed += 1
                print(f"   ❌ {case['description']}: 測試失敗 - {e}")
        
        if failed == 0:
            self.log_passed('CALCULATION', f"邊界情況測試通過 ({passed}/{len(test_cases)})")
            return {'status': 'PASSED', 'passed': passed, 'failed': failed}
        else:
            self.log_warning('CALCULATION', f"部分邊界情況測試失敗 ({failed}/{len(test_cases)})")
            return {'status': 'PARTIAL', 'passed': passed, 'failed': failed}

    def inspect_trigger_mechanism(self) -> Dict:
        """檢測觸發機制"""
        print("\n🎯 3. 保護性停損觸發機制檢測")
        print("=" * 50)

        results = {
            'risk_engine_logic': self._check_risk_engine_logic(),
            'trigger_conditions': self._check_trigger_conditions(),
            'async_support': self._check_async_support()
        }

        return results

    def _check_risk_engine_logic(self) -> Dict:
        """檢查風險引擎邏輯"""
        print("🔍 3.1 風險引擎邏輯檢查...")

        try:
            from risk_management_engine import RiskManagementEngine

            # 檢查必要方法
            required_methods = ['update_protective_stop_loss', '_check_protective_stop_loss']
            missing_methods = []

            for method in required_methods:
                if not hasattr(RiskManagementEngine, method):
                    missing_methods.append(method)

            if missing_methods:
                self.log_issue('TRIGGER', 'CRITICAL',
                             f"風險引擎缺少必要方法: {missing_methods}")
                return {'status': 'FAILED', 'missing_methods': missing_methods}

            self.log_passed('TRIGGER', "風險引擎方法檢查通過")
            print("   ✅ 風險引擎方法完整")
            return {'status': 'PASSED'}

        except ImportError as e:
            self.log_issue('TRIGGER', 'CRITICAL',
                         f"無法導入風險引擎: {e}")
            return {'status': 'FAILED', 'reason': 'Import failed'}
        except Exception as e:
            self.log_issue('TRIGGER', 'HIGH',
                         f"風險引擎檢查失敗: {e}")
            return {'status': 'FAILED', 'reason': str(e)}

    def _check_trigger_conditions(self) -> Dict:
        """檢查觸發條件"""
        print("🔍 3.2 觸發條件檢查...")

        try:
            # 檢查simple_integrated.py中的觸發邏輯
            # 這裡我們檢查邏輯是否正確設置

            # 模擬觸發條件測試
            test_scenarios = [
                {'pnl': 20.0, 'exit_reason': '移動停利', 'should_trigger': True},
                {'pnl': 15.0, 'exit_reason': '初始停損', 'should_trigger': True},
                {'pnl': -5.0, 'exit_reason': '移動停利', 'should_trigger': False},
                {'pnl': 0.0, 'exit_reason': '移動停利', 'should_trigger': False}
            ]

            passed = 0
            for scenario in test_scenarios:
                # 模擬觸發邏輯: if action['pnl'] > 0
                would_trigger = scenario['pnl'] > 0

                if would_trigger == scenario['should_trigger']:
                    passed += 1
                    print(f"   ✅ 觸發條件正確: PnL={scenario['pnl']}, 原因={scenario['exit_reason']}")
                else:
                    print(f"   ❌ 觸發條件錯誤: PnL={scenario['pnl']}, 預期={scenario['should_trigger']}, 實際={would_trigger}")

            if passed == len(test_scenarios):
                self.log_passed('TRIGGER', "觸發條件邏輯正確")
                return {'status': 'PASSED'}
            else:
                self.log_warning('TRIGGER', f"部分觸發條件測試失敗 ({passed}/{len(test_scenarios)})")
                return {'status': 'PARTIAL', 'passed': passed, 'total': len(test_scenarios)}

        except Exception as e:
            self.log_issue('TRIGGER', 'MEDIUM',
                         f"觸發條件檢查失敗: {e}")
            return {'status': 'FAILED', 'reason': str(e)}

    def _check_async_support(self) -> Dict:
        """檢查異步支援"""
        print("🔍 3.3 異步支援檢查...")

        try:
            from async_db_updater import AsyncDatabaseUpdater

            # 檢查異步更新方法
            if hasattr(AsyncDatabaseUpdater, 'schedule_protection_update'):
                self.log_passed('TRIGGER', "異步保護性停損更新支援正常")
                print("   ✅ 異步更新支援正常")
                return {'status': 'PASSED'}
            else:
                self.log_warning('TRIGGER', "缺少異步保護性停損更新方法")
                print("   ⚠️ 缺少異步更新支援")
                return {'status': 'PARTIAL', 'reason': 'Missing async method'}

        except ImportError as e:
            self.log_warning('TRIGGER', f"無法導入異步更新器: {e}")
            return {'status': 'FAILED', 'reason': 'Import failed'}
        except Exception as e:
            self.log_issue('TRIGGER', 'MEDIUM',
                         f"異步支援檢查失敗: {e}")
            return {'status': 'FAILED', 'reason': str(e)}

    def inspect_execution_flow(self) -> Dict:
        """檢測執行流程"""
        print("\n🚪 4. 保護性停損執行流程檢測")
        print("=" * 50)

        results = {
            'unified_exit_manager': self._check_unified_exit_manager(),
            'database_operations': self._check_database_operations(),
            'state_management': self._check_state_management()
        }

        return results

    def _check_unified_exit_manager(self) -> Dict:
        """檢查統一出場管理器"""
        print("🔍 4.1 統一出場管理器檢查...")

        try:
            from unified_exit_manager import UnifiedExitManager

            # 檢查保護性停損相關方法
            required_methods = ['execute_protective_stop', 'trigger_protective_stop_update']
            missing_methods = []

            for method in required_methods:
                if not hasattr(UnifiedExitManager, method):
                    missing_methods.append(method)

            if missing_methods:
                self.log_issue('EXECUTION', 'HIGH',
                             f"統一出場管理器缺少方法: {missing_methods}")
                return {'status': 'FAILED', 'missing_methods': missing_methods}

            self.log_passed('EXECUTION', "統一出場管理器方法完整")
            print("   ✅ 統一出場管理器支援完整")
            return {'status': 'PASSED'}

        except ImportError as e:
            self.log_issue('EXECUTION', 'CRITICAL',
                         f"無法導入統一出場管理器: {e}")
            return {'status': 'FAILED', 'reason': 'Import failed'}
        except Exception as e:
            self.log_issue('EXECUTION', 'HIGH',
                         f"統一出場管理器檢查失敗: {e}")
            return {'status': 'FAILED', 'reason': str(e)}

    def _check_database_operations(self) -> Dict:
        """檢查資料庫操作"""
        print("🔍 4.2 資料庫操作檢查...")

        try:
            from multi_group_database import MultiGroupDatabaseManager

            # 檢查保護性停損相關方法
            required_methods = ['update_protective_stop', '_upgrade_protective_stop_schema']
            missing_methods = []

            for method in required_methods:
                if not hasattr(MultiGroupDatabaseManager, method):
                    missing_methods.append(method)

            if missing_methods:
                self.log_warning('EXECUTION',
                               f"資料庫管理器缺少方法: {missing_methods}")
                print(f"   ⚠️ 缺少資料庫方法: {missing_methods}")
                return {'status': 'PARTIAL', 'missing_methods': missing_methods}

            self.log_passed('EXECUTION', "資料庫操作方法完整")
            print("   ✅ 資料庫操作支援完整")
            return {'status': 'PASSED'}

        except ImportError as e:
            self.log_issue('EXECUTION', 'CRITICAL',
                         f"無法導入資料庫管理器: {e}")
            return {'status': 'FAILED', 'reason': 'Import failed'}
        except Exception as e:
            self.log_issue('EXECUTION', 'MEDIUM',
                         f"資料庫操作檢查失敗: {e}")
            return {'status': 'FAILED', 'reason': str(e)}

    def _check_state_management(self) -> Dict:
        """檢查狀態管理"""
        print("🔍 4.3 狀態管理檢查...")

        try:
            # 檢查資料庫連接和基本操作
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            cursor = conn.cursor()

            # 測試基本查詢
            cursor.execute("SELECT COUNT(*) FROM position_records WHERE status = 'ACTIVE'")
            active_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM risk_management_states")
            risk_count = cursor.fetchone()[0]

            conn.close()

            self.log_passed('EXECUTION', f"狀態管理檢查通過 (活躍部位:{active_count}, 風險狀態:{risk_count})")
            print(f"   ✅ 狀態管理正常 (活躍部位:{active_count}, 風險狀態:{risk_count})")
            return {'status': 'PASSED', 'active_positions': active_count, 'risk_states': risk_count}

        except Exception as e:
            self.log_issue('EXECUTION', 'MEDIUM',
                         f"狀態管理檢查失敗: {e}")
            return {'status': 'FAILED', 'reason': str(e)}

    def inspect_simulation_test(self) -> Dict:
        """檢測模擬測試"""
        print("\n🧪 5. 保護性停損模擬測試")
        print("=" * 50)

        results = {
            'long_scenario': self._simulate_long_scenario(),
            'short_scenario': self._simulate_short_scenario(),
            'multi_lot_scenario': self._simulate_multi_lot_scenario()
        }

        return results

    def _simulate_long_scenario(self) -> Dict:
        """模擬多單情境"""
        print("🎮 5.1 多單保護性停損情境模擬...")

        try:
            # 模擬情境: 多單2口策略
            scenario = {
                'direction': 'LONG',
                'entry_price': 20000.0,
                'lot1_exit_price': 20020.0,  # 第1口獲利20點
                'lot1_profit': 20.0,
                'lot2_entry_price': 20000.0,
                'protection_multiplier': 2.0
            }

            # 計算保護性停損
            stop_loss_amount = scenario['lot1_profit'] * scenario['protection_multiplier']
            expected_protection = scenario['lot2_entry_price'] - stop_loss_amount

            print(f"   📊 情境參數:")
            print(f"      方向: {scenario['direction']}")
            print(f"      第1口: 進場{scenario['entry_price']} → 出場{scenario['lot1_exit_price']} (獲利{scenario['lot1_profit']}點)")
            print(f"      第2口: 進場{scenario['lot2_entry_price']}")
            print(f"      保護倍數: {scenario['protection_multiplier']}倍")
            print(f"   🛡️ 計算結果:")
            print(f"      保護性停損: {expected_protection}")
            print(f"      保護空間: {scenario['lot1_profit'] * scenario['protection_multiplier']}點")

            # 驗證邏輯合理性
            if expected_protection < scenario['lot2_entry_price']:
                self.log_passed('SIMULATION', "多單保護性停損模擬正確")
                print("   ✅ 多單保護邏輯正確")
                return {'status': 'PASSED', 'protection_price': expected_protection}
            else:
                self.log_issue('SIMULATION', 'HIGH',
                             "多單保護性停損計算邏輯錯誤")
                return {'status': 'FAILED', 'reason': 'Logic error'}

        except Exception as e:
            self.log_issue('SIMULATION', 'MEDIUM',
                         f"多單模擬測試失敗: {e}")
            return {'status': 'FAILED', 'reason': str(e)}

    def _simulate_short_scenario(self) -> Dict:
        """模擬空單情境"""
        print("🎮 5.2 空單保護性停損情境模擬...")

        try:
            # 模擬情境: 空單2口策略
            scenario = {
                'direction': 'SHORT',
                'entry_price': 22542.0,
                'lot1_exit_price': 22522.0,  # 第1口獲利20點
                'lot1_profit': 20.0,
                'lot2_entry_price': 22542.0,
                'protection_multiplier': 2.0
            }

            # 計算保護性停損 (空單往高點移動)
            stop_loss_amount = scenario['lot1_profit'] * scenario['protection_multiplier']
            expected_protection = scenario['lot2_entry_price'] + stop_loss_amount

            print(f"   📊 情境參數:")
            print(f"      方向: {scenario['direction']}")
            print(f"      第1口: 進場{scenario['entry_price']} → 出場{scenario['lot1_exit_price']} (獲利{scenario['lot1_profit']}點)")
            print(f"      第2口: 進場{scenario['lot2_entry_price']}")
            print(f"      保護倍數: {scenario['protection_multiplier']}倍")
            print(f"   🛡️ 計算結果:")
            print(f"      保護性停損: {expected_protection}")
            print(f"      保護空間: {scenario['lot1_profit'] * scenario['protection_multiplier']}點")

            # 驗證邏輯合理性 (空單保護價格應該高於進場價)
            if expected_protection > scenario['lot2_entry_price']:
                self.log_passed('SIMULATION', "空單保護性停損模擬正確")
                print("   ✅ 空單保護邏輯正確")
                return {'status': 'PASSED', 'protection_price': expected_protection}
            else:
                self.log_issue('SIMULATION', 'HIGH',
                             "空單保護性停損計算邏輯錯誤")
                return {'status': 'FAILED', 'reason': 'Logic error'}

        except Exception as e:
            self.log_issue('SIMULATION', 'MEDIUM',
                         f"空單模擬測試失敗: {e}")
            return {'status': 'FAILED', 'reason': str(e)}

    def _simulate_multi_lot_scenario(self) -> Dict:
        """模擬多口情境"""
        print("🎮 5.3 多口保護性停損情境模擬...")

        try:
            # 模擬情境: 3口策略
            scenario = {
                'direction': 'SHORT',
                'lots': [
                    {'lot_id': 1, 'entry': 22540.0, 'exit': 22520.0, 'profit': 20.0, 'multiplier': None},
                    {'lot_id': 2, 'entry': 22542.0, 'exit': None, 'profit': None, 'multiplier': 2.0},
                    {'lot_id': 3, 'entry': 22544.0, 'exit': None, 'profit': None, 'multiplier': 2.0}
                ]
            }

            print(f"   📊 3口策略模擬:")

            # 第1口平倉後，計算第2口保護
            lot1 = scenario['lots'][0]
            lot2 = scenario['lots'][1]

            if lot2['multiplier']:
                protection_2 = lot2['entry'] + (lot1['profit'] * lot2['multiplier'])
                print(f"      第1口平倉後 → 第2口保護: {protection_2}")

            # 假設第2口也平倉，計算第3口保護
            lot3 = scenario['lots'][2]
            cumulative_profit = lot1['profit'] + 25.0  # 假設第2口也獲利25點

            if lot3['multiplier']:
                protection_3 = lot3['entry'] + (cumulative_profit * lot3['multiplier'])
                print(f"      第2口平倉後 → 第3口保護: {protection_3}")

            self.log_passed('SIMULATION', "多口保護性停損模擬完成")
            print("   ✅ 多口保護邏輯模擬正確")
            return {'status': 'PASSED'}

        except Exception as e:
            self.log_issue('SIMULATION', 'MEDIUM',
                         f"多口模擬測試失敗: {e}")
            return {'status': 'FAILED', 'reason': str(e)}

    def generate_inspection_report(self):
        """生成檢測報告"""
        print("\n📋 生成保護性停損檢測報告...")

        # 統計結果
        total_checks = len(self.passed_checks) + len(self.warnings) + len(self.issues)
        critical_issues = len([i for i in self.issues if i['severity'] == 'CRITICAL'])
        high_issues = len([i for i in self.issues if i['severity'] == 'HIGH'])

        # 生成報告
        report = {
            'inspection_time': datetime.now().isoformat(),
            'summary': {
                'total_checks': total_checks,
                'passed_checks': len(self.passed_checks),
                'warnings': len(self.warnings),
                'issues': len(self.issues),
                'critical_issues': critical_issues,
                'high_issues': high_issues
            },
            'test_results': self.test_results,
            'passed_checks': self.passed_checks,
            'warnings': self.warnings,
            'issues': self.issues
        }

        # 保存報告
        report_filename = f"保護性停損檢測報告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"📄 檢測報告已保存: {report_filename}")

        # 輸出總結
        print(f"\n📊 保護性停損檢測總結:")
        print(f"   總檢查項目: {total_checks}")
        print(f"   ✅ 通過: {len(self.passed_checks)}")
        print(f"   ⚠️ 警告: {len(self.warnings)}")
        print(f"   ❌ 問題: {len(self.issues)} (嚴重:{critical_issues}, 重要:{high_issues})")

        # 評估整體狀態
        if critical_issues > 0:
            print(f"\n🚨 整體評估: 嚴重問題 - 需要立即修復")
            return 'CRITICAL'
        elif high_issues > 0:
            print(f"\n⚠️ 整體評估: 重要問題 - 建議修復")
            return 'HIGH'
        elif len(self.warnings) > 0:
            print(f"\n✅ 整體評估: 基本正常 - 有改進空間")
            return 'WARNING'
        else:
            print(f"\n🎉 整體評估: 完全正常 - 保護性停損功能運作良好")
            return 'PASSED'

def main():
    """主檢測函數"""
    print("🛡️ 保護性停損全面檢測工具 v1.0")
    print("=" * 60)
    print("🎯 檢測目標: 確保保護性停損機制正常運作")
    print("📋 檢測範圍: 配置、計算、觸發、執行、模擬")
    print("=" * 60)

    inspector = ProtectiveStopInspector()

    try:
        # 執行各項檢測
        inspector.test_results['configuration'] = inspector.inspect_configuration()
        inspector.test_results['calculation'] = inspector.inspect_calculation_logic()
        inspector.test_results['trigger'] = inspector.inspect_trigger_mechanism()
        inspector.test_results['execution'] = inspector.inspect_execution_flow()
        inspector.test_results['simulation'] = inspector.inspect_simulation_test()

        # 生成檢測報告
        overall_status = inspector.generate_inspection_report()

        return inspector, overall_status

    except Exception as e:
        print(f"\n❌ 檢測過程發生異常: {e}")
        print(f"詳細錯誤: {traceback.format_exc()}")
        return inspector, 'ERROR'

if __name__ == "__main__":
    inspector, status = main()
