#!/usr/bin/env python3
"""
Air-Gap Package Builder
========================

Creates a complete, ready-to-transfer air-gapped STIG package.

This script:
1. Verifies all required files are present
2. Downloads dependencies (if not already present)
3. Creates proper directory structure
4. Packages everything into a transferable archive
5. Generates checksums for verification

Usage:
    python build_airgap_package.py

Requirements:
    - Internet connection (for dependency download)
    - Python 3.6+
    - All required scripts in current directory

Output:
    stig-airgap-package-YYYYMMDD.zip - Complete transferable package

Author: Air-Gap Package Builder
Version: 1.0.0
"""

import os
import sys
import shutil
import zipfile
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime

class AirGapPackageBuilder:
    """Build complete air-gapped STIG package"""
    
    def __init__(self):
        self.package_name = f"stig-airgap-package-{datetime.now().strftime('%Y%m%d')}"
        self.package_dir = Path(self.package_name)
        self.required_files = [
            'airgap_windows_stig_executor.py',
            'ubuntu20_stig_v2r3_enhanced.py',
            'download_dependencies.py',
            'run_airgap_stig.bat',
            'README_AIRGAP.md',
            'AIRGAP_QUICK_START.md',
        ]
        self.optional_files = [
            'MAXIMUM_SECURITY_GUIDE.md',
            'TROUBLESHOOTING_AIRGAP.md',
        ]
        
    def print_banner(self):
        """Print script banner"""
        print("\n" + "="*80)
        print("AIR-GAP PACKAGE BUILDER")
        print("Creates complete offline STIG remediation package")
        print("="*80)
        print()
        
    def check_required_files(self):
        """Check if all required files are present"""
        print("Checking for required files...")
        
        missing = []
        found = []
        
        for filename in self.required_files:
            if Path(filename).exists():
                found.append(filename)
                print(f"  [OK] {filename}")
            else:
                missing.append(filename)
                print(f"  [FAIL] {filename} - MISSING")
        
        # Check optional files
        for filename in self.optional_files:
            if Path(filename).exists():
                found.append(filename)
                print(f"  [OK] {filename} (optional)")
        
        if missing:
            print(f"\n[ERROR] Missing required files: {len(missing)}")
            for f in missing:
                print(f"  - {f}")
            return False
        
        print(f"\n[OK] All required files present ({len(found)} total)")
        return True
    
    def check_dependencies(self):
        """Check if dependencies folder exists"""
        print("\nChecking dependencies folder...")
        
        deps_dir = Path('dependencies')
        
        if not deps_dir.exists():
            print("  [FAIL] dependencies/ folder not found")
            print("\n[DOWNLOAD] Dependencies need to be downloaded first")
            print("   This requires internet connection.")
            
            response = input("\nDownload dependencies now? [Y/n]: ").strip().lower()
            if response in ['', 'y', 'yes']:
                return self.download_dependencies()
            else:
                print("\n[ERROR] Cannot proceed without dependencies")
                print("   Run: python download_dependencies.py")
                return False
        
        # Check if dependencies folder has content
        wheel_files = list(deps_dir.glob('*.whl'))
        tar_files = list(deps_dir.glob('*.tar.gz'))
        
        if not wheel_files and not tar_files:
            print("  [FAIL] dependencies/ folder is empty")
            print("\n[DOWNLOAD] Need to download package files")
            
            response = input("\nDownload dependencies now? [Y/n]: ").strip().lower()
            if response in ['', 'y', 'yes']:
                return self.download_dependencies()
            else:
                print("\n[ERROR] Cannot proceed with empty dependencies")
                return False
        
        print(f"  [OK] dependencies/ folder found with {len(wheel_files + tar_files)} packages")
        return True
    
    def download_dependencies(self):
        """Download dependencies using the downloader script"""
        print("\n" + "="*80)
        print("DOWNLOADING DEPENDENCIES")
        print("="*80)
        
        try:
            # Run the download script
            result = subprocess.run(
                [sys.executable, 'download_dependencies.py'],
                timeout=600
            )
            
            if result.returncode == 0:
                print("\n[OK] Dependencies downloaded successfully")
                return True
            else:
                print("\n[ERROR] Dependency download failed")
                return False
                
        except subprocess.TimeoutExpired:
            print("\n[ERROR] Download timed out")
            return False
        except FileNotFoundError:
            print("\n[ERROR] download_dependencies.py not found")
            print("   Please ensure the download script is present")
            return False
        except Exception as e:
            print(f"\n[ERROR] Error during download: {e}")
            return False
    
    def create_package_structure(self):
        """Create package directory structure"""
        print("\n" + "="*80)
        print("CREATING PACKAGE STRUCTURE")
        print("="*80)
        
        # Remove existing package dir if it exists
        if self.package_dir.exists():
            print(f"\n[WARNING]  Package directory already exists: {self.package_dir}")
            response = input("Delete and recreate? [y/N]: ").strip().lower()
            if response == 'y':
                shutil.rmtree(self.package_dir)
                print("[OK] Removed existing package")
            else:
                print("[ERROR] Cannot proceed with existing directory")
                return False
        
        # Create main directory
        self.package_dir.mkdir()
        print(f"\n[OK] Created: {self.package_dir}/")
        
        # Create documentation subdirectory
        docs_dir = self.package_dir / 'Documentation'
        docs_dir.mkdir()
        print(f"[OK] Created: {docs_dir}/")
        
        return True
    
    def copy_files(self):
        """Copy all files to package directory"""
        print("\n" + "="*80)
        print("COPYING FILES TO PACKAGE")
        print("="*80)
        print()
        
        # Copy main scripts
        main_files = [
            'airgap_windows_stig_executor.py',
            'ubuntu20_stig_v2r3_enhanced.py',
            'download_dependencies.py',
            'run_airgap_stig.bat',
        ]
        
        for filename in main_files:
            src = Path(filename)
            dst = self.package_dir / filename
            if src.exists():
                shutil.copy2(src, dst)
                size_kb = src.stat().st_size / 1024
                print(f"  [OK] {filename} ({size_kb:.1f} KB)")
        
        # Copy documentation
        docs_dir = self.package_dir / 'Documentation'
        doc_files = self.required_files + self.optional_files
        
        for filename in doc_files:
            if filename.endswith('.md'):
                src = Path(filename)
                if src.exists():
                    dst = docs_dir / filename
                    shutil.copy2(src, dst)
                    size_kb = src.stat().st_size / 1024
                    print(f"  [OK] {filename} -> Documentation/ ({size_kb:.1f} KB)")
        
        # Copy dependencies folder
        print("\n  Copying dependencies folder...")
        src_deps = Path('dependencies')
        dst_deps = self.package_dir / 'dependencies'
        
        if src_deps.exists():
            shutil.copytree(src_deps, dst_deps)
            
            # Count files
            dep_files = list(dst_deps.glob('*'))
            total_size = sum(f.stat().st_size for f in dep_files) / (1024 * 1024)
            print(f"  [OK] dependencies/ ({len(dep_files)} files, {total_size:.1f} MB)")
        
        print("\n[OK] All files copied successfully")
        return True
    
    def generate_checksums(self):
        """Generate SHA256 checksums for verification"""
        print("\n" + "="*80)
        print("GENERATING CHECKSUMS")
        print("="*80)
        print()
        
        checksums = {}
        
        # Generate checksums for main files
        for item in self.package_dir.rglob('*'):
            if item.is_file() and item.name != 'checksums.txt':
                # Calculate SHA256
                sha256 = hashlib.sha256()
                with open(item, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b''):
                        sha256.update(chunk)
                
                # Store relative path and checksum
                rel_path = item.relative_to(self.package_dir)
                checksums[str(rel_path)] = sha256.hexdigest()
                print(f"  [OK] {rel_path}")
        
        # Write checksums file
        checksums_file = self.package_dir / 'checksums.txt'
        with open(checksums_file, 'w') as f:
            f.write("# SHA256 Checksums for Air-Gap STIG Package\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n")
            f.write("#\n")
            f.write("# Verify with: shasum -c checksums.txt (Linux/Mac)\n")
            f.write("# Or manually compare checksums\n\n")
            
            for filepath, checksum in sorted(checksums.items()):
                f.write(f"{checksum}  {filepath}\n")
        
        print(f"\n[OK] Generated checksums for {len(checksums)} files")
        print(f"[OK] Saved to: {checksums_file}")
        
        return True
    
    def create_readme(self):
        """Create main package README"""
        print("\nCreating package README...")
        
        readme_content = f"""# Air-Gapped STIG Package
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Package Contents

### Main Scripts:
- airgap_windows_stig_executor.py - Main Windows executor (MAXIMUM SECURITY)
- ubuntu20_stig_v2r3_enhanced.py - STIG remediation script  
- download_dependencies.py - Download script (for rebuilding)
- run_airgap_stig.bat - Windows quick launcher

### Dependencies:
- dependencies/ - All Python packages for offline installation
  (paramiko, cryptography, bcrypt, and all dependencies)

### Documentation:
- Documentation/README_AIRGAP.md - Comprehensive guide
- Documentation/AIRGAP_QUICK_START.md - 5-minute quick start
- Documentation/MAXIMUM_SECURITY_GUIDE.md - Security details
- Documentation/TROUBLESHOOTING_AIRGAP.md - Common issues

### Verification:
- checksums.txt - SHA256 checksums for all files

## Quick Start

1. Transfer this entire package to your air-gapped Windows system
2. Verify checksums (optional but recommended)
3. Run: `run_airgap_stig.bat` OR `python airgap_windows_stig_executor.py`
4. Follow interactive prompts
5. Reboot target Ubuntu system when complete

## Requirements

- Windows system with Python 3.6+
- Network access to target Ubuntu 20.04 system
- SSH credentials with sudo privileges
- Console access to target (KVM/IPMI/Physical)

## Security Mode

This package applies MAXIMUM SECURITY configuration:
- SSH password authentication DISABLED (keys only)
- Root login DISABLED
- USB storage DISABLED
- Wireless DISABLED  
- Strict firewall (deny all except SSH)
- All 172 STIG controls applied

## Support

See Documentation/README_AIRGAP.md for comprehensive documentation.

## Important Notes

[WARNING]  CRITICAL: Ensure you have console access before running
[WARNING]  CRITICAL: SSH keys must be configured (password auth disabled)
[WARNING]  CRITICAL: Create backup/snapshot before execution
[WARNING]  CRITICAL: Test in non-production environment first

## Verification

To verify package integrity:
1. Check file count matches manifest
2. Verify checksums: shasum -c checksums.txt (Linux/Mac)
3. On Windows: compare checksums manually using certutil

## Version Information

Package Version: 2.0.0-airgap
STIG Version: V2R3 (Release 3, July 2025)
Controls: 172 total (14 CAT I, 136 CAT II, 22 CAT III)
Security Mode: Maximum Lockdown
"""
        
        readme_file = self.package_dir / 'README.txt'
        with open(readme_file, 'w') as f:
            f.write(readme_content)
        
        print(f"[OK] Created: {readme_file}")
        return True
    
    def create_archive(self):
        """Create ZIP archive of package"""
        print("\n" + "="*80)
        print("CREATING ARCHIVE")
        print("="*80)
        print()
        
        archive_name = f"{self.package_name}.zip"
        
        print(f"Creating: {archive_name}")
        print("This may take a moment...")
        
        try:
            with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add all files
                for item in self.package_dir.rglob('*'):
                    if item.is_file():
                        arcname = item.relative_to(self.package_dir.parent)
                        zipf.write(item, arcname)
                        print(f"  + {arcname}")
            
            # Get archive size
            archive_path = Path(archive_name)
            size_mb = archive_path.stat().st_size / (1024 * 1024)
            
            print(f"\n[OK] Archive created: {archive_name}")
            print(f"[OK] Size: {size_mb:.2f} MB")
            
            # Generate archive checksum
            sha256 = hashlib.sha256()
            with open(archive_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256.update(chunk)
            
            checksum_file = Path(f"{archive_name}.sha256")
            with open(checksum_file, 'w') as f:
                f.write(f"{sha256.hexdigest()}  {archive_name}\n")
            
            print(f"[OK] Checksum: {checksum_file}")
            
            return archive_name
            
        except Exception as e:
            print(f"\n[ERROR] Failed to create archive: {e}")
            return None
    
    def print_summary(self, archive_name):
        """Print build summary"""
        print("\n" + "="*80)
        print("BUILD COMPLETE")
        print("="*80)
        
        archive_path = Path(archive_name)
        package_size = archive_path.stat().st_size / (1024 * 1024)
        
        print(f"\n[OK] Package created successfully!")
        print(f"\nPackage: {archive_name}")
        print(f"Size: {package_size:.2f} MB")
        print(f"Checksum: {archive_name}.sha256")
        
        print("\n" + "="*80)
        print("NEXT STEPS")
        print("="*80)
        
        print("\n1. VERIFY package integrity:")
        print(f"   Windows: certutil -hashfile {archive_name} SHA256")
        print(f"   Linux/Mac: shasum -a 256 {archive_name}")
        print(f"   Compare with: {archive_name}.sha256")

        print("\n2. TRANSFER to air-gapped system:")
        print("   - Use approved transfer method (USB, CD/DVD, secure transfer)")
        print("   - Scan for malware if required by policy")
        print("   - Document transfer for compliance")

        print("\n3. ON AIR-GAPPED SYSTEM:")
        print(f"   - Extract: {archive_name}")
        print("   - Verify checksums (optional)")
        print("   - Read: README.txt")
        print("   - Run: run_airgap_stig.bat")
        
        print("\n" + "="*80)
        print("PACKAGE CONTENTS")
        print("="*80)
        
        print(f"\n[PACKAGE] {archive_name} contains:")
        print("   [OK] airgap_windows_stig_executor.py - Main executor")
        print("   [OK] ubuntu20_stig_v2r3_enhanced.py - STIG script")
        print("   [OK] dependencies/ - All Python packages (offline)")
        print("   [OK] Documentation/ - Complete documentation")
        print("   [OK] run_airgap_stig.bat - Windows launcher")
        print("   [OK] checksums.txt - File verification")
        print("   [OK] README.txt - Package information")
        
        print("\n" + "="*80)
        print("SECURITY NOTES")
        print("="*80)
        
        print("\n[WARNING]  This package will apply MAXIMUM SECURITY:")
        print("   - SSH password authentication DISABLED")
        print("   - Root login DISABLED")
        print("   - USB storage DISABLED")
        print("   - Wireless DISABLED")
        print("   - Strict firewall (deny all except SSH)")
        print("   - All 172 STIG controls applied")
        
        print("\n[WARNING]  ENSURE before running:")
        print("   - Console access available (KVM/IPMI)")
        print("   - SSH keys configured on target")
        print("   - System backup/snapshot created")
        print("   - Tested in dev environment")
        
        print("\n" + "="*80)
        
    def build(self):
        """Main build process"""
        self.print_banner()
        
        # Check prerequisites
        if not self.check_required_files():
            print("\n[ERROR] Build failed: Missing required files")
            return False
        
        if not self.check_dependencies():
            print("\n[ERROR] Build failed: Dependencies not available")
            return False
        
        # Create package
        if not self.create_package_structure():
            print("\n[ERROR] Build failed: Could not create package structure")
            return False
        
        if not self.copy_files():
            print("\n[ERROR] Build failed: Could not copy files")
            return False
        
        if not self.generate_checksums():
            print("\n[ERROR] Build failed: Could not generate checksums")
            return False
        
        if not self.create_readme():
            print("\n[ERROR] Build failed: Could not create README")
            return False
        
        archive_name = self.create_archive()
        if not archive_name:
            print("\n[ERROR] Build failed: Could not create archive")
            return False
        
        self.print_summary(archive_name)
        
        print("\n[OK] Build successful! Package ready for transfer.")
        print("=" * 80)
        
        return True


def main():
    """Main entry point"""
    builder = AirGapPackageBuilder()
    
    success = builder.build()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
