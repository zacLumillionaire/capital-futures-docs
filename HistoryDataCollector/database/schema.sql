-- 群益期貨歷史資料收集器資料庫結構
-- 支援逐筆、五檔、K線三種資料類型
-- 設計重點：資料去重、查詢效能、完整性約束

-- 逐筆資料表
CREATE TABLE IF NOT EXISTS tick_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,                    -- 商品代碼 (MTX00, TXF00等)
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

    -- 建立唯一約束避免重複資料
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

    -- 建立唯一約束避免重複資料
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

    -- 建立唯一約束避免重複資料
    UNIQUE(symbol, kline_type, trade_date, trade_time)
);

-- 資料收集記錄表
CREATE TABLE IF NOT EXISTS collection_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_type TEXT NOT NULL,           -- 收集類型 (TICK/BEST5/KLINE)
    symbol TEXT NOT NULL,                    -- 商品代碼
    start_time TIMESTAMP NOT NULL,           -- 開始時間
    end_time TIMESTAMP,                      -- 結束時間
    records_count INTEGER DEFAULT 0,        -- 收集筆數
    status TEXT DEFAULT 'RUNNING',           -- 狀態 (RUNNING/COMPLETED/FAILED/STOPPED)
    error_message TEXT,                      -- 錯誤訊息
    parameters TEXT,                         -- 收集參數 (JSON格式)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 建立查詢索引以提升效能
-- 逐筆資料索引
CREATE INDEX IF NOT EXISTS idx_tick_symbol_date ON tick_data(symbol, trade_date);
CREATE INDEX IF NOT EXISTS idx_tick_time ON tick_data(trade_date, trade_time);
CREATE INDEX IF NOT EXISTS idx_tick_price ON tick_data(close_price);
CREATE INDEX IF NOT EXISTS idx_tick_volume ON tick_data(volume);

-- 五檔資料索引
CREATE INDEX IF NOT EXISTS idx_best5_symbol_date ON best5_data(symbol, trade_date);
CREATE INDEX IF NOT EXISTS idx_best5_time ON best5_data(trade_date, trade_time);
CREATE INDEX IF NOT EXISTS idx_best5_bid1 ON best5_data(bid_price_1);
CREATE INDEX IF NOT EXISTS idx_best5_ask1 ON best5_data(ask_price_1);

-- K線資料索引
CREATE INDEX IF NOT EXISTS idx_kline_symbol_type_date ON kline_data(symbol, kline_type, trade_date);
CREATE INDEX IF NOT EXISTS idx_kline_date_range ON kline_data(trade_date, trade_time);
CREATE INDEX IF NOT EXISTS idx_kline_price ON kline_data(close_price);

-- 收集記錄索引
CREATE INDEX IF NOT EXISTS idx_collection_type_symbol ON collection_log(collection_type, symbol);
CREATE INDEX IF NOT EXISTS idx_collection_time ON collection_log(start_time);
CREATE INDEX IF NOT EXISTS idx_collection_status ON collection_log(status);

-- 建立視圖以便查詢
-- 最新逐筆資料視圖
CREATE VIEW IF NOT EXISTS latest_tick_data AS
SELECT 
    symbol,
    trade_date,
    trade_time,
    close_price,
    volume,
    bid_price,
    ask_price,
    created_at
FROM tick_data 
WHERE id IN (
    SELECT MAX(id) 
    FROM tick_data 
    GROUP BY symbol, trade_date
)
ORDER BY symbol, trade_date DESC, trade_time DESC;

-- 最新五檔資料視圖
CREATE VIEW IF NOT EXISTS latest_best5_data AS
SELECT 
    symbol,
    trade_date,
    trade_time,
    bid_price_1, bid_volume_1,
    ask_price_1, ask_volume_1,
    created_at
FROM best5_data 
WHERE id IN (
    SELECT MAX(id) 
    FROM best5_data 
    GROUP BY symbol, trade_date
)
ORDER BY symbol, trade_date DESC, trade_time DESC;

-- 日統計視圖
CREATE VIEW IF NOT EXISTS daily_statistics AS
SELECT 
    symbol,
    trade_date,
    COUNT(*) as tick_count,
    MIN(close_price) as min_price,
    MAX(close_price) as max_price,
    AVG(close_price) as avg_price,
    SUM(volume) as total_volume,
    MIN(trade_time) as first_trade_time,
    MAX(trade_time) as last_trade_time
FROM tick_data 
GROUP BY symbol, trade_date
ORDER BY symbol, trade_date DESC;
