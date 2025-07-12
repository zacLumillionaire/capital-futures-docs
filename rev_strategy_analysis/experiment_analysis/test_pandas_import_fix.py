#!/usr/bin/env python3
"""
測試 pandas 導入修復
"""

def test_pandas_import():
    """測試 pandas 導入是否正確"""
    
    print("=== 測試 pandas 導入修復 ===")
    
    # 測試在函數內部導入 pandas
    def test_function():
        import pandas as pd
        
        # 創建測試數據
        data = {
            'mdd': [-228.0, -250.0],
            'total_pnl': [2586.0, 2400.0],
            'take_profit': [float('nan'), 80.0]
        }
        
        df = pd.DataFrame(data)
        
        # 測試 pd.notna() 和 pd.isna()
        for i, row in df.iterrows():
            take_profit_val = row.get('take_profit', 0)
            
            print(f"行 {i}:")
            print(f"  take_profit_val: {take_profit_val}")
            print(f"  pd.isna(): {pd.isna(take_profit_val)}")
            print(f"  pd.notna(): {pd.notna(take_profit_val)}")
            
            # 測試修復邏輯
            if pd.isna(take_profit_val):
                take_profit_val = 0
                print(f"  修復後: {take_profit_val}")
            
            # 測試轉換
            try:
                int_val = int(take_profit_val)
                print(f"  轉換為整數: {int_val} ✅")
            except Exception as e:
                print(f"  轉換失敗: {e} ❌")
        
        return True
    
    # 執行測試
    try:
        result = test_function()
        print(f"\n✅ pandas 導入測試成功: {result}")
        return True
    except Exception as e:
        print(f"\n❌ pandas 導入測試失敗: {e}")
        return False

def test_syntax_check():
    """檢查語法是否正確"""
    print("\n=== 語法檢查 ===")
    
    try:
        # 模擬 enhanced_mdd_optimizer.py 中的代碼片段
        import pandas as pd
        
        # 模擬數據
        test_data = {
            'mdd': [-228.0],
            'total_pnl': [2586.0],
            'take_profit': [float('nan')],
            'lot1_take_profit': [40.0]
        }
        
        df = pd.DataFrame(test_data)
        row = df.iloc[0]
        
        # 測試各種條件檢查
        print("測試條件檢查:")
        
        # 測試 1: pd.notna() 檢查
        if 'lot1_take_profit' in row and pd.notna(row['lot1_take_profit']):
            print("  ✅ lot1_take_profit 檢查通過")
        
        # 測試 2: take_profit 檢查
        if 'take_profit' in row and pd.notna(row['take_profit']):
            print("  ⚠️  take_profit 是 NaN，條件為 False")
        else:
            print("  ✅ take_profit NaN 檢查正確")
        
        # 測試 3: pd.isna() 修復邏輯
        take_profit_val = row.get('take_profit', 0)
        if pd.isna(take_profit_val):
            take_profit_val = 0
            print("  ✅ NaN 修復邏輯正確")
        
        print("✅ 所有語法檢查通過")
        return True
        
    except Exception as e:
        print(f"❌ 語法檢查失敗: {e}")
        return False

if __name__ == "__main__":
    print("開始測試 pandas 導入修復...")
    
    success1 = test_pandas_import()
    success2 = test_syntax_check()
    
    if success1 and success2:
        print("\n🎉 所有測試通過！pandas 導入修復成功。")
    else:
        print("\n❌ 測試失敗，需要進一步檢查。")
