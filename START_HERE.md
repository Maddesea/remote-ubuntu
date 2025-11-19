# [LAUNCH] START HERE - Windows STIG Remote Executor

## [FAST] What This Is

Execute Ubuntu 20.04 DISA STIG V2R3 compliance (172 security controls) from your Windows PC to a remote Ubuntu server.

**Result:** Near 100% STIG compliance in ~10 minutes.

---

## [DOWNLOAD] What You Downloaded

1. **windows_stig_remote_executor.py** - Runs from Windows, connects via SSH
2. **run_stig.bat** - Windows launcher (optional - makes it easier)
3. Documentation files (README, guides, etc.)

## [WARNING] What You Need From Your Upload

**Your STIG script:** The Python script you uploaded originally  
**Must be named:** `ubuntu20_stig_v2r3_enhanced.py`  
**Must be in:** Same folder as the Windows executor

---

## [TARGET] Setup (5 Minutes)

### 1. Install Python (Skip if you have it)
- Download: https://www.python.org/downloads/
- Install with **"Add Python to PATH" checked**
- Verify: Open PowerShell, type `python --version`

### 2. Install Required Package
Open PowerShell or Command Prompt:
```powershell
pip install paramiko scp
```

### 3. Organize Your Files
Create a folder (e.g., `C:\STIG\`) with:
```
C:\STIG\
|-- windows_stig_remote_executor.py  ← Downloaded from me
|-- ubuntu20_stig_v2r3_enhanced.py   ← Your uploaded STIG script
|-- run_stig.bat                     ← Downloaded from me (optional)
```

### 4. Have This Info Ready
- Ubuntu target IP address (e.g., `192.168.1.100`)
- SSH username (e.g., `ubuntu` or `admin`)
- SSH password
- Sudo password (usually same as SSH password)

---

## Run It

**Easy Way:**
```
Double-click: run_stig.bat
```

**Command Line:**
```powershell
cd C:\STIG
python windows_stig_remote_executor.py
```

**Follow Prompts:**
1. Enter Ubuntu IP address
2. Enter SSH credentials
3. Enter sudo password
4. Confirm execution (type 'EXECUTE')

**Wait ~10 minutes** while it:
- Connects to Ubuntu
- Transfers STIG script
- Applies 172 security controls
- Shows real-time progress
- Creates backups automatically

---

## [OK] After It Completes

**1. Reboot Ubuntu:**
```powershell
ssh user@target 'sudo reboot'
```

**2. Verify (after reboot):**
- [ ] Can still SSH to Ubuntu
- [ ] Critical services running (sshd, auditd, rsyslog)
- [ ] Applications still work

**3. Optional - Validate Compliance:**
- Run OpenSCAP SCAP scan on Ubuntu
- Should show 90-100% compliance

---

## [SHIELD] What Gets Changed

**172 STIG controls applied:**

**Security:**
- [OK] SSH hardened (root disabled, strong ciphers only)
- [OK] Password policy (15 char min, complexity required)
- [OK] Account lockout (3 failed attempts = locked)
- [OK] Firewall enabled (UFW, deny all incoming except SSH)
- [OK] Audit logging (comprehensive 136-rule audit)

**Restrictions:**
- [OK] USB storage disabled
- [OK] Wireless adapters disabled
- [OK] Sudo restrictions (no NOPASSWD, no ALL)
- [OK] Unnecessary services disabled

**Monitoring:**
- [OK] AppArmor enforcing
- [OK] AIDE integrity checking
- [OK] Comprehensive audit trails

---

## [WARNING] CRITICAL WARNINGS

**BEFORE Running:**
- [RED] Create backup/snapshot of Ubuntu system
- [RED] Test in non-production first
- [RED] Have console access ready (KVM/physical)
- [RED] Both .py files must be in same folder

**AFTER Running:**
- [RED] Root SSH login will be DISABLED
- [RED] System MUST be rebooted
- [RED] Users must have 15+ char passwords with complexity
- [RED] SSH may require keys instead of passwords

---

## [HELP] If Something Goes Wrong

**Can't find STIG script:**
```
ERROR: ubuntu20_stig_v2r3_enhanced.py not found!
FIX: Put your uploaded Python STIG script in same folder
     Rename it to: ubuntu20_stig_v2r3_enhanced.py
```

**Connection failed:**
```
FIX: Test SSH manually first: ssh user@target_ip
     Check firewall allows SSH (port 22)
     Verify credentials are correct
```

**Can't SSH after running:**
```
USE: Console access (KVM/physical)
RESTORE: sudo cp /var/backups/pre-stig-*/sshd_config /etc/ssh/
         sudo systemctl restart sshd
```

**Paramiko not found:**
```
FIX: pip install paramiko scp
```

---

##  Need More Info?

**Quick:** Read `QUICK_START.md` (5-minute guide)  
**Detailed:** Read `README_WINDOWS_EXECUTOR.md` (full documentation)  
**Summary:** Read `PACKAGE_SUMMARY.md` (overview of everything)  

**Logs:**
- Windows: `%USERPROFILE%\stig_execution_logs\`
- Ubuntu: `/var/log/ubuntu20-stig-v2r3-remediation.log`

**Backups:**
- Ubuntu: `/var/backups/pre-stig-YYYYMMDD_HHMMSS/`

---

## [TARGET] Quick Checklist

**Before Running:**
- [ ] Python 3.6+ installed on Windows
- [ ] `pip install paramiko` completed
- [ ] Both .py files in same folder
- [ ] Ubuntu target is 20.04 LTS
- [ ] Can SSH to Ubuntu manually
- [ ] Have sudo password
- [ ] Created backup/snapshot of Ubuntu
- [ ] Have console access ready
- [ ] Tested in non-production first

**After Running:**
- [ ] Script completed successfully
- [ ] Reviewed execution log
- [ ] Rebooted Ubuntu system
- [ ] Can still SSH to Ubuntu
- [ ] Services running (sshd, auditd, rsyslog)
- [ ] Applications work correctly
- [ ] Ran SCAP scan (optional)
- [ ] Documented any issues

---

## [IDEA] Pro Tip

**First Time?**
1. Test on a VM or dev system first
2. Take a VM snapshot before running
3. Have the VM console open in another window
4. Watch the real-time progress
5. After success, then move to production

**Production?**
1. Schedule during maintenance window
2. Have 2+ admins available
3. Keep console/KVM access ready
4. Notify users of password policy changes
5. Document everything

---

##  You're Ready!

**To run right now:**
1. Make sure both .py files are in same folder
2. Open PowerShell in that folder
3. Type: `python windows_stig_remote_executor.py`
4. Follow the prompts
5. Wait ~10 minutes
6. Reboot Ubuntu
7. Done! 

**Questions?** Check the README files or logs.

**Problems?** Use console access to restore from backup.

**Success?** Run SCAP scan to verify ~100% compliance!

---

**Version:** 1.0.0 | **STIG:** V2R3 | **Controls:** 172 (14 CAT I, 136 CAT II, 22 CAT III)

**[SHIELD] Good luck securing your systems!**

---

## [LIST] Quick Command Reference

```powershell
# Setup
pip install paramiko scp

# Run
python windows_stig_remote_executor.py

# Or double-click
run_stig.bat

# Check Python
python --version

# Test SSH
ssh username@target_ip

# Reboot Ubuntu after execution
ssh username@target_ip 'sudo reboot'

# View logs
notepad %USERPROFILE%\stig_execution_logs\stig_execution_*.log
```

---

**Need Help?** Read `README_WINDOWS_EXECUTOR.md` for comprehensive documentation!
