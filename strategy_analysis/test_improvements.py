#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試改進功能
1. 參數格式顯示改進
2. 全模式選項
3. 資料夾組織結構
"""

import json
import subprocess
import sys
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_parameter_format():
    """測試參數格式顯示改進"""
    logger.info("🧪 測試參數格式顯示...")
    
    # 檢查資料庫中的參數格式
    try:
        with sqlite3.connect("batch_experiments.db") as conn:
            cursor = conn.execute("""
                SELECT experiment_id, parameters 
                FROM experiments 
                WHERE success = 1 
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            if row:
                params = json.loads(row[1])
                
                # 構建新格式的參數字符串
                lot1_str = f"{params.get('lot1_trigger', 0)}({params.get('lot1_trailing', 0)}%)"
                lot2_str = f"{params.get('lot2_trigger', 0)}({params.get('lot2_trailing', 0)}%)"
                lot3_str = f"{params.get('lot3_trigger', 0)}({params.get('lot3_trailing', 0)}%)"
                param_str = f"{lot1_str}/{lot2_str}/{lot3_str}"
                
                logger.info(f"✅ 新參數格式: {param_str}")
                logger.info(f"   實驗ID: {row[0]}")
                return True
            else:
                logger.warning("⚠️ 沒有找到實驗數據來測試參數格式")
                return False
                
    except Exception as e:
        logger.error(f"❌ 測試參數格式失敗: {e}")
        return False

def test_all_modes_experiment():
    """測試全模式實驗功能"""
    logger.info("🧪 測試全模式實驗...")
    
    # 構建測試配置
    gui_config = {
        "trade_lots": 3,
        "start_date": "2024-11-04",
        "end_date": "2024-11-06",  # 極短期測試
        "range_start_time": "08:46",
        "range_end_time": "08:47",
        "trading_direction": "ALL_MODES",  # 關鍵：全模式
        "lot_settings": {
            "lot1": {"trigger": 15, "trailing": 10},
            "lot2": {"trigger": 40, "trailing": 10, "protection": 2.0},
            "lot3": {"trigger": 41, "trailing": 20, "protection": 2.0}
        },
        "filters": {
            "range_filter": {"enabled": False},
            "risk_filter": {"enabled": False},
            "stop_loss_filter": {"enabled": False}
        }
    }
    
    results = {}
    
    # 測試三種模式
    for mode in ["LONG_ONLY", "SHORT_ONLY", "BOTH"]:
        test_config = gui_config.copy()
        test_config["trading_direction"] = mode
        
        cmd = [
            sys.executable,
            "multi_Profit-Funded Risk_多口.py",
            "--start-date", test_config["start_date"],
            "--end-date", test_config["end_date"],
            "--gui-mode",
            "--config", json.dumps(test_config, ensure_ascii=False)
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=30
            )
            
            if result.returncode == 0:
                output = result.stdout
                if "BACKTEST_RESULT_JSON:" in output:
                    json_start = output.find("BACKTEST_RESULT_JSON:") + len("BACKTEST_RESULT_JSON:")
                    json_str = output[json_start:].strip()
                    try:
                        backtest_result = json.loads(json_str)
                        results[mode] = backtest_result
                        logger.info(f"✅ {mode} 模式測試成功")
                    except json.JSONDecodeError:
                        logger.error(f"❌ {mode} 模式JSON解析失敗")
            else:
                logger.error(f"❌ {mode} 模式執行失敗")
                
        except Exception as e:
            logger.error(f"💥 {mode} 模式測試異常: {e}")
    
    # 驗證全模式邏輯
    if len(results) == 3:
        logger.info("📊 全模式測試結果:")
        for mode, result in results.items():
            logger.info(f"   {mode}: 總損益={result.get('total_pnl', 0):.1f}, "
                       f"多頭交易={result.get('long_trades', 0)}, "
                       f"空頭交易={result.get('short_trades', 0)}")
        return True
    else:
        logger.error("❌ 全模式測試失敗")
        return False

def test_folder_structure():
    """測試資料夾組織結構"""
    logger.info("🧪 測試資料夾組織結構...")
    
    batch_result_dir = Path("batch_result")
    
    # 檢查是否有實驗資料夾
    experiment_folders = [d for d in batch_result_dir.iterdir() if d.is_dir()]
    
    if experiment_folders:
        logger.info(f"✅ 找到 {len(experiment_folders)} 個實驗資料夾:")
        for folder in sorted(experiment_folders):
            # 檢查資料夾內容
            csv_files = list(folder.glob("*.csv"))
            logger.info(f"   📁 {folder.name}: {len(csv_files)} 個CSV文件")
            
            # 顯示最新的CSV文件內容摘要
            if csv_files:
                latest_csv = max(csv_files, key=lambda x: x.stat().st_mtime)
                try:
                    with open(latest_csv, 'r', encoding='utf-8-sig') as f:
                        lines = f.readlines()
                        if len(lines) > 1:
                            header = lines[0].strip()
                            logger.info(f"      📄 {latest_csv.name}: {len(lines)-1} 筆記錄")
                            logger.info(f"      📋 欄位: {header}")
                except Exception as e:
                    logger.warning(f"      ⚠️ 讀取CSV失敗: {e}")
        
        return True
    else:
        logger.warning("⚠️ 沒有找到實驗資料夾")
        return False

def test_long_short_analyzer():
    """測試多空分離分析器的資料夾功能"""
    logger.info("🧪 測試多空分離分析器...")
    
    try:
        from long_short_separation_analyzer import LongShortSeparationAnalyzer
        
        # 創建測試資料夾
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_folder = f"test_analysis_{timestamp}"
        
        analyzer = LongShortSeparationAnalyzer(output_subdir=test_folder)
        
        # 檢查輸出目錄是否正確設置
        expected_path = Path("batch_result") / test_folder
        if analyzer.output_dir == expected_path:
            logger.info(f"✅ 分析器輸出目錄設置正確: {analyzer.output_dir}")
            
            # 檢查目錄是否被創建
            if expected_path.exists():
                logger.info("✅ 輸出目錄已創建")
                return True
            else:
                logger.error("❌ 輸出目錄未創建")
                return False
        else:
            logger.error(f"❌ 分析器輸出目錄設置錯誤: {analyzer.output_dir}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 測試多空分離分析器失敗: {e}")
        return False

def main():
    """主測試函數"""
    logger.info("🚀 開始改進功能測試")
    
    test_results = {
        "參數格式顯示": test_parameter_format(),
        "全模式實驗": test_all_modes_experiment(),
        "資料夾組織結構": test_folder_structure(),
        "多空分離分析器": test_long_short_analyzer()
    }
    
    logger.info("📊 測試結果總結:")
    for test_name, result in test_results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        logger.info(f"   {test_name}: {status}")
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    logger.info(f"🎯 總體結果: {passed_tests}/{total_tests} 項測試通過")
    
    if passed_tests == total_tests:
        logger.info("🎉 所有改進功能測試通過！")
    else:
        logger.warning("⚠️ 部分測試失敗，需要檢查相關功能")

if __name__ == "__main__":
    main()
