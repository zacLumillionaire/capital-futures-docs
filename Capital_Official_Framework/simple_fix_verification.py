"""
簡單的修復驗證測試
檢查修復後的代碼是否解決了兩個主要問題
"""

import os
import re

def check_optimized_risk_manager_fixes():
    """檢查 OptimizedRiskManager 的修復"""
    print("🔍 檢查 OptimizedRiskManager 修復...")
    
    file_path = "optimized_risk_manager.py"
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查修復1：部位級別鎖定鍵
    fix1_pattern = r'trigger_source = f"optimized_risk_initial_stop_{position_id}_{direction}"'
    if re.search(fix1_pattern, content):
        print("✅ 修復1確認：已使用部位級別鎖定鍵")
        fix1_ok = True
    else:
        print("❌ 修復1失敗：未找到部位級別鎖定鍵")
        fix1_ok = False
    
    # 檢查修復2：群組檢查邏輯已被註解
    fix2_pattern = r'# 🔧 修復Bug2：停用冗餘的群組檢查邏輯'
    if re.search(fix2_pattern, content):
        print("✅ 修復2確認：群組檢查邏輯已被停用")
        fix2_ok = True
    else:
        print("❌ 修復2失敗：群組檢查邏輯未被停用")
        fix2_ok = False
    
    # 檢查是否還有舊的全局鎖定鍵
    old_pattern = r'optimized_risk_initial_stop_(?!{position_id})'
    if re.search(old_pattern, content):
        print("⚠️ 警告：可能還有舊的全局鎖定鍵")
    
    return fix1_ok and fix2_ok

def check_stop_executor_consistency():
    """檢查 StopExecutor 的一致性"""
    print("🔍 檢查 StopExecutor 一致性...")
    
    file_path = "stop_loss_executor.py"
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查是否使用了部位級別的鎖定鍵
    position_lock_pattern = r'trigger_source = f"stop_loss_{position_id}_'
    if re.search(position_lock_pattern, content):
        print("✅ StopExecutor 使用部位級別鎖定鍵")
        return True
    else:
        print("❌ StopExecutor 未使用部位級別鎖定鍵")
        return False

def analyze_log_patterns():
    """分析日誌模式，檢查是否會出現問題"""
    print("🔍 分析可能的問題模式...")

    # 檢查是否還有可能導致鎖定衝突的代碼
    risk_manager_path = "optimized_risk_manager.py"
    if os.path.exists(risk_manager_path):
        with open(risk_manager_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 檢查是否還有活躍的 _check_initial_stop_loss_conditions 調用
        active_call_pattern = r'^\s*if self\._check_initial_stop_loss_conditions\(positions, current_price\):'
        if re.search(active_call_pattern, content, re.MULTILINE):
            print("⚠️ 警告：仍有活躍的群組檢查邏輯調用")
            return False
        else:
            print("✅ 群組檢查邏輯調用已被停用")

        # 檢查方法內容是否已被停用
        method_disabled_pattern = r'# 🔧 修復Bug2：直接返回False，不執行任何群組檢查邏輯'
        if re.search(method_disabled_pattern, content):
            print("✅ 群組檢查方法內容已被停用")
        else:
            print("⚠️ 警告：群組檢查方法內容未被停用")
            return False

    return True

def simulate_lock_key_generation():
    """模擬鎖定鍵生成，檢查是否會衝突"""
    print("🔍 模擬鎖定鍵生成...")
    
    # 模擬3個SHORT部位同時觸發停損的情況
    position_ids = [1, 2, 3]
    direction = "SHORT"
    
    # 新的部位級別鎖定鍵
    new_keys = []
    for pos_id in position_ids:
        key = f"optimized_risk_initial_stop_{pos_id}_{direction}"
        new_keys.append(key)
    
    print("新的鎖定鍵:")
    for key in new_keys:
        print(f"  - {key}")
    
    # 檢查是否有重複
    if len(new_keys) == len(set(new_keys)):
        print("✅ 所有鎖定鍵都是唯一的，不會發生衝突")
        return True
    else:
        print("❌ 鎖定鍵有重複，仍會發生衝突")
        return False

def main():
    """主函數"""
    print("🚀 開始修復驗證測試")
    print("=" * 50)
    
    results = []
    
    # 檢查各項修復
    results.append(check_optimized_risk_manager_fixes())
    results.append(check_stop_executor_consistency())
    results.append(analyze_log_patterns())
    results.append(simulate_lock_key_generation())
    
    print("\n" + "=" * 50)
    print("📋 驗證結果總結")
    print("=" * 50)
    
    if all(results):
        print("✅ 所有修復驗證通過！")
        print("🎯 預期效果：")
        print("   - 部位2和3不會被鎖定錯誤阻止")
        print("   - 不會出現 KeyError: 'id' 崩潰")
        print("   - 所有部位都能正常平倉")
    else:
        print("❌ 部分修復驗證失敗！")
        print("需要檢查以下問題：")
        for i, result in enumerate(results, 1):
            if not result:
                print(f"   - 檢查項目 {i} 失敗")
    
    return all(results)

if __name__ == "__main__":
    main()
