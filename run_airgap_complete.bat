@echo off
REM ============================================================================
REM Complete Air-Gap STIG Executor Launcher
REM ============================================================================
REM
REM This batch file launches the complete air-gapped STIG executor.
REM
REM Requirements:
REM   - Windows with Python 3.6+
REM   - airgap_complete_package/ folder in same directory
REM   - ubuntu20_stig_v2r3_enhanced.py in same directory
REM
REM Author: Complete Air-Gap Solution
REM Version: 3.0.0
REM ============================================================================

setlocal EnableDelayedExpansion

echo.
echo ================================================================================
echo COMPLETE AIR-GAP STIG EXECUTOR LAUNCHER
echo 100%% Offline Operation - NO Internet Required
echo ================================================================================
echo.

REM Check Python installation
echo Checking for Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Python is not installed or not in PATH
    echo.
    echo Please install Python 3.6 or higher from:
    echo   https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo   Python version: %PYTHON_VERSION%

REM Check for required files
echo.
echo Checking for required files...

if not exist "airgap_stig_executor_complete.py" (
    echo   [MISSING] airgap_stig_executor_complete.py
    echo.
    echo [ERROR] Main executor script not found!
    echo Please ensure airgap_stig_executor_complete.py is in the current directory.
    echo.
    pause
    exit /b 1
)
echo   [OK] airgap_stig_executor_complete.py

if not exist "ubuntu20_stig_v2r3_enhanced.py" (
    echo   [WARNING] ubuntu20_stig_v2r3_enhanced.py NOT FOUND
    echo.
    echo [ERROR] STIG remediation script is missing!
    echo.
    echo You need to obtain ubuntu20_stig_v2r3_enhanced.py and place it
    echo in the same directory as this batch file.
    echo.
    pause
    exit /b 1
)
echo   [OK] ubuntu20_stig_v2r3_enhanced.py

if not exist "airgap_complete_package\" (
    echo   [WARNING] airgap_complete_package\ folder NOT FOUND
    echo.
    echo [ERROR] Air-gap package folder is missing!
    echo.
    echo Expected structure:
    echo   airgap_complete_package\
    echo     python_dependencies\
    echo     ubuntu_packages\
    echo     scripts\
    echo.
    echo Please run download_all_airgap_packages.py first on an
    echo internet-connected system, then transfer the complete
    echo package to this air-gapped system.
    echo.
    pause
    exit /b 1
)
echo   [OK] airgap_complete_package\

if not exist "airgap_complete_package\python_dependencies\" (
    echo   [WARNING] python_dependencies\ folder NOT FOUND
    echo.
    echo [ERROR] Python dependencies are missing!
    echo Please ensure the complete package has been extracted properly.
    echo.
    pause
    exit /b 1
)
echo   [OK] airgap_complete_package\python_dependencies\

if not exist "airgap_complete_package\ubuntu_packages\" (
    echo   [WARNING] ubuntu_packages\ folder NOT FOUND
    echo.
    echo [WARNING] Ubuntu .deb packages are missing!
    echo This may cause some STIG controls to fail.
    echo.
    choice /C YN /M "Continue anyway"
    if errorlevel 2 exit /b 1
)
echo   [OK] airgap_complete_package\ubuntu_packages\

REM All checks passed
echo.
echo ================================================================================
echo PRE-FLIGHT CHECKS COMPLETE
echo ================================================================================
echo.
echo All required files are present.
echo.
echo This script will:
echo   1. Install Python dependencies from local files (if needed)
echo   2. Connect to Ubuntu target via SSH
echo   3. Transfer Ubuntu packages to target
echo   4. Install packages offline (NO apt)
echo   5. Execute STIG remediation
echo   6. Apply all 172 STIG controls
echo.
echo ================================================================================
echo CRITICAL WARNINGS
echo ================================================================================
echo.
echo   [WARNING] SSH password authentication will be DISABLED
echo   [WARNING] Only SSH keys will work after execution
echo   [WARNING] USB storage and wireless will be DISABLED
echo   [WARNING] Strict firewall rules will be applied
echo   [WARNING] System will require reboot
echo.
echo BEFORE PROCEEDING, ENSURE YOU HAVE:
echo   [X] Console access to target (KVM/IPMI/Physical)
echo   [X] SSH keys configured on target
echo   [X] System backup/snapshot created
echo   [X] Tested this in dev/test environment
echo.
echo ================================================================================
echo.

choice /C YN /M "Are you ready to proceed"
if errorlevel 2 (
    echo.
    echo Execution cancelled by user.
    echo.
    pause
    exit /b 0
)

echo.
echo ================================================================================
echo LAUNCHING EXECUTOR
echo ================================================================================
echo.

REM Launch the Python script
python airgap_stig_executor_complete.py

set EXIT_CODE=%errorlevel%

echo.
echo ================================================================================
echo EXECUTION FINISHED
echo ================================================================================
echo.

if %EXIT_CODE% equ 0 (
    echo [SUCCESS] STIG execution completed successfully!
    echo.
    echo NEXT STEPS:
    echo   1. REBOOT the target Ubuntu system
    echo   2. Test SSH access using SSH KEYS (password auth disabled^)
    echo   3. Verify services are running (auditd, ufw, sshd^)
    echo   4. Review logs for any errors
    echo.
) else (
    echo [ERROR] STIG execution encountered errors!
    echo.
    echo Please check:
    echo   1. Log file in %%USERPROFILE%%\stig_execution_logs\
    echo   2. Console output above for error messages
    echo   3. Network connectivity to target
    echo   4. SSH credentials
    echo.
)

echo Log files are saved in:
echo   %USERPROFILE%\stig_execution_logs\
echo.

pause
exit /b %EXIT_CODE%
