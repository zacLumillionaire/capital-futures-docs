#!/usr/bin/env python3
"""
每口獨立停利功能演示
展示如何使用新的每口停利設定功能來驗證MDD實驗結果
"""

import json
import subprocess
import sys
import os
from datetime import datetime

def demo_individual_take_profit():
    """演示每口獨立停利功能的不同配置"""
    
    print("🎯 每口獨立停利功能演示")
    print("=" * 80)
    print("此功能允許每口設定不同的停利點數，用於驗證MDD優化實驗結果")
    print()
    
    # 演示配置1：保守型停利設定
    demo_configs = [
        {
            "name": "保守型停利設定",
            "description": "較小的停利點數，降低風險",
            "config": {
                "individual_take_profit_enabled": True,
                "lot_settings": {
                    "lot1": {"trigger": 15, "trailing": 0, "take_profit": 30},
                    "lot2": {"trigger": 25, "trailing": 0, "protection": 0, "take_profit": 40},
                    "lot3": {"trigger": 35, "trailing": 0, "protection": 0, "take_profit": 50}
                }
            }
        },
        {
            "name": "積極型停利設定", 
            "description": "較大的停利點數，追求更高收益",
            "config": {
                "individual_take_profit_enabled": True,
                "lot_settings": {
                    "lot1": {"trigger": 15, "trailing": 0, "take_profit": 80},
                    "lot2": {"trigger": 25, "trailing": 0, "protection": 0, "take_profit": 100},
                    "lot3": {"trigger": 35, "trailing": 0, "protection": 0, "take_profit": 120}
                }
            }
        },
        {
            "name": "階梯型停利設定",
            "description": "遞增的停利點數，平衡風險與收益", 
            "config": {
                "individual_take_profit_enabled": True,
                "lot_settings": {
                    "lot1": {"trigger": 15, "trailing": 0, "take_profit": 45},
                    "lot2": {"trigger": 25, "trailing": 0, "protection": 0, "take_profit": 65},
                    "lot3": {"trigger": 35, "trailing": 0, "protection": 0, "take_profit": 85}
                }
            }
        }
    ]
    
    # 基礎配置
    base_config = {
        "trade_lots": 3,
        "start_date": "2024-11-04",
        "end_date": "2024-11-06",  # 3天測試
        "range_start_time": "10:30",
        "range_end_time": "10:31",
        "fixed_stop_mode": True,
        "filters": {
            "range_filter": {"enabled": False, "max_range_points": 50},
            "risk_filter": {"enabled": False, "daily_loss_limit": 150, "profit_target": 200},
            "stop_loss_filter": {"enabled": False, "stop_loss_type": "range_boundary", "fixed_stop_loss_points": 15.0}
        }
    }
    
    results = []
    
    for i, demo in enumerate(demo_configs, 1):
        print(f"📊 演示 {i}: {demo['name']}")
        print(f"   描述: {demo['description']}")
        print("   停利設定:")
        for lot_name, lot_config in demo['config']['lot_settings'].items():
            print(f"     {lot_name}: 停損{lot_config['trigger']}點, 停利{lot_config['take_profit']}點")
        print()
        
        # 合併配置
        test_config = {**base_config, **demo['config']}
        
        # 構建命令
        cmd = [
            sys.executable,
            "rev_multi_Profit-Funded Risk_多口.py",
            "--start-date", test_config["start_date"],
            "--end-date", test_config["end_date"],
            "--gui-mode",
            "--config", json.dumps(test_config, ensure_ascii=False)
        ]
        
        try:
            print(f"🚀 執行演示 {i}...")
            result = subprocess.run(
                cmd,
                cwd=os.path.dirname(os.path.abspath(__file__)),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=60
            )
            
            if result.returncode == 0:
                # 解析結果
                output = result.stderr  # LOG在stderr中
                total_pnl = None
                win_rate = None
                
                for line in output.split('\n'):
                    if "總損益(3口):" in line:
                        try:
                            total_pnl = float(line.split("總損益(3口):")[1].strip())
                        except:
                            pass
                    elif "勝率:" in line:
                        try:
                            win_rate = line.split("勝率:")[1].strip()
                        except:
                            pass
                
                results.append({
                    "name": demo['name'],
                    "total_pnl": total_pnl,
                    "win_rate": win_rate,
                    "config": demo['config']['lot_settings']
                })
                
                print(f"✅ 演示 {i} 完成")
                if total_pnl is not None:
                    print(f"   總損益: {total_pnl:+.2f} 點")
                if win_rate is not None:
                    print(f"   勝率: {win_rate}")
                    
            else:
                print(f"❌ 演示 {i} 執行失敗")
                results.append({
                    "name": demo['name'],
                    "total_pnl": None,
                    "win_rate": None,
                    "error": result.stderr
                })
                
        except Exception as e:
            print(f"❌ 演示 {i} 執行異常: {e}")
            results.append({
                "name": demo['name'],
                "total_pnl": None,
                "win_rate": None,
                "error": str(e)
            })
        
        print("-" * 60)
    
    # 結果總結
    print("\n📈 演示結果總結")
    print("=" * 80)
    print(f"{'配置名稱':<20} {'總損益(點)':<12} {'勝率':<10} {'停利設定'}")
    print("-" * 80)
    
    for result in results:
        if result['total_pnl'] is not None:
            pnl_str = f"{result['total_pnl']:+.2f}"
        else:
            pnl_str = "執行失敗"
            
        win_rate_str = result['win_rate'] or "N/A"
        
        # 停利設定摘要
        if 'config' in result:
            tp_summary = f"{result['config']['lot1']['take_profit']}/{result['config']['lot2']['take_profit']}/{result['config']['lot3']['take_profit']}"
        else:
            tp_summary = "N/A"
            
        print(f"{result['name']:<20} {pnl_str:<12} {win_rate_str:<10} {tp_summary}")
    
    print("\n🎯 功能說明")
    print("=" * 80)
    print("1. 每口獨立停利功能已成功實現")
    print("2. 可以通過GUI界面或程式配置設定每口不同的停利點數")
    print("3. 此功能可用於驗證MDD優化實驗的結果")
    print("4. 建議結合固定停損模式使用，避免複雜的移動停損邏輯")
    print("5. 可以通過 python rev_web_trading_gui.py 啟動GUI界面進行設定")
    
    print("\n🏁 演示完成")

if __name__ == "__main__":
    demo_individual_take_profit()
