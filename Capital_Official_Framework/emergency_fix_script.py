# -*- coding: utf-8 -*-
"""
緊急修復腳本
修復LOG中發現的錯誤問題
"""

import sys
import os
import sqlite3
from datetime import datetime

def apply_emergency_fixes():
    """應用緊急修復"""
    print("🔧 緊急修復腳本")
    print("=" * 50)
    
    fixes_applied = []
    
    try:
        # 修復1: 檢查並修復資料庫約束
        print("\n🔧 修復1: 檢查資料庫約束")
        print("-" * 30)
        
        if fix_database_constraints():
            fixes_applied.append("資料庫約束修復")
            print("✅ 資料庫約束修復完成")
        else:
            print("⚠️ 資料庫約束修復跳過")
        
        # 修復2: 驗證代碼修復
        print("\n🔧 修復2: 驗證代碼修復")
        print("-" * 30)
        
        if verify_code_fixes():
            fixes_applied.append("代碼修復驗證")
            print("✅ 代碼修復驗證通過")
        else:
            print("❌ 代碼修復驗證失敗")
        
        # 修復3: 創建安全配置
        print("\n🔧 修復3: 創建安全配置")
        print("-" * 30)
        
        if create_safe_config():
            fixes_applied.append("安全配置創建")
            print("✅ 安全配置創建完成")
        else:
            print("⚠️ 安全配置創建跳過")
        
        # 總結
        print(f"\n📋 修復總結")
        print("-" * 30)
        print(f"✅ 已應用修復: {len(fixes_applied)}項")
        for fix in fixes_applied:
            print(f"  - {fix}")
        
        print(f"\n💡 下次交易建議:")
        print("1. 先運行診斷工具檢查系統狀態")
        print("2. 密切觀察LOG輸出，特別是:")
        print("   - [ORDER_MGR] 下單方向")
        print("   - [SIMPLIFIED_TRACKER] 回報處理")
        print("   - [RISK_ENGINE] 錯誤訊息")
        print("3. 對比期貨商系統的實際委託")
        print("4. 如果問題持續，考慮暫時禁用異步更新")
        
        return True
        
    except Exception as e:
        print(f"❌ 修復過程失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def fix_database_constraints():
    """修復資料庫約束問題"""
    try:
        db_path = "multi_group_strategy.db"
        if not os.path.exists(db_path):
            print(f"⚠️ 資料庫檔案不存在: {db_path}")
            return False
        
        # 備份資料庫
        backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"📋 資料庫已備份: {backup_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 檢查當前約束
        cursor.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='risk_management_states'
        """)
        
        result = cursor.fetchone()
        if result and "CHECK(update_reason IN" in result[0]:
            table_sql = result[0]
            
            # 檢查是否包含所需的值
            required_values = ["成交初始化", "簡化追蹤成交確認"]
            missing_values = []
            
            for value in required_values:
                if f"'{value}'" not in table_sql:
                    missing_values.append(value)
            
            if missing_values:
                print(f"⚠️ 發現缺少的約束值: {missing_values}")
                print("💡 建議手動更新資料庫約束或重新創建表格")
                return False
            else:
                print("✅ 資料庫約束檢查通過")
                return True
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 修復資料庫約束失敗: {e}")
        return False

def verify_code_fixes():
    """驗證代碼修復"""
    try:
        fixes_verified = []
        
        # 檢查1: risk_management_engine.py 的格式化修復
        risk_engine_path = "risk_management_engine.py"
        if os.path.exists(risk_engine_path):
            with open(risk_engine_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 檢查是否包含 None 值安全處理
            if "if current_stop is None:" in content:
                fixes_verified.append("風險管理引擎格式化修復")
                print("✅ 風險管理引擎格式化修復已應用")
            else:
                print("⚠️ 風險管理引擎格式化修復未找到")
        
        # 檢查2: multi_group_position_manager.py 的約束修復
        manager_path = "multi_group_position_manager.py"
        if os.path.exists(manager_path):
            with open(manager_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 檢查是否使用正確的 update_reason
            if 'update_reason="成交初始化"' in content:
                fixes_verified.append("部位管理器約束修復")
                print("✅ 部位管理器約束修復已應用")
            else:
                print("⚠️ 部位管理器約束修復未找到")
        
        return len(fixes_verified) > 0
        
    except Exception as e:
        print(f"❌ 驗證代碼修復失敗: {e}")
        return False

def create_safe_config():
    """創建安全配置"""
    try:
        config_content = """# 緊急安全配置
# 用於下次交易時的安全設置

# 1. 異步更新控制
ENABLE_ASYNC_UPDATE = True  # 可以設為 False 來禁用異步更新

# 2. 追價機制控制
ENABLE_RETRY_MECHANISM = True  # 可以設為 False 來禁用追價
MAX_RETRY_COUNT = 3  # 降低最大重試次數
MAX_SLIPPAGE_POINTS = 3  # 降低最大滑價容忍

# 3. 調試輸出控制
ENABLE_DETAILED_LOGGING = True  # 啟用詳細LOG
ENABLE_ORDER_DIRECTION_DEBUG = True  # 啟用方向調試

# 4. 安全檢查
ENABLE_DIRECTION_VALIDATION = True  # 啟用方向驗證
ENABLE_DUPLICATE_ORDER_CHECK = True  # 啟用重複訂單檢查

# 使用方法:
# 在系統啟動時載入這些配置
# 如果出現問題，可以快速調整這些參數
"""
        
        config_path = "emergency_safe_config.py"
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print(f"✅ 安全配置已創建: {config_path}")
        return True
        
    except Exception as e:
        print(f"❌ 創建安全配置失敗: {e}")
        return False

if __name__ == "__main__":
    print("🚨 緊急修復腳本")
    print("修復LOG中發現的錯誤問題")
    print("=" * 60)
    
    success = apply_emergency_fixes()
    
    if success:
        print("\n🎉 緊急修復完成!")
        print("\n📋 後續步驟:")
        print("1. 運行 emergency_order_diagnosis.py 進行診斷")
        print("2. 檢查修復效果")
        print("3. 準備下次交易測試")
    else:
        print("\n❌ 緊急修復過程中出現問題")
        print("請檢查錯誤訊息並手動處理")
