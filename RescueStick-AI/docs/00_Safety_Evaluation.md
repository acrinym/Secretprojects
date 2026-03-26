# RescueStick AI - Safety Evaluation Engine
**Engine ID:** 00_safety_evaluation  
**Purpose:** Pre-repair safety checks, veto dangerous operations, require user confirmations  
**Dependencies:** Python 3.10+

---

## What It Does

1. **Evaluates** every proposed repair for safety
2. **Vetos** dangerous operations that could brick the system
3. **Requires** user confirmation for risky repairs
4. **Creates** automatic backups before any changes
5. **Provides** rollback capability

---

## Safety Philosophy

> **"First, do no harm"** - Before any repair, ensure we can recover.

---

## How to Build It

### Step 1: Safety Rules Database

```python
# engines/00_safety_evaluation.py

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

class SafetyLevel(Enum):
    SAFE = "safe"           # Auto-repair OK
    CAUTION = "caution"     # Proceed with warning
    DANGER = "danger"       # User confirmation required
    BLOCKED = "blocked"     # Do not proceed - too risky

@dataclass
class SafetyRule:
    """Rule for evaluating repair safety."""
    rule_id: str
    description: str
    check_function: str    # Function name to call
    safety_level: SafetyLevel
    message: str           # Message to show user

# Define safety rules
SAFETY_RULES = [
    SafetyRule(
        rule_id="boot_files",
        description="Don't modify boot-critical files without backup",
        check_function="check_boot_files",
        safety_level=SafetyLevel.CAUTION,
        message="This repair affects boot files. A backup will be created first."
    ),
    SafetyRule(
        rule_id="registry_system",
        description="System registry hives require extra caution",
        check_function="check_system_registry",
        safety_level=SafetyLevel.DANGER,
        message="This repairs SYSTEM registry. Confirm you want to proceed."
    ),
    SafetyRule(
        rule_id="boot_registry",
        description="Boot-related registry keys are high risk",
        check_function="check_boot_registry",
        safety_level=SafetyLevel.BLOCKED,
        message="This modifies boot-critical registry keys. Too risky to auto-repair."
    ),
    SafetyRule(
        rule_id="multiple_files",
        description="Large number of files - could take long or cause issues",
        check_function="check_file_count",
        safety_level=SafetyLevel.CAUTION,
        message="Repairing 50+ files. This may take significant time."
    ),
]
```

### Step 2: Core Safety Engine

```python
class SafetyEvaluation:
    """
    Pre-repair safety evaluation engine.
    
    Vetoes dangerous repairs, requires confirmations for risky ones.
    """
    
    # Files that are boot-critical
    BOOT_CRITICAL_FILES = {
        'Windows/Boot',
        'Windows/System32/boot',
        'Windows/System32/winload.exe',
        'Windows/System32/winresume.exe',
        'Windows/System32/bootmgr',
        'Windows/System32/hal.dll',
        'Windows/System32/ntoskrnl.exe',
        'Windows/System32/win32k.sys',
    }
    
    # Registry keys that are boot-critical
    BOOT_CRITICAL_REGISTRY = {
        'HKLM\\SYSTEM\\CurrentControlSet\\Control',
        'HKLM\\SYSTEM\\CurrentControlSet\\Services\\Winmgmt',
        'HKLM\\SYSTEM\\CurrentControlSet\\Services\\EventLog',
        'HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run',
    }
    
    # System registry hives
    SYSTEM_HIVES = {
        'SYSTEM', 'SOFTWARE', 'SECURITY', 'SAM'
    }
    
    def __init__(self):
        self.safety_checks = []
        self.blocked_repairs = []
        self.confirmations_needed = []
        
    def evaluate_repair(self, repair_item: dict) -> Dict:
        """
        Evaluate a single repair item for safety.
        
        Returns:
        {
            "allowed": bool,
            "safety_level": str,
            "message": str,
            "requires_backup": bool,
            "requires_confirmation": bool
        }
        """
        path = repair_item.get('path', '')
        repair_type = repair_item.get('type', '')
        
        # Check each safety rule
        for rule in SAFETY_RULES:
            check_func = getattr(self, rule.check_function, None)
            if check_func and check_func(path, repair_item):
                result = {
                    "allowed": rule.safety_level != SafetyLevel.BLOCKED,
                    "safety_level": rule.safety_level.value,
                    "message": rule.message,
                    "requires_backup": rule.safety_level in [
                        SafetyLevel.CAUTION, 
                        SafetyLevel.DANGER,
                        SafetyLevel.BLOCKED
                    ],
                    "requires_confirmation": rule.safety_level in [
                        SafetyLevel.DANGER,
                        SafetyLevel.BLOCKED
                    ]
                }
                
                if rule.safety_level == SafetyLevel.BLOCKED:
                    self.blocked_repairs.append({
                        "path": path,
                        "reason": rule.description,
                        "rule_id": rule.rule_id
                    })
                    
                if rule.safety_level == SafetyLevel.DANGER:
                    self.confirmations_needed.append({
                        "path": path,
                        "message": rule.message,
                        "repair_action": repair_item.get('action', '')
                    })
                
                return result
        
        # No rules triggered - safe to proceed
        return {
            "allowed": True,
            "safety_level": "safe",
            "message": "Repair appears safe",
            "requires_backup": False,
            "requires_confirmation": False
        }
    
    def check_boot_files(self, path: str, repair_item: dict) -> bool:
        """Check if repair involves boot-critical files."""
        return any(path.startswith(bcf) for bcf in self.BOOT_CRITICAL_FILES)
    
    def check_system_registry(self, path: str, repair_item: dict) -> bool:
        """Check if repair involves system registry hives."""
        # Check if it's a system hive
        for hive in self.SYSTEM_HIVES:
            if hive in path.upper():
                return True
        return False
    
    def check_boot_registry(self, path: str, repair_item: dict) -> bool:
        """Check if repair involves boot-critical registry."""
        return any(bcr in path.upper() for bcr in self.BOOT_CRITICAL_REGISTRY)
    
    def check_file_count(self, path: str, repair_item: dict) -> bool:
        """Check if repairing many files at once."""
        # This would be checked at repair plan level
        return False
    
    def evaluate_repair_plan(self, repair_plan: dict) -> Dict:
        """
        Evaluate entire repair plan for safety.
        
        Returns safety report and list of items needing user input.
        """
        results = []
        
        for repair_item in repair_plan.get('repairs', []):
            result = self.evaluate_repair(repair_item)
            results.append(result)
        
        # Summarize
        blocked = sum(1 for r in results if not r['allowed'])
        dangerous = sum(1 for r in results if r['safety_level'] == 'danger')
        caution = sum(1 for r in results if r['safety_level'] == 'caution')
        
        return {
            "safe_to_proceed": blocked == 0,
            "summary": {
                "blocked": blocked,
                "dangerous": dangerous,
                "caution": caution,
                "safe": len(results) - blocked - dangerous - caution
            },
            "blocked_repairs": self.blocked_repairs,
            "confirmations_needed": self.confirmations_needed,
            "recommendation": self._get_recommendation(blocked, dangerous, caution)
        }
    
    def _get_recommendation(self, blocked: int, dangerous: int, caution: int) -> str:
        """Get overall recommendation based on safety analysis."""
        if blocked > 0:
            return (
                f"STOP - {blocked} repair(s) are too dangerous to attempt. "
                "These repairs have been blocked. The system may need manual repair."
            )
        elif dangerous > 0:
            return (
                f"CAUTION - {dangerous} repair(s) require user confirmation. "
                "Review and confirm before proceeding."
            )
        elif caution > 0:
            return (
                f"PROCEED WITH CARE - {caution} repair(s) may have side effects. "
                "Backups will be created automatically."
            )
        else:
            return "SAFE - All repairs appear low risk. Proceeding."
```

### Step 3: Pre-Repair Backup System

```python
class PreRepairBackup:
    """
    Creates backups before any repair is made.
    Ensures rollback is always possible.
    """
    
    def __init__(self, backup_dir: str = "/rescue-stick/data/backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def create_backup(self, item_type: str, path: str) -> str:
        """
        Create backup of file or registry hive.
        
        Returns path to backup.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{item_type}_{Path(path).name}_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        if item_type == "file":
            shutil.copy2(path, backup_path)
        elif item_type == "registry":
            # Copy registry hive file
            shutil.copy2(path, backup_path)
            # Also copy transaction log
            if Path(path + ".LOG1").exists():
                shutil.copy2(path + ".LOG1", self.backup_dir / f"{backup_name}.LOG1")
        
        # Create manifest
        manifest = {
            "timestamp": timestamp,
            "original_path": path,
            "backup_path": str(backup_path),
            "sha256": hashlib.sha256(backup_path).hexdigest()
        }
        
        with open(backup_path.with_suffix('.json'), 'w') as f:
            json.dump(manifest, f)
        
        return str(backup_path)
    
    def restore_from_backup(self, backup_path: str, original_path: str) -> bool:
        """Restore from backup."""
        try:
            shutil.copy2(backup_path, original_path)
            return True
        except Exception as e:
            print(f"Restore failed: {e}")
            return False
    
    def list_backups(self) -> List[Dict]:
        """List all available backups."""
        backups = []
        for manifest_file in self.backup_dir.glob("*.json"):
            with open(manifest_file) as f:
                backups.append(json.load(f))
        return sorted(backups, key=lambda x: x['timestamp'], reverse=True)
```

### Step 4: User Confirmation Flow

```python
class SafetyConfirmation:
    """
    Handles user confirmations for dangerous repairs.
    """
    
    def __init__(self):
        self.confirmed_repairs = set()
        
    def request_confirmation(self, confirmations_needed: List[Dict]) -> bool:
        """
        Present confirmation dialog to user.
        
        Returns True if user confirms all, False if any rejected.
        """
        print("\n" + "="*60)
        print("SAFETY WARNING - User Confirmation Required")
        print("="*60)
        
        for item in confirmations_needed:
            print(f"\n⚠️  {item['message']}")
            print(f"   Path: {item['path']}")
            print(f"   Action: {item['repair_action']}")
            
            response = input("\n   Proceed with this repair? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("   ❌ Repair rejected by user")
                return False
            else:
                print("   ✅ Confirmed")
                self.confirmed_repairs.add(item['path'])
        
        return True
    
    def is_confirmed(self, path: str) -> bool:
        """Check if repair has been confirmed."""
        return path in self.confirmed_repairs
```

---

## Integration with Repair Execution

```python
# Before executing any repair:

safety = SafetyEvaluation()
backup_system = PreRepairBackup()
confirmation = SafetyConfirmation()

def safe_execute_repair(repair_item: dict) -> bool:
    """Execute repair with safety checks."""
    
    # 1. Evaluate safety
    safety_result = safety.evaluate_repair(repair_item)
    
    if not safety_result['allowed']:
        print(f"🚫 BLOCKED: {safety_result['message']}")
        return False
    
    # 2. Request confirmation if needed
    if safety_result['requires_confirmation']:
        if not confirmation.request_confirmation([repair_item]):
            return False
    
    # 3. Create backup if required
    if safety_result['requires_backup']:
        backup_system.create_backup(
            repair_item.get('type', 'file'),
            repair_item['path']
        )
        print(f"✅ Backup created for {repair_item['path']}")
    
    # 4. Execute repair
    # ... repair logic ...
    
    return True
```

---

## Testing

```bash
# Test safety evaluation
# 1. Create test repair items
# 2. Run safety evaluation
# 3. Verify blocking works for dangerous items
# 4. Verify confirmations are requested appropriately

# Test backup system
# 1. Create test file
# 2. Create backup
# 3. Modify original
# 4. Restore from backup
# 5. Verify file is unchanged
```

---

*Engine Status: SPEC COMPLETE - Implementation ready to begin*