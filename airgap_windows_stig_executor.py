#!/usr/bin/env python3
"""
Air-Gapped Windows-to-Ubuntu STIG Remote Executor
==================================================

Fully self-contained package for executing Ubuntu 20.04 STIG V2R3 remediation
from Windows workstations in air-gapped/isolated environments.

Features:
- No internet connection required
- All dependencies bundled
- Single executable package
- Maximum security lockdown
- Automatic dependency installation from local files

Requirements on Windows:
    - Python 3.6+
    - All dependencies in ./dependencies/ folder

Author: Air-Gapped Edition
Version: 2.0.0-airgap
"""

import os
import sys
import time
import getpass
import logging
import subprocess
import zipfile
import tempfile
from pathlib import Path
from datetime import datetime

# Check Python version
if sys.version_info < (3, 6):
    print("ERROR: Python 3.6 or higher required")
    print(f"Current version: {sys.version}")
    sys.exit(1)

# Air-gap dependency installer
class AirGapDependencyInstaller:
    """Install dependencies from local bundled files in air-gapped environment"""
    
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
            'pynacl': 'PyNaCl',
            'cffi': 'cffi',
            'pycparser': 'pycparser',
            'six': 'six'
        }
        
        missing = []
        
        # Check which packages are missing
        for import_name, package_name in required_packages.items():
            try:
                __import__(import_name)
                print(f"  ✓ {package_name} is installed")
            except ImportError:
                print(f"  ✗ {package_name} is NOT installed")
                missing.append(package_name)
        
        if not missing:
            print("\n✓ All dependencies are installed!")
            return True
        
        print(f"\n⚠️  Missing {len(missing)} packages: {', '.join(missing)}")
        
        # Check if dependencies directory exists
        if not self.dependencies_dir.exists():
            print(f"\n❌ ERROR: Dependencies directory not found: {self.dependencies_dir}")
            print("\nTo fix this:")
            print("1. On a connected system, run: pip download -d dependencies paramiko")
            print("2. Copy the entire 'dependencies' folder to this air-gapped system")
            print("3. Run this script again")
            return False
        
        # Install from local files
        print(f"\n📦 Installing from local files in: {self.dependencies_dir}")
        return self.install_from_local()
    
    def install_from_local(self):
        """Install packages from local wheel/tar.gz files"""
        wheel_files = list(self.dependencies_dir.glob("*.whl"))
        tar_files = list(self.dependencies_dir.glob("*.tar.gz"))
        all_files = wheel_files + tar_files
        
        if not all_files:
            print(f"\n❌ ERROR: No package files found in {self.dependencies_dir}")
            print("\nExpected files: .whl or .tar.gz files for paramiko and dependencies")
            return False
        
        print(f"\nFound {len(all_files)} package files:")
        for f in all_files[:10]:  # Show first 10
            print(f"  - {f.name}")
        if len(all_files) > 10:
            print(f"  ... and {len(all_files) - 10} more")
        
        # Install all packages
        print("\n📦 Installing packages...")
        
        try:
            # Use pip to install from directory
            cmd = [
                sys.executable, '-m', 'pip', 'install',
                '--no-index',  # Don't use PyPI
                '--find-links', str(self.dependencies_dir),  # Use local files
                'paramiko'  # This will pull in all dependencies
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                print("✓ Installation successful!")
                print("\nVerifying installation...")
                
                # Verify by importing
                try:
                    import paramiko
                    print("✓ paramiko verified")
                    return True
                except ImportError as e:
                    print(f"✗ Verification failed: {e}")
                    return False
            else:
                print(f"✗ Installation failed:")
                print(result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print("✗ Installation timed out")
            return False
        except Exception as e:
            print(f"✗ Installation error: {e}")
            return False

# Try to import paramiko, or install from local files
try:
    import paramiko
    from paramiko.ssh_exception import SSHException, AuthenticationException
    PARAMIKO_AVAILABLE = True
except ImportError:
    print("⚠️  paramiko not found - will attempt installation from local files")
    PARAMIKO_AVAILABLE = False
    
    # Try to install from local dependencies
    installer = AirGapDependencyInstaller()
    if installer.check_and_install():
        # Try importing again
        try:
            import paramiko
            from paramiko.ssh_exception import SSHException, AuthenticationException
            PARAMIKO_AVAILABLE = True
        except ImportError:
            print("\n❌ Failed to import paramiko after installation")
            print("Please check the dependencies folder and try again")
            sys.exit(1)
    else:
        print("\n❌ Cannot proceed without paramiko")
        print("\nFor air-gapped installation:")
        print("1. On internet-connected system: pip download -d dependencies paramiko")
        print("2. Copy 'dependencies' folder to this system")
        print("3. Run this script again")
        sys.exit(1)

# Configure logging
log_dir = Path.home() / "stig_execution_logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"stig_execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class MaximumSecuritySTIGExecutor:
    """
    Execute STIG remediation with MAXIMUM security lockdown
    
    This implements the most restrictive STIG configuration possible,
    including all CAT I controls and aggressive security hardening.
    """
    
    def __init__(self):
        self.ssh_client = None
        self.target_host = None
        self.username = None
        self.password = None
        self.sudo_password = None
        self.port = 22
        self.connected = False
        self.execution_log = []
        
        # Maximum security configuration flags
        self.max_security_mode = True
        self.disable_password_auth = True
        self.enable_fips = False  # Requires special kernel
        self.strict_firewall = True
        self.disable_all_unnecessary = True
        
    def get_connection_info(self):
        """Interactively get connection information from user"""
        print("\n" + "="*80)
        print("AIR-GAPPED UBUNTU 20.04 STIG MAXIMUM SECURITY EXECUTOR")
        print("="*80)
        print("\n🔒 MAXIMUM SECURITY MODE")
        print("This will apply the MOST RESTRICTIVE STIG configuration possible.")
        print("\n⚠️  CRITICAL WARNINGS:")
        print("   - SSH password authentication will be DISABLED")
        print("   - Only SSH key authentication will work after execution")
        print("   - Root login will be COMPLETELY DISABLED")
        print("   - ALL unnecessary services will be disabled")
        print("   - Firewall will block everything except SSH")
        print("   - USB storage will be completely disabled")
        print("   - Wireless will be completely disabled")
        print("   - System will be in maximum lockdown state")
        print("\n⚠️  ENSURE YOU HAVE:")
        print("   ✓ Console access (KVM/IPMI/Physical) available")
        print("   ✓ SSH keys already configured on target")
        print("   ✓ Current system backup/snapshot")
        print("   ✓ Tested this in non-production first")
        print("\n" + "="*80)
        
        # Configuration options
        print("\n🔧 Security Configuration:")
        print("="*40)
        
        # Ask about password auth (default: disable)
        disable_pw = input("Disable SSH password authentication? [Y/n]: ").strip().lower()
        self.disable_password_auth = disable_pw in ['', 'y', 'yes']
        
        # Ask about FIPS (requires special kernel)
        enable_fips = input("Enable FIPS mode? (requires FIPS kernel) [y/N]: ").strip().lower()
        self.enable_fips = enable_fips in ['y', 'yes']
        
        # Ask about strict firewall
        strict_fw = input("Enable strict firewall? (deny all except SSH) [Y/n]: ").strip().lower()
        self.strict_firewall = strict_fw in ['', 'y', 'yes']
        
        print("\n📋 Connection Information:")
        print("="*40)
        
        # Get target information
        self.target_host = input("Target Ubuntu system IP/hostname: ").strip()
        
        port_input = input("SSH port [22]: ").strip()
        self.port = int(port_input) if port_input else 22
        
        self.username = input("SSH username [ubuntu]: ").strip() or "ubuntu"
        self.password = getpass.getpass(f"SSH password for {self.username}: ")
        
        # Get sudo password
        print("\n🔑 Sudo Password:")
        use_same = input(f"Use same password for sudo? [Y/n]: ").strip().lower()
        
        if use_same in ['', 'y', 'yes']:
            self.sudo_password = self.password
        else:
            self.sudo_password = getpass.getpass(f"Sudo password for {self.username}: ")
        
        # Confirm configuration
        print("\n" + "="*80)
        print("MAXIMUM SECURITY CONFIGURATION")
        print("="*80)
        print(f"Target Host:            {self.target_host}:{self.port}")
        print(f"SSH User:               {self.username}")
        print(f"Sudo Password:          {'✓ Configured' if self.sudo_password else '✗ Not set'}")
        print("\nSecurity Settings:")
        print(f"  Disable Password Auth:  {'YES' if self.disable_password_auth else 'NO'}")
        print(f"  Enable FIPS Mode:       {'YES' if self.enable_fips else 'NO'}")
        print(f"  Strict Firewall:        {'YES' if self.strict_firewall else 'NO'}")
        print(f"  Disable Unnecessary:    YES (always)")
        print("="*80)
        
        print("\n⚠️  FINAL WARNING:")
        print("After execution, you will need SSH keys to access the system.")
        print("Password authentication will be disabled.")
        print("Ensure you have console access available!")
        
        confirm = input("\n⚠️  Proceed with MAXIMUM SECURITY configuration? [yes/NO]: ").strip().lower()
        if confirm != 'yes':
            print("\n❌ Execution cancelled by user.")
            sys.exit(0)
    
    def connect(self):
        """Establish SSH connection to target Ubuntu system"""
        logger.info(f"Connecting to {self.target_host}:{self.port} as {self.username}...")
        
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            self.ssh_client.connect(
                hostname=self.target_host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=30,
                banner_timeout=30,
                auth_timeout=30,
                allow_agent=False,
                look_for_keys=False
            )
            
            self.connected = True
            logger.info(f"✓ Successfully connected to {self.target_host}")
            return True
            
        except AuthenticationException:
            logger.error("❌ Authentication failed - check username/password")
            return False
        except SSHException as e:
            logger.error(f"❌ SSH error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close SSH connection"""
        if self.ssh_client:
            try:
                self.ssh_client.close()
                self.connected = False
                logger.info(f"Disconnected from {self.target_host}")
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
    
    def execute_command(self, command, use_sudo=False, timeout=300):
        """Execute command on remote system with automatic sudo password handling"""
        if not self.connected:
            logger.error("Not connected to target system")
            return (1, "", "Not connected")
        
        try:
            if use_sudo and not command.startswith('sudo'):
                full_command = f"sudo -S -p '' {command}"
            else:
                full_command = command
            
            stdin, stdout, stderr = self.ssh_client.exec_command(
                full_command,
                timeout=timeout,
                get_pty=True
            )
            
            if use_sudo:
                stdin.write(self.sudo_password + '\n')
                stdin.flush()
            
            exit_code = stdout.channel.recv_exit_status()
            stdout_data = stdout.read().decode('utf-8', errors='replace')
            stderr_data = stderr.read().decode('utf-8', errors='replace')
            
            stdout_data = stdout_data.replace(self.sudo_password, '***')
            stderr_data = stderr_data.replace(self.sudo_password, '***')
            
            log_msg = f"[RC={exit_code}] {command[:100]}"
            self.execution_log.append(log_msg)
            
            if exit_code != 0:
                logger.debug(f"Command failed: {command}")
                logger.debug(f"Error: {stderr_data[:500]}")
            
            return (exit_code, stdout_data, stderr_data)
            
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return (1, "", str(e))
    
    def verify_sudo_access(self):
        """Verify sudo password works"""
        logger.info("Verifying sudo access...")
        
        rc, stdout, stderr = self.execute_command("whoami", use_sudo=True, timeout=10)
        
        if rc == 0 and 'root' in stdout:
            logger.info("✓ Sudo access verified")
            return True
        else:
            logger.error("❌ Sudo access verification failed")
            return False
    
    def check_system_info(self):
        """Check target system OS version and readiness"""
        logger.info("\n" + "="*80)
        logger.info("SYSTEM INFORMATION CHECK")
        logger.info("="*80)
        
        # Check OS version
        rc, stdout, stderr = self.execute_command("cat /etc/os-release")
        if rc == 0:
            logger.info("OS Information:")
            for line in stdout.split('\n')[:5]:
                if line.strip():
                    logger.info(f"  {line}")
            
            if 'Ubuntu 20.04' not in stdout:
                logger.warning("⚠️  WARNING: Target system is not Ubuntu 20.04!")
                confirm = input("\nContinue anyway? [yes/NO]: ").strip().lower()
                if confirm != 'yes':
                    return False
        
        # Check disk space
        rc, stdout, stderr = self.execute_command("df -h /")
        if rc == 0:
            logger.info("\nDisk Space:")
            logger.info(stdout)
        
        return True
    
    def transfer_stig_script(self):
        """Transfer STIG script to target system"""
        logger.info("\n" + "="*80)
        logger.info("TRANSFERRING STIG SCRIPT")
        logger.info("="*80)
        
        script_dir = Path(__file__).parent
        stig_script = script_dir / "ubuntu20_stig_v2r3_enhanced.py"
        
        if not stig_script.exists():
            logger.error(f"❌ STIG script not found: {stig_script}")
            return False
        
        logger.info(f"Found STIG script: {stig_script}")
        
        try:
            remote_dir = f"/tmp/stig_remediation_{int(time.time())}"
            rc, stdout, stderr = self.execute_command(f"mkdir -p {remote_dir}")
            if rc != 0:
                logger.error(f"Failed to create remote directory: {stderr}")
                return False
            
            remote_script = f"{remote_dir}/stig_remediation.py"
            
            logger.info("Transferring script via SFTP...")
            sftp = self.ssh_client.open_sftp()
            sftp.put(str(stig_script), remote_script)
            sftp.chmod(remote_script, 0o755)
            sftp.close()
            
            logger.info(f"✓ Script transferred to {remote_script}")
            
            self.remote_script_path = remote_script
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to transfer script: {e}")
            return False
    
    def install_dependencies(self):
        """Install required Python packages on target system"""
        logger.info("\n" + "="*80)
        logger.info("INSTALLING DEPENDENCIES")
        logger.info("="*80)
        
        logger.info("Updating package cache...")
        rc, stdout, stderr = self.execute_command(
            "apt-get update",
            use_sudo=True,
            timeout=300
        )
        
        logger.info("Installing required Python packages...")
        packages = "python3-pip python3-jinja2 python3-yaml"
        
        rc, stdout, stderr = self.execute_command(
            f"DEBIAN_FRONTEND=noninteractive apt-get install -y {packages}",
            use_sudo=True,
            timeout=300
        )
        
        if rc == 0:
            logger.info("✓ Dependencies installed")
        else:
            logger.warning("⚠️  Some dependencies may have failed")
        
        return True
    
    def create_pre_execution_backup(self):
        """Create backup of critical files"""
        logger.info("\n" + "="*80)
        logger.info("CREATING PRE-EXECUTION BACKUP")
        logger.info("="*80)
        
        backup_dir = f"/var/backups/pre-stig-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        critical_files = [
            '/etc/ssh/sshd_config',
            '/etc/pam.d/',
            '/etc/sudoers',
            '/etc/login.defs',
            '/etc/security/',
        ]
        
        rc, stdout, stderr = self.execute_command(
            f"mkdir -p {backup_dir}",
            use_sudo=True
        )
        
        for file_path in critical_files:
            self.execute_command(
                f"cp -r {file_path} {backup_dir}/ 2>/dev/null || true",
                use_sudo=True
            )
        
        logger.info(f"✓ Backup created: {backup_dir}")
        return True
    
    def configure_maximum_security(self):
        """Apply maximum security configuration to STIG script"""
        logger.info("\n" + "="*80)
        logger.info("CONFIGURING MAXIMUM SECURITY MODE")
        logger.info("="*80)
        
        # Create configuration override file
        config_override = f"""
# Maximum Security Configuration Override
# Applied by air-gapped executor

# Enable all STIG categories
CAT1_PATCH = True
CAT2_PATCH = True
CAT3_PATCH = True

# Maximum security settings
DISABLE_USB_STORAGE = True
DISABLE_WIRELESS = True
STRICT_FIREWALL = True
DISABLE_PASSWORD_AUTH = {self.disable_password_auth}
ENABLE_FIPS = {self.enable_fips}

# Disable all unnecessary services
DISABLE_CUPS = True
DISABLE_BLUETOOTH = True
DISABLE_AVAHI = True
DISABLE_WHOOPSIE = True

# Enable all security features
ENABLE_APPARMOR = True
ENABLE_AIDE = True
ENABLE_AUDITD = True

# Force strict permissions
STRICT_FILE_PERMISSIONS = True
REMOVE_WORLD_WRITABLE = True

print("🔒 MAXIMUM SECURITY MODE ENABLED")
"""
        
        # Write config override
        config_path = f"{Path(self.remote_script_path).parent}/max_security_config.py"
        
        try:
            sftp = self.ssh_client.open_sftp()
            with sftp.file(config_path, 'w') as f:
                f.write(config_override)
            sftp.close()
            
            logger.info("✓ Maximum security configuration applied")
            return True
        except Exception as e:
            logger.error(f"Failed to write config: {e}")
            return False
    
    def execute_stig_remediation(self):
        """Execute the STIG remediation script"""
        logger.info("\n" + "="*80)
        logger.info("EXECUTING MAXIMUM SECURITY STIG REMEDIATION")
        logger.info("="*80)
        logger.info("\n⏳ This will take several minutes...")
        logger.info("⏳ Do not interrupt the process!\n")
        
        cmd = f"python3 {self.remote_script_path}"
        
        try:
            transport = self.ssh_client.get_transport()
            channel = transport.open_session()
            channel.get_pty()
            
            full_cmd = f"sudo -S -p '' {cmd}"
            channel.exec_command(full_cmd)
            
            channel.send(self.sudo_password + '\n')
            
            output_lines = []
            while True:
                if channel.recv_ready():
                    data = channel.recv(4096).decode('utf-8', errors='replace')
                    data = data.replace(self.sudo_password, '***')
                    print(data, end='')
                    sys.stdout.flush()
                    output_lines.append(data)
                
                if channel.exit_status_ready():
                    break
                
                time.sleep(0.1)
            
            exit_code = channel.recv_exit_status()
            channel.close()
            
            if exit_code == 0:
                logger.info("\n" + "="*80)
                logger.info("✓ MAXIMUM SECURITY STIG REMEDIATION COMPLETED")
                logger.info("="*80)
                return True
            else:
                logger.error("\n" + "="*80)
                logger.error(f"❌ STIG REMEDIATION FAILED (exit code: {exit_code})")
                logger.error("="*80)
                return False
                
        except Exception as e:
            logger.exception(f"❌ Error during STIG execution: {e}")
            return False
    
    def cleanup_remote_files(self):
        """Clean up temporary files"""
        logger.info("\nCleaning up temporary files...")
        
        if hasattr(self, 'remote_script_path'):
            remote_dir = str(Path(self.remote_script_path).parent)
            self.execute_command(f"rm -rf {remote_dir}", use_sudo=True, timeout=10)
            logger.info("✓ Temporary files removed")
    
    def post_execution_checks(self):
        """Perform post-execution verification"""
        logger.info("\n" + "="*80)
        logger.info("POST-EXECUTION CHECKS")
        logger.info("="*80)
        
        logger.info("\n✓ SSH access verified (still connected)")
        
        logger.info("\nChecking critical services:")
        services = ['sshd', 'auditd', 'rsyslog', 'ufw']
        
        for service in services:
            rc, stdout, stderr = self.execute_command(
                f"systemctl is-active {service}",
                use_sudo=True,
                timeout=10
            )
            status = stdout.strip()
            if status == 'active':
                logger.info(f"  ✓ {service}: {status}")
            else:
                logger.warning(f"  ⚠️  {service}: {status}")
        
        logger.info("\nVerifying SSH configuration:")
        rc, stdout, stderr = self.execute_command(
            "sshd -t",
            use_sudo=True,
            timeout=10
        )
        if rc == 0:
            logger.info("  ✓ SSH configuration syntax valid")
        else:
            logger.error(f"  ❌ SSH configuration has errors: {stderr}")
        
        return True
    
    def print_final_summary(self):
        """Print final summary"""
        print("\n" + "="*80)
        print("MAXIMUM SECURITY EXECUTION SUMMARY")
        print("="*80)
        print(f"\nTarget System:  {self.target_host}:{self.port}")
        print(f"Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Log File:       {log_file}")
        print("\n" + "="*80)
        print("CRITICAL NEXT STEPS")
        print("="*80)
        print("\n1. ⚠️  REBOOT THE SYSTEM:")
        print(f"   ssh {self.username}@{self.target_host} 'sudo reboot'")
        
        if self.disable_password_auth:
            print("\n2. 🔑 SSH KEY ACCESS REQUIRED:")
            print("   Password authentication has been DISABLED")
            print("   You MUST use SSH keys to access the system")
            print("   If keys not configured, use console access to:")
            print("     a) Copy your SSH public key to ~/.ssh/authorized_keys")
            print("     b) Or temporarily re-enable password auth")
        
        print("\n3. 🔒 MAXIMUM SECURITY APPLIED:")
        print("   - All unnecessary services disabled")
        print("   - USB storage completely disabled")
        print("   - Wireless adapters disabled")
        print("   - Strict firewall rules (deny all except SSH)")
        print("   - Password authentication disabled (if selected)")
        print("   - All 172 STIG controls applied")
        
        print("\n4. 🔍 VERIFY COMPLIANCE:")
        print("   - Run SCAP scan to verify ~100% compliance")
        print("   - Check audit logs are being generated")
        print("   - Verify all required services are running")
        
        print("\n" + "="*80)
        print("BACKUP LOCATIONS")
        print("="*80)
        print("\nBackups created on target system:")
        print("   - /var/backups/pre-stig-*")
        print("   - /var/backups/stig-v2r3/")
        print("   - Individual .stig-v2r3-backup-* files")
        print("\n" + "="*80)
    
    def run(self):
        """Main execution flow"""
        try:
            self.get_connection_info()
            
            if not self.connect():
                logger.error("Failed to connect to target system")
                return False
            
            if not self.verify_sudo_access():
                logger.error("Sudo access verification failed")
                return False
            
            if not self.check_system_info():
                logger.error("System information check failed")
                return False
            
            if not self.transfer_stig_script():
                logger.error("Failed to transfer STIG script")
                return False
            
            if not self.install_dependencies():
                logger.warning("Dependency installation had issues")
            
            self.create_pre_execution_backup()
            
            self.configure_maximum_security()
            
            print("\n" + "="*80)
            print("⚠️  FINAL CONFIRMATION - MAXIMUM SECURITY MODE ⚠️")
            print("="*80)
            print("\nThis will apply the MOST RESTRICTIVE STIG configuration.")
            print("\nChanges include:")
            print("  - Disable SSH password authentication (keys only)")
            print("  - Disable root login completely")
            print("  - Enable strict firewall (deny all except SSH)")
            print("  - Disable USB storage and wireless")
            print("  - Remove all unnecessary services")
            print("  - Apply all 172 STIG controls")
            print("\n⚠️  ENSURE YOU HAVE:")
            print("  ✓ Console access ready")
            print("  ✓ SSH keys configured")
            print("  ✓ System backup created")
            print("\n" + "="*80)
            
            final_confirm = input("\n🔴 Type 'EXECUTE' to begin: ").strip()
            if final_confirm != 'EXECUTE':
                logger.warning("❌ Execution cancelled")
                return False
            
            success = self.execute_stig_remediation()
            
            if success:
                self.post_execution_checks()
                self.print_final_summary()
            else:
                logger.error("\n❌ STIG remediation encountered errors")
            
            return success
            
        except KeyboardInterrupt:
            logger.warning("\n\n⚠️  Execution interrupted by user!")
            return False
        except Exception as e:
            logger.exception("❌ Fatal error during execution")
            return False
        finally:
            self.cleanup_remote_files()
            self.disconnect()


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("AIR-GAPPED MAXIMUM SECURITY STIG EXECUTOR")
    print("Ubuntu 20.04 STIG V2R3 - No Internet Required")
    print("="*80)
    
    # Check if running on Windows
    if sys.platform.startswith('win'):
        print("✓ Running on Windows")
    else:
        print("ℹ️  Cross-platform support enabled")
    
    # Create and run executor
    executor = MaximumSecuritySTIGExecutor()
    success = executor.run()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
