#!/usr/bin/env python3
"""
Complete Air-Gap Package Builder
=================================

Builds a complete, self-contained air-gapped STIG execution package.

This script:
1. Downloads all Python dependencies
2. Optionally downloads Ubuntu .deb packages (requires Ubuntu 20.04)
3. Bundles the STIG script
4. Creates a complete ZIP package

Run this on an internet-connected system to create a package for air-gapped deployment.

Usage:
    python3 build_complete_airgap_package.py

Output:
    stig-airgap-complete-YYYYMMDD.zip

Author: Complete Air-Gap Solution
Version: 3.0.0
"""

import os
import sys
import subprocess
import zipfile
import hashlib
import shutil
from pathlib import Path
from datetime import datetime

class CompletePackageBuilder:
    """Build complete air-gapped STIG package"""

    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.package_name = f"stig-airgap-complete-{datetime.now().strftime('%Y%m%d')}"
        self.build_dir = self.script_dir / "build" / self.package_name
        self.dependencies_dir = self.build_dir / "dependencies"
        self.ubuntu_packages_dir = self.build_dir / "ubuntu_packages"

        # Required files
        self.executor_script = "airgap_stig_executor_complete.py"
        self.stig_script = "ubuntu20_stig_v2r3_enhanced.py"
        self.download_ubuntu_script = "download_ubuntu_packages.py"

        # Stats
        self.stats = {
            'python_packages': 0,
            'ubuntu_packages': 0,
            'total_size': 0,
            'errors': []
        }

    def clean_build_dir(self):
        """Clean and create build directory"""
        print("\n" + "="*80)
        print("PREPARING BUILD DIRECTORY")
        print("="*80)

        if self.build_dir.exists():
            print(f"\n🗑️  Removing existing build directory...")
            shutil.rmtree(self.build_dir)

        self.build_dir.mkdir(parents=True)
        self.dependencies_dir.mkdir()
        print(f"✓ Created build directory: {self.build_dir}")

    def check_required_files(self):
        """Check if required files exist"""
        print("\n" + "="*80)
        print("CHECKING REQUIRED FILES")
        print("="*80)

        required = [
            (self.executor_script, "Air-gap executor script"),
            (self.stig_script, "STIG remediation script"),
        ]

        all_present = True

        for filename, description in required:
            filepath = self.script_dir / filename
            if filepath.exists():
                size_kb = filepath.stat().st_size / 1024
                print(f"  ✓ {description}: {filename} ({size_kb:.1f} KB)")
            else:
                print(f"  ✗ {description}: {filename} NOT FOUND")
                all_present = False
                self.stats['errors'].append(f"Missing required file: {filename}")

        if not all_present:
            print("\n❌ Required files are missing!")
            return False

        print("\n✓ All required files present")
        return True

    def download_python_dependencies(self):
        """Download Python dependencies"""
        print("\n" + "="*80)
        print("DOWNLOADING PYTHON DEPENDENCIES")
        print("="*80)

        packages = [
            'paramiko',
            'cryptography',
            'bcrypt',
            'PyNaCl',
            'cffi',
            'pycparser',
            'six'
        ]

        print(f"\n📦 Downloading {len(packages)} Python packages...")
        print("   (This includes all transitive dependencies)")

        try:
            # Download all packages
            cmd = [
                sys.executable, '-m', 'pip', 'download',
                '-d', str(self.dependencies_dir)
            ] + packages

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                # Count downloaded files
                wheel_files = list(self.dependencies_dir.glob("*.whl"))
                tar_files = list(self.dependencies_dir.glob("*.tar.gz"))
                all_files = wheel_files + tar_files

                self.stats['python_packages'] = len(all_files)

                print(f"✓ Downloaded {len(all_files)} package files")
                print(f"  - {len(wheel_files)} wheel files (.whl)")
                print(f"  - {len(tar_files)} source files (.tar.gz)")

                return True
            else:
                print(f"❌ Download failed:")
                print(result.stderr)
                self.stats['errors'].append("Python dependency download failed")
                return False

        except subprocess.TimeoutExpired:
            print("❌ Download timed out")
            self.stats['errors'].append("Python dependency download timed out")
            return False
        except Exception as e:
            print(f"❌ Error downloading dependencies: {e}")
            self.stats['errors'].append(f"Python dependency error: {e}")
            return False

    def download_ubuntu_packages(self):
        """Download Ubuntu packages if on Ubuntu 20.04"""
        print("\n" + "="*80)
        print("UBUNTU PACKAGES")
        print("="*80)

        # Check if on Linux
        if not sys.platform.startswith('linux'):
            print("\n⚠️  Not running on Linux - skipping Ubuntu package download")
            print("   Ubuntu packages must be downloaded separately on Ubuntu 20.04")
            print(f"   Use: python3 {self.download_ubuntu_script}")
            return True

        # Check if Ubuntu 20.04
        try:
            with open('/etc/os-release', 'r') as f:
                os_info = f.read()

            if 'Ubuntu 20.04' not in os_info:
                print("\n⚠️  Not running on Ubuntu 20.04 - skipping package download")
                print("   Ubuntu packages must be downloaded on Ubuntu 20.04")
                print(f"   Use: python3 {self.download_ubuntu_script}")
                return True

        except FileNotFoundError:
            print("\n⚠️  Cannot determine OS - skipping Ubuntu package download")
            return True

        # We're on Ubuntu 20.04 - download packages
        print("\n✓ Running on Ubuntu 20.04")
        print("📦 Downloading Ubuntu .deb packages...")

        response = input("\nDownload Ubuntu packages now? [Y/n]: ").strip().lower()
        if response in ['n', 'no']:
            print("⚠️  Skipping Ubuntu package download")
            print(f"   You can download them later with: python3 {self.download_ubuntu_script}")
            return True

        # Use the dedicated download script
        download_script = self.script_dir / self.download_ubuntu_script

        if not download_script.exists():
            print(f"❌ Download script not found: {download_script}")
            return True  # Not fatal

        try:
            # Run download script
            result = subprocess.run(
                [sys.executable, str(download_script)],
                timeout=600
            )

            if result.returncode == 0:
                # Check if packages were downloaded
                source_pkg_dir = self.script_dir / "ubuntu_packages"

                if source_pkg_dir.exists():
                    # Copy to build directory
                    print(f"\n📦 Copying packages to build directory...")
                    shutil.copytree(source_pkg_dir, self.ubuntu_packages_dir, dirs_exist_ok=True)

                    deb_files = list(self.ubuntu_packages_dir.glob("*.deb"))
                    self.stats['ubuntu_packages'] = len(deb_files)

                    print(f"✓ Copied {len(deb_files)} .deb files")
                    return True
                else:
                    print("⚠️  No packages directory created")
                    return True

            else:
                print("⚠️  Package download had issues - continuing without Ubuntu packages")
                return True

        except subprocess.TimeoutExpired:
            print("⚠️  Package download timed out - continuing without Ubuntu packages")
            return True
        except Exception as e:
            print(f"⚠️  Error downloading Ubuntu packages: {e}")
            return True

    def copy_scripts(self):
        """Copy required scripts to build directory"""
        print("\n" + "="*80)
        print("COPYING SCRIPTS")
        print("="*80)

        scripts = [
            (self.executor_script, "Air-gap executor"),
            (self.stig_script, "STIG remediation script"),
            (self.download_ubuntu_script, "Ubuntu package downloader (reference)"),
        ]

        for filename, description in scripts:
            source = self.script_dir / filename
            if not source.exists():
                if filename == self.download_ubuntu_script:
                    # Optional file
                    continue
                print(f"  ✗ {description}: {filename} NOT FOUND")
                continue

            dest = self.build_dir / filename
            shutil.copy2(source, dest)

            size_kb = dest.stat().st_size / 1024
            print(f"  ✓ {description}: {filename} ({size_kb:.1f} KB)")

        return True

    def create_readme(self):
        """Create comprehensive README"""
        readme_content = f'''# Complete Air-Gapped STIG Package
## Ubuntu 20.04 STIG V2R3 - 100% Offline Operation

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Version**: 3.0.0

This package contains everything needed to execute Ubuntu 20.04 STIG V2R3
remediation in a completely air-gapped/offline environment.

---

## 📦 Package Contents

### Core Scripts
- **airgap_stig_executor_complete.py** - Main executor (run this on Windows)
- **ubuntu20_stig_v2r3_enhanced.py** - STIG remediation script (transferred to Ubuntu)

### Python Dependencies
- **dependencies/** - {self.stats['python_packages']} Python packages (.whl files)
  - paramiko (SSH client)
  - cryptography, bcrypt, PyNaCl (crypto libraries)
  - cffi, pycparser, six (supporting libraries)

### Ubuntu Packages
- **ubuntu_packages/** - {self.stats['ubuntu_packages']} Ubuntu .deb files
  - auditd, aide, apparmor, libpam-pwquality, ufw, etc.
  - All dependencies included

### Reference Scripts
- **download_ubuntu_packages.py** - Re-download Ubuntu packages (if needed)

---

## 🚀 Quick Start

### Requirements
**On Windows (where you run the executor):**
- Python 3.6 or higher
- Network access to target Ubuntu system (via SSH)
- This package extracted

**On Ubuntu Target (air-gapped system):**
- Ubuntu 20.04 LTS
- SSH server running
- User account with sudo privileges

### Step 1: Extract Package
```cmd
# Extract this ZIP file to a directory
# Example: C:\\stig-airgap\\
```

### Step 2: Run Executor
```cmd
# Open Command Prompt or PowerShell
cd C:\\stig-airgap\\{self.package_name}
python airgap_stig_executor_complete.py
```

### Step 3: Follow Prompts
The executor will ask for:
- Target Ubuntu IP/hostname
- SSH credentials
- Sudo password
- Final confirmation

### Step 4: Wait for Completion
- Executor will transfer all files to Ubuntu
- Install packages offline
- Execute all 172 STIG controls
- This takes 5-15 minutes

### Step 5: Reboot Target
```bash
sudo reboot
```

---

## ⚠️ IMPORTANT WARNINGS

### Before Execution
1. **Create Backup/Snapshot** of target system
2. **Ensure Console Access** (KVM/IPMI/Physical)
3. **Test in Non-Production First**
4. **Have SSH Keys Ready** (password auth may be disabled)

### What Gets Changed
- **Password Policies**: 15 char minimum, complexity required
- **SSH Configuration**: Hardened, keys recommended
- **Firewall**: UFW enabled, restrictive rules
- **Services**: Many unnecessary services disabled
- **Audit Logging**: Comprehensive audit rules enabled
- **Kernel Parameters**: 59 sysctl settings modified
- **USB/Wireless**: May be disabled (configurable)

### After Execution
- System will be significantly hardened
- Some services may be disabled
- Password requirements will be strict
- SSH may require key-based authentication
- Firewall will be active

---

## 📋 Detailed Steps

### What the Executor Does

1. **Verify Local Files**
   - Checks all required files are present
   - Validates STIG script exists
   - Confirms packages are available

2. **Connect to Target**
   - Establishes SSH connection
   - Verifies sudo access
   - Checks Ubuntu version

3. **Transfer Files** (All Offline)
   - Transfers STIG script via SFTP
   - Transfers all Ubuntu .deb packages
   - Creates remote working directory

4. **Install Packages** (Completely Offline)
   - Installs .deb files using dpkg
   - Fixes dependencies with apt (offline)
   - Verifies key packages installed

5. **Execute STIG Remediation**
   - Runs Python STIG script
   - Applies all 172 controls
   - Creates backups automatically

6. **Verify and Report**
   - Checks critical services
   - Validates SSH configuration
   - Provides final summary

---

## 🔍 Troubleshooting

### "STIG script not found"
**Solution**: Ensure `ubuntu20_stig_v2r3_enhanced.py` is in the same directory

### "paramiko not found"
**Solution**: The executor will auto-install from dependencies/ folder

### "SSH connection failed"
**Solution**:
- Verify target IP/hostname is correct
- Check firewall allows SSH (port 22)
- Verify credentials are correct
- Ensure SSH server is running on target

### "Sudo password failed"
**Solution**:
- Verify user has sudo privileges
- Check password is correct
- Try: `ssh user@target 'sudo -v'`

### "Package installation failed"
**Solution**:
- Some packages may have been pre-installed
- Check /tmp/dpkg-install.log on target
- STIG execution will continue anyway

### "SSH broken after execution"
**Solution**:
- Use console access (KVM/physical)
- Restore from backup:
  ```bash
  sudo cp /var/backups/pre-stig-*/sshd_config /etc/ssh/
  sudo systemctl restart sshd
  ```

---

## 📁 Directory Structure

```
{self.package_name}/
├── README.md                              ← This file
├── airgap_stig_executor_complete.py       ← Main script (run this)
├── ubuntu20_stig_v2r3_enhanced.py         ← STIG script
├── download_ubuntu_packages.py            ← Reference (optional)
├── dependencies/                          ← Python packages
│   ├── paramiko-*.whl
│   ├── cryptography-*.whl
│   ├── bcrypt-*.whl
│   ├── PyNaCl-*.whl
│   ├── cffi-*.whl
│   ├── pycparser-*.whl
│   └── six-*.whl
└── ubuntu_packages/                       ← Ubuntu packages (if included)
    ├── auditd_*.deb
    ├── aide_*.deb
    ├── apparmor*.deb
    ├── libpam-*.deb
    └── ... (all dependencies)
```

---

## 🔒 Security Notes

### Air-Gap Compliance
- **NO internet required** on Windows or Ubuntu
- All packages pre-downloaded
- Completely offline operation
- Perfect for classified/isolated environments

### STIG Controls Applied
- **CAT I (High)**: 14 controls
- **CAT II (Medium)**: 136 controls
- **CAT III (Low)**: 22 controls
- **Total**: 172 controls

### Backup Locations
Automatic backups created on target:
- `/var/backups/pre-stig-airgap-YYYYMMDD_HHMMSS/`
- Individual files: `*.stig-v2r3-backup-*`

---

## 📞 Support

### Logs
**Windows Executor Log**:
- `%USERPROFILE%\\stig_execution_logs\\stig_execution_YYYYMMDD_HHMMSS.log`

**Ubuntu STIG Log**:
- `/var/log/ubuntu20-stig-v2r3-remediation.log`

### Verification
After execution and reboot:
```bash
# Check SSH
ssh user@target

# Check services
sudo systemctl status sshd auditd ufw

# Check firewall
sudo ufw status

# Check logs
sudo tail -100 /var/log/ubuntu20-stig-v2r3-remediation.log
```

---

## 📄 License
MIT License - See individual script headers for details

## 🏷️ Version
**Package Version**: 3.0.0
**STIG Version**: V2R3 (Release 3, July 2025)
**Target OS**: Ubuntu 20.04 LTS
**Build Date**: {datetime.now().strftime('%Y-%m-%d')}

---

## ✅ Checklist

### Before Execution
- [ ] Backup/snapshot target system
- [ ] Console access available (KVM/IPMI/physical)
- [ ] SSH access verified manually
- [ ] Sudo privileges confirmed
- [ ] All required files present
- [ ] Tested in non-production first

### After Execution
- [ ] Reboot target system
- [ ] Verify SSH access works
- [ ] Check critical services running
- [ ] Validate firewall is active
- [ ] Review audit logs
- [ ] Test critical applications
- [ ] Run SCAP compliance scan (optional)

---

**Generated by**: build_complete_airgap_package.py
**For**: Complete Air-Gapped STIG Execution
**Ready to Deploy**: YES ✓
'''

        readme_path = self.build_dir / "README.md"
        with open(readme_path, 'w') as f:
            f.write(readme_content)

        print(f"\n✓ Created comprehensive README.md")
        return True

    def create_checksums(self):
        """Create SHA256 checksums file"""
        print("\n" + "="*80)
        print("GENERATING CHECKSUMS")
        print("="*80)

        checksums = {}

        # Calculate checksum for each file
        for file_path in self.build_dir.rglob('*'):
            if file_path.is_file() and file_path.name != 'CHECKSUMS.txt':
                rel_path = file_path.relative_to(self.build_dir)

                sha256_hash = hashlib.sha256()
                with open(file_path, 'rb') as f:
                    for byte_block in iter(lambda: f.read(4096), b""):
                        sha256_hash.update(byte_block)

                checksums[str(rel_path)] = sha256_hash.hexdigest()

        # Write checksums file
        checksums_file = self.build_dir / "CHECKSUMS.txt"
        with open(checksums_file, 'w') as f:
            f.write(f"# SHA256 Checksums\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            for filepath, checksum in sorted(checksums.items()):
                f.write(f"{checksum}  {filepath}\n")

        print(f"✓ Created checksums for {len(checksums)} files")
        return True

    def create_zip_package(self):
        """Create ZIP package"""
        print("\n" + "="*80)
        print("CREATING ZIP PACKAGE")
        print("="*80)

        zip_path = self.script_dir / f"{self.package_name}.zip"

        if zip_path.exists():
            print(f"\n⚠️  Removing existing ZIP: {zip_path.name}")
            zip_path.unlink()

        print(f"\n📦 Creating ZIP package...")
        print("   This may take a minute...")

        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add all files from build directory
                for file_path in self.build_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(self.build_dir.parent)
                        zipf.write(file_path, arcname)

            # Calculate final size
            zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
            self.stats['total_size'] = zip_size_mb

            print(f"✓ Created ZIP package: {zip_path.name}")
            print(f"✓ Package size: {zip_size_mb:.1f} MB")

            return zip_path

        except Exception as e:
            print(f"❌ Failed to create ZIP: {e}")
            self.stats['errors'].append(f"ZIP creation failed: {e}")
            return None

    def print_summary(self, zip_path):
        """Print final summary"""
        print("\n" + "="*80)
        print("PACKAGE BUILD COMPLETE")
        print("="*80)

        print(f"\n✓ Package: {self.package_name}.zip")
        print(f"✓ Size: {self.stats['total_size']:.1f} MB")
        print(f"✓ Python packages: {self.stats['python_packages']}")
        print(f"✓ Ubuntu packages: {self.stats['ubuntu_packages']}")

        if self.stats['errors']:
            print(f"\n⚠️  Warnings/Errors:")
            for error in self.stats['errors']:
                print(f"  - {error}")

        print("\n" + "="*80)
        print("DEPLOYMENT INSTRUCTIONS")
        print("="*80)

        print(f"\n1. 📤 TRANSFER TO AIR-GAPPED WINDOWS SYSTEM:")
        print(f"   - Copy {self.package_name}.zip to target Windows system")
        print(f"   - Use approved transfer method (USB, DVD, etc.)")

        print(f"\n2. 📂 EXTRACT ON WINDOWS SYSTEM:")
        print(f"   - Extract ZIP to a directory (e.g., C:\\stig-airgap\\)")

        print(f"\n3. 🚀 RUN EXECUTOR:")
        print(f"   - Open Command Prompt")
        print(f"   - cd C:\\stig-airgap\\{self.package_name}")
        print(f"   - python airgap_stig_executor_complete.py")

        print(f"\n4. ✅ FOLLOW PROMPTS:")
        print(f"   - Enter target Ubuntu IP and credentials")
        print(f"   - Confirm execution")
        print(f"   - Wait for completion (5-15 minutes)")

        print(f"\n5. 🔄 REBOOT TARGET:")
        print(f"   - Reboot Ubuntu system after completion")
        print(f"   - Verify SSH access and services")

        print("\n" + "="*80)
        print("WHAT'S INCLUDED")
        print("="*80)

        print("\n✓ Executor script (Windows)")
        print("✓ STIG remediation script (Ubuntu)")
        print(f"✓ {self.stats['python_packages']} Python packages (offline)")

        if self.stats['ubuntu_packages'] > 0:
            print(f"✓ {self.stats['ubuntu_packages']} Ubuntu .deb files (offline)")
        else:
            print("⚠️  No Ubuntu packages (may need to download separately)")

        print("✓ Comprehensive README.md")
        print("✓ SHA256 checksums")

        print("\n" + "="*80)
        print(f"📦 Package ready: {zip_path}")
        print("="*80 + "\n")

    def build(self):
        """Main build process"""
        print("\n" + "="*80)
        print("COMPLETE AIR-GAP PACKAGE BUILDER")
        print("="*80)

        # Clean build directory
        self.clean_build_dir()

        # Check required files
        if not self.check_required_files():
            print("\n❌ Build failed - required files missing")
            return False

        # Download Python dependencies
        if not self.download_python_dependencies():
            print("\n❌ Build failed - Python dependency download failed")
            return False

        # Download Ubuntu packages (optional)
        self.download_ubuntu_packages()

        # Copy scripts
        if not self.copy_scripts():
            print("\n❌ Build failed - script copy failed")
            return False

        # Create README
        self.create_readme()

        # Create checksums
        self.create_checksums()

        # Create ZIP package
        zip_path = self.create_zip_package()
        if not zip_path:
            print("\n❌ Build failed - ZIP creation failed")
            return False

        # Print summary
        self.print_summary(zip_path)

        return True


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("COMPLETE AIR-GAP PACKAGE BUILDER")
    print("Ubuntu 20.04 STIG V2R3 - Version 3.0.0")
    print("="*80)

    print("\nThis script will create a complete air-gapped STIG package including:")
    print("  - Python dependencies (paramiko, cryptography, etc.)")
    print("  - Ubuntu .deb packages (auditd, aide, etc.) - if on Ubuntu 20.04")
    print("  - STIG executor and remediation scripts")
    print("  - Comprehensive documentation")

    print("\n📋 Requirements:")
    print("  - Internet connection (for downloading packages)")
    print("  - Python 3.6 or higher")
    print("  - pip (Python package installer)")

    if sys.platform.startswith('linux'):
        print("  - Ubuntu 20.04 (optional, for Ubuntu package download)")

    response = input("\nProceed with package build? [Y/n]: ").strip().lower()
    if response in ['n', 'no']:
        print("\n❌ Build cancelled")
        sys.exit(0)

    # Build package
    builder = CompletePackageBuilder()
    success = builder.build()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
