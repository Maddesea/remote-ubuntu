@echo off
REM ============================================================================
REM Complete Air-Gapped STIG Executor - Windows Launcher
REM ============================================================================
REM
REM This batch file launches the air-gapped STIG remediation tool.
REM No internet or package repositories required!
REM
REM Usage: Double-click this file or run from command prompt
REM
REM ============================================================================

echo.
echo ================================================================================
echo COMPLETE AIR-GAPPED STIG EXECUTOR
echo ================================================================================
echo.
echo This will connect to your Ubuntu 20.04 system and apply DISA STIG V2R3
echo security hardening in a completely air-gapped environment.
echo.
echo Requirements:
echo   - Python 3.6+ installed on this Windows machine
echo   - Network access to target Ubuntu system
echo   - SSH credentials with sudo privileges
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
    echo Or if Python is installed, add it to your PATH.
    echo.
    pause
    exit /b 1
)

echo Python detected:
python --version
echo.

REM Check if the main script exists
if not exist "windows_airgap_stig_complete.py" (
    echo ERROR: windows_airgap_stig_complete.py not found!
    echo.
    echo Please ensure the following files are in this directory:
    echo   - windows_airgap_stig_complete.py
    echo   - ubuntu20_stig_remediation_airgapped.py
    echo.
    pause
    exit /b 1
)

if not exist "ubuntu20_stig_remediation_airgapped.py" (
    echo WARNING: ubuntu20_stig_remediation_airgapped.py not found!
    echo This file is required for STIG remediation.
    echo.
    pause
    exit /b 1
)

echo All required files present.
echo.
echo ================================================================================
echo OPTIONAL: Enhanced Performance
echo ================================================================================
echo.
echo For better performance, you can install paramiko:
echo   1. On internet-connected system: pip download -d dependencies paramiko
echo   2. Copy 'dependencies' folder to this directory
echo   3. Re-run this script
echo.
echo The script will work without paramiko, but it will be slower.
echo.

REM Check if dependencies folder exists
if exist "dependencies\" (
    echo Dependencies folder found - will attempt to install paramiko
    echo.
)

echo ================================================================================
echo.
echo Press Ctrl+C now to cancel, or
pause

REM Run the main Python script
echo.
echo Starting STIG executor...
echo.

python windows_airgap_stig_complete.py

if errorlevel 1 (
    echo.
    echo ================================================================================
    echo EXECUTION FAILED
    echo ================================================================================
    echo.
    echo Please review the error messages above.
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo EXECUTION COMPLETE
echo ================================================================================
echo.
pause
