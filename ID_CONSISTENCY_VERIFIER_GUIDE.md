# ID一致性自動驗證器使用指南

## 專案概述

ID一致性自動驗證器是一個靜態程式碼分析工具，專門用於檢測交易系統中 `group_id` 與 `position_id` 的使用一致性問題。此工具使用 Python 的 AST (Abstract Syntax Tree) 模組，能夠精確地分析程式碼結構，而無需實際執行程式碼。

## 功能特點

- **自動遍歷**: 自動找到並分析專案中的所有 Python 檔案
- **靜態分析**: 使用 AST 進行靜態分析，無需執行程式碼
- **多種檢測**: 檢測多種 ID 使用不一致的情況
- **詳細報告**: 生成人類可讀的詳細報告
- **分類整理**: 按檔案和問題類型組織結果

## 檢測的問題類型

1. **模糊變數** (`模糊變數`): 
   - 使用模糊的變數名稱如 `group_id`, `position_id`, `id`, `group`, `position`
   - 建議使用更明確的名稱如 `group_pk`, `logical_group_id`, `position_pk`, `position_logical_id`

2. **函式簽名模糊** (`函式簽名模糊`): 
   - 函式參數使用模糊的名稱
   - 例如: `def process_order(group_id, position_id):`
   - 建議: `def process_order(group_pk, position_logical_id):`

3. **模糊字典鍵** (`模糊字典鍵`): 
   - 字典中使用模糊的鍵名
   - 例如: `data['id']`, `position['group_id']`
   - 建議: `data['position_pk']`, `position['logical_group_id']`

4. **SQL查詢不規範** (`SQL查詢不規範`): 
   - SQL查詢中未使用 AS 重命名
   - 例如: `SELECT id, group_id FROM positions`
   - 建議: `SELECT id AS position_pk, group_id AS logical_group_id FROM positions`

5. **SQL條件模糊** (`SQL條件模糊`): 
   - WHERE 子句中使用模糊的條件
   - 例如: `WHERE group_id = ?`
   - 建議: `WHERE logical_group_id = ?`

## 使用方法

### 基本使用

```bash
python id_consistency_verifier.py [目錄路徑]
```

如果未指定目錄，預設會分析 `Capital_Official_Framework` 目錄。

### 輸出說明

腳本執行後會在終端顯示分析結果，並生成一個報告文件 `id_consistency_report_X_issues.txt`，其中 X 是發現的問題數量。

報告格式範例:

```
--- ID Consistency Verification Report ---

Scanning file: /path/to/your/project/multi_group_position_manager.py
  [模糊變數] (120 issues):
    - L_152: 發現潛在的模糊變數 'group_id'。建議使用更明確的名稱，如 group_pk, logical_group_id, position_pk, position_logical_id
    - L_210: 發現潛在的模糊變數 'position_id'。建議使用更明確的名稱，如 group_pk, logical_group_id, position_pk, position_logical_id
    ...
  
  [函式簽名模糊] (15 issues):
    - L_210: 函式 'process_group' 使用了模糊參數 'group_id'。建議使用更明確的名稱，如 group_pk, logical_group_id, position_pk, position_logical_id
    ...

  [SQL查詢不規範] (5 issues):
    - L_88: SELECT查詢未對 'id', 'group_id', 或 'position_id' 使用 AS 進行重命名。建議使用 AS 明確指定列名
    ...

Found 140 potential issues across 3 files.

📋 Recommendations:
1. 重構前運行：執行此腳本獲取「問題清單」，作為重構的目標
2. 重構後運行：再次執行腳本，如果報告為空則證明重構成功且完整
3. 優先處理：函式簽名模糊 > 模糊變數 > SQL查詢不規範 > 模糊字典鍵
4. 建議命名：使用 group_pk, logical_group_id, position_pk, position_logical_id
```

## 建議使用流程

1. **重構前運行**:
   - 執行此腳本獲取「問題清單」
   - 將此清單作為重構的目標和指南

2. **重構過程**:
   - 優先處理函式簽名，因為這會影響API設計
   - 其次處理變數命名，確保一致性
   - 最後處理SQL查詢和字典鍵

3. **重構後運行**:
   - 再次執行腳本
   - 如果報告為空（Found 0 potential issues），則證明重構成功且完整

4. **持續整合**:
   - 考慮將此腳本加入到CI/CD流程中
   - 作為程式碼品質檢查的一部分

## 命名建議

為確保ID命名的一致性，建議使用以下命名規範:

- `group_pk`: 用於資料庫主鍵
- `logical_group_id`: 用於業務邏輯識別符
- `position_pk`: 用於資料庫主鍵
- `position_logical_id`: 用於業務邏輯識別符

## 技術說明

此工具使用 Python 的 `ast` 模組進行靜態程式碼分析。AST (Abstract Syntax Tree) 可以將 Python 程式碼解析成一個結構化的節點樹，讓我們可以精確地檢查變數名、函式參數、字串內容等，這遠比單純的文本搜索或正則表達式要強大和準確。

## 注意事項

- 此工具僅進行靜態分析，不會執行任何程式碼
- 分析結果僅供參考，最終的命名決策應由開發團隊決定
- 某些特殊情況下，使用 `id`, `group_id` 等名稱可能是合理的，請根據實際情況判斷
