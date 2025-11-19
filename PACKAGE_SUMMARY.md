# Windows-to-Ubuntu STIG Remote Executor - Complete Package

## [PACKAGE] What You've Received

This package enables you to execute Ubuntu 20.04 DISA STIG V2R3 compliance remediation **from your Windows workstation** to a remote Ubuntu server.

### Package Contents:

1. **windows_stig_remote_executor.py** (24 KB)
   - Main Windows launcher script
   - Handles SSH connection with password auth
   - Automatically handles sudo password prompts
   - Transfers STIG script to target
   - Shows real-time execution progress
   - Creates automatic backups

2. **run_stig.bat** (5.7 KB)
   - Windows batch file for easy launching
   - Checks prerequisites automatically
   - Offers to install missing packages
   - User-friendly interface

3. **README_WINDOWS_EXECUTOR.md** (16 KB)
   - Comprehensive documentation
   - Detailed setup instructions
   - Troubleshooting guide
   - Post-execution procedures
   - Rollback instructions

4. **QUICK_START.md** (3.8 KB)
   - 5-minute quick setup guide
   - Essential commands
   - Quick troubleshooting
   - Checklists

5. **IMPORTANT_STIG_SCRIPT_NOTE.md**
   - Information about the required STIG script
   - How to locate your script file

## [TARGET] What This Does

### Before (Manual):
- SSH into Ubuntu server
- Manually run commands
- Handle sudo prompts manually
- Monitor progress manually
- Risk losing SSH access if config breaks

### After (Automated):
- Run from your Windows PC
- One command execution
- Automatic password handling
- Real-time progress monitoring
- Automatic backups before changes
- Post-execution validation

## [LAUNCH] Quick Start (3 Steps)

### Step 1: Install Python (if not installed)
```powershell
# Download from https://www.python.org/downloads/
# Install with "Add to PATH" checked
python --version  # Verify
```

### Step 2: Install Required Package
```powershell
pip install paramiko scp
```

### Step 3: Run the Script
```powershell
# Place your STIG script (ubuntu20_stig_v2r3_enhanced.py) in same folder
python windows_stig_remote_executor.py

# OR just double-click
run_stig.bat
```

## [LIST] Prerequisites Checklist

### On Your Windows PC:
- [ ] Windows 10/11 (or Windows Server)
- [ ] Python 3.6 or higher installed
- [ ] paramiko package installed (`pip install paramiko`)
- [ ] Network connectivity to target Ubuntu system

### On Target Ubuntu System:
- [ ] Ubuntu 20.04 LTS
- [ ] SSH server running and accessible
- [ ] User account with sudo privileges
- [ ] Minimum 500 MB free disk space
- [ ] Console access available (KVM/physical)

### Before Execution:
- [ ] Backup/snapshot of Ubuntu system created
- [ ] Tested in non-production environment first
- [ ] Have console access ready (in case SSH breaks)
- [ ] Both Python scripts in same folder
- [ ] SSH credentials ready (username/password)
- [ ] Sudo password ready

## [FAST] What Gets Applied

The script applies **172 STIG controls** to achieve near 100% compliance:

### [RED] CAT I (High - 14 controls):
- SSH hardening (disable root login, password auth restrictions)
- Remove null password support
- Lock accounts with blank passwords
- Remove insecure packages (telnet, rsh-server)
- PAM SHA512 password hashing
- PKI authentication support

###  CAT II (Medium - 136 controls):
- Password quality (15 char min, complexity requirements)
- Account lockout (3 failed attempts = locked)
- 59 kernel security parameters (network, memory, security)
- Comprehensive audit rules (136 audit rules)
- SSH cipher restrictions (FIPS-validated only)
- Firewall configuration (UFW enabled, deny all incoming)
- Disable unnecessary services (cups, bluetooth, avahi, etc.)
- USB storage restrictions (NEW in V2R3)
- Wireless adapter disabling (NEW in V2R3)
- Sudo restrictions - no NOPASSWD, no ALL (NEW in V2R3)
- File permissions hardening
- Login banners
- Session timeouts (10 minutes)
- AppArmor enforcement
- AIDE file integrity monitoring
- Cron execution auditing (NEW in V2R3)

###  CAT III (Low - 22 controls):
- Additional file permission restrictions
- System documentation

## [SECURE] Security Changes Made

### Authentication:
- **Passwords:** 15 char minimum, complexity required
- **Lockout:** 3 failed attempts = locked for 15 minutes
- **SSH:** Root login disabled, weak ciphers removed
- **Sudo:** NOPASSWD removed, ALL usage restricted
- **Accounts:** Blank passwords locked immediately

### Network:
- **Firewall:** UFW enabled, default deny incoming
- **SSH:** FIPS ciphers only, idle timeout enforced
- **Kernel:** 59 security parameters hardened
- **Wireless:** Disabled (can be configured)
- **USB:** Storage auto-mount disabled

### Logging & Auditing:
- **Audit:** 136 comprehensive audit rules
- **Events:** All security events logged
- **Files:** File access tracked
- **Commands:** All command execution logged
- **Immutable:** Audit rules cannot be changed at runtime

### System Hardening:
- **AppArmor:** Enforcing mode on all profiles
- **AIDE:** File integrity monitoring configured
- **Services:** Unnecessary services disabled
- **GRUB:** Audit enabled at boot
- **Kernel:** Address space randomization (ASLR)

## [WARNING] Important Warnings

### SSH Access:
- **Root login will be DISABLED**
- **Password authentication may be DISABLED**
- **HAVE CONSOLE ACCESS READY!**
- Test with regular user account first

### Password Changes Required:
- **Users must change passwords** if they don't meet requirements
- **15 character minimum** with complexity
- **No dictionary words** allowed
- **8 characters must differ** from old password

### Services Affected:
- Bluetooth - Disabled
- CUPS (printing) - Disabled
- Avahi (mDNS) - Disabled
- Wireless - Disabled (configurable)
- USB storage - Disabled (configurable)

### System Must Reboot:
- **Reboot required** after execution
- Some kernel parameters need reboot
- GRUB changes need reboot
- Service changes finalized on reboot

## [CHART] Expected Results

After successful execution:

### Compliance:
- **90-100% STIG compliance** (automated controls)
- **SCAP scan** should show high compliance
- **Manual findings** may require documentation

### System State:
- **SSH hardened** but still accessible
- **Firewall active** with SSH allowed
- **Audit logging** comprehensive
- **Services restricted** to required only
- **Passwords enforced** with complexity

### What To Test:
- SSH access (may require keys instead of passwords)
- Critical application functionality
- User login with compliant passwords
- Required services running
- Firewall not blocking needed ports

## Rollback Procedures

If something goes wrong:

### Automatic Backups Created:
```
/var/backups/pre-stig-YYYYMMDD_HHMMSS/  <- Pre-execution backup
/var/backups/stig-v2r3/                  <- Configuration backups
*.stig-v2r3-backup-*                     <- Individual file backups
```

### Quick Restore (SSH broken):
```bash
# Use console access
sudo cp /var/backups/pre-stig-*/sshd_config /etc/ssh/
sudo systemctl restart sshd
```

### Full Restore:
```bash
# Find latest backup
BACKUP=$(ls -dt /var/backups/pre-stig-* | head -1)

# Restore all
sudo cp -r $BACKUP/sshd_config /etc/ssh/
sudo cp -r $BACKUP/pam.d/* /etc/pam.d/
sudo cp -r $BACKUP/security/* /etc/security/
sudo cp $BACKUP/sudoers /etc/
sudo systemctl restart sshd
```

## Documentation Files

### Start Here:
1. **QUICK_START.md** - 5-minute setup guide
2. **README_WINDOWS_EXECUTOR.md** - Comprehensive guide

### During Execution:
- Watch real-time progress in terminal
- Log file created: `%USERPROFILE%\stig_execution_logs\`

### After Execution:
- Review log file for any errors
- Check `/var/log/ubuntu20-stig-v2r3-remediation.log` on Ubuntu
- Run SCAP scan to verify compliance

## [LEARN] Learning Resources

### DISA STIG:
- STIG Library: https://public.cyber.mil/stigs/
- Ubuntu 20.04 STIG V2R3 Documentation
- SCAP Content: https://public.cyber.mil/stigs/scap/

### OpenSCAP:
- Documentation: https://www.open-scap.org/
- Ubuntu Security: https://ubuntu.com/security

### Compliance:
- NIST 800-53 Mappings
- CIS Benchmarks
- PCI-DSS Requirements

## [IDEA] Pro Tips

### For Testing:
1. Use VM snapshots for instant rollback
2. Test SSH access before AND after
3. Document baseline configuration
4. Take screenshots of current state

### For Production:
1. Schedule during maintenance window
2. Have multiple admins available
3. Keep console/KVM access ready
4. Notify users of password policy changes
5. Test application compatibility first

### For Ongoing Compliance:
1. Run monthly SCAP scans
2. Monitor audit logs weekly
3. Review firewall rules quarterly
4. Update STIG script when new versions release
5. Document all exceptions with risk acceptance

## [WARNING] Getting Help

### Check First:
1. **Logs:** `%USERPROFILE%\stig_execution_logs\` (Windows)
2. **Logs:** `/var/log/ubuntu20-stig-v2r3-remediation.log` (Ubuntu)
3. **README:** Full documentation in README_WINDOWS_EXECUTOR.md

### Common Issues:
- **Can't connect:** Check SSH service, firewall rules
- **Authentication failed:** Verify credentials work with `ssh` command
- **Sudo failed:** Verify user has sudo privileges
- **Script not found:** Both .py files must be in same directory

### Emergency:
- **SSH broken:** Use console access, restore from backup
- **System unbootable:** Boot recovery mode, restore GRUB config
- **Services down:** Check service status, restore from backup

## [TARGET] Success Checklist

Your STIG remediation is successful when:

[OK] Script completes without critical errors  
[OK] System reboots successfully  
[OK] SSH access works (possibly with new restrictions)  
[OK] Critical services running (sshd, auditd, rsyslog, ufw)  
[OK] SCAP scan shows 90%+ compliance  
[OK] Users can login (with compliant passwords)  
[OK] Audit logs being generated  
[OK] Firewall active and configured  
[OK] Applications function correctly  
[OK] No unexpected service disruptions  

## [NOTE] Next Steps After Successful Execution

1. **Immediate (before reboot):**
   - Review execution log for errors
   - Verify SSH still works
   - Test sudo access

2. **Reboot system:**
   ```powershell
   ssh user@target 'sudo reboot'
   ```

3. **After reboot:**
   - Verify SSH access
   - Check all services running
   - Test critical applications
   - Verify firewall configuration

4. **Validation:**
   - Run OpenSCAP SCAP scan
   - Review compliance results
   - Document remaining findings
   - Address or accept risks

5. **Documentation:**
   - Update system documentation
   - Record SCAP results
   - Document any exceptions
   - Update change control records

## You're Ready!

You now have everything needed to:
- [OK] Run STIG remediation from Windows
- [OK] Automatically handle passwords
- [OK] Monitor real-time progress
- [OK] Achieve near 100% compliance
- [OK] Rollback if needed
- [OK] Validate with SCAP scanning

**Remember:** Always test in non-production first!

---

## [FOLDER] Package File Summary

```
windows-stig-package/
|-- windows_stig_remote_executor.py    (24 KB) - Main executor
|-- run_stig.bat                       (5.7 KB) - Windows launcher
|-- README_WINDOWS_EXECUTOR.md         (16 KB) - Full docs
|-- QUICK_START.md                     (3.8 KB) - Quick guide
|-- IMPORTANT_STIG_SCRIPT_NOTE.md      - Script location info
\-- PACKAGE_SUMMARY.md                 (THIS FILE) - Overview

REQUIRED (you already have this):
\-- ubuntu20_stig_v2r3_enhanced.py     (~100 KB) - STIG script
```

---

**Version:** 1.0.0  
**Created:** November 2024  
**STIG Version:** V2R3 (Release 3, July 2025)  
**Controls:** 172 total (14 CAT I, 136 CAT II, 22 CAT III)  

**[SHIELD] Secure your Ubuntu systems with confidence!**
