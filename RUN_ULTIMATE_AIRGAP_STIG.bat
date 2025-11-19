@echo off
REM =============================================================================
REM ULTIMATE AIR-GAP STIG EXECUTOR - Windows Launcher
REM =============================================================================
REM
REM This batch file provides a user-friendly way to launch the
REM Ultimate Air-Gap STIG Executor on Windows systems.
REM
REM Version: 4.0.0
REM =============================================================================

setlocal EnableDelayedExpansion

echo.
echo ================================================================================
echo ULTIMATE AIR-GAP STIG EXECUTOR
echo ================================================================================
echo.
echo 100%% OFFLINE STIG Execution for Ubuntu 20.04
echo Applies all 172 STIG controls with NO internet required
echo.
echo ================================================================================
echo.

REM Check for Python
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Python is not installed or not in PATH!
    echo.
    echo Please install Python 3.6 or higher from:
    echo   https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)

echo [OK] Python is installed
python --version
echo.

REM Check for required files
echo [2/4] Checking required files...

if not exist "ULTIMATE_AIRGAP_STIG_EXECUTOR.py" (
    echo.
    echo [ERROR] ULTIMATE_AIRGAP_STIG_EXECUTOR.py not found!
    echo.
    echo Make sure this batch file is in the same directory as:
    echo   - ULTIMATE_AIRGAP_STIG_EXECUTOR.py
    echo   - ubuntu20_stig_v2r3_enhanced.py
    echo   - airgap_packages\ folder
    echo.
    pause
    exit /b 1
)

if not exist "ubuntu20_stig_v2r3_enhanced.py" (
    echo.
    echo [ERROR] ubuntu20_stig_v2r3_enhanced.py not found!
    echo.
    echo This file is REQUIRED for STIG remediation.
    echo Place it in the same directory as this launcher.
    echo.
    pause
    exit /b 1
)

if not exist "airgap_packages\" (
    echo.
    echo [ERROR] airgap_packages\ folder not found!
    echo.
    echo You need to:
    echo   1. Run BUILD_AIRGAP_PACKAGE.py on an internet-connected system
    echo   2. Transfer the airgap_packages\ folder here
    echo.
    pause
    exit /b 1
)

echo [OK] All required files present
echo.

REM Display structure
echo [3/4] Verifying package structure...
echo.
echo Directory structure:
dir /B ULTIMATE_AIRGAP_STIG_EXECUTOR.py
dir /B ubuntu20_stig_v2r3_enhanced.py
dir /B airgap_packages
echo.

REM Display warnings
echo [4/4] Pre-execution warnings...
echo.
echo ================================================================================
echo CRITICAL WARNINGS - READ BEFORE PROCEEDING
echo ================================================================================
echo.
echo This script will apply ALL 172 DISA STIG controls to your Ubuntu target.
echo.
echo CHANGES INCLUDE:
echo   - SSH password authentication will be DISABLED ^(keys only^)
echo   - USB storage will be DISABLED
echo   - Wireless will be DISABLED
echo   - Strict firewall enabled ^(deny all except SSH^)
echo   - Many system services will be disabled
echo   - Password complexity enforced
echo   - Account lockout enabled
echo.
echo REQUIREMENTS:
echo   [!] Console access to Ubuntu ^(KVM/IPMI/Physical^) - REQUIRED
echo   [!] SSH keys configured on target - REQUIRED
echo   [!] System backup/snapshot created - RECOMMENDED
echo   [!] Tested in non-production first - STRONGLY RECOMMENDED
echo.
echo ================================================================================
echo.

set /p PROCEED="Ready to proceed? [yes/NO]: "
if /I not "!PROCEED!"=="yes" (
    echo.
    echo Execution cancelled.
    echo.
    pause
    exit /b 0
)

REM Launch the executor
echo.
echo ================================================================================
echo LAUNCHING ULTIMATE AIR-GAP STIG EXECUTOR
echo ================================================================================
echo.

python ULTIMATE_AIRGAP_STIG_EXECUTOR.py

set EXIT_CODE=%ERRORLEVEL%

echo.
echo ================================================================================
echo EXECUTION FINISHED
echo ================================================================================
echo.

if %EXIT_CODE% EQU 0 (
    echo [SUCCESS] STIG execution completed successfully!
    echo.
    echo NEXT STEPS:
    echo   1. Reboot the Ubuntu system
    echo   2. Test SSH key access ^(password auth is now disabled^)
    echo   3. Verify services are running
    echo   4. Run SCAP scan to verify compliance
    echo.
) else (
    echo [ERROR] STIG execution failed!
    echo.
    echo Check logs at:
    echo   %%USERPROFILE%%\stig_execution_logs\
    echo.
)

echo Check detailed logs at:
echo   %USERPROFILE%\stig_execution_logs\
echo.
echo ================================================================================
echo.

pause
exit /b %EXIT_CODE%
