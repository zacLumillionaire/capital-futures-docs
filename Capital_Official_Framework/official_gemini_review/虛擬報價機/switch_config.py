#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
虛擬報價機配置切換工具
快速切換不同測試場景的配置
"""

import os
import json
import shutil
from datetime import datetime

class ConfigSwitcher:
    """配置切換器"""
    
    def __init__(self):
        self.config_dir = os.path.dirname(__file__)
        self.current_config = os.path.join(self.config_dir, "config.json")
        self.backup_dir = os.path.join(self.config_dir, "config_backups")
        
        # 確保備份目錄存在
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # 可用配置列表
        self.available_configs = {
            "1": {
                "name": "建倉測試",
                "file": "config_entry_test.json",
                "description": "穩定價格環境，適合測試進場建倉邏輯"
            },
            "2": {
                "name": "建倉追價測試", 
                "file": "config_entry_chase.json",
                "description": "快速變動價格環境，測試追價機制"
            },
            "3": {
                "name": "移動停利測試",
                "file": "config_trailing_stop.json", 
                "description": "趨勢性價格變動，測試移動停利啟動與平倉"
            },
            "4": {
                "name": "停損測試",
                "file": "config_stop_loss.json",
                "description": "逆向價格變動，測試停損觸發機制"
            },
            "5": {
                "name": "停損追價測試",
                "file": "config_stop_chase.json",
                "description": "快速惡化環境，測試停損追價機制"
            },
            "6": {
                "name": "綜合壓力測試",
                "file": "config_stress_test.json",
                "description": "極端市場環境，測試系統穩定性"
            }
        }
    
    def show_menu(self):
        """顯示配置選單"""
        print("🔧 虛擬報價機配置切換工具")
        print("=" * 60)
        print("📋 可用測試配置:")
        print()
        
        for key, config in self.available_configs.items():
            print(f"{key}. {config['name']}")
            print(f"   📝 {config['description']}")
            print()
        
        print("0. 顯示當前配置")
        print("b. 備份當前配置")
        print("r. 還原備份配置")
        print("q. 退出")
        print("=" * 60)
    
    def get_current_config_info(self):
        """獲取當前配置資訊"""
        try:
            with open(self.current_config, 'r', encoding='utf-8') as f:
                config = json.load(f)
                scenario = config.get('scenario', '未知場景')
                description = config.get('description', '無描述')
                return scenario, description
        except Exception as e:
            return "無法讀取", str(e)
    
    def backup_current_config(self):
        """備份當前配置"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.backup_dir, f"config_backup_{timestamp}.json")
            shutil.copy2(self.current_config, backup_file)
            print(f"✅ 當前配置已備份到: {backup_file}")
            return True
        except Exception as e:
            print(f"❌ 備份失敗: {e}")
            return False
    
    def switch_config(self, config_key):
        """切換配置"""
        if config_key not in self.available_configs:
            print("❌ 無效的配置選擇")
            return False
        
        config_info = self.available_configs[config_key]
        source_file = os.path.join(self.config_dir, config_info['file'])
        
        if not os.path.exists(source_file):
            print(f"❌ 配置文件不存在: {source_file}")
            return False
        
        try:
            # 備份當前配置
            self.backup_current_config()
            
            # 切換配置
            shutil.copy2(source_file, self.current_config)
            
            print(f"✅ 已切換到: {config_info['name']}")
            print(f"📝 描述: {config_info['description']}")
            print("💡 重啟虛擬報價機以應用新配置")
            return True
            
        except Exception as e:
            print(f"❌ 切換配置失敗: {e}")
            return False
    
    def list_backups(self):
        """列出備份文件"""
        try:
            backups = [f for f in os.listdir(self.backup_dir) if f.startswith('config_backup_')]
            backups.sort(reverse=True)  # 最新的在前
            
            if not backups:
                print("📁 沒有找到備份文件")
                return []
            
            print("📁 可用備份:")
            for i, backup in enumerate(backups[:10], 1):  # 只顯示最近10個
                timestamp = backup.replace('config_backup_', '').replace('.json', '')
                try:
                    dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                    print(f"{i}. {formatted_time}")
                except:
                    print(f"{i}. {backup}")
            
            return backups[:10]
            
        except Exception as e:
            print(f"❌ 列出備份失敗: {e}")
            return []
    
    def restore_backup(self):
        """還原備份配置"""
        backups = self.list_backups()
        if not backups:
            return False
        
        try:
            choice = input("\n請選擇要還原的備份 (輸入編號): ").strip()
            backup_index = int(choice) - 1
            
            if 0 <= backup_index < len(backups):
                backup_file = os.path.join(self.backup_dir, backups[backup_index])
                
                # 備份當前配置
                self.backup_current_config()
                
                # 還原備份
                shutil.copy2(backup_file, self.current_config)
                print(f"✅ 已還原備份配置")
                print("💡 重啟虛擬報價機以應用配置")
                return True
            else:
                print("❌ 無效的備份選擇")
                return False
                
        except ValueError:
            print("❌ 請輸入有效的數字")
            return False
        except Exception as e:
            print(f"❌ 還原備份失敗: {e}")
            return False
    
    def run(self):
        """運行配置切換器"""
        while True:
            self.show_menu()
            
            # 顯示當前配置
            scenario, description = self.get_current_config_info()
            print(f"🎯 當前配置: {scenario}")
            print(f"📝 描述: {description}")
            print()
            
            choice = input("請選擇操作: ").strip().lower()
            
            if choice == 'q':
                print("👋 再見！")
                break
            elif choice == '0':
                continue  # 重新顯示選單
            elif choice == 'b':
                self.backup_current_config()
                input("\n按 Enter 繼續...")
            elif choice == 'r':
                self.restore_backup()
                input("\n按 Enter 繼續...")
            elif choice in self.available_configs:
                self.switch_config(choice)
                input("\n按 Enter 繼續...")
            else:
                print("❌ 無效選擇，請重新輸入")
                input("\n按 Enter 繼續...")

if __name__ == "__main__":
    switcher = ConfigSwitcher()
    switcher.run()
