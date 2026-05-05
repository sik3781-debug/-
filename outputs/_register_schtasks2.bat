@echo off
set PYTHON=C:\Users\Jy\AppData\Local\Programs\Python\Python311\python.exe
set VPY=C:\Users\Jy\consulting-agent\agents\active\run_verifier.py
set DPY=C:\Users\Jy\consulting-agent\agents\active\run_discovery.py
set EPY=C:\Users\Jy\consulting-agent\agents\active\run_executor.py

echo Registering JunggiVerifier...
schtasks /create /tn "JunggiVerifier" /tr "%PYTHON% %VPY%" /sc daily /st 09:00 /f
echo Verifier result: %ERRORLEVEL%

echo Registering JunggiDiscovery...
schtasks /create /tn "JunggiDiscovery" /tr "%PYTHON% %DPY%" /sc daily /st 09:05 /f
echo Discovery result: %ERRORLEVEL%

echo Registering JunggiExecutor...
schtasks /create /tn "JunggiExecutor" /tr "%PYTHON% %EPY%" /sc daily /st 09:10 /f
echo Executor result: %ERRORLEVEL%

echo Done.
