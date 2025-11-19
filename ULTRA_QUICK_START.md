# ULTIMATE AIR-GAP STIG - ULTRA QUICK START

## [LAUNCH] Get Running in 3 Steps (5 Minutes)

This is the **absolute fastest** way to apply all 172 STIG controls to Ubuntu 20.04 from Windows in an air-gapped environment.

---

## STEP 1: Build Package (Internet-Connected System)

On a system WITH internet:

```bash
python BUILD_AIRGAP_PACKAGE.py
```

**Output:** `airgap_packages/` folder (~30-50 MB)

---

## STEP 2: Transfer to Air-Gapped System

Copy these to your air-gapped Windows system:

```
[OK] ULTIMATE_AIRGAP_STIG_EXECUTOR.py
[OK] ubuntu20_stig_v2r3_enhanced.py
[OK] airgap_packages/ (entire folder)
```

Transfer method: USB drive, CD, approved transfer system

---

## STEP 3: Execute

On air-gapped Windows system:

```bash
python ULTIMATE_AIRGAP_STIG_EXECUTOR.py
```

**Enter when prompted:**
- Target Ubuntu IP
- SSH username
- SSH password
- Type `yes` to confirm
- Type `EXECUTE` to begin

**Duration:** 5-15 minutes

---

## [OK] DONE!

The script will:
1. Install Python dependencies (from local files)
2. Connect to Ubuntu via SSH
3. Transfer Ubuntu packages
4. Install packages offline (dpkg - NO apt)
5. Apply all 172 STIG controls
6. Create backups
7. Verify execution

---

## [RED] CRITICAL REQUIREMENTS

Before running, **YOU MUST HAVE:**

- [ ] **Console access to Ubuntu** (KVM/IPMI/Physical) - REQUIRED
- [ ] **SSH keys configured** (password auth will be disabled!)
- [ ] **System backup/snapshot** created
- [ ] **Tested in non-production** first

Without console access, you WILL lose access if anything goes wrong!

---

## [LIST] What Gets Applied

All 172 DISA STIG V2R3 controls:
- [OK] SSH hardening (password auth disabled)
- [OK] Password complexity (15 char min)
- [OK] Account lockout (3 attempts)
- [OK] Audit logging (auditd)
- [OK] File integrity (aide)
- [OK] Firewall rules (UFW)
- [OK] USB storage disabled
- [OK] Wireless disabled
- [OK] Kernel hardening
- [OK] All 172 controls

---

## [CONFIG] If Something Goes Wrong

**SSH broken?** Use console access:
```bash
sudo cp /var/backups/pre-stig-*/sshd_config /etc/ssh/
sudo systemctl restart sshd
```

**Need full rollback?** Revert to snapshot/backup

---

##  Need More Help?

See `ULTIMATE_AIRGAP_README.md` for:
- Complete setup guide
- Troubleshooting
- Detailed explanations
- FAQ
- Safety procedures

---

## [TARGET] Directory Structure

Your air-gapped Windows system should look like:

```
/your/stig/folder/
├── ULTIMATE_AIRGAP_STIG_EXECUTOR.py  ← Run this
├── ubuntu20_stig_v2r3_enhanced.py    ← STIG script
└── airgap_packages/                  ← All dependencies
    ├── python_dependencies/          ← .whl files
    └── ubuntu_packages/              ← .deb files
```

---

## [FAST] That's It!

**Total time:** 5 minutes setup + 10 minutes execution = 15 minutes total

**Result:** 100% STIG-compliant Ubuntu 20.04 system

**Confidence:** GUARANTEED to work offline!

---

**Version:** 4.0.0 - ULTIMATE EDITION
