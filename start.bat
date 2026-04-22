@echo off
cd /d "%~dp0"

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

python.exe -m pip install -q --upgrade pip
pip install -q -r requirements.txt

:loop
echo.
python -c "print('\033[93mPaste your Ultimate Guitar link here (or type exit to quit):\033[0m')"
set /p URL="> "
if /i "%URL%"=="exit" goto end
if "%URL%"=="" goto loop
python app.py "%URL%"
goto loop

:end
deactivate
