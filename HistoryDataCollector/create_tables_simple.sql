-- =====================================================
-- PostgreSQL 簡化版資料表建立腳本
-- Full Tick 逐筆資料表 和 Best5 五檔報價資料表
-- =====================================================

-- 建立逐筆資料表 (tick_prices)
CREATE TABLE IF NOT EXISTS tick_prices (
    trade_datetime timestamp without time zone NOT NULL,
    symbol varchar(20) NOT NULL,
    bid_price numeric(10,2),
    ask_price numeric(10,2),
    close_price numeric(10,2) NOT NULL,
    volume integer NOT NULL,
    trade_time_ms integer DEFAULT 0,
    market_no integer DEFAULT 0,
    simulate_flag integer DEFAULT 0,
    CONSTRAINT pk_tick_prices PRIMARY KEY (trade_datetime, symbol)
);

-- 建立五檔報價資料表 (best5_prices)
CREATE TABLE IF NOT EXISTS best5_prices (
    trade_datetime timestamp without time zone NOT NULL,
    symbol varchar(20) NOT NULL,
    bid_price_1 numeric(10,2),
    bid_volume_1 integer DEFAULT 0,
    bid_price_2 numeric(10,2),
    bid_volume_2 integer DEFAULT 0,
    bid_price_3 numeric(10,2),
    bid_volume_3 integer DEFAULT 0,
    bid_price_4 numeric(10,2),
    bid_volume_4 integer DEFAULT 0,
    bid_price_5 numeric(10,2),
    bid_volume_5 integer DEFAULT 0,
    ask_price_1 numeric(10,2),
    ask_volume_1 integer DEFAULT 0,
    ask_price_2 numeric(10,2),
    ask_volume_2 integer DEFAULT 0,
    ask_price_3 numeric(10,2),
    ask_volume_3 integer DEFAULT 0,
    ask_price_4 numeric(10,2),
    ask_volume_4 integer DEFAULT 0,
    ask_price_5 numeric(10,2),
    ask_volume_5 integer DEFAULT 0,
    extend_bid numeric(10,2),
    extend_bid_qty integer DEFAULT 0,
    extend_ask numeric(10,2),
    extend_ask_qty integer DEFAULT 0,
    CONSTRAINT pk_best5_prices PRIMARY KEY (trade_datetime, symbol)
);

-- 建立索引以提升查詢效能
CREATE INDEX IF NOT EXISTS idx_tick_prices_symbol ON tick_prices(symbol);
CREATE INDEX IF NOT EXISTS idx_tick_prices_datetime ON tick_prices(trade_datetime);
CREATE INDEX IF NOT EXISTS idx_best5_prices_symbol ON best5_prices(symbol);
CREATE INDEX IF NOT EXISTS idx_best5_prices_datetime ON best5_prices(trade_datetime);

-- 檢查建立結果
SELECT 'tick_prices 表格建立完成' as message
WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'tick_prices');

SELECT 'best5_prices 表格建立完成' as message
WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'best5_prices');
