#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任務2：基本數據源檢查
"""

import os
import json
from datetime import datetime
from pathlib import Path

def check_files():
    """檢查關鍵文件"""
    print("=" * 50)
    print("任務2：基本數據源檢查")
    print("=" * 50)
    
    # 檢查數據庫文件
    print("\n1. 數據庫文件檢查")
    print("-" * 30)
    
    db_file = Path("stock_data.sqlite")
    if db_file.exists():
        stat = db_file.stat()
        print(f"✅ 數據庫文件存在: {db_file.name}")
        print(f"   路徑: {db_file.absolute()}")
        print(f"   大小: {stat.st_size:,} bytes")
        print(f"   修改時間: {datetime.fromtimestamp(stat.st_mtime)}")
    else:
        print(f"❌ 數據庫文件不存在: {db_file.name}")
    
    # 檢查核心引擎文件
    print("\n2. 核心引擎文件檢查")
    print("-" * 30)
    
    engines = {
        'rev_web_trading_gui 使用': 'rev_multi_Profit-Funded Risk_多口.py',
        'mdd_gui 使用': 'experiment_analysis/exp_rev_multi_Profit-Funded Risk_多口.py'
    }
    
    for name, path in engines.items():
        file_path = Path(path)
        if file_path.exists():
            stat = file_path.stat()
            print(f"✅ {name}: {path}")
            print(f"   大小: {stat.st_size:,} bytes")
            print(f"   修改時間: {datetime.fromtimestamp(stat.st_mtime)}")
        else:
            print(f"❌ {name}: {path} 不存在")
    
    # 檢查配置模組
    print("\n3. 配置模組檢查")
    print("-" * 30)
    
    modules = ['shared.py', 'sqlite_connection.py', 'strategy_config_factory.py']
    
    for module in modules:
        file_path = Path(module)
        if file_path.exists():
            stat = file_path.stat()
            print(f"✅ {module}: {stat.st_size:,} bytes")
        else:
            print(f"❌ {module}: 不存在")
    
    # 檢查 GUI 文件
    print("\n4. GUI 文件檢查")
    print("-" * 30)
    
    gui_files = [
        'rev_web_trading_gui.py',
        'experiment_analysis/mdd_gui.py'
    ]
    
    for gui_file in gui_files:
        file_path = Path(gui_file)
        if file_path.exists():
            stat = file_path.stat()
            print(f"✅ {gui_file}: {stat.st_size:,} bytes")
        else:
            print(f"❌ {gui_file}: 不存在")

def test_imports():
    """測試關鍵模組導入"""
    print("\n5. 模組導入測試")
    print("-" * 30)
    
    modules_to_test = [
        'shared',
        'sqlite_connection', 
        'strategy_config_factory'
    ]
    
    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"✅ {module_name}: 導入成功")
        except Exception as e:
            print(f"❌ {module_name}: 導入失敗 - {e}")

def test_database_basic():
    """基本數據庫測試"""
    print("\n6. 基本數據庫連接測試")
    print("-" * 30)
    
    try:
        import sqlite_connection
        
        # 初始化連接
        sqlite_connection.init_sqlite_connection()
        print("✅ SQLite 連接初始化成功")
        
        # 測試連接
        with sqlite_connection.get_conn_cur_from_sqlite_with_adapter(as_dict=True) as (conn, cur):
            # 簡單查詢測試
            cur.execute("SELECT COUNT(*) as count FROM stock_prices LIMIT 1")
            result = cur.fetchone()
            print(f"✅ 數據庫查詢成功，記錄數: {result['count'] if result else 0}")
            
            # 測試日期範圍
            cur.execute("""
                SELECT MIN(trade_datetime::date) as min_date, 
                       MAX(trade_datetime::date) as max_date
                FROM stock_prices
            """)
            date_range = cur.fetchone()
            if date_range:
                print(f"✅ 數據日期範圍: {date_range['min_date']} 到 {date_range['max_date']}")
            
    except Exception as e:
        print(f"❌ 數據庫連接測試失敗: {e}")

def compare_file_sizes():
    """比較關鍵文件大小"""
    print("\n7. 文件大小比較")
    print("-" * 30)
    
    rev_file = Path('rev_multi_Profit-Funded Risk_多口.py')
    exp_file = Path('experiment_analysis/exp_rev_multi_Profit-Funded Risk_多口.py')
    
    if rev_file.exists() and exp_file.exists():
        rev_size = rev_file.stat().st_size
        exp_size = exp_file.stat().st_size
        
        print(f"rev_multi_Profit-Funded Risk_多口.py: {rev_size:,} bytes")
        print(f"exp_rev_multi_Profit-Funded Risk_多口.py: {exp_size:,} bytes")
        print(f"大小差異: {abs(rev_size - exp_size):,} bytes")
        
        if rev_size == exp_size:
            print("✅ 兩個文件大小相同")
        else:
            print("⚠️ 兩個文件大小不同")
    else:
        print("❌ 無法比較文件大小，文件不存在")

def generate_summary():
    """生成總結報告"""
    print("\n8. 總結")
    print("-" * 30)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'database_file_exists': Path("stock_data.sqlite").exists(),
        'rev_engine_exists': Path('rev_multi_Profit-Funded Risk_多口.py').exists(),
        'exp_engine_exists': Path('experiment_analysis/exp_rev_multi_Profit-Funded Risk_多口.py').exists(),
        'shared_module_exists': Path('shared.py').exists(),
        'sqlite_connection_exists': Path('sqlite_connection.py').exists(),
        'config_factory_exists': Path('strategy_config_factory.py').exists()
    }
    
    # 保存報告
    with open('任務2_基本檢查報告.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("✅ 基本檢查完成")
    print(f"📊 報告已保存到: 任務2_基本檢查報告.json")

def main():
    """主函數"""
    check_files()
    test_imports()
    test_database_basic()
    compare_file_sizes()
    generate_summary()

if __name__ == "__main__":
    main()
