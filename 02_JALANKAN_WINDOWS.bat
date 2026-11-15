@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Jalankan 01_INSTALL_WINDOWS.bat terlebih dahulu.
  pause
  exit /b 1
)
echo Aplikasi akan terbuka di browser. Jangan tutup jendela ini saat digunakan.
echo Untuk berhenti, tekan Ctrl+C pada jendela ini.
".venv\Scripts\python.exe" -m streamlit run app.py --server.address localhost --server.showEmailPrompt false --browser.gatherUsageStats false
if errorlevel 1 pause
