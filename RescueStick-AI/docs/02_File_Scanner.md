# RescueStick AI - File Scanner Engine
**Engine ID:** 02_file_scanner  
**Purpose:** System file inventory, hash verification, corruption detection  
**Dependencies:** Python 3.10+, pytsk3 (SleuthKit), ntfs-3g

---

## What It Does

1. **Scans** all system files on Windows partition (System32, SysWOW64, Program Files, etc.)
2. **Calculates** SHA256 hashes for each file
3. **Compares** against Microsoft baseline databases
4. **Detects** corrupted, modified, or missing files
5. **Reports** severity and repair recommendations

---

## How to Build It

### Step 1: Understanding File Locations

Windows key directories to scan:

```
C:\Windows\System32          - 64-bit system files
C:\:\Windows\SysWOW64        - 32-bit system files (on 64-bit Windows)
C:\Windows\Sysnative        - 32-bit system files (on 64-bit Windows, from 32-bit process)
C:\Program Files            - 64-bit programs
C:\Program Files (x86)      - 32-bit programs
C:\Windows\WinSxS          - Windows component store
C:\Windows\System32\Catroot - Certificate trust list
C:\Windows\System32\Catroot2
C:\Windows\System32\DriverStore - Driver inventory
C:\Windows\Servicing\Packages - Update packages
```

### Step 2: Install Dependencies

```bash
# Linux build dependencies
sudo apt-get install:
    - ntfs-3g              # NTFS read/write support
    - sleuthkit            # File system forensic tools
    - libtsk-dev           # Python bindings for SleuthKit
    - python3-yara         # YARA rules for malware detection

pip install:
    - pytsk                # Python bindings for The SleuthKit
    - pytsk3               # Alternative bindings
    - yara-python          # YARA pattern matching
```

### Step 3: Core Code Structure

```python
# engines/02_file_scanner.py

import os
import hashlib
import struct
from pathlib import Path
from typing import Dict, List, Optional, Iterator
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

@dataclass
class FileInfo:
    """Information about a scanned file."""
    path: str
    size: int
    sha256: str
    modified_time: int
    is_system_file: bool
    is_corrupted: bool
    expected_hash: Optional[str]
    severity: str  # 'critical', 'high', 'medium', 'low', 'info'

class WindowsFileScanner:
    """
    Scans Windows filesystem, calculates hashes, detects corruption.
    """
    
    # Directories considered "system critical"
    SYSTEM_DIRECTORIES = {
        'Windows/System32',
        'Windows/SysWOW64', 
        'Windows/Sysnative',
        'Windows/WinSxS',
        'Windows/Catroot',
        'Windows/Catroot2',
        'Windows/Servicing',
        'Windows/Inf',
        'Windows/DriverStore',
    }
    
    # File extensions that are critical system files
    CRITICAL_EXTENSIONS = {
        '.dll', '.exe', '.sys', '.ocx', '.cpl',
        '.drv', '.tsp', '.msi', '.msp'
    }
    
    def __init__(self, mount_point: str):
        self.mount_point = Path(mount_point)
        self.files_scanned = 0
        self.issues_found = []
        
    def scan_directory(self, directory: str, max_files: Optional[int] = None) -> Iterator[FileInfo]:
        """
        Recursively scan a directory, yield FileInfo for each file.
        
        Args:
            directory: Relative path from mount point (e.g., "Windows/System32")
            max_files: Optional limit for testing
        """
        full_path = self.mount_point / directory
        
        for root, dirs, files in os.walk(full_path):
            for filename in files:
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, self.mount_point)
                
                try:
                    info = self._get_file_info(rel_path)
                    yield info
                    self.files_scanned += 1
                    
                    if max_files and self.files_scanned >= max_files:
                        return
                        
                except Exception as e:
                    # Log but continue - some files may be locked
                    self.issues_found.append({
                        'path': rel_path,
                        'error': str(e),
                        'type': 'access_error'
                    })
    
    def _get_file_info(self, rel_path: str) -> FileInfo:
        """Get detailed info about a single file."""
        full_path = self.mount_point / rel_path
        
        stat = os.stat(full_path)
        is_system = any(rel_path.startswith(d) for d in self.SYSTEM_DIRECTORIES)
        
        # Calculate hash (read in chunks for large files)
        sha256 = self._calculate_sha256(full_path)
        
        # Check if it's a critical file type
        ext = os.path.splitext(rel_path)[1].lower()
        is_critical = ext in self.CRITICAL_EXTENSIONS
        
        return FileInfo(
            path=rel_path,
            size=stat.st_size,
            sha256=sha256,
            modified_time=int(stat.st_mtime),
            is_system_file=is_system,
            is_corrupted=False,
            expected_hash=None,
            severity='info'
        )
    
    def _calculate_sha256(self, file_path: str) -> str:
        """Calculate SHA256 hash, handling large files."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            # Read in 64KB chunks
            for chunk in iter(lambda: f.read(65536), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def verify_against_baseline(self, file_info: FileInfo, baseline_db: Dict) -> FileInfo:
        """
        Check if file hash matches known-good baseline.
        
        Args:
            file_info: Scanned file
            baseline_db: Dict of path -> sha256 from known-good installation
        """
        expected = baseline_db.get(file_info.path)
        
        if expected is None:
            # Unknown file - could be added by user or malware
            file_info.severity = 'low'
        elif expected != file_info.sha256:
            # Hash mismatch - file is corrupted or modified
            file_info.is_corrupted = True
            file_info.expected_hash = expected
            
            # Determine severity based on file location
            if file_info.is_system_file:
                file_info.severity = 'high'
            else:
                file_info.severity = 'medium'
        
        return file_info
```

### Step 4: Building the Baseline Database

```python
# tools/build_baseline.py

"""
Build hash baseline from known-good Windows installations.

Process:
1. Boot various Windows versions in VM
2. Run this scanner on clean install
3. Store results in database
4. Use for comparison during repairs
"""

import json
import sqlite3
from pathlib import Path
from windows_file_scanner import WindowsFileScanner

def build_baseline(os_version: str, mount_point: str, output_db: str):
    """
    Build hash baseline from a clean Windows installation.
    
    Args:
        os_version: "win10-22h2", "win11-23h2", etc.
        mount_point: Path to mounted Windows partition
        output_db: Path to output SQLite database
    """
    conn = sqlite3.connect(output_db)
    cursor = conn.cursor()
    
    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_baselines (
            id INTEGER PRIMARY KEY,
            os_version TEXT NOT NULL,
            file_path TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            file_size INTEGER,
            is_critical INTEGER,
            INDEX idx_path (file_path),
            INDEX idx_os (os_version)
        )
    ''')
    
    scanner = WindowsFileScanner(mount_point)
    
    # Scan critical directories
    critical_dirs = [
        'Windows/System32',
        'Windows/SysWOW64',
        'Windows/WinSxS',
        'Windows/Inf',
    ]
    
    for directory in critical_dirs:
        print(f"Scanning {directory}...")
        for file_info in scanner.scan_directory(directory):
            cursor.execute('''
                INSERT INTO file_baselines 
                (os_version, file_path, sha256, file_size, is_critical)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                os_version,
                file_info.path,
                file_info.sha256,
                file_info.size,
                1 if file_info.is_system_file else 0
            ))
    
    conn.commit()
    conn.close()
    print(f"Baseline created: {output_db}")

# Run for each OS version:
# build_baseline("win10-22h2", "/mnt/win10-clean", "data/baselines/win10-22h2.db")
```

### Step 5: Quick Scan Mode (Optimized)

For faster scans, use file size + first/last chunk hash:

```python
class QuickScanner:
    """
    Fast hash verification - only recalculates full hash if quick check fails.
    """
    
    QUICK_HASH_SIZE = 8192  # First and last 8KB
    
    def quick_hash(self, file_path: str) -> str:
        """
        Create quick hash from:
        - File size
        - First 8KB
        - Last 8KB
        - File name
        
        Much faster for initial pass.
        """
        stat = os.stat(file_path)
        
        with open(file_path, 'rb') as f:
            first_chunk = f.read(self.QUICK_HASH_SIZE)
            f.seek(max(0, stat.st_size - self.QUICK_HASH_SIZE))
            last_chunk = f.read(self.QUICK_HASH_SIZE)
        
        quick = hashlib.sha256()
        quick.update(str(stat.st_size).encode())
        quick.update(first_chunk)
        quick.update(last_chunk)
        quick.update(os.path.basename(file_path).encode())
        
        return quick.hexdigest()
```

---

## Data Files Structure

```
data/
├── baselines/
│   ├── win10-20h2.db      # SQLite with hashes
│   ├── win10-21h2.db
│   ├── win10-22h2.db
│   ├── win11-22h2.db
│   ├── win11-23h2.db
│   └── win-server-2019.db
├── quick_hashes/          # Pre-computed quick hashes for fast scanning
└── file_index.db          # Global index of all known files
```

---

## Performance Notes

- Full scan of System32: ~15-30 minutes on SSD
- Quick scan mode: ~2-5 minutes
- Run in parallel threads for multiple directories
- Cache frequently accessed file hashes

---

## Testing

```bash
# Test on Windows VM
# 1. Boot VM with known corrupted files
# 2. Mount with RescueStick
# 3. Run scanner
# 4. Verify it finds the known issues
```

---

*Engine Status: SPEC COMPLETE - Implementation ready to begin*