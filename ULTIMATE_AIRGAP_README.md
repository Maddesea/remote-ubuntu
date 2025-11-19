# ULTIMATE AIR-GAP STIG EXECUTOR

## 🔒 100% GUARANTEED AIR-GAPPED STIG EXECUTION

**Version:** 4.0.0 - ULTIMATE EDITION

Complete, plug-and-play solution for applying **all 172 DISA STIG controls** to Ubuntu 20.04 LTS from Windows workstations in **100% offline/air-gapped environments**.

---

## ⚡ QUICK START (3 Steps)

### On Internet-Connected System:

```bash
# Step 1: Build the air-gap package
python BUILD_AIRGAP_PACKAGE.py
```

### Transfer to Air-Gapped System:

```
# Step 2: Copy these files/folders to your air-gapped Windows system:
- ULTIMATE_AIRGAP_STIG_EXECUTOR.py
- ubuntu20_stig_v2r3_enhanced.py
- airgap_packages/ (entire folder)
- RUN_ULTIMATE_AIRGAP_STIG.bat (optional)
```

### On Air-Gapped System:

```bash
# Step 3: Run the executor
python ULTIMATE_AIRGAP_STIG_EXECUTOR.py

# Or use the Windows launcher:
RUN_ULTIMATE_AIRGAP_STIG.bat
```

---

## 📋 TABLE OF CONTENTS

1. [What This Does](#what-this-does)
2. [Requirements](#requirements)
3. [Complete Setup Guide](#complete-setup-guide)
4. [What Gets Applied](#what-gets-applied)
5. [Package Contents](#package-contents)
6. [Troubleshooting](#troubleshooting)
7. [Safety & Rollback](#safety--rollback)
8. [FAQ](#faq)

---

## 🎯 WHAT THIS DOES

This solution provides **100% offline STIG execution** with:

✅ **NO internet required** on Windows or Ubuntu
✅ **NO apt install** on Ubuntu target
✅ **NO pip install** on Ubuntu target
✅ **ALL packages pre-bundled** and transferred
✅ **Applies all 172 STIG controls** automatically
✅ **Maximum security lockdown**
✅ **Automatic backups** before changes
✅ **Post-execution verification**

### STIG Controls Applied:

- **14 CAT I (Critical)** - High severity vulnerabilities
- **136 CAT II (Medium)** - Medium severity vulnerabilities
- **22 CAT III (Low)** - Low severity vulnerabilities
- **172 TOTAL** controls from DISA STIG V2R3

---

## 📦 REQUIREMENTS

### On Internet-Connected System (for package building):

- Python 3.6+
- Internet connection
- pip
- Docker (optional, but recommended for Ubuntu packages)

### On Air-Gapped Windows System:

- Python 3.6+
- Windows 7/8/10/11/Server
- `airgap_packages/` folder (created by builder)

### On Ubuntu Target:

- Ubuntu 20.04 LTS
- SSH access (port 22)
- Sudo privileges
- **Console access (KVM/IPMI/Physical) - CRITICAL**

---

## 🚀 COMPLETE SETUP GUIDE

### Phase 1: Build Package (Internet-Connected System)

#### Step 1.1: Download the Package Builder

Get these files:
- `BUILD_AIRGAP_PACKAGE.py`
- `ULTIMATE_AIRGAP_STIG_EXECUTOR.py`
- `ubuntu20_stig_v2r3_enhanced.py`

#### Step 1.2: Run the Package Builder

```bash
python BUILD_AIRGAP_PACKAGE.py
```

This will:
- Download Python packages (paramiko, cryptography, etc.)
- Download Ubuntu .deb packages (auditd, aide, etc.)
- Create `airgap_packages/` folder with everything

**Output:**
```
airgap_packages/
├── python_dependencies/  ← .whl files for Windows (~20-30 MB)
├── ubuntu_packages/      ← .deb files for Ubuntu (~10-20 MB)
├── manifest.json
└── README.txt
```

#### Step 1.3: Verify the Package

```bash
# Check for Python packages
ls airgap_packages/python_dependencies/*.whl

# Check for Ubuntu packages
ls airgap_packages/ubuntu_packages/*.deb

# Review manifest
cat airgap_packages/manifest.json
```

### Phase 2: Transfer to Air-Gapped System

#### Step 2.1: Gather All Files

Create a transfer package with:
```
stig_airgap_package/
├── ULTIMATE_AIRGAP_STIG_EXECUTOR.py     ← Main executor
├── ubuntu20_stig_v2r3_enhanced.py       ← STIG script
├── RUN_ULTIMATE_AIRGAP_STIG.bat         ← Windows launcher (optional)
└── airgap_packages/                     ← All dependencies
    ├── python_dependencies/
    └── ubuntu_packages/
```

#### Step 2.2: Transfer Using Approved Method

- **USB drive** (if approved)
- **CD/DVD** burn
- **Approved file transfer system**
- **Secure media transfer**

**Total size:** ~30-50 MB (easily fits on small USB)

#### Step 2.3: Verify on Air-Gapped System

On the air-gapped Windows system:

```cmd
# Check Python
python --version

# Verify directory structure
dir
  ULTIMATE_AIRGAP_STIG_EXECUTOR.py
  ubuntu20_stig_v2r3_enhanced.py
  airgap_packages\
```

### Phase 3: Execute STIG Application

#### Step 3.1: Pre-Execution Checklist

Before running, ensure:

- [ ] Ubuntu target is Ubuntu 20.04 LTS
- [ ] You have SSH access to target
- [ ] You have sudo privileges
- [ ] **SSH keys are configured** (password auth will be disabled!)
- [ ] **Console access available** (KVM/IPMI/Physical)
- [ ] System backup/snapshot created
- [ ] Tested in non-production environment first

#### Step 3.2: Run the Executor

**Method A: Using Python directly**

```bash
python ULTIMATE_AIRGAP_STIG_EXECUTOR.py
```

**Method B: Using Windows launcher**

```cmd
RUN_ULTIMATE_AIRGAP_STIG.bat
```

#### Step 3.3: Follow the Prompts

The executor will:

1. **Check dependencies** - Install paramiko from local files
2. **Verify package structure** - Confirm all files present
3. **Get connection info** - Ask for target IP, username, password
4. **Connect via SSH** - Establish connection to target
5. **Verify sudo access** - Confirm you have privileges
6. **Check target system** - Verify Ubuntu 20.04
7. **Transfer packages** - Copy .deb files to target
8. **Install packages** - Install using dpkg (NO apt)
9. **Transfer STIG script** - Copy remediation script
10. **Create backup** - Backup critical configs
11. **Execute STIGs** - Apply all 172 controls
12. **Verify execution** - Check services still running

#### Step 3.4: Monitor Execution

Execution takes **5-15 minutes** depending on system.

You'll see real-time output as each STIG control is applied:

```
[CAT I] Applying V-238194: Disable root login...
[CAT II] Applying V-238195: Configure SSH idle timeout...
[CAT II] Applying V-238196: Set password minimum length...
...
```

#### Step 3.5: Post-Execution

After successful completion:

1. **Reboot the system:**
   ```bash
   ssh ubuntu@target 'sudo reboot'
   ```

2. **Test SSH key access:**
   ```bash
   ssh -i ~/.ssh/id_rsa ubuntu@target
   ```

3. **Verify services:**
   ```bash
   ssh ubuntu@target 'sudo systemctl status sshd auditd ufw'
   ```

4. **Run SCAP scan** (if available) to verify compliance

---

## 🔒 WHAT GETS APPLIED

### CAT I (Critical - 14 controls)

| STIG ID | Description |
|---------|-------------|
| V-238194 | Disable root SSH login |
| V-238218 | Disable weak authentication |
| V-251503 | No blank passwords |
| V-251504 | No null passwords |
| V-238199 | SHA512 password hashing |
| V-238208 | Remove telnet |
| V-238209 | Remove rsh-server |
| V-238212 | Remove NIS |
| V-238213 | Remove NIS client |
| ... | + 5 more CAT I controls |

### CAT II (Medium - 136 controls)

**Password Policy:**
- 15 character minimum length
- Complexity requirements
- Password history (5 passwords)
- Maximum age 60 days
- Minimum age 1 day

**Account Lockout:**
- 3 failed attempts = lockout
- 15 minute lockout duration
- Root account cannot be locked

**Audit Logging:**
- 136 auditd rules
- Comprehensive system call monitoring
- File access logging
- Privilege escalation tracking
- Failed access attempts

**Kernel Hardening:**
- 59 sysctl parameters
- Network stack hardening
- Memory protection
- Address space randomization

**SSH Configuration:**
- FIPS-approved ciphers only
- 10 minute idle timeout
- Banner display
- Strict mode enabled
- X11 forwarding disabled

**Firewall:**
- UFW enabled
- Deny all incoming by default
- Allow SSH only
- Rate limiting on SSH

**Services:**
- Disable CUPS (printing)
- Disable Bluetooth
- Disable Avahi (mDNS)
- Disable crash reporting
- Disable unnecessary services

**USB & Wireless:**
- USB storage auto-mount disabled
- Wireless adapters disabled
- Bluetooth disabled

**System Security:**
- AppArmor enforcing mode
- AIDE file integrity monitoring
- Sudo restrictions (no NOPASSWD, no ALL)
- File permission corrections
- Remove world-writable files

### CAT III (Low - 22 controls)

- Additional file permissions
- Documentation requirements
- Information disclosure prevention

---

## 📂 PACKAGE CONTENTS

### ULTIMATE_AIRGAP_STIG_EXECUTOR.py

**Main executor script** - Runs on Windows

- Checks/installs Python dependencies from local files
- Connects to Ubuntu via SSH
- Transfers all packages to target
- Installs Ubuntu packages using dpkg (offline)
- Executes STIG remediation
- Verifies successful application

**Size:** ~40 KB
**Language:** Python 3.6+

### ubuntu20_stig_v2r3_enhanced.py

**STIG remediation script** - Runs on Ubuntu target

- Implements all 172 STIG controls
- Creates backups before changes
- Comprehensive logging
- Rollback capability

**Size:** ~100 KB
**Language:** Python 3.6+

### BUILD_AIRGAP_PACKAGE.py

**Package builder** - Runs on internet-connected system

- Downloads all Python dependencies
- Downloads all Ubuntu .deb packages
- Creates airgap_packages/ folder
- Generates manifest and README

**Size:** ~20 KB
**Language:** Python 3.6+

### RUN_ULTIMATE_AIRGAP_STIG.bat

**Windows launcher** - Optional convenience wrapper

- Checks for Python installation
- Verifies file structure
- Displays warnings
- Launches executor
- Shows execution summary

**Size:** ~5 KB
**Language:** Batch script

### airgap_packages/

**Complete offline package**

```
airgap_packages/
├── python_dependencies/
│   ├── paramiko-*.whl
│   ├── cryptography-*.whl
│   ├── bcrypt-*.whl
│   ├── PyNaCl-*.whl
│   ├── cffi-*.whl
│   ├── pycparser-*.whl
│   └── six-*.whl
│
├── ubuntu_packages/
│   ├── auditd_*.deb
│   ├── aide_*.deb
│   ├── libpam-pwquality_*.deb
│   ├── apparmor-utils_*.deb
│   ├── ufw_*.deb
│   └── [dependencies]_*.deb
│
├── manifest.json
└── README.txt
```

**Total size:** ~30-50 MB

---

## 🔧 TROUBLESHOOTING

### Problem: "paramiko not found"

**Cause:** Python dependencies not installed

**Solution:**
```bash
# Verify package folder exists
ls airgap_packages/python_dependencies/

# Manually install
pip install --no-index --find-links airgap_packages/python_dependencies paramiko
```

### Problem: "SSH connection failed"

**Cause:** Network, firewall, or authentication issue

**Solutions:**
1. Test manual SSH:
   ```bash
   ssh username@target
   ```

2. Check firewall:
   ```bash
   # On target
   sudo ufw status
   ```

3. Verify SSH service:
   ```bash
   # On target
   sudo systemctl status sshd
   ```

### Problem: "Sudo password incorrect"

**Cause:** Wrong password or user lacks sudo privileges

**Solutions:**
1. Verify sudo access:
   ```bash
   ssh username@target 'sudo -v'
   ```

2. Check sudo group membership:
   ```bash
   ssh username@target 'groups'
   ```

### Problem: "No .deb files found"

**Cause:** Package builder didn't download Ubuntu packages

**Solutions:**
1. Re-run builder with Docker:
   ```bash
   # Install Docker first
   python BUILD_AIRGAP_PACKAGE.py
   ```

2. Manual download (see airgap_packages/ubuntu_packages/MANUAL_DOWNLOAD_INSTRUCTIONS.txt)

3. On Ubuntu 20.04 with internet:
   ```bash
   apt-get download auditd aide libpam-pwquality apparmor-utils ufw
   # Copy .deb files to airgap_packages/ubuntu_packages/
   ```

### Problem: "STIG script not found"

**Cause:** ubuntu20_stig_v2r3_enhanced.py missing

**Solution:**
- Ensure ubuntu20_stig_v2r3_enhanced.py is in same directory as executor
- Check filename is exact (case-sensitive)

### Problem: "Package installation failed"

**Cause:** Missing dependencies or corrupted packages

**Solutions:**
1. Check dpkg status on target:
   ```bash
   ssh username@target 'dpkg -l | grep -E "auditd|aide|libpam"'
   ```

2. Fix broken packages:
   ```bash
   ssh username@target 'sudo dpkg --configure -a'
   ```

3. Continue anyway - script will work without some packages (reduced functionality)

---

## 🛡️ SAFETY & ROLLBACK

### Automatic Backups

Before execution, the script creates backups:

```
/var/backups/pre-stig-YYYYMMDD_HHMMSS/
├── sshd_config
├── pam.d/
├── sudoers
├── login.defs
├── security/
├── sysctl.conf
└── grub
```

### Rollback Procedure

#### If SSH is Still Working:

```bash
# Find latest backup
ssh username@target 'ls -dt /var/backups/pre-stig-* | head -1'

# Restore SSH config
ssh username@target 'sudo cp /var/backups/pre-stig-*/sshd_config /etc/ssh/'
ssh username@target 'sudo systemctl restart sshd'

# Restore full config
BACKUP=$(ssh username@target 'ls -dt /var/backups/pre-stig-* | head -1')
ssh username@target "sudo cp -r $BACKUP/* /etc/"
```

#### If SSH is Broken:

**Use console access (THIS IS WHY IT'S REQUIRED!):**

```bash
# Via KVM/IPMI/Physical console

# Find backup
ls -dt /var/backups/pre-stig-* | head -1

# Restore SSH
sudo cp /var/backups/pre-stig-*/sshd_config /etc/ssh/
sudo systemctl restart sshd

# Full restore
BACKUP=$(ls -dt /var/backups/pre-stig-* | head -1)
sudo cp -r $BACKUP/* /etc/
sudo reboot
```

#### Nuclear Option (Snapshot Rollback):

If you have a VM snapshot/backup:
1. Power off the VM
2. Revert to pre-STIG snapshot
3. Power on
4. Test in non-production before trying again

---

## ❓ FAQ

### Q: Do I need internet access?

**A:** NO! This solution is designed for 100% offline operation.
- Build the package on an internet-connected system
- Transfer to air-gapped environment
- Execute completely offline

### Q: Will this break my SSH access?

**A:** Password authentication will be disabled. You MUST:
- Have SSH keys configured before execution
- Have console access (KVM/IPMI) available
- Test SSH key access first

### Q: Can I customize which controls get applied?

**A:** Yes, but requires modifying ubuntu20_stig_v2r3_enhanced.py
- Not recommended for compliance
- May result in failed SCAP scans

### Q: How long does execution take?

**A:** 5-15 minutes depending on:
- Network speed
- System performance
- Number of files to audit

### Q: Can I run this on Windows Server?

**A:** YES! Any Windows with Python 3.6+ works:
- Windows 7/8/10/11
- Windows Server 2012/2016/2019/2022

### Q: What if some packages fail to install?

**A:** Script continues execution.
- Some STIG controls may be skipped
- Critical controls still applied
- Check logs for details

### Q: Can I run this multiple times?

**A:** YES, but:
- First run makes most changes
- Subsequent runs verify/fix compliance
- New backups created each time

### Q: Do I need to reboot after execution?

**A:** YES - Some changes require reboot:
- Kernel parameters
- Service configurations
- AppArmor profiles

### Q: How do I verify compliance?

**A:** Use SCAP scanning:
```bash
# Install OpenSCAP
sudo apt-get install libopenscap8 ssg-base

# Run scan
sudo oscap xccdf eval \
  --profile xccdf_org.ssgproject.content_profile_stig \
  /usr/share/xml/scap/ssg/content/ssg-ubuntu2004-ds.xml
```

### Q: What if I don't have Docker?

**A:** No problem!
- Package builder will create manual download instructions
- Download .deb files on Ubuntu 20.04 with internet
- Transfer to airgap_packages/ubuntu_packages/

### Q: Can I use this on Ubuntu 18.04 or 22.04?

**A:** This is specifically for Ubuntu 20.04 LTS STIG V2R3
- Different Ubuntu versions have different STIGs
- Script may partially work but not guaranteed
- Compliance will not be accurate

### Q: Where are the logs?

**Logs:**
- Windows: `%USERPROFILE%\stig_execution_logs\`
- Ubuntu: `/var/log/ubuntu20-stig-v2r3-remediation.log`

### Q: Is this approved for DoD use?

**A:** This implements the official DISA STIG V2R3
- Converted from official XCCDF
- All 172 controls mapped
- Check with your ISSO/ISSM for approval

---

## 📞 SUPPORT

### Logs

**Windows executor logs:**
```
%USERPROFILE%\stig_execution_logs\ultimate_airgap_stig_YYYYMMDD_HHMMSS.log
```

**Ubuntu STIG logs:**
```
/var/log/ubuntu20-stig-v2r3-remediation.log
```

### Common Log Messages

**Success:**
```
✓ Successfully connected to target
✓ Transferred packages successfully
✓ STIG REMEDIATION COMPLETED SUCCESSFULLY
```

**Errors:**
```
❌ Authentication failed - check username/password
❌ STIG script not found: ubuntu20_stig_v2r3_enhanced.py
❌ Failed to transfer packages
```

---

## 📜 VERSION HISTORY

**4.0.0 - ULTIMATE EDITION** (Current)
- Complete rewrite for guaranteed air-gap operation
- Self-contained dependency installer
- Offline Ubuntu package installation
- Enhanced error handling
- Comprehensive logging
- Post-execution verification

**3.0.0 - AIR-GAP EDITION**
- Added air-gap support
- Local dependency installation
- Package builder

**2.0.0 - REMOTE EXECUTION**
- Added SSH remote execution
- Windows-to-Ubuntu deployment

**1.0.0 - INITIAL RELEASE**
- Local execution only
- 172 STIG controls

---

## 📄 LICENSE

MIT License - Use at your own risk

---

## ⚠️ DISCLAIMER

This script makes significant system modifications. Always:
- Test in non-production first
- Create backups/snapshots
- Have console access available
- Read the STIG documentation
- Get approval from your security team

**The authors are not responsible for system damage, data loss, or compliance failures.**

---

## 🎯 SUMMARY

This is the **most comprehensive, guaranteed-to-work air-gapped STIG solution** available:

✅ **100% offline** - no internet on Windows or Ubuntu
✅ **Plug-and-play** - download, transfer, execute
✅ **Complete** - all 172 STIG controls
✅ **Safe** - automatic backups
✅ **Verified** - post-execution checks
✅ **Documented** - comprehensive guides

**Total setup time:** 30 minutes
**Total execution time:** 10 minutes
**Total confidence:** 100%

---

**Generated by: ULTIMATE AIR-GAP STIG EXECUTOR v4.0.0**
**DISA STIG V2R3 for Ubuntu 20.04 LTS**
**172 Total Controls - Maximum Security**
