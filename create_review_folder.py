#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
創建程式碼審查資料夾 - 複製所有必要檔案到 official_gemini_review 資料夾
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def should_exclude_file(file_path):
    """檢查檔案是否應該被排除"""
    file_name = os.path.basename(file_path)

    # 排除 test 開頭的檔案
    if file_name.lower().startswith('test'):
        return True, f"排除 test 開頭檔案: {file_name}"

    # 排除 json 檔案
    if file_name.lower().endswith('.json'):
        return True, f"排除 JSON 檔案: {file_name}"

    return False, ""

def create_review_folder():
    """創建程式碼審查資料夾並複製檔案"""
    
    # 定義目標路徑
    target_base_dir = Path("Capital_Official_Framework/official_gemini_review")
    
    # 創建目標資料夾
    target_base_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 創建目標資料夾: {target_base_dir}")
    
    # 讀取檔案清單
    file_list_path = "file_list_for_review.txt"
    if not os.path.exists(file_list_path):
        print(f"❌ 檔案清單不存在: {file_list_path}")
        print("💡 請先執行 dependency_analyzer.py 生成檔案清單")
        return False
    
    with open(file_list_path, 'r', encoding='utf-8') as f:
        source_files = [line.strip() for line in f if line.strip()]
    
    print(f"📋 準備複製 {len(source_files)} 個檔案...")
    print("🚫 排除規則: test開頭檔案 + JSON檔案")
    print("=" * 60)

    # 統計變數
    copied_count = 0
    failed_count = 0
    skipped_count = 0
    excluded_count = 0

    # 複製檔案
    for source_path in source_files:
        try:
            source_file = Path(source_path)

            # 檢查檔案是否應該被排除
            should_exclude, exclude_reason = should_exclude_file(source_path)
            if should_exclude:
                print(f"🚫 {exclude_reason}")
                excluded_count += 1
                continue

            # 檢查來源檔案是否存在
            if not source_file.exists():
                print(f"⚠️ 來源檔案不存在: {source_path}")
                skipped_count += 1
                continue
            
            # 計算相對路徑
            if source_path.startswith("Capital_Official_Framework"):
                # 移除 Capital_Official_Framework 前綴
                relative_path = source_path[len("Capital_Official_Framework"):].lstrip(os.sep)
            else:
                # 根目錄檔案，放在 root_files 子資料夾
                relative_path = os.path.join("root_files", os.path.basename(source_path))
            
            # 建立目標路徑
            target_path = target_base_dir / relative_path
            
            # 確保目標目錄存在
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 複製檔案
            shutil.copy2(source_file, target_path)
            print(f"✅ 已複製: {relative_path}")
            copied_count += 1
            
        except Exception as e:
            print(f"❌ 複製失敗 {source_path}: {e}")
            failed_count += 1
    
    # 創建複製腳本供未來使用
    create_copy_script(target_base_dir, source_files)

    # 創建說明文件
    create_readme(target_base_dir, copied_count, failed_count, skipped_count, excluded_count)

    # 輸出統計結果
    print("=" * 60)
    print(f"📊 複製完成統計:")
    print(f"   ✅ 成功複製: {copied_count} 個檔案")
    print(f"   🚫 排除檔案: {excluded_count} 個檔案")
    print(f"   ⚠️ 跳過檔案: {skipped_count} 個檔案")
    print(f"   ❌ 複製失敗: {failed_count} 個檔案")
    print(f"   📁 目標資料夾: {target_base_dir.absolute()}")

    return copied_count > 0

def create_copy_script(target_dir, source_files):
    """創建複製腳本供未來使用"""
    script_path = target_dir / "update_review_folder.py"
    
    script_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新程式碼審查資料夾腳本
自動生成於: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

import os
import shutil
from pathlib import Path

def should_exclude_file(file_path):
    """檢查檔案是否應該被排除"""
    file_name = os.path.basename(file_path)

    # 排除 test 開頭的檔案
    if file_name.lower().startswith('test'):
        return True, f"排除 test 開頭檔案: {{file_name}}"

    # 排除 json 檔案
    if file_name.lower().endswith('.json'):
        return True, f"排除 JSON 檔案: {{file_name}}"

    return False, ""

def update_review_folder():
    """更新程式碼審查資料夾"""
    
    # 檔案清單
    source_files = {repr(source_files)}
    
    target_base_dir = Path(__file__).parent
    print(f"📁 更新目標資料夾: {{target_base_dir}}")
    print("🚫 排除規則: test開頭檔案 + JSON檔案")

    copied_count = 0
    failed_count = 0
    skipped_count = 0
    excluded_count = 0

    for source_path in source_files:
        try:
            source_file = Path("../..") / source_path

            # 檢查檔案是否應該被排除
            should_exclude, exclude_reason = should_exclude_file(source_path)
            if should_exclude:
                print(f"🚫 {{exclude_reason}}")
                excluded_count += 1
                continue

            if not source_file.exists():
                print(f"⚠️ 來源檔案不存在: {{source_path}}")
                skipped_count += 1
                continue
            
            # 計算相對路徑
            if source_path.startswith("Capital_Official_Framework"):
                relative_path = source_path[len("Capital_Official_Framework"):].lstrip(os.sep)
            else:
                relative_path = os.path.join("root_files", os.path.basename(source_path))
            
            target_path = target_base_dir / relative_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(source_file, target_path)
            print(f"✅ 已更新: {{relative_path}}")
            copied_count += 1
            
        except Exception as e:
            print(f"❌ 更新失敗 {{source_path}}: {{e}}")
            failed_count += 1

    print(f"\\n📊 更新完成統計:")
    print(f"   ✅ 成功複製: {{copied_count}} 個檔案")
    print(f"   🚫 排除檔案: {{excluded_count}} 個檔案")
    print(f"   ⚠️ 跳過檔案: {{skipped_count}} 個檔案")
    print(f"   ❌ 失敗檔案: {{failed_count}} 個檔案")

if __name__ == "__main__":
    update_review_folder()
'''
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"📝 已創建更新腳本: {script_path.name}")

def create_readme(target_dir, copied_count, failed_count, skipped_count):
    """創建說明文件"""
    readme_path = target_dir / "README.md"
    
    readme_content = f"""# 程式碼審查資料夾

## 📋 概述

此資料夾包含 simple_integrated.py 及其相關測試環境的完整程式碼快照，用於程式碼審查。

## 📊 統計資訊

- **創建時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **成功複製**: {copied_count} 個檔案
- **複製失敗**: {failed_count} 個檔案  
- **跳過檔案**: {skipped_count} 個檔案

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
"""
    
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"📝 已創建說明文件: {readme_path.name}")

if __name__ == "__main__":
    success = create_review_folder()
    
    if success:
        print("\n🎉 程式碼審查資料夾創建完成！")
        print("📁 位置: Capital_Official_Framework/official_gemini_review")
        print("💡 您可以使用 update_review_folder.py 來更新程式碼快照")
    else:
        print("\n❌ 程式碼審查資料夾創建失敗")
        print("💡 請檢查錯誤訊息並重試")
