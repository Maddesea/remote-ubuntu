# Air-Gapped Maximum Security STIG Executor

## [SECURE] Overview

Complete air-gapped package for executing Ubuntu 20.04 DISA STIG V2R3 remediation with **MAXIMUM SECURITY LOCKDOWN** from Windows workstations in isolated/classified environments.

### Key Features:
- [OK] **NO INTERNET REQUIRED** - Fully self-contained
- [OK] **ALL DEPENDENCIES BUNDLED** - Ready to use offline
- [OK] **MAXIMUM SECURITY MODE** - Most restrictive configuration
- [OK] **172 STIG CONTROLS** - Complete compliance
- [OK] **AUTOMATIC PASSWORD HANDLING** - No manual intervention
- [OK] **CLASSIFIED ENVIRONMENT READY** - Designed for air-gapped systems

---

## [TARGET] What This Package Does

### Standard Mode:
- Applies 172 STIG controls (14 CAT I, 136 CAT II, 22 CAT III)
- Achieves 90-100% STIG compliance
- Maintains reasonable usability

### **MAXIMUM SECURITY MODE** (Default):
- **Most restrictive STIG configuration possible**
- **SSH password authentication DISABLED** (keys only)
- **All unnecessary services DISABLED**
- **USB storage COMPLETELY DISABLED**
- **Wireless adapters DISABLED**
- **Strict firewall (deny all except SSH)**
- **Root login COMPLETELY DISABLED**
- **AIDE integrity monitoring**
- **Comprehensive audit logging**
- **AppArmor enforcing mode**

---

## [PACKAGE] Package Contents

```
stig-airgap-package/
|-- dependencies/                          <- All Python packages (offline)
|   |-- paramiko-*.whl                    (SSH library)
|   |-- cryptography-*.whl                (Crypto backend)
|   |-- bcrypt-*.whl                      (Password hashing)
|   \-- ... (all dependencies)
|
|-- airgap_windows_stig_executor.py       <- Main Windows launcher (MAXIMUM SECURITY)
|-- ubuntu20_stig_v2r3_enhanced.py        <- STIG remediation script
|-- run_airgap_stig.bat                   <- Windows quick launcher
|
|-- download_dependencies.py              <- Run on internet-connected system
|
\-- Documentation/
    |-- README_AIRGAP.md                  (This file)
    |-- AIRGAP_QUICK_START.md             (5-minute guide)
    |-- MAXIMUM_SECURITY_GUIDE.md         (Security details)
    \-- TROUBLESHOOTING_AIRGAP.md         (Common issues)
```

---

## [LAUNCH] Quick Start (Air-Gapped System)

### Prerequisites on Windows:
- Python 3.6+ installed
- This complete package transferred to system
- Network access to target Ubuntu system

### Step 1: Verify Package Contents
```powershell
# Check you have all required files
dir
# Should see: dependencies/, airgap_windows_stig_executor.py, ubuntu20_stig_v2r3_enhanced.py
```

### Step 2: Run the Executor
```powershell
# Option A: Use batch file
run_airgap_stig.bat

# Option B: Direct Python
python airgap_windows_stig_executor.py
```

### Step 3: Follow Interactive Prompts
1. Enter target Ubuntu IP address
2. Enter SSH credentials
3. Enter sudo password
4. **Choose security options:**
   - Disable SSH password auth? [Y/n] <- Default: YES
   - Enable FIPS mode? [y/N] <- Default: NO
   - Strict firewall? [Y/n] <- Default: YES
5. Type 'EXECUTE' to confirm

### Step 4: Wait for Completion (~10 minutes)
- Watch real-time progress
- Script auto-handles all configurations
- Creates automatic backups

### Step 5: Reboot Target System
```powershell
ssh user@target 'sudo reboot'
```

---

## [LIST] Building the Air-Gap Package

### On Internet-Connected System:

#### 1. Download This Package
Get all files from the source system.

#### 2. Download Dependencies
```powershell
python download_dependencies.py
```

This creates the `dependencies/` folder with all required packages (~20-30 MB).

#### 3. Verify Download
```powershell
python dependencies/verify_packages.py
```

#### 4. Package Everything
Create a folder with:
```
stig-airgap-package/
|-- dependencies/ (folder with all .whl files)
|-- airgap_windows_stig_executor.py
|-- ubuntu20_stig_v2r3_enhanced.py
|-- run_airgap_stig.bat
\-- All .md documentation files
```

#### 5. Transfer to Air-Gapped System
- Use approved transfer method (USB, CD/DVD, secure file transfer)
- Verify file integrity after transfer
- Document transfer for compliance

---

## [SECURE] Maximum Security Configuration

### What Gets Locked Down:

#### Authentication:
- [OK] **SSH password auth DISABLED** - Keys only
- [OK] **Root login DISABLED** - No root access via SSH
- [OK] **Strong password policy** - 15 char min, complexity
- [OK] **Account lockout** - 3 failed attempts = locked
- [OK] **Sudo restrictions** - No NOPASSWD, no ALL

#### Network:
- [OK] **Firewall strict mode** - Deny all except SSH
- [OK] **FIPS ciphers only** - Weak ciphers removed
- [OK] **IP forwarding disabled** - Not a router
- [OK] **ICMP restricted** - Minimal response
- [OK] **Kernel hardening** - 59 security parameters

#### Services:
- [OK] **CUPS disabled** - No printing
- [OK] **Bluetooth disabled** - No wireless
- [OK] **Avahi disabled** - No mDNS
- [OK] **USB storage disabled** - No removable media
- [OK] **Wireless disabled** - No WiFi

#### Monitoring:
- [OK] **AppArmor enforcing** - Mandatory access control
- [OK] **AIDE enabled** - File integrity monitoring
- [OK] **Audit logging** - 136 comprehensive rules
- [OK] **All access logged** - Complete audit trail
- [OK] **Immutable audit** - Rules cannot be changed

---

## [WARNING] CRITICAL WARNINGS

### Before Execution:

#### [RED] MUST HAVE:
1. **Console access** (KVM/IPMI/Physical) - SSH will change
2. **SSH keys configured** - Password auth will be disabled
3. **System backup** - VM snapshot or full backup
4. **Tested in dev** - Never run first time in production
5. **Change control** - Documented and approved

#### [RED] AFTER EXECUTION:
1. **Password auth DISABLED** - Must use SSH keys
2. **Root login DISABLED** - Use sudo with regular user
3. **Many services DISABLED** - Only essential services run
4. **USB storage DISABLED** - No removable media
5. **Firewall STRICT** - Must explicitly allow new services

### Expected Impact:

#### [OK] SAFE:
- SSH with keys will work
- Sudo with compliant passwords works
- Essential services continue
- Network connectivity maintained
- System fully functional

#### [WARNING] BROKEN:
- SSH with passwords (disabled)
- Root SSH login (disabled)
- CUPS/printing (disabled)
- Bluetooth (disabled)
- USB storage (disabled)
- Wireless networking (disabled)
- Services not explicitly needed (disabled)

---

## [CONFIG] Configuration Options

### Security Level Options:

The executor asks for these options during setup:

#### 1. Disable SSH Password Authentication [Y/n]
- **YES (default)**: Keys only - MAXIMUM SECURITY
- **NO**: Keep password auth - Less secure but easier

#### 2. Enable FIPS Mode [y/N]
- **NO (default)**: Standard crypto - Works on all systems
- **YES**: FIPS 140-2 - Requires FIPS-enabled kernel

#### 3. Strict Firewall [Y/n]
- **YES (default)**: Deny all except SSH - MAXIMUM SECURITY
- **NO**: Basic firewall - Allow common services

### Recommendation:
- **Development/Testing**: Answer NO to all (less disruptive)
- **Production/Classified**: Answer YES to all (maximum security)

---

## [CHART] Compliance Results

### Expected SCAP Scan Results:

After execution and reboot:
- **90-100% automated controls**: PASS
- **Manual controls**: Require documentation
- **N/A controls**: Not applicable to configuration

### Controls Applied:

#### CAT I (High - 14 controls):
- SSH hardening
- Remove null passwords
- Lock blank password accounts
- PKI authentication support
- Disable root login

#### CAT II (Medium - 136 controls):
- Password quality (15+ chars, complexity)
- Account lockout (3 attempts)
- 59 kernel security parameters
- 136 audit rules
- SSH cipher restrictions
- Firewall configuration
- Service hardening
- USB/Wireless restrictions
- Sudo restrictions
- File permissions
- Login banners
- Session timeouts
- AppArmor enforcement
- AIDE integrity monitoring

#### CAT III (Low - 22 controls):
- Additional file permissions
- System documentation

---

## Rollback Procedures

### If SSH Access Lost:

#### Option 1: Console Access
```bash
# Use KVM/IPMI/Physical console

# Restore SSH config
sudo cp /var/backups/pre-stig-*/sshd_config /etc/ssh/
sudo systemctl restart sshd

# Temporarily enable password auth if needed
sudo sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
sudo systemctl restart sshd
```

#### Option 2: Recovery Mode
```bash
# Boot to recovery mode
# Mount filesystem
# Restore from backup

BACKUP=$(ls -dt /var/backups/pre-stig-* | head -1)
cp $BACKUP/sshd_config /etc/ssh/
systemctl restart sshd
```

### Full System Restore:

```bash
# Find latest backup
BACKUP=$(ls -dt /var/backups/pre-stig-* | head -1)

# Restore critical configs
sudo cp -r $BACKUP/sshd_config /etc/ssh/
sudo cp -r $BACKUP/pam.d/* /etc/pam.d/
sudo cp -r $BACKUP/security/* /etc/security/
sudo cp $BACKUP/sudoers /etc/
sudo cp $BACKUP/login.defs /etc/

# Restart services
sudo systemctl restart sshd
sudo systemctl restart auditd
```

---

## [WARNING] Troubleshooting

### Common Issues:

#### "Dependencies not found"
```
SOLUTION:
1. Verify 'dependencies' folder exists in same directory
2. Check folder contains .whl files
3. Run: python dependencies/verify_packages.py
```

#### "paramiko not installed"
```
SOLUTION:
The script will auto-install from dependencies folder.
If it fails:
1. Check dependencies folder contains paramiko*.whl
2. Manual install: pip install --no-index --find-links=dependencies paramiko
```

#### "Cannot connect to target"
```
SOLUTION:
1. Verify target IP address is correct
2. Check network connectivity: ping target_ip
3. Verify SSH is running: ssh user@target_ip (test manually)
4. Check firewall allows SSH port 22
```

#### "Authentication failed"
```
SOLUTION:
1. Verify username is correct
2. Verify password is correct
3. Test manually: ssh user@target_ip
4. Check user has sudo: ssh user@target_ip 'sudo whoami'
```

#### "Cannot SSH after execution"
```
SOLUTION:
1. USE CONSOLE ACCESS (KVM/IPMI/Physical)
2. Restore SSH config:
   sudo cp /var/backups/pre-stig-*/sshd_config /etc/ssh/
   sudo systemctl restart sshd
3. Set up SSH keys if password auth disabled
```

#### "System unbootable after execution"
```
SOLUTION:
1. Boot to recovery mode
2. Mount filesystem
3. Restore GRUB config:
   sudo cp /var/backups/pre-stig-*/grub /etc/default/
   sudo update-grub
4. Reboot
```

---

## [NOTE] Post-Execution Checklist

### Immediate (Before Reboot):
- [ ] Review execution log for errors
- [ ] Verify SSH still works
- [ ] Test sudo access
- [ ] Note backup locations

### After Reboot:
- [ ] **Reboot system**: `sudo reboot`
- [ ] Verify SSH access (with keys if password auth disabled)
- [ ] Check critical services:
  ```bash
  sudo systemctl status sshd
  sudo systemctl status auditd
  sudo systemctl status rsyslog
  sudo systemctl status ufw
  ```
- [ ] Verify firewall: `sudo ufw status verbose`
- [ ] Test sudo: `sudo whoami`
- [ ] Check audit logs: `sudo ausearch -ts today`

### Validation:
- [ ] Run SCAP scan
- [ ] Review compliance results
- [ ] Document findings
- [ ] Create Exception/Risk documents for remaining issues

### Documentation:
- [ ] Update system documentation
- [ ] Record SCAP results
- [ ] Document exceptions
- [ ] Update change control
- [ ] Archive logs

---

## [SEARCH] Verification & Scanning

### OpenSCAP Scanning:

```bash
# Install OpenSCAP
sudo apt-get install libopenscap8 ssg-debian

# Run SCAP scan
sudo oscap xccdf eval \
  --profile xccdf_org.ssgproject.content_profile_stig \
  --results scan-results.xml \
  --report scan-report.html \
  /usr/share/xml/scap/ssg/content/ssg-ubuntu2004-ds.xml

# View results
firefox scan-report.html
```

### Expected Results:
- **Pass**: 90-100% of automated controls
- **Fail**: Some manual controls requiring documentation
- **N/A**: Controls not applicable to configuration

---

## [LOCKED] Security Compliance

### Regulatory Alignment:

This configuration helps meet:
- **NIST 800-53** - Security controls
- **DISA STIG** - 172 controls (V2R3)
- **PCI-DSS** - Payment card security
- **FedRAMP** - Federal cloud security
- **FISMA** - Federal information security

### Audit Trail:

All actions logged:
- **Windows log**: `%USERPROFILE%\stig_execution_logs\`
- **Ubuntu log**: `/var/log/ubuntu20-stig-v2r3-remediation.log`
- **Audit log**: `/var/log/audit/audit.log`
- **Backups**: `/var/backups/pre-stig-*`

---

## [IDEA] Best Practices

### For Air-Gapped Environments:

1. **Verify package integrity**
   - Hash check after transfer
   - Scan for malware if required
   - Document chain of custody

2. **Test before production**
   - Use dev/test system first
   - Verify all applications work
   - Test rollback procedures

3. **Have recovery ready**
   - Console access available
   - Backup media on-site
   - Recovery procedures documented

4. **Document everything**
   - Transfer manifests
   - Change control records
   - Exception documentation
   - Compliance reports

### For Maximum Security:

1. **Use SSH keys**
   - Generate strong keys (4096-bit RSA or Ed25519)
   - Protect private keys
   - Rotate regularly

2. **Monitor continuously**
   - Review audit logs daily
   - Check for anomalies
   - Respond to alerts

3. **Update regularly**
   - Apply security patches
   - Update STIG script
   - Re-scan quarterly

4. **Maintain compliance**
   - Regular SCAP scans
   - Document exceptions
   - Review controls annually

---

## Support Resources

### Included Documentation:
- `README_AIRGAP.md` - This file (comprehensive guide)
- `AIRGAP_QUICK_START.md` - 5-minute quick start
- `MAXIMUM_SECURITY_GUIDE.md` - Security configuration details
- `TROUBLESHOOTING_AIRGAP.md` - Common issues and solutions

### External Resources:
- DISA STIG Library: https://public.cyber.mil/stigs/
- Ubuntu Security: https://ubuntu.com/security
- OpenSCAP: https://www.open-scap.org/

### Log Files:
- Windows execution: `%USERPROFILE%\stig_execution_logs\`
- Ubuntu remediation: `/var/log/ubuntu20-stig-v2r3-remediation.log`
- SSH logs: `/var/log/auth.log`
- Audit logs: `/var/log/audit/audit.log`

---

## License & Disclaimer

**License**: MIT License

**Disclaimer**: This script is provided as-is without warranty. Test thoroughly in non-production environments. The authors are not responsible for any system damage, data loss, or security incidents. Compliance must be verified through proper SCAP scanning and validation.

**Not Affiliated**: Not officially affiliated with DISA, DoD, or Canonical.

---

## [CHART] Quick Reference

### Files You Need:
```
[OK] dependencies/ (folder)
[OK] airgap_windows_stig_executor.py
[OK] ubuntu20_stig_v2r3_enhanced.py
[OK] run_airgap_stig.bat (optional)
```

### Quick Commands:
```powershell
# Run executor
python airgap_windows_stig_executor.py

# Or use batch file
run_airgap_stig.bat

# Verify dependencies
python dependencies/verify_packages.py

# View logs
notepad %USERPROFILE%\stig_execution_logs\stig_execution_*.log
```

### Emergency Recovery:
```bash
# Use console access
sudo cp /var/backups/pre-stig-*/sshd_config /etc/ssh/
sudo systemctl restart sshd
```

---

**Version**: 2.0.0-airgap  
**STIG**: V2R3 (Release 3, July 2025)  
**Controls**: 172 total (14 CAT I, 136 CAT II, 22 CAT III)  
**Mode**: Maximum Security Lockdown  

**[SECURE] Secure your air-gapped systems with confidence!**

---

## [TARGET] Success Criteria

Your STIG remediation is successful when:

[OK] Script completes without critical errors  
[OK] System reboots successfully  
[OK] SSH access works (with keys in max security mode)  
[OK] All critical services running  
[OK] SCAP scan shows 90-100% compliance  
[OK] Audit logs being generated  
[OK] Firewall active and configured  
[OK] Applications function correctly  
[OK] No unexpected access issues  
[OK] Documentation complete  

**Remember**: Maximum security means maximum restrictions. Plan accordingly!
