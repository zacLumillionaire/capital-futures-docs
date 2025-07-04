# 🎯 狀態監聽器實施指南

## 📋 **概述**

本指南詳細說明如何在 `simple_integrated.py` 中實施狀態監聽器系統，包括：
- 報價狀態監控
- Console輸出控制
- 預留下單/回報狀態擴展接口

## 🛠️ **實施步驟**

### **步驟1: 先實施簡單監聽器**
**目標**: 只監控報價狀態，確保基本功能正常

#### **1.1 修改 `__init__` 方法**
在現有初始化代碼後添加：

```python
# 🎯 狀態監聽器相關變數
self.monitoring_stats = {
    'last_quote_count': 0,
    'last_quote_time': None,
    'quote_status': '未知'
}

# Console輸出控制
self.console_quote_enabled = True
```

#### **1.2 修改 `create_main_page` 方法**
在現有UI創建代碼後添加狀態面板：

```python
# 在現有代碼後添加
self.create_status_display_panel(main_frame)
```

#### **1.3 新增狀態顯示面板方法**

```python
def create_status_display_panel(self, parent_frame):
    """創建狀態顯示面板 - 第一階段：只顯示報價狀態"""
    status_frame = ttk.LabelFrame(parent_frame, text="📊 系統狀態", padding=5)
    status_frame.pack(fill="x", pady=5)
    
    # 狀態顯示行
    status_row = ttk.Frame(status_frame)
    status_row.pack(fill="x", pady=2)
    
    # 報價狀態
    ttk.Label(status_row, text="報價狀態:").pack(side="left")
    self.label_quote_status = ttk.Label(status_row, text="未知", foreground="gray")
    self.label_quote_status.pack(side="left", padx=5)
    
    # Console控制按鈕
    self.btn_toggle_console = ttk.Button(status_row, text="🔇 關閉報價Console", 
                                       command=self.toggle_console_quote)
    self.btn_toggle_console.pack(side="left", padx=20)
    
    # 更新時間
    ttk.Label(status_row, text="更新:").pack(side="right", padx=(20,5))
    self.label_last_update = ttk.Label(status_row, text="--:--:--", foreground="gray")
    self.label_last_update.pack(side="right")
```

#### **1.4 實施基本監聽器**

```python
def start_status_monitor(self):
    """啟動狀態監控 - 第一階段：只監控報價"""
    def monitor_loop():
        try:
            # 檢查報價狀態
            current_count = getattr(self, 'price_count', 0)
            if current_count > self.monitoring_stats['last_quote_count']:
                self.monitoring_stats['quote_status'] = "報價中"
                self.monitoring_stats['last_quote_count'] = current_count
                quote_color = "green"
            else:
                self.monitoring_stats['quote_status'] = "報價中斷"
                quote_color = "red"
            
            # 更新UI
            self.label_quote_status.config(
                text=self.monitoring_stats['quote_status'], 
                foreground=quote_color
            )
            
            # 更新時間戳
            timestamp = time.strftime("%H:%M:%S")
            self.label_last_update.config(text=timestamp)
            
        except Exception as e:
            print(f"❌ [MONITOR] 狀態監控錯誤: {e}")
        
        # 排程下一次檢查（3秒間隔）
        self.root.after(3000, monitor_loop)
    
    # 啟動監控
    monitor_loop()

def toggle_console_quote(self):
    """切換報價Console輸出"""
    try:
        self.console_quote_enabled = not self.console_quote_enabled
        
        if self.console_quote_enabled:
            self.btn_toggle_console.config(text="🔇 關閉報價Console")
            print("✅ [CONSOLE] 報價Console輸出已啟用")
        else:
            self.btn_toggle_console.config(text="🔊 開啟報價Console")
            print("🔇 [CONSOLE] 報價Console輸出已關閉")
            
    except Exception as e:
        print(f"❌ [CONSOLE] 切換Console輸出錯誤: {e}")
```

#### **1.5 修改報價事件處理**
在 `OnNotifyTicksLONG` 方法中添加Console控制：

```python
# 在現有的Console輸出代碼前添加檢查
if getattr(self.parent, 'console_quote_enabled', True):
    print(f"[TICK] {formatted_time} 成交:{corrected_price:.0f} 買:{bid:.0f} 賣:{ask:.0f} 量:{nQty}")
```

#### **1.6 啟動監聽器**
在 `create_widgets` 方法最後添加：

```python
# 啟動狀態監聽器
self.start_status_monitor()
```

### **步驟2: 測試GIL穩定性（30分鐘）**
**目標**: 確認基本監聽器不會導致GIL錯誤

#### **測試檢查項目**
- [ ] 程序啟動正常
- [ ] 狀態面板顯示正確
- [ ] 報價狀態檢測準確
- [ ] Console控制按鈕功能正常
- [ ] 連續運行30分鐘無GIL錯誤
- [ ] 記憶體使用穩定

### **步驟3: 擴展到多狀態監控**
**目標**: 添加策略、連線狀態監控

#### **3.1 擴展狀態變數**

```python
# 擴展 monitoring_stats
self.monitoring_stats = {
    'last_quote_count': 0,
    'last_quote_time': None,
    'quote_status': '未知',
    'strategy_status': '未啟動',    # 新增
    'connection_status': '未連線'   # 新增
}
```

#### **3.2 擴展狀態面板**

```python
# 在狀態顯示行中添加更多狀態
ttk.Label(status_row, text="策略:").pack(side="left", padx=(20,0))
self.label_strategy_status = ttk.Label(status_row, text="未啟動", foreground="gray")
self.label_strategy_status.pack(side="left", padx=5)

ttk.Label(status_row, text="連線:").pack(side="left", padx=(20,0))
self.label_connection_status = ttk.Label(status_row, text="未連線", foreground="gray")
self.label_connection_status.pack(side="left", padx=5)
```

#### **3.3 擴展監聽器邏輯**

```python
# 在 monitor_loop 中添加更多檢查
# 2. 檢查策略狀態
if getattr(self, 'strategy_enabled', False):
    self.monitoring_stats['strategy_status'] = "監控中"
    strategy_color = "blue"
else:
    self.monitoring_stats['strategy_status'] = "已停止"
    strategy_color = "gray"

# 3. 檢查連線狀態
if getattr(self, 'logged_in', False):
    self.monitoring_stats['connection_status'] = "已連線"
    connection_color = "green"
else:
    self.monitoring_stats['connection_status'] = "未連線"
    connection_color = "red"

# 更新所有狀態
self.label_strategy_status.config(
    text=self.monitoring_stats['strategy_status'],
    foreground=strategy_color
)
self.label_connection_status.config(
    text=self.monitoring_stats['connection_status'],
    foreground=connection_color
)
```

### **步驟4: 預留下單/回報監聽擴展接口**
**目標**: 為未來功能擴展做準備

#### **4.1 預留狀態變數**

```python
# 在 monitoring_stats 中添加
'order_status': '無委託',      # 預留：下單狀態
'reply_status': '無回報'       # 預留：回報狀態
```

#### **4.2 預留UI元素**

```python
# 在狀態面板中添加第二行（預留）
row2 = ttk.Frame(status_frame)
row2.pack(fill="x", pady=2)

ttk.Label(row2, text="委託:").pack(side="left")
self.label_order_status = ttk.Label(row2, text="無委託", foreground="gray")
self.label_order_status.pack(side="left", padx=5)

ttk.Label(row2, text="回報:").pack(side="left", padx=(20,0))
self.label_reply_status = ttk.Label(row2, text="無回報", foreground="gray")
self.label_reply_status.pack(side="left", padx=5)
```

#### **4.3 預留接口方法**

```python
def update_order_status(self, status, details=None):
    """更新下單狀態 - 預留接口"""
    try:
        self.monitoring_stats['order_status'] = status
        if details:
            print(f"📋 [ORDER] {status}: {details}")
        
        # 未來可在此更新UI
        # if hasattr(self, 'label_order_status'):
        #     self.label_order_status.config(text=status)
        
    except Exception as e:
        print(f"❌ [ORDER] 狀態更新錯誤: {e}")

def update_reply_status(self, status, details=None):
    """更新回報狀態 - 預留接口"""
    try:
        self.monitoring_stats['reply_status'] = status
        if details:
            print(f"📨 [REPLY] {status}: {details}")
        
        # 未來可在此更新UI
        # if hasattr(self, 'label_reply_status'):
        #     self.label_reply_status.config(text=status)
        
    except Exception as e:
        print(f"❌ [REPLY] 狀態更新錯誤: {e}")
```

## 🎯 **實施優先級**

### **第一優先級（立即實施）**
1. ✅ 基本報價狀態監聽器
2. ✅ Console輸出控制按鈕
3. ✅ 30分鐘GIL穩定性測試

### **第二優先級（確認穩定後）**
1. ✅ 策略狀態監控
2. ✅ 連線狀態監控
3. ✅ 批次UI更新優化

### **第三優先級（預留擴展）**
1. ✅ 下單狀態監聽接口
2. ✅ 回報狀態監聽接口
3. ✅ 更多狀態指標

## 📊 **測試驗證**

### **基本功能測試**
- [ ] 狀態面板正確顯示
- [ ] 報價狀態檢測準確
- [ ] Console控制按鈕正常工作
- [ ] 時間戳更新正常

### **穩定性測試**
- [ ] 連續運行30分鐘無GIL錯誤
- [ ] 記憶體使用穩定
- [ ] CPU使用正常
- [ ] UI響應正常

### **擴展性測試**
- [ ] 預留接口可正常調用
- [ ] 新增狀態可正確顯示
- [ ] 批次更新無性能問題

---

**📝 文件建立時間**: 2025-07-04  
**🎯 實施狀態**: 待開始  
**💡 預期完成**: 1個工作天  
**📊 文檔版本**: v1.0
