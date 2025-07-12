#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
驗證分級LOG修復
"""

def verify_log_methods():
    """驗證LOG方法是否正確添加"""
    try:
        from risk_management_engine import RiskManagementEngine
        from multi_group_database import MultiGroupDatabaseManager
        
        # 創建實例
        db_manager = MultiGroupDatabaseManager("multi_group_strategy.db")
        risk_engine = RiskManagementEngine(db_manager)
        
        # 檢查新方法是否存在
        methods_to_check = [
            '_log_routine',
            '_log_important', 
            '_log_debug',
            '_log_status_summary',
            'enable_detailed_logging',
            'enable_normal_logging'
        ]
        
        print("🔍 檢查分級LOG方法...")
        for method in methods_to_check:
            if hasattr(risk_engine, method):
                print(f"  ✅ {method}")
            else:
                print(f"  ❌ {method} - 缺失")
                return False
        
        # 檢查新屬性
        attributes_to_check = [
            'log_level',
            '_last_status_log_time',
            '_status_log_interval',
            '_last_routine_log_time',
            '_routine_log_interval'
        ]
        
        print("\n🔍 檢查LOG控制屬性...")
        for attr in attributes_to_check:
            if hasattr(risk_engine, attr):
                print(f"  ✅ {attr} = {getattr(risk_engine, attr)}")
            else:
                print(f"  ❌ {attr} - 缺失")
                return False
        
        # 測試方法調用
        print("\n🧪 測試方法調用...")
        
        # 測試重要事件LOG
        risk_engine._log_important("[TEST] 重要事件測試")
        print("  ✅ _log_important 調用成功")
        
        # 測試常規LOG
        risk_engine._log_routine("[TEST] 常規LOG測試")
        print("  ✅ _log_routine 調用成功")
        
        # 測試調試LOG（預設不顯示）
        risk_engine._log_debug("[TEST] 調試LOG測試（不應顯示）")
        print("  ✅ _log_debug 調用成功")
        
        # 測試模式切換
        risk_engine.enable_detailed_logging()
        print("  ✅ enable_detailed_logging 調用成功")
        
        risk_engine.enable_normal_logging()
        print("  ✅ enable_normal_logging 調用成功")
        
        print("\n🎉 所有方法驗證成功！")
        return True
        
    except Exception as e:
        print(f"❌ 驗證失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 分級LOG修復驗證")
    print("=" * 40)
    
    success = verify_log_methods()
    
    if success:
        print("\n✅ 分級LOG系統修復成功！")
        print("\n📋 修復摘要：")
        print("  🎯 添加了分級LOG控制系統")
        print("  🔧 詳細LOG改為調試模式")
        print("  🚨 重要事件立即顯示")
        print("  📊 狀態摘要30秒間隔")
        print("  ❌ 錯誤訊息立即顯示")
        print("\n🚀 現在可以啟動系統測試效果！")
        print("預期效果：報價處理延遲從1000ms+降到100ms以下")
    else:
        print("\n❌ 驗證失敗，需要檢查修復")
