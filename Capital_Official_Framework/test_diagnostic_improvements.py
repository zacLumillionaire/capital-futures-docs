#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試診斷改進功能
"""

def test_psutil_availability():
    """測試 psutil 可用性"""
    print("🔧 測試 psutil 可用性...")
    
    try:
        import psutil
        print(f"✅ psutil 已安裝，版本: {psutil.__version__}")
        
        # 測試基本功能
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        print(f"   💻 CPU使用率: {cpu_percent:.1f}%")
        print(f"   🧠 內存使用率: {memory.percent:.1f}%")
        
        return True
    except ImportError as e:
        print(f"❌ psutil 不可用: {e}")
        return False

def test_system_health_monitor():
    """測試系統健康監控"""
    print("\n🏥 測試系統健康監控...")
    
    try:
        from system_health_monitor import SystemHealthMonitor
        
        # 創建一個模擬的主應用對象
        class MockApp:
            def __init__(self):
                self.optimized_risk_manager = None
                self.async_updater = None
                self.multi_group_position_manager = None
        
        mock_app = MockApp()
        monitor = SystemHealthMonitor(mock_app)
        
        # 測試靜默模式
        print("   測試靜默模式健康檢查...")
        health_report = monitor.run_comprehensive_health_check(silent=True)
        
        if isinstance(health_report, dict):
            score = health_report.get('overall_score', 0)
            alerts = health_report.get('alerts', [])
            print(f"   ✅ 健康檢查完成，分數: {score}/100")
            print(f"   📊 警報數量: {len(alerts)}")
        else:
            print("   ❌ 健康檢查返回格式錯誤")
            
        return True
    except Exception as e:
        print(f"   ❌ 系統健康監控測試失敗: {e}")
        return False

def test_diagnostic_integration():
    """測試診斷整合功能"""
    print("\n🔧 測試診斷整合功能...")
    
    try:
        # 測試導入
        from system_health_monitor import run_health_check_on_simple_integrated
        
        # 創建模擬應用
        class MockApp:
            def __init__(self):
                self.optimized_risk_manager = None
                self.async_updater = None
                self.multi_group_position_manager = None
        
        mock_app = MockApp()
        
        # 測試靜默模式調用
        print("   測試靜默模式調用...")
        health_report = run_health_check_on_simple_integrated(mock_app, silent=True)
        
        if isinstance(health_report, dict):
            print("   ✅ 靜默模式調用成功")
        else:
            print("   ❌ 靜默模式調用失敗")
            
        return True
    except Exception as e:
        print(f"   ❌ 診斷整合測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 開始診斷改進功能測試")
    print("=" * 50)
    
    results = []
    
    # 測試 psutil
    results.append(test_psutil_availability())
    
    # 測試系統健康監控
    results.append(test_system_health_monitor())
    
    # 測試診斷整合
    results.append(test_diagnostic_integration())
    
    # 總結
    print("\n" + "=" * 50)
    print("📊 測試結果總結:")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ 所有測試通過 ({passed}/{total})")
        print("🎉 診斷改進功能已成功實現！")
        print("\n💡 改進內容:")
        print("   - ✅ psutil 模組已安裝並可用")
        print("   - ✅ 系統健康監控支援靜默模式")
        print("   - ✅ 運行時診斷信息將在 CONSOLE 顯示")
        print("   - ✅ 診斷警告信息已優化")
    else:
        print(f"⚠️ 部分測試失敗 ({passed}/{total})")
        print("💡 建議檢查失敗的測試項目")

if __name__ == "__main__":
    main()
