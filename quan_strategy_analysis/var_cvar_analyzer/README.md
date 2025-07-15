# VaR/CVaR 風險分析器

## 📋 專案概述

本專案實現了一個完整的 VaR (風險價值) 和 CVaR (條件風險價值) 分析系統，用於評估交易策略的風險特徵。系統能夠：

1. **數據獲取**：從現有的回測引擎中提取每日損益數據
2. **風險計算**：計算 VaR 和 CVaR 風險指標
3. **報告生成**：生成詳細的風險分析報告
4. **視覺化**：創建損益分佈圖表，直觀展示風險指標

## 📁 檔案結構

```
var_cvar_analyzer/
├── var_cvar_analyzer.py      # 主分析程式
├── strategy_core.py          # 策略核心模組（從 future_path_analyzer 複製）
├── test_var_cvar.py          # 測試腳本
├── README.md                 # 本說明文件
└── var_cvar_reports/         # 分析報告輸出目錄（自動創建）
    ├── var_cvar_analysis_YYYYMMDD_HHMMSS.png
    └── var_cvar_report_YYYYMMDD_HHMMSS.txt
```

## 🔧 核心功能

### 1. 數據獲取 (`get_historical_pnls`)
- 從策略回測引擎中提取每日損益列表
- 支援自定義日期範圍
- 靜默模式減少日誌輸出

### 2. VaR 計算 (`calculate_var`)
- 計算指定信心水準下的風險價值
- 預設 95% 信心水準
- 使用百分位數方法

### 3. CVaR 計算 (`calculate_cvar`)
- 計算條件風險價值（預期損失）
- 基於 VaR 值計算極端損失的平均值
- 提供更保守的風險估計

### 4. 報告生成 (`print_risk_report`)
- 生成詳細的風險分析報告
- 包含風險指標解讀和統計資訊
- 提供實用的風險管理建議

### 5. 視覺化 (`create_risk_visualization`)
- 繪製損益分佈直方圖
- 標示 VaR、CVaR 和平均值線
- 支援圖片保存和顯示

## 🚀 使用方法

### 基本使用

1. **執行主程式**：
   ```bash
   cd /Users/z/big/my-capital-project/quan_strategy_analysis/var_cvar_analyzer
   python var_cvar_analyzer.py
   ```

2. **執行測試**：
   ```bash
   python test_var_cvar.py
   ```

### 自定義配置

您可以修改 `var_cvar_analyzer.py` 中的策略配置：

```python
config = StrategyConfig(
    trade_size_in_lots=3,  # 交易口數
    stop_loss_type=StopLossType.RANGE_BOUNDARY,
    lot_rules=[
        # 自定義口數規則
        LotRule(
            use_trailing_stop=True,
            trailing_activation=Decimal('15'),  # 觸發點
            trailing_pullback=Decimal('0.10')   # 回撤百分比
        ),
        # ... 更多口數規則
    ],
    range_filter=RangeFilter(
        use_range_size_filter=True,
        max_range_points=Decimal('160')  # 區間過濾
    )
)
```

### 自定義分析期間

修改主程式中的日期範圍：

```python
start_date = "2024-11-04"  # 開始日期
end_date = "2025-06-28"    # 結束日期
```

## 📊 輸出說明

### 1. 控制台輸出
- 執行進度和狀態資訊
- 詳細的風險分析報告
- 風險管理建議

### 2. 視覺化圖表 (PNG)
- 每日損益分佈直方圖
- VaR 和 CVaR 標示線
- 平均值參考線

### 3. 文字報告 (TXT)
- 完整的分析結果
- 策略配置資訊
- 基本統計數據

## 🧮 風險指標解讀

### VaR (風險價值)
- **定義**：在給定信心水準下，預期的最大損失
- **解讀**：95% VaR = -50 點表示有 95% 的信心，單日損失不會超過 50 點
- **頻率**：平均每 20 個交易日可能有 1 天超過此損失

### CVaR (條件風險價值)
- **定義**：超過 VaR 閾值時的平均損失
- **解讀**：更保守的風險估計，考慮極端情況的嚴重程度
- **用途**：風險管理和資本配置的重要參考

## ⚙️ 技術要求

### 依賴套件
- `numpy`：數值計算
- `matplotlib`：圖表繪製
- `seaborn`：統計視覺化
- `decimal`：精確數值計算

### 系統要求
- Python 3.8+
- 可訪問的 SQLite 或 PostgreSQL 數據庫
- 足夠的歷史交易數據

## 🔍 故障排除

### 常見問題

1. **無法獲取損益數據**
   - 檢查數據庫連接
   - 確認日期範圍內有交易數據
   - 驗證策略配置正確性

2. **視覺化失敗**
   - 確認已安裝 matplotlib 和 seaborn
   - 檢查圖形顯示環境
   - 嘗試在有 GUI 的環境中運行

3. **計算結果異常**
   - 檢查損益數據的有效性
   - 確認信心水準設定合理 (0.9-0.99)
   - 驗證數據量是否足夠

### 調試模式

將主程式中的 `silent=True` 改為 `silent=False` 可以看到詳細的回測日誌。

## 📈 擴展功能

### 可能的改進方向

1. **多信心水準分析**：同時計算多個信心水準的風險指標
2. **滾動窗口分析**：分析風險指標的時間變化
3. **壓力測試**：模擬極端市場條件下的風險
4. **風險歸因分析**：分析不同因素對風險的貢獻
5. **組合風險分析**：多策略組合的風險評估

### 整合建議

- 與現有的批量實驗系統整合
- 加入自動化風險監控
- 建立風險預警機制
- 與交易執行系統連接

## 📞 支援

如有問題或建議，請聯繫量化策略分析團隊。

---

**最後更新**：2025-07-14  
**版本**：1.0.0
