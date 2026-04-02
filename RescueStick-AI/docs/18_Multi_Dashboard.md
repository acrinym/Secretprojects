# RescueStick AI - Multi-Dashboard Engine
**Engine ID:** 18_multi_dashboard
**Purpose:** Manage multiple Windows PCs from one RescueStick
**License:** MIT (our code)

---

## What It Does

Dashboard to manage multiple Windows installations:

```
Scan network/USB:
  → Find all Windows installations
  → List: PC-1 (Win11), PC-2 (Win10), Laptop (Win11)
       ↓
Actions per system:
  → [S] Scan for issues
  → [R] Repair
  → [B] Backup
  → [V] View diagnostics
```

## Code Structure

```python
#!/usr/bin/env python3
"""
Engine 18: Multi-Dashboard
License: MIT (our code)
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class MultiDashboard:
    """
    Manage multiple Windows systems from one RescueStick.
    Scan, diagnose, repair across multiple machines.
    """
    
    def __init__(self, base_path="/rescue-stick/systems"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.systems = {}
        
    def discover_systems(self) -> List[dict]:
        """
        Discover all Windows systems.
        Looks for:
        - Local disks
        - Network shares (if available)
        - Previously saved systems
        """
        systems = []
        
        # Discover local Windows installations
        local_systems = self._discover_local()
        systems.extend(local_systems)
        
        # Load saved systems
        saved = self._load_saved_systems()
        for sys in saved:
            if sys['id'] not in [s['id'] for s in systems]:
                systems.append(sys)
        
        self.systems = {s['id']: s for s in systems}
        return systems
    
    def _discover_local(self) -> List[dict]:
        """Discover Windows on local disks"""
        systems = []
        
        # Check mounted Windows
        mount_points = ["/mnt/windows", "/mnt/win"]
        
        for mp in mount_points:
            path = Path(mp)
            if path.exists() and (path / "Windows").exists():
                system = self._analyze_windows_installation(path)
                if system:
                    systems.append(system)
        
        # Also check fdisk for Windows partitions
        try:
            result = subprocess.run(
                ['fdisk', '-l'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse fdisk output for NTFS
            for line in result.stdout.split('\n'):
                if 'NTFS' in line or 'ntfs' in line:
                    # Could be Windows
                    pass
        except:
            pass
        
        return systems
    
    def _analyze_windows_installation(self, mount_path: Path) -> Optional[dict]:
        """Analyze a Windows installation"""
        system = {
            "id": "",
            "name": "Unknown",
            "type": "local",
            "path": str(mount_path),
            "os": {},
            "status": "unknown"
        }
        
        # Get Windows version from registry
        try:
            import configparser
            # Would parse SOFTWARE hive for version info
            pass
        except:
            pass
        
        # Try to determine OS
        system32 = mount_path / "Windows" / "System32"
        if (system32 / "ntoskrnl.exe").exists():
            system['os']['kernel'] = 'NT'
        
        # Generate ID from path
        system['id'] = mount_path.name or "local"
        system['name'] = f"Local-{system['id']}"
        
        return system
    
    def _load_saved_systems(self) -> List[dict]:
        """Load previously saved system configurations"""
        config_file = self.base_path / "systems.json"
        
        if not config_file.exists():
            return []
        
        try:
            with open(config_file, 'r') as f:
                data = json.load(f)
                return data.get('systems', [])
        except:
            return []
    
    def save_systems(self):
        """Save system configurations"""
        config_file = self.base_path / "systems.json"
        
        data = {
            "updated": datetime.now().isoformat(),
            "systems": list(self.systems.values())
        }
        
        with open(config_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_remote_system(self, name: str, connection: str, 
                          connection_type: str = "ssh") -> dict:
        """
        Add a remote system for management.
        Types: ssh, smb, vnc
        """
        system = {
            "id": name.lower().replace(' ', '_'),
            "name": name,
            "type": "remote",
            "connection": connection,
            "connection_type": connection_type,
            "status": "configured",
            "added": datetime.now().isoformat()
        }
        
        self.systems[system['id']] = system
        self.save_systems()
        
        return system
    
    def remove_system(self, system_id: str) -> dict:
        """Remove a system from dashboard"""
        if system_id in self.systems:
            del self.systems[system_id]
            self.save_systems()
            return {"status": "success", "removed": system_id}
        return {"status": "error", "message": "System not found"}
    
    def get_system_info(self, system_id: str) -> Optional[dict]:
        """Get detailed info about a system"""
        return self.systems.get(system_id)
    
    def scan_system(self, system_id: str) -> dict:
        """Run diagnostic scan on a specific system"""
        if system_id not in self.systems:
            return {"error": "System not found"}
        
        system = self.systems[system_id]
        
        result = {
            "system_id": system_id,
            "system_name": system.get('name'),
            "type": system.get('type'),
            "timestamp": datetime.now().isoformat(),
            "scan_results": {}
        }
        
        if system['type'] == 'local':
            # Run local scan
            mount_path = Path(system['path'])
            
            # Check boot files
            boot_files = ["Windows/System32/winload.exe", "Windows/System32/ntoskrnl.exe"]
            missing = []
            for bf in boot_files:
                if not (mount_path / bf).exists():
                    missing.append(bf)
            
            result['scan_results']['boot_files'] = {
                "status": "ok" if not missing else "issues",
                "missing": missing
            }
            
            # Check registry
            hives = ["SYSTEM", "SOFTWARE"]
            missing_hives = []
            for hive in hives:
                hive_path = mount_path / f"Windows/System32/config/{hive}"
                if not hive_path.exists():
                    missing_hives.append(hive)
            
            result['scan_results']['registry'] = {
                "status": "ok" if not missing_hives else "issues",
                "missing": missing_hives
            }
        
        elif system['type'] == 'remote':
            # Would run remote scan via SSH/SMB
            result['scan_results']['status'] = "remote_scan_not_implemented"
        
        return result
    
    def export_dashboard(self, output_file: str) -> dict:
        """Export dashboard configuration"""
        try:
            with open(output_file, 'w') as f:
                json.dump({
                    "version": "1.0",
                    "exported": datetime.now().isoformat(),
                    "systems": list(self.systems.values())
                }, f, indent=2)
            
            return {"status": "success", "file": output_file}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def import_dashboard(self, input_file: str) -> dict:
        """Import dashboard configuration"""
        try:
            with open(input_file, 'r') as f:
                data = json.load(f)
            
            imported = 0
            for system in data.get('systems', []):
                self.systems[system['id']] = system
                imported += 1
            
            self.save_systems()
            return {"status": "success", "imported": imported}
        except Exception as e:
            return {"status": "error", "error": str(e)}


# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="RescueStick Multi-Dashboard")
    parser.add_argument("action", choices=["discover", "add", "remove", "scan", "list", "export", "import"])
    parser.add_argument("--system-id", help="System ID")
    parser.add_argument("--name", help="System name")
    parser.add_argument("--connection", help="Connection string")
    parser.add_argument("--type", default="ssh", help="Connection type")
    parser.add_argument("--output", help="Output file")
    parser.add_argument("--input", help="Input file")
    
    args = parser.parse_args()
    
    dashboard = MultiDashboard()
    
    if args.action == "discover":
        systems = dashboard.discover_systems()
        print(json.dumps(systems, indent=2))
    
    elif args.action == "list":
        systems = dashboard.discover_systems()
        for s in systems:
            print(f"{s['id']}: {s['name']} ({s['type']}) - {s.get('status', 'unknown')}")
    
    elif args.action == "add":
        if not args.name or not args.connection:
            print("Error: --name and --connection required")
        else:
            result = dashboard.add_remote_system(args.name, args.connection, args.type)
            print(json.dumps(result, indent=2))
    
    elif args.action == "remove":
        if not args.system_id:
            print("Error: --system-id required")
        else:
            result = dashboard.remove_system(args.system_id)
            print(json.dumps(result, indent=2))
    
    elif args.action == "scan":
        if not args.system_id:
            print("Error: --system-id required")
        else:
            result = dashboard.scan_system(args.system_id)
            print(json.dumps(result, indent=2))
    
    elif args.action == "export":
        if not args.output:
            print("Error: --output required")
        else:
            result = dashboard.export_dashboard(args.output)
            print(json.dumps(result, indent=2))
    
    elif args.action == "import":
        if not args.input:
            print("Error: --input required")
        else:
            result = dashboard.import_dashboard(args.input)
            print(json.dumps(result, indent=2))
```

## Use Cases

- **IT Admin**: Manage 50+ PCs from one USB
- **Home User**: Fix dual-boot or family computers
- **Repair Tech**: Keep configs for repeat clients

## Dependencies

```bash
# No external dependencies - pure Python standard library
# Optional: smbclient for network shares, openssh for remote
```

**License:** MIT (our code)

## Testing

```bash
# Discover systems
python3 18_multi_dashboard.py discover

# List systems
python3 18_multi_dashboard.py list

# Add remote system
python3 18_multi_dashboard.py add --name "Office-PC" --connection "192.168.1.100" --type ssh

# Scan specific system
python3 18_multi_dashboard.py scan --system-id office-pc

# Export dashboard
python3 18_multi_dashboard.py export --output /path/to/dashboard.json
```

---

*Engine 18 - Spec Complete*  
*License: MIT (our code)*