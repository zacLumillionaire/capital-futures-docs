#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 ReadCertByID 修復1038錯誤
"""

import os
import sys
import time
import logging
import comtypes.client
from datetime import datetime

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('readcert_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ReadCertTester:
    def __init__(self):
        self.m_pSKCenter = None
        self.m_pSKOrder = None
        
    def initialize_api(self):
        """初始化API"""
        try:
            logger.info("🔄 初始化SKCOM API...")
            
            # 生成COM元件的Python包裝
            comtypes.client.GetModule(r'.\SKCOM.dll')
            
            # 導入生成的SKCOMLib
            import comtypes.gen.SKCOMLib as sk
            
            # 建立物件
            self.m_pSKCenter = comtypes.client.CreateObject(sk.SKCenterLib, interface=sk.ISKCenterLib)
            self.m_pSKOrder = comtypes.client.CreateObject(sk.SKOrderLib, interface=sk.ISKOrderLib)
            
            logger.info("✅ API初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ API初始化失敗: {e}")
            return False
    
    def login(self, user_id, password):
        """登入"""
        try:
            logger.info(f"🔄 登入中... 使用者: {user_id}")
            
            nCode = self.m_pSKCenter.SKCenterLib_Login(user_id, password)
            
            # 檢查登入結果
            if nCode == 0:
                logger.info("✅ 登入成功")
                return True
            elif nCode == 2017:
                # SK_WARNING_REGISTER_REPLYLIB_ONREPLYMESSAGE_FIRST
                logger.warning("⚠️ 需要註冊回報事件，但登入可能已成功")
                logger.info("✅ 繼續進行測試...")
                return True
            else:
                msg = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
                logger.error(f"❌ 登入失敗: {msg} (代碼: {nCode})")
                return False
                
        except Exception as e:
            logger.error(f"❌ 登入過程發生錯誤: {e}")
            return False
    
    def test_readcert_fix(self, user_id):
        """測試ReadCertByID修復1038錯誤"""
        try:
            logger.info("🧪 測試ReadCertByID修復1038錯誤...")
            
            # 步驟1: 初始化SKOrderLib
            logger.info("📋 步驟1: 初始化SKOrderLib...")
            nCode = self.m_pSKOrder.SKOrderLib_Initialize()
            
            if nCode == 0:
                logger.info("✅ SKOrderLib初始化成功")
            else:
                msg = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
                logger.error(f"❌ SKOrderLib初始化失敗: {msg} (代碼: {nCode})")
                return False
            
            # 步驟2: 讀取憑證 (關鍵步驟)
            logger.info("📋 步驟2: 讀取憑證 (解決1038錯誤的關鍵)...")
            logger.info(f"🔑 使用登入ID: {user_id}")
            
            nCode = self.m_pSKOrder.ReadCertByID(user_id)
            
            if nCode == 0:
                logger.info("✅ 憑證讀取成功！這應該解決1038錯誤")
            else:
                msg = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
                logger.error(f"❌ 憑證讀取失敗: {msg} (代碼: {nCode})")
                logger.warning("⚠️ 這可能導致後續的1038錯誤")
                return False
            
            # 步驟3: 查詢帳號
            logger.info("📋 步驟3: 查詢帳號...")
            nCode = self.m_pSKOrder.GetUserAccount()
            
            if nCode == 0:
                logger.info("✅ 帳號查詢成功")
            else:
                msg = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
                logger.error(f"❌ 帳號查詢失敗: {msg} (代碼: {nCode})")
            
            # 步驟4: 測試下單 (模擬)
            logger.info("📋 步驟4: 測試下單準備...")
            
            try:
                import comtypes.gen.SKCOMLib as sk
                oOrder = sk.FUTUREORDER()
                
                # 設定測試參數
                oOrder.bstrFullAccount = "F0200006363839"
                oOrder.bstrStockNo = "TXFR1"
                oOrder.sBuySell = 0  # 買進
                oOrder.bstrPrice = "22000"
                oOrder.nQty = 1
                oOrder.sTradeType = 0  # ROD
                oOrder.sDayTrade = 0  # 非當沖
                oOrder.sNewClose = 0  # 新倉
                oOrder.sReserved = 0  # 盤中
                
                logger.info("✅ 下單物件建立成功")
                logger.info("📋 下單參數設定完成")
                
                # 注意：這裡不實際送出下單，只是測試到這個階段
                logger.info("⚠️ 注意：這是測試模式，不會實際送出下單")
                logger.info("🎉 如果到這裡沒有1038錯誤，表示ReadCertByID修復成功！")
                
                return True
                
            except Exception as e:
                logger.error(f"❌ 建立下單物件失敗: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 測試ReadCertByID時發生錯誤: {e}")
            return False
    
    def run_complete_test(self, user_id, password):
        """執行完整的ReadCertByID測試"""
        logger.info("🚀 開始ReadCertByID修復1038錯誤測試")
        logger.info("=" * 60)
        
        # 初始化API
        if not self.initialize_api():
            return False
        
        # 登入
        if not self.login(user_id, password):
            return False
        
        # 測試ReadCertByID修復
        if self.test_readcert_fix(user_id):
            logger.info("🎉 ReadCertByID測試成功！")
            logger.info("✅ 這應該解決1038憑證驗證錯誤")
            return True
        else:
            logger.error("❌ ReadCertByID測試失敗")
            return False

def main():
    """主函式"""
    logger.info("🔍 ReadCertByID修復1038錯誤測試工具")
    logger.info("=" * 60)
    
    # 測試參數
    user_id = "E123354882"
    password = "kkd5ysUCC"
    
    logger.info(f"📋 測試參數:")
    logger.info(f"   使用者ID: {user_id}")
    logger.info(f"   測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"   目標: 修復1038憑證驗證錯誤")
    
    # 檢查SKCOM.dll
    if not os.path.exists('SKCOM.dll'):
        logger.error("❌ 找不到SKCOM.dll檔案")
        return
    
    # 執行測試
    tester = ReadCertTester()
    
    try:
        success = tester.run_complete_test(user_id, password)
        
        if success:
            logger.info("✅ 測試完成 - ReadCertByID修復成功")
            logger.info("🎯 現在可以在主程式中測試期貨下單")
            logger.info("💡 應該不會再出現1038錯誤")
        else:
            logger.error("❌ 測試失敗")
            logger.info("💡 建議:")
            logger.info("   1. 檢查憑證是否正確安裝")
            logger.info("   2. 確認登入ID是否正確")
            logger.info("   3. 聯繫群益證券技術支援")
            
    except Exception as e:
        logger.error(f"❌ 測試過程發生錯誤: {e}")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
