# RescueStick AI - Registry Decorrupter Engine
**Engine ID:** 03-registry_parser  
**Purpose:** Analyze, repair, and restore Windows registry hives  
**Dependencies:** Python 3.10+, chntpw, hivex, pyregf

---

## What It Does

1. **Reads** Windows registry hives (SYSTEM, SOFTWARE, SECURITY, SAM, DEFAULT, USRCLASS.DAT, NTUSER.DAT)
2. **Analyzes** for corruption, missing keys, permission issues, wrong ownership
3. **Backs up** before any changes
4. **Repairs** common issues:
   - Orphaned keys
   - Broken value types
   - Missing security descriptors
   - Transaction log mismatches
5. **Restores** from backup or rebuilds from known-good sources

---

## How to Build It

### Step 1: Get Fresh Registry Copies from Each Windows Version

You need baseline registry hives for each OS version to compare against:

```bash
# Create directory structure
mkdir -p data/registry_baselines/{win10,win11,win-server-2019,win-server-2022}

# Method A: From Microsoft VMs (recommended)
# Download Windows evaluation VMs from:
# https://developer.microsoft.com/en-us/windows/downloads/virtual-machines/

# Method B: From working installations
# Boot RescueStick, mount target Windows, copy:
# Windows/System32/config/SYSTEM
# Windows/System32/config/SOFTWARE
# Windows/System32/config/SECURITY
# Windows/System32/config/SAM
# Windows/System32/config/DEFAULT

# Method C: From Windows ISO
# Extract install.wim, copy registry from mounted image

# Validate each copy - must be valid, non-corrupted
# SHA256 hash each baseline file
```

### Step 2: Install Required Tools

```bash
# On your build machine (Ubuntu/Debian)
sudo apt-get install:
    - libhivex-bin          # Binary tools for reading hives
    - chntpw                # Registry password utility (can reset, view)
    - python3-hivex        # Python bindings
    - python3-pyregf       # Python registry parsing
    - reglookup            # Command-line registry viewer
    - wine                 # For some Windows-only tools

# Python dependencies
pip install:
    - hivex                 # Python bindings
    - construct            # Binary parsing
    - pefile               # PE file analysis (for DLL/EXE in registry)
```

### Step 3: Core Code Structure

```python
# engines/03_registry_parser.py

import os
import struct
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class RegistryParser:
    """
    Windows Registry Analysis and Repair Engine
    
    Supported hives:
    - HKEY_LOCAL_MACHINE\SYSTEM (SYSTEM)
    - HKEY_LOCAL_MACHINE\SOFTWARE (SOFTWARE)
    - HKEY_LOCAL_MACHINE\SECURITY (SECURITY)
    - HKEY_LOCAL_MACHINE\SAM (SAM)
    - HKEY_USERS\.DEFAULT (DEFAULT)
    - HKEY_CURRENT_USER (USRCLASS.DAT in user folder)
    """
    
    def __init__(self, baseline_path: str):
        self.baseline_path = Path(baseline_path)
        self.hives = {}
        self.backups = {}
        
    def mount_hive(self, hive_path: str, mount_point: str) -> bool:
        """
        Mount a registry hive for reading.
        
        Windows registries are stored as:
        - C:\Windows\System32\config\SYSTEM
        - C:\Windows\System32\config\SOFTWARE
        
        On Linux (RescueStick), use hivex or chntpw to read.
        """
        # Use hivex to read the hive
        # Alternative: Usechntpw -l hivefile to list
        pass
    
    def analyze_hive(self, hive_path: str) -> Dict:
        """
        Full analysis of a registry hive.
        
        Returns:
        {
            'corrupted': bool,
            'issues': [
                {'type': 'missing_key', 'path': '...', 'severity': 'high'},
                {'type': 'bad_value', 'path': '...', 'expected_type': '...'},
                {'type': 'permission_issue', 'path': '...'},
                {'type': 'log_mismatch', 'path': '...'},
            ],
            'hash_matches_baseline': bool,
            'missing_keys': [...],
            'extra_keys': [...],
        }
        """
        pass
    
    def compare_to_baseline(self, hive_path: str, os_version: str) -> Dict:
        """
        Compare current hive to baseline for that OS version.
        
        Need to download baselines for:
        - Windows 10 20H2, 21H1, 21H2, 22H2
        - Windows 11 22H2, 23H2
        - Windows Server 2019, 2022
        """
        baseline = self.load_baseline(os_version)
        return self._diff_hives(current_hive, baseline)
    
    def backup_hive(self, hive_path: str) -> str:
        """
        Create backup before any repair.
        Store in: /rescue-stick/data/backups/{timestamp}/
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(f"/rescue-stick/data/backups/{timestamp}")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy hive file
        backup_path = backup_dir / Path(hive_path).name
        shutil.copy2(hive_path, backup_path)
        
        # Also copy transaction log if exists
        log_path = hive_path + ".LOG1"
        if os.path.exists(log_path):
            shutil.copy2(log_path, backup_dir / "LOG1")
        
        # Create metadata
        with open(backup_dir / "meta.txt", "w") as f:
            f.write(f"Backup of {hive_path}\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"SHA256: {sha256(backup_path)}\n")
        
        return str(backup_path)
    
    def repair_hive(self, hive_path: str, issues: List[Dict]) -> bool:
        """
        Attempt to repair identified issues.
        
        Common repairs:
        1. Remove orphaned keys (keys with no parent)
        2. Fix value type mismatches
        3. Rebuild security descriptors
        4. Clear transaction log mismatches
        
        For complex repairs, recommend offline registry edit:
        - Boot to WinRE
        - Use regedit to load hive
        - Manual repair
        """
        # Backup first
        self.backup_hive(hive_path)
        
        # Attempt repairs based on issue type
        for issue in issues:
            if issue['type'] == 'orphaned_key':
                self._remove_orphaned_key(hive_path, issue['path'])
            elif issue['type'] == 'bad_value_type':
                self._fix_value_type(hive_path, issue['path'], issue['value'])
            # ... etc
```

### Step 4: DLL Files Integration

```python
# Get DLL files from dll-files.com or Microsoft
# For missing DLLs, the repair engine should:

class DLLResolver:
    """
    Resolve missing DLL dependencies.
    Sources: dll-files.com API, Microsoft, local cache
    """
    
    def __init__(self):
        self.cache_dir = Path("/rescue-stick/data/dll_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
    def find_dll(self, dll_name: str, os_version: str) -> Optional[bytes]:
        """
        Find a DLL file from:
        1. Local cache (pre-downloaded DLLs)
        2. dll-files.com API
        3. Windows component store (DISM)
        4. Microsoft Update Catalog
        """
        # Check local cache first
        local = self.cache_dir / f"{dll_name}_{os_version}.dll"
        if local.exists():
            return local.read_bytes()
        
        # Try dll-files.com (they have many DLLs)
        # Note: Check their terms - some are free, some paid
        
        # Try DISM
        # DismGetCapabilities / DismGetPackageInfo
        
        return None
    
    def verify_dll_hash(self, dll_data: bytes, expected_hash: str) -> bool:
        """Verify DLL matches expected Microsoft hash."""
        actual = hashlib.sha256(dll_data).hexdigest()
        return actual.lower() == expected_hash.lower()
```

### Step 5: Framework Resolution

```python
class FrameworkResolver:
    """
    Detect and repair missing .NET, VC++ runtimes, etc.
    """
    
    FRAMEWORK_REGISTRY_PATHS = {
        'dotnet': [
            'HKLM\\SOFTWARE\\Microsoft\\NET Framework Setup\\NDP\\v4\\Full',
            'HKLM\\SOFTWARE\\Microsoft\\NET Framework Setup\\NDP\\v4\\Client',
        ],
        'vc_runtime': [
            'HKLM\\SOFTWARE\\Microsoft\\VisualStudio\\14.0\\VC\\Runtimes\\x64',
        ],
    }
    
    def detect_installed_frameworks(self) -> Dict[str, str]:
        """Read registry to find installed frameworks."""
        frameworks = {}
        # Read from registry parser results
        return frameworks
    
    def get_missing_frameworks(self, target_os: str) -> List[str]:
        """Compare installed vs required for that OS."""
        pass
    
    def install_framework(self, framework_name: str) -> bool:
        """
        Download and install framework via DISM or direct installer.
        """
        # DISM: Add-WindowsCapability
        # Or download from Microsoft Update Catalog
```

---

## Data Files Needed

### Registry Baselines (download/create)

```
data/registry_baselines/
├── win10-20h2/
│   ├── SYSTEM.sha256
│   ├── SOFTWARE.sha256
│   └── metadata.json
├── win10-21h1/
├── win10-22h2/
├── win11-22h2/
├── win11-23h2/
├── win-server-2019/
└── win-server-2022/
```

### DLL Cache (populate over time)

```
data/dll_cache/
├── msvcp140.dll_win10.bin
├── vcruntime140.dll_win11.bin
└── metadata.db (index of what's in cache)
```

### Known-Good Values Database

```
data/registry_values.db
-- SQLite database of:
-- - Critical registry keys by OS version
-- - Expected values for important settings
-- - Security descriptor templates
```

---

## Testing

```bash
# Test on virtual machine
# 1. Create Windows VM with known issues
# 2. Boot RescueStick USB
# 3. Run registry parser on the VM's hives
# 4. Verify detection and repair accuracy
```

---

## Key References

- **chntpw:** http://pogostick.net/~pnh/chntpw/
- **HiveX:** https://github.com/libguestfs/hivex
- **Windows Registry File Format:** https://github.com/libyal/libregf
- **DISM API:** https://docs.microsoft.com/en-us/windows-hardware/manufacture/desktop/dism-api

---

*Engine Status: SPEC COMPLETE - Implementation ready to begin*