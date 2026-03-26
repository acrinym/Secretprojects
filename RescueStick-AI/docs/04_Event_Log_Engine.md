# RescueStick AI - Event Log Engine
**Engine ID:** 04_event_log_engine  
**Purpose:** Parse Windows event logs, extract error patterns, correlate with file/registry issues  
**Dependencies:** Python 3.10+, python-evtx, pyevtx

---

## What It Does

1. **Reads** Windows .evtx event log files
2. **Extracts** errors, warnings, critical events
3. **Correlates** with file and registry findings
4. **Identifies** root causes from event patterns
5. **Reports** actionable diagnostics

---

## Event Log Locations

```
C:\Windows\System32\winevt\Logs\
├── System.evtx          - System component events
├── Application.evtx    - Application errors
├── Security.evtx       - Security events (may need权限)
├── Setup.evtx          - Windows setup events
├── Microsoft-Windows-PowerShell%4Operational.evtx
└── Microsoft-Windows-Kernel-Power%4Operational.evtx
```

---

## How to Build It

### Step 1: Install Dependencies

```bash
# Linux packages
sudo apt-get install:
    - libevtx-dev          # EVTX parsing library

# Python packages
pip install:
    - python-evtx         # EVTX file parser
    - evtx              # Alternative parser
```

### Step 2: Core Code Structure

```python
# engines/04_event_log_engine.py

import os
import struct
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import evtx

@dataclass
class EventLogEntry:
    """Single event from event log."""
    log_name: str          # "System", "Application", etc.
    event_id: int         # Event ID (e.g., 1001)
    level: str            # "Error", "Warning", "Information"
    time_created: datetime
    source: str           # Event source (e.g., "Microsoft-Windows-Kernel-Power")
    message: str         # Formatted message
    correlation_id: Optional[str]  # For linking related events

@dataclass
class ErrorPattern:
    """Identified error pattern with repair suggestions."""
    pattern_type: str     # "disk_failure", "driver_issue", "update_failure"
    events: List[EventLogEntry]
    likely_cause: str
    repair_suggestion: str
    severity: str        # "critical", "high", "medium"
    related_files: List[str]  # Files likely involved
    related_registry: List[str]  # Registry keys involved

class EventLogEngine:
    """
    Windows Event Log Analysis Engine
    
    Parses .evtx files, extracts errors, identifies patterns.
    """
    
    # Common error event IDs and their meanings
    KNOWN_ERRORS = {
        # Disk/Storage
        7: {"type": "disk_failure", "cause": "Disk device timeout"},
        11: {"type": "disk_failure", "cause": "Disk not ready"},
        153: {"type": "disk_failure", "cause": "Disk I/O error"},
        157: {"type": "disk_failure", "cause": "Disk bad block"},
        
        # Boot/BCD
        1001: {"type": "boot_failure", "cause": "Bugcheck, system crashed"},
        1003: {"type": "boot_failure", "cause": "Bootmgr not found"},
        1079: {"type": "boot_failure", "cause": "Boot configuration corrupted"},
        
        # Driver issues
        219: {"type": "driver_issue", "cause": "Driver failed to load"},
        219: {"type": "driver_issue", "cause": "Driver startup failure"},
        
        # Windows Update
        20: {"type": "update_failure", "cause": "Windows Update installation failure"},
        24: {"type": "update_failure", "cause": "Update installation timeout"},
        30: {"type": "update_failure", "cause": "Component store corrupted"},
        
        # Service failures
        7000: {"type": "service_failure", "cause": "Service failed to start"},
        7001: {"type": "service_dependency", "cause": "Service dependency failed"},
        7043: {"type": "service_failure", "cause": "Service control manager error"},
        
        # Application crashes
        1000: {"type": "app_crash", "cause": "Application error (crash)"},
        1001: {"type": "app_crash", "cause": "Application hang"},
        
        # System file corruption
        1005: {"type": "file_corruption", "cause": "Unrecoverable file error"},
    }
    
    # Known error sources
    EVENT_SOURCES = {
        'Microsoft-Windows-Kernel-Power': ['power', 'sleep', 'resume'],
        'Microsoft-Windows-Kernel-General': ['boot', 'timezone'],
        'Microsoft-Windows-Kernel-WHEA': ['hardware', 'WHEA errors'],
        'Microsoft-Windows-Kernel-Patch': ['patch', 'update'],
        'Microsoft-Windows-WindowsUpdateClient': ['update', 'WU'],
        'Microsoft-Windows-Servicing': ['servicing', 'update'],
        'Microsoft-Windows-DNS-Client': ['DNS', 'network'],
        'Microsoft-Windows-DHCP-Server': ['DHCP', 'network'],
        'EventLog': ['general', 'service'],
    }
    
    def __init__(self, winevt_path: str):
        self.winevt_path = Path(winevt_path)
        self.events = []
        self.patterns = []
        
    def parse_evtx_file(self, log_name: str, filename: str) -> List[EventLogEntry]:
        """
        Parse a single .evtx file.
        
        Args:
            log_name: Display name ("System", "Application")
            filename: Path to .evtx file
        """
        entries = []
        
        with open(filename, 'rb') as f:
            # EVTX header
            magic = f.read(4)
            if magic != b'Elf\x00':
                raise ValueError(f"Not a valid EVTX file: {filename}")
            
            # Use python-evtx library to parse
            parser = evtx.EvtxParser(f)
            
            for record in parser.records():
                entry = self._parse_record(log_name, record)
                if entry and entry.level in ['Error', 'Critical']:
                    entries.append(entry)
        
        return entries
    
    def _parse_record(self, log_name: str, record: dict) -> Optional[EventLogEntry]:
        """Parse a single event record."""
        try:
            # Extract fields from EVTX record
            event_id = record.get('EventID', 0)
            level = record.get('Level', 'Information')
            timestamp = record.get('TimeCreated', None)
            source = record.get('Provider', {}).get('Name', 'Unknown')
            message = record.get('Message', '')
            
            # Map level number to name
            level_map = {
                1: 'Critical',
                2: 'Error', 
                3: 'Warning',
                4: 'Information',
                5: 'Verbose'
            }
            level = level_map.get(level, 'Unknown')
            
            return EventLogEntry(
                log_name=log_name,
                event_id=event_id,
                level=level,
                time_created=timestamp,
                source=source,
                message=message[:500],  # Truncate long messages
                correlation_id=record.get('Correlation', {}).get('ActivityId')
            )
            
        except Exception as e:
            return None
    
    def scan_all_logs(self, mount_point: str) -> List[EventLogEntry]:
        """
        Scan all event logs on a Windows installation.
        
        Args:
            mount_point: Path to mounted Windows drive
        """
        log_dir = Path(mount_point) / "Windows" / "System32" / "winevt" / "Logs"
        
        log_map = {
            'System.evtx': 'System',
            'Application.evtx': 'Application', 
            'Security.evtx': 'Security',
            'Setup.evtx': 'Setup',
        }
        
        all_events = []
        
        for filename, display_name in log_map.items():
            filepath = log_dir / filename
            if filepath.exists():
                print(f"Scanning {display_name} log...")
                try:
                    events = self.parse_evtx_file(display_name, str(filepath))
                    all_events.extend(events)
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
        
        self.events = all_events
        return all_events
    
    def identify_patterns(self, events: List[EventLogEntry]) -> List[ErrorPattern]:
        """
        Identify error patterns from event list.
        
        Groups related events, identifies root cause.
        """
        patterns = []
        
        # Group by event ID
        from collections import defaultdict
        by_event_id = defaultdict(list)
        for event in events:
            by_event_id[event.event_id].append(event)
        
        # Identify patterns for known errors
        for event_id, events_list in by_event_id.items():
            if event_id in self.KNOWN_ERRORS:
                error_info = self.KNOWN_ERRORS[event_id]
                
                pattern = ErrorPattern(
                    pattern_type=error_info['type'],
                    events=events_list[:10],  # Limit to first 10
                    likely_cause=error_info['cause'],
                    repair_suggestion=self._get_repair_suggestion(error_info['type']),
                    severity=self._assess_severity(error_info['type'], len(events_list)),
                    related_files=self._get_related_files(error_info['type']),
                    related_registry=self._get_related_registry(error_info['type'])
                )
                patterns.append(pattern)
        
        self.patterns = patterns
        return patterns
    
    def _get_repair_suggestion(self, pattern_type: str) -> str:
        """Get repair suggestion for pattern type."""
        suggestions = {
            'disk_failure': 'Run chkdsk /r, check SMART status, consider disk replacement',
            'boot_failure': 'Run bootrec /rebuildbcd, bcdedit, check BCD store',
            'driver_issue': 'Update driver from OEM, roll back to previous version',
            'update_failure': 'Run DISM /RestoreHealth, SFC /Scannow',
            'service_failure': 'Check service dependencies, rebuild service database',
            'app_crash': 'Check event details for crash dump, reinstall application',
            'file_corruption': 'Run SFC /Scannow, DISM /RestoreHealth',
        }
        return suggestions.get(pattern_type, 'Manual investigation required')
    
    def _assess_severity(self, pattern_type: str, count: int) -> str:
        """Assess pattern severity."""
        critical_types = ['boot_failure', 'disk_failure', 'file_corruption']
        
        if pattern_type in critical_types:
            return 'critical' if count > 3 else 'high'
        elif count > 10:
            return 'high'
        else:
            return 'medium'
    
    def _get_related_files(self, pattern_type: str) -> List[str]:
        """Get file paths likely related to this issue."""
        related = {
            'boot_failure': [
                'Windows/System32/BCD',
                'Windows/Boot',
            ],
            'file_corruption': [
                'Windows/System32/config/SYSTEM',
                'Windows/System32/config/SOFTWARE',
            ],
        }
        return related.get(pattern_type, [])
    
    def _get_related_registry(self, pattern_type: str) -> List[str]:
        """Get registry keys likely related to this issue."""
        related = {
            'boot_failure': [
                'HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\BootExecute',
                'HKLM\\SYSTEM\\CurrentControlSet\\Services\\Winmgmt',
            ],
            'service_failure': [
                'HKLM\\SYSTEM\\CurrentControlSet\\Services',
            ],
        }
        return related.get(pattern_type, [])
    
    def correlate_with_scanner(self, file_scanner_results: dict, registry_results: dict) -> List[ErrorPattern]:
        """
        Cross-reference event patterns with file/registry scanner results.
        
        If event log shows "file not found" and scanner confirms file missing → high confidence.
        """
        correlated = []
        
        for pattern in self.patterns:
            # Check file correlations
            for rel_file in pattern.related_files:
                if rel_file in file_scanner_results.get('missing_files', []):
                    pattern.repair_suggestion += f"\n[CORRELATED: File {rel_file} is missing]"
                    pattern.severity = 'critical'  # Escalate
            
            # Check registry correlations
            for rel_key in pattern.related_registry:
                if rel_key in registry_results.get('corrupted_keys', []):
                    pattern.repair_suggestion += f"\n[CORRELATED: Registry {rel_key} is corrupted]"
                    pattern.severity = 'critical'
            
            correlated.append(pattern)
        
        return correlated
```

---

## Event ID Reference Database

```
data/event_id_database.json
{
  "1001": {
    "source": "Microsoft-Windows-Kernel-Power",
    "type": "Critical",
    "description": "The system has rebooted without cleanly shutting down first",
    "cause": "Kernel power event, system crashed or was powered off unexpectedly",
    "correlated_issues": ["disk_failure", "driver_issue"]
  },
  "7036": {
    "source": "Service Control Manager", 
    "type": "Information",
    "description": "The %service% service entered the %state% state",
    "correlated_issues": []
  }
}
```

---

## Testing

```bash
# Extract event logs from Windows VM
# Run event log engine
# Verify pattern detection
```

---

*Engine Status: SPEC COMPLETE - Implementation ready to begin*