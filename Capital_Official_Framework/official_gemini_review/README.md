# 程式碼審查資料夾

## 📋 概述

此資料夾包含 simple_integrated.py 及其相關測試環境的完整程式碼快照，用於程式碼審查。

## 📊 統計資訊

- **創建時間**: 2025-07-16 22:35:09
- **成功複製**: 146 個檔案
- **複製失敗**: 0 個檔案  
- **跳過檔案**: 0 個檔案

## 📁 資料夾結構

```
official_gemini_review/
├── README.md                           # 本說明文件
├── update_review_folder.py             # 更新腳本
├── root_files/                         # 根目錄檔案
│   ├── id_consistency_verifier.py      # ID一致性驗證器
│   ├── 平倉問題診斷工具.py              # 平倉問題診斷工具
│   └── ...                             # 其他診斷工具
├── simple_integrated.py                # 主程式（正式機）
├── virtual_simple_integrated.py        # 主程式（測試機）
├── 虛擬報價機/                         # 虛擬報價機完整資料夾
│   ├── Global.py                       # 虛擬API模組
│   ├── config.json                     # 報價配置
│   └── ...                             # 其他虛擬報價機檔案
├── multi_group_*.py                    # 多組策略系統模組
├── optimized_risk_manager.py           # 優化風險管理器
├── simplified_order_tracker.py         # 簡化追蹤器
├── stop_loss_executor.py               # 停損執行器
├── *.db                                # 資料庫檔案
└── ...                                 # 其他相關模組
```

## 🔧 使用方法

### 更新程式碼快照
```bash
python update_review_folder.py
```

### 主要檔案說明

1. **主程式**
   - `simple_integrated.py`: 正式機主程式
   - `virtual_simple_integrated.py`: 測試機主程式（使用虛擬報價機）

2. **核心模組**
   - `multi_group_*.py`: 多組策略系統
   - `optimized_risk_manager.py`: 優化風險管理
   - `simplified_order_tracker.py`: 簡化追蹤器
   - `stop_loss_executor.py`: 停損執行器

3. **虛擬報價機**
   - `虛擬報價機/`: 完整的虛擬報價機系統
   - 支援多種測試場景配置

4. **診斷工具**
   - `root_files/`: 各種診斷和驗證工具
   - 用於系統健康檢查和問題排查

## 📝 注意事項

- 此為程式碼快照，不包含執行時產生的日誌檔案
- 資料庫檔案(.db)包含測試資料，可用於分析
- 虛擬報價機可獨立運行，用於測試環境

## 🚀 快速開始

1. 查看主程式架構: `simple_integrated.py`
2. 了解虛擬測試環境: `virtual_simple_integrated.py`
3. 檢查診斷工具: `root_files/` 目錄
4. 運行系統驗證: `final_fixed_verification.py`
