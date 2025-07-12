# PostgreSQL 匯入性能優化指南

## 問題分析
目前1140筆資料匯入需要5分鐘，這明顯太慢了。正常情況下應該在幾秒內完成。

## 主要瓶頸分析

### 1. 資料庫層面瓶頸
- **主鍵約束檢查**: 每次INSERT都要檢查 `trade_datetime` 主鍵是否重複
- **同步提交**: PostgreSQL預設 `synchronous_commit = ON` 會等待WAL寫入磁碟
- **小批次大小**: 目前使用1000筆批次，可以增加到5000-10000
- **頻繁提交**: 每個批次都立即提交，增加I/O開銷

### 2. 應用程式層面瓶頸
- **逐筆資料轉換**: 在插入循環中進行資料轉換
- **過多日誌輸出**: 每筆資料都有詳細日誌
- **executemany效率**: 使用標準executemany而非優化版本

## 優化方案

### 方案1: 使用COPY命令 (推薦 - 最快)
```python
# 預期性能: 1140筆 < 1秒
def import_using_copy():
    # 1. 將資料寫入臨時CSV檔案
    # 2. 使用COPY命令一次性匯入
    # 3. 速度可達 50,000+ 筆/秒
```

### 方案2: 使用execute_values (次推薦)
```python
from psycopg2.extras import execute_values
# 預期性能: 1140筆 < 3秒
# 速度可達 10,000+ 筆/秒
```

### 方案3: 優化現有批量插入
```python
# 預期性能: 1140筆 < 10秒
# 1. 增加批次大小到5000
# 2. 關閉同步提交
# 3. 預先轉換所有資料
# 4. 減少日誌輸出
```

## 具體優化設定

### PostgreSQL設定優化
```sql
-- 暫時關閉同步提交 (匯入時)
SET synchronous_commit = OFF;

-- 增加工作記憶體
SET work_mem = '256MB';

-- 調整檢查點設定
SET checkpoint_segments = 32;
SET checkpoint_completion_target = 0.9;

-- 增加WAL緩衝區
SET wal_buffers = '16MB';
```

### 應用程式優化
```python
# 1. 增加批次大小
batch_size = 5000  # 從1000增加到5000

# 2. 預先轉換所有資料
converted_data = [convert_data(row) for row in all_rows]

# 3. 使用更高效的插入方法
execute_values(cursor, sql, data, page_size=1000)

# 4. 減少日誌輸出
# 只在批次完成時輸出進度，不要每筆都輸出
```

## 表格結構優化建議

### 當前表格結構分析
```sql
CREATE TABLE stock_prices (
    trade_datetime timestamp without time zone NOT NULL,
    open_price numeric(10,2),
    high_price numeric(10,2),
    low_price numeric(10,2),
    close_price numeric(10,2),
    price_change numeric(10,2),
    percentage_change numeric(8,4),
    volume bigint,
    CONSTRAINT pk_stock_prices PRIMARY KEY (trade_datetime)
);
```

### 優化建議
1. **暫時移除索引**: 匯入時移除非必要索引，匯入完成後重建
2. **考慮使用UNLOGGED表**: 如果資料可以重新匯入，可以暫時使用UNLOGGED表
3. **分區表**: 如果資料量很大，考慮按日期分區

## 實施步驟

### 立即可實施 (簡單修改)
1. 修改 `import_kline_to_postgres` 方法:
   - 增加 `batch_size=5000`
   - 添加 `SET synchronous_commit = OFF`
   - 預先轉換所有資料
   - 減少日誌輸出頻率

### 中期實施 (需要新代碼)
1. 實作 `execute_values` 版本的匯入器
2. 實作 COPY 命令版本的匯入器
3. 添加性能測試和比較功能

### 長期實施 (架構優化)
1. 考慮使用連線池優化
2. 實作並行匯入 (多執行緒)
3. 考慮使用更快的資料格式 (如Parquet)

## 預期性能提升

| 方法 | 當前時間 | 優化後時間 | 提升倍數 |
|------|----------|------------|----------|
| 當前方法 | 5分鐘 | - | - |
| 簡單優化 | 5分鐘 | 30秒 | 10倍 |
| execute_values | 5分鐘 | 3秒 | 100倍 |
| COPY命令 | 5分鐘 | 1秒 | 300倍 |

## 測試建議

1. **小批次測試**: 先用100筆資料測試各種方法
2. **性能監控**: 記錄每個步驟的耗時
3. **資料驗證**: 確保優化後資料正確性
4. **回滾計畫**: 保留原始方法作為備案

## 注意事項

1. **資料一致性**: 優化時要確保資料完整性
2. **錯誤處理**: 高速匯入時要有適當的錯誤處理
3. **記憶體使用**: 大批次可能增加記憶體使用
4. **連線管理**: 確保資料庫連線正確管理

## 監控指標

- **匯入速度**: 筆/秒
- **記憶體使用**: MB
- **CPU使用率**: %
- **磁碟I/O**: MB/s
- **網路延遲**: ms

通過這些優化，預期可以將1140筆資料的匯入時間從5分鐘縮短到1-3秒，提升100-300倍的性能。
