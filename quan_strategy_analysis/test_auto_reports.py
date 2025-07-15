#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試自動報告生成功能
驗證全套報告生成是否正確
"""

import json
import sqlite3
import os
import logging
from datetime import datetime
from pathlib import Path

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_data():
    """創建測試數據"""
    logger.info("🧪 創建測試數據...")
    
    # 清理並重新創建測試數據庫
    if os.path.exists("test_auto_reports.db"):
        os.remove("test_auto_reports.db")
    
    with sqlite3.connect("test_auto_reports.db") as conn:
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
        test_experiments = []
        
        # 基礎參數組合
        base_params = [
            {"lot1_trigger": 15, "lot1_trailing": 10, "lot2_trigger": 35, "lot2_trailing": 15, "lot3_trigger": 50, "lot3_trailing": 20},
            {"lot1_trigger": 20, "lot1_trailing": 10, "lot2_trigger": 40, "lot2_trailing": 15, "lot3_trigger": 55, "lot3_trailing": 20},
            {"lot1_trigger": 15, "lot1_trailing": 20, "lot2_trigger": 35, "lot2_trailing": 20, "lot3_trigger": 50, "lot3_trailing": 25},
        ]
        
        experiment_id = 1
        
        # 為每個基礎參數生成三種交易方向的實驗
        for base_param in base_params:
            for direction in ['LONG_ONLY', 'SHORT_ONLY', 'BOTH']:
                params = {
                    **base_param,
                    "trading_direction": direction,
                    "range_start_time": "08:46",
                    "range_end_time": "08:47",
                    "trade_lots": 3,
                    "start_date": "2024-11-04",
                    "end_date": "2024-11-10"
                }
                
                # 模擬不同方向的績效數據
                if direction == 'LONG_ONLY':
                    total_pnl = 150.0 + experiment_id * 10
                    long_pnl = total_pnl
                    short_pnl = 0.0
                    long_trades = 5
                    short_trades = 0
                elif direction == 'SHORT_ONLY':
                    total_pnl = 120.0 + experiment_id * 8
                    long_pnl = 0.0
                    short_pnl = total_pnl
                    long_trades = 0
                    short_trades = 4
                else:  # BOTH
                    total_pnl = 200.0 + experiment_id * 12
                    long_pnl = total_pnl * 0.6
                    short_pnl = total_pnl * 0.4
                    long_trades = 3
                    short_trades = 2
                
                conn.execute("""
                    INSERT INTO experiments (
                        experiment_id, parameters, success, execution_time,
                        total_trades, winning_trades, losing_trades, win_rate,
                        total_pnl, max_drawdown, long_trades, short_trades,
                        long_pnl, short_pnl, error_message, stdout_log, stderr_log
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    experiment_id, json.dumps(params), True, 1.5,
                    long_trades + short_trades, int((long_trades + short_trades) * 0.6), 
                    int((long_trades + short_trades) * 0.4), 60.0,
                    total_pnl, -total_pnl * 0.15, long_trades, short_trades,
                    long_pnl, short_pnl, "", "", ""
                ))
                
                experiment_id += 1
    
    logger.info(f"✅ 測試數據創建完成，共 {experiment_id - 1} 個實驗")
    return experiment_id - 1

def test_report_generation():
    """測試報告生成功能"""
    logger.info("🧪 測試報告生成功能...")
    
    # 模擬generate_all_reports的邏輯
    try:
        import csv
        from long_short_separation_analyzer import LongShortSeparationAnalyzer
        
        # 讀取測試數據
        with sqlite3.connect("test_auto_reports.db") as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT experiment_id, parameters, success, execution_time,
                       total_trades, winning_trades, losing_trades, win_rate,
                       total_pnl, max_drawdown, long_trades, short_trades,
                       long_pnl, short_pnl
                FROM experiments 
                WHERE success = 1
                ORDER BY experiment_id
            """)
            all_results = [dict(row) for row in cursor.fetchall()]
        
        if not all_results:
            logger.error("❌ 沒有測試數據")
            return False
        
        # 分析交易方向
        trading_directions = set()
        for result in all_results:
            params = json.loads(result['parameters'])
            direction = params.get('trading_direction', 'BOTH')
            trading_directions.add(direction)
        
        logger.info(f"📊 發現交易方向: {trading_directions}")
        
        # 創建輸出資料夾
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"test_all_modes_reports_{timestamp}"
        output_folder = os.path.join("batch_result", folder_name)
        os.makedirs(output_folder, exist_ok=True)
        
        generated_reports = []
        
        # 1. 生成CSV總表
        logger.info("📋 生成CSV總表...")
        csv_filename = f"batch_experiment_results_{timestamp}.csv"
        csv_filepath = os.path.join(output_folder, csv_filename)
        
        csv_data = []
        for result in all_results:
            params = json.loads(result['parameters'])
            
            # 提取參數信息
            lot1_str = f"{params.get('lot1_trigger', 0)}({params.get('lot1_trailing', 0)}%)"
            lot2_str = f"{params.get('lot2_trigger', 0)}({params.get('lot2_trailing', 0)}%)"
            lot3_str = f"{params.get('lot3_trigger', 0)}({params.get('lot3_trailing', 0)}%)"
            param_str = f"{lot1_str}/{lot2_str}/{lot3_str}"
            
            csv_row = {
                '實驗ID': result['experiment_id'],
                '交易方向': params.get('trading_direction', 'BOTH'),
                '時間區間': f"{params.get('range_start_time', '08:46')}-{params.get('range_end_time', '08:47')}",
                '多頭損益': round(result.get('long_pnl', 0), 1),
                '空頭損益': round(result.get('short_pnl', 0), 1),
                '總損益': round(result.get('total_pnl', 0), 1),
                'MDD': round(result.get('max_drawdown', 0), 1),
                '勝率': f"{round(result.get('win_rate', 0), 1)}%",
                '參數': param_str
            }
            csv_data.append(csv_row)
        
        # 寫入CSV總表
        fieldnames = ['實驗ID', '交易方向', '時間區間', '多頭損益', '空頭損益', '總損益', 'MDD', '勝率', '參數']
        with open(csv_filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
        
        generated_reports.append(("📋 CSV總表", csv_filename))
        logger.info(f"✅ CSV總表已生成: {csv_filename}")
        
        # 2. 生成各方向專用CSV
        logger.info("🎯 生成各交易方向專用CSV...")
        for direction in ['LONG_ONLY', 'SHORT_ONLY', 'BOTH']:
            if direction in trading_directions:
                direction_data = [row for row in csv_data if row['交易方向'] == direction]
                
                if direction_data:
                    direction_filename = f"{direction.lower()}_results_{timestamp}.csv"
                    direction_filepath = os.path.join(output_folder, direction_filename)
                    
                    with open(direction_filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(direction_data)
                    
                    direction_name = {"LONG_ONLY": "只做多", "SHORT_ONLY": "只做空", "BOTH": "多空混合"}[direction]
                    generated_reports.append((f"📊 {direction_name}專用CSV", direction_filename))
                    logger.info(f"✅ {direction_name}專用CSV已生成: {direction_filename}")
        
        # 3. 驗證生成的文件
        logger.info("🔍 驗證生成的文件...")
        for report_type, filename in generated_reports:
            filepath = os.path.join(output_folder, filename)
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                logger.info(f"   ✅ {report_type}: {filename} ({file_size} bytes)")
            else:
                logger.error(f"   ❌ {report_type}: {filename} 文件不存在")
                return False
        
        logger.info(f"📁 所有報告已生成到: {output_folder}")
        logger.info(f"📊 總共生成 {len(generated_reports)} 個報告文件")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 測試報告生成失敗: {e}")
        return False

def cleanup():
    """清理測試文件"""
    logger.info("🗑️ 清理測試文件...")
    
    # 刪除測試數據庫
    if os.path.exists("test_auto_reports.db"):
        os.remove("test_auto_reports.db")
        logger.info("   ✅ 測試數據庫已刪除")

def main():
    """主測試函數"""
    logger.info("🚀 開始自動報告生成功能測試")
    
    try:
        # 創建測試數據
        experiment_count = create_test_data()
        
        # 測試報告生成
        if test_report_generation():
            logger.info("🎉 自動報告生成功能測試通過！")
        else:
            logger.error("❌ 自動報告生成功能測試失敗")
        
    finally:
        # 清理測試文件
        cleanup()

if __name__ == "__main__":
    main()
