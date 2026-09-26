@echo off
setlocal
cd /d "%~dp0"
if not exist .venv py -3.12 -m venv .venv
if errorlevel 1 goto error
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto error
.venv\Scripts\python.exe scripts\build_data.py
if errorlevel 1 goto error
.venv\Scripts\python.exe -m streamlit run app.py
exit /b %errorlevel%
:error
echo Nao foi possivel iniciar. Confira o erro acima e a instalacao do Python 3.12.
pause
exit /b 1
