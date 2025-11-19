# Air-Gap STIG Quick Start - 5 Minutes

## [FAST] Ultra-Quick Guide for Air-Gapped Systems

### What You Have:
A complete offline package to apply maximum security STIG controls to Ubuntu 20.04.

### What You Need:
1. Python 3.6+ on Windows
2. This complete package
3. Target Ubuntu 20.04 system IP/credentials

---

## [LAUNCH] Run It Now (3 Steps)

### Step 1: Verify Files
```powershell
dir
```

You should see:
- `dependencies/` folder (with .whl files inside)
- `airgap_windows_stig_executor.py`
- `ubuntu20_stig_v2r3_enhanced.py`

**Missing files?** See README_AIRGAP.md for package contents.

### Step 2: Execute
```powershell
# Easy way
run_airgap_stig.bat

# Or direct
python airgap_windows_stig_executor.py
```

### Step 3: Follow Prompts
1. Enter Ubuntu IP: `192.168.1.100`
2. Enter SSH username: `ubuntu`
3. Enter SSH password: `********`
4. Enter sudo password: `********` (usually same)
5. Security options:
   - Disable password auth? **[Y/n]** <- Press Enter for YES
   - Enable FIPS? **[y/N]** <- Press Enter for NO
   - Strict firewall? **[Y/n]** <- Press Enter for YES
6. Type: **`EXECUTE`** <- Must type exactly

**Wait ~10 minutes** while it works.

---

## [OK] After Completion

### Reboot Target:
```powershell
ssh user@target 'sudo reboot'
```

### Verify (after reboot):
```powershell
# Test SSH (may need keys if password auth disabled)
ssh -i your_key user@target

# Check services
ssh user@target 'sudo systemctl status sshd auditd rsyslog ufw'
```

---

## [WARNING] CRITICAL WARNINGS

### Before Running:
- [RED] **Have console access ready** (KVM/IPMI)
- [RED] **Have SSH keys configured** (password auth will be disabled)
- [RED] **Create backup/snapshot**
- [RED] **Test in dev first**

### After Running:
- [RED] **SSH password login DISABLED** (use keys)
- [RED] **Many services DISABLED** (USB, WiFi, Bluetooth, CUPS)
- [RED] **Firewall STRICT** (only SSH allowed)
- [RED] **Must use compliant passwords** (15+ chars, complexity)

---

## [WARNING] Quick Fixes

### "dependencies not found"
```
CHECK: Is 'dependencies' folder in same directory?
FIX: Ensure complete package was transferred
```

### "paramiko not found"
```
WAIT: Script will auto-install from dependencies
IF FAILS: See README_AIRGAP.md section on manual install
```

### "Can't connect"
```
TEST: ssh user@target_ip
CHECK: Network connectivity, firewall, credentials
```

### "Can't SSH after execution"
```
USE: Console access (KVM/IPMI/Physical)
FIX: sudo cp /var/backups/pre-stig-*/sshd_config /etc/ssh/
     sudo systemctl restart sshd
```

---

## [LIST] What Gets Locked Down

### Maximum Security Applied:
- [OK] SSH password auth **DISABLED** (keys only)
- [OK] Root SSH login **DISABLED**
- [OK] USB storage **DISABLED**
- [OK] Wireless **DISABLED**
- [OK] Firewall **STRICT** (deny all except SSH)
- [OK] 172 STIG controls applied
- [OK] Password complexity enforced (15+ chars)
- [OK] Account lockout (3 attempts)
- [OK] Full audit logging
- [OK] AppArmor enforcing
- [OK] AIDE integrity monitoring

---

## Need More Info?

**Full Guide:** `README_AIRGAP.md`  
**Security Details:** `MAXIMUM_SECURITY_GUIDE.md`  
**Troubleshooting:** `TROUBLESHOOTING_AIRGAP.md`  

**Logs:**
- Windows: `%USERPROFILE%\stig_execution_logs\`
- Ubuntu: `/var/log/ubuntu20-stig-v2r3-remediation.log`

**Backups:**
- Ubuntu: `/var/backups/pre-stig-*`

---

## [TARGET] Checklist

**Before Running:**
- [ ] Python 3.6+ installed
- [ ] Complete package transferred
- [ ] Dependencies folder present
- [ ] Ubuntu target is 20.04
- [ ] Have SSH credentials
- [ ] Have console access ready
- [ ] Created backup/snapshot

**After Running:**
- [ ] Script completed successfully
- [ ] Rebooted Ubuntu
- [ ] Can access via SSH (keys)
- [ ] Services running
- [ ] Applications work
- [ ] Documented changes

---

## [NOTE] Pro Tips

**First Time?**
1. Test on VM with snapshot
2. Watch real-time progress
3. Keep console open
4. Document everything

**Production?**
1. Maintenance window
2. Multiple admins available
3. Console access ready
4. Change control approved

---

**Version:** 2.0.0-airgap | **Mode:** Maximum Security | **Controls:** 172

**[SECURE] Lock it down!**
