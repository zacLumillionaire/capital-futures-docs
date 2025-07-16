#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ID一致性深度分析工具
專門檢測group_id相關的混亂使用問題，包括主鍵ID vs 邏輯ID的混用
"""

import os
import sys
import re
import ast
import sqlite3
from datetime import datetime
from typing import Dict, List, Tuple, Set

# 添加當前目錄到路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

class IDConsistencyDeepAnalyzer:
    """ID一致性深度分析器"""
    
    def __init__(self):
        self.issues = []
        self.critical_issues = []
        self.warning_issues = []
        
        # 關鍵文件列表
        self.key_files = [
            "multi_group_database.py",
            "multi_group_position_manager.py", 
            "cumulative_profit_protection_manager.py",
            "optimized_risk_manager.py",
            "stop_loss_executor.py",
            "simplified_order_tracker.py"
        ]
        
        print("🔍 ID一致性深度分析工具")
        print("=" * 60)
        print("🎯 分析目標:")
        print("  1. group_id vs 主鍵ID混用問題")
        print("  2. position_id vs 主鍵ID混用問題")
        print("  3. 資料庫查詢邏輯一致性")
        print("  4. 函數參數命名混亂")
        print("  5. 變數命名不一致")
        print("=" * 60)
    
    def analyze_database_schema_consistency(self):
        """分析資料庫表結構一致性"""
        print("\n🔍 分析資料庫表結構一致性")
        print("-" * 50)
        
        # 檢查正式機和虛擬測試機
        databases = [
            ("正式機", "multi_group_strategy.db"),
            ("虛擬測試機", "test_virtual_strategy.db")
        ]
        
        schema_issues = []
        
        for env_name, db_path in databases:
            if not os.path.exists(db_path):
                schema_issues.append(f"❌ {env_name}資料庫不存在: {db_path}")
                continue
            
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                print(f"\n📊 {env_name} ({db_path}):")
                
                # 檢查strategy_groups表結構
                cursor.execute("PRAGMA table_info(strategy_groups)")
                sg_columns = {row[1]: row[2] for row in cursor.fetchall()}
                
                # 檢查position_records表結構
                cursor.execute("PRAGMA table_info(position_records)")
                pr_columns = {row[1]: row[2] for row in cursor.fetchall()}
                
                print(f"  strategy_groups欄位: {list(sg_columns.keys())}")
                print(f"  position_records欄位: {list(pr_columns.keys())}")
                
                # 檢查關鍵欄位
                critical_fields = {
                    'strategy_groups': ['id', 'group_id', 'date'],
                    'position_records': ['id', 'group_id', 'lot_id']
                }
                
                for table, fields in critical_fields.items():
                    table_columns = sg_columns if table == 'strategy_groups' else pr_columns
                    for field in fields:
                        if field not in table_columns:
                            schema_issues.append(f"❌ {env_name}.{table}缺少欄位: {field}")
                        else:
                            print(f"  ✅ {table}.{field}: {table_columns[field]}")
                
                # 檢查外鍵關係邏輯
                cursor.execute('''
                    SELECT COUNT(*) FROM position_records pr
                    LEFT JOIN strategy_groups sg ON pr.group_id = sg.group_id AND sg.date = date('now')
                    WHERE sg.id IS NULL AND pr.status = 'ACTIVE'
                ''')
                
                orphaned_positions = cursor.fetchone()[0]
                if orphaned_positions > 0:
                    schema_issues.append(f"⚠️ {env_name}有{orphaned_positions}個孤立部位（找不到對應策略組）")
                
                conn.close()
                
            except Exception as e:
                schema_issues.append(f"❌ {env_name}資料庫檢查失敗: {e}")
        
        if schema_issues:
            print(f"\n🚨 發現資料庫結構問題:")
            for issue in schema_issues:
                print(f"  {issue}")
            self.critical_issues.extend(schema_issues)
        else:
            print(f"\n✅ 資料庫結構一致性檢查通過")
    
    def analyze_sql_queries_in_code(self):
        """分析代碼中的SQL查詢邏輯"""
        print("\n🔍 分析代碼中的SQL查詢邏輯")
        print("-" * 50)
        
        sql_issues = []
        
        for filename in self.key_files:
            if not os.path.exists(filename):
                continue
            
            print(f"\n📄 分析文件: {filename}")
            
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # 查找SQL查詢
            sql_patterns = [
                r'WHERE\s+group_id\s*=\s*\?',
                r'WHERE\s+id\s*=\s*\?',
                r'WHERE\s+position_id\s*=\s*\?',
                r'SELECT.*FROM\s+strategy_groups',
                r'SELECT.*FROM\s+position_records',
                r'JOIN.*strategy_groups.*ON',
                r'JOIN.*position_records.*ON'
            ]
            
            for i, line in enumerate(lines, 1):
                line_stripped = line.strip()
                if not line_stripped or line_stripped.startswith('#'):
                    continue
                
                for pattern in sql_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        # 檢查是否有潛在的ID混用問題
                        if 'WHERE group_id = ?' in line and 'strategy_groups' in line:
                            # 這是正確的用法
                            continue
                        elif 'WHERE id = ?' in line and 'strategy_groups' in line:
                            # 檢查上下文是否明確這是主鍵查詢
                            context_lines = lines[max(0, i-3):min(len(lines), i+3)]
                            context = '\n'.join(context_lines)
                            if 'db_id' not in context.lower() and 'primary' not in context.lower():
                                sql_issues.append(f"⚠️ {filename}:{i} 可能的ID混用: {line_stripped}")
                        
                        # 檢查JOIN邏輯
                        if 'JOIN' in line.upper() and 'group_id' in line:
                            if 'pr.group_id = sg.group_id' not in line:
                                sql_issues.append(f"⚠️ {filename}:{i} JOIN邏輯可能有問題: {line_stripped}")
        
        if sql_issues:
            print(f"\n🚨 發現SQL查詢問題:")
            for issue in sql_issues:
                print(f"  {issue}")
            self.warning_issues.extend(sql_issues)
        else:
            print(f"\n✅ SQL查詢邏輯檢查通過")
    
    def analyze_function_parameters(self):
        """分析函數參數命名一致性"""
        print("\n🔍 分析函數參數命名一致性")
        print("-" * 50)
        
        param_issues = []
        
        for filename in self.key_files:
            if not os.path.exists(filename):
                continue
            
            print(f"\n📄 分析文件: {filename}")
            
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 使用AST解析Python代碼
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_name = node.name
                        
                        # 檢查函數參數
                        for arg in node.args.args:
                            arg_name = arg.arg
                            
                            # 檢查可能的ID參數混亂
                            if 'group' in arg_name and 'id' in arg_name:
                                if arg_name not in ['group_id', 'group_db_id', 'logical_group_id', 'group_pk']:
                                    param_issues.append(f"⚠️ {filename} {func_name}() 參數命名不規範: {arg_name}")
                            
                            if 'position' in arg_name and 'id' in arg_name:
                                if arg_name not in ['position_id', 'position_pk']:
                                    param_issues.append(f"⚠️ {filename} {func_name}() 參數命名不規範: {arg_name}")
                            
                            # 檢查簡單的'id'參數
                            if arg_name == 'id':
                                param_issues.append(f"⚠️ {filename} {func_name}() 使用模糊參數名: id (建議使用更明確的名稱)")
                
            except Exception as e:
                param_issues.append(f"❌ {filename} AST解析失敗: {e}")
        
        if param_issues:
            print(f"\n🚨 發現函數參數問題:")
            for issue in param_issues:
                print(f"  {issue}")
            self.warning_issues.extend(param_issues)
        else:
            print(f"\n✅ 函數參數命名檢查通過")
    
    def analyze_variable_naming_consistency(self):
        """分析變數命名一致性"""
        print("\n🔍 分析變數命名一致性")
        print("-" * 50)
        
        var_issues = []
        
        # 定義標準命名模式
        standard_patterns = {
            'group_id': r'\bgroup_id\b',
            'group_db_id': r'\bgroup_db_id\b',
            'group_pk': r'\bgroup_pk\b',
            'logical_group_id': r'\blogical_group_id\b',
            'position_id': r'\bposition_id\b',
            'position_pk': r'\bposition_pk\b'
        }
        
        # 檢查非標準命名
        non_standard_patterns = [
            r'\bgid\b', r'\bgrp_id\b', r'\bgroup_identifier\b',
            r'\bpos_id\b', r'\bposition_identifier\b',
            r'\bid\s*=', r'\bid\s*\)', r'\bid\s*,'
        ]
        
        for filename in self.key_files:
            if not os.path.exists(filename):
                continue
            
            print(f"\n📄 分析文件: {filename}")
            
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # 檢查非標準命名
            for i, line in enumerate(lines, 1):
                line_stripped = line.strip()
                if not line_stripped or line_stripped.startswith('#'):
                    continue
                
                for pattern in non_standard_patterns:
                    if re.search(pattern, line):
                        # 排除一些合理的使用情況
                        if 'PRIMARY KEY' in line.upper() or 'AUTOINCREMENT' in line.upper():
                            continue
                        if 'def ' in line and pattern == r'\bid\s*\)':
                            continue
                        
                        var_issues.append(f"⚠️ {filename}:{i} 非標準命名: {line_stripped}")
        
        if var_issues:
            print(f"\n🚨 發現變數命名問題:")
            for issue in var_issues[:10]:  # 只顯示前10個
                print(f"  {issue}")
            if len(var_issues) > 10:
                print(f"  ... 還有{len(var_issues)-10}個類似問題")
            self.warning_issues.extend(var_issues)
        else:
            print(f"\n✅ 變數命名一致性檢查通過")
    
    def check_critical_id_usage_patterns(self):
        """檢查關鍵ID使用模式"""
        print("\n🔍 檢查關鍵ID使用模式")
        print("-" * 50)
        
        critical_patterns = []
        
        # 檢查可能的關鍵問題模式
        problem_patterns = [
            {
                'pattern': r'get_strategy_group_info\(\s*(\w+)\s*\)',
                'description': '檢查get_strategy_group_info的參數是否為邏輯group_id',
                'file_focus': ['multi_group_position_manager.py', 'multi_group_database.py']
            },
            {
                'pattern': r'WHERE\s+group_id\s*=\s*\?\s*.*strategy_groups',
                'description': '檢查strategy_groups表的group_id查詢',
                'file_focus': ['multi_group_database.py']
            },
            {
                'pattern': r'WHERE\s+id\s*=\s*\?\s*.*strategy_groups',
                'description': '檢查strategy_groups表的主鍵查詢',
                'file_focus': ['multi_group_database.py']
            }
        ]
        
        for pattern_info in problem_patterns:
            pattern = pattern_info['pattern']
            description = pattern_info['description']
            files_to_check = pattern_info.get('file_focus', self.key_files)
            
            print(f"\n🔍 {description}")
            
            for filename in files_to_check:
                if not os.path.exists(filename):
                    continue
                
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    # 找到匹配的行號
                    line_num = content[:match.start()].count('\n') + 1
                    line_content = lines[line_num - 1].strip()
                    
                    print(f"  📍 {filename}:{line_num} {line_content}")
                    
                    # 分析上下文
                    context_start = max(0, line_num - 3)
                    context_end = min(len(lines), line_num + 3)
                    context = lines[context_start:context_end]
                    
                    # 檢查是否有明確的註釋說明
                    has_clear_comment = any('主鍵' in line or 'DB_ID' in line or 'logical' in line 
                                          for line in context)
                    
                    if not has_clear_comment:
                        critical_patterns.append(f"⚠️ {filename}:{line_num} {description} - 缺少明確註釋")
        
        if critical_patterns:
            print(f"\n🚨 發現關鍵ID使用問題:")
            for issue in critical_patterns:
                print(f"  {issue}")
            self.critical_issues.extend(critical_patterns)
        else:
            print(f"\n✅ 關鍵ID使用模式檢查通過")
    
    def generate_comprehensive_report(self):
        """生成綜合分析報告"""
        print("\n" + "=" * 60)
        print("📊 ID一致性深度分析報告")
        print("=" * 60)
        
        total_issues = len(self.critical_issues) + len(self.warning_issues)
        
        print(f"分析時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"分析文件數: {len(self.key_files)}")
        print(f"發現問題總數: {total_issues}")
        print(f"  關鍵問題: {len(self.critical_issues)}")
        print(f"  警告問題: {len(self.warning_issues)}")
        
        if self.critical_issues:
            print(f"\n🚨 關鍵問題 (需要立即修復):")
            for i, issue in enumerate(self.critical_issues, 1):
                print(f"  {i}. {issue}")
        
        if self.warning_issues:
            print(f"\n⚠️ 警告問題 (建議修復):")
            for i, issue in enumerate(self.warning_issues[:5], 1):  # 只顯示前5個
                print(f"  {i}. {issue}")
            if len(self.warning_issues) > 5:
                print(f"  ... 還有{len(self.warning_issues)-5}個警告問題")
        
        # 生成修復建議
        print(f"\n💡 修復建議:")
        if len(self.critical_issues) > 0:
            print("  1. 🔧 立即修復關鍵問題，特別是ID混用問題")
            print("  2. 📋 統一使用明確的參數命名 (group_id vs group_db_id)")
            print("  3. 🔍 為所有ID相關查詢添加明確註釋")
        
        if len(self.warning_issues) > 0:
            print("  4. ⚠️ 逐步修復警告問題，提高代碼可維護性")
            print("  5. 📝 建立ID命名規範文檔")
        
        if total_issues == 0:
            print("  🎉 ID一致性良好，無需修復！")
        
        # 保存詳細報告
        report_file = f"id_consistency_deep_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("ID一致性深度分析詳細報告\n")
            f.write("=" * 60 + "\n")
            f.write(f"分析時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"總問題數: {total_issues}\n\n")
            
            f.write("關鍵問題:\n")
            for issue in self.critical_issues:
                f.write(f"  {issue}\n")
            
            f.write("\n警告問題:\n")
            for issue in self.warning_issues:
                f.write(f"  {issue}\n")
        
        print(f"\n📄 詳細報告已保存至: {report_file}")
        
        return total_issues == 0
    
    def run_deep_analysis(self):
        """運行深度分析"""
        print("🚀 開始ID一致性深度分析")
        
        # 執行各項分析
        self.analyze_database_schema_consistency()
        self.analyze_sql_queries_in_code()
        self.analyze_function_parameters()
        self.analyze_variable_naming_consistency()
        self.check_critical_id_usage_patterns()
        
        # 生成綜合報告
        success = self.generate_comprehensive_report()
        
        return success

if __name__ == "__main__":
    analyzer = IDConsistencyDeepAnalyzer()
    success = analyzer.run_deep_analysis()
    
    if success:
        print("\n🎉 ID一致性深度分析完成：未發現嚴重問題！")
    else:
        print("\n⚠️ ID一致性深度分析完成：發現需要修復的問題")
    
    exit(0 if success else 1)
