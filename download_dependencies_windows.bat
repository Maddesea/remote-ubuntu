@echo off
REM ============================================================================
REM Download Dependencies for Air-Gapped STIG Executor
REM ============================================================================
REM
REM Run this on an INTERNET-CONNECTED Windows system to download all
REM dependencies, then transfer the 'dependencies' folder to your
REM air-gapped system.
REM
REM Requirements:
REM   - Internet connection
REM   - Python 3.6+ with pip
REM
REM ============================================================================

echo.
echo ================================================================================
echo DEPENDENCY DOWNLOADER FOR AIR-GAPPED STIG EXECUTOR
echo ================================================================================
echo.
echo This script will download all required Python packages for air-gapped
echo installation of the STIG executor.
echo.
echo Requirements:
echo   - Internet connection (active now)
echo   - Python 3.6+ with pip installed
echo.
echo ================================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.6 or higher from:
    echo   https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo Python version:
python --version
echo.

REM Check if pip is available
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is not available
    echo.
    echo Please ensure pip is installed with Python.
    echo.
    pause
    exit /b 1
)

echo pip version:
python -m pip --version
echo.

REM Check internet connectivity
echo Checking internet connectivity...
ping -n 1 pypi.org >nul 2>&1
if errorlevel 1 (
    echo.
    echo WARNING: Cannot reach pypi.org
    echo Please check your internet connection.
    echo.
    pause
)

echo Internet connection OK
echo.

REM Check if dependencies folder exists
if exist "dependencies\" (
    echo.
    echo WARNING: dependencies folder already exists.
    echo.
    choice /C YN /M "Delete and recreate"
    if errorlevel 2 goto :SKIP_DELETE
    if errorlevel 1 (
        echo Removing existing dependencies folder...
        rmdir /S /Q dependencies
    )
)
:SKIP_DELETE

REM Create dependencies folder
mkdir dependencies 2>nul

echo ================================================================================
echo DOWNLOADING PACKAGES
echo ================================================================================
echo.
echo Downloading paramiko and all dependencies...
echo This may take a few minutes depending on your connection speed.
echo.

REM Download packages
python -m pip download --dest dependencies --prefer-binary paramiko cryptography bcrypt pynacl cffi pycparser six

if errorlevel 1 (
    echo.
    echo ================================================================================
    echo DOWNLOAD FAILED
    echo ================================================================================
    echo.
    echo Please check the error messages above.
    echo Common issues:
    echo   - No internet connection
    echo   - PyPI is down
    echo   - Firewall blocking access
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo DOWNLOAD COMPLETE
echo ================================================================================
echo.

REM Count files
set /a count=0
for %%f in (dependencies\*) do set /a count+=1

echo Downloaded %count% package files to 'dependencies' folder
echo.

REM List files
echo Package files:
dir /B dependencies
echo.

REM Calculate total size
for /f "tokens=3" %%a in ('dir /s /-c dependencies ^| find "bytes"') do set size=%%a
echo Total size: %size% bytes
echo.

echo ================================================================================
echo NEXT STEPS
echo ================================================================================
echo.
echo 1. Verify the download:
echo    - Check that dependencies folder contains .whl files
echo    - Look for paramiko, cryptography, bcrypt, etc.
echo.
echo 2. Transfer to air-gapped system:
echo    - Copy the entire 'dependencies' folder
echo    - Use USB drive, CD/DVD, or approved transfer method
echo.
echo 3. On air-gapped system:
echo    - Place 'dependencies' folder in same directory as:
echo      * RUN_ME.bat
echo      * windows_airgap_stig_complete.py
echo      * ubuntu20_stig_remediation_airgapped.py
echo.
echo 4. Run the STIG executor:
echo    - Double-click RUN_ME.bat
echo    - Or: python windows_airgap_stig_complete.py
echo.
echo The script will automatically detect and install from dependencies folder.
echo.
echo ================================================================================
echo.

pause
