-- 緊急修復資料庫約束問題
-- 解決 '>=' not supported between instances of 'NoneType' and 'int' 錯誤

-- 步驟1: 創建修復後的表格
CREATE TABLE position_records_fixed (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    lot_id INTEGER NOT NULL,
    direction TEXT NOT NULL,
    entry_price REAL,
    entry_time TEXT,
    exit_price REAL,
    exit_time TEXT,
    exit_reason TEXT,
    pnl REAL,
    pnl_amount REAL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    rule_config TEXT,
    order_id TEXT,
    api_seq_no TEXT,
    order_status TEXT,
    retry_count INTEGER DEFAULT 0,
    max_slippage_points REAL DEFAULT 5.0,
    last_retry_time TEXT,
    retry_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CHECK(direction IN ('LONG', 'SHORT')),
    CHECK(status IN ('ACTIVE', 'EXITED', 'FAILED', 'PENDING')),
    CHECK(order_status IN ('PENDING', 'FILLED', 'CANCELLED', 'REJECTED') OR order_status IS NULL),
    CHECK(lot_id BETWEEN 1 AND 3),
    CHECK(exit_reason IN ('移動停利', '保護性停損', '初始停損', '手動出場', 'FOK失敗', '下單失敗') OR exit_reason IS NULL),
    CHECK(retry_count IS NULL OR (retry_count >= 0 AND retry_count <= 5)),
    CHECK(max_slippage_points IS NULL OR max_slippage_points > 0)
);

-- 步驟2: 複製現有數據
INSERT INTO position_records_fixed SELECT * FROM position_records;

-- 步驟3: 刪除舊表格
DROP TABLE position_records;

-- 步驟4: 重命名新表格
ALTER TABLE position_records_fixed RENAME TO position_records;

-- 步驟5: 修復現有的 None 值
UPDATE position_records SET retry_count = 0 WHERE retry_count IS NULL;
UPDATE position_records SET max_slippage_points = 5.0 WHERE max_slippage_points IS NULL;
