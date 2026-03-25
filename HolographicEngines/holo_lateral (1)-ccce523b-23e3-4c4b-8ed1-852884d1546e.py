"""
HOLO LATERAL - THE LATERAL JUMP ENGINE
======================================
"If the door is locked, try the window. If the window is stuck, break the wall."

Purpose:
When a direct approach fails (e.g., "Tesla Coil Drone"), this engine identifies the *Function*
and searches for *Functional Equivalents* in other domains.

Logic:
1. Identify Core Function (e.g., "Move energy through air").
2. Identify Constraint causing failure (e.g., "Dispersion / Inverse Square Law").
3. Generate Lateral Strategies that bypass the constraint.
4. Validate and search for those strategies.
5. Detect dependencies and generate tests for code-based jumps.

Improvements (Constructor-style):
- Robust JSON extraction (handles LLM hallucinations)
- Jump validation (feasibility checks)
- Dependency detection (for code-based mechanisms)
- Test generation (executable artifacts)
- Error handling & self-healing
"""

import logging
import json
import re
import os
import ast
import google.generativeai as genai
from holo_scout import HoloScout
from typing import Dict, List, Optional, Any

# Setup Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [LATERAL] - %(message)s')
logger = logging.getLogger(__name__)

class LateralEngine:
    def __init__(self, model, validation_enabled=True, scout=None):
        """
        Args:
            model: Gemini client (for analyze_failure).
            validation_enabled: Whether to validate lateral jumps.
            scout: Optional HoloScout instance to reuse (API keys, rate limits). If None, creates a new Scout with model only.
        """
        self.model = model
        self.scout = scout if scout is not None else HoloScout(model)
        self.validation_enabled = validation_enabled

    def _robust_json_extract(self, text: str) -> dict:
        """Robust JSON extraction (handles markdown, hallucinations, extras)."""
        text = text.replace("```json", "").replace("```", "").strip()
        # Try to find JSON object/array
        match = re.search(r'(\{[^{}]*\}|\[[^\[]*\])', text, re.DOTALL)
        if match:
            text = match.group(0)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("[LATERAL] JSON parse failed - retrying with LLM fix")
            fix_prompt = f"Fix this malformed JSON. Return ONLY valid JSON:\n{text}"
            try:
                response = self.model.models.generate_content(model='gemini-2.0-flash', contents=fix_prompt)
                fixed = response.text.replace("```json", "").replace("```", "").strip()
                match = re.search(r'(\{[^{}]*\}|\[[^\[]*\])', fixed, re.DOTALL)
                if match:
                    fixed = match.group(0)
                return json.loads(fixed)
            except Exception as e:
                logger.error(f"[LATERAL] LLM fix failed: {e}")
                return {}
    
    def _validate_jump(self, jump: dict) -> dict:
        """Validate jump feasibility (domain, mechanism, rationale)."""
        errors = []
        if 'domain' not in jump or len(jump.get('domain', '')) < 3:
            errors.append("Invalid domain (too short or missing)")
        if 'mechanism' not in jump or len(jump.get('mechanism', '')) < 5:
            errors.append("Invalid mechanism (too short or missing)")
        if 'rationale' not in jump or len(jump.get('rationale', '')) < 10:
            errors.append("Invalid rationale (too short or missing)")
        return {'valid': not errors, 'errors': errors}
    
    def _detect_dependencies(self, mechanism: str, hypothesis: str) -> List[str]:
        """Detect dependencies if mechanism implies code."""
        deps = []
        code_indicators = ['code', 'script', 'library', 'api', 'sdk', 'module', 'package']
        if any(ind in mechanism.lower() or ind in hypothesis.lower() for ind in code_indicators):
            # Extract potential library names from mechanism
            words = re.findall(r'\b[A-Z][a-z]+\b', mechanism)
            deps.extend([w.lower() for w in words if len(w) > 3])
        return list(set(deps))
    
    def _generate_tests(self, mechanism: str, hypothesis: str, rationale: str) -> Optional[dict]:
        """Generate test file if mechanism implies code."""
        if 'code' not in mechanism.lower() and 'script' not in mechanism.lower():
            return None
        test_name = re.sub(r'[^a-zA-Z0-9]', '_', mechanism.lower())[:30]
        prompt = f"""
        [TASK]
        Generate unit tests for: {mechanism}
        Hypothesis: {hypothesis}
        Rationale: {rationale}
        
        [OUTPUT]
        Python test file with:
        - Test imports
        - Test functions
        - Edge cases
        - Error handling
        
        Return ONLY test code, no explanations.
        """
        try:
            response = self.model.models.generate_content(model='gemini-2.0-flash', contents=prompt)
            content = response.text.strip()
            # Clean markdown
            if "```" in content:
                parts = content.split("```")
                if len(parts) >= 2:
                    content = parts[1]
                    for lang in ['python', 'test']:
                        if content.lower().startswith(lang):
                            content = content[len(lang):].lstrip()
                    if "```" in content:
                        content = content.split("```")[0]
            return {'filename': f"test_{test_name}.py", 'content': content.strip()}
        except Exception as e:
            logger.warning(f"[LATERAL] Test generation failed: {e}")
            return None
    
    def analyze_failure(self, query: str, failure_reason: str) -> dict:
        """Analyze failure and propose lateral jumps."""
        prompt = f"""
        [TASK]
        The user wants to achieve: "{query}"
        The standard approach fails because: "{failure_reason}"
        
        [GOAL]
        Generate 3 "Lateral Jumps" - alternative mechanisms from OTHER fields that achieve the same GOAL but avoid the CONSTRAINT.
        
        [FORMAT]
        Return JSON ONLY:
        {{
            "core_function": "Brief description of goal",
            "constraint": "Brief description of the blocker",
            "jumps": [
                {{
                    "domain": "e.g. Optics",
                    "mechanism": "e.g. Laser Beaming",
                    "rationale": "Why this bypasses the blocker"
                }},
                ...
            ]
        }}
        """
        try:
            response = self.model.models.generate_content(model='gemini-2.0-flash', contents=prompt)
            return self._robust_json_extract(response.text)
        except Exception as e:
            logger.error(f"[LATERAL] Analysis failed: {e}")
            return {}

    def execute_pivot(self, query: str, failure_reason="Scientific Consensus / Efficiency Limits", output_path: Optional[str] = None):
        """
        Main entry point: Analyze failure → Generate jumps → Validate → Scout → Detect deps → Generate tests.
        """
        logger.info(f"[LATERAL] Analyzing failure: '{query}'")
        
        analysis = self.analyze_failure(query, failure_reason)
        if not analysis or not analysis.get('jumps'):
            logger.error("[LATERAL] Analysis failed or no jumps generated")
            return {}
        
        logger.info(f"[LATERAL] Core Function: {analysis.get('core_function')}")
        logger.info(f"[LATERAL] Constraint: {analysis.get('constraint')}")
        
        results = {}
        valid_jumps = []
        
        # Validate jumps
        for jump in analysis.get("jumps", []):
            validation = self._validate_jump(jump)
            if validation['valid']:
                valid_jumps.append(jump)
            else:
                logger.warning(f"[LATERAL] Invalid jump filtered: {validation['errors']}")
        
        if not valid_jumps:
            logger.error("[LATERAL] No valid jumps after validation")
            return {}
        
        # Execute validated jumps
        for jump in valid_jumps:
            domain = jump.get('domain', 'Unknown')
            mechanism = jump.get('mechanism', 'Unknown')
            logger.info(f"[LATERAL] Jump: [{domain}] {mechanism}")
            
            # Construct search query
            new_query = f"{mechanism} {analysis['core_function']} working prototype"
            
            # Deploy scouts
            try:
                hits = self.scout.search(new_query, max_results=3)
                results[mechanism] = {
                    'hits': hits,
                    'domain': domain,
                    'rationale': jump.get('rationale', ''),
                    'hypothesis': f"{mechanism} achieves {analysis['core_function']}"
                }
                
                # Detect dependencies if code-related
                deps = self._detect_dependencies(mechanism, results[mechanism]['hypothesis'])
                if deps:
                    results[mechanism]['dependencies'] = deps
                    logger.info(f"[LATERAL] Dependencies detected: {', '.join(deps)}")
                
                # Generate tests if code-related
                if output_path and ('code' in mechanism.lower() or 'script' in mechanism.lower()):
                    test_file = self._generate_tests(mechanism, results[mechanism]['hypothesis'], jump.get('rationale', ''))
                    if test_file:
                        test_path = os.path.join(output_path, test_file['filename'])
                        os.makedirs(output_path, exist_ok=True)
                        with open(test_path, 'w', encoding='utf-8') as f:
                            f.write(test_file['content'])
                        results[mechanism]['test_file'] = test_file['filename']
                        logger.info(f"[LATERAL] Generated test: {test_file['filename']}")
            
            except Exception as e:
                logger.error(f"[LATERAL] Scout failed for {mechanism}: {e}")
                results[mechanism] = {'hits': [], 'error': str(e)}
        
        return results

# --- SIMULATION ---
if __name__ == "__main__":
    # API Key Setup
    import os
    key = None
    if os.path.exists("config.json"):
        with open("config.json") as f:
            key = json.load(f).get("apiKeys", {}).get("geminiKey")
    if not key:
        import hephaestus_hardwired
        key = hephaestus_hardwired.GEMINI_KEY
        
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    # THE TEST
    engine = LateralEngine(model)
    
    # Scenario: User wants wireless drone power via Tesla Coil.
    # Failure: Inverse Square Law (Power drops off too fast).
    query = "Power a flying drone wirelessly using a Tesla Coil"
    reason = "Inverse Square Law: Magnetic field strength drops too rapidly for sustained flight at distance."
    
    output_dir = "lateral_test_output"
    os.makedirs(output_dir, exist_ok=True)
    results = engine.execute_pivot(query, reason, output_path=output_dir)
    
    print("\n--- LATERAL RESULTS ---")
    for mech, data in results.items():
        if isinstance(data, dict):
            print(f"\n[MECHANISM: {mech}]")
            print(f"  Domain: {data.get('domain', 'Unknown')}")
            print(f"  Rationale: {data.get('rationale', '')}")
            if 'dependencies' in data:
                print(f"  Dependencies: {', '.join(data['dependencies'])}")
            if 'test_file' in data:
                print(f"  Test file: {data['test_file']}")
            for hit in data.get('hits', []):
                print(f"  - {hit.get('title', 'No Title')} ({hit.get('link', '')})")
        else:
            # Legacy format
            print(f"\n[MECHANISM: {mech}]")
            for hit in data:
                print(f"- {hit.get('title', 'No Title')} ({hit.get('link', '')})")
