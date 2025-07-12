# 📊 時間區間MDD優化分析使用指南

## 🎯 概述
本指南說明如何使用已修復MDD計算的時間區間分析系統，進行真實的風險優化實驗。

## ✅ 系統狀態
- **MDD計算已修復** ✅ - 現在能正確計算和顯示真實的最大回撤
- **SQLite高性能** ✅ - 928個實驗約2-3分鐘完成
- **完整結果保存** ✅ - 所有數據自動保存到CSV文件

## 🚀 快速開始（推薦方式）

### 步驟1: 修改配置
編輯 `/Users/z/big/my-capital-project/strategy_optimization/time_interval_config.py` 中的 `focused_mdd` 配置：

```python
'focused_mdd': {
    'name': '專注MDD最小化',
    'description': '專門用於尋找最低MDD的時間區間配置',
    'time_intervals': [
        ("10:30", "10:32"),  # 修改您想測試的時間區間
        ("11:30", "11:32"),
        ("13:30", "13:32"),
        ("14:30", "14:32")
    ],
    'date_range': {
        'start_date': '2024-11-04',  # 修改測試日期範圍
        'end_date': '2024-12-31'
    },
    'stop_loss_ranges': {
        'lot1': [15, 20, 25, 30],    # 修改停損範圍
        'lot2': [15, 20, 25, 30],
        'lot3': [15, 20, 25, 30]
    },
    'take_profit_settings': [
        {
            'mode': 'trailing_stop',
            'trailing_config': {
                'lot1': {'trigger': 15, 'pullback': 10},  # 您的成功配置
                'lot2': {'trigger': 40, 'pullback': 10},
                'lot3': {'trigger': 41, 'pullback': 20}
            }
        }
    ],
    'stop_loss_mode': 'range_boundary'  # 使用區間邊緣停損
}
```

### 步驟2: 執行分析
```bash
cd /Users/z/big/my-capital-project/strategy_optimization
python run_focused_mdd_analysis.py
```

### 步驟3: 查看結果
結果會自動保存到：
- `data/processed/mdd_optimization_results_[timestamp].csv`

## 📊 結果分析

### 結果文件格式
CSV文件包含以下欄位：
- `experiment_id`: 實驗編號
- `time_interval`: 時間區間 (例如: 10:30-10:32)
- `lot1_stop_loss`, `lot2_stop_loss`, `lot3_stop_loss`: 各口停損點數
- `total_pnl`: 總損益
- `mdd`: 最大回撤 (現在是真實數據！)
- `win_rate`: 勝率
- `total_trades`: 總交易次數

### 尋找最佳配置
```python
import pandas as pd

# 讀取結果
df = pd.read_csv('data/processed/mdd_optimization_results_[timestamp].csv')

# 找到MDD最小的配置
best_mdd = df.loc[df['mdd'].idxmax()]  # MDD是負數，最大值表示最小回撤
print(f"最佳MDD配置: {best_mdd['time_interval']}")
print(f"MDD: {best_mdd['mdd']}")
print(f"總損益: {best_mdd['total_pnl']}")

# 按時間區間分組，找每個區間的最佳配置
best_by_interval = df.groupby('time_interval').apply(
    lambda x: x.loc[x['mdd'].idxmax()]
)
```

## ⚙️ 高級配置選項

### 其他可用配置
除了 `focused_mdd`，您也可以修改其他配置：

1. **quick_test** - 快速測試（少量實驗）
2. **standard_analysis** - 標準分析
3. **comprehensive_analysis** - 綜合分析

### 自定義停利模式
```python
'take_profit_settings': [
    {
        'mode': 'trailing_stop',  # 移動停利
        'trailing_config': {
            'lot1': {'trigger': 15, 'pullback': 10},
            'lot2': {'trigger': 40, 'pullback': 10},
            'lot3': {'trigger': 41, 'pullback': 20}
        }
    },
    {
        'mode': 'range_boundary'  # 區間邊緣停利
    }
]
```

## 📋 參數說明

### 時間區間格式
- 格式: `("HH:MM", "HH:MM")`
- 例如: `("10:30", "10:32")` 表示10:30到10:32的2分鐘區間
- **重要**: 這是信號檢測時間，開盤區間仍使用08:46-08:47

### 停損參數
- `lot1`, `lot2`, `lot3`: 各口停損點數範圍
- **新功能**: 現在支持相等停損值 (例如: 全部設為15點)
- 約束: lot1 <= lot2 <= lot3 (允許相等)

### 停利模式
- `trailing_stop`: 移動停利（推薦使用您的成功配置）
- `range_boundary`: 區間邊緣停利

### 停損模式
- `range_boundary`: 區間邊緣停損（推薦）
- `fixed_points`: 固定點數停損

## ⚠️ 重要注意事項

### MDD計算修復
- ✅ **已修復**: 之前所有MDD=0的問題已解決
- ✅ **真實數據**: 現在顯示真實的最大回撤數據
- ✅ **可靠分析**: 能夠進行真正的風險優化

### 性能優化
- **SQLite**: 使用本地數據庫，速度提升10-20倍
- **並行處理**: 4個進程並行，928實驗約2-3分鐘
- **即時結果**: 結果即時保存，可隨時查看

### 實驗規模
- `focused_mdd`: 約928個實驗（推薦）
- `quick_test`: 約100個實驗（快速驗證）
- `comprehensive_analysis`: 約2000+實驗（深度分析）

## 🎯 最佳實踐

### 推薦工作流程
1. **修改配置**: 編輯 `time_interval_config.py` 中的 `focused_mdd`
2. **執行分析**: `python run_focused_mdd_analysis.py`
3. **查看結果**: 分析CSV文件中的MDD和P&L數據
4. **調整參數**: 根據結果優化配置
5. **重複實驗**: 持續優化直到找到最佳配置

### 配置建議
- 使用您已驗證的移動停利配置 (15/10%, 40/10%, 41/20%)
- 測試不同時間區間找到最低MDD
- 考慮風險收益比，不只看MDD最小值
