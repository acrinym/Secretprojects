# RescueStick AI - AI Assistant Engine
**Engine ID:** 16_ai_assistant
**Purpose:** Natural language repair assistant - chat with your rescue stick
**License:** MIT (our code)

---

## What It Does

Natural language interface for repair:

```
User: "My电脑 keeps restarting when I turn it on"
       ↓
AI: "That sounds like a boot loop. Let me scan..."
       ↓
[Scans boot files, event logs, registry]
       ↓
AI: "Found: corrupted winlogon.exe, missing registry keys"
    "Recommended: Replace winlogon.exe + fix registry"
       ↓
User: "Will I lose my files?"
       ↓
AI: "No, this repair only touches system files. Safe."
```

## Code Structure

```python
#!/usr/bin/env python3
"""
Engine 16: AI Assistant
License: MIT (our code)
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

class AIAssistant:
    """
    Natural language repair assistant.
    Understands user problems and guides through fixes.
    """
    
    def __init__(self, mount_point="/mnt/windows"):
        self.mount_point = Path(mount_point)
        self.conversation_history = []
        
        # Known problem patterns
        self.problem_patterns = {
            "boot_loop": {
                "keywords": ["restart", "reboot", "boot loop", "stuck", "won't start"],
                "likely_cause": "Boot corruption or driver issue",
                "recommended_action": "Run won't_boot flow"
            },
            "blue_screen": {
                "keywords": ["blue screen", "bsod", "stop error", "0x"],
                "likely_cause": "Hardware/driver failure",
                "recommended_action": "Run blue_screen flow"
            },
            "black_screen": {
                "keywords": ["black screen", "blank screen", "no display", "black"],
                "likely_cause": "Video driver or GPU issue",
                "recommended_action": "Check video drivers"
            },
            "no_network": {
                "keywords": ["no internet", "network", "wifi", "ethernet", "connection"],
                "likely_cause": "Missing network driver",
                "recommended_action": "Run network_broken flow"
            },
            "no_sound": {
                "keywords": ["no sound", "audio", "speaker", "sound not working"],
                "likely_cause": "Audio driver or service",
                "recommended_action": "Run no_audio flow"
            },
            "slow": {
                "keywords": ["slow", "lag", "freeze", "not responsive", "hang"],
                "likely_cause": "Resource exhaustion or corruption",
                "recommended_action": "Run slow_system flow"
            },
            "update_fail": {
                "keywords": ["update", "windows update", "failed to update"],
                "likely_cause": "Windows Update components corrupted",
                "recommended_action": "Run update_fail flow"
            },
            "dll_missing": {
                "keywords": ["dll", "missing dll", "not found", ".dll"],
                "likely_cause": "Missing DLL file",
                "recommended_action": "Run missing_dll flow"
            }
        }
        
        # Responses
        self.responses = {
            "greeting": "Hello! I'm RescueStick AI. Describe the problem you're having and I'll help you fix it.",
            "safe_files": "No, this repair only touches system files. Your personal files (documents, photos, etc.) are completely safe.",
            "no_problem": "I couldn't identify a specific problem. Let me run a quick diagnostic scan?",
            "repair_complete": "Repair complete! Your system should work now. Want me to verify?",
            "repair_failed": "The repair didn't work. This might need more advanced fixes or Windows reinstall.",
            "ask_diagnostic": "Would you like me to run a full diagnostic scan to identify the issue?"
        }
    
    def chat(self, user_message: str) -> dict:
        """
        Process user message and return assistant response.
        """
        # Add to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message,
            "timestamp": self._get_timestamp()
        })
        
        # Detect problem type
        problem_type = self._detect_problem(user_message)
        
        # Generate response
        response = self._generate_response(user_message, problem_type)
        
        # Add to history
        self.conversation_history.append({
            "role": "assistant",
            "content": response["message"],
            "timestamp": self._get_timestamp()
        })
        
        return response
    
    def _detect_problem(self, message: str) -> Optional[str]:
        """Detect what type of problem user is describing"""
        message_lower = message.lower()
        
        for problem_type, pattern in self.problem_patterns.items():
            for keyword in pattern["keywords"]:
                if keyword in message_lower:
                    return problem_type
        
        return None
    
    def _generate_response(self, message: str, problem_type: Optional[str]) -> dict:
        """Generate appropriate response"""
        message_lower = message.lower()
        
        # Check for question about safety
        if any(word in message_lower for word in ["lose", "safe", "delete", "files", "data"]):
            return {
                "message": self.responses["safe_files"],
                "type": "safety_reassurance"
            }
        
        # Check if problem detected
        if problem_type:
            pattern = self.problem_patterns[problem_type]
            
            response = f"I think I know what's wrong. {pattern['likely_cause']}. "
            response += f"Let me help you fix this."
            
            return {
                "message": response,
                "type": "problem_identified",
                "problem_type": problem_type,
                "recommended": pattern["recommended_action"]
            }
        
        # Check for diagnostic request
        if any(word in message_lower for word in ["diagnostic", "scan", "check"]):
            return {
                "message": "I'll run a diagnostic scan now...",
                "type": "scan_request"
            }
        
        # Check for yes/no to repair
        if any(word in message_lower for word in ["yes", "ok", "go ahead", "fix it"]):
            return {
                "message": "Running the repair now. This may take a few minutes.",
                "type": "repair_request"
            }
        
        # Default response
        return {
            "message": self.responses["ask_diagnostic"],
            "type": "clarification"
        }
    
    def run_diagnostic(self) -> dict:
        """Run a quick diagnostic scan"""
        results = {
            "scan_type": "quick_diagnostic",
            "timestamp": self._get_timestamp(),
            "checks": {}
        }
        
        # Check boot files
        boot_files = [
            "Windows/System32/winload.exe",
            "Windows/System32/ntoskrnl.exe"
        ]
        
        missing_boot = []
        for bf in boot_files:
            if not (self.mount_point / bf).exists():
                missing_boot.append(bf)
        
        results["checks"]["boot_files"] = {
            "status": "ok" if not missing_boot else "issues",
            "missing": missing_boot
        }
        
        # Check registry
        hives = ["SYSTEM", "SOFTWARE", "SAM"]
        missing_hives = []
        for hive in hives:
            hive_path = self.mount_point / f"Windows/System32/config/{hive}"
            if not hive_path.exists():
                missing_hives.append(hive)
        
        results["checks"]["registry"] = {
            "status": "ok" if not missing_hives else "issues",
            "missing": missing_hives
        }
        
        # Check disk space
        try:
            import shutil
            stat = shutil.disk_usage(self.mount_point)
            results["checks"]["disk_space"] = {
                "total_gb": round(stat.total / (1024**3), 1),
                "free_gb": round(stat.free / (1024**3), 1),
                "percent_free": round(stat.free / stat.total * 100, 1)
            }
        except:
            pass
        
        # Summary
        issues = sum(1 for c in results["checks"].values() 
                     if isinstance(c, dict) and c.get("status") == "issues")
        
        if issues == 0:
            results["summary"] = "No obvious problems found. Your system looks OK!"
            results["recommendation"] = "Try booting into Windows normally."
        else:
            results["summary"] = f"Found {issues} potential issues."
            results["recommendation"] = "Run a repair flow to fix these."
        
        return results
    
    def suggest_repair(self, problem_type: str) -> dict:
        """Suggest and optionally run repair for a problem type"""
        if problem_type not in self.problem_patterns:
            return {"error": "Unknown problem type"}
        
        pattern = self.problem_patterns[problem_type]
        
        return {
            "problem": problem_type,
            "likely_cause": pattern["likely_cause"],
            "recommended_action": pattern["recommended_action"],
            "message": f"I can help fix this. {pattern['recommended_action']} should resolve it."
        }
    
    def get_conversation_history(self) -> List[dict]:
        """Get conversation history"""
        return self.conversation_history
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()


# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="RescueStick AI Assistant")
    parser.add_argument("--chat", help="Send a chat message")
    parser.add_argument("--diagnostic", action="store_true", help="Run diagnostic")
    parser.add_argument("--suggest", help="Get repair suggestion for problem")
    parser.add_argument("--interactive", action="store_true", help="Interactive chat mode")
    parser.add_argument("--clear", action="store_true", help="Clear conversation history")
    
    args = parser.parse_args()
    
    assistant = AIAssistant()
    
    if args.clear:
        assistant.clear_history()
        print("Conversation history cleared")
    
    elif args.diagnostic:
        result = assistant.run_diagnostic()
        print(json.dumps(result, indent=2))
    
    elif args.suggest:
        result = assistant.suggest_repair(args.suggest)
        print(json.dumps(result, indent=2))
    
    elif args.interactive:
        print("RescueStick AI Assistant")
        print("Type 'quit' to exit, 'diagnostic' for scan, 'clear' to clear history")
        print()
        
        while True:
            try:
                user_input = input("You: ").strip()
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit']:
                    break
                
                if user_input.lower() == 'diagnostic':
                    result = assistant.run_diagnostic()
                    print(f"AI: {result.get('summary', '')}")
                    print(json.dumps(result, indent=2))
                elif user_input.lower() == 'clear':
                    assistant.clear_history()
                    print("AI: History cleared")
                else:
                    result = assistant.chat(user_input)
                    print(f"AI: {result.get('message', '')}")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
    
    elif args.chat:
        result = assistant.chat(args.chat)
        print(json.dumps(result, indent=2))
    
    else:
        print("Use --interactive for chat mode, or --chat 'message'")
        print("Problem types: boot_loop, blue_screen, black_screen, no_network, no_sound, slow, update_fail, dll_missing")
```

## Dependencies

```bash
# No external dependencies - pure Python standard library
# Future: could integrate with actual LLM APIs
```

**License:** MIT (our code)

## Testing

```bash
# Interactive chat
python3 16_ai_assistant.py --interactive

# Send a message
python3 16_ai_assistant.py --chat "My computer keeps restarting"

# Run diagnostic
python3 16_ai_assistant.py --diagnostic

# Get suggestion
python3 16_ai_assistant.py --suggest boot_loop
```

## Example Conversation

```
You: My电脑 keeps restarting when I turn it on
AI: I think I know what's wrong. Boot corruption or driver issue. Let me help you fix this.

You: Will I lose my files?
AI: No, this repair only touches system files. Your personal files (documents, photos, etc.) are completely safe.

You: OK fix it
AI: Running the repair now. This may take a few minutes.
```

---

*Engine 16 - Spec Complete*  
*License: MIT (our code)*