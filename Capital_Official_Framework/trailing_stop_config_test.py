#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
各口移動停利自訂功能測試工具
用於驗證配置系統的正確性和性能
"""

import os
import sys
import time
import threading
from typing import Dict, List

# 添加當前目錄到路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from trailing_stop_config_manager import (
    TrailingStopConfigManager,
    MultiLotTrailingStopConfig,
    LotTrailingStopConfig
)


class TrailingStopConfigTester:
    """移動停利配置測試器"""
    
    def __init__(self):
        self.config_manager = TrailingStopConfigManager("test_trailing_config.json")
        self.test_results = []
        
    def run_all_tests(self):
        """執行所有測試"""
        print("🧪 開始執行各口移動停利自訂功能測試")
        print("=" * 60)
        
        # 測試1: 基本配置功能
        self.test_basic_config_operations()
        
        # 測試2: 預設配置
        self.test_preset_configurations()
        
        # 測試3: 參數驗證
        self.test_parameter_validation()
        
        # 測試4: 配置持久化
        self.test_config_persistence()
        
        # 測試5: 異步安全性
        self.test_async_safety()
        
        # 測試6: 性能測試
        self.test_performance()
        
        # 顯示測試結果
        self.show_test_results()
        
        # 清理測試文件
        self.cleanup_test_files()
    
    def test_basic_config_operations(self):
        """測試基本配置操作"""
        print("\n📋 測試1: 基本配置操作")
        
        try:
            # 創建配置
            config = MultiLotTrailingStopConfig()
            
            # 添加口數配置
            for lot_id in range(1, 4):
                lot_config = LotTrailingStopConfig(
                    lot_id=lot_id,
                    enabled=True,
                    activation_points=20.0 + lot_id * 10,
                    pullback_percent=15.0 + lot_id * 5
                )
                config.add_lot_config(lot_id, lot_config)
            
            # 驗證配置
            valid, errors = config.validate_all()
            assert valid, f"配置驗證失敗: {errors}"
            
            # 測試取得配置
            lot1_config = config.get_lot_config(1)
            assert lot1_config is not None, "無法取得第1口配置"
            assert lot1_config.activation_points == 30.0, "第1口啟動點數不正確"
            
            self.test_results.append(("基本配置操作", True, "所有基本操作正常"))
            print("✅ 基本配置操作測試通過")
            
        except Exception as e:
            self.test_results.append(("基本配置操作", False, str(e)))
            print(f"❌ 基本配置操作測試失敗: {e}")
    
    def test_preset_configurations(self):
        """測試預設配置"""
        print("\n📋 測試2: 預設配置")
        
        try:
            presets = self.config_manager.get_preset_configs()
            
            # 檢查預設配置數量
            assert len(presets) == 3, f"預設配置數量不正確: {len(presets)}"
            
            # 檢查預設配置名稱
            expected_names = [
                "保守配置 (10:15-10:30)",
                "積極配置 (11:00-11:02)", 
                "平衡配置 (08:58-09:02)"
            ]
            
            for name in expected_names:
                assert name in presets, f"缺少預設配置: {name}"
            
            # 測試應用預設配置
            for name, config in presets.items():
                valid, errors = config.validate_all()
                assert valid, f"預設配置 {name} 驗證失敗: {errors}"
                
                # 檢查配置完整性
                for lot_id in range(1, 4):
                    lot_config = config.get_lot_config(lot_id)
                    assert lot_config is not None, f"預設配置 {name} 缺少第{lot_id}口配置"
            
            self.test_results.append(("預設配置", True, "所有預設配置有效"))
            print("✅ 預設配置測試通過")
            
        except Exception as e:
            self.test_results.append(("預設配置", False, str(e)))
            print(f"❌ 預設配置測試失敗: {e}")
    
    def test_parameter_validation(self):
        """測試參數驗證"""
        print("\n📋 測試3: 參數驗證")
        
        try:
            # 測試有效參數
            valid_config = LotTrailingStopConfig(
                lot_id=1,
                activation_points=25.0,
                pullback_percent=20.0
            )
            valid, message = valid_config.validate()
            assert valid, f"有效參數驗證失敗: {message}"
            
            # 測試無效啟動點數
            invalid_activation = LotTrailingStopConfig(
                lot_id=1,
                activation_points=300.0,  # 超過最大值
                pullback_percent=20.0
            )
            valid, message = invalid_activation.validate()
            assert not valid, "無效啟動點數應該驗證失敗"
            
            # 測試無效回撤百分比
            invalid_pullback = LotTrailingStopConfig(
                lot_id=1,
                activation_points=25.0,
                pullback_percent=90.0  # 超過最大值
            )
            valid, message = invalid_pullback.validate()
            assert not valid, "無效回撤百分比應該驗證失敗"
            
            self.test_results.append(("參數驗證", True, "驗證邏輯正確"))
            print("✅ 參數驗證測試通過")
            
        except Exception as e:
            self.test_results.append(("參數驗證", False, str(e)))
            print(f"❌ 參數驗證測試失敗: {e}")
    
    def test_config_persistence(self):
        """測試配置持久化"""
        print("\n📋 測試4: 配置持久化")
        
        try:
            # 創建測試配置
            original_config = MultiLotTrailingStopConfig()
            original_config.global_enabled = True
            
            test_lot_config = LotTrailingStopConfig(
                lot_id=1,
                enabled=True,
                activation_points=35.0,
                pullback_percent=25.0
            )
            original_config.add_lot_config(1, test_lot_config)
            
            # 保存配置
            success = self.config_manager.save_config(original_config)
            assert success, "配置保存失敗"
            
            # 載入配置
            loaded_config = self.config_manager.load_config()
            
            # 驗證載入的配置
            assert loaded_config.global_enabled == original_config.global_enabled, "全局啟用狀態不一致"
            
            loaded_lot_config = loaded_config.get_lot_config(1)
            assert loaded_lot_config is not None, "載入的配置缺少第1口"
            assert loaded_lot_config.activation_points == 35.0, "啟動點數不一致"
            assert loaded_lot_config.pullback_percent == 25.0, "回撤百分比不一致"
            
            self.test_results.append(("配置持久化", True, "保存和載入正常"))
            print("✅ 配置持久化測試通過")
            
        except Exception as e:
            self.test_results.append(("配置持久化", False, str(e)))
            print(f"❌ 配置持久化測試失敗: {e}")
    
    def test_async_safety(self):
        """測試異步安全性"""
        print("\n📋 測試5: 異步安全性")
        
        try:
            results = []
            errors = []
            
            def worker_thread(thread_id):
                """工作線程"""
                try:
                    for i in range(10):
                        # 創建配置
                        config = self.config_manager.get_default_config()
                        
                        # 修改配置
                        lot_config = config.get_lot_config(1)
                        if lot_config:
                            lot_config.activation_points = 20.0 + thread_id + i
                        
                        # 驗證配置
                        valid, _ = config.validate_all()
                        results.append((thread_id, i, valid))
                        
                        time.sleep(0.01)  # 模擬處理時間
                        
                except Exception as e:
                    errors.append((thread_id, str(e)))
            
            # 啟動多個線程
            threads = []
            for i in range(5):
                thread = threading.Thread(target=worker_thread, args=(i,))
                threads.append(thread)
                thread.start()
            
            # 等待所有線程完成
            for thread in threads:
                thread.join()
            
            # 檢查結果
            assert len(errors) == 0, f"異步操作出現錯誤: {errors}"
            assert len(results) == 50, f"結果數量不正確: {len(results)}"
            
            self.test_results.append(("異步安全性", True, "多線程操作安全"))
            print("✅ 異步安全性測試通過")
            
        except Exception as e:
            self.test_results.append(("異步安全性", False, str(e)))
            print(f"❌ 異步安全性測試失敗: {e}")
    
    def test_performance(self):
        """測試性能"""
        print("\n📋 測試6: 性能測試")
        
        try:
            # 測試配置創建性能
            start_time = time.time()
            for i in range(1000):
                config = MultiLotTrailingStopConfig()
                for lot_id in range(1, 4):
                    lot_config = LotTrailingStopConfig(lot_id=lot_id)
                    config.add_lot_config(lot_id, lot_config)
            creation_time = time.time() - start_time
            
            # 測試驗證性能
            start_time = time.time()
            for i in range(1000):
                config = self.config_manager.get_default_config()
                config.validate_all()
            validation_time = time.time() - start_time
            
            # 測試參數取得性能
            start_time = time.time()
            for i in range(1000):
                self.config_manager.get_lot_trailing_params(1)
            param_time = time.time() - start_time
            
            # 性能要求檢查
            assert creation_time < 1.0, f"配置創建過慢: {creation_time:.3f}s"
            assert validation_time < 0.5, f"驗證過慢: {validation_time:.3f}s"
            assert param_time < 0.1, f"參數取得過慢: {param_time:.3f}s"
            
            performance_info = f"創建:{creation_time:.3f}s, 驗證:{validation_time:.3f}s, 參數:{param_time:.3f}s"
            self.test_results.append(("性能測試", True, performance_info))
            print(f"✅ 性能測試通過 ({performance_info})")
            
        except Exception as e:
            self.test_results.append(("性能測試", False, str(e)))
            print(f"❌ 性能測試失敗: {e}")
    
    def show_test_results(self):
        """顯示測試結果"""
        print("\n" + "=" * 60)
        print("📊 測試結果摘要")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        for test_name, success, details in self.test_results:
            status = "✅ 通過" if success else "❌ 失敗"
            print(f"{status} {test_name}: {details}")
            
            if success:
                passed += 1
            else:
                failed += 1
        
        print("-" * 60)
        print(f"總計: {passed + failed} 項測試")
        print(f"通過: {passed} 項")
        print(f"失敗: {failed} 項")
        
        if failed == 0:
            print("\n🎉 所有測試通過！各口移動停利自訂功能系統運作正常")
        else:
            print(f"\n⚠️ 有 {failed} 項測試失敗，請檢查相關功能")
    
    def cleanup_test_files(self):
        """清理測試文件"""
        try:
            if os.path.exists("test_trailing_config.json"):
                os.remove("test_trailing_config.json")
                print("\n🧹 測試文件已清理")
        except Exception as e:
            print(f"\n⚠️ 清理測試文件失敗: {e}")


def main():
    """主函數"""
    print("🚀 各口移動停利自訂功能測試工具")
    print("版本: 1.0.0")
    print("日期: 2025-07-18")
    
    tester = TrailingStopConfigTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
