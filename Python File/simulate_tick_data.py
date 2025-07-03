"""
模擬Tick資料發送工具
用於測試OrderTester.py中的Queue架構處理能力
"""

import time
import threading
import random
from datetime import datetime

try:
    from queue_infrastructure import (
        get_queue_manager,
        TickData
    )
    print("✅ Queue基礎設施連接成功")
except ImportError as e:
    print(f"❌ 無法連接Queue基礎設施: {e}")
    exit(1)

class TickDataSimulator:
    """Tick資料模擬器"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.stats = {
            'sent': 0,
            'failed': 0,
            'start_time': None
        }
        
    def start_simulation(self, interval=0.5, price_base=22461):
        """開始模擬Tick資料"""
        if self.running:
            print("⚠️ 模擬器已在運行中")
            return
        
        self.running = True
        self.stats = {
            'sent': 0,
            'failed': 0,
            'start_time': datetime.now()
        }
        
        self.thread = threading.Thread(
            target=self._simulation_loop,
            args=(interval, price_base),
            daemon=True
        )
        self.thread.start()
        
        print(f"🚀 Tick模擬器已啟動 (間隔: {interval}秒, 基準價: {price_base})")
    
    def stop_simulation(self):
        """停止模擬"""
        if not self.running:
            print("⚠️ 模擬器未在運行")
            return
        
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        
        duration = (datetime.now() - self.stats['start_time']).total_seconds()
        print(f"🛑 Tick模擬器已停止")
        print(f"📊 統計: 發送={self.stats['sent']}, 失敗={self.stats['failed']}, 運行={duration:.1f}秒")
    
    def _simulation_loop(self, interval, price_base):
        """模擬循環"""
        queue_manager = get_queue_manager()
        counter = 0
        
        while self.running:
            try:
                # 生成模擬價格 (隨機波動)
                price_change = random.randint(-10, 10)  # -10到+10的變化
                current_price = price_base + price_change
                
                # 生成買賣價
                spread = random.randint(1, 3)
                bid_price = current_price - spread
                ask_price = current_price + spread
                
                # 生成成交量
                qty = random.randint(1, 10)
                
                # 生成時間
                current_time = datetime.now()
                time_hms = int(current_time.strftime("%H%M%S"))
                
                # 創建Tick資料
                tick_data = TickData(
                    market_no="TW",
                    stock_idx=1,
                    date=int(current_time.strftime("%Y%m%d")),
                    time_hms=time_hms,
                    time_millis=current_time.microsecond // 1000,
                    bid=bid_price,
                    ask=ask_price,
                    close=current_price,
                    qty=qty,
                    timestamp=current_time
                )
                
                # 發送到Queue
                if queue_manager.put_tick_data(tick_data):
                    self.stats['sent'] += 1
                    counter += 1
                    
                    # 每10個Tick顯示一次進度
                    if counter % 10 == 0:
                        print(f"📈 已發送 {counter} 個Tick, 最新價格: {current_price}")
                else:
                    self.stats['failed'] += 1
                    print(f"❌ Tick發送失敗 (Queue已滿)")
                
                time.sleep(interval)
                
            except Exception as e:
                self.stats['failed'] += 1
                print(f"❌ 模擬過程中發生錯誤: {e}")
                time.sleep(1)  # 錯誤後暫停1秒
    
    def get_stats(self):
        """獲取統計資訊"""
        if self.stats['start_time']:
            duration = (datetime.now() - self.stats['start_time']).total_seconds()
            rate = self.stats['sent'] / max(duration, 1)
        else:
            duration = 0
            rate = 0
        
        return {
            'sent': self.stats['sent'],
            'failed': self.stats['failed'],
            'duration': duration,
            'rate': rate,
            'running': self.running
        }

def main():
    """主函數"""
    print("📊 Tick資料模擬器")
    print("=" * 50)
    print("📝 此工具將向OrderTester.py的Queue發送模擬Tick資料")
    print("💡 請確保OrderTester.py已啟動且Queue服務已啟動")
    print()
    
    simulator = TickDataSimulator()
    
    try:
        # 檢查Queue狀態
        print("🔍 檢查Queue狀態...")
        queue_manager = get_queue_manager()
        queue_status = queue_manager.get_queue_status()
        
        if not queue_status.get('running', False):
            print("❌ Queue管理器未運行")
            print("🔧 請在OrderTester.py中啟動Queue服務")
            return
        
        print("✅ Queue管理器運行正常")
        print(f"📦 Tick佇列: {queue_status.get('tick_queue_size', 0)}/{queue_status.get('tick_queue_maxsize', 0)}")
        
        # 開始模擬
        print("\n🚀 開始Tick資料模擬...")
        print("⚠️ 按 Ctrl+C 停止模擬")
        
        # 啟動模擬器 (每0.2秒一個Tick，基準價22461)
        simulator.start_simulation(interval=0.2, price_base=22461)
        
        # 監控統計
        while simulator.running:
            time.sleep(5)  # 每5秒顯示統計
            
            stats = simulator.get_stats()
            queue_status = queue_manager.get_queue_status()
            
            print(f"\n📊 運行統計 ({datetime.now().strftime('%H:%M:%S')}):")
            print(f"  • 已發送Tick: {stats['sent']}")
            print(f"  • 發送失敗: {stats['failed']}")
            print(f"  • 發送速率: {stats['rate']:.1f} Tick/秒")
            print(f"  • Queue狀態: {queue_status.get('tick_queue_size', 0)}/{queue_status.get('tick_queue_maxsize', 0)}")
            print(f"  • 已處理: {queue_status.get('stats', {}).get('tick_processed', 0)}")
    
    except KeyboardInterrupt:
        print("\n⏹️ 用戶停止模擬")
    except Exception as e:
        print(f"\n❌ 模擬過程中發生錯誤: {e}")
    finally:
        simulator.stop_simulation()
        
        # 最終統計
        final_stats = simulator.get_stats()
        print(f"\n📊 最終統計:")
        print(f"  • 總發送: {final_stats['sent']} 個Tick")
        print(f"  • 總失敗: {final_stats['failed']} 個Tick")
        print(f"  • 運行時間: {final_stats['duration']:.1f} 秒")
        print(f"  • 平均速率: {final_stats['rate']:.1f} Tick/秒")
        
        if final_stats['sent'] > 0:
            print("✅ 模擬測試成功！Queue架構正常工作")
        else:
            print("❌ 模擬測試失敗，請檢查Queue配置")

if __name__ == "__main__":
    main()
