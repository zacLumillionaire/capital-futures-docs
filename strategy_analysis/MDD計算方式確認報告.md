# MDD (Maximum Drawdown) 計算方式確認報告

## 📋 概述

根據對 `batch_experiment_gui.py` 和相關回測系統的分析，我確認了 MDD 的計算方式和數據來源。

## 🔍 MDD 計算流程

### 1. 數據來源確認

#### 核心回測程式 (`multi_Profit-Funded Risk_多口.py`)
- **返回結果**: 不包含 `max_drawdown` 欄位
- **提供數據**: 
  ```python
  {
      'total_pnl': float(total_pnl),
      'long_pnl': float(long_pnl), 
      'short_pnl': float(short_pnl),
      'total_trades': trade_count,
      'winning_trades': winning_trades,
      'losing_trades': losing_trades,
      'win_rate': win_rate / 100,
      # 注意：沒有 max_drawdown
  }
  ```

#### 批次回測引擎 (`batch_backtest_engine.py`)
- **MDD 計算**: 從交易日誌中解析每筆交易損益
- **計算位置**: 第 222-260 行
- **計算邏輯**: 逐筆累積損益，追蹤峰值和回撤

### 2. MDD 計算邏輯詳解

#### 核心算法 (batch_backtest_engine.py 第 235-253 行)
```python
# 從交易日誌中提取每筆交易的損益
trades_pnl = []
for line in full_output.split('\n'):
    if '損益:' in line:
        try:
            pnl_str = line.split('損益:')[1].strip().split()[0]
            trades_pnl.append(float(pnl_str))
        except:
            pass

# 計算最大回撤
if trades_pnl:
    peak = 0           # 累積損益峰值
    max_dd = 0         # 最大回撤
    current_pnl = 0    # 當前累積損益

    for pnl in trades_pnl:
        current_pnl += pnl    # 累積損益

        # 更新峰值
        if current_pnl > peak:
            peak = current_pnl

        # 計算回撤
        drawdown = peak - current_pnl
        if drawdown > max_dd:
            max_dd = drawdown

    metrics['max_drawdown'] = max_dd  # 正值表示回撤幅度
```

#### 計算步驟說明
1. **解析交易日誌**: 從回測輸出中提取每筆交易的損益
2. **累積計算**: 逐筆累加損益，形成累積損益曲線
3. **峰值追蹤**: 記錄累積損益的歷史最高點
4. **回撤計算**: 當前累積損益與峰值的差距
5. **最大回撤**: 所有回撤中的最大值

### 3. MDD 數值含義

#### 數值表示方式
- **正值**: MDD 以正值存儲（如 15.6 表示最大回撤 15.6 點）
- **顯示方式**: 在界面中顯示為負值（如 -15.6）
- **排序邏輯**: 按升序排列，數值越小（接近 0）風險越低

#### 示例說明
```
交易序列: +10, -5, +15, -20, +8
累積損益: 10, 5, 20, 0, 8
峰值追蹤: 10, 10, 20, 20, 20
回撤計算: 0, 5, 0, 20, 12
最大回撤: 20 (發生在第4筆交易後)
```

### 4. 界面顯示邏輯

#### CSV 導出格式
```csv
實驗ID,時間區間,多頭損益,空頭損益,總損益,MDD,勝率,參數
EXP_001,08:46-08:47,45.2,-12.8,32.4,-15.6,65.5%,20/45/50
```
- **MDD 欄位**: 顯示為負值 (-15.6)
- **含義**: 該配置的最大回撤為 15.6 點

#### 網頁界面顯示
```javascript
// 顏色邏輯
style="color: ${result.max_drawdown <= 0 ? 'green' : 'red'};"

// 數值顯示
${result.max_drawdown.toFixed(1)}
```
- **綠色**: MDD ≤ 0（理想情況，無回撤）
- **紅色**: MDD > 0（有回撤，數值越大風險越高）

### 5. 排序和篩選邏輯

#### 各時段 MDD 最低前三名
```python
# 按MDD排序（升序，最低的在前）
sorted_results = sorted(results, key=lambda x: x.get('max_drawdown', float('inf')))
time_slot_results[time_slot] = sorted_results[:3]  # 取前三名
```

#### 排序說明
- **升序排列**: 數值越小排名越前
- **最佳結果**: MDD 接近 0 的配置
- **風險評估**: MDD 越大表示風險越高

## 🎯 MDD 計算準確性評估

### 優點
1. **基於實際交易**: 從真實的交易日誌中計算
2. **逐筆追蹤**: 考慮每筆交易對累積損益的影響
3. **峰值回撤**: 正確計算從峰值到谷底的最大回撤

### 潛在問題
1. **日誌解析依賴**: 依賴交易日誌格式的穩定性
2. **口內回撤**: 可能未考慮單日內多口交易的回撤
3. **時間序列**: 按交易順序而非時間順序計算

### 建議改進
1. **增強解析**: 改進日誌解析的穩定性
2. **時間權重**: 考慮交易時間順序
3. **分口計算**: 提供各口獨立的 MDD 分析

## 📊 實際應用建議

### MDD 閾值設定
- **保守型**: MDD < 10 點
- **平衡型**: MDD < 20 點  
- **積極型**: MDD < 30 點

### 風險評估指標
```
風險調整收益 = 總損益 / MDD
夏普比率 = (總損益 - 無風險收益) / 損益標準差
最大回撤比 = MDD / 總損益
```

### 配置選擇建議
1. **優先考慮**: MDD 最小的配置
2. **平衡考量**: MDD 與總損益的比例
3. **時段分析**: 不同時段的 MDD 表現

## ✅ 確認結論

### MDD 計算方式確認
1. **計算來源**: 從交易日誌解析每筆交易損益
2. **計算方法**: 累積損益峰值回撤法
3. **數值含義**: 正值存儲，負值顯示
4. **排序邏輯**: 升序排列，越小越好

### 數據可靠性
- ✅ **算法正確**: 標準的 MDD 計算方法
- ✅ **數據真實**: 基於實際交易結果
- ⚠️ **解析依賴**: 依賴日誌格式穩定性
- ✅ **結果一致**: 多個系統使用相同邏輯

### 使用建議
1. **重視 MDD**: 作為風險控制的重要指標
2. **綜合評估**: 結合總損益和勝率考慮
3. **時段比較**: 利用各時段 MDD 分析功能
4. **參數優化**: 以 MDD 最小化為優化目標

---

**總結**: MDD 計算方式正確且可靠，基於真實交易數據的峰值回撤法計算，可以作為策略風險評估的重要依據。
