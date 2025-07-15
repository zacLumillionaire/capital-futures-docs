#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單測試修復
"""

def test_dict_access():
    """測試字典訪問"""
    print("🧪 測試字典訪問...")
    
    # 模擬數據庫返回的數據
    test_group = {
        'group_pk': 3,
        'logical_group_id': 1,
        'date': '2025-07-15',
        'direction': 'LONG'
    }
    
    print(f"📋 測試數據: {test_group}")
    print(f"📋 可用鍵: {list(test_group.keys())}")
    
    # 測試舊的錯誤訪問方式
    try:
        old_access = test_group['group_id']
        print(f"❌ 舊方式成功: {old_access}")
    except KeyError as e:
        print(f"✅ 舊方式失敗 (預期): {e}")
    
    # 測試新的正確訪問方式
    try:
        new_access = test_group['logical_group_id']
        pk_access = test_group['group_pk']
        print(f"✅ 新方式成功: logical_group_id={new_access}, group_pk={pk_access}")
    except KeyError as e:
        print(f"❌ 新方式失敗: {e}")
    
    print("🎉 字典訪問測試完成!")

if __name__ == "__main__":
    test_dict_access()
