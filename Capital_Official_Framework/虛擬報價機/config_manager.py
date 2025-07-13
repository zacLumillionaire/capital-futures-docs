# 配置管理器
# Configuration Manager for Virtual Quote Machine

import json
import os
from typing import Dict, Any, Optional

class ConfigManager:
    """虛擬報價機配置管理器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路徑
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config = {}
        self.load_config()
    
    def _get_default_config_path(self) -> str:
        """取得預設配置文件路徑"""
        return os.path.join(os.path.dirname(__file__), 'config.json')
    
    def load_config(self) -> None:
        """載入配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                print(f"✅ [Config] 配置載入成功: {self.config_path}")
            else:
                self.config = self._get_default_config()
                self.save_config()
                print(f"⚠️ [Config] 使用預設配置並儲存: {self.config_path}")
        except Exception as e:
            print(f"❌ [Config] 配置載入失敗: {e}")
            self.config = self._get_default_config()
    
    def save_config(self) -> None:
        """儲存配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            print(f"✅ [Config] 配置儲存成功: {self.config_path}")
        except Exception as e:
            print(f"❌ [Config] 配置儲存失敗: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """取得預設配置"""
        return {
            "virtual_quote_config": {
                "base_price": 21500,
                "price_range": 50,
                "spread": 5,
                "quote_interval": 0.5,
                "fill_probability": 0.95,
                "fill_delay_ms": 200,
                "volatility": 0.02,
                "trend_factor": 0.0
            },
            "market_config": {
                "product": "MTX00",
                "market_no": 1,
                "stock_idx": 0,
                "trading_hours": {
                    "start": "08:45:00",
                    "end": "13:45:00"
                }
            },
            "order_config": {
                "default_account": "F0200006363839",
                "order_types": ["ROD", "IOC", "FOK"],
                "default_order_type": "FOK",
                "max_quantity": 10,
                "min_quantity": 1
            },
            "best5_config": {
                "enabled": True,
                "depth_levels": 5,
                "quantity_range": [10, 50],
                "price_step": 5
            },
            "logging_config": {
                "enabled": True,
                "level": "INFO",
                "console_output": True,
                "file_output": False,
                "log_file": "virtual_quote_machine.log"
            },
            "performance_config": {
                "max_memory_mb": 100,
                "max_cpu_percent": 5,
                "quote_buffer_size": 1000,
                "order_buffer_size": 500
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """取得配置值"""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """設定配置值"""
        keys = key.split('.')
        config = self.config
        
        # 導航到最後一層
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 設定值
        config[keys[-1]] = value
    
    def get_quote_config(self) -> Dict[str, Any]:
        """取得報價配置"""
        return self.get('virtual_quote_config', {})
    
    def get_market_config(self) -> Dict[str, Any]:
        """取得市場配置"""
        return self.get('market_config', {})
    
    def get_order_config(self) -> Dict[str, Any]:
        """取得下單配置"""
        return self.get('order_config', {})
    
    def get_best5_config(self) -> Dict[str, Any]:
        """取得五檔配置"""
        return self.get('best5_config', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """取得日誌配置"""
        return self.get('logging_config', {})
    
    def get_performance_config(self) -> Dict[str, Any]:
        """取得性能配置"""
        return self.get('performance_config', {})
    
    # 便捷方法
    def get_base_price(self) -> float:
        """取得基準價格"""
        return self.get('virtual_quote_config.base_price', 21500)
    
    def get_price_range(self) -> float:
        """取得價格波動範圍"""
        return self.get('virtual_quote_config.price_range', 50)
    
    def get_spread(self) -> float:
        """取得買賣價差"""
        return self.get('virtual_quote_config.spread', 5)
    
    def get_quote_interval(self) -> float:
        """取得報價間隔"""
        return self.get('virtual_quote_config.quote_interval', 0.5)
    
    def get_fill_probability(self) -> float:
        """取得成交機率"""
        return self.get('virtual_quote_config.fill_probability', 0.95)
    
    def get_fill_delay_ms(self) -> int:
        """取得成交延遲"""
        return self.get('virtual_quote_config.fill_delay_ms', 200)
    
    def get_product(self) -> str:
        """取得商品代碼"""
        return self.get('market_config.product', 'MTX00')
    
    def get_default_account(self) -> str:
        """取得預設帳號"""
        return self.get('order_config.default_account', 'F0200006363839')
    
    def is_logging_enabled(self) -> bool:
        """檢查是否啟用日誌"""
        return self.get('logging_config.enabled', True)
    
    def is_console_output_enabled(self) -> bool:
        """檢查是否啟用控制台輸出"""
        return self.get('logging_config.console_output', True)
    
    def reload_config(self) -> None:
        """重新載入配置"""
        self.load_config()
        print("🔄 [Config] 配置已重新載入")
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """批量更新配置"""
        for key, value in updates.items():
            self.set(key, value)
        self.save_config()
        print(f"✅ [Config] 配置已更新: {list(updates.keys())}")
    
    def __str__(self) -> str:
        """字串表示"""
        return f"ConfigManager(path={self.config_path})"
    
    def __repr__(self) -> str:
        """詳細表示"""
        return f"ConfigManager(path='{self.config_path}', config_keys={list(self.config.keys())})"
