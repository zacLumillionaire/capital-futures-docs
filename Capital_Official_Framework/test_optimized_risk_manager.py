"""
優化風險管理器測試腳本
用於安全測試和驗證優化風險管理器的功能
"""

import sys
import os
import time
from datetime import datetime

# 添加路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_optimized_risk_manager():
    """測試優化風險管理器"""
    print("🚀 開始測試優化風險管理器...")
    
    try:
        # 1. 測試模組導入
        print("\n📦 測試模組導入...")
        from optimized_risk_manager import create_optimized_risk_manager
        print("✅ 優化風險管理器模組導入成功")
        
        # 2. 測試多組資料庫管理器
        print("\n📊 測試資料庫管理器...")
        from multi_group_database import MultiGroupDatabaseManager
        db_manager = MultiGroupDatabaseManager()
        print("✅ 資料庫管理器創建成功")
        
        # 3. 創建優化風險管理器
        print("\n🎯 創建優化風險管理器...")
        risk_manager = create_optimized_risk_manager(
            db_manager=db_manager,
            console_enabled=True
        )
        print("✅ 優化風險管理器創建成功")
        
        # 4. 測試基本功能
        print("\n🔧 測試基本功能...")
        
        # 測試統計信息
        stats = risk_manager.get_stats()
        print(f"📊 初始統計: {stats}")
        
        # 測試模擬部位
        test_position = {
            'id': 'test_001',
            'direction': 'LONG',
            'entry_price': 22000.0,
            'range_high': 22050.0,
            'range_low': 21950.0,
            'group_id': 1
        }
        
        print("\n🎯 測試新部位事件...")
        risk_manager.on_new_position(test_position)
        print("✅ 新部位事件處理成功")
        
        # 測試價格更新
        print("\n📈 測試價格更新...")
        test_prices = [22010.0, 22020.0, 22015.0, 22025.0]
        
        for i, price in enumerate(test_prices):
            start_time = time.perf_counter()
            results = risk_manager.update_price(price)
            processing_time = (time.perf_counter() - start_time) * 1000
            
            print(f"價格 {price}: 處理時間 {processing_time:.2f}ms, 結果: {results}")
        
        # 測試部位移除
        print("\n🗑️ 測試部位移除...")
        risk_manager.on_position_closed('test_001')
        print("✅ 部位移除成功")
        
        # 最終統計
        final_stats = risk_manager.get_stats()
        print(f"\n📊 最終統計: {final_stats}")
        
        print("\n🎉 所有測試通過！優化風險管理器運行正常")
        return True
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def performance_test():
    """性能測試"""
    print("\n🚀 開始性能測試...")
    
    try:
        from optimized_risk_manager import create_optimized_risk_manager
        from multi_group_database import MultiGroupDatabaseManager
        
        db_manager = MultiGroupDatabaseManager()
        risk_manager = create_optimized_risk_manager(db_manager, console_enabled=False)
        
        # 添加測試部位
        for i in range(10):
            test_position = {
                'id': f'perf_test_{i}',
                'direction': 'LONG' if i % 2 == 0 else 'SHORT',
                'entry_price': 22000.0 + i * 10,
                'range_high': 22050.0,
                'range_low': 21950.0,
                'group_id': i + 1
            }
            risk_manager.on_new_position(test_position)
        
        # 性能測試：1000次價格更新
        print("📊 執行1000次價格更新測試...")
        start_time = time.perf_counter()
        
        for i in range(1000):
            price = 22000.0 + (i % 100)
            risk_manager.update_price(price)
        
        total_time = time.perf_counter() - start_time
        avg_time = (total_time / 1000) * 1000  # 毫秒
        
        print(f"✅ 性能測試完成:")
        print(f"   總時間: {total_time:.3f} 秒")
        print(f"   平均處理時間: {avg_time:.3f} 毫秒/次")
        print(f"   處理速度: {1000/total_time:.0f} 次/秒")
        
        # 獲取統計信息
        stats = risk_manager.get_stats()
        print(f"📊 性能統計: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ 性能測試失敗: {e}")
        return False

def integration_test():
    """整合測試 - 模擬實際使用場景"""
    print("\n🚀 開始整合測試...")
    
    try:
        from optimized_risk_manager import create_optimized_risk_manager
        from multi_group_database import MultiGroupDatabaseManager
        
        db_manager = MultiGroupDatabaseManager()
        risk_manager = create_optimized_risk_manager(db_manager, console_enabled=True)
        
        print("📊 模擬實際交易場景...")
        
        # 場景1: 建立多個部位
        positions = [
            {'id': 'pos_1', 'direction': 'LONG', 'entry_price': 22000.0},
            {'id': 'pos_2', 'direction': 'LONG', 'entry_price': 22005.0},
            {'id': 'pos_3', 'direction': 'SHORT', 'entry_price': 22010.0}
        ]
        
        for pos in positions:
            pos.update({
                'range_high': 22050.0,
                'range_low': 21950.0,
                'group_id': 1
            })
            risk_manager.on_new_position(pos)
            print(f"✅ 建立部位: {pos['id']} {pos['direction']} @{pos['entry_price']}")
        
        # 場景2: 模擬價格波動
        print("\n📈 模擬價格波動...")
        price_sequence = [
            22015.0,  # 小幅上漲
            22020.0,  # 繼續上漲 (可能觸發移動停利啟動)
            22018.0,  # 小幅回調
            22025.0,  # 再次上漲
            21945.0,  # 大幅下跌 (可能觸發停損)
        ]
        
        for price in price_sequence:
            print(f"\n💰 當前價格: {price}")
            results = risk_manager.update_price(price)
            
            if results:
                for event_type, count in results.items():
                    if count > 0:
                        print(f"   🚨 {event_type}: {count} 個事件")
        
        # 場景3: 部位平倉
        print("\n🗑️ 模擬部位平倉...")
        for pos in positions:
            risk_manager.on_position_closed(pos['id'])
            print(f"✅ 平倉部位: {pos['id']}")
        
        # 最終統計
        final_stats = risk_manager.get_stats()
        print(f"\n📊 整合測試統計: {final_stats}")
        
        print("\n🎉 整合測試完成！")
        return True
        
    except Exception as e:
        print(f"❌ 整合測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    print("=" * 60)
    print("🎯 優化風險管理器測試套件")
    print("=" * 60)
    
    # 基本功能測試
    test1_result = test_optimized_risk_manager()
    
    # 性能測試
    test2_result = performance_test()
    
    # 整合測試
    test3_result = integration_test()
    
    # 總結
    print("\n" + "=" * 60)
    print("📊 測試結果總結:")
    print(f"   基本功能測試: {'✅ 通過' if test1_result else '❌ 失敗'}")
    print(f"   性能測試: {'✅ 通過' if test2_result else '❌ 失敗'}")
    print(f"   整合測試: {'✅ 通過' if test3_result else '❌ 失敗'}")
    
    all_passed = test1_result and test2_result and test3_result
    
    if all_passed:
        print("\n🎉 所有測試通過！優化風險管理器可以安全使用")
        print("\n💡 使用建議:")
        print("   1. 在 simple_integrated.py 中啟用優化風險管理器")
        print("   2. 監控 Console 輸出確認運行狀態")
        print("   3. 觀察處理時間改善效果")
        print("   4. 如有問題可隨時回退到原始系統")
    else:
        print("\n⚠️ 部分測試失敗，建議檢查問題後再使用")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
