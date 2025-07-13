#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Graphiti知識庫狀態檢查腳本
檢查simple_integrated.py相關記錄的提交狀態
"""

import sys
import os

# 添加當前目錄到路徑，以便導入MCP工具
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_graphiti_records():
    """檢查Graphiti中的記錄狀態"""

    # 我們提交的記錄名稱列表
    submitted_records = [
        # 第一批：系統架構分析
        "Capital Trading System Architecture Analysis",
        "SimpleIntegratedApp Class Analysis",
        "Trading Signal Generation Functions",
        "Position Management Functions",
        "Event Handler Classes Analysis",
        "Stop-Loss and Trailing Stop Implementation",
        "System Architecture and Component Relationships",
        "Core Strategy Functions Detailed Analysis",
        "Order Execution and Multi-Group Integration",
        "Safety Design and GIL Problem Solutions",

        # 第二批：交易生命週期分析
        "Trading Entry Signal Generation and Execution",
        "Order Execution Mechanism and Price Determination",
        "Price Chasing Logic and Order Management",
        "Initial Stop-Loss Calculation and Implementation",
        "Trading Lifecycle Risk Management Design",

        # 第三批：在倉風險管理分析
        "Protective Stop-Loss Mechanisms Analysis",
        "Trailing Stop Activation and Logic",
        "Exit Condition Priority and Interaction",
        "EOD Close and Alternative Exit Conditions",
        "Position Exit Execution and P&L Calculation"
    ]

    # 從最近的記憶片段中找到的記錄
    found_in_episodes = [
        "Capital Trading System Architecture Analysis",
        "SimpleIntegratedApp Class Analysis",
        "Trading Signal Generation Functions",
        "Position Management Functions",
        "Event Handler Classes Analysis",
        "Stop-Loss and Trailing Stop Implementation",
        "System Architecture and Component Relationships",
        "Core Strategy Functions Detailed Analysis",
        "Order Execution and Multi-Group Integration",
        "Safety Design and GIL Problem Solutions",
        "Trading Entry Signal Generation and Execution",
        "Order Execution Mechanism and Price Determination",
        "Price Chasing Logic and Order Management",
        "Initial Stop-Loss Calculation and Implementation",
        "Trading Lifecycle Risk Management Design"
    ]

    print("🔍 檢查Graphiti知識庫記錄狀態")
    print("=" * 60)

    found_records = []
    missing_records = []

    # 檢查每個記錄
    for i, record_name in enumerate(submitted_records, 1):
        print(f"\n{i:2d}. 檢查: {record_name}")

        if record_name in found_in_episodes:
            print(f"    狀態: ✅ 已找到")
            found_records.append(record_name)
        else:
            print(f"    狀態: ❌ 遺失")
            missing_records.append(record_name)

    print("\n" + "=" * 60)
    print("📊 檢查結果統計")
    print(f"總記錄數: {len(submitted_records)}")
    print(f"已找到: {len(found_records)}")
    print(f"遺失: {len(missing_records)}")

    if missing_records:
        print("\n❌ 遺失的記錄:")
        for record in missing_records:
            print(f"   - {record}")

    return found_records, missing_records

def generate_resubmit_script(missing_records):
    """生成重新提交腳本"""
    if not missing_records:
        print("\n✅ 所有記錄都已存在，無需重新提交")
        return
    
    print(f"\n📝 生成重新提交腳本 (共{len(missing_records)}個記錄)")
    
    script_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新提交遺失的Graphiti記錄
自動生成的腳本
"""

# 重新提交遺失的記錄
missing_records_data = {
'''
    
    # 這裡需要包含實際的記錄內容
    # 由於我們無法在腳本中直接訪問原始內容，我們先生成框架
    
    for record in missing_records:
        script_content += f'''
    "{record}": {{
        "episode_body": "需要重新填入內容...",
        "source": "text",
        "source_description": "重新提交的記錄"
    }},'''
    
    script_content += '''
}

def resubmit_missing_records():
    """重新提交遺失的記錄"""
    for name, data in missing_records_data.items():
        print(f"重新提交: {name}")
        # 這裡需要調用實際的add_memory_python函數
        # add_memory_python(name=name, **data)

if __name__ == "__main__":
    resubmit_missing_records()
'''
    
    # 保存重新提交腳本
    with open("resubmit_missing_records.py", "w", encoding="utf-8") as f:
        f.write(script_content)
    
    print("✅ 重新提交腳本已生成: resubmit_missing_records.py")

def main():
    """主函數"""
    print("🚀 啟動Graphiti狀態檢查")
    
    try:
        found_records, missing_records = check_graphiti_records()
        generate_resubmit_script(missing_records)
        
        print("\n💡 使用說明:")
        print("1. 這個腳本提供了檢查框架")
        print("2. 實際檢查需要在有MCP工具的環境中進行")
        print("3. 您可以手動使用search_memory_nodes_python來檢查每個記錄")
        print("4. 對於遺失的記錄，可以重新提交")
        
        print("\n🔧 手動檢查命令範例:")
        print("search_memory_nodes_python(query='SimpleIntegratedApp')")
        print("search_memory_facts_python(query='Trading Signal Generation')")
        
    except Exception as e:
        print(f"❌ 檢查過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
