#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
各口移動停利自訂功能GUI配置面板
實現用戶友好的移動停利參數設定介面，支援異步處理避免GIL問題
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Dict, Callable, Optional
from trailing_stop_config_manager import (
    TrailingStopConfigManager, 
    MultiLotTrailingStopConfig, 
    LotTrailingStopConfig
)


class TrailingStopConfigPanel:
    """移動停利自訂配置面板"""
    
    def __init__(self, parent_frame, max_lots=3, console_enabled=True):
        self.parent_frame = parent_frame
        self.max_lots = max_lots
        self.console_enabled = console_enabled
        self.lot_configs = {}  # GUI控制項
        self.config_manager = TrailingStopConfigManager()
        self.config_manager.console_enabled = console_enabled
        
        # 回調函數
        self.on_config_changed = None  # 配置變更回調
        self.on_config_applied = None  # 配置應用回調
        
        # 異步處理控制
        self.update_lock = threading.Lock()
        self.pending_updates = False
        
        # 載入當前配置
        self.current_config = self.config_manager.load_config()
        
    def create_ui(self):
        """創建UI元件"""
        # 主框架
        self.config_frame = ttk.LabelFrame(
            self.parent_frame, 
            text="🎯 各口移動停利自訂設定", 
            padding=10
        )
        self.config_frame.pack(fill="x", pady=5)
        
        # 全局控制
        self.create_global_controls()
        
        # 各口獨立設定
        self.create_lot_specific_controls()
        
        # 預設值和操作按鈕
        self.create_action_buttons()
        
        # 載入當前配置到UI
        self.load_config_to_ui()
        
        if self.console_enabled:
            print("[TRAILING_UI] ✅ 移動停利配置面板已創建")
    
    def create_global_controls(self):
        """創建全局控制項"""
        global_frame = ttk.Frame(self.config_frame)
        global_frame.pack(fill="x", pady=(0, 10))
        
        # 全局啟用開關
        self.global_enabled_var = tk.BooleanVar(value=True)
        global_check = ttk.Checkbutton(
            global_frame,
            text="🔧 啟用各口移動停利自訂功能",
            variable=self.global_enabled_var,
            command=self.on_global_enabled_changed
        )
        global_check.pack(side="left")
        
        # 狀態顯示
        self.status_label = ttk.Label(
            global_frame, 
            text="狀態: 已載入配置", 
            foreground="green"
        )
        self.status_label.pack(side="right")
    
    def create_lot_specific_controls(self):
        """創建各口獨立設定控制項"""
        
        # 表頭
        header_frame = ttk.Frame(self.config_frame)
        header_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Label(header_frame, text="口數", width=6).grid(row=0, column=0, padx=5)
        ttk.Label(header_frame, text="啟用", width=6).grid(row=0, column=1, padx=5)
        ttk.Label(header_frame, text="啟動點數", width=10).grid(row=0, column=2, padx=5)
        ttk.Label(header_frame, text="回撤比例", width=10).grid(row=0, column=3, padx=5)
        ttk.Label(header_frame, text="說明", width=20).grid(row=0, column=4, padx=5)
        
        # 各口設定
        for lot_id in range(1, self.max_lots + 1):
            self.create_lot_row(lot_id)
    
    def create_lot_row(self, lot_id: int):
        """創建單口設定行"""
        lot_frame = ttk.Frame(self.config_frame)
        lot_frame.pack(fill="x", pady=2)
        
        # 口數標籤
        ttk.Label(lot_frame, text=f"第{lot_id}口", width=6).grid(row=0, column=0, padx=5)
        
        # 啟用移動停利
        enable_var = tk.BooleanVar(value=True)
        enable_check = ttk.Checkbutton(
            lot_frame,
            variable=enable_var,
            command=lambda: self.on_lot_config_changed(lot_id)
        )
        enable_check.grid(row=0, column=1, padx=5)
        
        # 啟動點數設定
        activation_var = tk.StringVar(value=str(self.get_default_activation(lot_id)))
        activation_entry = ttk.Entry(lot_frame, textvariable=activation_var, width=8)
        activation_entry.grid(row=0, column=2, padx=2)
        activation_entry.bind('<KeyRelease>', lambda e: self.on_lot_config_changed(lot_id))
        
        ttk.Label(lot_frame, text="點").grid(row=0, column=2, padx=(60, 5), sticky="w")
        
        # 回撤百分比設定
        pullback_var = tk.StringVar(value="20")
        pullback_entry = ttk.Entry(lot_frame, textvariable=pullback_var, width=8)
        pullback_entry.grid(row=0, column=3, padx=2)
        pullback_entry.bind('<KeyRelease>', lambda e: self.on_lot_config_changed(lot_id))
        
        ttk.Label(lot_frame, text="%").grid(row=0, column=3, padx=(60, 5), sticky="w")
        
        # 說明文字
        description = self.get_lot_description(lot_id)
        ttk.Label(lot_frame, text=description, width=20, foreground="gray").grid(row=0, column=4, padx=5)
        
        # 儲存控制項引用
        self.lot_configs[lot_id] = {
            'enabled': enable_var,
            'activation_points': activation_var,
            'pullback_percent': pullback_var,
            'activation_entry': activation_entry,
            'pullback_entry': pullback_entry
        }
    
    def create_action_buttons(self):
        """創建操作按鈕"""
        button_frame = ttk.Frame(self.config_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        # 預設配置選擇
        ttk.Label(button_frame, text="快速配置:").pack(side="left", padx=(0, 5))
        
        self.preset_var = tk.StringVar()
        preset_combo = ttk.Combobox(
            button_frame, 
            textvariable=self.preset_var,
            values=list(self.config_manager.get_preset_configs().keys()),
            width=20,
            state="readonly"
        )
        preset_combo.pack(side="left", padx=5)
        preset_combo.bind('<<ComboboxSelected>>', self.on_preset_selected)
        
        # 操作按鈕
        ttk.Button(
            button_frame, 
            text="🔄 重置為預設", 
            command=self.reset_to_default
        ).pack(side="left", padx=10)
        
        ttk.Button(
            button_frame, 
            text="💾 保存配置", 
            command=self.save_config
        ).pack(side="left", padx=5)
        
        ttk.Button(
            button_frame, 
            text="✅ 應用到系統", 
            command=self.apply_config
        ).pack(side="left", padx=5)
        
        # 驗證結果顯示
        self.validation_label = ttk.Label(
            button_frame, 
            text="", 
            foreground="red"
        )
        self.validation_label.pack(side="right", padx=10)
    
    def get_default_activation(self, lot_id: int) -> float:
        """取得預設啟動點數"""
        defaults = {1: 20.0, 2: 35.0, 3: 40.0}
        return defaults.get(lot_id, 25.0)
    
    def get_lot_description(self, lot_id: int) -> str:
        """取得口數說明"""
        descriptions = {
            1: "快速獲利口",
            2: "平衡獲利口", 
            3: "長期持有口"
        }
        return descriptions.get(lot_id, "自訂口")
    
    def on_global_enabled_changed(self):
        """全局啟用狀態變更"""
        enabled = self.global_enabled_var.get()
        
        # 啟用/禁用所有控制項
        for lot_id, controls in self.lot_configs.items():
            state = "normal" if enabled else "disabled"
            controls['activation_entry'].config(state=state)
            controls['pullback_entry'].config(state=state)
        
        self.update_status("全局設定已變更")
        self.schedule_async_validation()
    
    def on_lot_config_changed(self, lot_id: int):
        """單口配置變更"""
        self.update_status(f"第{lot_id}口設定已變更")
        self.schedule_async_validation()
    
    def schedule_async_validation(self):
        """排程異步驗證（避免GIL問題）"""
        if not self.pending_updates:
            self.pending_updates = True
            # 使用after方法避免直接在事件處理中進行複雜操作
            self.parent_frame.after(100, self.perform_async_validation)
    
    def perform_async_validation(self):
        """執行異步驗證"""
        try:
            with self.update_lock:
                self.pending_updates = False
                
                # 驗證當前配置
                config = self.get_current_config_from_ui()
                valid, errors = config.validate_all()
                
                if valid:
                    self.validation_label.config(text="✅ 配置有效", foreground="green")
                else:
                    error_msg = "; ".join(errors[:2])  # 只顯示前兩個錯誤
                    self.validation_label.config(text=f"❌ {error_msg}", foreground="red")
                
                # 觸發配置變更回調
                if self.on_config_changed:
                    self.on_config_changed(config)
                    
        except Exception as e:
            if self.console_enabled:
                print(f"[TRAILING_UI] ❌ 異步驗證失敗: {e}")
    
    def on_preset_selected(self, event=None):
        """預設配置選擇"""
        preset_name = self.preset_var.get()
        if preset_name:
            success = self.config_manager.apply_preset(preset_name)
            if success:
                self.current_config = self.config_manager.current_config
                self.load_config_to_ui()
                self.update_status(f"已載入預設配置: {preset_name}")
            else:
                self.update_status("載入預設配置失敗", error=True)
    
    def reset_to_default(self):
        """重置為預設配置"""
        self.current_config = self.config_manager.get_default_config()
        self.load_config_to_ui()
        self.update_status("已重置為預設配置")
    
    def save_config(self):
        """保存配置"""
        try:
            config = self.get_current_config_from_ui()
            valid, errors = config.validate_all()
            
            if not valid:
                messagebox.showerror("配置錯誤", "\n".join(errors))
                return
            
            success = self.config_manager.save_config(config)
            if success:
                self.current_config = config
                self.update_status("配置已保存")
                messagebox.showinfo("成功", "移動停利配置已保存")
            else:
                self.update_status("保存失敗", error=True)
                messagebox.showerror("錯誤", "配置保存失敗")
                
        except Exception as e:
            if self.console_enabled:
                print(f"[TRAILING_UI] ❌ 保存配置失敗: {e}")
            messagebox.showerror("錯誤", f"保存配置時發生錯誤: {e}")
    
    def apply_config(self):
        """應用配置到系統"""
        try:
            config = self.get_current_config_from_ui()
            valid, errors = config.validate_all()
            
            if not valid:
                messagebox.showerror("配置錯誤", "\n".join(errors))
                return
            
            # 先保存配置
            success = self.config_manager.save_config(config)
            if not success:
                messagebox.showerror("錯誤", "配置保存失敗")
                return
            
            self.current_config = config
            self.config_manager.current_config = config
            
            # 觸發應用回調
            if self.on_config_applied:
                self.on_config_applied(config)
            
            self.update_status("配置已應用到系統")
            messagebox.showinfo("成功", "移動停利配置已應用到交易系統")
            
        except Exception as e:
            if self.console_enabled:
                print(f"[TRAILING_UI] ❌ 應用配置失敗: {e}")
            messagebox.showerror("錯誤", f"應用配置時發生錯誤: {e}")
    
    def get_current_config_from_ui(self) -> MultiLotTrailingStopConfig:
        """從UI取得當前配置"""
        config = MultiLotTrailingStopConfig()
        config.global_enabled = self.global_enabled_var.get()
        config.max_lots = self.max_lots
        
        for lot_id, controls in self.lot_configs.items():
            try:
                lot_config = LotTrailingStopConfig(
                    lot_id=lot_id,
                    enabled=controls['enabled'].get(),
                    activation_points=float(controls['activation_points'].get()),
                    pullback_percent=float(controls['pullback_percent'].get())
                )
                config.add_lot_config(lot_id, lot_config)
            except ValueError:
                # 處理無效輸入
                pass
        
        return config
    
    def load_config_to_ui(self):
        """載入配置到UI"""
        try:
            self.global_enabled_var.set(self.current_config.global_enabled)
            
            for lot_id, controls in self.lot_configs.items():
                lot_config = self.current_config.get_lot_config(lot_id)
                if lot_config:
                    controls['enabled'].set(lot_config.enabled)
                    controls['activation_points'].set(str(lot_config.activation_points))
                    controls['pullback_percent'].set(str(lot_config.pullback_percent))
                else:
                    # 使用預設值
                    controls['enabled'].set(True)
                    controls['activation_points'].set(str(self.get_default_activation(lot_id)))
                    controls['pullback_percent'].set("20")
            
            self.on_global_enabled_changed()  # 更新控制項狀態
            
        except Exception as e:
            if self.console_enabled:
                print(f"[TRAILING_UI] ❌ 載入配置到UI失敗: {e}")
    
    def update_status(self, message: str, error: bool = False):
        """更新狀態顯示"""
        color = "red" if error else "green"
        self.status_label.config(text=f"狀態: {message}", foreground=color)
        
        if self.console_enabled:
            status = "❌" if error else "✅"
            print(f"[TRAILING_UI] {status} {message}")
    
    def set_config_changed_callback(self, callback: Callable):
        """設置配置變更回調"""
        self.on_config_changed = callback
    
    def set_config_applied_callback(self, callback: Callable):
        """設置配置應用回調"""
        self.on_config_applied = callback
