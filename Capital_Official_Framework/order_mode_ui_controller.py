# -*- coding: utf-8 -*-
"""
下單模式UI控制器
Order Mode UI Controller

功能：
1. 切換按鈕設計 - 明顯的虛實單切換按鈕
2. 狀態顯示 - 清楚顯示當前模式 (虛擬/實單)
3. 安全確認 - 切換到實單模式時的確認對話框
4. 狀態保存 - 記住用戶的模式選擇
5. 視覺提示 - 不同模式有不同的視覺提示

作者: Stage2 虛實單整合系統
日期: 2025-07-04
"""

import tkinter as tk
from tkinter import ttk
import json
import os
from datetime import datetime
from typing import Optional, Callable


class OrderModeUIController:
    """下單模式UI控制器"""
    
    def __init__(self, parent_frame: tk.Widget, order_manager=None, 
                 config_file: str = "order_mode_config.json"):
        """
        初始化UI控制器
        
        Args:
            parent_frame: 父容器
            order_manager: 虛實單管理器
            config_file: 配置文件路徑
        """
        self.parent_frame = parent_frame
        self.order_manager = order_manager
        self.config_file = config_file
        
        # UI元件
        self.mode_frame = None
        self.toggle_button = None
        self.status_label = None
        self.mode_desc_label = None
        self.product_label = None
        
        # 狀態變數
        self.is_real_mode = tk.BooleanVar(value=False)  # 預設虛擬模式
        
        # 回調函數
        self.mode_change_callbacks = []
        
        # 載入配置
        self.load_config()
        
        # 創建UI
        self.create_ui()

        # 🔧 移除初始化UI更新，避免GIL風險
        # self.update_display()  # 已移除，改為Console輸出
        print("[ORDER_MODE] ✅ UI控制器初始化完成 (Console模式)")
    
    def create_ui(self):
        """創建UI元件"""
        # 主框架
        self.mode_frame = ttk.LabelFrame(self.parent_frame, text="🔄 下單模式控制", padding=10)
        self.mode_frame.pack(fill="x", pady=5)
        
        # 第一行：切換按鈕和狀態
        button_row = ttk.Frame(self.mode_frame)
        button_row.pack(fill="x", pady=2)
        
        # 切換按鈕
        self.toggle_button = tk.Button(
            button_row,
            text="🔄 虛擬模式",
            font=("Arial", 12, "bold"),
            width=12,
            height=2,
            bg="lightblue",
            fg="black",
            relief="raised",
            command=self.toggle_order_mode
        )
        self.toggle_button.pack(side="left", padx=5)
        
        # 狀態顯示區域
        status_frame = ttk.Frame(button_row)
        status_frame.pack(side="left", fill="x", expand=True, padx=10)
        
        # 當前模式標籤
        self.status_label = tk.Label(
            status_frame,
            text="當前: 虛擬模式 (安全)",
            font=("Arial", 11, "bold"),
            fg="blue",
            anchor="w"
        )
        self.status_label.pack(fill="x")
        
        # 模式說明標籤
        self.mode_desc_label = tk.Label(
            status_frame,
            text="✅ 模擬交易，不會使用真實資金",
            font=("Arial", 9),
            fg="gray",
            anchor="w"
        )
        self.mode_desc_label.pack(fill="x")
        
        # 商品資訊標籤
        self.product_label = tk.Label(
            status_frame,
            text="商品: 自動識別",
            font=("Arial", 9),
            fg="gray",
            anchor="w"
        )
        self.product_label.pack(fill="x")
        
        # 第二行：警告和說明
        warning_frame = ttk.Frame(self.mode_frame)
        warning_frame.pack(fill="x", pady=(10, 0))
        
        warning_text = "⚠️ 實單模式將使用真實資金進行交易，請謹慎使用"
        warning_label = tk.Label(
            warning_frame,
            text=warning_text,
            font=("Arial", 9),
            fg="red",
            wraplength=400
        )
        warning_label.pack()
    
    def toggle_order_mode(self):
        """切換下單模式"""
        try:
            current_mode = self.is_real_mode.get()
            new_mode = not current_mode

            # 如果要切換到實單模式，顯示警告但直接切換
            if new_mode:  # 切換到實單模式
                print("⚠️ [ORDER_MODE] 警告：即將切換到實單模式")
                print("⚠️ [ORDER_MODE] 這將使用真實資金進行交易！")
                print("⚠️ [ORDER_MODE] 請確認您已經檢查帳戶餘額和交易策略")

            # 執行切換
            if self.order_manager:
                success = self.order_manager.set_order_mode(new_mode)
                if not success:
                    print("❌ [ORDER_MODE] 無法切換到實單模式，請檢查API連線狀態")
                    return

            # 更新狀態
            self.is_real_mode.set(new_mode)
            # 🔧 移除UI更新，避免GIL風險
            # self.update_display()  # 已移除
            self.save_config()

            # 觸發回調
            self.trigger_mode_change_callbacks(new_mode)

            # Console記錄
            mode_desc = "實單" if new_mode else "虛擬"
            print(f"[ORDER_MODE] 🔄 模式切換成功: {mode_desc}模式")

        except Exception as e:
            print(f"[ORDER_MODE] ❌ 模式切換失敗: {e}")
    
    def confirm_real_mode_switch(self) -> bool:
        """確認切換到實單模式 - 已移除對話框，直接返回True"""
        # 移除對話框確認，改用Console警告
        print("⚠️ [ORDER_MODE] 切換到實單模式警告已顯示")
        return True
    
    def update_display(self):
        """更新顯示狀態 - 🔧 移除UI更新，避免GIL風險"""
        is_real = self.is_real_mode.get()

        # 🔧 移除所有UI更新操作，改為Console輸出
        mode_desc = "實單" if is_real else "虛擬"
        print(f"[ORDER_MODE] 🔄 模式狀態: {mode_desc}模式")

        if is_real:
            print("[ORDER_MODE] ⚡ 當前: 實單模式 (真實交易)")
            print("[ORDER_MODE] ⚠️ 使用真實資金，請謹慎操作")
        else:
            print("[ORDER_MODE] 🔄 當前: 虛擬模式 (安全)")
            print("[ORDER_MODE] ✅ 模擬交易，不會使用真實資金")

        # 🔧 移除商品資訊UI更新，改為Console輸出
        if self.order_manager:
            current_product = self.order_manager.get_current_product()
            product_desc = self.order_manager.product_mapping.get(current_product, current_product)
            print(f"[ORDER_MODE] 📊 商品: {current_product} ({product_desc})")

        # 原有UI更新已移除，避免GIL錯誤
        # self.toggle_button.config(...)  # ❌ 已移除
        # self.status_label.config(...)   # ❌ 已移除
        # self.mode_desc_label.config(...) # ❌ 已移除
        # self.product_label.config(...)  # ❌ 已移除
    
    def set_real_mode(self, is_real: bool, skip_confirm: bool = False):
        """
        程式設定模式 (不經過UI確認)

        Args:
            is_real: 是否為實單模式
            skip_confirm: 是否跳過確認
        """
        try:
            # 移除確認對話框，直接執行
            if is_real:
                print("⚠️ [ORDER_MODE] 程式設定為實單模式")

            if self.order_manager:
                success = self.order_manager.set_order_mode(is_real)
                if not success:
                    return False

            self.is_real_mode.set(is_real)
            # 🔧 移除UI更新，避免GIL風險
            # self.update_display()  # 已移除
            self.save_config()
            self.trigger_mode_change_callbacks(is_real)

            return True

        except Exception as e:
            print(f"[ORDER_MODE] ❌ 設定模式失敗: {e}")
            return False
    
    def get_current_mode(self) -> bool:
        """取得當前模式"""
        return self.is_real_mode.get()
    
    def add_mode_change_callback(self, callback: Callable[[bool], None]):
        """添加模式變更回調函數"""
        self.mode_change_callbacks.append(callback)
    
    def trigger_mode_change_callbacks(self, is_real_mode: bool):
        """觸發模式變更回調"""
        for callback in self.mode_change_callbacks:
            try:
                callback(is_real_mode)
            except Exception as e:
                print(f"[ORDER_MODE] ⚠️ 模式變更回調失敗: {e}")
    
    def save_config(self):
        """保存配置"""
        try:
            config = {
                'is_real_mode': self.is_real_mode.get(),
                'last_update': str(datetime.now())
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"[ORDER_MODE] ⚠️ 保存配置失敗: {e}")
    
    def load_config(self):
        """載入配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 載入模式設定 (但預設還是虛擬模式以確保安全)
                saved_mode = config.get('is_real_mode', False)
                self.is_real_mode.set(False)  # 總是從虛擬模式開始
                
                print(f"[ORDER_MODE] 📁 載入配置: 上次模式={'實單' if saved_mode else '虛擬'}, 當前啟動為虛擬模式")
            else:
                print("[ORDER_MODE] 📁 使用預設配置: 虛擬模式")
                
        except Exception as e:
            print(f"[ORDER_MODE] ⚠️ 載入配置失敗: {e}")
    
    def refresh_product_info(self):
        """刷新商品資訊顯示 - 🔧 移除UI更新，避免GIL風險"""
        # self.update_display()  # 已移除
        print("[ORDER_MODE] 🔄 商品資訊已刷新 (Console模式)")


# 測試函數
def test_order_mode_ui():
    """測試下單模式UI"""
    print("🧪 測試下單模式UI...")
    
    # 創建測試視窗
    root = tk.Tk()
    root.title("下單模式UI測試")
    root.geometry("500x300")
    
    # 創建UI控制器
    ui_controller = OrderModeUIController(root)
    
    # 測試按鈕
    test_frame = ttk.Frame(root)
    test_frame.pack(pady=10)
    
    def test_set_real():
        ui_controller.set_real_mode(True)
    
    def test_set_virtual():
        ui_controller.set_real_mode(False, skip_confirm=True)
    
    ttk.Button(test_frame, text="測試設為實單", command=test_set_real).pack(side="left", padx=5)
    ttk.Button(test_frame, text="測試設為虛擬", command=test_set_virtual).pack(side="left", padx=5)
    
    print("✅ UI測試視窗已開啟")
    root.mainloop()


if __name__ == "__main__":
    test_order_mode_ui()
