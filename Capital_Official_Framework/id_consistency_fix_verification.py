#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ID一致性修復驗證工具
驗證所有ID一致性修復是否生效
"""

import os
import sys
import re
import sqlite3
from datetime import datetime
from typing import Dict, List, Tuple

# 添加當前目錄到路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

class IDConsistencyFixVerifier:
    """ID一致性修復驗證器"""
    
    def __init__(self):
        self.verification_results = []
        self.passed_checks = 0
        self.failed_checks = 0
        
        print("🔍 ID一致性修復驗證工具")
        print("=" * 50)
        print("🎯 驗證目標:")
        print("  1. JOIN邏輯修復驗證")
        print("  2. 外鍵約束修復驗證")
        print("  3. 函數參數命名修復驗證")
        print("  4. SQL查詢AS別名驗證")
        print("  5. 變數命名規範驗證")
        print("=" * 50)
    
    def verify_join_logic_fixes(self):
        """驗證JOIN邏輯修復"""
        print("\n🔍 驗證JOIN邏輯修復")
        print("-" * 30)
        
        files_to_check = [
            "multi_group_database.py",
            "optimized_risk_manager.py"
        ]
        
        join_issues = []
        
        for filename in files_to_check:
            if not os.path.exists(filename):
                continue
            
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # 檢查是否還有錯誤的JOIN邏輯
            wrong_join_pattern = r'JOIN.*strategy_groups.*ON.*\.id\s*=.*\.group_id'
            matches = re.finditer(wrong_join_pattern, content, re.IGNORECASE)
            
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                line_content = lines[line_num - 1].strip()
                join_issues.append(f"❌ {filename}:{line_num} 仍有錯誤JOIN: {line_content}")
            
            # 檢查正確的JOIN邏輯
            correct_join_pattern = r'JOIN.*strategy_groups.*ON.*\.group_id\s*=.*\.group_id'
            correct_matches = list(re.finditer(correct_join_pattern, content, re.IGNORECASE))
            
            if correct_matches:
                print(f"✅ {filename}: 發現{len(correct_matches)}個正確的JOIN邏輯")
                self.passed_checks += len(correct_matches)
        
        if join_issues:
            print("❌ JOIN邏輯修復未完成:")
            for issue in join_issues:
                print(f"  {issue}")
            self.failed_checks += len(join_issues)
        else:
            print("✅ JOIN邏輯修復驗證通過")
    
    def verify_foreign_key_fixes(self):
        """驗證外鍵約束修復"""
        print("\n🔍 驗證外鍵約束修復")
        print("-" * 30)
        
        with open("multi_group_database.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查是否還有錯誤的外鍵定義
        wrong_fk_pattern = r'FOREIGN KEY.*REFERENCES strategy_groups\(id\)'
        wrong_matches = re.findall(wrong_fk_pattern, content, re.IGNORECASE)
        
        if wrong_matches:
            print(f"❌ 仍有{len(wrong_matches)}個錯誤的外鍵定義")
            self.failed_checks += len(wrong_matches)
        else:
            print("✅ 外鍵約束修復驗證通過")
            self.passed_checks += 1
        
        # 檢查是否有註釋說明
        comment_pattern = r'修復：外鍵應該引用邏輯group_id'
        comment_matches = re.findall(comment_pattern, content)
        
        if comment_matches:
            print(f"✅ 發現{len(comment_matches)}個修復註釋")
            self.passed_checks += len(comment_matches)
    
    def verify_parameter_naming_fixes(self):
        """驗證函數參數命名修復"""
        print("\n🔍 驗證函數參數命名修復")
        print("-" * 30)
        
        with open("cumulative_profit_protection_manager.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查是否還有舊的參數名
        old_param_pattern = r'successful_exit_position_id'
        old_matches = re.findall(old_param_pattern, content)
        
        if old_matches:
            print(f"❌ 仍有{len(old_matches)}個舊的參數名")
            self.failed_checks += len(old_matches)
        else:
            print("✅ 舊參數名已全部替換")
            self.passed_checks += 1
        
        # 檢查新的參數名
        new_param_pattern = r'trigger_position_id'
        new_matches = re.findall(new_param_pattern, content)
        
        if new_matches:
            print(f"✅ 發現{len(new_matches)}個新的參數名")
            self.passed_checks += 1
        else:
            print("❌ 未發現新的參數名")
            self.failed_checks += 1
    
    def verify_sql_alias_improvements(self):
        """驗證SQL查詢AS別名改進"""
        print("\n🔍 驗證SQL查詢AS別名改進")
        print("-" * 30)
        
        files_to_check = [
            "cumulative_profit_protection_manager.py",
            "multi_group_database.py"
        ]
        
        alias_count = 0
        
        for filename in files_to_check:
            if not os.path.exists(filename):
                continue
            
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 檢查AS別名使用
            alias_patterns = [
                r'id AS position_pk',
                r'id AS group_pk',
                r'group_id AS logical_group_id'
            ]
            
            for pattern in alias_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                alias_count += len(matches)
        
        if alias_count > 0:
            print(f"✅ 發現{alias_count}個AS別名使用")
            self.passed_checks += 1
        else:
            print("❌ 未發現AS別名改進")
            self.failed_checks += 1
    
    def verify_variable_naming_fixes(self):
        """驗證變數命名規範修復"""
        print("\n🔍 驗證變數命名規範修復")
        print("-" * 30)
        
        with open("simplified_order_tracker.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查是否還有gid變數
        gid_pattern = r'\bgid\b'
        gid_matches = re.findall(gid_pattern, content)
        
        if gid_matches:
            print(f"❌ 仍有{len(gid_matches)}個gid變數")
            self.failed_checks += len(gid_matches)
        else:
            print("✅ gid變數已全部替換")
            self.passed_checks += 1
        
        # 檢查是否有正確的group_id使用
        group_id_pattern = r'group_id'
        group_id_matches = re.findall(group_id_pattern, content)
        
        if group_id_matches:
            print(f"✅ 發現{len(group_id_matches)}個group_id使用")
            self.passed_checks += 1
    
    def test_database_operations(self):
        """測試資料庫操作是否正常"""
        print("\n🔍 測試資料庫操作")
        print("-" * 30)
        
        databases = [
            ("正式機", "multi_group_strategy.db"),
            ("虛擬測試機", "test_virtual_strategy.db")
        ]
        
        for env_name, db_path in databases:
            if not os.path.exists(db_path):
                print(f"⚠️ {env_name}資料庫不存在: {db_path}")
                continue
            
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # 測試修復後的JOIN查詢
                cursor.execute('''
                    SELECT COUNT(*) 
                    FROM position_records pr
                    LEFT JOIN strategy_groups sg ON pr.group_id = sg.group_id AND sg.date = date('now')
                ''')
                
                count = cursor.fetchone()[0]
                print(f"✅ {env_name}JOIN查詢正常: {count}條記錄")
                self.passed_checks += 1
                
                conn.close()
                
            except Exception as e:
                print(f"❌ {env_name}資料庫操作失敗: {e}")
                self.failed_checks += 1
    
    def run_comprehensive_verification(self):
        """運行綜合驗證"""
        print("🚀 開始ID一致性修復驗證")
        
        start_time = datetime.now()
        
        # 執行各項驗證
        self.verify_join_logic_fixes()
        self.verify_foreign_key_fixes()
        self.verify_parameter_naming_fixes()
        self.verify_sql_alias_improvements()
        self.verify_variable_naming_fixes()
        self.test_database_operations()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 生成驗證報告
        self.generate_verification_report(duration)
        
        return self.failed_checks == 0
    
    def generate_verification_report(self, duration: float):
        """生成驗證報告"""
        print("\n" + "=" * 50)
        print("📊 ID一致性修復驗證報告")
        print("=" * 50)
        
        total_checks = self.passed_checks + self.failed_checks
        success_rate = (self.passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        print(f"驗證時間: {duration:.2f} 秒")
        print(f"總檢查項目: {total_checks}")
        print(f"通過檢查: {self.passed_checks}")
        print(f"失敗檢查: {self.failed_checks}")
        print(f"成功率: {success_rate:.1f}%")
        
        if self.failed_checks == 0:
            print("\n🎉 所有修復驗證通過！")
            print("💡 建議:")
            print("  1. 運行生產環境檢查工具確認實際效果")
            print("  2. 執行實際交易測試驗證系統穩定性")
            print("  3. 監控後續運行中的ID一致性問題")
        else:
            print(f"\n⚠️ 有{self.failed_checks}項檢查未通過")
            print("💡 建議:")
            print("  1. 檢查修復是否完整")
            print("  2. 重新運行修復工具")
            print("  3. 手動檢查失敗的項目")
        
        # 保存報告
        report_file = f"id_fix_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("ID一致性修復驗證報告\n")
            f.write("=" * 50 + "\n")
            f.write(f"驗證時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"總檢查項目: {total_checks}\n")
            f.write(f"通過檢查: {self.passed_checks}\n")
            f.write(f"失敗檢查: {self.failed_checks}\n")
            f.write(f"成功率: {success_rate:.1f}%\n")
        
        print(f"\n📄 詳細報告已保存至: {report_file}")

if __name__ == "__main__":
    verifier = IDConsistencyFixVerifier()
    success = verifier.run_comprehensive_verification()
    
    if success:
        print("\n✅ ID一致性修復驗證完成：所有修復生效！")
    else:
        print("\n⚠️ ID一致性修復驗證完成：部分修復需要進一步檢查")
    
    exit(0 if success else 1)
