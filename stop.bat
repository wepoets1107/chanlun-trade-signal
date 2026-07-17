@echo off
chcp 65001 >nul
echo ═══════════════════════════════════════
echo   停止缠论交易工作台服务器
echo ═══════════════════════════════════════
echo.

netstat -ano | findstr ":8040 " >nul
if %ERRORLEVEL% NEQ 0 (
    echo [信息] 端口 8040 未被占用，服务器未运行。
    pause
    exit /b
)

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8040 "') do (
    taskkill /PID %%a /F >nul 2>nul
)

echo [OK] 服务器已停止。
pause
