#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
group_id一致性修復工具
專門修復group_id相關的混亂使用問題
"""

import os
import sys
import sqlite3
import re
from datetime import datetime, date
from typing import Dict, List, Tuple, Optional

# 添加當前目錄到路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

class GroupIDConsistencyFixer:
    """group_id一致性修復器"""
    
    def __init__(self):
        self.databases = [
            ("正式機", "multi_group_strategy.db"),
            ("虛擬測試機", "test_virtual_strategy.db")
        ]
        
        self.fixes_applied = []
        self.issues_found = []
        
        print("🔧 group_id一致性修復工具")
        print("=" * 50)
        print("🎯 修復目標:")
        print("  1. 檢查並修復孤立部位（找不到對應策略組）")
        print("  2. 修復group_id vs 主鍵ID混用問題")
        print("  3. 驗證外鍵關係邏輯一致性")
        print("  4. 修復資料庫約束問題")
        print("=" * 50)
    
    def check_orphaned_positions(self, db_path: str, env_name: str) -> List[Dict]:
        """檢查孤立部位"""
        if not os.path.exists(db_path):
            print(f"❌ {env_name}資料庫不存在: {db_path}")
            return []
        
        orphaned_positions = []
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            today = date.today().isoformat()
            
            # 查找孤立部位：部位記錄中的group_id在strategy_groups表中找不到對應記錄
            cursor.execute('''
                SELECT pr.id, pr.group_id, pr.lot_id, pr.status, pr.entry_time
                FROM position_records pr
                LEFT JOIN strategy_groups sg ON pr.group_id = sg.group_id AND sg.date = ?
                WHERE sg.id IS NULL AND pr.status IN ('ACTIVE', 'PENDING')
                ORDER BY pr.id
            ''', (today,))
            
            orphaned = cursor.fetchall()
            
            for pos_id, group_id, lot_id, status, entry_time in orphaned:
                # 檢查是否錯誤使用了DB_ID
                cursor.execute('''
                    SELECT id, group_id, date FROM strategy_groups
                    WHERE id = ? OR group_id = ?
                    ORDER BY date DESC
                ''', (group_id, group_id))
                
                potential_matches = cursor.fetchall()
                
                orphaned_positions.append({
                    'position_id': pos_id,
                    'group_id': group_id,
                    'lot_id': lot_id,
                    'status': status,
                    'entry_time': entry_time,
                    'potential_matches': potential_matches
                })
            
            conn.close()
            
            if orphaned_positions:
                print(f"\n🚨 {env_name}發現{len(orphaned_positions)}個孤立部位:")
                for pos in orphaned_positions:
                    print(f"  部位{pos['position_id']} (組{pos['group_id']}_口{pos['lot_id']}) - {pos['status']}")
                    if pos['potential_matches']:
                        print(f"    可能匹配: {pos['potential_matches']}")
            else:
                print(f"✅ {env_name}沒有孤立部位")
            
            return orphaned_positions
            
        except Exception as e:
            print(f"❌ {env_name}孤立部位檢查失敗: {e}")
            return []
    
    def fix_orphaned_positions(self, db_path: str, env_name: str, orphaned_positions: List[Dict]) -> bool:
        """修復孤立部位"""
        if not orphaned_positions:
            return True
        
        print(f"\n🔧 修復{env_name}的孤立部位...")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            today = date.today().isoformat()
            fixes_count = 0
            
            for pos in orphaned_positions:
                position_id = pos['position_id']
                current_group_id = pos['group_id']
                potential_matches = pos['potential_matches']
                
                # 嘗試找到正確的group_id
                correct_group_id = None
                
                # 策略1：檢查是否錯誤使用了DB_ID
                for db_id, logical_group_id, sg_date in potential_matches:
                    if db_id == current_group_id and sg_date == today:
                        # 找到了！current_group_id實際上是DB_ID
                        correct_group_id = logical_group_id
                        print(f"  🔍 部位{position_id}: 發現錯誤使用DB_ID {current_group_id} → 修正為group_id {logical_group_id}")
                        break
                
                # 策略2：檢查是否有同日期的策略組可以匹配
                if not correct_group_id:
                    cursor.execute('''
                        SELECT group_id FROM strategy_groups
                        WHERE date = ? AND group_id != ?
                        ORDER BY id DESC LIMIT 1
                    ''', (today, current_group_id))
                    
                    result = cursor.fetchone()
                    if result:
                        correct_group_id = result[0]
                        print(f"  🔍 部位{position_id}: 嘗試匹配到最新策略組 {correct_group_id}")
                
                # 執行修復
                if correct_group_id:
                    cursor.execute('''
                        UPDATE position_records 
                        SET group_id = ?
                        WHERE id = ?
                    ''', (correct_group_id, position_id))
                    
                    fixes_count += 1
                    self.fixes_applied.append(f"{env_name}: 部位{position_id} group_id {current_group_id} → {correct_group_id}")
                else:
                    print(f"  ⚠️ 部位{position_id}: 無法找到合適的策略組進行修復")
                    self.issues_found.append(f"{env_name}: 部位{position_id} 無法修復")
            
            conn.commit()
            conn.close()
            
            if fixes_count > 0:
                print(f"✅ {env_name}修復了{fixes_count}個孤立部位")
            
            return True
            
        except Exception as e:
            print(f"❌ {env_name}孤立部位修復失敗: {e}")
            return False
    
    def verify_foreign_key_consistency(self, db_path: str, env_name: str) -> bool:
        """驗證外鍵關係一致性"""
        if not os.path.exists(db_path):
            return True
        
        print(f"\n🔍 驗證{env_name}外鍵關係一致性...")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            today = date.today().isoformat()
            
            # 檢查1：所有活躍部位都有對應的策略組
            cursor.execute('''
                SELECT COUNT(*) FROM position_records pr
                LEFT JOIN strategy_groups sg ON pr.group_id = sg.group_id AND sg.date = ?
                WHERE sg.id IS NULL AND pr.status IN ('ACTIVE', 'PENDING')
            ''', (today,))
            
            orphaned_count = cursor.fetchone()[0]
            
            # 檢查2：策略組的total_lots與實際部位數是否一致
            cursor.execute('''
                SELECT sg.group_id, sg.total_lots, COUNT(pr.id) as actual_lots
                FROM strategy_groups sg
                LEFT JOIN position_records pr ON sg.group_id = pr.group_id
                WHERE sg.date = ?
                GROUP BY sg.group_id, sg.total_lots
                HAVING sg.total_lots != COUNT(pr.id)
            ''', (today,))
            
            lot_mismatches = cursor.fetchall()
            
            # 檢查3：重複的group_id（同一天不應該有相同的group_id）
            cursor.execute('''
                SELECT group_id, COUNT(*) as count
                FROM strategy_groups
                WHERE date = ?
                GROUP BY group_id
                HAVING COUNT(*) > 1
            ''', (today,))
            
            duplicate_groups = cursor.fetchall()
            
            conn.close()
            
            # 報告結果
            issues = []
            if orphaned_count > 0:
                issues.append(f"孤立部位: {orphaned_count}個")
            
            if lot_mismatches:
                issues.append(f"口數不匹配: {len(lot_mismatches)}組")
                for group_id, expected, actual in lot_mismatches:
                    print(f"  ⚠️ 組{group_id}: 預期{expected}口，實際{actual}口")
            
            if duplicate_groups:
                issues.append(f"重複組ID: {len(duplicate_groups)}組")
                for group_id, count in duplicate_groups:
                    print(f"  ⚠️ 組{group_id}: 重複{count}次")
            
            if issues:
                print(f"❌ {env_name}外鍵一致性問題: {', '.join(issues)}")
                return False
            else:
                print(f"✅ {env_name}外鍵關係一致性正常")
                return True
            
        except Exception as e:
            print(f"❌ {env_name}外鍵一致性檢查失敗: {e}")
            return False
    
    def check_database_constraints(self, db_path: str, env_name: str) -> bool:
        """檢查資料庫約束"""
        if not os.path.exists(db_path):
            return True
        
        print(f"\n🔍 檢查{env_name}資料庫約束...")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 檢查必要欄位是否存在
            required_fields = {
                'strategy_groups': ['id', 'group_id', 'date', 'direction'],
                'position_records': ['id', 'group_id', 'lot_id', 'direction', 'entry_time']
            }
            
            constraint_issues = []
            
            for table, fields in required_fields.items():
                cursor.execute(f"PRAGMA table_info({table})")
                existing_fields = [row[1] for row in cursor.fetchall()]
                
                for field in fields:
                    if field not in existing_fields:
                        constraint_issues.append(f"{table}缺少欄位: {field}")
            
            # 檢查NOT NULL約束
            cursor.execute("SELECT COUNT(*) FROM strategy_groups WHERE group_id IS NULL")
            null_group_ids = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM position_records WHERE group_id IS NULL")
            null_position_group_ids = cursor.fetchone()[0]
            
            if null_group_ids > 0:
                constraint_issues.append(f"strategy_groups有{null_group_ids}個NULL group_id")
            
            if null_position_group_ids > 0:
                constraint_issues.append(f"position_records有{null_position_group_ids}個NULL group_id")
            
            conn.close()
            
            if constraint_issues:
                print(f"❌ {env_name}約束問題: {constraint_issues}")
                return False
            else:
                print(f"✅ {env_name}資料庫約束正常")
                return True
            
        except Exception as e:
            print(f"❌ {env_name}約束檢查失敗: {e}")
            return False
    
    def run_comprehensive_fix(self):
        """運行綜合修復"""
        print("🚀 開始group_id一致性綜合修復")
        
        all_success = True
        
        for env_name, db_path in self.databases:
            print(f"\n{'='*20} {env_name} {'='*20}")
            
            # 1. 檢查孤立部位
            orphaned_positions = self.check_orphaned_positions(db_path, env_name)
            
            # 2. 修復孤立部位
            if orphaned_positions:
                fix_success = self.fix_orphaned_positions(db_path, env_name, orphaned_positions)
                if not fix_success:
                    all_success = False
            
            # 3. 驗證外鍵一致性
            fk_success = self.verify_foreign_key_consistency(db_path, env_name)
            if not fk_success:
                all_success = False
            
            # 4. 檢查資料庫約束
            constraint_success = self.check_database_constraints(db_path, env_name)
            if not constraint_success:
                all_success = False
        
        # 生成修復報告
        self.generate_fix_report()
        
        return all_success
    
    def generate_fix_report(self):
        """生成修復報告"""
        print("\n" + "=" * 50)
        print("📊 group_id一致性修復報告")
        print("=" * 50)
        
        print(f"修復時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"應用修復: {len(self.fixes_applied)}項")
        print(f"未解決問題: {len(self.issues_found)}項")
        
        if self.fixes_applied:
            print(f"\n✅ 已應用的修復:")
            for fix in self.fixes_applied:
                print(f"  {fix}")
        
        if self.issues_found:
            print(f"\n⚠️ 未解決的問題:")
            for issue in self.issues_found:
                print(f"  {issue}")
        
        # 保存報告
        report_file = f"group_id_fix_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("group_id一致性修復報告\n")
            f.write("=" * 50 + "\n")
            f.write(f"修復時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("已應用的修復:\n")
            for fix in self.fixes_applied:
                f.write(f"  {fix}\n")
            
            f.write("\n未解決的問題:\n")
            for issue in self.issues_found:
                f.write(f"  {issue}\n")
        
        print(f"\n📄 詳細報告已保存至: {report_file}")
        
        if len(self.fixes_applied) > 0:
            print("\n💡 建議:")
            print("  1. 重新運行生產環境檢查工具驗證修復效果")
            print("  2. 測試實際交易功能確保正常運行")
            print("  3. 監控後續運行中是否還有ID一致性問題")

if __name__ == "__main__":
    fixer = GroupIDConsistencyFixer()
    success = fixer.run_comprehensive_fix()
    
    if success:
        print("\n🎉 group_id一致性修復完成：所有檢查通過！")
    else:
        print("\n⚠️ group_id一致性修復完成：仍有部分問題需要手動處理")
    
    exit(0 if success else 1)
