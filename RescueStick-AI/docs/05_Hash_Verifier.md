# RescueStick AI - Hash Verifier Engine
**Engine ID:** 05_hash_verifier  
**Purpose:** Compare scanned files against known-good baselines, score integrity, prioritize repairs  
**Dependencies:** Python 3.10+, SQLite3

---

## What It Does

1. **Loads** baseline hash databases for the target Windows version
2. **Compares** scanned file hashes against baselines
3. **Scores** file integrity (0-100%)
4. **Prioritizes** repairs by severity and system impact
5. **Reports** actionable findings to synthesis engine

---

## How to Build It

### Step 1: Database Schema

```python
# Create baseline database tables

CREATE TABLE IF NOT EXISTS os_versions (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,           -- "Windows 10 22H2"
    version_string TEXT,          -- "10.0.19045 N/A Build 19045"
    build_number INTEGER,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS file_baselines (
    id INTEGER PRIMARY KEY,
    os_version_id INTEGER,
    file_path TEXT NOT NULL,      -- "Windows/System32/ntoskrnl.exe"
    sha256 TEXT NOT NULL,
    file_size INTEGER,
    is_critical INTEGER DEFAULT 0,  -- 1 if system-critical
    category TEXT,                -- "kernel", "driver", "dll", "exe"
    INDEX idx_path (file_path),
    INDEX idx_os (os_version_id)
);

CREATE TABLE IF NOT EXISTS known_issues (
    id INTEGER PRIMARY KEY,
    os_version_id INTEGER,
    file_path TEXT,
    expected_hash TEXT,
    description TEXT,
    repair_method TEXT
);
```

### Step 2: Core Code Structure

```python
# engines/05_hash_verifier.py

import sqlite3
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class IntegrityScore(Enum):
    PRISTINE = "pristine"      # 100% match
    MODIFIED = "modified"     # Hash mismatch - intentional change
    CORRUPTED = "corrupted"   # Hash mismatch - damage
    MISSING = "missing"       # File doesn't exist
    UNKNOWN = "unknown"       # Not in baseline

@dataclass
class VerificationResult:
    """Result of hash verification for a single file."""
    path: str
    expected_hash: Optional[str]
    actual_hash: Optional[str]
    score: IntegrityScore
    severity: str          # "critical", "high", "medium", "low"
    repair_priority: int   # 1 (highest) to 10
    repair_method: Optional[str]
    is_system_critical: bool

@dataclass
class OverallIntegrityReport:
    """Overall system integrity report."""
    os_version: str
    total_files_checked: int
    pristine_count: int
    modified_count: int
    corrupted_count: int
    missing_count: int
    unknown_count: int
    integrity_score: float    # 0-100
    critical_issues: List[VerificationResult]
    recommended_repairs: List[VerificationResult]

class HashVerifier:
    """
    Verifies file hashes against known-good baselines.
    
    Compares scanned files to baseline databases, identifies issues,
    prioritizes repairs.
    """
    
    def __init__(self, baseline_db_path: str):
        self.db_path = baseline_db_path
        self.conn = None
        self.os_version = None
        
    def connect(self) -> bool:
        """Open database connection."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            return True
        except Exception as e:
            print(f"Error connecting to baseline DB: {e}")
            return False
    
    def detect_os_version(self, mount_point: str) -> Optional[Dict]:
        """
        Detect Windows version from mounted drive.
        
        Reads:
        - Windows/System32/ntoskrnl.exe version info
        - Windows/System32/config/SYSTEM - CurrentControlSet
        - Windows/servicing/versions - build version
        """
        import pefile
        
        # Method 1: Check ntoskrnl.exe version
        kernel_path = Path(mount_point) / "Windows" / "System32" / "ntoskrnl.exe"
        if kernel_path.exists():
            pe = pefile.PE(str(kernel_path))
            vs = pe.VSFixedFileInfo
            # Extract version info
            
        # Method 2: Check registry
        # Read SYSTEM hive, find CurrentControlSet
        
        # Return detected version
        return {
            "name": "Windows 10 22H2",
            "build": 19045,
            "version": "10.0.19045 N/A Build 19045"
        }
    
    def load_baseline_for_os(self, os_version: Dict) -> bool:
        """Load baseline hashes for detected OS version."""
        cursor = self.conn.cursor()
        
        # Find matching OS in database
        cursor.execute('''
            SELECT id FROM os_versions 
            WHERE name LIKE ? OR build_number = ?
        ''', (f"%{os_version['name']}%", os_version['build']))
        
        result = cursor.fetchone()
        if result:
            self.os_version = {
                'id': result[0],
                **os_version
            }
            return True
        return False
    
    def verify_file(self, file_path: str, actual_hash: str, is_critical: bool) -> VerificationResult:
        """
        Verify a single file against baseline.
        
        Returns detailed verification result.
        """
        cursor = self.conn.cursor()
        
        # Look up expected hash
        cursor.execute('''
            SELECT sha256, category FROM file_baselines
            WHERE os_version_id = ? AND file_path = ?
        ''', (self.os_version['id'], file_path))
        
        result = cursor.fetchone()
        
        if not result:
            # File not in baseline - could be user-added
            return VerificationResult(
                path=file_path,
                expected_hash=None,
                actual_hash=actual_hash,
                score=IntegrityScore.UNKNOWN,
                severity="low",
                repair_priority=10,
                repair_method=None,
                is_system_critical=is_critical
            )
        
        expected_hash, category = result
        
        if actual_hash == expected_hash:
            # Perfect match
            return VerificationResult(
                path=file_path,
                expected_hash=expected_hash,
                actual_hash=actual_hash,
                score=IntegrityScore.PRISTINE,
                severity="none",
                repair_priority=10,
                repair_method=None,
                is_system_critical=is_critical
            )
        
        # Hash mismatch - determine if corrupted or intentionally modified
        # If it's a user config file, might be intentional
        # If it's a system DLL, likely corrupted
        
        if category in ['dll', 'exe', 'sys', 'kernel']:
            score = IntegrityScore.CORRUPTED
            severity = "critical" if is_critical else "high"
            repair_priority = 1
            repair_method = "Replace from DISM/Source"
        else:
            score = IntegrityScore.MODIFIED
            severity = "medium"
            repair_priority = 5
            repair_method = "Review and restore if needed"
        
        return VerificationResult(
            path=file_path,
            expected_hash=expected_hash,
            actual_hash=actual_hash,
            score=score,
            severity=severity,
            repair_priority=repair_priority,
            repair_method=repair_method,
            is_system_critical=is_critical
        )
    
    def verify_missing_file(self, file_path: str, is_critical: bool) -> VerificationResult:
        """Handle missing file case."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT sha256, category FROM file_baselines
            WHERE os_version_id = ? AND file_path = ?
        ''', (self.os_version['id'], file_path))
        
        result = cursor.fetchone()
        
        if result:
            expected_hash, category = result
            severity = "critical" if is_critical else "high"
            repair_priority = 1 if is_critical else 3
            
            return VerificationResult(
                path=file_path,
                expected_hash=expected_hash,
                actual_hash=None,
                score=IntegrityScore.MISSING,
                severity=severity,
                repair_priority=repair_priority,
                repair_method="Download from Microsoft Update/DISM",
                is_system_critical=is_critical
            )
        
        # Not in baseline - may not be required
        return VerificationResult(
            path=file_path,
            expected_hash=None,
            actual_hash=None,
            score=IntegrityScore.UNKNOWN,
            severity="low",
            repair_priority=10,
            repair_method=None,
            is_system_critical=is_critical
        )
    
    def generate_report(self, results: List[VerificationResult]) -> OverallIntegrityReport:
        """
        Generate overall integrity report from verification results.
        """
        total = len(results)
        if total == 0:
            return OverallIntegrityReport(
                os_version=self.os_version['name'] if self.os_version else "Unknown",
                total_files_checked=0,
                pristine_count=0,
                modified_count=0,
                corrupted_count=0,
                missing_count=0,
                unknown_count=0,
                integrity_score=100.0,
                critical_issues=[],
                recommended_repairs=[]
            )
        
        pristine = sum(1 for r in results if r.score == IntegrityScore.PRISTINE)
        modified = sum(1 for r in results if r.score == IntegrityScore.MODIFIED)
        corrupted = sum(1 for r in results if r.score == IntegrityScore.CORRUPTED)
        missing = sum(1 for r in results if r.score == IntegrityScore.MISSING)
        unknown = sum(1 for r in results if r.score == IntegrityScore.UNKNOWN)
        
        # Calculate integrity score (0-100)
        integrity_score = (pristine / total) * 100
        
        # Get critical issues
        critical = [r for r in results if r.severity == "critical"]
        
        # Get recommended repairs (sorted by priority)
        repairs = sorted(
            [r for r in results if r.repair_method],
            key=lambda x: x.repair_priority
        )[:20]  # Top 20 repairs
        
        return OverallIntegrityReport(
            os_version=self.os_version['name'] if self.os_version else "Unknown",
            total_files_checked=total,
            pristine_count=pristine,
            modified_count=modified,
            corrupted_count=corrupted,
            missing_count=missing,
            unknown_count=unknown,
            integrity_score=round(integrity_score, 2),
            critical_issues=critical,
            recommended_repairs=repairs
        )
```

### Step 3: Integration with File Scanner

```python
# Integration: Run after File Scanner completes

def verify_scan_results(scanner_results: List[FileInfo], baseline_db: str):
    """
    Verify file scanner results against baseline.
    """
    verifier = HashVerifier(baseline_db)
    verifier.connect()
    
    results = []
    for file_info in scanner_results:
        result = verifier.verify_file(
            file_info.path,
            file_info.sha256,
            file_info.is_system_file
        )
        results.append(result)
    
    report = verifier.generate_report(results)
    
    # Pass to synthesis engine
    return report
```

---

## Baseline Database Structure

```
data/
├── baselines/
│   ├── win10-20h2.db
│   ├── win10-21h1.db
│   ├── win10-22h2.db
│   ├── win11-22h2.db
│   ├── win11-23h2.db
│   ├── win-server-2019.db
│   └── win-server-2022.db
```

Each database contains:
- os_versions table
- file_baselines table (millions of entries)
- known_issues table

---

## How to Build Baselines

```bash
# tools/build_baseline.py

"""
Build hash baseline from known-good Windows installation.
Run on a clean Windows VM, export to SQLite.
"""

# Use Engine 02 File Scanner to scan clean installation
# Output to SQLite database
# Store in data/baselines/
```

---

## Testing

```bash
# Test on Windows with known corrupted files
# 1. Run File Scanner to get hashes
# 2. Run Hash Verifier against baseline
# 3. Verify it correctly identifies issues
# 4. Check repair prioritization makes sense
```

---

*Engine Status: SPEC COMPLETE - Implementation ready to begin*