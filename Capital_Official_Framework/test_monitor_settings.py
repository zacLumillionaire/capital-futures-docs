#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
監控設定測試腳本
測試不同的監控間隔和中斷判定設定
"""

import time

def test_monitor_configurations():
    """測試不同的監控配置"""
    print("🧪 監控設定測試")
    print("=" * 50)
    
    print("📋 目前的問題分析:")
    print("   - 原設定: 3秒檢查間隔，3秒無報價就判定中斷")
    print("   - 問題: 太敏感，市場正常的報價間隔也會被判定為中斷")
    print()
    
    print("🔧 建議的監控設定選項:")
    print()
    
    # 配置選項1: 保守設定
    print("📊 選項1: 保守設定（推薦）")
    print("   - 檢查間隔: 5秒")
    print("   - 中斷判定: 10秒無報價")
    print("   - 適用: 一般交易時段，減少誤報")
    print("   - 配置方法: app.configure_monitor_settings(5, 10)")
    print()
    
    # 配置選項2: 平衡設定
    print("📊 選項2: 平衡設定")
    print("   - 檢查間隔: 3秒")
    print("   - 中斷判定: 9秒無報價")
    print("   - 適用: 需要較快反應的場景")
    print("   - 配置方法: app.configure_monitor_settings(3, 9)")
    print()
    
    # 配置選項3: 寬鬆設定
    print("📊 選項3: 寬鬆設定")
    print("   - 檢查間隔: 8秒")
    print("   - 中斷判定: 16秒無報價")
    print("   - 適用: 盤後或低流動性時段")
    print("   - 配置方法: app.configure_monitor_settings(8, 16)")
    print()
    
    # 配置選項4: 敏感設定
    print("📊 選項4: 敏感設定（不推薦）")
    print("   - 檢查間隔: 2秒")
    print("   - 中斷判定: 4秒無報價")
    print("   - 適用: 測試或特殊需求")
    print("   - 配置方法: app.configure_monitor_settings(2, 4)")
    print("   - 注意: 可能產生過多誤報")
    print()

def simulate_monitoring_behavior():
    """模擬不同設定下的監控行為"""
    print("🎬 監控行為模擬")
    print("-" * 30)
    
    configurations = [
        {"name": "原設定", "interval": 3, "timeout": 3},
        {"name": "保守設定", "interval": 5, "timeout": 10},
        {"name": "平衡設定", "interval": 3, "timeout": 9},
        {"name": "寬鬆設定", "interval": 8, "timeout": 16}
    ]
    
    # 模擬報價間隔場景
    quote_gaps = [2, 4, 6, 8, 10, 12, 15]  # 不同的報價間隔（秒）
    
    print("📊 不同報價間隔下的監控反應:")
    print()
    
    for config in configurations:
        print(f"🔧 {config['name']} (檢查:{config['interval']}s, 判定:{config['timeout']}s)")
        
        for gap in quote_gaps:
            if gap <= config['timeout']:
                status = "✅ 正常"
            else:
                status = "❌ 中斷"
            
            print(f"   報價間隔{gap}s: {status}")
        print()

def create_monitor_config_guide():
    """創建監控配置指南"""
    print("📝 監控配置使用指南")
    print("=" * 40)
    
    print("🎯 如何選擇合適的設定:")
    print()
    
    print("1️⃣ 一般交易時段（09:00-13:30）")
    print("   推薦: 保守設定 (5秒檢查, 10秒判定)")
    print("   原因: 交易活躍，報價頻繁，避免誤報")
    print()
    
    print("2️⃣ 開盤前後（08:45-09:00, 13:30-13:45）")
    print("   推薦: 平衡設定 (3秒檢查, 9秒判定)")
    print("   原因: 需要較快反應，但報價可能不穩定")
    print()
    
    print("3️⃣ 盤後時段或測試")
    print("   推薦: 寬鬆設定 (8秒檢查, 16秒判定)")
    print("   原因: 報價較少，避免過多提醒")
    print()
    
    print("🔧 實際配置方法:")
    print()
    print("方法1: 在程式啟動後調用")
    print("```python")
    print("# 在simple_integrated.py中添加")
    print("app.configure_monitor_settings(5, 10)  # 5秒檢查, 10秒判定")
    print("```")
    print()
    
    print("方法2: 修改預設值")
    print("```python")
    print("# 在start_status_monitor方法中修改")
    print("self.monitor_interval = 5000  # 5秒")
    print("self.quote_timeout_threshold = 2  # 10秒 = 5秒 × 2次")
    print("```")
    print()
    
    print("📊 監控輸出說明:")
    print("✅ [MONITOR] 報價恢復正常 - 報價重新開始")
    print("❌ [MONITOR] 報價中斷 (超過10秒無報價) - 首次檢測到中斷")
    print("⚠️ [MONITOR] 報價持續中斷 (30秒) - 持續中斷提醒")

if __name__ == "__main__":
    print("🔧 監控設定優化指南")
    print("解決報價監控過於敏感的問題")
    print()
    
    test_monitor_configurations()
    print()
    simulate_monitoring_behavior()
    print()
    create_monitor_config_guide()
    
    print("\n🎯 建議行動:")
    print("1. 使用保守設定: app.configure_monitor_settings(5, 10)")
    print("2. 觀察一段時間的監控行為")
    print("3. 根據實際情況微調參數")
    print("4. 不同時段可以使用不同設定")
    
    print("\n💡 優化效果:")
    print("- 減少誤報，提升監控準確性")
    print("- 避免Console被過多提醒污染")
    print("- 保持對真正問題的敏感度")
    print("- 提供靈活的配置選項")
