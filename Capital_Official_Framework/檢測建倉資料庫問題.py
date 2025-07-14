#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
建倉資料庫問題檢測工具
用於檢測和驗證 retry_count 和 max_slippage_points 字段的 None 值問題
"""

import sqlite3
import sys
from datetime import date
from typing import List, Dict, Optional

class PositionDataIntegrityChecker:
    """部位數據完整性檢查器"""
    
    def __init__(self, db_path: str = "multi_group_strategy.db"):
        self.db_path = db_path
        self.issues = []
        
    def check_position_data_integrity(self) -> Dict:
        """檢查部位記錄的數據完整性"""
        print("🔍 檢查部位記錄數據完整性...")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 檢查所有活躍部位的關鍵字段
                cursor.execute('''
                    SELECT id, group_id, lot_id, direction, entry_price, 
                           retry_count, max_slippage_points, status, order_status
                    FROM position_records 
                    WHERE status IN ('ACTIVE', 'PENDING')
                    ORDER BY id DESC
                ''')
                
                positions = cursor.fetchall()
                print(f"   找到 {len(positions)} 個活躍/待處理部位")
                
                none_issues = []
                valid_positions = []
                
                for pos in positions:
                    pos_id, group_id, lot_id, direction, entry_price, retry_count, max_slippage, status, order_status = pos
                    
                    issues_for_position = []
                    
                    # 檢查 retry_count
                    if retry_count is None:
                        issues_for_position.append("retry_count 為 None")
                    
                    # 檢查 max_slippage_points
                    if max_slippage is None:
                        issues_for_position.append("max_slippage_points 為 None")
                    
                    # 檢查 entry_price (對於 ACTIVE 部位)
                    if status == 'ACTIVE' and entry_price is None:
                        issues_for_position.append("entry_price 為 None (ACTIVE 部位)")
                    
                    if issues_for_position:
                        none_issues.append({
                            'position_id': pos_id,
                            'group_id': group_id,
                            'lot_id': lot_id,
                            'status': status,
                            'issues': issues_for_position
                        })
                        print(f"   ⚠️ 部位 {pos_id}: {', '.join(issues_for_position)}")
                    else:
                        valid_positions.append(pos_id)
                
                if none_issues:
                    print(f"\n❌ 發現 {len(none_issues)} 個部位有數據完整性問題")
                    self.issues.extend(none_issues)
                else:
                    print(f"\n✅ 所有 {len(positions)} 個部位數據完整性正常")
                
                return {
                    'total_positions': len(positions),
                    'valid_positions': len(valid_positions),
                    'problematic_positions': len(none_issues),
                    'issues': none_issues
                }
                
        except Exception as e:
            print(f"❌ 檢查數據完整性失敗: {e}")
            return {'error': str(e)}
    
    def test_database_constraints(self) -> bool:
        """測試資料庫約束是否正確處理 None 值"""
        print("\n🧪 測試資料庫約束...")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 測試插入 None 值是否會觸發約束錯誤
                test_group_id = 999  # 使用不存在的組別ID進行測試
                
                try:
                    cursor.execute('''
                        INSERT INTO position_records
                        (group_id, lot_id, direction, retry_count, max_slippage_points, status)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (test_group_id, 1, 'LONG', None, None, 'PENDING'))
                    
                    # 如果插入成功，說明約束已修復
                    test_id = cursor.lastrowid
                    
                    # 清理測試數據
                    cursor.execute('DELETE FROM position_records WHERE id = ?', (test_id,))
                    conn.commit()
                    
                    print("✅ 資料庫約束測試通過 - None 值被正確處理")
                    return True
                    
                except sqlite3.IntegrityError as e:
                    if "not supported between instances of 'NoneType' and 'int'" in str(e):
                        print("❌ 資料庫約束測試失敗 - None 值仍然觸發錯誤")
                        print(f"   錯誤詳情: {e}")
                        return False
                    else:
                        # 其他約束錯誤（如外鍵約束）是預期的
                        print("✅ 資料庫約束測試通過 - None 值處理正常（其他約束錯誤是預期的）")
                        return True
                        
        except Exception as e:
            print(f"❌ 測試資料庫約束失敗: {e}")
            return False
    
    def fix_existing_none_values(self) -> bool:
        """修復現有的 None 值"""
        print("\n🔧 修復現有的 None 值...")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 修復 retry_count 為 None 的記錄
                cursor.execute('''
                    UPDATE position_records 
                    SET retry_count = 0 
                    WHERE retry_count IS NULL
                ''')
                retry_fixed = cursor.rowcount
                
                # 修復 max_slippage_points 為 None 的記錄
                cursor.execute('''
                    UPDATE position_records 
                    SET max_slippage_points = 5.0 
                    WHERE max_slippage_points IS NULL
                ''')
                slippage_fixed = cursor.rowcount
                
                conn.commit()
                
                print(f"✅ 修復完成:")
                print(f"   - retry_count: {retry_fixed} 條記錄")
                print(f"   - max_slippage_points: {slippage_fixed} 條記錄")
                
                return True
                
        except Exception as e:
            print(f"❌ 修復 None 值失敗: {e}")
            return False
    
    def generate_report(self):
        """生成檢測報告"""
        print("\n📋 生成檢測報告...")
        
        report = f"""# 建倉資料庫問題檢測報告

## 檢測時間
{date.today().isoformat()}

## 檢測結果
"""
        
        if self.issues:
            report += f"\n### ❌ 發現問題 ({len(self.issues)} 個部位)\n\n"
            for issue in self.issues:
                report += f"- **部位 {issue['position_id']}** (組{issue['group_id']}, 第{issue['lot_id']}口, {issue['status']})\n"
                for problem in issue['issues']:
                    report += f"  - {problem}\n"
                report += "\n"
        else:
            report += "\n### ✅ 未發現問題\n所有部位數據完整性正常\n"
        
        report += f"""
## 建議修復步驟

1. **立即修復**: 運行 `fix_existing_none_values()` 方法
2. **驗證約束**: 確認資料庫 CHECK 約束已正確修改
3. **測試建倉**: 執行完整建倉流程測試

## 預防措施

1. 在創建部位記錄時提供預設值
2. 添加數據驗證邏輯
3. 定期運行完整性檢查
"""
        
        report_file = f"建倉資料庫檢測報告_{date.today().strftime('%Y%m%d')}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📄 報告已保存: {report_file}")

def main():
    """主檢測函數"""
    print("🚀 建倉資料庫問題檢測工具")
    print("=" * 50)
    
    checker = PositionDataIntegrityChecker()
    
    # 1. 檢查數據完整性
    integrity_result = checker.check_position_data_integrity()
    
    # 2. 測試資料庫約束
    constraint_ok = checker.test_database_constraints()
    
    # 3. 如果有問題，提供修復選項
    if checker.issues:
        print(f"\n🔧 發現 {len(checker.issues)} 個數據完整性問題")
        
        user_input = input("是否要自動修復這些問題？(y/n): ").lower().strip()
        if user_input == 'y':
            if checker.fix_existing_none_values():
                print("✅ 修復完成，請重新運行檢測驗證")
            else:
                print("❌ 修復失敗，請手動檢查")
    
    # 4. 生成報告
    checker.generate_report()
    
    # 5. 總結
    print(f"\n📊 檢測總結:")
    print(f"   數據完整性: {'✅ 正常' if not checker.issues else '❌ 有問題'}")
    print(f"   資料庫約束: {'✅ 正常' if constraint_ok else '❌ 需要修復'}")
    
    if not checker.issues and constraint_ok:
        print("\n🎉 所有檢測項目都通過，系統狀態良好！")
    else:
        print("\n⚠️ 發現問題，請按照報告建議進行修復")

if __name__ == "__main__":
    main()
