# CLAUDE.md - AI Assistant Guide for Windows STIG Remote Executor

## Project Overview

**Repository Name**: Windows-to-Ubuntu STIG Remote Executor
**Purpose**: Automate Ubuntu 20.04 DISA STIG V2R3 compliance (172 security controls) from Windows workstations to remote Ubuntu servers
**Language**: Python 3.6+
**Target Platforms**: Windows (client) → Ubuntu 20.04 LTS (target)
**Security Level**: High - DoD/DISA compliance automation

### Key Features
- Remote SSH-based execution from Windows to Ubuntu
- Dual mode: Internet-connected and Air-gapped environments
- Automatic backup creation before modifications
- Real-time progress monitoring
- Comprehensive logging
- 172 STIG controls (14 CAT I, 136 CAT II, 22 CAT III)

---

## Repository Structure

```
/
├── Core Executors (Primary Scripts)
│   ├── windows_stig_remote_executor.py      (24 KB) - Internet-connected mode
│   └── airgap_windows_stig_executor.py      (30 KB) - Air-gapped mode
│
├── Helper Scripts
│   ├── download_dependencies.py              (9.6 KB) - Pre-download Python packages
│   └── build_airgap_package.py              (18 KB) - Build complete air-gap package
│
├── Windows Launchers (Optional convenience wrappers)
│   ├── run_stig.bat                          (5.7 KB) - Launch internet-connected mode
│   └── run_airgap_stig.bat                   (7.5 KB) - Launch air-gapped mode
│
├── Documentation (User-facing)
│   ├── START_HERE.md                         (6.5 KB) - Quick start for internet mode
│   ├── AIRGAP_QUICK_START.md                 (4.1 KB) - Quick start for air-gap mode
│   ├── QUICK_START.md                        (3.8 KB) - 5-minute setup guide
│   ├── COMPLETE_PACKAGE_GUIDE.md            (15 KB) - Comprehensive overview
│   ├── PACKAGE_SUMMARY.md                   (12 KB) - Summary of what gets changed
│   ├── ALL_FILES_GUIDE.md                   (10 KB) - All files overview
│   ├── README_WINDOWS_EXECUTOR.md           (16 KB) - Detailed internet mode docs
│   ├── README_AIRGAP.md                     (16 KB) - Detailed air-gap mode docs
│   └── IMPORTANT_STIG_SCRIPT_NOTE.md         (3 KB) - Notes about required STIG script
│
└── Required External File (Not in repo)
    └── ubuntu20_stig_v2r3_enhanced.py       (~100 KB) - Actual STIG remediation script
```

---

## Codebase Architecture

### 1. windows_stig_remote_executor.py
**Purpose**: Internet-connected execution mode
**Key Classes**:
- `WindowsSTIGRemoteExecutor`: Main orchestration class
  - SSH connection management via paramiko
  - Interactive credential collection
  - SCP file transfer to target
  - Remote sudo command execution with password handling
  - Real-time output streaming
  - Logging and error handling

**Dependencies**:
- `paramiko`: SSH protocol implementation
- `scp`: SCP file transfer (optional but recommended)
- Standard library: `os`, `sys`, `time`, `getpass`, `logging`, `pathlib`, `datetime`

**Key Methods**:
- `get_connection_info()`: Interactive credential collection
- `test_connection()`: SSH connectivity validation
- `transfer_script()`: SCP file transfer to target
- `execute_remote_command()`: Execute commands with sudo password handling
- `execute_stig()`: Main execution orchestration

### 2. airgap_windows_stig_executor.py
**Purpose**: Air-gapped/isolated environment execution
**Key Classes**:
- `AirGapDependencyInstaller`: Install packages from local files
  - Check for missing Python packages
  - Install from local wheel/tar.gz files
  - Fallback to setup.py installation if needed
- `AirGapSTIGRemoteExecutor`: Enhanced executor with local dependency support
  - All features of `WindowsSTIGRemoteExecutor`
  - Maximum security lockdown mode by default
  - Local dependency installation

**Additional Features**:
- Pre-bundled dependencies in `dependencies/` folder
- Offline package installation
- Enhanced security configurations

### 3. download_dependencies.py
**Purpose**: Download Python packages for air-gap transfer
**Functionality**:
- Downloads paramiko and all transitive dependencies
- Creates `dependencies/` folder
- Downloads as wheels (.whl) for faster installation
- Platform-aware downloads (Windows-specific binaries)

**Key Packages Downloaded**:
- paramiko
- cryptography
- bcrypt
- PyNaCl
- cffi
- pycparser
- six

### 4. build_airgap_package.py
**Purpose**: Create complete transferable air-gap package
**Key Classes**:
- `AirGapPackageBuilder`: Package assembly and validation
  - Verify all required files present
  - Download dependencies if needed
  - Create proper directory structure
  - Generate ZIP archive
  - Create SHA256 checksums
  - Generate README with package contents

**Output**: `stig-airgap-package-YYYYMMDD.zip`

### 5. Batch Launchers (.bat files)
**Purpose**: User-friendly Windows interfaces
**Functionality**:
- Python installation check
- Dependency verification
- Interactive prerequisites checking
- Offer to install missing packages
- Launch appropriate Python executor

---

## Key Conventions

### Code Style
- **Python Version**: 3.6+ required (uses f-strings, pathlib)
- **Docstrings**: Module-level and class-level docstrings in triple quotes
- **Comments**: Inline comments for complex logic
- **Error Handling**: Try-except blocks with user-friendly error messages
- **Logging**: Both file and console logging via Python `logging` module

### File Organization
- **Two-script architecture**: Executor script + STIG script (must be in same directory)
- **Executor scripts**: Handle connection, transfer, orchestration
- **STIG script**: Actual remediation logic (external file: `ubuntu20_stig_v2r3_enhanced.py`)

### Naming Conventions
- **Scripts**: `snake_case.py`
- **Classes**: `PascalCase`
- **Methods/Functions**: `snake_case()`
- **Constants**: `UPPER_SNAKE_CASE`
- **Variables**: `snake_case`

### Documentation Standards
- **User docs**: Markdown with emoji for visual hierarchy
- **Format**: `## Title`, bullet lists, code blocks with language tags
- **Structure**: What/Why/How format
- **Warnings**: Clearly marked with [WARNING] symbol
- **Checklists**: Interactive with `- [ ]` syntax

---

## Development Workflows

### Adding New Features

1. **Determine Scope**:
   - Internet-only, air-gap-only, or both?
   - User-facing or internal functionality?
   - Backward compatibility considerations

2. **Implementation Locations**:
   - **Connection handling**: Modify `WindowsSTIGRemoteExecutor` class
   - **Air-gap features**: Modify `AirGapDependencyInstaller` or `AirGapSTIGRemoteExecutor`
   - **Dependency management**: Modify `download_dependencies.py`
   - **Packaging**: Modify `build_airgap_package.py`

3. **Update Documentation**:
   - Update appropriate README files
   - Add to quick start guides if user-facing
   - Update PACKAGE_SUMMARY.md if it changes what gets applied

### Modifying Executors

**For windows_stig_remote_executor.py**:
```python
# Pattern for adding new SSH functionality
class WindowsSTIGRemoteExecutor:
    def new_feature_method(self):
        """Docstring explaining what this does"""
        if not self.connected:
            logger.error("Not connected")
            return False

        try:
            # Implementation
            logger.info("Feature executed successfully")
            return True
        except Exception as e:
            logger.error(f"Error: {e}")
            return False
```

**For air-gap mode**:
- Ensure feature works without internet
- Add any new dependencies to `download_dependencies.py`
- Update dependency installer in `airgap_windows_stig_executor.py`

### Testing Procedures

**Manual Testing Checklist**:
1. **Internet-connected mode**:
   - [ ] Fresh Python 3.6+ environment
   - [ ] Install paramiko via pip
   - [ ] Place both .py files in same directory
   - [ ] Run `python windows_stig_remote_executor.py`
   - [ ] Verify SSH connection
   - [ ] Verify file transfer
   - [ ] Verify execution completes
   - [ ] Check logs in `%USERPROFILE%\stig_execution_logs\`

2. **Air-gapped mode**:
   - [ ] On connected system: run `python download_dependencies.py`
   - [ ] Run `python build_airgap_package.py`
   - [ ] Transfer ZIP to isolated system
   - [ ] Extract and verify structure
   - [ ] Run `python airgap_windows_stig_executor.py`
   - [ ] Verify offline dependency installation
   - [ ] Verify execution completes

3. **Ubuntu target validation**:
   - [ ] Pre-execution: Take snapshot/backup
   - [ ] Post-execution: Verify SSH still works
   - [ ] Verify critical services running
   - [ ] Check `/var/log/ubuntu20-stig-v2r3-remediation.log`
   - [ ] Verify backups created in `/var/backups/pre-stig-*`
   - [ ] Reboot system
   - [ ] Re-verify SSH and services

**Test Environment Recommendations**:
- Windows 10/11 VM or physical system
- Ubuntu 20.04 LTS VM (easily restorable)
- Non-production test network
- Console access to Ubuntu (VM console or KVM)

---

## Security Considerations

### Critical Security Aspects

1. **Password Handling**:
   - Passwords collected via `getpass.getpass()` (not echoed)
   - Stored in memory only, not logged
   - Passed to SSH via paramiko's secure authentication
   - Sudo password sent via stdin with timeout

2. **SSH Security**:
   - Uses paramiko's SSH client (tested, secure implementation)
   - Supports password and key-based authentication
   - Validates host keys (can be configured)
   - All communication encrypted

3. **STIG Application**:
   - **High impact**: 172 security controls applied to target
   - **Irreversible changes**: Some settings cannot be easily undone
   - **Backup creation**: Automatic backups before changes
   - **Risk areas**: SSH configuration, password policies, firewall rules

### User Safety Features

1. **Pre-execution warnings**: Clear display of what will change
2. **Confirmation prompts**: Must type 'EXECUTE' to proceed
3. **Connection testing**: Validates SSH before execution
4. **Backup creation**: Automatic pre-execution backups
5. **Console access reminder**: Warns users to have console ready
6. **Comprehensive logging**: All actions logged for audit

### What Gets Modified on Target

**CAT I (Critical - 14 controls)**:
- SSH: Root login disabled, weak auth disabled
- Passwords: SHA512 hashing, no null passwords
- Packages: Remove telnet, rsh-server

**CAT II (Medium - 136 controls)**:
- Password policy: 15 char minimum, complexity required
- Account lockout: 3 failed attempts = 15 min lockout
- Kernel: 59 sysctl parameters (network, memory, security)
- Audit: 136 auditd rules (comprehensive logging)
- SSH: FIPS ciphers only, idle timeout
- Firewall: UFW enabled, deny all incoming except SSH
- Services: Disable cups, bluetooth, avahi, unnecessary services
- USB: Storage auto-mount disabled
- Wireless: Adapters disabled (configurable)
- Sudo: No NOPASSWD, no ALL usage
- AppArmor: Enforcing mode
- AIDE: File integrity monitoring

**CAT III (Low - 22 controls)**:
- Additional file permissions
- Documentation requirements

---

## Common Tasks

### Task 1: Create New Executor Variant

**Goal**: Create a new execution mode (e.g., for different OS)

**Steps**:
1. Copy appropriate base executor (internet or air-gap)
2. Rename file descriptively (e.g., `debian_stig_executor.py`)
3. Update class names and docstrings
4. Modify STIG script filename reference
5. Adjust any OS-specific commands
6. Update documentation to reference new variant
7. Create corresponding launcher .bat file if needed

**Files to modify**:
- New executor script
- `COMPLETE_PACKAGE_GUIDE.md` (add new option)
- Create new README for the variant

### Task 2: Add New Dependency for Air-gap

**Goal**: Add a new Python package that air-gap mode needs

**Steps**:
1. Update `download_dependencies.py`:
   ```python
   packages = [
       'paramiko',
       'cryptography',
       # ... existing packages ...
       'your-new-package',  # Add here
   ]
   ```

2. Update `airgap_windows_stig_executor.py`:
   ```python
   required_packages = {
       # ... existing packages ...
       'import_name': 'PackageName',  # Add here
   }
   ```

3. Update `build_airgap_package.py` if special handling needed

4. Test full air-gap workflow:
   - Run download_dependencies.py
   - Run build_airgap_package.py
   - Extract and test package

### Task 3: Update Documentation

**Goal**: Keep docs synchronized with code changes

**Documentation hierarchy**:
1. **Entry points**: `START_HERE.md`, `AIRGAP_QUICK_START.md`
2. **Comprehensive**: `README_WINDOWS_EXECUTOR.md`, `README_AIRGAP.md`
3. **Overviews**: `COMPLETE_PACKAGE_GUIDE.md`, `PACKAGE_SUMMARY.md`
4. **Reference**: `ALL_FILES_GUIDE.md`

**When to update**:
- New feature: Update all relevant levels
- Behavior change: Update READMEs and quick starts
- New file: Update ALL_FILES_GUIDE.md
- Security change: Update PACKAGE_SUMMARY.md (What Gets Changed section)

### Task 4: Debug Connection Issues

**Common issues and solutions**:

1. **"paramiko not installed"**:
   - Solution: `pip install paramiko scp`
   - Air-gap: Verify dependencies/ folder exists

2. **"SSH connection failed"**:
   - Check: `ssh username@target` works manually
   - Verify: Firewall allows port 22
   - Check: Target SSH service running
   - Verify: Credentials are correct

3. **"Permission denied (publickey,password)"**:
   - Verify: Password authentication enabled in sshd_config
   - Check: User account not locked
   - Try: Manual SSH with same credentials

4. **"Sudo password failed"**:
   - Verify: User has sudo privileges
   - Check: Sudo password is correct
   - Test: `ssh user@target 'sudo -v'`

5. **"STIG script not found"**:
   - Verify: `ubuntu20_stig_v2r3_enhanced.py` in same directory
   - Check: Filename is exactly correct (case-sensitive)
   - Verify: File is readable

### Task 5: Rollback After Failed Execution

**Goal**: Restore system if STIG application causes issues

**Backup locations**:
```
/var/backups/pre-stig-YYYYMMDD_HHMMSS/  ← Full pre-execution backup
/var/backups/stig-v2r3/                  ← Individual config backups
*.stig-v2r3-backup-*                     ← Per-file backups
```

**Quick SSH restore** (if SSH broken):
```bash
# Via console access
sudo cp /var/backups/pre-stig-*/sshd_config /etc/ssh/
sudo systemctl restart sshd
```

**Full restore**:
```bash
# Find latest backup
BACKUP=$(ls -dt /var/backups/pre-stig-* | head -1)

# Restore critical configs
sudo cp -r $BACKUP/sshd_config /etc/ssh/
sudo cp -r $BACKUP/pam.d/* /etc/pam.d/
sudo cp -r $BACKUP/security/* /etc/security/
sudo cp $BACKUP/sudoers /etc/

# Restart services
sudo systemctl restart sshd
```

---

## Logging and Debugging

### Log Locations

**Windows (executor logs)**:
```
%USERPROFILE%\stig_execution_logs\
└── stig_execution_YYYYMMDD_HHMMSS.log
```

**Ubuntu (STIG application logs)**:
```
/var/log/ubuntu20-stig-v2r3-remediation.log
```

### Log Format

```
YYYY-MM-DD HH:MM:SS - LEVEL - Message
```

**Levels**:
- `INFO`: Normal operation, progress updates
- `WARNING`: Non-critical issues, degraded functionality
- `ERROR`: Critical failures, operation aborted
- `DEBUG`: Verbose technical details (not used by default)

### Adding Debug Logging

```python
# Add to class methods
logger.debug(f"Variable value: {variable}")
logger.info(f"Completed step: {step_name}")
logger.warning(f"Unexpected condition: {condition}")
logger.error(f"Operation failed: {error}")
```

### Common Log Messages

**Success indicators**:
```
INFO - Connected to target successfully
INFO - Script transferred successfully
INFO - STIG execution started
INFO - STIG execution completed successfully
```

**Error indicators**:
```
ERROR - Connection failed: <reason>
ERROR - Authentication failed
ERROR - Script not found: ubuntu20_stig_v2r3_enhanced.py
ERROR - Remote execution failed
ERROR - Sudo password incorrect
```

---

## File Dependencies

### Required for Internet-Connected Mode
```
windows_stig_remote_executor.py      ← Executor
ubuntu20_stig_v2r3_enhanced.py       ← STIG script (external)
```

### Required for Air-Gapped Mode
```
airgap_windows_stig_executor.py      ← Executor
ubuntu20_stig_v2r3_enhanced.py       ← STIG script (external)
dependencies/                         ← Python packages
├── paramiko-*.whl
├── cryptography-*.whl
├── bcrypt-*.whl
├── PyNaCl-*.whl
├── cffi-*.whl
├── pycparser-*.whl
└── six-*.whl
```

### External Dependencies

**Python packages (Internet mode - auto-installed)**:
- `paramiko>=2.7.0`: SSH protocol implementation
- `scp`: SCP file transfer (optional)

**Python packages (Air-gap mode - pre-bundled)**:
- `paramiko`: SSH client
- `cryptography`: Cryptographic primitives for paramiko
- `bcrypt`: Password hashing for paramiko
- `PyNaCl`: Sodium cryptography bindings
- `cffi`: C Foreign Function Interface
- `pycparser`: C parser for cffi
- `six`: Python 2/3 compatibility utilities

**External file (not in repository)**:
- `ubuntu20_stig_v2r3_enhanced.py`: The actual STIG remediation script
  - Must be provided by user
  - Must be named exactly as shown
  - Must be in same directory as executor
  - Size: ~100 KB
  - Contains 172 STIG control implementations

---

## Version Information

**Current Version**: 2.0.0 (Complete Package with Air-gap support)
**STIG Version**: V2R3 (Release 3, July 2025)
**Target OS**: Ubuntu 20.04 LTS
**Python Required**: 3.6+
**Controls Applied**: 172 total (14 CAT I, 136 CAT II, 22 CAT III)

### Version History Pattern
- **1.x.x**: Internet-connected mode only
- **2.x.x**: Both internet-connected and air-gapped modes

---

## AI Assistant Guidelines

### When Helping Users

1. **Identify Mode First**: Ask if they need internet-connected or air-gapped mode
2. **Check Prerequisites**: Verify Python version, dependencies, file placement
3. **Emphasize Safety**: Always remind about backups and console access
4. **Guide to Correct Docs**: Point to appropriate README/quick start
5. **Test Before Production**: Always recommend testing on non-production first

### When Modifying Code

1. **Maintain Dual Mode Support**: Changes should work in both modes when applicable
2. **Update Documentation**: Always update relevant .md files
3. **Preserve Security**: Don't weaken password handling or SSH security
4. **Add Logging**: Include appropriate log statements for new functionality
5. **Error Handling**: Use try-except with user-friendly messages
6. **Backward Compatibility**: Avoid breaking changes to file formats/interfaces

### When Debugging Issues

1. **Check Logs First**: Always examine executor and Ubuntu logs
2. **Verify Environment**: Python version, dependencies, file locations
3. **Test Connectivity**: Verify manual SSH works before troubleshooting executor
4. **Isolate Problem**: Separate connection issues from execution issues
5. **Provide Rollback**: Always give user a way to restore if needed

### Common User Questions

**Q: "Which mode should I use?"**
A: Internet-connected mode if Windows has internet. Air-gapped if Windows is isolated/classified.

**Q: "Can I run this on Windows Server?"**
A: Yes, any Windows with Python 3.6+ works.

**Q: "Will this break my Ubuntu system?"**
A: It makes significant security changes. Always test in non-production first. Backups are automatic.

**Q: "Can I undo the changes?"**
A: Partially. Backups are created in `/var/backups/pre-stig-*/`. Some changes are architectural.

**Q: "Do I need administrator rights on Windows?"**
A: Not for the executor. Just need to install Python and packages.

**Q: "What if SSH breaks?"**
A: Use console access (KVM/physical). Restore sshd_config from backup. This is why console access is critical.

**Q: "Can I customize which controls are applied?"**
A: Yes, but that requires modifying the STIG script (`ubuntu20_stig_v2r3_enhanced.py`), not the executor.

---

## Best Practices

### For Code Changes
1. Test in both modes (internet and air-gap)
2. Update all relevant documentation
3. Add logging for new operations
4. Handle errors gracefully with user-friendly messages
5. Maintain the two-script architecture (executor + STIG script)

### For Documentation Updates
1. Use consistent emoji and formatting
2. Keep quick starts concise (one page)
3. Put details in comprehensive READMEs
4. Use checklists for procedures
5. Mark warnings clearly with [WARNING]

### For User Support
1. Direct users to appropriate documentation level
2. Emphasize testing before production
3. Remind about backups and console access
4. Provide rollback instructions when issues occur
5. Explain what will change on their system

---

## Related Resources

### DISA STIG Documentation
- STIG Library: https://public.cyber.mil/stigs/
- Ubuntu 20.04 STIG V2R3 Documentation
- SCAP Content: https://public.cyber.mil/stigs/scap/

### Technical References
- paramiko documentation: https://www.paramiko.org/
- OpenSCAP: https://www.open-scap.org/
- Ubuntu Security: https://ubuntu.com/security

### Compliance Frameworks
- NIST 800-53 (Security Controls)
- CIS Benchmarks (Security Best Practices)
- PCI-DSS (Payment Card Industry Standards)

---

## Quick Reference Commands

```powershell
# Setup (Internet mode)
pip install paramiko scp

# Run (Internet mode)
python windows_stig_remote_executor.py

# Setup (Air-gap mode) - On connected system
python download_dependencies.py
python build_airgap_package.py

# Run (Air-gap mode) - On isolated system
python airgap_windows_stig_executor.py

# Check Python version
python --version

# Test SSH manually
ssh username@target_ip

# View Windows logs
notepad %USERPROFILE%\stig_execution_logs\stig_execution_*.log
```

---

## Summary for AI Assistants

This repository provides Windows-based remote execution of Ubuntu STIG compliance automation. Key points:

1. **Two modes**: Internet-connected (simple) and air-gapped (secure)
2. **Two-script architecture**: Executor (handles connection) + STIG script (does remediation)
3. **High impact**: Applies 172 security controls to target Ubuntu system
4. **Safety first**: Always emphasize backups, testing, and console access
5. **Well documented**: 9 markdown files covering different user needs
6. **Python 3.6+**: Uses modern Python with paramiko for SSH

When helping users:
- Identify their mode (internet vs. air-gap)
- Guide to correct documentation
- Emphasize safety (backups, testing, console access)
- Provide clear troubleshooting steps
- Include rollback procedures when relevant

When modifying code:
- Maintain dual-mode support
- Update documentation comprehensively
- Preserve security posture
- Add appropriate logging
- Test in both modes

---

**Last Updated**: 2024-11-18
**Maintained By**: AI-assisted development
**For Questions**: Refer to comprehensive README files
