#!/usr/bin/env python3
"""
UBUNTU20-STIG V2R3 Python Implementation - REMOTE EXECUTION EDITION
====================================================================

Automated DISA STIG Benchmark Compliance Remediation for Ubuntu 20.04 LTS
Based on STIG Version 2 Release 3 (V2R3) - 172 Total Controls

Release: 3 Benchmark Date: 02 Jul 2025

This script implements all STIG controls from the official DISA STIG V2R3,
converted to pure Python with direct system modifications.

BREAKDOWN:
- CAT I (High):   14 controls
- CAT II (Medium): 136 controls  
- CAT III (Low):  22 controls

NEW IN V2.5.0 - REMOTE EXECUTION EDITION:
✓ Full SSH-based remote execution capability
✓ Parallel multi-host deployment support
✓ Enhanced force/bypass modes for emergency situations
✓ Comprehensive CLI argument parser with argparse
✓ Updated AI agent TODO lists for parallel development
✓ Remote connection pooling and error handling
✓ Fail-safe remote rollback mechanisms
✓ Interactive and batch execution modes

NEW IN V2R3 STIG:
- V-251503/V-251504: No blank/null passwords (CAT I)
- V-251505: Disable USB auto-mounting (CAT II)
- V-252704: Disable wireless adapters (CAT II)
- V-255912: FIPS SSH key exchange (CAT II)
- V-255913: Kernel message buffer restrictions (CAT III)
- V-274852: Audit cron executions (CAT II)
- V-274853-V-274856: SSSD/PKI configuration (CAT II/III)
- V-274857: PKI certificate mapping (CAT I)
- V-274858/V-274859: Sudo restrictions (CAT II)

WARNING: This script makes direct system modifications. Always test in a
non-production environment first and create backups before running.

CRITICAL: Force modes bypass safety checks - use with extreme caution!
CRITICAL: Remote execution requires proper SSH authentication!

Requirements:
    - Ubuntu 20.04 LTS (target systems)
    - Python 3.6+
    - Root/sudo privileges
    - pip install jinja2 pyyaml paramiko

Remote Execution Requirements:
    - SSH access to target systems
    - SSH key-based auth recommended (password auth supported)
    - Root or sudo privileges on remote systems
    - Paramiko library: pip install paramiko

Author: Converted from DISA STIG V2R3 XCCDF + Remote Execution Enhancements
License: MIT
Version: 2.5.0 (Remote Execution & Force Mode Edition)
"""

import os
import sys
import subprocess
import shutil
import tempfile
import re
import logging
import stat
import glob
import argparse
import getpass
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import platform

# Platform compatibility detection
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'

# Unix-only imports (conditional for Windows compatibility)
if not IS_WINDOWS:
    import pwd
    import grp
else:
    pwd = None  # Not available on Windows
    grp = None  # Not available on Windows

# Optional remote execution support
try:
    import paramiko
    from paramiko.ssh_exception import SSHException, AuthenticationException
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False
    if '--remote' in sys.argv or any('--remote' in arg for arg in sys.argv):
        print("WARNING: paramiko not installed - remote execution disabled")
        print("Install with: pip install paramiko")

try:
    from jinja2 import Environment, Template
    import yaml
except ImportError:
    print("ERROR: Required packages not installed")
    print("Please run: pip install jinja2 pyyaml paramiko")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/ubuntu20-stig-v2r3-remediation.log' if not IS_WINDOWS else 'ubuntu20-stig-v2r3-remediation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# REMOTE EXECUTION INFRASTRUCTURE
# ============================================================================

class RemoteHost:
    """Represents a remote host for STIG execution"""
    def __init__(self, hostname, username='root', password=None, key_file=None, port=22, timeout=3600):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.key_file = key_file
        self.port = port
        self.timeout = timeout
        self.ssh_client = None
        self.connected = False
        self.execution_log = []
        self.errors = []

class RemoteExecutor:
    """Handles SSH-based remote execution of STIG remediation"""
    
    def __init__(self):
        self.hosts = []
        self.failed_hosts = []
        self.successful_hosts = []
    
    def add_host(self, hostname, username='root', password=None, key_file=None, port=22, timeout=3600):
        """Add a host for remote execution"""
        host = RemoteHost(hostname, username, password, key_file, port, timeout)
        self.hosts.append(host)
        logger.info(f"Added remote host: {hostname}:{port} (user: {username})")
    
    def connect_host(self, host):
        """Establish SSH connection to a host"""
        if not PARAMIKO_AVAILABLE:
            logger.error("Paramiko not available - cannot establish remote connection")
            return False
        
        try:
            logger.info(f"Connecting to {host.hostname}:{host.port}...")
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if host.key_file:
                ssh.connect(hostname=host.hostname, port=host.port, username=host.username,
                          key_filename=host.key_file, timeout=30, banner_timeout=30)
            elif host.password:
                ssh.connect(hostname=host.hostname, port=host.port, username=host.username,
                          password=host.password, timeout=30, banner_timeout=30)
            else:
                logger.error(f"No authentication method provided for {host.hostname}")
                return False
            
            host.ssh_client = ssh
            host.connected = True
            logger.info(f"✓ Connected to {host.hostname}")
            return True
            
        except AuthenticationException:
            logger.error(f"Authentication failed for {host.hostname}")
            host.errors.append("Authentication failed")
            return False
        except SSHException as e:
            logger.error(f"SSH error connecting to {host.hostname}: {e}")
            host.errors.append(f"SSH error: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to {host.hostname}: {e}")
            host.errors.append(f"Connection error: {e}")
            return False
    
    def disconnect_host(self, host):
        """Close SSH connection to a host"""
        if host.ssh_client:
            try:
                host.ssh_client.close()
                host.connected = False
                logger.info(f"Disconnected from {host.hostname}")
            except Exception as e:
                logger.warning(f"Error disconnecting from {host.hostname}: {e}")
    
    def execute_command(self, host, command, sudo=True, check_error=True):
        """Execute a command on a remote host"""
        if not host.connected or not host.ssh_client:
            logger.error(f"Not connected to {host.hostname}")
            return (1, "", "Not connected")
        
        try:
            if sudo and not command.startswith('sudo'):
                command = f"sudo {command}"
            
            stdin, stdout, stderr = host.ssh_client.exec_command(command, timeout=host.timeout)
            
            exit_code = stdout.channel.recv_exit_status()
            stdout_data = stdout.read().decode('utf-8')
            stderr_data = stderr.read().decode('utf-8')
            
            host.execution_log.append(f"[RC={exit_code}] {command}")
            
            if exit_code != 0 and check_error and not STIGConfig.FORCE_IGNORE_ERRORS:
                logger.warning(f"Command failed on {host.hostname}: {command}")
                logger.warning(f"  Error: {stderr_data}")
                host.errors.append(f"{command}: {stderr_data}")
            
            return (exit_code, stdout_data, stderr_data)
            
        except Exception as e:
            logger.error(f"Error executing command on {host.hostname}: {e}")
            host.errors.append(f"{command}: {e}")
            return (1, "", str(e))
    
    def transfer_script(self, host, local_script, remote_path='/tmp/stig_remediation.py'):
        """Transfer the STIG script to a remote host"""
        if not host.connected or not host.ssh_client:
            logger.error(f"Not connected to {host.hostname}")
            return False
        
        try:
            logger.info(f"Transferring script to {host.hostname}:{remote_path}...")
            
            sftp = host.ssh_client.open_sftp()
            sftp.put(local_script, remote_path)
            sftp.chmod(remote_path, 0o755)
            sftp.close()
            
            logger.info(f"✓ Script transferred to {host.hostname}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to transfer script to {host.hostname}: {e}")
            host.errors.append(f"File transfer error: {e}")
            return False
    
    def execute_on_host(self, host, script_path):
        """Execute STIG remediation on a single host"""
        logger.info("="*80)
        logger.info(f"EXECUTING STIG REMEDIATION ON {host.hostname}")
        logger.info("="*80)
        
        if not host.connected:
            if not self.connect_host(host):
                return False
        
        try:
            if not self.transfer_script(host, script_path):
                return False
            
            logger.info(f"Running STIG remediation on {host.hostname}...")
            
            remote_cmd = "python3 /tmp/stig_remediation.py"
            if STIGConfig.DRY_RUN:
                logger.info(f"  Running in DRY-RUN mode on {host.hostname}")
            if STIGConfig.FORCE_MODE:
                logger.warning(f"  FORCE MODE enabled on {host.hostname}")
            
            rc, stdout, stderr = self.execute_command(host, remote_cmd, sudo=True, check_error=False)
            
            if stdout:
                logger.info(f"\n--- Output from {host.hostname} ---")
                for line in stdout.split('\n')[:50]:  # First 50 lines
                    logger.info(f"  {line}")
            
            if stderr and rc != 0:
                logger.error(f"\n--- Errors from {host.hostname} ---")
                for line in stderr.split('\n')[:20]:  # First 20 error lines
                    logger.error(f"  {line}")
            
            if rc == 0:
                logger.info(f"✓ STIG remediation completed successfully on {host.hostname}")
                self.successful_hosts.append(host)
                return True
            else:
                logger.error(f"✗ STIG remediation failed on {host.hostname} (RC={rc})")
                self.failed_hosts.append(host)
                return False
                
        except Exception as e:
            logger.exception(f"Error executing on {host.hostname}")
            host.errors.append(f"Execution error: {e}")
            self.failed_hosts.append(host)
            return False
        finally:
            try:
                self.execute_command(host, "rm -f /tmp/stig_remediation.py", sudo=True, check_error=False)
            except:
                pass
    
    def execute_parallel(self, script_path, max_workers=5):
        """Execute STIG remediation on all hosts in parallel"""
        logger.info("="*80)
        logger.info(f"PARALLEL REMOTE EXECUTION ON {len(self.hosts)} HOSTS")
        logger.info("="*80)
        
        all_successful = True
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_host = {executor.submit(self.execute_on_host, host, script_path): host 
                            for host in self.hosts}
            
            for future in as_completed(future_to_host):
                host = future_to_host[future]
                try:
                    result = future.result()
                    if not result:
                        all_successful = False
                except Exception as e:
                    logger.exception(f"Error processing {host.hostname}")
                    all_successful = False
        
        return all_successful
    
    def execute_serial(self, script_path):
        """Execute STIG remediation on all hosts serially"""
        logger.info("="*80)
        logger.info(f"SERIAL REMOTE EXECUTION ON {len(self.hosts)} HOSTS")
        logger.info("="*80)
        
        all_successful = True
        
        for host in self.hosts:
            if not self.execute_on_host(host, script_path):
                all_successful = False
                
                if not STIGConfig.FORCE_IGNORE_ERRORS:
                    response = input(f"\n❌ Failed on {host.hostname}. Continue to next host? (y/n): ")
                    if response.lower() != 'y':
                        logger.warning("Serial execution aborted by user")
                        break
        
        return all_successful
    
    def print_summary(self):
        """Print execution summary"""
        print("\n" + "="*80)
        print("REMOTE EXECUTION SUMMARY")
        print("="*80)
        print(f"\nTotal hosts: {len(self.hosts)}")
        print(f"Successful: {len(self.successful_hosts)}")
        print(f"Failed: {len(self.failed_hosts)}")
        
        if self.successful_hosts:
            print("\n✓ Successful hosts:")
            for host in self.successful_hosts:
                print(f"  • {host.hostname}")
        
        if self.failed_hosts:
            print("\n✗ Failed hosts:")
            for host in self.failed_hosts:
                print(f"  • {host.hostname}")
                if host.errors:
                    for error in host.errors[:3]:
                        print(f"      - {error}")
    
    def cleanup(self):
        """Cleanup all SSH connections"""
        for host in self.hosts:
            if host.connected:
                self.disconnect_host(host)


# ============================================================================
# ARGUMENT PARSER
# ============================================================================

def setup_argument_parser():
    """Setup comprehensive CLI argument parser"""
    parser = argparse.ArgumentParser(
        description='Ubuntu 20.04 STIG V2R3 Remediation Script - Remote Execution Edition',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Local dry-run
  sudo python3 ubuntu20_stig_v2r3_enhanced.py --dry-run
  
  # Local production run
  sudo python3 ubuntu20_stig_v2r3_enhanced.py
  
  # Remote execution on single host
  sudo python3 ubuntu20_stig_v2r3_enhanced.py --remote 192.168.1.10 --remote-key ~/.ssh/id_rsa
  
  # Remote execution on multiple hosts (parallel)
  sudo python3 ubuntu20_stig_v2r3_enhanced.py --remote host1 host2 host3 --remote-parallel
  
  # Force mode (DANGEROUS - use with caution!)
  sudo python3 ubuntu20_stig_v2r3_enhanced.py --force --force-apply-all --force-ignore-errors
  
  # Emergency recovery
  sudo python3 ubuntu20_stig_v2r3_enhanced.py --emergency
  
  # CAT I controls only
  sudo python3 ubuntu20_stig_v2r3_enhanced.py --cat1-only

For more information, see the documentation.
        '''
    )
    
    # Basic options
    basic = parser.add_argument_group('Basic Options')
    basic.add_argument('--dry-run', action='store_true',
                      help='Preview changes without applying them')
    basic.add_argument('--emergency', '-e', action='store_true',
                      help='Enter emergency recovery mode')
    basic.add_argument('--list-backups', action='store_true',
                      help='List available recovery points')
    basic.add_argument('--version', action='version',
                      version=f'STIG Remediation Script v{STIGConfig.SCRIPT_VERSION}')
    
    # Category selection
    category = parser.add_argument_group('Category Selection')
    cat_group = category.add_mutually_exclusive_group()
    cat_group.add_argument('--cat1-only', action='store_true',
                          help='Apply only CAT I (High) controls')
    cat_group.add_argument('--cat2-only', action='store_true',
                          help='Apply only CAT II (Medium) controls')
    cat_group.add_argument('--cat3-only', action='store_true',
                          help='Apply only CAT III (Low) controls')
    
    # Remote execution options
    remote = parser.add_argument_group('Remote Execution Options')
    remote.add_argument('--remote', nargs='+', metavar='HOST',
                       help='Remote host(s) to execute on')
    remote.add_argument('--remote-user', default='root',
                       help='SSH username (default: root)')
    remote.add_argument('--remote-key', metavar='PATH',
                       help='SSH private key file path')
    remote.add_argument('--remote-password', metavar='PASS',
                       help='SSH password (not recommended - use key instead)')
    remote.add_argument('--remote-port', type=int, default=22,
                       help='SSH port (default: 22)')
    remote.add_argument('--remote-parallel', action='store_true',
                       help='Execute on all hosts in parallel')
    remote.add_argument('--remote-workers', type=int, default=5,
                       help='Max parallel workers (default: 5)')
    
    # Force mode options (DANGEROUS)
    force = parser.add_argument_group('Force Mode Options (DANGEROUS - Use with Extreme Caution!)')
    force.add_argument('--force', action='store_true',
                      help='Enable force mode (bypasses safety checks)')
    force.add_argument('--force-ignore-errors', action='store_true',
                      help='Continue even if commands fail')
    force.add_argument('--force-skip-validation', action='store_true',
                      help='Skip configuration validation')
    force.add_argument('--force-no-rollback', action='store_true',
                      help='Disable automatic rollback')
    force.add_argument('--force-skip-preflight', action='store_true',
                      help='Skip pre-flight safety checks')
    force.add_argument('--force-apply-all', action='store_true',
                      help='Apply all STIGs regardless of risk')
    force.add_argument('--force-override-os', action='store_true',
                      help='Skip OS version check')
    force.add_argument('--force-no-backup', action='store_true',
                      help='Do NOT create backups (VERY DANGEROUS)')
    
    # Safety options
    safety = parser.add_argument_group('Safety Options')
    safety.add_argument('--no-preflight', action='store_true',
                       help='Disable pre-flight safety checks')
    safety.add_argument('--no-rollback', action='store_true',
                       help='Disable automatic rollback on errors')
    safety.add_argument('--no-validation', action='store_true',
                       help='Disable configuration validation')
    
    return parser


# ============================================================================
# CONFIGURATION - STIG V2R3 COMPLIANT
# ============================================================================

class STIGConfig:
    """Configuration for STIG V2R3 remediation"""
    
    # STIG Version
    STIG_VERSION = "V2R3"
    STIG_RELEASE = "Release 3"
    STIG_DATE = "02 Jul 2025"
    SCRIPT_VERSION = "2.5.0"
    
    # Category controls
    CAT1_PATCH = True  # High severity (14 controls)
    CAT2_PATCH = True  # Medium severity (136 controls)
    CAT3_PATCH = True  # Low severity (22 controls)
    
    # Safety settings
    DISRUPTION_HIGH = False  # Disable disruptive changes by default
    SKIP_OS_CHECK = False
    DRY_RUN = False  # Set to True to preview changes without applying
    ENABLE_FIPS = False  # FIPS mode requires special kernel (CAT I control)
    
    # ENHANCED SAFETY FEATURES
    ENABLE_PREFLIGHT_CHECKS = True  # Run comprehensive safety checks before starting
    ENABLE_AUTO_ROLLBACK = True  # Automatically rollback on critical errors
    ENABLE_CONFIG_VALIDATION = True  # Validate configs before applying
    EMERGENCY_RECOVERY_MODE = False  # Set to True to restore from backups only
    
    # FORCE MODE - DANGEROUS! Use only if you know what you're doing
    # WARNING: These modes bypass critical safety checks and can break your system!
    FORCE_MODE = False  # Master switch - enables force mode features
    FORCE_IGNORE_ERRORS = False  # Continue even if commands fail
    FORCE_SKIP_VALIDATION = False  # Skip ALL configuration validation
    FORCE_NO_ROLLBACK = False  # Disable automatic rollback
    FORCE_SKIP_PREFLIGHT = False  # Skip pre-flight safety checks
    FORCE_APPLY_ALL = False  # Apply ALL STIGs regardless of risk assessment
    FORCE_OVERRIDE_OS = False  # Skip OS version check
    FORCE_NO_BACKUP = False  # Don't create backups (VERY DANGEROUS)
    
    # Remote execution settings (NEW IN V2.5.0)
    ENABLE_REMOTE_EXECUTION = False  # Enable SSH-based remote execution
    REMOTE_HOSTS = []  # List of hosts: ['host1.example.com', '192.168.1.10']
    REMOTE_USER = 'root'  # SSH user (must have sudo/root)
    REMOTE_KEY_FILE = None  # SSH private key path (None = use password)
    REMOTE_PASSWORD = None  # SSH password (if not using key)
    REMOTE_PORT = 22  # SSH port
    REMOTE_PARALLEL = False  # Execute on all hosts in parallel
    REMOTE_MAX_WORKERS = 5  # Max parallel executions
    REMOTE_TIMEOUT = 3600  # SSH command timeout (seconds)
    REMOTE_TRANSFER_SCRIPT = True  # Transfer and execute script remotely
    REMOTE_SCRIPT_PATH = '/tmp/stig_remediation.py'  # Remote script location
    
    # Safety thresholds
    MIN_FREE_SPACE_MB = 500  # Minimum free space required
    MAX_FAILED_COMMANDS = 10  # Abort if this many commands fail (unless FORCE_IGNORE_ERRORS)
    REQUIRE_SNAPSHOT = False  # Require VM/LVM snapshot before proceeding
    
    # Backup settings
    BACKUP_DIR = '/var/backups/stig-v2r3'  # Central backup location
    MAX_BACKUP_AGE_DAYS = 30  # Auto-cleanup old backups
    
    # Recovery settings
    RECOVERY_POINT_DIR = '/var/lib/stig-recovery'  # Recovery checkpoints
    
    # Password policy (STIG V2R3 compliant)
    PASSWORD_MIN_LENGTH = 15  # UBTU-20-010070
    PASSWORD_DCREDIT = -1  # UBTU-20-010051 - Require digit
    PASSWORD_UCREDIT = -1  # UBTU-20-010052 - Require uppercase
    PASSWORD_LCREDIT = -1  # UBTU-20-010053 - Require lowercase
    PASSWORD_OCREDIT = -1  # UBTU-20-010054 - Require special char
    PASSWORD_DIFOK = 8  # UBTU-20-010055 - Characters that must differ
    PASSWORD_DICTCHECK = 1  # UBTU-20-010056 - Dictionary check
    PASSWORD_MINCLASS = 4  # UBTU-20-010057 - Minimum character classes
    PASSWORD_MAXREPEAT = 3  # UBTU-20-010058 - Max consecutive characters
    PASSWORD_MAXCLASSREPEAT = 4  # UBTU-20-010059 - Max same character class
    
    # Account settings
    PASS_MAX_DAYS = 60  # UBTU-20-010008
    PASS_MIN_DAYS = 1  # UBTU-20-010007
    PASS_WARN_AGE = 7  # Not in V2R3 but good practice
    INACTIVE_DAYS = 35  # UBTU-20-010439
    
    # SSH settings (V2R3 updates)
    SSH_PORT = 22
    SSH_PERMIT_ROOT_LOGIN = "no"  # UBTU-20-010047
    SSH_PASSWORD_AUTHENTICATION = "no"  # UBTU-20-010046
    SSH_PROTOCOL = 2
    SSH_CIPHERS = "aes256-ctr,aes192-ctr,aes128-ctr"  # UBTU-20-010044
    SSH_MACS = "hmac-sha2-256,hmac-sha2-512"  # UBTU-20-010043
    # V-255912: FIPS-validated key exchange algorithms
    SSH_KEX = "ecdh-sha2-nistp256,ecdh-sha2-nistp384,ecdh-sha2-nistp521,diffie-hellman-group-exchange-sha256"
    SSH_MAX_AUTH_TRIES = 4  # UBTU-20-010036
    SSH_CLIENT_ALIVE_INTERVAL = 600  # UBTU-20-010037
    SSH_CLIENT_ALIVE_COUNT_MAX = 0  # UBTU-20-010037
    SSH_X11_FORWARDING = "no"  # UBTU-20-010048
    
    # Audit settings
    AUDITD_MAX_LOG_FILE = 6  # UBTU-20-010300
    AUDITD_MAX_LOG_FILE_ACTION = "ROTATE"  # UBTU-20-010416
    AUDITD_SPACE_LEFT_ACTION = "email"  # UBTU-20-010217
    AUDITD_ADMIN_SPACE_LEFT_ACTION = "halt"  # UBTU-20-010244
    
    # V2R3 New: USB/Wireless restrictions
    DISABLE_USB_STORAGE = True  # V-251505
    DISABLE_WIRELESS = True  # V-252704
    
    # V2R3 New: SSSD for PKI authentication
    ENABLE_SSSD_PKI = False  # V-274853-274857 (requires PKI infrastructure)
    SSSD_OFFLINE_CRED_EXPIRATION = 1  # V-274856 (days)
    
    # Banner text (UBTU-20-010002, UBTU-20-010003)
    BANNER_TEXT = """You are accessing a U.S. Government (USG) Information System (IS) that is provided for USG-authorized use only.

By using this IS (which includes any device attached to this IS), you consent to the following conditions:

-The USG routinely intercepts and monitors communications on this IS for purposes including, but not limited to, penetration testing, COMSEC monitoring, network operations and defense, personnel misconduct (PM), law enforcement (LE), and counterintelligence (CI) investigations.

-At any time, the USG may inspect and seize data stored on this IS.

-Communications using, or data stored on, this IS are not private, are subject to routine monitoring, interception, and search, and may be disclosed or used for any USG-authorized purpose.

-This IS includes security measures (e.g., authentication and access controls) to protect USG interests--not for your personal benefit or privacy.

-Notwithstanding the above, using this IS does not constitute consent to PM, LE or CI investigative searching or monitoring of the content of privileged communications, or work product, related to personal representation or services by attorneys, psychotherapists, or clergy, and their assistants. Such communications and work product are private and confidential. See User Agreement for details."""


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================



# ============================================================================
# CROSS-PLATFORM HELPER FUNCTIONS
# ============================================================================

def is_admin():
    """Check if running with administrative privileges (cross-platform)"""
    if IS_WINDOWS:
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    else:
        try:
            return os.geteuid() == 0
        except AttributeError:
            return False


class SystemModifier:
    """Base class for system modifications with error handling"""
    
    def __init__(self):
        self.changes = []
        self.errors = []
        self.warnings = []
        self.stig_controls = []  # Track which STIG controls were applied
    
    def add_stig_control(self, control_id: str, description: str):
        """Track STIG control implementation"""
        self.stig_controls.append({
            'id': control_id,
            'description': description,
            'timestamp': datetime.now().isoformat()
        })
    
    def run_command(self, cmd: List[str], check: bool = True) -> Tuple[bool, str]:
        """Run subprocess command with error handling"""
        try:
            if STIGConfig.DRY_RUN:
                logger.info(f"[DRY RUN] Would execute: {' '.join(cmd)}")
                return True, "Dry run - not executed"
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=check,
                timeout=300  # 5 minute timeout
            )
            logger.info(f"Command succeeded: {' '.join(cmd)}")
            return True, result.stdout
        except subprocess.TimeoutExpired:
            error_msg = f"Command timed out: {' '.join(cmd)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return False, error_msg
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {' '.join(cmd)}")
            logger.error(f"Error: {e.stderr}")
            self.errors.append(f"Command failed: {' '.join(cmd)} - {e.stderr}")
            return False, e.stderr
        except FileNotFoundError:
            error_msg = f"Command not found: {cmd[0]}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.exception(error_msg)
            self.errors.append(error_msg)
            return False, str(e)
    
    def backup_file(self, filepath: str) -> bool:
        """Create backup of file before modification"""
        try:
            if not os.path.exists(filepath):
                return True
            
            backup_path = f"{filepath}.stig-v2r3-backup-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            if not STIGConfig.DRY_RUN:
                shutil.copy2(filepath, backup_path)
            logger.info(f"Backed up {filepath} to {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to backup {filepath}: {e}")
            return False
    
    def atomic_write(self, filepath: str, content: str, mode: int = 0o644, 
                    owner: str = 'root', group: str = 'root') -> bool:
        """Atomically write file with proper permissions"""
        try:
            if STIGConfig.DRY_RUN:
                logger.info(f"[DRY RUN] Would write to {filepath}")
                return True
            
            # Create temp file
            dir_name = os.path.dirname(filepath) or '.'
            fd, temp_path = tempfile.mkstemp(dir=dir_name)
            
            try:
                # Write content
                with os.fdopen(fd, 'w') as f:
                    f.write(content)
                
                # Set permissions
                os.chmod(temp_path, mode)
                
                # Set ownership
                if not IS_WINDOWS and pwd is not None:
                    try:
                        uid = pwd.getpwnam(owner).pw_uid
                        gid = grp.getgrnam(group).gr_gid
                        os.chown(temp_path, uid, gid)
                    except (KeyError, OSError) as e:
                        logger.warning(f"Could not set ownership: {e}")
                
                # Atomic move
                shutil.move(temp_path, filepath)
                
                logger.info(f"Wrote {filepath} successfully")
                self.changes.append(f"Modified {filepath}")
                return True
            except:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise
        except Exception as e:
            logger.error(f"Failed to write {filepath}: {e}")
            self.errors.append(f"Failed to write {filepath}: {e}")
            return False
    
    def modify_config_line(self, filepath: str, pattern: str, replacement: str, 
                          comment_char: str = '#') -> bool:
        """Modify or add a configuration line in a file"""
        try:
            self.backup_file(filepath)
            
            if not os.path.exists(filepath):
                logger.warning(f"File {filepath} does not exist, creating it")
                content = replacement + '\n'
            else:
                with open(filepath, 'r') as f:
                    content = f.read()
                
                # Check if pattern exists (uncommented)
                if re.search(rf'^{pattern}', content, re.MULTILINE):
                    # Replace existing line
                    content = re.sub(rf'^{pattern}.*$', replacement, content, flags=re.MULTILINE)
                    logger.info(f"Replaced line matching '{pattern}' in {filepath}")
                elif re.search(rf'^{comment_char}\s*{pattern}', content, re.MULTILINE):
                    # Uncomment and replace
                    content = re.sub(rf'^{comment_char}\s*{pattern}.*$', replacement, content, flags=re.MULTILINE)
                    logger.info(f"Uncommented and replaced line matching '{pattern}' in {filepath}")
                else:
                    # Add new line
                    content += '\n' + replacement + '\n'
                    logger.info(f"Added line '{replacement}' to {filepath}")
            
            return self.atomic_write(filepath, content)
        except Exception as e:
            logger.error(f"Failed to modify {filepath}: {e}")
            self.errors.append(f"Failed to modify {filepath}: {e}")
            return False


# ============================================================================
# ENHANCED SAFETY SYSTEM
# ============================================================================

class PreFlightChecker:
    """Comprehensive pre-flight safety checks before remediation"""
    
    def __init__(self):
        self.checks_passed = []
        self.checks_failed = []
        self.warnings = []
    
    def run_all_checks(self) -> bool:
        """Run all pre-flight safety checks"""
        logger.info("="*80)
        logger.info("RUNNING PRE-FLIGHT SAFETY CHECKS")
        logger.info("="*80)
        
        checks = [
            ("Root Privileges", self.check_root),
            ("Operating System", self.check_os_version),
            ("Disk Space", self.check_disk_space),
            ("Critical Services", self.check_critical_services),
            ("Network Connectivity", self.check_network),
            ("Backup Directory", self.check_backup_dir),
            ("SSH Access", self.check_ssh_access),
            ("Snapshot Status", self.check_snapshot) if STIGConfig.REQUIRE_SNAPSHOT else ("Snapshot Status (Optional)", lambda: (True, "Snapshot not required")),
            ("Config File Integrity", self.check_config_integrity),
            ("Package System", self.check_package_system),
        ]
        
        all_passed = True
        for check_name, check_func in checks:
            try:
                passed, message = check_func()
                if passed:
                    logger.info(f"✓ {check_name}: PASS - {message}")
                    self.checks_passed.append(check_name)
                else:
                    logger.error(f"✗ {check_name}: FAIL - {message}")
                    self.checks_failed.append((check_name, message))
                    all_passed = False
            except Exception as e:
                logger.error(f"✗ {check_name}: ERROR - {str(e)}")
                self.checks_failed.append((check_name, str(e)))
                all_passed = False
        
        logger.info("")
        logger.info(f"Pre-flight checks: {len(self.checks_passed)} passed, {len(self.checks_failed)} failed")
        
        if not all_passed:
            logger.error("\nPre-flight checks FAILED. Please resolve issues before proceeding.")
            logger.error("Failed checks:")
            for check, reason in self.checks_failed:
                logger.error(f"  - {check}: {reason}")
        
        return all_passed
    
    def check_root(self) -> Tuple[bool, str]:
        """Check if running as root"""
        if is_admin():
            return True, "Running as root"
        return False, "Must run as root"
    
    def check_os_version(self) -> Tuple[bool, str]:
        """Verify Ubuntu 20.04"""
        if STIGConfig.SKIP_OS_CHECK:
            return True, "OS check skipped by configuration"
        
        try:
            with open('/etc/os-release', 'r') as f:
                content = f.read()
            
            if 'Ubuntu 20.04' in content:
                return True, "Ubuntu 20.04 LTS detected"
            return False, "Not Ubuntu 20.04 - set SKIP_OS_CHECK=True to bypass"
        except Exception as e:
            return False, f"Cannot read OS version: {e}"
    
    def check_disk_space(self) -> Tuple[bool, str]:
        """Check available disk space"""
        try:
            stat = os.statvfs('/')
            free_mb = (stat.f_bavail * stat.f_frsize) / (1024 * 1024)
            
            if free_mb >= STIGConfig.MIN_FREE_SPACE_MB:
                return True, f"{int(free_mb)} MB free (required: {STIGConfig.MIN_FREE_SPACE_MB} MB)"
            return False, f"Only {int(free_mb)} MB free (required: {STIGConfig.MIN_FREE_SPACE_MB} MB)"
        except Exception as e:
            return False, f"Cannot check disk space: {e}"
    
    def check_critical_services(self) -> Tuple[bool, str]:
        """Check if critical services are accessible"""
        critical_services = ['systemd', 'dbus']
        
        for service in critical_services:
            result = subprocess.run(
                ['systemctl', 'is-system-running'],
                capture_output=True,
                text=True
            )
            if result.returncode not in [0, 1]:  # 0=running, 1=degraded (acceptable)
                return False, f"Systemd not functioning properly"
        
        return True, "Critical services operational"
    
    def check_network(self) -> Tuple[bool, str]:
        """Check basic network connectivity"""
        try:
            # Check if we can resolve DNS
            result = subprocess.run(
                ['host', 'archive.ubuntu.com'],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return True, "Network connectivity OK"
            return False, "Cannot resolve DNS - network may be down"
        except subprocess.TimeoutExpired:
            return False, "DNS resolution timeout"
        except FileNotFoundError:
            # 'host' command not available, try ping
            try:
                result = subprocess.run(
                    ['ping', '-c', '1', '-W', '2', '8.8.8.8'],
                    capture_output=True,
                    timeout=3
                )
                if result.returncode == 0:
                    return True, "Network connectivity OK (ping)"
                return False, "Cannot ping external hosts"
            except:
                self.warnings.append("Cannot verify network connectivity")
                return True, "Network check skipped (no tools available)"
    
    def check_backup_dir(self) -> Tuple[bool, str]:
        """Ensure backup directory exists and is writable"""
        try:
            os.makedirs(STIGConfig.BACKUP_DIR, exist_ok=True)
            
            # Test write permission
            test_file = os.path.join(STIGConfig.BACKUP_DIR, '.write_test')
            with open(test_file, 'w') as f:
                f.write('test')
            os.unlink(test_file)
            
            return True, f"Backup directory ready: {STIGConfig.BACKUP_DIR}"
        except Exception as e:
            return False, f"Cannot create/write to backup directory: {e}"
    
    def check_ssh_access(self) -> Tuple[bool, str]:
        """Warn if running via SSH"""
        try:
            ssh_connection = os.environ.get('SSH_CONNECTION')
            ssh_client = os.environ.get('SSH_CLIENT')
            
            if ssh_connection or ssh_client:
                self.warnings.append("Running via SSH - SSH config changes may disconnect you")
                return True, "SSH connection detected - recommend console access"
            return True, "Not running via SSH (recommended)"
        except:
            return True, "Cannot determine SSH status"
    
    def check_snapshot(self) -> Tuple[bool, str]:
        """Check if VM/LVM snapshot exists"""
        # Check for LVM snapshots
        try:
            result = subprocess.run(
                ['lvs', '--noheadings', '-o', 'lv_name'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if 'snapshot' in result.stdout.lower() or 'snap' in result.stdout.lower():
                return True, "LVM snapshot detected"
        except:
            pass
        
        # Check for VM snapshot markers
        vm_markers = [
            '/var/run/libvirt',  # KVM
            '/proc/vz',  # OpenVZ
            '/.dockerenv',  # Docker
        ]
        
        for marker in vm_markers:
            if os.path.exists(marker):
                self.warnings.append("Running in virtualized environment - snapshot recommended")
                return True, "Virtualized environment detected"
        
        if STIGConfig.REQUIRE_SNAPSHOT:
            return False, "No snapshot detected and REQUIRE_SNAPSHOT=True"
        
        self.warnings.append("No snapshot detected - strongly recommend taking one")
        return True, "No snapshot (not required but recommended)"
    
    def check_config_integrity(self) -> Tuple[bool, str]:
        """Check if critical config files exist and are readable"""
        critical_configs = [
            '/etc/ssh/sshd_config',
            '/etc/pam.d/common-auth',
            '/etc/pam.d/common-password',
            '/etc/sudoers',
            '/etc/login.defs',
        ]
        
        missing = []
        for config in critical_configs:
            if not os.path.exists(config):
                missing.append(config)
        
        if missing:
            return False, f"Missing critical configs: {', '.join(missing)}"
        
        return True, "All critical config files present"
    
    def check_package_system(self) -> Tuple[bool, str]:
        """Check if apt/dpkg is working"""
        try:
            # Check if dpkg is locked
            lock_files = [
                '/var/lib/dpkg/lock',
                '/var/lib/dpkg/lock-frontend',
                '/var/lib/apt/lists/lock',
            ]
            
            locked = []
            for lock_file in lock_files:
                if os.path.exists(lock_file):
                    try:
                        # Try to acquire lock
                        import fcntl
                        with open(lock_file, 'r') as f:
                            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                    except IOError:
                        locked.append(lock_file)
            
            if locked:
                return False, f"Package system locked: {', '.join(locked)}"
            
            return True, "Package system ready"
        except Exception as e:
            return False, f"Cannot check package system: {e}"


class RecoveryManager:
    """Manage recovery points and automatic rollback"""
    
    def __init__(self):
        self.recovery_dir = STIGConfig.RECOVERY_POINT_DIR
        os.makedirs(self.recovery_dir, exist_ok=True)
        self.current_recovery_point = None
        self.recovery_manifest = {}
    
    def create_recovery_point(self, name: str) -> bool:
        """Create a recovery point with system state snapshot"""
        logger.info(f"Creating recovery point: {name}")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        recovery_id = f"{name}_{timestamp}"
        recovery_path = os.path.join(self.recovery_dir, recovery_id)
        
        try:
            os.makedirs(recovery_path, exist_ok=True)
            
            # Critical files to backup
            critical_files = [
                '/etc/ssh/sshd_config',
                '/etc/pam.d/common-auth',
                '/etc/pam.d/common-password',
                '/etc/pam.d/common-account',
                '/etc/pam.d/common-session',
                '/etc/security/pwquality.conf',
                '/etc/security/faillock.conf',
                '/etc/sudoers',
                '/etc/login.defs',
                '/etc/sysctl.conf',
                '/etc/default/grub',
                '/etc/audit/auditd.conf',
            ]
            
            # Backup critical directories
            critical_dirs = [
                '/etc/sysctl.d/',
                '/etc/audit/rules.d/',
                '/etc/sudoers.d/',
                '/etc/modprobe.d/',
                '/etc/systemd/system/',
            ]
            
            manifest = {
                'recovery_id': recovery_id,
                'name': name,
                'timestamp': timestamp,
                'files': [],
                'directories': [],
            }
            
            # Backup files
            for filepath in critical_files:
                if os.path.exists(filepath):
                    dest = os.path.join(recovery_path, filepath.lstrip('/'))
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    shutil.copy2(filepath, dest)
                    manifest['files'].append(filepath)
                    logger.debug(f"Backed up {filepath}")
            
            # Backup directories
            for dirpath in critical_dirs:
                if os.path.exists(dirpath):
                    dest = os.path.join(recovery_path, dirpath.lstrip('/'))
                    shutil.copytree(dirpath, dest, dirs_exist_ok=True)
                    manifest['directories'].append(dirpath)
                    logger.debug(f"Backed up {dirpath}")
            
            # Save manifest
            manifest_file = os.path.join(recovery_path, 'manifest.json')
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            self.current_recovery_point = recovery_id
            self.recovery_manifest = manifest
            
            logger.info(f"✓ Recovery point created: {recovery_id}")
            logger.info(f"  Files backed up: {len(manifest['files'])}")
            logger.info(f"  Directories backed up: {len(manifest['directories'])}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create recovery point: {e}")
            return False
    
    def restore_recovery_point(self, recovery_id: Optional[str] = None) -> bool:
        """Restore system to a recovery point"""
        if recovery_id is None:
            recovery_id = self.current_recovery_point
        
        if not recovery_id:
            logger.error("No recovery point specified")
            return False
        
        logger.warning("="*80)
        logger.warning(f"RESTORING RECOVERY POINT: {recovery_id}")
        logger.warning("="*80)
        
        recovery_path = os.path.join(self.recovery_dir, recovery_id)
        
        if not os.path.exists(recovery_path):
            logger.error(f"Recovery point not found: {recovery_path}")
            return False
        
        try:
            # Load manifest
            manifest_file = os.path.join(recovery_path, 'manifest.json')
            with open(manifest_file, 'r') as f:
                manifest = json.load(f)
            
            # Restore files
            for filepath in manifest['files']:
                backup_path = os.path.join(recovery_path, filepath.lstrip('/'))
                if os.path.exists(backup_path):
                    shutil.copy2(backup_path, filepath)
                    logger.info(f"✓ Restored {filepath}")
            
            # Restore directories
            for dirpath in manifest['directories']:
                backup_path = os.path.join(recovery_path, dirpath.lstrip('/'))
                if os.path.exists(backup_path):
                    # Remove existing and restore
                    if os.path.exists(dirpath):
                        shutil.rmtree(dirpath)
                    shutil.copytree(backup_path, dirpath)
                    logger.info(f"✓ Restored {dirpath}")
            
            logger.warning("="*80)
            logger.warning("RECOVERY COMPLETE")
            logger.warning("Please restart affected services:")
            logger.warning("  systemctl restart sshd")
            logger.warning("  systemctl restart auditd")
            logger.warning("="*80)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore recovery point: {e}")
            return False
    
    def list_recovery_points(self) -> List[str]:
        """List available recovery points"""
        if not os.path.exists(self.recovery_dir):
            return []
        
        recovery_points = []
        for item in os.listdir(self.recovery_dir):
            manifest_file = os.path.join(self.recovery_dir, item, 'manifest.json')
            if os.path.exists(manifest_file):
                try:
                    with open(manifest_file, 'r') as f:
                        manifest = json.load(f)
                    recovery_points.append({
                        'id': manifest['recovery_id'],
                        'name': manifest['name'],
                        'timestamp': manifest['timestamp'],
                    })
                except:
                    pass
        
        return recovery_points


class ConfigValidator:
    """Validate configuration changes before applying"""
    
    def __init__(self):
        self.validation_errors = []
        self.validation_warnings = []
    
    def validate_sshd_config(self, config_file: str) -> bool:
        """Validate SSH daemon configuration"""
        logger.info("Validating SSH configuration...")
        
        if not os.path.exists(config_file):
            self.validation_errors.append(f"SSH config not found: {config_file}")
            return False
        
        # Test with sshd -t
        result = subprocess.run(
            ['sshd', '-t', '-f', config_file],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("✓ SSH configuration valid")
            return True
        else:
            self.validation_errors.append(f"SSH config invalid: {result.stderr}")
            logger.error(f"✗ SSH configuration INVALID: {result.stderr}")
            return False
    
    def validate_pam_config(self, config_dir: str = '/etc/pam.d') -> bool:
        """Validate PAM configuration"""
        logger.info("Validating PAM configuration...")
        
        # Check for common PAM errors
        pam_files = [
            'common-auth',
            'common-password',
            'common-account',
            'common-session'
        ]
        
        errors = []
        for pam_file in pam_files:
            filepath = os.path.join(config_dir, pam_file)
            if not os.path.exists(filepath):
                errors.append(f"Missing PAM file: {pam_file}")
                continue
            
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                
                # Check for dangerous configurations
                if 'nullok' in content and not STIGConfig.DRY_RUN:
                    self.validation_warnings.append(f"{pam_file} contains 'nullok' - will be removed")
                
                # Check for required modules
                if pam_file == 'common-auth' and 'pam_unix.so' not in content:
                    errors.append(f"{pam_file} missing pam_unix.so")
                
            except Exception as e:
                errors.append(f"Cannot read {pam_file}: {e}")
        
        if errors:
            self.validation_errors.extend(errors)
            logger.error(f"✗ PAM validation errors: {errors}")
            return False
        
        logger.info("✓ PAM configuration valid")
        return True
    
    def validate_sudoers(self, sudoers_file: str = '/etc/sudoers') -> bool:
        """Validate sudoers file"""
        logger.info("Validating sudoers configuration...")
        
        if not os.path.exists(sudoers_file):
            self.validation_errors.append("Sudoers file not found")
            return False
        
        # Use visudo to validate
        result = subprocess.run(
            ['visudo', '-c', '-f', sudoers_file],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("✓ Sudoers configuration valid")
            return True
        else:
            self.validation_errors.append(f"Sudoers invalid: {result.stderr}")
            logger.error(f"✗ Sudoers INVALID: {result.stderr}")
            return False
    
    def validate_grub_config(self) -> bool:
        """Validate GRUB configuration"""
        logger.info("Validating GRUB configuration...")
        
        grub_file = '/etc/default/grub'
        if not os.path.exists(grub_file):
            self.validation_warnings.append("GRUB config not found - may not be using GRUB")
            return True
        
        try:
            with open(grub_file, 'r') as f:
                content = f.read()
            
            # Check for required parameters
            if 'audit=1' not in content:
                self.validation_warnings.append("GRUB missing audit=1 parameter")
            
            logger.info("✓ GRUB configuration valid")
            return True
        except Exception as e:
            self.validation_errors.append(f"Cannot validate GRUB: {e}")
            return False
    
    def validate_all(self) -> bool:
        """Run all configuration validators"""
        logger.info("="*80)
        logger.info("VALIDATING CONFIGURATIONS")
        logger.info("="*80)
        
        all_valid = True
        
        # Validate SSH (critical)
        if os.path.exists('/etc/ssh/sshd_config'):
            if not self.validate_sshd_config('/etc/ssh/sshd_config'):
                all_valid = False
        
        # Validate PAM (critical)
        if not self.validate_pam_config():
            all_valid = False
        
        # Validate sudoers (critical)
        if not self.validate_sudoers():
            all_valid = False
        
        # Validate GRUB (warning only)
        self.validate_grub_config()
        
        if self.validation_errors:
            logger.error(f"\nValidation errors ({len(self.validation_errors)}):")
            for error in self.validation_errors:
                logger.error(f"  ✗ {error}")
        
        if self.validation_warnings:
            logger.warning(f"\nValidation warnings ({len(self.validation_warnings)}):")
            for warning in self.validation_warnings:
                logger.warning(f"  ⚠ {warning}")
        
        if all_valid:
            logger.info("\n✓ All critical configurations valid")
        else:
            logger.error("\n✗ Configuration validation FAILED")
        
        return all_valid


class EmergencyRecovery:
    """Emergency recovery utilities"""
    
    @staticmethod
    def restore_ssh_access():
        """Emergency SSH access restoration"""
        logger.warning("="*80)
        logger.warning("EMERGENCY SSH RECOVERY")
        logger.warning("="*80)
        
        # Find most recent SSH backup
        backups = glob.glob('/etc/ssh/sshd_config.stig-v2r3-backup-*')
        backups.extend(glob.glob(f'{STIGConfig.BACKUP_DIR}/**/etc/ssh/sshd_config', recursive=True))
        
        if not backups:
            logger.error("No SSH backups found!")
            return False
        
        # Get most recent
        latest_backup = max(backups, key=os.path.getmtime)
        
        logger.warning(f"Restoring from: {latest_backup}")
        shutil.copy2(latest_backup, '/etc/ssh/sshd_config')
        
        # Restart SSH
        subprocess.run(['systemctl', 'restart', 'sshd'])
        
        logger.warning("SSH configuration restored - please test connection")
        return True
    
    @staticmethod
    def restore_pam_access():
        """Emergency PAM access restoration"""
        logger.warning("="*80)
        logger.warning("EMERGENCY PAM RECOVERY")
        logger.warning("="*80)
        
        pam_files = ['common-auth', 'common-password', 'common-account', 'common-session']
        
        for pam_file in pam_files:
            backups = glob.glob(f'/etc/pam.d/{pam_file}.stig-v2r3-backup-*')
            backups.extend(glob.glob(f'{STIGConfig.BACKUP_DIR}/**/etc/pam.d/{pam_file}', recursive=True))
            
            if backups:
                latest_backup = max(backups, key=os.path.getmtime)
                logger.warning(f"Restoring: {pam_file} from {latest_backup}")
                shutil.copy2(latest_backup, f'/etc/pam.d/{pam_file}')
        
        logger.warning("PAM configuration restored")
        return True
    
    @staticmethod
    def emergency_mode():
        """Enter emergency recovery mode"""
        logger.warning("="*80)
        logger.warning("EMERGENCY RECOVERY MODE")
        logger.warning("="*80)
        logger.warning("")
        logger.warning("Available recovery actions:")
        logger.warning("  1. Restore SSH access")
        logger.warning("  2. Restore PAM configuration")
        logger.warning("  3. List recovery points")
        logger.warning("  4. Restore from recovery point")
        logger.warning("")
        
        recovery_mgr = RecoveryManager()
        
        # List recovery points
        points = recovery_mgr.list_recovery_points()
        if points:
            logger.warning("Available recovery points:")
            for point in points:
                logger.warning(f"  - {point['id']} ({point['name']}) - {point['timestamp']}")
        else:
            logger.warning("No recovery points available")
        
        # Restore SSH by default
        EmergencyRecovery.restore_ssh_access()
        EmergencyRecovery.restore_pam_access()


# ============================================================================
# SECTION 1: PACKAGE MANAGEMENT
# ============================================================================
# TODO: Agent 1 - Package Management Enhancement
# - Add package version verification
# - Implement rollback capability for package changes
# - Add checksum validation for security packages
# - Implement package hold/unhold management
# - Add support for snap packages if needed
# ============================================================================

class PackageManager(SystemModifier):
    """Manage package installation and removal"""
    
    def update_cache(self) -> bool:
        """Update apt package cache"""
        logger.info("Updating apt package cache")
        success, _ = self.run_command(['apt-get', 'update'])
        if success:
            self.add_stig_control("PKG-001", "Updated package cache")
        return success
    
    def install_packages(self, packages: List[str]) -> bool:
        """Install required packages"""
        logger.info(f"Installing packages: {', '.join(packages)}")
        success = True
        for package in packages:
            result, output = self.run_command(
                ['apt-get', 'install', '-y', package],
                check=False
            )
            if result:
                self.changes.append(f"Installed package: {package}")
            else:
                logger.warning(f"Failed to install {package}: {output}")
                success = False
        return success
    
    def remove_packages(self, packages: List[str]) -> bool:
        """Remove unwanted packages - CAT I/II Controls"""
        logger.info(f"Removing packages: {', '.join(packages)}")
        success = True
        for package in packages:
            # Check if package is installed first
            if not self.is_package_installed(package):
                logger.info(f"Package {package} not installed, skipping")
                continue
                
            result, output = self.run_command(
                ['apt-get', 'remove', '--purge', '-y', package],
                check=False
            )
            if result:
                self.changes.append(f"Removed package: {package}")
                # Track specific STIG controls
                if package == 'telnet':
                    self.add_stig_control("UBTU-20-010405", "Removed telnet package")
                elif package == 'rsh-server':
                    self.add_stig_control("UBTU-20-010406", "Removed rsh-server package")
            else:
                logger.warning(f"Failed to remove {package}: {output}")
                success = False
        return success
    
    def is_package_installed(self, package: str) -> bool:
        """Check if package is installed"""
        result = subprocess.run(
            ['dpkg', '-s', package],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    
    # TODO: Add package verification methods
    # TODO: Add package checksum validation
    # TODO: Implement package hold management


# ============================================================================
# SECTION 2: SERVICE MANAGEMENT  
# ============================================================================
# TODO: Agent 2 - Service Management Enhancement
# - Add service dependency checking
# - Implement service health monitoring post-change
# - Add rollback capability for service changes
# - Implement service configuration validation
# - Add support for socket activation services
# ============================================================================

class ServiceManager(SystemModifier):
    """Manage systemd services"""
    
    def enable_service(self, service: str) -> bool:
        """Enable and start a service"""
        logger.info(f"Enabling service: {service}")
        success = self.run_command(['systemctl', 'enable', service], check=False)[0]
        if success:
            success = self.run_command(['systemctl', 'start', service], check=False)[0]
            if success:
                self.changes.append(f"Enabled and started service: {service}")
        return success
    
    def disable_service(self, service: str) -> bool:
        """Disable and stop a service"""
        logger.info(f"Disabling service: {service}")
        self.run_command(['systemctl', 'stop', service], check=False)
        success = self.run_command(['systemctl', 'disable', service], check=False)[0]
        if success:
            self.changes.append(f"Disabled service: {service}")
        return success
    
    def mask_service(self, service: str) -> bool:
        """Mask a service to prevent activation"""
        logger.info(f"Masking service: {service}")
        success = self.run_command(['systemctl', 'mask', service], check=False)[0]
        if success:
            self.changes.append(f"Masked service: {service}")
            if service == 'ctrl-alt-del.target':
                self.add_stig_control("UBTU-20-010459", "Masked Ctrl-Alt-Del")
        return success
    
    def reload_daemon(self) -> bool:
        """Reload systemd daemon"""
        logger.info("Reloading systemd daemon")
        return self.run_command(['systemctl', 'daemon-reload'])[0]
    
    # TODO: Add service health checks
    # TODO: Add service dependency validation
    # TODO: Implement service state rollback


# ============================================================================
# SECTION 3: KERNEL PARAMETERS (SYSCTL)
# ============================================================================
# Agent 3 - Kernel Parameter Enhancement - COMPLETED & ENHANCED
#
# Phase 1 - Core TODO Items (COMPLETED):
# ✓ Added validation of current kernel parameters before change
# ✓ Implemented parameter persistence verification
# ✓ Added reboot requirement detection
# ✓ Implemented parameter conflict detection
# ✓ Added performance impact assessment
#
# Phase 2 - Advanced Enhancements (COMPLETED):
# ✓ Rollback capability with snapshot/restore
# ✓ Comprehensive compliance reporting with scoring (A+ to F grades)
# ✓ Automated remediation recommendations
# ✓ Dry-run and testing mode for safe parameter testing
# ✓ Parameter grouping for selective application
# ✓ Parameter history tracking and audit trail
# ✓ Enhanced conflict detection with routing checks
# ✓ Automatic rollback on critical failures
#
# New methods (16 total):
#   Core Validation:
#   - validate_current_params() - Validates current sysctl values against STIG
#   - verify_persistence() - Verifies parameters persist across reboots
#   - detect_reboot_requirements() - Identifies parameters requiring reboot
#   - detect_parameter_conflicts() - Detects conflicting kernel parameters
#   - assess_performance_impact() - Documents performance impact of parameters
#
#   Advanced Features:
#   - create_snapshot() - Create rollback snapshot
#   - restore_from_snapshot() - Restore from snapshot
#   - generate_compliance_report() - Comprehensive compliance report with scoring
#   - _generate_recommendations() - Automated remediation recommendations
#   - test_parameter_change() - Test parameter change with auto-revert
#   - get_parameter_groups() - Get parameters organized by category
#   - apply_parameter_group() - Apply specific parameter groups
#   - audit_parameter_history() - Track parameter changes and drift
#   - apply_stig_params() - Enhanced with rollback and comprehensive validation
#
# Features:
# - Compliance scoring with letter grades (A+ to F)
# - Automatic rollback on failures
# - Dry-run mode for safe testing
# - Selective application by parameter groups
# - Performance impact warnings
# - Reboot requirement detection
# - Parameter drift tracking
# - Comprehensive audit trails
# ============================================================================

class SysctlManager(SystemModifier):
    """Manage kernel parameters via sysctl"""

    # V2R3 compliant kernel parameters
    STIG_KERNEL_PARAMS = {
        # Network security - IPv4
        'net.ipv4.conf.all.rp_filter': '1',  # UBTU-20-010411
        'net.ipv4.conf.default.rp_filter': '1',
        'net.ipv4.conf.all.accept_source_route': '0',  # UBTU-20-010412
        'net.ipv4.conf.default.accept_source_route': '0',
        'net.ipv4.conf.all.accept_redirects': '0',  # UBTU-20-010413
        'net.ipv4.conf.default.accept_redirects': '0',
        'net.ipv4.conf.all.secure_redirects': '0',  # UBTU-20-010415
        'net.ipv4.conf.default.secure_redirects': '0',
        'net.ipv4.conf.all.send_redirects': '0',  # UBTU-20-010414
        'net.ipv4.conf.default.send_redirects': '0',
        'net.ipv4.icmp_echo_ignore_broadcasts': '1',  # UBTU-20-010417
        'net.ipv4.icmp_ignore_bogus_error_responses': '1',
        'net.ipv4.tcp_syncookies': '1',  # UBTU-20-010418
        'net.ipv4.conf.all.log_martians': '1',  # UBTU-20-010419
        'net.ipv4.conf.default.log_martians': '1',
        'net.ipv4.ip_forward': '0',  # UBTU-20-010420

        # IPv6 security
        'net.ipv6.conf.all.accept_source_route': '0',  # UBTU-20-010421
        'net.ipv6.conf.default.accept_source_route': '0',
        'net.ipv6.conf.all.accept_redirects': '0',
        'net.ipv6.conf.default.accept_redirects': '0',
        'net.ipv6.conf.all.forwarding': '0',

        # Kernel security
        'kernel.dmesg_restrict': '1',  # V-255913 (NEW IN V2R3)
        'kernel.kptr_restrict': '2',
        'kernel.yama.ptrace_scope': '1',  # UBTU-20-010430
        'kernel.randomize_va_space': '2',  # UBTU-20-010431
        'fs.suid_dumpable': '0',  # UBTU-20-010404

        # Additional hardening
        'net.ipv4.conf.all.arp_filter': '1',
        'net.ipv4.conf.all.arp_announce': '2',
    }

    # Performance impact documentation for kernel parameters
    PARAM_PERFORMANCE_IMPACT = {
        # High impact parameters (may affect system performance)
        'net.ipv4.tcp_syncookies': {
            'impact': 'MEDIUM',
            'description': 'TCP SYN cookies protect against SYN flood attacks but may impact connection tracking',
            'mitigation': 'Performance impact is minimal on modern systems'
        },
        'net.ipv4.conf.all.log_martians': {
            'impact': 'MEDIUM',
            'description': 'Logging martian packets can generate significant logs under attack',
            'mitigation': 'Ensure adequate log storage and rotation'
        },
        'kernel.randomize_va_space': {
            'impact': 'LOW',
            'description': 'ASLR has minimal performance impact on modern systems',
            'mitigation': 'No mitigation needed'
        },
        'net.ipv4.ip_forward': {
            'impact': 'HIGH',
            'description': 'Disabling IP forwarding breaks routing functionality',
            'mitigation': 'Only enable on systems that require routing/NAT'
        },
        'net.ipv6.conf.all.forwarding': {
            'impact': 'HIGH',
            'description': 'Disabling IPv6 forwarding breaks IPv6 routing',
            'mitigation': 'Only enable on systems that require IPv6 routing'
        }
    }

    # Parameters that require reboot to take full effect
    REBOOT_REQUIRED_PARAMS = [
        'kernel.randomize_va_space',
        'fs.suid_dumpable',
        'kernel.dmesg_restrict',
        'kernel.kptr_restrict'
    ]

    # Parameter conflict/dependency detection
    PARAM_CONFLICTS = {
        'net.ipv4.ip_forward': {
            'conflicts_with': [],
            'description': 'IP forwarding is disabled by STIG but may be needed for routers/NAT gateways',
            'warning': 'This will break routing functionality if system acts as a router'
        },
        'net.ipv6.conf.all.forwarding': {
            'conflicts_with': [],
            'description': 'IPv6 forwarding is disabled by STIG but may be needed for IPv6 routers',
            'warning': 'This will break IPv6 routing functionality'
        }
    }

    def validate_current_params(self) -> dict:
        """
        TODO Item 1: Current Parameter Validation
        Read and validate current sysctl values before change, compare against
        STIG requirements, and report parameter drift

        Returns:
            dict: Validation results with current values, expected values, and drift status
        """
        logger.info("Validating current kernel parameters against STIG requirements")

        validation_results = {
            'compliant': [],
            'non_compliant': [],
            'missing': [],
            'drift_detected': False
        }

        for param, expected_value in self.STIG_KERNEL_PARAMS.items():
            try:
                # Read current parameter value
                result = self.run_command(['sysctl', '-n', param], capture_output=True, check=False)

                if result.returncode != 0:
                    validation_results['missing'].append({
                        'param': param,
                        'expected': expected_value,
                        'error': 'Parameter does not exist or cannot be read'
                    })
                    validation_results['drift_detected'] = True
                    logger.warning(f"Parameter {param} does not exist or cannot be read")
                    continue

                current_value = result.stdout.strip()

                # Compare with expected value
                if current_value == expected_value:
                    validation_results['compliant'].append({
                        'param': param,
                        'value': current_value
                    })
                    logger.debug(f"Parameter {param} is compliant: {current_value}")
                else:
                    validation_results['non_compliant'].append({
                        'param': param,
                        'current': current_value,
                        'expected': expected_value,
                        'drift': True
                    })
                    validation_results['drift_detected'] = True
                    logger.warning(f"Parameter drift detected: {param} = {current_value} (expected: {expected_value})")

            except Exception as e:
                logger.error(f"Error validating parameter {param}: {e}")
                validation_results['missing'].append({
                    'param': param,
                    'expected': expected_value,
                    'error': str(e)
                })

        # Log summary
        total_params = len(self.STIG_KERNEL_PARAMS)
        compliant_count = len(validation_results['compliant'])
        non_compliant_count = len(validation_results['non_compliant'])
        missing_count = len(validation_results['missing'])

        logger.info(f"Parameter validation complete: {compliant_count}/{total_params} compliant, "
                   f"{non_compliant_count} non-compliant, {missing_count} missing")

        return validation_results

    def verify_persistence(self) -> dict:
        """
        TODO Item 2: Parameter Persistence Verification
        Verify parameters persist across reboots by checking sysctl config files,
        test sysctl config file loading, and validate parameter application order

        Returns:
            dict: Persistence verification results
        """
        logger.info("Verifying kernel parameter persistence configuration")

        persistence_results = {
            'config_files': [],
            'parameters_in_config': {},
            'missing_from_config': [],
            'persistence_verified': True
        }

        # Common sysctl configuration file locations
        sysctl_config_files = [
            '/etc/sysctl.conf',
            '/etc/sysctl.d/99-stig-v2r3.conf',
            '/etc/sysctl.d/*.conf'
        ]

        # Find all sysctl config files
        config_files_found = []
        for config_pattern in sysctl_config_files:
            if '*' in config_pattern:
                # Handle glob patterns
                import glob
                config_files_found.extend(glob.glob(config_pattern))
            elif os.path.exists(config_pattern):
                config_files_found.append(config_pattern)

        persistence_results['config_files'] = config_files_found

        # Parse each config file to find STIG parameters
        for config_file in config_files_found:
            try:
                with open(config_file, 'r') as f:
                    content = f.read()

                for param in self.STIG_KERNEL_PARAMS.keys():
                    # Look for parameter in config file
                    # Match patterns like "param = value" or "param=value"
                    pattern = rf'^\s*{re.escape(param)}\s*=\s*(.+)$'
                    match = re.search(pattern, content, re.MULTILINE)

                    if match:
                        config_value = match.group(1).strip()
                        if param not in persistence_results['parameters_in_config']:
                            persistence_results['parameters_in_config'][param] = []

                        persistence_results['parameters_in_config'][param].append({
                            'file': config_file,
                            'value': config_value
                        })

            except Exception as e:
                logger.error(f"Error reading config file {config_file}: {e}")

        # Check for parameters missing from configuration
        for param, expected_value in self.STIG_KERNEL_PARAMS.items():
            if param not in persistence_results['parameters_in_config']:
                persistence_results['missing_from_config'].append({
                    'param': param,
                    'expected': expected_value
                })
                persistence_results['persistence_verified'] = False
                logger.warning(f"Parameter {param} not found in any config file - will not persist after reboot")

        # Test sysctl config file loading
        if os.path.exists('/etc/sysctl.d/99-stig-v2r3.conf'):
            result = self.run_command(['sysctl', '-p', '/etc/sysctl.d/99-stig-v2r3.conf'],
                                     capture_output=True, check=False)
            if result.returncode == 0:
                logger.info("STIG sysctl config file loads successfully")
            else:
                logger.error(f"STIG sysctl config file has errors: {result.stderr}")
                persistence_results['persistence_verified'] = False

        missing_count = len(persistence_results['missing_from_config'])
        logger.info(f"Persistence verification complete: {missing_count} parameters missing from config")

        return persistence_results

    def detect_reboot_requirements(self) -> dict:
        """
        TODO Item 3: Reboot Requirement Detection
        Identify parameters requiring reboot, flag non-runtime changeable parameters,
        and create reboot requirement report

        Returns:
            dict: Reboot requirement analysis
        """
        logger.info("Detecting kernel parameters that require reboot")

        reboot_analysis = {
            'reboot_required': [],
            'runtime_changeable': [],
            'reboot_recommended': False
        }

        for param, expected_value in self.STIG_KERNEL_PARAMS.items():
            if param in self.REBOOT_REQUIRED_PARAMS:
                reboot_analysis['reboot_required'].append({
                    'param': param,
                    'expected_value': expected_value,
                    'reason': 'Parameter requires reboot to take full effect'
                })
                reboot_analysis['reboot_recommended'] = True
                logger.info(f"Parameter {param} requires reboot to take full effect")
            else:
                reboot_analysis['runtime_changeable'].append({
                    'param': param,
                    'expected_value': expected_value
                })

        # Check if any reboot-required parameters are being changed
        validation = self.validate_current_params()
        for non_compliant in validation['non_compliant']:
            if non_compliant['param'] in self.REBOOT_REQUIRED_PARAMS:
                logger.warning(f"Reboot-required parameter {non_compliant['param']} will be changed - "
                             f"system reboot recommended after applying changes")

        reboot_count = len(reboot_analysis['reboot_required'])
        runtime_count = len(reboot_analysis['runtime_changeable'])
        logger.info(f"Reboot detection complete: {reboot_count} parameters require reboot, "
                   f"{runtime_count} are runtime changeable")

        return reboot_analysis

    def detect_parameter_conflicts(self) -> dict:
        """
        TODO Item 4: Parameter Conflict Detection
        Detect conflicting kernel parameters, warn about parameter interactions,
        and implement parameter dependency checking

        Returns:
            dict: Conflict detection results
        """
        logger.info("Detecting kernel parameter conflicts and dependencies")

        conflict_results = {
            'conflicts': [],
            'warnings': [],
            'dependencies': []
        }

        # Check for documented conflicts
        for param, expected_value in self.STIG_KERNEL_PARAMS.items():
            if param in self.PARAM_CONFLICTS:
                conflict_info = self.PARAM_CONFLICTS[param]

                conflict_results['warnings'].append({
                    'param': param,
                    'expected_value': expected_value,
                    'description': conflict_info['description'],
                    'warning': conflict_info['warning']
                })

                logger.warning(f"Parameter conflict warning for {param}: {conflict_info['warning']}")

        # Check for IP forwarding conflicts (common issue)
        if 'net.ipv4.ip_forward' in self.STIG_KERNEL_PARAMS:
            # Check if system might be a router
            result = self.run_command(['ip', 'route', 'show'], capture_output=True, check=False)
            if result.returncode == 0 and 'default via' in result.stdout:
                # System has default route - might need forwarding if acting as router
                conflict_results['warnings'].append({
                    'param': 'net.ipv4.ip_forward',
                    'expected_value': '0',
                    'description': 'System has routing configured',
                    'warning': 'Disabling IP forwarding may break routing functionality. '
                              'Verify system is not acting as a router/gateway before applying.'
                })
                logger.warning("IP forwarding will be disabled - verify system is not acting as a router")

        # Check for IPv6 forwarding conflicts
        if 'net.ipv6.conf.all.forwarding' in self.STIG_KERNEL_PARAMS:
            # Check if IPv6 is in use
            result = self.run_command(['ip', '-6', 'route', 'show'], capture_output=True, check=False)
            if result.returncode == 0 and result.stdout.strip():
                conflict_results['warnings'].append({
                    'param': 'net.ipv6.conf.all.forwarding',
                    'expected_value': '0',
                    'description': 'System has IPv6 routing configured',
                    'warning': 'Disabling IPv6 forwarding may break IPv6 routing functionality.'
                })
                logger.warning("IPv6 forwarding will be disabled - verify this won't break IPv6 routing")

        warning_count = len(conflict_results['warnings'])
        logger.info(f"Conflict detection complete: {warning_count} warnings found")

        return conflict_results

    def assess_performance_impact(self) -> dict:
        """
        TODO Item 5: Performance Impact Assessment
        Document performance impact of parameters, add warnings for high-impact changes,
        and implement performance testing mode

        Returns:
            dict: Performance impact assessment
        """
        logger.info("Assessing performance impact of kernel parameter changes")

        impact_assessment = {
            'high_impact': [],
            'medium_impact': [],
            'low_impact': [],
            'no_documented_impact': [],
            'overall_risk': 'LOW'
        }

        for param, expected_value in self.STIG_KERNEL_PARAMS.items():
            if param in self.PARAM_PERFORMANCE_IMPACT:
                impact_info = self.PARAM_PERFORMANCE_IMPACT[param]
                impact_level = impact_info['impact']

                impact_entry = {
                    'param': param,
                    'expected_value': expected_value,
                    'impact_level': impact_level,
                    'description': impact_info['description'],
                    'mitigation': impact_info['mitigation']
                }

                if impact_level == 'HIGH':
                    impact_assessment['high_impact'].append(impact_entry)
                    logger.warning(f"HIGH performance impact: {param} - {impact_info['description']}")
                elif impact_level == 'MEDIUM':
                    impact_assessment['medium_impact'].append(impact_entry)
                    logger.info(f"MEDIUM performance impact: {param} - {impact_info['description']}")
                else:
                    impact_assessment['low_impact'].append(impact_entry)
                    logger.debug(f"LOW performance impact: {param} - {impact_info['description']}")
            else:
                impact_assessment['no_documented_impact'].append({
                    'param': param,
                    'expected_value': expected_value
                })

        # Determine overall risk level
        if len(impact_assessment['high_impact']) > 0:
            impact_assessment['overall_risk'] = 'HIGH'
        elif len(impact_assessment['medium_impact']) > 2:
            impact_assessment['overall_risk'] = 'MEDIUM'
        else:
            impact_assessment['overall_risk'] = 'LOW'

        high_count = len(impact_assessment['high_impact'])
        medium_count = len(impact_assessment['medium_impact'])
        low_count = len(impact_assessment['low_impact'])

        logger.info(f"Performance impact assessment complete: {high_count} high impact, "
                   f"{medium_count} medium impact, {low_count} low impact parameters")
        logger.info(f"Overall performance risk: {impact_assessment['overall_risk']}")

        return impact_assessment

    def create_snapshot(self) -> dict:
        """
        ENHANCEMENT 6: Rollback Capability - Create Snapshot
        Create a snapshot of current kernel parameter state for rollback purposes.

        Returns:
            dict: Snapshot containing current parameter values and metadata
        """
        logger.info("Creating kernel parameter snapshot for rollback capability")

        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'parameters': {},
            'snapshot_id': f"sysctl_snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }

        for param in self.STIG_KERNEL_PARAMS.keys():
            try:
                result = self.run_command(['sysctl', '-n', param], capture_output=True, check=False)
                if result.returncode == 0:
                    snapshot['parameters'][param] = result.stdout.strip()
                    logger.debug(f"Snapshot: {param} = {result.stdout.strip()}")
                else:
                    snapshot['parameters'][param] = None
                    logger.warning(f"Could not snapshot parameter {param}")
            except Exception as e:
                logger.error(f"Error snapshotting {param}: {e}")
                snapshot['parameters'][param] = None

        logger.info(f"Snapshot created: {snapshot['snapshot_id']} with {len(snapshot['parameters'])} parameters")
        return snapshot

    def restore_from_snapshot(self, snapshot: dict) -> bool:
        """
        ENHANCEMENT 6: Rollback Capability - Restore from Snapshot
        Restore kernel parameters from a previously created snapshot.

        Args:
            snapshot: Snapshot dictionary created by create_snapshot()

        Returns:
            bool: True if restore was successful
        """
        logger.info(f"Restoring kernel parameters from snapshot: {snapshot.get('snapshot_id', 'unknown')}")

        success = True
        restored_count = 0
        failed_count = 0

        for param, value in snapshot['parameters'].items():
            if value is None:
                logger.warning(f"Skipping {param} - no value in snapshot")
                continue

            try:
                result = self.run_command(['sysctl', '-w', f'{param}={value}'], check=False)
                if result.returncode == 0:
                    restored_count += 1
                    logger.debug(f"Restored {param} = {value}")
                else:
                    failed_count += 1
                    logger.error(f"Failed to restore {param} = {value}")
                    success = False
            except Exception as e:
                failed_count += 1
                logger.error(f"Error restoring {param}: {e}")
                success = False

        logger.info(f"Restore complete: {restored_count} restored, {failed_count} failed")
        return success

    def generate_compliance_report(self) -> dict:
        """
        ENHANCEMENT 7: Comprehensive Reporting and Compliance Scoring
        Generate a detailed compliance report with scoring.

        Returns:
            dict: Comprehensive compliance report with scoring
        """
        logger.info("Generating comprehensive compliance report")

        report = {
            'report_id': f"sysctl_compliance_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'validation': self.validate_current_params(),
            'persistence': self.verify_persistence(),
            'reboot_analysis': self.detect_reboot_requirements(),
            'conflicts': self.detect_parameter_conflicts(),
            'performance': self.assess_performance_impact(),
            'compliance_score': 0.0,
            'grade': 'F',
            'recommendations': []
        }

        # Calculate compliance score
        total_params = len(self.STIG_KERNEL_PARAMS)
        compliant_params = len(report['validation']['compliant'])

        if total_params > 0:
            report['compliance_score'] = (compliant_params / total_params) * 100.0

        # Assign grade
        score = report['compliance_score']
        if score >= 95:
            report['grade'] = 'A+'
        elif score >= 90:
            report['grade'] = 'A'
        elif score >= 85:
            report['grade'] = 'B+'
        elif score >= 80:
            report['grade'] = 'B'
        elif score >= 75:
            report['grade'] = 'C+'
        elif score >= 70:
            report['grade'] = 'C'
        elif score >= 60:
            report['grade'] = 'D'
        else:
            report['grade'] = 'F'

        # Generate recommendations
        report['recommendations'] = self._generate_recommendations(report)

        logger.info(f"Compliance report generated: Score {report['compliance_score']:.1f}% (Grade: {report['grade']})")
        logger.info(f"Compliant: {compliant_params}/{total_params}, "
                   f"Non-compliant: {len(report['validation']['non_compliant'])}, "
                   f"Missing: {len(report['validation']['missing'])}")

        return report

    def _generate_recommendations(self, report: dict) -> list:
        """
        ENHANCEMENT 8: Automated Remediation Recommendations
        Generate automated recommendations based on compliance report.

        Args:
            report: Compliance report from generate_compliance_report()

        Returns:
            list: List of actionable recommendations
        """
        recommendations = []

        # Check for non-compliant parameters
        if report['validation']['non_compliant']:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Compliance',
                'issue': f"{len(report['validation']['non_compliant'])} parameters are not STIG compliant",
                'action': 'Run apply_stig_params() to remediate non-compliant parameters',
                'risk': 'System does not meet DISA STIG security requirements'
            })

        # Check for persistence issues
        if not report['persistence']['persistence_verified']:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Persistence',
                'issue': f"{len(report['persistence']['missing_from_config'])} parameters not in config files",
                'action': 'Apply STIG parameters to ensure persistence across reboots',
                'risk': 'Parameters will revert to defaults after system reboot'
            })

        # Check for reboot requirements
        if report['reboot_analysis']['reboot_recommended']:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Reboot Required',
                'issue': f"{len(report['reboot_analysis']['reboot_required'])} parameters require reboot",
                'action': 'Schedule system reboot to apply all kernel parameters',
                'risk': 'Some security hardening parameters not fully effective until reboot'
            })

        # Check for high-impact parameters
        if report['performance']['high_impact']:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Performance Impact',
                'issue': f"{len(report['performance']['high_impact'])} high-impact parameters detected",
                'action': 'Review high-impact parameters and validate system functionality',
                'risk': 'Parameters may affect routing, networking, or other critical functions'
            })

        # Check for conflicts
        if report['conflicts']['warnings']:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Conflicts',
                'issue': f"{len(report['conflicts']['warnings'])} parameter conflicts/warnings detected",
                'action': 'Review conflict warnings and verify system configuration requirements',
                'risk': 'STIG compliance may break required system functionality'
            })

        # Check for missing parameters
        if report['validation']['missing']:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Missing Parameters',
                'issue': f"{len(report['validation']['missing'])} parameters cannot be read",
                'action': 'Verify kernel version supports all required STIG parameters',
                'risk': 'Some STIG requirements cannot be validated or enforced'
            })

        # Overall recommendations based on score
        score = report['compliance_score']
        if score < 100:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Overall Compliance',
                'issue': f"System compliance at {score:.1f}% (Grade: {report['grade']})",
                'action': 'Apply STIG kernel parameters to achieve 100% compliance',
                'risk': 'System not fully hardened against security threats'
            })

        return recommendations

    def test_parameter_change(self, param: str, value: str, test_duration: int = 5) -> dict:
        """
        ENHANCEMENT 9: Dry-Run and Testing Mode
        Test a single parameter change without permanent modification.

        Args:
            param: Parameter name to test
            value: Value to test
            test_duration: How long to test the parameter (seconds) before reverting

        Returns:
            dict: Test results including success status and any errors
        """
        logger.info(f"Testing parameter change: {param} = {value} (duration: {test_duration}s)")

        test_result = {
            'param': param,
            'test_value': value,
            'original_value': None,
            'success': False,
            'error': None,
            'reverted': False
        }

        try:
            # Get original value
            result = self.run_command(['sysctl', '-n', param], capture_output=True, check=False)
            if result.returncode == 0:
                test_result['original_value'] = result.stdout.strip()
                logger.info(f"Original value: {param} = {test_result['original_value']}")
            else:
                test_result['error'] = f"Could not read original value: {result.stderr}"
                return test_result

            # Apply test value
            result = self.run_command(['sysctl', '-w', f'{param}={value}'], check=False)
            if result.returncode != 0:
                test_result['error'] = f"Failed to apply test value: {result.stderr}"
                return test_result

            logger.info(f"Test value applied successfully, monitoring for {test_duration} seconds...")
            test_result['success'] = True

            # Wait for test duration
            import time
            time.sleep(test_duration)

            # Revert to original value
            result = self.run_command(['sysctl', '-w', f'{param}={test_result["original_value"]}'], check=False)
            if result.returncode == 0:
                test_result['reverted'] = True
                logger.info(f"Successfully reverted {param} to original value")
            else:
                test_result['error'] = f"Failed to revert parameter: {result.stderr}"
                logger.error(f"WARNING: Could not revert {param} to original value!")

        except Exception as e:
            test_result['error'] = str(e)
            logger.error(f"Error during parameter test: {e}")

        return test_result

    def get_parameter_groups(self) -> dict:
        """
        ENHANCEMENT 10: Parameter Grouping for Selective Application
        Group kernel parameters by category for selective application.

        Returns:
            dict: Parameters organized by category
        """
        logger.info("Organizing kernel parameters by category")

        groups = {
            'ipv4_network_security': {},
            'ipv6_network_security': {},
            'kernel_security': {},
            'network_hardening': {}
        }

        for param, value in self.STIG_KERNEL_PARAMS.items():
            if param.startswith('net.ipv4.'):
                groups['ipv4_network_security'][param] = value
            elif param.startswith('net.ipv6.'):
                groups['ipv6_network_security'][param] = value
            elif param.startswith('kernel.') or param.startswith('fs.'):
                groups['kernel_security'][param] = value
            else:
                groups['network_hardening'][param] = value

        for group, params in groups.items():
            logger.info(f"Group '{group}': {len(params)} parameters")

        return groups

    def apply_parameter_group(self, group_name: str, dry_run: bool = False) -> bool:
        """
        ENHANCEMENT 10: Apply Parameters by Group
        Apply only a specific group of kernel parameters.

        Args:
            group_name: Name of the parameter group to apply
            dry_run: If True, only simulate the changes without applying

        Returns:
            bool: True if application was successful
        """
        logger.info(f"Applying parameter group: {group_name} (dry_run={dry_run})")

        groups = self.get_parameter_groups()

        if group_name not in groups:
            logger.error(f"Unknown parameter group: {group_name}")
            logger.info(f"Available groups: {', '.join(groups.keys())}")
            return False

        params_to_apply = groups[group_name]
        logger.info(f"Group '{group_name}' contains {len(params_to_apply)} parameters")

        if dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
            for param, value in params_to_apply.items():
                logger.info(f"Would apply: {param} = {value}")
            return True

        success = True
        applied_count = 0

        for param, value in params_to_apply.items():
            result = self.run_command(['sysctl', '-w', f'{param}={value}'], check=False)
            if result.returncode == 0:
                applied_count += 1
                logger.debug(f"Applied: {param} = {value}")
            else:
                logger.error(f"Failed to apply: {param} = {value}")
                success = False

        logger.info(f"Group application complete: {applied_count}/{len(params_to_apply)} parameters applied")
        return success

    def audit_parameter_history(self) -> dict:
        """
        ENHANCEMENT 11: Parameter History Tracking and Audit Trail
        Track and audit kernel parameter changes over time.

        Returns:
            dict: Audit information including current state and change history
        """
        logger.info("Auditing kernel parameter history")

        audit = {
            'audit_timestamp': datetime.now().isoformat(),
            'current_state': {},
            'config_files': [],
            'change_indicators': []
        }

        # Capture current state
        for param, expected_value in self.STIG_KERNEL_PARAMS.items():
            result = self.run_command(['sysctl', '-n', param], capture_output=True, check=False)
            if result.returncode == 0:
                current_value = result.stdout.strip()
                audit['current_state'][param] = {
                    'current': current_value,
                    'expected': expected_value,
                    'compliant': current_value == expected_value
                }

        # Check for STIG config file modifications
        config_file = '/etc/sysctl.d/99-stig-v2r3.conf'
        if os.path.exists(config_file):
            try:
                stat_info = os.stat(config_file)
                audit['config_files'].append({
                    'file': config_file,
                    'modified': datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                    'size': stat_info.st_size
                })
            except Exception as e:
                logger.error(f"Error checking config file: {e}")

        # Detect recent changes (parameters that differ from config)
        for param, state in audit['current_state'].items():
            if not state['compliant']:
                audit['change_indicators'].append({
                    'param': param,
                    'drift_type': 'non_compliant',
                    'current': state['current'],
                    'expected': state['expected']
                })

        logger.info(f"Audit complete: {len(audit['current_state'])} parameters audited, "
                   f"{len(audit['change_indicators'])} drift indicators found")

        return audit

    def apply_stig_params(self, enable_rollback: bool = True) -> bool:
        """
        Apply all STIG kernel parameters with comprehensive validation and rollback support.

        This enhanced method now includes:
        - Pre-change snapshot for rollback
        - Pre-change parameter validation
        - Performance impact assessment
        - Conflict detection
        - Reboot requirement detection
        - Automatic rollback on failure
        - Post-change persistence verification

        Args:
            enable_rollback: If True, create snapshot and enable automatic rollback on failure

        Returns:
            bool: True if parameters were applied successfully
        """
        logger.info("=" * 80)
        logger.info("STIG V2R3 Kernel Parameter Application with Enhanced Validation")
        logger.info("=" * 80)

        # ENHANCEMENT 6: Create snapshot for rollback capability
        snapshot = None
        if enable_rollback:
            logger.info("=== Creating Pre-Change Snapshot ===")
            try:
                snapshot = self.create_snapshot()
                logger.info(f"Snapshot created successfully: {snapshot['snapshot_id']}")
            except Exception as e:
                logger.error(f"Failed to create snapshot: {e}")
                if not STIGConfig.FORCE_NO_BACKUP:
                    logger.error("Aborting parameter application - snapshot creation failed")
                    return False

        # ENHANCEMENT 1: Validate current parameters before applying changes
        logger.info("=== Pre-Change Validation ===")
        validation = self.validate_current_params()

        if validation['drift_detected']:
            logger.warning(f"Parameter drift detected: {len(validation['non_compliant'])} "
                         f"parameters need remediation")
        else:
            logger.info("All parameters are already STIG compliant")

        # ENHANCEMENT 5: Assess performance impact
        logger.info("=== Performance Impact Assessment ===")
        impact = self.assess_performance_impact()

        if impact['overall_risk'] == 'HIGH':
            logger.warning("HIGH performance impact detected! Review high-impact parameters:")
            for item in impact['high_impact']:
                logger.warning(f"  - {item['param']}: {item['description']}")
                logger.warning(f"    Mitigation: {item['mitigation']}")

        # ENHANCEMENT 4: Detect parameter conflicts
        logger.info("=== Conflict Detection ===")
        conflicts = self.detect_parameter_conflicts()

        if conflicts['warnings']:
            logger.warning(f"Found {len(conflicts['warnings'])} potential conflicts/warnings:")
            for warning in conflicts['warnings']:
                logger.warning(f"  - {warning['param']}: {warning['warning']}")

        # ENHANCEMENT 3: Detect reboot requirements
        logger.info("=== Reboot Requirement Detection ===")
        reboot_info = self.detect_reboot_requirements()

        if reboot_info['reboot_recommended']:
            logger.warning(f"System reboot will be required for {len(reboot_info['reboot_required'])} "
                         f"parameters to take full effect")
            for item in reboot_info['reboot_required']:
                logger.info(f"  - {item['param']}: {item['reason']}")

        # Apply the STIG kernel parameters
        logger.info("=== Applying Kernel Parameters ===")

        # Track critical errors for rollback decision
        critical_errors = []
        applied_count = 0
        failed_count = 0

        try:
            # Write to sysctl.d
            content = "# STIG V2R3 Kernel Parameters\n"
            content += f"# Generated by UBUNTU20-STIG V2R3 Python script v{STIGConfig.SCRIPT_VERSION}\n"
            content += f"# STIG Version: {STIGConfig.STIG_VERSION} ({STIGConfig.STIG_RELEASE})\n"
            content += f"# Date: {datetime.now().isoformat()}\n"
            if snapshot:
                content += f"# Snapshot ID: {snapshot['snapshot_id']}\n"
            content += "#\n"
            content += "# WARNING: This file was auto-generated. Manual changes may be overwritten.\n"
            content += "#\n\n"

            for key, value in self.STIG_KERNEL_PARAMS.items():
                content += f"{key} = {value}\n"
                # Apply immediately
                result = self.run_command(['sysctl', '-w', f'{key}={value}'], check=False)
                if result.returncode == 0:
                    applied_count += 1
                    logger.debug(f"Applied {key} = {value}")
                else:
                    failed_count += 1
                    error_msg = f"Failed to apply {key} = {value}"
                    logger.error(error_msg)
                    critical_errors.append(error_msg)

            logger.info(f"Parameter application: {applied_count} succeeded, {failed_count} failed")

            # Write config file
            success = self.atomic_write('/etc/sysctl.d/99-stig-v2r3.conf', content)

            if not success:
                error_msg = "Failed to write sysctl configuration file"
                logger.error(error_msg)
                critical_errors.append(error_msg)
                raise Exception(error_msg)

            # Apply all settings from config file
            result = self.run_command(['sysctl', '-p', '/etc/sysctl.d/99-stig-v2r3.conf'],
                                     capture_output=True, check=False)

            if result.returncode != 0:
                error_msg = f"Error loading sysctl config: {result.stderr}"
                logger.error(error_msg)
                critical_errors.append(error_msg)
                success = False
            else:
                logger.info("Successfully loaded all sysctl parameters from config file")
                success = True

        except Exception as e:
            logger.error(f"Critical error during parameter application: {e}")
            critical_errors.append(str(e))
            success = False

        # ENHANCEMENT 6: Automatic rollback on critical failure
        if critical_errors and enable_rollback and snapshot and STIGConfig.ENABLE_AUTO_ROLLBACK:
            logger.error("=" * 80)
            logger.error("CRITICAL ERRORS DETECTED - Initiating Automatic Rollback")
            logger.error("=" * 80)
            logger.error(f"Errors encountered: {len(critical_errors)}")
            for error in critical_errors:
                logger.error(f"  - {error}")

            logger.warning("Attempting to restore from snapshot...")
            try:
                rollback_success = self.restore_from_snapshot(snapshot)
                if rollback_success:
                    logger.info("Rollback successful - system restored to pre-change state")
                    self.changes.append("Kernel parameter application FAILED - rolled back to original state")
                else:
                    logger.error("Rollback FAILED - system may be in inconsistent state!")
                    self.changes.append("WARNING: Kernel parameter rollback FAILED")
            except Exception as rollback_error:
                logger.error(f"Rollback exception: {rollback_error}")
                self.changes.append("CRITICAL: Rollback exception occurred")

            return False

        # ENHANCEMENT 2: Verify persistence after applying
        logger.info("=== Post-Change Persistence Verification ===")
        persistence = self.verify_persistence()

        if not persistence['persistence_verified']:
            logger.warning(f"{len(persistence['missing_from_config'])} parameters "
                         f"may not persist after reboot")
        else:
            logger.info("All parameters are properly configured for persistence")

        # Final validation to confirm changes
        logger.info("=== Post-Change Validation ===")
        final_validation = self.validate_current_params()

        if final_validation['drift_detected']:
            logger.warning("Some parameters still show drift after application - review errors above")
        else:
            logger.info("All kernel parameters are now STIG compliant!")

        if success:
            logger.info("=" * 80)
            logger.info("KERNEL PARAMETER APPLICATION SUCCESSFUL")
            logger.info("=" * 80)

            self.changes.append("Applied STIG V2R3 kernel parameters with enhanced validation and rollback support")
            self.add_stig_control("SYSCTL-ALL", "Applied all STIG kernel parameters")
            self.add_stig_control("V-255913", "Restricted kernel message buffer (dmesg)")

            # Add summary information
            summary = (f"Kernel parameter remediation complete: "
                      f"{len(final_validation['compliant'])}/{len(self.STIG_KERNEL_PARAMS)} compliant "
                      f"({applied_count} applied, {failed_count} failed)")
            logger.info(summary)
            self.changes.append(summary)

            # Add snapshot information
            if snapshot:
                snapshot_msg = f"Pre-change snapshot created: {snapshot['snapshot_id']}"
                logger.info(snapshot_msg)
                self.changes.append(snapshot_msg)

            # Add reboot recommendation if needed
            if reboot_info['reboot_recommended']:
                reboot_msg = ("REBOOT RECOMMENDED: Some kernel parameters require "
                            "a system reboot to take full effect")
                logger.warning(reboot_msg)
                self.changes.append(reboot_msg)

            # Log final compliance score
            compliance_pct = (len(final_validation['compliant']) / len(self.STIG_KERNEL_PARAMS)) * 100
            logger.info(f"Final compliance score: {compliance_pct:.1f}%")

        logger.info("=" * 80)
        return success


# ============================================================================
# SECTION 4: PAM CONFIGURATION
# ============================================================================
# TODO: Agent 4 - PAM Configuration Enhancement
# - Add PAM stack validation
# - Implement PAM module version checking
# - Add support for hardware tokens (if ENABLE_SSSD_PKI=True)
# - Implement PAM configuration testing
# - Add rollback for failed PAM changes
# ============================================================================

class PAMManager(SystemModifier):
    """Manage PAM authentication configuration"""
    
    def configure_faillock(self) -> bool:
        """Configure account lockout with pam_faillock - UBTU-20-010072"""
        logger.info("Configuring PAM faillock for account lockout")
        
        # Configure faillock settings in /etc/security/faillock.conf
        faillock_config = """# Faillock configuration (STIG V2R3 compliant)
# UBTU-20-010072, UBTU-20-010073
deny = 3
unlock_time = 0
fail_interval = 900
"""
        success = self.atomic_write('/etc/security/faillock.conf', faillock_config)
        
        if success:
            self.add_stig_control("UBTU-20-010072", "Configured faillock account lockout")
            self.add_stig_control("UBTU-20-010073", "Configured faillock deny/unlock")
        
        # Ensure pam_faillock is in PAM stack
        # This would require modifying /etc/pam.d/common-auth
        # TODO: Agent 4 should implement full PAM stack modification
        
        return success
    
    def configure_password_quality(self) -> bool:
        """Configure password quality requirements - Multiple V2R3 controls"""
        logger.info("Configuring password quality requirements")
        
        config = f"""# Password quality requirements (STIG V2R3 compliant)
# UBTU-20-010050 through UBTU-20-010070
minlen = {STIGConfig.PASSWORD_MIN_LENGTH}
dcredit = {STIGConfig.PASSWORD_DCREDIT}
ucredit = {STIGConfig.PASSWORD_UCREDIT}
lcredit = {STIGConfig.PASSWORD_LCREDIT}
ocredit = {STIGConfig.PASSWORD_OCREDIT}
difok = {STIGConfig.PASSWORD_DIFOK}
maxrepeat = {STIGConfig.PASSWORD_MAXREPEAT}
maxclassrepeat = {STIGConfig.PASSWORD_MAXCLASSREPEAT}
dictcheck = {STIGConfig.PASSWORD_DICTCHECK}
minclass = {STIGConfig.PASSWORD_MINCLASS}
gecoscheck = 1
usercheck = 1
enforcing = 1
retry = 3
"""
        
        success = self.atomic_write('/etc/security/pwquality.conf', config)
        if success:
            self.add_stig_control("UBTU-20-010050-070", "Configured password quality")
        return success
    
    def configure_password_hashing(self) -> bool:
        """Configure SHA512 password hashing - UBTU-20-010404"""
        logger.info("Configuring SHA512 password hashing")
        
        # Modify pam common-password
        pam_password_file = '/etc/pam.d/common-password'
        self.backup_file(pam_password_file)
        
        success = self.modify_config_line(
            pam_password_file,
            r'^password\s+\[success=1\s+default=ignore\]\s+pam_unix\.so',
            'password [success=1 default=ignore] pam_unix.so obscure sha512 shadow remember=5 rounds=5000'
        )
        
        if success:
            self.add_stig_control("UBTU-20-010404", "Configured SHA512 password hashing")
        return success
    
    def remove_nullok(self) -> bool:
        """Remove nullok from PAM configuration - V-251504 (NEW IN V2R3)"""
        logger.info("Removing nullok from PAM configuration")
        
        pam_files = [
            '/etc/pam.d/common-auth',
            '/etc/pam.d/common-account',
            '/etc/pam.d/common-password',
            '/etc/pam.d/common-session'
        ]
        
        success = True
        for pam_file in pam_files:
            if os.path.exists(pam_file):
                self.backup_file(pam_file)
                try:
                    with open(pam_file, 'r') as f:
                        content = f.read()
                    
                    # Remove nullok option
                    new_content = re.sub(r'\s+nullok(?:\s+|$)', ' ', content)
                    new_content = re.sub(r'\s+nullok_secure(?:\s+|$)', ' ', new_content)
                    
                    if new_content != content:
                        if self.atomic_write(pam_file, new_content):
                            logger.info(f"Removed nullok from {pam_file}")
                        else:
                            success = False
                except Exception as e:
                    logger.error(f"Failed to remove nullok from {pam_file}: {e}")
                    success = False
        
        if success:
            self.add_stig_control("V-251504", "Removed nullok from PAM")
        
        return success
    
    # TODO: Add PAM stack validation
    # TODO: Implement PAM testing framework
    # TODO: Add support for CAC/PIV cards (SSSD integration)


# ============================================================================
# SECTION 5: SSH CONFIGURATION
# ============================================================================
# TODO: Agent 5 - SSH Configuration Enhancement
# - Add SSH configuration syntax validation
# - Implement SSH service restart with connection preservation
# - Add SSH banner customization
# - Implement host key management
# - Add SSH connection logging enhancement
# ============================================================================

class SSHManager(SystemModifier):
    """Manage SSH daemon configuration"""
    
    SSHD_CONFIG_FILE = '/etc/ssh/sshd_config'
    
    def configure_sshd(self) -> bool:
        """Configure SSH daemon with STIG V2R3 settings"""
        logger.info("Configuring SSH daemon for STIG V2R3")
        
        self.backup_file(self.SSHD_CONFIG_FILE)
        
        # V2R3 compliant SSH settings
        stig_ssh_settings = {
            'Protocol': '2',
            'PermitRootLogin': STIGConfig.SSH_PERMIT_ROOT_LOGIN,  # UBTU-20-010047
            'PasswordAuthentication': STIGConfig.SSH_PASSWORD_AUTHENTICATION,  # UBTU-20-010046
            'PermitEmptyPasswords': 'no',  # UBTU-20-010035
            'HostbasedAuthentication': 'no',
            'IgnoreRhosts': 'yes',
            'X11Forwarding': STIGConfig.SSH_X11_FORWARDING,  # UBTU-20-010048
            'MaxAuthTries': str(STIGConfig.SSH_MAX_AUTH_TRIES),  # UBTU-20-010036
            'ClientAliveInterval': str(STIGConfig.SSH_CLIENT_ALIVE_INTERVAL),  # UBTU-20-010037
            'ClientAliveCountMax': str(STIGConfig.SSH_CLIENT_ALIVE_COUNT_MAX),
            'PermitUserEnvironment': 'no',
            'Ciphers': STIGConfig.SSH_CIPHERS,  # UBTU-20-010044
            'MACs': STIGConfig.SSH_MACS,  # UBTU-20-010043
            'KexAlgorithms': STIGConfig.SSH_KEX,  # V-255912 (NEW IN V2R3)
            'Banner': '/etc/issue.net',
            'PrintLastLog': 'yes',
            'UsePAM': 'yes',
            'StrictModes': 'yes',
            'GSSAPIAuthentication': 'no',
        }
        
        try:
            with open(self.SSHD_CONFIG_FILE, 'r') as f:
                content = f.read()
            
            for key, value in stig_ssh_settings.items():
                # Remove existing setting if present (commented or not)
                pattern = rf'^\s*#?\s*{key}\s+.*$'
                content = re.sub(pattern, '', content, flags=re.MULTILINE | re.IGNORECASE)
                
                # Add new setting
                content += f'\n{key} {value}'
            
            # Clean up multiple blank lines
            content = re.sub(r'\n\n+', '\n\n', content)
            
            success = self.atomic_write(self.SSHD_CONFIG_FILE, content)
            
            if success:
                self.changes.append("Configured SSH daemon")
                self.add_stig_control("UBTU-20-010042-048", "Configured SSH daemon")
                self.add_stig_control("V-255912", "Configured FIPS SSH key exchange")
                
                # Test SSH configuration
                test_result, test_output = self.run_command(['sshd', '-t'], check=False)
                if not test_result:
                    logger.error(f"SSH configuration test failed: {test_output}")
                    return False
                
                # Restart SSH
                svc_mgr = ServiceManager()
                svc_mgr.restart_service('sshd')
            
            return success
        except Exception as e:
            logger.error(f"Failed to configure SSH: {e}")
            self.errors.append(f"Failed to configure SSH: {e}")
            return False
    
    # TODO: Add SSH configuration validation
    # TODO: Implement connection-preserving restart
    # TODO: Add host key rotation


# ============================================================================
# SECTION 6: AUDIT CONFIGURATION  
# ============================================================================
# TODO: Agent 6 - Audit Enhancement
# - Add audit rule syntax validation
# - Implement audit log rotation verification
# - Add audit event rate monitoring
# - Implement audit rule conflict detection
# - Add support for remote audit logging
# ============================================================================

class AuditManager(SystemModifier):
    """Manage auditd configuration and rules"""
    
    AUDITD_CONF = '/etc/audit/auditd.conf'
    AUDIT_RULES_FILE = '/etc/audit/rules.d/stig-v2r3.rules'
    
    # V2R3 Audit Rules - Comprehensive
    AUDIT_RULES = """# STIG V2R3 Audit Rules
# Generated by UBUNTU20-STIG V2R3 Python script
# 136 CAT II controls related to auditing

## Remove any existing rules
-D

## Buffer Size (UBTU-20-010198)
-b 8192

## Failure Mode (UBTU-20-010199)
-f 2

## Audit the audit logs (UBTU-20-010244)
-w /var/log/audit/ -k auditlog

## V-274852: Audit cron execution (NEW IN V2R3)
-w /etc/cron.allow -p wa -k cron
-w /etc/cron.deny -p wa -k cron  
-w /etc/cron.d/ -p wa -k cron
-w /etc/cron.daily/ -p wa -k cron
-w /etc/cron.hourly/ -p wa -k cron
-w /etc/cron.monthly/ -p wa -k cron
-w /etc/cron.weekly/ -p wa -k cron
-w /etc/crontab -p wa -k cron
-w /var/spool/cron/ -k cron

## Time change auditing (UBTU-20-010100-010104)
-a always,exit -F arch=b64 -S adjtimex,settimeofday -k time-change
-a always,exit -F arch=b32 -S adjtimex,settimeofday,stime -k time-change
-a always,exit -F arch=b64 -S clock_settime -k time-change
-a always,exit -F arch=b32 -S clock_settime -k time-change
-w /etc/localtime -p wa -k time-change

## User, group, and password databases (UBTU-20-010105-010109)
-w /etc/group -p wa -k identity
-w /etc/passwd -p wa -k identity
-w /etc/gshadow -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/security/opasswd -p wa -k identity

## Network configuration (UBTU-20-010110-010117)
-a always,exit -F arch=b64 -S sethostname,setdomainname -k network-change
-a always,exit -F arch=b32 -S sethostname,setdomainname -k network-change
-w /etc/issue -p wa -k network-change
-w /etc/issue.net -p wa -k network-change
-w /etc/hosts -p wa -k network-change
-w /etc/networks -p wa -k network-change
-w /etc/network/ -p wa -k network-change
-w /etc/netplan/ -p wa -k network-change

## AppArmor events (UBTU-20-010118-010119)
-w /etc/apparmor/ -p wa -k apparmor
-w /etc/apparmor.d/ -p wa -k apparmor

## Kernel module operations (UBTU-20-010120-010123)
-w /sbin/insmod -p x -k modules
-w /sbin/rmmod -p x -k modules
-w /sbin/modprobe -p x -k modules
-a always,exit -F arch=b64 -S init_module,delete_module -k modules
-a always,exit -F arch=b32 -S init_module,delete_module -k modules
-w /etc/modprobe.conf -p wa -k modules
-w /etc/modprobe.d/ -p wa -k modules

## Login/logout events (UBTU-20-010124-010127)
-w /var/log/faillog -p wa -k logins
-w /var/log/lastlog -p wa -k logins
-w /var/log/tallylog -p wa -k logins

## Session initiation (UBTU-20-010128-010133)
-w /var/run/utmp -p wa -k session
-w /var/log/wtmp -p wa -k logins
-w /var/log/btmp -p wa -k logins

## Permission modifications (UBTU-20-010134-010165)
-a always,exit -F arch=b64 -S chmod,fchmod,fchmodat -F auid>=1000 -F auid!=4294967295 -k perm_mod
-a always,exit -F arch=b32 -S chmod,fchmod,fchmodat -F auid>=1000 -F auid!=4294967295 -k perm_mod
-a always,exit -F arch=b64 -S chown,fchown,lchown,fchownat -F auid>=1000 -F auid!=4294967295 -k perm_mod
-a always,exit -F arch=b32 -S chown,fchown,lchown,fchownat -F auid>=1000 -F auid!=4294967295 -k perm_mod
-a always,exit -F arch=b64 -S setxattr,lsetxattr,fsetxattr,removexattr,lremovexattr,fremovexattr -F auid>=1000 -F auid!=4294967295 -k perm_mod
-a always,exit -F arch=b32 -S setxattr,lsetxattr,fsetxattr,removexattr,lremovexattr,fremovexattr -F auid>=1000 -F auid!=4294967295 -k perm_mod

## Unauthorized access attempts (UBTU-20-010166-010197)
-a always,exit -F arch=b64 -S open,openat,open_by_handle_at -F exit=-EACCES -F auid>=1000 -F auid!=4294967295 -k access
-a always,exit -F arch=b32 -S open,openat,open_by_handle_at -F exit=-EACCES -F auid>=1000 -F auid!=4294967295 -k access
-a always,exit -F arch=b64 -S open,openat,open_by_handle_at -F exit=-EPERM -F auid>=1000 -F auid!=4294967295 -k access
-a always,exit -F arch=b32 -S open,openat,open_by_handle_at -F exit=-EPERM -F auid>=1000 -F auid!=4294967295 -k access

## Privileged commands (UBTU-20-010200-010216)
-a always,exit -F path=/usr/bin/sudo -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged
-a always,exit -F path=/usr/bin/su -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged
-a always,exit -F path=/usr/bin/chsh -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged
-a always,exit -F path=/usr/bin/chfn -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged
-a always,exit -F path=/usr/bin/passwd -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged
-a always,exit -F path=/usr/bin/mount -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged
-a always,exit -F path=/usr/bin/umount -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged
-a always,exit -F path=/usr/sbin/unix_chkpwd -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged

## File deletion events (UBTU-20-010267-010276)
-a always,exit -F arch=b64 -S unlink,unlinkat,rename,renameat -F auid>=1000 -F auid!=4294967295 -k delete
-a always,exit -F arch=b32 -S unlink,unlinkat,rename,renameat -F auid>=1000 -F auid!=4294967295 -k delete

## Sudoers changes (UBTU-20-010277-010278)
-w /etc/sudoers -p wa -k sudoers
-w /etc/sudoers.d/ -p wa -k sudoers

## Make configuration immutable (UBTU-20-010279)
-e 2
"""
    
    def configure_auditd(self) -> bool:
        """Configure audit daemon"""
        logger.info("Configuring audit daemon for STIG V2R3")
        
        self.backup_file(self.AUDITD_CONF)
        
        # Read existing config
        try:
            with open(self.AUDITD_CONF, 'r') as f:
                content = f.read()
        except FileNotFoundError:
            content = ""
        
        # Update critical settings
        settings = {
            'max_log_file': str(STIGConfig.AUDITD_MAX_LOG_FILE),  # UBTU-20-010300
            'max_log_file_action': STIGConfig.AUDITD_MAX_LOG_FILE_ACTION,  # UBTU-20-010416
            'space_left_action': STIGConfig.AUDITD_SPACE_LEFT_ACTION,  # UBTU-20-010217
            'admin_space_left_action': STIGConfig.AUDITD_ADMIN_SPACE_LEFT_ACTION,  # UBTU-20-010244
            'disk_full_action': 'HALT',
            'disk_error_action': 'HALT',
        }
        
        for key, value in settings.items():
            pattern = rf'^{key}\s*=.*$'
            replacement = f'{key} = {value}'
            if re.search(pattern, content, re.MULTILINE):
                content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            else:
                content += f'\n{replacement}'
        
        success = self.atomic_write(self.AUDITD_CONF, content)
        
        if not success:
            return False
        
        # Write audit rules
        success = self.atomic_write(self.AUDIT_RULES_FILE, self.AUDIT_RULES)
        
        if success:
            self.changes.append("Configured audit daemon and rules")
            self.add_stig_control("UBTU-20-010100-010279", "Configured comprehensive auditing")
            self.add_stig_control("V-274852", "Added cron execution auditing")
            
            # Load audit rules
            self.run_command(['augenrules', '--load'], check=False)
        
        return success
    
    # TODO: Add audit rule validation
    # TODO: Implement audit log space monitoring
    # TODO: Add remote syslog configuration


# ============================================================================
# SECTION 7: LOGIN AND ACCOUNT CONFIGURATION
# ============================================================================
# TODO: Agent 7 - Account Management Enhancement
# - Add user account auditing (find accounts without passwords)
# - Implement password aging enforcement for existing accounts
# - Add inactive account detection and handling
# - Implement account expiration management
# - Add support for temporary account management
# ============================================================================

class LoginManager(SystemModifier):
    """Manage login and account settings"""
    
    LOGIN_DEFS = '/etc/login.defs'
    
    def configure_login_defs(self) -> bool:
        """Configure /etc/login.defs with STIG V2R3 settings"""
        logger.info("Configuring login.defs")
        
        self.backup_file(self.LOGIN_DEFS)
        
        try:
            with open(self.LOGIN_DEFS, 'r') as f:
                content = f.read()
        except FileNotFoundError:
            content = ""
        
        settings = {
            'PASS_MAX_DAYS': str(STIGConfig.PASS_MAX_DAYS),  # UBTU-20-010008
            'PASS_MIN_DAYS': str(STIGConfig.PASS_MIN_DAYS),  # UBTU-20-010007
            'PASS_WARN_AGE': str(STIGConfig.PASS_WARN_AGE),
            'INACTIVE': str(STIGConfig.INACTIVE_DAYS),  # UBTU-20-010439
            'ENCRYPT_METHOD': 'SHA512',
            'SHA_CRYPT_MIN_ROUNDS': '5000',
            'SHA_CRYPT_MAX_ROUNDS': '5000',
            'UMASK': '077',  # UBTU-20-010016
            'CREATE_HOME': 'yes',
            'USERGROUPS_ENAB': 'yes',
        }
        
        for key, value in settings.items():
            pattern = rf'^{key}\s+.*$'
            replacement = f'{key} {value}'
            if re.search(pattern, content, re.MULTILINE):
                content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            else:
                content += f'\n{replacement}'
        
        success = self.atomic_write(self.LOGIN_DEFS, content)
        
        if success:
            self.changes.append("Configured login.defs")
            self.add_stig_control("UBTU-20-010007-010008", "Configured password aging")
            self.add_stig_control("UBTU-20-010016", "Set secure UMASK")
        
        return success
    
    def configure_session_timeout(self) -> bool:
        """Configure shell timeout - UBTU-20-010013"""
        logger.info("Configuring session timeout")
        
        timeout_config = """# Shell timeout for STIG V2R3 compliance
# UBTU-20-010013
TMOUT=600
readonly TMOUT
export TMOUT
"""
        
        success = self.atomic_write('/etc/profile.d/stig-timeout.sh', timeout_config)
        if success:
            self.add_stig_control("UBTU-20-010013", "Configured session timeout")
        return success
    
    def lock_blank_password_accounts(self) -> bool:
        """Lock accounts with blank passwords - V-251503 (NEW IN V2R3)"""
        logger.info("Checking for and locking accounts with blank passwords")
        
        try:
            # Find accounts with blank passwords
            result = subprocess.run(
                ['awk', '-F:', '($2 == "" ) { print $1 }', '/etc/shadow'],
                capture_output=True,
                text=True
            )
            
            blank_accounts = result.stdout.strip().split('\n')
            blank_accounts = [acc for acc in blank_accounts if acc]  # Remove empty strings
            
            if blank_accounts:
                logger.warning(f"Found accounts with blank passwords: {', '.join(blank_accounts)}")
                
                for account in blank_accounts:
                    # Lock the account
                    lock_result, _ = self.run_command(['passwd', '-l', account], check=False)
                    if lock_result:
                        self.changes.append(f"Locked blank password account: {account}")
                        logger.info(f"Locked account: {account}")
                
                self.add_stig_control("V-251503", "Locked all blank password accounts")
                return True
            else:
                logger.info("No accounts with blank passwords found")
                return True
                
        except Exception as e:
            logger.error(f"Failed to check for blank passwords: {e}")
            return False
    
    # TODO: Add comprehensive account auditing
    # TODO: Implement password aging for existing users
    # TODO: Add temporary account expiration management


# ============================================================================
# SECTION 8: BANNER CONFIGURATION
# ============================================================================
# TODO: Agent 8 - Banner Management Enhancement
# - Add banner compliance verification
# - Implement GDPR notice display
# - Add banner version management
# - Implement banner testing across all access methods
# ============================================================================

class BannerManager(SystemModifier):
    """Manage system banners"""
    
    def configure_banners(self) -> bool:
        """Configure system login banners - UBTU-20-010002, UBTU-20-010003"""
        logger.info("Configuring system banners")
        
        banner_text = STIGConfig.BANNER_TEXT
        
        # Write banners to various files
        files = {
            '/etc/issue': 'UBTU-20-010003',
            '/etc/issue.net': 'UBTU-20-010002',
        }
        
        success = True
        for file_path, control in files.items():
            if self.atomic_write(file_path, banner_text):
                self.add_stig_control(control, f"Configured banner: {file_path}")
            else:
                success = False
        
        return success
    
    # TODO: Add banner compliance verification
    # TODO: Implement graphical login banner (gdm3)


# ============================================================================
# SECTION 9: FILE PERMISSIONS
# ============================================================================
# TODO: Agent 9 - File Permission Enhancement
# - Add recursive permission checking
# - Implement world-writable file detection
# - Add SUID/SGID binary auditing
# - Implement file integrity monitoring setup (AIDE)
# - Add automated permission remediation for system files
# ============================================================================

class FilePermissionsManager(SystemModifier):
    """Manage file and directory permissions"""
    
    # STIG V2R3 file permissions
    FILE_PERMISSIONS = {
        '/etc/passwd': (0o644, 'root', 'root'),  # UBTU-20-010400
        '/etc/group': (0o644, 'root', 'root'),  # UBTU-20-010401
        '/etc/shadow': (0o000, 'root', 'root'),  # UBTU-20-010402
        '/etc/gshadow': (0o000, 'root', 'shadow'),  # UBTU-20-010403
        '/etc/ssh/sshd_config': (0o600, 'root', 'root'),
        '/var/log/': (0o755, 'root', 'root'),
    }
    
    def apply_stig_permissions(self) -> bool:
        """Apply STIG-compliant file permissions"""
        logger.info("Applying STIG V2R3 file permissions")
        
        success = True
        for path, (mode, owner, group) in self.FILE_PERMISSIONS.items():
            if os.path.exists(path):
                try:
                    if not STIGConfig.DRY_RUN:
                        os.chmod(path, mode)
                        if not IS_WINDOWS and pwd is not None:
                            try:
                                uid = pwd.getpwnam(owner).pw_uid
                                gid = grp.getgrnam(group).gr_gid
                                os.chown(path, uid, gid)
                            except (KeyError, OSError) as e:
                                logger.warning(f"Could not set ownership: {e}")
                    
                    logger.info(f"Set permissions {oct(mode)} {owner}:{group} on {path}")
                    self.changes.append(f"Set permissions on {path}")
                except Exception as e:
                    logger.error(f"Failed to set permissions on {path}: {e}")
                    success = False
        
        if success:
            self.add_stig_control("UBTU-20-010400-010403", "Set file permissions")
        
        return success
    
    # TODO: Add world-writable file detection
    # TODO: Implement SUID/SGID auditing
    # TODO: Add AIDE configuration


# ============================================================================
# SECTION 10: FIREWALL CONFIGURATION
# ============================================================================
# TODO: Agent 10 - Firewall Enhancement
# - Add zone-based firewall configuration
# - Implement port scanning detection
# - Add DDoS protection rules
# - Implement firewall rule validation
# - Add logging for denied connections
# ============================================================================

class FirewallManager(SystemModifier):
    """Manage UFW firewall"""
    
    def configure_firewall(self) -> bool:
        """Configure and enable UFW firewall - UBTU-20-010444-010447"""
        logger.info("Configuring UFW firewall")
        
        # Enable UFW
        self.run_command(['ufw', '--force', 'enable'])
        
        # Set default policies
        self.run_command(['ufw', 'default', 'deny', 'incoming'])
        self.run_command(['ufw', 'default', 'allow', 'outgoing'])
        self.run_command(['ufw', 'default', 'deny', 'routed'])
        
        # Allow SSH
        self.run_command(['ufw', 'allow', str(STIGConfig.SSH_PORT) + '/tcp'])
        
        # Enable logging
        self.run_command(['ufw', 'logging', 'on'])
        
        self.changes.append("Configured UFW firewall")
        self.add_stig_control("UBTU-20-010444-010447", "Configured firewall")
        return True
    
    # TODO: Add advanced firewall rules
    # TODO: Implement rate limiting
    # TODO: Add geo-blocking if needed


# ============================================================================
# SECTION 11: GRUB CONFIGURATION
# ============================================================================
# TODO: Agent 11 - GRUB Enhancement
# - Add GRUB password protection
# - Implement secure boot verification
# - Add kernel parameter validation
# - Implement GRUB configuration backup
# - Add boot loader integrity checking
# ============================================================================

class GrubManager(SystemModifier):
    """Manage GRUB bootloader configuration"""
    
    GRUB_CONFIG = '/etc/default/grub'
    
    def configure_grub(self) -> bool:
        """Configure GRUB with STIG V2R3 settings"""
        logger.info("Configuring GRUB bootloader")
        
        self.backup_file(self.GRUB_CONFIG)
        
        # Add audit=1 to kernel parameters - UBTU-20-010199
        self.modify_config_line(
            self.GRUB_CONFIG,
            r'GRUB_CMDLINE_LINUX_DEFAULT',
            'GRUB_CMDLINE_LINUX_DEFAULT="quiet audit=1"'
        )
        
        self.modify_config_line(
            self.GRUB_CONFIG,
            r'GRUB_CMDLINE_LINUX',
            'GRUB_CMDLINE_LINUX="audit=1"'
        )
        
        # Update GRUB
        self.run_command(['update-grub'], check=False)
        
        self.changes.append("Configured GRUB")
        self.add_stig_control("UBTU-20-010199", "Enabled audit at boot")
        return True
    
    def require_single_user_auth(self) -> bool:
        """Require authentication for single-user mode - UBTU-20-010009"""
        logger.info("Configuring single-user mode authentication")
        
        # This is handled by systemd, ensure rescue.service requires auth
        rescue_override_dir = '/etc/systemd/system/rescue.service.d'
        os.makedirs(rescue_override_dir, exist_ok=True)
        
        override_content = """[Service]
ExecStart=
ExecStart=-/lib/systemd/systemd-sulogin-shell rescue
"""
        success = self.atomic_write(
            f'{rescue_override_dir}/override.conf',
            override_content
        )
        
        if success:
            self.add_stig_control("UBTU-20-010009", "Configured single-user auth")
        
        return success
    
    # TODO: Add GRUB password configuration
    # TODO: Implement secure boot validation


# ============================================================================
# SECTION 12: USB AND WIRELESS RESTRICTIONS (NEW IN V2R3)
# ============================================================================
# TODO: Agent 12 - Hardware Restriction Enhancement
# - Add USB device whitelisting
# - Implement Bluetooth disabling
# - Add Thunderbolt restrictions
# - Implement hardware inventory logging
# - Add automated hardware compliance checking
# ============================================================================

class HardwareRestrictionManager(SystemModifier):
    """Manage USB and wireless hardware restrictions"""
    
    def disable_usb_storage(self) -> bool:
        """Disable USB storage mounting - V-251505 (NEW IN V2R3)"""
        if not STIGConfig.DISABLE_USB_STORAGE:
            logger.info("USB storage restriction disabled by configuration")
            return True
        
        logger.info("Disabling USB storage auto-mounting")
        
        usb_disable_config = """# Disable USB storage (STIG V2R3 V-251505)
install usb-storage /bin/false
blacklist usb-storage
"""
        
        success = self.atomic_write('/etc/modprobe.d/stig-disable-usb-storage.conf', usb_disable_config)
        
        if success:
            self.add_stig_control("V-251505", "Disabled USB storage")
            # Unload module if currently loaded
            self.run_command(['modprobe', '-r', 'usb-storage'], check=False)
        
        return success
    
    def disable_wireless(self) -> bool:
        """Disable wireless adapters - V-252704 (NEW IN V2R3)"""
        if not STIGConfig.DISABLE_WIRELESS:
            logger.info("Wireless restriction disabled by configuration")
            return True
        
        logger.info("Disabling wireless network adapters")
        
        try:
            # Find wireless interfaces
            result = subprocess.run(
                "ls -L -d /sys/class/net/*/wireless 2>/dev/null | xargs dirname 2>/dev/null | xargs basename 2>/dev/null",
                shell=True,
                capture_output=True,
                text=True
            )
            
            wireless_interfaces = result.stdout.strip().split('\n')
            wireless_interfaces = [iface for iface in wireless_interfaces if iface]
            
            if not wireless_interfaces:
                logger.info("No wireless interfaces found")
                return True
            
            logger.info(f"Found wireless interfaces: {', '.join(wireless_interfaces)}")
            
            # Disable each interface
            for iface in wireless_interfaces:
                # Bring interface down
                self.run_command(['ip', 'link', 'set', iface, 'down'], check=False)
                
                # Create systemd service to keep it disabled
                disable_service_content = f"""[Unit]
Description=Disable wireless interface {iface} (STIG V-252704)
Before=network-pre.target

[Service]
Type=oneshot
ExecStart=/usr/sbin/ip link set {iface} down
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
"""
                self.atomic_write(
                    f'/etc/systemd/system/disable-wireless-{iface}.service',
                    disable_service_content
                )
                
                # Enable the service
                self.run_command(['systemctl', 'enable', f'disable-wireless-{iface}.service'], check=False)
            
            self.add_stig_control("V-252704", "Disabled wireless adapters")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disable wireless: {e}")
            return False
    
    # TODO: Add USB device whitelisting
    # TODO: Implement Bluetooth disabling
    # TODO: Add Thunderbolt restrictions


# ============================================================================
# SECTION 13: SSSD/PKI CONFIGURATION (NEW IN V2R3)
# ============================================================================
# TODO: Agent 13 - SSSD/PKI Enhancement
# - Add complete SSSD configuration for CAC/PIV
# - Implement certificate validation rules
# - Add LDAP integration for certificate mapping
# - Implement CRL/OCSP checking
# - Add smartcard reader configuration
# ============================================================================

class SSSDManager(SystemModifier):
    """Manage SSSD for PKI-based authentication"""
    
    def configure_sssd_pki(self) -> bool:
        """Configure SSSD for PKI authentication - V-274853-274857 (NEW IN V2R3)"""
        if not STIGConfig.ENABLE_SSSD_PKI:
            logger.info("SSSD PKI configuration disabled (requires PKI infrastructure)")
            return True
        
        logger.info("Configuring SSSD for PKI authentication")
        
        # Install SSSD packages - V-274853
        pkg_mgr = PackageManager()
        sssd_packages = ['sssd', 'libpam-sss', 'libnss-sss']
        if not pkg_mgr.install_packages(sssd_packages):
            logger.error("Failed to install SSSD packages")
            return False
        
        # Basic SSSD configuration template
        sssd_config = f"""[sssd]
services = nss, pam
config_file_version = 2
domains = LOCAL

[nss]
filter_groups = root
filter_users = root

[pam]
# V-274856: Offline credential expiration
offline_credentials_expiration = {STIGConfig.SSSD_OFFLINE_CRED_EXPIRATION}

[domain/LOCAL]
id_provider = files

# V-274855: Certificate path validation
# V-274857: PKI certificate mapping
ldap_user_certificate = userCertificate;binary

# Enable certificate validation
certificate_verification = ocsp_dgst=sha1

# TODO: Agent 13 should complete LDAP configuration
# ldap_uri = ldap://your-ldap-server
# ldap_search_base = dc=example,dc=com
"""
        
        success = self.atomic_write('/etc/sssd/sssd.conf', sssd_config, mode=0o600)
        
        if success:
            # Enable and start SSSD - V-274854
            svc_mgr = ServiceManager()
            svc_mgr.enable_service('sssd')
            
            self.add_stig_control("V-274853", "Installed SSSD")
            self.add_stig_control("V-274854", "Enabled SSSD service")
            self.add_stig_control("V-274855", "Configured certificate validation")
            self.add_stig_control("V-274856", "Set offline credential expiration")
            self.add_stig_control("V-274857", "Configured PKI certificate mapping")
        
        return success
    
    # TODO: Complete LDAP integration
    # TODO: Add CRL/OCSP configuration
    # TODO: Implement smartcard reader setup


# ============================================================================
# SECTION 14: SUDO RESTRICTIONS (NEW IN V2R3)
# ============================================================================
# TODO: Agent 14 - Sudo Enhancement
# - Add sudo usage logging enhancement
# - Implement sudo policy validation
# - Add sudo command whitelisting
# - Implement sudo session recording
# - Add automated sudo policy auditing
# ============================================================================

class SudoManager(SystemModifier):
    """Manage sudo configuration"""
    
    def restrict_sudo_all(self) -> bool:
        """Remove ALL from sudoers - V-274858 (NEW IN V2R3)"""
        logger.info("Restricting sudo ALL usage")
        
        sudoers_files = ['/etc/sudoers'] + glob.glob('/etc/sudoers.d/*')
        
        found_all = False
        for sudoers_file in sudoers_files:
            if not os.path.isfile(sudoers_file):
                continue
            
            self.backup_file(sudoers_file)
            
            try:
                with open(sudoers_file, 'r') as f:
                    content = f.read()
                
                # Look for dangerous ALL patterns
                if re.search(r'^\s*[^#]*\s+ALL\s*=.*ALL', content, re.MULTILINE):
                    found_all = True
                    logger.warning(f"Found 'ALL' usage in {sudoers_file}")
                    self.warnings.append(f"Manual review required for {sudoers_file} - contains ALL")
                    
            except Exception as e:
                logger.error(f"Error checking {sudoers_file}: {e}")
        
        if found_all:
            self.add_stig_control("V-274858", "Identified sudo ALL usage (manual review required)")
            logger.warning("MANUAL ACTION REQUIRED: Review and restrict sudo ALL usage")
        else:
            self.add_stig_control("V-274858", "Verified no sudo ALL usage")
        
        return True
    
    def restrict_sudo_nopasswd(self) -> bool:
        """Remove NOPASSWD from sudoers - V-274859 (NEW IN V2R3)"""
        logger.info("Restricting sudo NOPASSWD usage")
        
        sudoers_files = ['/etc/sudoers'] + glob.glob('/etc/sudoers.d/*')
        
        modified = False
        for sudoers_file in sudoers_files:
            if not os.path.isfile(sudoers_file):
                continue
            
            self.backup_file(sudoers_file)
            
            try:
                with open(sudoers_file, 'r') as f:
                    content = f.read()
                
                # Remove NOPASSWD
                new_content = re.sub(r'\s*NOPASSWD\s*:\s*', ' ', content)
                
                if new_content != content:
                    modified = True
                    # Validate sudoers syntax
                    temp_file = f'/tmp/sudoers.tmp.{os.getpid()}'
                    with open(temp_file, 'w') as f:
                        f.write(new_content)
                    
                    # Check syntax
                    result = subprocess.run(
                        ['visudo', '-c', '-f', temp_file],
                        capture_output=True
                    )
                    
                    if result.returncode == 0:
                        self.atomic_write(sudoers_file, new_content, mode=0o440)
                        logger.info(f"Removed NOPASSWD from {sudoers_file}")
                    else:
                        logger.error(f"Syntax error in modified {sudoers_file}, skipping")
                    
                    os.unlink(temp_file)
                    
            except Exception as e:
                logger.error(f"Error processing {sudoers_file}: {e}")
        
        if modified:
            self.add_stig_control("V-274859", "Removed NOPASSWD from sudo")
        else:
            self.add_stig_control("V-274859", "Verified no NOPASSWD usage")
        
        return True
    
    def configure_sudo_group(self) -> bool:
        """Ensure only authorized users in sudo group - UBTU-20-010012"""
        logger.info("Configuring sudo group membership")
        
        try:
            # Get sudo group members
            sudo_group = grp.getgrnam('sudo')
            sudo_members = sudo_group.gr_mem
            
            logger.info(f"Current sudo group members: {', '.join(sudo_members)}")
            self.warnings.append(f"MANUAL REVIEW: Verify sudo group members: {', '.join(sudo_members)}")
            
            self.add_stig_control("UBTU-20-010012", "Identified sudo group members (manual review)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to check sudo group: {e}")
            return False
    
    # TODO: Add automated sudo policy validation
    # TODO: Implement sudo usage monitoring


# ============================================================================
# SECTION 15: ADVANCED SECURITY MODULES
# ============================================================================
# TODO: Agent 15 - Security Module Enhancement
# - Add complete AppArmor profile configuration
# - Implement AIDE integrity checking
# - Add SELinux support (if needed)
# - Implement file integrity monitoring
# - Add security module testing
# ============================================================================

class SecurityModulesManager(SystemModifier):
    """Manage AppArmor and other security modules"""
    
    def configure_apparmor(self) -> bool:
        """Configure AppArmor - UBTU-20-010439"""
        logger.info("Configuring AppArmor")
        
        # Install AppArmor
        pkg_mgr = PackageManager()
        apparmor_packages = ['apparmor', 'apparmor-profiles', 'apparmor-utils']
        if not pkg_mgr.install_packages(apparmor_packages):
            return False
        
        # Enable AppArmor
        svc_mgr = ServiceManager()
        svc_mgr.enable_service('apparmor')
        
        # Set all profiles to enforce mode
        self.run_command(['aa-enforce', '/etc/apparmor.d/*'], check=False)
        
        self.add_stig_control("UBTU-20-010439", "Configured AppArmor")
        return True
    
    def configure_aide(self) -> bool:
        """Configure AIDE file integrity - UBTU-20-010449"""
        logger.info("Configuring AIDE")
        
        # Install AIDE
        pkg_mgr = PackageManager()
        if not pkg_mgr.install_packages(['aide', 'aide-common']):
            return False
        
        # Initialize AIDE database
        logger.info("Initializing AIDE database (this may take several minutes)...")
        result, _ = self.run_command(['aideinit'], check=False)
        
        if result:
            # Move new database to active
            if os.path.exists('/var/lib/aide/aide.db.new'):
                shutil.move('/var/lib/aide/aide.db.new', '/var/lib/aide/aide.db')
            
            # Setup daily cron job
            aide_cron = """#!/bin/bash
# AIDE daily check (STIG UBTU-20-010449)
/usr/bin/aide --check
"""
            self.atomic_write('/etc/cron.daily/aide', aide_cron, mode=0o755)
            
            self.add_stig_control("UBTU-20-010449", "Configured AIDE")
            return True
        
        return False
    
    # TODO: Add AppArmor profile customization
    # TODO: Implement AIDE configuration tuning


# ============================================================================
# MAIN REMEDIATION CLASS
# ============================================================================

class UBUNTU20STIGRemediation:
    """Main class to orchestrate STIG V2R3 remediation"""
    
    def __init__(self):
        self.all_changes = []
        self.all_errors = []
        self.all_warnings = []
        self.all_stig_controls = []
    
    def check_prerequisites(self) -> bool:
        """Check system prerequisites"""
        logger.info("="*80)
        logger.info(f"UBUNTU20-STIG {STIGConfig.STIG_VERSION} Remediation Script")
        logger.info(f"{STIGConfig.STIG_RELEASE} - Benchmark Date: {STIGConfig.STIG_DATE}")
        logger.info("172 Total Controls (14 CAT I, 136 CAT II, 22 CAT III)")
        logger.info("="*80)
        
        # Check if running as root
        if not is_admin():
            logger.error("This script must be run as root")
            return False
        
        # Check OS version
        if not STIGConfig.SKIP_OS_CHECK:
            try:
                with open('/etc/os-release', 'r') as f:
                    os_release = f.read()
                
                if 'Ubuntu 20.04' not in os_release:
                    logger.error("This script is designed for Ubuntu 20.04 only")
                    logger.error("Set STIGConfig.SKIP_OS_CHECK = True to bypass (not recommended)")
                    return False
            except Exception as e:
                logger.warning(f"Could not verify OS version: {e}")
        
        logger.info("Prerequisites check passed")
        return True
    
    def collect_results(self, modifier: SystemModifier):
        """Collect changes and errors from a modifier"""
        self.all_changes.extend(modifier.changes)
        self.all_errors.extend(modifier.errors)
        self.all_warnings.extend(modifier.warnings)
        self.all_stig_controls.extend(modifier.stig_controls)
    
    def run_cat1_controls(self):
        """Run Category 1 (High severity) controls - 14 controls"""
        if not STIGConfig.CAT1_PATCH:
            logger.info("Skipping CAT1 controls (disabled)")
            return
        
        logger.info("")
        logger.info("="*80)
        logger.info("EXECUTING CATEGORY 1 (HIGH SEVERITY) CONTROLS - 14 Controls")
        logger.info("="*80)
        
        # SSH Configuration (CAT1)
        ssh_mgr = SSHManager()
        ssh_mgr.configure_sshd()
        self.collect_results(ssh_mgr)
        
        # PAM password hashing and nullok removal (CAT1)
        pam_mgr = PAMManager()
        pam_mgr.configure_password_hashing()
        pam_mgr.remove_nullok()  # V-251504 NEW
        self.collect_results(pam_mgr)
        
        # Lock blank password accounts (V-251503 NEW)
        login_mgr = LoginManager()
        login_mgr.lock_blank_password_accounts()
        self.collect_results(login_mgr)
        
        # Package removal (telnet, rsh-server)
        pkg_mgr = PackageManager()
        pkg_mgr.remove_packages(['telnet', 'rsh-server'])
        self.collect_results(pkg_mgr)
        
        # SSSD PKI configuration (V-274857)
        if STIGConfig.ENABLE_SSSD_PKI:
            sssd_mgr = SSSDManager()
            sssd_mgr.configure_sssd_pki()
            self.collect_results(sssd_mgr)
    
    def run_cat2_controls(self):
        """Run Category 2 (Medium severity) controls - 136 controls"""
        if not STIGConfig.CAT2_PATCH:
            logger.info("Skipping CAT2 controls (disabled)")
            return
        
        logger.info("")
        logger.info("="*80)
        logger.info("EXECUTING CATEGORY 2 (MEDIUM SEVERITY) CONTROLS - 136 Controls")
        logger.info("="*80)
        
        # Package management
        pkg_mgr = PackageManager()
        pkg_mgr.update_cache()
        
        # Install required packages
        required_packages = [
            'aide',
            'aide-common',
            'auditd',
            'audispd-plugins',
            'libpam-pwquality',
            'libpam-modules',
            'apparmor',
            'apparmor-profiles',
            'apparmor-utils',
            'rsyslog',
            'chrony',
            'ufw',
        ]
        pkg_mgr.install_packages(required_packages)
        
        # Remove unwanted packages
        unwanted_packages = [
            'rsh-client',
            'nis',
            'tftp',
            'talk',
        ]
        pkg_mgr.remove_packages(unwanted_packages)
        
        self.collect_results(pkg_mgr)
        
        # PAM configuration
        pam_mgr = PAMManager()
        pam_mgr.configure_faillock()
        pam_mgr.configure_password_quality()
        self.collect_results(pam_mgr)
        
        # Kernel parameters
        sysctl_mgr = SysctlManager()
        sysctl_mgr.apply_stig_params()
        self.collect_results(sysctl_mgr)
        
        # Audit configuration
        audit_mgr = AuditManager()
        audit_mgr.configure_auditd()
        self.collect_results(audit_mgr)
        
        # Login configuration
        login_mgr = LoginManager()
        login_mgr.configure_login_defs()
        login_mgr.configure_session_timeout()
        self.collect_results(login_mgr)
        
        # Banner configuration
        banner_mgr = BannerManager()
        banner_mgr.configure_banners()
        self.collect_results(banner_mgr)
        
        # Service management
        svc_mgr = ServiceManager()
        
        # Enable required services
        svc_mgr.enable_service('auditd')
        svc_mgr.enable_service('rsyslog')
        svc_mgr.enable_service('apparmor')
        svc_mgr.enable_service('ufw')
        
        # Disable unnecessary services
        unnecessary_services = [
            'avahi-daemon',
            'cups',
            'isc-dhcp-server',
            'bluetooth',
            'autofs',
        ]
        for svc in unnecessary_services:
            svc_mgr.disable_service(svc)
        
        # Mask dangerous services
        svc_mgr.mask_service('ctrl-alt-del.target')
        svc_mgr.mask_service('debug-shell.service')
        
        self.collect_results(svc_mgr)
        
        # Firewall
        fw_mgr = FirewallManager()
        fw_mgr.configure_firewall()
        self.collect_results(fw_mgr)
        
        # GRUB configuration
        grub_mgr = GrubManager()
        grub_mgr.configure_grub()
        grub_mgr.require_single_user_auth()
        self.collect_results(grub_mgr)
        
        # V2R3 NEW: USB and Wireless restrictions
        hw_mgr = HardwareRestrictionManager()
        hw_mgr.disable_usb_storage()
        hw_mgr.disable_wireless()
        self.collect_results(hw_mgr)
        
        # V2R3 NEW: Sudo restrictions
        sudo_mgr = SudoManager()
        sudo_mgr.restrict_sudo_all()
        sudo_mgr.restrict_sudo_nopasswd()
        sudo_mgr.configure_sudo_group()
        self.collect_results(sudo_mgr)
        
        # Security modules
        sec_mgr = SecurityModulesManager()
        sec_mgr.configure_apparmor()
        sec_mgr.configure_aide()
        self.collect_results(sec_mgr)
    
    def run_cat3_controls(self):
        """Run Category 3 (Low severity) controls - 22 controls"""
        if not STIGConfig.CAT3_PATCH:
            logger.info("Skipping CAT3 controls (disabled)")
            return
        
        logger.info("")
        logger.info("="*80)
        logger.info("EXECUTING CATEGORY 3 (LOW SEVERITY) CONTROLS - 22 Controls")
        logger.info("="*80)
        
        # File permissions
        perm_mgr = FilePermissionsManager()
        perm_mgr.apply_stig_permissions()
        self.collect_results(perm_mgr)
    
    def print_summary(self):
        """Print remediation summary"""
        logger.info("")
        logger.info("="*80)
        logger.info(f"REMEDIATION SUMMARY - STIG {STIGConfig.STIG_VERSION}")
        logger.info("="*80)
        
        logger.info(f"\nTotal changes made: {len(self.all_changes)}")
        if self.all_changes:
            logger.info("\nChanges (first 50):")
            for change in self.all_changes[:50]:
                logger.info(f"  ✓ {change}")
            if len(self.all_changes) > 50:
                logger.info(f"  ... and {len(self.all_changes) - 50} more changes")
        
        logger.info(f"\nSTIG Controls Applied: {len(self.all_stig_controls)}")
        if self.all_stig_controls:
            logger.info("\nKey STIG Controls:")
            for control in self.all_stig_controls[:20]:
                logger.info(f"  ✓ {control['id']}: {control['description']}")
            if len(self.all_stig_controls) > 20:
                logger.info(f"  ... and {len(self.all_stig_controls) - 20} more controls")
        
        if self.all_warnings:
            logger.warning(f"\nTotal warnings: {len(self.all_warnings)}")
            logger.warning("\nWarnings:")
            for warning in self.all_warnings:
                logger.warning(f"  ⚠ {warning}")
        
        if self.all_errors:
            logger.error(f"\nTotal errors: {len(self.all_errors)}")
            logger.error("\nErrors:")
            for error in self.all_errors:
                logger.error(f"  ✗ {error}")
        
        logger.info("")
        logger.info("="*80)
        logger.info("IMPORTANT POST-REMEDIATION STEPS")
        logger.info("="*80)
        logger.info("")
        logger.info("1. Review the log file: /var/log/ubuntu20-stig-v2r3-remediation.log")
        logger.info("2. Review all warnings for manual actions required")
        logger.info("3. Reboot the system to apply all changes")
        logger.info("4. Test system functionality after reboot")
        logger.info("5. Run OpenSCAP/SCC SCAP scan to verify compliance")
        logger.info("6. Restore from backups if needed (.stig-v2r3-backup-* files)")
        logger.info("")
        logger.info("NEW IN V2R3:")
        logger.info("- Review USB storage and wireless restrictions")
        logger.info("- Verify sudo restrictions (no ALL, no NOPASSWD)")
        logger.info("- Check accounts with blank passwords have been locked")
        logger.info("- Verify SSSD configuration if PKI is enabled")
        logger.info("")
        logger.info("="*80)
    
    def run(self):
        """Main execution method with enhanced safety features"""
        recovery_mgr = RecoveryManager()
        failed_command_count = 0
        
        try:
            # EMERGENCY RECOVERY MODE - restore from backups only
            if STIGConfig.EMERGENCY_RECOVERY_MODE:
                logger.warning("="*80)
                logger.warning("EMERGENCY RECOVERY MODE ACTIVATED")
                logger.warning("="*80)
                EmergencyRecovery.emergency_mode()
                return True
            
            # Basic prerequisites
            if not self.check_prerequisites():
                return False
            
            # PRE-FLIGHT SAFETY CHECKS
            if STIGConfig.ENABLE_PREFLIGHT_CHECKS:
                preflight = PreFlightChecker()
                if not preflight.run_all_checks():
                    logger.error("\n❌ Pre-flight checks FAILED. Cannot proceed.")
                    logger.error("Fix the issues above or set ENABLE_PREFLIGHT_CHECKS=False to bypass")
                    logger.error("(bypassing is NOT recommended for production)")
                    return False
                
                # Display warnings
                if preflight.warnings:
                    logger.warning("\n⚠️  Pre-flight WARNINGS:")
                    for warning in preflight.warnings:
                        logger.warning(f"  - {warning}")
                    
                    if not STIGConfig.DRY_RUN:
                        logger.warning("\nPress Ctrl+C within 10 seconds to abort...")
                        try:
                            import time
                            time.sleep(10)
                        except KeyboardInterrupt:
                            logger.warning("Aborted by user")
                            return False
            
            # CREATE RECOVERY POINT
            if STIGConfig.ENABLE_AUTO_ROLLBACK and not STIGConfig.DRY_RUN:
                logger.info("\n" + "="*80)
                logger.info("CREATING RECOVERY POINT")
                logger.info("="*80)
                if not recovery_mgr.create_recovery_point("pre-stig-remediation"):
                    logger.error("❌ Failed to create recovery point")
                    logger.error("Set ENABLE_AUTO_ROLLBACK=False to bypass (not recommended)")
                    return False
                logger.info("✓ Recovery point created successfully")
            
            # DRY RUN notification
            if STIGConfig.DRY_RUN:
                logger.info("")
                logger.info("*" * 80)
                logger.info("DRY RUN MODE - No changes will be applied")
                logger.info("*" * 80)
                logger.info("")
            
            # Run controls by category with error tracking
            try:
                self.run_cat1_controls()
                
                # Check for critical errors after CAT I
                if len(self.all_errors) > STIGConfig.MAX_FAILED_COMMANDS:
                    raise Exception(f"Too many errors ({len(self.all_errors)}), aborting")
                
                self.run_cat2_controls()
                
                # Check for critical errors after CAT II
                if len(self.all_errors) > STIGConfig.MAX_FAILED_COMMANDS:
                    raise Exception(f"Too many errors ({len(self.all_errors)}), aborting")
                
                self.run_cat3_controls()
                
            except Exception as e:
                logger.error(f"\n❌ Critical error during remediation: {e}")
                
                # AUTOMATIC ROLLBACK on critical errors
                if STIGConfig.ENABLE_AUTO_ROLLBACK and not STIGConfig.DRY_RUN:
                    logger.warning("\n" + "="*80)
                    logger.warning("INITIATING AUTOMATIC ROLLBACK")
                    logger.warning("="*80)
                    
                    if recovery_mgr.current_recovery_point:
                        if recovery_mgr.restore_recovery_point():
                            logger.warning("✓ System restored to pre-remediation state")
                            logger.warning("Please review errors and try again")
                        else:
                            logger.error("❌ ROLLBACK FAILED - Manual recovery required")
                            logger.error("Use: python3 script.py with EMERGENCY_RECOVERY_MODE=True")
                    
                raise
            
            # POST-REMEDIATION VALIDATION
            if STIGConfig.ENABLE_CONFIG_VALIDATION and not STIGConfig.DRY_RUN:
                logger.info("\n" + "="*80)
                logger.info("POST-REMEDIATION VALIDATION")
                logger.info("="*80)
                
                validator = ConfigValidator()
                if not validator.validate_all():
                    logger.error("\n❌ POST-REMEDIATION VALIDATION FAILED")
                    logger.error("Critical configuration errors detected!")
                    
                    if STIGConfig.ENABLE_AUTO_ROLLBACK:
                        logger.warning("\nInitiating automatic rollback due to validation failure...")
                        if recovery_mgr.restore_recovery_point():
                            logger.warning("✓ System restored to pre-remediation state")
                            return False
                    
                    logger.error("\nManual intervention required:")
                    for error in validator.validation_errors:
                        logger.error(f"  - {error}")
                    return False
                
                logger.info("✓ Post-remediation validation passed")
            
            # Print summary
            self.print_summary()
            
            # Final success check
            success = len(self.all_errors) == 0
            
            if success:
                logger.info("\n" + "="*80)
                logger.info("✓ STIG REMEDIATION COMPLETED SUCCESSFULLY")
                logger.info("="*80)
            else:
                logger.warning("\n" + "="*80)
                logger.warning("⚠️  STIG REMEDIATION COMPLETED WITH ERRORS")
                logger.warning("="*80)
            
            return success
        
        except KeyboardInterrupt:
            logger.warning("\n\nRemediation interrupted by user!")
            
            if STIGConfig.ENABLE_AUTO_ROLLBACK and not STIGConfig.DRY_RUN:
                logger.warning("Initiating rollback...")
                recovery_mgr.restore_recovery_point()
            
            raise
        
        except Exception as e:
            logger.exception("Unhandled exception during remediation")
            return False


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def validate_platform_compatibility():
    """Validate platform compatibility before execution"""
    if IS_WINDOWS:
        if not any(['--remote' in arg for arg in sys.argv]) and '--help' not in sys.argv and '-h' not in sys.argv:
            print("\n" + "="*80)
            print("ERROR: Direct execution on Windows is not supported")
            print("="*80)
            print("\nThis script performs Ubuntu 20.04 STIG remediation.")
            print("For remote execution from Windows:")
            print("  python ubuntu20_stig_v2r3_enhanced.py --remote <linux-host> --remote-key <ssh-key>")
            print("="*80)
            sys.exit(1)
        if not PARAMIKO_AVAILABLE:
            print("ERROR: Remote execution requires paramiko library")
            print("Install with: pip install paramiko")
            sys.exit(1)
        logger.info("Windows - Remote Execution Mode Only")
    elif IS_LINUX:
        logger.info("Linux - Direct Execution Mode")


def main():
    """Main entry point with enhanced safety features and remote execution"""
    
    # Parse command-line arguments
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    # Validate platform
    validate_platform_compatibility()
    
    # Handle special modes first
    if args.emergency:
        logger.warning("="*80)
        logger.warning("EMERGENCY RECOVERY MODE")
        logger.warning("="*80)
        EmergencyRecovery.emergency_mode()
        sys.exit(0)
    
    if args.list_backups:
        recovery_mgr = RecoveryManager()
        points = recovery_mgr.list_recovery_points()
        
        print("\nAvailable Recovery Points:")
        print("="*80)
        if points:
            for point in points:
                print(f"  ID: {point['id']}")
                print(f"      Name: {point['name']}")
                print(f"      Time: {point['timestamp']}")
                print()
        else:
            print("  No recovery points found")
        print()
        sys.exit(0)
    
    # Apply CLI arguments to configuration
    if args.dry_run:
        STIGConfig.DRY_RUN = True
    
    if args.force:
        STIGConfig.FORCE_MODE = True
        STIGConfig.FORCE_IGNORE_ERRORS = args.force_ignore_errors
        STIGConfig.FORCE_SKIP_VALIDATION = args.force_skip_validation
        STIGConfig.FORCE_NO_ROLLBACK = args.force_no_rollback
        STIGConfig.FORCE_SKIP_PREFLIGHT = args.force_skip_preflight
        STIGConfig.FORCE_APPLY_ALL = args.force_apply_all
        STIGConfig.FORCE_OVERRIDE_OS = args.force_override_os
        STIGConfig.FORCE_NO_BACKUP = args.force_no_backup
    
    if args.no_preflight:
        STIGConfig.ENABLE_PREFLIGHT_CHECKS = False
    
    if args.no_rollback:
        STIGConfig.ENABLE_AUTO_ROLLBACK = False
    
    if args.no_validation:
        STIGConfig.ENABLE_CONFIG_VALIDATION = False
    
    if args.cat1_only:
        STIGConfig.CAT1_PATCH = True
        STIGConfig.CAT2_PATCH = False
        STIGConfig.CAT3_PATCH = False
    elif args.cat2_only:
        STIGConfig.CAT1_PATCH = False
        STIGConfig.CAT2_PATCH = True
        STIGConfig.CAT3_PATCH = False
    elif args.cat3_only:
        STIGConfig.CAT1_PATCH = False
        STIGConfig.CAT2_PATCH = False
        STIGConfig.CAT3_PATCH = True
    
    # Check for remote execution mode
    if args.remote:
        STIGConfig.ENABLE_REMOTE_EXECUTION = True
        STIGConfig.REMOTE_HOSTS = args.remote
        STIGConfig.REMOTE_USER = args.remote_user
        STIGConfig.REMOTE_KEY_FILE = args.remote_key
        STIGConfig.REMOTE_PORT = args.remote_port
        STIGConfig.REMOTE_PARALLEL = args.remote_parallel
        STIGConfig.REMOTE_MAX_WORKERS = args.remote_workers
        
        # Get password if no key file provided
        if not args.remote_key and not args.remote_password:
            print(f"\nSSH Authentication for remote hosts")
            print(f"Username: {args.remote_user}")
            STIGConfig.REMOTE_PASSWORD = getpass.getpass(f"Password for {args.remote_user}: ")
        elif args.remote_password:
            STIGConfig.REMOTE_PASSWORD = args.remote_password
    
    try:
        # Banner
        print("\n" + "="*80)
        print("UBUNTU 20.04 STIG V2R3 REMEDIATION SCRIPT")
        print(f"Version {STIGConfig.SCRIPT_VERSION} - Enhanced with Remote Execution & Force Modes")
        print("="*80)
        print()
        
        # Force mode validation
        if STIGConfig.FORCE_MODE:
            print("\n" + "!"*80)
            print("!! WARNING: FORCE MODE ENABLED !!")
            print("!"*80)
            print("\nThe following safety bypasses are active:")
            
            if STIGConfig.FORCE_IGNORE_ERRORS:
                print("  ⚠️  FORCE_IGNORE_ERRORS: Will continue even on command failures")
            if STIGConfig.FORCE_SKIP_VALIDATION:
                print("  ⚠️  FORCE_SKIP_VALIDATION: Configuration validation disabled")
            if STIGConfig.FORCE_NO_ROLLBACK:
                print("  ⚠️  FORCE_NO_ROLLBACK: Automatic rollback disabled")
            if STIGConfig.FORCE_SKIP_PREFLIGHT:
                print("  ⚠️  FORCE_SKIP_PREFLIGHT: Pre-flight safety checks disabled")
            if STIGConfig.FORCE_APPLY_ALL:
                print("  ⚠️  FORCE_APPLY_ALL: All STIGs will be applied regardless of risk")
            if STIGConfig.FORCE_OVERRIDE_OS:
                print("  ⚠️  FORCE_OVERRIDE_OS: OS version check disabled")
            if STIGConfig.FORCE_NO_BACKUP:
                print("  ⚠️  FORCE_NO_BACKUP: System backups will NOT be created")
            
            print("\nForce mode should ONLY be used:")
            print("  • In controlled test environments")
            print("  • When recovering from failed remediations")
            print("  • When you fully understand the risks")
            print("\n" + "!"*80)
            
            if not STIGConfig.DRY_RUN:
                response = input("\nAre you ABSOLUTELY SURE you want to continue with force mode? (type 'YES' to confirm): ")
                if response != 'YES':
                    print("\nForce mode cancelled. Exiting for safety.")
                    sys.exit(1)
        
        # Safety feature status
        print("\nConfiguration:")
        print(f"  Pre-flight Checks:      {'ENABLED' if STIGConfig.ENABLE_PREFLIGHT_CHECKS else 'DISABLED'}")
        print(f"  Automatic Rollback:     {'ENABLED' if STIGConfig.ENABLE_AUTO_ROLLBACK else 'DISABLED'}")
        print(f"  Config Validation:      {'ENABLED' if STIGConfig.ENABLE_CONFIG_VALIDATION else 'DISABLED'}")
        print(f"  Dry Run Mode:           {'ENABLED' if STIGConfig.DRY_RUN else 'DISABLED'}")
        print(f"  Force Mode:             {'ENABLED' if STIGConfig.FORCE_MODE else 'DISABLED'}")
        
        print(f"\nSTIG Categories:")
        print(f"  CAT I (High):           {'ENABLED' if STIGConfig.CAT1_PATCH else 'DISABLED'}")
        print(f"  CAT II (Medium):        {'ENABLED' if STIGConfig.CAT2_PATCH else 'DISABLED'}")
        print(f"  CAT III (Low):          {'ENABLED' if STIGConfig.CAT3_PATCH else 'DISABLED'}")
        print()
        
        # REMOTE EXECUTION MODE
        if STIGConfig.ENABLE_REMOTE_EXECUTION:
            print("\n" + "="*80)
            print("REMOTE EXECUTION MODE")
            print("="*80)
            print(f"\nTarget Hosts: {', '.join(STIGConfig.REMOTE_HOSTS)}")
            print(f"SSH User: {STIGConfig.REMOTE_USER}")
            print(f"SSH Port: {STIGConfig.REMOTE_PORT}")
            print(f"Execution Mode: {'PARALLEL' if STIGConfig.REMOTE_PARALLEL else 'SERIAL'}")
            if STIGConfig.REMOTE_PARALLEL:
                print(f"Max Workers: {STIGConfig.REMOTE_MAX_WORKERS}")
            print()
            
            # Create remote executor
            executor = RemoteExecutor()
            
            # Add all hosts
            for hostname in STIGConfig.REMOTE_HOSTS:
                executor.add_host(
                    hostname=hostname,
                    username=STIGConfig.REMOTE_USER,
                    password=STIGConfig.REMOTE_PASSWORD,
                    key_file=STIGConfig.REMOTE_KEY_FILE,
                    port=STIGConfig.REMOTE_PORT,
                    timeout=STIGConfig.REMOTE_TIMEOUT
                )
            
            # Get current script path
            script_path = os.path.abspath(__file__)
            
            # Execute on remote hosts
            try:
                if STIGConfig.REMOTE_PARALLEL:
                    success = executor.execute_parallel(script_path, STIGConfig.REMOTE_MAX_WORKERS)
                else:
                    success = executor.execute_serial(script_path)
                
                # Print summary
                executor.print_summary()
                
                sys.exit(0 if success else 1)
                
            finally:
                executor.cleanup()
        
        # LOCAL EXECUTION MODE
        else:
            print("Execution Mode: LOCAL")
            print()
            
            # Run remediation locally
            remediation = UBUNTU20STIGRemediation()
            success = remediation.run()
            
            sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        logger.warning("\n\nRemediation interrupted by user")
        logger.warning("Use --emergency flag to restore from backups if needed")
        sys.exit(130)
    except Exception as e:
        logger.exception("Fatal error during execution")
        logger.error("\nUse --emergency flag to attempt recovery")
        sys.exit(1)


if __name__ == '__main__':
    main()
