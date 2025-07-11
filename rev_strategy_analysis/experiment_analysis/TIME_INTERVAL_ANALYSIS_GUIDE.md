# 時間區間分析配置使用指南

## 🎯 功能概述

`time_interval_analysis` 配置是專為找出每個時間區間最小MDD配置而設計的新功能，讓您能夠在一天內運行多個最佳化策略。

### 核心特點
- **7個時間區間**: 每個區間獨立分析最佳配置
- **混合停利模式**: 同時測試固定停利和區間邊緣停利
- **智能推薦**: 自動選擇每個時間段的最佳配置
- **實用輸出**: 直接提供每日交易配置建議

## 📊 配置詳情

```
🎯 TIME_INTERVAL_ANALYSIS 配置:
   停損範圍: L1=10, L2=10, L3=10 (每口 10 個值)
   時間區間: 7 個 (10:00-10:02 到 13:00-13:02)
   預估組合數: 9,240
   說明: 220 停損組合 × 6 停利模式 (5固定+1區間) × 7 時間區間
```

### 時間區間列表
- 10:00-10:02
- 10:30-10:32  
- 11:00-11:02
- 11:30-11:32
- 12:00-12:02
- 12:30-12:32
- 13:00-13:02

### 停利模式
1. **固定停利**: 40, 50, 60, 70, 80 點 (5種)
2. **區間邊緣停利**: 動態區間邊緣 (1種)

## 🚀 使用方法

### 1. 快速測試 (14 個樣本)
```bash
python enhanced_mdd_optimizer.py --config time_interval_analysis --sample-size 14 --max-workers 2
```

### 2. 中等規模測試 (100 個樣本)
```bash
python enhanced_mdd_optimizer.py --config time_interval_analysis --sample-size 100 --max-workers 4
```

### 3. 完整分析 (9,240 組合)
```bash
python enhanced_mdd_optimizer.py --config time_interval_analysis --max-workers 4
```

### 4. 查看配置摘要
```bash
python enhanced_mdd_optimizer.py --show-configs
```

## 📈 結果分析

### 標準MDD分析
系統會先顯示標準的MDD最小和風險調整收益排名：

```
🏆 MDD最小 TOP 10:
10. MDD: -572.00 | 總P&L: 1837.00 | L1SL:15 L2SL:15 L3SL:65 | TP:70 | 11:30-11:32
 9. MDD: -661.00 | 總P&L: 2987.00 | L1SL:20 L2SL:55 L3SL:60 | 區間邊緣停利 | 11:30-11:32
```

### 時間區間專門分析
接著會顯示每個時間區間的詳細分析：

```
🕙 10:30-10:32 最佳配置:
   固定停利: MDD: -738.00 | P&L: 2669.00 | L1SL:20 L2SL:20 L3SL:50 | TP:80
   區間邊緣: MDD:-1058.00 | P&L: 2547.00 | L1SL:20 L2SL:45 L3SL:70 | 區間邊緣停利
   ⭐ 推薦: 固定停利 (MDD更小: -738.00 vs -1058.00)
```

### 每日交易配置建議
最後提供實用的每日配置建議：

```
📋 一日交易配置建議:
10:00-10:02: 固定停利 TP:40, L1SL:20 L2SL:25 L3SL:55 (MDD:-1215.00, P&L:1560.00)
10:30-10:32: 固定停利 TP:80, L1SL:20 L2SL:20 L3SL:50 (MDD:-738.00, P&L:2669.00)
11:30-11:32: 固定停利 TP:70, L1SL:15 L2SL:15 L3SL:65 (MDD:-572.00, P&L:1837.00)

📈 預期每日總計: MDD:-6164.00 | P&L: 7937.00
```

## 🎯 推薦邏輯

系統會為每個時間區間自動選擇最佳配置：

1. **比較兩種模式**: 固定停利 vs 區間邊緣停利
2. **MDD優先**: 選擇MDD更小(風險更低)的配置
3. **智能標註**: 
   - "MDD更小" - 當兩種模式都有結果時
   - "唯一選項" - 當只有一種模式有結果時

## 📁 結果文件

結果保存在：
```
results/enhanced_mdd_results_time_interval_analysis_YYYYMMDD_HHMMSS.csv
```

包含欄位：
- `experiment_id`: 實驗標識
- `time_interval`: 時間區間
- `lot1_stop_loss`, `lot2_stop_loss`, `lot3_stop_loss`: 各口停損
- `take_profit` 或 `take_profit_mode`: 停利設定
- `mdd`: 最大回撤
- `total_pnl`: 總損益
- `risk_adjusted_return`: 風險調整收益

## 💡 實際應用

### 多策略並行
使用分析結果，您可以：
1. **同時運行多個策略**: 每個時間段使用不同的最佳配置
2. **風險分散**: 不同時間段使用不同的停損停利設定
3. **收益最大化**: 每個時段都使用該時段的最佳配置

### 配置範例
根據分析結果設定GUI：
```
10:00-10:02 時段:
- 第1口: 停損20點, 停利40點
- 第2口: 停損25點, 停利40點  
- 第3口: 停損55點, 停利40點

10:30-10:32 時段:
- 第1口: 停損20點, 停利80點
- 第2口: 停損20點, 停利80點
- 第3口: 停損50點, 停利80點
```

## ⚠️ 注意事項

1. **樣本大小**: 建議先用小樣本測試，確認功能正常
2. **執行時間**: 完整9,240組合需要較長時間
3. **結果解讀**: 注意區分固定停利和區間邊緣停利的差異
4. **實際應用**: 建議結合實際市場情況調整配置

## 🔄 與其他配置比較

| 配置 | 組合數 | 特點 | 適用場景 |
|------|--------|------|----------|
| `user_custom` | 35,000 | 統一停利優化 | 單一策略優化 |
| `range_boundary` | 7,000 | 區間邊緣停利 | 原策略驗證 |
| `time_interval_analysis` | 9,240 | 時間區間分析 | 多策略並行 |

## 🎊 總結

`time_interval_analysis` 配置是為實現"一天跑多次策略"目標而設計的專門工具，通過智能分析每個時間區間的最佳配置，讓您能夠最大化每日交易收益並最小化風險。
