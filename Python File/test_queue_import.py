"""
測試Queue基礎設施導入
"""

import sys
import os

print("🧪 測試Queue基礎設施導入...")
print(f"當前工作目錄: {os.getcwd()}")
print(f"Python路徑: {sys.path}")

try:
    from queue_infrastructure import (
        get_queue_infrastructure, 
        TickData, 
        get_queue_manager
    )
    print("✅ Queue基礎設施導入成功")
    
    # 測試基本功能
    queue_manager = get_queue_manager()
    print(f"✅ QueueManager實例創建成功: {queue_manager}")
    
    # 測試TickData創建
    from datetime import datetime
    tick_data = TickData(
        market_no="TW",
        stock_idx=1,
        date=20250703,
        time_hms=143000,
        time_millis=500,
        bid=2246100,
        ask=2246200,
        close=2246200,
        qty=5,
        timestamp=datetime.now()
    )
    print(f"✅ TickData創建成功: {tick_data}")
    
    print("🎉 所有測試通過！")
    
except ImportError as e:
    print(f"❌ Queue基礎設施導入失敗: {e}")
    print("📁 檢查目錄結構...")
    
    if os.path.exists("queue_infrastructure"):
        print("✅ queue_infrastructure目錄存在")
        files = os.listdir("queue_infrastructure")
        print(f"📂 目錄內容: {files}")
    else:
        print("❌ queue_infrastructure目錄不存在")
        
except Exception as e:
    print(f"❌ 其他錯誤: {e}")
