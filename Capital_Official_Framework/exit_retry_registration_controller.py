#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
追價訂單註冊控制器
提供安全的開關控制和測試功能
"""

import os
import sys
from datetime import datetime

class ExitRetryRegistrationController:
    """追價訂單註冊控制器"""
    
    def __init__(self, console_enabled: bool = True):
        self.console_enabled = console_enabled
        self.app_instance = None
        
    def connect_to_app(self, app_instance):
        """連接到主應用實例"""
        self.app_instance = app_instance
        if self.console_enabled:
            print("[CONTROLLER] 🔗 已連接到主應用")
    
    def check_current_status(self):
        """檢查當前註冊機制狀態"""
        if not self.app_instance:
            print("[CONTROLLER] ❌ 未連接到主應用")
            return None
            
        try:
            # 檢查開關狀態
            full_registration_enabled = getattr(self.app_instance, 'enable_exit_retry_full_registration', False)
            
            # 檢查組件可用性
            components = {
                "simplified_tracker": False,
                "unified_tracker": False,
                "fifo_matcher": False,
                "multi_group_manager": False
            }
            
            if hasattr(self.app_instance, 'multi_group_position_manager') and \
               hasattr(self.app_instance.multi_group_position_manager, 'simplified_tracker'):
                components["simplified_tracker"] = True
                
            if hasattr(self.app_instance, 'unified_order_tracker') and self.app_instance.unified_order_tracker:
                components["unified_tracker"] = True
                
                # 檢查FIFO匹配器
                if hasattr(self.app_instance.unified_order_tracker, 'fifo_matcher'):
                    components["fifo_matcher"] = True
                    
            if hasattr(self.app_instance, 'multi_group_position_manager') and self.app_instance.multi_group_position_manager:
                components["multi_group_manager"] = True
            
            status = {
                "full_registration_enabled": full_registration_enabled,
                "components": components,
                "ready_for_full_registration": all(components.values())
            }
            
            if self.console_enabled:
                print(f"\n[CONTROLLER] 📊 當前狀態:")
                print(f"  完整註冊開關: {'✅ 啟用' if full_registration_enabled else '❌ 禁用'}")
                print(f"  組件狀態:")
                for component, available in components.items():
                    status_icon = "✅" if available else "❌"
                    print(f"    {status_icon} {component}: {'可用' if available else '不可用'}")
                print(f"  完整註冊就緒: {'✅ 是' if status['ready_for_full_registration'] else '❌ 否'}")
            
            return status
            
        except Exception as e:
            if self.console_enabled:
                print(f"[CONTROLLER] ❌ 檢查狀態失敗: {e}")
            return None
    
    def enable_full_registration(self, force: bool = False):
        """啟用完整註冊功能"""
        if not self.app_instance:
            print("[CONTROLLER] ❌ 未連接到主應用")
            return False
            
        try:
            # 檢查系統就緒狀態
            status = self.check_current_status()
            if not status:
                return False
                
            if not status["ready_for_full_registration"] and not force:
                print("[CONTROLLER] ⚠️ 系統未就緒，無法啟用完整註冊")
                print("[CONTROLLER] 💡 使用 force=True 強制啟用")
                return False
            
            # 啟用完整註冊
            if hasattr(self.app_instance, 'enable_exit_retry_full_registration'):
                self.app_instance.enable_exit_retry_full_registration(True)
            else:
                self.app_instance.enable_exit_retry_full_registration = True
                
            if self.console_enabled:
                print("[CONTROLLER] ✅ 完整註冊功能已啟用")
                if force:
                    print("[CONTROLLER] ⚠️ 強制啟用模式，請密切監控")
                    
            return True
            
        except Exception as e:
            if self.console_enabled:
                print(f"[CONTROLLER] ❌ 啟用完整註冊失敗: {e}")
            return False
    
    def disable_full_registration(self):
        """禁用完整註冊功能（回到安全模式）"""
        if not self.app_instance:
            print("[CONTROLLER] ❌ 未連接到主應用")
            return False
            
        try:
            if hasattr(self.app_instance, 'enable_exit_retry_full_registration'):
                self.app_instance.enable_exit_retry_full_registration(False)
            else:
                self.app_instance.enable_exit_retry_full_registration = False
                
            if self.console_enabled:
                print("[CONTROLLER] ✅ 完整註冊功能已禁用（安全模式）")
                
            return True
            
        except Exception as e:
            if self.console_enabled:
                print(f"[CONTROLLER] ❌ 禁用完整註冊失敗: {e}")
            return False
    
    def test_registration_safety(self):
        """測試註冊機制安全性"""
        if self.console_enabled:
            print("\n[CONTROLLER] 🧪 開始安全性測試...")
            
        try:
            # 測試1: 檢查基本平倉功能
            print("\n📋 測試1: 基本平倉功能檢查")
            status = self.check_current_status()
            if status and status["components"]["simplified_tracker"]:
                print("  ✅ 簡化追蹤器可用 - 基本平倉應該正常")
            else:
                print("  ❌ 簡化追蹤器不可用 - 基本平倉可能有問題")
                
            # 測試2: 檢查完整註冊準備度
            print("\n📋 測試2: 完整註冊準備度檢查")
            if status and status["ready_for_full_registration"]:
                print("  ✅ 所有組件就緒 - 可以安全啟用完整註冊")
            else:
                print("  ⚠️ 部分組件未就緒 - 建議暫時不啟用完整註冊")
                
            # 測試3: 檢查日誌機制
            print("\n📋 測試3: 日誌機制檢查")
            try:
                test_log_path = "exit_retry_registration_test.log"
                with open(test_log_path, "w", encoding="utf-8") as f:
                    f.write(f"{datetime.now()}: 測試日誌寫入\n")
                os.remove(test_log_path)
                print("  ✅ 日誌機制正常")
            except Exception as log_error:
                print(f"  ⚠️ 日誌機制異常: {log_error}")
                
            return True
            
        except Exception as e:
            if self.console_enabled:
                print(f"[CONTROLLER] ❌ 安全性測試失敗: {e}")
            return False
    
    def get_usage_guide(self):
        """獲取使用指南"""
        guide = """
🔧 追價訂單註冊控制器使用指南

📋 基本使用流程:
1. controller.check_current_status()     # 檢查系統狀態
2. controller.test_registration_safety() # 測試安全性
3. controller.enable_full_registration() # 啟用完整註冊（可選）

🛡️ 安全建議:
- 預設禁用完整註冊，確保基本平倉功能不受影響
- 啟用前先檢查所有組件是否就緒
- 啟用後密切監控日誌和交易狀況
- 如有問題立即使用 disable_full_registration() 回到安全模式

📊 監控要點:
- 觀察 exit_retry_registration.log 日誌
- 檢查追價訂單是否正確匹配
- 確認基本平倉功能正常運作

🔄 階段性實施:
階段1: 只使用簡化追蹤器（當前狀態，最安全）
階段2: 啟用完整註冊（需要確認系統穩定）
階段3: 根據實際效果調整和優化
        """
        
        if self.console_enabled:
            print(guide)
        
        return guide

def main():
    """主函數 - 獨立測試"""
    print("=" * 60)
    print("🚀 追價訂單註冊控制器測試")
    print("=" * 60)
    
    controller = ExitRetryRegistrationController(console_enabled=True)
    
    # 顯示使用指南
    controller.get_usage_guide()
    
    print("\n" + "=" * 60)
    print("💡 控制器已準備就緒，等待連接到主應用")
    print("=" * 60)

if __name__ == "__main__":
    main()
