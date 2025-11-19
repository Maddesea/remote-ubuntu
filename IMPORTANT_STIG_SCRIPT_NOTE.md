# Important Note About the STIG Script

## Required File: ubuntu20_stig_v2r3_enhanced.py

The Windows remote executor requires the original STIG remediation script that you uploaded.

### What You Need To Do:

1. **Use the Python script you already have** - The script you uploaded as `U_CAN_Ubuntu_20-04_LTS_V2R3_STIG.zip` or provided separately

2. **Ensure the script is named:** `ubuntu20_stig_v2r3_enhanced.py`

3. **Place it in the same folder as:**
   - `windows_stig_remote_executor.py` (Windows launcher)
   - `run_stig.bat` (optional batch file)

### File Structure Should Look Like:

```
C:\STIG\
|-- windows_stig_remote_executor.py    ← Windows launcher (provided)
|-- ubuntu20_stig_v2r3_enhanced.py     ← Your STIG script (you already have this)
|-- run_stig.bat                        ← Quick launcher (provided)
|-- README_WINDOWS_EXECUTOR.md          ← Full documentation (provided)
|-- QUICK_START.md                      ← Quick setup guide (provided)
```

### If You Need To Extract/Locate Your Script:

**If you provided it as a document:**
- Look for the file you uploaded initially
- It should be a Python (.py) file with STIG remediation code
- Rename it to: `ubuntu20_stig_v2r3_enhanced.py`

**If it's in a ZIP:**
- Extract the ZIP file
- Find the Python script (should be 100KB+)
- Copy it to your working directory
- Rename to: `ubuntu20_stig_v2r3_enhanced.py`

### Verify You Have The Right File:

The correct script should:
- Be a Python file (`.py` extension)
- Contain Ubuntu 20.04 STIG V2R3 remediation code
- Be approximately 80-150 KB in size
- Have imports like: `paramiko`, `jinja2`, `yaml`
- Have a main class like `UBUNTU20STIGRemediation`

### Quick Check:

Open the file in Notepad and verify it starts with something like:
```python
#!/usr/bin/env python3
"""
UBUNTU20-STIG V2R3 Python Implementation
...
```

---

## If You Can't Find The Original Script

The script you provided was a comprehensive Ubuntu 20.04 STIG V2R3 remediation script.

**Key characteristics:**
- Version: 2.5.0 (Remote Execution Edition)
- STIG Version: V2R3 (Release 3)
- Date: July 2, 2025
- Total Controls: 172 (14 CAT I, 136 CAT II, 22 CAT III)

**The script includes:**
- Package management
- Service configuration
- Kernel parameter hardening (sysctl)
- PAM authentication configuration
- SSH hardening
- Audit configuration (auditd)
- Account management
- File permissions
- Firewall setup (UFW)
- GRUB configuration
- USB/Wireless restrictions (new in V2R3)
- SSSD/PKI support
- Sudo restrictions
- AppArmor enforcement
- AIDE integrity checking

If you need to recreate it, you can copy the Python script content from your original upload or documentation.

---

## Once You Have Both Files:

Simply run:
```powershell
python windows_stig_remote_executor.py
```

Or double-click:
```
run_stig.bat
```

The Windows executor will automatically find and use the `ubuntu20_stig_v2r3_enhanced.py` script!
