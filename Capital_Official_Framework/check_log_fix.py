print("🔍 檢查分級LOG修復...")
try:
    from risk_management_engine import RiskManagementEngine
    print("✅ RiskManagementEngine 導入成功")
    
    # 檢查新方法是否存在
    methods = ['_log_routine', '_log_important', '_log_debug', 'enable_detailed_logging']
    for method in methods:
        if hasattr(RiskManagementEngine, method):
            print(f"✅ 方法 {method} 存在")
        else:
            print(f"❌ 方法 {method} 缺失")
    
    print("🎉 分級LOG修復檢查完成！")
    
except Exception as e:
    print(f"❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()
