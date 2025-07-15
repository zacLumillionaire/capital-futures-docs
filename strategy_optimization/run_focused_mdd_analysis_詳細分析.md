# run_focused_mdd_analysis.py 詳細功能分析報告

## 📋 概述

`run_focused_mdd_analysis.py` 是一個專門用於執行 MDD (Maximum Drawdown) 最小化參數優化的分析工具，屬於 strategy_optimization 項目的核心組件。

## 🎯 1. 主要回測核心程式

### 核心程式架構
```
run_focused_mdd_analysis.py (主控制器)
    ↓
enhanced_mdd_optimizer_adapted.py (優化器)
    ↓
multi_Profit-Funded Risk_多口.py (回測引擎)
```

### 回測核心程式對比

#### 1.1 strategy_optimization 版本 (純做多)
**文件**: `strategy_optimization/multi_Profit-Funded Risk_多口.py`

⚠️ **重要發現**: 當前版本是**純做多策略**，已移除空單邏輯：
```python
# 只做多：僅當價格突破上軌時進場
if candle['close_price'] > range_high:
    position, entry_price, entry_time, entry_candle_index = 'LONG', candle['close_price'], candle['trade_datetime'].time(), i

# 移除做空邏輯 - 只做多策略
```

#### 1.2 strategy_analysis 版本 (多空雙向)
**文件**: `strategy_analysis/multi_Profit-Funded Risk_多口.py`

✅ **完整多空策略**，支援雙向交易：
```python
for i, candle in enumerate(trade_candles):
    if candle['close_price'] > range_high:
        position, entry_price, entry_time, entry_candle_index = 'LONG', candle['close_price'], candle['trade_datetime'].time(), i
        break
    elif candle['low_price'] < range_low:
        position, entry_price, entry_time, entry_candle_index = 'SHORT', candle['close_price'], candle['trade_datetime'].time(), i
        break
```

## 🔧 2. run_focused_mdd_analysis.py 運作方式

### 2.1 執行流程
```python
def run_focused_mdd_analysis():
    # 1. 創建優化器
    optimizer = EnhancedMDDOptimizer('focused_mdd')
    
    # 2. 設定日期範圍
    optimizer.set_date_range('2024-11-04', '2025-06-28')
    
    # 3. 運行優化 (4個並行進程)
    results = optimizer.run_optimization(max_workers=4)
    
    # 4. 分析結果並顯示最佳配置
```

### 2.2 配置來源
- **配置文件**: `time_interval_config.py`
- **配置名稱**: `focused_mdd`
- **預期實驗數**: 928 個

### 2.3 優化目標
- **主要目標**: MDD (最大回撤) 最小化
- **次要指標**: 總損益、勝率、交易次數

## ⚙️ 3. 配置修改方式

### 3.1 修改 focused_mdd 配置
**文件位置**: `strategy_optimization/time_interval_config.py`

**關鍵配置參數**:
```python
'focused_mdd': {
    'time_intervals': [
        ("08:46", "08:47"),  # 基礎驗證時間
        ("10:30", "10:32"),
        ("11:30", "11:32"),
        ("12:30", "12:32"),
        ("13:00", "13:02")
    ],
    'stop_loss_ranges': {
        'lot1': [15, 20, 25, 30],
        'lot2': [15, 20, 25, 30],
        'lot3': [15, 20, 25, 30]
    },
    'take_profit_ranges': {
        'unified': [55],
        'individual': [15, 40, 41]
    },
    'take_profit_settings': [
        {
            'mode': 'trailing_stop',
            'trailing_config': {
                'lot1': {'trigger': 15, 'pullback': 10},
                'lot2': {'trigger': 40, 'pullback': 10},
                'lot3': {'trigger': 41, 'pullback': 20}
            }
        }
    ]
}
```

### 3.2 可修改的配置項目

#### 時間區間調整
```python
'time_intervals': [
    ("08:46", "08:47"),  # 可添加更多時間區間
    ("09:30", "09:32"),  # 新增時間區間
]
```

#### 停損範圍調整
```python
'stop_loss_ranges': {
    'lot1': [10, 15, 20, 25],  # 擴展範圍
    'lot2': [20, 25, 30, 35],  # 調整數值
    'lot3': [30, 35, 40, 45]   # 增加選項
}
```

#### 停利設定調整
```python
'take_profit_ranges': {
    'unified': [50, 60, 70],     # 統一停利選項
    'individual': [40, 50, 60]   # 各口獨立停利
}
```

## 🔍 4. 核心回測方式與 simple_integrated.py 比較

### 4.1 進場機制比較

| 項目 | strategy_optimization | strategy_analysis | simple_integrated.py | 一致性 |
|------|---------------------|------------------|---------------------|--------|
| **支援方向** | 純做多 | 多空雙向 | 多空雙向 | ⚠️ 部分一致 |
| **多單觸發** | `close_price > range_high` | `close_price > range_high` | `close_price > range_high` | ✅ 完全一致 |
| **空單觸發** | 已移除 | `low_price < range_low` | `price < range_low` (即時) | ⚠️ 部分一致 |
| **進場價格** | K棒收盤價 | K棒收盤價 | 下一個報價 | ❌ 不一致 |

### 4.2 詳細差異分析

#### 空單進場邏輯對比

**strategy_analysis 版本** (完整多空):
```python
elif candle['low_price'] < range_low:
    position, entry_price, entry_time, entry_candle_index = 'SHORT', candle['close_price'], candle['trade_datetime'].time(), i
    break
```

**simple_integrated.py** (實盤):
```python
def check_immediate_short_entry_safe(self, price, time_str):
    # 🚀 空單即時檢測：任何報價跌破區間下緣就立即觸發
    if price < self.range_low:
        self.first_breakout_detected = True
        self.breakout_direction = 'SHORT'
        self.waiting_for_entry = True

def check_breakout_signals_safe(self, price, time_str):
    entry_price = price  # 使用下一個報價進場
```

#### 關鍵差異分析

1. **觸發條件**:
   - **strategy_analysis**: `candle['low_price'] < range_low` (K棒最低價跌破)
   - **simple_integrated**: `price < range_low` (即時報價跌破)

2. **進場價格**:
   - **strategy_analysis**: `candle['close_price']` (跌破當根K棒收盤價)
   - **simple_integrated**: `price` (跌破後下一個報價)

3. **觸發時機**:
   - **strategy_analysis**: 等待K棒收盤確認
   - **simple_integrated**: 即時觸發，不等收盤

### 4.3 配置靈活性比較

#### strategy_optimization 優勢
✅ **更多配置選項**:
- 多種時間區間測試
- 靈活的停損停利組合
- 批量參數優化
- MDD 最小化目標
- 並行處理能力

✅ **豐富的分析模式**:
- 時間區間分析
- 參數敏感性測試
- 統計報告生成
- 視覺化圖表

#### simple_integrated.py 優勢
✅ **實盤交易特性**:
- 即時報價處理
- 多空雙向交易
- 實時風險管理
- 追價機制
- 回報確認

## 🚨 5. 重要發現與建議

### 5.1 關鍵問題
1. **版本差異**:
   - `strategy_optimization` 版本是純做多
   - `strategy_analysis` 版本支援多空雙向
   - `simple_integrated.py` 是實盤多空策略

2. **進場價格差異**:
   - 回測版本用K棒收盤價
   - 實盤版本用下一個報價

3. **觸發機制差異**:
   - 回測版本等K棒收盤確認
   - 實盤版本即時觸發

### 5.2 建議改進
1. **選擇正確版本**:
   - 多空策略優化使用 `strategy_analysis` 版本
   - 純做多策略使用 `strategy_optimization` 版本

2. **統一進場價格**: 考慮加入滑價模擬

3. **對齊觸發機制**: 實現即時觸發邏輯

### 5.3 使用建議

#### 針對多空策略
- ✅ 使用 `strategy_analysis/multi_Profit-Funded Risk_多口.py`
- ✅ 支援完整的空單進場邏輯
- ⚠️ 注意進場價格與實盤的差異

#### 針對純做多策略
- ✅ 使用 `strategy_optimization/multi_Profit-Funded Risk_多口.py`
- ✅ 適合做多策略的參數優化
- ✅ 可直接使用 `run_focused_mdd_analysis.py`

#### 實盤部署建議
- 🔍 驗證回測與實盤策略一致性
- 🔍 測試進場價格差異的影響
- 🔍 考慮滑價和延遲因素

## 📊 6. 執行方式

### 6.1 直接執行
```bash
cd /Users/z/big/my-capital-project/strategy_optimization
python run_focused_mdd_analysis.py
```

### 6.2 修改配置後執行
1. 編輯 `time_interval_config.py` 中的 `focused_mdd` 配置
2. 執行分析程式
3. 查看結果報告

## 🎯 7. 輸出結果

### 7.1 控制台輸出
- 實驗進度
- 最佳 MDD 配置
- 各時間區間最佳結果
- 統計摘要

### 7.2 文件輸出
- 詳細日誌: `data/processed/enhanced_mdd_optimization.log`
- 結果數據: CSV 格式
- 分析報告: HTML 格式

---

## 📋 問題回答總結

### Q1: 主要回測核心程式是哪個？
**答案**: 有兩個版本
- **多空版本**: `strategy_analysis/multi_Profit-Funded Risk_多口.py` (支援空單)
- **純做多版本**: `strategy_optimization/multi_Profit-Funded Risk_多口.py` (不支援空單)

### Q2: 如何修改 run_focused_mdd_analysis.py 配置？
**答案**: 修改 `strategy_optimization/time_interval_config.py` 中的 `focused_mdd` 配置
- 時間區間: `time_intervals`
- 停損範圍: `stop_loss_ranges`
- 停利設定: `take_profit_ranges`

### Q3: 核心回測方式的空單與 simple_integrated.py 比較？
**答案**:
- ✅ **strategy_analysis 版本**: 支援空單，觸發條件 `low_price < range_low`，使用收盤價進場
- ❌ **strategy_optimization 版本**: 不支援空單，已移除空單邏輯
- 🔄 **simple_integrated.py**: 支援空單，即時觸發 `price < range_low`，使用下一個報價進場

### Q4: 是否有更多配置選項？
**答案**: ✅ 是的，strategy_optimization 提供豐富的配置選項：
- 🕐 多種時間區間測試
- 🎯 靈活的停損停利組合
- 📊 MDD 最小化優化
- ⚡ 並行處理能力
- 📈 統計分析和視覺化

---

**總結**: `run_focused_mdd_analysis.py` 是功能強大的參數優化工具，但需要注意版本差異。如需多空策略分析，建議使用 `strategy_analysis` 版本的回測引擎。
