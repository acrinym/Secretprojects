# RescueStick AI - Learning Engine
**Engine ID:** 08_learning  
**Purpose:** Track repair outcomes, improve confidence over time, learn from successes/failures  
**Dependencies:** Python 3.10+, SQLite3

---

## What It Does

1. **Tracks** repair outcomes (success/failure)
2. **Updates** confidence scores based on results
3. **Learns** patterns that predict repair success
4. **Improves** recommendations over time
5. **Adapts** confidence thresholds dynamically

---

## How to Build It

### Step 1: Database Schema

```python
# engines/08_learning.py

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class RepairOutcome:
    """Result of a repair attempt."""
    repair_id: str
    issue_type: str
    repair_method: str
    success: bool
    issues_resolved: bool
    new_issues_created: bool
    duration_seconds: int

@dataclass
class ConfidenceUpdate:
    """How confidence should be adjusted."""
    issue_type: str
    repair_method: str
    adjustment: float  # positive or negative
    reason: str

class LearningEngine:
    """
    Learns from repair outcomes to improve future confidence scores.
    """
    
    def __init__(self, db_path: str = "/rescue-stick/data/learning.db"):
        self.db_path = db_path
        self.conn = None
        self._init_database()
        
    def _init_database(self):
        """Initialize learning database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Repair outcomes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS repair_outcomes (
                id INTEGER PRIMARY KEY,
                repair_id TEXT UNIQUE,
                issue_type TEXT,
                repair_method TEXT,
                success INTEGER,
                issues_resolved INTEGER,
                new_issues_created INTEGER,
                duration_seconds INTEGER,
                timestamp TEXT,
                session_id TEXT
            )
        ''')
        
        # Confidence adjustments
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS confidence_adjustments (
                id INTEGER PRIMARY KEY,
                issue_type TEXT,
                repair_method TEXT,
                base_confidence REAL,
                adjustment REAL,
                sample_count INTEGER,
                last_updated TEXT
            )
        ''')
        
        # Pattern recognition
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS repair_patterns (
                id INTEGER PRIMARY KEY,
                pattern TEXT,
                success_rate REAL,
                sample_count INTEGER,
                recommendations TEXT
            )
        ''')
        
        conn.commit()
        
    def record_outcome(self, outcome: RepairOutcome):
        """Record the outcome of a repair."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO repair_outcomes 
            (repair_id, issue_type, repair_method, success, issues_resolved, 
             new_issues_created, duration_seconds, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            outcome.repair_id,
            outcome.issue_type,
            outcome.repair_method,
            1 if outcome.success else 0,
            1 if outcome.issues_resolved else 0,
            1 if outcome.new_issues_created else 0,
            outcome.duration_seconds,
            datetime.now().isoformat()
        ))
        
        self.conn.commit()
        
        # Trigger confidence update
        self._update_confidence(outcome)
    
    def _update_confidence(self, outcome: RepairOutcome):
        """Update confidence scores based on outcome."""
        cursor = self.conn.cursor()
        
        # Get current adjustment for this issue/repair combo
        cursor.execute('''
            SELECT * FROM confidence_adjustments 
            WHERE issue_type = ? AND repair_method = ?
        ''', (outcome.issue_type, outcome.repair_method))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing
            current_adjustment = existing[4]
            sample_count = existing[5]
            
            # Calculate new adjustment
            # If successful: increase confidence slightly
            # If failed: decrease confidence
            if outcome.success:
                new_adjustment = current_adjustment + 0.01  # Small boost
            else:
                new_adjustment = current_adjustment - 0.05  # Larger penalty
            
            # Clamp to reasonable range
            new_adjustment = max(-0.3, min(0.2, new_adjustment))
            
            cursor.execute('''
                UPDATE confidence_adjustments
                SET adjustment = ?, sample_count = ?, last_updated = ?
                WHERE issue_type = ? AND repair_method = ?
            ''', (
                new_adjustment,
                sample_count + 1,
                datetime.now().isoformat(),
                outcome.issue_type,
                outcome.repair_method
            ))
        else:
            # Create new
            initial_adjustment = 0.05 if outcome.success else -0.1
            cursor.execute('''
                INSERT INTO confidence_adjustments 
                (issue_type, repair_method, base_confidence, adjustment, sample_count, last_updated)
                VALUES (?, ?, 0.7, ?, 1, ?)
            ''', (
                outcome.issue_type,
                outcome.repair_method,
                initial_adjustment,
                datetime.now().isoformat()
            ))
        
        self.conn.commit()
    
    def get_adjusted_confidence(self, issue_type: str, repair_method: str, base_confidence: float) -> float:
        """Get confidence adjusted for this issue/repair combo."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT adjustment, sample_count 
            FROM confidence_adjustments 
            WHERE issue_type = ? AND repair_method = ?
        ''', (issue_type, repair_method))
        
        result = cursor.fetchone()
        
        if not result:
            return base_confidence
        
        adjustment, samples = result
        
        # Require minimum samples before applying adjustment
        if samples < 3:
            return base_confidence
        
        # Apply adjustment
        adjusted = base_confidence + adjustment
        
        # Clamp to valid range
        return max(0.1, min(0.95, adjusted))
    
    def get_repair_success_rate(self, issue_type: str, repair_method: str) -> float:
        """Get historical success rate for this repair method."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes
            FROM repair_outcomes
            WHERE issue_type = ? AND repair_method = ?
        ''', (issue_type, repair_method))
        
        result = cursor.fetchone()
        
        if not result or result[0] == 0:
            return 0.5  # Default 50% if no data
        
        total, successes = result
        return successes / total
    
    def suggest_best_repair_method(self, issue_type: str, available_methods: List[str]) -> Optional[str]:
        """Suggest best repair method based on history."""
        best_method = None
        best_rate = 0.0
        
        for method in available_methods:
            rate = self.get_repair_success_rate(issue_type, method)
            if rate > best_rate:
                best_rate = rate
                best_method = method
        
        # Only recommend if better than random
        if best_rate > 0.4:
            return best_method
        
        return None
    
    def get_pattern_insights(self) -> List[Dict]:
        """Get learned patterns and insights."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT issue_type, repair_method, adjustment, sample_count
            FROM confidence_adjustments
            WHERE sample_count >= 5
            ORDER BY sample_count DESC
        ''')
        
        insights = []
        for row in cursor.fetchall():
            issue_type, method, adjustment, samples = row
            
            if adjustment > 0.1:
                status = "reliable"
            elif adjustment < -0.1:
                status = "unreliable"
            else:
                status = "neutral"
            
            insights.append({
                "issue_type": issue_type,
                "repair_method": method,
                "status": status,
                "adjustment": adjustment,
                "samples": samples
            })
        
        return insights
```

### Step 2: Usage in Repair Loop

```python
# Integration with repair execution

learning = LearningEngine()

def execute_repair_with_learning(repair_item: dict) -> bool:
    """Execute repair and record outcome."""
    
    start_time = time.time()
    
    # Get adjusted confidence based on learning
    base_confidence = repair_item.get('confidence', 0.7)
    adjusted_confidence = learning.get_adjusted_confidence(
        repair_item['issue_type'],
        repair_item['method'],
        base_confidence
    )
    
    # If confidence too low, warn user
    if adjusted_confidence < 0.3:
        print(f"⚠️  Warning: This repair has low historical success rate")
    
    # Execute repair
    success = execute_repair(repair_item)
    
    duration = time.time() - start_time
    
    # Record outcome
    outcome = RepairOutcome(
        repair_id=generate_id(),
        issue_type=repair_item['issue_type'],
        repair_method=repair_item['method'],
        success=success,
        issues_resolved=check_issues_resolved(),
        new_issues_created=check_new_issues(),
        duration_seconds=int(duration)
    )
    
    learning.record_outcome(outcome)
    
    return success
```

---

*Engine Status: SPEC COMPLETE - Implementation ready to begin*