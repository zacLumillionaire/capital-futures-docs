#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
價格橋接模組
OrderTester和test_ui_improvements之間的價格數據傳遞

🔗 PRICE_BRIDGE_2025_06_30
✅ 簡單的檔案共享方式
✅ OrderTester寫入價格
✅ UI讀取價格
✅ 無需複雜的API初始化
"""

import json
import time
import os
from datetime import datetime
import threading
import logging

logger = logging.getLogger(__name__)

class PriceBridge:
    """價格橋接類 - 處理OrderTester和UI之間的價格傳遞"""
    
    def __init__(self, bridge_file="price_data.json"):
        self.bridge_file = bridge_file
        self.is_running = False
        self.last_update = None
        self.price_callback = None
        
    def write_price(self, price, volume=0, timestamp=None):
        """寫入價格數據 (OrderTester調用)"""
        try:
            if timestamp is None:
                timestamp = datetime.now()

            # 確保價格和時間戳正確
            current_time = time.time()

            price_data = {
                "price": float(price),
                "volume": int(volume),
                "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S.%f"),
                "update_time": current_time
            }

            # 使用臨時檔案避免讀寫衝突
            temp_file = self.bridge_file + ".tmp"

            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(price_data, f, ensure_ascii=False, indent=2)
                f.flush()  # 確保寫入完成
                os.fsync(f.fileno())  # 強制寫入磁碟

            # 原子性替換檔案
            if os.path.exists(self.bridge_file):
                os.remove(self.bridge_file)
            os.rename(temp_file, self.bridge_file)

            logger.debug(f"📊 寫入價格: {price}")
            return True

        except Exception as e:
            logger.error(f"❌ 寫入價格失敗: {e}")
            # 清理臨時檔案
            temp_file = self.bridge_file + ".tmp"
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            return False
    
    def read_price(self):
        """讀取價格數據 (UI調用) - 帶重試機制"""
        max_retries = 3
        retry_delay = 0.01  # 10ms

        for attempt in range(max_retries):
            try:
                if not os.path.exists(self.bridge_file):
                    return None

                # 檢查檔案大小，避免讀取空檔案
                if os.path.getsize(self.bridge_file) == 0:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    return None

                with open(self.bridge_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            continue
                        return None

                    price_data = json.loads(content)

                # 檢查數據是否太舊 (超過10秒，放寬限制)
                update_time = price_data.get('update_time', 0)
                current_time = time.time()
                if current_time - update_time > 10:
                    logger.warning("⚠️ 價格數據過舊")
                    return None

                return price_data

            except json.JSONDecodeError as e:
                if attempt < max_retries - 1:
                    logger.debug(f"JSON解析失敗，重試 {attempt + 1}/{max_retries}: {e}")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"❌ JSON解析失敗: {e}")
                    return None

            except Exception as e:
                if attempt < max_retries - 1:
                    logger.debug(f"讀取失敗，重試 {attempt + 1}/{max_retries}: {e}")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"❌ 讀取價格失敗: {e}")
                    return None

        return None
    
    def start_monitoring(self, callback):
        """開始監控價格變化 (UI調用)"""
        self.price_callback = callback
        self.is_running = True
        
        def monitor_thread():
            last_update_time = 0
            
            while self.is_running:
                try:
                    price_data = self.read_price()
                    
                    if price_data:
                        update_time = price_data.get('update_time', 0)
                        
                        # 只處理新的價格數據
                        if update_time > last_update_time:
                            last_update_time = update_time
                            
                            if self.price_callback:
                                self.price_callback(
                                    price_data['price'],
                                    price_data.get('volume', 0),
                                    datetime.strptime(price_data['timestamp'], "%Y-%m-%d %H:%M:%S.%f")
                                )
                    
                    time.sleep(0.1)  # 每100ms檢查一次
                    
                except Exception as e:
                    logger.error(f"❌ 監控價格失敗: {e}")
                    time.sleep(1)
        
        threading.Thread(target=monitor_thread, daemon=True).start()
        logger.info("🚀 價格監控已啟動")
    
    def stop_monitoring(self):
        """停止監控"""
        self.is_running = False
        logger.info("⏹️ 價格監控已停止")
    
    def cleanup(self):
        """清理橋接檔案"""
        try:
            if os.path.exists(self.bridge_file):
                os.remove(self.bridge_file)
                logger.info("🗑️ 橋接檔案已清理")
        except Exception as e:
            logger.error(f"❌ 清理橋接檔案失敗: {e}")

# 全域橋接實例
price_bridge = PriceBridge()

def write_price_to_bridge(price, volume=0, timestamp=None):
    """便利函數：寫入價格到橋接 (OrderTester使用)"""
    return price_bridge.write_price(price, volume, timestamp)

def start_price_monitoring(callback):
    """便利函數：開始價格監控 (UI使用)"""
    return price_bridge.start_monitoring(callback)

def stop_price_monitoring():
    """便利函數：停止價格監控"""
    return price_bridge.stop_monitoring()

def get_latest_price():
    """便利函數：取得最新價格"""
    price_data = price_bridge.read_price()
    return price_data['price'] if price_data else None

if __name__ == "__main__":
    # 測試用例
    print("🧪 價格橋接測試")
    
    # 測試寫入
    print("📊 測試寫入價格...")
    for i in range(5):
        price = 22000 + i
        write_price_to_bridge(price, 100)
        print(f"  寫入價格: {price}")
        time.sleep(0.5)
    
    # 測試讀取
    print("\n📊 測試讀取價格...")
    price_data = price_bridge.read_price()
    if price_data:
        print(f"  讀取價格: {price_data['price']}")
        print(f"  時間戳: {price_data['timestamp']}")
    else:
        print("  無價格數據")
    
    # 測試監控
    print("\n📊 測試價格監控...")
    def test_callback(price, volume, timestamp):
        print(f"  收到價格: {price} @ {timestamp.strftime('%H:%M:%S')}")
    
    start_price_monitoring(test_callback)
    
    # 模擬價格更新
    for i in range(3):
        time.sleep(1)
        price = 22010 + i
        write_price_to_bridge(price, 150)
    
    stop_price_monitoring()
    price_bridge.cleanup()
    
    print("✅ 測試完成")
