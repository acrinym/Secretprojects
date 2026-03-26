# RescueStick AI - Diagnostic Synthesis Engine
**Engine ID:** 06_diagnostic_synthesis  
**Purpose:** Integrate all engine findings, generate repair strategy, calculate confidence scores  
**Dependencies:** Python 3.10+, all other engines

---

## What It Does

1. **Receives** outputs from all diagnostic engines (files, registry, events, hashes)
2. **Correlates** findings - links related issues together
3. **Calculates** confidence scores for each diagnosis
4. **Generates** prioritized repair strategy
5. **Produces** final report for user/repair execution

---

## How It Works

### The Synthesis Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   File      │    │  Registry   │    │   Event     │
│   Scanner   │    │   Parser    │    │    Log      │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │   DIAGNOSTIC           │
              │   SYNTHESIS           │
              │                       │
              │  1. Normalize         │
              │  2. Correlate         │
              │  3. Score             │
              │  4. Prioritize        │
              │  5. Generate Plan     │
              └───────────┬────────────┘
                          │
                          ▼
              ┌────────────────────────┐
              │   REPAIR STRATEGY     │
              │   (Output)            │
              └────────────────────────┘
```

---

## How to Build It

### Step 1: Data Structures

```python
# engines/06_diagnostic_synthesis.py

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from enum import Enum
from datetime import datetime

class IssueType(Enum):
    FILE_CORRUPTED = "file_corrupted"
    FILE_MISSING = "file_missing"
    FILE_MODIFIED = "file_modified"
    REGISTRY_CORRUPTED = "registry_corrupted"
    REGISTRY_MISSING = "registry_missing"
    EVENT_ERROR = "event_error"
    SERVICE_FAILED = "service_failed"
    DRIVER_MISSING = "driver_missing"
    UPDATE_FAILED = "update_failed"
    BOOT_FAILURE = "boot_failure"

class Severity(Enum):
    CRITICAL = 1    # System won't boot
    HIGH = 2       # Major functionality broken
    MEDIUM = 3     # Functionality impaired
    LOW = 4        # Minor issue, cosmetic

@dataclass
class DiagnosticFinding:
    """Single finding from any engine."""
    issue_type: IssueType
    path: str                            # File path, registry key, etc.
    description: str
    severity: Severity
    source_engine: str                   # Which engine found this
    raw_data: Dict                       # Engine-specific data
    confidence: float                    # 0.0 - 1.0

@dataclass
class CorrelatedIssue:
    """Group of related findings that represent a single problem."""
    root_cause: str                      # "Windows Update corrupted"
    findings: List[DiagnosticFinding]
    severity: Severity
    total_confidence: float              # Combined confidence
    repair_steps: List[str]             # How to fix
    risk_level: str                     # "safe", "moderate", "risky"

@dataclass
class RepairPlan:
    """Final repair strategy."""
    issues: List[CorrelatedIssue]
    total_issues: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    estimated_duration: str              # "15 minutes", "2 hours"
    user_confirmations_needed: List[str]
    rollback_available: bool
    success_probability: float           # 0.0 - 1.0
```

### Step 2: Core Synthesis Logic

```python
class DiagnosticSynthesis:
    """
    Synthesizes findings from all engines into coherent repair strategy.
    
    Uses:
    - Adaptive confidence from Synoptic Executive
    - Pattern taxonomy for correlation
    - Risk assessment for repair decisions
    """
    
    # Issue correlation rules
    CORRELATION_RULES = {
        # If file is missing AND event log shows "file not found" errors
        # → Same issue, link them
        ("file_missing", "event_error"): lambda f, e: (
            "file_not_found" in e.description.lower()
        ),
        
        # If registry key is corrupt AND event shows service failure
        # → Likely root cause is registry
        ("registry_corrupted", "service_failed"): lambda r, s: True,
        
        # If multiple files in same directory are corrupted
        # → Likely same cause (disk issue, malware, etc.)
        ("file_corrupted", "file_corrupted"): lambda f1, f2: (
            f1.path.split('/')[0] == f2.path.split('/')[0]  # Same dir
        ),
    }
    
    def __init__(self):
        self.findings = []
        self.correlated_issues = []
        
    def ingest_findings(self, findings: List[DiagnosticFinding]):
        """
        Receive findings from all engines.
        
        Called after each engine completes scanning.
        """
        self.findings.extend(findings)
        
    def normalize_findings(self) -> None:
        """
        Normalize findings to common format.
        
        Ensures all findings have:
        - Standardized issue types
        - Severity assigned
        - Confidence calculated
        """
        for finding in self.findings:
            # Apply adaptive confidence adjustment
            finding.confidence = self._adjust_confidence(finding)
            
            # Ensure severity is set
            if not finding.severity:
                finding.severity = self._infer_severity(finding)
    
    def _adjust_confidence(self, finding: DiagnosticFinding) -> float:
        """
        Adaptive confidence calculation (from Synoptic Executive).
        
        Adjust base confidence based on:
        - Evidence count (more findings = higher confidence)
        - Source reliability (file scanner = high, event log = medium)
        - Pattern match strength
        """
        base = finding.confidence
        
        # Count supporting evidence
        evidence_count = len([f for f in self.findings 
                              if f.path == finding.path])
        
        # More evidence = higher confidence
        if evidence_count > 3:
            base += 0.1
        elif evidence_count > 1:
            base += 0.05
        
        # Adjust by source reliability
        source_weights = {
            "file_scanner": 1.0,
            "hash_verifier": 1.0,
            "registry_parser": 0.9,
            "event_log_engine": 0.7,
        }
        source_weight = source_weights.get(finding.source_engine, 0.5)
        
        # Boost confidence for high-reliability sources
        if source_weight >= 0.9:
            base += 0.05
        
        return min(base, 0.95)  # Cap at 95%
    
    def _infer_severity(self, finding: DiagnosticFinding) -> Severity:
        """Infer severity from issue type if not set."""
        critical_types = {
            IssueType.BOOT_FAILURE,
            IssueType.FILE_MISSING,
        }
        
        high_types = {
            IssueType.FILE_CORRUPTED,
            IssueType.REGISTRY_CORRUPTED,
            IssueType.DRIVER_MISSING,
            IssueType.SERVICE_FAILED,
        }
        
        if finding.issue_type in critical_types:
            return Severity.CRITICAL
        elif finding.issue_type in high_types:
            return Severity.HIGH
        else:
            return Severity.MEDIUM
    
    def correlate_findings(self) -> List[CorrelatedIssue]:
        """
        Group related findings into correlated issues.
        
        Uses correlation rules to identify findings that are
        different symptoms of the same root cause.
        """
        # Group by path
        by_path: Dict[str, List[DiagnosticFinding]] = {}
        for f in self.findings:
            key = f.path.split('/')[0]  # Group by directory/root
            if key not in by_path:
                by_path[key] = []
            by_path[key].append(f)
        
        # Create correlated issues
        issues = []
        
        # For each path group, check if multiple related issues
        for path, findings in by_path.items():
            if len(findings) > 1:
                # Multiple issues in same area - likely related
                issue = CorrelatedIssue(
                    root_cause=self._identify_root_cause(findings),
                    findings=findings,
                    severity=max(f.severity for f in findings),
                    total_confidence=sum(f.confidence for f in findings) / len(findings),
                    repair_steps=self._generate_repair_steps(findings),
                    risk_level=self._assess_risk(findings)
                )
                issues.append(issue)
            elif len(findings) == 1:
                # Single issue - still create entry
                issue = CorrelatedIssue(
                    root_cause=findings[0].description,
                    findings=findings,
                    severity=findings[0].severity,
                    total_confidence=findings[0].confidence,
                    repair_steps=self._generate_repair_steps(findings),
                    risk_level=self._assess_risk(findings)
                )
                issues.append(issue)
        
        self.correlated_issues = issues
        return issues
    
    def _identify_root_cause(self, findings: List[DiagnosticFinding]) -> str:
        """Identify likely root cause from findings."""
        # Use pattern taxonomy here
        issue_types = set(f.issue_type for f in findings)
        
        if IssueType.FILE_CORRUPTED in issue_types:
            return "System file corruption - run DISM/SFC"
        elif IssueType.REGISTRY_CORRUPTED in issue_types:
            return "Registry corruption - restore from backup"
        elif IssueType.SERVICE_FAILED in issue_types:
            return "Service failure - check dependencies"
        else:
            return "Multiple issues - needs detailed analysis"
    
    def _generate_repair_steps(self, findings: List[DiagnosticFinding]) -> List[str]:
        """Generate repair steps for findings."""
        steps = []
        
        for f in findings:
            if f.issue_type == IssueType.FILE_CORRUPTED:
                steps.append(f"Replace corrupted file: {f.path}")
            elif f.issue_type == IssueType.FILE_MISSING:
                steps.append(f"Download missing file: {f.path}")
            elif f.issue_type == IssueType.REGISTRY_CORRUPTED:
                steps.append(f"Repair registry key: {f.path}")
            elif f.issue_type == IssueType.SERVICE_FAILED:
                steps.append(f"Restart/repair service: {f.path}")
        
        return steps
    
    def _assess_risk(self, findings: List[DiagnosticFinding]) -> str:
        """Assess risk level of repairs."""
        critical_count = sum(1 for f in findings if f.severity == Severity.CRITICAL)
        
        if critical_count > 0:
            return "moderate"  # Risky but necessary
        else:
            return "safe"
    
    def generate_repair_plan(self) -> RepairPlan:
        """
        Generate final repair plan.
        
        Sorts issues by severity, calculates stats,
        produces actionable output.
        """
        # Sort by severity (critical first)
        sorted_issues = sorted(
            self.correlated_issues,
            key=lambda x: x.severity.value
        )
        
        # Count by severity
        critical = sum(1 for i in sorted_issues if i.severity == Severity.CRITICAL)
        high = sum(1 for i in sorted_issues if i.severity == Severity.HIGH)
        medium = sum(1 for i in sorted_issues if i.severity == Severity.MEDIUM)
        low = sum(1 for i in sorted_issues if i.severity == Severity.LOW)
        
        # Calculate success probability
        avg_confidence = sum(i.total_confidence for i in sorted_issues) / len(sorted_issues) if sorted_issues else 0.0
        
        # Estimate duration
        duration = self._estimate_duration(sorted_issues)
        
        # Identify what needs user confirmation
        confirmations = [
            issue.root_cause 
            for issue in sorted_issues 
            if issue.risk_level == "moderate"
        ]
        
        return RepairPlan(
            issues=sorted_issues,
            total_issues=len(sorted_issues),
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low,
            estimated_duration=duration,
            user_confirmations_needed=confirmations,
            rollback_available=True,
            success_probability=avg_confidence
        )
    
    def _estimate_duration(self, issues: List[CorrelatedIssue]) -> str:
        """Estimate time to complete repairs."""
        # Simple estimation based on issue count
        total = len(issues)
        
        if total <= 5:
            return "15-30 minutes"
        elif total <= 10:
            return "30-60 minutes"
        elif total <= 20:
            return "1-2 hours"
        else:
            return "2-4 hours"
```

### Step 3: Integration

```python
# Main diagnostic flow

def run_full_diagnosis(mount_point: str, baseline_db: str):
    """
    Run all engines and synthesize results.
    """
    synthesis = DiagnosticSynthesis()
    
    # Run each engine and ingest findings
    # 1. File Scanner
    scanner = FileScanner(mount_point)
    files = scanner.scan_system_files()
    scanner_findings = [
        DiagnosticFinding(
            issue_type=IssueType.FILE_CORRUPTED if f.is_corrupted else IssueType.FILE_MISSING,
            path=f.path,
            description=f"Hash mismatch: {f.sha256[:16]}...",
            severity=Severity.HIGH if f.is_system_file else Severity.MEDIUM,
            source_engine="file_scanner",
            raw_data={"file_info": f}
        )
        for f in files if f.is_corrupted
    ]
    synthesis.ingest_findings(scanner_findings)
    
    # 2. Registry Parser
    # ... same pattern ...
    
    # 3. Event Log Engine
    # ... same pattern ...
    
    # 4. Hash Verifier
    # ... same pattern ...
    
    # Synthesize
    synthesis.normalize_findings()
    issues = synthesis.correlate_findings()
    plan = synthesis.generate_repair_plan()
    
    return plan
```

---

## Output Format

```json
{
  "diagnosis_summary": {
    "os_version": "Windows 10 22H2",
    "scan_time": "2026-03-25T12:00:00",
    "total_issues": 7,
    "critical": 1,
    "high": 3,
    "medium": 2,
    "low": 1,
    "confidence": 0.87
  },
  "repair_plan": {
    "estimated_duration": "30-60 minutes",
    "success_probability": "87%",
    "rollbacks_available": true,
    "issues": [
      {
        "id": 1,
        "root_cause": "Windows Update component store corrupted",
        "severity": "critical",
        "findings": [
          "File: Windows/System32/ApiSetSchema.dll - CORRUPTED",
          "Event ID 301 - Component store corrupted"
        ],
        "repair_steps": [
          "Run DISM /RestoreHealth",
          "Run SFC /Scannow",
          "Reboot"
        ],
        "confidence": 0.92,
        "requires_confirmation": true
      }
    ]
  }
}
```

---

## Testing

```bash
# Test synthesis with known issue combinations
# 1. Create test findings from multiple engines
# 2. Run synthesis
# 3. Verify correlation works correctly
# 4. Check repair plan is sensible
```

---

*Engine Status: SPEC COMPLETE - Implementation ready to begin*