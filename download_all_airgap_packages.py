#!/usr/bin/env python3
"""
Complete Air-Gap Package Downloader
====================================

Downloads ALL required packages for 100% offline STIG execution:
- Python packages for Windows SSH client
- Ubuntu .deb packages for STIG tools (auditd, aide, etc.)
- All dependencies

Run this on an INTERNET-CONNECTED system.
Transfer the complete package to your air-gapped environment.

Requirements:
    - Python 3.6+
    - Internet connection
    - pip
    - docker (optional but recommended for downloading .deb packages)

Author: Complete Air-Gap Solution
Version: 3.0.0
"""

import os
import sys
import subprocess
import shutil
import json
from pathlib import Path
from datetime import datetime

class CompleteAirGapDownloader:
    """Download ALL packages needed for air-gapped STIG execution"""

    def __init__(self):
        self.output_dir = Path("airgap_complete_package")
        self.python_deps_dir = self.output_dir / "python_dependencies"
        self.ubuntu_debs_dir = self.output_dir / "ubuntu_packages"
        self.scripts_dir = self.output_dir / "scripts"

    def print_banner(self):
        """Print banner"""
        print("\n" + "="*80)
        print("COMPLETE AIR-GAP PACKAGE DOWNLOADER")
        print("Downloads ALL packages for 100% offline STIG execution")
        print("="*80)
        print()

    def check_prerequisites(self):
        """Check prerequisites"""
        print("Checking prerequisites...")

        # Check Python version
        if sys.version_info < (3, 6):
            print(f"❌ Python 3.6+ required (current: {sys.version})")
            return False
        print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}")

        # Check pip
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', '--version'],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✓ pip available")
            else:
                print("❌ pip not found")
                return False
        except Exception:
            print("❌ pip not available")
            return False

        # Check internet
        print("Checking internet connectivity...")
        try:
            import urllib.request
            urllib.request.urlopen('https://pypi.org', timeout=5)
            print("✓ Internet connection available")
        except Exception as e:
            print(f"❌ No internet: {e}")
            return False

        return True

    def create_directories(self):
        """Create directory structure"""
        print("\n" + "="*80)
        print("CREATING DIRECTORY STRUCTURE")
        print("="*80)

        # Remove existing if present
        if self.output_dir.exists():
            print(f"\n⚠️  Directory exists: {self.output_dir}")
            response = input("Delete and recreate? [y/N]: ").strip().lower()
            if response == 'y':
                shutil.rmtree(self.output_dir)
                print("✓ Removed existing directory")
            else:
                print("❌ Cannot proceed")
                return False

        # Create structure
        self.output_dir.mkdir()
        self.python_deps_dir.mkdir()
        self.ubuntu_debs_dir.mkdir()
        self.scripts_dir.mkdir()

        print(f"\n✓ Created: {self.output_dir}/")
        print(f"✓ Created: {self.python_deps_dir}/")
        print(f"✓ Created: {self.ubuntu_debs_dir}/")
        print(f"✓ Created: {self.scripts_dir}/")

        return True

    def download_python_packages(self):
        """Download Python packages for Windows SSH client"""
        print("\n" + "="*80)
        print("DOWNLOADING PYTHON PACKAGES (for Windows)")
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

        print(f"\nPackages: {', '.join(packages)}")
        print("Downloading...")

        try:
            cmd = [
                sys.executable, '-m', 'pip', 'download',
                '--dest', str(self.python_deps_dir),
                '--prefer-binary',
            ] + packages

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if result.returncode == 0:
                files = list(self.python_deps_dir.glob('*'))
                total_size = sum(f.stat().st_size for f in files) / (1024 * 1024)
                print(f"\n✓ Downloaded {len(files)} Python packages ({total_size:.1f} MB)")
                return True
            else:
                print(f"\n❌ Download failed:\n{result.stderr}")
                return False

        except Exception as e:
            print(f"\n❌ Error: {e}")
            return False

    def download_ubuntu_packages_docker(self):
        """Download Ubuntu packages using Docker"""
        print("\n" + "="*80)
        print("DOWNLOADING UBUNTU PACKAGES (using Docker)")
        print("="*80)

        print("\nChecking for Docker...")
        try:
            result = subprocess.run(['docker', '--version'],
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ Docker not available")
                return self.download_ubuntu_packages_urls()
        except FileNotFoundError:
            print("❌ Docker not installed")
            return self.download_ubuntu_packages_urls()

        print("✓ Docker available")

        # Ubuntu packages needed for STIG compliance
        ubuntu_packages = [
            'auditd',           # Audit daemon (required for audit logging)
            'aide',             # File integrity monitoring
            'aide-common',      # AIDE common files
            'libpam-pwquality', # Password quality checking
            'libpam-modules',   # PAM modules
            'apparmor-utils',   # AppArmor utilities
            'ufw',              # Firewall
            'libauparse0',      # Audit parsing library
            'audispd-plugins',  # Audit dispatcher plugins
            'python3',          # Python3 runtime
            'python3-minimal',  # Minimal Python3
        ]

        print(f"\nPackages to download: {len(ubuntu_packages)}")
        for pkg in ubuntu_packages:
            print(f"  - {pkg}")

        print("\nDownloading using Ubuntu 20.04 Docker container...")

        try:
            # Create download script for Docker
            download_script = f"""#!/bin/bash
set -e
apt-get update -qq
cd /output
for pkg in {' '.join(ubuntu_packages)}; do
    echo "Downloading $pkg..."
    apt-get download $pkg 2>/dev/null || echo "Warning: $pkg not found"
    apt-cache depends $pkg | grep Depends | awk '{{print $2}}' | while read dep; do
        apt-get download $dep 2>/dev/null || true
    done
done
echo "Download complete!"
"""

            script_file = self.ubuntu_debs_dir / "download.sh"
            script_file.write_text(download_script)
            script_file.chmod(0o755)

            # Run Docker to download packages
            cmd = [
                'docker', 'run', '--rm',
                '-v', f'{self.ubuntu_debs_dir.absolute()}:/output',
                'ubuntu:20.04',
                '/bin/bash', '/output/download.sh'
            ]

            print("\nRunning Docker container...")
            result = subprocess.run(cmd, timeout=600)

            # Remove download script
            script_file.unlink()

            if result.returncode == 0:
                deb_files = list(self.ubuntu_debs_dir.glob('*.deb'))
                total_size = sum(f.stat().st_size for f in deb_files) / (1024 * 1024)
                print(f"\n✓ Downloaded {len(deb_files)} .deb packages ({total_size:.1f} MB)")

                # Create package list
                package_list = self.ubuntu_debs_dir / "package_list.txt"
                with open(package_list, 'w') as f:
                    f.write("# Ubuntu packages for STIG compliance\n")
                    f.write(f"# Downloaded: {datetime.now().isoformat()}\n\n")
                    for deb in sorted(deb_files):
                        f.write(f"{deb.name}\n")

                return True
            else:
                print("❌ Docker download failed")
                return False

        except Exception as e:
            print(f"\n❌ Error: {e}")
            return False

    def download_ubuntu_packages_urls(self):
        """Download Ubuntu packages from URLs (fallback method)"""
        print("\n" + "="*80)
        print("DOWNLOADING UBUNTU PACKAGES (from URLs)")
        print("="*80)
        print("\n⚠️  Manual download required")

        # Package URLs for Ubuntu 20.04
        package_info = {
            'auditd': 'http://archive.ubuntu.com/ubuntu/pool/main/a/audit/',
            'aide': 'http://archive.ubuntu.com/ubuntu/pool/main/a/aide/',
            'aide-common': 'http://archive.ubuntu.com/ubuntu/pool/main/a/aide/',
            'libpam-pwquality': 'http://archive.ubuntu.com/ubuntu/pool/main/libp/libpwquality/',
            'apparmor-utils': 'http://archive.ubuntu.com/ubuntu/pool/main/a/apparmor/',
        }

        instructions_file = self.ubuntu_debs_dir / "DOWNLOAD_INSTRUCTIONS.txt"
        with open(instructions_file, 'w') as f:
            f.write("Manual Ubuntu Package Download Instructions\n")
            f.write("=" * 80 + "\n\n")
            f.write("Docker not available. Please download packages manually:\n\n")

            for pkg, url in package_info.items():
                f.write(f"{pkg}:\n")
                f.write(f"  1. Visit: {url}\n")
                f.write(f"  2. Download the latest .deb for Ubuntu 20.04 (focal)\n")
                f.write(f"  3. Save to: {self.ubuntu_debs_dir}/\n\n")

            f.write("\nAlternative: Use an Ubuntu 20.04 system:\n")
            f.write("  apt-get download auditd aide aide-common libpam-pwquality apparmor-utils\n")
            f.write(f"  Copy all .deb files to: {self.ubuntu_debs_dir}/\n")

        print(f"\n✓ Created instructions: {instructions_file}")
        print(f"\nPlease download packages manually and place in:")
        print(f"  {self.ubuntu_debs_dir}/")

        return True

    def create_offline_installer_script(self):
        """Create Python script to install everything offline on target"""
        print("\n" + "="*80)
        print("CREATING OFFLINE INSTALLER SCRIPT")
        print("="*80)

        installer_script = '''#!/usr/bin/env python3
"""
Offline Package Installer for Ubuntu Target
Installs all packages without internet access
"""

import os
import sys
import subprocess
from pathlib import Path

def install_deb_packages():
    """Install .deb packages offline"""
    print("\\n" + "="*60)
    print("INSTALLING UBUNTU PACKAGES (OFFLINE)")
    print("="*60)

    deb_dir = Path("/tmp/stig_packages/ubuntu_packages")
    if not deb_dir.exists():
        print(f"❌ Package directory not found: {deb_dir}")
        return False

    deb_files = list(deb_dir.glob("*.deb"))
    if not deb_files:
        print(f"❌ No .deb files found in {deb_dir}")
        return False

    print(f"\\nFound {len(deb_files)} .deb packages")
    print("Installing...")

    try:
        # Install all packages with dpkg
        cmd = ['dpkg', '-i'] + [str(f) for f in deb_files]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            # Try to fix dependencies
            print("\\nFixing dependencies...")
            subprocess.run(['apt-get', 'install', '-f', '-y'],
                         env={'DEBIAN_FRONTEND': 'noninteractive'})

        print("✓ Ubuntu packages installed")
        return True

    except Exception as e:
        print(f"❌ Installation error: {e}")
        return False

def verify_packages():
    """Verify required packages are installed"""
    print("\\n" + "="*60)
    print("VERIFYING PACKAGE INSTALLATION")
    print("="*60)

    required_commands = {
        'auditd': '/sbin/auditd',
        'aide': '/usr/bin/aide',
        'auditctl': '/sbin/auditctl',
    }

    all_ok = True
    for name, path in required_commands.items():
        if Path(path).exists():
            print(f"  ✓ {name}")
        else:
            print(f"  ✗ {name} - NOT FOUND")
            all_ok = False

    return all_ok

def main():
    print("\\n" + "="*60)
    print("OFFLINE PACKAGE INSTALLER")
    print("="*60)

    if os.geteuid() != 0:
        print("\\n❌ This script must be run as root (via sudo)")
        sys.exit(1)

    if not install_deb_packages():
        print("\\n❌ Package installation failed")
        sys.exit(1)

    if verify_packages():
        print("\\n✓ All packages installed successfully!")
        return 0
    else:
        print("\\n⚠️  Some packages may not have installed correctly")
        return 1

if __name__ == '__main__':
    sys.exit(main())
'''

        installer_file = self.scripts_dir / "offline_package_installer.py"
        installer_file.write_text(installer_script)
        installer_file.chmod(0o755)

        print(f"✓ Created: {installer_file}")
        return True

    def create_manifest(self):
        """Create manifest of all downloaded files"""
        print("\n" + "="*80)
        print("CREATING PACKAGE MANIFEST")
        print("="*80)

        manifest = {
            'created': datetime.now().isoformat(),
            'python_packages': [],
            'ubuntu_packages': [],
        }

        # Python packages
        for f in self.python_deps_dir.glob('*'):
            if f.is_file():
                manifest['python_packages'].append({
                    'name': f.name,
                    'size': f.stat().st_size,
                })

        # Ubuntu packages
        for f in self.ubuntu_debs_dir.glob('*.deb'):
            manifest['ubuntu_packages'].append({
                'name': f.name,
                'size': f.stat().st_size,
            })

        manifest_file = self.output_dir / "manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)

        print(f"\n✓ Created manifest: {manifest_file}")
        print(f"  Python packages: {len(manifest['python_packages'])}")
        print(f"  Ubuntu packages: {len(manifest['ubuntu_packages'])}")

        return True

    def create_readme(self):
        """Create README for the package"""
        print("\nCreating README...")

        readme_content = f"""# Complete Air-Gap Package for STIG Execution
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Package Contents

### Python Dependencies (for Windows)
- Location: python_dependencies/
- Contains: paramiko, cryptography, and all dependencies
- Purpose: Allows Windows system to connect via SSH

### Ubuntu Packages (for target Ubuntu system)
- Location: ubuntu_packages/
- Contains: .deb files for auditd, aide, and STIG tools
- Purpose: Installed on target Ubuntu system (offline)

### Scripts
- Location: scripts/
- offline_package_installer.py: Installs packages on target

## Usage

1. Transfer this ENTIRE folder to your air-gapped Windows system

2. Install Python dependencies on Windows:
   ```
   pip install --no-index --find-links python_dependencies paramiko
   ```

3. Run the air-gapped STIG executor:
   ```
   python airgap_stig_executor_complete.py
   ```

4. The script will:
   - Transfer Ubuntu packages to target
   - Install them offline using dpkg
   - Execute STIG remediation
   - Apply all 172 controls

## Requirements

- Windows with Python 3.6+
- Ubuntu 20.04 target with SSH access
- Sudo privileges on target
- Console access to target (KVM/IPMI)

## Package Sizes

- Python packages: ~20-30 MB
- Ubuntu packages: ~10-20 MB
- Total: ~30-50 MB

## Security Notes

⚠️  This package will:
- Apply ALL 172 STIG controls
- Disable SSH password authentication
- Enable strict firewall rules
- Disable USB and wireless
- Require SSH key access after execution

## Support

See included documentation for troubleshooting.

Generated by: Complete Air-Gap Package Downloader v3.0.0
"""

        readme_file = self.output_dir / "README.txt"
        readme_file.write_text(readme_content)

        print(f"✓ Created: {readme_file}")
        return True

    def print_summary(self):
        """Print final summary"""
        print("\n" + "="*80)
        print("DOWNLOAD COMPLETE")
        print("="*80)

        # Calculate sizes
        python_files = list(self.python_deps_dir.glob('*'))
        python_size = sum(f.stat().st_size for f in python_files if f.is_file()) / (1024 * 1024)

        ubuntu_files = list(self.ubuntu_debs_dir.glob('*.deb'))
        ubuntu_size = sum(f.stat().st_size for f in ubuntu_files) / (1024 * 1024)

        print(f"\n✓ Package directory: {self.output_dir}/")
        print(f"\nPython packages: {len(python_files)} files ({python_size:.1f} MB)")
        print(f"Ubuntu packages: {len(ubuntu_files)} .deb files ({ubuntu_size:.1f} MB)")
        print(f"Total size: {python_size + ubuntu_size:.1f} MB")

        print("\n" + "="*80)
        print("NEXT STEPS")
        print("="*80)

        print("\n1️⃣  VERIFY downloads are complete:")
        print(f"   - Check {self.python_deps_dir}/ has .whl files")
        print(f"   - Check {self.ubuntu_debs_dir}/ has .deb files")

        print("\n2️⃣  COPY required scripts:")
        print("   - Copy airgap_stig_executor_complete.py")
        print("   - Copy ubuntu20_stig_v2r3_enhanced.py")
        print(f"   - To: {self.output_dir}/")

        print("\n3️⃣  TRANSFER entire package to air-gapped system:")
        print(f"   - Copy entire folder: {self.output_dir}/")
        print("   - Use USB, CD/DVD, or approved method")

        print("\n4️⃣  ON AIR-GAPPED SYSTEM:")
        print("   - Extract package")
        print("   - Read README.txt")
        print("   - Run: python airgap_stig_executor_complete.py")

        print("\n" + "="*80)

    def download(self):
        """Main download process"""
        self.print_banner()

        if not self.check_prerequisites():
            return False

        if not self.create_directories():
            return False

        if not self.download_python_packages():
            print("\n❌ Failed to download Python packages")
            return False

        # Try Docker method first, fall back to manual instructions
        self.download_ubuntu_packages_docker()

        if not self.create_offline_installer_script():
            return False

        if not self.create_manifest():
            return False

        if not self.create_readme():
            return False

        self.print_summary()

        return True

def main():
    """Main entry point"""
    downloader = CompleteAirGapDownloader()

    success = downloader.download()

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
