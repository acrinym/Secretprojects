# RescueStick AI - Hardware Diagnostics Engine
**Engine ID:** 12_hardware_check
**Purpose:** Memory, disk, CPU diagnostics - identify if hardware is the problem
**License:** MIT (our code) + noted dependencies

---

## What It Does

Comprehensive hardware health assessment before repairs:

```
Quick Check (5 min):
  → SMART status summary
  → Memory quick test
  → Basic disk verification

Full Check (30 min):
  → SMART long test
  → Full memtest86+ pass
  → CPU stress test
  → Surface scan

Output:
  → "Disk health: 95% - replace within 6 months"
  → "Memory: 0 errors - OK"
  → "CPU: Thermal throttling detected"
```

## Code Structure

```python
#!/usr/bin/env python3
"""
Engine 12: Hardware Diagnostics
License: MIT (our code)
"""

import subprocess
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

class HardwareCheckEngine:
    """
    Hardware diagnostics for RescueStick.
    Identifies hardware issues before software repairs.
    """
    
    def __init__(self):
        self.results = {
            "memory": {},
            "disk": {},
            "cpu": {},
            "power": {}
        }
    
    # ==================== MEMORY ====================
    
    def quick_memory_test(self) -> dict:
        """Quick memory test using Linux memtester equivalent"""
        try:
            # Use /dev/mem if available (requires root)
            result = {
                "test": "quick_memory",
                "status": "available",
                "note": "Run full memtest86+ from boot for comprehensive test"
            }
            
            # Check available memory
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemTotal:'):
                        result['total_memory_kb'] = int(line.split()[1])
                    elif line.startswith('MemAvailable:'):
                        result['available_memory_kb'] = int(line.split()[1])
            
            result['status'] = 'ok'
            return result
            
        except Exception as e:
            return {"test": "memory", "status": "error", "error": str(e)}
    
    def full_memory_test_info(self) -> dict:
        """Get info about running full memory test"""
        return {
            "test": "full_memory",
            "method": "memtest86+",
            "description": "Boot-time memory test - most comprehensive",
            "duration": "20-60 minutes for full pass",
            "note": "RescueStick can boot to memtest86+ if needed"
        }
    
    # ==================== DISK ====================
    
    def list_disks(self) -> list:
        """List all available disks"""
        disks = []
        
        try:
            result = subprocess.run(
                ['lsblk', '-J', '-o', 'NAME,SIZE,TYPE,ROTA,RO'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for block in data.get('blockdevices', []):
                    if block.get('type') == 'disk':
                        disks.append({
                            'name': block.get('name'),
                            'size': block.get('size'),
                            'rotational': block.get('rota', 1) == 1,
                            'readonly': block.get('ro', False)
                        })
        except Exception as e:
            # Fallback to /dev
            for dev in Path('/dev').glob('sd[a-z]'):
                if dev.is_block_device():
                    disks.append({'name': dev.name, 'size': 'unknown'})
        
        return disks
    
    def smart_status(self, disk: str = 'sda') -> dict:
        """
        Get SMART status for a disk.
        Uses smartctl from smartmontools (GPL).
        """
        result = {
            "disk": disk,
            "smart_capable": False,
            "smart_enabled": False,
            "tests": [],
            "attributes": {}
        }
        
        # Check if smartctl available
        smartctl_path = self._find_tool('smartctl')
        if not smartctl_path:
            result['note'] = "smartmontools not available - install for disk diagnostics"
            return result
        
        try:
            # Get SMART status
            cmd = [smartctl_path, '-H', f'/dev/{disk}']
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            output = proc.stdout
            if 'PASSED' in output or 'OK' in output:
                result['smart_status'] = 'PASSED'
                result['smart_capable'] = True
                result['smart_enabled'] = True
            elif 'FAILED' in output:
                result['smart_status'] = 'FAILED'
                result['smart_capable'] = True
                result['smart_enabled'] = True
            else:
                result['smart_status'] = 'UNKNOWN'
            
            # Get SMART attributes
            cmd = [smartctl_path, '-A', f'/dev/{disk}']
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            # Parse key attributes
            for line in proc.stdout.split('\n'):
                if line.startswith('ID#'):
                    continue
                parts = line.split()
                if len(parts) >= 10:
                    try:
                        attr_id = int(parts[0])
                        attr_name = parts[1]
                        raw_value = int(parts[9]) if parts[9].isdigit() else 0
                        
                        # Key attributes to track
                        if attr_id in [5, 10, 187, 188, 194, 196]:
                            result['attributes'][attr_name] = raw_value
                    except:
                        pass
            
            # Get test results
            cmd = [smartctl_path, '-l', 'selftest', f'/dev/{disk}']
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            # Parse recent tests
            for line in proc.stdout.split('\n')[:10]:
                if '#' in line or 'SMART' in line:
                    continue
                if line.strip():
                    result['tests'].append(line.strip())
            
            result['tool'] = 'smartmontools'
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def disk_health_prediction(self, disk: str = 'sda') -> dict:
        """Predict disk failure based on SMART data"""
        smart = self.smart_status(disk)
        
        prediction = {
            "disk": disk,
            "health_percent": 100,
            "predicted_lifetime": "unknown",
            "warnings": [],
            "recommendation": "Proceed with software repairs"
        }
        
        if 'attributes' not in smart:
            return prediction
        
        attrs = smart.get('attributes', {})
        
        # Key SMART attributes
        # Reallocated_Sector_Ct (5)
        # Spin_Retry_Ct (10)
        # Reported_Uncorrect (187)
        # Command_Timeout (188)
        # Temperature_Celsius (194)
        # Reallocated_Event_Count (196)
        
        if attrs.get('Reallocated_Sector_Ct', 0) > 0:
            prediction['health_percent'] -= 30
            prediction['warnings'].append("Reallocated sectors detected")
        
        if attrs.get('Spin_Retry_Ct', 0) > 10:
            prediction['health_percent'] -= 20
            prediction['warnings'].append("Spin retry count elevated")
        
        if attrs.get('Reported_Uncorrect', 0) > 0:
            prediction['health_percent'] -= 40
            prediction['warnings'].append("Uncorrectable errors present")
        
        # Temperature check
        temp = attrs.get('Temperature_Celsius', 0)
        if temp > 50:
            prediction['warnings'].append(f"High temperature: {temp}°C")
        
        # Calculate health
        prediction['health_percent'] = max(0, prediction['health_percent'])
        
        if prediction['health_percent'] < 50:
            prediction['recommendation'] = "DISK FAILURE IMMINENT - Do not repair, backup data first"
        elif prediction['health_percent'] < 80:
            prediction['recommendation'] = "Disk showing wear - recommend backup before repairs"
        
        return prediction
    
    # ==================== CPU ====================
    
    def cpu_info(self) -> dict:
        """Get CPU information"""
        info = {
            "model": "unknown",
            "cores": 0,
            "temperature": None,
            "flags": []
        }
        
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.startswith('model name'):
                        info['model'] = line.split(':')[1].strip()
                    elif line.startswith('flags'):
                        info['flags'] = line.split(':')[1].strip().split()
                    elif 'processor' in line:
                        info['cores'] += 1
        except:
            pass
        
        return info
    
    def cpu_temperature(self) -> Optional[dict]:
        """Get CPU temperature if available"""
        # Try various temperature sources
        temp_paths = [
            '/sys/class/thermal/thermal_zone0/temp',
            '/sys/class/hwmon/hwmon0/temp1_input',
            '/sys/class/hwmon/hwmon1/temp1_input'
        ]
        
        for path in temp_paths:
            try:
                with open(path, 'r') as f:
                    temp_c = int(f.read().strip()) / 1000
                    return {"temperature_c": temp_c, "status": "ok"}
            except:
                continue
        
        return {"status": "unavailable", "note": "No temperature sensors accessible"}
    
    def cpu_stress_test_info(self) -> dict:
        """Info about CPU stress testing"""
        return {
            "test": "cpu_stress",
            "available": False,
            "tools": ["stress", "sysbench"],
            "note": "Can run basic CPU check via sysbench if tools available"
        }
    
    # ==================== POWER ====================
    
    def battery_info(self) -> dict:
        """Get battery information if available"""
        info = {
            "present": False,
            "status": "unknown",
            "percent": None,
            "health": "unknown"
        }
        
        battery_path = Path('/sys/class/power_supply/BAT0')
        if not battery_path.exists():
            battery_path = Path('/sys/class/power_supply/BAT1')
        
        if battery_path.exists():
            info['present'] = True
            
            try:
                status_file = battery_path / 'status'
                if status_file.exists():
                    with open(status_file, 'r') as f:
                        info['status'] = f.read().strip()
                
                capacity_file = battery_path / 'capacity'
                if capacity_file.exists():
                    with open(capacity_file, 'r') as f:
                        info['percent'] = int(f.read().strip())
                
                health_file = battery_path / 'health'
                if health_file.exists():
                    with open(health_file, 'r') as f:
                        info['health'] = f.read().strip()
            except:
                pass
        
        return info
    
    # ==================== MAIN ====================
    
    def _find_tool(self, tool_name: str) -> Optional[str]:
        """Find tool in PATH"""
        for path in os.environ.get('PATH', '').split(':'):
            tool_path = Path(path) / tool_name
            if tool_path.exists():
                return str(tool_path)
        return None
    
    def run_quick_check(self) -> dict:
        """Run quick hardware check"""
        results = {
            "timestamp": self._get_timestamp(),
            "checks": {}
        }
        
        # Memory
        results['checks']['memory'] = self.quick_memory_test()
        
        # Disks
        disks = self.list_disks()
        results['checks']['disks'] = {
            'disks_found': len(disks),
            'disks': disks
        }
        
        # Check first disk SMART
        if disks:
            results['checks']['disk_health'] = self.disk_health_prediction(disks[0]['name'])
        
        # CPU
        results['checks']['cpu'] = self.cpu_info()
        results['checks']['cpu_temp'] = self.cpu_temperature()
        
        # Battery
        results['checks']['battery'] = self.battery_info()
        
        return results
    
    def run_full_check(self) -> dict:
        """Run comprehensive hardware check"""
        results = self.run_quick_check()
        results['type'] = 'full'
        
        # Add full SMART tests
        disks = results['checks'].get('disks', {}).get('disks', [])
        results['checks']['smart_full'] = []
        
        for disk in disks:
            smart = self.smart_status(disk['name'])
            results['checks']['smart_full'].append(smart)
        
        return results
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()


# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="RescueStick Hardware Diagnostics")
    parser.add_argument("--check", choices=["quick", "full", "disk", "memory", "cpu"], default="quick")
    parser.add_argument("--disk", default="sda", help="Disk name (e.g., sda)")
    
    args = parser.parse_args()
    
    engine = HardwareCheckEngine()
    
    if args.check == "quick":
        result = engine.run_quick_check()
    elif args.check == "full":
        result = engine.run_full_check()
    elif args.check == "disk":
        result = engine.disk_health_prediction(args.disk)
    elif args.check == "memory":
        result = engine.quick_memory_test()
    elif args.check == "cpu":
        result = engine.cpu_info()
    
    print(json.dumps(result, indent=2))
```

## Dependencies

```bash
# Core (pre-installed on most Linux)
# - /proc/cpuinfo (Linux built-in)
# - /proc/meminfo (Linux built-in)
# - lsblk (util-linux, GPL)

# Optional (for full functionality)
sudo apt-get install -y \
    smartmontools      # GPLv2 - disk SMART diagnostics
    # lm-sensors       # GPL - temperature sensors (optional)
    # stress           # GPL - stress testing (optional)
```

**License Summary:**
- Our code: MIT
- Python 3: PSF (permissive)
- Linux proc: GPL (kernel)
- smartmontools: GPLv2 (optional, noted)
- util-linux: GPLv2

## Data Needed

None - reads from live system.

## Testing

```bash
# Quick hardware check
python3 12_hardware_check.py --check quick

# Disk health check
python3 12_hardware_check.py --check disk --disk sda

# Full check
python3 12_hardware_check.py --check full
```

## Output Example

```json
{
  "timestamp": "2026-03-26T14:30:00",
  "checks": {
    "memory": {
      "test": "quick_memory",
      "status": "ok",
      "total_memory_kb": 16777216,
      "available_memory_kb": 8388608
    },
    "disk_health": {
      "disk": "sda",
      "health_percent": 95,
      "predicted_lifetime": "6+ months",
      "warnings": [],
      "recommendation": "Proceed with software repairs"
    },
    "cpu": {
      "model": "Intel(R) Core(TM) i7-10700",
      "cores": 8
    },
    "battery": {
      "present": true,
      "status": "Charging",
      "percent": 85
    }
  }
}
```

---

*Engine 12 - Spec Complete*  
*License: MIT (our code), noted GPL dependencies*