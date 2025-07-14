# PowerShell 快速清理腳本
# 用於清理測試環境數據

Write-Host "🧹 PowerShell 快速清理腳本" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green

# 檢查數據庫文件
$dbPath = "multi_group_strategy.db"
if (-not (Test-Path $dbPath)) {
    Write-Host "❌ 資料庫檔案不存在" -ForegroundColor Red
    Read-Host "按任意鍵退出"
    exit 1
}

Write-Host "✅ 資料庫檔案存在" -ForegroundColor Green

# 檢查當前狀態
Write-Host "`n🔍 檢查當前狀態..." -ForegroundColor Yellow

try {
    # 使用 sqlite3 命令檢查狀態
    $activePositions = & sqlite3 $dbPath "SELECT COUNT(*) FROM position_records WHERE status = 'ACTIVE';"
    $riskStates = & sqlite3 $dbPath "SELECT COUNT(*) FROM risk_management_states;"
    $todayGroups = & sqlite3 $dbPath "SELECT COUNT(*) FROM strategy_groups WHERE date = date('now');"
    
    Write-Host "   - 活躍部位: $activePositions" -ForegroundColor Cyan
    Write-Host "   - 風險管理狀態: $riskStates" -ForegroundColor Cyan
    Write-Host "   - 今日策略組: $todayGroups" -ForegroundColor Cyan
    
    $totalItems = [int]$activePositions + [int]$riskStates + [int]$todayGroups
    
    if ($totalItems -eq 0) {
        Write-Host "✅ 環境已經是乾淨狀態，無需清理" -ForegroundColor Green
        Read-Host "按任意鍵退出"
        exit 0
    }
    
    Write-Host "`n⚠️ 檢測到 $totalItems 項需要清理的數據" -ForegroundColor Yellow
    Write-Host "🔧 將執行以下清理操作:" -ForegroundColor Yellow
    Write-Host "   - 清理所有活躍部位" -ForegroundColor White
    Write-Host "   - 清理風險管理狀態" -ForegroundColor White
    Write-Host "   - 清理今日策略組" -ForegroundColor White
    Write-Host "   - 清理舊報價數據" -ForegroundColor White
    
    $confirm = Read-Host "`n確定要執行清理嗎？(y/N)"
    if ($confirm -ne "y" -and $confirm -ne "Y") {
        Write-Host "❌ 取消清理" -ForegroundColor Red
        Read-Host "按任意鍵退出"
        exit 0
    }
    
    Write-Host "`n🚀 開始執行清理..." -ForegroundColor Green
    
    # 執行清理
    & sqlite3 $dbPath "DELETE FROM position_records WHERE status = 'ACTIVE';"
    Write-Host "   ✅ 清理活躍部位完成" -ForegroundColor Green
    
    & sqlite3 $dbPath "DELETE FROM risk_management_states;"
    Write-Host "   ✅ 清理風險管理狀態完成" -ForegroundColor Green
    
    & sqlite3 $dbPath "DELETE FROM strategy_groups WHERE date = date('now');"
    Write-Host "   ✅ 清理今日策略組完成" -ForegroundColor Green
    
    # 清理舊報價數據（檢查表是否存在）
    try {
        $tableExists = & sqlite3 $dbPath "SELECT name FROM sqlite_master WHERE type='table' AND name='real_time_quotes';"
        if ($tableExists) {
            & sqlite3 $dbPath "DELETE FROM real_time_quotes WHERE timestamp < datetime('now', '-1 hour');"
            Write-Host "   ✅ 清理舊報價數據完成" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️ real_time_quotes表不存在，跳過清理" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "   ⚠️ 清理報價數據失敗: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    # 驗證清理結果
    Write-Host "`n📊 清理後狀態:" -ForegroundColor Yellow
    $finalActive = & sqlite3 $dbPath "SELECT COUNT(*) FROM position_records WHERE status = 'ACTIVE';"
    $finalRisk = & sqlite3 $dbPath "SELECT COUNT(*) FROM risk_management_states;"
    $finalGroups = & sqlite3 $dbPath "SELECT COUNT(*) FROM strategy_groups WHERE date = date('now');"
    
    Write-Host "   - 活躍部位: $finalActive" -ForegroundColor Cyan
    Write-Host "   - 風險管理狀態: $finalRisk" -ForegroundColor Cyan
    Write-Host "   - 今日策略組: $finalGroups" -ForegroundColor Cyan
    
    Write-Host "`n🎉 清理完成！" -ForegroundColor Green
    Write-Host "💡 建議重啟 simple_integrated.py 程序以確保內存狀態也被清除" -ForegroundColor Yellow
    Write-Host "💡 現在可以重新測試策略，環境已完全重置" -ForegroundColor Yellow
    
    Write-Host "`n🧠 內存狀態清理提示:" -ForegroundColor Yellow
    Write-Host "   📋 建議重啟程序以清理內存狀態" -ForegroundColor White
    Write-Host "   📋 或者在程序中調用:" -ForegroundColor White
    Write-Host "      - global_exit_manager.clear_all_exits()" -ForegroundColor Gray
    Write-Host "      - optimized_risk_manager.clear_all_caches()" -ForegroundColor Gray
    
} catch {
    Write-Host "❌ 清理失敗: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.Exception.StackTrace -ForegroundColor Red
}

Read-Host "`n按任意鍵退出"
