# 🎯 策略監控開發計劃

## 📋 **開發概述**

**開發階段**: 第二階段 - 策略監控系統  
**開始日期**: 2025-07-04  
**預計完成**: 5個工作天  
**狀態**: 🚀 準備開始

## 🏗️ **第一階段成果回顧**

### **✅ 已完成的基礎設施**
1. **Console模式架構** - 穩定運行，無GIL錯誤
2. **報價系統** - 支援TICK和五檔數據
3. **下單回報系統** - 完整的9種委託類型支援
4. **狀態監聽器** - 智能監控和提醒機制
5. **商品選擇功能** - 支援多商品切換
6. **風險控制** - 最低風險實施策略

### **🎯 為策略開發準備的數據**
- ✅ 實時TICK數據 (`last_price`, `last_update_time`)
- ✅ 五檔報價數據 (`best5_data`)
- ✅ 商品選擇 (`config['DEFAULT_PRODUCT']`)
- ✅ 報價狀態監控 (`monitoring_stats`)
- ✅ Console輸出控制 (`console_quote_enabled`)

## 🎯 **策略需求分析**

### **開盤區間策略規格**
```
策略名稱: 開盤區間突破策略
監控時間: 08:46-08:47 (2分鐘)
數據需求: 1分鐘K線數據
進場條件: 收盤價突破區間上軌/下軌
風險控制: 20%回撤追蹤停損
交易規模: 3口 (可配置)
```

### **技術實現要點**
1. **K線數據收集** - 從TICK數據生成1分鐘K線
2. **區間計算** - 08:46和08:47兩根K線的高低點
3. **突破檢測** - 實時監控收盤價vs區間邊界
4. **進場邏輯** - 突破確認後觸發下單
5. **風險管理** - 動態停損點計算和執行

## 🛠️ **詳細開發計劃**

### **第六天: 開盤區間策略基礎**

#### **6.1 K線數據結構設計**
```python
class KLineData:
    def __init__(self):
        self.open_price = 0.0
        self.high_price = 0.0
        self.low_price = 0.0
        self.close_price = 0.0
        self.volume = 0
        self.start_time = ""
        self.end_time = ""
        self.is_complete = False
```

#### **6.2 K線收集器實施**
**位置**: 新增 `KLineCollector` 類
```python
def collect_tick_data(self, price, volume, timestamp):
    """收集TICK數據並生成K線"""
    # 判斷是否需要開始新的K線
    # 更新當前K線數據
    # 檢查K線是否完成
```

#### **6.3 開盤區間監控**
**位置**: 新增 `OpeningRangeMonitor` 類
```python
def monitor_opening_range(self, kline_data):
    """監控開盤區間形成"""
    # 檢查時間是否在08:46-08:47
    # 收集兩根K線數據
    # 計算區間高低點
```

#### **6.4 Console輸出設計**
```
🎯 [STRATEGY] 開盤區間監控啟動
📊 [STRATEGY] 08:46 K線: 開22650 高22658 低22645 收22655
📊 [STRATEGY] 08:47 K線: 開22655 高22662 低22650 收22660
✅ [STRATEGY] 區間形成: 上軌22662 下軌22645 (區間17點)
```

### **第七天: 突破檢測與進場邏輯**

#### **7.1 突破檢測器**
```python
class BreakoutDetector:
    def check_breakout(self, current_price, range_high, range_low):
        """檢測突破信號"""
        if current_price > range_high:
            return "LONG"  # 做多信號
        elif current_price < range_low:
            return "SHORT"  # 做空信號
        return None
```

#### **7.2 進場邏輯**
```python
def process_entry_signal(self, signal_type, current_price):
    """處理進場信號"""
    if signal_type == "LONG":
        # 使用五檔數據進行FOK買ASK追價
        entry_price = self.best5_data['ask1']
        self.place_strategy_order("BUY", entry_price, 3)
    elif signal_type == "SHORT":
        # 使用五檔數據進行FOK賣BID追價
        entry_price = self.best5_data['bid1']
        self.place_strategy_order("SELL", entry_price, 3)
```

#### **7.3 策略狀態管理**
```python
class StrategyState:
    def __init__(self):
        self.status = "WAITING"  # WAITING/MONITORING/ENTERED/STOPPED
        self.entry_price = 0.0
        self.entry_time = ""
        self.position_size = 0
        self.unrealized_pnl = 0.0
```

### **第八天: 風險管理與停損邏輯**

#### **8.1 追蹤停損計算**
```python
def calculate_trailing_stop(self, entry_price, current_price, direction):
    """計算20%回撤追蹤停損"""
    if direction == "LONG":
        # 做多：從最高點回撤20%
        highest_price = max(self.highest_since_entry, current_price)
        stop_price = highest_price * 0.8
    else:
        # 做空：從最低點反彈20%
        lowest_price = min(self.lowest_since_entry, current_price)
        stop_price = lowest_price * 1.2
    return stop_price
```

#### **8.2 多筆委託保護邏輯**
```python
def update_stop_loss(self, new_stop_price):
    """更新停損邏輯 - 保護已獲利部位"""
    profitable_lots = self.get_profitable_lots()
    if len(profitable_lots) == self.total_lots:
        # 所有部位都獲利才更新停損
        self.current_stop_price = new_stop_price
        print(f"🛡️ [RISK] 停損更新至: {new_stop_price}")
```

### **第九天: 策略整合與測試**

#### **9.1 完整策略流程**
```python
def run_strategy_cycle(self, tick_data):
    """完整策略執行週期"""
    # 1. 收集K線數據
    kline = self.kline_collector.process_tick(tick_data)
    
    # 2. 監控開盤區間
    if self.is_opening_period():
        self.opening_range_monitor.update(kline)
    
    # 3. 檢測突破信號
    if self.range_formed and not self.position_entered:
        signal = self.breakout_detector.check(tick_data.price)
        if signal:
            self.process_entry_signal(signal, tick_data.price)
    
    # 4. 風險管理
    if self.position_entered:
        self.risk_manager.update_stops(tick_data.price)
```

#### **9.2 策略參數配置**
```python
STRATEGY_CONFIG = {
    "opening_start": "08:46:00",
    "opening_end": "08:47:59",
    "position_size": 3,
    "trailing_stop_ratio": 0.2,
    "max_entries_per_day": 1,
    "enable_console_output": True
}
```

### **第十天: 策略優化與文檔**

#### **10.1 交易記錄系統**
```python
def record_trade(self, trade_data):
    """記錄交易到TXT文件"""
    record = {
        "date": trade_data.date,
        "entry_time": trade_data.entry_time,
        "exit_time": trade_data.exit_time,
        "direction": trade_data.direction,
        "entry_price": trade_data.entry_price,
        "exit_price": trade_data.exit_price,
        "quantity": trade_data.quantity,
        "pnl": trade_data.pnl,
        "strategy": "OpeningRange"
    }
    self.save_trade_record(record)
```

#### **10.2 性能監控**
```python
def calculate_strategy_performance(self):
    """計算策略績效"""
    total_trades = len(self.trade_history)
    winning_trades = len([t for t in self.trade_history if t.pnl > 0])
    win_rate = winning_trades / total_trades if total_trades > 0 else 0
    
    print(f"📊 [PERFORMANCE] 總交易: {total_trades}")
    print(f"📊 [PERFORMANCE] 勝率: {win_rate:.2%}")
    print(f"📊 [PERFORMANCE] 總損益: {self.total_pnl}")
```

## 🎯 **實施優先級**

### **P0 - 核心功能 (必須)**
- K線數據收集和存儲
- 開盤區間識別和計算
- 突破信號檢測
- 基本進場邏輯

### **P1 - 風險控制 (重要)**
- 追蹤停損機制
- 多筆委託保護
- 風險參數配置
- 異常處理

### **P2 - 優化功能 (可選)**
- 策略參數調優
- 性能分析報告
- 交易記錄系統
- 策略回測功能

## 📊 **成功指標**

### **技術指標**
- [ ] K線數據準確率 > 99%
- [ ] 突破信號延遲 < 1秒
- [ ] 策略運行穩定性 > 8小時
- [ ] 記憶體使用增長 < 10%

### **業務指標**
- [ ] 區間識別準確率 100%
- [ ] 進場信號正確性 100%
- [ ] 風險控制有效性 100%
- [ ] 交易記錄完整性 100%

---

**📝 計劃建立時間**: 2025-07-04  
**🎯 開發狀態**: 準備開始第六天開發  
**💡 下一步**: 實施K線數據收集器  
**📊 計劃版本**: v1.0
