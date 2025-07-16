# 配置管理器
# Configuration Manager for Virtual Quote Machine

import json
import os
import shutil
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

class ConfigManager:
    """虛擬報價機配置管理器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路徑
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config_dir = os.path.dirname(self.config_path)
        self.backup_dir = os.path.join(self.config_dir, "config_backups")
        self.config = {}

        # 確保備份目錄存在
        os.makedirs(self.backup_dir, exist_ok=True)

        # 🔧 新增：可用配置定義
        self.available_configs = {
            "entry_test": {
                "name": "建倉測試",
                "file": "config_entry_test.json",
                "description": "穩定價格環境，適合測試進場建倉邏輯",
                "icon": "🏗️"
            },
            "entry_chase": {
                "name": "建倉追價測試",
                "file": "config_entry_chase.json",
                "description": "快速變動價格環境，測試追價機制",
                "icon": "🏃"
            },
            "trailing_stop": {
                "name": "移動停利測試",
                "file": "config_trailing_stop.json",
                "description": "趨勢性價格變動，測試移動停利啟動與平倉",
                "icon": "📈"
            },
            "stop_loss": {
                "name": "停損測試",
                "file": "config_stop_loss.json",
                "description": "逆向價格變動，測試停損觸發機制",
                "icon": "🛡️"
            },
            "stop_chase": {
                "name": "停損追價測試",
                "file": "config_stop_chase.json",
                "description": "快速惡化環境，測試停損追價機制",
                "icon": "🚨"
            },
            "stress_test": {
                "name": "綜合壓力測試",
                "file": "config_stress_test.json",
                "description": "極端市場環境，測試系統穩定性",
                "icon": "⚡"
            }
        }

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

    # 🔧 新增：配置切換功能
    def get_config_list(self) -> List[Tuple[str, str, str, str]]:
        """
        獲取配置列表

        Returns:
            List[Tuple[key, name, description, icon]]: 配置列表
        """
        config_list = []
        for key, config in self.available_configs.items():
            config_list.append((
                key,
                config['name'],
                config['description'],
                config['icon']
            ))
        return config_list

    def get_current_config_info(self) -> Tuple[str, str, str]:
        """
        獲取當前配置資訊

        Returns:
            Tuple[scenario, description, icon]: 當前配置資訊
        """
        try:
            scenario = self.config.get('scenario', '未知場景')
            description = self.config.get('description', '無描述')

            # 嘗試找到對應的圖標
            icon = "⚙️"  # 默認圖標
            for key, cfg in self.available_configs.items():
                if cfg['name'] == scenario:
                    icon = cfg['icon']
                    break

            return scenario, description, icon
        except Exception as e:
            return "無法讀取", str(e), "❌"

    def backup_current_config(self) -> bool:
        """
        備份當前配置

        Returns:
            bool: 備份是否成功
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.backup_dir, f"config_backup_{timestamp}.json")
            shutil.copy2(self.config_path, backup_file)
            print(f"✅ [Config] 配置已備份: {backup_file}")
            return True
        except Exception as e:
            print(f"❌ [Config] 備份配置失敗: {e}")
            return False

    def switch_config(self, config_key: str) -> bool:
        """
        切換配置

        Args:
            config_key: 配置鍵值

        Returns:
            bool: 切換是否成功
        """
        if config_key not in self.available_configs:
            print(f"❌ [Config] 無效的配置鍵值: {config_key}")
            return False

        config_info = self.available_configs[config_key]
        source_file = os.path.join(self.config_dir, config_info['file'])

        if not os.path.exists(source_file):
            print(f"❌ [Config] 配置文件不存在: {source_file}")
            return False

        try:
            # 備份當前配置
            self.backup_current_config()

            # 切換配置
            shutil.copy2(source_file, self.config_path)

            # 重新加載配置
            self.load_config()

            print(f"✅ [Config] 已切換到: {config_info['name']}")
            print(f"📝 [Config] 描述: {config_info['description']}")

            return True

        except Exception as e:
            print(f"❌ [Config] 切換配置失敗: {e}")
            return False

    def hot_reload_config(self) -> bool:
        """
        熱重載配置（不重啟程序）

        Returns:
            bool: 重載是否成功
        """
        try:
            old_config = self.config.copy()
            self.load_config()

            # 檢查關鍵配置是否有變化
            critical_changes = []
            critical_keys = [
                'virtual_quote_config.base_price',
                'virtual_quote_config.price_range',
                'virtual_quote_config.spread',
                'virtual_quote_config.quote_interval',
                'virtual_quote_config.volatility'
            ]

            for key in critical_keys:
                old_value = self._get_nested_value(old_config, key)
                new_value = self.get(key)
                if old_value != new_value:
                    critical_changes.append(f"{key}: {old_value} → {new_value}")

            if critical_changes:
                print("🔄 [Config] 檢測到關鍵配置變化:")
                for change in critical_changes:
                    print(f"   📝 {change}")
                print("💡 [Config] 虛擬報價機將使用新配置")

            return True

        except Exception as e:
            print(f"❌ [Config] 熱重載失敗: {e}")
            return False

    def _get_nested_value(self, config: Dict, key: str) -> Any:
        """獲取嵌套配置值"""
        keys = key.split('.')
        value = config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return None
