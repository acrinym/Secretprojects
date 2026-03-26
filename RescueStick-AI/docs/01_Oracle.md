# RescueStick AI - Oracle Engine
**Engine ID:** 01_oracle  
**Purpose:** Multiple diagnostic perspectives, think like different experts to find issues  
**Dependencies:** Python 3.10+

---

## What It Does

Runs 6 parallel diagnostic perspectives on the system, like having 6 different experts examine the same problem:

1. **System Administrator** - "What would break in a normal Windows setup?"
2. **Malware Researcher** - "What would malware break or hide?"
3. **Forensic Analyst** - "What evidence remains of past failures?"
4. **Update Expert** - "What could go wrong with Windows Update?"
5. **Driver Engineer** - "What driver issues cause these symptoms?"
6. **Network Admin** - "What network-related issues could cause this?"

---

## How to Build It

### Step 1: Perspective Prompts

```python
# engines/01_oracle.py

from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class PerspectiveResult:
    """Result from a single diagnostic perspective."""
    perspective: str
    findings: List[str]
    hypotheses: List[str]
    recommended_checks: List[str]
    confidence: float

class OracleEngine:
    """
    Multi-perspective diagnostic engine.
    
    Runs 6 different diagnostic viewpoints in parallel,
    synthesizes insights into actionable findings.
    """
    
    # The 6 diagnostic perspectives
    PERSPECTIVES = {
        "sysadmin": {
            "name": "System Administrator",
            "description": "Experienced Windows admin who knows common failure modes",
            "focus_areas": [
                "Service failures",
                "Boot issues", 
                "Update problems",
                "Disk space",
                "Permission issues"
            ],
            "prompt_template": """
You are an experienced Windows system administrator.
Examine the following diagnostic data and identify issues 
a typical sysadmin would notice:

Data:
{finding_data}

For each issue found, explain:
1. What you observed
2. Why it's a problem
3. What you would check first
"""
        },
        
        "malware_researcher": {
            "name": "Malware Researcher",
            "description": "Security expert who knows how malware hides and persists",
            "focus_areas": [
                "Rootkit behavior",
                "Persistence mechanisms",
                "Hidden processes",
                "Suspicious registry",
                "Unusual network connections"
            ],
            "prompt_template": """
You are a malware researcher examining a Windows system.
Look for signs of compromise:
- Files that should exist but are missing or modified
- Registry keys used by malware for persistence
- Services that shouldn't be there
- Suspicious scheduled tasks
- Host file modifications

Data:
{finding_data}

What anomalies suggest malware or persistent threat?
"""
        },
        
        "forensic_analyst": {
            "name": "Forensic Analyst",
            "description": "Digital forensics expert who reads the evidence trail",
            "focus_areas": [
                "Event log patterns",
                "Crash dumps",
                "File timestamps",
                "Recent changes",
                "Failed operations"
            ],
            "prompt_template": """
You are a digital forensics analyst.
Examine the system for evidence of what went wrong:

Data:
{finding_data}

Look for:
- Event log error patterns
- Crash dump files
- Correlated failures
- Timeline of what happened

What sequence of events led to the current state?
"""
        },
        
        "update_expert": {
            "name": "Windows Update Expert",
            "description": "Specialist in Windows Update and component store",
            "focus_areas": [
                "Component store corruption",
                "Update failures",
                "Pending updates",
                "DISM issues",
                "WinSxS problems"
            ],
            "prompt_template": """
You specialize in Windows Update and DISM.
Examine the system for update-related issues:

Data:
{finding_data}

Look for:
- Component store (WinSxS) issues
- Pending updates that failed
- Update database corruption
- DISM failures in event log

What update-related problems exist?
"""
        },
        
        "driver_engineer": {
            "name": "Driver Engineer",
            "description": "Windows driver developer who knows driver failure modes",
            "focus_areas": [
                "Driver conflicts",
                "Missing drivers",
                "Outdated drivers",
                "Driver signature issues",
                "Boot driver problems"
            ],
            "prompt_template": """
You are a Windows driver engineer.
Examine the system for driver-related issues:

Data:
{finding_data}

Look for:
- Missing or corrupted drivers
- Driver conflicts
- Signature validation failures
- Boot-critical driver issues

What driver problems exist?
"""
        },
        
        "network_admin": {
            "name": "Network Administrator",
            "description": "Network expert who knows how network issues manifest",
            "focus_areas": [
                "DNS resolution",
                "Network adapter issues",
                "Firewall rules",
                "NLA (Network Location Awareness)",
                "VPN issues"
            ],
            "prompt_template": """
You are a Windows network administrator.
Examine the system for network-related issues:

Data:
{finding_data}

Look for:
- DNS resolver issues
- Network adapter failures
- Firewall blocking
- NLA problems
- VPN/authentication failures

What network issues could cause these symptoms?
"""
        },
    }
    
    def __init__(self):
        self.perspectives = self.PERSPECTIVES
        self.results = []
        
    def run_all_perspectives(self, findings: Dict) -> List[PerspectiveResult]:
        """
        Run all 6 perspectives on the diagnostic data.
        
        Args:
            findings: Dict containing data from all other engines
        """
        results = []
        
        for perspective_id, perspective in self.perspectives.items():
            # Format the data for this perspective
            formatted_data = self._format_findings(findings, perspective['focus_areas'])
            
            # Generate perspective result (would call LLM in real implementation)
            result = self._run_perspective(
                perspective_id,
                perspective,
                formatted_data
            )
            results.append(result)
        
        self.results = results
        return results
    
    def _format_findings(self, findings: Dict, focus_areas: List[str]) -> str:
        """Format findings data for perspective."""
        # Filter and format data based on focus areas
        lines = []
        
        if "service failures" in focus_areas:
            if 'services' in findings:
                lines.append("=== Service Issues ===")
                for svc in findings['services']:
                    lines.append(f"  {svc}")
        
        if "boot issues" in focus_areas:
            if 'boot' in findings:
                lines.append("=== Boot Issues ===")
                for issue in findings['boot']:
                    lines.append(f"  {issue}")
        
        # ... more formatting
        
        return "\n".join(lines)
    
    def _run_perspective(self, perspective_id: str, perspective: Dict, data: str) -> PerspectiveResult:
        """Run a single perspective analysis."""
        # In real implementation, this would call an LLM
        # For now, return placeholder that would be replaced
        
        prompt = perspective['prompt_template'].format(finding_data=data)
        
        # Would use LLM here
        # result = llm.generate(prompt)
        
        # Placeholder:
        return PerspectiveResult(
            perspective=perspective['name'],
            findings=[],  # Would be populated by LLM
            hypotheses=[],  # Would be populated by LLM
            recommended_checks=[],  # Would be populated by LLM
            confidence=0.0  # Would be calculated by LLM
        )
    
    def synthesize_perspectives(self, results: List[PerspectiveResult]) -> Dict:
        """
        Synthesize results from all perspectives into unified findings.
        
        Identifies:
        - Common findings across perspectives
        - Unique insights from each
        - Priority items to investigate
        """
        all_findings = []
        
        for result in results:
            all_findings.extend(result.findings)
        
        # Identify patterns that appear in multiple perspectives
        from collections import Counter
        finding_counts = Counter(all_findings)
        
        # High agreement = high confidence
        common_findings = [
            {"finding": f, "count": c, "confidence": c / len(results)}
            for f, c in finding_counts.items()
            if c > 1  # Appears in multiple perspectives
        ]
        
        # Unique findings (only one perspective noticed)
        unique_findings = [
            {"finding": f, "perspective": results[i].perspective}
            for i, result in enumerate(results)
            for f in result.findings
            if finding_counts[f] == 1
        ]
        
        return {
            "high_confidence_findings": sorted(
                common_findings, 
                key=lambda x: x['confidence'], 
                reverse=True
            ),
            "unique_insights": unique_findings,
            "all_hypotheses": [
                hyp 
                for result in results 
                for hyp in result.hypotheses
            ],
            "recommended_checks": list(set(
                check 
                for result in results 
                for check in result.recommended_checks
            ))
        }
```

### Step 2: Example Output

```python
# Example output from Oracle engine

{
    "perspectives_run": 6,
    "synthesis": {
        "high_confidence_findings": [
            {"finding": "Service 'Windows Update' failed to start", "count": 3, "confidence": 0.75},
            {"finding": "Component store has orphaned entries", "count": 2, "confidence": 0.5},
        ],
        "unique_insights": [
            {"finding": "Suspicious scheduled task found", "perspective": "malware_researcher"},
            {"finding": "DNS client service in stopped state", "perspective": "network_admin"},
        ],
        "recommended_checks": [
            "Check DISM /RestoreHealth",
            "Verify Windows Update service permissions",
            "Review scheduled tasks for anomalies",
            "Test DNS resolution",
        ]
    }
}
```

---

## Integration with Other Engines

```python
# Oracle runs after other engines have completed

def run_oracle(diagnostic_data: dict) -> dict:
    """
    Run Oracle engine after File Scanner, Registry Parser, etc.
    """
    oracle = OracleEngine()
    
    # Get findings from all engines
    findings = {
        'files': file_scanner_results,
        'registry': registry_results,
        'events': event_log_results,
        'services': service_status,
        'boot': boot_info,
    }
    
    # Run all 6 perspectives
    results = oracle.run_all_perspectives(findings)
    
    # Synthesize
    synthesis = oracle.synthesize_perspectives(results)
    
    return synthesis
```

---

## Why This Matters

- **Different experts see different things** - Malware researcher notices what sysadmin misses
- **Cross-validation** - Findings seen by multiple perspectives are more reliable
- **Comprehensive** - Each perspective has unique focus areas
- **Actionable** - Synthesized output goes to Diagnostic Synthesis engine

---

## Testing

```bash
# Test with known issue scenarios
# 1. Create system with known problem
# 2. Run all engines including Oracle
# 3. Verify perspectives produce different insights
# 4. Check synthesis identifies common findings
```

---

*Engine Status: SPEC COMPLETE - Implementation ready to begin*