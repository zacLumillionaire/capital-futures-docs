# -*- coding: utf-8 -*-
"""
測試策略配置參數修改
驗證移動停利參數是否正確更新
"""

def test_multi_group_config():
    """測試多組策略配置"""
    print("🧪 測試多組策略配置參數")
    print("=" * 50)
    
    try:
        from multi_group_config import create_preset_configs, MultiGroupStrategyConfig
        
        # 測試標準3口配置
        config = MultiGroupStrategyConfig(
            total_groups=1,
            lots_per_group=3
        )
        
        print("📋 標準3口配置:")
        print(f"總組數: {config.total_groups}")
        print(f"每組口數: {config.lots_per_group}")
        
        # 檢查第一組的口數規則
        if config.groups:
            group = config.groups[0]
            print(f"\n🔍 組{group.group_id}的口數規則:")
            
            for rule in group.lot_rules:
                print(f"  第{rule.lot_id}口:")
                print(f"    啟動點數: {rule.trailing_activation}點")
                print(f"    回撤比例: {float(rule.trailing_pullback)*100:.0f}%")
                if rule.protective_stop_multiplier:
                    print(f"    保護倍數: {rule.protective_stop_multiplier}倍")
                print()
        
        # 驗證參數是否符合要求
        expected_params = [
            (1, 15, 0.10, None),      # 第1口: 15點, 10%
            (2, 40, 0.10, 2.0),       # 第2口: 40點, 10%, 2倍保護
            (3, 41, 0.20, 2.0)        # 第3口: 41點, 20%, 2倍保護
        ]
        
        print("✅ 參數驗證:")
        all_correct = True
        
        for i, (lot_id, expected_activation, expected_pullback, expected_protection) in enumerate(expected_params):
            if i < len(group.lot_rules):
                rule = group.lot_rules[i]
                
                # 檢查啟動點數
                if float(rule.trailing_activation) == expected_activation:
                    print(f"  ✅ 第{lot_id}口啟動點數: {rule.trailing_activation}點 (正確)")
                else:
                    print(f"  ❌ 第{lot_id}口啟動點數: {rule.trailing_activation}點 (應為{expected_activation}點)")
                    all_correct = False
                
                # 檢查回撤比例
                if float(rule.trailing_pullback) == expected_pullback:
                    print(f"  ✅ 第{lot_id}口回撤比例: {float(rule.trailing_pullback)*100:.0f}% (正確)")
                else:
                    print(f"  ❌ 第{lot_id}口回撤比例: {float(rule.trailing_pullback)*100:.0f}% (應為{expected_pullback*100:.0f}%)")
                    all_correct = False
                
                # 檢查保護倍數
                if rule.protective_stop_multiplier == expected_protection:
                    if expected_protection:
                        print(f"  ✅ 第{lot_id}口保護倍數: {rule.protective_stop_multiplier}倍 (正確)")
                    else:
                        print(f"  ✅ 第{lot_id}口無保護倍數 (正確)")
                else:
                    print(f"  ❌ 第{lot_id}口保護倍數不正確")
                    all_correct = False
        
        if all_correct:
            print("\n🎉 所有參數配置正確！")
        else:
            print("\n⚠️ 部分參數配置不正確")
        
        return all_correct
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_config():
    """測試資料庫配置"""
    print("\n🧪 測試資料庫預設規則")
    print("=" * 50)
    
    try:
        from exit_mechanism_database_extension import ExitMechanismDatabaseExtension
        from multi_group_database import MultiGroupDatabaseManager
        
        # 創建資料庫管理器
        db_manager = MultiGroupDatabaseManager("test_config.db")
        
        # 創建資料庫擴展
        db_extension = ExitMechanismDatabaseExtension(db_manager)
        
        print("📊 初始化資料庫擴展...")
        success = db_extension.initialize_database()
        
        if success:
            print("✅ 資料庫擴展初始化成功")
            
            # 查詢預設規則
            cursor = db_manager.get_cursor()
            cursor.execute('''
                SELECT lot_number, trailing_activation_points, trailing_pullback_ratio, 
                       protective_stop_multiplier, description
                FROM lot_exit_rules 
                WHERE is_default = 1 
                ORDER BY lot_number
            ''')
            
            rules = cursor.fetchall()
            
            print("\n📋 資料庫中的預設規則:")
            for rule in rules:
                lot_num, activation, pullback, protection, desc = rule
                print(f"  第{lot_num}口: {activation}點啟動, {pullback*100:.0f}%回撤", end="")
                if protection:
                    print(f", {protection}倍保護")
                else:
                    print()
                print(f"    描述: {desc}")
            
            # 驗證規則
            expected_db_params = [
                (1, 15, 0.10, None),
                (2, 40, 0.10, 2.0),
                (3, 41, 0.20, 2.0)
            ]
            
            print("\n✅ 資料庫參數驗證:")
            db_correct = True
            
            for i, (expected_lot, expected_activation, expected_pullback, expected_protection) in enumerate(expected_db_params):
                if i < len(rules):
                    lot_num, activation, pullback, protection, _ = rules[i]
                    
                    if (lot_num == expected_lot and 
                        activation == expected_activation and 
                        abs(pullback - expected_pullback) < 0.001 and
                        protection == expected_protection):
                        print(f"  ✅ 第{lot_num}口規則正確")
                    else:
                        print(f"  ❌ 第{lot_num}口規則不正確")
                        db_correct = False
            
            if db_correct:
                print("\n🎉 資料庫規則配置正確！")
            else:
                print("\n⚠️ 資料庫規則配置不正確")
            
            return db_correct
        else:
            print("❌ 資料庫擴展初始化失敗")
            return False
            
    except Exception as e:
        print(f"❌ 資料庫測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_summary():
    """顯示修改摘要"""
    print("\n📋 配置修改摘要")
    print("=" * 60)
    
    print("🎯 修改內容：")
    print("  第一口：15點啟動，回撤 20% → 10%")
    print("  第二口：40點啟動，回撤 20% → 10%")
    print("  第三口：65點啟動 → 41點啟動，回撤保持 20%")
    
    print("\n📊 修改前後對比：")
    print("  口數 | 啟動點數 | 回撤比例 | 保護倍數")
    print("  -----|----------|----------|----------")
    print("  第1口 |   15點   | 20%→10% |    無")
    print("  第2口 |   40點   | 20%→10% |   2倍")
    print("  第3口 | 65→41點  |   20%   |   2倍")
    
    print("\n🔧 修改檔案：")
    print("  ✅ multi_group_config.py - 程式碼配置")
    print("  ✅ exit_mechanism_database_extension.py - 資料庫預設值")
    
    print("\n🛡️ 安全性：")
    print("  ✅ 只修改配置參數，不影響交易邏輯")
    print("  ✅ 保持所有保護機制不變")
    print("  ✅ 可隨時回退到原始配置")
    
    print("\n🚀 生效方式：")
    print("  - 新建的策略組會自動使用新參數")
    print("  - 現有運行中的策略組不受影響")
    print("  - 重新啟動系統後全面生效")

if __name__ == "__main__":
    print("🔧 策略配置參數修改測試")
    print("=" * 60)
    
    # 測試1: 多組配置
    config_success = test_multi_group_config()
    
    # 測試2: 資料庫配置
    db_success = test_database_config()
    
    # 顯示摘要
    show_summary()
    
    print("\n🎯 測試結果：")
    if config_success and db_success:
        print("🎉 所有配置修改成功！")
        print("✅ 程式碼配置正確")
        print("✅ 資料庫配置正確")
        print("\n🚀 現在可以重新啟動系統使用新參數！")
    else:
        print("⚠️ 部分配置可能有問題")
        if not config_success:
            print("❌ 程式碼配置需要檢查")
        if not db_success:
            print("❌ 資料庫配置需要檢查")
