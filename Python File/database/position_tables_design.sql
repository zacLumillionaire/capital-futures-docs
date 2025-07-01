-- =====================================================
-- 部位管理資料庫表格設計
-- 設計原則：在現有SQLite基礎上新增，不修改現有表格
-- 確保向後相容，支援完整的部位生命週期管理
-- =====================================================

-- 1. 部位主表 (positions)
-- 記錄每口部位的基本資訊和當前狀態
CREATE TABLE IF NOT EXISTS positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 基本識別資訊
    session_id TEXT NOT NULL,              -- 交易會話ID (格式: YYYYMMDD_HHMMSS)
    date TEXT NOT NULL,                    -- 交易日期 (YYYY-MM-DD)
    lot_id INTEGER NOT NULL,               -- 口數編號 (1, 2, 3...)
    strategy_name TEXT DEFAULT '開盤區間突破策略',
    
    -- 部位基本資訊
    position_type TEXT NOT NULL,           -- 部位類型: LONG/SHORT
    entry_price REAL NOT NULL,             -- 進場價格
    entry_time TEXT NOT NULL,              -- 進場時間 (HH:MM:SS)
    entry_datetime TEXT NOT NULL,          -- 完整進場時間 (YYYY-MM-DD HH:MM:SS)
    
    -- 區間資訊 (用於計算初始停損)
    range_high REAL NOT NULL,              -- 開盤區間高點
    range_low REAL NOT NULL,               -- 開盤區間低點
    
    -- 當前狀態
    status TEXT NOT NULL DEFAULT 'ACTIVE', -- 部位狀態: ACTIVE/EXITED/CANCELLED
    current_stop_loss REAL,                -- 當前停損價格
    peak_price REAL,                       -- 峰值價格 (多頭最高/空頭最低)
    trailing_activated BOOLEAN DEFAULT FALSE, -- 移動停利是否已啟動
    
    -- 出場資訊
    exit_price REAL,                       -- 出場價格
    exit_time TEXT,                        -- 出場時間 (HH:MM:SS)
    exit_datetime TEXT,                    -- 完整出場時間 (YYYY-MM-DD HH:MM:SS)
    exit_reason TEXT,                      -- 出場原因: TRAILING_STOP/PROTECTIVE_STOP/RANGE_STOP/EOD_CLOSE/MANUAL_CLOSE
    
    -- 損益計算
    realized_pnl REAL DEFAULT 0,           -- 已實現損益 (出場後計算)
    unrealized_pnl REAL DEFAULT 0,         -- 未實現損益 (即時計算)
    
    -- 規則配置 (JSON格式儲存LotRule)
    lot_rule_config TEXT,                  -- 該口的規則配置 (JSON)
    
    -- 時間戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 索引約束
    UNIQUE(session_id, lot_id)             -- 同一會話中口數不重複
);

-- 2. 停損調整記錄表 (stop_loss_adjustments)
-- 記錄每次停損點位調整的詳細資訊
CREATE TABLE IF NOT EXISTS stop_loss_adjustments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 關聯資訊
    position_id INTEGER NOT NULL,          -- 關聯的部位ID
    session_id TEXT NOT NULL,              -- 交易會話ID
    lot_id INTEGER NOT NULL,               -- 口數編號
    
    -- 調整資訊
    old_stop_loss REAL,                    -- 調整前停損價格
    new_stop_loss REAL NOT NULL,           -- 調整後停損價格
    adjustment_reason TEXT NOT NULL,       -- 調整原因: INITIAL/TRAILING/PROTECTIVE/MANUAL
    
    -- 觸發資訊
    trigger_price REAL,                    -- 觸發調整的價格
    trigger_time TEXT NOT NULL,            -- 觸發時間 (HH:MM:SS)
    trigger_datetime TEXT NOT NULL,        -- 完整觸發時間 (YYYY-MM-DD HH:MM:SS)
    
    -- 移動停利相關
    peak_price_at_adjustment REAL,         -- 調整時的峰值價格
    trailing_activation_points REAL,       -- 移動停利啟動點數
    trailing_pullback_ratio REAL,          -- 回檔比例
    
    -- 保護性停損相關
    cumulative_pnl_before REAL,            -- 調整前累積損益
    protection_multiplier REAL,            -- 保護倍數
    
    -- 備註資訊
    notes TEXT,                            -- 調整備註
    
    -- 時間戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 外鍵約束
    FOREIGN KEY (position_id) REFERENCES positions(id) ON DELETE CASCADE
);

-- 3. 部位快照表 (position_snapshots)
-- 記錄部位狀態的定期快照，用於分析和恢復
CREATE TABLE IF NOT EXISTS position_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 關聯資訊
    position_id INTEGER NOT NULL,          -- 關聯的部位ID
    session_id TEXT NOT NULL,              -- 交易會話ID
    lot_id INTEGER NOT NULL,               -- 口數編號
    
    -- 快照時間
    snapshot_time TEXT NOT NULL,           -- 快照時間 (HH:MM:SS)
    snapshot_datetime TEXT NOT NULL,       -- 完整快照時間 (YYYY-MM-DD HH:MM:SS)
    
    -- 價格資訊
    current_price REAL NOT NULL,           -- 當時價格
    peak_price REAL NOT NULL,              -- 當時峰值價格
    stop_loss_price REAL,                  -- 當時停損價格
    
    -- 狀態資訊
    status TEXT NOT NULL,                  -- 當時狀態
    trailing_activated BOOLEAN,            -- 移動停利是否已啟動
    unrealized_pnl REAL,                   -- 當時未實現損益
    
    -- 時間戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 外鍵約束
    FOREIGN KEY (position_id) REFERENCES positions(id) ON DELETE CASCADE
);

-- 4. 交易會話表 (trading_sessions)
-- 記錄每個交易會話的基本資訊
CREATE TABLE IF NOT EXISTS trading_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 會話識別
    session_id TEXT NOT NULL UNIQUE,       -- 會話ID (YYYYMMDD_HHMMSS)
    date TEXT NOT NULL,                    -- 交易日期
    
    -- 策略資訊
    strategy_name TEXT NOT NULL,           -- 策略名稱
    strategy_config TEXT,                  -- 策略配置 (JSON)
    total_lots INTEGER NOT NULL,           -- 總口數
    
    -- 區間資訊
    range_high REAL,                       -- 開盤區間高點
    range_low REAL,                        -- 開盤區間低點
    range_calculated_time TEXT,            -- 區間計算完成時間
    
    -- 信號資訊
    signal_type TEXT,                      -- 信號類型: LONG/SHORT/NONE
    signal_price REAL,                     -- 信號價格
    signal_time TEXT,                      -- 信號時間
    
    -- 會話狀態
    status TEXT NOT NULL DEFAULT 'ACTIVE', -- 會話狀態: ACTIVE/COMPLETED/CANCELLED
    
    -- 統計資訊
    total_realized_pnl REAL DEFAULT 0,     -- 總已實現損益
    total_unrealized_pnl REAL DEFAULT 0,   -- 總未實現損益
    active_positions INTEGER DEFAULT 0,    -- 活躍部位數
    
    -- 時間戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 索引設計 (提升查詢效能)
-- =====================================================

-- positions表索引
CREATE INDEX IF NOT EXISTS idx_positions_session_date ON positions(session_id, date);
CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status);
CREATE INDEX IF NOT EXISTS idx_positions_date_status ON positions(date, status);
CREATE INDEX IF NOT EXISTS idx_positions_lot_id ON positions(lot_id);

-- stop_loss_adjustments表索引
CREATE INDEX IF NOT EXISTS idx_stop_loss_position_id ON stop_loss_adjustments(position_id);
CREATE INDEX IF NOT EXISTS idx_stop_loss_session_lot ON stop_loss_adjustments(session_id, lot_id);
CREATE INDEX IF NOT EXISTS idx_stop_loss_reason ON stop_loss_adjustments(adjustment_reason);
CREATE INDEX IF NOT EXISTS idx_stop_loss_datetime ON stop_loss_adjustments(trigger_datetime);

-- position_snapshots表索引
CREATE INDEX IF NOT EXISTS idx_snapshots_position_id ON position_snapshots(position_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_datetime ON position_snapshots(snapshot_datetime);

-- trading_sessions表索引
CREATE INDEX IF NOT EXISTS idx_sessions_date ON trading_sessions(date);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON trading_sessions(status);

-- =====================================================
-- 觸發器設計 (自動維護資料一致性)
-- =====================================================

-- 自動更新positions表的updated_at欄位
CREATE TRIGGER IF NOT EXISTS update_positions_timestamp 
    AFTER UPDATE ON positions
    FOR EACH ROW
BEGIN
    UPDATE positions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- 自動更新trading_sessions表的updated_at欄位
CREATE TRIGGER IF NOT EXISTS update_sessions_timestamp 
    AFTER UPDATE ON trading_sessions
    FOR EACH ROW
BEGIN
    UPDATE trading_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- 部位狀態變更時自動更新會話統計
CREATE TRIGGER IF NOT EXISTS update_session_stats_on_position_change
    AFTER UPDATE OF status, realized_pnl ON positions
    FOR EACH ROW
BEGIN
    UPDATE trading_sessions 
    SET 
        total_realized_pnl = (
            SELECT COALESCE(SUM(realized_pnl), 0) 
            FROM positions 
            WHERE session_id = NEW.session_id AND status = 'EXITED'
        ),
        active_positions = (
            SELECT COUNT(*) 
            FROM positions 
            WHERE session_id = NEW.session_id AND status = 'ACTIVE'
        )
    WHERE session_id = NEW.session_id;
END;
