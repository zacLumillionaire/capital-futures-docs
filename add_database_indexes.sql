-- 🚀 立即執行：添加資料庫索引提升查詢性能
-- 執行方式：在資料庫管理工具中執行，或通過Python腳本執行

-- 1. position_records 表索引
-- 針對平倉查詢優化：WHERE pr.id = ? AND pr.status = 'ACTIVE'
CREATE INDEX IF NOT EXISTS idx_position_records_id_status 
ON position_records(id, status);

-- 針對組別查詢優化：WHERE pr.group_id = ? AND pr.status = 'ACTIVE'
CREATE INDEX IF NOT EXISTS idx_position_records_group_status 
ON position_records(group_id, status);

-- 針對組別+口數查詢優化：ORDER BY pr.group_id, pr.lot_id
CREATE INDEX IF NOT EXISTS idx_position_records_group_lot 
ON position_records(group_id, lot_id);

-- 2. strategy_groups 表索引
-- 針對JOIN查詢優化：WHERE sg.group_id = ? AND sg.date = ?
CREATE INDEX IF NOT EXISTS idx_strategy_groups_group_date 
ON strategy_groups(group_id, date);

-- 針對日期查詢優化：WHERE date = ? ORDER BY id DESC
CREATE INDEX IF NOT EXISTS idx_strategy_groups_date_id 
ON strategy_groups(date, id DESC);

-- 3. 複合索引（最重要）
-- 針對完整JOIN查詢優化
CREATE INDEX IF NOT EXISTS idx_position_records_complete 
ON position_records(id, status, group_id);

-- 檢查索引創建結果
-- 執行後可用以下查詢驗證：
-- SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='position_records';
-- SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='strategy_groups';
