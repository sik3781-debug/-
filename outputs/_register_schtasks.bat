@echo off
chcp 65001 > nul
set PYTHON=C:\Users\Jy\AppData\Local\Programs\Python\Python311\python.exe
set WORKDIR=C:\Users\Jy\consulting-agent\agents\active

echo [1] JunggiVerifier 09:00 등록
schtasks /create /tn "JunggiVerifier" /tr "\"%PYTHON%\" \"%WORKDIR%\run_verifier.py\"" /sc daily /st 09:00 /f /rl highest
echo EXIT: %ERRORLEVEL%

echo.
echo [2] JunggiDiscovery 09:05 등록
schtasks /create /tn "JunggiDiscovery" /tr "\"%PYTHON%\" \"%WORKDIR%\run_discovery.py\"" /sc daily /st 09:05 /f /rl highest
echo EXIT: %ERRORLEVEL%

echo.
echo [3] JunggiExecutor 09:10 등록
schtasks /create /tn "JunggiExecutor" /tr "\"%PYTHON%\" \"%WORKDIR%\run_executor.py\"" /sc daily /st 09:10 /f /rl highest
echo EXIT: %ERRORLEVEL%

echo.
echo === 등록 확인 ===
schtasks /query /tn "JunggiVerifier" /fo CSV
schtasks /query /tn "JunggiDiscovery" /fo CSV
schtasks /query /tn "JunggiExecutor" /fo CSV
