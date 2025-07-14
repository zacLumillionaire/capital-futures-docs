-- 緊急清理SQL腳本
-- 用於直接清理數據庫中的測試數據

-- 1. 檢查當前狀態
SELECT '=== 清理前狀態 ===' as status;
SELECT 'Active Positions: ' || COUNT(*) FROM position_records WHERE status = 'ACTIVE';
SELECT 'Risk States: ' || COUNT(*) FROM risk_management_states;
SELECT 'Today Groups: ' || COUNT(*) FROM strategy_groups WHERE date = date('now');

-- 2. 清理活躍部位
DELETE FROM position_records WHERE status = 'ACTIVE';

-- 3. 清理風險管理狀態
DELETE FROM risk_management_states;

-- 4. 清理今日策略組
DELETE FROM strategy_groups WHERE date = date('now');

-- 5. 清理舊報價數據（如果表存在）
-- 注意：此表可能不存在，如果執行失敗請忽略
-- DELETE FROM real_time_quotes WHERE timestamp < datetime('now', '-1 hour');

-- 6. 檢查清理後狀態
SELECT '=== 清理後狀態 ===' as status;
SELECT 'Active Positions: ' || COUNT(*) FROM position_records WHERE status = 'ACTIVE';
SELECT 'Risk States: ' || COUNT(*) FROM risk_management_states;
SELECT 'Today Groups: ' || COUNT(*) FROM strategy_groups WHERE date = date('now');

-- 7. 顯示完成信息
SELECT '=== 清理完成 ===' as status;
SELECT '建議重啟 simple_integrated.py 程序' as recommendation;
