# Windows-to-Ubuntu STIG Remote Executor

Execute Ubuntu 20.04 DISA STIG V2R3 compliance remediation from your Windows workstation to a remote Ubuntu server.

## [TARGET] Overview

This tool allows you to:
- Run STIG remediation from Windows to Ubuntu 20.04 systems
- Automatically handle SSH and sudo password authentication
- Apply 172 STIG controls (14 CAT I, 136 CAT II, 22 CAT III)
- Achieve near 100% STIG compliance automatically
- Monitor real-time execution progress
- Create automatic backups before changes

## [WARNING] CRITICAL WARNINGS

**BEFORE YOU BEGIN:**

1. **[RED] This makes MAJOR security changes to your Ubuntu system**
2. **[RED] ALWAYS test in a non-production environment first**
3. **[RED] Have console access ready - SSH config will change**
4. **[RED] Create VM snapshot or system backup before running**
5. **[RED] Some services may be disabled (Bluetooth, CUPS, Avahi, etc.)**
6. **[RED] Password policies will be enforced immediately**

**AFTER EXECUTION:**
- SSH root login will be DISABLED
- SSH password authentication may be DISABLED  
- System MUST be rebooted to complete
- Passwords must meet complexity requirements

## [LIST] Prerequisites

### On Windows (your workstation):
```powershell
# Python 3.6 or higher required
python --version

# Install required packages
pip install paramiko scp
```

### On Ubuntu Target (20.04 LTS):
- Ubuntu 20.04 LTS (verified)
- SSH server enabled and accessible
- User account with sudo privileges
- Minimum 500 MB free disk space
- Network connectivity

## [LAUNCH] Quick Start

### Option 1: Automated (Recommended for beginners)

1. **Download all files:**
   - `windows_stig_remote_executor.py`
   - `ubuntu20_stig_v2r3_enhanced.py` (the original STIG script)
   - `run_stig.bat` (optional Windows batch file)

2. **Place both Python files in the same directory**

3. **Double-click `run_stig.bat`** or run in PowerShell:
   ```powershell
   python windows_stig_remote_executor.py
   ```

4. **Follow the interactive prompts:**
   - Enter target Ubuntu IP address
   - Enter SSH port (default: 22)
   - Enter SSH username (default: ubuntu)
   - Enter SSH password
   - Enter sudo password (can be same as SSH)
   - Confirm execution

### Option 2: Command Line (Advanced)

```powershell
# Navigate to script directory
cd C:\Path\To\STIG\Scripts

# Verify both scripts are present
dir *.py

# Run executor
python windows_stig_remote_executor.py
```

##  Detailed Setup Instructions

### Step 1: Install Python on Windows

If you don't have Python installed:

1. Download Python from: https://www.python.org/downloads/
2. Run installer - **CHECK "Add Python to PATH"**
3. Verify installation:
   ```powershell
   python --version
   pip --version
   ```

### Step 2: Install Required Python Packages

Open PowerShell or Command Prompt as Administrator:

```powershell
# Install paramiko for SSH
pip install paramiko

# Install scp for file transfer (optional but recommended)
pip install scp

# Verify installation
python -c "import paramiko; print('Paramiko OK')"
```

### Step 3: Prepare Target System Info

Gather this information about your Ubuntu target:

- **IP Address or Hostname:** `192.168.1.100` (example)
- **SSH Port:** Usually `22`
- **Username:** User with sudo privileges (e.g., `ubuntu`, `admin`)
- **SSH Password:** Password for that user
- **Sudo Password:** Usually same as SSH password

**Test connectivity first:**
```powershell
# Test SSH connectivity from Windows
ssh username@192.168.1.100
```

### Step 4: Prepare for Execution

**IMPORTANT:** Before running:

1. **Create backup/snapshot of target system**
   - VMware: Create VM snapshot
   - Physical: Ensure recent backup exists

2. **Verify console access**
   - Have KVM/IPMI access ready
   - Have physical access if needed
   - SSH config will change!

3. **Test in non-production first**
   - Never run on production without testing
   - Verify application compatibility

4. **Document current state**
   - Note current users
   - Note current services
   - Note current firewall rules

### Step 5: Execute STIG Remediation

Run the script:

```powershell
python windows_stig_remote_executor.py
```

**Interactive prompts will ask for:**

1. Target Ubuntu system IP/hostname
2. SSH port (press Enter for 22)
3. SSH username (press Enter for 'ubuntu')
4. SSH password (hidden input)
5. Sudo password (can use same as SSH)
6. Confirmation to proceed
7. Final confirmation by typing 'EXECUTE'

**Execution will:**

1. Connect to target via SSH
2. Verify sudo access
3. Check OS version (Ubuntu 20.04)
4. Transfer STIG script
5. Install dependencies
6. Create backup
7. Execute STIG remediation (5-15 minutes)
8. Show real-time progress
9. Perform post-execution checks
10. Display summary and next steps

## [CHART] What Gets Changed

### Category I (High - 14 controls)
- [OK] SSH hardening (root login, password auth)
- [OK] PAM password hashing (SHA512)
- [OK] Remove null password support
- [OK] Lock blank password accounts
- [OK] Remove insecure packages (telnet, rsh)

### Category II (Medium - 136 controls)
- [OK] Password quality requirements (15 char min, complexity)
- [OK] Account lockout policies (3 failed attempts)
- [OK] Kernel security parameters (59 settings)
- [OK] Comprehensive audit rules (136 rules)
- [OK] SSH cipher restrictions (FIPS-validated)
- [OK] Firewall configuration (UFW enabled)
- [OK] Service hardening (disable unnecessary services)
- [OK] USB storage restrictions
- [OK] Wireless adapter disabling
- [OK] Sudo restrictions (no NOPASSWD, no ALL)
- [OK] File permissions (passwd, shadow, etc.)
- [OK] Login banners
- [OK] Session timeouts
- [OK] AppArmor enforcement
- [OK] AIDE integrity checking

### Category III (Low - 22 controls)
- [OK] Additional file permissions
- [OK] System documentation

## [FOLDER] Files Created/Modified

### On Windows (local):
- `stig_execution_logs/stig_execution_YYYYMMDD_HHMMSS.log` - Detailed execution log

### On Ubuntu Target:
**Backups created in:**
- `/var/backups/pre-stig-YYYYMMDD_HHMMSS/` - Pre-execution backup
- `/var/backups/stig-v2r3/` - Configuration backups
- Individual files: `*.stig-v2r3-backup-*`

**Main configuration files modified:**
- `/etc/ssh/sshd_config` - SSH hardening
- `/etc/pam.d/*` - PAM configuration
- `/etc/security/pwquality.conf` - Password quality
- `/etc/security/faillock.conf` - Account lockout
- `/etc/login.defs` - Login defaults
- `/etc/sysctl.d/99-stig-v2r3.conf` - Kernel parameters
- `/etc/audit/auditd.conf` - Audit daemon
- `/etc/audit/rules.d/stig-v2r3.rules` - Audit rules
- `/etc/sudoers*` - Sudo restrictions
- `/etc/default/grub` - Boot parameters
- `/etc/issue`, `/etc/issue.net` - Login banners

**Logs:**
- `/var/log/ubuntu20-stig-v2r3-remediation.log` - Script execution log

## [CONFIG] Troubleshooting

### Connection Issues

**Error: "Authentication failed"**
```
Solution: Verify username/password are correct
Test: ssh username@target_ip
```

**Error: "Connection refused"**
```
Solution: Verify SSH service is running on target
Test: telnet target_ip 22
Check: sudo systemctl status sshd (on target)
```

**Error: "Network unreachable"**
```
Solution: Check network connectivity
Test: ping target_ip
Check: Firewall rules on both Windows and Ubuntu
```

### Execution Issues

**Error: "Sudo access verification failed"**
```
Solution: Verify sudo password is correct
Test: ssh username@target_ip 'sudo whoami'
Check: User is in sudo group
```

**Error: "STIG script not found"**
```
Solution: Ensure both .py files in same directory
Check: dir *.py (should show both scripts)
```

**Error: "Paramiko not installed"**
```
Solution: Install paramiko
Run: pip install paramiko scp
```

### Post-Execution Issues

**Can't SSH after remediation:**
```
1. Use console access (KVM/physical)
2. Restore SSH config from backup:
   sudo cp /var/backups/pre-stig-*/sshd_config /etc/ssh/sshd_config
   sudo systemctl restart sshd
3. Check SSH logs:
   sudo tail -f /var/log/auth.log
```

**Password doesn't meet requirements:**
```
New requirements:
- Minimum 15 characters
- At least 1 digit
- At least 1 uppercase letter  
- At least 1 lowercase letter
- At least 1 special character
- Max 3 consecutive same characters
```

**Services not working:**
```
Check which services were disabled:
sudo systemctl list-unit-files | grep disabled

Re-enable if needed:
sudo systemctl enable service_name
sudo systemctl start service_name
```

##  Rollback Procedures

### Automatic Rollback

The script creates backups automatically. If something fails:

**Restore SSH configuration:**
```bash
# Find latest backup
ls -lt /var/backups/pre-stig-*

# Restore SSH config
sudo cp /var/backups/pre-stig-YYYYMMDD_HHMMSS/sshd_config /etc/ssh/
sudo systemctl restart sshd
```

**Restore PAM configuration:**
```bash
sudo cp /var/backups/pre-stig-*/pam.d/* /etc/pam.d/
```

**Restore all configurations:**
```bash
# Find backup directory
BACKUP_DIR="/var/backups/pre-stig-YYYYMMDD_HHMMSS"

# Restore SSH
sudo cp $BACKUP_DIR/sshd_config /etc/ssh/
sudo systemctl restart sshd

# Restore PAM
sudo cp -r $BACKUP_DIR/pam.d/* /etc/pam.d/

# Restore security
sudo cp -r $BACKUP_DIR/security/* /etc/security/

# Restore sudoers
sudo cp $BACKUP_DIR/sudoers /etc/

# Restore login.defs
sudo cp $BACKUP_DIR/login.defs /etc/
```

### Emergency Recovery

If system is inaccessible:

1. **Boot to recovery mode** or use console access
2. **Mount filesystem** (if recovery mode)
3. **Restore from backup:**
   ```bash
   cd /var/backups
   ls -lt pre-stig-*
   
   # Copy most recent backup
   BACKUP="/var/backups/pre-stig-LATEST"
   cp $BACKUP/sshd_config /etc/ssh/
   systemctl restart sshd
   ```
4. **Test SSH access**

## [LIST] Post-Execution Checklist

After successful execution:

### Immediate (Before Reboot):
- [ ] Review execution log for errors
- [ ] Verify SSH still works
- [ ] Test sudo access
- [ ] Check critical services are running

### After Reboot:
- [ ] **Reboot the system:** `sudo reboot`
- [ ] Verify SSH access works
- [ ] Test sudo with new password policies
- [ ] Check all required services are running:
  ```bash
  sudo systemctl status sshd
  sudo systemctl status auditd  
  sudo systemctl status rsyslog
  sudo systemctl status ufw
  ```
- [ ] Verify firewall rules: `sudo ufw status`
- [ ] Test application functionality
- [ ] Update user passwords if needed

### Validation:
- [ ] Run OpenSCAP SCAP scan
- [ ] Review SCAP scan results
- [ ] Document any remaining findings
- [ ] Address findings or accept as risk

### Documentation:
- [ ] Document changes made
- [ ] Update system documentation
- [ ] Note backup locations
- [ ] Record SCAP scan results
- [ ] Update change control records

## [SEARCH] Verification & Compliance Scanning

### OpenSCAP Scanning

Install OpenSCAP:
```bash
sudo apt-get install libopenscap8 ssg-debian
```

Run SCAP scan:
```bash
sudo oscap xccdf eval \
  --profile xccdf_org.ssgproject.content_profile_stig \
  --results scan-results.xml \
  --report scan-report.html \
  /usr/share/xml/scap/ssg/content/ssg-ubuntu2004-ds.xml
```

View results:
```bash
# Open HTML report in browser
firefox scan-report.html
```

### DISA SCC (SCAP Compliance Checker)

1. Download SCC from: https://public.cyber.mil/stigs/scap/
2. Install on target or scan remotely
3. Select "STIG" benchmark
4. Run scan
5. Review findings

### Expected Results

After remediation, you should see:
- **90-100%** STIG compliance (automated controls)
- **Some manual findings** (require documentation/configuration)
- **Possible exceptions** for:
  - FIPS mode (requires special kernel)
  - PKI/CAC authentication (requires infrastructure)
  - Some organizational policies

## [LEARN] Understanding the Changes

### Password Policy Changes

**Old:** Weak passwords allowed
**New:** Strong password requirements:
- 15 character minimum
- Complexity enforced (digit, upper, lower, special)
- Dictionary words blocked
- 8 character difference from old password
- Max 3 consecutive same characters

**Impact:** Users must change passwords to comply

### SSH Hardening

**Old:** Root login allowed, weak ciphers
**New:** 
- Root login disabled
- Password auth may be disabled (key-based only)
- FIPS-validated ciphers only
- Key exchange algorithms restricted
- Idle timeout enforced (10 minutes)

**Impact:** Alternative access methods required

### Account Lockout

**Old:** Unlimited login attempts
**New:** 
- 3 failed attempts = locked
- 15 minute lockout period
- Administrator unlock required

**Impact:** User training needed

### Audit Logging

**Old:** Minimal logging
**New:** Comprehensive audit trail:
- All file access tracked
- All command execution logged
- Security events captured
- Immutable audit rules

**Impact:** Increased log storage needs

### Firewall

**Old:** Firewall disabled or permissive
**New:**
- UFW enabled
- Default deny incoming
- Only SSH allowed
- Logging enabled

**Impact:** Explicitly allow required services

## [IDEA] Tips & Best Practices

### For Testing:
1. Use VM snapshots for quick rollback
2. Test in isolated network first
3. Document baseline before changes
4. Compare before/after configurations

### For Production:
1. Schedule during maintenance window
2. Have multiple administrators ready
3. Keep console access available
4. Test rollback procedures beforehand
5. Notify users of password changes

### For Ongoing Compliance:
1. Run monthly SCAP scans
2. Monitor audit logs regularly
3. Review firewall rules quarterly
4. Update STIG script as new versions release
5. Document exceptions with risk acceptance

##  Support & Resources

### DISA STIG Resources:
- STIG Library: https://public.cyber.mil/stigs/
- Ubuntu 20.04 STIG: Search for "Ubuntu 20.04 LTS STIG"
- SCAP Content: https://public.cyber.mil/stigs/scap/

### OpenSCAP Resources:
- Documentation: https://www.open-scap.org/
- Ubuntu Guide: https://ubuntu.com/security/certifications/docs/usg

### Community:
- DISA STIGs Discussion: https://public.cyber.mil/
- Ubuntu Security: https://ubuntu.com/security

## [FILE] License & Disclaimer

**License:** MIT License

**Disclaimer:** 
This script is provided as-is without warranty. The authors and contributors are not responsible for any damage or data loss caused by using this script. Always test in non-production environments first. This script implements DISA STIG controls but compliance must be verified through proper SCAP scanning and validation processes.

**Not Affiliated:** This tool is not officially affiliated with DISA, DoD, or Canonical. It is an independent implementation of publicly available STIG requirements.

## [NOTE] Version History

### v1.0.0 (Current)
- Initial Windows remote executor
- Automatic password handling
- Real-time progress streaming
- Comprehensive error handling
- Automatic backups
- Post-execution validation

### Planned Features:
- Multiple host support
- Parallel execution
- Dry-run mode from Windows
- Configuration presets
- Compliance reporting
- Automated rollback testing

##  Contributing

Found a bug? Have a suggestion? Contributions are welcome!

Areas for improvement:
- Additional safety checks
- Better error messages
- More granular control options
- Additional platform support
- Enhanced reporting

## [FAST] Quick Reference Commands

```powershell
# Install dependencies
pip install paramiko scp

# Run executor
python windows_stig_remote_executor.py

# View logs
notepad %USERPROFILE%\stig_execution_logs\stig_execution_*.log

# Test SSH connection
ssh username@target_ip

# Check Python version
python --version
```

## [TARGET] Success Criteria

Your STIG remediation is successful when:

[OK] Script completes without critical errors  
[OK] System reboots successfully  
[OK] SSH access still works (with new restrictions)  
[OK] Critical services are running  
[OK] SCAP scan shows 90%+ compliance  
[OK] Users can login with compliant passwords  
[OK] Audit logs are being generated  
[OK] Firewall is active and configured  
[OK] Applications still function correctly  

---

**Remember:** Security is a journey, not a destination. Regular scanning, monitoring, and updates are essential for maintaining compliance.

**Good luck with your STIG compliance journey! [SHIELD]**
