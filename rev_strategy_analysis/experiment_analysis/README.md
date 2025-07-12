# 反轉策略參數優化實驗系統

## 概述

這是一個完整的參數優化實驗系統，專為反轉策略設計，能夠系統性地測試不同的停損和停利參數組合，並生成詳細的分析報告和熱力圖。

## 系統架構

```
experiment_analysis/
├── experiment_runner.py          # 主控制器
├── parameter_optimizer.py        # 參數優化器
├── heatmap_generator.py          # 熱力圖生成器
├── simple_backtest_engine.py     # 簡化回測引擎
├── test_experiment.py            # 系統測試腳本
├── README.md                     # 使用說明
└── results/                      # 結果目錄
    ├── parameter_optimization_results_*.csv
    ├── experiment_runner.log
    ├── parameter_optimization.log
    └── heatmap_analysis/
        ├── heatmap_*.png          # 靜態熱力圖
        ├── interactive_heatmap_*.html  # 互動式熱力圖
        ├── comparison_heatmap_*.html   # 比較熱力圖
        └── heatmap_analysis_report.txt # 分析報告
```

## 實驗參數

### 停損點測試範圍
- **範圍**: 15-100 點
- **步長**: 5 點
- **測試點數**: 18 個

### 停利點測試範圍
- **範圍**: 30-100 點
- **步長**: 10 點
- **測試點數**: 8 個

### 時間區間
- **10:30~10:31**: 早盤活躍時段
- **11:30~11:31**: 中午震盪時段
- **12:30~12:31**: 午後時段

### 總實驗數量
18 × 8 × 3 = **432 個實驗組合**

## 使用方法

### 1. 快速測試（推薦開始）

```bash
# 執行 10 個實驗的快速測試
python experiment_runner.py --quick-test --sample-size 10

# 執行 50 個實驗的中等測試
python experiment_runner.py --quick-test --sample-size 50
```

### 2. 完整實驗（432 個組合）

```bash
# 執行完整的參數優化實驗
python experiment_runner.py

# 使用更多並行進程加速
python experiment_runner.py --max-workers 4

# 不生成熱力圖（僅獲得CSV結果）
python experiment_runner.py --no-heatmaps
```

### 3. 系統測試

```bash
# 測試系統基本功能
python test_experiment.py
```

## 輸出結果

### 1. CSV 結果文件
包含所有實驗的詳細數據：
- `experiment_id`: 實驗標識
- `time_interval`: 時間區間
- `stop_loss_points`: 停損點數
- `take_profit_points`: 停利點數
- `total_pnl`: 總損益
- `total_trades`: 總交易數
- `win_rate`: 勝率
- `long_pnl`: 多頭損益
- `short_pnl`: 空頭損益
- `both_profitable`: 多空都獲利

### 2. 熱力圖分析
- **靜態熱力圖** (PNG): 適合報告和打印
- **互動式熱力圖** (HTML): 支持縮放和數據查看
- **比較熱力圖**: 不同時間區間的對比分析

### 3. 分析報告
- 最佳參數組合排名
- 獲利實驗統計
- 多空都獲利分析
- 詳細的性能指標

## 配置選項

### 實驗控制器配置
```python
config = {
    'max_workers': 2,              # 並行進程數
    'timeout_per_experiment': 300,  # 單個實驗超時時間（秒）
    'retry_failed': True,          # 是否重試失敗的實驗
    'generate_heatmaps': True,     # 是否生成熱力圖
    'save_intermediate_results': True,  # 是否保存中間結果
}
```

### 回測期間
- **開始日期**: 2024-11-04
- **結束日期**: 2025-06-27
- **交易口數**: 3 口（固定）

## 性能考量

### 執行時間估算
- **快速測試** (10 個實驗): ~30 秒
- **中等測試** (50 個實驗): ~2 分鐘
- **完整實驗** (432 個實驗): ~15-20 分鐘

### 並行處理
- 預設使用 2 個並行進程
- 可通過 `--max-workers` 參數調整
- 建議不超過 CPU 核心數

### 記憶體使用
- 每個實驗約使用 10-20MB 記憶體
- 完整實驗約需 500MB-1GB 記憶體

## 結果解讀

### 最佳參數選擇標準
1. **總損益** (total_pnl): 主要評估指標
2. **多空都獲利** (both_profitable): 策略穩健性指標
3. **勝率** (win_rate): 交易成功率
4. **夏普比率** (sharpe_ratio): 風險調整後收益

### 熱力圖解讀
- **顏色深淺**: 代表性能指標的強弱
- **X軸**: 停利點數
- **Y軸**: 停損點數
- **最佳區域**: 通常在高停利、適中停損的區域

## 故障排除

### 常見問題

1. **模組導入錯誤**
   ```bash
   # 確保在正確目錄執行
   cd rev_strategy_analysis/experiment_analysis
   python experiment_runner.py --quick-test
   ```

2. **記憶體不足**
   ```bash
   # 減少並行進程數
   python experiment_runner.py --max-workers 1
   ```

3. **實驗失敗**
   ```bash
   # 檢查日誌文件
   cat results/experiment_runner.log
   cat results/parameter_optimization.log
   ```

### 日誌文件
- `results/experiment_runner.log`: 主控制器日誌
- `results/parameter_optimization.log`: 參數優化日誌

## 擴展功能

### 自定義參數範圍
修改 `parameter_optimizer.py` 中的參數範圍：
```python
self.stop_loss_range = range(15, 101, 5)    # 停損範圍
self.take_profit_range = range(30, 101, 10) # 停利範圍
```

### 添加新的評估指標
在 `simple_backtest_engine.py` 中添加新的計算邏輯。

### 自定義時間區間
修改 `parameter_optimizer.py` 中的時間區間設定：
```python
self.time_intervals = [
    ("09:00", "09:01"),  # 開盤時段
    ("13:30", "13:31"),  # 收盤時段
]
```

## 技術細節

### 模擬回測引擎
- 使用機率模型模擬不同市場場景
- 根據風險回報比調整成功概率
- 支援多種交易場景（趨勢、震盪、假突破）

### 熱力圖生成
- 使用 matplotlib 生成靜態圖表
- 使用 plotly 生成互動式圖表
- 支援多種顏色映射和數據透視

### 並行處理
- 使用 ProcessPoolExecutor 實現並行執行
- 支援進程間結果收集和錯誤處理
- 自動重試失敗的實驗

---

## 聯絡資訊

如有問題或建議，請查看日誌文件或聯絡開發團隊。
