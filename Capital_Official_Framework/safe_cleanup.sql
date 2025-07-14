-- 安全清理SQL腳本 - 避免表不存在的錯誤
-- 使用條件檢查來避免錯誤

-- 1. 檢查清理前狀態
.print "=== 清理前狀態 ==="
.print "檢查活躍部位..."
SELECT CASE 
    WHEN EXISTS(SELECT name FROM sqlite_master WHERE type='table' AND name='position_records') 
    THEN 'Active Positions: ' || (SELECT COUNT(*) FROM position_records WHERE status = 'ACTIVE')
    ELSE 'position_records表不存在'
END;

.print "檢查風險管理狀態..."
SELECT CASE 
    WHEN EXISTS(SELECT name FROM sqlite_master WHERE type='table' AND name='risk_management_states') 
    THEN 'Risk States: ' || (SELECT COUNT(*) FROM risk_management_states)
    ELSE 'risk_management_states表不存在'
END;

.print "檢查今日策略組..."
SELECT CASE 
    WHEN EXISTS(SELECT name FROM sqlite_master WHERE type='table' AND name='strategy_groups') 
    THEN 'Today Groups: ' || (SELECT COUNT(*) FROM strategy_groups WHERE date = date('now'))
    ELSE 'strategy_groups表不存在'
END;

-- 2. 開始清理
.print ""
.print "=== 開始清理 ==="

-- 清理活躍部位（如果表存在）
DELETE FROM position_records WHERE status = 'ACTIVE' AND EXISTS(
    SELECT name FROM sqlite_master WHERE type='table' AND name='position_records'
);

-- 清理風險管理狀態（如果表存在）
DELETE FROM risk_management_states WHERE EXISTS(
    SELECT name FROM sqlite_master WHERE type='table' AND name='risk_management_states'
);

-- 清理今日策略組（如果表存在）
DELETE FROM strategy_groups WHERE date = date('now') AND EXISTS(
    SELECT name FROM sqlite_master WHERE type='table' AND name='strategy_groups'
);

-- 3. 檢查清理後狀態
.print ""
.print "=== 清理後狀態 ==="
.print "檢查活躍部位..."
SELECT CASE 
    WHEN EXISTS(SELECT name FROM sqlite_master WHERE type='table' AND name='position_records') 
    THEN 'Active Positions: ' || (SELECT COUNT(*) FROM position_records WHERE status = 'ACTIVE')
    ELSE 'position_records表不存在'
END;

.print "檢查風險管理狀態..."
SELECT CASE 
    WHEN EXISTS(SELECT name FROM sqlite_master WHERE type='table' AND name='risk_management_states') 
    THEN 'Risk States: ' || (SELECT COUNT(*) FROM risk_management_states)
    ELSE 'risk_management_states表不存在'
END;

.print "檢查今日策略組..."
SELECT CASE 
    WHEN EXISTS(SELECT name FROM sqlite_master WHERE type='table' AND name='strategy_groups') 
    THEN 'Today Groups: ' || (SELECT COUNT(*) FROM strategy_groups WHERE date = date('now'))
    ELSE 'strategy_groups表不存在'
END;

-- 4. 完成信息
.print ""
.print "=== 清理完成 ==="
.print "建議重啟 simple_integrated.py 程序"
.print "現在可以重新測試策略"
