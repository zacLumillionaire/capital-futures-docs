#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SKCOM API管理器 - 基於群益官方案例程式的穩定實現
專門用於歷史資料收集，整合登入、報價連線、事件處理等功能
"""

import os
import sys
import logging
import comtypes.client
from datetime import datetime

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from history_config import SKCOM_DLL_PATH, DEFAULT_USER_ID, DEFAULT_PASSWORD

logger = logging.getLogger(__name__)

class SKCOMManager:
    """SKCOM API管理器 - 基於群益官方案例程式"""

    def __init__(self):
        # SKCOM物件 - 基於官方案例程式的宣告方式
        self.sk = None
        self.m_pSKCenter = None
        self.m_pSKOrder = None
        self.m_pSKQuote = None
        self.m_pSKReply = None

        # 連線狀態
        self.is_logged_in = False
        self.is_quote_connected = False
        self.stocks_ready = False

        # 事件處理器
        self.quote_event_handler = None
        self.reply_event_handler = None
        self.center_event_handler = None

        # 資料收集回調函數
        self.on_history_tick_received = None
        self.on_realtime_tick_received = None
        self.on_best5_received = None
        self.on_kline_received = None
        self.on_kline_complete = None

    def initialize_skcom(self):
        """初始化SKCOM API - 基於官方案例程式的方式"""
        try:
            logger.info("🔄 初始化SKCOM API...")

            # 檢查DLL檔案是否存在
            if not os.path.exists(SKCOM_DLL_PATH):
                raise FileNotFoundError(f"找不到SKCOM.dll檔案: {SKCOM_DLL_PATH}")

            # 基於官方案例程式的初始化方式
            comtypes.client.GetModule(SKCOM_DLL_PATH)
            import comtypes.gen.SKCOMLib as sk_module
            self.sk = sk_module

            logger.info("✅ SKCOM API初始化成功")
            return True

        except Exception as e:
            logger.error(f"❌ SKCOM API初始化失敗: {e}")
            return False

    def initialize_skcom_objects(self):
        """初始化SKCOM物件 - 基於官方案例程式的方式"""
        if self.sk is None:
            logger.error("❌ SKCOM API 未初始化")
            return False

        try:
            # 基於官方案例程式的物件建立方式
            logger.info("🔄 建立SKCenterLib物件...")
            self.m_pSKCenter = comtypes.client.CreateObject(
                self.sk.SKCenterLib, interface=self.sk.ISKCenterLib)

            logger.info("🔄 建立SKQuoteLib物件...")
            self.m_pSKQuote = comtypes.client.CreateObject(
                self.sk.SKQuoteLib, interface=self.sk.ISKQuoteLib)

            logger.info("🔄 建立SKReplyLib物件...")
            self.m_pSKReply = comtypes.client.CreateObject(
                self.sk.SKReplyLib, interface=self.sk.ISKReplyLib)

            logger.info("🔄 建立SKOrderLib物件...")
            self.m_pSKOrder = comtypes.client.CreateObject(
                self.sk.SKOrderLib, interface=self.sk.ISKOrderLib)

            logger.info("✅ 所有SKCOM物件建立成功")

            # 根據官方案例程式，在物件建立後立即註冊事件處理器
            logger.info("🔄 註冊事件處理器...")
            self.register_reply_events()
            self.register_center_events()

            return True

        except Exception as e:
            logger.error(f"❌ SKCOM物件建立失敗: {e}")
            return False

    def login(self, user_id=None, password=None):
        """登入群益API - 基於官方案例程式的登入方式"""
        # 使用預設登入資訊
        if not user_id:
            user_id = DEFAULT_USER_ID
        if not password:
            password = DEFAULT_PASSWORD

        if not user_id or not password:
            logger.error("❌ 請提供身分證字號和密碼")
            return False

        if not self.m_pSKCenter:
            logger.error("❌ SKCenter物件未初始化")
            return False

        try:
            logger.info(f"🔄 開始登入 - 帳號: {user_id}")

            # 執行登入 - 基於官方案例程式的方式
            nCode = self.m_pSKCenter.SKCenterLib_Login(user_id, password)

            # 取得回傳訊息
            msg_text = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
            logger.info(f"【SKCenterLib_Login】{msg_text} (代碼: {nCode})")

            if nCode == 0:  # 登入成功
                self.is_logged_in = True
                logger.info("✅ 群益證券API登入成功！")
                return True
            elif nCode == 2017:  # SK_WARNING_REGISTER_REPLYLIB_ONREPLYMESSAGE_FIRST
                logger.warning("⚠️ 收到ReplyLib註冊警告，這是正常的警告訊息")
                self.is_logged_in = True
                logger.info("✅ 群益證券API登入成功！")
                return True
            else:
                logger.error(f"❌ 登入失敗: {msg_text}")
                return False

        except Exception as e:
            logger.error(f"❌ 登入時發生錯誤: {str(e)}")
            return False

    def register_center_events(self):
        """註冊CenterLib事件處理"""
        if not self.m_pSKCenter:
            return False

        try:
            class SKCenterLibEvent:
                def __init__(self, parent):
                    self.parent = parent

                def OnTimer(self, nTime):
                    """定時Timer通知"""
                    logger.debug(f"【OnTimer】{nTime}")
                    return 0

                def OnShowAgreement(self, bstrData):
                    """同意書狀態通知"""
                    logger.info(f"【OnShowAgreement】{bstrData}")
                    return 0

            self.center_event = SKCenterLibEvent(self)
            self.center_event_handler = comtypes.client.GetEvents(self.m_pSKCenter, self.center_event)
            logger.info("✅ CenterLib事件處理註冊成功")
            return True

        except Exception as e:
            logger.error(f"❌ 註冊CenterLib事件失敗: {str(e)}")
            return False

    def register_reply_events(self):
        """註冊ReplyLib事件處理"""
        if not self.m_pSKReply:
            return False

        try:
            class SKReplyLibEvent:
                def __init__(self, parent):
                    self.parent = parent

                def OnReplyMessage(self, bstrUserID, bstrMessages):
                    """回報訊息事件"""
                    logger.info(f"【OnReplyMessage】{bstrUserID}_{bstrMessages}")
                    return -1

            self.reply_event = SKReplyLibEvent(self)
            self.reply_event_handler = comtypes.client.GetEvents(self.m_pSKReply, self.reply_event)
            logger.info("✅ ReplyLib事件處理註冊成功")
            return True

        except Exception as e:
            logger.error(f"❌ 註冊ReplyLib事件失敗: {str(e)}")
            return False

    def connect_quote_server(self):
        """連線報價主機 - 基於官方案例程式的方式"""
        if not self.m_pSKQuote:
            logger.error("❌ SKQuote物件未初始化")
            return False

        try:
            logger.info("🔄 開始連線報價主機...")

            # 重置連線狀態
            self.is_quote_connected = False
            self.stocks_ready = False

            # 註冊報價事件
            if not self.register_quote_events():
                logger.error("❌ 註冊報價事件失敗")
                return False

            # 調用API連線報價主機 - 基於官方案例程式
            nCode = self.m_pSKQuote.SKQuoteLib_EnterMonitorLONG()

            if self.m_pSKCenter:
                msg_text = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
            else:
                msg_text = f"結果代碼: {nCode}"

            logger.info(f"【API調用】SKQuoteLib_EnterMonitorLONG() - {msg_text} (代碼: {nCode})")

            if nCode == 0:
                logger.info("✅ 連線請求已送出，等待連線完成...")
                return True
            else:
                logger.error(f"❌ 連線報價主機失敗: {msg_text}")
                return False

        except Exception as e:
            logger.error(f"❌ 連線報價主機時發生錯誤: {str(e)}")
            return False

    def register_quote_events(self):
        """註冊報價事件處理 - 基於官方案例程式"""
        if not self.m_pSKQuote:
            logger.error("❌ SKQuote物件未初始化，無法註冊事件")
            return False

        try:
            logger.info("🔄 開始註冊報價事件處理...")

            # 建立事件處理類別 - 基於官方案例程式
            class SKQuoteLibEvent:
                def __init__(self, parent):
                    self.parent = parent

                def OnConnection(self, nKind, nCode):
                    """連線狀態事件 - 根據官方案例實現"""
                    if nKind == 3001:
                        msg = "【連線狀態】Connected! 已連線到報價主機"
                        self.parent.is_quote_connected = True
                    elif nKind == 3002:
                        msg = "【連線狀態】DisConnected! 已斷線"
                        self.parent.is_quote_connected = False
                        self.parent.stocks_ready = False
                    elif nKind == 3003:
                        msg = "【連線狀態】Stocks ready! 商品資料已準備完成"
                        self.parent.stocks_ready = True
                        self.parent.on_stocks_ready()  # 觸發商品資料準備完成事件
                    elif nKind == 3021:
                        msg = "【連線狀態】Connect Error! 連線錯誤"
                        self.parent.is_quote_connected = False
                    else:
                        msg = f"【連線狀態】Unknown Kind: {nKind}, Code: {nCode}"

                    logger.info(msg)
                    return 0

                def OnNotifyHistoryTicksLONG(self, sMarketNo, nIndex, nPtr, nDate,
                                           nTimehms, nTimemillismicros, nBid, nAsk,
                                           nClose, nQty, nSimulate):
                    """歷史逐筆資料事件"""
                    if self.parent.on_history_tick_received:
                        self.parent.on_history_tick_received(
                            sMarketNo, nIndex, nPtr, nDate, nTimehms,
                            nTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate)
                    return 0

                def OnNotifyTicksLONG(self, sMarketNo, nIndex, nPtr, nDate,
                                    nTimehms, nTimemillismicros, nBid, nAsk,
                                    nClose, nQty, nSimulate):
                    """即時逐筆資料事件"""
                    if self.parent.on_realtime_tick_received:
                        self.parent.on_realtime_tick_received(
                            sMarketNo, nIndex, nPtr, nDate, nTimehms,
                            nTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate)
                    return 0

                def OnNotifyBest5LONG(self, sMarketNo, nIndex, nBestBid1, nBestBidQty1,
                                    nBestBid2, nBestBidQty2, nBestBid3, nBestBidQty3,
                                    nBestBid4, nBestBidQty4, nBestBid5, nBestBidQty5,
                                    nExtendBid, nExtendBidQty, nBestAsk1, nBestAskQty1,
                                    nBestAsk2, nBestAskQty2, nBestAsk3, nBestAskQty3,
                                    nBestAsk4, nBestAskQty4, nBestAsk5, nBestAskQty5,
                                    nExtendAsk, nExtendAskQty, nSimulate):
                    """五檔報價事件"""
                    if self.parent.on_best5_received:
                        self.parent.on_best5_received(
                            sMarketNo, nIndex, nBestBid1, nBestBidQty1, nBestBid2, nBestBidQty2,
                            nBestBid3, nBestBidQty3, nBestBid4, nBestBidQty4, nBestBid5, nBestBidQty5,
                            nExtendBid, nExtendBidQty, nBestAsk1, nBestAskQty1, nBestAsk2, nBestAskQty2,
                            nBestAsk3, nBestAskQty3, nBestAsk4, nBestAskQty4, nBestAsk5, nBestAskQty5,
                            nExtendAsk, nExtendAskQty, nSimulate)
                    return 0

                def OnNotifyKLineData(self, bstrStockNo, bstrData):
                    """K線資料事件"""
                    if self.parent.on_kline_received:
                        self.parent.on_kline_received(bstrStockNo, bstrData)
                    return 0

                def OnKLineComplete(self, bstrEndString):
                    """K線查詢完成事件"""
                    if self.parent.on_kline_complete:
                        self.parent.on_kline_complete(bstrEndString)
                    return 0

            # 建立事件處理器
            self.quote_event = SKQuoteLibEvent(self)

            # 註冊事件
            self.quote_event_handler = comtypes.client.GetEvents(self.m_pSKQuote, self.quote_event)
            logger.info("✅ 報價事件處理註冊成功")
            return True

        except Exception as e:
            logger.error(f"❌ 註冊報價事件失敗: {str(e)}")
            return False

    def on_stocks_ready(self):
        """商品資料準備完成事件處理"""
        logger.info("✅ 商品資料已下載完成，可以開始查詢歷史資料")

    def request_history_ticks(self, symbol, page_no=0):
        """請求歷史逐筆資料"""
        if not self.stocks_ready:
            logger.error("❌ 商品資料未準備完成，無法請求歷史資料")
            return False

        try:
            logger.info(f"🔄 請求 {symbol} 歷史逐筆資料 (頁數: {page_no})...")

            # 調用API請求逐筆資料
            nCode = self.m_pSKQuote.SKQuoteLib_RequestTicks(page_no, symbol)

            if self.m_pSKCenter:
                msg_text = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
            else:
                msg_text = f"結果代碼: {nCode}"

            logger.info(f"【API調用】SKQuoteLib_RequestTicks({page_no}, {symbol}) - {msg_text} (代碼: {nCode})")

            if nCode == 0:
                logger.info("✅ 歷史逐筆資料請求已送出，等待資料回傳...")
                return True
            else:
                logger.error(f"❌ 請求歷史逐筆資料失敗: {msg_text}")
                return False

        except Exception as e:
            logger.error(f"❌ 請求歷史逐筆資料時發生錯誤: {str(e)}")
            return False

    def request_kline_data(self, symbol, kline_type=0, start_date='20240101',
                          end_date='20241231', trading_session=0, minute_number=1):
        """
        請求K線資料

        Args:
            symbol: 商品代碼
            kline_type: K線類型 (0=分線, 4=日線, 5=週線, 6=月線)
            start_date: 起始日期 (YYYYMMDD)
            end_date: 結束日期 (YYYYMMDD)
            trading_session: 交易時段 (0=全盤, 1=AM盤)
            minute_number: 分鐘數（當kline_type=0時有效）
        """
        if not self.stocks_ready:
            logger.error("❌ 商品資料未準備完成，無法請求K線資料")
            return False

        try:
            logger.info(f"🔄 請求 {symbol} K線資料...")
            logger.info(f"📊 參數: K線類型={kline_type}, {start_date}~{end_date}, 交易時段={trading_session}")

            # 調用API請求K線資料 - 基於官方案例程式
            nCode = self.m_pSKQuote.SKQuoteLib_RequestKLineAMByDate(
                symbol, kline_type, 1, trading_session,  # sOutType=1 新版格式
                start_date, end_date, minute_number)

            if self.m_pSKCenter:
                msg_text = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
            else:
                msg_text = f"結果代碼: {nCode}"

            logger.info(f"【API調用】SKQuoteLib_RequestKLineAMByDate() - {msg_text} (代碼: {nCode})")

            if nCode == 0:
                logger.info("✅ K線資料請求已送出，等待資料回傳...")
                return True
            else:
                logger.error(f"❌ 請求K線資料失敗: {msg_text}")
                return False

        except Exception as e:
            logger.error(f"❌ 請求K線資料時發生錯誤: {str(e)}")
            return False

    def get_api_version(self):
        """取得API版本資訊"""
        try:
            if self.m_pSKCenter:
                version_info = self.m_pSKCenter.SKCenterLib_GetSKAPIVersionAndBit()
                logger.info(f"📋 API版本資訊: {version_info}")
                return version_info
            return None
        except Exception as e:
            logger.error(f"❌ 取得API版本失敗: {str(e)}")
            return None

    def logout(self):
        """登出API"""
        try:
            if self.m_pSKCenter and self.is_logged_in:
                # 根據群益API文件，登出不需要參數
                nCode = self.m_pSKCenter.SKCenterLib_Logout()

                # 取得回傳訊息
                msg_text = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
                logger.info(f"【SKCenterLib_Logout】{msg_text} (代碼: {nCode})")

                if nCode == 0:
                    self.is_logged_in = False
                    logger.info("✅ 登出成功")
                else:
                    logger.warning(f"⚠️ 登出回傳代碼: {nCode}, 但繼續處理")
                    self.is_logged_in = False

                return True
            else:
                logger.info("ℹ️ 未登入或SKCenter物件不存在，無需登出")
                return True
        except Exception as e:
            logger.error(f"❌ 登出時發生錯誤: {str(e)}")
            # 即使登出失敗，也設定為未登入狀態
            self.is_logged_in = False
            return False

    def cleanup(self):
        """清理資源"""
        try:
            # 登出
            if self.is_logged_in:
                self.logout()

            # 清理事件處理器
            if self.quote_event_handler:
                self.quote_event_handler = None
            if self.reply_event_handler:
                self.reply_event_handler = None
            if self.center_event_handler:
                self.center_event_handler = None

            # 清理物件
            self.m_pSKCenter = None
            self.m_pSKQuote = None
            self.m_pSKReply = None
            self.m_pSKOrder = None

            logger.info("✅ 資源清理完成")

        except Exception as e:
            logger.error(f"❌ 清理資源時發生錯誤: {str(e)}")

    def is_ready_for_data_collection(self):
        """檢查是否準備好進行資料收集"""
        return (self.is_logged_in and
                self.is_quote_connected and
                self.stocks_ready and
                self.m_pSKQuote is not None)
