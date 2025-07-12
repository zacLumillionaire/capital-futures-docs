# 🚀 Queue方案實施指南

## 📋 **實施前準備**

### **1. 備份關鍵文件**
```bash
# 在 Python File 目錄下執行
copy "OrderTester.py" "OrderTester_pre_queue_backup.py"
copy "order\future_order.py" "order\future_order_pre_queue_backup.py"
```

### **2. 確認當前狀態**
- ✅ 程式能正常啟動
- ✅ 策略監控功能正常
- ✅ 下單功能正常
- ✅ 已閱讀完整實施計畫

---

## 🔧 **步驟1: 建立Queue基礎架構** (30分鐘)

### **目標文件**: `Python File/OrderTester.py`

### **修改位置**: 類初始化 `__init__` 方法

**在現有初始化代碼後添加**:
```python
# 🚀 Queue機制：建立線程安全的佇列系統
self.tick_data_queue = queue.Queue(maxsize=1000)    # 原始Tick數據
self.strategy_queue = queue.Queue(maxsize=100)      # 策略處理數據  
self.log_queue = queue.Queue(maxsize=500)           # UI日誌更新

# 策略執行緒控制
self.strategy_thread = None
self.strategy_thread_running = False

print("✅ Queue機制已初始化")
```

### **添加導入**:
在文件頂部添加：
```python
import queue
import threading
import time
```

### **驗證步驟1**:
1. 啟動程式，確認無語法錯誤
2. 檢查控制台是否顯示 "✅ Queue機制已初始化"

---

## 🔧 **步驟2: 修改COM事件處理** (45分鐘)

### **目標文件**: `Python File/order/future_order.py`

### **修改函數**: `OnNotifyTicksLONG`

**找到現有的函數並完全替換**:
```python
def OnNotifyTicksLONG(self, sMarketNo, nStockidx, nPtr, lDate, lTimehms, lTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate):
    """COM事件 - 只負責數據打包，絕不操作UI"""
    try:
        # 只做最基本的數據打包
        tick_data = {
            'type': 'tick',
            'market': sMarketNo,
            'stock_idx': nStockidx,
            'date': lDate,
            'time': lTimehms,
            'bid': nBid,
            'ask': nAsk,
            'close': nClose,
            'qty': nQty,
            'timestamp': time.time()
        }

        # 非阻塞放入佇列
        if hasattr(self.parent, 'tick_data_queue') and not self.parent.tick_data_queue.full():
            self.parent.tick_data_queue.put_nowait(tick_data)

    except Exception:
        # 絕對不拋出任何異常
        pass
    return 0
```

### **同樣修改**: `OnNotifyBest5LONG` (如果存在)

### **驗證步驟2**:
1. 啟動程式，確認無語法錯誤
2. 連接報價，觀察是否有Tick數據進入Queue

---

## 🔧 **步驟3: 建立主線程Queue處理** (60分鐘)

### **目標文件**: `Python File/OrderTester.py`

### **添加新函數** (在類中添加以下方法):

```python
def start_queue_processing(self):
    """啟動Queue處理機制"""
    self.process_tick_queue()
    self.process_log_queue()
    print("✅ Queue處理機制已啟動")

def process_tick_queue(self):
    """主線程中安全處理Tick佇列"""
    try:
        processed_count = 0
        while not self.tick_data_queue.empty() and processed_count < 10:
            try:
                data = self.tick_data_queue.get_nowait()

                if data['type'] == 'tick':
                    # 處理價格數據
                    corrected_price = data['close'] / 100.0 if data['close'] > 100000 else data['close']
                    time_str = f"{data['time']:06d}"
                    formatted_time = f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"

                    # 安全更新UI (在主線程中)
                    if hasattr(self, 'label_price'):
                        self.label_price.config(text=f"{corrected_price:.0f}")
                    if hasattr(self, 'label_time'):
                        self.label_time.config(text=formatted_time)

                    # 傳遞給策略處理
                    if hasattr(self, 'strategy_monitoring') and self.strategy_monitoring:
                        strategy_data = {
                            'price': corrected_price,
                            'time': formatted_time,
                            'timestamp': data['timestamp']
                        }
                        if not self.strategy_queue.full():
                            self.strategy_queue.put_nowait(strategy_data)

                processed_count += 1

            except queue.Empty:
                break
            except Exception as e:
                print(f"處理Tick佇列錯誤: {e}")

    except Exception as e:
        print(f"Tick佇列處理異常: {e}")
    finally:
        # 每50ms檢查一次
        if hasattr(self, 'root'):
            self.root.after(50, self.process_tick_queue)

def process_log_queue(self):
    """處理日誌佇列"""
    try:
        processed_count = 0
        while not self.log_queue.empty() and processed_count < 5:
            try:
                log_message = self.log_queue.get_nowait()
                
                # 安全更新策略日誌
                if hasattr(self, 'strategy_log_text'):
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    log_entry = f"[{timestamp}] {log_message}\n"
                    self.strategy_log_text.insert(tk.END, log_entry)
                    self.strategy_log_text.see(tk.END)
                
                processed_count += 1
                
            except queue.Empty:
                break
            except Exception as e:
                print(f"處理日誌佇列錯誤: {e}")
                
    except Exception as e:
        print(f"日誌佇列處理異常: {e}")
    finally:
        # 每100ms檢查一次
        if hasattr(self, 'root'):
            self.root.after(100, self.process_log_queue)

def add_log_to_queue(self, message):
    """線程安全的日誌添加"""
    try:
        if not self.log_queue.full():
            self.log_queue.put_nowait(message)
    except Exception:
        pass
```

### **驗證步驟3**:
1. 啟動程式，確認無語法錯誤
2. 檢查控制台是否顯示 "✅ Queue處理機制已啟動"

---

## 🔧 **步驟4: 創建策略執行緒** (90分鐘)

### **目標文件**: `Python File/OrderTester.py`

### **添加策略執行緒函數**:

```python
def start_strategy_thread(self):
    """啟動策略執行緒"""
    if self.strategy_thread and self.strategy_thread.is_alive():
        self.add_log_to_queue("⚠️ 策略執行緒已在運行中")
        return
    
    self.strategy_thread_running = True
    self.strategy_thread = threading.Thread(target=self.strategy_logic_thread, daemon=True)
    self.strategy_thread.start()
    self.add_log_to_queue("🚀 策略執行緒已啟動")

def stop_strategy_thread(self):
    """停止策略執行緒"""
    self.strategy_thread_running = False
    if self.strategy_thread:
        self.strategy_thread.join(timeout=2)
    self.add_log_to_queue("⏹️ 策略執行緒已停止")

def strategy_logic_thread(self):
    """策略運算核心執行緒"""
    self.add_log_to_queue("✅ 策略引擎執行緒已啟動，等待即時報價...")

    while self.strategy_thread_running:
        try:
            # 從策略佇列取得數據
            strategy_data = self.strategy_queue.get(timeout=1)

            # 執行策略邏輯
            price = strategy_data['price']
            time_str = strategy_data['time']
            timestamp = strategy_data['timestamp']

            # 檢查交易時間
            now = datetime.now()
            if self.is_within_trading_hours(now):
                # 更新區間高低點 (如果函數存在)
                if hasattr(self, 'update_range_high_low'):
                    self.update_range_high_low(price)

                # 檢查進出場條件 (如果函數存在)
                if hasattr(self, 'check_entry_conditions'):
                    self.check_entry_conditions(price, time_str)
                
                if hasattr(self, 'position') and self.position and hasattr(self, 'lots') and self.lots:
                    if hasattr(self, 'check_exit_conditions'):
                        timestamp_obj = datetime.strptime(time_str, "%H:%M:%S").replace(
                            year=now.year, month=now.month, day=now.day
                        )
                        self.check_exit_conditions(Decimal(str(price)), timestamp_obj)

                # 更新狀態
                status_msg = f"價格更新: {price} 時間: {time_str}"
                self.add_log_to_queue(status_msg)

        except queue.Empty:
            continue
        except Exception as e:
            error_msg = f"【錯誤】策略執行緒錯誤: {e}"
            self.add_log_to_queue(error_msg)

    self.add_log_to_queue("⏹️ 策略引擎執行緒已停止")
```

### **驗證步驟4**:
1. 啟動程式，確認無語法錯誤
2. 啟動策略監控，檢查是否有策略執行緒啟動訊息

---

## ⚠️ **緊急回滾程序**

如果任何步驟出現問題：

```bash
# 立即執行回滾
copy "OrderTester_pre_queue_backup.py" "OrderTester.py"
copy "order\future_order_pre_queue_backup.py" "order\future_order.py"
```

---

## 📊 **測試檢查清單**

### **每步驟後檢查**:
- [ ] 程式能正常啟動
- [ ] 無Python語法錯誤
- [ ] 控制台無異常訊息
- [ ] UI響應正常

### **完成後全面測試**:
- [ ] 策略監控能正常啟動/停止
- [ ] 報價數據正常顯示
- [ ] 策略日誌正常更新
- [ ] 連續運行1小時無GIL錯誤

---

**📝 注意事項**:
1. 每完成一個步驟就測試一次
2. 如有問題立即停止並回滾
3. 保持備份文件直到確認穩定
4. 記錄任何異常情況

**🎯 成功標準**: 連續運行4小時無GIL錯誤，所有功能正常
