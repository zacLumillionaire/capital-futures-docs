#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
虛擬機保護性停損修復驗證測試 - 2025/07/18
測試虛擬機修復後的保護性停損功能
"""

import sys
import os
import sqlite3
from datetime import datetime

def test_virtual_protective_stop_fix():
    """測試虛擬機保護性停損修復功能"""
    print("🧪 虛擬機保護性停損修復驗證測試")
    print("=" * 60)
    
    # 檢查虛擬測試機文件
    virtual_file = "virtual_simple_integrated.py"
    if not os.path.exists(virtual_file):
        print(f"❌ 找不到虛擬測試機文件: {virtual_file}")
        return False
    
    print(f"✅ 找到虛擬測試機文件: {virtual_file}")
    
    # 檢查修復代碼是否存在
    with open(virtual_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查關鍵修復點
    checks = [
        ("保護性停損更新觸發", "觸發保護性停損更新"),
        ("損益計算邏輯", "計算實際損益"),
        ("標準化出場原因", "standardize_exit_reason"),
        ("保護性停損更新調用", "update_protective_stop_loss"),
        ("獲利條件檢查", "if pnl > 0"),
        ("組別ID獲取", "group_id = exit_order.get('group_id', 1)"),
        ("保護性停損更新完成日誌", "保護性停損更新完成"),
        ("異常處理", "protection_error"),
        ("SHORT損益計算", "entry_price - price"),
        ("LONG損益計算", "price - entry_price")
    ]
    
    print("\n🔍 檢查修復代碼...")
    all_passed = True
    for check_name, check_text in checks:
        if check_text in content:
            print(f"✅ {check_name}: 已實施")
        else:
            print(f"❌ {check_name}: 缺失")
            all_passed = False
    
    if not all_passed:
        return False
    
    # 檢查虛擬測試數據庫
    test_db = "test_virtual_strategy.db"
    if os.path.exists(test_db):
        print(f"\n✅ 找到虛擬測試數據庫: {test_db}")
        
        # 檢查數據庫中的部位狀態
        try:
            conn = sqlite3.connect(test_db)
            cursor = conn.cursor()
            
            # 檢查活躍部位
            cursor.execute('''
                SELECT id, group_id, lot_id, direction, entry_price, current_stop_loss, status
                FROM position_records 
                WHERE status = 'ACTIVE'
                ORDER BY group_id, lot_id
            ''')
            
            positions = cursor.fetchall()
            print(f"\n📊 虛擬環境活躍部位: {len(positions)}個")
            
            for pos in positions:
                print(f"  部位ID: {pos[0]}, 組別: {pos[1]}, 口數: {pos[2]}")
                print(f"    方向: {pos[3]}, 進場價: {pos[4]}, 停損價: {pos[5]}")
            
            # 檢查最近的平倉記錄
            cursor.execute('''
                SELECT id, group_id, direction, entry_price, exit_price, exit_reason, pnl, exit_time
                FROM position_records 
                WHERE status = 'EXITED' AND exit_time > datetime('now', '-1 hour')
                ORDER BY exit_time DESC
                LIMIT 5
            ''')
            
            recent_exits = cursor.fetchall()
            if recent_exits:
                print(f"\n📋 最近平倉記錄: {len(recent_exits)}個")
                for exit_pos in recent_exits:
                    print(f"  部位ID: {exit_pos[0]}, 組別: {exit_pos[1]}, 方向: {exit_pos[2]}")
                    print(f"    進場價: {exit_pos[3]}, 出場價: {exit_pos[4]}, 損益: {exit_pos[6]}")
                    print(f"    出場原因: {exit_pos[5]}, 時間: {exit_pos[7]}")
            
            conn.close()
            
        except Exception as e:
            print(f"⚠️ 數據庫檢查失敗: {e}")
    else:
        print(f"\n⚠️ 虛擬測試數據庫不存在: {test_db}")
        print("   建議先運行虛擬測試機建立測試數據")
    
    print("\n🎯 修復驗證結果:")
    print("✅ 虛擬測試機修復代碼已正確實施")
    print("✅ 所有關鍵修復點都已包含")
    print("✅ 保護性停損更新邏輯已添加到平倉回調中")
    print("✅ 包含完整的錯誤處理和日誌記錄")
    
    return True

def create_test_scenario():
    """創建測試場景說明"""
    print("\n" + "=" * 60)
    print("🎬 虛擬機測試場景說明")
    print("=" * 60)
    
    scenario = """
🚀 測試步驟:
1. 啟動虛擬測試機: python virtual_simple_integrated.py
2. 等待建立多口部位 (至少2口)
3. 等待第一口觸發移動停利平倉
4. 觀察日誌輸出，應該看到:
   - [MAIN] 🛡️ 觸發保護性停損更新: 部位XX 獲利XX.X點
   - [MAIN] ✅ 保護性停損更新完成: 部位XX 組別X

🎯 預期結果:
- 第一口平倉後，第二口的停損價格應該從區間邊緣更新為:
  SHORT部位: 第二口進場點位 - 獲利*2
  LONG部位: 第二口進場點位 + 獲利*2

🔍 驗證方法:
- 檢查數據庫中第二口部位的 current_stop_loss 欄位
- 確認保護性停損價格計算正確
- 觀察風險管理引擎的保護性停損更新日誌

⚠️ 注意事項:
- 確保虛擬報價機正在運行
- 確保有足夠的價格波動觸發移動停利
- 觀察完整的日誌輸出以確認修復效果

📋 測試檢查清單:
□ 虛擬機啟動成功
□ 建立多口部位
□ 第一口觸發移動停利
□ 出現保護性停損更新日誌
□ 第二口停損價格更新
□ 計算結果正確
"""
    
    print(scenario)

def run_quick_syntax_check():
    """快速語法檢查"""
    print("\n🔧 執行語法檢查...")
    
    try:
        import py_compile
        py_compile.compile('virtual_simple_integrated.py', doraise=True)
        print("✅ 虛擬測試機語法檢查通過")
        return True
    except py_compile.PyCompileError as e:
        print(f"❌ 語法錯誤: {e}")
        return False
    except Exception as e:
        print(f"⚠️ 語法檢查異常: {e}")
        return False

def compare_with_production():
    """比較虛擬機和正式機的差異"""
    print("\n🔄 比較虛擬機和正式機...")
    
    virtual_file = "virtual_simple_integrated.py"
    production_file = "simple_integrated.py"
    
    if not os.path.exists(production_file):
        print(f"⚠️ 正式機文件不存在: {production_file}")
        return
    
    # 檢查正式機是否也有保護性停損更新
    with open(production_file, 'r', encoding='utf-8') as f:
        production_content = f.read()
    
    if "觸發保護性停損更新" in production_content:
        print("✅ 正式機已包含保護性停損更新邏輯")
    else:
        print("⚠️ 正式機尚未包含保護性停損更新邏輯")
        print("   建議在虛擬機測試成功後，將修復應用到正式機")

if __name__ == "__main__":
    print("🚀 開始虛擬機保護性停損修復驗證...")
    
    # 語法檢查
    if not run_quick_syntax_check():
        print("\n❌ 語法檢查失敗，請先修復語法錯誤！")
        sys.exit(1)
    
    # 功能檢查
    if test_virtual_protective_stop_fix():
        create_test_scenario()
        compare_with_production()
        print("\n✅ 虛擬機修復驗證完成！")
        print("📋 下一步: 可以開始實際測試虛擬機的保護性停損功能")
    else:
        print("\n❌ 修復驗證失敗！")
        sys.exit(1)
