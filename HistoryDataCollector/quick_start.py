#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速開始腳本 - 一鍵收集期貨資料並匯入PostgreSQL
適合日常使用的簡化版本
"""

import sys
import os
from datetime import datetime, timedelta

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from collect_and_import import CollectAndImportTool

def quick_collect_today():
    """快速收集今日MTX00 1分K線資料並匯入PostgreSQL"""
    
    # 設定參數
    USER_ID = "E123354882"
    PASSWORD = "kkd5ysUCC"
    SYMBOL = "MTX00"
    KLINE_TYPE = "MINUTE"
    
    # 今日日期
    today = datetime.now().strftime("%Y%m%d")
    
    print("🚀 快速收集今日期貨資料並匯入PostgreSQL")
    print("=" * 50)
    print(f"📊 商品代碼: {SYMBOL}")
    print(f"📈 K線類型: {KLINE_TYPE}")
    print(f"📅 收集日期: {today}")
    print(f"🔄 自動匯入: 是")
    print("=" * 50)
    
    # 確認執行
    confirm = input("確定要開始收集嗎？(y/N): ")
    if confirm.lower() != 'y':
        print("❌ 已取消")
        return
    
    # 建立工具並執行
    tool = CollectAndImportTool()
    
    success = tool.run(
        user_id=USER_ID,
        password=PASSWORD,
        symbol=SYMBOL,
        kline_type=KLINE_TYPE,
        start_date=today,
        end_date=today,
        trading_session='DAY',
        auto_import=True
    )
    
    if success:
        print("\n🎉 收集和匯入完成！")
        print("💡 您可以在PostgreSQL的stock_prices表中查看資料")
    else:
        print("\n❌ 收集或匯入失敗，請檢查日誌")

def quick_collect_recent_days(days=3):
    """快速收集最近幾天的MTX00 1分K線資料"""
    
    # 設定參數
    USER_ID = "E123354882"
    PASSWORD = "kkd5ysUCC"
    SYMBOL = "MTX00"
    KLINE_TYPE = "MINUTE"
    
    # 計算日期範圍
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    start_date_str = start_date.strftime("%Y%m%d")
    end_date_str = end_date.strftime("%Y%m%d")
    
    print(f"🚀 快速收集最近{days}天期貨資料並匯入PostgreSQL")
    print("=" * 50)
    print(f"📊 商品代碼: {SYMBOL}")
    print(f"📈 K線類型: {KLINE_TYPE}")
    print(f"📅 日期範圍: {start_date_str} ~ {end_date_str}")
    print(f"🔄 自動匯入: 是")
    print("=" * 50)
    
    # 確認執行
    confirm = input("確定要開始收集嗎？(y/N): ")
    if confirm.lower() != 'y':
        print("❌ 已取消")
        return
    
    # 建立工具並執行
    tool = CollectAndImportTool()
    
    success = tool.run(
        user_id=USER_ID,
        password=PASSWORD,
        symbol=SYMBOL,
        kline_type=KLINE_TYPE,
        start_date=start_date_str,
        end_date=end_date_str,
        trading_session='DAY',
        auto_import=True
    )
    
    if success:
        print(f"\n🎉 最近{days}天的資料收集和匯入完成！")
        print("💡 您可以在PostgreSQL的stock_prices表中查看資料")
    else:
        print("\n❌ 收集或匯入失敗，請檢查日誌")

def main():
    """主選單"""
    print("📈 期貨資料收集快速工具")
    print("=" * 30)
    print("1. 收集今日資料")
    print("2. 收集最近3天資料")
    print("3. 收集最近7天資料")
    print("4. 退出")
    print("=" * 30)
    
    choice = input("請選擇 (1-4): ")
    
    if choice == '1':
        quick_collect_today()
    elif choice == '2':
        quick_collect_recent_days(3)
    elif choice == '3':
        quick_collect_recent_days(7)
    elif choice == '4':
        print("👋 再見！")
    else:
        print("❌ 無效選擇")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 使用者中斷")
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
