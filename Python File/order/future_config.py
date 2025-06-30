#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期貨下單設定檔 - 根據官方案例
"""

# 買賣別設定
BUYSELLSET = [
    "買進",
    "賣出"
]

# 委託條件設定
PERIODSET = {
    'future': [
        "ROD",
        "IOC", 
        "FOK"
    ]
}

# 當沖與否設定
FLAGSET = {
    'future': [
        "非當沖",
        "當沖"
    ]
}

# 倉別設定
NEWCLOSESET = {
    'future': [
        "新倉",
        "平倉",
        "自動"
    ]
}

# 盤別設定
RESERVEDSET = [
    "盤中",
    "T盤預約"
]

# 常用期貨商品代碼 (根據群益API官方格式)
FUTURE_PRODUCTS = {
    # 小台指期貨 (推薦使用)
    'MTX00': {
        'name': '小台指期貨(近月)',
        'code': 'MTX00',
        'description': '小型台灣加權股價指數期貨近月合約',
        'tick_size': 1,
        'contract_size': 50
    },
    'MXFR1': {
        'name': '小台指期貨(R1格式)',
        'code': 'MXFR1',
        'description': '小型台灣加權股價指數期貨近月合約',
        'tick_size': 1,
        'contract_size': 50
    },
    # 台指期貨 (大台)
    'TX00': {
        'name': '台指期貨(近月)',
        'code': 'TX00',
        'description': '台灣加權股價指數期貨近月合約',
        'tick_size': 1,
        'contract_size': 200
    },
    'TXFR1': {
        'name': '台指期貨(R1格式)',
        'code': 'TXFR1',
        'description': '台灣加權股價指數期貨近月合約',
        'tick_size': 1,
        'contract_size': 200
    },
    
    # 電子期貨
    'TE': {
        'name': '電子期貨',
        'code': 'TE', 
        'description': '電子類股價指數期貨',
        'tick_size': 0.05,
        'contract_size': 4000
    },
    'TF': {
        'name': '金融期貨',
        'code': 'TF',
        'description': '金融保險類股價指數期貨', 
        'tick_size': 0.05,
        'contract_size': 1000
    },
    
    # 其他期貨
    'GTX': {
        'name': '櫃買期貨',
        'code': 'GTX',
        'description': '櫃買中心股價指數期貨',
        'tick_size': 0.05,
        'contract_size': 1000
    }
}

# 期貨月份代碼
FUTURE_MONTHS = [
    "202501",  # 2025年1月
    "202502",  # 2025年2月  
    "202503",  # 2025年3月
    "202504",  # 2025年4月
    "202505",  # 2025年5月
    "202506",  # 2025年6月
    "202507",  # 2025年7月
    "202508",  # 2025年8月
    "202509",  # 2025年9月
    "202510",  # 2025年10月
    "202511",  # 2025年11月
    "202512",  # 2025年12月
]

# 測試用期貨設定
TEST_FUTURE_CONFIG = {
    'ACCOUNT': 'F0200006363839',  # 期貨帳號 (含前綴)
    'BRANCH': 'F020000',         # 期貨帳號前綴
    'PRODUCT_CODE': 'MTX00',     # 測試用商品代碼 (小台指近月)
    'MONTH': '202501',           # 測試用月份
    'QUANTITY': 1,               # 測試用數量 (最小單位)
    'PRICE': 22000               # 測試用價格
}

# 風險提醒
RISK_WARNING = """
⚠️ 期貨交易風險提醒：
1. 期貨具有高槓桿特性，可能產生巨大損失
2. 請確保充分了解期貨交易規則
3. 建議先使用最小單位進行測試
4. 請確認保證金充足
5. 注意結算日和到期日
6. 當沖交易需注意時間限制
"""
