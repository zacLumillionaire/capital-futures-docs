@echo off
echo 🧹 安全清理腳本
echo ================

echo 🔍 檢查數據庫檔案...
if not exist "multi_group_strategy.db" (
    echo ❌ 資料庫檔案不存在
    pause
    exit /b 1
)

echo ✅ 資料庫檔案存在

echo.
echo 🚀 執行安全清理...
echo.

sqlite3 multi_group_strategy.db < safe_cleanup.sql

if %errorlevel% equ 0 (
    echo.
    echo ✅ 安全清理完成！
    echo 💡 建議重啟 simple_integrated.py 程序
    echo 💡 現在可以重新測試策略
    echo.
    echo 🧠 內存狀態清理提示:
    echo    📋 建議重啟程序以清理內存狀態
    echo    📋 或者在程序中調用:
    echo       - global_exit_manager.clear_all_exits()
    echo       - optimized_risk_manager.clear_all_caches()
) else (
    echo.
    echo ❌ 清理失敗，錯誤代碼: %errorlevel%
)

echo.
pause
