@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

if not exist ".venv\Scripts\streamlit.exe" (
    echo.
    echo Could not find .venv\Scripts\streamlit.exe
    echo Set up the virtual environment first ^(see README.md^):
    echo   python -m venv .venv
    echo   .venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo Starting Analytics UI...
start "" /B ".venv\Scripts\streamlit.exe" run app.py --server.headless true

set /a tries=0
:waitready
curl.exe -s -o nul -m 2 http://localhost:8501
if errorlevel 1 (
    set /a tries+=1
    if !tries! GEQ 30 (
        echo.
        echo Streamlit did not start in time. Try running this from a
        echo terminal instead to see the underlying error:
        echo   .venv\Scripts\streamlit.exe run app.py
        echo.
        taskkill /IM streamlit.exe /T /F >nul 2>&1
        pause
        exit /b 1
    )
    timeout /t 1 /nobreak >nul
    goto waitready
)

set "EDGE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
if not exist "!EDGE!" set "EDGE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if not exist "!EDGE!" set "EDGE=msedge.exe"

echo Opening browser...
start "" "!EDGE!" --app=http://localhost:8501

set seen=0
:pollwindow
timeout /t 2 /nobreak >nul
tasklist /FI "WINDOWTITLE eq Analytics UI" /FI "IMAGENAME eq msedge.exe" 2>nul | findstr /I "msedge.exe" >nul
if !errorlevel! EQU 0 (
    set seen=1
    goto pollwindow
)
if !seen! EQU 1 (
    goto cleanup
)
goto pollwindow

:cleanup
echo Closing Analytics UI...
taskkill /IM streamlit.exe /T /F >nul 2>&1
exit /b 0
