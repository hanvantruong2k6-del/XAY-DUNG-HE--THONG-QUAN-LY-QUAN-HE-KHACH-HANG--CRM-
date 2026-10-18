@echo off
chcp 65001 >nul
title CRM Tunnel

REM ===== THONG SO =====
set CF_DIR=F:\XAY-DUNG-HE--THONG-QUAN-LY-QUAN-HE-KHACH-HANG--CRM-\cloudflared
set PORT=8080
REM ====================

set CF=
for /r "%CF_DIR%" %%f in (cloudflared*.exe) do (
  if not defined CF set CF=%%f
)

if not defined CF (
  echo [LOI] Khong tim thay file cloudflared*.exe trong %CF_DIR%
  echo Hay mo thu muc do va kiem tra da co file .exe chua.
  pause
  exit /b 1
)

echo ============================================
echo  Dang dung: %CF%
echo  Dang bat tunnel cho http://localhost:%PORT%
echo  Cho vai giay, tim dong co dang:
echo    https://ten-ngau-nhien.trycloudflare.com
echo  Copy link do gui cho nguoi can xem.
echo  Chay chay_server.bat TRUOC khi bat tunnel.
echo  Tat tunnel: dong cua so nay hoac nhan Ctrl+C
echo ============================================
echo.

"%CF%" tunnel --url http://localhost:%PORT%

echo.
echo Tunnel da dung.
pause
