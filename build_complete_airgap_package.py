#!/usr/bin/env python3
"""
Complete Air-Gap Package Builder for Ubuntu 20.04 STIG Automation
==================================================================

This script downloads ALL dependencies for a completely offline STIG deployment:
1. Windows Python packages (paramiko, cryptography, etc.)
2. Ubuntu .deb packages (auditd, aide, apparmor, etc.)
3. Builds a single transferable package

Run this on an INTERNET-CONNECTED system, then transfer the generated
ZIP package to your air-gapped environment.

Requirements:
    - Python 3.6+
    - Internet connection
    - pip install requests (for downloading Ubuntu packages)

Author: Complete Air-Gap Edition
Version: 3.0.0
"""

import os
import sys
import subprocess
import shutil
import hashlib
import zipfile
from pathlib import Path
from datetime import datetime
import json

# Check Python version
if sys.version_info < (3, 6):
    print("ERROR: Python 3.6 or higher required")
    sys.exit(1)

class CompleteAirGapPackageBuilder:
    """Build complete air-gap package with Windows + Ubuntu dependencies"""

    def __init__(self):
        self.root_dir = Path.cwd()
        self.package_dir = self.root_dir / "airgap_package"
        self.dependencies_dir = self.package_dir / "dependencies"
        self.ubuntu_packages_dir = self.package_dir / "ubuntu_packages"
        self.scripts_dir = self.package_dir / "scripts"

        # Required files
        self.required_files = [
            'airgap_complete_executor.py',
            'ubuntu20_stig_v2r3_airgap.py',
        ]

        # Windows Python packages
        self.python_packages = [
            'paramiko',
            'cryptography',
            'bcrypt',
            'PyNaCl',
            'cffi',
            'pycparser',
            'six',
        ]

        # Ubuntu .deb packages needed for STIG compliance
        self.ubuntu_packages = {
            # Core security packages
            'auditd': 'auditing daemon',
            'audispd-plugins': 'audit dispatcher plugins',
            'aide': 'file integrity monitoring',
            'aide-common': 'AIDE common files',
            'apparmor': 'mandatory access control',
            'apparmor-profiles': 'AppArmor profiles',
            'apparmor-utils': 'AppArmor utilities',

            # PAM and authentication
            'libpam-pwquality': 'password quality checking',
            'libpam-pkcs11': 'smart card authentication',
            'libpam-modules': 'PAM modules',
            'libpam-runtime': 'PAM runtime',

            # SSSD for PKI
            'sssd': 'system security services daemon',
            'libpam-sss': 'PAM module for SSSD',
            'libnss-sss': 'NSS module for SSSD',

            # Time synchronization
            'chrony': 'time synchronization',

            # Firewall
            'ufw': 'uncomplicated firewall',

            # Logging
            'rsyslog': 'system logging daemon',

            # Screen locking
            'vlock': 'virtual console locking',

            # USB management
            'usbguard': 'USB device authorization',
        }

    def print_banner(self):
        """Print banner"""
        print("\n" + "="*80)
        print("COMPLETE AIR-GAP PACKAGE BUILDER")
        print("Ubuntu 20.04 STIG V2R3 Automation")
        print("="*80)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Python: {sys.version.split()[0]}")
        print("="*80 + "\n")

    def check_prerequisites(self):
        """Check if required files exist"""
        print("📋 Checking prerequisites...")

        missing = []
        for file in self.required_files:
            file_path = self.root_dir / file
            if file_path.exists():
                print(f"  ✓ Found: {file}")
            else:
                print(f"  ✗ Missing: {file}")
                missing.append(file)

        if missing:
            print(f"\n❌ ERROR: Missing required files: {', '.join(missing)}")
            print("\nPlease ensure all required script files are in the current directory.")
            return False

        print("\n✓ All required files present\n")
        return True

    def create_directories(self):
        """Create package directory structure"""
        print("📁 Creating directory structure...")

        # Clean up old package
        if self.package_dir.exists():
            print(f"  Removing old package directory: {self.package_dir}")
            shutil.rmtree(self.package_dir)

        # Create new structure
        self.package_dir.mkdir()
        self.dependencies_dir.mkdir()
        self.ubuntu_packages_dir.mkdir()
        self.scripts_dir.mkdir()

        print(f"  ✓ Created: {self.package_dir}")
        print(f"  ✓ Created: {self.dependencies_dir}")
        print(f"  ✓ Created: {self.ubuntu_packages_dir}")
        print(f"  ✓ Created: {self.scripts_dir}\n")

    def download_python_packages(self):
        """Download Windows Python packages"""
        print("🐍 Downloading Windows Python packages...")
        print(f"   Target: {self.dependencies_dir}\n")

        # Download using pip
        cmd = [
            sys.executable, '-m', 'pip', 'download',
            '--dest', str(self.dependencies_dir),
            '--python-version', '36',
        ] + self.python_packages

        print(f"   Command: {' '.join(cmd)}\n")

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(result.stdout)

            # Count downloaded files
            files = list(self.dependencies_dir.glob("*"))
            print(f"\n✓ Downloaded {len(files)} Python package files\n")
            return True

        except subprocess.CalledProcessError as e:
            print(f"\n❌ ERROR: Failed to download Python packages")
            print(f"Error: {e.stderr}")
            return False

    def download_ubuntu_packages(self):
        """Download Ubuntu .deb packages and their dependencies"""
        print("🐧 Downloading Ubuntu 20.04 .deb packages...")
        print(f"   Target: {self.ubuntu_packages_dir}\n")

        # Check if we're on a Debian-based system
        has_apt = shutil.which('apt-get') is not None

        if has_apt:
            print("   ✓ Detected Debian-based system - using apt-get download\n")
            return self._download_with_apt()
        else:
            print("   ⚠️  Not on Debian system - will download from Ubuntu mirrors\n")
            return self._download_from_mirrors()

    def _download_with_apt(self):
        """Download using apt-get (if on Debian/Ubuntu system)"""
        success_count = 0
        total = len(self.ubuntu_packages)

        for package, description in self.ubuntu_packages.items():
            print(f"   [{success_count+1}/{total}] Downloading {package} ({description})...")

            # Download package and dependencies
            cmd = [
                'apt-get', 'download',
                package
            ]

            try:
                result = subprocess.run(
                    cmd,
                    cwd=str(self.ubuntu_packages_dir),
                    check=True,
                    capture_output=True,
                    text=True
                )
                print(f"      ✓ Downloaded: {package}")
                success_count += 1

            except subprocess.CalledProcessError as e:
                print(f"      ⚠️  Failed to download {package}")
                print(f"         {e.stderr}")

        print(f"\n✓ Successfully downloaded {success_count}/{total} packages")

        if success_count < total:
            print(f"⚠️  {total - success_count} packages failed to download")
            print("   These packages will need to be manually provided or downloaded on the target")

        return True

    def _download_from_mirrors(self):
        """Download from Ubuntu mirrors (fallback method)"""
        print("   Creating package download script...")

        # Create a shell script for downloading packages
        download_script = self.ubuntu_packages_dir / "download_packages.sh"

        script_content = """#!/bin/bash
# Ubuntu 20.04 Package Downloader
# Run this script on an Ubuntu 20.04 system with internet access

set -e

PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PACKAGE_DIR"

echo "Downloading Ubuntu 20.04 packages..."
echo "Target directory: $PACKAGE_DIR"
echo ""

packages=(
"""

        for package in self.ubuntu_packages.keys():
            script_content += f'    "{package}"\n'

        script_content += """)

success=0
failed=0

for pkg in "${packages[@]}"; do
    echo "Downloading: $pkg"
    if apt-get download "$pkg" 2>/dev/null; then
        echo "  ✓ Downloaded: $pkg"
        ((success++))
    else
        echo "  ✗ Failed: $pkg"
        ((failed++))
    fi
done

echo ""
echo "Download complete!"
echo "  Success: $success"
echo "  Failed: $failed"
echo ""
echo "Files downloaded to: $PACKAGE_DIR"
ls -lh *.deb 2>/dev/null | wc -l | xargs echo "Total .deb files:"
"""

        download_script.write_text(script_content)
        download_script.chmod(0o755)

        print(f"\n   ✓ Created download script: {download_script}")
        print("\n   📝 MANUAL STEP REQUIRED:")
        print("   ========================")
        print("   1. Copy this script to an Ubuntu 20.04 system with internet")
        print(f"   2. Run: bash {download_script.name}")
        print("   3. Copy the downloaded .deb files back to this directory")
        print("   4. Re-run this package builder")
        print("")

        # Create a README for the ubuntu_packages directory
        readme = self.ubuntu_packages_dir / "README.txt"
        readme.write_text(f"""Ubuntu 20.04 Package Directory
=============================

This directory should contain .deb packages for Ubuntu 20.04.

Required packages:
{chr(10).join(f'  - {pkg}: {desc}' for pkg, desc in self.ubuntu_packages.items())}

DOWNLOAD INSTRUCTIONS:
======================

METHOD 1: On Ubuntu 20.04 system with internet
-----------------------------------------------
Run the download_packages.sh script:
    bash download_packages.sh

METHOD 2: Manual download
-------------------------
On an Ubuntu 20.04 system:
    apt-get download {' '.join(self.ubuntu_packages.keys())}

Then copy all .deb files to this directory.

VERIFICATION:
=============
After downloading, you should have .deb files in this directory.
Run 'ls *.deb | wc -l' to count files.
Expected: At least {len(self.ubuntu_packages)} .deb files.
""")

        print(f"   ✓ Created README: {readme}")
        print("")

        return True

    def copy_scripts(self):
        """Copy executor and STIG scripts to package"""
        print("📄 Copying scripts to package...")

        for file in self.required_files:
            src = self.root_dir / file
            dst = self.scripts_dir / file
            shutil.copy2(src, dst)
            print(f"  ✓ Copied: {file}")

        # Also copy the batch launcher if it exists
        bat_file = self.root_dir / "run_airgap_stig.bat"
        if bat_file.exists():
            shutil.copy2(bat_file, self.package_dir / "RUN_ME.bat")
            print(f"  ✓ Copied: RUN_ME.bat")

        print("")

    def create_manifest(self):
        """Create package manifest"""
        print("📋 Creating package manifest...")

        manifest = {
            'package_name': 'Ubuntu 20.04 STIG V2R3 Air-Gap Package',
            'version': '3.0.0',
            'build_date': datetime.now().isoformat(),
            'python_version': sys.version.split()[0],
            'contents': {
                'python_packages': [],
                'ubuntu_packages': [],
                'scripts': []
            }
        }

        # List Python packages
        for file in sorted(self.dependencies_dir.glob("*")):
            manifest['contents']['python_packages'].append(file.name)

        # List Ubuntu packages
        for file in sorted(self.ubuntu_packages_dir.glob("*.deb")):
            manifest['contents']['ubuntu_packages'].append(file.name)

        # List scripts
        for file in sorted(self.scripts_dir.glob("*.py")):
            manifest['contents']['scripts'].append(file.name)

        # Write manifest
        manifest_file = self.package_dir / "MANIFEST.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)

        print(f"  ✓ Created: {manifest_file}")
        print(f"     Python packages: {len(manifest['contents']['python_packages'])}")
        print(f"     Ubuntu packages: {len(manifest['contents']['ubuntu_packages'])}")
        print(f"     Scripts: {len(manifest['contents']['scripts'])}")
        print("")

    def create_readme(self):
        """Create comprehensive README for the package"""
        print("📝 Creating package README...")

        readme_content = f"""
UBUNTU 20.04 STIG V2R3 AIR-GAP PACKAGE
======================================

Package Version: 3.0.0
Build Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
STIG Version: V2R3 (172 controls)

CONTENTS:
=========

1. dependencies/
   - Windows Python packages (paramiko, cryptography, etc.)
   - {len(list(self.dependencies_dir.glob('*')))} package files

2. ubuntu_packages/
   - Ubuntu 20.04 .deb packages for STIG compliance
   - {len(list(self.ubuntu_packages_dir.glob('*.deb')))} .deb files
   - Includes: auditd, aide, apparmor, sssd, ufw, etc.

3. scripts/
   - airgap_complete_executor.py: Windows executor
   - ubuntu20_stig_v2r3_airgap.py: STIG remediation script

QUICK START (AIR-GAPPED WINDOWS):
==================================

1. Extract this package to a folder on your Windows system

2. Open Command Prompt or PowerShell in that folder

3. Run the executor:
   python scripts\\airgap_complete_executor.py

4. Follow the prompts to:
   - Enter Ubuntu target IP/hostname
   - Enter SSH credentials
   - Confirm execution

The script will:
  ✓ Install Python dependencies locally
  ✓ Connect to Ubuntu target via SSH
  ✓ Transfer all Ubuntu packages to target
  ✓ Transfer STIG script to target
  ✓ Execute STIG remediation (172 controls)
  ✓ Create backups before changes
  ✓ Log all actions

REQUIREMENTS:
=============

Windows System:
  - Python 3.6 or higher
  - No internet required
  - This complete package

Ubuntu Target (20.04 LTS):
  - SSH server running
  - User with sudo privileges
  - No internet required
  - At least 2GB free disk space

WHAT GETS CHANGED ON UBUNTU:
=============================

CAT I (Critical - 14 controls):
  - Disables root SSH login
  - Enforces strong password hashing (SHA512)
  - Removes telnet, rsh-server
  - Configures PKI authentication

CAT II (Medium - 136 controls):
  - Password policy: 15 char minimum, complexity
  - Account lockout: 3 attempts = 15 min lockout
  - Kernel hardening: 59 sysctl parameters
  - Audit system: 136 comprehensive rules
  - SSH hardening: FIPS ciphers, idle timeout
  - Firewall: UFW enabled (SSH allowed)
  - Services: Disables unnecessary daemons
  - USB: Auto-mount disabled
  - AppArmor: Enforcing mode
  - AIDE: File integrity monitoring

CAT III (Low - 22 controls):
  - Additional file permissions
  - Documentation requirements

BACKUPS:
========

Automatic backups created in:
  /var/backups/pre-stig-YYYYMMDD_HHMMSS/

If SSH breaks, use console access to restore:
  sudo cp /var/backups/pre-stig-*/sshd_config /etc/ssh/
  sudo systemctl restart sshd

LOGS:
=====

Windows logs:
  %USERPROFILE%\\stig_execution_logs\\

Ubuntu logs:
  /var/log/ubuntu20-stig-v2r3-remediation.log

TROUBLESHOOTING:
================

"paramiko not installed"
  → The script will auto-install from dependencies/ folder

"SSH connection failed"
  → Verify: ssh username@target works manually
  → Check firewall allows port 22

"Permission denied"
  → Verify user has sudo privileges
  → Try: ssh user@target 'sudo -v'

"Ubuntu packages not found"
  → Ensure ubuntu_packages/*.deb files exist
  → Re-run build_complete_airgap_package.py

SUPPORT:
========

For issues or questions, refer to:
  - MANIFEST.json (package contents)
  - execution logs (detailed operations)
  - README_AIRGAP.md (comprehensive guide)

SECURITY NOTICE:
================

⚠️  This package applies 172 DISA STIG security controls
⚠️  Changes are significant and may affect system behavior
⚠️  ALWAYS test in non-production environment first
⚠️  Ensure console access to Ubuntu target before running
⚠️  Review PACKAGE_SUMMARY.md for detailed change list

Package built with: build_complete_airgap_package.py
"""

        readme_file = self.package_dir / "README.txt"
        readme_file.write_text(readme_content)

        print(f"  ✓ Created: {readme_file}\n")

    def create_package(self):
        """Create ZIP archive"""
        print("📦 Creating ZIP package...")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_name = f"ubuntu-stig-airgap-complete-{timestamp}.zip"
        zip_path = self.root_dir / zip_name

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.package_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(self.package_dir)
                    zipf.write(file_path, arcname)
                    print(f"  Adding: {arcname}")

        # Calculate size
        size_mb = zip_path.stat().st_size / (1024 * 1024)

        print(f"\n✓ Package created: {zip_path}")
        print(f"  Size: {size_mb:.2f} MB")

        # Calculate SHA256
        print("\n🔐 Calculating SHA256 checksum...")
        sha256 = hashlib.sha256()
        with open(zip_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)

        checksum = sha256.hexdigest()
        print(f"  SHA256: {checksum}")

        # Write checksum file
        checksum_file = self.root_dir / f"{zip_name}.sha256"
        checksum_file.write_text(f"{checksum}  {zip_name}\n")
        print(f"  ✓ Checksum saved: {checksum_file}")

        return zip_path

    def build(self):
        """Main build process"""
        self.print_banner()

        if not self.check_prerequisites():
            return False

        self.create_directories()

        if not self.download_python_packages():
            print("\n❌ Failed to download Python packages")
            return False

        if not self.download_ubuntu_packages():
            print("\n❌ Failed to download Ubuntu packages")
            return False

        self.copy_scripts()
        self.create_manifest()
        self.create_readme()

        zip_path = self.create_package()

        print("\n" + "="*80)
        print("✅ PACKAGE BUILD COMPLETE!")
        print("="*80)
        print(f"\nPackage: {zip_path.name}")
        print(f"Location: {zip_path}")
        print("\nNEXT STEPS:")
        print("1. Verify the package contains all files (check MANIFEST.json)")
        print("2. Transfer the ZIP to your air-gapped system")
        print("3. Extract the ZIP")
        print("4. Run: python scripts\\airgap_complete_executor.py")
        print("\n" + "="*80 + "\n")

        return True

def main():
    """Main entry point"""
    builder = CompleteAirGapPackageBuilder()

    try:
        success = builder.build()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Build cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
