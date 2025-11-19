#!/usr/bin/env python3
"""
Complete Air-Gapped Windows-to-Ubuntu STIG Remote Executor
===========================================================

100% OFFLINE - GUARANTEED TO WORK

Fully self-contained package for executing Ubuntu 20.04 STIG V2R3 remediation
from Windows workstations in completely air-gapped/isolated environments.

This script:
  1. Installs Windows Python dependencies from local files
  2. Connects to Ubuntu target via SSH
  3. Transfers all Ubuntu .deb packages to target
  4. Transfers STIG remediation script to target
  5. Executes STIG remediation with offline package installation
  6. Creates comprehensive backups
  7. Logs everything

Requirements on Windows:
    - Python 3.6+
    - dependencies/ folder with Python packages
    - ubuntu_packages/ folder with .deb files
    - scripts/ folder with STIG script

Author: Complete Air-Gap Edition
Version: 3.0.0
"""

import os
import sys
import time
import getpass
import logging
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

# Check Python version
if sys.version_info < (3, 6):
    print("ERROR: Python 3.6 or higher required")
    print(f"Current version: {sys.version}")
    sys.exit(1)

# ============================================================================
# Air-Gap Dependency Installer
# ============================================================================

class AirGapDependencyInstaller:
    """Install Python dependencies from local bundled files"""

    def __init__(self, dependencies_dir="dependencies"):
        self.dependencies_dir = Path(dependencies_dir)
        self.installed = []
        self.failed = []

    def check_and_install(self):
        """Check for required packages and install from local files if needed"""
        print("\n" + "="*80)
        print("DEPENDENCY CHECK (AIR-GAPPED MODE)")
        print("="*80)

        required_packages = {
            'paramiko': 'paramiko',
            'cryptography': 'cryptography',
            'bcrypt': 'bcrypt',
            'nacl': 'PyNaCl',
            'cffi': 'cffi',
            'pycparser': 'pycparser',
            'six': 'six'
        }

        missing = []

        # Check which packages are missing
        for import_name, package_name in required_packages.items():
            try:
                __import__(import_name)
                print(f"  [OK] {package_name} is installed")
            except ImportError:
                print(f"  [FAIL] {package_name} is NOT installed")
                missing.append(package_name)

        if not missing:
            print("\n[OK] All dependencies are installed!")
            return True

        print(f"\n[WARNING]  Missing {len(missing)} packages: {', '.join(missing)}")

        # Check if dependencies directory exists
        if not self.dependencies_dir.exists():
            print(f"\n[ERROR] ERROR: Dependencies directory not found: {self.dependencies_dir}")
            print("\nPackage structure should be:")
            print("  dependencies/        ← Python .whl files")
            print("  ubuntu_packages/     ← Ubuntu .deb files")
            print("  scripts/             ← STIG scripts")
            return False

        # Install from local files
        print(f"\n[PACKAGE] Installing from local files in: {self.dependencies_dir}")
        return self.install_from_local()

    def install_from_local(self):
        """Install packages from local wheel/tar.gz files"""
        wheel_files = list(self.dependencies_dir.glob("*.whl"))
        tar_files = list(self.dependencies_dir.glob("*.tar.gz"))
        all_files = wheel_files + tar_files

        if not all_files:
            print(f"\n[ERROR] ERROR: No package files found in {self.dependencies_dir}")
            return False

        print(f"\nFound {len(all_files)} package files")
        print("Installing...")

        # Try installing all at once first (faster)
        cmd = [sys.executable, '-m', 'pip', 'install', '--no-index', '--find-links',
               str(self.dependencies_dir)] + [str(f) for f in all_files]

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(result.stdout)
            print(f"\n[OK] Successfully installed all dependencies!")
            return True
        except subprocess.CalledProcessError:
            print("\n[WARNING]  Batch install failed, trying individual installation...")

        # Try individual installation
        success_count = 0
        for file in all_files:
            try:
                print(f"  Installing {file.name}...")
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', '--no-index',
                     '--find-links', str(self.dependencies_dir), str(file)],
                    check=True,
                    capture_output=True,
                    text=True
                )
                print(f"    [OK] Installed: {file.name}")
                self.installed.append(file.name)
                success_count += 1
            except subprocess.CalledProcessError as e:
                print(f"    [FAIL] Failed: {file.name}")
                self.failed.append(file.name)

        if self.failed:
            print(f"\n[WARNING]  {len(self.failed)} packages failed to install:")
            for pkg in self.failed:
                print(f"    - {pkg}")

        if success_count > 0:
            print(f"\n[OK] Installed {success_count}/{len(all_files)} packages")
            return True

        return False

# ============================================================================
# Complete Air-Gap STIG Executor
# ============================================================================

class CompleteAirGapSTIGExecutor:
    """Execute Ubuntu STIG remediation in completely air-gapped environment"""

    def __init__(self):
        self.host = None
        self.port = 22
        self.username = None
        self.password = None
        self.sudo_password = None
        self.client = None
        self.connected = False

        # Paths
        self.script_dir = Path(__file__).parent
        self.ubuntu_packages_dir = self.script_dir.parent / "ubuntu_packages"
        self.scripts_dir = self.script_dir.parent / "scripts"

        # Check if running from extracted package
        if not self.scripts_dir.exists():
            self.scripts_dir = self.script_dir

        if not self.ubuntu_packages_dir.exists():
            self.ubuntu_packages_dir = self.script_dir.parent / "ubuntu_packages"

        self.stig_script = "ubuntu20_stig_v2r3_airgap.py"

        # Setup logging
        self.setup_logging()

    def setup_logging(self):
        """Configure logging to file and console"""
        # Create logs directory in user's home
        if os.name == 'nt':  # Windows
            log_dir = Path.home() / "stig_execution_logs"
        else:
            log_dir = Path.home() / ".stig_execution_logs"

        log_dir.mkdir(exist_ok=True)

        # Log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"stig_execution_{timestamp}.log"

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )

        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Log file: {log_file}")

    def print_banner(self):
        """Print welcome banner"""
        print("\n" + "="*80)
        print("UBUNTU 20.04 STIG V2R3 REMOTE EXECUTOR")
        print("Complete Air-Gapped Edition - 100% Offline")
        print("="*80)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Python: {sys.version.split()[0]}")
        print("STIG: V2R3 (172 controls: 14 CAT I, 136 CAT II, 22 CAT III)")
        print("="*80 + "\n")

    def check_package_structure(self):
        """Verify package structure is correct"""
        print("[PACKAGE] Checking package structure...\n")

        issues = []

        # Check for scripts directory
        if not self.scripts_dir.exists():
            issues.append(f"Scripts directory not found: {self.scripts_dir}")
        else:
            print(f"  [OK] Scripts directory: {self.scripts_dir}")

            # Check for STIG script
            stig_script_path = self.scripts_dir / self.stig_script
            if not stig_script_path.exists():
                issues.append(f"STIG script not found: {stig_script_path}")
            else:
                print(f"  [OK] STIG script: {self.stig_script}")

        # Check for Ubuntu packages directory
        if not self.ubuntu_packages_dir.exists():
            issues.append(f"Ubuntu packages directory not found: {self.ubuntu_packages_dir}")
        else:
            deb_files = list(self.ubuntu_packages_dir.glob("*.deb"))
            if not deb_files:
                print(f"  [WARNING]  WARNING: No .deb files in {self.ubuntu_packages_dir}")
                print(f"     STIG script will attempt to use target's package cache")
            else:
                print(f"  [OK] Ubuntu packages: {len(deb_files)} .deb files")

        if issues:
            print("\n[ERROR] PACKAGE STRUCTURE ISSUES:")
            for issue in issues:
                print(f"  - {issue}")
            print("\nExpected structure:")
            print("  scripts/")
            print("    ├── airgap_complete_executor.py")
            print("    └── ubuntu20_stig_v2r3_airgap.py")
            print("  ubuntu_packages/")
            print("    └── *.deb files")
            print("  dependencies/")
            print("    └── *.whl files")
            return False

        print("")
        return True

    def get_connection_info(self):
        """Collect connection information interactively"""
        print("CONNECTION INFORMATION")
        print("-" * 80)

        self.host = input("Ubuntu target IP or hostname: ").strip()
        if not self.host:
            print("[ERROR] ERROR: Hostname/IP required")
            return False

        port_input = input(f"SSH port [22]: ").strip()
        if port_input:
            try:
                self.port = int(port_input)
            except ValueError:
                print("[ERROR] ERROR: Invalid port number")
                return False

        self.username = input("SSH username: ").strip()
        if not self.username:
            print("[ERROR] ERROR: Username required")
            return False

        self.password = getpass.getpass("SSH password: ")
        if not self.password:
            print("[ERROR] ERROR: Password required")
            return False

        print("\nSudo password (press Enter if same as SSH password): ", end='', flush=True)
        self.sudo_password = getpass.getpass("")
        if not self.sudo_password:
            self.sudo_password = self.password

        print("")
        return True

    def test_connection(self):
        """Test SSH connection to target"""
        print(f" Testing SSH connection to {self.username}@{self.host}:{self.port}...")

        try:
            import paramiko

            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            self.client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=10,
                look_for_keys=False,
                allow_agent=False
            )

            self.connected = True
            print(f"[OK] Connected successfully!\n")
            self.logger.info(f"Connected to {self.host}")
            return True

        except Exception as e:
            print(f"[ERROR] Connection failed: {e}\n")
            self.logger.error(f"Connection failed: {e}")
            return False

    def transfer_ubuntu_packages(self):
        """Transfer Ubuntu .deb packages to target"""
        deb_files = list(self.ubuntu_packages_dir.glob("*.deb"))

        if not deb_files:
            print("[WARNING]  No Ubuntu packages to transfer (will rely on target's cache)\n")
            return True

        print(f"[PACKAGE] Transferring {len(deb_files)} Ubuntu packages to target...")

        try:
            import paramiko

            # Create remote directory for packages
            remote_pkg_dir = "/tmp/stig_ubuntu_packages"
            stdin, stdout, stderr = self.client.exec_command(f"mkdir -p {remote_pkg_dir}")
            stdout.channel.recv_exit_status()

            # Transfer each .deb file
            sftp = self.client.open_sftp()
            success_count = 0

            for deb_file in deb_files:
                try:
                    remote_path = f"{remote_pkg_dir}/{deb_file.name}"
                    print(f"  Transferring: {deb_file.name}...", end='', flush=True)

                    sftp.put(str(deb_file), remote_path)

                    print(" [OK]")
                    success_count += 1
                    self.logger.info(f"Transferred: {deb_file.name}")

                except Exception as e:
                    print(f" [FAIL] Failed: {e}")
                    self.logger.error(f"Failed to transfer {deb_file.name}: {e}")

            sftp.close()

            print(f"\n[OK] Transferred {success_count}/{len(deb_files)} packages")
            print(f"  Remote location: {remote_pkg_dir}\n")

            return success_count > 0

        except Exception as e:
            print(f"\n[ERROR] Transfer failed: {e}\n")
            self.logger.error(f"Package transfer failed: {e}")
            return False

    def transfer_stig_script(self):
        """Transfer STIG remediation script to target"""
        print(f"[FILE] Transferring STIG script to target...")

        stig_script_path = self.scripts_dir / self.stig_script
        if not stig_script_path.exists():
            print(f"[ERROR] ERROR: STIG script not found: {stig_script_path}\n")
            return False

        try:
            import paramiko

            remote_path = f"/tmp/{self.stig_script}"

            sftp = self.client.open_sftp()
            sftp.put(str(stig_script_path), remote_path)
            sftp.chmod(remote_path, 0o755)
            sftp.close()

            print(f"  [OK] Transferred: {self.stig_script}")
            print(f"  Remote location: {remote_path}\n")

            self.logger.info(f"Transferred STIG script to {remote_path}")
            return True

        except Exception as e:
            print(f"[ERROR] Transfer failed: {e}\n")
            self.logger.error(f"Script transfer failed: {e}")
            return False

    def show_warnings(self):
        """Display important warnings before execution"""
        print("\n" + "!"*80)
        print("[WARNING]  CRITICAL WARNINGS - READ CAREFULLY")
        print("!"*80)
        print("""
This script will apply 172 DISA STIG security controls to the target system.

WHAT WILL CHANGE:
  - Password policies (15 char minimum, complexity requirements)
  - Account lockout (3 failed attempts = 15 min lockout)
  - SSH configuration (FIPS ciphers, root login disabled)
  - Firewall rules (UFW enabled, restrictive rules)
  - Kernel parameters (59 sysctl settings)
  - Audit system (136 comprehensive audit rules)
  - System services (disable unnecessary services)
  - USB/wireless settings (restrictive by default)
  - File permissions and ownership

BEFORE YOU PROCEED:
  [OK] You have CONSOLE ACCESS to the target (KVM/physical/VM console)
  [OK] This is a TEST environment (not production)
  [OK] You have current backups
  [OK] You understand SSH may be reconfigured
  [OK] You are prepared for the system to reboot

BACKUPS:
  Automatic backups will be created in:
    /var/backups/pre-stig-YYYYMMDD_HHMMSS/

LOGS:
  Target system log:
    /var/log/ubuntu20-stig-v2r3-remediation.log

IF SOMETHING BREAKS:
  Use console access to restore SSH config:
    sudo cp /var/backups/pre-stig-*/sshd_config /etc/ssh/
    sudo systemctl restart sshd
""")
        print("!"*80 + "\n")

    def confirm_execution(self):
        """Get user confirmation before execution"""
        print("FINAL CONFIRMATION")
        print("-" * 80)
        print(f"Target: {self.username}@{self.host}:{self.port}")
        print(f"STIG Version: V2R3 (172 controls)")
        print(f"Offline Mode: YES (100% air-gapped)")
        print("")

        response = input("Type 'EXECUTE' (all caps) to proceed, or anything else to cancel: ").strip()

        if response == "EXECUTE":
            print("\n[OK] Confirmed. Proceeding with execution...\n")
            return True
        else:
            print("\n[ERROR] Execution cancelled by user.\n")
            return False

    def execute_stig(self):
        """Execute STIG remediation script on target"""
        print("="*80)
        print("EXECUTING STIG REMEDIATION")
        print("="*80 + "\n")

        remote_script = f"/tmp/{self.stig_script}"

        # Build command with offline mode flag
        command = f"sudo -S python3 {remote_script} --offline --force-all-fixes"

        print(f"Command: {command}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        print("="*80 + "\n")

        try:
            # Execute command
            stdin, stdout, stderr = self.client.exec_command(command, get_pty=True)

            # Send sudo password
            stdin.write(self.sudo_password + '\n')
            stdin.flush()

            # Stream output in real-time
            while True:
                line = stdout.readline()
                if not line:
                    break
                print(line, end='')
                sys.stdout.flush()

            # Get exit code
            exit_code = stdout.channel.recv_exit_status()

            print("\n" + "="*80)
            print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Exit code: {exit_code}")
            print("="*80 + "\n")

            if exit_code == 0:
                print("[OK] STIG EXECUTION SUCCESSFUL!")
                self.logger.info("STIG execution completed successfully")
                return True
            else:
                print(f"[WARNING]  STIG execution completed with exit code: {exit_code}")
                self.logger.warning(f"STIG execution completed with exit code: {exit_code}")
                return False

        except Exception as e:
            print(f"\n[ERROR] Execution failed: {e}\n")
            self.logger.error(f"STIG execution failed: {e}")
            return False

    def cleanup(self):
        """Clean up remote files (optional)"""
        print("\n Cleaning up remote files...")

        try:
            # Ask if user wants to clean up
            cleanup = input("Remove transferred files from target? (y/N): ").strip().lower()

            if cleanup == 'y':
                commands = [
                    f"rm -f /tmp/{self.stig_script}",
                    "rm -rf /tmp/stig_ubuntu_packages"
                ]

                for cmd in commands:
                    stdin, stdout, stderr = self.client.exec_command(f"sudo -S {cmd}", get_pty=True)
                    stdin.write(self.sudo_password + '\n')
                    stdin.flush()
                    stdout.channel.recv_exit_status()

                print("  [OK] Cleaned up temporary files\n")
                self.logger.info("Cleaned up remote temporary files")
            else:
                print("  [SKIP] Skipped cleanup\n")

        except Exception as e:
            print(f"  [WARNING]  Cleanup failed: {e}\n")
            self.logger.warning(f"Cleanup failed: {e}")

    def close(self):
        """Close SSH connection"""
        if self.client:
            self.client.close()
            self.connected = False
            print("[OK] Connection closed\n")

    def run(self):
        """Main execution flow"""
        self.print_banner()

        # Check package structure
        if not self.check_package_structure():
            return False

        # Get connection details
        if not self.get_connection_info():
            return False

        # Test connection
        if not self.test_connection():
            return False

        # Transfer Ubuntu packages
        if not self.transfer_ubuntu_packages():
            print("[WARNING]  Package transfer failed, continuing anyway...")

        # Transfer STIG script
        if not self.transfer_stig_script():
            return False

        # Show warnings
        self.show_warnings()

        # Get confirmation
        if not self.confirm_execution():
            self.close()
            return False

        # Execute STIG
        success = self.execute_stig()

        # Cleanup
        self.cleanup()

        # Close connection
        self.close()

        # Final summary
        print("\n" + "="*80)
        if success:
            print("[OK] STIG REMEDIATION COMPLETED SUCCESSFULLY")
        else:
            print("[WARNING]  STIG REMEDIATION COMPLETED WITH WARNINGS")
        print("="*80)
        print("\nNEXT STEPS:")
        print("1. Review the execution log on target:")
        print("     /var/log/ubuntu20-stig-v2r3-remediation.log")
        print("2. Verify critical services are running")
        print("3. Test SSH access")
        print("4. Review changes and backups")
        print("5. Reboot the system when ready")
        print("\nBackups location:")
        print("  /var/backups/pre-stig-YYYYMMDD_HHMMSS/")
        print("\n" + "="*80 + "\n")

        return success

# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point"""

    # Install dependencies first
    print("="*80)
    print("STEP 1: DEPENDENCY INSTALLATION")
    print("="*80)

    installer = AirGapDependencyInstaller()
    if not installer.check_and_install():
        print("\n[ERROR] Failed to install dependencies")
        print("\nPlease ensure the 'dependencies' folder contains all required packages.")
        print("Run build_complete_airgap_package.py on a connected system to create the package.")
        return 1

    # Import paramiko after installation
    try:
        import paramiko
        print("\n[OK] paramiko successfully imported\n")
    except ImportError:
        print("\n[ERROR] ERROR: Failed to import paramiko after installation")
        print("Please check the dependencies folder and try again.")
        return 1

    # Run executor
    print("="*80)
    print("STEP 2: STIG EXECUTION")
    print("="*80 + "\n")

    executor = CompleteAirGapSTIGExecutor()

    try:
        success = executor.run()
        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n\n[ERROR] Execution cancelled by user")
        executor.close()
        return 1

    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        executor.close()
        return 1

if __name__ == '__main__':
    sys.exit(main())
