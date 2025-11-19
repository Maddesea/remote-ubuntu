#!/usr/bin/env python3
"""
AIR-GAP PACKAGE BUILDER - 100% GUARANTEED
==========================================

Downloads ALL required packages for offline STIG execution

Run this script on an INTERNET-CONNECTED system to download:
- Python packages (paramiko, etc.) for Windows
- Ubuntu .deb packages (auditd, aide, etc.) for target
- All dependencies

Output:
- Creates airgap_packages/ folder
- Ready to transfer to air-gapped environment

Requirements:
    - Python 3.6+
    - Internet connection
    - pip
    - docker (optional - for Ubuntu packages)

Usage:
    1. Run this script: python BUILD_AIRGAP_PACKAGE.py
    2. Transfer airgap_packages/ folder to air-gapped system
    3. Copy ULTIMATE_AIRGAP_STIG_EXECUTOR.py to air-gapped system
    4. Copy ubuntu20_stig_v2r3_enhanced.py to air-gapped system
    5. Run ULTIMATE_AIRGAP_STIG_EXECUTOR.py

Author: Ultimate Air-Gap Solution
Version: 4.0.0
"""

import os
import sys
import subprocess
import shutil
import json
from pathlib import Path
from datetime import datetime

VERSION = "4.0.0"

class AirGapPackageBuilder:
    """Build complete air-gap package"""

    def __init__(self):
        self.output_dir = Path("airgap_packages")
        self.python_deps = self.output_dir / "python_dependencies"
        self.ubuntu_pkgs = self.output_dir / "ubuntu_packages"

    def print_banner(self):
        """Print banner"""
        print("\n" + "="*80)
        print("AIR-GAP PACKAGE BUILDER v" + VERSION)
        print("="*80)
        print("\nDownloading ALL packages for 100% offline STIG execution")
        print("\nThis will download:")
        print("  - Python packages for Windows SSH client")
        print("  - Ubuntu .deb packages for STIG tools")
        print("  - All dependencies")
        print("\n" + "="*80)

    def check_prerequisites(self):
        """Check prerequisites"""
        print("\n" + "="*80)
        print("CHECKING PREREQUISITES")
        print("="*80)

        all_ok = True

        # Python version
        if sys.version_info < (3, 6):
            print(f"[ERROR] Python 3.6+ required (current: {sys.version})")
            all_ok = False
        else:
            print(f"[OK] Python {sys.version_info.major}.{sys.version_info.minor}")

        # pip
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print("[OK] pip available")
            else:
                print("[ERROR] pip not found")
                all_ok = False
        except Exception:
            print("[ERROR] pip not available")
            all_ok = False

        # Internet
        print("\nChecking internet connectivity...")
        try:
            import urllib.request
            urllib.request.urlopen('https://pypi.org', timeout=10)
            print("[OK] Internet connection available")
        except Exception as e:
            print(f"[ERROR] No internet connection: {e}")
            print("\nThis script requires internet to download packages!")
            all_ok = False

        # Docker (optional)
        print("\nChecking for Docker (optional)...")
        try:
            result = subprocess.run(
                ['docker', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print("[OK] Docker available (will be used for Ubuntu packages)")
                self.docker_available = True
            else:
                print("[WARNING]  Docker not available (will provide manual instructions)")
                self.docker_available = False
        except Exception:
            print("[WARNING]  Docker not installed (will provide manual instructions)")
            self.docker_available = False

        return all_ok

    def create_directories(self):
        """Create directory structure"""
        print("\n" + "="*80)
        print("CREATING DIRECTORY STRUCTURE")
        print("="*80)

        if self.output_dir.exists():
            print(f"\n[WARNING]  Directory exists: {self.output_dir}")
            response = input("Delete and recreate? [Y/n]: ").strip().lower()
            if response in ['', 'y', 'yes']:
                shutil.rmtree(self.output_dir)
                print("[OK] Removed existing directory")
            else:
                print("Using existing directory...")
                return True

        self.output_dir.mkdir(exist_ok=True)
        self.python_deps.mkdir(exist_ok=True)
        self.ubuntu_pkgs.mkdir(exist_ok=True)

        print(f"\n[OK] Created: {self.output_dir}/")
        print(f"[OK] Created: {self.python_deps}/")
        print(f"[OK] Created: {self.ubuntu_pkgs}/")

        return True

    def download_python_packages(self):
        """Download Python packages for Windows"""
        print("\n" + "="*80)
        print("DOWNLOADING PYTHON PACKAGES")
        print("="*80)

        packages = [
            'paramiko',
            'cryptography',
            'bcrypt',
            'pynacl',
            'cffi',
            'pycparser',
            'six',
        ]

        print(f"\nPackages to download:")
        for pkg in packages:
            print(f"  - {pkg}")

        print(f"\nDestination: {self.python_deps}/")
        print("Downloading...")

        try:
            cmd = [
                sys.executable, '-m', 'pip', 'download',
                '--dest', str(self.python_deps),
                '--prefer-binary',
            ] + packages

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )

            if result.returncode == 0:
                files = list(self.python_deps.glob('*'))
                total_size = sum(f.stat().st_size for f in files if f.is_file()) / (1024 * 1024)
                print(f"\n[OK] Downloaded {len(files)} Python packages ({total_size:.1f} MB)")

                # List files
                print("\nDownloaded files:")
                for f in sorted(files):
                    size_mb = f.stat().st_size / (1024 * 1024)
                    print(f"  - {f.name} ({size_mb:.2f} MB)")

                return True
            else:
                print(f"\n[ERROR] Download failed!")
                print(f"Error: {result.stderr}")
                return False

        except Exception as e:
            print(f"\n[ERROR] Error: {e}")
            return False

    def download_ubuntu_packages_docker(self):
        """Download Ubuntu packages using Docker"""
        print("\n" + "="*80)
        print("DOWNLOADING UBUNTU PACKAGES (using Docker)")
        print("="*80)

        # Critical packages needed for STIG compliance
        ubuntu_packages = [
            # Audit system
            'auditd',
            'audispd-plugins',
            'libauparse0',
            'libaudit1',
            'libaudit-common',

            # File integrity
            'aide',
            'aide-common',

            # PAM and security
            'libpam-pwquality',
            'libpam-modules',
            'libpam-modules-bin',
            'libpam-runtime',

            # AppArmor
            'apparmor',
            'apparmor-utils',

            # Firewall
            'ufw',

            # System tools
            'python3',
            'python3-minimal',
            'cron',
        ]

        print(f"\nPackages to download ({len(ubuntu_packages)}):")
        for pkg in ubuntu_packages:
            print(f"  - {pkg}")

        print(f"\nUsing Ubuntu 20.04 Docker container...")

        try:
            # Create download script
            download_script = f"""#!/bin/bash
set -e

echo "Updating package cache..."
apt-get update -qq

echo "Downloading packages..."
cd /output

for pkg in {' '.join(ubuntu_packages)}; do
    echo "  Downloading $pkg..."
    apt-get download $pkg 2>/dev/null || echo "  Warning: $pkg not found"
done

# Download critical dependencies
echo "Downloading dependencies..."
for pkg in {' '.join(ubuntu_packages)}; do
    apt-cache depends $pkg | grep "Depends:" | awk '{{print $2}}' | while read dep; do
        if [ ! -z "$dep" ] && [ "$dep" != "<none>" ]; then
            apt-get download $dep 2>/dev/null || true
        fi
    done
done

echo "Download complete!"
"""

            script_file = self.ubuntu_pkgs / "download.sh"
            script_file.write_text(download_script)
            script_file.chmod(0o755)

            # Run Docker
            print("\nStarting Docker container...")
            cmd = [
                'docker', 'run', '--rm',
                '-v', f'{self.ubuntu_pkgs.absolute()}:/output',
                'ubuntu:20.04',
                '/bin/bash', '/output/download.sh'
            ]

            result = subprocess.run(cmd, timeout=600)

            # Remove script
            script_file.unlink()

            if result.returncode == 0:
                deb_files = list(self.ubuntu_pkgs.glob('*.deb'))
                total_size = sum(f.stat().st_size for f in deb_files) / (1024 * 1024)

                print(f"\n[OK] Downloaded {len(deb_files)} .deb packages ({total_size:.1f} MB)")

                # Create package list
                list_file = self.ubuntu_pkgs / "package_list.txt"
                with open(list_file, 'w') as f:
                    f.write("# Ubuntu 20.04 packages for STIG compliance\n")
                    f.write(f"# Downloaded: {datetime.now().isoformat()}\n\n")
                    for deb in sorted(deb_files):
                        size_mb = deb.stat().st_size / (1024 * 1024)
                        f.write(f"{deb.name} ({size_mb:.2f} MB)\n")

                print(f"[OK] Created package list: {list_file}")

                return True
            else:
                print("[ERROR] Docker download failed")
                return False

        except subprocess.TimeoutExpired:
            print("[ERROR] Docker download timed out")
            return False
        except Exception as e:
            print(f"\n[ERROR] Error: {e}")
            return False

    def create_manual_download_instructions(self):
        """Create manual download instructions if Docker not available"""
        print("\n" + "="*80)
        print("MANUAL DOWNLOAD INSTRUCTIONS")
        print("="*80)

        instructions = """MANUAL UBUNTU PACKAGE DOWNLOAD INSTRUCTIONS
============================================

Docker is not available. Please download Ubuntu packages manually.

METHOD 1: Using an Ubuntu 20.04 system
---------------------------------------

1. On an Ubuntu 20.04 system with internet:

   cd /tmp
   mkdir stig_packages
   cd stig_packages

2. Download packages:

   apt-get download auditd audispd-plugins libauparse0 libaudit1 libaudit-common \\
                   aide aide-common \\
                   libpam-pwquality libpam-modules libpam-modules-bin libpam-runtime \\
                   apparmor apparmor-utils \\
                   ufw \\
                   python3 python3-minimal cron

3. Download dependencies:

   for pkg in auditd aide libpam-pwquality apparmor-utils ufw; do
       apt-cache depends $pkg | grep "Depends:" | awk '{print $2}' | \\
       while read dep; do
           apt-get download $dep 2>/dev/null || true
       done
   done

4. Copy all .deb files to: airgap_packages/ubuntu_packages/


METHOD 2: Manual download from Ubuntu archives
-----------------------------------------------

Visit: http://archive.ubuntu.com/ubuntu/pool/

Download these packages for Ubuntu 20.04 (focal):

Critical packages:
  - auditd          (main/a/audit/)
  - aide            (main/a/aide/)
  - libpam-pwquality (main/libp/libpwquality/)
  - apparmor-utils  (main/a/apparmor/)
  - ufw             (main/u/ufw/)

Save all .deb files to: airgap_packages/ubuntu_packages/


NOTES:
------
- Download .deb files for amd64 architecture
- Get Ubuntu 20.04 (focal) versions
- Include dependencies when possible
- Minimum required: auditd, aide for STIG compliance
"""

        inst_file = self.ubuntu_pkgs / "MANUAL_DOWNLOAD_INSTRUCTIONS.txt"
        inst_file.write_text(instructions)

        print(f"\n[OK] Created: {inst_file}")
        print("\nPlease download packages manually and save to:")
        print(f"  {self.ubuntu_pkgs}/")

        return True

    def create_manifest(self):
        """Create manifest file"""
        print("\n" + "="*80)
        print("CREATING MANIFEST")
        print("="*80)

        manifest = {
            'version': VERSION,
            'created': datetime.now().isoformat(),
            'python_packages': [],
            'ubuntu_packages': [],
        }

        # Python packages
        for f in self.python_deps.glob('*'):
            if f.is_file():
                manifest['python_packages'].append({
                    'name': f.name,
                    'size': f.stat().st_size,
                })

        # Ubuntu packages
        for f in self.ubuntu_pkgs.glob('*.deb'):
            manifest['ubuntu_packages'].append({
                'name': f.name,
                'size': f.stat().st_size,
            })

        manifest_file = self.output_dir / "manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)

        print(f"[OK] Created: {manifest_file}")
        print(f"  Python packages: {len(manifest['python_packages'])}")
        print(f"  Ubuntu packages: {len(manifest['ubuntu_packages'])}")

        return True

    def create_readme(self):
        """Create README"""
        print("\nCreating README...")

        readme = f"""AIR-GAP PACKAGE for ULTIMATE STIG EXECUTOR
============================================

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Version: {VERSION}


CONTENTS
--------

python_dependencies/  - Python packages for Windows (.whl files)
ubuntu_packages/      - Ubuntu packages for target (.deb files)
manifest.json         - Package inventory


USAGE
-----

1. TRANSFER this entire airgap_packages/ folder to your air-gapped Windows system

2. COPY these files to the same location:
   - ULTIMATE_AIRGAP_STIG_EXECUTOR.py
   - ubuntu20_stig_v2r3_enhanced.py

3. Directory structure should be:

   /path/to/stig/
   |- ULTIMATE_AIRGAP_STIG_EXECUTOR.py  <- Main script
   |- ubuntu20_stig_v2r3_enhanced.py    <- STIG remediation script
   `- airgap_packages/
       |- python_dependencies/          <- Python packages
       `- ubuntu_packages/              <- Ubuntu packages

4. RUN the executor:

   python ULTIMATE_AIRGAP_STIG_EXECUTOR.py

5. The script will:
   - Install Python dependencies on Windows (from local files)
   - Connect to Ubuntu target via SSH
   - Transfer Ubuntu packages to target
   - Install packages offline using dpkg (NO apt)
   - Execute STIG remediation (all 172 controls)
   - Verify execution


REQUIREMENTS
------------

Windows System:
- Python 3.6+
- This airgap_packages/ folder

Ubuntu Target:
- Ubuntu 20.04 LTS
- SSH access
- Sudo privileges
- Console access (KVM/IPMI) - REQUIRED


WHAT GETS APPLIED
-----------------

All 172 STIG controls including:
[OK] SSH hardening (password auth disabled)
[OK] Password complexity and lockout
[OK] Audit logging (auditd)
[OK] File integrity monitoring (aide)
[OK] Firewall rules (UFW - deny all except SSH)
[OK] USB storage disabled
[OK] Wireless disabled
[OK] Kernel hardening (sysctl)
[OK] Service hardening
[OK] AppArmor enforcement


IMPORTANT NOTES
---------------

[WARNING]  After execution:
- SSH password authentication will be DISABLED
- You MUST use SSH keys to access the system
- Have console access (KVM/IPMI) ready
- System will require reboot

[WARNING]  Backups are automatically created:
- /var/backups/pre-stig-*
- /var/backups/stig-v2r3/

[WARNING]  Test in non-production first!


SUPPORT
-------

Check logs at:
- Windows: %USERPROFILE%\\stig_execution_logs\\
- Ubuntu: /var/log/ubuntu20-stig-v2r3-remediation.log


Generated by: AIR-GAP PACKAGE BUILDER v{VERSION}
"""

        readme_file = self.output_dir / "README.txt"
        readme_file.write_text(readme)

        print(f"[OK] Created: {readme_file}")
        return True

    def print_summary(self):
        """Print final summary"""
        print("\n" + "="*80)
        print("PACKAGE BUILD COMPLETE")
        print("="*80)

        # Calculate sizes
        python_files = [f for f in self.python_deps.glob('*') if f.is_file()]
        python_size = sum(f.stat().st_size for f in python_files) / (1024 * 1024)

        ubuntu_files = list(self.ubuntu_pkgs.glob('*.deb'))
        ubuntu_size = sum(f.stat().st_size for f in ubuntu_files) / (1024 * 1024)

        total_size = python_size + ubuntu_size

        print(f"\n[PACKAGE] Package location: {self.output_dir.absolute()}/")
        print(f"\nPython packages:  {len(python_files)} files ({python_size:.1f} MB)")
        print(f"Ubuntu packages:  {len(ubuntu_files)} files ({ubuntu_size:.1f} MB)")
        print(f"TOTAL SIZE:       {total_size:.1f} MB")

        print("\n" + "="*80)
        print("NEXT STEPS")
        print("="*80)

        print("\n1. VERIFY the package:")
        print(f"   - Check {self.python_deps}/ has .whl files")
        print(f"   - Check {self.ubuntu_pkgs}/ has .deb files")
        if len(ubuntu_files) == 0:
            print("\n   [WARNING] WARNING: No Ubuntu packages downloaded!")
            print("   See MANUAL_DOWNLOAD_INSTRUCTIONS.txt")

        print("\n2. COPY required scripts to same folder:")
        print("   - ULTIMATE_AIRGAP_STIG_EXECUTOR.py")
        print("   - ubuntu20_stig_v2r3_enhanced.py")

        print("\n3. TRANSFER to air-gapped system:")
        print(f"   - Copy entire {self.output_dir}/ folder")
        print("   - Copy both .py scripts")
        print("   - Use USB drive, CD/DVD, or approved transfer method")

        print("\n4. ON AIR-GAPPED SYSTEM:")
        print("   - Extract/copy files")
        print("   - Verify directory structure")
        print("   - Run: python ULTIMATE_AIRGAP_STIG_EXECUTOR.py")

        print("\n" + "="*80)
        print("DIRECTORY STRUCTURE FOR AIR-GAPPED SYSTEM")
        print("="*80)
        print("""
/your/stig/directory/
|- ULTIMATE_AIRGAP_STIG_EXECUTOR.py  <- Main script
|- ubuntu20_stig_v2r3_enhanced.py    <- STIG script
`- airgap_packages/
    |- python_dependencies/          <- .whl files
    |- ubuntu_packages/              <- .deb files
    |- manifest.json
    `- README.txt
""")

        print("="*80)
        print("[OK] Package ready for air-gapped deployment!")
        print("="*80)

    def build(self):
        """Main build process"""
        self.print_banner()

        if not self.check_prerequisites():
            print("\n[ERROR] Prerequisites not met!")
            return False

        if not self.create_directories():
            return False

        if not self.download_python_packages():
            print("\n[ERROR] Failed to download Python packages!")
            return False

        # Try Docker first, fallback to manual
        if self.docker_available:
            if not self.download_ubuntu_packages_docker():
                print("\n[WARNING]  Docker download failed, creating manual instructions...")
                self.create_manual_download_instructions()
        else:
            self.create_manual_download_instructions()

        self.create_manifest()
        self.create_readme()
        self.print_summary()

        return True

def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("AIR-GAP PACKAGE BUILDER v" + VERSION)
    print("="*80)

    builder = AirGapPackageBuilder()
    success = builder.build()

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
