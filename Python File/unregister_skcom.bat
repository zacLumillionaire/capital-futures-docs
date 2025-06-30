@echo off
echo ========================================
echo 群益證券API COM元件解除註冊工具
echo ========================================
echo.

REM 檢查管理員權限
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ 已確認管理員權限
) else (
    echo ❌ 需要管理員權限！
    echo 請以「系統管理員身分執行」此批次檔
    pause
    exit /b 1
)

echo.
echo 🔍 檢查SKCOM.dll檔案...

REM 檢查當前目錄的SKCOM.dll
if exist "SKCOM.dll" (
    echo ✅ 找到SKCOM.dll檔案
    set DLL_PATH=%~dp0SKCOM.dll
    goto :unregister
)

REM 檢查常見安裝路徑
if exist "C:\SKCOM\SKCOM.dll" (
    echo ✅ 找到SKCOM.dll於 C:\SKCOM\
    set DLL_PATH=C:\SKCOM\SKCOM.dll
    goto :unregister
)

if exist "C:\Program Files (x86)\Capital\API\SKCOM.dll" (
    echo ✅ 找到SKCOM.dll於 C:\Program Files (x86)\Capital\API\
    set DLL_PATH=C:\Program Files (x86)\Capital\API\SKCOM.dll
    goto :unregister
)

if exist "C:\Program Files\Capital\API\SKCOM.dll" (
    echo ✅ 找到SKCOM.dll於 C:\Program Files\Capital\API\
    set DLL_PATH=C:\Program Files\Capital\API\SKCOM.dll
    goto :unregister
)

echo ❌ 找不到SKCOM.dll檔案
echo 請確認檔案位置
pause
exit /b 1

:unregister
echo.
echo 🔄 正在解除註冊COM元件...
echo 檔案路徑: %DLL_PATH%
echo.

REM 解除註冊COM元件
regsvr32 /u /s "%DLL_PATH%"

if %errorLevel% == 0 (
    echo ✅ COM元件解除註冊成功！
    echo.
    echo 📝 解除註冊資訊:
    echo    - 檔案: %DLL_PATH%
    echo    - 狀態: 已解除註冊
    echo    - 時間: %date% %time%
) else (
    echo ❌ COM元件解除註冊失敗！
    echo 錯誤代碼: %errorLevel%
)

echo.
echo ========================================
pause
