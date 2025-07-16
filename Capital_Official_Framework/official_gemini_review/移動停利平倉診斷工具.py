#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移動停利平倉機制全流程診斷工具
檢查從建倉成功到移動停利平倉的完整流程
"""

import sqlite3
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class TrailingStopDiagnostic:
    """移動停利診斷器"""
    
    def __init__(self, db_path: str = "multi_group_strategy.db"):
        self.db_path = db_path
        self.results = {}
        self.issues = []
        
    def run_full_diagnostic(self):
        """執行完整診斷"""
        print("🚀 移動停利平倉機制全流程診斷")
        print("=" * 60)
        
        # 階段1: 建倉成功後部位狀態檢查
        self.results['stage1'] = self.check_position_state_after_entry()
        
        # 階段2: 移動停利計算邏輯驗證
        self.results['stage2'] = self.check_trailing_stop_calculation()
        
        # 階段3: 移動停利觸發機制檢查
        self.results['stage3'] = self.check_trailing_stop_trigger()
        
        # 階段4: 平倉條件判斷邏輯檢查
        self.results['stage4'] = self.check_exit_condition_logic()
        
        # 階段5: 平倉執行機制檢查
        self.results['stage5'] = self.check_exit_execution_mechanism()
        
        # 階段6: 資料庫同步和狀態管理檢查
        self.results['stage6'] = self.check_database_sync_and_state()
        
        # 生成診斷報告
        self.generate_diagnostic_report()
        
    def check_position_state_after_entry(self) -> Dict:
        """階段1: 檢查建倉成功後部位狀態"""
        print("\n🔍 階段1: 建倉成功後部位狀態檢查")
        print("-" * 40)
        
        result = {'status': 'UNKNOWN', 'issues': [], 'details': {}}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 獲取最近的活躍部位
                cursor.execute("""
                    SELECT id, group_id, lot_id, direction, entry_price, 
                           trailing_activated, peak_price, trailing_activation_points,
                           trailing_pullback_ratio, status, created_at
                    FROM position_records 
                    WHERE status = 'ACTIVE'
                    ORDER BY id DESC
                    LIMIT 10
                """)
                
                positions = cursor.fetchall()
                result['details']['active_positions'] = len(positions)
                
                print(f"   找到 {len(positions)} 個活躍部位")
                
                for pos in positions:
                    pos_id, group_id, lot_id, direction, entry_price, trailing_activated, \
                    peak_price, trailing_points, pullback_ratio, status, created_at = pos
                    
                    print(f"\n   📊 部位 {pos_id} (組{group_id}, 第{lot_id}口, {direction}):")
                    print(f"      進場價格: {entry_price}")
                    print(f"      移動停利啟動: {trailing_activated}")
                    print(f"      峰值價格: {peak_price}")
                    print(f"      啟動點數: {trailing_points}")
                    print(f"      回撤比例: {pullback_ratio}")
                    print(f"      狀態: {status}")
                    
                    # 檢查關鍵字段
                    issues_for_position = []
                    
                    if entry_price is None:
                        issues_for_position.append("進場價格為 None")
                    
                    if trailing_points is None:
                        issues_for_position.append("移動停利啟動點數未設置")
                    
                    if pullback_ratio is None:
                        issues_for_position.append("回撤比例未設置")
                    
                    if peak_price is None and trailing_activated:
                        issues_for_position.append("移動停利已啟動但峰值價格為 None")
                    
                    if issues_for_position:
                        result['issues'].extend([f"部位{pos_id}: {issue}" for issue in issues_for_position])
                        print(f"      ⚠️ 問題: {', '.join(issues_for_position)}")
                    else:
                        print(f"      ✅ 狀態正常")
                
                # 檢查風險管理狀態
                cursor.execute("""
                    SELECT position_id, current_price, peak_price, trailing_stop_price,
                           trailing_activated, last_update_time
                    FROM risk_management_states
                    WHERE position_id IN (
                        SELECT id FROM position_records WHERE status = 'ACTIVE'
                    )
                    ORDER BY position_id DESC
                """)
                
                risk_states = cursor.fetchall()
                result['details']['risk_states'] = len(risk_states)
                
                print(f"\n   🎯 風險管理狀態: {len(risk_states)} 個")
                
                for risk in risk_states:
                    pos_id, current_price, peak_price, trailing_stop, \
                    trailing_activated, last_update = risk
                    
                    print(f"      部位 {pos_id}: 當前價格={current_price}, 峰值={peak_price}, "
                          f"移停價格={trailing_stop}, 啟動={trailing_activated}")
                
                result['status'] = 'PASSED' if not result['issues'] else 'FAILED'
                
        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            print(f"   ❌ 檢查失敗: {e}")
            
        return result
    
    def check_trailing_stop_calculation(self) -> Dict:
        """階段2: 檢查移動停利計算邏輯"""
        print("\n🔍 階段2: 移動停利計算邏輯驗證")
        print("-" * 40)
        
        result = {'status': 'UNKNOWN', 'issues': [], 'details': {}}
        
        try:
            # 檢查計算邏輯代碼
            print("   📋 檢查移動停利計算相關文件...")
            
            key_files = [
                'risk_management_engine.py',
                'optimized_risk_manager.py', 
                'trailing_stop_calculator.py'
            ]
            
            for file_name in key_files:
                try:
                    with open(file_name, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    print(f"   ✅ 找到文件: {file_name}")
                    
                    # 檢查關鍵方法
                    if 'trailing_stop' in content.lower():
                        print(f"      包含移動停利相關代碼")
                    
                    if 'calculate' in content.lower() and 'trailing' in content.lower():
                        print(f"      包含移動停利計算邏輯")
                    
                    # 檢查具體的計算邏輯
                    if 'peak_price' in content:
                        print(f"      包含峰值價格處理")
                    
                    if 'pullback' in content.lower():
                        print(f"      包含回撤計算")
                        
                except FileNotFoundError:
                    result['issues'].append(f"找不到關鍵文件: {file_name}")
                    print(f"   ❌ 找不到文件: {file_name}")
                except Exception as e:
                    result['issues'].append(f"讀取文件 {file_name} 失敗: {e}")
            
            # 模擬計算測試
            print("\n   🧪 模擬移動停利計算測試...")
            
            # 測試案例：SHORT部位，進場價格22540，當前價格22502，啟動點數20
            test_cases = [
                {
                    'direction': 'SHORT',
                    'entry_price': 22540,
                    'current_price': 22502,
                    'activation_points': 20,
                    'pullback_ratio': 0.20,
                    'expected_activated': True,
                    'expected_profit': 38  # 22540 - 22502 = 38點
                }
            ]
            
            for i, case in enumerate(test_cases):
                print(f"      測試案例 {i+1}:")
                print(f"         方向: {case['direction']}")
                print(f"         進場價格: {case['entry_price']}")
                print(f"         當前價格: {case['current_price']}")
                print(f"         啟動點數: {case['activation_points']}")
                
                # 計算獲利
                if case['direction'] == 'SHORT':
                    profit = case['entry_price'] - case['current_price']
                else:
                    profit = case['current_price'] - case['entry_price']
                
                print(f"         計算獲利: {profit}點")
                
                # 檢查是否應該啟動
                should_activate = profit >= case['activation_points']
                print(f"         應該啟動: {should_activate}")
                
                if should_activate != case['expected_activated']:
                    result['issues'].append(f"測試案例{i+1}啟動判斷錯誤")
            
            result['status'] = 'PASSED' if not result['issues'] else 'FAILED'
            
        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            print(f"   ❌ 檢查失敗: {e}")
            
        return result
    
    def check_trailing_stop_trigger(self) -> Dict:
        """階段3: 檢查移動停利觸發機制"""
        print("\n🔍 階段3: 移動停利觸發機制檢查")
        print("-" * 40)
        
        result = {'status': 'UNKNOWN', 'issues': [], 'details': {}}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 檢查移動停利啟動記錄
                cursor.execute("""
                    SELECT id, trailing_activated, peak_price, 
                           trailing_activation_points, entry_price, direction
                    FROM position_records 
                    WHERE status = 'ACTIVE' AND trailing_activated = 1
                    ORDER BY id DESC
                """)
                
                activated_positions = cursor.fetchall()
                result['details']['activated_positions'] = len(activated_positions)
                
                print(f"   找到 {len(activated_positions)} 個已啟動移動停利的部位")
                
                for pos in activated_positions:
                    pos_id, trailing_activated, peak_price, activation_points, entry_price, direction = pos
                    
                    print(f"\n   📊 部位 {pos_id} ({direction}):")
                    print(f"      進場價格: {entry_price}")
                    print(f"      峰值價格: {peak_price}")
                    print(f"      啟動點數: {activation_points}")
                    
                    # 計算啟動時的獲利
                    if direction == 'SHORT' and entry_price and peak_price:
                        profit_at_activation = entry_price - peak_price
                        print(f"      啟動時獲利: {profit_at_activation}點")
                        
                        if profit_at_activation < activation_points:
                            result['issues'].append(f"部位{pos_id}啟動條件不符：獲利{profit_at_activation}點 < 啟動點數{activation_points}點")
                    
                    # 檢查風險管理狀態
                    cursor.execute("""
                        SELECT current_price, trailing_stop_price, last_update_time
                        FROM risk_management_states
                        WHERE position_id = ?
                    """, (pos_id,))
                    
                    risk_state = cursor.fetchone()
                    if risk_state:
                        current_price, trailing_stop_price, last_update = risk_state
                        print(f"      當前價格: {current_price}")
                        print(f"      移停價格: {trailing_stop_price}")
                        print(f"      最後更新: {last_update}")
                        
                        if trailing_stop_price is None:
                            result['issues'].append(f"部位{pos_id}移動停利已啟動但停利價格為None")
                    else:
                        result['issues'].append(f"部位{pos_id}缺少風險管理狀態記錄")
                
                result['status'] = 'PASSED' if not result['issues'] else 'FAILED'
                
        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            print(f"   ❌ 檢查失敗: {e}")
            
        return result
    
    def check_exit_condition_logic(self) -> Dict:
        """階段4: 檢查平倉條件判斷邏輯"""
        print("\n🔍 階段4: 平倉條件判斷邏輯檢查")
        print("-" * 40)
        
        result = {'status': 'UNKNOWN', 'issues': [], 'details': {}}
        
        try:
            # 檢查平倉條件判斷代碼
            print("   📋 檢查平倉條件判斷相關代碼...")
            
            # 模擬平倉條件檢查
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 獲取已啟動移動停利的部位
                cursor.execute("""
                    SELECT pr.id, pr.direction, pr.entry_price, pr.peak_price,
                           pr.trailing_pullback_ratio, rms.current_price, 
                           rms.trailing_stop_price
                    FROM position_records pr
                    LEFT JOIN risk_management_states rms ON pr.id = rms.position_id
                    WHERE pr.status = 'ACTIVE' AND pr.trailing_activated = 1
                """)
                
                positions = cursor.fetchall()
                
                print(f"   檢查 {len(positions)} 個已啟動移動停利的部位...")
                
                for pos in positions:
                    pos_id, direction, entry_price, peak_price, pullback_ratio, \
                    current_price, trailing_stop_price = pos
                    
                    print(f"\n   📊 部位 {pos_id} ({direction}):")
                    print(f"      進場價格: {entry_price}")
                    print(f"      峰值價格: {peak_price}")
                    print(f"      當前價格: {current_price}")
                    print(f"      移停價格: {trailing_stop_price}")
                    print(f"      回撤比例: {pullback_ratio}")
                    
                    # 檢查平倉條件
                    should_exit = False
                    exit_reason = ""
                    
                    if direction == 'SHORT' and current_price and trailing_stop_price:
                        # SHORT部位：當前價格 >= 移停價格時平倉
                        if current_price >= trailing_stop_price:
                            should_exit = True
                            exit_reason = f"SHORT部位觸發移動停利：{current_price} >= {trailing_stop_price}"
                    
                    elif direction == 'LONG' and current_price and trailing_stop_price:
                        # LONG部位：當前價格 <= 移停價格時平倉
                        if current_price <= trailing_stop_price:
                            should_exit = True
                            exit_reason = f"LONG部位觸發移動停利：{current_price} <= {trailing_stop_price}"
                    
                    print(f"      應該平倉: {should_exit}")
                    if should_exit:
                        print(f"      平倉原因: {exit_reason}")
                        
                        # 檢查是否已經有平倉記錄
                        cursor.execute("""
                            SELECT COUNT(*) FROM position_records 
                            WHERE id = ? AND (exit_price IS NOT NULL OR status = 'EXITED')
                        """, (pos_id,))
                        
                        has_exit = cursor.fetchone()[0] > 0
                        
                        if not has_exit:
                            result['issues'].append(f"部位{pos_id}應該平倉但未執行：{exit_reason}")
                            print(f"      ❌ 應該平倉但未執行")
                        else:
                            print(f"      ✅ 已執行平倉")
                    else:
                        print(f"      ✅ 暫不需要平倉")
                
                result['status'] = 'PASSED' if not result['issues'] else 'FAILED'
                
        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            print(f"   ❌ 檢查失敗: {e}")
            
        return result
    
    def check_exit_execution_mechanism(self) -> Dict:
        """階段5: 檢查平倉執行機制"""
        print("\n🔍 階段5: 平倉執行機制檢查")
        print("-" * 40)
        
        result = {'status': 'UNKNOWN', 'issues': [], 'details': {}}
        
        try:
            # 檢查平倉執行相關文件
            print("   📋 檢查平倉執行相關文件...")
            
            exit_files = [
                'unified_exit_manager.py',
                'exit_mechanism_manager.py',
                'stop_loss_executor.py'
            ]
            
            for file_name in exit_files:
                try:
                    with open(file_name, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    print(f"   ✅ 找到文件: {file_name}")
                    
                    # 檢查關鍵方法
                    if 'execute_exit' in content or 'place_exit_order' in content:
                        print(f"      包含平倉執行方法")
                    
                    if 'trailing_stop' in content.lower():
                        print(f"      包含移動停利處理")
                        
                except FileNotFoundError:
                    result['issues'].append(f"找不到平倉執行文件: {file_name}")
                    print(f"   ❌ 找不到文件: {file_name}")
            
            # 檢查平倉訂單記錄
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 檢查是否有平倉訂單記錄
                cursor.execute("""
                    SELECT COUNT(*) FROM position_records 
                    WHERE exit_reason = '移動停利' AND exit_time IS NOT NULL
                """)
                
                trailing_exits = cursor.fetchone()[0]
                result['details']['trailing_stop_exits'] = trailing_exits
                
                print(f"   📊 移動停利平倉記錄: {trailing_exits} 筆")
                
                # 檢查最近的平倉記錄
                cursor.execute("""
                    SELECT id, exit_reason, exit_price, exit_time, pnl
                    FROM position_records 
                    WHERE exit_reason IS NOT NULL
                    ORDER BY exit_time DESC
                    LIMIT 5
                """)
                
                recent_exits = cursor.fetchall()
                print(f"   📋 最近的平倉記錄: {len(recent_exits)} 筆")
                
                for exit_record in recent_exits:
                    pos_id, exit_reason, exit_price, exit_time, pnl = exit_record
                    print(f"      部位 {pos_id}: {exit_reason} @{exit_price} 損益:{pnl}")
            
            result['status'] = 'PASSED' if not result['issues'] else 'FAILED'
            
        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            print(f"   ❌ 檢查失敗: {e}")
            
        return result
    
    def check_database_sync_and_state(self) -> Dict:
        """階段6: 檢查資料庫同步和狀態管理"""
        print("\n🔍 階段6: 資料庫同步和狀態管理檢查")
        print("-" * 40)
        
        result = {'status': 'UNKNOWN', 'issues': [], 'details': {}}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 檢查資料庫表的一致性
                print("   📋 檢查資料庫表一致性...")
                
                # 檢查 position_records 和 risk_management_states 的一致性
                cursor.execute("""
                    SELECT pr.id, pr.status, rms.position_id
                    FROM position_records pr
                    LEFT JOIN risk_management_states rms ON pr.id = rms.position_id
                    WHERE pr.status = 'ACTIVE'
                """)
                
                consistency_check = cursor.fetchall()
                
                missing_risk_states = 0
                for pos_id, status, risk_pos_id in consistency_check:
                    if risk_pos_id is None:
                        missing_risk_states += 1
                        result['issues'].append(f"部位{pos_id}缺少風險管理狀態記錄")
                
                print(f"   活躍部位: {len(consistency_check)} 個")
                print(f"   缺少風險狀態: {missing_risk_states} 個")
                
                # 檢查異步更新狀態
                print("\n   📊 檢查異步更新狀態...")
                
                # 檢查最近的更新時間
                cursor.execute("""
                    SELECT position_id, last_update_time, current_price
                    FROM risk_management_states
                    ORDER BY last_update_time DESC
                    LIMIT 5
                """)
                
                recent_updates = cursor.fetchall()
                print(f"   最近更新記錄: {len(recent_updates)} 筆")
                
                for pos_id, last_update, current_price in recent_updates:
                    print(f"      部位 {pos_id}: {last_update} @{current_price}")
                
                result['status'] = 'PASSED' if not result['issues'] else 'FAILED'
                
        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            print(f"   ❌ 檢查失敗: {e}")
            
        return result
    
    def generate_diagnostic_report(self):
        """生成診斷報告"""
        print("\n📋 移動停利平倉診斷報告")
        print("=" * 60)
        
        # 統計結果
        total_stages = len(self.results)
        passed_stages = sum(1 for r in self.results.values() if r.get('status') == 'PASSED')
        failed_stages = sum(1 for r in self.results.values() if r.get('status') == 'FAILED')
        error_stages = sum(1 for r in self.results.values() if r.get('status') == 'ERROR')
        
        print(f"📊 診斷統計:")
        print(f"   總階段數: {total_stages}")
        print(f"   ✅ 通過: {passed_stages}")
        print(f"   ❌ 失敗: {failed_stages}")
        print(f"   💥 錯誤: {error_stages}")
        
        # 收集所有問題
        all_issues = []
        for stage, result in self.results.items():
            if result.get('issues'):
                all_issues.extend([f"[{stage}] {issue}" for issue in result['issues']])
        
        print(f"\n🔍 發現的問題 ({len(all_issues)} 個):")
        if all_issues:
            for issue in all_issues:
                print(f"   ❌ {issue}")
        else:
            print("   ✅ 未發現明顯問題")
        
        # 保存詳細報告
        report_file = f"移動停利診斷報告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total_stages': total_stages,
                    'passed': passed_stages,
                    'failed': failed_stages,
                    'errors': error_stages
                },
                'results': self.results,
                'all_issues': all_issues
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 詳細報告已保存: {report_file}")

def main():
    """主診斷函數"""
    diagnostic = TrailingStopDiagnostic()
    diagnostic.run_full_diagnostic()

if __name__ == "__main__":
    main()
