#!/usr/bin/env python3
"""
STIG Air-Gap Package Dependency Downloader
===========================================

Run this script on an INTERNET-CONNECTED system to download
all required dependencies for air-gapped STIG execution.

This will create a 'dependencies' folder containing all Python
packages that can be transferred to the air-gapped system.

Usage:
    python download_dependencies.py

Requirements:
    - Python 3.6+
    - pip
    - Internet connection

Author: Air-Gap Package Builder
Version: 1.0.0
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_prerequisites():
    """Check if prerequisites are met"""
    print("\n" + "="*80)
    print("STIG AIR-GAP DEPENDENCY DOWNLOADER")
    print("="*80)
    print("\nChecking prerequisites...")
    
    # Check Python version
    if sys.version_info < (3, 6):
        print(f"❌ Python 3.6+ required (current: {sys.version})")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Check pip
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', '--version'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ pip is available")
        else:
            print("❌ pip not found")
            return False
    except Exception as e:
        print(f"❌ pip error: {e}")
        return False
    
    # Check internet connectivity
    print("\nChecking internet connectivity...")
    try:
        import urllib.request
        urllib.request.urlopen('https://pypi.org', timeout=5)
        print("✓ Internet connection available")
    except Exception as e:
        print(f"❌ No internet connection: {e}")
        print("\nThis script requires internet to download packages.")
        return False
    
    return True

def download_dependencies(output_dir="dependencies"):
    """Download all required dependencies"""
    print("\n" + "="*80)
    print("DOWNLOADING DEPENDENCIES")
    print("="*80)
    
    # Create output directory
    output_path = Path(output_dir)
    if output_path.exists():
        print(f"\n⚠️  Directory '{output_dir}' already exists.")
        response = input("Delete and recreate? [y/N]: ").strip().lower()
        if response == 'y':
            shutil.rmtree(output_path)
            print(f"✓ Removed existing directory")
        else:
            print("Using existing directory (may contain old files)")
    
    output_path.mkdir(exist_ok=True)
    print(f"\n📁 Output directory: {output_path.absolute()}")
    
    # List of packages to download
    packages = [
        'paramiko',       # Main SSH library
        'cryptography',   # Crypto backend
        'bcrypt',         # Password hashing
        'pynacl',         # Sodium library
        'cffi',           # Foreign function interface
        'pycparser',      # C parser
        'six',            # Python 2/3 compatibility
    ]
    
    print(f"\n📦 Packages to download: {', '.join(packages)}")
    print("\nDownloading packages...")
    print("This may take a few minutes depending on your connection speed.")
    
    try:
        # Use pip download to get all packages and dependencies
        cmd = [
            sys.executable, '-m', 'pip', 'download',
            '--dest', str(output_path),
            '--prefer-binary',  # Prefer wheel files over source
        ] + packages
        
        print(f"\nExecuting: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode == 0:
            print("\n✓ Download completed successfully!")
            
            # List downloaded files
            files = list(output_path.glob('*'))
            print(f"\n📦 Downloaded {len(files)} package files:")
            
            total_size = 0
            for f in sorted(files):
                size = f.stat().st_size
                total_size += size
                size_mb = size / (1024 * 1024)
                print(f"  - {f.name} ({size_mb:.2f} MB)")
            
            total_mb = total_size / (1024 * 1024)
            print(f"\n✓ Total size: {total_mb:.2f} MB")
            
            return True
        else:
            print(f"\n❌ Download failed!")
            print(f"Error output:\n{result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("\n❌ Download timed out (exceeded 10 minutes)")
        return False
    except Exception as e:
        print(f"\n❌ Download error: {e}")
        return False

def create_verification_script(output_dir="dependencies"):
    """Create a script to verify the downloaded packages"""
    verification_script = f'''#!/usr/bin/env python3
"""
Verify downloaded dependencies
"""
import sys
from pathlib import Path

deps_dir = Path("{output_dir}")
if not deps_dir.exists():
    print(f"❌ Dependencies directory not found: {{deps_dir}}")
    sys.exit(1)

files = list(deps_dir.glob("*.whl")) + list(deps_dir.glob("*.tar.gz"))
print(f"Found {{len(files)}} package files in {{deps_dir}}")

if len(files) < 5:
    print("⚠️  Warning: Expected more package files")
    print("Some dependencies may be missing")
else:
    print("✓ Package count looks good")

# Check for critical packages
critical = ['paramiko', 'cryptography', 'bcrypt']
found = {{pkg: False for pkg in critical}}

for f in files:
    for pkg in critical:
        if pkg.lower() in f.name.lower():
            found[pkg] = True

print("\\nCritical packages:")
for pkg, present in found.items():
    status = "✓" if present else "❌"
    print(f"  {{status}} {{pkg}}")

if all(found.values()):
    print("\\n✓ All critical packages present")
    sys.exit(0)
else:
    print("\\n❌ Some critical packages missing")
    sys.exit(1)
'''
    
    verify_path = Path(output_dir) / "verify_packages.py"
    with open(verify_path, 'w') as f:
        f.write(verification_script)
    
    print(f"\n✓ Created verification script: {verify_path}")
    print(f"  Run 'python {verify_path}' to verify packages")

def print_next_steps(output_dir="dependencies"):
    """Print next steps for user"""
    print("\n" + "="*80)
    print("DOWNLOAD COMPLETE - NEXT STEPS")
    print("="*80)
    
    abs_path = Path(output_dir).absolute()
    
    print(f"\n✓ Dependencies downloaded to: {abs_path}")
    print(f"✓ Total files: {len(list(Path(output_dir).glob('*')))} packages")
    
    print("\n📋 Next Steps:")
    print("\n1️⃣  VERIFY the downloaded packages (optional):")
    print(f"   python {output_dir}/verify_packages.py")
    
    print("\n2️⃣  CREATE the air-gap package:")
    print("   a) Copy the entire 'dependencies' folder")
    print("   b) Copy 'airgap_windows_stig_executor.py'")
    print("   c) Copy 'ubuntu20_stig_v2r3_enhanced.py' (your STIG script)")
    print("   d) Copy all documentation files (.md)")
    
    print("\n3️⃣  TRANSFER to air-gapped system:")
    print("   - Use USB drive, CD/DVD, or approved transfer method")
    print("   - Ensure all files maintain their structure")
    
    print("\n4️⃣  ON AIR-GAPPED SYSTEM:")
    print("   - Place all files in same directory")
    print("   - Run: python airgap_windows_stig_executor.py")
    print("   - Script will auto-install from local dependencies")
    
    print("\n" + "="*80)
    print("PACKAGE STRUCTURE")
    print("="*80)
    print("\nYour air-gap package should look like:")
    print("""
    stig-airgap-package/
    ├── dependencies/              ← This folder (with all .whl/.tar.gz files)
    │   ├── paramiko-*.whl
    │   ├── cryptography-*.whl
    │   ├── bcrypt-*.whl
    │   └── ... (more packages)
    ├── airgap_windows_stig_executor.py
    ├── ubuntu20_stig_v2r3_enhanced.py
    ├── README_AIRGAP.md
    └── other documentation files
    """)
    
    print("\n" + "="*80)
    print("SECURITY NOTES")
    print("="*80)
    print("\n⚠️  IMPORTANT:")
    print("   - Verify package integrity before transfer")
    print("   - Use approved transfer methods only")
    print("   - Scan for malware if required by policy")
    print("   - Document transfer for compliance")
    
    print("\n" + "="*80)

def main():
    """Main entry point"""
    print("\n🌐 This script requires internet connection")
    print("📥 It will download all dependencies for offline installation")
    
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Cannot continue.")
        sys.exit(1)
    
    print("\n" + "="*80)
    print("READY TO DOWNLOAD")
    print("="*80)
    print("\nThis will download:")
    print("  - paramiko (SSH library)")
    print("  - cryptography (crypto backend)")
    print("  - bcrypt (password hashing)")
    print("  - All dependencies (~20-30 MB)")
    
    response = input("\nProceed with download? [Y/n]: ").strip().lower()
    if response not in ['', 'y', 'yes']:
        print("❌ Download cancelled.")
        sys.exit(0)
    
    # Download dependencies
    if not download_dependencies():
        print("\n❌ Download failed. Please check errors above.")
        sys.exit(1)
    
    # Create verification script
    create_verification_script()
    
    # Print next steps
    print_next_steps()
    
    print("\n✓ All done! Ready to create air-gap package.")
    print("=" * 80)

if __name__ == '__main__':
    main()
