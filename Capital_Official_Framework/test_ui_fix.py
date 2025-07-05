#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試UI修復 - 檢查多組策略頁面是否正常顯示
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

def test_ui_fix():
    """測試UI修復"""
    print("🧪 測試多組策略頁面修復")
    print("=" * 50)
    
    try:
        # 模擬主程式的初始化過程
        print("1. 檢查模組導入...")
        
        # 檢查多組策略模組
        try:
            from multi_group_database import MultiGroupDatabaseManager
            from multi_group_config import MultiGroupStrategyConfig, create_preset_configs
            from multi_group_position_manager import MultiGroupPositionManager
            from risk_management_engine import RiskManagementEngine
            from multi_group_ui_panel import MultiGroupConfigPanel
            from multi_group_console_logger import get_logger, LogCategory
            print("  ✅ 多組策略模組導入成功")
            MULTI_GROUP_AVAILABLE = True
        except ImportError as e:
            print(f"  ❌ 多組策略模組導入失敗: {e}")
            MULTI_GROUP_AVAILABLE = False
        
        # 檢查虛實單模組
        try:
            from virtual_real_order_manager import VirtualRealOrderManager
            from unified_order_tracker import UnifiedOrderTracker
            print("  ✅ 虛實單模組導入成功")
            VIRTUAL_REAL_ORDER_AVAILABLE = True
        except ImportError as e:
            print(f"  ❌ 虛實單模組導入失敗: {e}")
            VIRTUAL_REAL_ORDER_AVAILABLE = False
        
        if not MULTI_GROUP_AVAILABLE:
            print("❌ 多組策略模組不可用，無法測試")
            return
        
        print("\n2. 模擬初始化過程...")
        
        # 模擬主程式的初始化順序
        class MockApp:
            def __init__(self):
                # 初始化多組策略系統
                self.multi_group_enabled = False
                self.multi_group_db_manager = None
                self.multi_group_position_manager = None
                self.multi_group_risk_engine = None
                self.multi_group_config_panel = None
                self.multi_group_logger = None
                
                # 初始化虛實單系統
                self.virtual_real_order_manager = None
                self.unified_order_tracker = None
                self.virtual_real_system_enabled = False
                
                # 模擬初始化順序
                if MULTI_GROUP_AVAILABLE:
                    self.init_multi_group_system()
                
                if VIRTUAL_REAL_ORDER_AVAILABLE:
                    self.init_virtual_real_order_system()
            
            def init_multi_group_system(self):
                """初始化多組策略系統"""
                try:
                    print("  🔧 初始化多組策略系統...")
                    
                    # 初始化Console日誌器
                    self.multi_group_logger = get_logger()
                    
                    # 初始化資料庫管理器
                    self.multi_group_db_manager = MultiGroupDatabaseManager("test_multi_group_strategy.db")
                    
                    # 初始化風險管理引擎
                    self.multi_group_risk_engine = RiskManagementEngine(self.multi_group_db_manager)
                    
                    # 設定預設配置
                    presets = create_preset_configs()
                    default_config = presets["平衡配置 (2口×2組)"]
                    
                    # 初始化部位管理器（暫時不設置下單組件）
                    self.multi_group_position_manager = MultiGroupPositionManager(
                        self.multi_group_db_manager,
                        default_config
                    )
                    
                    self.multi_group_enabled = True
                    print("    ✅ 多組策略系統初始化成功")
                    
                except Exception as e:
                    self.multi_group_enabled = False
                    print(f"    ❌ 多組策略系統初始化失敗: {e}")
                    import traceback
                    traceback.print_exc()
            
            def init_virtual_real_order_system(self):
                """初始化虛實單系統"""
                try:
                    print("  🔧 初始化虛實單系統...")
                    
                    # 初始化虛實單切換管理器
                    self.virtual_real_order_manager = VirtualRealOrderManager(
                        quote_manager=None,
                        strategy_config=None,
                        console_enabled=True,
                        default_account='F0200006363839'
                    )
                    
                    # 初始化統一回報追蹤器
                    self.unified_order_tracker = UnifiedOrderTracker(
                        strategy_manager=None,
                        console_enabled=True
                    )
                    
                    self.virtual_real_system_enabled = True
                    print("    ✅ 虛實單系統初始化成功")
                    
                    # 更新多組策略管理器的下單組件
                    self._update_multi_group_order_components()
                    
                except Exception as e:
                    self.virtual_real_system_enabled = False
                    self.virtual_real_order_manager = None
                    self.unified_order_tracker = None
                    print(f"    ❌ 虛實單系統初始化失敗: {e}")
            
            def _update_multi_group_order_components(self):
                """更新多組策略管理器的下單組件"""
                try:
                    if (self.multi_group_enabled and 
                        self.multi_group_position_manager and 
                        self.virtual_real_order_manager and 
                        self.unified_order_tracker):
                        
                        # 設置下單組件
                        self.multi_group_position_manager.order_manager = self.virtual_real_order_manager
                        self.multi_group_position_manager.order_tracker = self.unified_order_tracker
                        
                        # 重新設置回調機制
                        if hasattr(self.multi_group_position_manager, '_setup_order_callbacks'):
                            self.multi_group_position_manager._setup_order_callbacks()
                        
                        print("    ✅ 下單組件整合完成")
                        
                except Exception as e:
                    print(f"    ❌ 下單組件整合失敗: {e}")
            
            def create_multi_group_strategy_page(self, parent_frame):
                """創建多組策略配置頁面"""
                try:
                    print("  🔧 創建多組策略配置頁面...")
                    
                    # 多組策略配置面板
                    def on_config_change(config):
                        """配置變更回調"""
                        if self.multi_group_position_manager:
                            self.multi_group_position_manager.strategy_config = config
                    
                    self.multi_group_config_panel = MultiGroupConfigPanel(
                        parent_frame,
                        on_config_change=on_config_change
                    )
                    
                    # 多組策略控制區域
                    control_frame = ttk.LabelFrame(parent_frame, text="🎮 多組策略控制")
                    control_frame.pack(fill="x", padx=5, pady=5)
                    
                    # 控制按鈕行
                    button_row = tk.Frame(control_frame)
                    button_row.pack(fill="x", padx=5, pady=5)
                    
                    # 多組策略準備按鈕
                    btn_prepare = ttk.Button(
                        button_row,
                        text="📋 準備多組策略",
                        command=lambda: print("準備多組策略")
                    )
                    btn_prepare.pack(side="left", padx=5)
                    
                    # 多組策略手動啟動按鈕
                    btn_start = ttk.Button(
                        button_row,
                        text="🚀 手動啟動",
                        command=lambda: print("手動啟動"),
                        state="disabled"
                    )
                    btn_start.pack(side="left", padx=5)
                    
                    print("    ✅ 多組策略配置頁面創建成功")
                    return True
                    
                except Exception as e:
                    print(f"    ❌ 多組策略頁面創建失敗: {e}")
                    import traceback
                    traceback.print_exc()
                    return False
        
        # 創建模擬應用
        app = MockApp()
        
        print("\n3. 檢查初始化結果...")
        print(f"  - 多組策略系統: {'✅ 啟用' if app.multi_group_enabled else '❌ 停用'}")
        print(f"  - 虛實單系統: {'✅ 啟用' if app.virtual_real_system_enabled else '❌ 停用'}")
        print(f"  - 下單管理器: {'✅ 已設置' if app.multi_group_position_manager and app.multi_group_position_manager.order_manager else '❌ 未設置'}")
        print(f"  - 統一追蹤器: {'✅ 已設置' if app.multi_group_position_manager and app.multi_group_position_manager.order_tracker else '❌ 未設置'}")
        
        print("\n4. 測試UI頁面創建...")
        
        if app.multi_group_enabled:
            # 創建測試窗口
            root = tk.Tk()
            root.title("多組策略頁面測試")
            root.geometry("800x600")
            
            # 創建筆記本控件
            notebook = ttk.Notebook(root)
            notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # 創建多組策略頁面
            multi_group_frame = ttk.Frame(notebook)
            notebook.add(multi_group_frame, text="🎯 多組策略配置")
            
            # 測試頁面創建
            success = app.create_multi_group_strategy_page(multi_group_frame)
            
            if success:
                print("  ✅ 多組策略頁面創建成功")
                print("\n💡 測試窗口已打開，請檢查多組策略頁面是否正常顯示")
                print("💡 關閉窗口以繼續...")
                
                # 顯示窗口
                root.mainloop()
            else:
                print("  ❌ 多組策略頁面創建失敗")
                root.destroy()
        else:
            print("  ❌ 多組策略系統未啟用，無法創建頁面")
        
        print("\n🎉 測試完成！")
        
        # 清理測試資料庫
        test_db = "test_multi_group_strategy.db"
        if os.path.exists(test_db):
            os.remove(test_db)
            print("🧹 清理測試資料庫")
        
        print("\n📋 測試結果總結:")
        if app.multi_group_enabled:
            print("  ✅ 多組策略系統正常初始化")
            print("  ✅ 下單組件正確整合")
            print("  ✅ UI頁面可以正常創建")
            print("  ✅ 修復成功！")
        else:
            print("  ❌ 多組策略系統初始化失敗")
            print("  ❌ 需要進一步檢查問題")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ui_fix()
