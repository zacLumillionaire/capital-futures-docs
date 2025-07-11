# 策略模組診斷指南
## Strategy Module Diagnosis Guide

**目的**: 詳細診斷策略模組載入失敗的原因  
**方法**: 使用新增的診斷按鈕和詳細日誌  
**日期**: 2025-07-01

---

## 🔍 如何使用診斷功能

### 步驟1: 啟動OrderTester.py
```bash
cd "Python File"
python OrderTester.py
```

### 步驟2: 查看策略交易標籤頁
- 如果策略模組載入失敗，您會看到錯誤頁面
- 錯誤頁面現在包含一個綠色的診斷按鈕

### 步驟3: 點擊診斷按鈕
- 點擊「🔍 開始診斷策略模組問題」按鈕
- 系統會自動進行詳細檢查
- 所有診斷資訊會顯示在頁面上的日誌區域
- 同時也會輸出到VS Code終端

### 步驟4: 查看診斷結果
診斷會檢查以下項目：
1. **基本環境**: Python版本、當前目錄
2. **strategy資料夾**: 是否存在、內容列表
3. **策略模組導入**: 測試三個版本的策略面板
4. **依賴模組**: 檢查所有必要的依賴
5. **總結建議**: 提供具體的解決建議

---

## 📊 診斷項目詳解

### 1. 基本環境檢查
```
✓ Python版本: 3.x.x
✓ 當前目錄: /path/to/project
✓ Python路徑: /path/to/python
```

### 2. strategy資料夾檢查
```
✓ strategy資料夾存在: /full/path
✓ strategy資料夾內容: ['__init__.py', 'strategy_panel.py', ...]
```

### 3. 策略模組導入測試
```
測試完整版策略面板...
✓/✗ 完整版策略面板導入成功/失敗: 錯誤詳情

測試簡化版策略面板...
✓/✗ 簡化版策略面板導入成功/失敗: 錯誤詳情

測試最簡化版策略面板...
✓/✗ 最簡化版策略面板導入成功/失敗: 錯誤詳情
```

### 4. 依賴模組檢查
```
✓/✗ tkinter: 可用/失敗
✓/✗ 資料庫管理: 可用/失敗
✓/✗ 時間工具: 可用/失敗
✓/✗ 策略配置: 可用/失敗
✓/✗ 信號檢測: 可用/失敗
```

### 5. 診斷總結
根據檢查結果，系統會提供具體建議：
- 如果完整版可用：建議重新啟動
- 如果簡化版可用：建議使用簡化版
- 如果最簡化版可用：建議使用最簡化版
- 如果都不可用：建議檢查環境

---

## 🛠️ 常見問題和解決方案

### 問題1: strategy資料夾不存在
**症狀**: `✗ strategy資料夾不存在`
**解決**: 檢查是否在正確的目錄中運行OrderTester.py

### 問題2: 完整版策略面板導入失敗
**症狀**: `✗ 完整版策略面板導入失敗: ModuleNotFoundError`
**解決**: 檢查依賴模組，可能需要使用簡化版

### 問題3: 所有策略面板都無法導入
**症狀**: 三個版本都顯示導入失敗
**解決**: 檢查Python環境和基本依賴

### 問題4: tkinter不可用
**症狀**: `✗ tkinter: 失敗`
**解決**: 重新安裝Python或安裝tkinter

### 問題5: 資料庫模組失敗
**症狀**: `✗ 資料庫管理: 失敗`
**解決**: 檢查database資料夾和sqlite3

---

## 📝 診斷日誌示例

### 成功案例
```
[14:30:15] 開始策略模組診斷...
[14:30:15] 1. 檢查基本環境:
[14:30:15]    Python版本: 3.11.0
[14:30:15]    當前目錄: C:\...\Python File
[14:30:15] 2. 檢查strategy資料夾:
[14:30:15]    ✓ strategy資料夾存在
[14:30:15]    strategy資料夾內容: ['__init__.py', 'strategy_panel.py', ...]
[14:30:15] 3. 測試策略模組導入:
[14:30:15]    ✓ 完整版策略面板導入成功
[14:30:15] 4. 檢查依賴模組:
[14:30:15]    ✓ tkinter: 可用
[14:30:15]    ✓ 資料庫管理: 可用
[14:30:15] 5. 診斷總結:
[14:30:15]    ✓ 完整版策略面板可用 - 應該能正常工作
[14:30:15] 診斷完成！
```

### 失敗案例
```
[14:30:15] 開始策略模組診斷...
[14:30:15] 1. 檢查基本環境:
[14:30:15]    Python版本: 3.11.0
[14:30:15] 2. 檢查strategy資料夾:
[14:30:15]    ✓ strategy資料夾存在
[14:30:15] 3. 測試策略模組導入:
[14:30:15]    ✗ 完整版策略面板導入失敗: ImportError: No module named 'database'
[14:30:15]    ✗ 簡化版策略面板導入失敗: ImportError: No module named 'database'
[14:30:15]    ✓ 最簡化版策略面板導入成功
[14:30:15] 4. 檢查依賴模組:
[14:30:15]    ✓ tkinter: 可用
[14:30:15]    ✗ 資料庫管理: 失敗 - No module named 'database'
[14:30:15] 5. 診斷總結:
[14:30:15]    ✓ 最簡化版策略面板可用 - 最基本功能可用
[14:30:15] 診斷完成！
```

---

## 🎯 下一步行動

### 根據診斷結果採取行動

1. **如果完整版可用**:
   - 重新啟動OrderTester.py
   - 應該能看到完整的策略功能

2. **如果只有簡化版可用**:
   - 可以使用基本策略功能
   - 考慮修復完整版的依賴問題

3. **如果只有最簡化版可用**:
   - 可以使用最基本的策略功能
   - 需要修復其他版本的問題

4. **如果都不可用**:
   - 檢查Python環境
   - 重新安裝必要的模組
   - 檢查檔案完整性

---

## 💡 使用提示

### 診斷最佳實踐
1. **完整記錄**: 將診斷日誌完整複製給開發者
2. **多次測試**: 如果修復後，重新運行診斷確認
3. **環境檢查**: 注意Python版本和路徑
4. **依賴追蹤**: 特別注意哪些依賴模組失敗

### VS Code終端查看
- 診斷資訊會同時輸出到VS Code終端
- 搜尋「策略診斷:」來找到相關日誌
- 可以複製終端內容進行分析

---

## 🔧 現在就開始診斷！

1. **啟動OrderTester.py**
2. **切換到策略交易標籤頁**
3. **點擊診斷按鈕**
4. **查看詳細診斷結果**
5. **根據建議採取行動**

**這個診斷工具會幫助我們找到確切的問題所在！** 🎯🔍
