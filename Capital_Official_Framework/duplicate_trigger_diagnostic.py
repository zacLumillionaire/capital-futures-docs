#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重複觸發診斷工具
專門監控和分析重複觸發問題，驗證修復效果並提供持續監控能力
"""

import os
import sys
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict

# 添加當前目錄到路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

class DuplicateTriggerDiagnostic:
    """重複觸發診斷器"""
    
    def __init__(self, console_enabled: bool = True):
        self.console_enabled = console_enabled
        self.trigger_history = []  # 完整的觸發歷史
        self.duplicate_events = []  # 重複觸發事件
        self.position_stats = defaultdict(lambda: {
            'total_triggers': 0,
            'duplicate_triggers': 0,
            'last_trigger_time': 0,
            'trigger_types': defaultdict(int)
        })
        
        # 監控參數
        self.duplicate_threshold = 1.0  # 1秒內視為重複
        self.price_threshold = 3.0  # 3點內視為相同價格
        
        if self.console_enabled:
            print("[TRIGGER_DIAG] 🔍 重複觸發診斷器初始化")
    
    def record_trigger(self, position_id: str, trigger_type: str, current_price: float, 
                      success: bool, details: dict = None):
        """記錄觸發事件"""
        current_time = time.time()
        
        event = {
            'timestamp': current_time,
            'time_str': datetime.now().strftime('%H:%M:%S.%f')[:-3],
            'position_id': position_id,
            'trigger_type': trigger_type,
            'price': current_price,
            'success': success,
            'details': details or {}
        }
        
        self.trigger_history.append(event)
        
        # 更新統計
        stats = self.position_stats[position_id]
        stats['total_triggers'] += 1
        stats['trigger_types'][trigger_type] += 1
        
        # 檢查是否為重複觸發
        if self._is_duplicate_trigger(event, stats):
            stats['duplicate_triggers'] += 1
            self.duplicate_events.append(event)
            
            if self.console_enabled:
                print(f"[TRIGGER_DIAG] ⚠️ 檢測到重複觸發:")
                print(f"[TRIGGER_DIAG]   部位: {position_id}")
                print(f"[TRIGGER_DIAG]   類型: {trigger_type}")
                print(f"[TRIGGER_DIAG]   價格: {current_price}")
                print(f"[TRIGGER_DIAG]   成功: {success}")
        
        stats['last_trigger_time'] = current_time
        
        # 清理舊記錄（保留最近10分鐘）
        self._cleanup_old_records(current_time)
    
    def _is_duplicate_trigger(self, current_event: dict, stats: dict) -> bool:
        """檢查是否為重複觸發"""
        if stats['last_trigger_time'] == 0:
            return False
        
        time_diff = current_event['timestamp'] - stats['last_trigger_time']
        
        # 查找最近的相同類型觸發
        for event in reversed(self.trigger_history[-10:]):  # 檢查最近10個事件
            if (event['position_id'] == current_event['position_id'] and
                event['trigger_type'] == current_event['trigger_type']):
                
                event_time_diff = current_event['timestamp'] - event['timestamp']
                price_diff = abs(current_event['price'] - event['price'])
                
                # 判斷是否為重複
                if (event_time_diff < self.duplicate_threshold and
                    price_diff < self.price_threshold):
                    return True
                break
        
        return False
    
    def _cleanup_old_records(self, current_time: float):
        """清理舊記錄"""
        cutoff_time = current_time - 600  # 10分鐘前
        
        # 清理觸發歷史
        self.trigger_history = [
            event for event in self.trigger_history
            if event['timestamp'] > cutoff_time
        ]
        
        # 清理重複事件
        self.duplicate_events = [
            event for event in self.duplicate_events
            if event['timestamp'] > cutoff_time
        ]
    
    def get_statistics(self) -> dict:
        """獲取統計信息"""
        total_triggers = len(self.trigger_history)
        total_duplicates = len(self.duplicate_events)
        
        # 按部位統計
        position_summary = {}
        for position_id, stats in self.position_stats.items():
            if stats['total_triggers'] > 0:
                position_summary[position_id] = {
                    'total_triggers': stats['total_triggers'],
                    'duplicate_triggers': stats['duplicate_triggers'],
                    'duplicate_rate': stats['duplicate_triggers'] / stats['total_triggers'] * 100,
                    'trigger_types': dict(stats['trigger_types'])
                }
        
        # 按觸發類型統計
        type_summary = defaultdict(lambda: {'total': 0, 'duplicates': 0})
        for event in self.trigger_history:
            type_summary[event['trigger_type']]['total'] += 1
        
        for event in self.duplicate_events:
            type_summary[event['trigger_type']]['duplicates'] += 1
        
        return {
            'total_triggers': total_triggers,
            'total_duplicates': total_duplicates,
            'duplicate_rate': total_duplicates / total_triggers * 100 if total_triggers > 0 else 0,
            'position_summary': position_summary,
            'type_summary': dict(type_summary),
            'recent_duplicates': self.duplicate_events[-5:] if self.duplicate_events else []
        }
    
    def print_report(self):
        """打印診斷報告"""
        stats = self.get_statistics()
        
        print(f"\n{'='*60}")
        print(f"[TRIGGER_DIAG] 📊 重複觸發診斷報告")
        print(f"{'='*60}")
        
        print(f"📈 總體統計:")
        print(f"   總觸發次數: {stats['total_triggers']}")
        print(f"   重複觸發次數: {stats['total_duplicates']}")
        print(f"   重複觸發率: {stats['duplicate_rate']:.1f}%")
        
        if stats['position_summary']:
            print(f"\n📋 部位統計:")
            for position_id, pos_stats in stats['position_summary'].items():
                print(f"   部位{position_id}:")
                print(f"     總觸發: {pos_stats['total_triggers']}")
                print(f"     重複觸發: {pos_stats['duplicate_triggers']}")
                print(f"     重複率: {pos_stats['duplicate_rate']:.1f}%")
                print(f"     觸發類型: {pos_stats['trigger_types']}")
        
        if stats['type_summary']:
            print(f"\n🎯 觸發類型統計:")
            for trigger_type, type_stats in stats['type_summary'].items():
                duplicate_rate = type_stats['duplicates'] / type_stats['total'] * 100 if type_stats['total'] > 0 else 0
                print(f"   {trigger_type}:")
                print(f"     總觸發: {type_stats['total']}")
                print(f"     重複觸發: {type_stats['duplicates']}")
                print(f"     重複率: {duplicate_rate:.1f}%")
        
        if stats['recent_duplicates']:
            print(f"\n⚠️ 最近重複觸發事件:")
            for event in stats['recent_duplicates']:
                print(f"   {event['time_str']} 部位{event['position_id']} {event['trigger_type']} @{event['price']}")
        
        # 評估修復效果
        print(f"\n🎯 修復效果評估:")
        if stats['duplicate_rate'] < 5.0:
            print(f"   ✅ 優秀: 重複觸發率 < 5%")
        elif stats['duplicate_rate'] < 15.0:
            print(f"   ⚠️ 良好: 重複觸發率 < 15%，仍有改進空間")
        else:
            print(f"   ❌ 需要改進: 重複觸發率 > 15%，建議進一步優化")
        
        print(f"{'='*60}")
    
    def monitor_optimized_risk_manager(self, risk_manager):
        """監控 OptimizedRiskManager 的觸發事件"""
        if not hasattr(risk_manager, 'trigger_dedup_cache'):
            print("[TRIGGER_DIAG] ⚠️ OptimizedRiskManager 未啟用去重機制")
            return
        
        print("[TRIGGER_DIAG] 🔍 開始監控 OptimizedRiskManager")
        
        # 監控去重緩存的變化
        last_cache_size = 0
        
        def monitor_loop():
            nonlocal last_cache_size
            
            while True:
                try:
                    current_cache_size = len(risk_manager.trigger_dedup_cache)
                    
                    if current_cache_size != last_cache_size:
                        if self.console_enabled:
                            print(f"[TRIGGER_DIAG] 📊 去重緩存大小變化: {last_cache_size} → {current_cache_size}")
                        last_cache_size = current_cache_size
                    
                    # 檢查去重緩存內容
                    for position_id, cache_data in risk_manager.trigger_dedup_cache.items():
                        age = time.time() - cache_data['timestamp']
                        if age > risk_manager.dedup_timeout:
                            if self.console_enabled:
                                print(f"[TRIGGER_DIAG] ⚠️ 發現過期去重記錄: 部位{position_id} 已過期{age:.1f}秒")
                    
                    time.sleep(1.0)  # 每秒檢查一次
                    
                except Exception as e:
                    print(f"[TRIGGER_DIAG] ❌ 監控錯誤: {e}")
                    time.sleep(5.0)
        
        # 啟動監控線程
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()

def main():
    """主函數"""
    print("🔍 重複觸發診斷工具")
    print("監控和分析重複觸發問題")
    print("="*50)
    
    diagnostic = DuplicateTriggerDiagnostic(console_enabled=True)
    
    # 模擬一些觸發事件來測試
    print("\n📋 模擬觸發事件測試:")
    
    # 正常觸發
    diagnostic.record_trigger("100", "trailing_stop", 22540.0, True)
    time.sleep(0.5)
    
    # 重複觸發（相同價格，短時間內）
    diagnostic.record_trigger("100", "trailing_stop", 22541.0, False, {"reason": "鎖定衝突"})
    time.sleep(0.3)
    
    # 另一個部位的觸發
    diagnostic.record_trigger("101", "stop_loss", 22500.0, True)
    time.sleep(0.8)
    
    # 價格顯著變化的觸發（不應視為重複）
    diagnostic.record_trigger("100", "trailing_stop", 22550.0, True)
    
    # 打印報告
    diagnostic.print_report()
    
    return diagnostic

if __name__ == "__main__":
    main()
