#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系統健康監控工具 - 全面檢查系統狀態，預防潛在問題
"""

import time
import threading
import sqlite3
import os
import gc
from datetime import datetime, timedelta

# 可選導入psutil，如果不存在則使用替代方案
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    # 移除直接print，改為在需要時通過日誌系統輸出

class SystemHealthMonitor:
    """系統健康監控器"""
    
    def __init__(self, main_app):
        self.main_app = main_app
        self.health_history = []
        self.alert_thresholds = {
            'memory_usage': 80,  # 內存使用率 %
            'cache_size': 1000,  # 緩存項目數
            'queue_size': 100,   # 隊列大小
            'failure_rate': 5,   # 失敗率 %
            'response_time': 1.0, # 響應時間 秒
            'lock_count': 20     # 鎖定數量
        }
    
    def run_comprehensive_health_check(self, silent=False):
        """運行全面健康檢查

        Args:
            silent (bool): 是否靜默模式，不輸出詳細信息
        """
        if not silent:
            print("\n🏥 系統健康檢查開始...")
            print("=" * 70)
        
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'system_resources': self.check_system_resources(silent),
            'database_health': self.check_database_health(silent),
            'memory_health': self.check_memory_health(silent),
            'thread_health': self.check_thread_health(silent),
            'cache_health': self.check_cache_health(silent),
            'lock_health': self.check_lock_health(silent),
            'performance_health': self.check_performance_health(silent),
            'overall_score': 0,
            'alerts': [],
            'recommendations': []
        }
        
        # 計算總體健康分數
        health_report['overall_score'] = self.calculate_health_score(health_report)
        
        # 生成警報和建議
        health_report['alerts'] = self.generate_alerts(health_report)
        health_report['recommendations'] = self.generate_health_recommendations(health_report)
        
        # 保存到歷史記錄
        self.health_history.append(health_report)
        
        # 輸出報告（除非是靜默模式）
        if not silent:
            self.print_health_report(health_report)

        return health_report
    
    def check_system_resources(self, silent=False):
        """檢查系統資源"""
        if not silent:
            print("📋 檢查系統資源...")

        try:
            if PSUTIL_AVAILABLE:
                # 使用psutil獲取詳細信息
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                disk = psutil.disk_usage('.')
                disk_percent = (disk.used / disk.total) * 100
                process = psutil.Process()
                process_memory = process.memory_info().rss / 1024 / 1024  # MB

                resources = {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory_percent,
                    'disk_percent': disk_percent,
                    'process_memory_mb': process_memory,
                    'status': 'healthy'
                }

                if not silent:
                    print(f"   💻 CPU使用率: {cpu_percent:.1f}%")
                    print(f"   🧠 內存使用率: {memory_percent:.1f}%")
                    print(f"   💾 磁盤使用率: {disk_percent:.1f}%")
                    print(f"   🔧 進程內存: {process_memory:.1f}MB")

                # 檢查警告
                if memory_percent > self.alert_thresholds['memory_usage']:
                    resources['status'] = 'warning'
                    if not silent:
                        print(f"   ⚠️ 內存使用率過高")
            else:
                # 簡化版本，不依賴psutil
                import platform
                import shutil

                # 基本系統信息
                system_info = platform.system()
                python_version = platform.python_version()

                # 磁盤空間（當前目錄）
                try:
                    disk_usage = shutil.disk_usage('.')
                    disk_percent = (disk_usage.used / disk_usage.total) * 100
                except:
                    disk_percent = 0

                resources = {
                    'system': system_info,
                    'python_version': python_version,
                    'disk_percent': disk_percent,
                    'status': 'limited'
                }

                print(f"   💻 系統: {system_info}")
                print(f"   🐍 Python版本: {python_version}")
                print(f"   💾 磁盤使用率: {disk_percent:.1f}%")
                print(f"   ⚠️ 簡化監控模式（psutil不可用）")

            return resources

        except Exception as e:
            print(f"   ❌ 系統資源檢查失敗: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def check_database_health(self, silent=False):
        """檢查數據庫健康狀態"""
        if not silent:
            print("\n📋 檢查數據庫健康...")
        
        try:
            db_path = "multi_group_strategy.db"
            if not os.path.exists(db_path):
                return {'status': 'missing', 'error': '數據庫文件不存在'}
            
            # 文件大小
            file_size = os.path.getsize(db_path) / 1024 / 1024  # MB
            
            # 連接測試
            start_time = time.time()
            conn = sqlite3.connect(db_path, timeout=5.0)
            cursor = conn.cursor()
            
            # 基本查詢測試
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            
            # 數據完整性檢查
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            
            # 活躍部位檢查
            cursor.execute("SELECT COUNT(*) FROM position_records WHERE status = 'ACTIVE'")
            active_positions = cursor.fetchone()[0]
            
            # 風險管理狀態檢查
            cursor.execute("SELECT COUNT(*) FROM risk_management_states")
            risk_states = cursor.fetchone()[0]
            
            response_time = time.time() - start_time
            
            conn.close()
            
            db_health = {
                'file_size_mb': file_size,
                'table_count': table_count,
                'integrity': integrity,
                'active_positions': active_positions,
                'risk_states': risk_states,
                'response_time': response_time,
                'status': 'healthy'
            }
            
            if not silent:
                print(f"   📊 數據庫大小: {file_size:.1f}MB")
                print(f"   📋 表數量: {table_count}")
                print(f"   🛡️ 完整性: {integrity}")
                print(f"   📈 活躍部位: {active_positions}")
                print(f"   ⚡ 響應時間: {response_time:.3f}秒")

            if response_time > self.alert_thresholds['response_time']:
                db_health['status'] = 'warning'
                if not silent:
                    print(f"   ⚠️ 數據庫響應時間過長")
            
            return db_health
            
        except Exception as e:
            print(f"   ❌ 數據庫健康檢查失敗: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def check_memory_health(self, silent=False):
        """檢查內存健康狀態"""
        if not silent:
            print("\n📋 檢查內存健康...")
        
        try:
            memory_health = {
                'cache_sizes': {},
                'total_cache_items': 0,
                'memory_leaks': [],
                'gc_stats': {},
                'status': 'healthy'
            }
            
            # 檢查各種緩存
            cache_components = [
                ('optimized_risk_manager', ['position_cache', 'stop_loss_cache', 'activation_cache', 'trailing_cache']),
                ('async_updater', ['memory_cache']),
            ]
            
            for component_name, cache_attrs in cache_components:
                if hasattr(self.main_app, component_name):
                    component = getattr(self.main_app, component_name)
                    if component:
                        for cache_attr in cache_attrs:
                            if hasattr(component, cache_attr):
                                cache = getattr(component, cache_attr)
                                if isinstance(cache, dict):
                                    size = len(cache)
                                    memory_health['cache_sizes'][f'{component_name}.{cache_attr}'] = size
                                    memory_health['total_cache_items'] += size
            
            # 垃圾回收統計
            gc_stats = gc.get_stats()
            memory_health['gc_stats'] = {
                'collections': [stat['collections'] for stat in gc_stats],
                'collected': [stat['collected'] for stat in gc_stats]
            }
            
            print(f"   📊 緩存統計:")
            for cache_name, size in memory_health['cache_sizes'].items():
                print(f"      - {cache_name}: {size} 項")
            
            print(f"   🗑️ 總緩存項目: {memory_health['total_cache_items']}")
            
            # 檢查警告
            if memory_health['total_cache_items'] > self.alert_thresholds['cache_size']:
                memory_health['status'] = 'warning'
                memory_health['memory_leaks'].append(f"總緩存項目過多: {memory_health['total_cache_items']}")
                print(f"   ⚠️ 緩存項目過多")
            
            return memory_health
            
        except Exception as e:
            print(f"   ❌ 內存健康檢查失敗: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def check_thread_health(self, silent=False):
        """檢查線程健康狀態"""
        if not silent:
            print("\n📋 檢查線程健康...")
        
        try:
            all_threads = threading.enumerate()
            
            thread_health = {
                'total_threads': len(all_threads),
                'active_threads': sum(1 for t in all_threads if t.is_alive()),
                'daemon_threads': sum(1 for t in all_threads if t.daemon),
                'async_worker_status': 'unknown',
                'thread_details': [],
                'status': 'healthy'
            }
            
            # 檢查AsyncUpdater工作線程
            if hasattr(self.main_app, 'async_updater') and self.main_app.async_updater:
                updater = self.main_app.async_updater
                if hasattr(updater, 'worker_thread'):
                    worker = updater.worker_thread
                    if worker and worker.is_alive():
                        thread_health['async_worker_status'] = 'active'
                    else:
                        thread_health['async_worker_status'] = 'inactive'
                        thread_health['status'] = 'warning'
            
            # 記錄線程詳情
            for thread in all_threads:
                thread_info = {
                    'name': thread.name,
                    'alive': thread.is_alive(),
                    'daemon': thread.daemon
                }
                thread_health['thread_details'].append(thread_info)
            
            print(f"   🧵 總線程數: {thread_health['total_threads']}")
            print(f"   ✅ 活躍線程: {thread_health['active_threads']}")
            print(f"   🔧 AsyncWorker: {thread_health['async_worker_status']}")
            
            if thread_health['total_threads'] > 20:
                thread_health['status'] = 'warning'
                print(f"   ⚠️ 線程數量較多")
            
            return thread_health
            
        except Exception as e:
            print(f"   ❌ 線程健康檢查失敗: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def check_cache_health(self, silent=False):
        """檢查緩存健康狀態"""
        if not silent:
            print("\n📋 檢查緩存健康...")
        
        try:
            cache_health = {
                'hit_rates': {},
                'cache_efficiency': 'unknown',
                'stale_entries': 0,
                'status': 'healthy'
            }
            
            # 檢查AsyncUpdater緩存命中率
            if hasattr(self.main_app, 'async_updater') and self.main_app.async_updater:
                updater = self.main_app.async_updater
                if hasattr(updater, 'stats'):
                    stats = updater.stats
                    total_tasks = stats.get('total_tasks', 0)
                    cache_hits = stats.get('cache_hits', 0)
                    
                    if total_tasks > 0:
                        hit_rate = (cache_hits / total_tasks) * 100
                        cache_health['hit_rates']['async_updater'] = hit_rate
                        
                        if hit_rate < 50:
                            cache_health['status'] = 'warning'
            
            print(f"   📊 緩存命中率:")
            for component, rate in cache_health['hit_rates'].items():
                print(f"      - {component}: {rate:.1f}%")
            
            return cache_health
            
        except Exception as e:
            print(f"   ❌ 緩存健康檢查失敗: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def check_lock_health(self, silent=False):
        """檢查鎖定健康狀態"""
        if not silent:
            print("\n📋 檢查鎖定健康...")
        
        try:
            lock_health = {
                'total_locks': 0,
                'expired_locks': 0,
                'lock_details': {},
                'status': 'healthy'
            }
            
            # 檢查GlobalExitManager鎖定
            if hasattr(self.main_app, 'multi_group_position_manager') and self.main_app.multi_group_position_manager:
                if hasattr(self.main_app.multi_group_position_manager, 'simplified_tracker'):
                    tracker = self.main_app.multi_group_position_manager.simplified_tracker
                    if hasattr(tracker, 'global_exit_manager'):
                        manager = tracker.global_exit_manager
                        if hasattr(manager, 'exit_locks'):
                            lock_count = len(manager.exit_locks)
                            lock_health['total_locks'] = lock_count
                            
                            # 檢查過期鎖定
                            current_time = time.time()
                            expired_count = 0
                            for pos_id, lock_info in manager.exit_locks.items():
                                age = current_time - lock_info.get('timestamp', 0)
                                if age > 300:  # 5分鐘
                                    expired_count += 1
                            
                            lock_health['expired_locks'] = expired_count
                            lock_health['lock_details']['exit_locks'] = lock_count
            
            print(f"   🔒 總鎖定數: {lock_health['total_locks']}")
            print(f"   ⏰ 過期鎖定: {lock_health['expired_locks']}")
            
            if lock_health['total_locks'] > self.alert_thresholds['lock_count']:
                lock_health['status'] = 'warning'
                print(f"   ⚠️ 鎖定數量過多")
            
            if lock_health['expired_locks'] > 0:
                lock_health['status'] = 'warning'
                print(f"   ⚠️ 發現過期鎖定")
            
            return lock_health
            
        except Exception as e:
            print(f"   ❌ 鎖定健康檢查失敗: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def check_performance_health(self, silent=False):
        """檢查性能健康狀態"""
        if not silent:
            print("\n📋 檢查性能健康...")
        
        try:
            performance_health = {
                'queue_sizes': {},
                'response_times': {},
                'failure_rates': {},
                'bottlenecks': [],
                'status': 'healthy'
            }
            
            # 檢查隊列大小
            if hasattr(self.main_app, 'async_updater') and self.main_app.async_updater:
                updater = self.main_app.async_updater
                if hasattr(updater, 'task_queue'):
                    queue_size = updater.task_queue.qsize()
                    performance_health['queue_sizes']['async_updater'] = queue_size
                    
                    if queue_size > self.alert_thresholds['queue_size']:
                        performance_health['status'] = 'warning'
                        performance_health['bottlenecks'].append(f"AsyncUpdater隊列過大: {queue_size}")
                
                # 檢查失敗率
                if hasattr(updater, 'stats'):
                    stats = updater.stats
                    total_tasks = stats.get('total_tasks', 0)
                    failed_tasks = stats.get('failed_tasks', 0)
                    
                    if total_tasks > 0:
                        failure_rate = (failed_tasks / total_tasks) * 100
                        performance_health['failure_rates']['async_updater'] = failure_rate
                        
                        if failure_rate > self.alert_thresholds['failure_rate']:
                            performance_health['status'] = 'warning'
                            performance_health['bottlenecks'].append(f"AsyncUpdater失敗率過高: {failure_rate:.1f}%")
            
            print(f"   📊 隊列大小:")
            for component, size in performance_health['queue_sizes'].items():
                print(f"      - {component}: {size}")
            
            print(f"   📊 失敗率:")
            for component, rate in performance_health['failure_rates'].items():
                print(f"      - {component}: {rate:.1f}%")
            
            return performance_health
            
        except Exception as e:
            print(f"   ❌ 性能健康檢查失敗: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def calculate_health_score(self, health_report):
        """計算健康分數 (0-100)"""
        score = 100
        
        # 根據各項檢查結果扣分
        for category, data in health_report.items():
            if isinstance(data, dict) and 'status' in data:
                if data['status'] == 'error':
                    score -= 20
                elif data['status'] == 'warning':
                    score -= 10
        
        return max(0, score)
    
    def generate_alerts(self, health_report):
        """生成警報"""
        alerts = []
        
        for category, data in health_report.items():
            if isinstance(data, dict) and 'status' in data:
                if data['status'] == 'error':
                    alerts.append({
                        'level': 'critical',
                        'category': category,
                        'message': f"{category} 檢查失敗"
                    })
                elif data['status'] == 'warning':
                    alerts.append({
                        'level': 'warning',
                        'category': category,
                        'message': f"{category} 發現問題"
                    })
        
        return alerts
    
    def generate_health_recommendations(self, health_report):
        """生成健康建議"""
        recommendations = []
        
        # 基於各項檢查結果生成建議
        if health_report.get('lock_health', {}).get('expired_locks', 0) > 0:
            recommendations.append("清理過期鎖定狀態")
        
        if health_report.get('memory_health', {}).get('total_cache_items', 0) > 1000:
            recommendations.append("清理內存緩存")
        
        if health_report.get('performance_health', {}).get('bottlenecks'):
            recommendations.append("優化性能瓶頸")
        
        return recommendations
    
    def print_health_report(self, health_report):
        """輸出健康報告"""
        print("\n🏥 系統健康報告")
        print("=" * 70)
        
        score = health_report['overall_score']
        print(f"📊 總體健康分數: {score}/100")
        
        if score >= 90:
            print("✅ 系統健康狀態優秀")
        elif score >= 70:
            print("⚠️ 系統健康狀態良好，有輕微問題")
        elif score >= 50:
            print("⚠️ 系統健康狀態一般，需要關注")
        else:
            print("❌ 系統健康狀態較差，需要立即處理")
        
        # 顯示警報
        alerts = health_report.get('alerts', [])
        if alerts:
            print(f"\n🚨 警報 ({len(alerts)} 項):")
            for alert in alerts:
                level_icon = "🚨" if alert['level'] == 'critical' else "⚠️"
                print(f"   {level_icon} {alert['category']}: {alert['message']}")
        
        # 顯示建議
        recommendations = health_report.get('recommendations', [])
        if recommendations:
            print(f"\n💡 建議:")
            for rec in recommendations:
                print(f"   - {rec}")

def run_health_check_on_simple_integrated(main_app, silent=False):
    """在simple_integrated實例上運行健康檢查

    Args:
        main_app: 主應用實例
        silent (bool): 是否靜默模式，不輸出詳細信息
    """
    monitor = SystemHealthMonitor(main_app)
    return monitor.run_comprehensive_health_check(silent=silent)

if __name__ == "__main__":
    print("系統健康監控工具")
    print("請在 simple_integrated.py 中調用此模組的函數")
