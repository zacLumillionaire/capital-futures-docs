#!/usr/bin/env python3
"""
測試 Web GUI API 的腳本
"""

import requests
import json
import time

def test_web_gui_backtest():
    """測試 Web GUI 回測 API"""
    print("🧪 測試 Web GUI 回測 API...")
    
    # 設定與 rev_future_path_analyzer.py 一致的參數
    backtest_config = {
        'trade_lots': 3,
        'start_date': '2024-11-04',  # 與 rev_future_path_analyzer.py 一致
        'end_date': '2025-06-28',    # 與 rev_future_path_analyzer.py 一致
        'range_start_time': '11:30', # 與 rev_future_path_analyzer.py 一致
        'range_end_time': '11:45',   # 與 rev_future_path_analyzer.py 一致
        'fixed_stop_mode': 'off',    # 使用移動停損
        'individual_take_profit_enabled': True,  # 啟用個別停利
        'entry_price_mode': 'range_boundary',
        'trading_direction': 'LONG_ONLY',  # 🚀 【修改】測試只做多模式
        'lot_settings': {
            'lot1': {
                'trigger': 15,      # 與標準配置一致
                'trailing': 10,     # 10%
                'take_profit': 30   # 固定停利30點
            },
            'lot2': {
                'trigger': 35,      # 與標準配置一致
                'trailing': 10,     # 10%
                'protection': 2.0,  # 2倍保護
                'take_profit': 30   # 固定停利30點
            },
            'lot3': {
                'trigger': 40,      # 與標準配置一致
                'trailing': 20,     # 20%
                'protection': 2.0,  # 2倍保護
                'take_profit': 30   # 固定停利30點
            }
        },
        'filters': {
            'range_filter': {
                'enabled': True,           # 啟用區間過濾
                'max_range_points': 160    # 160點上限
            },
            'risk_filter': {
                'enabled': False,          # 停用風險管理
                'daily_loss_limit': 150,
                'profit_target': 200
            },
            'stop_loss_filter': {
                'enabled': False,
                'stop_loss_type': 'range_boundary',
                'fixed_stop_loss_points': 15.0
            }
        }
    }
    
    try:
        # 發送回測請求
        print("📤 發送回測請求...")
        response = requests.post('http://localhost:8080/run_backtest', json=backtest_config)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ 回測請求成功發送")
                
                # 等待回測完成
                print("⏳ 等待回測完成...")
                max_wait = 120  # 最多等待2分鐘
                wait_time = 0
                
                while wait_time < max_wait:
                    time.sleep(2)
                    wait_time += 2
                    
                    # 檢查狀態
                    status_response = requests.get('http://localhost:8080/status')
                    if status_response.status_code == 200:
                        status = status_response.json()
                        
                        if not status.get('running', False):
                            if status.get('error'):
                                print(f"❌ 回測失敗: {status['error']}")
                                return False
                            else:
                                print("✅ 回測完成")
                                
                                # 獲取結果
                                if 'results' in status:
                                    results = status['results']
                                    print("📊 回測結果:")
                                    print(f"   總損益: {results.get('total_pnl', 'N/A')} 點")
                                    print(f"   最大回撤: {results.get('max_drawdown', 'N/A')} 點")
                                    print(f"   交易次數: {results.get('total_trades', 'N/A')}")
                                    print(f"   勝率: {results.get('win_rate', 'N/A')}%")
                                    print(f"   總交易天數: {results.get('total_trading_days', 'N/A')}")
                                    
                                    return results
                                else:
                                    print("⚠️ 回測完成但無結果數據")
                                    return False
                        else:
                            print(f"⏳ 回測進行中... ({wait_time}s)")
                    else:
                        print(f"❌ 無法獲取狀態: {status_response.status_code}")
                        return False
                
                print("⏰ 回測超時")
                return False
                
            else:
                print(f"❌ 回測請求失敗: {result.get('error', '未知錯誤')}")
                return False
        else:
            print(f"❌ HTTP 請求失敗: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 測試過程中發生異常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 開始測試 Web GUI API...")
    
    # 測試回測
    results = test_web_gui_backtest()
    
    if results:
        print("🎉 API 測試成功！")
        print("\n📋 最終結果摘要:")
        print(f"總損益: {results.get('total_pnl', 'N/A')} 點")
        print(f"最大回撤: {results.get('max_drawdown', 'N/A')} 點")
        print(f"交易次數: {results.get('total_trades', 'N/A')}")
        print(f"勝率: {results.get('win_rate', 'N/A')}%")
    else:
        print("❌ API 測試失敗")
