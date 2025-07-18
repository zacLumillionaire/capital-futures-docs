#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
正式環境修復實施腳本
基於虛擬測試環境的成功經驗，安全地修復正式環境中的問題
"""

import os
import sys
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

class ProductionFixImplementer:
    """正式環境修復實施器"""
    
    def __init__(self):
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    def create_backup(self):
        """創建系統備份"""
        print("🔄 創建系統備份...")
        
        # 備份資料庫
        db_files = [
            "multi_group_strategy.db",
            "multi_group_strategy.db-wal",
            "multi_group_strategy.db-shm"
        ]
        
        for db_file in db_files:
            if os.path.exists(db_file):
                backup_path = self.backup_dir / f"{db_file}.backup_{self.timestamp}"
                shutil.copy2(db_file, backup_path)
                print(f"✅ 已備份: {db_file} → {backup_path}")
        
        # 備份關鍵代碼文件
        code_files = [
            "simple_integrated.py",
            "stop_loss_executor.py",
            "multi_group_database.py"
        ]
        
        for code_file in code_files:
            if os.path.exists(code_file):
                backup_path = self.backup_dir / f"{code_file}.backup_{self.timestamp}"
                shutil.copy2(code_file, backup_path)
                print(f"✅ 已備份: {code_file} → {backup_path}")
        
        print("✅ 系統備份完成")
        return True
    
    def test_standardize_function(self):
        """測試標準化函數"""
        print("\n🧪 測試標準化函數...")
        
        try:
            from stop_loss_executor import standardize_exit_reason
            
            test_cases = [
                "移動停利: LONG部位20%回撤觸發",
                "保護性停損: 價格突破停損線", 
                "初始停損: 價格觸及停損點",
                "手動出場: 用戶手動平倉",
                "FOK失敗: 訂單無法成交",
                "下單失敗: API調用失敗"
            ]
            
            print("標準化測試結果:")
            for case in test_cases:
                result = standardize_exit_reason(case)
                print(f"  原始: '{case}'")
                print(f"  標準化: '{result}'")
                print()
            
            # 驗證結果是否符合資料庫約束
            allowed_values = ['移動停利', '保護性停損', '初始停損', '手動出場', 'FOK失敗', '下單失敗']
            for case in test_cases:
                result = standardize_exit_reason(case)
                if result not in allowed_values:
                    print(f"❌ 標準化失敗: '{case}' → '{result}' 不在允許值中")
                    return False
            
            print("✅ 標準化函數測試通過")
            return True
            
        except Exception as e:
            print(f"❌ 標準化函數測試失敗: {e}")
            return False
    
    def check_database_constraints(self):
        """檢查資料庫約束"""
        print("\n🔍 檢查資料庫約束...")
        
        try:
            conn = sqlite3.connect("multi_group_strategy.db")
            cursor = conn.cursor()
            
            # 檢查position_records表的約束
            cursor.execute("PRAGMA table_info(position_records)")
            columns = cursor.fetchall()
            
            print("position_records表結構:")
            for col in columns:
                print(f"  {col[1]} {col[2]} {'NOT NULL' if col[3] else 'NULL'}")
            
            # 檢查約束定義
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='position_records'")
            table_sql = cursor.fetchone()[0]
            
            if "CHECK(exit_reason IN" in table_sql:
                print("✅ 找到exit_reason約束定義")
                # 提取約束內容
                start = table_sql.find("CHECK(exit_reason IN")
                end = table_sql.find(")", start) + 1
                constraint = table_sql[start:end]
                print(f"約束內容: {constraint}")
            else:
                print("⚠️ 未找到exit_reason約束定義")
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ 資料庫約束檢查失敗: {e}")
            return False
    
    def implement_database_fix(self):
        """實施資料庫約束修復"""
        print("\n🔧 實施資料庫約束修復...")
        
        # 這裡會修改simple_integrated.py中的平倉回調函數
        fix_code = '''
    def on_exit_fill(exit_order: dict, price: float, qty: int):
        """平倉成交回調函數 - 更新部位狀態為EXITED"""
        try:
            position_id = exit_order.get('position_id')
            exit_reason = exit_order.get('exit_reason', '平倉')
            
            # 🔧 新增：標準化出場原因
            from stop_loss_executor import standardize_exit_reason
            standardized_reason = standardize_exit_reason(exit_reason)
            
            if self.console_enabled:
                print(f"[MAIN] 🎯 收到平倉成交回調: 部位{position_id} @{price:.0f}")
                print(f"[MAIN] 📋 原始原因: '{exit_reason}' → 標準化: '{standardized_reason}'")
            
            # 使用標準化後的原因更新資料庫
            if hasattr(self, 'multi_group_db_manager') and self.multi_group_db_manager:
                success = self.multi_group_db_manager.update_position_exit(
                    position_id=position_id,
                    exit_price=price,
                    exit_time=datetime.now().strftime('%H:%M:%S'),
                    exit_reason=standardized_reason,  # 使用標準化後的原因
                    pnl=0.0
                )
                
                if success:
                    self.add_strategy_log(f"✅ 平倉記錄更新成功: 部位{position_id}")
                else:
                    self.add_strategy_log(f"❌ 平倉記錄更新失敗: 部位{position_id}")
            
        except Exception as e:
            self.add_strategy_log(f"❌ 平倉成交回調異常: {e}")
            # 記錄到備用日誌
            try:
                with open("exit_callback_errors.log", "a", encoding="utf-8") as f:
                    f.write(f"{datetime.now()}: 部位{position_id} 平倉回調失敗: {e}\\n")
            except:
                pass
        '''
        
        print("修復代碼已準備，需要手動應用到simple_integrated.py")
        print("請將上述代碼替換現有的on_exit_fill函數")
        
        return True
    
    def implement_duplicate_exit_fix(self):
        """實施重複平倉修復"""
        print("\n🔧 實施重複平倉修復...")
        
        cleanup_code = '''
    def init_multi_group_system(self):
        """初始化多組策略系統"""
        try:
            # 現有初始化代碼...
            
            # 🔧 新增：清理可能的舊平倉鎖定
            try:
                if hasattr(self, 'multi_group_position_manager') and self.multi_group_position_manager:
                    if hasattr(self.multi_group_position_manager, 'simplified_tracker'):
                        global_exit_manager = self.multi_group_position_manager.simplified_tracker.global_exit_manager
                        # 清理所有鎖定
                        if hasattr(global_exit_manager, 'clear_all_locks'):
                            global_exit_manager.clear_all_locks()
                            print("[INIT] 🧹 已清除所有平倉鎖定狀態")
                        else:
                            # 手動清理已知的鎖定
                            for position_id in range(1, 100):  # 清理可能的部位ID
                                try:
                                    global_exit_manager.clear_exit(position_id)
                                except:
                                    pass
                            print("[INIT] 🧹 已手動清除平倉鎖定狀態")
            except Exception as clear_error:
                print(f"[INIT] ⚠️ 清除鎖定失敗: {clear_error}")
        '''
        
        print("重複平倉修復代碼已準備")
        print("請將清理邏輯添加到init_multi_group_system函數中")
        
        return True
    
    def verify_fixes(self):
        """驗證修復效果"""
        print("\n✅ 驗證修復效果...")
        
        # 檢查修復是否正確應用
        checks = [
            ("標準化函數", self.test_standardize_function),
            ("資料庫約束", self.check_database_constraints)
        ]
        
        all_passed = True
        for check_name, check_func in checks:
            try:
                result = check_func()
                if result:
                    print(f"✅ {check_name}檢查通過")
                else:
                    print(f"❌ {check_name}檢查失敗")
                    all_passed = False
            except Exception as e:
                print(f"❌ {check_name}檢查異常: {e}")
                all_passed = False
        
        return all_passed
    
    def create_rollback_script(self):
        """創建回滾腳本"""
        print("\n📝 創建回滾腳本...")
        
        rollback_script = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
緊急回滾腳本 - {self.timestamp}
"""

import shutil
import os

def rollback():
    """執行回滾操作"""
    print("🔄 開始回滾操作...")
    
    # 回滾資料庫
    db_files = [
        "multi_group_strategy.db",
        "multi_group_strategy.db-wal", 
        "multi_group_strategy.db-shm"
    ]
    
    for db_file in db_files:
        backup_file = f"backups/{db_file}.backup_{self.timestamp}"
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, db_file)
            print(f"✅ 已回滾: {backup_file} → {db_file}")
    
    # 回滾代碼文件
    code_files = [
        "simple_integrated.py",
        "stop_loss_executor.py", 
        "multi_group_database.py"
    ]
    
    for code_file in code_files:
        backup_file = f"backups/{code_file}.backup_{self.timestamp}"
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, code_file)
            print(f"✅ 已回滾: {backup_file} → {code_file}")
    
    print("✅ 回滾完成")

if __name__ == "__main__":
    rollback()
'''
        
        rollback_path = f"rollback_{self.timestamp}.py"
        with open(rollback_path, "w", encoding="utf-8") as f:
            f.write(rollback_script)
        
        # 設置執行權限
        os.chmod(rollback_path, 0o755)
        
        print(f"✅ 回滾腳本已創建: {rollback_path}")
        return rollback_path

def main():
    """主執行函數"""
    print("🚀 正式環境修復實施開始")
    print("=" * 60)
    
    implementer = ProductionFixImplementer()
    
    # 步驟1：創建備份
    if not implementer.create_backup():
        print("❌ 備份失敗，終止修復")
        return False
    
    # 步驟2：測試標準化函數
    if not implementer.test_standardize_function():
        print("❌ 標準化函數測試失敗，終止修復")
        return False
    
    # 步驟3：檢查資料庫約束
    if not implementer.check_database_constraints():
        print("❌ 資料庫約束檢查失敗，終止修復")
        return False
    
    # 步驟4：實施修復
    implementer.implement_database_fix()
    implementer.implement_duplicate_exit_fix()
    
    # 步驟5：創建回滾腳本
    rollback_script = implementer.create_rollback_script()
    
    print("\n🎯 修復實施完成")
    print("=" * 60)
    print("📋 後續步驟:")
    print("1. 手動應用提供的修復代碼")
    print("2. 重啟交易系統")
    print("3. 監控系統運行狀況")
    print(f"4. 如需回滾，執行: python {rollback_script}")
    
    return True

if __name__ == "__main__":
    main()
