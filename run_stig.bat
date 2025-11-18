@echo off
REM ============================================================================
REM Windows STIG Remote Executor - Quick Launch Script
REM ============================================================================
REM This batch file makes it easy to run the STIG remediation from Windows
REM 
REM Requirements:
REM   - Python 3.6+ installed and in PATH
REM   - paramiko package installed (pip install paramiko)
REM   - Both .py files in the same directory as this .bat file
REM
REM Usage:
REM   1. Double-click this file
REM   2. Follow the interactive prompts
REM ============================================================================

TITLE Ubuntu 20.04 STIG Remote Executor
COLOR 0A
CLS

echo.
echo ================================================================================
echo                   UBUNTU 20.04 STIG REMOTE EXECUTOR
echo                          Windows Quick Launcher
echo ================================================================================
echo.
echo This will execute DISA STIG V2R3 compliance remediation on your Ubuntu target.
echo.
echo CRITICAL WARNINGS:
echo   - This makes MAJOR security changes to the target system
echo   - ALWAYS test in non-production first
echo   - Have console access ready
echo   - Create VM snapshot or backup before running
echo.
echo ================================================================================
echo.

REM Check if Python is installed
echo Checking for Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.6 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%I in ('python --version 2^>^&1') do set PYTHON_VERSION=%%I
echo Found Python version: %PYTHON_VERSION%
echo.

REM Check if paramiko is installed
echo Checking for required packages...
python -c "import paramiko" >nul 2>&1
if errorlevel 1 (
    echo.
    echo WARNING: paramiko package not found
    echo.
    echo Would you like to install it now? (Requires internet connection^)
    echo.
    set /p INSTALL_PARAMIKO="Install paramiko? (Y/N): "
    
    if /i "%INSTALL_PARAMIKO%"=="Y" (
        echo.
        echo Installing paramiko and scp...
        pip install paramiko scp
        if errorlevel 1 (
            echo.
            echo ERROR: Failed to install packages
            echo Please run manually: pip install paramiko scp
            echo.
            pause
            exit /b 1
        )
        echo.
        echo Packages installed successfully!
    ) else (
        echo.
        echo Cannot proceed without paramiko.
        echo Please run: pip install paramiko scp
        echo.
        pause
        exit /b 1
    )
)

python -c "import paramiko; print('  [OK] paramiko')" 2>nul
python -c "import scp; print('  [OK] scp (optional)')" 2>nul
echo.

REM Check if STIG scripts exist
echo Checking for required scripts...
if not exist "windows_stig_remote_executor.py" (
    echo.
    echo ERROR: windows_stig_remote_executor.py not found!
    echo.
    echo Please ensure both Python scripts are in the same directory as this batch file:
    echo   - windows_stig_remote_executor.py
    echo   - ubuntu20_stig_v2r3_enhanced.py
    echo.
    pause
    exit /b 1
)

if not exist "ubuntu20_stig_v2r3_enhanced.py" (
    echo.
    echo ERROR: ubuntu20_stig_v2r3_enhanced.py not found!
    echo.
    echo Please ensure both Python scripts are in the same directory as this batch file:
    echo   - windows_stig_remote_executor.py
    echo   - ubuntu20_stig_v2r3_enhanced.py
    echo.
    pause
    exit /b 1
)

echo   [OK] windows_stig_remote_executor.py
echo   [OK] ubuntu20_stig_v2r3_enhanced.py
echo.

echo All prerequisites satisfied!
echo.
echo ================================================================================
echo                              READY TO EXECUTE
echo ================================================================================
echo.
echo The script will now connect to your Ubuntu target and apply STIG controls.
echo.
echo You will be prompted for:
echo   - Target IP address
echo   - SSH credentials
echo   - Sudo password
echo   - Confirmation to proceed
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause >nul

REM Launch the Python script
cls
python windows_stig_remote_executor.py

REM Check exit code
if errorlevel 1 (
    echo.
    echo ================================================================================
    echo                           EXECUTION FAILED
    echo ================================================================================
    echo.
    echo The STIG remediation encountered errors.
    echo.
    echo Check the log file in: %USERPROFILE%\stig_execution_logs\
    echo.
    echo If the target system is inaccessible:
    echo   1. Use console access (KVM/physical)
    echo   2. Restore from backup in: /var/backups/pre-stig-*
    echo.
) else (
    echo.
    echo ================================================================================
    echo                        EXECUTION COMPLETED
    echo ================================================================================
    echo.
    echo NEXT STEPS:
    echo   1. REBOOT the Ubuntu system to apply all changes
    echo   2. Verify SSH access still works
    echo   3. Test critical services and applications
    echo   4. Run SCAP scan to verify compliance
    echo.
    echo Log file location: %USERPROFILE%\stig_execution_logs\
    echo.
)

echo.
echo Press any key to exit...
pause >nul
