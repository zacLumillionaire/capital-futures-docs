@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo 🚀 虛擬報價機快速配置切換
echo ================================
echo 1. 建倉測試 (穩定環境)
echo 2. 建倉追價測試 (快速變動)
echo 3. 移動停利測試 (趨勢環境)
echo 4. 停損測試 (逆向環境)
echo 5. 停損追價測試 (惡化環境)
echo 6. 綜合壓力測試 (極端環境)
echo ================================

set /p choice="請選擇配置 (1-6): "

if "%choice%"=="1" (
    copy /y "config_entry_test.json" "config.json"
    echo ✅ 已切換到建倉測試配置
) else if "%choice%"=="2" (
    copy /y "config_entry_chase.json" "config.json"
    echo ✅ 已切換到建倉追價測試配置
) else if "%choice%"=="3" (
    copy /y "config_trailing_stop.json" "config.json"
    echo ✅ 已切換到移動停利測試配置
) else if "%choice%"=="4" (
    copy /y "config_stop_loss.json" "config.json"
    echo ✅ 已切換到停損測試配置
) else if "%choice%"=="5" (
    copy /y "config_stop_chase.json" "config.json"
    echo ✅ 已切換到停損追價測試配置
) else if "%choice%"=="6" (
    copy /y "config_stress_test.json" "config.json"
    echo ✅ 已切換到綜合壓力測試配置
) else (
    echo ❌ 無效選擇
    goto end
)

echo 💡 配置已更新，請重啟虛擬報價機

:end
pause
