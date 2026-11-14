@echo off
setlocal
cd /d "%~dp0"
echo Memasang MANGROVE-FIT. Internet diperlukan pada pemasangan pertama.
set "MF_PY=py -3.12"
%MF_PY% --version >nul 2>&1
if errorlevel 1 (
  set "MF_PY=py -3.11"
)
%MF_PY% --version >nul 2>&1
if errorlevel 1 (
  set "MF_PY=python"
)
%MF_PY% -c "import sys; sys.exit(0 if (3,11) <= sys.version_info[:2] <= (3,12) else 1)" >nul 2>&1
if errorlevel 1 (
  echo Python 3.11 atau 3.12 tidak ditemukan.
  echo Pasang Python 64-bit dari python.org dan centang Add python.exe to PATH.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" %MF_PY% -m venv .venv
if errorlevel 1 goto gagal
".venv\Scripts\python.exe" -m pip install --no-cache-dir -r requirements.txt
if errorlevel 1 goto gagal
".venv\Scripts\python.exe" -m pip check
if errorlevel 1 goto gagal
".venv\Scripts\python.exe" scripts\seed_demo.py
if errorlevel 1 goto gagal
echo.
echo Selesai. Klik dua kali 02_JALANKAN_WINDOWS.bat.
pause
exit /b 0
:gagal
echo Pemasangan belum selesai. Baca pesan kesalahan di atas dan README.md.
pause
exit /b 1
