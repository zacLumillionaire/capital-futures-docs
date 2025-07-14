#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
詳細部位狀態檢查工具
深入檢查移動停利相關的資料庫結構和數據
"""

import sqlite3
import json
from datetime import datetime

def check_database_structure():
    """檢查資料庫結構"""
    print("🔍 檢查資料庫結構...")
    
    with sqlite3.connect("multi_group_strategy.db") as conn:
        cursor = conn.cursor()
        
        # 檢查 position_records 表結構
        print("\n📋 position_records 表結構:")
        cursor.execute("PRAGMA table_info(position_records)")
        columns = cursor.fetchall()
        
        for col in columns:
            col_id, name, data_type, not_null, default_val, pk = col
            print(f"   {name}: {data_type} {'NOT NULL' if not_null else ''} {'PK' if pk else ''}")
        
        # 檢查 risk_management_states 表結構
        print("\n📋 risk_management_states 表結構:")
        try:
            cursor.execute("PRAGMA table_info(risk_management_states)")
            risk_columns = cursor.fetchall()
            
            if risk_columns:
                for col in risk_columns:
                    col_id, name, data_type, not_null, default_val, pk = col
                    print(f"   {name}: {data_type} {'NOT NULL' if not_null else ''} {'PK' if pk else ''}")
            else:
                print("   ❌ risk_management_states 表不存在或為空")
        except Exception as e:
            print(f"   ❌ 檢查 risk_management_states 表失敗: {e}")

def check_position_details():
    """檢查部位詳細狀態"""
    print("\n🔍 檢查部位詳細狀態...")
    
    with sqlite3.connect("multi_group_strategy.db") as conn:
        cursor = conn.cursor()
        
        # 獲取所有活躍部位的完整信息
        cursor.execute("SELECT * FROM position_records WHERE status = 'ACTIVE' ORDER BY id DESC")
        positions = cursor.fetchall()
        
        # 獲取列名
        cursor.execute("PRAGMA table_info(position_records)")
        columns = [col[1] for col in cursor.fetchall()]
        
        print(f"找到 {len(positions)} 個活躍部位:")
        
        for pos in positions:
            pos_dict = dict(zip(columns, pos))
            pos_id = pos_dict['id']
            
            print(f"\n📊 部位 {pos_id}:")
            
            # 顯示關鍵字段
            key_fields = [
                'group_id', 'lot_id', 'direction', 'entry_price', 'status',
                'trailing_activated', 'peak_price', 'trailing_activation_points',
                'trailing_pullback_ratio', 'created_at'
            ]
            
            for field in key_fields:
                if field in pos_dict:
                    value = pos_dict[field]
                    print(f"   {field}: {value}")
                else:
                    print(f"   {field}: [欄位不存在]")
            
            # 檢查風險管理狀態
            try:
                cursor.execute("SELECT * FROM risk_management_states WHERE position_id = ?", (pos_id,))
                risk_state = cursor.fetchone()
                
                if risk_state:
                    # 獲取風險管理狀態的列名
                    cursor.execute("PRAGMA table_info(risk_management_states)")
                    risk_columns = [col[1] for col in cursor.fetchall()]
                    risk_dict = dict(zip(risk_columns, risk_state))
                    
                    print(f"   🎯 風險管理狀態:")
                    for field, value in risk_dict.items():
                        if field != 'position_id':
                            print(f"      {field}: {value}")
                else:
                    print(f"   ❌ 無風險管理狀態記錄")
                    
            except Exception as e:
                print(f"   ❌ 檢查風險管理狀態失敗: {e}")

def check_trailing_stop_configuration():
    """檢查移動停利配置"""
    print("\n🔍 檢查移動停利配置...")
    
    # 檢查配置文件
    config_files = [
        'multi_group_config.py',
        'user_config.py'
    ]
    
    for config_file in config_files:
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"\n📋 檢查 {config_file}:")
            
            # 查找移動停利相關配置
            if 'trailing' in content.lower():
                print("   ✅ 包含移動停利配置")
                
                # 提取相關配置行
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'trailing' in line.lower() and ('=' in line or ':' in line):
                        print(f"   第{i+1}行: {line.strip()}")
            else:
                print("   ❌ 未找到移動停利配置")
                
        except FileNotFoundError:
            print(f"   ❌ 找不到配置文件: {config_file}")
        except Exception as e:
            print(f"   ❌ 讀取配置文件失敗: {e}")

def check_risk_engine_status():
    """檢查風險引擎狀態"""
    print("\n🔍 檢查風險引擎狀態...")
    
    try:
        # 檢查風險引擎相關文件
        with open('risk_management_engine.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("📋 風險引擎關鍵功能檢查:")
        
        # 檢查移動停利啟動邏輯
        if 'def check_trailing_stop_activation' in content:
            print("   ✅ 包含移動停利啟動檢查方法")
        else:
            print("   ❌ 缺少移動停利啟動檢查方法")
        
        # 檢查峰值更新邏輯
        if 'def update_peak_price' in content:
            print("   ✅ 包含峰值價格更新方法")
        else:
            print("   ❌ 缺少峰值價格更新方法")
        
        # 檢查平倉觸發邏輯
        if 'def check_exit_conditions' in content:
            print("   ✅ 包含平倉條件檢查方法")
        else:
            print("   ❌ 缺少平倉條件檢查方法")
        
        # 檢查移動停利計算
        if 'trailing_stop_price' in content:
            print("   ✅ 包含移動停利價格計算")
        else:
            print("   ❌ 缺少移動停利價格計算")
            
    except FileNotFoundError:
        print("   ❌ 找不到 risk_management_engine.py")
    except Exception as e:
        print(f"   ❌ 檢查風險引擎失敗: {e}")

def analyze_log_patterns():
    """分析日誌模式"""
    print("\n🔍 分析日誌模式...")
    
    # 從用戶提供的日誌分析問題
    log_analysis = {
        "移動停利啟動": "✅ 日誌顯示移動停利已啟動",
        "峰值更新": "✅ 日誌顯示峰值價格正在更新",
        "風險監控": "✅ 風險引擎正在監控部位",
        "平倉執行": "❌ 未看到平倉執行日誌",
        "移停計數": "❌ 移停計數始終為 0/2"
    }
    
    print("📊 日誌分析結果:")
    for item, status in log_analysis.items():
        print(f"   {status} {item}")
    
    print("\n🔍 關鍵問題識別:")
    print("   1. 移動停利啟動了但計數器沒有更新")
    print("   2. 峰值價格在更新但可能沒有觸發平倉邏輯")
    print("   3. 風險引擎監控正常但平倉機制可能斷開")

def generate_diagnosis_summary():
    """生成診斷總結"""
    print("\n📋 診斷總結")
    print("=" * 50)
    
    issues = [
        "部位記錄中 trailing_activation_points 為 None",
        "移動停利啟動狀態未正確更新到資料庫",
        "風險管理狀態表可能缺少 current_price 欄位",
        "移動停利計數器與實際啟動狀態不同步",
        "平倉條件判斷可能沒有正確執行"
    ]
    
    print("🔍 發現的主要問題:")
    for i, issue in enumerate(issues, 1):
        print(f"   {i}. {issue}")
    
    print("\n🎯 建議檢查重點:")
    print("   1. 檢查部位創建時移動停利參數的設置")
    print("   2. 檢查移動停利啟動後的資料庫更新邏輯")
    print("   3. 檢查風險管理狀態表的結構和數據")
    print("   4. 檢查平倉條件判斷和執行的連接")
    
    # 保存診斷結果
    diagnosis = {
        'timestamp': datetime.now().isoformat(),
        'issues': issues,
        'status': 'CRITICAL',
        'next_steps': [
            '檢查部位創建邏輯',
            '修復移動停利參數設置',
            '檢查資料庫結構一致性',
            '驗證平倉執行機制'
        ]
    }
    
    with open('移動停利問題診斷.json', 'w', encoding='utf-8') as f:
        json.dump(diagnosis, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 診斷結果已保存: 移動停利問題診斷.json")

def main():
    """主檢查函數"""
    print("🚀 詳細部位狀態檢查")
    print("=" * 50)
    
    check_database_structure()
    check_position_details()
    check_trailing_stop_configuration()
    check_risk_engine_status()
    analyze_log_patterns()
    generate_diagnosis_summary()

if __name__ == "__main__":
    main()
