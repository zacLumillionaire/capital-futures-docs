# PostgreSQL 表格建立和測試指南

## 🎯 目標
建立 Full Tick 和五檔報價的 PostgreSQL 資料表，並測試 API 資料匯入功能。

## 📋 步驟1: 建立 PostgreSQL 資料表

### 方法1: 使用簡化版 SQL 腳本 (推薦)
```sql
-- 在你的 PostgreSQL 資料庫中執行以下腳本
-- 檔案: create_tables_simple.sql

-- 建立逐筆資料表
CREATE TABLE IF NOT EXISTS tick_prices (
    trade_datetime timestamp without time zone NOT NULL,
    symbol varchar(20) NOT NULL,
    bid_price numeric(10,2),
    ask_price numeric(10,2),
    close_price numeric(10,2) NOT NULL,
    volume integer NOT NULL,
    trade_time_ms integer DEFAULT 0,
    market_no integer DEFAULT 0,
    simulate_flag integer DEFAULT 0,
    CONSTRAINT pk_tick_prices PRIMARY KEY (trade_datetime, symbol)
);

-- 建立五檔報價資料表
CREATE TABLE IF NOT EXISTS best5_prices (
    trade_datetime timestamp without time zone NOT NULL,
    symbol varchar(20) NOT NULL,
    bid_price_1 numeric(10,2), bid_volume_1 integer DEFAULT 0,
    bid_price_2 numeric(10,2), bid_volume_2 integer DEFAULT 0,
    bid_price_3 numeric(10,2), bid_volume_3 integer DEFAULT 0,
    bid_price_4 numeric(10,2), bid_volume_4 integer DEFAULT 0,
    bid_price_5 numeric(10,2), bid_volume_5 integer DEFAULT 0,
    ask_price_1 numeric(10,2), ask_volume_1 integer DEFAULT 0,
    ask_price_2 numeric(10,2), ask_volume_2 integer DEFAULT 0,
    ask_price_3 numeric(10,2), ask_volume_3 integer DEFAULT 0,
    ask_price_4 numeric(10,2), ask_volume_4 integer DEFAULT 0,
    ask_price_5 numeric(10,2), ask_volume_5 integer DEFAULT 0,
    extend_bid numeric(10,2), extend_bid_qty integer DEFAULT 0,
    extend_ask numeric(10,2), extend_ask_qty integer DEFAULT 0,
    CONSTRAINT pk_best5_prices PRIMARY KEY (trade_datetime, symbol)
);

-- 建立索引
CREATE INDEX IF NOT EXISTS idx_tick_prices_symbol ON tick_prices(symbol);
CREATE INDEX IF NOT EXISTS idx_tick_prices_datetime ON tick_prices(trade_datetime);
CREATE INDEX IF NOT EXISTS idx_best5_prices_symbol ON best5_prices(symbol);
CREATE INDEX IF NOT EXISTS idx_best5_prices_datetime ON best5_prices(trade_datetime);
```

### 方法2: 使用完整版 SQL 腳本
```bash
# 如果你想要完整的表格、索引、視圖和註解
# 執行: create_tick_best5_tables.sql
```

### 驗證表格建立
```sql
-- 檢查表格是否建立成功
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_name IN ('tick_prices', 'best5_prices', 'stock_prices')
ORDER BY table_name;

-- 應該看到3個表格:
-- best5_prices | BASE TABLE
-- stock_prices | BASE TABLE  
-- tick_prices  | BASE TABLE
```

## 📋 步驟2: 收集 API 資料

### 使用 GUI 模式收集資料 (推薦)
```bash
cd HistoryDataCollector
python main.py --mode gui
```

**GUI 操作步驟:**
1. 輸入帳號密碼 (E123354882 / kkd5ysUCC)
2. 點擊「登入」
3. 等待連線成功
4. **重要**: 勾選「收集逐筆資料」和「收集五檔資料」
5. 設定收集時間 (建議5-10分鐘)
6. 點擊「開始收集」
7. 等待收集完成

### 使用 CLI 模式收集資料
```bash
cd HistoryDataCollector
python main.py --mode cli --symbol MTX00 --duration 10 --tick --best5
```

### 驗證資料收集
```bash
# 檢查 SQLite 中的資料
cd HistoryDataCollector
python -c "
from database.db_manager import DatabaseManager
db = DatabaseManager()
stats = db.get_data_statistics()
print(f'K線: {stats[\"kline_count\"]} 筆')
print(f'逐筆: {stats[\"tick_count\"]} 筆') 
print(f'五檔: {stats[\"best5_count\"]} 筆')
"
```

## 📋 步驟3: 測試匯入功能

### 執行自動化測試
```bash
cd HistoryDataCollector
python test_api_data_import.py
```

**測試項目:**
- ✅ PostgreSQL 表格檢查
- ✅ SQLite 資料檢查
- ✅ K線資料匯入測試
- ✅ 逐筆資料匯入測試
- ✅ 五檔資料匯入測試
- ✅ 匯入結果驗證

### 手動測試匯入功能

#### 使用 GUI 匯入
1. 啟動 GUI: `python main.py --mode gui`
2. 使用新增的匯入按鈕:
   - **匯入K線**: 匯入K線資料
   - **匯入逐筆**: 匯入逐筆資料
   - **匯入五檔**: 匯入五檔資料
   - **匯入全部**: 一鍵匯入所有資料
   - **PostgreSQL統計**: 查看匯入結果

#### 使用 Python 腳本匯入
```python
from database.postgres_importer import PostgreSQLImporter

importer = PostgreSQLImporter()

# 匯入K線資料
importer.import_kline_to_postgres('MTX00', 'MINUTE')

# 匯入逐筆資料
importer.import_tick_to_postgres('MTX00')

# 匯入五檔資料
importer.import_best5_to_postgres('MTX00')

# 匯入全部資料
importer.import_all_data_to_postgres('MTX00')

# 查看統計
stats = importer.get_postgres_data_statistics()
print(stats)
```

## 📋 步驟4: 驗證匯入結果

### 檢查 PostgreSQL 資料
```sql
-- 檢查各表格資料筆數
SELECT 'stock_prices' as table_name, COUNT(*) as count FROM stock_prices
UNION ALL
SELECT 'tick_prices' as table_name, COUNT(*) as count FROM tick_prices  
UNION ALL
SELECT 'best5_prices' as table_name, COUNT(*) as count FROM best5_prices;

-- 查看最新的逐筆資料
SELECT * FROM tick_prices 
WHERE symbol = 'MTX00' 
ORDER BY trade_datetime DESC 
LIMIT 5;

-- 查看最新的五檔資料
SELECT 
    trade_datetime, symbol,
    bid_price_1, bid_volume_1,
    ask_price_1, ask_volume_1
FROM best5_prices 
WHERE symbol = 'MTX00' 
ORDER BY trade_datetime DESC 
LIMIT 5;
```

### 檢查資料完整性
```sql
-- 檢查是否有NULL的必要欄位
SELECT COUNT(*) as null_close_price_count 
FROM tick_prices 
WHERE close_price IS NULL;

-- 檢查時間範圍
SELECT 
    MIN(trade_datetime) as earliest,
    MAX(trade_datetime) as latest,
    COUNT(*) as total_records
FROM tick_prices;
```

## 🎯 預期結果

### 成功的測試輸出
```
🎯 總體成功率: 3/3 (100.0%)
  kline 匯入: ✅ 成功
  tick 匯入: ✅ 成功  
  best5 匯入: ✅ 成功
  匯入結果檢查: ✅ 成功

🎉 所有測試通過！API資料匯入功能正常運作
```

### 成功的資料統計
```
📊 PostgreSQL匯入結果:
  - K線資料: 1,234 筆
  - 逐筆資料: 5,678 筆
  - 五檔資料: 2,345 筆
  - 總計: 9,257 筆
```

## 🔧 故障排除

### 常見問題1: PostgreSQL 表格不存在
**錯誤**: `relation "tick_prices" does not exist`
**解決**: 執行 `create_tables_simple.sql` 建立表格

### 常見問題2: SQLite 沒有資料
**錯誤**: `SQLite中沒有資料`
**解決**: 
1. 確保勾選「收集逐筆資料」和「收集五檔資料」
2. 收集時間要足夠 (建議5-10分鐘)
3. 確保在交易時間內收集

### 常見問題3: PostgreSQL 連線失敗
**錯誤**: `PostgreSQL未初始化`
**解決**: 
1. 檢查 PostgreSQL 服務是否啟動
2. 檢查連線設定
3. 確保資料庫權限正確

### 常見問題4: 匯入速度慢
**解決**: 
1. 確保啟用性能優化 (`optimize_performance=True`)
2. 調整批次大小 (`batch_size=5000`)
3. 檢查網路連線和資料庫性能

## ✅ 完成檢查清單

- [ ] PostgreSQL 表格建立完成
- [ ] API 資料收集完成 (包含逐筆和五檔)
- [ ] 匯入測試全部通過
- [ ] PostgreSQL 中有資料
- [ ] GUI 匯入按鈕正常運作
- [ ] 性能達到預期 (1000+ 筆/秒)

完成以上步驟後，你的 Full Tick 和五檔報價功能就完全可用了！🎉
