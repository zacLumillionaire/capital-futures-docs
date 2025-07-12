# 🎯 反向策略完整功能指南

## 📋 目錄
1. [反向策略Web GUI](#反向策略web-gui)
2. [MDD最小化實驗系統](#mdd最小化實驗系統)
3. [參數優化實驗系統](#參數優化實驗系統)
4. [時間區間實驗系統](#時間區間實驗系統)
5. [停損停利點實驗系統](#停損停利點實驗系統)
6. [系統架構說明](#系統架構說明)

---

## 🖥️ 反向策略Web GUI

### 📍 文件位置
```
rev_strategy_analysis/rev_web_trading_gui.py
```

### 🚀 啟動方式
```bash
cd rev_strategy_analysis
python rev_web_trading_gui.py
```

### 🎛️ 功能特色

#### ✅ 基本回測功能
- **時間範圍設定**: 開始日期、結束日期
- **時間區間設定**: 開盤範圍時間 (如 10:30-10:31)
- **反向策略**: 自動將原策略信號反向

#### ✅ 三口獨立停損設定
- **第1口停損**: 可設定固定停損點數
- **第2口停損**: 可設定固定停損點數
- **第3口停損**: 可設定固定停損點數
- **固定停損模式**: 禁用移動停損機制

#### ✅ 每口獨立停利設定 🎯 **NEW**
- **第1口停利**: 可設定獨立停利點數
- **第2口停利**: 可設定獨立停利點數
- **第3口停利**: 可設定獨立停利點數
- **驗證實驗**: 用於驗證MDD優化實驗結果
- **策略測試**: 測試不同停利點數組合的效果

#### ✅ 風險管理設定
- **每日虧損限制**: 設定單日最大虧損
- **利潤目標**: 設定單日利潤目標
- **範圍過濾**: 設定最大範圍點數過濾

#### ✅ 報告功能
- **詳細交易記錄**: 每筆交易的完整資訊
- **個別口數分析**: 每口的損益統計
- **策略配置摘要**: 完整參數記錄
- **圖表分析**: 損益曲線圖

### 🔧 參數修改方式

#### 停損設定
```python
# 在GUI介面中設定
第1口停損點數: 15    # 固定停損15點
第2口停損點數: 25    # 固定停損25點  
第3口停損點數: 30    # 固定停損30點
固定停損模式: ✓      # 啟用固定停損
```

#### 時間區間設定
```python
開盤範圍開始時間: 10:30
開盤範圍結束時間: 10:31
```

#### 風險管理
```python
每日虧損限制: 500    # 單日最大虧損500點
利潤目標: 1000       # 單日利潤目標1000點
範圍過濾: 160        # 最大範圍160點
```

#### 每口獨立停利設定 🎯 **NEW**
```python
# 在GUI介面中設定
啟用每口獨立停利點數: ✓    # 啟用每口獨立停利功能
第1口停利點數: 50          # 第1口停利50點
第2口停利點數: 70          # 第2口停利70點
第3口停利點數: 90          # 第3口停利90點

# 建議搭配固定停損模式使用
固定停損模式: ✓            # 避免移動停損邏輯干擾
```

**功能說明**:
- 每口可設定不同的停利點數，替代預設的區間邊緣停利
- 用於驗證MDD優化實驗結果和測試不同停利策略組合
- 建議搭配固定停損模式使用，確保策略邏輯簡潔明確

---

## 📊 MDD最小化實驗系統

### 📍 文件位置
```
rev_strategy_analysis/experiment_analysis/enhanced_mdd_optimizer.py    # 🆕 增強版優化器
rev_strategy_analysis/experiment_analysis/mdd_search_config.py         # 🆕 搜索配置管理
rev_strategy_analysis/experiment_analysis/mdd_optimizer.py             # 原版優化器
rev_strategy_analysis/experiment_analysis/mdd_backtest_engine.py       # 回測引擎
rev_strategy_analysis/experiment_analysis/test_mdd_optimizer.py        # 系統測試
```

### 🚀 使用方式

#### 🆕 增強版 MDD 優化器（推薦）

##### 1. 查看所有可用配置
```bash
cd rev_strategy_analysis/experiment_analysis
python enhanced_mdd_optimizer.py --show-configs
```

##### 2. 快速測試（推薦新手）
```bash
# 聚焦搜索，50個樣本
python enhanced_mdd_optimizer.py --config focused --sample-size 50

# 時間重點搜索，30個樣本
python enhanced_mdd_optimizer.py --config time_focus --sample-size 30
```

##### 3. 完整搜索（進階用戶）
```bash
# 聚焦搜索，統一停利模式
python enhanced_mdd_optimizer.py --config focused --sample-size 500

# 每口獨立停利模式（組合數量大）
python enhanced_mdd_optimizer.py --config focused --individual-tp --sample-size 200
```

##### 4. 詳細搜索（需要更長時間）
```bash
# 詳細搜索，統一停利
python enhanced_mdd_optimizer.py --config detailed --sample-size 1000

# 時間重點，完整搜索
python enhanced_mdd_optimizer.py --config time_focus
```

#### 原版 MDD 優化器
```bash
# 系統測試
python test_mdd_optimizer.py

# 快速實驗 (20個樣本)
python mdd_optimizer.py --sample-size 20

# 中等實驗 (50個樣本) + 可視化
python mdd_optimizer.py --sample-size 50 --create-viz

# 完整優化 (4,176個實驗)
python mdd_optimizer.py --create-viz
```

### 🎯 實驗範圍

#### 🆕 增強版配置類型

| 配置類型 | 描述 | 統一停利組合數 | 獨立停利組合數 | 適用場景 |
|---------|------|---------------|---------------|----------|
| **QUICK** | 快速搜索 | 1,620 | 14,580 | 初步探索 |
| **DETAILED** | 詳細搜索 | 180,224 | 11,534,336 | 全面分析 |
| **FOCUSED** | 聚焦搜索 | 2,500 | 62,500 | 精確優化 |
| **TIME_FOCUS** | 時間重點 | 208 | 832 | 時間區間測試 |

#### 🆕 增強版參數範圍

##### FOCUSED 配置
```python
第1口停損: [12, 14, 15, 16, 18] 點
第2口停損: [22, 24, 25, 26, 28] 點
第3口停損: [28, 29, 30, 31, 32] 點
統一停利: [50, 55, 60, 65, 70] 點
時間區間: ['10:30-10:31', '11:30-11:31', '11:30-11:32', '12:30-12:31']
```

##### TIME_FOCUS 配置
```python
第1口停損: [15, 20] 點
第2口停損: [25, 30] 點
第3口停損: [30, 35] 點
統一停利: [60, 80] 點
時間區間: ['09:00-09:01', '09:00-09:02', '10:30-10:31', '10:30-10:32',
          '11:00-11:01', '11:30-11:31', '11:30-11:32', '12:00-12:01',
          '12:30-12:31', '12:30-12:32', '13:00-13:01', '13:30-13:31', '13:30-13:32']
```

#### 原版參數範圍
```python
第1口停損: 10, 15, 20, 25, 30 點
第2口停損: 20, 25, 30, 35, 40, 45, 50 點
第3口停損: 30, 35, 40, 45, 50, 55, 60 點
停利目標: 30, 40, 50, 60, 70, 80, 90, 100 點
時間區間: ['10:30-10:31', '11:30-11:31', '12:30-12:31']
```

### 🔧 參數修改方式

#### 🆕 增強版配置修改

##### 創建自定義配置
```python
# 在 mdd_search_config.py 中新增配置
@staticmethod
def get_custom_search_config():
    """自定義搜索配置"""
    return {
        'stop_loss_ranges': {
            'lot1': [15, 20, 25, 30, 45, 50, 55, 60, 65, 70],  # 你的需求
            'lot2': [15, 20, 25, 30, 45, 50, 55, 60, 65, 70],  # 你的需求
            'lot3': [15, 20, 25, 30, 45, 50, 55, 60, 65, 70]   # 你的需求
        },
        'take_profit_ranges': {
            'unified': [40, 50, 60, 70, 80]  # 你的需求
        },
        'time_intervals': [
            ("10:00", "10:02"), ("10:30", "10:32"),  # 你的需求
            ("11:00", "11:02"), ("11:30", "11:32"),  # 你的需求
            ("12:00", "12:02"), ("12:30", "12:32"),  # 你的需求
            ("13:00", "13:02")                       # 你的需求
        ]
    }
```

##### 使用自定義配置
```python
# 在 enhanced_mdd_optimizer.py 中添加
def get_config_by_name(self, config_name):
    if config_name == 'custom':
        return MDDSearchConfig.get_custom_search_config()
    # ... 其他配置
```

#### 原版配置修改

##### 修改停損範圍
```python
# 在 mdd_optimizer.py 中修改
self.stop_loss_ranges = {
    'lot1': range(10, 31, 5),    # 第1口: 10-30點，步長5
    'lot2': range(20, 51, 5),    # 第2口: 20-50點，步長5
    'lot3': range(30, 61, 5)     # 第3口: 30-60點，步長5
}
```

##### 修改停利範圍
```python
# 在 mdd_optimizer.py 中修改
self.take_profit_range = range(30, 101, 10)  # 30-100點，步長10
```

##### 修改時間區間
```python
# 在 mdd_optimizer.py 中修改
self.time_intervals = [
    ('10:30', '10:31'),
    ('11:30', '11:31'),
    ('12:30', '12:31'),
    ('14:30', '14:31')  # 新增時間區間
]
```

### 📈 輸出結果

#### 🆕 增強版結果文件
```
results/enhanced_mdd_results_[配置]_[時間戳].csv
```

#### 🆕 增強版結果分析
- **TOP 10 最小 MDD 配置**: 按 MDD 絕對值排序
- **TOP 10 風險調整收益**: 按 總收益/|MDD| 排序
- **實時進度顯示**: 顯示實驗進度和中間結果
- **配置詳情**: 包含每口停損、停利、時間區間完整信息

#### 🆕 最佳實踐結果示例
```
🏆 MDD最小 TOP 3:
1. MDD: -265.00 | 總P&L: 2850.00 | L1SL:15 L2SL:25 L3SL:35 | TP:60 | 12:00-12:01
2. MDD: -393.00 | 總P&L: 1832.00 | L1SL:12 L2SL:22 L3SL:31 | TP:65 | 12:30-12:31
3. MDD: -414.00 | 總P&L: 1687.00 | L1SL:12 L2SL:22 L3SL:28 | TP:70 | 12:30-12:31

💎 風險調整收益 TOP 3:
1. 風險調整收益: 10.75 | MDD: -265.00 | 總P&L: 2850.00
2. 風險調整收益:  4.66 | MDD: -393.00 | 總P&L: 1832.00
3. 風險調整收益:  4.65 | MDD: -502.00 | 總P&L: 2336.00
```

#### 原版結果文件
```
results/mdd_optimization_results_YYYYMMDD_HHMMSS.csv
results/mdd_visualization/mdd_vs_pnl_scatter.png
results/mdd_visualization/mdd_heatmap_lot1_lot2.png
```

---

## 🔬 參數優化實驗系統

### 📍 文件位置
```
rev_strategy_analysis/experiment_analysis/parameter_optimizer.py
rev_strategy_analysis/experiment_analysis/experiment_runner.py
```

### 🚀 使用方式

#### 基本實驗
```bash
cd rev_strategy_analysis/experiment_analysis

# 快速測試 (100個實驗)
python parameter_optimizer.py --sample-size 100

# 完整實驗 (432個實驗)
python parameter_optimizer.py
```

#### 進階實驗
```bash
# 帶可視化的實驗
python parameter_optimizer.py --create-charts

# 指定評估指標
python parameter_optimizer.py --metric "LONG_PNL"
```

### 🎯 實驗範圍

#### 第1口參數
```python
觸發點數: 10-30 點 (步長5)
回撤百分比: 10%-30% (步長5%)
```

#### 第2口參數  
```python
觸發點數: 30-40 點 (步長5)
回撤百分比: 10%-30% (步長5%)
```

#### 第3口參數
```python
觸發點數: 40-60 點 (步長5)  
回撤百分比: 10%-30% (步長5%)
```

### 🔧 參數修改方式

#### 修改實驗範圍
```python
# 在 parameter_optimizer.py 中修改
self.lot1_trigger_range = range(10, 31, 5)      # 第1口觸發點
self.lot1_pullback_range = range(10, 31, 5)     # 第1口回撤%
self.lot2_trigger_range = range(30, 41, 5)      # 第2口觸發點
self.lot2_pullback_range = range(10, 31, 5)     # 第2口回撤%
self.lot3_trigger_range = range(40, 61, 5)      # 第3口觸發點
self.lot3_pullback_range = range(10, 31, 5)     # 第3口回撤%
```

#### 修改評估指標
```python
# 可選指標
"TOTAL_PNL"     # 總損益
"LONG_PNL"      # 多頭損益
"SHORT_PNL"     # 空頭損益
"WIN_RATE"      # 勝率
"MAX_DRAWDOWN"  # 最大回撤
```

---

## ⏰ 時間區間實驗系統

### 📍 文件位置
```
rev_strategy_analysis/experiment_analysis/time_interval_optimizer.py
```

### 🚀 使用方式

#### 基本時間實驗
```bash
cd rev_strategy_analysis/experiment_analysis

# 測試不同時間區間
python time_interval_optimizer.py --intervals "10:30-10:31,11:30-11:31,12:30-12:31"

# 測試單一時間區間
python time_interval_optimizer.py --intervals "10:30-10:31"
```

### 🎯 實驗範圍

#### 預設時間區間
```python
時間區間選項:
- 10:30-10:31  # 早盤開盤
- 11:30-11:31  # 中午時段
- 12:30-12:31  # 午盤時段
- 13:30-13:31  # 下午開盤
- 14:30-14:31  # 尾盤時段
```

### 🔧 參數修改方式

#### 新增時間區間
```python
# 在 time_interval_optimizer.py 中修改
self.time_intervals = [
    ('09:30', '09:31'),  # 新增早盤
    ('10:30', '10:31'),
    ('11:30', '11:31'),
    ('12:30', '12:31'),
    ('13:30', '13:31'),
    ('14:30', '14:31'),
    ('15:30', '15:31')   # 新增尾盤
]
```

---

## 🎯 停損停利點實驗系統

### 📍 文件位置
```
rev_strategy_analysis/experiment_analysis/stop_loss_optimizer.py
rev_strategy_analysis/experiment_analysis/take_profit_optimizer.py
```

### 🚀 使用方式

#### 停損點實驗
```bash
cd rev_strategy_analysis/experiment_analysis

# 停損點優化 (15-100點，步長5)
python stop_loss_optimizer.py --range "15-100" --step 5

# 快速停損測試
python stop_loss_optimizer.py --sample-size 20
```

#### 停利點實驗
```bash
# 停利點優化 (30-100點，步長10)
python take_profit_optimizer.py --range "30-100" --step 10

# 快速停利測試  
python take_profit_optimizer.py --sample-size 15
```

### 🎯 實驗範圍

#### 停損點範圍
```python
停損點數: 15-100 點 (步長5點)
測試配置: 固定3口配置
時間區間: 10:30-10:31, 11:30-11:31, 12:30-12:31
```

#### 停利點範圍
```python
停利點數: 30-100 點 (步長10點)
測試配置: 固定3口配置
時間區間: 10:30-10:31, 11:30-11:31, 12:30-12:31
```

### 🔧 參數修改方式

#### 修改停損範圍
```python
# 在 stop_loss_optimizer.py 中修改
self.stop_loss_range = range(15, 101, 5)  # 15-100點，步長5
```

#### 修改停利範圍
```python
# 在 take_profit_optimizer.py 中修改  
self.take_profit_range = range(30, 101, 10)  # 30-100點，步長10
```

#### 修改測試配置
```python
# 固定配置設定
self.fixed_config = {
    'lot1_stop_loss': 20,
    'lot2_stop_loss': 30, 
    'lot3_stop_loss': 40,
    'time_interval': '11:30-11:31'
}
```

---

## 🏗️ 系統架構說明

### 📁 目錄結構
```
rev_strategy_analysis/
├── rev_web_trading_gui.py              # 主要GUI介面
├── rev_multi_Profit-Funded Risk_多口.py # 核心策略引擎
├── experiment_analysis/                 # 實驗分析系統
│   ├── mdd_optimizer.py                # MDD最小化優化
│   ├── mdd_backtest_engine.py          # MDD回測引擎
│   ├── parameter_optimizer.py          # 參數優化系統
│   ├── stop_loss_optimizer.py          # 停損點優化
│   ├── take_profit_optimizer.py        # 停利點優化
│   ├── time_interval_optimizer.py      # 時間區間優化
│   ├── experiment_runner.py            # 實驗執行器
│   ├── test_mdd_optimizer.py           # 系統測試
│   └── results/                        # 實驗結果目錄
│       ├── mdd_optimization_results_*.csv
│       ├── parameter_optimization_results_*.csv
│       └── mdd_visualization/          # 可視化圖表
└── reports/                            # 回測報告目錄
```

### 🔄 系統流程

#### 1. GUI回測流程
```
用戶設定參數 → rev_web_trading_gui.py → 核心策略引擎 → 生成報告
```

#### 2. 實驗優化流程
```
實驗配置 → 參數組合生成 → 批量回測 → 結果分析 → 可視化輸出
```

#### 3. 數據流向
```
歷史數據 → 策略引擎 → 交易信號 → 損益計算 → 統計分析 → 報告生成
```

### 🎯 核心組件

#### 策略引擎
- **文件**: `rev_multi_Profit-Funded Risk_多口.py`
- **功能**: 反向策略邏輯、三口交易管理、風險控制

#### GUI介面
- **文件**: `rev_web_trading_gui.py`  
- **功能**: 參數設定、回測執行、報告展示

#### 實驗系統
- **目錄**: `experiment_analysis/`
- **功能**: 批量測試、參數優化、結果分析

---

## 🎊 使用建議

### 🔰 新手入門
1. **先使用GUI**: 熟悉基本回測功能
2. **快速實驗**: 使用小樣本測試各種實驗系統
3. **參數調整**: 根據結果調整參數範圍
4. **完整優化**: 運行完整實驗找出最佳配置

### 🎯 進階使用
1. **組合實驗**: 結合多個實驗系統
2. **自定義範圍**: 修改參數範圍針對性優化
3. **結果分析**: 深入分析實驗數據
4. **實戰驗證**: 將實驗結果應用到GUI回測

### 📊 性能優化
1. **並行處理**: 大型實驗使用多進程
2. **樣本測試**: 先用小樣本驗證邏輯
3. **結果緩存**: 避免重複計算
4. **資源監控**: 注意內存和CPU使用

---

## 🆕 用戶自定義 MDD 配置使用指南

### 📋 配置詳情
根據你的需求，已創建專門的 `user_custom` 配置：

#### 參數範圍
```python
各口停損範圍: [15, 20, 25, 30, 45, 50, 55, 60, 65, 70] 點
統一停利範圍: [40, 50, 60, 70, 80] 點
時間區間: 10:00-10:02, 10:30-10:32, 11:00-11:02,
         11:30-11:32, 12:00-12:02, 12:30-12:32, 13:00-13:02
```

#### 組合數量
- **統一停利模式**: 35,000 個組合
- **獨立停利模式**: 875,000 個組合

### 🚀 執行步驟

#### 第一步：系統測試
```bash
cd rev_strategy_analysis/experiment_analysis

# 測試配置是否正常
python test_user_custom_config.py
```

#### 第二步：小樣本測試
```bash
# 快速測試 100 個樣本
python enhanced_mdd_optimizer.py --config user_custom --sample-size 100
```

#### 第三步：中等規模實驗
```bash
# 測試 500 個樣本
python enhanced_mdd_optimizer.py --config user_custom --sample-size 500
```

#### 第四步：大規模實驗
```bash
# 測試 2000 個樣本（統一停利）
python enhanced_mdd_optimizer.py --config user_custom --sample-size 2000

# 測試 1000 個樣本（獨立停利）
python enhanced_mdd_optimizer.py --config user_custom --individual-tp --sample-size 1000

# 測試找出個區間最佳解
python enhanced_mdd_optimizer.py --config time_interval_analysis --max-workers 4
```

### 📊 結果分析

#### 關鍵指標
1. **MDD (最大回撤)**: 目標 < -500 點
2. **風險調整收益**: 目標 > 3.0
3. **總P&L**: 參考指標

#### 預期結果格式
```
🏆 MDD最小 TOP 10:
1. MDD: -XXX.XX | 總P&L: XXXX.XX | L1SL:XX L2SL:XX L3SL:XX | TP:XX | 時間區間
...

💎 風險調整收益 TOP 10:
1. 風險調整收益: X.XX | MDD: -XXX.XX | 總P&L: XXXX.XX | 配置詳情
...
```

### 🎯 參數調整建議

#### 如需修改參數範圍
```python
# 編輯 mdd_search_config.py 中的 get_user_custom_search_config()
'stop_loss_ranges': {
    'lot1': [你的第1口停損範圍],
    'lot2': [你的第2口停損範圍],
    'lot3': [你的第3口停損範圍]
},
'take_profit_ranges': {
    'unified': [你的停利範圍]
},
'time_intervals': [
    ("開始時間", "結束時間"),
    # 更多時間區間...
]
```

### ⚡ 執行建議

1. **先小後大**: 從 100 樣本開始，確認系統正常
2. **並行執行**: 可同時運行多個不同樣本數的實驗
3. **結果比較**: 對比不同樣本數的結果一致性
4. **GUI驗證**: 將最佳配置在GUI中手動驗證

---

**📖 詳細文檔**: 各系統都有對應的詳細使用指南，請參考相應的README和GUIDE文件。
