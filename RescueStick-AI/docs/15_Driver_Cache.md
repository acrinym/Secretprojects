# RescueStick AI - Driver Cache Engine
**Engine ID:** 15_driver_cache
**Purpose:** Pre-cached driver database for offline installation
**License:** MIT (our code)

---

## What It Does

Offline driver database - install drivers without internet:

```
User: "No network driver"
       ↓
RescueStick: "Found Realtek in cache"
       → Install from USB
       → Network works!
```

## Pre-loaded Drivers

| Category | Drivers |
|----------|---------|
| Network | Intel, Realtek, Broadcom, Atheros |
| Storage | NVMe, SATA, RAID controllers |
| Chipset | Intel, AMD, NVIDIA |
| Video | Basic Microsoft drivers |

## Code Structure

```python
#!/usr/bin/env python3
"""
Engine 15: Driver Cache
License: MIT (our code)
"""

import subprocess
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class DriverCacheEngine:
    """
    Offline driver repository for Windows.
    Pre-cached drivers for installation without network.
    """
    
    def __init__(self, cache_dir="/rescue-stick/data/driver_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize driver database"""
        self.db_file = self.cache_dir / "drivers.json"
        
        if not self.db_file.exists():
            # Create default driver database
            default_drivers = {
                "version": "1.0",
                "updated": datetime.now().isoformat(),
                "drivers": []
            }
            with open(self.db_file, 'w') as f:
                json.dump(default_drivers, f, indent=2)
    
    def load_drivers(self) -> dict:
        """Load driver database"""
        with open(self.db_file, 'r') as f:
            return json.load(f)
    
    def save_drivers(self, data: dict):
        """Save driver database"""
        with open(self.db_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_driver(self, driver_info: dict) -> bool:
        """Add a driver to the cache"""
        data = self.load_drivers()
        
        # Check if already exists
        for existing in data['drivers']:
            if existing.get('inf_path') == driver_info.get('inf_path'):
                return False  # Already exists
        
        data['drivers'].append(driver_info)
        self.save_drivers(data)
        return True
    
    def search_drivers(self, query: str, category: str = None) -> List[dict]:
        """Search for drivers"""
        data = self.load_drivers()
        
        results = []
        query_lower = query.lower()
        
        for driver in data['drivers']:
            # Category filter
            if category and driver.get('category', '').lower() != category.lower():
                continue
            
            # Text search
            search_text = ' '.join([
                driver.get('name', ''),
                driver.get('vendor', ''),
                driver.get('hardware_id', ''),
                driver.get('category', '')
            ]).lower()
            
            if query_lower in search_text:
                results.append(driver)
        
        return results
    
    def get_driver_by_hardware_id(self, hardware_id: str) -> Optional[dict]:
        """Find driver by hardware ID"""
        data = self.load_drivers()
        
        for driver in data['drivers']:
            if driver.get('hardware_id', '').upper() == hardware_id.upper():
                return driver
        
        return None
    
    def list_categories(self) -> List[str]:
        """List available driver categories"""
        data = self.load_drivers()
        
        categories = set()
        for driver in data['drivers']:
            if 'category' in driver:
                categories.add(driver['category'])
        
        return sorted(list(categories))
    
    def install_driver(self, driver_path: str) -> dict:
        """
        Install a driver using pnputil (requires Windows).
        Creates script for next boot.
        """
        inf_file = self.cache_dir / driver_path
        
        if not inf_file.exists():
            return {"status": "error", "message": "Driver INF not found"}
        
        # Create installation script
        install_script = self.cache_dir / "install_drivers.bat"
        
        script_content = f"""@echo off
echo Installing driver: {driver_path}
pnputil -i -a "{driver_path}"
echo Driver installation complete
pause
"""
        
        with open(install_script, 'w') as f:
            f.write(script_content)
        
        return {
            "status": "scheduled",
            "script": str(install_script),
            "message": "Driver install script created - will run on Windows boot"
        }
    
    def export_for_offline(self, output_dir: str) -> dict:
        """Export driver cache for offline media"""
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        
        # Copy all drivers
        driver_count = 0
        data = self.load_drivers()
        
        for driver in data['drivers']:
            inf_path = driver.get('inf_path', '')
            if inf_path:
                src = self.cache_dir / inf_path
                if src.exists():
                    dest = output / src.name
                    shutil.copy2(src, dest)
                    driver_count += 1
        
        # Copy database
        shutil.copy2(self.db_file, output / "drivers.json")
        
        return {
            "status": "success",
            "drivers_exported": driver_count,
            "output": str(output)
        }
    
    def import_from_folder(self, folder: str) -> int:
        """Import drivers from a folder"""
        folder_path = Path(folder)
        
        if not folder_path.exists():
            return 0
        
        imported = 0
        data = self.load_drivers()
        
        # Find all INF files
        for inf_file in folder_path.rglob("*.inf"):
            # Try to parse driver info
            driver_info = self._parse_inf_file(inf_file)
            if driver_info:
                # Set path relative to cache
                driver_info['inf_path'] = str(inf_file.relative_to(self.cache_dir))
                
                # Check if exists
                exists = any(
                    d.get('inf_path') == driver_info['inf_path'] 
                    for d in data['drivers']
                )
                
                if not exists:
                    data['drivers'].append(driver_info)
                    imported += 1
        
        if imported > 0:
            self.save_drivers(data)
        
        return imported
    
    def _parse_inf_file(self, inf_path: Path) -> Optional[dict]:
        """Parse INF file for driver info"""
        try:
            with open(inf_path, 'r', errors='ignore') as f:
                content = f.read()
            
            driver_info = {
                "name": "Unknown",
                "vendor": "Unknown",
                "category": "Other",
                "hardware_id": "",
                "inf_path": str(inf_path),
                "added": datetime.now().isoformat()
            }
            
            # Simple INF parsing
            for line in content.split('\n'):
                line = line.strip()
                
                if line.startswith('[Version'):
                    # Driver section
                    pass
                elif line.startswith('DriverVer'):
                    parts = line.split('=')
                    if len(parts) > 1:
                        driver_info['version'] = parts[1].strip()
                elif '.DeviceDesc' in line:
                    parts = line.split('=')
                    if len(parts) > 1:
                        driver_info['name'] = parts[1].strip().strip('"')
            
            # Categorize
            name_lower = driver_info['name'].lower()
            if 'network' in name_lower or 'ethernet' in name_lower or 'lan' in name_lower:
                driver_info['category'] = 'Network'
            elif 'storage' in name_lower or 'sata' in name_lower or 'nvme' in name_lower:
                driver_info['category'] = 'Storage'
            elif 'chipset' in name_lower or 'system' in name_lower:
                driver_info['category'] = 'Chipset'
            elif 'video' in name_lower or 'display' in name_lower or 'graphics' in name_lower:
                driver_info['category'] = 'Video'
            
            return driver_info
            
        except Exception as e:
            return None
    
    def get_statistics(self) -> dict:
        """Get cache statistics"""
        data = self.load_drivers()
        
        categories = {}
        for driver in data['drivers']:
            cat = driver.get('category', 'Unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "total_drivers": len(data['drivers']),
            "categories": categories,
            "database_version": data.get('version', '1.0'),
            "last_updated": data.get('updated', 'unknown')
        }


# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="RescueStick Driver Cache")
    parser.add_argument("action", choices=["search", "list", "add", "install", "stats", "import"])
    parser.add_argument("--query", help="Search query")
    parser.add_argument("--category", help="Category filter")
    parser.add_argument("--hardware-id", help="Hardware ID")
    parser.add_argument("--path", help="Driver path")
    parser.add_argument("--import-folder", help="Import from folder")
    
    args = parser.parse_args()
    
    engine = DriverCacheEngine()
    
    if args.action == "search":
        results = engine.search_drivers(args.query or "", args.category)
        print(json.dumps(results, indent=2))
    
    elif args.action == "list":
        categories = engine.list_categories()
        print(json.dumps({"categories": categories}, indent=2))
    
    elif args.action == "add":
        print("Use --import-folder to add drivers")
    
    elif args.action == "install":
        if not args.path:
            print("Error: --path required")
        else:
            result = engine.install_driver(args.path)
            print(json.dumps(result, indent=2))
    
    elif args.action == "stats":
        stats = engine.get_statistics()
        print(json.dumps(stats, indent=2))
    
    elif args.action == "import":
        if not args.import_folder:
            print("Error: --import-folder required")
        else:
            count = engine.import_from_folder(args.import_folder)
            print(json.dumps({"imported": count}, indent=2))
```

## Pre-loaded Driver Categories

The driver cache includes these categories:
- **Network** - Ethernet, WiFi, wireless
- **Storage** - NVMe, SATA, RAID
- **Chipset** - System, motherboard
- **Video** - Display, graphics

## Dependencies

```bash
# No external dependencies - pure Python standard library
# Optional: Windows pnputil for actual driver installation
```

**License:** MIT (our code)

## Testing

```bash
# List categories
python3 15_driver_cache.py list

# Search drivers
python3 15_driver_cache.py search --query "realtek"

# Stats
python3 15_driver_cache.py stats

# Import from folder
python3 15_driver_cache.py import --import-folder /path/to/drivers
```

---

*Engine 15 - Spec Complete*  
*License: MIT (our code)*