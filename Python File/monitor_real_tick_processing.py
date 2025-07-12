"""
實時監控群益API Tick資料處理
監控OrderTester.py中Queue架構對實際Tick資料的處理情況
"""

import time
import threading
from datetime import datetime, timedelta

try:
    from queue_infrastructure import (
        get_queue_manager,
        get_tick_processor
    )
    print("✅ Queue基礎設施連接成功")
except ImportError as e:
    print(f"❌ 無法連接Queue基礎設施: {e}")
    exit(1)

class RealTickMonitor:
    """實時Tick監控器"""
    
    def __init__(self):
        self.monitoring = False
        self.monitor_thread = None
        self.last_stats = None
        self.start_time = None
        
    def start_monitoring(self, interval=2):
        """開始監控"""
        if self.monitoring:
            print("⚠️ 監控器已在運行中")
            return
        
        self.monitoring = True
        self.start_time = datetime.now()
        self.last_stats = None
        
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        
        print(f"🔍 實時Tick監控已啟動 (間隔: {interval}秒)")
        print("📝 監控OrderTester.py中的Queue架構處理實際群益API資料")
        print("-" * 60)
    
    def stop_monitoring(self):
        """停止監控"""
        if not self.monitoring:
            print("⚠️ 監控器未在運行")
            return
        
        self.monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
        
        duration = (datetime.now() - self.start_time).total_seconds()
        print(f"\n🛑 監控已停止 (運行時間: {duration:.1f}秒)")
    
    def _monitoring_loop(self, interval):
        """監控循環"""
        while self.monitoring:
            try:
                self._check_and_display_status()
                time.sleep(interval)
            except Exception as e:
                print(f"❌ 監控過程中發生錯誤: {e}")
                time.sleep(interval)
    
    def _check_and_display_status(self):
        """檢查並顯示狀態"""
        try:
            current_time = datetime.now()
            
            # 獲取Queue管理器狀態
            queue_manager = get_queue_manager()
            queue_status = queue_manager.get_queue_status()
            
            # 獲取Tick處理器狀態
            tick_processor = get_tick_processor()
            processor_status = tick_processor.get_status()
            
            # 當前統計
            current_stats = {
                'tick_received': queue_status.get('stats', {}).get('tick_received', 0),
                'tick_processed': queue_status.get('stats', {}).get('tick_processed', 0),
                'log_generated': queue_status.get('stats', {}).get('log_generated', 0),
                'queue_full_errors': queue_status.get('stats', {}).get('queue_full_errors', 0),
                'processing_errors': queue_status.get('stats', {}).get('processing_errors', 0),
                'processor_count': processor_status.get('stats', {}).get('processed_count', 0),
                'processor_errors': processor_status.get('stats', {}).get('error_count', 0),
                'tick_queue_size': queue_status.get('tick_queue_size', 0),
                'log_queue_size': queue_status.get('log_queue_size', 0)
            }
            
            # 計算增量
            if self.last_stats:
                delta_stats = {
                    key: current_stats[key] - self.last_stats[key] 
                    for key in current_stats.keys()
                }
            else:
                delta_stats = {key: 0 for key in current_stats.keys()}
            
            # 顯示狀態
            self._display_status(current_time, current_stats, delta_stats, queue_status, processor_status)
            
            # 更新上次統計
            self.last_stats = current_stats.copy()
            
        except Exception as e:
            print(f"❌ 狀態檢查錯誤: {e}")
    
    def _display_status(self, current_time, current_stats, delta_stats, queue_status, processor_status):
        """顯示狀態資訊"""
        time_str = current_time.strftime("%H:%M:%S")
        
        # 系統狀態
        queue_running = queue_status.get('running', False)
        processor_running = processor_status.get('running', False)
        processor_alive = processor_status.get('thread_alive', False)
        
        status_icon = "✅" if (queue_running and processor_running and processor_alive) else "❌"
        
        print(f"\n🕐 {time_str} {status_icon} Queue架構狀態:")
        
        # 基本狀態
        print(f"  📦 Queue管理器: {'✅ 運行' if queue_running else '❌ 停止'}")
        print(f"  🔄 Tick處理器: {'✅ 運行' if processor_running else '❌ 停止'} "
              f"({'✅ 線程存活' if processor_alive else '❌ 線程死亡'})")
        
        # 佇列狀態
        tick_queue_usage = f"{current_stats['tick_queue_size']}/{queue_status.get('tick_queue_maxsize', 0)}"
        log_queue_usage = f"{current_stats['log_queue_size']}/{queue_status.get('log_queue_maxsize', 0)}"
        
        print(f"  📊 Tick佇列: {tick_queue_usage}")
        print(f"  📝 日誌佇列: {log_queue_usage}")
        
        # 處理統計 (總計 + 增量)
        print(f"  📈 已接收Tick: {current_stats['tick_received']} (+{delta_stats['tick_received']})")
        print(f"  ✅ 已處理Tick: {current_stats['tick_processed']} (+{delta_stats['tick_processed']})")
        print(f"  📄 已生成日誌: {current_stats['log_generated']} (+{delta_stats['log_generated']})")
        
        # 錯誤統計
        if current_stats['queue_full_errors'] > 0 or current_stats['processing_errors'] > 0:
            print(f"  ⚠️ Queue滿錯誤: {current_stats['queue_full_errors']} (+{delta_stats['queue_full_errors']})")
            print(f"  ❌ 處理錯誤: {current_stats['processing_errors']} (+{delta_stats['processing_errors']})")
        
        # 處理效率
        if current_stats['tick_received'] > 0:
            efficiency = (current_stats['tick_processed'] / current_stats['tick_received']) * 100
            print(f"  🎯 處理效率: {efficiency:.1f}%")
        
        # 實時活動檢測
        if delta_stats['tick_received'] > 0:
            print(f"  🔥 實時活動: 新增 {delta_stats['tick_received']} 個Tick")
        elif current_stats['tick_received'] == 0:
            print(f"  ⏳ 等待資料: 尚未收到任何Tick (請確認市場開盤或有交易活動)")
        else:
            print(f"  😴 無新資料: 最近無新Tick進入")
        
        # 回調函數狀態
        callback_count = processor_status.get('callback_count', 0)
        if callback_count > 0:
            print(f"  🎯 策略回調: {callback_count} 個已註冊")
        
        # 最後處理時間
        last_process_time = processor_status.get('stats', {}).get('last_process_time')
        if last_process_time:
            time_diff = (datetime.now() - last_process_time).total_seconds()
            if time_diff < 60:
                print(f"  ⏰ 最後處理: {time_diff:.1f}秒前")
            else:
                print(f"  ⏰ 最後處理: {last_process_time.strftime('%H:%M:%S')}")

def main():
    """主函數"""
    print("🔍 群益API實時Tick處理監控器")
    print("=" * 60)
    print("📝 此工具監控OrderTester.py中Queue架構對實際群益API資料的處理")
    print("💡 請確保:")
    print("   1. OrderTester.py已啟動")
    print("   2. 已點擊'監控報價'啟動群益API報價")
    print("   3. Queue服務已啟動")
    print("   4. 已切換到Queue模式")
    print()
    
    monitor = RealTickMonitor()
    
    try:
        # 初始狀態檢查
        print("🔍 檢查初始狀態...")
        queue_manager = get_queue_manager()
        queue_status = queue_manager.get_queue_status()
        
        if not queue_status.get('running', False):
            print("❌ Queue管理器未運行")
            print("🔧 請在OrderTester.py中:")
            print("   1. 找到 '🚀 Queue架構控制' 面板")
            print("   2. 點擊 '🚀 啟動Queue服務'")
            print("   3. 確認狀態顯示 '✅ 運行中'")
            return
        
        tick_processor = get_tick_processor()
        processor_status = tick_processor.get_status()
        
        if not processor_status.get('running', False):
            print("❌ Tick處理器未運行")
            print("🔧 請檢查Queue服務是否正常啟動")
            return
        
        print("✅ Queue架構狀態正常，開始監控...")
        print("⚠️ 按 Ctrl+C 停止監控")
        print()
        
        # 開始監控
        monitor.start_monitoring(interval=3)  # 每3秒檢查一次
        
        # 保持運行
        while monitor.monitoring:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n⏹️ 用戶停止監控")
    except Exception as e:
        print(f"\n❌ 監控過程中發生錯誤: {e}")
    finally:
        monitor.stop_monitoring()
        
        print("\n📊 監控總結:")
        print("✅ 如果看到 '實時活動: 新增 X 個Tick'，說明Queue架構正常處理群益API資料")
        print("⏳ 如果顯示 '等待資料'，可能是市場未開盤或無交易活動")
        print("❌ 如果有錯誤統計，請檢查OrderTester.py的日誌訊息")

if __name__ == "__main__":
    main()
