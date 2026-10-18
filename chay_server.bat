@echo off
chcp 65001 >nul
title CRM Server

REM ===== THONG SO =====
set MSYS2_DIR=C:\msys64
set PROJECT_DIR=/f/XAY-DUNG-HE--THONG-QUAN-LY-QUAN-HE-KHACH-HANG--CRM-/crm
set START_CMD=./crm.exe
set PORT=8080
REM ====================================================

set IP=
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
  if not defined IP set IP=%%a
)
set IP=%IP: =%

echo ============================================
echo  CRM dang khoi dong...
echo  May server mo:     http://localhost:%PORT%
echo  Cung mang LAN:     http://%IP%:%PORT%
echo  (hoac http://%COMPUTERNAME%:%PORT%)
echo  Tat server: dong cua so nay hoac nhan Ctrl+C
echo ============================================
echo.

if not exist "%MSYS2_DIR%\msys2_shell.cmd" (
  echo [LOI] Khong tim thay MSYS2 tai %MSYS2_DIR%
  pause
  exit /b 1
)

call "%MSYS2_DIR%\msys2_shell.cmd" -ucrt64 -defterm -no-start -here -c "cd '%PROJECT_DIR%' && %START_CMD%"

echo.
echo Server da dung.
pause
