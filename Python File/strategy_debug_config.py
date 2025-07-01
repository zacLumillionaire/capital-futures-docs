#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略調試配置文件
用於控制策略功能的漸進式集成
"""

# 調試級別定義
DEBUG_LEVELS = {
    0: "完全禁用策略功能（穩定版本）",
    1: "只顯示策略標籤頁（空白頁面）",
    2: "顯示基本策略面板（無功能）", 
    3: "添加策略控制按鈕（無事件）",
    4: "添加價格顯示功能",
    5: "添加API接口集成",
    6: "完整策略功能"
}

# 當前調試級別 - 從0開始逐步提升
CURRENT_DEBUG_LEVEL = 0

# 詳細日誌開關
ENABLE_DETAILED_LOGGING = True

# 安全回退開關
ENABLE_SAFE_FALLBACK = True

# GIL錯誤檢測
ENABLE_GIL_DETECTION = True

def get_debug_level():
    """獲取當前調試級別"""
    return CURRENT_DEBUG_LEVEL

def get_debug_description():
    """獲取當前調試級別的描述"""
    return DEBUG_LEVELS.get(CURRENT_DEBUG_LEVEL, "未知級別")

def is_strategy_enabled():
    """檢查策略功能是否啟用"""
    return CURRENT_DEBUG_LEVEL > 0

def is_strategy_panel_enabled():
    """檢查策略面板是否啟用"""
    return CURRENT_DEBUG_LEVEL >= 2

def is_strategy_controls_enabled():
    """檢查策略控制是否啟用"""
    return CURRENT_DEBUG_LEVEL >= 3

def is_price_display_enabled():
    """檢查價格顯示是否啟用"""
    return CURRENT_DEBUG_LEVEL >= 4

def is_api_integration_enabled():
    """檢查API集成是否啟用"""
    return CURRENT_DEBUG_LEVEL >= 5

def is_full_strategy_enabled():
    """檢查完整策略功能是否啟用"""
    return CURRENT_DEBUG_LEVEL >= 6

def log_debug_status():
    """記錄當前調試狀態"""
    if ENABLE_DETAILED_LOGGING:
        print(f"[DEBUG] 當前調試級別: {CURRENT_DEBUG_LEVEL}")
        print(f"[DEBUG] 級別描述: {get_debug_description()}")
        print(f"[DEBUG] 策略功能: {'啟用' if is_strategy_enabled() else '禁用'}")
        print(f"[DEBUG] 策略面板: {'啟用' if is_strategy_panel_enabled() else '禁用'}")
        print(f"[DEBUG] 策略控制: {'啟用' if is_strategy_controls_enabled() else '禁用'}")
        print(f"[DEBUG] 價格顯示: {'啟用' if is_price_display_enabled() else '禁用'}")
        print(f"[DEBUG] API集成: {'啟用' if is_api_integration_enabled() else '禁用'}")
        print(f"[DEBUG] 完整功能: {'啟用' if is_full_strategy_enabled() else '禁用'}")

# 調試級別升級函數
def upgrade_debug_level():
    """升級調試級別"""
    global CURRENT_DEBUG_LEVEL
    if CURRENT_DEBUG_LEVEL < 6:
        CURRENT_DEBUG_LEVEL += 1
        print(f"[DEBUG] 調試級別已升級到: {CURRENT_DEBUG_LEVEL} - {get_debug_description()}")
        return True
    else:
        print(f"[DEBUG] 已達到最高調試級別: {CURRENT_DEBUG_LEVEL}")
        return False

def downgrade_debug_level():
    """降級調試級別"""
    global CURRENT_DEBUG_LEVEL
    if CURRENT_DEBUG_LEVEL > 0:
        CURRENT_DEBUG_LEVEL -= 1
        print(f"[DEBUG] 調試級別已降級到: {CURRENT_DEBUG_LEVEL} - {get_debug_description()}")
        return True
    else:
        print(f"[DEBUG] 已達到最低調試級別: {CURRENT_DEBUG_LEVEL}")
        return False

def set_debug_level(level):
    """設定特定的調試級別"""
    global CURRENT_DEBUG_LEVEL
    if 0 <= level <= 6:
        CURRENT_DEBUG_LEVEL = level
        print(f"[DEBUG] 調試級別已設定為: {CURRENT_DEBUG_LEVEL} - {get_debug_description()}")
        return True
    else:
        print(f"[DEBUG] 無效的調試級別: {level}，有效範圍: 0-6")
        return False

# 初始化時顯示狀態
if __name__ == "__main__":
    print("=== 策略調試配置 ===")
    log_debug_status()
    print("===================")
else:
    # 被導入時也顯示狀態
    if ENABLE_DETAILED_LOGGING:
        log_debug_status()
