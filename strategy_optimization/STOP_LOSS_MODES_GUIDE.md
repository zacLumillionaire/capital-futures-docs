# 停損模式支援指南

## 概述

時間區間分析系統現在支援兩種停損模式，讓用戶可以測試原策略的預設區間邊緣停損和固定點數停損的效果差異。

## 支援的停損模式

### 1. 區間邊緣停損 (Range Boundary)
- **描述**: 使用區間邊緣作為停損點（原策略預設）
- **LONG位置**: 停損點 = range_low（區間下緣）
- **SHORT位置**: 停損點 = range_high（區間上緣）
- **優點**: 符合原策略設計邏輯，停損點隨區間動態調整
- **配置**: `stop_loss_mode: 'range_boundary'`

### 2. 固定點數停損 (Fixed Points)
- **描述**: 使用固定點數作為停損距離
- **LONG位置**: 停損點 = 入場價 - 固定點數
- **SHORT位置**: 停損點 = 入場價 + 固定點數
- **優點**: 風險控制更精確，適合風險管理測試
- **配置**: `stop_loss_mode: 'fixed_points'`

## 配置設定

### 在 time_interval_config.py 中啟用

```python
'focused_mdd': {
    'analysis_mode': 'per_time_interval',  # 啟用時間區間分析
    'stop_loss_modes': {
        'range_boundary': True,    # 區間邊緣停損
        'fixed_points': True       # 固定點數停損
    },
    'stop_loss_ranges': {
        'lot1': [15, 25, 40],
        'lot2': [15, 35, 40], 
        'lot3': [15, 40, 41]
    },
    # ... 其他配置
}
```

## 使用方法

### 1. 互動模式使用

```bash
python run_time_interval_analysis.py interactive
```

系統會提示選擇停損模式：
```
🛡️ 停損模式選擇
可用的停損模式:
1. 區間邊緣停損 (原策略預設)
2. 固定點數停損
3. 兩種模式都測試

請選擇停損模式 (1-3, 預設: 3):
```

### 2. 程式化使用

```python
from enhanced_mdd_optimizer_adapted import EnhancedMDDOptimizer

# 初始化優化器
optimizer = EnhancedMDDOptimizer('focused_mdd')

# 生成實驗組合（自動包含兩種停損模式）
combinations = optimizer.generate_experiment_combinations()

# 檢查組合中的停損模式
for combo in combinations:
    stop_loss_mode = combo.get('stop_loss_mode', 'fixed_points')
    print(f"實驗 {combo['experiment_id']}: 停損模式 = {stop_loss_mode}")
```

## 實驗組合生成

系統會為每種停損模式生成完整的實驗組合：

### 組合數量計算
- **基礎組合**: 時間區間 × 停損參數組合 × 停利模式
- **停損模式倍增**: 每個基礎組合 × 2（兩種停損模式）

### 範例組合
```
10:3010:32_L1SL15_L2SL25_L3SL35_RangeBoundary_range_boundary
10:3010:32_L1SL15_L2SL25_L3SL35_RangeBoundary_fixed_points
10:3010:32_L1SL15_L2SL25_L3SL35_TP60_range_boundary
10:3010:32_L1SL15_L2SL25_L3SL35_TP60_fixed_points
```

## 配置轉換

### 區間邊緣停損配置
```python
config = {
    'filters': {
        'stop_loss_filter': {
            'enabled': True,
            'stop_loss_type': 'range_boundary'
        }
    }
}
```

### 固定點數停損配置
```python
config = {
    'filters': {
        'stop_loss_filter': {
            'enabled': True,
            'stop_loss_type': 'fixed_points',
            'fixed_stop_loss_points': 15  # 使用第1口停損作為基準
        }
    }
}
```

## 與原策略的兼容性

### StopLossType 枚舉支援
- ✅ `RANGE_BOUNDARY`: 區間邊緣停損
- ✅ `FIXED_POINTS`: 固定點數停損  
- ✅ `OPENING_PRICE`: 開盤價停損

### StopLossConfig 類別
```python
@dataclass
class StopLossConfig:
    stop_loss_type: StopLossType = StopLossType.RANGE_BOUNDARY  # 預設區間邊緣
    fixed_stop_loss_points: int = 15
    use_range_midpoint: bool = False
```

## 測試驗證

### 運行測試
```bash
python test_stop_loss_modes.py
```

### 測試內容
1. ✅ 停損模式配置轉換
2. ✅ 實驗組合生成
3. ✅ 與原策略兼容性
4. ✅ 配置驗證

## 注意事項

1. **配置要求**: 只有設定 `analysis_mode: 'per_time_interval'` 的配置才支援停損模式選擇
2. **向後兼容**: 未設定停損模式的配置會使用預設的固定點數停損
3. **組合數量**: 啟用兩種停損模式會使實驗組合數量翻倍
4. **移動停利**: 停損模式不影響移動停利功能，移動停利仍正常運作

## 實際應用

### 研究目標
- 比較區間邊緣停損 vs 固定點數停損的績效差異
- 找出在不同時間區間下最適合的停損模式
- 驗證原策略預設停損邏輯的有效性

### 分析建議
1. 先運行小樣本測試確認功能正常
2. 比較兩種停損模式的MDD表現
3. 分析不同時間區間的停損模式偏好
4. 結合移動停利效果進行綜合評估
