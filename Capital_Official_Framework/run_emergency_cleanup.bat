@echo off
echo 🧹 緊急清理腳本
echo ================

echo 🔍 檢查數據庫檔案...
if not exist "multi_group_strategy.db" (
    echo ❌ 資料庫檔案不存在
    pause
    exit /b 1
)

echo ✅ 資料庫檔案存在

echo.
echo ⚠️ 將清理以下數據:
echo    - 所有活躍部位
echo    - 風險管理狀態  
echo    - 今日策略組
echo    - 舊報價數據
echo.

set /p confirm="確定要執行清理嗎？(y/N): "
if /i not "%confirm%"=="y" (
    echo ❌ 取消清理
    pause
    exit /b 0
)

echo.
echo 🚀 執行清理...

sqlite3 multi_group_strategy.db < emergency_cleanup.sql

if %errorlevel% equ 0 (
    echo.
    echo ✅ 清理完成！
    echo 💡 建議重啟 simple_integrated.py 程序
    echo 💡 現在可以重新測試策略
) else (
    echo.
    echo ❌ 清理失敗，錯誤代碼: %errorlevel%
)

echo.
pause
