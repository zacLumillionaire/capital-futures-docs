#!/usr/bin/env python3
"""
SQLite性能測試腳本
比較PostgreSQL和SQLite的回測性能
"""

import time
import subprocess
import sys
import json
from pathlib import Path

def test_performance(use_sqlite=True, test_name="", start_date="2024-11-01", end_date="2024-11-05"):
    """測試回測性能"""
    print(f"\n🧪 {test_name}")
    print(f"📅 測試期間: {start_date} 至 {end_date}")
    print(f"🗄️ 數據源: {'SQLite (本機)' if use_sqlite else 'PostgreSQL (遠程)'}")
    
    # 修改配置文件中的USE_SQLITE設定
    config_file = Path(__file__).parent / "multi_Profit-Funded Risk_多口.py"
    
    # 讀取文件內容
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修改USE_SQLITE設定
    if use_sqlite:
        new_content = content.replace('USE_SQLITE = False', 'USE_SQLITE = True')
    else:
        new_content = content.replace('USE_SQLITE = True', 'USE_SQLITE = False')
    
    # 寫回文件
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    # 執行回測
    start_time = time.time()
    
    cmd = [
        sys.executable,
        'multi_Profit-Funded Risk_多口.py',
        '--start-date', start_date,
        '--end-date', end_date
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        print(f"⏱️ 執行時間: {execution_time:.2f} 秒")
        print(f"📊 返回碼: {result.returncode}")
        
        if result.returncode == 0:
            print("✅ 測試成功！")
            
            # 提取關鍵結果
            if result.stderr:
                lines = result.stderr.split('\n')
                for line in lines:
                    if '總損益' in line or '勝率' in line or '交易次數' in line:
                        print(f"📈 {line.strip()}")
        else:
            print("❌ 測試失敗")
            if result.stderr:
                print(f"錯誤: {result.stderr[-500:]}")
        
        return execution_time, result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏰ 測試超時（300秒）")
        return 300, False
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return 0, False

def main():
    """主測試函數"""
    print("🚀 SQLite vs PostgreSQL 性能比較測試")
    print("=" * 60)
    
    # 測試配置
    test_configs = [
        {
            'name': '短期測試 (5天)',
            'start_date': '2024-11-01',
            'end_date': '2024-11-05'
        },
        {
            'name': '中期測試 (1個月)',
            'start_date': '2024-11-01',
            'end_date': '2024-11-30'
        }
    ]
    
    results = []
    
    for config in test_configs:
        print(f"\n{'='*60}")
        print(f"📋 {config['name']}")
        print(f"{'='*60}")
        
        # 測試PostgreSQL
        pg_time, pg_success = test_performance(
            use_sqlite=False,
            test_name="PostgreSQL 性能測試",
            start_date=config['start_date'],
            end_date=config['end_date']
        )
        
        # 測試SQLite
        sqlite_time, sqlite_success = test_performance(
            use_sqlite=True,
            test_name="SQLite 性能測試",
            start_date=config['start_date'],
            end_date=config['end_date']
        )
        
        # 計算性能提升
        if pg_success and sqlite_success and pg_time > 0:
            improvement = pg_time / sqlite_time
            print(f"\n🎯 性能比較結果:")
            print(f"  PostgreSQL: {pg_time:.2f} 秒")
            print(f"  SQLite: {sqlite_time:.2f} 秒")
            print(f"  性能提升: {improvement:.1f}x 倍")
            
            if improvement > 5:
                print("🚀 顯著性能提升！")
            elif improvement > 2:
                print("✅ 良好性能提升")
            else:
                print("📊 輕微性能提升")
        
        results.append({
            'config': config['name'],
            'pg_time': pg_time,
            'sqlite_time': sqlite_time,
            'pg_success': pg_success,
            'sqlite_success': sqlite_success
        })
    
    # 總結報告
    print(f"\n{'='*60}")
    print("📊 性能測試總結報告")
    print(f"{'='*60}")
    
    for result in results:
        print(f"\n📋 {result['config']}:")
        if result['pg_success'] and result['sqlite_success']:
            improvement = result['pg_time'] / result['sqlite_time'] if result['sqlite_time'] > 0 else 0
            print(f"  PostgreSQL: {result['pg_time']:.2f}秒")
            print(f"  SQLite: {result['sqlite_time']:.2f}秒")
            print(f"  提升倍數: {improvement:.1f}x")
        else:
            print(f"  測試失敗 - PG: {result['pg_success']}, SQLite: {result['sqlite_success']}")
    
    # 恢復SQLite設定
    print(f"\n🔄 恢復SQLite設定...")
    test_performance(use_sqlite=True, test_name="恢復設定", start_date="2024-11-01", end_date="2024-11-01")
    
    print(f"\n✅ 性能測試完成！")

if __name__ == "__main__":
    main()
