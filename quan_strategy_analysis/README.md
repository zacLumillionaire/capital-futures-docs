# 量化策略分析實驗環境

## 🚀 環境說明

這是從 `strategy_analysis` 完整複製的批次實驗環境，專門用於進行更多的量化策略實驗和分析。

## 📁 目錄結構

```
quan_strategy_analysis/
├── batch_experiment_gui.py          # 🎯 主要的批次實驗GUI
├── batch_backtest_engine.py         # 批次回測引擎
├── parameter_matrix_generator.py    # 參數矩陣生成器
├── experiment_analyzer.py           # 實驗結果分析器
├── long_short_separation_analyzer.py # 多空分離分析器
├── multi_Profit-Funded Risk_多口.py  # 核心回測策略
├── sqlite_connection.py             # SQLite數據庫連接
├── stock_data.sqlite                # 股票數據庫
├── app_setup.py                     # 應用設置
├── shared.py                        # 共享模組
├── requirements.txt                 # Python依賴包
├── batch_result/                    # 實驗結果輸出目錄
├── charts/                          # 圖表輸出目錄
└── data/                           # 數據目錄
```

## 🎯 核心功能

### 1. 批次實驗GUI (`batch_experiment_gui.py`)
- **Web界面**：Flask應用，提供直觀的參數設置界面
- **參數配置**：支援多口數、移動停利、交易方向等設置
- **實時監控**：實驗進度追蹤和日誌顯示
- **自動報告**：實驗完成後自動生成完整報告套餐

### 2. 交易方向支援
- **只做多** (`LONG_ONLY`)：僅執行多頭交易
- **只做空** (`SHORT_ONLY`)：僅執行空頭交易  
- **多空都做** (`BOTH`)：同時執行多空交易
- **3模式都跑**：自動執行上述三種模式的實驗

### 3. 自動報告生成
實驗完成後自動生成：
- 📋 **CSV總表**：包含所有實驗結果
- 📈 **多方專用報告**：只做多策略分析
- 📉 **空方專用報告**：只做空策略分析
- 📊 **HTML報告**：包含圖表的完整分析報告

### 4. 表格分析功能
- **最高總損益前10名**：顯示交易方向欄位
- **最高多頭損益前10名**：只顯示多頭進場實驗
- **最高空頭損益前10名**：只顯示空頭進場實驗
- **最低回撤前10名**：顯示交易方向欄位
- **各時段MDD最低前三名**：顯示交易方向欄位

## 🚀 快速開始

### 1. 啟動實驗環境
```bash
cd /Users/z/big/my-capital-project/quan_strategy_analysis
python batch_experiment_gui.py
```

### 2. 訪問Web界面
打開瀏覽器訪問：`http://localhost:5000`

### 3. 設置實驗參數
- 選擇交易方向（只做多/只做空/多空都做/3模式都跑）
- 設定時間區間（預設：08:46-08:47）
- 配置各口數的觸發點和回檔百分比
- 設定實驗範圍和步長

### 4. 開始實驗
點擊「開始實驗」按鈕，系統會：
- 生成參數矩陣
- 執行批次回測
- 實時顯示進度
- 自動生成完整報告套餐

## 📊 實驗結果

### 輸出位置
所有實驗結果會保存在 `batch_result/` 目錄下，按時間戳組織：
```
batch_result/
└── complete_reports_[模式]_[時間戳]/
    ├── batch_experiment_results_[時間戳].csv
    ├── long_only_results_[時間戳].csv
    ├── short_only_results_[時間戳].csv
    ├── experiment_analysis_report_long_only_[時間戳].html
    ├── experiment_analysis_report_short_only_[時間戳].html
    ├── experiment_analysis_report_both_[時間戳].html
    └── charts/
        ├── total_pnl_distribution.png
        ├── winrate_vs_pnl.png
        ├── parameter_sensitivity.png
        ├── max_drawdown_distribution.png
        └── long_vs_short_pnl.png
```

### 數據庫
實驗結果同時保存在 `batch_experiments.db` SQLite數據庫中，支援：
- 實驗結果查詢
- 歷史數據分析
- 參數敏感度分析
- 績效統計計算

## 🔧 技術特點

### 1. 高性能設計
- SQLite本地數據庫，快速讀寫
- 多線程並行處理（支援6線程）
- 內存優化的數據處理

### 2. 完整的分析工具
- Parameter Sensitivity：皮爾遜相關係數分析
- 多空分離分析：獨立評估多空策略表現
- 圖表可視化：自動生成分析圖表

### 3. 靈活的配置
- 支援任意口數配置
- 動態時間區間設置
- 多種交易方向組合

## 🎯 使用建議

1. **小規模測試**：先用較小的參數範圍測試系統穩定性
2. **分批實驗**：大規模實驗建議分批進行，避免系統負載過重
3. **結果備份**：重要實驗結果建議及時備份
4. **參數記錄**：記錄有效的參數組合，便於後續優化

## 📝 注意事項

- 確保有足夠的磁盤空間存儲實驗結果
- 大規模實驗可能需要較長時間，建議在系統空閒時進行
- 實驗過程中避免關閉瀏覽器或終止程序
- 定期清理舊的實驗結果以節省空間

---

**準備開始更多實驗！** 🚀
