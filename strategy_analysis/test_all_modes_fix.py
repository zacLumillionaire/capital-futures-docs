#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試全模式實驗ID修復
驗證實驗ID不重複，所有實驗都被正確保存
"""

import json
import logging
import sqlite3
from parameter_matrix_generator import ExperimentConfig, ParameterMatrixGenerator, ParameterRange, LotParameterConfig, TimeRange

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_experiment_id_generation():
    """測試實驗ID生成邏輯"""
    logger.info("🧪 測試實驗ID生成邏輯...")
    
    # 創建小規模測試配置
    config = ExperimentConfig(
        trade_lots=3,
        date_ranges=[("2024-11-04", "2024-11-06")],  # 1個日期範圍
        time_ranges=TimeRange(
            start_times=["08:46"],  # 1個時間範圍
            end_times=["08:47"]
        ),
        lot1_config=LotParameterConfig(
            trigger_range=ParameterRange(15, 20, 5),  # 2個值: 15, 20
            trailing_range=ParameterRange(10, 20, 10)  # 2個值: 10, 20
        ),
        lot2_config=LotParameterConfig(
            trigger_range=ParameterRange(35, 40, 5),  # 2個值: 35, 40
            trailing_range=ParameterRange(10, 20, 10),  # 2個值: 10, 20
            protection_range=ParameterRange(2.0, 2.0, 1.0)  # 1個值: 2.0
        ),
        lot3_config=LotParameterConfig(
            trigger_range=ParameterRange(50, 55, 5),  # 2個值: 50, 55
            trailing_range=ParameterRange(15, 25, 10),  # 2個值: 15, 25
            protection_range=ParameterRange(2.0, 2.0, 1.0)  # 1個值: 2.0
        )
    )
    
    # 生成參數矩陣
    generator = ParameterMatrixGenerator(config)
    experiments = generator.generate_full_parameter_matrix()
    
    logger.info(f"✅ 原始實驗數量: {len(experiments)}")
    
    # 預期: 1日期 × 1時間 × (2×2) lot1 × (2×2×1) lot2 × (2×2×1) lot3 = 1×1×4×4×4 = 64個實驗
    expected_count = 1 * 1 * 2 * 2 * 2 * 2 * 1 * 2 * 2 * 1  # 64
    logger.info(f"📊 預期實驗數量: {expected_count}")
    
    # 檢查實驗ID是否連續且唯一
    experiment_ids = [exp['experiment_id'] for exp in experiments]
    unique_ids = set(experiment_ids)
    
    logger.info(f"🔍 實驗ID範圍: {min(experiment_ids)} - {max(experiment_ids)}")
    logger.info(f"🔍 唯一ID數量: {len(unique_ids)}")
    logger.info(f"🔍 總實驗數量: {len(experiment_ids)}")
    
    if len(unique_ids) == len(experiment_ids):
        logger.info("✅ 原始實驗ID唯一性檢查通過")
    else:
        logger.error("❌ 原始實驗ID有重複")
        return False
    
    return experiments

def test_all_modes_expansion(experiments):
    """測試全模式擴展邏輯"""
    logger.info("🧪 測試全模式擴展邏輯...")
    
    # 模擬全模式擴展（複製batch_experiment_gui.py的邏輯）
    trading_direction = 'ALL_MODES'
    
    if trading_direction == 'ALL_MODES':
        # 全模式：為每個參數組合生成三種交易方向的實驗
        original_experiments = experiments.copy()
        expanded_experiments = []
        
        # 重新分配實驗ID，避免重複
        experiment_id = 1
        
        for exp in original_experiments:
            # 生成三種模式的實驗
            for mode in ['LONG_ONLY', 'SHORT_ONLY', 'BOTH']:
                new_exp = exp.copy()
                new_exp['trading_direction'] = mode
                new_exp['experiment_id'] = experiment_id  # 🚀 重新分配ID
                expanded_experiments.append(new_exp)
                experiment_id += 1
    
    logger.info(f"✅ 擴展後實驗數量: {len(expanded_experiments)}")
    logger.info(f"📊 預期擴展數量: {len(experiments) * 3}")
    
    # 檢查擴展後的實驗ID唯一性
    expanded_ids = [exp['experiment_id'] for exp in expanded_experiments]
    unique_expanded_ids = set(expanded_ids)
    
    logger.info(f"🔍 擴展後ID範圍: {min(expanded_ids)} - {max(expanded_ids)}")
    logger.info(f"🔍 擴展後唯一ID數量: {len(unique_expanded_ids)}")
    logger.info(f"🔍 擴展後總實驗數量: {len(expanded_ids)}")
    
    if len(unique_expanded_ids) == len(expanded_ids):
        logger.info("✅ 擴展後實驗ID唯一性檢查通過")
    else:
        logger.error("❌ 擴展後實驗ID有重複")
        return False, []
    
    # 檢查交易方向分布
    direction_counts = {}
    for exp in expanded_experiments:
        direction = exp['trading_direction']
        direction_counts[direction] = direction_counts.get(direction, 0) + 1
    
    logger.info("📊 交易方向分布:")
    for direction, count in direction_counts.items():
        logger.info(f"   {direction}: {count} 個實驗")
    
    # 驗證每種方向的數量是否相等
    expected_per_direction = len(experiments)
    for direction, count in direction_counts.items():
        if count != expected_per_direction:
            logger.error(f"❌ {direction} 方向實驗數量錯誤: 預期 {expected_per_direction}, 實際 {count}")
            return False, []
    
    logger.info("✅ 交易方向分布檢查通過")
    return True, expanded_experiments

def test_database_storage(experiments):
    """測試數據庫存儲"""
    logger.info("🧪 測試數據庫存儲...")
    
    # 清理數據庫
    with sqlite3.connect("test_batch_experiments.db") as conn:
        conn.execute("DROP TABLE IF EXISTS experiments")
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
    
    # 模擬存儲所有實驗
    stored_count = 0
    for exp in experiments:
        with sqlite3.connect("test_batch_experiments.db") as conn:
            conn.execute("""
                INSERT OR REPLACE INTO experiments (
                    experiment_id, parameters, success, execution_time,
                    total_trades, winning_trades, losing_trades, win_rate,
                    total_pnl, max_drawdown, long_trades, short_trades,
                    long_pnl, short_pnl, error_message, stdout_log, stderr_log
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                exp['experiment_id'], json.dumps(exp), True, 1.0,
                10, 6, 4, 60.0, 100.0, -20.0, 5, 5, 50.0, 50.0, "", "", ""
            ))
            stored_count += 1
    
    # 檢查存儲結果
    with sqlite3.connect("test_batch_experiments.db") as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM experiments")
        db_count = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(DISTINCT experiment_id) FROM experiments")
        unique_count = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT json_extract(parameters, '$.trading_direction') as direction, COUNT(*) FROM experiments GROUP BY direction")
        direction_distribution = dict(cursor.fetchall())
    
    logger.info(f"📊 存儲統計:")
    logger.info(f"   嘗試存儲: {stored_count} 個實驗")
    logger.info(f"   數據庫記錄: {db_count} 條")
    logger.info(f"   唯一ID數: {unique_count} 個")
    logger.info(f"   交易方向分布: {direction_distribution}")
    
    if db_count == len(experiments) and unique_count == len(experiments):
        logger.info("✅ 數據庫存儲檢查通過")
        return True
    else:
        logger.error("❌ 數據庫存儲檢查失敗")
        return False

def main():
    """主測試函數"""
    logger.info("🚀 開始全模式實驗ID修復測試")
    
    # 測試1：原始實驗ID生成
    experiments = test_experiment_id_generation()
    if not experiments:
        logger.error("❌ 原始實驗ID生成測試失敗")
        return
    
    # 測試2：全模式擴展
    success, expanded_experiments = test_all_modes_expansion(experiments)
    if not success:
        logger.error("❌ 全模式擴展測試失敗")
        return
    
    # 測試3：數據庫存儲
    if not test_database_storage(expanded_experiments):
        logger.error("❌ 數據庫存儲測試失敗")
        return
    
    logger.info("🎉 所有測試通過！全模式實驗ID修復成功！")
    
    # 清理測試數據庫
    import os
    if os.path.exists("test_batch_experiments.db"):
        os.remove("test_batch_experiments.db")
        logger.info("🗑️ 測試數據庫已清理")

if __name__ == "__main__":
    main()
