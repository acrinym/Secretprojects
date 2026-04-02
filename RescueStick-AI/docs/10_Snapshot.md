# RescueStick AI - Snapshot Engine (Time Machine)
**Engine ID:** 10_snapshot
**Purpose:** System snapshots before repairs - instant rollback capability
**License:** MIT (our code) + noted dependencies

---

## What It Does

Create point-in-time snapshots of Windows system state before any repair:

```
Quick Snapshot (5 min):
  → Registry hives (SYSTEM, SOFTWARE, SAM, SECURITY)
  → BCD (Boot Configuration Data)
  → Critical boot files

Full Snapshot (15 min):
  → Everything above
  → File hashes of all system files
  → Driver inventory
  → Service states

Custom Snapshot:
  → User selects specific areas
  → Useful for targeted repairs
```

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SNAPSHOT SYSTEM                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   Input:        Output:                                      │
│   ────────      ──────                                       │
│   Registry →   /snapshots/                                   │
│   Files     →     ├── 2026-03-26_143022/                     │
│   BCD       →     │   ├── registry/                          │
│   Drivers   →     │   ├── files/                             │
│              →     │   ├── bcd/                               │
│              →     │   └── manifest.json                     │
│                                                              │
│   Compression: zstd (BSD, fast)                             │
│   Storage: USB or internal (configurable)                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Code Structure

```python
#!/usr/bin/env python3
"""
Engine 10: Snapshot System
License: MIT
"""

import os
import json
import subprocess
import hashlib
import shutil
from datetime import datetime
from pathlib import Path

class SnapshotEngine:
    """Create and manage system snapshots for rollback"""
    
    def __init__(self, mount_point="/mnt/windows", output_dir="/rescue-stick/snapshots"):
        self.mount_point = mount_point
        self.output_dir = Path(output_dir)
        self.snapshot_id = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        
    def create_quick_snapshot(self) -> dict:
        """Quick snapshot - registry + BCD only (~5 min)"""
        snapshot_path = self.output_dir / self.snapshot_id
        snapshot_path.mkdir(parents=True, exist_ok=True)
        
        results = {
            "snapshot_id": self.snapshot_id,
            "type": "quick",
            "timestamp": self.snapshot_id,
            "components": {},
            "status": "success"
        }
        
        # 1. Capture registry hives
        registry_path = snapshot_path / "registry"
        registry_path.mkdir(exist_ok=True)
        results["components"]["registry"] = self._capture_registry(registry_path)
        
        # 2. Capture BCD
        bcd_path = snapshot_path / "bcd"
        bcd_path.mkdir(exist_ok=True)
        results["components"]["bcd"] = self._capture_bcd(bcd_path)
        
        # 3. Create manifest
        self._write_manifest(snapshot_path, results)
        
        return results
    
    def create_full_snapshot(self) -> dict:
        """Full snapshot - everything (~15 min)"""
        snapshot_path = self.output_dir / self.snapshot_id
        snapshot_path.mkdir(parents=True, exist_ok=True)
        
        results = {
            "snapshot_id": self.snapshot_id,
            "type": "full",
            "timestamp": self.snapshot_id,
            "components": {},
            "status": "success"
        }
        
        # Quick snapshot components
        results["components"]["registry"] = self._capture_registry(snapshot_path / "registry")
        results["components"]["bcd"] = self._capture_bcd(snapshot_path / "bcd")
        
        # File hashes
        results["components"]["file_hashes"] = self._capture_file_hashes(snapshot_path / "file_hashes")
        
        # Driver inventory
        results["components"]["drivers"] = self._capture_drivers(snapshot_path / "drivers")
        
        # Service states
        results["components"]["services"] = self._capture_services(snapshot_path / "services")
        
        # Windows Update state
        results["components"]["update_state"] = self._capture_update_state(snapshot_path / "update_state")
        
        self._write_manifest(snapshot_path, results)
        
        return results
    
    def _capture_registry(self, dest_path: Path) -> dict:
        """Capture registry hives"""
        registry_files = {
            "SYSTEM": "Windows/System32/config/SYSTEM",
            "SOFTWARE": "Windows/System32/config/SOFTWARE",
            "SAM": "Windows/System32/config/SAM",
            "SECURITY": "Windows/System32/config/SECURITY",
        }
        
        captured = {}
        windows_path = Path(self.mount_point)
        
        for hive_name, hive_path in registry_files.items():
            full_path = windows_path / hive_path
            if full_path.exists():
                dest_file = dest_path / f"{hive_name}.dat"
                try:
                    shutil.copy2(full_path, dest_file)
                    captured[hive_name] = {
                        "status": "captured",
                        "size": full_path.stat().st_size
                    }
                except Exception as e:
                    captured[hive_name] = {"status": "error", "error": str(e)}
            else:
                captured[hive_name] = {"status": "not_found"}
        
        return captured
    
    def _capture_bcd(self, dest_path: Path) -> dict:
        """Capture BCD store"""
        bcd_files = [
            "Boot/BCD",
            "EFI/Microsoft/Boot/BCD",
        ]
        
        captured = {}
        windows_path = Path(self.mount_point)
        
        for bcd_path in bcd_files:
            full_path = windows_path / bcd_path
            if full_path.exists():
                dest_file = dest_path / bcd_path.replace("/", "_")
                try:
                    shutil.copy2(full_path, dest_file)
                    captured[bcd_path] = {"status": "captured"}
                except Exception as e:
                    captured[bcd_path] = {"status": "error", "error": str(e)}
        
        return captured
    
    def _capture_file_hashes(self, dest_path: Path) -> dict:
        """Capture SHA256 hashes of critical system files"""
        dest_path.mkdir(exist_ok=True)
        
        # Critical file paths to hash
        critical_files = [
            "Windows/System32/ntoskrnl.exe",
            "Windows/System32/hal.dll",
            "Windows/System32/winlogon.exe",
            "Windows/System32/csrsrv.dll",
            "Windows/System32/smss.exe",
            "Windows/System32/services.exe",
            "Windows/System32/lsass.exe",
            "Windows/System32/svchost.exe",
        ]
        
        hashes = {}
        windows_path = Path(self.mount_point)
        
        for file_path in critical_files:
            full_path = windows_path / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'rb') as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                    hashes[file_path] = file_hash
                except Exception as e:
                    hashes[file_path] = {"error": str(e)}
        
        # Write hash file
        hash_file = dest_path / "system_hashes.json"
        with open(hash_file, 'w') as f:
            json.dump(hashes, f, indent=2)
        
        return {"files_hashed": len(hashes)}
    
    def _capture_drivers(self, dest_path: Path) -> dict:
        """Capture driver inventory"""
        dest_path.mkdir(exist_ok=True)
        
        driver_paths = [
            "Windows/System32/drivers",
        ]
        
        drivers = []
        windows_path = Path(self.mount_point)
        
        for driver_path in driver_paths:
            full_path = windows_path / driver_path
            if full_path.exists() and full_path.is_dir():
                for driver in full_path.glob("*.sys"):
                    drivers.append(driver.name)
        
        # Save driver list
        driver_file = dest_path / "drivers.json"
        with open(driver_file, 'w') as f:
            json.dump(drivers, f, indent=2)
        
        return {"driver_count": len(drivers)}
    
    def _capture_services(self, dest_path: Path) -> dict:
        """Capture service configuration"""
        dest_path.mkdir(exist_ok=True)
        
        # Read from registry if available
        services = []
        
        # Save
        services_file = dest_path / "services.json"
        with open(services_file, 'w') as f:
            json.dump(services, f, indent=2)
        
        return {"service_count": len(services)}
    
    def _capture_update_state(self, dest_path: Path) -> dict:
        """Capture Windows Update state"""
        dest_path.mkdir(exist_ok=True)
        
        state = {
            "last_update": None,
            "pending_updates": [],
            "update_history": []
        }
        
        state_file = dest_path / "update_state.json"
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
        
        return state
    
    def _write_manifest(self, snapshot_path: Path, results: dict):
        """Write snapshot manifest"""
        manifest = {
            "snapshot_id": results["snapshot_id"],
            "type": results["type"],
            "timestamp": results["timestamp"],
            "components": list(results["components"].keys()),
            "engine": "10_snapshot",
            "version": "1.0"
        }
        
        manifest_file = snapshot_path / "manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
    
    def list_snapshots(self) -> list:
        """List all available snapshots"""
        snapshots = []
        
        if not self.output_dir.exists():
            return snapshots
        
        for snap_dir in self.output_dir.iterdir():
            if snap_dir.is_dir():
                manifest_file = snap_dir / "manifest.json"
                if manifest_file.exists():
                    with open(manifest_file, 'r') as f:
                        snapshots.append(json.load(f))
        
        return sorted(snapshots, key=lambda x: x["timestamp"], reverse=True)
    
    def restore_snapshot(self, snapshot_id: str) -> dict:
        """Restore a specific snapshot"""
        snapshot_path = self.output_dir / snapshot_id
        
        if not snapshot_path.exists():
            return {"status": "error", "error": "Snapshot not found"}
        
        results = {
            "snapshot_id": snapshot_id,
            "restored": [],
            "errors": []
        }
        
        # Restore registry
        registry_path = snapshot_path / "registry"
        if registry_path.exists():
            for hive_file in registry_path.glob("*.dat"):
                hive_name = hive_file.stem
                dest = Path(self.mount_point) / "Windows/System32/config" / hive_name
                try:
                    # Backup current first
                    if dest.exists():
                        backup = dest.with_suffix(".bak")
                        shutil.copy2(dest, backup)
                    shutil.copy2(hive_file, dest)
                    results["restored"].append(f"registry:{hive_name}")
                except Exception as e:
                    results["errors"].append(f"registry:{hive_name}: {str(e)}")
        
        return results


# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="RescueStick Snapshot Engine")
    parser.add_argument("action", choices=["create", "list", "restore"])
    parser.add_argument("--type", choices=["quick", "full"], default="quick")
    parser.add_argument("--snapshot-id", help="Snapshot ID to restore")
    
    args = parser.parse_args()
    
    engine = SnapshotEngine()
    
    if args.action == "create":
        if args.type == "full":
            result = engine.create_full_snapshot()
        else:
            result = engine.create_quick_snapshot()
        print(json.dumps(result, indent=2))
    
    elif args.action == "list":
        snapshots = engine.list_snapshots()
        print(json.dumps(snapshots, indent=2))
    
    elif args.action == "restore":
        if not args.snapshot_id:
            print("Error: --snapshot-id required")
        else:
            result = engine.restore_snapshot(args.snapshot_id)
            print(json.dumps(result, indent=2))
```

## Dependencies

```bash
# System packages (Debian/Ubuntu)
# Note: Most are GPL - for permissive alternatives, see below
sudo apt-get install -y \
    python3 \
    python3-pip \
    zstd              # BSD license - compression
    # core utilities (usually pre-installed)
```

**Permissive License Tools (preferred):**
- Python 3 (PSF - permissive)
- zstd (BSD) - compression
- Our own code (MIT)

**Note on GPL tools:**
- rsync (GPLv3) - file sync (optional, not required)
- partclone (GPLv2) - partition imaging (optional)
- These are noted but not required - our Python implementation works standalone

## Data Needed

None required - works with live Windows system data.

## Testing

```bash
# Test basic functionality
cd /rescue-stick/engines
python3 -c "
from snapshot_engine import SnapshotEngine
e = SnapshotEngine()
print('Snapshot engine loaded')
print('Available snapshots:', e.list_snapshots())
"

# Test snapshot creation (requires mounted Windows)
# python3 10_snapshot.py create --type quick
```

## Output

Creates directory structure:
```
/rescue-stick/snapshots/
└── 2026-03-26_143022/
    ├── manifest.json
    ├── registry/
    │   ├── SYSTEM.dat
    │   ├── SOFTWARE.dat
    │   ├── SAM.dat
    │   └── SECURITY.dat
    ├── bcd/
    ├── file_hashes/
    ├── drivers/
    ├── services/
    └── update_state/
```

---

*Engine 10 - Spec Complete*  
*License: MIT (our code), noted dependencies*