#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 安全診斷測試腳本
在不影響現有系統的情況下測試診斷工具
"""

import sys
import os
import time
import sqlite3
from datetime import date

def test_database_connectivity():
    """測試資料庫連接"""
    print("🔍 測試資料庫連接...")
    
    db_path = "multi_group_strategy.db"
    
    try:
        if not os.path.exists(db_path):
            print(f"❌ 資料庫文件不存在: {db_path}")
            return False
        
        with sqlite3.connect(db_path, timeout=2.0) as conn:
            cursor = conn.cursor()
            
            # 檢查表結構
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"✅ 資料庫表: {tables}")
            
            # 檢查問題部位
            problem_positions = [133, 134, 135]
            for position_id in problem_positions:
                cursor.execute('''
                    SELECT id, status, direction, group_id 
                    FROM position_records 
                    WHERE id = ?
                ''', (position_id,))
                
                row = cursor.fetchone()
                if row:
                    print(f"✅ 部位{position_id}: 狀態={row[1]}, 方向={row[2]}, 組={row[3]}")
                else:
                    print(f"❌ 部位{position_id}: 不存在")
            
            # 檢查今日策略組
            cursor.execute('''
                SELECT COUNT(*) FROM strategy_groups 
                WHERE date = ?
            ''', (date.today().isoformat(),))
            
            group_count = cursor.fetchone()[0]
            print(f"✅ 今日策略組數量: {group_count}")
            
            return True
            
    except Exception as e:
        print(f"❌ 資料庫連接失敗: {e}")
        return False

def test_join_query_performance():
    """測試JOIN查詢性能"""
    print("\n🔍 測試JOIN查詢性能...")
    
    db_path = "multi_group_strategy.db"
    problem_positions = [133, 134, 135]
    
    try:
        with sqlite3.connect(db_path, timeout=2.0) as conn:
            cursor = conn.cursor()
            
            for position_id in problem_positions:
                start_time = time.time()
                
                # 執行實際的JOIN查詢
                cursor.execute('''
                    SELECT pr.*, sg.range_high, sg.range_low, sg.direction as group_direction
                    FROM position_records pr
                    JOIN (
                        SELECT * FROM strategy_groups
                        WHERE date = ?
                        ORDER BY id DESC
                    ) sg ON pr.group_id = sg.group_id
                    WHERE pr.id = ? AND pr.status = 'ACTIVE'
                ''', (date.today().isoformat(), position_id))
                
                row = cursor.fetchone()
                elapsed = (time.time() - start_time) * 1000
                
                print(f"📊 部位{position_id}:")
                print(f"  - 查詢時間: {elapsed:.1f}ms")
                print(f"  - 查詢結果: {'成功' if row else '失敗'}")
                
                if elapsed > 100:
                    print(f"  ⚠️ 查詢時間過長: {elapsed:.1f}ms")
                
                if not row:
                    print(f"  ❌ 查詢失敗 - 這可能是問題原因")
                    
                    # 嘗試簡化查詢
                    simple_start = time.time()
                    cursor.execute('''
                        SELECT * FROM position_records 
                        WHERE id = ? AND status = 'ACTIVE'
                    ''', (position_id,))
                    simple_row = cursor.fetchone()
                    simple_elapsed = (time.time() - simple_start) * 1000
                    
                    print(f"  🔍 簡化查詢:")
                    print(f"    - 查詢時間: {simple_elapsed:.1f}ms")
                    print(f"    - 查詢結果: {'成功' if simple_row else '失敗'}")
                    
                    if simple_row and not row:
                        print(f"  🚨 JOIN查詢問題確認：簡化查詢成功但JOIN失敗")
                
    except Exception as e:
        print(f"❌ JOIN查詢測試失敗: {e}")

def test_concurrent_query_simulation():
    """測試併發查詢模擬"""
    print("\n🔍 測試併發查詢模擬...")
    
    import threading
    import random
    
    db_path = "multi_group_strategy.db"
    problem_positions = [133, 134, 135]
    results = []
    
    def query_worker(position_id, worker_id):
        """查詢工作線程"""
        try:
            # 隨機延遲模擬真實併發
            time.sleep(random.uniform(0, 0.05))
            
            start_time = time.time()
            with sqlite3.connect(db_path, timeout=1.0) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT pr.*, sg.range_high, sg.range_low, sg.direction as group_direction
                    FROM position_records pr
                    JOIN (
                        SELECT * FROM strategy_groups
                        WHERE date = ?
                        ORDER BY id DESC
                    ) sg ON pr.group_id = sg.group_id
                    WHERE pr.id = ? AND pr.status = 'ACTIVE'
                ''', (date.today().isoformat(), position_id))
                
                row = cursor.fetchone()
                elapsed = (time.time() - start_time) * 1000
                
                result = {
                    'position_id': position_id,
                    'worker_id': worker_id,
                    'success': row is not None,
                    'elapsed_ms': elapsed,
                    'error': None
                }
                results.append(result)
                
        except Exception as e:
            result = {
                'position_id': position_id,
                'worker_id': worker_id,
                'success': False,
                'elapsed_ms': 0,
                'error': str(e)
            }
            results.append(result)
    
    # 啟動併發查詢
    threads = []
    for position_id in problem_positions:
        for worker_id in range(3):  # 每個部位3個併發查詢
            thread = threading.Thread(target=query_worker, args=(position_id, worker_id))
            threads.append(thread)
            thread.start()
    
    # 等待所有線程完成
    for thread in threads:
        thread.join()
    
    # 分析結果
    success_count = sum(1 for r in results if r['success'])
    total_count = len(results)
    success_rate = success_count / total_count if total_count > 0 else 0
    
    print(f"📊 併發查詢結果:")
    print(f"  - 總查詢數: {total_count}")
    print(f"  - 成功數: {success_count}")
    print(f"  - 成功率: {success_rate*100:.1f}%")
    
    if success_rate < 0.9:
        print(f"  ⚠️ 併發查詢成功率過低: {success_rate*100:.1f}%")
    
    # 顯示失敗詳情
    failed_results = [r for r in results if not r['success']]
    if failed_results:
        print(f"  ❌ 失敗查詢詳情:")
        for result in failed_results[:5]:  # 只顯示前5個
            print(f"    - 部位{result['position_id']}, 工作者{result['worker_id']}: {result['error']}")

def test_module_imports():
    """測試模組導入"""
    print("\n🔍 測試模組導入...")
    
    modules_to_test = [
        'optimized_risk_manager',
        'stop_loss_executor', 
        'simplified_order_tracker',
        'multi_group_database'
    ]
    
    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"✅ {module_name}: 導入成功")
        except ImportError as e:
            print(f"❌ {module_name}: 導入失敗 - {e}")
        except Exception as e:
            print(f"⚠️ {module_name}: 導入異常 - {e}")

def test_diagnostic_tool_import():
    """測試診斷工具導入"""
    print("\n🔍 測試診斷工具導入...")
    
    try:
        from async_lot_level_diagnostic_tool import AsyncLotLevelDiagnosticTool
        print("✅ AsyncLotLevelDiagnosticTool: 導入成功")
        
        # 創建診斷工具實例
        diagnostic_tool = AsyncLotLevelDiagnosticTool(console_enabled=False)
        print("✅ 診斷工具實例: 創建成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 診斷工具導入失敗: {e}")
        return False
    except Exception as e:
        print(f"⚠️ 診斷工具異常: {e}")
        return False

def test_simulator_import():
    """測試模擬器導入"""
    print("\n🔍 測試模擬器導入...")
    
    try:
        from async_lot_level_simulator import AsyncLotLevelSimulator
        print("✅ AsyncLotLevelSimulator: 導入成功")
        
        # 創建模擬器實例
        simulator = AsyncLotLevelSimulator(console_enabled=False)
        print("✅ 模擬器實例: 創建成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 模擬器導入失敗: {e}")
        return False
    except Exception as e:
        print(f"⚠️ 模擬器異常: {e}")
        return False

def run_safe_diagnostic_test():
    """運行安全診斷測試"""
    print("🧪 安全診斷測試開始")
    print("="*60)
    
    test_results = {
        'database_connectivity': False,
        'join_query_performance': False,
        'concurrent_query': False,
        'module_imports': False,
        'diagnostic_tool': False,
        'simulator': False
    }
    
    try:
        # 1. 測試資料庫連接
        test_results['database_connectivity'] = test_database_connectivity()
        
        # 2. 測試JOIN查詢性能
        if test_results['database_connectivity']:
            test_join_query_performance()
            test_results['join_query_performance'] = True
        
        # 3. 測試併發查詢
        if test_results['database_connectivity']:
            test_concurrent_query_simulation()
            test_results['concurrent_query'] = True
        
        # 4. 測試模組導入
        test_module_imports()
        test_results['module_imports'] = True
        
        # 5. 測試診斷工具
        test_results['diagnostic_tool'] = test_diagnostic_tool_import()
        
        # 6. 測試模擬器
        test_results['simulator'] = test_simulator_import()
        
    except Exception as e:
        print(f"❌ 測試過程出錯: {e}")
    
    # 總結報告
    print("\n" + "="*60)
    print("📊 測試結果總結")
    print("="*60)
    
    for test_name, result in test_results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    success_rate = passed_tests / total_tests * 100
    
    print(f"\n📊 總體結果: {passed_tests}/{total_tests} 通過 ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("✅ 系統狀態良好，可以進行診斷")
    elif success_rate >= 60:
        print("⚠️ 系統狀態一般，建議謹慎診斷")
    else:
        print("❌ 系統狀態不佳，不建議進行診斷")
    
    return test_results

def main():
    """主函數"""
    print("🔍 Async和口級別機制安全診斷測試")
    print("目的：在不影響現有系統的情況下檢查診斷工具可用性")
    print("="*80)
    
    # 檢查當前目錄
    current_dir = os.getcwd()
    print(f"📁 當前目錄: {current_dir}")
    
    # 檢查關鍵文件
    key_files = [
        "multi_group_strategy.db",
        "simple_integrated.py",
        "async_lot_level_diagnostic_tool.py",
        "async_lot_level_simulator.py"
    ]
    
    print(f"\n📋 檢查關鍵文件:")
    for file_name in key_files:
        if os.path.exists(file_name):
            file_size = os.path.getsize(file_name)
            print(f"✅ {file_name}: 存在 ({file_size} bytes)")
        else:
            print(f"❌ {file_name}: 不存在")
    
    # 運行測試
    test_results = run_safe_diagnostic_test()
    
    # 提供建議
    print("\n" + "="*80)
    print("💡 建議")
    print("="*80)
    
    if test_results['database_connectivity']:
        print("✅ 資料庫連接正常，可以進行資料庫相關診斷")
    else:
        print("❌ 資料庫連接異常，請檢查資料庫文件和權限")
    
    if test_results['diagnostic_tool']:
        print("✅ 診斷工具可用，可以進行詳細診斷")
    else:
        print("❌ 診斷工具不可用，請檢查文件和依賴")
    
    if test_results['simulator']:
        print("✅ 模擬器可用，可以進行安全模擬測試")
    else:
        print("❌ 模擬器不可用，請檢查文件和依賴")
    
    print("\n🎯 下一步建議:")
    if all(test_results.values()):
        print("1. 運行完整診斷工具")
        print("2. 執行模擬測試")
        print("3. 分析診斷結果")
    else:
        print("1. 修復失敗的測試項目")
        print("2. 重新運行安全測試")
        print("3. 確認系統狀態後再進行診斷")


if __name__ == "__main__":
    main()
