# 群益期貨歷史資料收集器開發說明

## 📋 專案概述

**專案名稱**：HistoryDataCollector
**目標**：開發專門用來取得台灣小台指期貨（MTX00）歷史資料並建立到資料庫的程式
**策略**：直接採用 OrderTester.py 已驗證的登入機制和API元件，降低開發風險和時間成本

### 🎯 核心功能
- 取得MTX00歷史逐筆報價資料
- 取得MTX00歷史五檔報價資料
- 取得MTX00歷史K線資料（1分K、日K、週K、月K）
- 資料儲存到SQLite資料庫
- 支援指定日期區間查詢
- 資料去重和完整性驗證

---

## 🏗️ 階段一：建立新資料夾與基礎架構

### 1.1 專案目錄結構

```
/my-capital-project/HistoryDataCollector/
├── main.py                    # 主程式入口
├── config.py                  # 配置檔案
├── requirements.txt           # Python依賴套件
├── README.md                  # 專案說明
├── SKCOM.dll                  # 群益API元件（從OrderTester目錄複製）
├── SKCOMTester.exe           # 群益測試工具（從OrderTester目錄複製）
├── database/                  # 資料庫模組
│   ├── __init__.py
│   ├── db_manager.py         # 資料庫管理器
│   ├── models.py             # 資料模型定義
│   └── schema.sql            # 資料庫結構定義
├── collectors/               # 資料收集器模組
│   ├── __init__.py
│   ├── base_collector.py     # 基礎收集器類別
│   ├── tick_collector.py     # 逐筆資料收集器
│   ├── best5_collector.py    # 五檔資料收集器
│   └── kline_collector.py    # K線資料收集器
├── utils/                    # 工具模組
│   ├── __init__.py
│   ├── skcom_manager.py      # SKCOM API管理器
│   ├── date_utils.py         # 日期工具
│   └── logger.py             # 日誌工具
├── data/                     # 資料儲存目錄
│   └── history_data.db       # SQLite資料庫檔案
└── logs/                     # 日誌檔案目錄
    └── collector.log
```

### 1.2 建立基礎檔案

#### config.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
歷史資料收集器配置檔案
"""

import os

# 基礎配置
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")

# 資料庫配置
DATABASE_PATH = os.path.join(DATA_DIR, "history_data.db")

# 群益API配置
SKCOM_DLL_PATH = os.path.join(PROJECT_ROOT, "SKCOM.dll")

# 商品配置
MTX_SYMBOL = "MTX00"           # 小台指代碼
MTX_AM_SYMBOL = "MTX00AM"      # 小台指日盤代碼

# 資料收集配置
DEFAULT_DATE_RANGE = 30        # 預設查詢30天
BATCH_SIZE = 1000             # 批量插入大小
MAX_RETRY_COUNT = 3           # 最大重試次數
RETRY_DELAY = 5               # 重試延遲秒數

# K線類型配置
KLINE_TYPES = {
    'MINUTE': 0,              # 分線
    'DAILY': 4,               # 日線
    'WEEKLY': 5,              # 週線
    'MONTHLY': 6              # 月線
}

# 交易時段配置
TRADING_SESSIONS = {
    'ALL': 0,                 # 全盤（包含夜盤）
    'AM_ONLY': 1              # 僅日盤
}

# 日誌配置
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = os.path.join(LOGS_DIR, "collector.log")
```

---

## 🔐 階段二：複製並改造登入機制

### 2.1 SKCOM API管理器

#### utils/skcom_manager.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SKCOM API管理器 - 基於OrderTester.py的穩定實現
"""

import os
import sys
import logging
import comtypes.client
from config import SKCOM_DLL_PATH

logger = logging.getLogger(__name__)

class SKCOMManager:
    """SKCOM API管理器"""

    def __init__(self):
        # SKCOM物件
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

    def initialize_skcom(self):
        """初始化SKCOM API - 複製自OrderTester.py"""
        try:
            logger.info("🔄 初始化SKCOM API...")

            # 檢查DLL檔案是否存在
            if not os.path.exists(SKCOM_DLL_PATH):
                raise FileNotFoundError(f"找不到SKCOM.dll檔案: {SKCOM_DLL_PATH}")

            # 生成COM元件的Python包裝
            comtypes.client.GetModule(SKCOM_DLL_PATH)

            # 導入生成的SKCOMLib
            import comtypes.gen.SKCOMLib as sk_module
            self.sk = sk_module

            logger.info("✅ SKCOM API初始化成功")
            return True

        except Exception as e:
            logger.error(f"❌ SKCOM API初始化失敗: {e}")
            return False

    def initialize_skcom_objects(self):
        """初始化SKCOM物件 - 複製自OrderTester.py"""
        if self.sk is None:
            logger.error("❌ SKCOM API 未初始化")
            return False

        try:
            # 建立物件
            logger.info("🔄 建立SKCenterLib物件...")
            self.m_pSKCenter = comtypes.client.CreateObject(
                self.sk.SKCenterLib, interface=self.sk.ISKCenterLib)

            logger.info("🔄 建立SKQuoteLib物件...")
            self.m_pSKQuote = comtypes.client.CreateObject(
                self.sk.SKQuoteLib, interface=self.sk.ISKQuoteLib)

            logger.info("🔄 建立SKReplyLib物件...")
            self.m_pSKReply = comtypes.client.CreateObject(
                self.sk.SKReplyLib, interface=self.sk.ISKReplyLib)

            logger.info("✅ 所有SKCOM物件建立成功")
            return True

        except Exception as e:
            logger.error(f"❌ SKCOM物件建立失敗: {e}")
            return False

    def login(self, user_id, password):
        """登入群益API - 複製自OrderTester.py"""
        if not user_id or not password:
            logger.error("❌ 請提供身分證字號和密碼")
            return False

        if not self.m_pSKCenter:
            logger.error("❌ SKCenter物件未初始化")
            return False

        try:
            logger.info(f"🔄 開始登入 - 帳號: {user_id}")

            # 執行登入
            nCode = self.m_pSKCenter.SKCenterLib_Login(user_id, password)

            # 取得回傳訊息
            msg_text = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
            logger.info(f"【SKCenterLib_Login】{msg_text} (代碼: {nCode})")

            if nCode == 0:  # 登入成功
                self.is_logged_in = True
                logger.info("✅ 群益證券API登入成功！")
                return True
            else:
                logger.error(f"❌ 登入失敗: {msg_text}")
                return False

        except Exception as e:
            logger.error(f"❌ 登入時發生錯誤: {str(e)}")
            return False
```

### 2.2 報價連線機制

繼續在 `utils/skcom_manager.py` 中添加報價連線功能：

```python
    def connect_quote_server(self):
        """連線報價主機 - 複製自OrderTester.py"""
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

            # 調用API連線報價主機
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
        """註冊報價事件處理 - 複製自OrderTester.py"""
        if not self.m_pSKQuote:
            logger.error("❌ SKQuote物件未初始化，無法註冊事件")
            return False

        try:
            logger.info("🔄 開始註冊報價事件處理...")

            # 建立事件處理類別
            class SKQuoteLibEvent():
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
                    self.parent.on_history_tick_received(
                        sMarketNo, nIndex, nPtr, nDate, nTimehms,
                        nTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate)
                    return 0

                def OnNotifyTicksLONG(self, sMarketNo, nIndex, nPtr, nDate,
                                    nTimehms, nTimemillismicros, nBid, nAsk,
                                    nClose, nQty, nSimulate):
                    """即時逐筆資料事件"""
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
                    self.parent.on_best5_received(
                        sMarketNo, nIndex, nBestBid1, nBestBidQty1, nBestBid2, nBestBidQty2,
                        nBestBid3, nBestBidQty3, nBestBid4, nBestBidQty4, nBestBid5, nBestBidQty5,
                        nExtendBid, nExtendBidQty, nBestAsk1, nBestAskQty1, nBestAsk2, nBestAskQty2,
                        nBestAsk3, nBestAskQty3, nBestAsk4, nBestAskQty4, nBestAsk5, nBestAskQty5,
                        nExtendAsk, nExtendAskQty, nSimulate)
                    return 0

                def OnNotifyKLineData(self, bstrStockNo, bstrData):
                    """K線資料事件"""
                    self.parent.on_kline_received(bstrStockNo, bstrData)
                    return 0

                def OnKLineComplete(self, bstrEndString):
                    """K線查詢完成事件"""
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
        # 這裡可以觸發自動開始收集歷史資料的邏輯

    # 事件回調函數（由子類別或外部註冊）
    def on_history_tick_received(self, *args):
        """歷史逐筆資料回調 - 由收集器實現"""
        pass

    def on_realtime_tick_received(self, *args):
        """即時逐筆資料回調 - 由收集器實現"""
        pass

    def on_best5_received(self, *args):
        """五檔資料回調 - 由收集器實現"""
        pass

    def on_kline_received(self, stock_no, data):
        """K線資料回調 - 由收集器實現"""
        pass

    def on_kline_complete(self, end_string):
        """K線查詢完成回調 - 由收集器實現"""
        pass

---

## 📊 階段三：開發歷史資料取得功能

### 3.1 基礎收集器類別

#### collectors/base_collector.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基礎資料收集器類別
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

class BaseCollector(ABC):
    """基礎資料收集器抽象類別"""

    def __init__(self, skcom_manager, db_manager):
        self.skcom_manager = skcom_manager
        self.db_manager = db_manager
        self.is_collecting = False
        self.collected_count = 0

    @abstractmethod
    def start_collection(self, symbol, **kwargs):
        """開始收集資料"""
        pass

    @abstractmethod
    def stop_collection(self):
        """停止收集資料"""
        pass

    def format_price(self, price_value):
        """格式化價格 - 除以100.0處理小數點"""
        if price_value is None or price_value == 0:
            return None
        return price_value / 100.0

    def format_time(self, date_value, time_value):
        """格式化時間"""
        try:
            date_str = str(date_value)
            time_str = str(time_value).zfill(6)  # 補齊6位數

            # 解析日期 YYYYMMDD
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])

            # 解析時間 HHMMSS
            hour = int(time_str[:2])
            minute = int(time_str[2:4])
            second = int(time_str[4:6])

            return datetime(year, month, day, hour, minute, second)
        except Exception as e:
            logger.error(f"時間格式化錯誤: {e}")
            return None
```

### 3.2 逐筆資料收集器

#### collectors/tick_collector.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
逐筆資料收集器 - 收集歷史和即時逐筆報價
"""

import logging
from .base_collector import BaseCollector
from config import MTX_SYMBOL, BATCH_SIZE

logger = logging.getLogger(__name__)

class TickCollector(BaseCollector):
    """逐筆資料收集器"""

    def __init__(self, skcom_manager, db_manager):
        super().__init__(skcom_manager, db_manager)
        self.tick_buffer = []  # 批量插入緩衝區

        # 註冊事件回調
        self.skcom_manager.on_history_tick_received = self.on_history_tick_received
        self.skcom_manager.on_realtime_tick_received = self.on_realtime_tick_received

    def start_collection(self, symbol=MTX_SYMBOL, page_no=0):
        """開始收集逐筆資料"""
        if not self.skcom_manager.stocks_ready:
            logger.error("❌ 商品資料未準備完成，無法開始收集")
            return False

        try:
            logger.info(f"🔄 開始收集 {symbol} 逐筆資料...")
            self.is_collecting = True
            self.collected_count = 0
            self.tick_buffer.clear()

            # 調用API請求逐筆資料
            # 根據API說明：SKQuoteLib_RequestTicks(psPageNo, bstrStockNo)
            nCode = self.skcom_manager.m_pSKQuote.SKQuoteLib_RequestTicks(page_no, symbol)

            if self.skcom_manager.m_pSKCenter:
                msg_text = self.skcom_manager.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
            else:
                msg_text = f"結果代碼: {nCode}"

            logger.info(f"【API調用】SKQuoteLib_RequestTicks({page_no}, {symbol}) - {msg_text} (代碼: {nCode})")

            if nCode == 0:
                logger.info("✅ 逐筆資料請求已送出，等待資料回傳...")
                return True
            else:
                logger.error(f"❌ 請求逐筆資料失敗: {msg_text}")
                self.is_collecting = False
                return False

        except Exception as e:
            logger.error(f"❌ 開始收集逐筆資料時發生錯誤: {str(e)}")
            self.is_collecting = False
            return False

    def stop_collection(self):
        """停止收集逐筆資料"""
        self.is_collecting = False

        # 處理剩餘的緩衝區資料
        if self.tick_buffer:
            self._flush_buffer()

        logger.info(f"✅ 逐筆資料收集已停止，共收集 {self.collected_count} 筆資料")

    def on_history_tick_received(self, sMarketNo, nIndex, nPtr, nDate, nTimehms,
                               nTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate):
        """處理歷史逐筆資料"""
        if not self.is_collecting:
            return

        try:
            # 格式化資料
            tick_data = {
                'symbol': MTX_SYMBOL,
                'market_no': sMarketNo,
                'index': nIndex,
                'ptr': nPtr,
                'trade_date': str(nDate),
                'trade_time': str(nTimehms).zfill(6),
                'trade_time_ms': nTimemillismicros,
                'bid_price': self.format_price(nBid),
                'ask_price': self.format_price(nAsk),
                'close_price': self.format_price(nClose),
                'volume': nQty,
                'simulate_flag': nSimulate,
                'data_type': 'HISTORY'
            }

            # 添加到緩衝區
            self.tick_buffer.append(tick_data)
            self.collected_count += 1

            # 批量插入
            if len(self.tick_buffer) >= BATCH_SIZE:
                self._flush_buffer()

            # 每1000筆顯示進度
            if self.collected_count % 1000 == 0:
                logger.info(f"📊 已收集歷史逐筆資料: {self.collected_count} 筆")

        except Exception as e:
            logger.error(f"❌ 處理歷史逐筆資料時發生錯誤: {str(e)}")

    def on_realtime_tick_received(self, sMarketNo, nIndex, nPtr, nDate, nTimehms,
                                nTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate):
        """處理即時逐筆資料"""
        if not self.is_collecting:
            return

        try:
            # 格式化資料
            tick_data = {
                'symbol': MTX_SYMBOL,
                'market_no': sMarketNo,
                'index': nIndex,
                'ptr': nPtr,
                'trade_date': str(nDate),
                'trade_time': str(nTimehms).zfill(6),
                'trade_time_ms': nTimemillismicros,
                'bid_price': self.format_price(nBid),
                'ask_price': self.format_price(nAsk),
                'close_price': self.format_price(nClose),
                'volume': nQty,
                'simulate_flag': nSimulate,
                'data_type': 'REALTIME'
            }

            # 即時資料直接插入
            self.db_manager.insert_tick_data(tick_data)
            self.collected_count += 1

            logger.debug(f"📈 即時逐筆: {tick_data['close_price']} @{tick_data['trade_time']}")

        except Exception as e:
            logger.error(f"❌ 處理即時逐筆資料時發生錯誤: {str(e)}")

    def _flush_buffer(self):
        """清空緩衝區並批量插入資料庫"""
        if not self.tick_buffer:
            return

        try:
            self.db_manager.batch_insert_tick_data(self.tick_buffer)
            logger.debug(f"💾 批量插入 {len(self.tick_buffer)} 筆逐筆資料")
            self.tick_buffer.clear()
        except Exception as e:
            logger.error(f"❌ 批量插入逐筆資料失敗: {str(e)}")
```

### 3.3 五檔資料收集器

#### collectors/best5_collector.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
五檔資料收集器 - 收集歷史和即時五檔報價
"""

import logging
from .base_collector import BaseCollector
from config import MTX_SYMBOL, BATCH_SIZE

logger = logging.getLogger(__name__)

class Best5Collector(BaseCollector):
    """五檔資料收集器"""

    def __init__(self, skcom_manager, db_manager):
        super().__init__(skcom_manager, db_manager)
        self.best5_buffer = []  # 批量插入緩衝區

        # 註冊事件回調
        self.skcom_manager.on_best5_received = self.on_best5_received

    def start_collection(self, symbol=MTX_SYMBOL, page_no=0):
        """開始收集五檔資料"""
        if not self.skcom_manager.stocks_ready:
            logger.error("❌ 商品資料未準備完成，無法開始收集")
            return False

        try:
            logger.info(f"🔄 開始收集 {symbol} 五檔資料...")
            self.is_collecting = True
            self.collected_count = 0
            self.best5_buffer.clear()

            # 五檔資料與逐筆資料使用相同的API
            nCode = self.skcom_manager.m_pSKQuote.SKQuoteLib_RequestTicks(page_no, symbol)

            if self.skcom_manager.m_pSKCenter:
                msg_text = self.skcom_manager.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
            else:
                msg_text = f"結果代碼: {nCode}"

            logger.info(f"【API調用】SKQuoteLib_RequestTicks({page_no}, {symbol}) - {msg_text} (代碼: {nCode})")

            if nCode == 0:
                logger.info("✅ 五檔資料請求已送出，等待資料回傳...")
                return True
            else:
                logger.error(f"❌ 請求五檔資料失敗: {msg_text}")
                self.is_collecting = False
                return False

        except Exception as e:
            logger.error(f"❌ 開始收集五檔資料時發生錯誤: {str(e)}")
            self.is_collecting = False
            return False

    def stop_collection(self):
        """停止收集五檔資料"""
        self.is_collecting = False

        # 處理剩餘的緩衝區資料
        if self.best5_buffer:
            self._flush_buffer()

        logger.info(f"✅ 五檔資料收集已停止，共收集 {self.collected_count} 筆資料")

    def on_best5_received(self, sMarketNo, nIndex, nBestBid1, nBestBidQty1, nBestBid2, nBestBidQty2,
                         nBestBid3, nBestBidQty3, nBestBid4, nBestBidQty4, nBestBid5, nBestBidQty5,
                         nExtendBid, nExtendBidQty, nBestAsk1, nBestAskQty1, nBestAsk2, nBestAskQty2,
                         nBestAsk3, nBestAskQty3, nBestAsk4, nBestAskQty4, nBestAsk5, nBestAskQty5,
                         nExtendAsk, nExtendAskQty, nSimulate):
        """處理五檔資料"""
        if not self.is_collecting:
            return

        try:
            # 格式化資料
            best5_data = {
                'symbol': MTX_SYMBOL,
                'market_no': sMarketNo,
                'index': nIndex,
                'trade_date': datetime.now().strftime('%Y%m%d'),
                'trade_time': datetime.now().strftime('%H%M%S'),
                # 五檔買價買量
                'bid_price_1': self.format_price(nBestBid1),
                'bid_volume_1': nBestBidQty1,
                'bid_price_2': self.format_price(nBestBid2),
                'bid_volume_2': nBestBidQty2,
                'bid_price_3': self.format_price(nBestBid3),
                'bid_volume_3': nBestBidQty3,
                'bid_price_4': self.format_price(nBestBid4),
                'bid_volume_4': nBestBidQty4,
                'bid_price_5': self.format_price(nBestBid5),
                'bid_volume_5': nBestBidQty5,
                # 五檔賣價賣量
                'ask_price_1': self.format_price(nBestAsk1),
                'ask_volume_1': nBestAskQty1,
                'ask_price_2': self.format_price(nBestAsk2),
                'ask_volume_2': nBestAskQty2,
                'ask_price_3': self.format_price(nBestAsk3),
                'ask_volume_3': nBestAskQty3,
                'ask_price_4': self.format_price(nBestAsk4),
                'ask_volume_4': nBestAskQty4,
                'ask_price_5': self.format_price(nBestAsk5),
                'ask_volume_5': nBestAskQty5,
                # 延伸買賣
                'extend_bid': self.format_price(nExtendBid),
                'extend_bid_qty': nExtendBidQty,
                'extend_ask': self.format_price(nExtendAsk),
                'extend_ask_qty': nExtendAskQty,
                'simulate_flag': nSimulate
            }

            # 添加到緩衝區
            self.best5_buffer.append(best5_data)
            self.collected_count += 1

            # 批量插入
            if len(self.best5_buffer) >= BATCH_SIZE:
                self._flush_buffer()

            # 每100筆顯示進度
            if self.collected_count % 100 == 0:
                logger.info(f"📊 已收集五檔資料: {self.collected_count} 筆")

        except Exception as e:
            logger.error(f"❌ 處理五檔資料時發生錯誤: {str(e)}")

    def _flush_buffer(self):
        """清空緩衝區並批量插入資料庫"""
        if not self.best5_buffer:
            return

        try:
            self.db_manager.batch_insert_best5_data(self.best5_buffer)
            logger.debug(f"💾 批量插入 {len(self.best5_buffer)} 筆五檔資料")
            self.best5_buffer.clear()
        except Exception as e:
            logger.error(f"❌ 批量插入五檔資料失敗: {str(e)}")
```

### 3.4 K線資料收集器

#### collectors/kline_collector.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K線資料收集器 - 收集歷史K線資料
"""

import logging
from .base_collector import BaseCollector
from config import MTX_SYMBOL, KLINE_TYPES, TRADING_SESSIONS

logger = logging.getLogger(__name__)

class KLineCollector(BaseCollector):
    """K線資料收集器"""

    def __init__(self, skcom_manager, db_manager):
        super().__init__(skcom_manager, db_manager)
        self.kline_buffer = []
        self.is_complete = False

        # 註冊事件回調
        self.skcom_manager.on_kline_received = self.on_kline_received
        self.skcom_manager.on_kline_complete = self.on_kline_complete

    def start_collection(self, symbol=MTX_SYMBOL, kline_type='MINUTE',
                        start_date='20240101', end_date='20241231',
                        trading_session='ALL', minute_number=1):
        """
        開始收集K線資料

        Args:
            symbol: 商品代碼
            kline_type: K線類型 ('MINUTE', 'DAILY', 'WEEKLY', 'MONTHLY')
            start_date: 起始日期 (YYYYMMDD)
            end_date: 結束日期 (YYYYMMDD)
            trading_session: 交易時段 ('ALL', 'AM_ONLY')
            minute_number: 分鐘數（當kline_type='MINUTE'時有效）
        """
        if not self.skcom_manager.stocks_ready:
            logger.error("❌ 商品資料未準備完成，無法開始收集")
            return False

        try:
            logger.info(f"🔄 開始收集 {symbol} K線資料...")
            logger.info(f"📊 參數: {kline_type}K線, {start_date}~{end_date}, 交易時段:{trading_session}")

            self.is_collecting = True
            self.is_complete = False
            self.collected_count = 0
            self.kline_buffer.clear()

            # 轉換參數
            sKLineType = KLINE_TYPES.get(kline_type, 0)
            sTradeSession = TRADING_SESSIONS.get(trading_session, 0)
            sOutType = 1  # 新版格式
            sMinuteNumber = minute_number if kline_type == 'MINUTE' else 1

            # 調用API請求K線資料
            # SKQuoteLib_RequestKLineAMByDate(bstrStockNo, sKLineType, sOutType,
            #                                sTradeSession, bstrStartDate, bstrEndDate, sMinuteNumber)
            nCode = self.skcom_manager.m_pSKQuote.SKQuoteLib_RequestKLineAMByDate(
                symbol, sKLineType, sOutType, sTradeSession,
                start_date, end_date, sMinuteNumber)

            if self.skcom_manager.m_pSKCenter:
                msg_text = self.skcom_manager.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
            else:
                msg_text = f"結果代碼: {nCode}"

            logger.info(f"【API調用】SKQuoteLib_RequestKLineAMByDate() - {msg_text} (代碼: {nCode})")

            if nCode == 0:
                logger.info("✅ K線資料請求已送出，等待資料回傳...")
                return True
            else:
                logger.error(f"❌ 請求K線資料失敗: {msg_text}")
                self.is_collecting = False
                return False

        except Exception as e:
            logger.error(f"❌ 開始收集K線資料時發生錯誤: {str(e)}")
            self.is_collecting = False
            return False

    def stop_collection(self):
        """停止收集K線資料"""
        self.is_collecting = False

        # 處理剩餘的緩衝區資料
        if self.kline_buffer:
            self._flush_buffer()

        logger.info(f"✅ K線資料收集已停止，共收集 {self.collected_count} 筆資料")

    def on_kline_received(self, stock_no, data):
        """處理K線資料"""
        if not self.is_collecting:
            return

        try:
            # 解析K線資料字串
            # 根據API文件，資料格式可能為：日期,時間,開,高,低,收,量
            data_parts = data.split(',')
            if len(data_parts) < 6:
                logger.warning(f"⚠️ K線資料格式不正確: {data}")
                return

            kline_data = {
                'symbol': stock_no,
                'trade_date': data_parts[0],
                'trade_time': data_parts[1] if len(data_parts) > 6 else None,
                'open_price': float(data_parts[2]) if data_parts[2] else None,
                'high_price': float(data_parts[3]) if data_parts[3] else None,
                'low_price': float(data_parts[4]) if data_parts[4] else None,
                'close_price': float(data_parts[5]) if data_parts[5] else None,
                'volume': int(data_parts[6]) if len(data_parts) > 6 and data_parts[6] else None
            }

            # 添加到緩衝區
            self.kline_buffer.append(kline_data)
            self.collected_count += 1

            # 每100筆顯示進度
            if self.collected_count % 100 == 0:
                logger.info(f"📊 已收集K線資料: {self.collected_count} 筆")

        except Exception as e:
            logger.error(f"❌ 處理K線資料時發生錯誤: {str(e)}")

    def on_kline_complete(self, end_string):
        """K線查詢完成事件"""
        if end_string == "##":
            logger.info("✅ K線資料查詢完成")
            self.is_complete = True

            # 處理剩餘的緩衝區資料
            if self.kline_buffer:
                self._flush_buffer()

            self.stop_collection()

    def _flush_buffer(self):
        """清空緩衝區並批量插入資料庫"""
        if not self.kline_buffer:
            return

        try:
            self.db_manager.batch_insert_kline_data(self.kline_buffer)
            logger.debug(f"💾 批量插入 {len(self.kline_buffer)} 筆K線資料")
            self.kline_buffer.clear()
        except Exception as e:
            logger.error(f"❌ 批量插入K線資料失敗: {str(e)}")
```

---

## 🗄️ 階段四：資料庫設計與實現

### 4.1 資料庫結構定義

#### database/schema.sql
```sql
-- 群益期貨歷史資料收集器資料庫結構

-- 逐筆資料表
CREATE TABLE IF NOT EXISTS tick_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,                    -- 商品代碼 (MTX00)
    market_no INTEGER,                       -- 市場別代號
    index_code INTEGER,                      -- 系統索引代碼
    ptr INTEGER,                             -- 資料位址/成交明細順序
    trade_date TEXT NOT NULL,                -- 交易日期 (YYYYMMDD)
    trade_time TEXT NOT NULL,                -- 交易時間 (HHMMSS)
    trade_time_ms INTEGER,                   -- 毫秒微秒
    bid_price REAL,                          -- 買價
    ask_price REAL,                          -- 賣價
    close_price REAL NOT NULL,               -- 成交價
    volume INTEGER NOT NULL,                 -- 成交量
    simulate_flag INTEGER DEFAULT 0,         -- 揭示類型 (0:一般, 1:試算)
    data_type TEXT DEFAULT 'HISTORY',        -- 資料類型 (HISTORY/REALTIME)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 建立索引
    UNIQUE(symbol, trade_date, trade_time, trade_time_ms, ptr)
);

-- 五檔資料表
CREATE TABLE IF NOT EXISTS best5_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,                    -- 商品代碼
    market_no INTEGER,                       -- 市場別代號
    index_code INTEGER,                      -- 系統索引代碼
    trade_date TEXT NOT NULL,                -- 交易日期
    trade_time TEXT NOT NULL,                -- 交易時間

    -- 五檔買價買量
    bid_price_1 REAL, bid_volume_1 INTEGER,
    bid_price_2 REAL, bid_volume_2 INTEGER,
    bid_price_3 REAL, bid_volume_3 INTEGER,
    bid_price_4 REAL, bid_volume_4 INTEGER,
    bid_price_5 REAL, bid_volume_5 INTEGER,

    -- 五檔賣價賣量
    ask_price_1 REAL, ask_volume_1 INTEGER,
    ask_price_2 REAL, ask_volume_2 INTEGER,
    ask_price_3 REAL, ask_volume_3 INTEGER,
    ask_price_4 REAL, ask_volume_4 INTEGER,
    ask_price_5 REAL, ask_volume_5 INTEGER,

    -- 延伸買賣
    extend_bid REAL, extend_bid_qty INTEGER,
    extend_ask REAL, extend_ask_qty INTEGER,

    simulate_flag INTEGER DEFAULT 0,         -- 揭示類型
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 建立索引
    UNIQUE(symbol, trade_date, trade_time, market_no, index_code)
);

-- K線資料表
CREATE TABLE IF NOT EXISTS kline_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,                    -- 商品代碼
    kline_type TEXT NOT NULL,                -- K線類型 (MINUTE/DAILY/WEEKLY/MONTHLY)
    trade_date TEXT NOT NULL,                -- 交易日期
    trade_time TEXT,                         -- 交易時間 (分線才有)
    open_price REAL NOT NULL,                -- 開盤價
    high_price REAL NOT NULL,                -- 最高價
    low_price REAL NOT NULL,                 -- 最低價
    close_price REAL NOT NULL,               -- 收盤價
    volume INTEGER,                          -- 成交量
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 建立索引
    UNIQUE(symbol, kline_type, trade_date, trade_time)
);

-- 建立查詢索引
CREATE INDEX IF NOT EXISTS idx_tick_symbol_date ON tick_data(symbol, trade_date);
CREATE INDEX IF NOT EXISTS idx_tick_time ON tick_data(trade_date, trade_time);
CREATE INDEX IF NOT EXISTS idx_best5_symbol_date ON best5_data(symbol, trade_date);
CREATE INDEX IF NOT EXISTS idx_best5_time ON best5_data(trade_date, trade_time);
CREATE INDEX IF NOT EXISTS idx_kline_symbol_type_date ON kline_data(symbol, kline_type, trade_date);

-- 資料收集記錄表
CREATE TABLE IF NOT EXISTS collection_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_type TEXT NOT NULL,           -- 收集類型 (TICK/BEST5/KLINE)
    symbol TEXT NOT NULL,                    -- 商品代碼
    start_time TIMESTAMP NOT NULL,           -- 開始時間
    end_time TIMESTAMP,                      -- 結束時間
    records_count INTEGER DEFAULT 0,        -- 收集筆數
    status TEXT DEFAULT 'RUNNING',           -- 狀態 (RUNNING/COMPLETED/FAILED)
    error_message TEXT,                      -- 錯誤訊息
    parameters TEXT,                         -- 收集參數 (JSON格式)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.2 資料庫管理器

#### database/db_manager.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
資料庫管理器 - 處理所有資料庫操作
"""

import sqlite3
import logging
import os
import json
from datetime import datetime
from config import DATABASE_PATH, DATA_DIR

logger = logging.getLogger(__name__)

class DatabaseManager:
    """資料庫管理器"""

    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
        self.connection = None

        # 確保資料目錄存在
        os.makedirs(DATA_DIR, exist_ok=True)

        # 初始化資料庫
        self.initialize_database()

    def initialize_database(self):
        """初始化資料庫結構"""
        try:
            # 讀取SQL結構檔案
            schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')

            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()

            # 執行建表語句
            with self.get_connection() as conn:
                conn.executescript(schema_sql)
                conn.commit()

            logger.info("✅ 資料庫初始化完成")

        except Exception as e:
            logger.error(f"❌ 資料庫初始化失敗: {e}")
            raise

    def get_connection(self):
        """取得資料庫連線"""
        return sqlite3.connect(self.db_path)

    def insert_tick_data(self, tick_data):
        """插入單筆逐筆資料"""
        sql = """
        INSERT OR IGNORE INTO tick_data
        (symbol, market_no, index_code, ptr, trade_date, trade_time, trade_time_ms,
         bid_price, ask_price, close_price, volume, simulate_flag, data_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        values = (
            tick_data['symbol'], tick_data.get('market_no'), tick_data.get('index'),
            tick_data.get('ptr'), tick_data['trade_date'], tick_data['trade_time'],
            tick_data.get('trade_time_ms'), tick_data.get('bid_price'),
            tick_data.get('ask_price'), tick_data.get('close_price'),
            tick_data.get('volume'), tick_data.get('simulate_flag', 0),
            tick_data.get('data_type', 'HISTORY')
        )

        try:
            with self.get_connection() as conn:
                conn.execute(sql, values)
                conn.commit()
        except Exception as e:
            logger.error(f"❌ 插入逐筆資料失敗: {e}")
            raise

    def batch_insert_tick_data(self, tick_data_list):
        """批量插入逐筆資料"""
        if not tick_data_list:
            return

        sql = """
        INSERT OR IGNORE INTO tick_data
        (symbol, market_no, index_code, ptr, trade_date, trade_time, trade_time_ms,
         bid_price, ask_price, close_price, volume, simulate_flag, data_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        values_list = []
        for tick_data in tick_data_list:
            values = (
                tick_data['symbol'], tick_data.get('market_no'), tick_data.get('index'),
                tick_data.get('ptr'), tick_data['trade_date'], tick_data['trade_time'],
                tick_data.get('trade_time_ms'), tick_data.get('bid_price'),
                tick_data.get('ask_price'), tick_data.get('close_price'),
                tick_data.get('volume'), tick_data.get('simulate_flag', 0),
                tick_data.get('data_type', 'HISTORY')
            )
            values_list.append(values)

        try:
            with self.get_connection() as conn:
                conn.executemany(sql, values_list)
                conn.commit()
                logger.debug(f"💾 批量插入 {len(values_list)} 筆逐筆資料")
        except Exception as e:
            logger.error(f"❌ 批量插入逐筆資料失敗: {e}")
            raise

    def batch_insert_best5_data(self, best5_data_list):
        """批量插入五檔資料"""
        if not best5_data_list:
            return

        sql = """
        INSERT OR IGNORE INTO best5_data
        (symbol, market_no, index_code, trade_date, trade_time,
         bid_price_1, bid_volume_1, bid_price_2, bid_volume_2, bid_price_3, bid_volume_3,
         bid_price_4, bid_volume_4, bid_price_5, bid_volume_5,
         ask_price_1, ask_volume_1, ask_price_2, ask_volume_2, ask_price_3, ask_volume_3,
         ask_price_4, ask_volume_4, ask_price_5, ask_volume_5,
         extend_bid, extend_bid_qty, extend_ask, extend_ask_qty, simulate_flag)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        values_list = []
        for best5_data in best5_data_list:
            values = (
                best5_data['symbol'], best5_data.get('market_no'), best5_data.get('index'),
                best5_data['trade_date'], best5_data['trade_time'],
                best5_data.get('bid_price_1'), best5_data.get('bid_volume_1'),
                best5_data.get('bid_price_2'), best5_data.get('bid_volume_2'),
                best5_data.get('bid_price_3'), best5_data.get('bid_volume_3'),
                best5_data.get('bid_price_4'), best5_data.get('bid_volume_4'),
                best5_data.get('bid_price_5'), best5_data.get('bid_volume_5'),
                best5_data.get('ask_price_1'), best5_data.get('ask_volume_1'),
                best5_data.get('ask_price_2'), best5_data.get('ask_volume_2'),
                best5_data.get('ask_price_3'), best5_data.get('ask_volume_3'),
                best5_data.get('ask_price_4'), best5_data.get('ask_volume_4'),
                best5_data.get('ask_price_5'), best5_data.get('ask_volume_5'),
                best5_data.get('extend_bid'), best5_data.get('extend_bid_qty'),
                best5_data.get('extend_ask'), best5_data.get('extend_ask_qty'),
                best5_data.get('simulate_flag', 0)
            )
            values_list.append(values)

        try:
            with self.get_connection() as conn:
                conn.executemany(sql, values_list)
                conn.commit()
                logger.debug(f"💾 批量插入 {len(values_list)} 筆五檔資料")
        except Exception as e:
            logger.error(f"❌ 批量插入五檔資料失敗: {e}")
            raise

    def batch_insert_kline_data(self, kline_data_list):
        """批量插入K線資料"""
        if not kline_data_list:
            return

        sql = """
        INSERT OR IGNORE INTO kline_data
        (symbol, kline_type, trade_date, trade_time, open_price, high_price, low_price, close_price, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        values_list = []
        for kline_data in kline_data_list:
            values = (
                kline_data['symbol'], kline_data.get('kline_type', 'MINUTE'),
                kline_data['trade_date'], kline_data.get('trade_time'),
                kline_data.get('open_price'), kline_data.get('high_price'),
                kline_data.get('low_price'), kline_data.get('close_price'),
                kline_data.get('volume')
            )
            values_list.append(values)

        try:
            with self.get_connection() as conn:
                conn.executemany(sql, values_list)
                conn.commit()
                logger.debug(f"💾 批量插入 {len(values_list)} 筆K線資料")
        except Exception as e:
            logger.error(f"❌ 批量插入K線資料失敗: {e}")
            raise

    def log_collection_start(self, collection_type, symbol, parameters=None):
        """記錄收集開始"""
        sql = """
        INSERT INTO collection_log
        (collection_type, symbol, start_time, status, parameters)
        VALUES (?, ?, ?, 'RUNNING', ?)
        """

        try:
            with self.get_connection() as conn:
                cursor = conn.execute(sql, (
                    collection_type, symbol, datetime.now(),
                    json.dumps(parameters) if parameters else None
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"❌ 記錄收集開始失敗: {e}")
            return None

    def log_collection_end(self, log_id, records_count, status='COMPLETED', error_message=None):
        """記錄收集結束"""
        sql = """
        UPDATE collection_log
        SET end_time = ?, records_count = ?, status = ?, error_message = ?
        WHERE id = ?
        """

        try:
            with self.get_connection() as conn:
                conn.execute(sql, (datetime.now(), records_count, status, error_message, log_id))
                conn.commit()
        except Exception as e:
            logger.error(f"❌ 記錄收集結束失敗: {e}")

    def get_data_statistics(self):
        """取得資料統計"""
        try:
            with self.get_connection() as conn:
                # 逐筆資料統計
                tick_count = conn.execute("SELECT COUNT(*) FROM tick_data").fetchone()[0]

                # 五檔資料統計
                best5_count = conn.execute("SELECT COUNT(*) FROM best5_data").fetchone()[0]

                # K線資料統計
                kline_count = conn.execute("SELECT COUNT(*) FROM kline_data").fetchone()[0]

                # 最新資料時間
                latest_tick = conn.execute(
                    "SELECT MAX(trade_date || trade_time) FROM tick_data"
                ).fetchone()[0]

                return {
                    'tick_count': tick_count,
                    'best5_count': best5_count,
                    'kline_count': kline_count,
                    'latest_tick_time': latest_tick
                }
        except Exception as e:
            logger.error(f"❌ 取得資料統計失敗: {e}")
            return None
```

---

## 🚀 階段五：整合與測試

### 5.1 主程式

#### main.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
群益期貨歷史資料收集器主程式
"""

import os
import sys
import logging
import argparse
import time
from datetime import datetime, timedelta

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import *
from utils.skcom_manager import SKCOMManager
from utils.logger import setup_logger
from database.db_manager import DatabaseManager
from collectors.tick_collector import TickCollector
from collectors.best5_collector import Best5Collector
from collectors.kline_collector import KLineCollector

# 設定日誌
setup_logger()
logger = logging.getLogger(__name__)

class HistoryDataCollector:
    """歷史資料收集器主類別"""

    def __init__(self):
        self.skcom_manager = None
        self.db_manager = None
        self.tick_collector = None
        self.best5_collector = None
        self.kline_collector = None

    def initialize(self):
        """初始化所有元件"""
        try:
            logger.info("🚀 開始初始化歷史資料收集器...")

            # 初始化SKCOM管理器
            logger.info("🔄 初始化SKCOM管理器...")
            self.skcom_manager = SKCOMManager()

            if not self.skcom_manager.initialize_skcom():
                raise Exception("SKCOM API初始化失敗")

            if not self.skcom_manager.initialize_skcom_objects():
                raise Exception("SKCOM物件初始化失敗")

            # 初始化資料庫管理器
            logger.info("🔄 初始化資料庫管理器...")
            self.db_manager = DatabaseManager()

            # 初始化收集器
            logger.info("🔄 初始化資料收集器...")
            self.tick_collector = TickCollector(self.skcom_manager, self.db_manager)
            self.best5_collector = Best5Collector(self.skcom_manager, self.db_manager)
            self.kline_collector = KLineCollector(self.skcom_manager, self.db_manager)

            logger.info("✅ 所有元件初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ 初始化失敗: {e}")
            return False

    def login(self, user_id, password):
        """登入群益API"""
        logger.info("🔐 開始登入群益API...")

        if not self.skcom_manager.login(user_id, password):
            logger.error("❌ 登入失敗")
            return False

        logger.info("✅ 登入成功")
        return True

    def connect_quote_server(self):
        """連線報價主機"""
        logger.info("📡 開始連線報價主機...")

        if not self.skcom_manager.connect_quote_server():
            logger.error("❌ 連線報價主機失敗")
            return False

        # 等待商品資料準備完成
        logger.info("⏳ 等待商品資料準備完成...")
        timeout = 30  # 30秒超時
        start_time = time.time()

        while not self.skcom_manager.stocks_ready:
            if time.time() - start_time > timeout:
                logger.error("❌ 等待商品資料準備完成超時")
                return False
            time.sleep(1)

        logger.info("✅ 報價主機連線成功，商品資料已準備完成")
        return True

    def collect_tick_data(self, symbol=MTX_SYMBOL):
        """收集逐筆資料"""
        logger.info(f"📊 開始收集 {symbol} 逐筆資料...")

        # 記錄收集開始
        log_id = self.db_manager.log_collection_start('TICK', symbol)

        try:
            if self.tick_collector.start_collection(symbol):
                logger.info("✅ 逐筆資料收集已啟動，請等待資料回傳...")
                return True
            else:
                self.db_manager.log_collection_end(log_id, 0, 'FAILED', '啟動收集失敗')
                return False
        except Exception as e:
            logger.error(f"❌ 收集逐筆資料失敗: {e}")
            self.db_manager.log_collection_end(log_id, 0, 'FAILED', str(e))
            return False

    def collect_best5_data(self, symbol=MTX_SYMBOL):
        """收集五檔資料"""
        logger.info(f"📊 開始收集 {symbol} 五檔資料...")

        # 記錄收集開始
        log_id = self.db_manager.log_collection_start('BEST5', symbol)

        try:
            if self.best5_collector.start_collection(symbol):
                logger.info("✅ 五檔資料收集已啟動，請等待資料回傳...")
                return True
            else:
                self.db_manager.log_collection_end(log_id, 0, 'FAILED', '啟動收集失敗')
                return False
        except Exception as e:
            logger.error(f"❌ 收集五檔資料失敗: {e}")
            self.db_manager.log_collection_end(log_id, 0, 'FAILED', str(e))
            return False

    def collect_kline_data(self, symbol=MTX_SYMBOL, kline_type='MINUTE',
                          start_date=None, end_date=None):
        """收集K線資料"""
        # 預設查詢最近30天
        if not start_date:
            start_date = (datetime.now() - timedelta(days=DEFAULT_DATE_RANGE)).strftime('%Y%m%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')

        logger.info(f"📊 開始收集 {symbol} K線資料 ({kline_type}, {start_date}~{end_date})...")

        # 記錄收集開始
        parameters = {
            'kline_type': kline_type,
            'start_date': start_date,
            'end_date': end_date
        }
        log_id = self.db_manager.log_collection_start('KLINE', symbol, parameters)

        try:
            if self.kline_collector.start_collection(symbol, kline_type, start_date, end_date):
                logger.info("✅ K線資料收集已啟動，請等待資料回傳...")
                return True
            else:
                self.db_manager.log_collection_end(log_id, 0, 'FAILED', '啟動收集失敗')
                return False
        except Exception as e:
            logger.error(f"❌ 收集K線資料失敗: {e}")
            self.db_manager.log_collection_end(log_id, 0, 'FAILED', str(e))
            return False

    def show_statistics(self):
        """顯示資料統計"""
        stats = self.db_manager.get_data_statistics()
        if stats:
            logger.info("📊 資料庫統計:")
            logger.info(f"   逐筆資料: {stats['tick_count']:,} 筆")
            logger.info(f"   五檔資料: {stats['best5_count']:,} 筆")
            logger.info(f"   K線資料: {stats['kline_count']:,} 筆")
            logger.info(f"   最新逐筆時間: {stats['latest_tick_time']}")
        else:
            logger.error("❌ 無法取得資料統計")

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='群益期貨歷史資料收集器')
    parser.add_argument('--user-id', required=True, help='身分證字號')
    parser.add_argument('--password', required=True, help='密碼')
    parser.add_argument('--symbol', default=MTX_SYMBOL, help='商品代碼')
    parser.add_argument('--collect-type', choices=['tick', 'best5', 'kline', 'all'],
                       default='all', help='收集類型')
    parser.add_argument('--kline-type', choices=['MINUTE', 'DAILY', 'WEEKLY', 'MONTHLY'],
                       default='MINUTE', help='K線類型')
    parser.add_argument('--start-date', help='開始日期 (YYYYMMDD)')
    parser.add_argument('--end-date', help='結束日期 (YYYYMMDD)')
    parser.add_argument('--duration', type=int, default=60, help='收集持續時間(秒)')

    args = parser.parse_args()

    # 建立收集器
    collector = HistoryDataCollector()

    try:
        # 初始化
        if not collector.initialize():
            logger.error("❌ 初始化失敗")
            return 1

        # 登入
        if not collector.login(args.user_id, args.password):
            logger.error("❌ 登入失敗")
            return 1

        # 連線報價主機
        if not collector.connect_quote_server():
            logger.error("❌ 連線報價主機失敗")
            return 1

        # 開始收集資料
        if args.collect_type in ['tick', 'all']:
            collector.collect_tick_data(args.symbol)

        if args.collect_type in ['best5', 'all']:
            collector.collect_best5_data(args.symbol)

        if args.collect_type in ['kline', 'all']:
            collector.collect_kline_data(args.symbol, args.kline_type,
                                       args.start_date, args.end_date)

        # 等待收集完成
        logger.info(f"⏳ 收集中，將持續 {args.duration} 秒...")
        time.sleep(args.duration)

        # 停止收集
        if collector.tick_collector:
            collector.tick_collector.stop_collection()
        if collector.best5_collector:
            collector.best5_collector.stop_collection()
        if collector.kline_collector:
            collector.kline_collector.stop_collection()

        # 顯示統計
        collector.show_statistics()

        logger.info("✅ 歷史資料收集完成")
        return 0

    except KeyboardInterrupt:
        logger.info("⏹️ 使用者中斷收集")
        return 0
    except Exception as e:
        logger.error(f"❌ 程式執行錯誤: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### 5.2 工具模組

#### utils/logger.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日誌工具模組
"""

import logging
import os
from config import LOG_LEVEL, LOG_FORMAT, LOG_FILE, LOGS_DIR

def setup_logger():
    """設定日誌系統"""
    # 確保日誌目錄存在
    os.makedirs(LOGS_DIR, exist_ok=True)

    # 設定根日誌器
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    # 設定comtypes日誌級別（避免過多輸出）
    logging.getLogger('comtypes').setLevel(logging.WARNING)
```

#### utils/date_utils.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日期工具模組
"""

from datetime import datetime, timedelta

def get_trading_days(start_date, end_date):
    """取得交易日清單（排除週末）"""
    trading_days = []
    current_date = datetime.strptime(start_date, '%Y%m%d')
    end_date_obj = datetime.strptime(end_date, '%Y%m%d')

    while current_date <= end_date_obj:
        # 排除週末 (0=週一, 6=週日)
        if current_date.weekday() < 5:
            trading_days.append(current_date.strftime('%Y%m%d'))
        current_date += timedelta(days=1)

    return trading_days

def format_date_range(days_back=30):
    """格式化日期範圍"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    return start_date.strftime('%Y%m%d'), end_date.strftime('%Y%m%d')
```

---

## 📖 使用說明

### 6.1 安裝與設定

1. **複製必要檔案**
   ```bash
   # 從OrderTester目錄複製SKCOM相關檔案
   cp /Users/z/big/my-capital-project/Python\ File/SKCOM.dll ./
   cp /Users/z/big/my-capital-project/Python\ File/SKCOMTester.exe ./
   ```

2. **安裝Python依賴**
   ```bash
   pip install comtypes
   ```

3. **建立目錄結構**
   ```bash
   mkdir -p data logs database collectors utils
   ```

### 6.2 基本使用

1. **收集所有類型資料**
   ```bash
   python main.py --user-id YOUR_ID --password YOUR_PASSWORD
   ```

2. **只收集逐筆資料**
   ```bash
   python main.py --user-id YOUR_ID --password YOUR_PASSWORD --collect-type tick
   ```

3. **收集指定日期範圍的K線資料**
   ```bash
   python main.py --user-id YOUR_ID --password YOUR_PASSWORD \
                   --collect-type kline --kline-type DAILY \
                   --start-date 20240101 --end-date 20241231
   ```

4. **收集特定商品資料**
   ```bash
   python main.py --user-id YOUR_ID --password YOUR_PASSWORD \
                   --symbol MTX00 --duration 300
   ```

### 6.3 資料查詢範例

```python
# 查詢逐筆資料
import sqlite3
conn = sqlite3.connect('data/history_data.db')

# 查詢今日逐筆資料
today = '20241201'
cursor = conn.execute("""
    SELECT trade_time, close_price, volume
    FROM tick_data
    WHERE symbol='MTX00' AND trade_date=?
    ORDER BY trade_time
""", (today,))

for row in cursor:
    print(f"時間: {row[0]}, 價格: {row[1]}, 量: {row[2]}")

# 查詢五檔資料
cursor = conn.execute("""
    SELECT trade_time, bid_price_1, bid_volume_1, ask_price_1, ask_volume_1
    FROM best5_data
    WHERE symbol='MTX00' AND trade_date=?
    ORDER BY trade_time DESC LIMIT 10
""", (today,))

# 查詢K線資料
cursor = conn.execute("""
    SELECT trade_date, open_price, high_price, low_price, close_price, volume
    FROM kline_data
    WHERE symbol='MTX00' AND kline_type='DAILY'
    ORDER BY trade_date DESC LIMIT 30
""")
```

---

## ⚠️ 重要注意事項

### 7.1 API使用限制

1. **連線數限制**
   - 群益API最多允許2條行情連線
   - 國內證券與期貨共用一條連線
   - 海外期貨使用另一條連線

2. **權限要求**
   - 需要申請API權限
   - 需要簽署相關同意書
   - 需要完成雙因子認證設定

3. **資料限制**
   - 歷史資料通常只提供當天的逐筆資料
   - K線資料可查詢較長時間範圍
   - 五檔資料主要為即時資料

### 7.2 開發注意事項

1. **錯誤處理**
   - 實現完整的異常處理機制
   - 添加重連和重試邏輯
   - 記錄詳細的錯誤日誌

2. **效能優化**
   - 使用批量插入提高資料庫效能
   - 適當設定緩衝區大小
   - 建立必要的資料庫索引

3. **資料完整性**
   - 實現資料去重機制
   - 驗證資料格式正確性
   - 定期備份重要資料

4. **記憶體管理**
   - 避免長時間累積大量資料在記憶體中
   - 定期清理緩衝區
   - 監控記憶體使用情況

### 7.3 測試建議

1. **階段性測試**
   - 先測試登入和連線功能
   - 再測試單一類型資料收集
   - 最後測試完整流程

2. **資料驗證**
   - 比對收集的資料與官方工具
   - 檢查資料的時間順序
   - 驗證價格格式是否正確

3. **長時間運行測試**
   - 測試程式穩定性
   - 監控記憶體洩漏
   - 驗證錯誤恢復機制

---

## 🎯 開發優先順序

1. **第一優先**：建立基礎架構和SKCOM連接
2. **第二優先**：實現逐筆資料收集（最重要的功能）
3. **第三優先**：實現資料庫儲存和查詢
4. **第四優先**：實現K線資料收集
5. **第五優先**：實現五檔資料收集和完善錯誤處理

這個開發說明提供了完整的實現架構和程式碼範例，您可以按照階段逐步開發，確保每個階段都能正常運作後再進行下一階段。
```
```
```