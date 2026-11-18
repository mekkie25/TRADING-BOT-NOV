@echo off
cd /d "%~dp0.."
echo.
echo Did you add a line to docs\DECISIONS.md for what you changed?
echo.

git ls-files | findstr /R "\.env$" >nul
if not errorlevel 1 (
  echo STOP: a .env file is tracked by git. Nothing was pushed.
  echo Send a screenshot to Claude.
  pause
  exit /b
)

set /p MSG=Type a short note about what you changed, then press Enter: 
if "%MSG%"=="" set MSG=update

git add .
git commit -m "%MSG%"
git push

echo.
echo Finished. Check above for any red error text.
pause