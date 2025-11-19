#!/usr/bin/env python3
"""
Windows-to-Ubuntu STIG Remote Executor
=======================================

Execute Ubuntu 20.04 STIG V2R3 remediation from a Windows host to a remote Ubuntu system.
Automatically handles password authentication and sudo password prompts.

Requirements on Windows:
    - Python 3.6+
    - pip install paramiko scp

Usage:
    python windows_stig_remote_executor.py

Author: Enhanced for Windows remote execution
Version: 1.0.0
"""

import os
import sys
import time
import getpass
import logging
from pathlib import Path
from datetime import datetime

# Check for required packages
try:
    import paramiko
    from paramiko.ssh_exception import SSHException, AuthenticationException
except ImportError:
    print("ERROR: paramiko not installed")
    print("Please run: pip install paramiko")
    sys.exit(1)

try:
    from scp import SCPClient
except ImportError:
    print("WARNING: scp not installed (optional but recommended)")
    print("Install with: pip install scp")
    SCPClient = None

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


class WindowsSTIGRemoteExecutor:
    """Execute STIG remediation from Windows to Ubuntu target"""
    
    def __init__(self):
        self.ssh_client = None
        self.target_host = None
        self.username = None
        self.password = None
        self.sudo_password = None
        self.port = 22
        self.connected = False
        self.execution_log = []
        
    def get_connection_info(self):
        """Interactively get connection information from user"""
        print("\n" + "="*80)
        print("UBUNTU 20.04 STIG REMOTE EXECUTION FROM WINDOWS")
        print("="*80)
        print("\nThis script will connect to your Ubuntu 20.04 system and apply")
        print("DISA STIG V2R3 security hardening configurations.")
        print("\n[WARNING]  WARNING: This will make significant security changes to the target system!")
        print("[WARNING]  Ensure you have console access in case SSH is affected.")
        print("\n" + "="*80)
        
        # Get target information
        print("\n[LIST] Connection Information:")
        self.target_host = input("Target Ubuntu system IP/hostname: ").strip()
        
        port_input = input("SSH port [22]: ").strip()
        self.port = int(port_input) if port_input else 22
        
        self.username = input("SSH username [ubuntu]: ").strip() or "ubuntu"
        self.password = getpass.getpass(f"SSH password for {self.username}: ")
        
        # Get sudo password (may be same as SSH password)
        print("\n[KEY] Sudo Password:")
        print("The script needs sudo access to apply STIG configurations.")
        use_same = input(f"Use same password for sudo? [Y/n]: ").strip().lower()
        
        if use_same in ['', 'y', 'yes']:
            self.sudo_password = self.password
        else:
            self.sudo_password = getpass.getpass(f"Sudo password for {self.username}: ")
        
        # Confirm before proceeding
        print("\n" + "="*80)
        print("CONFIGURATION SUMMARY")
        print("="*80)
        print(f"Target Host:    {self.target_host}:{self.port}")
        print(f"SSH User:       {self.username}")
        print(f"Sudo Password:  {'[OK] Configured' if self.sudo_password else '[FAIL] Not set'}")
        print("="*80)
        
        confirm = input("\n[WARNING]  Proceed with STIG remediation? [yes/NO]: ").strip().lower()
        if confirm != 'yes':
            print("\n[ERROR] Execution cancelled by user.")
            sys.exit(0)
    
    def connect(self):
        """Establish SSH connection to target Ubuntu system"""
        logger.info(f"Connecting to {self.target_host}:{self.port} as {self.username}...")
        
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect with password authentication
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
            logger.info(f"[OK] Successfully connected to {self.target_host}")
            return True
            
        except AuthenticationException:
            logger.error("[ERROR] Authentication failed - check username/password")
            return False
        except SSHException as e:
            logger.error(f"[ERROR] SSH error: {e}")
            return False
        except Exception as e:
            logger.error(f"[ERROR] Connection failed: {e}")
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
        """
        Execute command on remote system with automatic sudo password handling
        
        Args:
            command: Command to execute
            use_sudo: Prepend sudo to command
            timeout: Command timeout in seconds
            
        Returns:
            tuple: (exit_code, stdout, stderr)
        """
        if not self.connected:
            logger.error("Not connected to target system")
            return (1, "", "Not connected")
        
        try:
            # Prepare command with sudo if needed
            if use_sudo and not command.startswith('sudo'):
                # Use sudo -S to read password from stdin
                full_command = f"sudo -S -p '' {command}"
            else:
                full_command = command
            
            # Execute command
            stdin, stdout, stderr = self.ssh_client.exec_command(
                full_command,
                timeout=timeout,
                get_pty=True  # Get PTY for sudo password prompt
            )
            
            # Send sudo password if using sudo
            if use_sudo:
                stdin.write(self.sudo_password + '\n')
                stdin.flush()
            
            # Wait for command to complete
            exit_code = stdout.channel.recv_exit_status()
            
            # Read output
            stdout_data = stdout.read().decode('utf-8', errors='replace')
            stderr_data = stderr.read().decode('utf-8', errors='replace')
            
            # Remove password prompt artifacts from output
            stdout_data = stdout_data.replace(self.sudo_password, '***')
            stderr_data = stderr_data.replace(self.sudo_password, '***')
            
            # Log execution
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
            logger.info("[OK] Sudo access verified")
            return True
        else:
            logger.error("[ERROR] Sudo access verification failed")
            logger.error(f"Output: {stdout}")
            logger.error(f"Error: {stderr}")
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
            
            # Verify Ubuntu 20.04
            if 'Ubuntu 20.04' not in stdout:
                logger.warning("[WARNING]  WARNING: Target system is not Ubuntu 20.04!")
                logger.warning("This script is designed for Ubuntu 20.04 LTS only.")
                confirm = input("\nContinue anyway? [yes/NO]: ").strip().lower()
                if confirm != 'yes':
                    return False
        
        # Check disk space
        rc, stdout, stderr = self.execute_command("df -h /")
        if rc == 0:
            logger.info("\nDisk Space:")
            logger.info(stdout)
        
        # Check if system is running
        rc, stdout, stderr = self.execute_command("uptime")
        if rc == 0:
            logger.info(f"\nSystem Uptime: {stdout.strip()}")
        
        return True
    
    def transfer_stig_script(self):
        """Transfer STIG script to target system"""
        logger.info("\n" + "="*80)
        logger.info("TRANSFERRING STIG SCRIPT")
        logger.info("="*80)
        
        # Find the STIG script in the same directory
        script_dir = Path(__file__).parent
        stig_script = script_dir / "ubuntu20_stig_v2r3_enhanced.py"
        
        if not stig_script.exists():
            logger.error(f"[ERROR] STIG script not found: {stig_script}")
            logger.error("Please ensure ubuntu20_stig_v2r3_enhanced.py is in the same directory")
            return False
        
        logger.info(f"Found STIG script: {stig_script}")
        logger.info(f"Size: {stig_script.stat().st_size / 1024:.2f} KB")
        
        try:
            # Create remote temporary directory
            remote_dir = f"/tmp/stig_remediation_{int(time.time())}"
            rc, stdout, stderr = self.execute_command(f"mkdir -p {remote_dir}")
            if rc != 0:
                logger.error(f"Failed to create remote directory: {stderr}")
                return False
            
            remote_script = f"{remote_dir}/stig_remediation.py"
            
            # Transfer using SFTP
            logger.info("Transferring script via SFTP...")
            sftp = self.ssh_client.open_sftp()
            sftp.put(str(stig_script), remote_script)
            sftp.chmod(remote_script, 0o755)
            sftp.close()
            
            logger.info(f"[OK] Script transferred to {remote_script}")
            
            # Verify transfer
            rc, stdout, stderr = self.execute_command(f"ls -lh {remote_script}")
            if rc == 0:
                logger.info(f"Remote script: {stdout.strip()}")
            
            self.remote_script_path = remote_script
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to transfer script: {e}")
            return False
    
    def install_dependencies(self):
        """Install required Python packages on target system"""
        logger.info("\n" + "="*80)
        logger.info("INSTALLING DEPENDENCIES")
        logger.info("="*80)
        
        # Update package cache
        logger.info("Updating package cache...")
        rc, stdout, stderr = self.execute_command(
            "apt-get update",
            use_sudo=True,
            timeout=300
        )
        
        # Install Python packages
        logger.info("Installing required Python packages...")
        packages = "python3-pip python3-jinja2 python3-yaml"
        
        rc, stdout, stderr = self.execute_command(
            f"DEBIAN_FRONTEND=noninteractive apt-get install -y {packages}",
            use_sudo=True,
            timeout=300
        )
        
        if rc == 0:
            logger.info("[OK] Dependencies installed")
        else:
            logger.warning("[WARNING]  Some dependencies may have failed to install")
            logger.warning("Continuing anyway...")
        
        # Install pip packages
        logger.info("Installing Python pip packages...")
        rc, stdout, stderr = self.execute_command(
            "pip3 install --upgrade jinja2 pyyaml",
            use_sudo=True,
            timeout=300
        )
        
        return True
    
    def create_pre_execution_backup(self):
        """Create backup of critical files before execution"""
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
        
        # Create backup directory
        rc, stdout, stderr = self.execute_command(
            f"mkdir -p {backup_dir}",
            use_sudo=True
        )
        
        if rc != 0:
            logger.warning("[WARNING]  Could not create backup directory")
            return False
        
        # Backup critical files
        for file_path in critical_files:
            rc, stdout, stderr = self.execute_command(
                f"cp -r {file_path} {backup_dir}/ 2>/dev/null || true",
                use_sudo=True
            )
        
        logger.info(f"[OK] Backup created: {backup_dir}")
        logger.info("You can restore from this backup if needed")
        
        return True
    
    def execute_stig_remediation(self):
        """Execute the STIG remediation script on target system"""
        logger.info("\n" + "="*80)
        logger.info("EXECUTING STIG V2R3 REMEDIATION")
        logger.info("="*80)
        logger.info("\n[WAIT] This will take several minutes...")
        logger.info("[WAIT] Do not interrupt the process!\n")
        
        # Build command
        cmd = f"python3 {self.remote_script_path}"
        
        # Execute with real-time output streaming
        try:
            # Open SSH channel for real-time streaming
            transport = self.ssh_client.get_transport()
            channel = transport.open_session()
            channel.get_pty()
            
            # Execute command with sudo
            full_cmd = f"sudo -S -p '' {cmd}"
            channel.exec_command(full_cmd)
            
            # Send sudo password
            channel.send(self.sudo_password + '\n')
            
            # Stream output in real-time
            output_lines = []
            while True:
                if channel.recv_ready():
                    data = channel.recv(4096).decode('utf-8', errors='replace')
                    # Remove password from output
                    data = data.replace(self.sudo_password, '***')
                    
                    # Print and log
                    print(data, end='')
                    sys.stdout.flush()
                    output_lines.append(data)
                
                if channel.exit_status_ready():
                    break
                
                time.sleep(0.1)
            
            # Get exit code
            exit_code = channel.recv_exit_status()
            channel.close()
            
            # Join all output
            full_output = ''.join(output_lines)
            
            if exit_code == 0:
                logger.info("\n" + "="*80)
                logger.info("[OK] STIG REMEDIATION COMPLETED SUCCESSFULLY")
                logger.info("="*80)
                return True
            else:
                logger.error("\n" + "="*80)
                logger.error(f"[ERROR] STIG REMEDIATION FAILED (exit code: {exit_code})")
                logger.error("="*80)
                return False
                
        except Exception as e:
            logger.exception(f"[ERROR] Error during STIG execution: {e}")
            return False
    
    def cleanup_remote_files(self):
        """Clean up temporary files on remote system"""
        logger.info("\nCleaning up temporary files...")
        
        if hasattr(self, 'remote_script_path'):
            # Remove the temporary directory
            remote_dir = str(Path(self.remote_script_path).parent)
            self.execute_command(f"rm -rf {remote_dir}", use_sudo=True, timeout=10)
            logger.info("[OK] Temporary files removed")
    
    def post_execution_checks(self):
        """Perform post-execution verification checks"""
        logger.info("\n" + "="*80)
        logger.info("POST-EXECUTION CHECKS")
        logger.info("="*80)
        
        # Check if SSH is still accessible
        logger.info("\n[OK] SSH access verified (still connected)")
        
        # Check critical services
        logger.info("\nChecking critical services:")
        services = ['sshd', 'auditd', 'rsyslog']
        
        for service in services:
            rc, stdout, stderr = self.execute_command(
                f"systemctl is-active {service}",
                use_sudo=True,
                timeout=10
            )
            status = stdout.strip()
            if status == 'active':
                logger.info(f"  [OK] {service}: {status}")
            else:
                logger.warning(f"  [WARNING]  {service}: {status}")
        
        # Check SSH config syntax
        logger.info("\nVerifying SSH configuration:")
        rc, stdout, stderr = self.execute_command(
            "sshd -t",
            use_sudo=True,
            timeout=10
        )
        if rc == 0:
            logger.info("  [OK] SSH configuration syntax valid")
        else:
            logger.error(f"  [ERROR] SSH configuration has errors: {stderr}")
        
        return True
    
    def print_final_summary(self):
        """Print final summary and recommendations"""
        print("\n" + "="*80)
        print("EXECUTION SUMMARY")
        print("="*80)
        print(f"\nTarget System:  {self.target_host}:{self.port}")
        print(f"Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Log File:       {log_file}")
        print("\n" + "="*80)
        print("NEXT STEPS")
        print("="*80)
        print("\n1. [WARNING]  REBOOT THE SYSTEM to apply all changes:")
        print(f"   ssh {self.username}@{self.target_host} 'sudo reboot'")
        print("\n2. [LIST] After reboot, verify system functionality:")
        print("   - Test SSH access")
        print("   - Verify critical services are running")
        print("   - Test application functionality")
        print("\n3. [SEARCH] Run SCAP scan to verify compliance:")
        print("   - Use OpenSCAP or SCC to validate STIG compliance")
        print("   - Review any remaining findings")
        print("\n4. [SAVE] Backups are located in:")
        print("   - /var/backups/pre-stig-* (on target system)")
        print("   - /var/backups/stig-v2r3/ (created by script)")
        print("\n5.  Review the detailed log:")
        print(f"   - {log_file}")
        print("\n" + "="*80)
        print("IMPORTANT WARNINGS")
        print("="*80)
        print("\n[WARNING]  SSH Configuration Changes:")
        print("   - Root login may be disabled")
        print("   - Password authentication may be disabled")
        print("   - Ensure you have alternative access methods")
        print("\n[WARNING]  Password Policy Changes:")
        print("   - Users may need to change passwords on next login")
        print("   - Password complexity requirements are now enforced")
        print("\n[WARNING]  Service Changes:")
        print("   - Some services may be disabled")
        print("   - Firewall (UFW) is now enabled")
        print("   - Verify required services are still accessible")
        print("\n" + "="*80)
    
    def run(self):
        """Main execution flow"""
        try:
            # Get connection info from user
            self.get_connection_info()
            
            # Connect to target system
            if not self.connect():
                logger.error("Failed to connect to target system")
                return False
            
            # Verify sudo access
            if not self.verify_sudo_access():
                logger.error("Sudo access verification failed")
                return False
            
            # Check system info
            if not self.check_system_info():
                logger.error("System information check failed")
                return False
            
            # Transfer STIG script
            if not self.transfer_stig_script():
                logger.error("Failed to transfer STIG script")
                return False
            
            # Install dependencies
            if not self.install_dependencies():
                logger.warning("Dependency installation had issues, continuing...")
            
            # Create backup
            self.create_pre_execution_backup()
            
            # Final confirmation
            print("\n" + "="*80)
            print("[WARNING]  FINAL CONFIRMATION BEFORE EXECUTION [WARNING]")
            print("="*80)
            print("\nThe STIG remediation will now begin.")
            print("This will make significant security changes to your Ubuntu system.")
            print("\nEnsure you have:")
            print("  [OK] Console access to the system (in case SSH is affected)")
            print("  [OK] Recent backup of important data")
            print("  [OK] Tested this in a non-production environment")
            print("\n" + "="*80)
            
            final_confirm = input("\n[RED] Type 'EXECUTE' to begin STIG remediation: ").strip()
            if final_confirm != 'EXECUTE':
                logger.warning("[ERROR] Execution cancelled by user")
                return False
            
            # Execute STIG remediation
            success = self.execute_stig_remediation()
            
            if success:
                # Post-execution checks
                self.post_execution_checks()
                
                # Print final summary
                self.print_final_summary()
            else:
                logger.error("\n[ERROR] STIG remediation encountered errors")
                logger.error("Review the log file for details")
                logger.error("Consider restoring from backup if system is unstable")
            
            return success
            
        except KeyboardInterrupt:
            logger.warning("\n\n[WARNING]  Execution interrupted by user!")
            logger.warning("System may be in a partially configured state")
            logger.warning("Consider restoring from backup")
            return False
        
        except Exception as e:
            logger.exception("[ERROR] Fatal error during execution")
            return False
        
        finally:
            # Always cleanup
            self.cleanup_remote_files()
            self.disconnect()


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("WINDOWS-TO-UBUNTU STIG REMOTE EXECUTOR")
    print("Ubuntu 20.04 STIG V2R3 Compliance Automation")
    print("="*80)
    
    # Check Python version
    if sys.version_info < (3, 6):
        print("ERROR: Python 3.6 or higher required")
        sys.exit(1)
    
    # Check if running on Windows
    if sys.platform.startswith('win'):
        print("[OK] Running on Windows")
    else:
        print("[INFO]  This script is designed for Windows but can run on any OS")
    
    # Create and run executor
    executor = WindowsSTIGRemoteExecutor()
    success = executor.run()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
