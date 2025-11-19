# Quick Reference Guide

## 1-Minute Setup

### Windows Host

1. Ensure these files exist:
   - `RUN_ME.bat`
   - `windows_airgap_stig_complete.py`
   - `ubuntu20_stig_remediation_airgapped.py`

2. Double-click `RUN_ME.bat`

3. Enter when prompted:
   - Target Ubuntu IP
   - SSH username/password
   - Sudo password

4. Type `EXECUTE` when prompted

5. Wait 5-15 minutes

6. Reboot Ubuntu: `ssh user@target 'sudo reboot'`

## File Descriptions

| File | Purpose |
|------|---------|
| `RUN_ME.bat` | Windows launcher - double-click this! |
| `windows_airgap_stig_complete.py` | Main executor (Windows → Ubuntu) |
| `ubuntu20_stig_remediation_airgapped.py` | STIG remediation script (runs on Ubuntu) |
| `COMPLETE_AIRGAP_README.md` | Full documentation |
| `dependencies/` (optional) | Paramiko wheels for better performance |

## Common Commands

### Run from Windows
```cmd
RUN_ME.bat
```

### Run manually
```cmd
python windows_airgap_stig_complete.py
```

### Check logs on Ubuntu
```bash
tail -f /var/log/stig/stig_remediation_*.log
```

### Verify services
```bash
systemctl status sshd auditd rsyslog ufw
```

### Check firewall
```bash
sudo ufw status verbose
```

### View backups
```bash
ls -la /var/backups/stig-v2r3/
ls -la /var/backups/pre-stig-*/
```

## Unlock Locked Account
```bash
sudo faillock --user username --reset
sudo passwd username  # Reset password if needed
```

## Allow Additional Firewall Ports
```bash
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw reload
```

## Restore SSH Config (if locked out)
```bash
# Via console access
sudo cp /var/backups/pre-stig-*/sshd_config /etc/ssh/sshd_config
sudo systemctl restart sshd
```

## Check Password Policy
```bash
cat /etc/security/pwquality.conf
cat /etc/login.defs | grep PASS
```

## View Audit Rules
```bash
sudo auditctl -l
```

## Check Applied STIG Controls
```bash
# Find all STIG configuration files
find /etc -name "*stig*" -o -name "99-stig.conf"

# View kernel parameters
sysctl -a | grep -E "net.ipv4|kernel|fs.suid"

# Check disabled modules
cat /etc/modprobe.d/stig-disable.conf
```

## Disable Strict Firewall (if needed)
```bash
sudo ufw default allow outgoing  # Re-enable outgoing
sudo ufw reload
```

## Re-enable USB Storage (if disabled)
```bash
sudo rmmod usb-storage
sudo sed -i '/usb-storage/d' /etc/modprobe.d/stig-disable.conf
sudo modprobe usb-storage
```

## Check Compliance Score

### Using OpenSCAP (if installed)
```bash
sudo oscap xccdf eval \
  --profile stig-ubuntu2004-disa \
  --results /tmp/scap-results.xml \
  --report /tmp/scap-report.html \
  /usr/share/xml/scap/ssg/content/ssg-ubuntu2004-xccdf.xml
```

### Manual Check List

- [ ] SSH allows only key-based auth (or password if configured)
- [ ] Root login disabled via SSH
- [ ] Audit daemon running: `systemctl status auditd`
- [ ] Firewall active: `sudo ufw status`
- [ ] Password policy enforced: Test password change
- [ ] Services disabled: Check `/etc/systemd/system/*.service`
- [ ] File permissions correct: `ls -l /etc/shadow` shows 640
- [ ] Login banner displays: `cat /etc/issue`
- [ ] System boots successfully
- [ ] Applications function correctly

## Troubleshooting Quick Fixes

### Can't SSH after reboot
1. Use console access (KVM/IPMI/Physical)
2. Check SSH status: `sudo systemctl status sshd`
3. Review SSH logs: `sudo tail -f /var/log/auth.log`
4. Restore config: `sudo cp /var/backups/pre-stig-*/sshd_config /etc/ssh/sshd_config`
5. Restart SSH: `sudo systemctl restart sshd`

### Account locked
```bash
sudo faillock --user username --reset
```

### Forgotten password policy
```bash
# Min 15 chars, 1 upper, 1 lower, 1 digit, 1 special
# Example: MyP@ssw0rd12345
```

### Services not starting
```bash
sudo systemctl status SERVICE_NAME
sudo journalctl -u SERVICE_NAME -n 50
```

### Firewall blocking needed service
```bash
sudo ufw allow PORT/tcp
sudo ufw reload
```

## Important Notes

⚠️ **Before Running:**
- Have console access ready
- Create VM snapshot or backup
- Test in dev environment first
- Read COMPLETE_AIRGAP_README.md

⚠️ **After Running:**
- Reboot is required
- Verify SSH access
- Check all services
- Test applications
- Document any issues

⚠️ **Security Changes:**
- Firewall enabled (UFW)
- Password policy enforced (15 char min)
- Account lockout after 3 fails
- Audit logging enabled
- Many services disabled
- File permissions restricted

## Getting Full Details

Read `COMPLETE_AIRGAP_README.md` for:
- Complete troubleshooting guide
- Detailed file descriptions
- Configuration options
- Security considerations
- Technical specifications

## Quick Test Script

Save as `test_stig.sh` and run on Ubuntu target:

```bash
#!/bin/bash
echo "STIG Compliance Quick Check"
echo "============================"

echo -n "SSH config valid: "
sudo sshd -t 2>/dev/null && echo "✓" || echo "✗"

echo -n "Auditd running: "
systemctl is-active auditd >/dev/null && echo "✓" || echo "✗"

echo -n "Firewall active: "
sudo ufw status | grep -q "Status: active" && echo "✓" || echo "✗"

echo -n "/etc/shadow perms: "
[[ "$(stat -c %a /etc/shadow)" == "640" ]] && echo "✓" || echo "✗"

echo -n "Root login disabled: "
grep -q "^PermitRootLogin no" /etc/ssh/sshd_config && echo "✓" || echo "✗"

echo -n "Login banner exists: "
[[ -s /etc/issue ]] && echo "✓" || echo "✗"

echo -n "Password min length: "
grep -q "minlen = 15" /etc/security/pwquality.conf && echo "✓" || echo "✗"

echo
echo "Log files:"
ls -lh /var/log/stig/ 2>/dev/null || echo "No STIG logs"

echo
echo "Backups:"
ls -ld /var/backups/*stig* 2>/dev/null || echo "No backups found"
```

---

**Need help?** Check COMPLETE_AIRGAP_README.md or review execution logs.
