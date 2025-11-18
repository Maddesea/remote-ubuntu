@echo off
REM ============================================================================
REM Air-Gapped Maximum Security STIG Executor - Windows Launcher
REM ============================================================================
REM 
REM This batch file launches the air-gapped STIG executor
REM No internet connection required - all dependencies bundled
REM
REM Requirements:
REM   - Python 3.6+ installed
REM   - dependencies/ folder in same directory
REM   - ubuntu20_stig_v2r3_enhanced.py in same directory
REM
REM Usage: Double-click this file or run from command prompt
REM ============================================================================

TITLE Air-Gapped Maximum Security STIG Executor
COLOR 0C
CLS

echo.
echo ================================================================================
echo              AIR-GAPPED MAXIMUM SECURITY STIG EXECUTOR
echo                  Ubuntu 20.04 DISA STIG V2R3 (172 Controls)
echo                        NO INTERNET REQUIRED
echo ================================================================================
echo.
echo This will apply MAXIMUM SECURITY STIG configuration to your Ubuntu target.
echo.
echo CRITICAL WARNINGS:
echo   - SSH password authentication will be DISABLED (keys only)
echo   - Root SSH login will be DISABLED
echo   - Many services will be DISABLED (USB, Wireless, CUPS, etc.)
echo   - Firewall will be STRICT (deny all except SSH)
echo   - System will be in MAXIMUM LOCKDOWN state
echo.
echo ENSURE YOU HAVE:
echo   ^> Console access available (KVM/IPMI/Physical)
echo   ^> SSH keys configured on target system
echo   ^> Current system backup/snapshot
echo   ^> Tested in non-production first
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

REM Check if dependencies folder exists
echo Checking for dependencies folder...
if not exist "dependencies" (
    echo.
    echo ERROR: 'dependencies' folder not found!
    echo.
    echo This air-gapped package requires the dependencies folder.
    echo.
    echo To fix this:
    echo   1. On internet-connected system: python download_dependencies.py
    echo   2. Transfer the 'dependencies' folder to this system
    echo   3. Place in same directory as this script
    echo.
    pause
    exit /b 1
)

echo Found dependencies folder
echo.

REM Check for required scripts
echo Checking for required scripts...
if not exist "airgap_windows_stig_executor.py" (
    echo.
    echo ERROR: airgap_windows_stig_executor.py not found!
    echo.
    echo Please ensure the main executor script is in the same directory.
    echo.
    pause
    exit /b 1
)

echo   [OK] airgap_windows_stig_executor.py

if not exist "ubuntu20_stig_v2r3_enhanced.py" (
    echo.
    echo ERROR: ubuntu20_stig_v2r3_enhanced.py not found!
    echo.
    echo Please ensure the STIG remediation script is in the same directory.
    echo.
    pause
    exit /b 1
)

echo   [OK] ubuntu20_stig_v2r3_enhanced.py
echo.

REM Check dependencies content
echo Verifying dependencies...
dir /b dependencies\*.whl >nul 2>&1
if errorlevel 1 (
    echo.
    echo WARNING: No .whl files found in dependencies folder
    echo This may cause installation issues.
    echo.
    set /p CONTINUE="Continue anyway? (Y/N): "
    if /i not "%CONTINUE%"=="Y" (
        echo.
        echo Execution cancelled.
        pause
        exit /b 1
    )
) else (
    echo   [OK] Found package files in dependencies/
)
echo.

echo All prerequisites satisfied!
echo.
echo ================================================================================
echo                       READY FOR MAXIMUM SECURITY EXECUTION
echo ================================================================================
echo.
echo The script will:
echo   1. Connect to your Ubuntu target via SSH
echo   2. Verify dependencies (auto-install from local files if needed)
echo   3. Transfer STIG remediation script
echo   4. Apply MAXIMUM SECURITY configuration (172 controls)
echo   5. Create automatic backups
echo   6. Show real-time progress
echo.
echo Security options will be presented interactively.
echo.
echo RECOMMENDED SETTINGS for MAXIMUM SECURITY:
echo   - Disable SSH password auth: YES
echo   - Enable FIPS mode: NO (unless you have FIPS kernel)
echo   - Strict firewall: YES
echo.
echo ================================================================================
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause >nul

REM Launch the Python script
cls
echo.
echo ================================================================================
echo                    LAUNCHING AIR-GAPPED STIG EXECUTOR
echo ================================================================================
echo.

python airgap_windows_stig_executor.py

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
    echo   1. Use console access (KVM/IPMI/Physical)
    echo   2. Restore from backup: /var/backups/pre-stig-*
    echo   3. See README_AIRGAP.md for rollback procedures
    echo.
    echo For troubleshooting, see: TROUBLESHOOTING_AIRGAP.md
    echo.
) else (
    echo.
    echo ================================================================================
    echo                    MAXIMUM SECURITY EXECUTION COMPLETED
    echo ================================================================================
    echo.
    echo CRITICAL NEXT STEPS:
    echo.
    echo 1. REBOOT the Ubuntu system:
    echo    ssh user@target 'sudo reboot'
    echo.
    echo 2. After reboot, access via SSH KEYS (password auth disabled):
    echo    ssh -i your_private_key user@target
    echo.
    echo 3. Verify critical services:
    echo    ssh -i key user@target 'sudo systemctl status sshd auditd rsyslog ufw'
    echo.
    echo 4. Test applications and verify functionality
    echo.
    echo 5. Run SCAP scan to verify compliance
    echo.
    echo SECURITY CHANGES APPLIED:
    echo   - SSH password authentication: DISABLED
    echo   - Root SSH login: DISABLED
    echo   - USB storage: DISABLED
    echo   - Wireless: DISABLED
    echo   - Firewall: STRICT (deny all except SSH)
    echo   - All unnecessary services: DISABLED
    echo   - 172 STIG controls: APPLIED
    echo.
    echo Log file: %USERPROFILE%\stig_execution_logs\
    echo Backups on target: /var/backups/pre-stig-*
    echo.
    echo For recovery procedures, see: README_AIRGAP.md
    echo.
)

echo.
echo ================================================================================
echo Press any key to exit...
pause >nul
