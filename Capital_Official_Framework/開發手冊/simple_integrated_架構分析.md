# simple_integrated.py 策略下單機宏觀架構分析

## 1. 核心目的 (Core Purpose)

`simple_integrated.py` 是一個在 Windows 系統上運行的**自動化交易策略執行系統**，主要用於：

- **期貨自動交易**：連接群益證券 API 進行台指期貨自動下單
- **開盤區間突破策略**：實現基於開盤區間突破的交易策略
- **多組策略管理**：支援多組策略同時運行，提供風險分散
- **實時監控與風控**：提供即時報價監控、部位管理和風險控制

**解決的核心問題**：
- 自動化執行複雜的期貨交易策略
- 降低人工操作錯誤和情緒干擾
- 提供穩定的策略執行環境和完整的交易記錄

## 2. 主要功能模塊 (Key Functional Blocks)

### 2.1 系統登入與連線模塊
- **群益 API 登入**：處理身分證字號/密碼登入
- **下單模組初始化**：初始化 SKOrderLib 和憑證讀取
- **報價連線管理**：建立即時報價連線和商品訂閱

### 2.2 訊號生成模塊
- **開盤區間計算**：在指定時間區間（預設 08:46-08:48）計算高低點
- **突破訊號檢測**：監控價格突破區間上下邊界
- **分鐘 K 線處理**：處理即時報價數據並生成交易訊號

### 2.3 部位管理模塊
- **多組策略部位管理**：`MultiGroupPositionManager` 管理多個策略組
- **單一策略部位追蹤**：追蹤個別部位的進場、出場狀態
- **部位狀態同步**：與資料庫同步部位資訊

### 2.4 訂單執行模塊
- **虛實單整合系統**：`VirtualRealOrderManager` 支援虛擬/實際下單切換
- **統一回報追蹤**：`UnifiedOrderTracker` 處理下單回報
- **簡化追蹤器**：`SimplifiedOrderTracker` 提供 FIFO 訂單追蹤

### 2.5 風險控制模塊
- **初始停損**：基於區間邊界的停損機制
- **移動停利**：動態調整停利點位
- **收盤平倉**：13:30 自動平倉功能
- **風險管理引擎**：`RiskManagementEngine` 統一風險控制

### 2.6 用戶介面模塊
- **主控制面板**：登入、連線、下單控制
- **策略監控面板**：策略狀態、區間結果顯示
- **多組策略配置**：策略參數設定和狀態監控
- **日誌系統**：系統日誌和策略日誌分離顯示

## 3. 技術堆疊 (Tech Stack)

### 3.1 核心 Python 函式庫
```python
import tkinter as tk          # GUI 框架
from tkinter import ttk       # 進階 GUI 組件
import sqlite3               # 本地資料庫
import comtypes.client       # COM 組件操作（群益 API）
from datetime import datetime # 時間處理
import time                  # 時間相關功能
```

### 3.2 群益證券 API
```python
import Global                # 群益全域設定
from user_config import get_user_config  # 使用者配置
import comtypes.gen.SKCOMLib as sk       # 群益 COM 介面
```

### 3.3 自定義交易模組
```python
# 多組策略系統
from multi_group_database import MultiGroupDatabaseManager
from multi_group_position_manager import MultiGroupPositionManager
from unified_exit_manager import UnifiedExitManager
from risk_management_engine import RiskManagementEngine

# 虛實單整合系統
from virtual_real_order_manager import VirtualRealOrderManager
from unified_order_tracker import UnifiedOrderTracker

# 報價與風險管理
from real_time_quote_manager import RealTimeQuoteManager
from optimized_risk_manager import create_optimized_risk_manager
```

### 3.4 資料庫與日誌系統
```python
from database.sqlite_manager import SQLiteManager
from multi_group_console_logger import get_logger, LogCategory
```

## 4. 假設的執行流程 (Hypothetical Flow)

### 4.1 系統啟動階段
1. **初始化應用程式**
   - 載入使用者配置（帳號、密碼、商品代碼）
   - 初始化 GUI 介面和各種管理器
   - 設定報價頻率控制器（預設 500ms 間隔）

2. **模組載入檢查**
   - 檢查多組策略系統可用性
   - 檢查虛實單整合系統可用性
   - 檢查優化風險管理器可用性
   - 根據可用性決定功能啟用狀態

### 4.2 連線與登入階段
3. **群益 API 登入**
   ```
   使用者輸入身分證字號/密碼 → SKCenterLib_Login() → 
   設定 LOG 路徑 → 註冊回報事件處理器
   ```

4. **下單模組初始化**
   ```
   SKOrderLib_Initialize() → ReadCertByID() → 
   啟用測試下單功能
   ```

5. **報價連線建立**
   ```
   連線報價伺服器 → 訂閱指定商品（MTX00/TM0000）→ 
   啟動即時報價接收
   ```

### 4.3 策略執行階段
6. **策略監控啟動**
   - 啟動開盤區間突破策略監控
   - 設定監控時間區間（預設 08:46-08:48）
   - 初始化多組策略系統（如果啟用）

7. **區間計算階段**
   ```
   監控指定時間區間 → 收集價格數據 → 
   計算區間高低點 → 準備突破監控
   ```

8. **突破訊號檢測**
   ```
   即時監控價格 → 檢測突破區間邊界 → 
   生成 LONG/SHORT 訊號 → 觸發下單邏輯
   ```

### 4.4 交易執行階段
9. **多筆下單執行**
   ```
   接收突破訊號 → 執行多筆 1 口 FOK 下單 → 
   註冊到統一回報追蹤器 → 等待成交回報
   ```

10. **部位管理與風控**
    ```
    監控部位狀態 → 檢查停損/停利條件 → 
    執行出場邏輯 → 更新部位狀態
    ```

### 4.5 風險控制與出場
11. **即時風險監控**
    - 初始停損：價格跌破區間邊界
    - 移動停利：獲利 15 點後啟動 20% 回撤停利
    - 收盤平倉：13:30 強制平倉（可選）

12. **回報處理與追價**
    ```
    接收 API 回報 → 解析委託狀態 → 
    處理未成交訂單 → 執行追價邏輯（如需要）
    ```

### 4.6 系統維護階段
13. **日誌記錄與監控**
    - Console 模式輸出詳細執行日誌
    - GUI 顯示重要狀態更新
    - 資料庫記錄完整交易歷史

14. **系統關閉**
    - 停止策略監控
    - 斷開報價連線
    - 保存系統狀態和日誌

## 5. 關鍵設計特點

### 5.1 安全性設計
- **Console 模式優先**：避免 GUI 更新造成的 GIL 問題
- **回報過濾機制**：防止歷史回報干擾當前交易
- **多重風險控制**：初始停損 + 移動停利 + 收盤平倉

### 5.2 模組化架構
- **可選模組載入**：根據模組可用性動態啟用功能
- **統一介面設計**：虛實單切換、多組策略管理
- **向後相容性**：保留舊版功能作為備用方案

### 5.3 性能優化
- **報價頻率控制**：預設 500ms 間隔避免過度處理
- **異步處理機制**：峰值更新、部位填充等異步處理
- **智能監控**：定期狀態檢查而非即時更新

這個系統代表了一個成熟的自動化交易平台，整合了策略執行、風險管理、部位追蹤等完整功能，適合專業交易者使用。
