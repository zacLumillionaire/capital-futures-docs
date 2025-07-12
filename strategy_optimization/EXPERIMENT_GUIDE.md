# 🧪 策略優化實驗指南

## 📋 概述

這個實驗套件專門用於優化 **Profit-Funded Risk 多口策略**，基於您觀察到的問題：
- 第三口通常虧損
- 做空PNL遠大於做多
- 開盤2分鐘區間大小對獲利的影響

## 🚀 快速開始

### 方法1: 執行所有實驗（推薦）
```bash
cd strategy_optimization
python experiment_controller.py
```

### 方法2: 執行單一實驗
```bash
# 區間分析
python experiment_controller.py -e range

# 方向性分析  
python experiment_controller.py -e direction

# 口數效率分析
python experiment_controller.py -e lot
```

### 方法3: 指定時間範圍
```bash
# 分析2023年的數據
python experiment_controller.py -s 2023-01-01 -e 2023-12-31

# 分析最近3個月
python experiment_controller.py -s 2023-10-01 -e 2023-12-31
```

## 📊 實驗內容詳解

### 1. 開盤區間分析 (`range_analyzer.py`)

**研究問題**: 開盤2分鐘區間大小是否影響獲利？

**分析內容**:
- 統計所有交易日的區間大小分布
- 分析區間大小與突破成功率的關係
- 測試不同區間過濾閾值 (20, 25, 30, 35, 40, 45, 50, 60, 70點)
- 生成區間大小分布圖和過濾效果比較

**預期發現**:
- 最佳區間大小範圍
- 是否需要過濾過大或過小的區間
- 區間大小與方向偏差的關係

### 2. 方向性偏差分析 (`direction_optimizer.py`)

**研究問題**: 為什麼做空PNL遠大於做多？

**分析內容**:
- 比較雙向交易 vs 純做多 vs 純做空
- 分析不同時間段的方向偏差
- 計算各方向的勝率、平均獲利、風險指標
- 研究方向偏差的穩定性

**預期發現**:
- 確認做空是否真的優於做多
- 是否應該專注於單一方向
- 方向偏差的時間特性

### 3. 口數效率分析 (`lot_efficiency_analyzer.py`)

**研究問題**: 第三口是否真的通常虧損？

**分析內容**:
- 比較1口 vs 2口 vs 3口的整體表現
- 分析每口的邊際效益
- 計算風險調整後報酬
- 評估資金使用效率

**預期發現**:
- 最佳口數配置
- 每口的獨立表現
- 是否存在邊際效益遞減

## 📈 報告輸出

### 自動生成的報告
1. **綜合實驗報告**: `reports/comprehensive_experiment_report_*.html`
2. **區間分析報告**: `reports/range_analysis_report_*.html`
3. **方向分析報告**: `reports/direction_analysis_report_*.html`
4. **口數效率報告**: `reports/lot_efficiency_report_*.html`

### 圖表輸出
- `charts/range_analysis.png` - 區間分析圖表
- `charts/direction_analysis.png` - 方向分析圖表
- `charts/lot_efficiency_analysis.png` - 口數效率圖表

### 數據輸出
- `data/processed/experiment_results_*.json` - 實驗結果JSON
- `data/processed/` - 處理後的數據文件

## 🔍 結果解讀指南

### 區間分析結果
- **平均區間大小**: 了解市場開盤波動特性
- **最佳過濾閾值**: 找出最有效的區間大小範圍
- **突破成功率**: 不同區間大小的突破效果

### 方向分析結果
- **總損益比較**: 各方向的絕對獲利
- **風險調整報酬**: 考慮風險後的真實表現
- **交易頻率**: 各方向的交易機會

### 口數分析結果
- **邊際效益**: 每增加一口的額外收益
- **夏普比率**: 風險調整後的效率
- **資金效率**: 每單位資金的報酬

## 💡 優化建議框架

基於實驗結果，可能的優化方向：

### 如果區間分析顯示：
- **小區間更有效** → 添加區間上限過濾
- **大區間更穩定** → 添加區間下限過濾
- **特定範圍最佳** → 實施區間範圍過濾

### 如果方向分析顯示：
- **做空明顯優於做多** → 考慮純做空策略
- **特定時段有偏差** → 添加時間過濾
- **偏差不穩定** → 保持雙向交易

### 如果口數分析顯示：
- **第三口確實虧損** → 改為2口策略
- **單口效率最高** → 考慮單口策略
- **邊際效益遞減** → 優化口數配置

## 🛠️ 進階使用

### 自定義實驗參數

修改各分析器的參數：

```python
# 在 range_analyzer.py 中修改測試閾值
thresholds = [15, 20, 25, 30, 35, 40, 45, 50, 55, 60]

# 在 direction_optimizer.py 中添加時間分析
time_analysis = optimizer.analyze_time_based_bias()

# 在 lot_efficiency_analyzer.py 中測試更多口數
for lot_count in [1, 2, 3, 4, 5]:
```

### 添加新的實驗

1. 創建新的分析器類別
2. 在 `experiment_controller.py` 中註冊
3. 添加到實驗流程中

### 數據導出

```python
# 導出實驗結果為CSV
import pandas as pd
import json

with open('data/processed/experiment_results_*.json', 'r') as f:
    results = json.load(f)

# 轉換為DataFrame並導出
df = pd.DataFrame(results)
df.to_csv('experiment_summary.csv', index=False)
```

## 🔄 持續優化流程

1. **執行基準實驗** → 了解當前策略表現
2. **識別問題點** → 基於實驗結果找出改進空間
3. **實施優化** → 修改策略參數
4. **驗證效果** → 重新執行實驗確認改進
5. **部署新策略** → 將優化後的配置應用到實際交易

## 📞 支援與故障排除

### 常見問題

1. **數據庫連接失敗**
   - 檢查 `shared.py` 中的數據庫配置
   - 確認數據庫服務正在運行

2. **記憶體不足**
   - 縮小分析時間範圍
   - 減少測試參數數量

3. **圖表顯示問題**
   - 安裝中文字體或使用英文標籤
   - 檢查matplotlib配置

### 日誌檢查
查看 `analysis.log` 文件了解詳細執行過程。

### 性能優化
- 使用較小的時間範圍進行初步測試
- 並行執行獨立的實驗
- 緩存中間結果避免重複計算

---

**準備好開始實驗了嗎？** 

建議從執行完整實驗套件開始：
```bash
cd strategy_optimization
python experiment_controller.py
```

這將為您提供全面的策略分析，幫助您做出數據驅動的優化決策！
