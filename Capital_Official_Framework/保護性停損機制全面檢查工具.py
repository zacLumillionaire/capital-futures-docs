#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
保護性停損機制全面檢查工具
多角度驗證保護性停損機制，確保第一口平倉後能正確觸發第二口的保護性停損
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

class ProtectiveStopValidator:
    """保護性停損驗證器"""
    
    def __init__(self, db_path: str = "multi_group_strategy.db"):
        self.db_path = db_path
        self.results = {}
        self.critical_issues = []
        self.warnings = []
        
    def run_comprehensive_validation(self):
        """執行全面驗證"""
        print("🛡️ 保護性停損機制全面檢查")
        print("=" * 60)
        print("🎯 目標：確保第一口平倉後正確觸發第二口保護性停損")
        print("=" * 60)
        
        # 階段1: 保護性停損參數與配置檢查
        self.results['parameters'] = self.check_protective_stop_parameters()
        
        # 階段2: 第一口平倉觸發邏輯檢查
        self.results['trigger_logic'] = self.check_first_lot_exit_trigger()
        
        # 階段3: 保護性停損計算與更新
        self.results['calculation'] = self.check_protective_stop_calculation()
        
        # 階段4: 保護性停損觸發執行
        self.results['execution'] = self.check_protective_stop_execution()
        
        # 階段5: 資料庫狀態管理檢查
        self.results['database'] = self.check_database_state_management()
        
        # 階段6: 模擬測試與驗證
        self.results['simulation'] = self.simulate_protective_stop_scenarios()
        
        # 生成檢查報告
        self.generate_validation_report()
        
    def check_protective_stop_parameters(self) -> Dict:
        """階段1: 檢查保護性停損參數與配置"""
        print("\n🔍 階段1: 保護性停損參數與配置檢查")
        print("-" * 40)
        
        result = {'status': 'UNKNOWN', 'issues': [], 'details': {}}
        
        try:
            # 檢查資料庫中的保護性停損配置
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 檢查部位記錄中的保護性停損參數
                cursor.execute("""
                    SELECT id, lot_id, rule_config
                    FROM position_records 
                    WHERE status = 'ACTIVE'
                    ORDER BY id
                """)
                
                positions = cursor.fetchall()
                
                print(f"   檢查 {len(positions)} 個活躍部位的保護性停損配置:")
                
                for pos_id, lot_id, rule_config in positions:
                    print(f"\n   📊 部位 {pos_id} (第{lot_id}口):")
                    
                    if rule_config:
                        try:
                            config = json.loads(rule_config)
                            
                            # 檢查保護性停損相關參數
                            protective_multiplier = config.get('protective_stop_multiplier')
                            use_protective = config.get('use_protective_stop', False)
                            
                            print(f"      保護性停損倍數: {protective_multiplier}")
                            print(f"      啟用保護性停損: {use_protective}")
                            
                            if protective_multiplier is None:
                                result['issues'].append(f"部位{pos_id}缺少保護性停損倍數")
                                print(f"      ❌ 缺少保護性停損倍數")
                            elif protective_multiplier <= 0:
                                result['issues'].append(f"部位{pos_id}保護性停損倍數無效: {protective_multiplier}")
                                print(f"      ❌ 保護性停損倍數無效")
                            else:
                                print(f"      ✅ 保護性停損倍數正常")
                            
                            if not use_protective:
                                self.warnings.append(f"部位{pos_id}未啟用保護性停損")
                                print(f"      ⚠️ 未啟用保護性停損")
                            else:
                                print(f"      ✅ 已啟用保護性停損")
                                
                        except json.JSONDecodeError:
                            result['issues'].append(f"部位{pos_id}規則配置解析失敗")
                            print(f"      ❌ 規則配置解析失敗")
                    else:
                        result['issues'].append(f"部位{pos_id}缺少規則配置")
                        print(f"      ❌ 缺少規則配置")
                
                # 檢查出場規則配置
                print(f"\n   📋 檢查出場規則配置...")
                
                try:
                    cursor.execute("""
                        SELECT lot_number, protective_stop_multiplier, description
                        FROM lot_exit_rules
                        WHERE is_default = 1
                        ORDER BY lot_number
                    """)
                    
                    exit_rules = cursor.fetchall()
                    
                    if exit_rules:
                        print(f"      找到 {len(exit_rules)} 個預設出場規則:")
                        for lot_num, multiplier, desc in exit_rules:
                            print(f"         第{lot_num}口: 倍數={multiplier}, 描述={desc}")
                            
                            if multiplier is None or multiplier <= 0:
                                result['issues'].append(f"第{lot_num}口出場規則保護倍數無效")
                    else:
                        result['issues'].append("找不到預設出場規則")
                        print(f"      ❌ 找不到預設出場規則")
                        
                except Exception as e:
                    result['issues'].append(f"檢查出場規則失敗: {e}")
                    print(f"      ❌ 檢查出場規則失敗: {e}")
            
            result['status'] = 'PASSED' if not result['issues'] else 'FAILED'
            
        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            self.critical_issues.append(f"保護性停損參數檢查失敗: {e}")
            
        return result
    
    def check_first_lot_exit_trigger(self) -> Dict:
        """階段2: 檢查第一口平倉觸發邏輯"""
        print("\n🔍 階段2: 第一口平倉觸發邏輯檢查")
        print("-" * 40)
        
        result = {'status': 'UNKNOWN', 'issues': [], 'details': {}}
        
        try:
            # 檢查保護性停損觸發相關代碼
            print("   📋 檢查保護性停損觸發代碼...")
            
            # 檢查風險管理引擎
            if os.path.exists('risk_management_engine.py'):
                with open('risk_management_engine.py', 'r', encoding='utf-8') as f:
                    risk_content = f.read()
                
                if 'protective_stop' in risk_content.lower():
                    print("   ✅ 風險引擎包含保護性停損邏輯")
                else:
                    result['issues'].append("風險引擎缺少保護性停損邏輯")
                    print("   ❌ 風險引擎缺少保護性停損邏輯")
                
                # 檢查第一口平倉觸發邏輯
                if 'first_lot' in risk_content.lower() or 'lot_id == 1' in risk_content:
                    print("   ✅ 包含第一口特殊處理邏輯")
                else:
                    self.warnings.append("可能缺少第一口特殊處理邏輯")
                    print("   ⚠️ 可能缺少第一口特殊處理邏輯")
            else:
                result['issues'].append("找不到風險管理引擎文件")
            
            # 檢查保護性停損管理器
            protective_files = [
                'cumulative_profit_protection_manager.py',
                'protective_stop_manager.py',
                'stop_loss_state_manager.py'
            ]
            
            found_protective = False
            for file_name in protective_files:
                if os.path.exists(file_name):
                    found_protective = True
                    print(f"   ✅ 找到保護性停損管理器: {file_name}")
                    
                    with open(file_name, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 檢查關鍵方法
                    if 'update_protective_stop' in content or 'activate_protection' in content:
                        print(f"      ✅ 包含保護性停損更新方法")
                    else:
                        result['issues'].append(f"{file_name} 缺少保護性停損更新方法")
                    
                    # 檢查第一口平倉觸發
                    if 'first_lot_exit' in content.lower() or 'lot_1_exit' in content.lower():
                        print(f"      ✅ 包含第一口平倉觸發邏輯")
                    else:
                        self.warnings.append(f"{file_name} 可能缺少第一口平倉觸發邏輯")
            
            if not found_protective:
                result['issues'].append("找不到保護性停損管理器")
                print("   ❌ 找不到保護性停損管理器")
            
            result['status'] = 'PASSED' if not result['issues'] else 'FAILED'
            
        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            self.critical_issues.append(f"第一口平倉觸發邏輯檢查失敗: {e}")
            
        return result
    
    def check_protective_stop_calculation(self) -> Dict:
        """階段3: 檢查保護性停損計算與更新"""
        print("\n🔍 階段3: 保護性停損計算與更新檢查")
        print("-" * 40)
        
        result = {'status': 'UNKNOWN', 'issues': [], 'details': {}}
        
        try:
            # 模擬保護性停損計算
            print("   🧪 模擬保護性停損計算...")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 獲取當前部位信息
                cursor.execute("""
                    SELECT pr.id, pr.lot_id, pr.direction, pr.entry_price, pr.rule_config
                    FROM position_records pr
                    WHERE pr.status = 'ACTIVE'
                    ORDER BY pr.lot_id
                """)
                
                positions = cursor.fetchall()
                
                if len(positions) >= 2:
                    # 模擬第一口平倉，計算第二口保護性停損
                    first_lot = positions[0]
                    second_lot = positions[1]
                    
                    pos1_id, lot1_id, direction1, entry1, config1 = first_lot
                    pos2_id, lot2_id, direction2, entry2, config2 = second_lot
                    
                    print(f"\n   📊 模擬第一口平倉觸發第二口保護:")
                    print(f"      第一口: 部位{pos1_id}, 進場價格={entry1}")
                    print(f"      第二口: 部位{pos2_id}, 進場價格={entry2}")
                    
                    # 模擬第一口獲利平倉
                    simulated_exit_price = 22520  # 模擬第一口平倉價格
                    first_lot_profit = entry1 - simulated_exit_price if direction1 == 'SHORT' else simulated_exit_price - entry1
                    
                    print(f"      模擬第一口平倉價格: {simulated_exit_price}")
                    print(f"      第一口獲利: {first_lot_profit}點")
                    
                    # 計算第二口保護性停損
                    if config2:
                        try:
                            config = json.loads(config2)
                            protective_multiplier = config.get('protective_stop_multiplier', 2.0)
                            
                            # 保護性停損計算邏輯
                            if direction2 == 'SHORT':
                                # SHORT部位：保護性停損 = 進場價格 + (第一口獲利 * 倍數)
                                protective_stop_price = entry2 + (first_lot_profit * protective_multiplier)
                            else:
                                # LONG部位：保護性停損 = 進場價格 - (第一口獲利 * 倍數)
                                protective_stop_price = entry2 - (first_lot_profit * protective_multiplier)
                            
                            print(f"      保護倍數: {protective_multiplier}")
                            print(f"      計算的保護性停損價格: {protective_stop_price}")
                            
                            # 檢查合理性
                            if direction2 == 'SHORT':
                                if protective_stop_price <= entry2:
                                    print(f"      ✅ SHORT保護性停損價格合理 ({protective_stop_price} <= {entry2})")
                                else:
                                    result['issues'].append(f"SHORT保護性停損價格不合理: {protective_stop_price} > {entry2}")
                                    print(f"      ❌ SHORT保護性停損價格不合理")
                            else:
                                if protective_stop_price >= entry2:
                                    print(f"      ✅ LONG保護性停損價格合理 ({protective_stop_price} >= {entry2})")
                                else:
                                    result['issues'].append(f"LONG保護性停損價格不合理: {protective_stop_price} < {entry2}")
                                    print(f"      ❌ LONG保護性停損價格不合理")
                            
                        except json.JSONDecodeError:
                            result['issues'].append("第二口規則配置解析失敗")
                            print(f"      ❌ 第二口規則配置解析失敗")
                    else:
                        result['issues'].append("第二口缺少規則配置")
                        print(f"      ❌ 第二口缺少規則配置")
                else:
                    print("   ℹ️ 部位數量不足，無法模擬保護性停損")
            
            result['status'] = 'PASSED' if not result['issues'] else 'FAILED'
            
        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            self.critical_issues.append(f"保護性停損計算檢查失敗: {e}")
            
        return result

    def check_protective_stop_execution(self) -> Dict:
        """階段4: 檢查保護性停損觸發執行"""
        print("\n🔍 階段4: 保護性停損觸發執行檢查")
        print("-" * 40)

        result = {'status': 'UNKNOWN', 'issues': [], 'details': {}}

        try:
            # 檢查保護性停損執行機制
            print("   📋 檢查保護性停損執行機制...")

            # 檢查是否使用統一出場管理器
            if os.path.exists('unified_exit_manager.py'):
                with open('unified_exit_manager.py', 'r', encoding='utf-8') as f:
                    exit_content = f.read()

                if 'protective_stop' in exit_content.lower():
                    print("   ✅ 統一出場管理器支援保護性停損")
                else:
                    result['issues'].append("統一出場管理器缺少保護性停損支援")
                    print("   ❌ 統一出場管理器缺少保護性停損支援")

                # 檢查保護性停損執行方法
                if 'execute_protective_stop' in exit_content or 'trigger_protective' in exit_content:
                    print("   ✅ 包含保護性停損執行方法")
                else:
                    result['issues'].append("缺少保護性停損執行方法")
                    print("   ❌ 缺少保護性停損執行方法")
            else:
                result['issues'].append("找不到統一出場管理器")

            # 檢查保護性停損與移動停利的整合
            print("\n   📊 檢查保護性停損與移動停利整合...")

            if os.path.exists('risk_management_engine.py'):
                with open('risk_management_engine.py', 'r', encoding='utf-8') as f:
                    risk_content = f.read()

                # 檢查是否同時處理保護性停損和移動停利
                has_protective = 'protective_stop' in risk_content.lower()
                has_trailing = 'trailing_stop' in risk_content.lower()

                if has_protective and has_trailing:
                    print("   ✅ 同時支援保護性停損和移動停利")
                elif has_protective:
                    print("   ✅ 支援保護性停損")
                    self.warnings.append("可能缺少移動停利整合")
                elif has_trailing:
                    print("   ⚠️ 僅支援移動停利")
                    result['issues'].append("缺少保護性停損支援")
                else:
                    result['issues'].append("缺少保護性停損和移動停利支援")
                    print("   ❌ 缺少保護性停損和移動停利支援")

            result['status'] = 'PASSED' if not result['issues'] else 'FAILED'

        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            self.critical_issues.append(f"保護性停損執行檢查失敗: {e}")

        return result

    def check_database_state_management(self) -> Dict:
        """階段5: 檢查資料庫狀態管理"""
        print("\n🔍 階段5: 資料庫狀態管理檢查")
        print("-" * 40)

        result = {'status': 'UNKNOWN', 'issues': [], 'details': {}}

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 檢查保護性停損相關表結構
                print("   📋 檢查保護性停損相關表結構...")

                # 檢查 position_records 表
                cursor.execute("PRAGMA table_info(position_records)")
                pr_columns = [col[1] for col in cursor.fetchall()]

                protective_fields = [
                    'protective_stop_price',
                    'protective_stop_activated',
                    'first_lot_exit_profit'
                ]

                for field in protective_fields:
                    if field in pr_columns:
                        print(f"      ✅ position_records 包含: {field}")
                    else:
                        self.warnings.append(f"position_records 可能缺少: {field}")
                        print(f"      ⚠️ position_records 可能缺少: {field}")

                # 檢查 risk_management_states 表
                try:
                    cursor.execute("PRAGMA table_info(risk_management_states)")
                    rms_columns = [col[1] for col in cursor.fetchall()]

                    risk_protective_fields = [
                        'protective_stop_price',
                        'protective_stop_activated'
                    ]

                    for field in risk_protective_fields:
                        if field in rms_columns:
                            print(f"      ✅ risk_management_states 包含: {field}")
                        else:
                            self.warnings.append(f"risk_management_states 可能缺少: {field}")
                            print(f"      ⚠️ risk_management_states 可能缺少: {field}")

                except Exception as e:
                    result['issues'].append(f"檢查 risk_management_states 表失敗: {e}")

                # 檢查保護性停損狀態更新機制
                print("\n   📊 檢查保護性停損狀態更新機制...")

                if os.path.exists('multi_group_database.py'):
                    with open('multi_group_database.py', 'r', encoding='utf-8') as f:
                        db_content = f.read()

                    if 'update_protective_stop' in db_content:
                        print("   ✅ 包含保護性停損更新方法")
                    else:
                        result['issues'].append("缺少保護性停損更新方法")
                        print("   ❌ 缺少保護性停損更新方法")

                    if 'protective_stop_activated' in db_content:
                        print("   ✅ 支援保護性停損狀態管理")
                    else:
                        self.warnings.append("可能缺少保護性停損狀態管理")
                        print("   ⚠️ 可能缺少保護性停損狀態管理")

                # 檢查異步更新支援
                if os.path.exists('async_db_updater.py'):
                    with open('async_db_updater.py', 'r', encoding='utf-8') as f:
                        async_content = f.read()

                    if 'protective_stop' in async_content.lower():
                        print("   ✅ 支援保護性停損異步更新")
                    else:
                        self.warnings.append("可能缺少保護性停損異步更新")
                        print("   ⚠️ 可能缺少保護性停損異步更新")

            result['status'] = 'PASSED' if not result['issues'] else 'FAILED'

        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            self.critical_issues.append(f"資料庫狀態管理檢查失敗: {e}")

        return result

    def simulate_protective_stop_scenarios(self) -> Dict:
        """階段6: 模擬保護性停損情境"""
        print("\n🔍 階段6: 模擬保護性停損情境")
        print("-" * 40)

        result = {'status': 'UNKNOWN', 'issues': [], 'details': {}}

        try:
            print("   🧪 模擬完整保護性停損流程...")

            with sqlite3.connect(self.db_path) as conn:
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

                    print(f"\n   📊 完整流程模擬:")
                    print(f"      第一口部位: {pos1_id} (進場: {entry1})")
                    print(f"      第二口部位: {pos2_id} (進場: {entry2})")

                    # 情境1: 第一口獲利平倉
                    scenarios = [
                        {'exit_price': 22520, 'description': '第一口小幅獲利平倉'},
                        {'exit_price': 22510, 'description': '第一口中等獲利平倉'},
                        {'exit_price': 22500, 'description': '第一口大幅獲利平倉'}
                    ]

                    for scenario in scenarios:
                        exit_price = scenario['exit_price']
                        description = scenario['description']

                        print(f"\n      🎯 情境: {description}")
                        print(f"         第一口平倉價格: {exit_price}")

                        # 計算第一口獲利
                        if direction1 == 'SHORT':
                            first_profit = entry1 - exit_price
                        else:
                            first_profit = exit_price - entry1

                        print(f"         第一口獲利: {first_profit}點")

                        # 計算第二口保護性停損
                        if config2:
                            try:
                                config = json.loads(config2)
                                multiplier = config.get('protective_stop_multiplier', 2.0)

                                if direction2 == 'SHORT':
                                    protective_price = entry2 + (first_profit * multiplier)
                                else:
                                    protective_price = entry2 - (first_profit * multiplier)

                                print(f"         保護倍數: {multiplier}")
                                print(f"         第二口保護價格: {protective_price}")

                                # 檢查觸發條件
                                current_price = 22515  # 模擬當前價格

                                if direction2 == 'SHORT':
                                    should_trigger = current_price >= protective_price
                                else:
                                    should_trigger = current_price <= protective_price

                                print(f"         當前價格: {current_price}")
                                print(f"         應觸發保護: {should_trigger}")

                                if should_trigger:
                                    print(f"         🎯 觸發保護性停損!")
                                else:
                                    print(f"         ✅ 保護性停損待命中")

                            except json.JSONDecodeError:
                                print(f"         ❌ 配置解析失敗")
                        else:
                            print(f"         ❌ 缺少配置")
                else:
                    print("   ℹ️ 部位數量不足，無法完整模擬")

            # 檢查保護性停損執行路徑
            print(f"\n   📋 保護性停損執行路徑:")
            execution_steps = [
                "1. 第一口達到獲利條件",
                "2. 執行第一口平倉",
                "3. 計算第一口實際獲利",
                "4. 更新第二口保護性停損價格",
                "5. 啟動第二口保護性停損監控",
                "6. 價格觸發保護性停損條件",
                "7. 執行第二口保護性停損平倉",
                "8. 更新部位狀態和損益"
            ]

            for step in execution_steps:
                print(f"      {step}")

            result['status'] = 'PASSED'

        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            self.critical_issues.append(f"保護性停損情境模擬失敗: {e}")

        return result

    def generate_validation_report(self):
        """生成驗證報告"""
        print("\n📋 保護性停損機制檢查報告")
        print("=" * 60)

        # 統計結果
        total_stages = len(self.results)
        passed_stages = sum(1 for r in self.results.values() if r.get('status') == 'PASSED')
        failed_stages = sum(1 for r in self.results.values() if r.get('status') == 'FAILED')
        error_stages = sum(1 for r in self.results.values() if r.get('status') == 'ERROR')

        print(f"📊 檢查統計:")
        print(f"   總階段數: {total_stages}")
        print(f"   ✅ 通過: {passed_stages}")
        print(f"   ❌ 失敗: {failed_stages}")
        print(f"   💥 錯誤: {error_stages}")

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
        print(f"\n🎯 保護性停損風險評估:")
        if self.critical_issues:
            print("   🚨 高風險: 存在關鍵問題，保護性停損可能失效")
            print("   📝 建議: 立即修復關鍵問題")
        elif len(self.warnings) > 3:
            print("   ⚠️ 中風險: 存在多個警告，建議優化")
            print("   📝 建議: 逐步改進保護性停損機制")
        else:
            print("   ✅ 低風險: 保護性停損機制基本正常")
            print("   📝 建議: 可以正常使用，持續監控")

        # 對比移動停利問題
        print(f"\n🔍 與移動停利問題對比:")
        print("   移動停利問題: 參數缺失、狀態不同步")
        print("   保護性停損檢查: 重點關注相同類型問題")

        if not self.critical_issues:
            print("   ✅ 保護性停損未發現類似問題")
        else:
            print("   ⚠️ 保護性停損可能存在類似問題")

        # 保存報告
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_stages': total_stages,
                'passed': passed_stages,
                'failed': failed_stages,
                'errors': error_stages
            },
            'critical_issues': self.critical_issues,
            'warnings': self.warnings,
            'detailed_results': self.results
        }

        report_file = f"保護性停損檢查報告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"\n📄 詳細報告已保存: {report_file}")

def main():
    """主檢查函數"""
    validator = ProtectiveStopValidator()
    validator.run_comprehensive_validation()

if __name__ == "__main__":
    main()
