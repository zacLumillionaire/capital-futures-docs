# 期貨資料自動匯入PostgreSQL系統

## 🎯 系統概述

這個系統提供完整的期貨歷史資料收集和自動匯入PostgreSQL功能，讓您可以：

✅ **自動收集**：使用群益證券API收集期貨K線資料
✅ **自動匯入**：收集完成後自動匯入到PostgreSQL
✅ **多種模式**：支援GUI、命令列、快速腳本三種使用方式
✅ **正式資料**：適合收集真實交易資料進行回測分析
✅ **已修復**：PostgreSQL匯入功能已完全修復並測試通過（2025-07-05）

## 📁 檔案結構

```
HistoryDataCollector/
├── collect_and_import.py      # 主要工具：一鍵收集並匯入
├── quick_start.py             # 快速開始腳本
├── main.py                    # GUI主程式（已加入自動匯入選項）
├── import_to_postgres.py      # 獨立匯入工具
├── test_postgres_import.py    # 連接測試工具
├── database/
│   ├── postgres_importer.py   # PostgreSQL匯入核心模組
│   └── db_manager.py          # SQLite資料庫管理
├── PostgreSQL_Import_Guide.md # 詳細使用說明
└── AUTO_IMPORT_SYSTEM.md      # 本文件
```

## 🚀 快速開始

### 最簡單的方式：
```bash
python quick_start.py
```
選擇選項1，自動收集今日MTX00資料並匯入PostgreSQL

### 命令列方式：
```bash
python collect_and_import.py \
    --user-id E123354882 \
    --password kkd5ysUCC \
    --symbol MTX00 \
    --kline-type MINUTE \
    --start-date 20250705 \
    --end-date 20250705
```

## 🔧 系統架構

### 1. 資料收集層
- **SKCOMManager**: 群益證券API管理
- **KLineCollector**: K線資料收集器
- **DatabaseManager**: SQLite資料庫管理

### 2. 資料轉換層
- **PostgreSQLImporter**: 資料格式轉換和匯入
- 自動處理時間格式轉換
- 批量插入優化

### 3. 使用者介面層
- **GUI模式**: 視覺化操作，支援自動匯入選項
- **CLI模式**: 命令列操作，適合自動化
- **快速腳本**: 預設參數，一鍵執行

## 📊 資料流程

```
群益證券API → SQLite暫存 → 格式轉換 → PostgreSQL
     ↓              ↓           ↓           ↓
   K線資料      本地儲存    時間格式化   stock_prices表
```

### 時間格式處理
- **SQLite格式**: `2025/06/05 08:46` (trade_date欄位)
- **PostgreSQL格式**: `2025-06-05 08:46:00` (trade_datetime欄位)

### 資料對應
| SQLite欄位 | PostgreSQL欄位 | 說明 |
|-----------|---------------|------|
| trade_date | trade_datetime | 交易時間（已轉換格式） |
| open_price | open_price | 開盤價 |
| high_price | high_price | 最高價 |
| low_price | low_price | 最低價 |
| close_price | close_price | 收盤價 |
| volume | volume | 成交量 |
| - | price_change | 價格變化（設為0） |
| - | percentage_change | 百分比變化（忽略） |

## ⚙️ 配置說明

### 必要條件
1. **PostgreSQL資料庫**已啟動
2. **app_setup.py**和**shared.py**在專案根目錄
3. **stock_prices表**已建立
4. **群益證券API**環境已設定

### 預設參數
- **帳號**: E123354882
- **密碼**: kkd5ysUCC
- **商品**: MTX00 (小台指期貨)
- **K線**: MINUTE (1分K線)
- **時段**: DAY (日盤)
- **批量**: 100筆/批次

## 🔍 使用場景

### 1. 日常資料收集
```bash
# 每日收集當天資料
python quick_start.py  # 選擇選項1
```

### 2. 歷史資料補齊
```bash
# 收集指定日期範圍
python collect_and_import.py \
    --start-date 20250701 \
    --end-date 20250705 \
    --user-id E123354882 \
    --password kkd5ysUCC
```

### 3. 測試和驗證
```bash
# 測試連接
python test_postgres_import.py

# 只收集不匯入
python collect_and_import.py --no-auto-import \
    --start-date 20250705 --end-date 20250705 \
    --user-id E123354882 --password kkd5ysUCC
```

### 4. GUI操作
```bash
python main.py
# 勾選「收集完成後自動匯入PostgreSQL」
```

## 📈 效能特點

- **批量處理**: 100筆/批次，避免單筆插入效能問題
- **重複檢查**: 使用WHERE NOT EXISTS避免重複資料
- **錯誤處理**: 單筆錯誤不影響整體匯入
- **事務管理**: 支援回滾機制

## 🛠️ 故障排除

### 常見問題
1. **PostgreSQL連接失敗**: 檢查app_setup.py路徑和資料庫服務
2. **表不存在**: 確認stock_prices表已建立
3. **資料重複**: 系統自動跳過重複時間的資料
4. **API連接失敗**: 檢查群益證券API環境和帳號密碼

### 日誌檔案
- **主日誌**: `logs/collector.log`
- **匯入日誌**: `logs/collect_and_import.log`

## 🎯 下一步發展

1. **多商品支援**: 擴展到TXF00、TM0000等
2. **增量匯入**: 只匯入新增資料
3. **排程執行**: 定時自動收集
4. **監控告警**: 匯入失敗通知
5. **資料驗證**: 完整性檢查

## 💡 使用建議

1. **正式環境**: 使用命令列模式，穩定可靠
2. **測試環境**: 使用GUI模式，方便調試
3. **日常使用**: 使用quick_start.py，簡單快速
4. **批量處理**: 分批收集，避免單次資料量過大

---

**🎉 現在您可以開始收集正式的期貨資料並自動匯入PostgreSQL進行回測分析了！**
