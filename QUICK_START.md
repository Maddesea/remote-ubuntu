# Quick Installation Guide - Windows STIG Remote Executor

## [LAUNCH] 5-Minute Setup

### Step 1: Download Files (1 minute)

Download these 3 files to a folder on your Windows computer (e.g., `C:\STIG\`):

1. **windows_stig_remote_executor.py** - Main Windows executor script
2. **ubuntu20_stig_v2r3_enhanced.py** - STIG remediation script  
3. **run_stig.bat** - Easy Windows launcher (optional)

### Step 2: Install Python (2 minutes - skip if already installed)

1. Go to https://www.python.org/downloads/
2. Download Python 3.12 (or latest 3.x)
3. Run installer
4. [OK] **IMPORTANT: Check "Add Python to PATH"**
5. Click Install

Verify installation:
```powershell
python --version
# Should show: Python 3.12.x
```

### Step 3: Install Required Packages (1 minute)

Open PowerShell or Command Prompt:

```powershell
pip install paramiko scp
```

Wait for installation to complete.

### Step 4: Prepare Target Info (1 minute)

Have this information ready:
- Ubuntu system IP address (e.g., `192.168.1.100`)
- SSH username (e.g., `ubuntu`, `admin`)  
- SSH password
- Sudo password (usually same as SSH password)

### Step 5: Run the Script!

**Option A: Double-click `run_stig.bat`** (easiest)

**Option B: Use PowerShell**
```powershell
cd C:\STIG
python windows_stig_remote_executor.py
```

Follow the prompts and confirm execution.

---

## [FAST] Ultra-Quick Reference

```powershell
# One-time setup
pip install paramiko scp

# Every time you run
python windows_stig_remote_executor.py

# Or just double-click
run_stig.bat
```

**That's it!** The script will:
1. Connect to your Ubuntu system
2. Transfer the STIG script
3. Apply all security controls
4. Show you real-time progress
5. Give you a summary when done

---

## [HELP] Quick Troubleshooting

**"Python not found"**
- Install Python from python.org
- Make sure "Add to PATH" is checked

**"paramiko not found"**
```powershell
pip install paramiko scp
```

**"Connection failed"**
- Check Ubuntu IP address
- Verify SSH is running: `ssh user@ip`
- Check firewall allows SSH (port 22)

**"Authentication failed"**
- Verify username and password
- Test manually: `ssh user@ip`

**"Can't SSH after running"**
- Use console access (KVM/physical)
- Restore backup:
  ```bash
  sudo cp /var/backups/pre-stig-*/sshd_config /etc/ssh/
  sudo systemctl restart sshd
  ```

---

## [LIST] Pre-Flight Checklist

Before running the script:

- [ ] Python 3.6+ installed on Windows
- [ ] paramiko package installed (`pip install paramiko`)
- [ ] Both .py files in same folder
- [ ] Ubuntu target is 20.04 LTS
- [ ] Have SSH access to Ubuntu
- [ ] Have sudo password for Ubuntu
- [ ] Created backup/snapshot of Ubuntu system
- [ ] Have console access to Ubuntu (in case SSH breaks)
- [ ] Tested in non-production first (if going to production)

---

## [TARGET] Post-Execution Checklist

After script completes:

- [ ] Review execution log (in `%USERPROFILE%\stig_execution_logs\`)
- [ ] Reboot Ubuntu system: `ssh user@ip 'sudo reboot'`
- [ ] Test SSH access after reboot
- [ ] Verify critical services running
- [ ] Test applications still work
- [ ] Run SCAP scan to verify compliance
- [ ] Document any issues or exceptions

---

##  Need Help?

**Read the full documentation:**
- README_WINDOWS_EXECUTOR.md (comprehensive guide)

**Check logs:**
- Windows: `%USERPROFILE%\stig_execution_logs\`
- Ubuntu: `/var/log/ubuntu20-stig-v2r3-remediation.log`

**Restore from backup:**
- Ubuntu backups: `/var/backups/pre-stig-*/`
- Use console access if SSH is broken

**Resources:**
- DISA STIGs: https://public.cyber.mil/stigs/
- Ubuntu Security: https://ubuntu.com/security

---

## [WARNING] Remember

1. **Always test in non-production first**
2. **Have console access ready**
3. **Create backups before running**
4. **System must be rebooted after**
5. **SSH configuration will change**

**Good luck! [SHIELD]**
