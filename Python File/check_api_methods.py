#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查可用的API方法
"""

import os
import sys
import comtypes.client
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_skcom_methods():
    """檢查SKCOM可用的方法"""
    try:
        logger.info("🔄 初始化SKCOM API...")
        
        # 生成COM元件的Python包裝
        comtypes.client.GetModule(r'.\SKCOM.dll')
        
        # 導入生成的SKCOMLib
        import comtypes.gen.SKCOMLib as sk
        logger.info("✅ SKCOMLib 導入成功")
        
        # 建立物件
        logger.info("🔄 建立SKOrderLib物件...")
        m_pSKOrder = comtypes.client.CreateObject(sk.SKOrderLib, interface=sk.ISKOrderLib)
        logger.info("✅ SKOrderLib建立成功")
        
        # 檢查可用方法
        logger.info("🔍 檢查SKOrderLib可用方法...")
        methods = [attr for attr in dir(m_pSKOrder) if not attr.startswith('_')]
        
        # 過濾期貨相關方法
        future_methods = [method for method in methods if 'future' in method.lower() or 'order' in method.lower()]
        
        logger.info("📋 期貨/下單相關方法:")
        for method in sorted(future_methods):
            logger.info(f"   - {method}")
        
        # 檢查初始化方法
        init_methods = [method for method in methods if 'init' in method.lower()]
        logger.info("📋 初始化相關方法:")
        for method in sorted(init_methods):
            logger.info(f"   - {method}")
        
        # 檢查SKCOMLib中的結構
        logger.info("🔍 檢查SKCOMLib可用結構...")
        sk_attrs = [attr for attr in dir(sk) if not attr.startswith('_')]
        
        # 過濾期貨相關結構
        future_structs = [attr for attr in sk_attrs if 'future' in attr.lower() or 'order' in attr.lower()]
        logger.info("📋 期貨/下單相關結構:")
        for struct in sorted(future_structs):
            logger.info(f"   - {struct}")
        
        # 嘗試建立FUTUREORDER物件
        logger.info("🧪 測試建立FUTUREORDER物件...")
        try:
            if hasattr(sk, 'FUTUREORDER'):
                oOrder = sk.FUTUREORDER()
                logger.info("✅ FUTUREORDER物件建立成功")
                
                # 檢查FUTUREORDER的屬性
                order_attrs = [attr for attr in dir(oOrder) if not attr.startswith('_')]
                logger.info("📋 FUTUREORDER可用屬性:")
                for attr in sorted(order_attrs):
                    logger.info(f"   - {attr}")
            else:
                logger.warning("⚠️ 找不到FUTUREORDER結構")
                
                # 尋找其他可能的期貨下單結構
                possible_structs = [attr for attr in sk_attrs if 'order' in attr.lower()]
                logger.info("📋 可能的下單結構:")
                for struct in sorted(possible_structs):
                    logger.info(f"   - {struct}")
                    
        except Exception as e:
            logger.error(f"❌ 建立FUTUREORDER失敗: {e}")
        
        # 測試初始化方法
        logger.info("🧪 測試初始化方法...")
        for method in init_methods:
            try:
                if hasattr(m_pSKOrder, method):
                    logger.info(f"✅ 找到方法: {method}")
                else:
                    logger.warning(f"⚠️ 方法不存在: {method}")
            except Exception as e:
                logger.error(f"❌ 檢查方法 {method} 失敗: {e}")
        
        # 測試下單方法
        logger.info("🧪 測試下單方法...")
        possible_order_methods = [
            'SendFutureOrder',
            'SendFutureOrderCLR',
            'SendOrder',
            'SendOrderCLR'
        ]
        
        for method in possible_order_methods:
            try:
                if hasattr(m_pSKOrder, method):
                    logger.info(f"✅ 找到下單方法: {method}")
                else:
                    logger.warning(f"⚠️ 下單方法不存在: {method}")
            except Exception as e:
                logger.error(f"❌ 檢查下單方法 {method} 失敗: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 檢查API方法失敗: {e}")
        return False

def main():
    """主函式"""
    logger.info("🔍 SKCOM API方法檢查工具")
    logger.info("=" * 50)
    
    # 檢查SKCOM.dll
    if not os.path.exists('SKCOM.dll'):
        logger.error("❌ 找不到SKCOM.dll檔案")
        return
    
    # 檢查API方法
    if check_skcom_methods():
        logger.info("✅ API方法檢查完成")
    else:
        logger.error("❌ API方法檢查失敗")
    
    logger.info("=" * 50)

if __name__ == "__main__":
    main()
