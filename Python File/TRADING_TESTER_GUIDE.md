# 🎯 完整交易測試系統使用指南

## 📋 **系統概覽**

本系統包含兩個核心程式，實現完整的期貨交易策略測試：

### 🔧 **雙程式架構**
1. **OrderTester.py** - 群益API管理器 + TCP價格伺服器
2. **test_ui_improvements.py** - 策略執行器 + 建倉機制

### ✅ **最新功能 (2025-07-01)**
1. **開盤區間突破策略** - 8:46-8:47區間計算，第一次突破建倉
2. **手動設定區間時間** - 可設定任意2分鐘時段進行測試
3. **一天一次進場機制** - 第一根突破K線觸發，當天不再進場
4. **多口分開建倉** - 支援1-4口，每口單獨下單和管理
5. **TCP價格傳輸** - 簡化架構，解決GIL錯誤和多重連接問題
6. **三種報價模式** - 模擬/橋接/TCP，可自由切換
7. **完整日誌系統** - 15行日誌面板，詳細記錄所有事件
8. **動態時間顯示** - 區間面板顯示當前時間

### 🏷️ **版本標記**
```
🏷️ TRADING_SYSTEM_2025_07_01_UPDATED
✅ 開盤區間突破策略
✅ 手動設定區間時間功能
✅ 第一次突破建倉機制
✅ 簡化TCP價格傳輸系統
✅ 多口分開建倉管理
✅ 一天一次進場控制
✅ TCP連接問題修復
```

## 🚀 **啟動方式**

### **標準啟動流程 (推薦)**
```bash
# 步驟1: 啟動API管理器
cd "Python File"
python OrderTester.py

# 步驟2: 登入群益API
# 在OrderTester界面中輸入帳號密碼並登入
# 勾選「☑️ 啟用TCP價格伺服器」

# 步驟3: 啟動策略系統
python test_ui_improvements.py

# 步驟4: 選擇報價模式
# 點擊「🚀 TCP模式」(推薦) 或 「🌉 橋接模式」
```

### **快速測試模式**
```bash
# 僅啟動策略系統進行模擬測試
python test_ui_improvements.py
# 使用「🎮 模擬報價」模式
```

### **檔案說明**
- 🎯 **OrderTester.py** - 群益API管理器 + TCP價格伺服器
- 🎯 **test_ui_improvements.py** - 策略執行器 + 建倉機制
- 📋 **tcp_price_server.py** - TCP價格傳輸模組
- 📋 **price_bridge.py** - 檔案橋接模組 (備用)

## 🎮 **界面說明**

### **OrderTester.py 界面**
```
群益證券API期貨下單測試程式

┌─ 登入資訊 ─────────────────────────────┐
│ 登入帳號: [E123354882] 密碼: [****]      │
│ [登入] [登出] 狀態: 已登入               │
└─────────────────────────────────────┘

┌─ TCP價格伺服器 (新功能) ──────────────────┐
│ ☑️ 啟用TCP價格伺服器                     │
│ 伺服器狀態: 運行中  連接數: 1             │
│ 📡 啟用後可讓策略程式透過TCP接收即時報價    │
└─────────────────────────────────────┘

┌─ 期貨下單 ─────────────────────────────┐
│ 商品代碼: [MTX00] 買賣別: [買進]         │
│ 委託價格: [22000] 委託量: [1]           │
│ [下單] [查詢部位] [查詢委託]             │
└─────────────────────────────────────┘
```

### **test_ui_improvements.py 界面**
```
🎯 完整交易測試系統 - UI改進版

┌─ 🎯 開盤區間突破策略 - 實盤建倉版 ──────────┐
│ 策略配置                                  │
│ 區間模式: [正常交易模式▼] 交易口數: [3口▼] │
│ 測試開始時間: [14:30] [應用]              │
│ 策略狀態: � 未啟動                       │
│                                          │
│ 開盤區間監控                              │
│ 當前時間: 14:28:35  | 目標區間: 08:46-08:47│
│ 區間高點: --       | 當前價格: 22000      │
│ 區間低點: --       | 區間狀態: 等待8:46-8:47│
│                                          │
│ 部位狀態                                  │
│ 持倉方向: 無部位  | 活躍口數: 0           │
│ 進場價格: --     | 已實現損益: 0          │
│                                          │
│ [� 啟動策略] [⏹️ 停止策略] [🔄 重置狀態]   │
└─────────────────────────────────────┘

┌─ 🎮 報價控制 ─────────────────────────┐
│ 報價模式: 模擬報價  當前價格: 22000        │
│ [🎮 模擬報價] [🌉 橋接模式] [🚀 TCP模式]   │
│ [▶️ 開始模擬] [⏹️ 停止模擬]              │
└─────────────────────────────────────┘

┌─ � 系統日誌 ─────────────────────────┐
│ [07:56:30] 🎉 完整交易測試系統已啟動       │
│ [07:56:30] ✅ 日誌系統已就緒              │
│ [07:56:35] 🚀 策略已啟動 - 等待開盤區間形成 │
│ [08:47:59] 📊 開盤區間計算完成: 21998-22010│
│ [08:51:00] 🔥 第一次突破！51分K線收盤價突破上緣│
│ [08:51:03] 🎯 執行進場! 方向: LONG, 進場價: 22014│
│ [08:51:03] 📋 [模擬建倉] 第1口 LONG MTX00 @ 22014│
│ [08:51:03] 📋 [模擬建倉] 第2口 LONG MTX00 @ 22014│
│ [08:51:03] � [模擬建倉] 第3口 LONG MTX00 @ 22014│
│ [08:51:03] ✅ 建倉完成 - LONG 3口 @ 22014  │
│ [08:51:03] ✅ 當天進場已完成，後續只執行停利/停損│
│ [🗑️ 清除日誌]                           │
└─────────────────────────────────────┘
```

## 🎯 **完整使用流程**

### **步驟1: 啟動OrderTester (API管理器)**
1. 運行 `python OrderTester.py`
2. 輸入群益帳號密碼並點擊「登入」
3. 等待登入成功，狀態顯示「已登入」
4. 勾選「☑️ 啟用TCP價格伺服器」
5. 確認狀態顯示「運行中」

### **步驟2: 啟動策略系統**
1. 運行 `python test_ui_improvements.py`
2. 檢查模組載入狀態：
   - ✅ TCP價格客戶端模組載入成功
   - ✅ 實盤交易管理器初始化

### **步驟3: 選擇報價模式**
#### **🚀 TCP模式 (推薦)**
1. 點擊「🚀 TCP模式」按鈕
2. 觀察狀態變成「TCP已連接」
3. 系統自動接收OrderTester的即時報價

#### **🌉 橋接模式 (備用)**
1. 點擊「🌉 橋接模式」按鈕
2. 觀察狀態變成「橋接監控中」
3. 系統透過檔案接收報價

#### **🎮 模擬模式 (測試)**
1. 點擊「🎮 模擬報價」按鈕
2. 點擊「▶️ 開始模擬」
3. 系統產生隨機價格變動

### **步驟4: 配置策略參數**
1. 選擇「區間模式」：
   - **正常交易模式** - 使用8:46-8:47區間
   - **測試模式** - 手動設定任意2分鐘區間
2. 如選擇測試模式：
   - 輸入開始時間 (如14:30)
   - 點擊「應用」按鈕
3. 選擇「交易口數」(1-4口)
4. 確認策略狀態為「🔴 未啟動」

### **步驟5: 啟動策略**
1. 點擊「🚀 啟動策略」按鈕
2. 確認策略狀態變成「🟢 策略運行中」
3. 觀察日誌顯示「策略已啟動 - 等待開盤區間形成」

### **步驟6: 等待開盤區間計算**
1. **正常模式**: 等待8:46-8:47時間到達
2. **測試模式**: 等待設定的時間區間到達 (如14:30-14:31)
3. 觀察日誌顯示「📊 開盤區間計算完成: XXXX-XXXX」
4. 區間狀態變成「✅ 區間已確定」
5. 區間高點/低點顯示具體數值

### **步驟7: 等待突破信號**
1. 8:48後系統自動監控一分K收盤價
2. 等待第一次突破信號
3. 觀察日誌顯示「� 第一次突破！XX分K線收盤價突破上緣」
4. 系統進入「⏳ 等待下一個報價進場」狀態

### **步驟8: 自動建倉執行**
1. 下一個報價到達時自動觸發建倉
2. 觀察日誌顯示「🎯 執行進場! 方向: LONG/SHORT」
3. 系統分開執行3筆建倉單
4. 觀察「✅ 建倉完成」和「當天進場已完成」訊息

### **步驟9: 監控部位管理**
1. 觀察部位狀態更新：
   - 持倉方向：📈 多頭 / 📉 空頭
   - 進場價格：實際建倉價格
   - 活躍口數：未出場的口數
   - 已實現損益：已出場口單的損益
2. 系統自動執行移動停利和保護性停損

## 📊 **策略邏輯詳解**

### **開盤區間突破策略**

#### **階段1: 區間計算 (8:46-8:47)**
```
時間範圍: 8:46:00 - 8:47:59
收集數據: 所有tick價格
計算方式:
- 區間高點 = max(8:46所有價格, 8:47所有價格)
- 區間低點 = min(8:46所有價格, 8:47所有價格)
結果示例: 區間 21998 - 22010 (12點區間)
```

#### **階段2: 突破監控 (8:48後)**
```
監控對象: 每分鐘K線收盤價
檢查時機: 分鐘變化時 (如8:49:XX → 8:50:XX)
突破條件:
- 多頭信號: 收盤價 > 區間高點
- 空頭信號: 收盤價 < 區間低點
重要限制: 只有第一次突破才觸發 (一天一次進場)
```

#### **階段3: 建倉執行**
```
觸發時機: 第一次突破確認後的下一個報價
建倉方式: 分開下單 (每口單獨執行)
口數配置: 1-4口可選
下單類型: 模擬下單 (可切換真實下單)
```

#### **階段4: 部位管理**
```
移動停利: 每口單獨管理
- 第1口: 15點啟動, 20%回檔
- 第2口: 40點啟動, 20%回檔, 2倍保護
- 第3口: 65點啟動, 20%回檔, 2倍保護

保護性停損: 基於前序獲利動態調整
初始停損: 區間邊緣 (突破點的反向邊緣)
```

## 📊 **日誌輸出示例**

### **完整交易流程日誌**
```
[08:45:30] 🎉 完整交易測試系統已啟動
[08:45:30] ✅ 日誌系統已就緒
[08:45:35] 🚀 策略已啟動 - 等待開盤區間形成
[08:46:15] 📊 8:46分價格收集中: 22005
[08:47:30] 📊 8:47分價格收集中: 22008
[08:47:59] 📊 開盤區間計算完成: 21998 - 22010
[08:48:30] 📊 48分收盤價未突破: 22007 (區間: 21998-22010)
[08:49:30] 📊 49分收盤價未突破: 22009 (區間: 21998-22010)
[08:50:59] 🔥 第一次突破！50分K線收盤價突破上緣!
[08:50:59]    收盤價: 22013, 區間上緣: 22010
[08:50:59] ⏳ 等待下一個報價進場做多...
[08:51:03] 🎯 執行進場! 方向: LONG, 進場價: 22014
[08:51:03] 🎯 開始分開建倉 - LONG 3口
[08:51:03] 📋 [模擬建倉] 第1口 LONG MTX00 @ 22014 (ID: SIM_LONG_1_085103)
[08:51:03] 📋 [模擬建倉] 第2口 LONG MTX00 @ 22014 (ID: SIM_LONG_2_085103)
[08:51:03] 📋 [模擬建倉] 第3口 LONG MTX00 @ 22014 (ID: SIM_LONG_3_085103)
[08:51:03] ✅ 建倉完成 - LONG 3口 @ 22014
[08:51:03] ✅ 當天進場已完成，後續只執行停利/停損機制
[08:52:15] � 第1口移動停利啟動 | 時間: 08:52:15
[08:53:20] ✅ 第1口移動停利 | 出場價: 22032, 損益: +18
[08:53:20] 🛡️ 第2口保護性停損更新: 22020 (基於累積獲利 18)
```

## 🧪 **手動設定區間時間使用方法**

### **測試模式設定**
1. **選擇測試模式**：
   - 在「區間模式」下拉選單選擇「測試模式」
   - 系統啟用時間設定功能

2. **設定測試時間**：
   - 在「測試開始時間」輸入框輸入時間 (格式: HH:MM)
   - 例如：14:30 (代表14:30-14:31區間)
   - 點擊「應用」按鈕

3. **確認設定**：
   - 觀察「目標區間」顯示更新
   - 觀察「區間狀態」顯示更新

4. **啟動策略**：
   - 點擊「🚀 啟動策略」
   - 系統開始監控設定的時間區間

### **測試模式優勢**
- ✅ **隨時測試** - 不用等到8:46才能測試策略
- ✅ **靈活調試** - 可設定任意時間進行調試
- ✅ **快速驗證** - 可在幾分鐘內完成完整測試流程
- ✅ **完全相容** - 所有策略邏輯與正常模式完全相同

## 🔧 **功能特色**

### **🚀 TCP價格傳輸 (簡化架構)**
- ✅ **解決檔案鎖定問題** - 徹底解決WinError 32
- ✅ **修復GIL錯誤** - 簡化線程架構，避免GIL衝突
- ✅ **單一連接保證** - 修復多重連接問題
- ✅ **支援每tick傳輸** - 延遲 < 1ms，高接收率
- ✅ **詳細診斷日誌** - 完整的連接過程記錄
- ✅ **重複點擊防護** - 避免用戶操作錯誤

### **🎯 開盤區間突破策略**
- ✅ **精確區間計算** - 8:46-8:47兩分鐘完整數據
- ✅ **手動設定區間時間** - 可設定任意2分鐘時段測試
- ✅ **第一次突破檢測** - 只有第一根突破K線觸發
- ✅ **一天一次進場** - 進場後不再監控新機會
- ✅ **分開建倉機制** - 每口單獨下單和管理
- ✅ **完整部位管理** - 移動停利 + 保護性停損

### **🎮 三種報價模式**
- ✅ **🎮 模擬報價** - 內建隨機價格變動，適合測試
- ✅ **🌉 橋接模式** - 檔案共享方式，向後相容
- ✅ **🚀 TCP模式** - 直接TCP連接，推薦使用

### **📋 完整日誌系統**
- ✅ **15行日誌面板** - 即時顯示策略執行狀態
- ✅ **時間戳記錄** - 精確到秒的事件記錄
- ✅ **自動滾動** - 自動滾動到最新訊息
- ✅ **清除功能** - 一鍵清除日誌
- ✅ **詳細事件** - 從區間計算到建倉完成全記錄

### **🛡️ 安全特性**
- ✅ **模擬建倉** - 預設模擬模式，不會真實下單
- ✅ **漸進式測試** - 可選擇不同報價模式測試
- ✅ **完整狀態控制** - 隨時啟動/停止/重置
- ✅ **錯誤處理** - 完整的異常處理和恢復機制
- ✅ **向後相容** - 保留所有原有功能

## 🚨 **注意事項**

### **🔧 系統需求**
- ✅ **Python 3.7+** - 基本運行環境
- ✅ **tkinter** - GUI界面 (通常內建)
- ✅ **群益API** - 實盤交易功能
- ✅ **OrderTester.py** - API管理器

### **⚠️ 使用注意**
- ⚠️ **模擬建倉** - 預設為模擬模式，不會真實下單
- ⚠️ **TCP連接** - 需要OrderTester啟動TCP伺服器
- ⚠️ **時間設定** - 策略基於8:46-8:47區間，注意時間
- ⚠️ **一天一次** - 策略設計為一天只進場一次

### **🛡️ 安全建議**
- � **先測試後實盤** - 使用模擬模式驗證策略
- � **小口數測試** - 實盤測試建議1口開始
- � **監控日誌** - 密切關注系統日誌訊息
- 🔒 **備用方案** - 保留橋接模式作為備用

## � **故障排除**

### **常見問題**

#### **TCP連接問題**
```
問題: TCP客戶端連接失敗或多重連接
解決:
1. 確認OrderTester已啟動並登入
2. 確認勾選「☑️ 啟用TCP價格伺服器」
3. 檢查防火牆設定 (localhost:8888)
4. 避免重複點擊TCP模式按鈕
5. 如出現多重連接，重啟兩個程式
```

#### **檔案鎖定問題**
```
問題: WinError 32 檔案正由另一個程序使用
解決:
1. 切換到TCP模式
2. 或重啟兩個程式
3. 檢查是否有多個程式同時運行
```

#### **策略不觸發**
```
問題: 策略啟動但不執行建倉
解決:
1. 檢查當前時間是否在8:46後
2. 確認區間是否已計算完成
3. 檢查是否已經進場過 (一天一次限制)
4. 觀察日誌中的突破檢測訊息
```

### **🔍 調試技巧**
1. **觀察日誌面板** - 所有事件都有詳細記錄
2. **檢查狀態顯示** - 區間狀態、連接狀態、策略狀態
3. **使用模擬模式** - 先用模擬報價測試邏輯
4. **分步驟測試** - 先測試連接，再測試策略

## 📈 **效能優化**

### **TCP模式優勢**
- ⚡ **延遲 < 1ms** - 比檔案橋接快20倍
- ⚡ **100%接收率** - 無檔案鎖定問題
- ⚡ **支援高頻** - 可處理每tick更新
- ⚡ **多客戶端** - 支援多個策略同時運行

### **建議配置**
- 🎯 **推薦模式**: TCP模式 (最穩定)
- 🎯 **備用模式**: 橋接模式 (相容性)
- 🎯 **測試模式**: 模擬模式 (開發測試)

## 📞 **技術支援**

### **檢查清單**
1. ✅ **模組載入** - 啟動時檢查載入訊息
2. ✅ **API狀態** - OrderTester登入狀態
3. ✅ **TCP狀態** - 伺服器和客戶端連接狀態
4. ✅ **策略狀態** - 區間計算和突破檢測狀態

### **日誌分析**
- 🔍 **系統啟動** - 檢查模組載入是否成功
- 🔍 **連接建立** - 檢查TCP連接是否正常
- 🔍 **區間計算** - 檢查8:46-8:47數據收集
- 🔍 **突破檢測** - 檢查收盤價突破邏輯
- � **建倉執行** - 檢查分開建倉是否成功

---

🎯 **完整交易測試系統 - 開盤區間突破策略**
✅ 雙程式架構：OrderTester.py + test_ui_improvements.py
🚀 TCP價格傳輸 + 第一次突破建倉 + 一天一次進場
📊 從區間計算到建倉完成的完整自動化交易系統

*使用指南版本: 2025-07-01*
*適用程式: OrderTester.py + test_ui_improvements.py*
