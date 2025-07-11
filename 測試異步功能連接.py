#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試異步功能連接腳本
用於驗證全局異步更新器是否正確連接到所有組件
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'Capital_Official_Framework'))

def test_async_updater_connection():
    """測試異步更新器連接"""
    print("🧪 測試異步更新器連接...")
    
    try:
        # 1. 測試異步更新器創建
        from multi_group_database import MultiGroupDatabaseManager
        from async_db_updater import AsyncDatabaseUpdater
        
        print("1️⃣ 創建數據庫管理器...")
        db_manager = MultiGroupDatabaseManager("test_async_connection.db")
        
        print("2️⃣ 創建異步更新器...")
        async_updater = AsyncDatabaseUpdater(db_manager, console_enabled=True)
        async_updater.start()
        
        print("✅ 異步更新器創建成功")
        
        # 2. 測試風險管理引擎連接
        from risk_management_engine import RiskManagementEngine
        
        print("3️⃣ 創建風險管理引擎...")
        risk_engine = RiskManagementEngine(db_manager)
        
        print("4️⃣ 連接異步更新器到風險管理引擎...")
        risk_engine.set_async_updater(async_updater)
        
        # 檢查連接狀態
        if hasattr(risk_engine, 'async_updater') and risk_engine.async_updater:
            print("✅ 風險管理引擎異步更新器連接成功")
            print(f"   - 異步峰值更新啟用: {risk_engine.enable_async_peak_update}")
        else:
            print("❌ 風險管理引擎異步更新器連接失敗")
            return False
        
        # 3. 測試停損執行器連接
        from stop_loss_executor import StopLossExecutor
        
        print("5️⃣ 創建停損執行器...")
        stop_executor = StopLossExecutor(db_manager, console_enabled=True)
        
        print("6️⃣ 連接異步更新器到停損執行器...")
        stop_executor.set_async_updater(async_updater, enabled=True)
        
        # 檢查連接狀態
        if hasattr(stop_executor, 'async_updater') and stop_executor.async_updater:
            print("✅ 停損執行器異步更新器連接成功")
            print(f"   - 異步更新啟用: {stop_executor.async_update_enabled}")
        else:
            print("❌ 停損執行器異步更新器連接失敗")
            return False
        
        # 4. 測試統一出場管理器連接
        from unified_exit_manager import UnifiedExitManager
        
        print("7️⃣ 創建統一出場管理器...")
        unified_exit = UnifiedExitManager(
            order_manager=None,  # 測試時可以為None
            position_manager=None,
            db_manager=db_manager,
            console_enabled=True
        )
        
        print("8️⃣ 連接異步更新器到統一出場管理器...")
        unified_exit.set_async_updater(async_updater, enabled=True)
        
        # 檢查連接狀態
        if hasattr(unified_exit, 'async_updater') and unified_exit.async_updater:
            print("✅ 統一出場管理器異步更新器連接成功")
            print(f"   - 異步更新啟用: {unified_exit.async_update_enabled}")
        else:
            print("❌ 統一出場管理器異步更新器連接失敗")
            return False
        
        # 5. 測試異步功能
        print("9️⃣ 測試異步功能...")
        
        # 測試峰值更新
        async_updater.schedule_peak_update(
            position_id=1,
            peak_price=22500.0,
            current_time="18:30:00",
            update_reason="測試峰值更新"
        )
        
        # 測試風險狀態創建
        async_updater.schedule_risk_state_creation(
            position_id=1,
            peak_price=22500.0,
            current_time="18:30:00",
            update_reason="測試風險狀態創建"
        )
        
        print("✅ 異步功能測試完成")
        
        # 6. 檢查隊列狀態
        import time
        time.sleep(1)  # 等待處理
        
        queue_size = async_updater.update_queue.qsize()
        print(f"📊 當前隊列大小: {queue_size}")
        
        # 7. 停止異步更新器
        print("🛑 停止異步更新器...")
        async_updater.stop()
        
        print("🎉 所有測試通過！")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_integrated_async():
    """測試 simple_integrated.py 中的異步功能"""
    print("\n🧪 測試 simple_integrated.py 異步功能...")
    
    try:
        # 檢查 simple_integrated.py 中的異步相關代碼
        import inspect
        
        # 檢查是否有 async_updater 初始化
        with open('Capital_Official_Framework/simple_integrated.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ('AsyncDatabaseUpdater導入', 'from async_db_updater import AsyncDatabaseUpdater' in content),
            ('異步更新器初始化', 'self.async_updater = AsyncDatabaseUpdater' in content),
            ('異步更新器啟動', 'self.async_updater.start()' in content),
            ('風險引擎連接', 'self.multi_group_risk_engine.set_async_updater' in content),
            ('部位管理器連接', 'self.multi_group_position_manager.async_updater = self.async_updater' in content),
        ]
        
        all_passed = True
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print("✅ simple_integrated.py 異步功能檢查通過")
            return True
        else:
            print("❌ simple_integrated.py 異步功能檢查失敗")
            return False
            
    except Exception as e:
        print(f"❌ simple_integrated.py 檢查失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 開始異步功能連接測試")
    print("=" * 50)
    
    # 測試1: 異步更新器連接
    test1_passed = test_async_updater_connection()
    
    # 測試2: simple_integrated.py 異步功能
    test2_passed = test_simple_integrated_async()
    
    print("\n" + "=" * 50)
    print("📊 測試結果總結:")
    print(f"   異步更新器連接測試: {'✅ 通過' if test1_passed else '❌ 失敗'}")
    print(f"   simple_integrated異步功能: {'✅ 通過' if test2_passed else '❌ 失敗'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 所有測試通過！異步功能應該能正常工作")
        print("💡 建議重新啟動 simple_integrated.py 查看效果")
    else:
        print("\n⚠️ 部分測試失敗，請檢查相關配置")
    
    return test1_passed and test2_passed

if __name__ == "__main__":
    main()
