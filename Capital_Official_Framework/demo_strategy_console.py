#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略Console化功能演示腳本
展示新實施的策略監控Console化功能
"""

import time
import sys
import os

def demo_strategy_console_features():
    """演示策略Console化功能"""
    print("🎬 策略Console化功能演示")
    print("=" * 60)
    
    print("📋 本演示將展示以下功能:")
    print("   1. 策略Console輸出控制")
    print("   2. 策略狀態監聽器")
    print("   3. 智能提醒機制")
    print("   4. 與報價監控的整合")
    print()
    
    # 模擬策略Console控制
    console_strategy_enabled = True
    console_quote_enabled = True
    
    def add_strategy_log(message):
        """模擬策略日誌方法"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        if console_strategy_enabled:
            print(f"[STRATEGY] {formatted_message}")
    
    def simulate_quote_tick(price, time_str):
        """模擬報價數據"""
        if console_quote_enabled:
            print(f"[TICK] {time_str} 成交:{price:.0f} 買:{price-1:.0f} 賣:{price+1:.0f} 量:10")
    
    def simulate_monitor_status(quote_status, strategy_status):
        """模擬狀態監聽器"""
        timestamp = time.strftime("%H:%M:%S")
        if quote_status == "正常":
            print(f"✅ [MONITOR] 報價恢復正常 (檢查時間: {timestamp})")
        else:
            print(f"❌ [MONITOR] 報價中斷 (檢查時間: {timestamp})")
            
        if strategy_status == "正常":
            print(f"✅ [MONITOR] 策略恢復正常 (檢查時間: {timestamp})")
        else:
            print(f"❌ [MONITOR] 策略中斷 (檢查時間: {timestamp})")
    
    # 演示1: 策略啟動
    print("🎬 演示1: 策略啟動過程")
    print("-" * 30)
    add_strategy_log("🚀 策略監控已啟動（Console模式）")
    add_strategy_log("📊 監控區間: 08:46-08:47")
    add_strategy_log("💡 策略監控已完全Console化，避免GIL問題")
    time.sleep(1)
    
    # 演示2: 報價和策略數據
    print("\n🎬 演示2: 報價和策略數據流")
    print("-" * 30)
    for i in range(3):
        price = 22500 + i * 5
        time_str = f"09:0{i}:30"
        simulate_quote_tick(price, time_str)
        if i % 2 == 0:  # 每隔一次顯示策略統計
            print(f"🔍 策略收到: price={price}, time={time_str}, count={50*(i+1)}")
        time.sleep(0.5)
    
    # 演示3: Console控制功能
    print("\n🎬 演示3: Console控制功能")
    print("-" * 30)
    print("🔊 當前狀態: 報價Console=開啟, 策略Console=開啟")
    
    # 關閉策略Console
    print("\n🔇 關閉策略Console...")
    console_strategy_enabled = False
    add_strategy_log("這條策略訊息不會顯示")
    simulate_quote_tick(22515, "09:03:45")
    print("   (注意: 策略日誌已停止，但報價仍然顯示)")
    
    # 重新開啟策略Console
    print("\n🔊 重新開啟策略Console...")
    console_strategy_enabled = True
    add_strategy_log("策略Console已重新啟用")
    add_strategy_log("策略監控恢復正常")
    
    # 關閉報價Console
    print("\n🔇 關閉報價Console...")
    console_quote_enabled = False
    simulate_quote_tick(22520, "09:04:00")
    add_strategy_log("報價Console已關閉，但策略仍在運行")
    print("   (注意: 報價已停止顯示，但策略日誌仍然顯示)")
    
    # 重新開啟報價Console
    print("\n🔊 重新開啟報價Console...")
    console_quote_enabled = True
    simulate_quote_tick(22525, "09:04:15")
    add_strategy_log("所有Console輸出已恢復")
    
    # 演示4: 狀態監聽器
    print("\n🎬 演示4: 智能狀態監聽器")
    print("-" * 30)
    print("模擬狀態變化...")
    simulate_monitor_status("正常", "正常")
    time.sleep(1)
    simulate_monitor_status("中斷", "正常")
    time.sleep(1)
    simulate_monitor_status("正常", "中斷")
    time.sleep(1)
    simulate_monitor_status("正常", "正常")
    
    # 演示5: 策略區間監控
    print("\n🎬 演示5: 策略區間監控模擬")
    print("-" * 30)
    add_strategy_log("📊 開始收集區間數據: 08:46:00")
    time.sleep(0.5)
    add_strategy_log("✅ 區間計算完成: 高:22530 低:22480 大小:50")
    time.sleep(0.5)
    add_strategy_log("📊 收集數據點數: 120 筆，開始監測突破")
    time.sleep(0.5)
    add_strategy_log("🔥 突破信號檢測: 價格22535 > 上軌22530")
    time.sleep(0.5)
    add_strategy_log("🚀 LONG 突破進場 @22535 時間:08:48:15")
    
    print("\n🎉 演示完成！")
    print("=" * 60)
    
    print("\n📋 功能總結:")
    print("✅ 策略Console輸出可以獨立控制")
    print("✅ 報價Console輸出可以獨立控制") 
    print("✅ 狀態監聽器提供智能提醒")
    print("✅ 完全避免GIL問題")
    print("✅ 保持完整的監控功能")
    
    print("\n🔧 實際使用方法:")
    print("1. 啟動 simple_integrated.py")
    print("2. 使用界面上的Console控制按鈕:")
    print("   - '🔇 關閉報價Console' / '🔊 開啟報價Console'")
    print("   - '🔇 關閉策略Console' / '🔊 開啟策略Console'")
    print("3. 在VS Code Console中查看所有監控信息")
    print("4. 狀態監聽器會自動監控並在狀態變化時提醒")
    
    print("\n💡 優勢:")
    print("- 🛡️ 完全避免GIL錯誤，系統穩定運行")
    print("- 🎮 靈活的輸出控制，避免Console污染")
    print("- 🔍 智能監聽器，只在需要時提醒")
    print("- 📊 完整的策略監控功能")
    print("- 🚀 為後續策略開發奠定穩固基礎")

if __name__ == "__main__":
    print("🚀 策略Console化功能演示腳本")
    print("本腳本展示新實施的策略監控Console化功能")
    print()
    
    try:
        demo_strategy_console_features()
    except KeyboardInterrupt:
        print("\n\n⏹️ 演示被用戶中斷")
    except Exception as e:
        print(f"\n❌ 演示過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n📝 相關文檔:")
    print("- STRATEGY_CONSOLE_IMPLEMENTATION_GUIDE.md")
    print("- STRATEGY_CONSOLE_COMPLETION_REPORT.md")
    print("- CONSOLE_MODE_IMPLEMENTATION_PLAN.md")
    print("- STRATEGY_MONITORING_DEVELOPMENT_PLAN.md")
