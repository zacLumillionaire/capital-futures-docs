#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多角度資料庫問題診斷工具
全面檢測建倉資料庫更新失敗問題
"""

import sqlite3
import os
import sys
import traceback
import threading
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

class MultiAngleDatabaseDiagnostic:
    """多角度資料庫診斷器"""
    
    def __init__(self, db_path: str = "multi_group_strategy.db"):
        self.db_path = db_path
        self.results = {}
        self.errors = []
        
    def run_all_diagnostics(self):
        """執行所有診斷檢查"""
        print("🚀 多角度資料庫問題診斷開始")
        print("=" * 60)
        
        # 角度1: 資料庫結構驗證
        self.results['structure'] = self.check_database_structure()
        
        # 角度2: 運行時資料庫狀態檢測
        self.results['runtime_state'] = self.check_runtime_database_state()
        
        # 角度3: 代碼執行路徑追蹤
        self.results['code_path'] = self.trace_code_execution_path()
        
        # 角度4: 數據類型和值檢測
        self.results['data_types'] = self.check_data_types_and_values()
        
        # 角度5: 併發和競爭條件檢測
        self.results['concurrency'] = self.check_concurrency_issues()
        
        # 角度6: 系統環境和依賴檢測
        self.results['environment'] = self.check_system_environment()
        
        # 生成綜合報告
        self.generate_comprehensive_report()
        
    def check_database_structure(self) -> Dict:
        """角度1: 資料庫結構驗證"""
        print("\n🔍 角度1: 資料庫結構驗證")
        print("-" * 40)
        
        result = {'status': 'UNKNOWN', 'issues': [], 'details': {}}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 檢查表是否存在
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='position_records'
                """)
                if not cursor.fetchone():
                    result['issues'].append("position_records 表不存在")
                    return result
                
                # 獲取表結構
                cursor.execute("PRAGMA table_info(position_records)")
                columns = cursor.fetchall()
                result['details']['columns'] = columns
                
                # 檢查關鍵字段
                column_names = [col[1] for col in columns]
                required_fields = ['retry_count', 'max_slippage_points']
                for field in required_fields:
                    if field not in column_names:
                        result['issues'].append(f"缺少字段: {field}")
                
                # 獲取約束信息
                cursor.execute("""
                    SELECT sql FROM sqlite_master 
                    WHERE type='table' AND name='position_records'
                """)
                table_sql = cursor.fetchone()[0]
                result['details']['table_sql'] = table_sql
                
                # 檢查約束是否正確
                if 'retry_count IS NULL OR' in table_sql:
                    print("✅ retry_count 約束已修復")
                else:
                    result['issues'].append("retry_count 約束未修復")
                    
                if 'max_slippage_points IS NULL OR' in table_sql:
                    print("✅ max_slippage_points 約束已修復")
                else:
                    result['issues'].append("max_slippage_points 約束未修復")
                
                # 檢查索引
                cursor.execute("PRAGMA index_list(position_records)")
                indexes = cursor.fetchall()
                result['details']['indexes'] = indexes
                
                result['status'] = 'PASSED' if not result['issues'] else 'FAILED'
                
        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            self.errors.append(f"結構檢查錯誤: {e}")
            
        return result
    
    def check_runtime_database_state(self) -> Dict:
        """角度2: 運行時資料庫狀態檢測"""
        print("\n🔍 角度2: 運行時資料庫狀態檢測")
        print("-" * 40)
        
        result = {'status': 'UNKNOWN', 'issues': [], 'details': {}}
        
        try:
            # 檢查資料庫文件狀態
            if not os.path.exists(self.db_path):
                result['issues'].append("資料庫文件不存在")
                return result
                
            file_stat = os.stat(self.db_path)
            result['details']['file_size'] = file_stat.st_size
            result['details']['last_modified'] = datetime.fromtimestamp(file_stat.st_mtime)
            
            # 檢查資料庫連接
            with sqlite3.connect(self.db_path, timeout=1.0) as conn:
                cursor = conn.cursor()
                
                # 檢查資料庫版本
                cursor.execute("SELECT sqlite_version()")
                sqlite_version = cursor.fetchone()[0]
                result['details']['sqlite_version'] = sqlite_version
                print(f"   SQLite 版本: {sqlite_version}")
                
                # 檢查資料庫完整性
                cursor.execute("PRAGMA integrity_check")
                integrity = cursor.fetchone()[0]
                result['details']['integrity'] = integrity
                if integrity != 'ok':
                    result['issues'].append(f"資料庫完整性問題: {integrity}")
                
                # 檢查當前連接數
                cursor.execute("PRAGMA database_list")
                databases = cursor.fetchall()
                result['details']['databases'] = databases
                
                # 檢查鎖定狀態
                try:
                    cursor.execute("BEGIN IMMEDIATE")
                    cursor.execute("ROLLBACK")
                    print("✅ 資料庫無鎖定問題")
                except sqlite3.OperationalError as e:
                    result['issues'].append(f"資料庫鎖定: {e}")
                
                # 檢查最近的部位記錄
                cursor.execute("""
                    SELECT id, retry_count, max_slippage_points, status, created_at
                    FROM position_records 
                    ORDER BY id DESC LIMIT 5
                """)
                recent_positions = cursor.fetchall()
                result['details']['recent_positions'] = recent_positions
                
                # 檢查 None 值
                cursor.execute("""
                    SELECT COUNT(*) FROM position_records 
                    WHERE retry_count IS NULL OR max_slippage_points IS NULL
                """)
                null_count = cursor.fetchone()[0]
                result['details']['null_values_count'] = null_count
                if null_count > 0:
                    result['issues'].append(f"仍有 {null_count} 個記錄包含 None 值")
                
                result['status'] = 'PASSED' if not result['issues'] else 'FAILED'
                
        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            self.errors.append(f"運行時狀態檢查錯誤: {e}")
            
        return result
    
    def trace_code_execution_path(self) -> Dict:
        """角度3: 代碼執行路徑追蹤"""
        print("\n🔍 角度3: 代碼執行路徑追蹤")
        print("-" * 40)
        
        result = {'status': 'UNKNOWN', 'issues': [], 'details': {}}
        
        try:
            # 檢查關鍵文件是否存在
            key_files = [
                'multi_group_position_manager.py',
                'multi_group_database.py',
                'simplified_order_tracker.py'
            ]
            
            for file_name in key_files:
                if os.path.exists(file_name):
                    print(f"✅ 找到文件: {file_name}")
                    
                    # 檢查文件修改時間
                    file_stat = os.stat(file_name)
                    mod_time = datetime.fromtimestamp(file_stat.st_mtime)
                    result['details'][f'{file_name}_modified'] = mod_time
                    
                    # 檢查關鍵方法
                    with open(file_name, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    if file_name == 'multi_group_database.py':
                        # 檢查 confirm_position_filled 方法
                        if 'def confirm_position_filled' in content:
                            print(f"   ✅ 找到 confirm_position_filled 方法")
                        else:
                            result['issues'].append(f"{file_name} 缺少 confirm_position_filled 方法")
                            
                        # 檢查約束修復
                        if 'retry_count IS NULL OR' in content:
                            print(f"   ✅ {file_name} 包含修復的約束")
                        else:
                            result['issues'].append(f"{file_name} 約束未修復")
                            
                    elif file_name == 'multi_group_position_manager.py':
                        # 檢查成交回調方法
                        if '_update_group_positions_on_fill' in content:
                            print(f"   ✅ 找到 _update_group_positions_on_fill 方法")
                        else:
                            result['issues'].append(f"{file_name} 缺少關鍵回調方法")
                else:
                    result['issues'].append(f"找不到關鍵文件: {file_name}")
            
            # 模擬執行路徑測試
            try:
                # 導入模組測試
                sys.path.append('.')
                import multi_group_database
                db_manager = multi_group_database.MultiGroupDatabase()
                print("✅ 成功導入 multi_group_database 模組")
                result['details']['module_import'] = 'SUCCESS'
            except Exception as e:
                result['issues'].append(f"模組導入失敗: {e}")
                result['details']['module_import'] = f'FAILED: {e}'
            
            result['status'] = 'PASSED' if not result['issues'] else 'FAILED'
            
        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            self.errors.append(f"代碼路徑追蹤錯誤: {e}")
            
        return result
    
    def check_data_types_and_values(self) -> Dict:
        """角度4: 數據類型和值檢測"""
        print("\n🔍 角度4: 數據類型和值檢測")
        print("-" * 40)
        
        result = {'status': 'UNKNOWN', 'issues': [], 'details': {}}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 檢查字段類型
                cursor.execute("PRAGMA table_info(position_records)")
                columns = cursor.fetchall()
                
                for col in columns:
                    col_name = col[1]
                    col_type = col[2]
                    if col_name in ['retry_count', 'max_slippage_points']:
                        result['details'][f'{col_name}_type'] = col_type
                        print(f"   {col_name}: {col_type}")
                
                # 測試插入 None 值
                try:
                    cursor.execute("""
                        INSERT INTO position_records 
                        (group_id, lot_id, direction, retry_count, max_slippage_points, status)
                        VALUES (9999, 1, 'LONG', NULL, NULL, 'PENDING')
                    """)
                    test_id = cursor.lastrowid
                    print("✅ None 值插入測試成功")
                    
                    # 清理測試數據
                    cursor.execute("DELETE FROM position_records WHERE id = ?", (test_id,))
                    conn.commit()
                    
                except Exception as e:
                    if 'not supported between instances' in str(e):
                        result['issues'].append("None 值約束問題仍然存在")
                        print(f"❌ None 值插入失敗: {e}")
                    else:
                        print(f"✅ None 值處理正常 (其他約束錯誤: {e})")
                
                # 檢查現有數據的類型
                cursor.execute("""
                    SELECT id, retry_count, max_slippage_points, 
                           typeof(retry_count), typeof(max_slippage_points)
                    FROM position_records 
                    WHERE status IN ('ACTIVE', 'PENDING')
                    ORDER BY id DESC LIMIT 10
                """)
                
                data_samples = cursor.fetchall()
                result['details']['data_samples'] = data_samples
                
                for sample in data_samples:
                    pos_id, retry_count, max_slippage, retry_type, slippage_type = sample
                    if retry_type == 'null' or slippage_type == 'null':
                        result['issues'].append(f"部位 {pos_id} 仍有 null 值: retry_count={retry_type}, max_slippage_points={slippage_type}")
                
                result['status'] = 'PASSED' if not result['issues'] else 'FAILED'
                
        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            self.errors.append(f"數據類型檢查錯誤: {e}")
            
        return result
    
    def check_concurrency_issues(self) -> Dict:
        """角度5: 併發和競爭條件檢測"""
        print("\n🔍 角度5: 併發和競爭條件檢測")
        print("-" * 40)
        
        result = {'status': 'UNKNOWN', 'issues': [], 'details': {}}
        
        try:
            # 檢查是否有多個進程在使用資料庫
            import psutil
            
            current_pid = os.getpid()
            python_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'python' in proc.info['name'].lower():
                        if proc.info['pid'] != current_pid:
                            python_processes.append(proc.info)
                except:
                    continue
            
            result['details']['python_processes'] = len(python_processes)
            print(f"   發現 {len(python_processes)} 個其他 Python 進程")
            
            if len(python_processes) > 0:
                result['issues'].append(f"可能有 {len(python_processes)} 個其他 Python 進程在運行")
            
            # 測試併發訪問
            def test_concurrent_access():
                try:
                    with sqlite3.connect(self.db_path, timeout=0.1) as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM position_records")
                        return True
                except sqlite3.OperationalError:
                    return False
            
            concurrent_success = test_concurrent_access()
            result['details']['concurrent_access'] = concurrent_success
            
            if not concurrent_success:
                result['issues'].append("資料庫可能被其他進程鎖定")
            
            result['status'] = 'PASSED' if not result['issues'] else 'WARNING'
            
        except ImportError:
            result['status'] = 'SKIPPED'
            result['details']['reason'] = 'psutil 模組未安裝'
        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            self.errors.append(f"併發檢查錯誤: {e}")
            
        return result
    
    def check_system_environment(self) -> Dict:
        """角度6: 系統環境和依賴檢測"""
        print("\n🔍 角度6: 系統環境和依賴檢測")
        print("-" * 40)
        
        result = {'status': 'UNKNOWN', 'issues': [], 'details': {}}
        
        try:
            # Python 版本
            python_version = sys.version
            result['details']['python_version'] = python_version
            print(f"   Python 版本: {python_version}")
            
            # SQLite 版本
            sqlite_version = sqlite3.sqlite_version
            result['details']['sqlite_version'] = sqlite_version
            print(f"   SQLite 版本: {sqlite_version}")
            
            # 檢查 SQLite 編譯選項
            with sqlite3.connect(':memory:') as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA compile_options")
                compile_options = [row[0] for row in cursor.fetchall()]
                result['details']['sqlite_compile_options'] = compile_options
            
            # 檢查工作目錄
            cwd = os.getcwd()
            result['details']['working_directory'] = cwd
            print(f"   工作目錄: {cwd}")
            
            # 檢查資料庫文件權限
            if os.path.exists(self.db_path):
                file_stat = os.stat(self.db_path)
                result['details']['file_permissions'] = oct(file_stat.st_mode)
                print(f"   資料庫文件權限: {oct(file_stat.st_mode)}")
            
            result['status'] = 'PASSED'
            
        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            self.errors.append(f"環境檢查錯誤: {e}")
            
        return result
    
    def generate_comprehensive_report(self):
        """生成綜合診斷報告"""
        print("\n📋 綜合診斷報告")
        print("=" * 60)
        
        # 統計結果
        passed = sum(1 for r in self.results.values() if r.get('status') == 'PASSED')
        failed = sum(1 for r in self.results.values() if r.get('status') == 'FAILED')
        errors = sum(1 for r in self.results.values() if r.get('status') == 'ERROR')
        warnings = sum(1 for r in self.results.values() if r.get('status') == 'WARNING')
        
        print(f"✅ 通過: {passed}")
        print(f"❌ 失敗: {failed}")
        print(f"⚠️ 警告: {warnings}")
        print(f"💥 錯誤: {errors}")
        
        # 關鍵發現
        print(f"\n🔍 關鍵發現:")
        
        all_issues = []
        for angle, result in self.results.items():
            if result.get('issues'):
                all_issues.extend([f"[{angle}] {issue}" for issue in result['issues']])
        
        if all_issues:
            for issue in all_issues:
                print(f"   ❌ {issue}")
        else:
            print("   ✅ 未發現明顯問題")
        
        # 保存詳細報告
        report_file = f"多角度診斷報告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        import json
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'passed': passed,
                    'failed': failed,
                    'warnings': warnings,
                    'errors': errors
                },
                'results': self.results,
                'all_issues': all_issues,
                'errors': self.errors
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 詳細報告已保存: {report_file}")

def main():
    """主診斷函數"""
    diagnostic = MultiAngleDatabaseDiagnostic()
    diagnostic.run_all_diagnostics()

if __name__ == "__main__":
    main()
