# 區間邊緣停利 MDD 優化指南

## 概述

區間邊緣停利配置是 MDD 優化器的新功能，允許測試策略原設計的區間邊緣停利機制，而不是固定點數停利。

## 功能特點

### 🎯 區間邊緣停利 vs 固定點停利

| 特性 | 區間邊緣停利 | 固定點停利 |
|------|-------------|-----------|
| **停利機制** | 動態區間邊緣 (range_high/range_low) | 固定點數 (如 40, 50, 60 點) |
| **參數數量** | 僅停損參數 | 停損 + 停利參數 |
| **組合數量** | 7,000 組合 | 35,000 組合 |
| **策略一致性** | 與原策略設計一致 | 優化後的固定停利 |

### 📊 配置詳情

```
🎯 RANGE_BOUNDARY 配置:
   停損範圍: L1=10, L2=10, L3=10 (每口 10 個值)
   時間區間: 7 個 (10:00-10:02 到 13:00-13:02)
   預估組合數: 7,000 (區間邊緣停利)
```

## 使用方法

### 1. 快速測試 (5 個樣本)
```bash
python enhanced_mdd_optimizer.py --config range_boundary --sample-size 5 --max-workers 2
```

### 2. 中等規模測試 (100 個樣本)
```bash
python enhanced_mdd_optimizer.py --config range_boundary --sample-size 100 --max-workers 4
```

### 3. 完整優化 (7,000 組合)
```bash
python enhanced_mdd_optimizer.py --config range_boundary --max-workers 4
```

### 4. 查看所有配置
```bash
python enhanced_mdd_optimizer.py --show-configs
```

## 結果分析

### 範例輸出
```
🏆 MDD最小 TOP 10:
 5. MDD: -643.00 | 總P&L: 2532.00 | L1SL:15 L2SL:15 L3SL:65 | 區間邊緣停利 | 10:30-10:32
 4. MDD:-1227.00 | 總P&L: -387.00 | L1SL:25 L2SL:50 L3SL:60 | 區間邊緣停利 | 11:00-11:02

💎 風險調整收益 TOP 10:
 5. 風險調整收益:  3.94 | MDD: -643.00 | 總P&L: 2532.00 | L1SL:15 L2SL:15 L3SL:65 | 區間邊緣停利
```

### 結果文件
- 文件位置: `results/enhanced_mdd_results_range_boundary_YYYYMMDD_HHMMSS.csv`
- 包含欄位: `experiment_id`, `time_interval`, `lot1_stop_loss`, `lot2_stop_loss`, `lot3_stop_loss`, `mdd`, `total_pnl`, `risk_adjusted_return`, `take_profit_mode`

## 比較分析建議

### 1. 與固定停利比較
```bash
# 先跑固定停利 (user_custom)
python enhanced_mdd_optimizer.py --config user_custom --sample-size 100

# 再跑區間邊緣停利
python enhanced_mdd_optimizer.py --config range_boundary --sample-size 100
```

### 2. 分析重點
- **MDD 最小值**: 哪種方式風險更低？
- **風險調整收益**: 哪種方式效率更高？
- **總收益**: 哪種方式獲利更多？
- **策略一致性**: 區間邊緣是否更符合原策略設計？

## 技術實現

### 配置差異
```python
# 區間邊緣停利配置
{
    'take_profit_mode': 'range_boundary',  # 關鍵標識
    'individual_take_profit_enabled': False,  # 關閉個別停利
    'lot_settings': {
        'lot1': {'trigger': 15, 'trailing': 0},  # 無 take_profit 參數
        'lot2': {'trigger': 15, 'trailing': 0},
        'lot3': {'trigger': 65, 'trailing': 0}
    }
}
```

### 策略行為
- **LONG 位置**: 在 `range_high` 停利
- **SHORT 位置**: 在 `range_low` 停利
- **停損**: 使用 GUI 設定的固定停損點
- **無移動停損**: 每口獨立運作

## 預期效果

### 優勢
1. **策略一致性**: 與原策略設計完全一致
2. **參數簡化**: 只需調整停損，無需停利參數
3. **動態適應**: 停利點隨市場區間動態調整
4. **實驗效率**: 組合數量較少，測試更快

### 適用場景
- 驗證原策略設計的有效性
- 尋找最佳停損配置
- 比較動態 vs 固定停利效果
- MDD 最小化優化

## 注意事項

1. **時間區間**: 確保區間計算正確，影響停利點位置
2. **停損約束**: 維持 lot1_sl ≤ lot2_sl ≤ lot3_sl 的邏輯約束
3. **結果比較**: 與固定停利結果比較時注意參數差異
4. **性能考量**: 完整 7,000 組合需要較長執行時間

## 下一步

1. **小規模測試**: 先用 `--sample-size 10` 驗證功能
2. **中等規模**: 用 `--sample-size 100` 獲得初步結果
3. **完整優化**: 執行全部 7,000 組合獲得最佳配置
4. **結果比較**: 與 user_custom 配置結果進行對比分析
