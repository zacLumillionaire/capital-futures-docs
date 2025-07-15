#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試自動HTML報告生成功能
驗證能否為不同交易方向生成獨立的HTML報告
"""

import json
import sqlite3
import os
import logging
from datetime import datetime
from pathlib import Path
from experiment_analyzer import ExperimentAnalyzer

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_data():
    """創建測試數據"""
    logger.info("🧪 創建測試數據...")
    
    # 清理並重新創建測試數據庫
    if os.path.exists("test_html_reports.db"):
        os.remove("test_html_reports.db")
    
    with sqlite3.connect("test_html_reports.db") as conn:
        # 創建表格
        conn.execute("""
            CREATE TABLE experiments (
                experiment_id INTEGER PRIMARY KEY,
                parameters TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                execution_time REAL NOT NULL,
                total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                win_rate REAL DEFAULT 0.0,
                total_pnl REAL DEFAULT 0.0,
                max_drawdown REAL DEFAULT 0.0,
                long_trades INTEGER DEFAULT 0,
                short_trades INTEGER DEFAULT 0,
                long_pnl REAL DEFAULT 0.0,
                short_pnl REAL DEFAULT 0.0,
                error_message TEXT DEFAULT '',
                stdout_log TEXT DEFAULT '',
                stderr_log TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 插入測試數據（模擬全模式實驗結果）
        experiment_id = 1
        
        # 為每種交易方向創建5個實驗
        for direction in ['LONG_ONLY', 'SHORT_ONLY', 'BOTH']:
            for i in range(5):
                params = {
                    "lot1_trigger": 15 + i * 5,
                    "lot1_trailing": 10 + i * 2,
                    "lot2_trigger": 35 + i * 5,
                    "lot2_trailing": 15 + i * 2,
                    "lot3_trigger": 50 + i * 5,
                    "lot3_trailing": 20 + i * 2,
                    "trading_direction": direction,
                    "range_start_time": "08:46",
                    "range_end_time": "08:47",
                    "trade_lots": 3,
                    "start_date": "2024-11-04",
                    "end_date": "2024-11-10"
                }
                
                # 模擬不同方向的績效數據
                if direction == 'LONG_ONLY':
                    total_pnl = 150.0 + i * 20
                    long_pnl = total_pnl
                    short_pnl = 0.0
                    long_trades = 5 + i
                    short_trades = 0
                elif direction == 'SHORT_ONLY':
                    total_pnl = 120.0 + i * 15
                    long_pnl = 0.0
                    short_pnl = total_pnl
                    long_trades = 0
                    short_trades = 4 + i
                else:  # BOTH
                    total_pnl = 200.0 + i * 25
                    long_pnl = total_pnl * 0.6
                    short_pnl = total_pnl * 0.4
                    long_trades = 3 + i
                    short_trades = 2 + i
                
                conn.execute("""
                    INSERT INTO experiments (
                        experiment_id, parameters, success, execution_time,
                        total_trades, winning_trades, losing_trades, win_rate,
                        total_pnl, max_drawdown, long_trades, short_trades,
                        long_pnl, short_pnl, error_message, stdout_log, stderr_log
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    experiment_id, json.dumps(params), True, 1.5,
                    long_trades + short_trades, int((long_trades + short_trades) * 0.65), 
                    int((long_trades + short_trades) * 0.35), 65.0,
                    total_pnl, -total_pnl * 0.12, long_trades, short_trades,
                    long_pnl, short_pnl, "", "", ""
                ))
                
                experiment_id += 1
    
    logger.info(f"✅ 測試數據創建完成，共 {experiment_id - 1} 個實驗")
    return experiment_id - 1

def test_single_direction_reports():
    """測試單一方向報告生成"""
    logger.info("🧪 測試單一方向報告生成...")
    
    # 創建輸出目錄
    output_dir = "test_html_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # 創建分析器
    analyzer = ExperimentAnalyzer("test_html_reports.db")
    
    # 測試三種方向的報告
    directions = ['LONG_ONLY', 'SHORT_ONLY', 'BOTH']
    generated_files = []
    
    for direction in directions:
        try:
            logger.info(f"📊 生成 {direction} 方向的報告...")
            
            # 生成報告
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(output_dir, f"test_report_{direction.lower()}_{timestamp}.html")
            
            report_file = analyzer.generate_analysis_report(
                output_file=output_file,
                trading_direction=direction
            )
            
            if report_file and os.path.exists(report_file):
                file_size = os.path.getsize(report_file)
                logger.info(f"✅ {direction} 報告生成成功: {os.path.basename(report_file)} ({file_size} bytes)")
                generated_files.append((direction, report_file))
                
                # 檢查報告內容
                with open(report_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 驗證標題包含方向信息
                direction_map = {
                    'LONG_ONLY': '只做多',
                    'SHORT_ONLY': '只做空',
                    'BOTH': '多空混合'
                }
                expected_title = direction_map[direction]
                
                if expected_title in content:
                    logger.info(f"   ✅ 標題包含方向信息: {expected_title}")
                else:
                    logger.warning(f"   ⚠️ 標題未包含方向信息: {expected_title}")
                
                # 檢查是否包含圖表
                if 'chart' in content.lower() or 'img' in content.lower():
                    logger.info(f"   ✅ 報告包含圖表元素")
                else:
                    logger.warning(f"   ⚠️ 報告未包含圖表元素")
                    
            else:
                logger.error(f"❌ {direction} 報告生成失敗")
                return False
                
        except Exception as e:
            logger.error(f"❌ 生成 {direction} 報告時發生錯誤: {e}")
            return False
    
    logger.info(f"✅ 成功生成 {len(generated_files)} 個方向的報告")
    return True

def test_data_filtering():
    """測試數據過濾功能"""
    logger.info("🧪 測試數據過濾功能...")
    
    analyzer = ExperimentAnalyzer("test_html_reports.db")
    
    # 測試每個方向的數據過濾
    for direction in ['LONG_ONLY', 'SHORT_ONLY', 'BOTH']:
        logger.info(f"🔍 測試 {direction} 方向的數據過濾...")
        
        # 載入過濾後的數據
        df = analyzer.load_results_dataframe(success_only=True, trading_direction=direction)
        
        if df.empty:
            logger.error(f"❌ {direction} 方向沒有數據")
            return False
        
        # 檢查數據是否正確過濾
        unique_directions = df['trading_direction'].unique()
        
        if len(unique_directions) == 1 and unique_directions[0] == direction:
            logger.info(f"   ✅ {direction} 數據過濾正確，共 {len(df)} 筆記錄")
        else:
            logger.error(f"   ❌ {direction} 數據過濾錯誤，包含方向: {unique_directions}")
            return False
        
        # 檢查統計數據
        summary = analyzer.get_summary_statistics(trading_direction=direction)
        if summary and 'total_experiments' in summary:
            logger.info(f"   📊 {direction} 統計: {summary['total_experiments']} 個實驗")
        else:
            logger.warning(f"   ⚠️ {direction} 統計數據異常")
    
    logger.info("✅ 數據過濾功能測試通過")
    return True

def cleanup():
    """清理測試文件"""
    logger.info("🗑️ 清理測試文件...")
    
    # 刪除測試數據庫
    if os.path.exists("test_html_reports.db"):
        os.remove("test_html_reports.db")
        logger.info("   ✅ 測試數據庫已刪除")
    
    # 清理測試輸出目錄
    import shutil
    if os.path.exists("test_html_output"):
        shutil.rmtree("test_html_output")
        logger.info("   ✅ 測試輸出目錄已清理")

def main():
    """主測試函數"""
    logger.info("🚀 開始HTML報告生成功能測試")
    
    try:
        # 創建測試數據
        experiment_count = create_test_data()
        
        # 測試數據過濾
        if not test_data_filtering():
            logger.error("❌ 數據過濾功能測試失敗")
            return
        
        # 測試報告生成
        if test_single_direction_reports():
            logger.info("🎉 HTML報告生成功能測試通過！")
        else:
            logger.error("❌ HTML報告生成功能測試失敗")
        
    finally:
        # 清理測試文件
        cleanup()

if __name__ == "__main__":
    main()
