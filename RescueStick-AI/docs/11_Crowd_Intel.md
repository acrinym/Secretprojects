# RescueStick AI - Crowd Intelligence Engine
**Engine ID:** 11_crowd_intel
**Purpose:** Anonymous repair pattern sharing - learn from aggregated user experiences
**License:** MIT (our code)

---

## What It Does

Anonymous, privacy-preserving repair pattern database:

```
Input: User's error code (e.g., 0x80070005)
       ↓
Query local pattern database
       ↓
Output: "Similar to 847 users solved by:
         - DISM /RestoreHealth (73% success)
         - Registry restore (21% success)
         - Clean boot (6% success)"
```

## Privacy Design

```
┌─────────────────────────────────────────────────────────────┐
│                  PRIVACY ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  What is TRANSMITTED (anonymous):                          │
│  ─────────────────────────────────                         │
│  - Error code (e.g., "0x80070005")                         │
│  - Windows version (e.g., "Win11-22H2")                    │
│  - Outcome (success/fail)                                   │
│  - Repair action taken                                     │
│                                                              │
│  What is NEVER transmitted:                                │
│  ─────────────────────────────────                         │
│  - User identity                                           │
│  - Machine identifiers                                     │
│  - Personal data                                           │
│  - Network addresses                                        │
│                                                              │
│  Local Processing:                                         │
│  ─────────────────────────────────                         │
│  - All matching done locally                               │
│  - Can work fully offline                                  │
│  - Optional sync when connected                             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Code Structure

```python
#!/usr/bin/env python3
"""
Engine 11: Crowd Intelligence
License: MIT
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional
import hashlib

class CrowdIntelEngine:
    """
    Anonymous repair pattern sharing system.
    All processing local - no PII leaves the device.
    """
    
    def __init__(self, db_path="/rescue-stick/data/crowd_intel.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize local pattern database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Pattern table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_code TEXT NOT NULL,
                windows_version TEXT,
                repair_action TEXT NOT NULL,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                last_seen TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Success rate index
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_error_code 
            ON patterns(error_code, windows_version)
        """)
        
        conn.commit()
        conn.close()
    
    def record_outcome(self, error_code: str, repair_action: str, 
                       success: bool, windows_version: str = None) -> bool:
        """
        Record repair outcome locally (anonymous).
        Called after any repair attempt.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Find existing pattern or create new
        cursor.execute("""
            SELECT id, success_count, failure_count FROM patterns
            WHERE error_code = ? AND repair_action = ? AND 
                  (windows_version = ? OR windows_version IS NULL)
        """, (error_code, repair_action, windows_version))
        
        row = cursor.fetchone()
        
        if row:
            # Update existing
            pattern_id, success_count, failure_count = row
            if success:
                success_count += 1
            else:
                failure_count += 1
            
            cursor.execute("""
                UPDATE patterns 
                SET success_count = ?, failure_count = ?, last_seen = ?
                WHERE id = ?
            """, (success_count, failure_count, datetime.now().isoformat(), pattern_id))
        else:
            # Create new
            cursor.execute("""
                INSERT INTO patterns (error_code, windows_version, repair_action, 
                                     success_count, failure_count, last_seen)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (error_code, windows_version, repair_action, 
                  1 if success else 0, 0 if success else 1,
                  datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        return True
    
    def get_recommendations(self, error_code: str, windows_version: str = None) -> list:
        """
        Get repair recommendations for an error code.
        Returns ranked list of actions with success rates.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Query patterns
        cursor.execute("""
            SELECT 
                repair_action,
                SUM(success_count) as total_success,
                SUM(failure_count) as total_failure,
                COUNT(*) as occurrences
            FROM patterns
            WHERE error_code = ? AND 
                  (windows_version = ? OR windows_version IS NULL)
            GROUP BY repair_action
            ORDER BY total_success DESC
        """, (error_code, windows_version))
        
        results = []
        for row in cursor.fetchall():
            total = row['total_success'] + row['total_failure']
            success_rate = (row['total_success'] / total * 100) if total > 0 else 0
            
            results.append({
                "action": row['repair_action'],
                "success_rate": round(success_rate, 1),
                "total_attempts": total,
                "occurrences": row['occurrences']
            })
        
        conn.close()
        return results
    
    def search_similar(self, error_code: str, limit: int = 5) -> list:
        """
        Find similar error codes (fuzzy matching).
        Useful when exact code doesn't match.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Simple prefix matching for now
        cursor.execute("""
            SELECT DISTINCT error_code, 
                   COUNT(*) as usage_count,
                   SUM(success_count) as successes,
                   SUM(failure_count) as failures
            FROM patterns
            WHERE error_code LIKE ? || '%'
            GROUP BY error_code
            ORDER BY usage_count DESC
            LIMIT ?
        """, (error_code[:4], limit))
        
        results = []
        for row in cursor.fetchall():
            total = row[2] + row[3]
            success_rate = (row[2] / total * 100) if total > 0 else 0
            results.append({
                "error_code": row[0],
                "usage_count": row[1],
                "success_rate": round(success_rate, 1)
            })
        
        conn.close()
        return results
    
    def get_statistics(self) -> dict:
        """Get overall statistics (anonymous)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total patterns
        cursor.execute("SELECT COUNT(*) FROM patterns")
        total_patterns = cursor.fetchone()[0]
        
        # Unique error codes
        cursor.execute("SELECT COUNT(DISTINCT error_code) FROM patterns")
        unique_errors = cursor.fetchone()[0]
        
        # Overall success rate
        cursor.execute("SELECT SUM(success_count), SUM(failure_count) FROM patterns")
        success, failure = cursor.fetchone()
        overall_rate = (success / (success + failure) * 100) if (success + failure) > 0 else 0
        
        conn.close()
        
        return {
            "total_patterns": total_patterns,
            "unique_error_codes": unique_errors,
            "overall_success_rate": round(overall_rate, 1),
            "database_version": "1.0"
        }
    
    def export_anonymous(self, output_path: str) -> bool:
        """
        Export pattern data for sharing (anonymous).
        Removes all identifiable information.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Export aggregated patterns only
        cursor.execute("""
            SELECT 
                error_code,
                windows_version,
                repair_action,
                SUM(success_count) as success_count,
                SUM(failure_count) as failure_count
            FROM patterns
            GROUP BY error_code, windows_version, repair_action
        """)
        
        data = []
        for row in cursor.fetchall():
            data.append({
                "error_code": row[0],
                "windows_version": row[1],
                "repair_action": row[2],
                "success_count": row[3],
                "failure_count": row[4]
            })
        
        conn.close()
        
        # Write to file
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return True
    
    def import_patterns(self, import_path: str) -> int:
        """Import patterns from file (for offline updates)"""
        with open(import_path, 'r') as f:
            patterns = json.load(f)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        imported = 0
        for pattern in patterns:
            cursor.execute("""
                INSERT INTO patterns (error_code, windows_version, repair_action,
                                     success_count, failure_count, last_seen)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (pattern.get('error_code'),
                  pattern.get('windows_version'),
                  pattern.get('repair_action'),
                  pattern.get('success_count', 0),
                  pattern.get('failure_count', 0),
                  datetime.now().isoformat()))
            imported += 1
        
        conn.commit()
        conn.close()
        
        return imported


# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="RescueStick Crowd Intelligence")
    parser.add_argument("action", choices=["recommend", "record", "stats", "export", "import"])
    parser.add_argument("--error", help="Error code")
    parser.add_argument("--action-name", help="Repair action taken")
    parser.add_argument("--success", type=bool, help="Did it succeed?")
    parser.add_argument("--windows-version", help="Windows version")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--input", help="Input file path")
    
    args = parser.parse_args()
    
    engine = CrowdIntelEngine()
    
    if args.action == "recommend":
        if not args.error:
            print("Error: --error required")
        else:
            results = engine.get_recommendations(args.error, args.windows_version)
            print(json.dumps(results, indent=2))
    
    elif args.action == "record":
        if not args.error or not args.action_name or args.success is None:
            print("Error: --error, --action-name, --success required")
        else:
            engine.record_outcome(args.error, args.action_name, args.success, args.windows_version)
            print("Recorded")
    
    elif args.action == "stats":
        stats = engine.get_statistics()
        print(json.dumps(stats, indent=2))
    
    elif args.action == "export":
        if not args.output:
            print("Error: --output required")
        else:
            engine.export_anonymous(args.output)
            print(f"Exported to {args.output}")
    
    elif args.action == "import":
        if not args.input:
            print("Error: --input required")
        else:
            count = engine.import_patterns(args.input)
            print(f"Imported {count} patterns")
```

## Dependencies

```bash
# Minimal dependencies - all Python standard library + SQLite (built-in)
# No external packages required for core functionality
```

**License Notes:**
- Python 3 (PSF)
- SQLite (public domain)
- Our code (MIT)

## Data Needed

```
/rescue-stick/data/
└── crowd_intel.db     # SQLite database (auto-created)
```

Initial patterns can be seeded from:
- Pre-built pattern file (included)
- Import from shared data
- User contributions (opt-in)

## Testing

```bash
# Test database creation
python3 -c "
from crowd_intel import CrowdIntelEngine
e = CrowdIntelEngine()
print('Database initialized')
print('Stats:', e.get_statistics())
"

# Test recording
python3 11_crowd_intel.py record \
    --error 0x80070005 \
    --action-name 'DISM /RestoreHealth' \
    --success True

# Test recommendations
python3 11_crowd_intel.py recommend --error 0x80070005
```

## Pre-loaded Patterns

Bundle with common error codes:

```json
[
  {"error_code": "0x80070005", "repair_action": "DISM /RestoreHealth", "success_count": 73, "failure_count": 27},
  {"error_code": "0x80070005", "repair_action": "sfc /scannow", "success_count": 45, "failure_count": 55},
  {"error_code": "0x80070005", "repair_action": "registry restore", "success_count": 21, "failure_count": 79},
  {"error_code": "0x80073712", "repair_action": "DISM /Online /Cleanup-Image /RestoreHealth", "success_count": 85, "failure_count": 15},
  {"error_code": "0xC0000001", "repair_action": "bootrec /fixmbr", "success_count": 60, "failure_count": 40},
  {"error_code": "0xC0000001", "repair_action": "bootrec /scanos", "success_count": 35, "failure_count": 65}
]
```

---

*Engine 11 - Spec Complete*  
*License: MIT (our code), no external dependencies*