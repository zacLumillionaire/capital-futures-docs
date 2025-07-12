# 策略回測分析工具

一個完整的交易策略分析工具，專為分析 `multi_Profit-Funded Risk_多口.py` 的回測結果而設計。

## 🎯 功能特色

- **📊 日誌解析**: 自動解析回測程式的日誌輸出，提取交易事件和損益資料
- **📈 統計分析**: 計算完整的績效指標，包含基本指標、風險指標、口數分析等
- **📊 視覺化圖表**: 生成多種分析圖表，包含每日損益、資金曲線、分布圖等
- **📋 報告生成**: 自動生成包含圖表和統計數據的HTML報告
- **🔧 模組化設計**: 各功能模組獨立，易於擴展和維護

## 📁 專案結構

```
strategy_analysis/
├── backtest_analyzer.py          # 主分析程式
├── data_extractor.py             # 日誌解析器
├── statistics_calculator.py      # 統計計算器
├── visualization.py              # 視覺化工具
├── report_generator.py           # 報告生成器
├── config.py                     # 設定檔
├── utils.py                      # 工具函數
├── sample_log_data.py            # 範例日誌資料
├── requirements.txt              # 依賴套件
├── data/                         # 資料目錄
│   ├── processed/                # 處理後資料
│   └── reports/                  # 分析報告
├── charts/                       # 圖表輸出
└── multi_Profit-Funded Risk_多口.py  # 複製的回測程式
```

## 🚀 快速開始

### 1. 安裝依賴套件

```bash
pip install -r requirements.txt
```

### 2. 執行分析

#### 使用範例資料（推薦用於測試）
```bash
python backtest_analyzer.py --sample
```

#### 使用實際回測程式
```bash
python backtest_analyzer.py
```

### 3. 查看結果

分析完成後會生成：
- **HTML報告**: `data/reports/strategy_analysis_report.html`
- **圖表檔案**: `charts/` 目錄下的各種PNG圖表
- **處理後資料**: `data/processed/` 目錄下的CSV和JSON檔案

## 📊 分析內容

### 基本績效指標
- 總損益、平均損益
- 勝率、獲利因子
- 最大獲利/虧損
- 交易次數統計

### 風險指標
- 最大回撤
- 夏普比率、索提諾比率
- 波動率
- 連續虧損分析

### 口數分析
- 各口單表現
- 移動停利效果
- 保護性停損統計

### 視覺化圖表
- 每日損益分析
- 資金曲線圖
- 損益分布圖
- 口數貢獻圖
- 月度績效圖
- 回撤分析圖
- 多空方向分析
- 互動式儀表板

## 🔧 模組說明

### data_extractor.py
負責解析回測程式的日誌輸出，提取交易事件和每日損益資料。

**主要功能**:
- 執行回測程式並捕獲日誌
- 解析各種交易事件（進場、出場、移動停利等）
- 建立結構化的交易資料

### statistics_calculator.py
計算各種統計指標和績效分析。

**主要功能**:
- 基本績效指標計算
- 風險指標計算
- 交易分析和口數分析
- 時間序列分析

### visualization.py
生成各種分析圖表。

**主要功能**:
- 每日損益圖表
- 資金曲線和回撤分析
- 損益分布圖
- 口數貢獻分析
- 互動式圖表

### report_generator.py
生成包含圖表和統計數據的HTML報告。

**主要功能**:
- HTML報告模板
- 圖表嵌入
- 統計數據整合
- 交易明細表格

## ⚙️ 設定選項

在 `config.py` 中可以調整：

- **分析參數**: 無風險利率、交易日數、初始資金等
- **圖表設定**: 圖表大小、顏色、字體等
- **報告設定**: 報告標題、輸出格式等
- **日誌模式**: 日誌等級和格式

## 📝 使用範例

### 基本使用
```python
from backtest_analyzer import BacktestAnalyzer

# 建立分析器
analyzer = BacktestAnalyzer(use_sample_data=True)

# 執行完整分析
report_file = analyzer.run_complete_analysis()

print(f"報告已生成: {report_file}")
```

### 單獨使用各模組
```python
# 只提取資料
from data_extractor import extract_from_sample_data
events_df, daily_df = extract_from_sample_data()

# 只計算統計
from statistics_calculator import calculate_strategy_statistics
statistics = calculate_strategy_statistics(daily_df, events_df)

# 只生成圖表
from visualization import create_all_visualizations
chart_files = create_all_visualizations(daily_df, events_df, statistics)
```

## 🐛 故障排除

### 常見問題

1. **中文字體警告**
   - 這是正常現象，不影響圖表生成
   - 可以安裝中文字體來解決

2. **回測程式執行失敗**
   - 檢查資料庫連線設定
   - 使用 `--sample` 參數測試工具功能

3. **記憶體不足**
   - 對於大量資料，可以調整批次處理大小
   - 關閉不需要的圖表生成

### 日誌檢查
查看 `analysis.log` 檔案了解詳細的執行過程和錯誤訊息。

## 🔄 擴展功能

工具採用模組化設計，易於擴展：

- **新增指標**: 在 `statistics_calculator.py` 中添加新的計算函數
- **新增圖表**: 在 `visualization.py` 中添加新的圖表類型
- **自訂報告**: 修改 `report_generator.py` 中的HTML模板
- **新增資料源**: 擴展 `data_extractor.py` 支援其他格式

## 📄 授權

本專案僅供學習和研究使用。

## 🤝 貢獻

歡迎提出建議和改進意見！
