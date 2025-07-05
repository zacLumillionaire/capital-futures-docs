-- =====================================================
-- PostgreSQL 資料表建立腳本
-- Full Tick 逐筆資料表 和 Best5 五檔報價資料表
-- =====================================================

-- 建立逐筆資料表 (tick_prices)
-- =====================================================
DROP TABLE IF EXISTS tick_prices CASCADE;

CREATE TABLE tick_prices (
    trade_datetime timestamp without time zone NOT NULL,
    symbol varchar(20) NOT NULL,
    bid_price numeric(10,2),
    ask_price numeric(10,2),
    close_price numeric(10,2) NOT NULL,
    volume integer NOT NULL,
    trade_time_ms integer DEFAULT 0,
    market_no integer DEFAULT 0,
    simulate_flag integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    
    -- 主鍵約束
    CONSTRAINT pk_tick_prices PRIMARY KEY (trade_datetime, symbol)
);

-- 建立逐筆資料表索引
CREATE INDEX idx_tick_prices_symbol ON tick_prices(symbol);
CREATE INDEX idx_tick_prices_datetime ON tick_prices(trade_datetime);
CREATE INDEX idx_tick_prices_symbol_datetime ON tick_prices(symbol, trade_datetime);

-- 逐筆資料表註解
COMMENT ON TABLE tick_prices IS '期貨逐筆交易資料表';
COMMENT ON COLUMN tick_prices.trade_datetime IS '交易時間 (精確到秒或毫秒)';
COMMENT ON COLUMN tick_prices.symbol IS '商品代碼 (如: MTX00, TM0000)';
COMMENT ON COLUMN tick_prices.bid_price IS '買價';
COMMENT ON COLUMN tick_prices.ask_price IS '賣價';
COMMENT ON COLUMN tick_prices.close_price IS '成交價';
COMMENT ON COLUMN tick_prices.volume IS '成交量';
COMMENT ON COLUMN tick_prices.trade_time_ms IS '毫秒時間戳';
COMMENT ON COLUMN tick_prices.market_no IS '市場別代號';
COMMENT ON COLUMN tick_prices.simulate_flag IS '揭示類型 (0:一般, 1:試算)';

-- =====================================================
-- 建立五檔報價資料表 (best5_prices)
-- =====================================================
DROP TABLE IF EXISTS best5_prices CASCADE;

CREATE TABLE best5_prices (
    trade_datetime timestamp without time zone NOT NULL,
    symbol varchar(20) NOT NULL,
    
    -- 五檔買價買量
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
    
    -- 五檔賣價賣量
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
    
    -- 延伸買賣
    extend_bid numeric(10,2),
    extend_bid_qty integer DEFAULT 0,
    extend_ask numeric(10,2),
    extend_ask_qty integer DEFAULT 0,
    
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    
    -- 主鍵約束
    CONSTRAINT pk_best5_prices PRIMARY KEY (trade_datetime, symbol)
);

-- 建立五檔資料表索引
CREATE INDEX idx_best5_prices_symbol ON best5_prices(symbol);
CREATE INDEX idx_best5_prices_datetime ON best5_prices(trade_datetime);
CREATE INDEX idx_best5_prices_symbol_datetime ON best5_prices(symbol, trade_datetime);

-- 五檔資料表註解
COMMENT ON TABLE best5_prices IS '期貨五檔報價資料表';
COMMENT ON COLUMN best5_prices.trade_datetime IS '報價時間';
COMMENT ON COLUMN best5_prices.symbol IS '商品代碼 (如: MTX00, TM0000)';
COMMENT ON COLUMN best5_prices.bid_price_1 IS '買一價';
COMMENT ON COLUMN best5_prices.bid_volume_1 IS '買一量';
COMMENT ON COLUMN best5_prices.bid_price_2 IS '買二價';
COMMENT ON COLUMN best5_prices.bid_volume_2 IS '買二量';
COMMENT ON COLUMN best5_prices.bid_price_3 IS '買三價';
COMMENT ON COLUMN best5_prices.bid_volume_3 IS '買三量';
COMMENT ON COLUMN best5_prices.bid_price_4 IS '買四價';
COMMENT ON COLUMN best5_prices.bid_volume_4 IS '買四量';
COMMENT ON COLUMN best5_prices.bid_price_5 IS '買五價';
COMMENT ON COLUMN best5_prices.bid_volume_5 IS '買五量';
COMMENT ON COLUMN best5_prices.ask_price_1 IS '賣一價';
COMMENT ON COLUMN best5_prices.ask_volume_1 IS '賣一量';
COMMENT ON COLUMN best5_prices.ask_price_2 IS '賣二價';
COMMENT ON COLUMN best5_prices.ask_volume_2 IS '賣二量';
COMMENT ON COLUMN best5_prices.ask_price_3 IS '賣三價';
COMMENT ON COLUMN best5_prices.ask_volume_3 IS '賣三量';
COMMENT ON COLUMN best5_prices.ask_price_4 IS '賣四價';
COMMENT ON COLUMN best5_prices.ask_volume_4 IS '賣四量';
COMMENT ON COLUMN best5_prices.ask_price_5 IS '賣五價';
COMMENT ON COLUMN best5_prices.ask_volume_5 IS '賣五量';
COMMENT ON COLUMN best5_prices.extend_bid IS '延伸買價';
COMMENT ON COLUMN best5_prices.extend_bid_qty IS '延伸買量';
COMMENT ON COLUMN best5_prices.extend_ask IS '延伸賣價';
COMMENT ON COLUMN best5_prices.extend_ask_qty IS '延伸賣量';

-- =====================================================
-- 建立視圖 (Views) - 方便查詢
-- =====================================================

-- 最新逐筆資料視圖
CREATE OR REPLACE VIEW v_latest_tick_prices AS
SELECT 
    symbol,
    trade_datetime,
    bid_price,
    ask_price,
    close_price,
    volume,
    trade_time_ms
FROM tick_prices t1
WHERE trade_datetime = (
    SELECT MAX(trade_datetime) 
    FROM tick_prices t2 
    WHERE t2.symbol = t1.symbol
)
ORDER BY symbol, trade_datetime DESC;

-- 最新五檔報價視圖
CREATE OR REPLACE VIEW v_latest_best5_prices AS
SELECT 
    symbol,
    trade_datetime,
    bid_price_1, bid_volume_1,
    bid_price_2, bid_volume_2,
    bid_price_3, bid_volume_3,
    ask_price_1, ask_volume_1,
    ask_price_2, ask_volume_2,
    ask_price_3, ask_volume_3
FROM best5_prices b1
WHERE trade_datetime = (
    SELECT MAX(trade_datetime) 
    FROM best5_prices b2 
    WHERE b2.symbol = b1.symbol
)
ORDER BY symbol, trade_datetime DESC;

-- 資料統計視圖
CREATE OR REPLACE VIEW v_data_statistics AS
SELECT 
    'tick_prices' as table_name,
    COUNT(*) as record_count,
    COUNT(DISTINCT symbol) as symbol_count,
    MIN(trade_datetime) as earliest_datetime,
    MAX(trade_datetime) as latest_datetime
FROM tick_prices
UNION ALL
SELECT 
    'best5_prices' as table_name,
    COUNT(*) as record_count,
    COUNT(DISTINCT symbol) as symbol_count,
    MIN(trade_datetime) as earliest_datetime,
    MAX(trade_datetime) as latest_datetime
FROM best5_prices
UNION ALL
SELECT 
    'stock_prices' as table_name,
    COUNT(*) as record_count,
    1 as symbol_count,
    MIN(trade_datetime) as earliest_datetime,
    MAX(trade_datetime) as latest_datetime
FROM stock_prices;

-- =====================================================
-- 權限設定 (如果需要)
-- =====================================================

-- 如果有特定使用者，可以設定權限
-- GRANT SELECT, INSERT, UPDATE, DELETE ON tick_prices TO your_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON best5_prices TO your_user;
-- GRANT SELECT ON v_latest_tick_prices TO your_user;
-- GRANT SELECT ON v_latest_best5_prices TO your_user;
-- GRANT SELECT ON v_data_statistics TO your_user;

-- =====================================================
-- 測試資料插入 (可選)
-- =====================================================

-- 插入測試逐筆資料
INSERT INTO tick_prices (
    trade_datetime, symbol, bid_price, ask_price, close_price, volume
) VALUES 
    ('2025-01-06 08:46:00', 'MTX00', 22950.00, 22955.00, 22952.00, 5),
    ('2025-01-06 08:47:00', 'MTX00', 22951.00, 22956.00, 22953.00, 8)
ON CONFLICT (trade_datetime, symbol) DO NOTHING;

-- 插入測試五檔資料
INSERT INTO best5_prices (
    trade_datetime, symbol, 
    bid_price_1, bid_volume_1, bid_price_2, bid_volume_2,
    ask_price_1, ask_volume_1, ask_price_2, ask_volume_2
) VALUES 
    ('2025-01-06 08:46:00', 'MTX00', 
     22950.00, 10, 22949.00, 5,
     22951.00, 8, 22952.00, 12),
    ('2025-01-06 08:47:00', 'MTX00', 
     22951.00, 15, 22950.00, 7,
     22952.00, 6, 22953.00, 10)
ON CONFLICT (trade_datetime, symbol) DO NOTHING;

-- =====================================================
-- 驗證建立結果
-- =====================================================

-- 檢查表格是否建立成功
SELECT 
    table_name,
    table_type,
    table_comment
FROM information_schema.tables 
WHERE table_name IN ('tick_prices', 'best5_prices')
ORDER BY table_name;

-- 檢查索引是否建立成功
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename IN ('tick_prices', 'best5_prices')
ORDER BY tablename, indexname;

-- 檢查測試資料
SELECT 'tick_prices' as table_name, COUNT(*) as count FROM tick_prices
UNION ALL
SELECT 'best5_prices' as table_name, COUNT(*) as count FROM best5_prices;

-- 顯示資料統計
SELECT * FROM v_data_statistics ORDER BY table_name;

-- =====================================================
-- 完成訊息
-- =====================================================
SELECT 'PostgreSQL Full Tick 和 Best5 資料表建立完成！' as message;
