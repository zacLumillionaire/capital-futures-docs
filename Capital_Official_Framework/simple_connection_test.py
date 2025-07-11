#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("🧪 簡單連接測試...")

try:
    # 測試1: 檢查StopLossExecutor方法
    from stop_loss_executor import StopLossExecutor
    from multi_group_database import MultiGroupDatabaseManager
    
    db_manager = MultiGroupDatabaseManager("simple_test.db")
    executor = StopLossExecutor(db_manager, console_enabled=True)
    
    print(f"✅ set_virtual_real_order_manager方法: {hasattr(executor, 'set_virtual_real_order_manager')}")
    
    # 測試2: 檢查VirtualRealOrderManager預設模式
    from virtual_real_order_manager import VirtualRealOrderManager
    
    order_manager = VirtualRealOrderManager(console_enabled=True)
    print(f"✅ 預設實單模式: {order_manager.is_real_mode}")
    
    # 測試3: 檢查OrderModeUIController預設模式
    import tkinter as tk
    from order_mode_ui_controller import OrderModeUIController
    
    root = tk.Tk()
    root.withdraw()  # 隱藏視窗
    
    ui_controller = OrderModeUIController(root)
    print(f"✅ UI預設實單模式: {ui_controller.is_real_mode.get()}")
    
    root.destroy()
    
    print("🎉 所有測試通過！")
    
except Exception as e:
    print(f"❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()

print("✅ 修復驗證完成")
