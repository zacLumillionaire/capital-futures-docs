# 多空分離分析設計方案

## 📋 需求分析

用戶希望從batch_experiment_gui.py的實驗結果中，分析以下場景的策略績效：
1. **只做多策略**：僅在多方訊號出現時進場
2. **只做空策略**：僅在空方訊號出現時進場

目標是生成包含以下指標的報告：
- 實驗ID
- 時間區間  
- 總損益
- MDD（最大回撤）
- 勝率
- 參數

## 🔍 現有數據結構分析

### 1. 資料庫結構
```sql
-- batch_experiments.db 的 experiments 表
CREATE TABLE experiments (
    experiment_id INTEGER PRIMARY KEY,
    parameters TEXT NOT NULL,           -- JSON格式參數
    success BOOLEAN NOT NULL,
    execution_time REAL NOT NULL,
    total_trades INTEGER DEFAULT 0,     -- 總交易次數
    winning_trades INTEGER DEFAULT 0,   -- 獲利交易次數
    losing_trades INTEGER DEFAULT 0,    -- 虧損交易次數
    win_rate REAL DEFAULT 0.0,         -- 總勝率
    total_pnl REAL DEFAULT 0.0,        -- 總損益
    max_drawdown REAL DEFAULT 0.0,     -- 總MDD
    long_trades INTEGER DEFAULT 0,      -- 多頭交易次數
    short_trades INTEGER DEFAULT 0,     -- 空頭交易次數
    long_pnl REAL DEFAULT 0.0,         -- 多頭總損益
    short_pnl REAL DEFAULT 0.0,        -- 空頭總損益
    error_message TEXT DEFAULT '',
    stdout_log TEXT DEFAULT '',
    stderr_log TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. CSV輸出格式
```csv
實驗ID,時間區間,多頭損益,空頭損益,總損益,MDD,勝率,參數
2186,13:00-13:02,-379.8,429.2,49.4,1270.0,38.0%,25/50/55
```

### 3. 數據驗證結果
✅ **多空損益加總正確**：long_pnl + short_pnl = total_pnl
✅ **數據完整性**：所有實驗都有完整的多空分離數據

## ⚠️ 關鍵限制

### 1. MDD計算限制
**問題**：現有的max_drawdown是基於總策略（多空混合）計算的，不是只做多或只做空的MDD。

**原因**：
- MDD需要基於交易序列的累積損益曲線計算
- 現有系統只存儲最終的多空損益總和，沒有交易明細序列
- 無法重新構建只做多或只做空的損益曲線

### 2. 勝率計算限制
**問題**：現有系統沒有分別記錄多頭和空頭的獲利/虧損次數。

**現有數據**：
- `long_trades`: 多頭交易總次數
- `short_trades`: 空頭交易總次數
- `winning_trades`: 總獲利次數（多空混合）
- `losing_trades`: 總虧損次數（多空混合）

**缺失數據**：
- 多頭獲利次數
- 多頭虧損次數
- 空頭獲利次數
- 空頭虧損次數

## 💡 可行解決方案

### 方案A：基於現有數據的近似分析（推薦）

#### 1. 損益分析（精確）
- ✅ 直接使用 `long_pnl` 和 `short_pnl`
- ✅ 數據完全準確

#### 2. MDD估算（近似）
**方法1：比例估算法**
```python
# 假設MDD與損益成正比
long_mdd_estimate = max_drawdown * abs(long_pnl) / abs(total_pnl)
short_mdd_estimate = max_drawdown * abs(short_pnl) / abs(total_pnl)
```

**方法2：保守估算法**
```python
# 保守估計：如果該方向虧損，MDD至少等於虧損金額
if long_pnl < 0:
    long_mdd_estimate = abs(long_pnl)
else:
    long_mdd_estimate = max_drawdown * 0.3  # 保守估計

if short_pnl < 0:
    short_mdd_estimate = abs(short_pnl)
else:
    short_mdd_estimate = max_drawdown * 0.3
```

#### 3. 勝率估算（近似）
**方法1：平均分配法**
```python
# 假設多空勝率相近
long_win_rate_estimate = win_rate  # 使用總勝率作為估計
short_win_rate_estimate = win_rate
```

**方法2：損益權重法**
```python
# 基於損益表現調整勝率估計
if long_pnl > short_pnl:
    long_win_rate_estimate = win_rate * 1.1  # 略高於平均
    short_win_rate_estimate = win_rate * 0.9  # 略低於平均
else:
    long_win_rate_estimate = win_rate * 0.9
    short_win_rate_estimate = win_rate * 1.1
```

### 方案B：回測程式修改（未來改進）

修改 `multi_Profit-Funded Risk_多口.py` 以輸出更詳細的統計：
```python
# 在回測結果中添加
return {
    'total_pnl': float(total_pnl),
    'long_pnl': float(long_pnl),
    'short_pnl': float(short_pnl),
    'long_wins': long_wins,        # 新增
    'short_wins': short_wins,      # 新增
    'long_win_rate': long_win_rate,   # 新增
    'short_win_rate': short_win_rate, # 新增
    # ... 其他現有欄位
}
```

## 🎯 實施計劃

### 階段1：多空分離報告生成器（立即實施）

創建 `long_short_separation_analyzer.py`：

```python
class LongShortSeparationAnalyzer:
    def __init__(self, db_path="batch_experiments.db"):
        self.db_path = db_path
    
    def generate_long_only_report(self):
        """生成只做多策略報告"""
        # 從資料庫提取數據
        # 使用方案A進行MDD和勝率估算
        # 生成CSV報告
    
    def generate_short_only_report(self):
        """生成只做空策略報告"""
        # 類似邏輯
    
    def estimate_mdd(self, total_mdd, direction_pnl, total_pnl):
        """MDD估算邏輯"""
    
    def estimate_win_rate(self, total_win_rate, direction_pnl, total_pnl):
        """勝率估算邏輯"""
```

### 階段2：Web GUI整合

在 `batch_experiment_gui.py` 中添加：
- "📊 生成多方報告" 按鈕
- "📊 生成空方報告" 按鈕
- 報告下載功能

### 階段3：報告格式

#### 多方專用報告 (long_only_results.csv)
```csv
實驗ID,時間區間,多方損益,多方MDD估算,多方勝率估算,參數,備註
2186,13:00-13:02,-379.8,379.8,35.0%,25/50/55,MDD/勝率為估算值
```

#### 空方專用報告 (short_only_results.csv)
```csv
實驗ID,時間區間,空方損益,空方MDD估算,空方勝率估算,參數,備註
2186,13:00-13:02,429.2,200.0,41.0%,25/50/55,MDD/勝率為估算值
```

## 📊 預期效果

### 優點
1. ✅ **立即可用**：基於現有數據，無需修改回測機制
2. ✅ **損益精確**：多空損益數據完全準確
3. ✅ **快速分析**：可快速識別適合只做多或只做空的時段和參數
4. ✅ **風險可控**：不影響現有系統穩定性

### 限制
1. ⚠️ **MDD估算**：非精確計算，僅供參考
2. ⚠️ **勝率估算**：非精確計算，僅供參考
3. ⚠️ **需要標註**：報告中需明確標示估算性質

### 使用建議
1. **主要參考損益**：以多空損益為主要決策依據
2. **MDD/勝率參考**：將估算的MDD和勝率作為輔助參考
3. **後續驗證**：對有潛力的配置進行專門的只做多/只做空回測驗證

## 🚀 下一步行動

1. **實作分析工具**：創建 `long_short_separation_analyzer.py`
2. **測試驗證**：使用現有數據測試分析邏輯
3. **GUI整合**：添加到batch_experiment_gui.py
4. **用戶測試**：生成實際報告供用戶評估

這個方案在不修改現有回測機制的前提下，提供了有價值的多空分離分析功能，雖然某些指標是估算的，但仍能幫助用戶識別最適合的交易方向和時段。
