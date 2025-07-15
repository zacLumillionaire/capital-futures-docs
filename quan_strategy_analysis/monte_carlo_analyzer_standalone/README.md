# 蒙地卡羅策略穩健性分析器 - 獨立版本

這是一個獨立的蒙地卡羅分析工具，可以獨立運行而不影響其他系統功能。

## 📁 文件說明

- `monte_carlo_analyzer.py` - 主要分析程式
- `monte_carlo_functions.py` - 蒙地卡羅模擬函式庫
- `multi_Profit-Funded Risk_多口.py` - 回測引擎
- `sqlite_connection.py` - 資料庫連接模組
- `shared.py` - 共用函式
- `stock_data.sqlite` - 股票數據資料庫

## 🚀 使用方法

### 1. 直接執行分析
```bash
cd monte_carlo_analyzer_standalone
python monte_carlo_analyzer.py
```

### 2. 修改策略參數
編輯 `monte_carlo_analyzer.py` 中的策略配置：

```python
# 在 main() 函數中修改以下參數：

# 策略參數
strategy_config = {
    'lot1': {
        'trailing_activation': Decimal('15'),  # 第1口觸發點
        'trailing_percentage': Decimal('10')   # 第1口回檔百分比
    },
    'lot2': {
        'trailing_activation': Decimal('35'),  # 第2口觸發點
        'trailing_percentage': Decimal('10'),  # 第2口回檔百分比
        'protection_multiplier': Decimal('2')  # 保護性停損倍數
    },
    'lot3': {
        'trailing_activation': Decimal('45'),  # 第3口觸發點
        'trailing_percentage': Decimal('20'),  # 第3口回檔百分比
        'protection_multiplier': Decimal('2')  # 保護性停損倍數
    }
}

# 時間參數
backtest_config = {
    'start_date': "2024-11-04",
    'end_date': "2025-06-28",
    'range_start_time': "11:00",  # 開盤區間開始時間
    'range_end_time': "11:02"     # 開盤區間結束時間
}

# 蒙地卡羅模擬參數
num_simulations = 2000  # 模擬次數
```

## 📊 輸出結果

分析完成後會在當前目錄下創建：
- `monte_carlo_analyzer/analysis_YYYYMMDD_HHMMSS/` 資料夾
- 包含視覺化圖表和分析摘要

## 🔧 自定義分析

您可以修改以下參數來進行不同的分析：

1. **策略參數調整**：修改觸發點、回檔百分比等
2. **時間區間調整**：修改回測時間範圍和開盤區間
3. **模擬次數調整**：增加或減少蒙地卡羅模擬次數
4. **風險參數調整**：修改保護性停損倍數等

## ⚠️ 注意事項

- 此版本完全獨立，不會影響其他系統功能
- 確保 `stock_data.sqlite` 包含所需的歷史數據
- 建議在修改參數前備份原始文件
- 大量模擬可能需要較長時間，請耐心等待

## 📈 分析結果解讀

蒙地卡羅分析會提供：
- 策略在不同交易順序下的表現分布
- 最大回撤的可能範圍
- 策略穩健性評估
- 風險評估指標

這些結果可以幫助您：
- 評估策略的穩健性
- 了解潛在風險
- 優化策略參數
- 制定風險管理策略
