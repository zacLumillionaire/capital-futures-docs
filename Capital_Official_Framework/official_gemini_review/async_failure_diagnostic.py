#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
異步失敗診斷工具 - 深度分析緩存命中增加但失敗任務也增加的問題
"""

import time
import threading
import sqlite3
import os
import traceback
from datetime import datetime, timedelta

def run_diagnostic_on_simple_integrated(main_app):
    """在simple_integrated實例上運行完整診斷"""
    print("\n🔬 異步失敗深度診斷開始...")
    print("=" * 70)
    
    diagnostic_results = {
        'timestamp': datetime.now().isoformat(),
        'database_analysis': {},
        'memory_analysis': {},
        'thread_analysis': {},
        'performance_analysis': {},
        'error_analysis': {},
        'recommendations': []
    }
    
    # 1. 數據庫深度分析
    print("📋 步驟1: 數據庫深度分析...")
    diagnostic_results['database_analysis'] = analyze_database_issues(main_app)
    
    # 2. 內存使用分析
    print("\n📋 步驟2: 內存使用分析...")
    diagnostic_results['memory_analysis'] = analyze_memory_usage(main_app)
    
    # 3. 線程狀態分析
    print("\n📋 步驟3: 線程狀態分析...")
    diagnostic_results['thread_analysis'] = analyze_thread_status(main_app)
    
    # 4. 性能瓶頸分析
    print("\n📋 步驟4: 性能瓶頸分析...")
    diagnostic_results['performance_analysis'] = analyze_performance_bottlenecks(main_app)
    
    # 5. 錯誤模式分析
    print("\n📋 步驟5: 錯誤模式分析...")
    diagnostic_results['error_analysis'] = analyze_error_patterns(main_app)
    
    # 6. 生成建議
    print("\n📋 步驟6: 生成修復建議...")
    diagnostic_results['recommendations'] = generate_recommendations(diagnostic_results)
    
    # 7. 輸出診斷報告
    print_diagnostic_report(diagnostic_results)
    
    return diagnostic_results

def analyze_database_issues(main_app):
    """分析數據庫相關問題"""
    analysis = {
        'connection_pool': 'unknown',
        'lock_conflicts': 0,
        'transaction_time': 0,
        'table_sizes': {},
        'index_efficiency': 'unknown'
    }
    
    try:
        db_path = "multi_group_strategy.db"
        if not os.path.exists(db_path):
            analysis['connection_pool'] = 'no_database'
            return analysis
        
        conn = sqlite3.connect(db_path, timeout=10.0)
        cursor = conn.cursor()
        
        # 檢查表大小
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for (table_name,) in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                analysis['table_sizes'][table_name] = count
            except:
                analysis['table_sizes'][table_name] = 'error'
        
        # 測試事務時間
        start_time = time.time()
        cursor.execute("BEGIN TRANSACTION")
        cursor.execute("CREATE TABLE IF NOT EXISTS perf_test (id INTEGER)")
        cursor.execute("INSERT INTO perf_test VALUES (1)")
        cursor.execute("DELETE FROM perf_test WHERE id = 1")
        cursor.execute("COMMIT")
        analysis['transaction_time'] = time.time() - start_time
        
        # 檢查鎖定情況
        cursor.execute("PRAGMA database_list")
        analysis['connection_pool'] = 'healthy'
        
        conn.close()
        
        print(f"   📊 數據庫表數量: {len(analysis['table_sizes'])}")
        print(f"   ⏱️ 事務時間: {analysis['transaction_time']:.3f}秒")
        
        if analysis['transaction_time'] > 1.0:
            print(f"   ⚠️ 警告: 事務時間過長")
        
    except Exception as e:
        print(f"   ❌ 數據庫分析失敗: {e}")
        analysis['connection_pool'] = 'error'
    
    return analysis

def analyze_memory_usage(main_app):
    """分析內存使用情況"""
    analysis = {
        'cache_sizes': {},
        'memory_leaks': [],
        'cache_hit_rates': {},
        'memory_efficiency': 'unknown'
    }
    
    try:
        # 檢查OptimizedRiskManager緩存
        if hasattr(main_app, 'optimized_risk_manager') and main_app.optimized_risk_manager:
            manager = main_app.optimized_risk_manager
            
            caches = ['position_cache', 'stop_loss_cache', 'activation_cache', 'trailing_cache']
            for cache_name in caches:
                if hasattr(manager, cache_name):
                    cache = getattr(manager, cache_name)
                    if isinstance(cache, dict):
                        analysis['cache_sizes'][f'risk_manager_{cache_name}'] = len(cache)
        
        # 檢查AsyncUpdater緩存
        if hasattr(main_app, 'async_updater') and main_app.async_updater:
            updater = main_app.async_updater
            
            if hasattr(updater, 'memory_cache'):
                for cache_type, cache_data in updater.memory_cache.items():
                    if isinstance(cache_data, dict):
                        analysis['cache_sizes'][f'async_{cache_type}'] = len(cache_data)
            
            # 檢查緩存命中率
            if hasattr(updater, 'stats'):
                stats = updater.stats
                total_tasks = stats.get('total_tasks', 0)
                cache_hits = stats.get('cache_hits', 0)
                
                if total_tasks > 0:
                    hit_rate = (cache_hits / total_tasks) * 100
                    analysis['cache_hit_rates']['async_updater'] = hit_rate
        
        # 檢查SimplifiedTracker狀態
        if hasattr(main_app, 'multi_group_position_manager') and main_app.multi_group_position_manager:
            if hasattr(main_app.multi_group_position_manager, 'simplified_tracker'):
                tracker = main_app.multi_group_position_manager.simplified_tracker
                
                if hasattr(tracker, 'strategy_groups'):
                    analysis['cache_sizes']['strategy_groups'] = len(tracker.strategy_groups)
                
                if hasattr(tracker, 'exit_groups'):
                    analysis['cache_sizes']['exit_groups'] = len(tracker.exit_groups)
        
        # 檢查內存洩漏跡象
        total_cache_items = sum(analysis['cache_sizes'].values())
        if total_cache_items > 1000:
            analysis['memory_leaks'].append(f"總緩存項目過多: {total_cache_items}")
        
        print(f"   📊 緩存統計:")
        for cache_name, size in analysis['cache_sizes'].items():
            print(f"      - {cache_name}: {size} 項")
        
        if analysis['cache_hit_rates']:
            print(f"   📊 緩存命中率:")
            for component, rate in analysis['cache_hit_rates'].items():
                print(f"      - {component}: {rate:.1f}%")
        
    except Exception as e:
        print(f"   ❌ 內存分析失敗: {e}")
    
    return analysis

def analyze_thread_status(main_app):
    """分析線程狀態"""
    analysis = {
        'active_threads': 0,
        'thread_details': [],
        'deadlock_risk': 'low',
        'thread_efficiency': 'unknown'
    }
    
    try:
        # 獲取所有活躍線程
        all_threads = threading.enumerate()
        analysis['active_threads'] = len(all_threads)
        
        for thread in all_threads:
            thread_info = {
                'name': thread.name,
                'alive': thread.is_alive(),
                'daemon': thread.daemon,
                'ident': thread.ident
            }
            analysis['thread_details'].append(thread_info)
        
        # 檢查AsyncUpdater工作線程
        if hasattr(main_app, 'async_updater') and main_app.async_updater:
            updater = main_app.async_updater
            if hasattr(updater, 'worker_thread'):
                worker = updater.worker_thread
                if worker and worker.is_alive():
                    print(f"   ✅ AsyncUpdater工作線程正常")
                else:
                    print(f"   ❌ AsyncUpdater工作線程異常")
                    analysis['deadlock_risk'] = 'high'
        
        print(f"   📊 活躍線程數: {analysis['active_threads']}")
        
        if analysis['active_threads'] > 20:
            print(f"   ⚠️ 警告: 線程數量較多")
            analysis['deadlock_risk'] = 'medium'
        
    except Exception as e:
        print(f"   ❌ 線程分析失敗: {e}")
    
    return analysis

def analyze_performance_bottlenecks(main_app):
    """分析性能瓶頸"""
    analysis = {
        'queue_latency': 0,
        'database_latency': 0,
        'cache_efficiency': 'unknown',
        'bottleneck_sources': []
    }
    
    try:
        # 測試數據庫延遲
        start_time = time.time()
        try:
            conn = sqlite3.connect("multi_group_strategy.db", timeout=5.0)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            conn.close()
            analysis['database_latency'] = time.time() - start_time
        except:
            analysis['database_latency'] = -1
        
        # 檢查隊列延遲
        if hasattr(main_app, 'async_updater') and main_app.async_updater:
            updater = main_app.async_updater
            if hasattr(updater, 'task_queue'):
                queue_size = updater.task_queue.qsize()
                if queue_size > 50:
                    analysis['bottleneck_sources'].append(f"任務隊列過大: {queue_size}")
        
        print(f"   ⏱️ 數據庫延遲: {analysis['database_latency']:.3f}秒")
        
        if analysis['database_latency'] > 0.1:
            print(f"   ⚠️ 警告: 數據庫延遲較高")
            analysis['bottleneck_sources'].append("數據庫延遲過高")
        
    except Exception as e:
        print(f"   ❌ 性能分析失敗: {e}")
    
    return analysis

def analyze_error_patterns(main_app):
    """分析錯誤模式"""
    analysis = {
        'recent_errors': [],
        'error_frequency': {},
        'critical_errors': [],
        'error_trends': 'unknown'
    }
    
    try:
        # 檢查AsyncUpdater統計
        if hasattr(main_app, 'async_updater') and main_app.async_updater:
            updater = main_app.async_updater
            if hasattr(updater, 'stats'):
                stats = updater.stats
                failed_tasks = stats.get('failed_tasks', 0)
                total_tasks = stats.get('total_tasks', 0)
                
                if total_tasks > 0:
                    failure_rate = (failed_tasks / total_tasks) * 100
                    analysis['error_frequency']['async_updater'] = failure_rate
                    
                    if failure_rate > 10:
                        analysis['critical_errors'].append(f"AsyncUpdater失敗率過高: {failure_rate:.1f}%")
        
        print(f"   📊 錯誤統計:")
        for component, rate in analysis['error_frequency'].items():
            print(f"      - {component}: {rate:.1f}% 失敗率")
        
        if analysis['critical_errors']:
            print(f"   🚨 關鍵錯誤:")
            for error in analysis['critical_errors']:
                print(f"      - {error}")
        
    except Exception as e:
        print(f"   ❌ 錯誤分析失敗: {e}")
    
    return analysis

def generate_recommendations(diagnostic_results):
    """生成修復建議"""
    recommendations = []
    
    # 基於數據庫分析的建議
    db_analysis = diagnostic_results.get('database_analysis', {})
    if db_analysis.get('transaction_time', 0) > 1.0:
        recommendations.append({
            'priority': 'high',
            'category': 'database',
            'issue': '數據庫事務時間過長',
            'solution': '調整數據庫超時設置，優化查詢語句'
        })
    
    # 基於內存分析的建議
    memory_analysis = diagnostic_results.get('memory_analysis', {})
    if memory_analysis.get('memory_leaks'):
        recommendations.append({
            'priority': 'medium',
            'category': 'memory',
            'issue': '可能的內存洩漏',
            'solution': '定期清理緩存，實施內存監控'
        })
    
    # 基於線程分析的建議
    thread_analysis = diagnostic_results.get('thread_analysis', {})
    if thread_analysis.get('deadlock_risk') == 'high':
        recommendations.append({
            'priority': 'high',
            'category': 'threading',
            'issue': '線程死鎖風險',
            'solution': '重啟異步更新器，檢查線程同步邏輯'
        })
    
    # 基於錯誤分析的建議
    error_analysis = diagnostic_results.get('error_analysis', {})
    if error_analysis.get('critical_errors'):
        recommendations.append({
            'priority': 'critical',
            'category': 'errors',
            'issue': '關鍵錯誤需要立即處理',
            'solution': '啟用詳細日誌，分析具體錯誤原因'
        })
    
    return recommendations

def print_diagnostic_report(diagnostic_results):
    """輸出診斷報告"""
    print("\n📊 診斷報告總結")
    print("=" * 70)
    
    recommendations = diagnostic_results.get('recommendations', [])
    
    if not recommendations:
        print("✅ 未發現重大問題")
        return
    
    # 按優先級分組
    critical = [r for r in recommendations if r['priority'] == 'critical']
    high = [r for r in recommendations if r['priority'] == 'high']
    medium = [r for r in recommendations if r['priority'] == 'medium']
    
    if critical:
        print("\n🚨 關鍵問題 (立即處理):")
        for rec in critical:
            print(f"   - {rec['issue']}")
            print(f"     解決方案: {rec['solution']}")
    
    if high:
        print("\n⚠️ 高優先級問題:")
        for rec in high:
            print(f"   - {rec['issue']}")
            print(f"     解決方案: {rec['solution']}")
    
    if medium:
        print("\n💡 中優先級問題:")
        for rec in medium:
            print(f"   - {rec['issue']}")
            print(f"     解決方案: {rec['solution']}")
    
    print(f"\n📋 總計發現 {len(recommendations)} 個問題需要處理")

if __name__ == "__main__":
    print("異步失敗診斷工具")
    print("請在 simple_integrated.py 中調用此模組的函數")
