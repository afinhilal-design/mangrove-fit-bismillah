@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
echo Memasang MANGROVE-FIT. Internet diperlukan pada pemasangan pertama.
set "MF_PY="

rem Python Manager menaruh launcher nyata di lokasi ini.
if exist "%LocalAppData%\Python\bin\python.exe" (
  "%LocalAppData%\Python\bin\python.exe" -c "import sys; sys.exit(0 if (3,11) <= sys.version_info[:2] <= (3,14) else 1)" >nul 2>&1
  if not errorlevel 1 set "MF_PY=%LocalAppData%\Python\bin\python.exe"
)

rem Coba semua python.exe pada PATH; alias Windows Store yang rusak akan dilewati.
if not defined MF_PY (
  for /f "delims=" %%P in ('where python 2^>nul') do (
    if not defined MF_PY (
      "%%P" -c "import sys; sys.exit(0 if (3,11) <= sys.version_info[:2] <= (3,14) else 1)" >nul 2>&1
      if not errorlevel 1 set "MF_PY=%%P"
    )
  )
)

rem Fallback untuk instalasi klasik Python Launcher.
if not defined MF_PY (
  for %%V in (3.14 3.13 3.12 3.11) do (
    if not defined MF_PY (
      for /f "delims=" %%P in ('py -%%V -c "import sys; print(sys.executable)" 2^>nul') do set "MF_PY=%%P"
    )
  )
)

if not defined MF_PY (
  echo Python 3.11 sampai 3.14 tidak ditemukan.
  echo Pasang Python 64-bit dari python.org dan centang Add python.exe to PATH.
  pause
  exit /b 1
)
echo Menggunakan: "%MF_PY%"
"%MF_PY%" --version
if not exist ".venv\Scripts\python.exe" "%MF_PY%" -m venv .venv
if errorlevel 1 goto gagal
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto gagal
".venv\Scripts\python.exe" -m pip install --only-binary=:all: -r requirements.txt
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
