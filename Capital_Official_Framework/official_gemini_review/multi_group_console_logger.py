#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多組策略Console化日誌系統
避免UI更新造成的GIL問題，提供完整的策略監控日誌
"""

import time
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

class LogLevel(Enum):
    """日誌級別"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCategory(Enum):
    """日誌分類"""
    STRATEGY = "STRATEGY"      # 策略相關
    POSITION = "POSITION"      # 部位相關
    RISK = "RISK"             # 風險管理
    CONFIG = "CONFIG"         # 配置相關
    SYSTEM = "SYSTEM"         # 系統相關

class MultiGroupConsoleLogger:
    """多組策略Console化日誌器"""
    
    def __init__(self, enable_console: bool = True, enable_file: bool = False):
        self.enable_console = enable_console
        self.enable_file = enable_file
        
        # 日誌控制開關
        self.console_controls = {
            LogCategory.STRATEGY: True,
            LogCategory.POSITION: True,
            LogCategory.RISK: True,
            LogCategory.CONFIG: True,
            LogCategory.SYSTEM: True
        }
        
        # 統計信息
        self.log_stats = {
            'total_logs': 0,
            'by_category': {cat: 0 for cat in LogCategory},
            'by_level': {level: 0 for level in LogLevel}
        }
        
        # 設定文件日誌（如果啟用）
        if self.enable_file:
            self.setup_file_logging()
        
        print("🎯 [LOGGER] 多組策略Console日誌系統啟動")
        print("💡 [LOGGER] 使用Console模式，避免GIL問題")
    
    def setup_file_logging(self):
        """設定文件日誌（帶輪轉機制）"""
        try:
            # 創建logs目錄
            logs_dir = "logs"
            os.makedirs(logs_dir, exist_ok=True)

            # 設定日誌文件名
            log_filename = os.path.join(logs_dir, f"multi_group_strategy_{datetime.now().strftime('%Y%m%d')}.log")

            # 設定輪轉日誌處理器
            from logging.handlers import RotatingFileHandler

            # 創建輪轉處理器：最大10MB，保留5個備份
            file_handler = RotatingFileHandler(
                filename=log_filename,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )

            # 設定格式
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.INFO)

            # 添加到根記錄器
            root_logger = logging.getLogger()
            root_logger.setLevel(logging.INFO)
            root_logger.addHandler(file_handler)

            print(f"📁 [LOGGER] 輪轉文件日誌啟用: {log_filename} (最大10MB，保留5個備份)")

            # 清理舊日誌文件
            self._cleanup_old_logs(logs_dir)

        except Exception as e:
            print(f"❌ [LOGGER] 文件日誌設定失敗: {e}")

    def _cleanup_old_logs(self, logs_dir, max_days=7):
        """清理舊日誌文件（保留最近7天）"""
        try:
            current_time = time.time()
            count = 0

            for filename in os.listdir(logs_dir):
                if filename.endswith('.log') or filename.endswith('.log.1'):
                    file_path = os.path.join(logs_dir, filename)
                    file_age = current_time - os.path.getmtime(file_path)

                    # 如果文件超過7天，刪除
                    if file_age > (max_days * 24 * 60 * 60):
                        os.remove(file_path)
                        count += 1

            if count > 0:
                print(f"🧹 [LOGGER] 清理{count}個超過{max_days}天的舊日誌文件")

        except Exception as e:
            print(f"⚠️ [LOGGER] 清理舊日誌文件失敗: {e}")
    
    def log(self, category: LogCategory, level: LogLevel, message: str, 
            group_id: Optional[int] = None, position_id: Optional[int] = None):
        """記錄日誌"""
        try:
            # 檢查是否啟用該分類的Console輸出
            if not self.console_controls.get(category, True):
                return
            
            # 生成時間戳
            timestamp = time.strftime("%H:%M:%S")
            
            # 生成日誌前綴
            prefix = self._get_log_prefix(category, level)
            
            # 生成位置信息
            location_info = ""
            if group_id is not None:
                location_info += f" [組{group_id}]"
            if position_id is not None:
                location_info += f" [部位{position_id}]"
            
            # 組合完整日誌
            full_message = f"{prefix} [{timestamp}]{location_info} {message}"
            
            # Console輸出
            if self.enable_console:
                print(full_message)
            
            # 文件輸出
            if self.enable_file:
                logging.info(f"{category.value} - {message}")
            
            # 更新統計
            self._update_stats(category, level)
            
        except Exception as e:
            print(f"❌ [LOGGER] 日誌記錄失敗: {e}")
    
    def _get_log_prefix(self, category: LogCategory, level: LogLevel) -> str:
        """取得日誌前綴"""
        category_icons = {
            LogCategory.STRATEGY: "🎯",
            LogCategory.POSITION: "📊",
            LogCategory.RISK: "🛡️",
            LogCategory.CONFIG: "⚙️",
            LogCategory.SYSTEM: "🔧"
        }
        
        level_icons = {
            LogLevel.DEBUG: "🔍",
            LogLevel.INFO: "ℹ️",
            LogLevel.WARNING: "⚠️",
            LogLevel.ERROR: "❌",
            LogLevel.CRITICAL: "🚨"
        }
        
        category_icon = category_icons.get(category, "📝")
        level_icon = level_icons.get(level, "📝")
        
        return f"{category_icon} [{category.value}] {level_icon}"
    
    def _update_stats(self, category: LogCategory, level: LogLevel):
        """更新統計信息"""
        self.log_stats['total_logs'] += 1
        self.log_stats['by_category'][category] += 1
        self.log_stats['by_level'][level] += 1
    
    # 便利方法 - 策略相關
    def strategy_info(self, message: str, group_id: Optional[int] = None):
        """策略信息日誌"""
        self.log(LogCategory.STRATEGY, LogLevel.INFO, message, group_id=group_id)
    
    def strategy_warning(self, message: str, group_id: Optional[int] = None):
        """策略警告日誌"""
        self.log(LogCategory.STRATEGY, LogLevel.WARNING, message, group_id=group_id)
    
    def strategy_error(self, message: str, group_id: Optional[int] = None):
        """策略錯誤日誌"""
        self.log(LogCategory.STRATEGY, LogLevel.ERROR, message, group_id=group_id)
    
    # 便利方法 - 部位相關
    def position_entry(self, message: str, group_id: int, position_id: int):
        """部位進場日誌"""
        self.log(LogCategory.POSITION, LogLevel.INFO, f"進場: {message}", 
                group_id=group_id, position_id=position_id)
    
    def position_exit(self, message: str, group_id: int, position_id: int, pnl: float):
        """部位出場日誌"""
        pnl_icon = "💰" if pnl > 0 else "💸" if pnl < 0 else "⚖️"
        self.log(LogCategory.POSITION, LogLevel.INFO, 
                f"出場: {message} {pnl_icon} {pnl:+.1f}點", 
                group_id=group_id, position_id=position_id)
    
    def position_update(self, message: str, group_id: int, position_id: int):
        """部位更新日誌"""
        self.log(LogCategory.POSITION, LogLevel.DEBUG, message, 
                group_id=group_id, position_id=position_id)
    
    # 便利方法 - 風險管理相關
    def risk_activation(self, message: str, group_id: int, position_id: int):
        """風險管理啟動日誌"""
        self.log(LogCategory.RISK, LogLevel.INFO, f"啟動: {message}", 
                group_id=group_id, position_id=position_id)
    
    def risk_update(self, message: str, group_id: int, position_id: int):
        """風險管理更新日誌"""
        self.log(LogCategory.RISK, LogLevel.DEBUG, f"更新: {message}", 
                group_id=group_id, position_id=position_id)
    
    def risk_trigger(self, message: str, group_id: int, position_id: int):
        """風險管理觸發日誌"""
        self.log(LogCategory.RISK, LogLevel.WARNING, f"觸發: {message}", 
                group_id=group_id, position_id=position_id)
    
    # 便利方法 - 配置相關
    def config_change(self, message: str):
        """配置變更日誌"""
        self.log(LogCategory.CONFIG, LogLevel.INFO, message)
    
    def config_error(self, message: str):
        """配置錯誤日誌"""
        self.log(LogCategory.CONFIG, LogLevel.ERROR, message)
    
    # 便利方法 - 系統相關
    def system_info(self, message: str):
        """系統信息日誌"""
        self.log(LogCategory.SYSTEM, LogLevel.INFO, message)
    
    def system_error(self, message: str):
        """系統錯誤日誌"""
        self.log(LogCategory.SYSTEM, LogLevel.ERROR, message)
    
    # Console控制方法
    def toggle_category_console(self, category: LogCategory) -> bool:
        """切換分類的Console輸出"""
        current_state = self.console_controls.get(category, True)
        new_state = not current_state
        self.console_controls[category] = new_state
        
        state_text = "開啟" if new_state else "關閉"
        print(f"🔧 [LOGGER] {category.value} Console輸出已{state_text}")
        
        return new_state
    
    def set_category_console(self, category: LogCategory, enabled: bool):
        """設定分類的Console輸出狀態"""
        self.console_controls[category] = enabled
        state_text = "開啟" if enabled else "關閉"
        print(f"🔧 [LOGGER] {category.value} Console輸出已{state_text}")
    
    def get_console_status(self) -> Dict[str, bool]:
        """取得Console輸出狀態"""
        return {cat.value: enabled for cat, enabled in self.console_controls.items()}
    
    def get_log_statistics(self) -> Dict:
        """取得日誌統計信息"""
        return {
            'total_logs': self.log_stats['total_logs'],
            'by_category': {cat.value: count for cat, count in self.log_stats['by_category'].items()},
            'by_level': {level.value: count for level, count in self.log_stats['by_level'].items()},
            'console_status': self.get_console_status()
        }
    
    def print_statistics(self):
        """打印統計信息"""
        stats = self.get_log_statistics()
        
        print("\n📊 [LOGGER] 日誌統計信息")
        print("=" * 40)
        print(f"總日誌數: {stats['total_logs']}")
        
        print("\n📋 分類統計:")
        for category, count in stats['by_category'].items():
            print(f"   {category}: {count}")
        
        print("\n📈 級別統計:")
        for level, count in stats['by_level'].items():
            print(f"   {level}: {count}")
        
        print("\n🎛️ Console狀態:")
        for category, enabled in stats['console_status'].items():
            status = "✅ 開啟" if enabled else "❌ 關閉"
            print(f"   {category}: {status}")

# 全局日誌器實例
_global_logger: Optional[MultiGroupConsoleLogger] = None

def get_logger() -> MultiGroupConsoleLogger:
    """取得全局日誌器實例"""
    global _global_logger
    if _global_logger is None:
        _global_logger = MultiGroupConsoleLogger()
    return _global_logger

def init_logger(enable_console: bool = True, enable_file: bool = False) -> MultiGroupConsoleLogger:
    """初始化全局日誌器"""
    global _global_logger
    _global_logger = MultiGroupConsoleLogger(enable_console, enable_file)
    return _global_logger

if __name__ == "__main__":
    # 測試多組策略Console日誌系統
    print("🧪 測試多組策略Console日誌系統")
    print("=" * 50)
    
    # 創建日誌器
    logger = MultiGroupConsoleLogger(enable_console=True, enable_file=False)
    
    # 測試各種日誌
    print("\n📝 測試策略日誌:")
    logger.strategy_info("策略系統啟動", group_id=1)
    logger.strategy_info("創建進場信號: LONG @ 08:48:15", group_id=1)
    
    print("\n📝 測試部位日誌:")
    logger.position_entry("第1口 @ 22535", group_id=1, position_id=1)
    logger.position_entry("第2口 @ 22536", group_id=1, position_id=2)
    logger.position_exit("移動停利", group_id=1, position_id=1, pnl=25.0)
    
    print("\n📝 測試風險管理日誌:")
    logger.risk_activation("移動停利啟動 @ 22550", group_id=1, position_id=1)
    logger.risk_update("峰值更新: 22565", group_id=1, position_id=1)
    logger.risk_trigger("移動停利觸發 @ 22555", group_id=1, position_id=1)
    
    print("\n📝 測試配置日誌:")
    logger.config_change("應用配置: 2組×2口")
    logger.config_change("切換為積極配置: 3組×3口")
    
    print("\n📝 測試Console控制:")
    logger.toggle_category_console(LogCategory.POSITION)
    logger.position_entry("這條訊息不應該顯示", group_id=2, position_id=3)
    logger.toggle_category_console(LogCategory.POSITION)
    logger.position_entry("這條訊息應該顯示", group_id=2, position_id=3)
    
    print("\n📊 統計信息:")
    logger.print_statistics()
    
    print("\n✅ 多組策略Console日誌系統測試完成")
