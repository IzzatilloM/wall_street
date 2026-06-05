@echo off
REM ── Wall Street backend — telefon (LAN) uchun ishga tushirish ──
REM Telefon va kompyuter BIR XIL Wi-Fi tarmog'ida bo'lishi shart.
cd /d "%~dp0"
chcp 65001 >nul

echo ================================================================
echo  Kompyuterning LAN IP manzil(lar)i:
ipconfig | findstr /i "IPv4"
echo ----------------------------------------------------------------
echo  Mobil ilovadagi manzil (lib\core\constants.dart -> baseUrl)
echo  shu IP bilan bir xil bo'lsin, masalan:  http://192.168.x.x:8000
echo ================================================================
echo.
echo  Server ishga tushmoqda (http://0.0.0.0:8000). To'xtatish: Ctrl+C
echo.

".venv\Scripts\python.exe" manage.py runserver 0.0.0.0:8000
pause
