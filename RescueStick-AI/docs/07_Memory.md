# RescueStick AI - Memory Engine
**Engine ID:** 07_memory  
**Purpose:** Session continuity, remember previous scans, track changes between sessions  
**Dependencies:** Python 3.10+, SQLite3

---

## What It Does

1. **Persists** scan results between sessions
2. **Tracks** what changed since last scan
3. **Maintains** historical context for diagnosis
4. **Provides** baseline for comparison over time

---

## How to Build It

### Step 1: Database Schema

```python
# engines/07_memory.py

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class ScanSession:
    """Record of a single scan session."""
    session_id: str
    timestamp: str
    os_version: str
    mount_point: str
    files_scanned: int
    issues_found: int
    repair_actions: List[str]
    status: str  # "completed", "partial", "failed"

@dataclass
class FileSnapshot:
    """Snapshot of a file at a point in time."""
    session_id: str
    path: str
    sha256: str
    size: int
    modified_time: int

@dataclass
class IssueHistory:
    """History of an issue across sessions."""
    issue_id: str
    first_seen: str
    last_seen: str
    session_count: int
    attempts_to_fix: int
    resolved: bool

class MemoryEngine:
    """
    Maintains session memory and historical context.
    """
    
    def __init__(self, db_path: str = "/rescue-stick/data/memory.db"):
        self.db_path = db_path
        self.conn = None
        self._init_database()
        
    def _init_database(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY,
                session_id TEXT UNIQUE,
                timestamp TEXT,
                os_version TEXT,
                mount_point TEXT,
                files_scanned INTEGER,
                issues_found INTEGER,
                repair_actions TEXT,
                status TEXT
            )
        ''')
        
        # File snapshots
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_snapshots (
                id INTEGER PRIMARY KEY,
                session_id TEXT,
                path TEXT,
                sha256 TEXT,
                size INTEGER,
                modified_time INTEGER,
                INDEX idx_path (path),
                INDEX idx_session (session_id)
            )
        ''')
        
        # Issue tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS issue_history (
                id INTEGER PRIMARY KEY,
                issue_id TEXT UNIQUE,
                issue_type TEXT,
                first_seen TEXT,
                last_seen TEXT,
                session_count INTEGER DEFAULT 1,
                attempts_to_fix INTEGER DEFAULT 0,
                resolved INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        
    def start_session(self, os_version: str, mount_point: str) -> str:
        """Start a new scan session."""
        session_id = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO sessions (session_id, timestamp, os_version, mount_point, status)
            VALUES (?, ?, ?, ?, 'in_progress')
        ''', (session_id, datetime.now().isoformat(), os_version, mount_point))
        
        self.conn.commit()
        return session_id
    
    def record_file_snapshot(self, session_id: str, path: str, sha256: str, size: int, modified_time: int):
        """Record file state."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO file_snapshots (session_id, path, sha256, size, modified_time)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, path, sha256, size, modified_time))
    
    def track_issue(self, issue_id: str, issue_type: str):
        """Track an issue across sessions."""
        cursor = self.conn.cursor()
        
        # Check if issue already exists
        cursor.execute('SELECT * FROM issue_history WHERE issue_id = ?', (issue_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing
            cursor.execute('''
                UPDATE issue_history 
                SET last_seen = ?, session_count = session_count + 1
                WHERE issue_id = ?
            ''', (datetime.now().isoformat(), issue_id))
        else:
            # Insert new
            cursor.execute('''
                INSERT INTO issue_history (issue_id, issue_type, first_seen, last_seen)
                VALUES (?, ?, ?, ?)
            ''', (issue_id, issue_type, datetime.now().isoformat(), datetime.now().isoformat()))
        
        self.conn.commit()
    
    def get_session_history(self, limit: int = 10) -> List[ScanSession]:
        """Get recent scan sessions."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM sessions 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        return [
            ScanSession(
                session_id=r[1],
                timestamp=r[2],
                os_version=r[3],
                mount_point=r[4],
                files_scanned=r[5],
                issues_found=r[6],
                repair_actions=json.loads(r[7]) if r[7] else [],
                status=r[8]
            )
            for r in rows
        ]
    
    def compare_to_previous(self, session_id: str) -> Dict:
        """Compare current scan to previous session."""
        # Get previous session
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT session_id FROM sessions 
            WHERE id = (SELECT id FROM sessions WHERE session_id = ?)-1
        ''', (session_id,))
        
        prev_row = cursor.fetchone()
        if not prev_row:
            return {"first_scan": True}
        
        prev_session_id = prev_row[0]
        
        # Find new files (in current but not in previous)
        cursor.execute('''
            SELECT path FROM file_snapshots WHERE session_id = ?
            EXCEPT
            SELECT path FROM file_snapshots WHERE session_id = ?
        ''', (session_id, prev_session_id))
        
        new_files = [r[0] for r in cursor.fetchall()]
        
        # Find deleted files (in previous but not in current)
        cursor.execute('''
            SELECT path FROM file_snapshots WHERE session_id = ?
            EXCEPT
            SELECT path FROM file_snapshots WHERE session_id = ?
        ''', (prev_session_id, session_id))
        
        deleted_files = [r[0] for r in cursor.fetchall()]
        
        # Find modified files
        # (same path, different hash)
        
        return {
            "first_scan": False,
            "new_files": new_files[:10],  # Limit
            "deleted_files": deleted_files[:10],
            "modified_files": []  # Would need more complex query
        }
    
    def complete_session(self, session_id: str, issues_found: int, repair_actions: List[str]):
        """Mark session as complete."""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE sessions 
            SET issues_found = ?, repair_actions = ?, status = 'completed'
            WHERE session_id = ?
        ''', (issues_found, json.dumps(repair_actions), session_id))
        
        self.conn.commit()
```

---

## Integration

```python
# Usage in main diagnostic flow

memory = MemoryEngine()

# Start new session
session_id = memory.start_session(os_version, mount_point)

# During scan, record file states
for file_info in scanner_results:
    memory.record_file_snapshot(
        session_id, 
        file_info.path, 
        file_info.sha256,
        file_info.size,
        file_info.modified_time
    )

# Track issues
for issue in found_issues:
    memory.track_issue(issue.id, issue.type)

# Complete session
memory.complete_session(session_id, len(issues), repairs_performed)

# Compare to previous if available
changes = memory.compare_to_previous(session_id)
```

---

*Engine Status: SPEC COMPLETE - Implementation ready to begin*