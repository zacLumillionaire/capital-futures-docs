#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多組策略配置用戶界面面板
提供直觀的多組多口策略配置界面
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
from typing import Dict, List, Optional, Callable

from multi_group_config import (
    MultiGroupStrategyConfig, StrategyGroupConfig, LotRule,
    create_preset_configs, validate_config
)

class MultiGroupConfigPanel:
    """多組策略配置面板"""
    
    def __init__(self, parent_frame: tk.Widget, 
                 on_config_change: Optional[Callable] = None):
        self.parent_frame = parent_frame
        self.on_config_change = on_config_change
        
        # 當前配置
        self.current_config: Optional[MultiGroupStrategyConfig] = None
        
        # UI變數
        self.total_groups_var = tk.StringVar(value="1")
        self.lots_per_group_var = tk.StringVar(value="3")
        self.preset_var = tk.StringVar(value="標準配置 (3口×1組)")
        
        # 預設配置
        self.preset_configs = create_preset_configs()
        
        # 創建界面
        self.create_ui()
        
        # 載入預設配置
        self.load_preset_config()
    
    def create_ui(self):
        """創建用戶界面"""
        # 主容器
        self.main_frame = ttk.LabelFrame(self.parent_frame, text="🎯 多組策略配置")
        self.main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 創建各個區域
        self.create_preset_selection_area()
        self.create_basic_config_area()
        self.create_advanced_config_area()
        self.create_preview_area()
        self.create_control_buttons()
    
    def create_preset_selection_area(self):
        """創建預設配置選擇區域"""
        preset_frame = ttk.LabelFrame(self.main_frame, text="📋 預設配置")
        preset_frame.pack(fill="x", padx=5, pady=5)
        
        # 預設配置選擇
        tk.Label(preset_frame, text="選擇預設配置:").pack(side="left", padx=5)
        
        preset_combo = ttk.Combobox(
            preset_frame, 
            textvariable=self.preset_var,
            values=list(self.preset_configs.keys()),
            state="readonly",
            width=25
        )
        preset_combo.pack(side="left", padx=5)
        preset_combo.bind("<<ComboboxSelected>>", self.on_preset_changed)
        
        # 載入按鈕
        ttk.Button(
            preset_frame, 
            text="📥 載入預設",
            command=self.load_preset_config
        ).pack(side="left", padx=10)
    
    def create_basic_config_area(self):
        """創建基本配置區域"""
        basic_frame = ttk.LabelFrame(self.main_frame, text="⚙️ 基本配置")
        basic_frame.pack(fill="x", padx=5, pady=5)
        
        # 第一行：組數和口數
        row1 = tk.Frame(basic_frame)
        row1.pack(fill="x", padx=5, pady=5)
        
        # 總組數
        tk.Label(row1, text="策略組數:").pack(side="left", padx=5)
        groups_combo = ttk.Combobox(
            row1,
            textvariable=self.total_groups_var,
            values=["1", "2", "3", "4", "5"],
            state="readonly",
            width=5
        )
        groups_combo.pack(side="left", padx=5)
        groups_combo.bind("<<ComboboxSelected>>", self.on_basic_config_changed)
        
        # 每組口數
        tk.Label(row1, text="每組口數:").pack(side="left", padx=(20, 5))
        lots_combo = ttk.Combobox(
            row1,
            textvariable=self.lots_per_group_var,
            values=["1", "2", "3"],
            state="readonly",
            width=5
        )
        lots_combo.pack(side="left", padx=5)
        lots_combo.bind("<<ComboboxSelected>>", self.on_basic_config_changed)
        
        # 總部位數顯示
        self.total_positions_label = tk.Label(
            row1, 
            text="總部位數: 4", 
            font=("Arial", 10, "bold"),
            fg="blue"
        )
        self.total_positions_label.pack(side="left", padx=(20, 5))
        
        # 第二行：配置說明
        row2 = tk.Frame(basic_frame)
        row2.pack(fill="x", padx=5, pady=5)
        
        self.config_description_label = tk.Label(
            row2,
            text="配置說明: 2組策略，每組2口，總共4個部位",
            fg="gray"
        )
        self.config_description_label.pack(side="left", padx=5)
    
    def create_advanced_config_area(self):
        """創建進階配置區域"""
        advanced_frame = ttk.LabelFrame(self.main_frame, text="🔧 進階配置")
        advanced_frame.pack(fill="x", padx=5, pady=5)
        
        # 風險管理規則顯示
        rules_frame = tk.Frame(advanced_frame)
        rules_frame.pack(fill="x", padx=5, pady=5)
        
        tk.Label(rules_frame, text="風險管理規則:", font=("Arial", 9, "bold")).pack(anchor="w")
        
        # 規則詳情文字區域
        self.rules_text = tk.Text(
            rules_frame,
            height=6,
            width=80,
            font=("Consolas", 9),
            bg="#f8f8f8",
            state="disabled"
        )
        self.rules_text.pack(fill="x", padx=5, pady=5)
        
        # 滾動條
        rules_scrollbar = ttk.Scrollbar(rules_frame, orient="vertical", command=self.rules_text.yview)
        self.rules_text.configure(yscrollcommand=rules_scrollbar.set)
    
    def create_preview_area(self):
        """創建配置預覽區域"""
        preview_frame = ttk.LabelFrame(self.main_frame, text="📊 配置預覽")
        preview_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 預覽文字區域
        self.preview_text = tk.Text(
            preview_frame,
            height=8,
            font=("Consolas", 9),
            bg="#f0f8ff",
            state="disabled"
        )
        self.preview_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 預覽滾動條
        preview_scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=preview_scrollbar.set)
    
    def create_control_buttons(self):
        """創建控制按鈕"""
        button_frame = tk.Frame(self.main_frame)
        button_frame.pack(fill="x", padx=5, pady=5)
        
        # 驗證配置按鈕
        ttk.Button(
            button_frame,
            text="✅ 驗證配置",
            command=self.validate_current_config
        ).pack(side="left", padx=5)
        
        # 應用配置按鈕
        ttk.Button(
            button_frame,
            text="🚀 應用配置",
            command=self.apply_config
        ).pack(side="left", padx=5)
        
        # 重置按鈕
        ttk.Button(
            button_frame,
            text="🔄 重置",
            command=self.reset_config
        ).pack(side="left", padx=5)
        
        # 狀態標籤
        self.status_label = tk.Label(
            button_frame,
            text="✅ 配置有效",
            fg="green"
        )
        self.status_label.pack(side="right", padx=5)
    
    def on_preset_changed(self, event=None):
        """預設配置改變事件"""
        self.load_preset_config()
    
    def on_basic_config_changed(self, event=None):
        """基本配置改變事件"""
        self.update_config_from_ui()
        self.update_display()
    
    def load_preset_config(self):
        """載入預設配置"""
        try:
            preset_name = self.preset_var.get()
            if preset_name in self.preset_configs:
                self.current_config = self.preset_configs[preset_name]
                
                # 更新UI變數
                self.total_groups_var.set(str(self.current_config.total_groups))
                self.lots_per_group_var.set(str(self.current_config.lots_per_group))
                
                # 更新顯示
                self.update_display()
                
                print(f"✅ 載入預設配置: {preset_name}")
                
        except Exception as e:
            messagebox.showerror("錯誤", f"載入預設配置失敗: {e}")
    
    def update_config_from_ui(self):
        """從UI更新配置"""
        try:
            total_groups = int(self.total_groups_var.get())
            lots_per_group = int(self.lots_per_group_var.get())
            
            # 創建新配置
            self.current_config = MultiGroupStrategyConfig(
                total_groups=total_groups,
                lots_per_group=lots_per_group
            )
            
        except Exception as e:
            print(f"❌ 更新配置失敗: {e}")
    
    def update_display(self):
        """更新顯示"""
        if not self.current_config:
            return
        
        try:
            # 更新總部位數
            total_positions = self.current_config.get_total_positions()
            self.total_positions_label.config(text=f"總部位數: {total_positions}")
            
            # 更新配置說明
            description = f"配置說明: {self.current_config.total_groups}組策略，每組{self.current_config.lots_per_group}口，總共{total_positions}個部位"
            self.config_description_label.config(text=description)
            
            # 更新風險管理規則
            self.update_rules_display()
            
            # 更新配置預覽
            self.update_preview_display()
            
            # 觸發配置改變回調
            if self.on_config_change:
                self.on_config_change(self.current_config)
                
        except Exception as e:
            print(f"❌ 更新顯示失敗: {e}")
    
    def update_rules_display(self):
        """更新風險管理規則顯示"""
        if not self.current_config:
            return
        
        try:
            self.rules_text.config(state="normal")
            self.rules_text.delete(1.0, tk.END)
            
            rules_content = "風險管理規則詳情:\n\n"
            
            for group in self.current_config.groups:
                rules_content += f"📊 組 {group.group_id} ({group.lots_per_group}口):\n"
                
                for rule in group.lot_rules:
                    rules_content += f"   第{rule.lot_id}口: "
                    
                    if rule.use_trailing_stop:
                        rules_content += f"{rule.trailing_activation}點啟動移動停利, {float(rule.trailing_pullback)*100:.0f}%回撤"
                        
                        if rule.protective_stop_multiplier:
                            rules_content += f", {rule.protective_stop_multiplier}倍保護"
                    else:
                        rules_content += "固定停損"
                    
                    rules_content += "\n"
                
                rules_content += "\n"
            
            rules_content += "💡 說明:\n"
            rules_content += "- 初始停損: 區間邊界 (做多停損在區間低點，做空停損在區間高點)\n"
            rules_content += "- 移動停利: 達到啟動點數後，價格回撤指定比例時出場\n"
            rules_content += "- 保護性停損: 前一口獲利出場後，更新下一口的停損點位\n"
            
            self.rules_text.insert(1.0, rules_content)
            self.rules_text.config(state="disabled")
            
        except Exception as e:
            print(f"❌ 更新規則顯示失敗: {e}")
    
    def update_preview_display(self):
        """更新配置預覽顯示"""
        if not self.current_config:
            return
        
        try:
            self.preview_text.config(state="normal")
            self.preview_text.delete(1.0, tk.END)
            
            # 生成預覽內容
            preview_content = self.current_config.to_summary_string()
            
            # 添加詳細組別信息
            for group in self.current_config.groups:
                preview_content += f"\n\n📊 組 {group.group_id}:"
                preview_content += f"\n   狀態: {'✅ 啟用' if group.is_active else '❌ 停用'}"
                preview_content += f"\n   口數: {group.lots_per_group}"
                
                for rule in group.lot_rules:
                    preview_content += f"\n   第{rule.lot_id}口: {rule.trailing_activation}點啟動"
            
            # 添加統計信息
            preview_content += f"\n\n📈 統計信息:"
            preview_content += f"\n   啟用組數: {len(self.current_config.get_active_groups())}"
            preview_content += f"\n   總部位數: {self.current_config.get_total_positions()}"
            preview_content += f"\n   最大風險: {self.current_config.get_total_positions()} × 區間大小"
            
            self.preview_text.insert(1.0, preview_content)
            self.preview_text.config(state="disabled")
            
        except Exception as e:
            print(f"❌ 更新預覽顯示失敗: {e}")
    
    def validate_current_config(self):
        """驗證當前配置"""
        if not self.current_config:
            messagebox.showwarning("警告", "沒有配置可驗證")
            return
        
        try:
            errors = validate_config(self.current_config)
            
            if errors:
                error_msg = "配置驗證失敗:\n\n" + "\n".join(f"• {error}" for error in errors)
                messagebox.showerror("配置錯誤", error_msg)
                self.status_label.config(text="❌ 配置無效", fg="red")
            else:
                messagebox.showinfo("驗證成功", "✅ 配置驗證通過！\n\n配置有效且可以使用。")
                self.status_label.config(text="✅ 配置有效", fg="green")
                
        except Exception as e:
            messagebox.showerror("錯誤", f"驗證過程發生錯誤: {e}")
    
    def apply_config(self):
        """應用配置"""
        if not self.current_config:
            messagebox.showwarning("警告", "沒有配置可應用")
            return
        
        try:
            # 先驗證配置
            errors = validate_config(self.current_config)
            if errors:
                error_msg = "無法應用配置，存在以下錯誤:\n\n" + "\n".join(f"• {error}" for error in errors)
                messagebox.showerror("配置錯誤", error_msg)
                return
            
            # 確認應用
            result = messagebox.askyesno(
                "確認應用",
                f"確定要應用以下配置嗎?\n\n"
                f"組數: {self.current_config.total_groups}\n"
                f"每組口數: {self.current_config.lots_per_group}\n"
                f"總部位數: {self.current_config.get_total_positions()}\n\n"
                f"這將替換當前的策略配置。"
            )
            
            if result:
                # 觸發配置應用回調
                if self.on_config_change:
                    self.on_config_change(self.current_config)
                
                messagebox.showinfo("應用成功", "✅ 配置已成功應用！")
                print(f"✅ 應用多組策略配置: {self.current_config.total_groups}組×{self.current_config.lots_per_group}口")
                
        except Exception as e:
            messagebox.showerror("錯誤", f"應用配置失敗: {e}")
    
    def reset_config(self):
        """重置配置"""
        try:
            # 重置為預設配置
            self.preset_var.set("標準配置 (3口×1組)")
            self.load_preset_config()

            messagebox.showinfo("重置完成", "✅ 配置已重置為預設值")

        except Exception as e:
            messagebox.showerror("錯誤", f"重置配置失敗: {e}")
    
    def get_current_config(self) -> Optional[MultiGroupStrategyConfig]:
        """取得當前配置"""
        return self.current_config

if __name__ == "__main__":
    # 測試多組配置面板
    print("🧪 測試多組配置面板")
    
    root = tk.Tk()
    root.title("多組策略配置測試")
    root.geometry("800x700")
    
    def on_config_change(config):
        print(f"配置改變: {config.total_groups}組×{config.lots_per_group}口")
    
    panel = MultiGroupConfigPanel(root, on_config_change)
    
    root.mainloop()
