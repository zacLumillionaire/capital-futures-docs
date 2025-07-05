# 群益期貨歷史資料收集器

## 📋 專案概述

**HistoryDataCollector** 是一個專門用來取得台灣期貨歷史資料並建立到資料庫的工具程式。

基於群益證券官方API案例程式開發，確保穩定性和相容性。

## 🎯 主要功能

- ✅ **多商品支援**：MTX00（小台指）、TXF00（台指）、TM0000（微型台指）等
- ✅ **多資料類型**：逐筆報價、五檔報價、K線資料（1分K、日K、週K、月K）
- ✅ **靈活時段選擇**：全部時段、早盤（日盤）、夜盤
- ✅ **自訂日期區間**：支援指定起始和結束日期
- ✅ **資料庫儲存**：SQLite資料庫，支援大量資料儲存
- ✅ **資料去重**：自動避免重複資料
- ✅ **批量處理**：高效能資料插入
- ✅ **詳細日誌**：完整的操作記錄和錯誤追蹤

## 🏗️ 專案結構

```
HistoryDataCollector/
├── main.py                    # 主程式入口
├── history_config.py          # 專案配置檔案
├── Config.py                  # 群益官方配置
├── LoginForm.py               # 群益登入模組
├── Quote.py                   # 群益報價模組
├── SKCOM.dll                  # 群益API元件
├── database/                  # 資料庫模組
├── collectors/                # 資料收集器模組
├── utils/                     # 工具模組
├── data/                      # 資料儲存目錄
└── logs/                      # 日誌檔案目錄
```

## 🚀 快速開始

### 1. 環境需求
- Python 3.8+
- Windows 作業系統
- 群益證券API權限
- 有效的群益證券帳號

### 2. 安裝依賴
```bash
pip install -r requirements.txt
```

### 3. 測試系統
```bash
# 執行系統測試，確認所有元件正常運作
python test_collector.py
```

### 4. 執行程式

#### GUI模式（推薦）
```bash
# 啟動圖形介面
python main.py

# 或明確指定GUI模式
python main.py --mode gui
```

#### 命令列模式
```bash
# 基本使用（使用預設設定）
python main.py --mode cli

# 指定參數
python main.py --mode cli --symbol MTX00 --kline-type MINUTE --duration 120

# 只收集特定類型資料
python main.py --mode cli --no-best5 --no-kline  # 只收集逐筆資料

# 指定日期範圍
python main.py --mode cli --start-date 20241201 --end-date 20241205
```

## 📖 使用說明

### GUI介面操作

1. **登入設定**
   - 輸入身分證字號和密碼
   - 點擊「登入」按鈕
   - 等待連線完成和商品資料準備

2. **收集設定**
   - 選擇商品代碼（MTX00、TXF00等）
   - 選擇K線類型（分線、日線、週線、月線）
   - 選擇交易時段（全部、早盤）
   - 設定日期範圍
   - 勾選要收集的資料類型

3. **開始收集**
   - 點擊「開始收集」按鈕
   - 在狀態區域查看收集進度
   - 可隨時點擊「停止收集」中斷

4. **查看統計**
   - 點擊「查看統計」查看資料庫統計資訊

### 命令列參數說明

```
--mode              執行模式 (gui/cli)
--user-id           身分證字號
--password          密碼
--symbol            商品代碼 (預設: MTX00)
--kline-type        K線類型 (MINUTE/DAILY/WEEKLY/MONTHLY)
--trading-session   交易時段 (ALL/AM_ONLY)
--start-date        開始日期 (YYYYMMDD)
--end-date          結束日期 (YYYYMMDD)
--duration          收集持續時間(秒)
--no-tick           不收集逐筆資料
--no-best5          不收集五檔資料
--no-kline          不收集K線資料
```

## ⚙️ 配置說明

### 商品代碼
- `MTX00`: 小台指期貨（預設）
- `TXF00`: 台指期貨
- `TM0000`: 微型台指期貨
- 其他期貨商品

### 交易時段
- `ALL`: 全部時段（包含夜盤）
- `AM_ONLY`: 早盤（日盤）

### K線類型
- `MINUTE`: 分線
- `DAILY`: 日線
- `WEEKLY`: 週線
- `MONTHLY`: 月線

## 📊 資料庫結構

### 逐筆資料表 (tick_data)
- 商品代碼、交易日期時間
- 買價、賣價、成交價、成交量
- 唯一約束避免重複

### 五檔資料表 (best5_data)
- 五檔買賣價量資訊
- 延伸買賣資訊

### K線資料表 (kline_data)
- 開高低收價格
- 成交量資訊
- 支援多種K線週期

## 🔧 開發說明

本專案基於群益證券官方API案例程式開發：
- 使用已驗證的登入機制
- 採用穩定的API調用方式
- 完整的錯誤處理和重試機制

## 📝 版本記錄

- v1.0.0: 初始版本，支援基礎歷史資料收集功能

## 📞 技術支援

如有問題請參考：
- 群益證券API官方文件
- 專案日誌檔案 (logs/collector.log)
