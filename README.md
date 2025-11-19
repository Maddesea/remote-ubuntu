# Windows STIG Remote Executor for Ubuntu 20.04

Automate Ubuntu 20.04 DISA STIG V2R3 compliance (172 security controls) from your Windows PC to remote Ubuntu servers.

## Overview

This tool allows Windows administrators to remotely apply comprehensive DISA STIG (Defense Information Systems Agency Security Technical Implementation Guide) security controls to Ubuntu 20.04 LTS systems via SSH. The automation applies 172 security controls in approximately 10 minutes, achieving near 100% STIG compliance.

**STIG Version:** V2R3
**Security Controls:** 172 (14 CAT I, 136 CAT II, 22 CAT III)
**Execution Time:** ~10 minutes
**Expected Compliance:** 90-100%

## Key Features

- **Remote Execution**: Run from Windows, execute on Ubuntu via SSH
- **Comprehensive Security**: 172 DISA STIG controls applied automatically
- **Real-time Progress**: Live feedback during execution
- **Automatic Backups**: All changes backed up before modification
- **Detailed Logging**: Complete audit trail on both Windows and Ubuntu
- **Air-gap Support**: Build offline packages for disconnected environments
- **Safe Rollback**: Easy restoration from automatic backups

## Security Controls Applied

### Critical Security Hardening
- SSH hardening (root disabled, strong ciphers only)
- Password policy enforcement (15 char minimum, complexity required)
- Account lockout (3 failed attempts)
- Firewall configuration (UFW enabled, restrictive rules)
- Comprehensive audit logging (136-rule audit configuration)

### System Restrictions
- USB storage disabled
- Wireless adapters disabled
- Sudo restrictions (no NOPASSWD, no wildcards)
- Unnecessary services disabled

### Monitoring & Compliance
- AppArmor enforcing
- AIDE integrity checking
- Comprehensive audit trails
- FIPS compliance configurations

## Quick Start

**See [START_HERE.md](START_HERE.md) for the fastest way to get started (5 minutes).**

### Prerequisites

- **Windows System:**
  - Python 3.6 or higher
  - Network access to target Ubuntu system

- **Target Ubuntu System:**
  - Ubuntu 20.04 LTS
  - SSH access enabled
  - Sudo privileges for the user account

### Installation

1. **Clone or download this repository**

2. **Install Python dependencies:**
   ```powershell
   pip install paramiko scp
   ```

3. **Prepare required files:**
   - `windows_stig_remote_executor.py` - Main executor (included)
   - `ubuntu20_stig_v2r3_enhanced.py` - STIG script (required, not included)
   - `run_stig.bat` - Optional launcher (included)

### Basic Usage

**Option 1: Use the batch file**
```powershell
run_stig.bat
```

**Option 2: Run directly**
```powershell
python windows_stig_remote_executor.py
```

Follow the interactive prompts to:
1. Enter Ubuntu target IP address
2. Provide SSH credentials
3. Provide sudo password
4. Confirm execution

**After completion, reboot the Ubuntu system:**
```bash
ssh user@target 'sudo reboot'
```

## Air-gap Deployment

For systems without internet access, use the air-gap package builder:

```powershell
python build_airgap_package.py
```

See [README_AIRGAP.md](README_AIRGAP.md) or [AIRGAP_QUICK_START.md](AIRGAP_QUICK_START.md) for detailed instructions.

## Documentation

| Document | Description |
|----------|-------------|
| [START_HERE.md](START_HERE.md) | **Start here** - Quick setup guide (5 minutes) |
| [QUICK_START.md](QUICK_START.md) | Condensed installation and usage guide |
| [README_WINDOWS_EXECUTOR.md](README_WINDOWS_EXECUTOR.md) | Complete documentation for the Windows executor |
| [README_AIRGAP.md](README_AIRGAP.md) | Air-gap deployment guide |
| [AIRGAP_QUICK_START.md](AIRGAP_QUICK_START.md) | Quick air-gap setup |
| [COMPLETE_PACKAGE_GUIDE.md](COMPLETE_PACKAGE_GUIDE.md) | Comprehensive guide to all features |
| [PACKAGE_SUMMARY.md](PACKAGE_SUMMARY.md) | Overview of all components |
| [ALL_FILES_GUIDE.md](ALL_FILES_GUIDE.md) | Description of all files in the package |
| [IMPORTANT_STIG_SCRIPT_NOTE.md](IMPORTANT_STIG_SCRIPT_NOTE.md) | Critical notes about the STIG script |

## Project Structure

```
.
|-- windows_stig_remote_executor.py   # Main Windows executor
|-- airgap_windows_stig_executor.py   # Air-gap executor
|-- build_airgap_package.py           # Air-gap package builder
|-- download_dependencies.py          # Dependency downloader
|-- run_stig.bat                      # Windows launcher
|-- run_airgap_stig.bat               # Air-gap launcher
|-- Documentation files (*.md)
```

## Critical Warnings

### Before Execution

- **Create a backup or snapshot** of the Ubuntu system
- **Test in a non-production environment first**
- **Have console access ready** (KVM/physical) in case SSH breaks
- **Both Python files must be in the same folder**
- **Review all STIG controls** to understand system changes

### After Execution

- **System MUST be rebooted** for all changes to take effect
- **Root SSH login will be DISABLED**
- **Password complexity requirements** enforced (15+ characters)
- **SSH configuration changes** may require key-based authentication
- **Account lockout enabled** (3 failed login attempts)

### Potential Impacts

- Existing weak passwords will no longer work
- Some sudo commands may be restricted
- USB storage devices will not mount
- Wireless adapters will be disabled
- Some services may be stopped/disabled

## Troubleshooting

### Common Issues

**Connection Failed**
- Verify SSH access: `ssh username@target_ip`
- Check firewall allows port 22
- Confirm credentials are correct

**STIG Script Not Found**
- Ensure `ubuntu20_stig_v2r3_enhanced.py` is in the same folder
- Check filename matches exactly

**Can't SSH After Running**
- Use console access (KVM/physical)
- Restore SSH config from backup:
  ```bash
  sudo cp /var/backups/pre-stig-*/sshd_config /etc/ssh/
  sudo systemctl restart sshd
  ```

**Paramiko Not Found**
- Install dependencies: `pip install paramiko scp`

## Logs and Backups

### Logs

**Windows:**
```
%USERPROFILE%\stig_execution_logs\stig_execution_*.log
```

**Ubuntu:**
```
/var/log/ubuntu20-stig-v2r3-remediation.log
```

### Backups

**Ubuntu system backups:**
```
/var/backups/pre-stig-YYYYMMDD_HHMMSS/
```

All modified files are backed up before changes are applied.

## Verification

After execution and reboot, verify compliance:

1. **Test SSH access:**
   ```bash
   ssh username@target_ip
   ```

2. **Check critical services:**
   ```bash
   systemctl status sshd auditd rsyslog
   ```

3. **Run SCAP scan (optional):**
   Use OpenSCAP to validate STIG compliance

4. **Review audit log:**
   Check `/var/log/ubuntu20-stig-v2r3-remediation.log`

## Support

### Logs Location
- Windows execution logs: `%USERPROFILE%\stig_execution_logs\`
- Ubuntu remediation log: `/var/log/ubuntu20-stig-v2r3-remediation.log`

### Resources
- [DISA STIGs](https://public.cyber.mil/stigs/)
- [Ubuntu Security](https://ubuntu.com/security)
- [OpenSCAP](https://www.open-scap.org/)

## License

This tool is provided as-is for security compliance automation. Always test in non-production environments before deploying to production systems.

## Version

**Version:** 1.0.0
**STIG Version:** V2R3
**Target OS:** Ubuntu 20.04 LTS

---

**Need help getting started?** Read [START_HERE.md](START_HERE.md) for a 5-minute quick start guide!
