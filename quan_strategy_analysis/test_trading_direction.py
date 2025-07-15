#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試交易方向功能
驗證只做多、只做空、都跑三種模式的回測結果
"""

import json
import subprocess
import sys
import logging
from datetime import datetime

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_trading_direction(direction: str, test_name: str):
    """測試特定交易方向的回測"""
    logger.info(f"🧪 開始測試 {test_name} (方向: {direction})")
    
    # 構建測試配置
    gui_config = {
        "trade_lots": 3,
        "start_date": "2024-11-04",
        "end_date": "2024-11-10",  # 短期測試
        "range_start_time": "08:46",
        "range_end_time": "08:47",
        "trading_direction": direction,  # 關鍵參數
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
    
    # 構建命令
    cmd = [
        sys.executable,
        "multi_Profit-Funded Risk_多口.py",
        "--start-date", gui_config["start_date"],
        "--end-date", gui_config["end_date"],
        "--gui-mode",
        "--config", json.dumps(gui_config, ensure_ascii=False)
    ]
    
    try:
        # 執行回測
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=60  # 1分鐘超時
        )
        
        if result.returncode == 0:
            # 解析結果
            output = result.stdout
            if "BACKTEST_RESULT_JSON:" in output:
                json_start = output.find("BACKTEST_RESULT_JSON:") + len("BACKTEST_RESULT_JSON:")
                json_str = output[json_start:].strip()
                try:
                    backtest_result = json.loads(json_str)
                    
                    logger.info(f"✅ {test_name} 測試成功")
                    logger.info(f"   總損益: {backtest_result.get('total_pnl', 0):.1f}")
                    logger.info(f"   多頭損益: {backtest_result.get('long_pnl', 0):.1f}")
                    logger.info(f"   空頭損益: {backtest_result.get('short_pnl', 0):.1f}")
                    logger.info(f"   多頭交易: {backtest_result.get('long_trades', 0)}")
                    logger.info(f"   空頭交易: {backtest_result.get('short_trades', 0)}")
                    logger.info(f"   總交易: {backtest_result.get('total_trades', 0)}")
                    
                    return backtest_result
                    
                except json.JSONDecodeError as e:
                    logger.error(f"❌ {test_name} JSON解析失敗: {e}")
                    logger.error(f"   原始輸出: {json_str[:200]}...")
            else:
                logger.error(f"❌ {test_name} 未找到結構化結果")
                logger.error(f"   stdout: {result.stdout[:500]}...")
        else:
            logger.error(f"❌ {test_name} 執行失敗 (返回碼: {result.returncode})")
            logger.error(f"   stderr: {result.stderr[:500]}...")
            
    except subprocess.TimeoutExpired:
        logger.error(f"⏰ {test_name} 執行超時")
    except Exception as e:
        logger.error(f"💥 {test_name} 執行異常: {e}")
    
    return None

def main():
    """主測試函數"""
    logger.info("🚀 開始交易方向功能測試")
    
    # 測試三種模式
    test_cases = [
        ("BOTH", "多空都跑"),
        ("LONG_ONLY", "只做多"),
        ("SHORT_ONLY", "只做空")
    ]
    
    results = {}
    
    for direction, test_name in test_cases:
        result = test_trading_direction(direction, test_name)
        if result:
            results[direction] = result
        print("-" * 50)
    
    # 分析結果
    if len(results) == 3:
        logger.info("📊 測試結果分析:")
        
        both_result = results["BOTH"]
        long_result = results["LONG_ONLY"]
        short_result = results["SHORT_ONLY"]
        
        logger.info("🔍 驗證邏輯正確性:")
        
        # 驗證1：只做多時應該沒有空頭交易
        if long_result["short_trades"] == 0:
            logger.info("✅ 只做多模式：空頭交易數為0 ✓")
        else:
            logger.error(f"❌ 只做多模式：空頭交易數應為0，實際為{long_result['short_trades']}")
        
        # 驗證2：只做空時應該沒有多頭交易
        if short_result["long_trades"] == 0:
            logger.info("✅ 只做空模式：多頭交易數為0 ✓")
        else:
            logger.error(f"❌ 只做空模式：多頭交易數應為0，實際為{short_result['long_trades']}")
        
        # 驗證3：只做多的損益應該等於都跑模式的多頭損益
        if abs(long_result["total_pnl"] - both_result["long_pnl"]) < 0.1:
            logger.info("✅ 只做多損益 = 都跑模式的多頭損益 ✓")
        else:
            logger.error(f"❌ 只做多損益({long_result['total_pnl']}) ≠ 都跑多頭損益({both_result['long_pnl']})")
        
        # 驗證4：只做空的損益應該等於都跑模式的空頭損益
        if abs(short_result["total_pnl"] - both_result["short_pnl"]) < 0.1:
            logger.info("✅ 只做空損益 = 都跑模式的空頭損益 ✓")
        else:
            logger.error(f"❌ 只做空損益({short_result['total_pnl']}) ≠ 都跑空頭損益({both_result['short_pnl']})")
        
        # 驗證5：多空損益加總應該等於都跑的總損益
        calculated_total = long_result["total_pnl"] + short_result["total_pnl"]
        if abs(calculated_total - both_result["total_pnl"]) < 0.1:
            logger.info("✅ 多空損益加總 = 都跑總損益 ✓")
        else:
            logger.error(f"❌ 多空損益加總({calculated_total}) ≠ 都跑總損益({both_result['total_pnl']})")
        
        logger.info("🎉 交易方向功能測試完成！")
        
    else:
        logger.error("❌ 部分測試失敗，無法進行完整驗證")

if __name__ == "__main__":
    main()
