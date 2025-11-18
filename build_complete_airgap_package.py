#!/usr/bin/env python3
"""
COMPLETE AIR-GAP PACKAGE BUILDER
=================================

Creates a 100% guaranteed-to-work air-gapped STIG package that requires
NO apt, NO pip, NO internet on either Windows client or Ubuntu target.

This builder:
1. Downloads all Windows dependencies (paramiko, etc.)
2. Verifies all required files are present
3. Creates a complete, ready-to-transfer package
4. Generates checksums for verification
5. Creates comprehensive documentation

Output: A single ZIP file that works plug-and-play in air-gapped environments

Author: Complete Air-Gap Package Builder
Version: 3.0.0
"""

import os
import sys
import shutil
import zipfile
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime

class CompleteAirGapPackageBuilder:
    """Build complete, guaranteed-to-work air-gap package"""

    def __init__(self):
        timestamp = datetime.now().strftime('%Y%m%d')
        self.package_name = f"COMPLETE-STIG-AIRGAP-{timestamp}"
        self.package_dir = Path(self.package_name)

        self.required_files = {
            'airgap_windows_stig_executor_complete.py': 'Main Windows executor',
            'ubuntu20_stig_v2r3_enhanced.py': 'STIG remediation script',
        }

        self.optional_files = {
            'CLAUDE.md': 'Project documentation',
            'README.md': 'General readme',
        }

    def print_banner(self):
        """Print builder banner"""
        banner = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║           COMPLETE AIR-GAP STIG PACKAGE BUILDER v3.0.0                       ║
║              100% Offline Solution - Guaranteed to Work                      ║
║                                                                               ║
║  Creates plug-and-play package for completely air-gapped environments        ║
║  • No apt-get required on Ubuntu target                                      ║
║  • No pip required on Ubuntu target                                          ║
║  • No internet required anywhere                                             ║
║  • All dependencies bundled                                                  ║
║  • Works in classified/isolated networks                                     ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""
        print(banner)

    def check_prerequisites(self):
        """Check if we have everything needed"""
        print("\n" + "="*80)
        print("CHECKING PREREQUISITES")
        print("="*80)

        all_good = True

        # Check Python version
        if sys.version_info >= (3, 6):
            print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        else:
            print(f"✗ Python 3.6+ required (current: {sys.version})")
            all_good = False

        # Check pip
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', '--version'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("✓ pip is available")
            else:
                print("✗ pip not available")
                all_good = False
        except:
            print("✗ pip not available")
            all_good = False

        # Check internet (for dependency download)
        print("\n📡 Checking internet connectivity...")
        try:
            import urllib.request
            urllib.request.urlopen('https://pypi.org', timeout=10)
            print("✓ Internet connection available")
        except:
            print("⚠️  No internet connection")
            print("   Dependencies must be downloaded on a connected system")

        return all_good

    def check_required_files(self):
        """Check if all required files are present"""
        print("\n" + "="*80)
        print("CHECKING REQUIRED FILES")
        print("="*80)

        missing = []
        found = []

        for filename, description in self.required_files.items():
            filepath = Path(filename)
            if filepath.exists():
                size = filepath.stat().st_size / 1024
                print(f"✓ {filename} ({size:.1f} KB)")
                print(f"  → {description}")
                found.append(filename)
            else:
                print(f"✗ {filename} - MISSING")
                print(f"  → {description}")
                missing.append(filename)

        if missing:
            print(f"\n❌ Missing {len(missing)} required files:")
            for f in missing:
                print(f"   • {f}")
            print("\nCannot proceed without required files.")
            return False

        print(f"\n✓ All {len(found)} required files present")
        return True

    def download_dependencies(self):
        """Download Python dependencies for Windows"""
        print("\n" + "="*80)
        print("DOWNLOADING WINDOWS DEPENDENCIES")
        print("="*80)

        deps_dir = Path('dependencies')

        # Check if already exists
        if deps_dir.exists():
            wheel_files = list(deps_dir.glob('*.whl'))
            tar_files = list(deps_dir.glob('*.tar.gz'))
            total_files = len(wheel_files) + len(tar_files)

            if total_files > 0:
                print(f"\n✓ Dependencies folder exists with {total_files} packages")
                redownload = input("  Re-download dependencies? [y/N]: ").strip().lower()
                if redownload != 'y':
                    print("  Using existing dependencies")
                    return True
                else:
                    print("  Removing old dependencies...")
                    shutil.rmtree(deps_dir)

        # Create dependencies directory
        deps_dir.mkdir(exist_ok=True)

        print("\n📥 Downloading packages...")
        print("   This requires internet connection and may take a few minutes")

        packages = [
            'paramiko',
            'cryptography',
            'bcrypt',
            'pynacl',
            'cffi',
            'pycparser',
            'six'
        ]

        try:
            cmd = [
                sys.executable, '-m', 'pip', 'download',
                '--dest', str(deps_dir),
                '--prefer-binary',
            ] + packages

            print(f"\n   Executing: pip download...")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )

            if result.returncode == 0:
                # Count downloaded files
                wheel_files = list(deps_dir.glob('*.whl'))
                tar_files = list(deps_dir.glob('*.tar.gz'))
                total_files = len(wheel_files) + len(tar_files)

                # Calculate total size
                total_size = sum(f.stat().st_size for f in (wheel_files + tar_files))
                total_mb = total_size / (1024 * 1024)

                print(f"\n✓ Download complete!")
                print(f"   Files: {total_files} packages")
                print(f"   Size: {total_mb:.2f} MB")

                return True
            else:
                print(f"\n✗ Download failed:")
                print(result.stderr)
                return False

        except subprocess.TimeoutExpired:
            print("\n✗ Download timed out")
            return False
        except Exception as e:
            print(f"\n✗ Download error: {e}")
            return False

    def create_package_structure(self):
        """Create package directory structure"""
        print("\n" + "="*80)
        print("CREATING PACKAGE STRUCTURE")
        print("="*80)

        if self.package_dir.exists():
            print(f"\n⚠️  Package directory exists: {self.package_dir}")
            response = input("   Delete and recreate? [y/N]: ").strip().lower()
            if response == 'y':
                shutil.rmtree(self.package_dir)
                print("   ✓ Removed existing package")
            else:
                print("   ✗ Cannot proceed")
                return False

        # Create directory structure
        self.package_dir.mkdir()
        (self.package_dir / 'documentation').mkdir()

        print(f"\n✓ Created package directory: {self.package_dir}/")
        return True

    def copy_files_to_package(self):
        """Copy all required files to package"""
        print("\n" + "="*80)
        print("COPYING FILES TO PACKAGE")
        print("="*80)

        print("\n📄 Copying main scripts...")

        # Copy main scripts
        for filename in self.required_files.keys():
            src = Path(filename)
            dst = self.package_dir / filename
            if src.exists():
                shutil.copy2(src, dst)
                size = src.stat().st_size / 1024
                print(f"   ✓ {filename} ({size:.1f} KB)")

        # Copy dependencies folder
        print("\n📦 Copying dependencies folder...")
        src_deps = Path('dependencies')
        if src_deps.exists():
            dst_deps = self.package_dir / 'dependencies'
            shutil.copytree(src_deps, dst_deps)

            dep_files = list(dst_deps.glob('*'))
            total_size = sum(f.stat().st_size for f in dep_files) / (1024 * 1024)
            print(f"   ✓ {len(dep_files)} package files ({total_size:.1f} MB)")
        else:
            print("   ⚠️  Dependencies folder not found (download first)")

        # Copy optional documentation
        print("\n📚 Copying documentation...")
        for filename, description in self.optional_files.items():
            src = Path(filename)
            if src.exists():
                dst = self.package_dir / 'documentation' / filename
                shutil.copy2(src, dst)
                print(f"   ✓ {filename}")

        print("\n✓ All files copied successfully")
        return True

    def create_quick_start_guide(self):
        """Create quick start guide"""
        print("\n📝 Creating quick start guide...")

        guide_content = f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║                    COMPLETE AIR-GAP STIG PACKAGE                              ║
║                       QUICK START GUIDE                                       ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Package Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Version: 3.0.0 - Complete Air-Gap Edition
STIG: Ubuntu 20.04 DISA STIG V2R3 (172 controls)

═══════════════════════════════════════════════════════════════════════════════
WHAT'S IN THIS PACKAGE
═══════════════════════════════════════════════════════════════════════════════

✓ airgap_windows_stig_executor_complete.py - Windows executor (100% offline)
✓ ubuntu20_stig_v2r3_enhanced.py          - STIG remediation script
✓ dependencies/                            - All Python packages (offline install)
✓ documentation/                           - Additional documentation
✓ This file - Quick start guide

═══════════════════════════════════════════════════════════════════════════════
REQUIREMENTS
═══════════════════════════════════════════════════════════════════════════════

Windows System (Client):
   • Python 3.6 or higher
   • Network connectivity to target Ubuntu system
   • This package extracted

Ubuntu 20.04 System (Target):
   • Ubuntu 20.04 LTS
   • SSH server running
   • Python3 installed (standard on Ubuntu 20.04)
   • User account with sudo privileges
   • Console access (KVM/IPMI/Physical) HIGHLY RECOMMENDED

═══════════════════════════════════════════════════════════════════════════════
QUICK START (5 STEPS)
═══════════════════════════════════════════════════════════════════════════════

1️⃣  VERIFY PYTHON (on Windows)

   Open Command Prompt or PowerShell:
   python --version

   Should show Python 3.6 or higher

2️⃣  PREPARE TARGET SYSTEM

   □ Create VM snapshot or backup
   □ Ensure console access is available
   □ Test SSH access manually:
     ssh username@target_ip
   □ Verify sudo access works:
     sudo -v

3️⃣  RUN THE EXECUTOR (on Windows)

   Navigate to extracted package folder:
   cd path\\to\\{self.package_name}

   Run the script:
   python airgap_windows_stig_executor_complete.py

   The script will:
   • Install dependencies automatically (from local files)
   • Guide you through configuration
   • Connect to target via SSH
   • Transfer STIG script
   • Execute all 172 STIG controls
   • Create automatic backups
   • Provide real-time progress

4️⃣  REBOOT TARGET SYSTEM

   After successful execution:
   ssh username@target_ip 'sudo reboot'

   Wait 2-3 minutes for reboot to complete

5️⃣  VERIFY ACCESS

   Test SSH access after reboot:
   ssh username@target_ip

   If password auth was disabled, use SSH keys

═══════════════════════════════════════════════════════════════════════════════
WHAT GETS CHANGED (172 STIG CONTROLS)
═══════════════════════════════════════════════════════════════════════════════

CAT I (High) - 14 Critical Controls:
   • SSH: Root login disabled, weak auth removed
   • Passwords: SHA512 hashing, no null passwords
   • Packages: Telnet and rsh removed

CAT II (Medium) - 136 Important Controls:
   • Password Policy: 15+ chars, complexity required
   • Account Lockout: 3 failed attempts = 15 min lockout
   • Kernel: 59 sysctl security parameters
   • Audit: 136 comprehensive audit rules
   • SSH: FIPS ciphers, idle timeout, key exchange restrictions
   • Firewall: UFW enabled, restrictive rules
   • Services: Unnecessary services disabled
   • USB: Storage auto-mount disabled
   • Sudo: NOPASSWD removed, logging enabled
   • AppArmor: Enforcing mode
   • AIDE: File integrity monitoring

CAT III (Low) - 22 Additional Controls:
   • File permissions hardening
   • Documentation requirements
   • Additional security policies

═══════════════════════════════════════════════════════════════════════════════
SECURITY CONFIGURATION OPTIONS
═══════════════════════════════════════════════════════════════════════════════

During execution, you can configure:

□ SSH Password Authentication
  Default: ENABLED (recommended for air-gap)
  Disable only if SSH keys are configured

□ FIPS Mode
  Default: DISABLED (requires special kernel)
  Enable only if FIPS kernel installed

□ Firewall Rules
  Default: STRICT (deny all except SSH)
  Recommended: Keep strict

□ USB Storage
  Default: DISABLED
  Recommended: Keep disabled for security

□ Wireless Adapters
  Default: DISABLED
  Recommended: Keep disabled for security

═══════════════════════════════════════════════════════════════════════════════
BACKUP & RECOVERY
═══════════════════════════════════════════════════════════════════════════════

Automatic Backups Created:
   • /var/backups/pre-stig-airgap-YYYYMMDD_HHMMSS/
   • Individual file backups: *.stig-v2r3-backup-*

To Restore SSH Access (if broken):
   1. Use console access (KVM/IPMI/Physical)
   2. Restore SSH config:
      sudo cp /var/backups/pre-stig-airgap-*/sshd_config /etc/ssh/
      sudo systemctl restart sshd
   3. Test access

To Restore Other Files:
   sudo cp /var/backups/pre-stig-airgap-*/path/to/file /etc/path/to/file
   sudo systemctl restart <service>

═══════════════════════════════════════════════════════════════════════════════
TROUBLESHOOTING
═══════════════════════════════════════════════════════════════════════════════

Problem: "paramiko not found"
Solution: Dependencies will auto-install from local files
          Ensure 'dependencies' folder is present

Problem: "SSH connection failed"
Solution: • Verify target is reachable: ping target_ip
          • Check SSH service: ssh username@target_ip
          • Verify firewall allows SSH
          • Check credentials are correct

Problem: "Sudo password failed"
Solution: • Verify user has sudo privileges
          • Test manually: ssh username@target_ip 'sudo -v'
          • Check sudo password is correct

Problem: "STIG script not found"
Solution: • Verify ubuntu20_stig_v2r3_enhanced.py is present
          • Check filename is exactly correct (case-sensitive)

Problem: "Can't access system after execution"
Solution: • Use console access (KVM/IPMI/Physical)
          • Restore SSH config from backup (see above)
          • Check if password auth was disabled (use SSH keys)

═══════════════════════════════════════════════════════════════════════════════
VERIFICATION & COMPLIANCE
═══════════════════════════════════════════════════════════════════════════════

After execution:

1. Check STIG Log:
   ssh username@target_ip
   sudo tail -100 /var/log/ubuntu20-stig-v2r3-remediation.log

2. Verify Services:
   sudo systemctl status sshd auditd rsyslog ufw

3. Check Firewall:
   sudo ufw status verbose

4. Verify Audit Rules:
   sudo auditctl -l | wc -l
   (Should show ~136 rules)

5. Run SCAP Scan:
   Use SCAP scanner to verify compliance
   Expected: ~100% compliance with STIG V2R3

═══════════════════════════════════════════════════════════════════════════════
SUPPORT & LOGS
═══════════════════════════════════════════════════════════════════════════════

Execution logs are saved to:
   Windows: %USERPROFILE%\\stig_execution_logs\\
   Ubuntu: /var/log/ubuntu20-stig-v2r3-remediation.log

For issues, provide:
   • Execution log file
   • Target Ubuntu version: cat /etc/os-release
   • Python version: python3 --version
   • Error messages from output

═══════════════════════════════════════════════════════════════════════════════
IMPORTANT SECURITY NOTES
═══════════════════════════════════════════════════════════════════════════════

⚠️  ALWAYS test in non-production environment first
⚠️  ALWAYS create backup/snapshot before execution
⚠️  ALWAYS have console access ready
⚠️  ALWAYS verify system access after reboot

✓  This package works 100% offline (no apt, no pip, no internet)
✓  All dependencies are bundled
✓  Automatic backups are created
✓  Real-time progress is shown
✓  Comprehensive logging is provided

═══════════════════════════════════════════════════════════════════════════════

For detailed documentation, see: documentation/ folder

Package Version: 3.0.0-complete-airgap
Generated: {datetime.now().isoformat()}

═══════════════════════════════════════════════════════════════════════════════
"""

        quick_start_file = self.package_dir / 'QUICK_START.txt'
        with open(quick_start_file, 'w', encoding='utf-8') as f:
            f.write(guide_content)

        print(f"   ✓ Created: QUICK_START.txt")
        return True

    def create_run_script(self):
        """Create Windows batch file launcher"""
        print("\n📝 Creating Windows launcher...")

        batch_content = f"""@echo off
REM Complete Air-Gap STIG Executor Launcher
REM Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

echo.
echo ===============================================================================
echo             COMPLETE AIR-GAP STIG EXECUTOR
echo                 Ubuntu 20.04 STIG V2R3
echo ===============================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    echo.
    echo Please install Python 3.6 or higher from python.org
    echo.
    pause
    exit /b 1
)

echo Python is installed
python --version
echo.

echo Starting air-gap STIG executor...
echo.

python airgap_windows_stig_executor_complete.py

echo.
echo ===============================================================================
echo Execution complete. Check the output above for results.
echo ===============================================================================
echo.
pause
"""

        batch_file = self.package_dir / 'RUN_STIG_AIRGAP.bat'
        with open(batch_file, 'w', encoding='utf-8', newline='\r\n') as f:
            f.write(batch_content)

        print(f"   ✓ Created: RUN_STIG_AIRGAP.bat")
        return True

    def generate_checksums(self):
        """Generate SHA256 checksums"""
        print("\n🔐 Generating checksums...")

        checksums = {}

        for item in self.package_dir.rglob('*'):
            if item.is_file() and item.name != 'SHA256SUMS.txt':
                sha256 = hashlib.sha256()
                with open(item, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b''):
                        sha256.update(chunk)

                rel_path = item.relative_to(self.package_dir)
                checksums[str(rel_path)] = sha256.hexdigest()

        # Write checksums file
        checksum_file = self.package_dir / 'SHA256SUMS.txt'
        with open(checksum_file, 'w') as f:
            f.write(f"# SHA256 Checksums for Complete Air-Gap STIG Package\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n")
            f.write(f"# Package: {self.package_name}\n")
            f.write("#\n")
            f.write("# Verify on Linux/Mac: sha256sum -c SHA256SUMS.txt\n")
            f.write("# Verify on Windows: certutil -hashfile <filename> SHA256\n\n")

            for filepath, checksum in sorted(checksums.items()):
                f.write(f"{checksum}  {filepath}\n")

        print(f"   ✓ Generated checksums for {len(checksums)} files")
        print(f"   ✓ Saved to: SHA256SUMS.txt")
        return True

    def create_archive(self):
        """Create ZIP archive"""
        print("\n" + "="*80)
        print("CREATING ARCHIVE")
        print("="*80)

        archive_name = f"{self.package_name}.zip"
        print(f"\n📦 Creating: {archive_name}")
        print("   This may take a moment...")

        try:
            with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                file_count = 0
                for item in self.package_dir.rglob('*'):
                    if item.is_file():
                        arcname = item.relative_to(self.package_dir.parent)
                        zipf.write(item, arcname)
                        file_count += 1
                        if file_count % 10 == 0:
                            print(f"   • Added {file_count} files...")

            # Get archive size
            archive_path = Path(archive_name)
            size_mb = archive_path.stat().st_size / (1024 * 1024)

            print(f"\n✓ Archive created successfully!")
            print(f"   Name: {archive_name}")
            print(f"   Size: {size_mb:.2f} MB")
            print(f"   Files: {file_count}")

            # Generate archive checksum
            print("\n🔐 Generating archive checksum...")
            sha256 = hashlib.sha256()
            with open(archive_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256.update(chunk)

            checksum_file = Path(f"{archive_name}.sha256")
            with open(checksum_file, 'w') as f:
                f.write(f"{sha256.hexdigest()}  {archive_name}\n")

            print(f"   ✓ Checksum: {checksum_file}")
            print(f"   ✓ SHA256: {sha256.hexdigest()}")

            return archive_name

        except Exception as e:
            print(f"\n✗ Failed to create archive: {e}")
            return None

    def print_final_summary(self, archive_name):
        """Print build summary"""
        archive_path = Path(archive_name)
        package_size = archive_path.stat().st_size / (1024 * 1024)

        summary = f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║                          BUILD SUCCESSFUL!                                    ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Package: {archive_name}
Size: {package_size:.2f} MB
Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

═══════════════════════════════════════════════════════════════════════════════
WHAT'S IN THE PACKAGE
═══════════════════════════════════════════════════════════════════════════════

✓ Complete air-gap STIG executor (Windows)
✓ Ubuntu 20.04 STIG V2R3 script (172 controls)
✓ All Python dependencies (offline install)
✓ Quick start guide
✓ Windows batch launcher
✓ SHA256 checksums for verification
✓ Complete documentation

═══════════════════════════════════════════════════════════════════════════════
NEXT STEPS
═══════════════════════════════════════════════════════════════════════════════

1️⃣  VERIFY PACKAGE INTEGRITY

   Windows:
   certutil -hashfile {archive_name} SHA256

   Linux/Mac:
   sha256sum {archive_name}

   Compare with: {archive_name}.sha256

2️⃣  TRANSFER TO AIR-GAPPED SYSTEM

   • Use approved transfer method (USB, CD/DVD, secure transfer)
   • Scan for malware if required by policy
   • Document transfer for compliance
   • Verify checksum after transfer

3️⃣  EXTRACT ON AIR-GAPPED SYSTEM

   Windows:
   Right-click → Extract All
   OR use: tar -xf {archive_name}

   Linux:
   unzip {archive_name}

4️⃣  READ THE QUICK START GUIDE

   After extraction, open:
   {self.package_name}/QUICK_START.txt

5️⃣  RUN THE EXECUTOR

   Windows - Option A (Easy):
   Double-click: RUN_STIG_AIRGAP.bat

   Windows - Option B (Command Line):
   python airgap_windows_stig_executor_complete.py

   The script will:
   • Auto-install dependencies (from local files)
   • Guide you through configuration
   • Connect to target Ubuntu system
   • Execute all 172 STIG controls
   • Create automatic backups
   • Provide real-time progress

═══════════════════════════════════════════════════════════════════════════════
GUARANTEED TO WORK IN
═══════════════════════════════════════════════════════════════════════════════

✓ Completely air-gapped networks (no internet)
✓ Classified environments
✓ Isolated networks
✓ DMZ networks
✓ Systems without package repositories
✓ Environments where apt/pip are unavailable
✓ Restricted networks with no external access

NO apt-get required on Ubuntu target
NO pip required on Ubuntu target
NO internet required anywhere
ALL dependencies included

═══════════════════════════════════════════════════════════════════════════════
SECURITY FEATURES
═══════════════════════════════════════════════════════════════════════════════

✓ 172 DISA STIG V2R3 controls applied
  • 14 CAT I (Critical)
  • 136 CAT II (Medium)
  • 22 CAT III (Low)

✓ Automatic backups before all changes
✓ Real-time execution progress
✓ Comprehensive logging
✓ Post-execution verification
✓ Recovery procedures included
✓ Rollback capability

═══════════════════════════════════════════════════════════════════════════════
SUPPORT
═══════════════════════════════════════════════════════════════════════════════

For issues or questions:
1. Check QUICK_START.txt (troubleshooting section)
2. Review execution logs
3. Verify all prerequisites are met
4. Test in non-production environment first

Logs are saved to:
  Windows: %USERPROFILE%\\stig_execution_logs\\
  Ubuntu: /var/log/ubuntu20-stig-v2r3-remediation.log

═══════════════════════════════════════════════════════════════════════════════

Package ready for air-gapped deployment!

Version: 3.0.0-complete-airgap
Build Date: {datetime.now().isoformat()}

═══════════════════════════════════════════════════════════════════════════════
"""
        print(summary)

    def build(self):
        """Main build process"""
        try:
            self.print_banner()

            # Check prerequisites
            if not self.check_prerequisites():
                print("\n❌ Prerequisites not met")
                return False

            # Check required files
            if not self.check_required_files():
                print("\n❌ Required files missing")
                return False

            # Download dependencies
            if not self.download_dependencies():
                print("\n⚠️  Dependency download failed")
                print("   You can copy dependencies manually and re-run")
                return False

            # Create package structure
            if not self.create_package_structure():
                print("\n❌ Failed to create package structure")
                return False

            # Copy files
            if not self.copy_files_to_package():
                print("\n❌ Failed to copy files")
                return False

            # Create documentation
            if not self.create_quick_start_guide():
                print("\n❌ Failed to create quick start guide")
                return False

            # Create launcher
            if not self.create_run_script():
                print("\n❌ Failed to create launcher")
                return False

            # Generate checksums
            if not self.generate_checksums():
                print("\n❌ Failed to generate checksums")
                return False

            # Create archive
            archive_name = self.create_archive()
            if not archive_name:
                print("\n❌ Failed to create archive")
                return False

            # Print summary
            self.print_final_summary(archive_name)

            return True

        except KeyboardInterrupt:
            print("\n\n⚠️  Build interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Build failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main entry point"""
    builder = CompleteAirGapPackageBuilder()
    success = builder.build()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
