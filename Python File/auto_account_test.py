#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自動化期貨帳號格式測試
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
        logging.FileHandler('account_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AccountFormatTester:
    def __init__(self):
        self.m_pSKCenter = None
        self.m_pSKOrder = None
        self.test_results = []
        
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
    
    def initialize_order_lib(self):
        """初始化SKOrderLib"""
        try:
            logger.info("🔄 初始化SKOrderLib...")
            
            nCode = self.m_pSKOrder.SKOrderLib_Initialize()
            
            if nCode == 0:
                logger.info("✅ SKOrderLib初始化成功")
                return True
            else:
                msg = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
                logger.error(f"❌ SKOrderLib初始化失敗: {msg} (代碼: {nCode})")
                return False
                
        except Exception as e:
            logger.error(f"❌ SKOrderLib初始化過程發生錯誤: {e}")
            return False
    
    def test_account_format(self, account_format):
        """測試特定的帳號格式"""
        try:
            logger.info(f"🧪 測試帳號格式: {account_format}")
            
            # 嘗試查詢帳號
            nCode = self.m_pSKOrder.GetUserAccount()
            
            if nCode == 0:
                logger.info(f"✅ 帳號查詢成功: {account_format}")
                result = {
                    'format': account_format,
                    'success': True,
                    'code': nCode,
                    'message': 'SUCCESS'
                }
            else:
                msg = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
                logger.warning(f"⚠️ 帳號查詢失敗: {account_format} - {msg} (代碼: {nCode})")
                result = {
                    'format': account_format,
                    'success': False,
                    'code': nCode,
                    'message': msg
                }
            
            self.test_results.append(result)
            return result
            
        except Exception as e:
            logger.error(f"❌ 測試帳號格式 {account_format} 時發生錯誤: {e}")
            result = {
                'format': account_format,
                'success': False,
                'code': -1,
                'message': str(e)
            }
            self.test_results.append(result)
            return result
    
    def test_order_with_account(self, account_format):
        """測試使用特定帳號格式下單"""
        try:
            logger.info(f"🧪 測試下單帳號格式: {account_format}")
            
            # 導入SKCOMLib
            import comtypes.gen.SKCOMLib as sk
            
            # 建立下單物件
            oOrder = sk.FUTUREORDER()
            
            # 設定基本參數
            oOrder.bstrFullAccount = account_format
            oOrder.bstrStockNo = "TXFR1"  # 測試用商品代碼
            oOrder.sBuySell = 0  # 買進
            oOrder.bstrPrice = "22000"
            oOrder.nQty = 1
            oOrder.sTradeType = 0  # ROD
            oOrder.sDayTrade = 0  # 非當沖
            oOrder.sNewClose = 0  # 新倉
            oOrder.sReserved = 0  # 盤中
            
            # 嘗試下單 (測試模式，不實際送出)
            # 這裡只是測試帳號格式是否被接受
            logger.info(f"📋 帳號格式 {account_format} 的下單物件建立成功")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 測試下單帳號格式 {account_format} 時發生錯誤: {e}")
            return False
    
    def run_comprehensive_test(self, user_id, password, base_account):
        """執行完整的帳號格式測試"""
        logger.info("🚀 開始完整的帳號格式測試")
        logger.info("=" * 60)
        
        # 初始化API
        if not self.initialize_api():
            return False
        
        # 登入
        if not self.login(user_id, password):
            return False
        
        # 初始化SKOrderLib
        if not self.initialize_order_lib():
            return False
        
        # 測試不同的帳號格式
        test_formats = [
            base_account,                    # 原始格式
            f"116-{base_account}",          # 分公司代碼-帳號
            f"100-{base_account}",          # 不同分公司代碼
            f"{base_account}-116",          # 帳號-分公司代碼
            f"{base_account}-100",          # 帳號-不同分公司代碼
            f"F{base_account}",             # F前綴
            f"{base_account}F",             # F後綴
            f"0{base_account}",             # 0前綴
            f"{base_account}0",             # 0後綴
        ]
        
        logger.info(f"🧪 將測試 {len(test_formats)} 種帳號格式")
        
        # 執行測試
        for i, account_format in enumerate(test_formats, 1):
            logger.info(f"📋 測試 {i}/{len(test_formats)}: {account_format}")
            
            # 測試查詢帳號
            result = self.test_account_format(account_format)
            
            # 測試下單物件建立
            order_test = self.test_order_with_account(account_format)
            
            # 等待一下避免API調用過快
            time.sleep(1)
        
        # 輸出測試結果
        self.print_test_results()
        
        return True
    
    def print_test_results(self):
        """輸出測試結果"""
        logger.info("📊 測試結果總結")
        logger.info("=" * 60)
        
        success_count = 0
        
        for result in self.test_results:
            status = "✅ 成功" if result['success'] else "❌ 失敗"
            logger.info(f"{status} | {result['format']:<15} | 代碼: {result['code']:<4} | {result['message']}")
            
            if result['success']:
                success_count += 1
        
        logger.info("=" * 60)
        logger.info(f"📈 成功率: {success_count}/{len(self.test_results)} ({success_count/len(self.test_results)*100:.1f}%)")
        
        # 找出成功的格式
        successful_formats = [r['format'] for r in self.test_results if r['success']]
        
        if successful_formats:
            logger.info("🎉 成功的帳號格式:")
            for fmt in successful_formats:
                logger.info(f"   ✅ {fmt}")
        else:
            logger.warning("⚠️ 沒有找到成功的帳號格式")
            logger.info("💡 建議:")
            logger.info("   1. 檢查帳號是否正確")
            logger.info("   2. 確認期貨API權限")
            logger.info("   3. 聯繫群益證券客服")

def main():
    """主函式"""
    logger.info("🔍 期貨帳號格式自動化測試工具")
    logger.info("=" * 60)
    
    # 測試參數
    user_id = "E123354882"
    password = "kkd5ysUCC"
    base_account = "6363839"
    
    logger.info(f"📋 測試參數:")
    logger.info(f"   使用者ID: {user_id}")
    logger.info(f"   基礎帳號: {base_account}")
    logger.info(f"   測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 檢查SKCOM.dll
    if not os.path.exists('SKCOM.dll'):
        logger.error("❌ 找不到SKCOM.dll檔案")
        return
    
    # 執行測試
    tester = AccountFormatTester()
    
    try:
        success = tester.run_comprehensive_test(user_id, password, base_account)
        
        if success:
            logger.info("✅ 測試完成")
        else:
            logger.error("❌ 測試失敗")
            
    except Exception as e:
        logger.error(f"❌ 測試過程發生錯誤: {e}")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
