# RescueStick AI - Risk Assessment Engine
**Engine ID:** 09_risk_assessment  
**Purpose:** Evaluate repair risk, consider emotional factors, recommend escalation path  
**Dependencies:** Python 3.10+

---

## What It Does

1. **Evaluates** risk level of each repair
2. **Considers** user stress/urgency level
3. **Calculates** "brick probability" for repairs
4. **Recommends** when to stop and seek help
5. **Provides** escalation path for difficult cases

---

## Risk Model

### Risk Factors

- **System Criticality** - Is this a boot-critical file?
- **Reversibility** - Can we easily undo this repair?
- **Confidence** - How sure are we this will work?
- **Data Risk** - Could this lose user data?
- **Complexity** - How many steps are involved?

### Risk Levels

- **SAFE** - Routine repair, low risk
- **CAUTION** - Moderate risk, proceed carefully
- **DANGEROUS** - High risk, user must confirm
- **CRITICAL** - Very high risk, recommend escalation

---

## How to Build It

### Step 1: Risk Calculation

```python
# engines/09_risk_assessment.py

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

class RiskLevel(Enum):
    SAFE = "safe"
    CAUTION = "caution"
    DANGEROUS = "dangerous"
    CRITICAL = "critical"

@dataclass
class RiskAssessment:
    """Risk assessment for a repair or repair plan."""
    risk_level: RiskLevel
    risk_score: float           # 0.0 - 1.0
    brick_probability: float    # 0.0 - 1.0
    factors: List[str]
    recommendations: List[str]
    escalation_recommended: bool

class RiskAssessmentEngine:
    """
    Evaluates risk of repairs and recommends caution levels.
    """
    
    # Files that if broken = system won't boot
    BOOT_CRITICAL_PATHS = {
        'Windows/System32/ntoskrnl.exe',
        'Windows/System32/hal.dll',
        'Windows/System32/winload.exe',
        'Windows/System32/winresume.exe',
        'Windows/System32/bootmgr',
        'Windows/Boot',
        'Windows/System32/drivers',
    }
    
    # Registry keys that are high-risk
    HIGH_RISK_REGISTRY = {
        'HKLM\\SYSTEM\\CurrentControlSet\\Control',
        'HKLM\\SYSTEM\\CurrentControlSet\\Services',
        'HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run',
    }
    
    # Repair methods that are reversible
    REVERSIBLE_METHODS = {
        'file_replace': 0.9,      # Easy to replace again
        'registry_backup_restore': 0.8,
        'service_restart': 0.95,
        'dism_restore_health': 0.7,
    }
    
    # Repair methods that are hard to reverse
    IRREVERSIBLE_METHODS = {
        'registry_delete': 0.3,
        'disk_format': 0.0,
        'boot_sector_repair': 0.4,
    }
    
    def __init__(self):
        self.assessments = []
        
    def assess_repair(self, repair_item: dict, confidence: float) -> RiskAssessment:
        """
        Assess risk for a single repair.
        
        Args:
            repair_item: Repair details
            confidence: Confidence score from diagnostic engine
        """
        risk_factors = []
        risk_score = 0.0
        
        path = repair_item.get('path', '')
        method = repair_item.get('method', '')
        
        # Factor 1: System criticality
        if any(path.startswith(bcp) for bcp in self.BOOT_CRITICAL_PATHS):
            risk_factors.append("Boot-critical file")
            risk_score += 0.4
        elif any(hr in path.upper() for hr in self.HIGH_RISK_REGISTRY):
            risk_factors.append("High-risk registry key")
            risk_score += 0.3
        
        # Factor 2: Reversibility
        reversibility = self.REVERSIBLE_METHODS.get(method, 0.5)
        risk_score += (1 - reversibility) * 0.2
        
        # Factor 3: Confidence (low confidence = high risk)
        if confidence < 0.5:
            risk_factors.append("Low confidence in diagnosis")
            risk_score += 0.2
        elif confidence < 0.7:
            risk_factors.append("Moderate confidence")
            risk_score += 0.1
        
        # Factor 4: Method-specific risks
        if method in self.IRREVERSIBLE_METHODS:
            risk_factors.append(f"Method '{method}' is hard to reverse")
            risk_score += 0.2
        
        # Calculate brick probability
        # Higher for boot-critical + low confidence + irreversible
        brick_prob = min(risk_score * 0.5, 0.95)
        
        # Determine risk level
        if risk_score < 0.2:
            risk_level = RiskLevel.SAFE
            recommendations = ["Proceed normally"]
        elif risk_score < 0.4:
            risk_level = RiskLevel.CAUTION
            recommendations = [
                "Create backup before proceeding",
                "Monitor system closely after repair"
            ]
        elif risk_score < 0.7:
            risk_level = RiskLevel.DANGEROUS
            recommendations = [
                "User confirmation required",
                "Ensure backup is available",
                "Prepare recovery options"
            ]
        else:
            risk_level = RiskLevel.CRITICAL
            recommendations = [
                "STOP - Too risky to proceed automatically",
                "Recommend manual repair or professional help",
                "Consider system restore point instead"
            ]
        
        # Escalation check
        escalation = (
            risk_level in [RiskLevel.DANGEROUS, RiskLevel.CRITICAL] or
            brick_prob > 0.3
        )
        
        return RiskAssessment(
            risk_level=risk_level,
            risk_score=min(risk_score, 1.0),
            brick_probability=brick_prob,
            factors=risk_factors,
            recommendations=recommendations,
            escalation_recommended=escalation
        )
    
    def assess_repair_plan(self, repair_plan: dict, user_stress: str = "normal") -> Dict:
        """
        Assess entire repair plan.
        
        Args:
            repair_plan: Full repair plan from synthesis
            user_stress: User's stress level ("calm", "normal", "stressed", "panic")
        """
        repairs = repair_plan.get('repairs', [])
        
        assessments = []
        for repair in repairs:
            assessment = self.assess_repair(repair, repair.get('confidence', 0.7))
            assessments.append(assessment)
        
        # Aggregate risk
        dangerous_count = sum(1 for a in assessments if a.risk_level in [
            RiskLevel.DANGEROUS, RiskLevel.CRITICAL
        ])
        
        total_risk = sum(a.risk_score for a in assessments) / len(assessments) if assessments else 0
        max_brick_prob = max(a.brick_probability for a in assessments) if assessments else 0
        
        # User stress adjustment
        stress_multipliers = {
            "calm": 1.0,
            "normal": 1.0,
            "stressed": 1.2,    # More likely to make mistakes
            "panic": 1.5        # High chance of errors
        }
        
        adjusted_risk = total_risk * stress_multipliers.get(user_stress, 1.0)
        
        # Overall recommendation
        if dangerous_count > 3 or max_brick_prob > 0.5:
            overall = "STOP - Too many high-risk repairs"
            proceed = False
        elif dangerous_count > 0:
            overall = "CAUTION - Some high-risk repairs need attention"
            proceed = True
        else:
            overall = "SAFE - Proceed with repairs"
            proceed = True
        
        return {
            "proceed": proceed,
            "overall_risk": adjusted_risk,
            "dangerous_repairs": dangerous_count,
            "max_brick_probability": max_brick_prob,
            "recommendation": overall,
            "assessments": [
                {
                    "path": r.get('path'),
                    "risk_level": a.risk_level.value,
                    "factors": a.factors,
                    "recommendations": a.recommendations
                }
                for r, a in zip(repairs, assessments)
            ]
        }
    
    def get_escalation_path(self, risk_level: RiskLevel) -> Dict:
        """Get escalation recommendations based on risk level."""
        paths = {
            RiskLevel.SAFE: {
                "level": 0,
                "action": "Proceed automatically",
                "escalation": "None needed"
            },
            RiskLevel.CAUTION: {
                "level": 1,
                "action": "Inform user, proceed with backup",
                "escalation": "User aware"
            },
            RiskLevel.DANGEROUS: {
                "level": 2,
                "action": "Block until user confirms",
                "escalation": "User must explicitly approve"
            },
            RiskLevel.CRITICAL: {
                "level": 3,
                "action": "STOP - Do not proceed",
                "escalation": "Recommend professional help or system restore"
            }
        }
        
        return paths.get(risk_level, paths[RiskLevel.SAFE])
```

### Step 2: User Stress Detection

```python
class UserStressDetector:
    """
    Detect user stress level from conversation/behavior.
    """
    
    STRESS_INDICATORS = {
        "panic": ["help", "urgent", "emergency", "asap", "now", "crashed", "bricked"],
        "stressed": ["worried", "concerned", "afraid", "nervous", "careful"],
        "calm": ["when you can", "when convenient", "no rush", "take your time"]
    }
    
    def detect_stress(self, user_input: str) -> str:
        """Detect stress level from user messages."""
        text = user_input.lower()
        
        if any(word in text for word in self.STRESS_INDICATORS["panic"]):
            return "panic"
        elif any(word in text for word in self.STRESS_INDICATORS["stressed"]):
            return "stressed"
        elif any(word in text for word in self.STRESS_INDICATORS["calm"]):
            return "calm"
        else:
            return "normal"
    
    def adjust_recommendations(self, base_recommendation: str, stress_level: str) -> str:
        """Adjust recommendations based on user stress."""
        if stress_level == "panic":
            return (
                base_recommendation + 
                "\n\n⚠️  I understand you're stressed. Let's take this slowly. "
                "I'll explain each step before doing anything."
            )
        elif stress_level == "calm":
            return base_recommendation
        else:
            return base_recommendation
```

---

## Integration

```python
# In main repair flow

risk_engine = RiskAssessmentEngine()

# Assess repair plan
risk = risk_engine.assess_repair_plan(repair_plan, user_stress)

if not risk['proceed']:
    print(f"\n🚫 {risk['recommendation']}")
    print(f"   Brick probability: {risk['max_brick_probability']:.1%}")
    # Stop repairs, show escalation path
else:
    print(f"\n✅ {risk['recommendation']}")
    # Proceed with repairs
```

---

*Engine Status: SPEC COMPLETE - Implementation ready to begin*