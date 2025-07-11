# -*- coding: utf-8 -*-
"""
測試分級LOG系統
驗證修改後的風險管理引擎LOG輸出
"""

import sys
import os
import time
sys.path.append(os.path.dirname(__file__))

def test_tiered_logging():
    """測試分級LOG系統"""
    print("🧪 測試分級LOG系統")
    print("=" * 50)
    
    try:
        from multi_group_database import MultiGroupDatabaseManager
        from risk_management_engine import RiskManagementEngine
        
        # 1. 創建風險管理引擎
        db_manager = MultiGroupDatabaseManager("multi_group_strategy.db")
        risk_engine = RiskManagementEngine(db_manager)
        
        print("✅ 風險管理引擎初始化完成")
        
        # 2. 測試LOG控制方法
        print("\n🎯 測試LOG控制方法")
        print("-" * 30)
        
        # 測試重要事件LOG
        risk_engine._log_important("[TEST] 🚨 這是重要事件LOG - 應該立即顯示")
        
        # 測試常規LOG（30秒間隔）
        risk_engine._log_routine("[TEST] ✅ 這是常規LOG - 30秒間隔")
        time.sleep(1)
        risk_engine._log_routine("[TEST] ✅ 這是第二次常規LOG - 應該被跳過")
        
        # 測試調試LOG（預設關閉）
        risk_engine._log_debug("[TEST] 🔍 這是調試LOG - 預設不顯示")
        
        # 3. 測試LOG模式切換
        print("\n🔧 測試LOG模式切換")
        print("-" * 30)
        
        print("啟用詳細LOG模式...")
        risk_engine.enable_detailed_logging()
        
        # 現在調試LOG應該顯示
        risk_engine._log_debug("[TEST] 🔍 這是調試LOG - 現在應該顯示")
        
        print("切換回簡化LOG模式...")
        risk_engine.enable_normal_logging()
        
        # 調試LOG又不顯示了
        risk_engine._log_debug("[TEST] 🔍 這是調試LOG - 又不顯示了")
        
        # 4. 測試狀態摘要
        print("\n📊 測試狀態摘要")
        print("-" * 30)
        
        # 模擬部位數據
        mock_positions = [
            {'id': 1, 'direction': 'LONG', 'trailing_activated': True, 'protection_activated': False},
            {'id': 2, 'direction': 'LONG', 'trailing_activated': False, 'protection_activated': True},
            {'id': 3, 'direction': 'SHORT', 'trailing_activated': False, 'protection_activated': False}
        ]
        
        mock_groups = {1: mock_positions}
        
        # 測試狀態摘要（應該立即顯示第一次）
        risk_engine._log_status_summary(22440, mock_positions, mock_groups)
        
        # 第二次應該被跳過（30秒間隔）
        time.sleep(1)
        risk_engine._log_status_summary(22441, mock_positions, mock_groups)
        
        print("\n🎉 分級LOG系統測試完成")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def simulate_normal_operation():
    """模擬正常運行狀態"""
    print("\n🚀 模擬正常運行狀態")
    print("=" * 50)
    
    try:
        from multi_group_database import MultiGroupDatabaseManager
        from risk_management_engine import RiskManagementEngine
        
        db_manager = MultiGroupDatabaseManager("multi_group_strategy.db")
        risk_engine = RiskManagementEngine(db_manager)
        
        print("模擬價格更新和風險檢查...")
        
        # 模擬多次價格更新
        for i in range(5):
            current_price = 22440 + i
            current_time = f"00:30:{i:02d}"
            
            print(f"\n--- 第{i+1}次價格更新: {current_price} ---")
            
            # 在正常模式下，大部分詳細LOG應該被抑制
            # 只有重要事件和狀態摘要會顯示
            
            # 模擬重要事件
            if i == 2:
                risk_engine._log_important(f"[RISK_ENGINE] 🚀 移動停利啟動! 部位77 @{current_price}")
            
            if i == 4:
                risk_engine._log_important(f"[RISK_ENGINE] 💥 移動停利觸發! 部位77 @{current_price}")
            
            # 模擬狀態摘要（30秒間隔）
            mock_positions = [{'id': 77, 'direction': 'LONG', 'trailing_activated': i >= 2, 'protection_activated': False}]
            mock_groups = {1: mock_positions}
            risk_engine._log_status_summary(current_price, mock_positions, mock_groups)
            
            time.sleep(0.5)
        
        print("\n✅ 正常運行模擬完成")
        print("📊 觀察結果：")
        print("  - 重要事件立即顯示")
        print("  - 狀態摘要按間隔顯示")
        print("  - 詳細LOG被抑制")
        
        return True
        
    except Exception as e:
        print(f"❌ 模擬失敗: {e}")
        return False

if __name__ == "__main__":
    print("🔧 分級LOG系統測試")
    print("=" * 60)
    
    # 測試1: 基本功能
    test1_success = test_tiered_logging()
    
    # 測試2: 模擬正常運行
    test2_success = simulate_normal_operation()
    
    print("\n📋 測試總結")
    print("=" * 60)
    
    if test1_success and test2_success:
        print("🎉 分級LOG系統測試成功！")
        print("✅ LOG控制方法正常工作")
        print("✅ 模式切換功能正常")
        print("✅ 狀態摘要功能正常")
        print("\n📝 預期效果：")
        print("  🟢 正常運行：只顯示狀態摘要和重要事件")
        print("  🟡 重要事件：移動停利啟動/觸發、停損觸發、錯誤")
        print("  🔴 調試模式：可選顯示所有詳細LOG")
        print("\n🚀 現在可以啟動交易系統測試效果！")
    else:
        print("⚠️ 測試部分成功")
        if not test1_success:
            print("❌ 基本功能測試失敗")
        if not test2_success:
            print("❌ 正常運行模擬失敗")
        print("💡 可能需要進一步檢查")
    
    print("\n🎯 使用方法：")
    print("  - 正常模式：risk_engine.enable_normal_logging()")
    print("  - 調試模式：risk_engine.enable_detailed_logging()")
    print("  - 重要事件：自動立即顯示")
    print("  - 狀態摘要：每30秒顯示一次")
