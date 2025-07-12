#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用者帳號配置檔案
根據記憶中的帳號資訊進行設定
"""

# 使用者帳號資訊
USER_CONFIG = {
    # 登入資訊
    'USER_ID': 'E123354882',  # 您的身分證字號
    'PASSWORD': 'kkd5ysUCC',  # 您的密碼
    
    # 期貨帳號資訊
    'FUTURES_ACCOUNT': 'F0200006363839',  # 完整期貨帳號 (含前綴)
    'FUTURES_BRANCH': 'F020000',          # 期貨分公司代碼
    'FUTURES_ACCOUNT_NO': '6363839',      # 純帳號數字
    
    # 預設交易商品
    'DEFAULT_PRODUCT': 'MTX00',           # 小台指期貨
    'ALTERNATIVE_PRODUCT': 'TM0000',      # 微型台指期貨
    
    # 測試參數
    'TEST_QUANTITY': 1,                   # 測試數量 (最小單位)
    'TEST_PRICE': 22000,                  # 測試價格
    
    # 自動登入設定
    'AUTO_LOGIN': True,                   # 是否自動登入
    'SAVE_PASSWORD': True,                # 是否儲存密碼
}

# 商品代碼對照表
PRODUCT_MAPPING = {
    'MTX00': {
        'name': '小台指期貨(近月)',
        'description': '小型台灣加權股價指數期貨近月合約',
        'tick_size': 1,
        'contract_size': 50,  # 每點50元
        'margin': 45000       # 約略保證金
    },
    'TM0000': {
        'name': '微型台指期貨',
        'description': '微型台灣加權股價指數期貨',
        'tick_size': 1,
        'contract_size': 5,   # 每點5元 (1/10小台)
        'margin': 4500        # 約略保證金
    }
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

📋 您的帳號設定：
- 期貨帳號: F0200006363839
- 預設商品: MTX00 (小台指)
- 測試數量: 1口
- 自動登入: 已啟用
"""

def get_user_config():
    """取得使用者配置"""
    return USER_CONFIG

def get_product_info(product_code):
    """取得商品資訊"""
    return PRODUCT_MAPPING.get(product_code, {})

def show_risk_warning():
    """顯示風險提醒"""
    print(RISK_WARNING)

if __name__ == "__main__":
    print("=== 群益證券API - 使用者配置 ===")
    show_risk_warning()
    
    config = get_user_config()
    print(f"\n📋 目前配置：")
    for key, value in config.items():
        if 'PASSWORD' in key:
            print(f"  {key}: {'*' * len(str(value))}")
        else:
            print(f"  {key}: {value}")
