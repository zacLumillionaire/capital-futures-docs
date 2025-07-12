#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
調試OnNewData欄位分析工具
分析實際回報數據中的買賣別位置
"""

def analyze_onnewdata_fields():
    """分析你的實際LOG數據"""
    print("🔍 分析實際OnNewData回報數據")
    print("=" * 60)
    
    # 你的實際LOG數據
    raw_data = "2315544959105,TF,N,N,F020000,6363839,SNF20,TW,TM2507,,u1875,22353.0000,,,,,,,,,1,,,20250707,09:58:06,,0000000,7174,y,20250707,2110000519435,A,FITM,202507,,,,,,,A,20250707,,,,,N,,2315544959105"
    
    fields = raw_data.split(',')
    
    print(f"📊 總欄位數: {len(fields)}")
    print()
    
    # 分析每個欄位
    print("📋 欄位詳細分析:")
    for i, field in enumerate(fields):
        # 標記重要欄位
        importance = ""
        if i == 0:
            importance = "⭐ KeyNo (委託序號)"
        elif i == 1:
            importance = "⭐ MarketType (市場類型)"
        elif i == 2:
            importance = "⭐ Type (委託狀態)"
        elif i == 3:
            importance = "⭐ OrderErr (委託結果)"
        elif i == 4:
            importance = "⭐ Broker (券商代號)"
        elif i == 5:
            importance = "⭐ CustNo (交易帳號)"
        elif i == 6:
            importance = "❓ 可能的BuySell?"
        elif i == 7:
            importance = "⭐ ExchangeNo (交易所)"
        elif i == 8:
            importance = "⭐ StockNo (商品代號)"
        elif i == 11:
            importance = "⭐ Price (價格)"
        elif i == 20:
            importance = "⭐ Qty (數量)"
        elif i == 23:
            importance = "⭐ Date (日期)"
        elif i == 24:
            importance = "⭐ Time (時間)"
        elif i == 47:
            importance = "⭐ SeqNo (新序號)"
        
        print(f"   [{i:2d}] '{field}' {importance}")
    
    print()
    
    # 尋找可能的買賣別欄位
    print("🔍 尋找買賣別欄位:")
    possible_buysell_fields = []
    
    for i, field in enumerate(fields):
        if field in ['B', 'S', 'BUY', 'SELL', 'Buy', 'Sell']:
            possible_buysell_fields.append((i, field))
    
    if possible_buysell_fields:
        print("   找到可能的買賣別欄位:")
        for idx, value in possible_buysell_fields:
            print(f"   索引[{idx}]: '{value}'")
    else:
        print("   ❌ 沒有找到明顯的買賣別欄位 (B/S)")
    
    print()
    
    # 分析特殊欄位
    print("🔍 特殊欄位分析:")
    print(f"   索引[6]: '{fields[6]}' - 原以為是BuySell，實際是: {analyze_field_content(fields[6])}")
    print(f"   索引[10]: '{fields[10]}' - {analyze_field_content(fields[10])}")
    print(f"   索引[31]: '{fields[31]}' - {analyze_field_content(fields[31])}")
    print(f"   索引[40]: '{fields[40]}' - {analyze_field_content(fields[40])}")
    
    return fields

def analyze_field_content(field_value):
    """分析欄位內容的可能含義"""
    if not field_value:
        return "空值"
    elif field_value in ['B', 'S']:
        return "可能是買賣別"
    elif field_value in ['BUY', 'SELL']:
        return "可能是買賣別(英文)"
    elif field_value in ['A', 'N', 'Y']:
        return "可能是狀態碼"
    elif field_value.isdigit():
        return "數字"
    elif len(field_value) == 1:
        return "單字元代碼"
    elif len(field_value) > 10:
        return "長字串/序號"
    else:
        return "未知格式"

def compare_with_expected_format():
    """與預期格式對比"""
    print("\n📋 與群益API文檔對比:")
    print("=" * 60)
    
    expected_format = [
        "KeyNo (委託序號)",
        "MarketType (市場類型)",
        "Type (委託狀態)",
        "OrderErr (委託結果)",
        "Broker (券商代號)",
        "CustNo (交易帳號)",
        "BuySell (買賣別)",  # 這裡應該是B或S
        "PositionType (倉別)",
        "OrderCond (委託條件)",
        "PriceType (價格類型)",
        "StockNo (商品代號)",
        "OrderNo (委託編號)",
        "Price (價格)",
        # ... 其他欄位
    ]
    
    actual_data = "2315544959105,TF,N,N,F020000,6363839,SNF20,TW,TM2507,,u1875,22353.0000".split(',')
    
    print("預期 vs 實際:")
    for i, (expected, actual) in enumerate(zip(expected_format, actual_data)):
        match_status = "✅" if is_field_match(expected, actual, i) else "❌"
        print(f"   [{i:2d}] {match_status} {expected:20} -> '{actual}'")
    
    print()
    print("🔍 關鍵發現:")
    print("   索引[6]: 預期'B'或'S'，實際'SNF20' ❌")
    print("   這表明欄位順序可能與文檔不同，或有額外欄位")

def is_field_match(expected, actual, index):
    """檢查欄位是否符合預期"""
    if index == 0:  # KeyNo
        return actual.isdigit() and len(actual) > 10
    elif index == 1:  # MarketType
        return actual in ['TF', 'TO', 'TS']
    elif index == 2:  # Type
        return actual in ['N', 'C', 'D', 'U', 'P', 'B', 'S', 'X', 'R']
    elif index == 3:  # OrderErr
        return actual in ['N', 'Y', 'T']
    elif index == 6:  # BuySell (關鍵檢查)
        return actual in ['B', 'S']
    else:
        return True  # 其他欄位暫時不檢查

def suggest_solution():
    """建議解決方案"""
    print("\n💡 解決方案建議:")
    print("=" * 60)
    
    print("1. **完全放棄方向檢測**:")
    print("   - 既然OnNewData中沒有可靠的買賣別欄位")
    print("   - 完全依賴FIFO匹配機制")
    print("   - 基於時間+價格+商品的組合匹配")
    
    print()
    print("2. **FIFO匹配邏輯**:")
    print("   - 下單時記錄: (時間, 價格, 數量, 方向, 商品)")
    print("   - 回報時匹配: 忽略方向，只用價格+時間+商品")
    print("   - 按FIFO順序匹配最早的未完成訂單")
    
    print()
    print("3. **實施步驟**:")
    print("   - ✅ 修改_detect_direction()返回UNKNOWN")
    print("   - ✅ 修改匹配邏輯不依賴方向")
    print("   - ✅ 加強價格容差和時間窗口匹配")
    print("   - ✅ 測試新的匹配機制")

if __name__ == "__main__":
    print("🚀 OnNewData欄位調試分析工具")
    print("🎯 目標: 找到買賣別欄位的正確位置")
    print()
    
    # 分析實際數據
    fields = analyze_onnewdata_fields()
    
    # 與預期格式對比
    compare_with_expected_format()
    
    # 建議解決方案
    suggest_solution()
    
    print("\n🎯 結論:")
    print("   群益API的OnNewData回報中可能沒有明確的買賣別欄位")
    print("   或者欄位順序與文檔不同")
    print("   建議完全依賴FIFO匹配機制，不再嘗試方向檢測")
