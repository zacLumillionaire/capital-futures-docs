# PostgreSQL自動匯入功能使用指南

## 📋 功能概述

這個功能提供兩種方式將期貨K線資料自動匯入到PostgreSQL的`stock_prices`表中：
1. **GUI模式**：收集完成後自動匯入
2. **命令列模式**：一鍵收集並匯入

## 🎯 使用場景

✅ **適合正式資料收集**：收集真實交易資料並自動匯入PostgreSQL進行回測分析
✅ **自動化流程**：無需手動操作，收集完成後自動匯入
✅ **批量處理**：支援大量資料的高效匯入

## 🎯 資料格式對應

### SQLite K線資料 → PostgreSQL stock_price表

| SQLite欄位 | PostgreSQL欄位 | 說明 |
|-----------|---------------|------|
| trade_date + trade_time | trade_datetime | 交易日期時間 |
| open_price | open_price | 開盤價 |
| high_price | high_price | 最高價 |
| low_price | low_price | 最低價 |
| close_price | close_price | 收盤價 |
| - | price_change | 價格變化（暫設為0） |
| - | percentage_change | 百分比變化（忽略） |
| volume | volume | 成交量 |

## 🚀 使用方式

### 方法零：快速開始（推薦）

#### 一鍵收集今日資料
```bash
python quick_start.py
```
選擇選項1，自動收集今日MTX00 1分K線並匯入PostgreSQL

#### 直接命令列（最快）
```bash
# 收集今日資料
python collect_and_import.py --user-id E123354882 --password kkd5ysUCC --symbol MTX00 --kline-type MINUTE --start-date 20250705 --end-date 20250705
```

### 方法一：GUI模式（推薦新手）

#### 1. 準備工作
確認以下條件已滿足：
✅ **PostgreSQL資料庫已啟動**
✅ **app_setup.py和shared.py在正確路徑**
✅ **stock_prices表已建立**

#### 2. 啟動GUI並設定自動匯入
```bash
python main.py
```

#### 3. 操作步驟
1. 輸入群益證券帳號密碼並登入
2. 設定收集參數（商品代碼、日期範圍等）
3. **勾選「收集完成後自動匯入PostgreSQL」**
4. 點擊「開始收集」
5. 等待收集完成，系統會自動匯入PostgreSQL

### 方法二：命令列模式（推薦自動化）

#### 一鍵收集並匯入
```bash
# 收集MTX00今日1分K線並自動匯入
python collect_and_import.py \
    --user-id E123354882 \
    --password kkd5ysUCC \
    --symbol MTX00 \
    --kline-type MINUTE \
    --start-date 20250705 \
    --end-date 20250705

# 收集多日資料
python collect_and_import.py \
    --user-id E123354882 \
    --password kkd5ysUCC \
    --symbol MTX00 \
    --kline-type MINUTE \
    --start-date 20250701 \
    --end-date 20250705 \
    --trading-session DAY

# 只收集不匯入
python collect_and_import.py \
    --user-id E123354882 \
    --password kkd5ysUCC \
    --symbol MTX00 \
    --kline-type MINUTE \
    --start-date 20250705 \
    --end-date 20250705 \
    --no-auto-import
```

### 方法三：測試現有資料匯入

```bash
# 測試PostgreSQL連接
python test_postgres_import.py

# 匯入現有SQLite資料
python import_to_postgres.py --check-only  # 先檢查
python import_to_postgres.py               # 執行匯入
```

## 📊 匯入參數說明

| 參數 | 預設值 | 說明 |
|------|--------|------|
| --symbol | MTX00 | 商品代碼 |
| --kline-type | MINUTE | K線類型（MINUTE/DAILY/WEEKLY/MONTHLY） |
| --batch-size | 100 | 批量處理大小 |
| --check-only | False | 只檢查不匯入 |

## 🔍 匯入過程監控

### 日誌輸出說明

```
✅ PostgreSQL連線池初始化成功
📊 SQLite K線資料統計: MTX00 MINUTE: 600 筆
🚀 開始匯入 MTX00 MINUTE K線資料到PostgreSQL...
📊 已處理 1000 筆，已插入 950 筆
✅ 匯入完成！
📊 統計結果:
  - 總處理筆數: 600
  - 成功插入: 580
  - 錯誤筆數: 0
  - 重複跳過: 20
```

### 狀態說明

- **成功插入**：新增到PostgreSQL的資料筆數
- **錯誤筆數**：格式錯誤或其他問題的資料
- **重複跳過**：已存在的資料（基於trade_datetime唯一約束）

## ⚠️ 注意事項

### 1. 資料重複處理
- 使用`ON CONFLICT (trade_datetime) DO NOTHING`避免重複插入
- 相同時間的資料會被跳過

### 2. 價格變化計算
- 目前`price_change`設為0，可後續優化
- `percentage_change`忽略不處理

### 3. 時間格式轉換
- 分線資料：`2025/06/05 08:46` → `2025-06-05 08:46:00`
- 日線資料：`2025/06/05` → `2025-06-05 13:45:00`（設為收盤時間）

### 4. 錯誤處理
- 批量處理，單筆錯誤不影響整體
- 詳細錯誤記錄在日誌中
- 支援事務回滾

## 🛠️ 故障排除

### 常見問題

#### 1. PostgreSQL連接失敗
```
❌ PostgreSQL連線池初始化失敗
```
**解決方案：**
- 檢查PostgreSQL服務是否啟動
- 確認app_setup.py路徑正確
- 檢查資料庫連線設定

#### 2. 找不到stock_price表
```
❌ PostgreSQL中找不到stock_price表
```
**解決方案：**
- 確認表名正確（stock_price）
- 檢查資料庫schema
- 確認有適當權限

#### 3. SQLite資料為空
```
⚠️ SQLite資料庫中沒有K線資料
```
**解決方案：**
- 先使用主程式收集K線資料
- 檢查SQLite資料庫路徑
- 確認資料收集成功

#### 4. 匯入模組找不到
```
⚠️ 無法導入PostgreSQL模組
```
**解決方案：**
- 確認app_setup.py在專案根目錄
- 確認shared.py在專案根目錄
- 檢查Python路徑設定

## 📈 匯入後驗證

### 檢查匯入結果

```sql
-- 檢查總筆數
SELECT COUNT(*) FROM stock_price;

-- 檢查日期範圍
SELECT 
    MIN(trade_datetime) as min_time,
    MAX(trade_datetime) as max_time,
    COUNT(DISTINCT trade_datetime::date) as trading_days
FROM stock_price;

-- 檢查最新資料
SELECT * FROM stock_price 
ORDER BY trade_datetime DESC 
LIMIT 10;
```

### 資料品質檢查

```sql
-- 檢查是否有空值
SELECT 
    COUNT(*) as total,
    COUNT(open_price) as has_open,
    COUNT(close_price) as has_close,
    COUNT(volume) as has_volume
FROM stock_price;

-- 檢查價格合理性
SELECT 
    MIN(open_price) as min_price,
    MAX(high_price) as max_price,
    AVG(close_price) as avg_price
FROM stock_price;
```

## 🗂️ 資料管理功能

### 查看收集到的資料
```bash
# 查看資料摘要和詳細內容
python view_collected_data.py
```

### 管理和刪除資料
```bash
# 完整的資料管理工具
python manage_collected_data.py
```

#### 支援的操作：
1. **查看資料摘要** - 統計各類型資料筆數
2. **刪除指定商品/類型** - 刪除特定商品的資料
3. **刪除日期範圍** - 刪除指定時間範圍的資料
4. **清空所有資料** - 完全清空SQLite資料庫
5. **備份資料庫** - 建立備份檔案

#### GUI管理（在主程式中）：
```bash
python main.py
# 點擊「管理資料」按鈕
```

### 常見使用場景

#### 重新收集資料前清理
```bash
# 1. 查看現有資料
python view_collected_data.py

# 2. 清空舊資料
python manage_collected_data.py  # 選擇選項4

# 3. 重新收集
python collect_and_import.py --user-id E123354882 --password kkd5ysUCC --symbol MTX00 --start-date 20250705 --end-date 20250705
```

#### 刪除特定日期的錯誤資料
```bash
python manage_collected_data.py  # 選擇選項3，輸入日期範圍
```

## 🎯 下一步建議

1. **優化價格變化計算**：實現真實的price_change計算
2. **支援多商品匯入**：擴展到TXF00、TM0000等
3. **增量匯入**：只匯入新增的資料
4. **資料驗證**：加強資料品質檢查
5. **效能優化**：大量資料的匯入優化

## 📞 技術支援

如遇到問題，請檢查：
1. 日誌檔案：`logs/collector.log`
2. 錯誤訊息的詳細內容
3. PostgreSQL和SQLite的連接狀態
