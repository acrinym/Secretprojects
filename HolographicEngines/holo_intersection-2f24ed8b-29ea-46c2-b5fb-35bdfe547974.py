"""
HOLO INTERSECTION - CROSS-DOMAIN SYNTHESIS ENGINE
=================================================
"The Bridge Builder."

Purpose:
Takes two or more disparate domains (e.g., "Bamboo" + "Magnetism") and finds
the scientific/engineering "Interface Points" that allow them to merge.

Logic:
1. Deconstructs inputs into Material Properties.
2. Searches for "Bridge Concepts" (e.g., "Cellulose" + "Magnetic" -> "Magnetic Paper").
3. Proposes a "Hybrid Mechanism".

Integration:
Uses DomainTaxonomy for domain validation and example generation.
"""

import logging
import json
import random
import google.generativeai as genai
from holo_scout import HoloScout
from onyx_domain_taxonomy import DomainTaxonomy, get_taxonomy

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [INTERSECTION] - %(message)s')
logger = logging.getLogger(__name__)


class IntersectionEngine:
    def __init__(self, model):
        self.model = model
        self.scout = HoloScout(model)
        self.taxonomy = get_taxonomy()
    
    def find_related_domains(self, domain_name: str, max_results: int = 10) -> list:
        """
        Find domains related to the given domain using the taxonomy.
        Uses domain_taxonomy.json for structured relationship lookup.
        
        Args:
            domain_name: Name of the domain to find related domains for
            max_results: Maximum number of related domains to return
            
        Returns:
            List of related domain names
        """
        return self.taxonomy.find_related(domain_name, max_results)
        
    def _get_dynamic_examples(self, count: int = 3) -> list:
        """
        Generate dynamic examples from taxonomy instead of hardcoded ones.
        Creates random domain combinations for prompt examples.
        """
        examples = []
        all_domains = list(self.taxonomy.domains.values())
        
        if len(all_domains) < 4:
            return [
                ("Speaker + Lasers + Sound + Underwater", ["Speaker", "Lasers", "Sound", "Underwater"]),
                ("Magnetism + Bamboo + Wind Energy", ["Magnetism", "Bamboo", "Wind Energy"]),
                ("Piezoelectricity + Ferrofluid", ["Piezoelectricity", "Ferrofluid"]),
            ]
        
        for _ in range(count):
            num_domains = random.randint(2, 4)
            selected = random.sample(all_domains, min(num_domains, len(all_domains)))
            domain_names = [d.name for d in selected]
            query_str = " + ".join(domain_names)
            examples.append((query_str, domain_names))
        
        return examples
    
    def _format_examples_for_prompt(self, examples: list) -> str:
        """Format examples for LLM prompts."""
        lines = []
        for query_str, domain_list in examples:
            lines.append(f'- "{query_str}" → {json.dumps(domain_list)}')
        return "\n".join(lines)
    
    def _get_bridge_example(self) -> str:
        """Generate a dynamic bridge example from taxonomy."""
        properties = self.taxonomy.get_by_type(self.taxonomy.domains.get('magnetism', None) and 
                                               self.taxonomy.domains['magnetism'].domain_type or None)
        
        if 'magnetism' in self.taxonomy.domains and 'polymers' in self.taxonomy.domains:
            return 'If A is "Porous/Plant-based" and B is "Magnetic/Ferrous", Bridge = "Capillary uptake of Ferrofluids"'
        
        return 'Example: If A has porous structures and B has magnetic properties, Bridge = combination mechanism'

    def deconstruct(self, concept: str) -> dict:
        """
        Asks LLM to break a concept into its constituent Engineering Properties.
        Enhanced with better JSON parsing and error handling.
        Uses taxonomy for validation.
        """
        taxonomy_domain = self.taxonomy.lookup(concept)
        taxonomy_hint = ""
        if taxonomy_domain:
            taxonomy_hint = f"""
        [TAXONOMY CONTEXT]
        Known domain: {taxonomy_domain.name}
        Category: {taxonomy_domain.category}
        Known properties: {taxonomy_domain.properties}
        Related domains: {taxonomy_domain.related_domains}
        """
        
        prompt = f"""
        [TASK]
        Break down the concept "{concept}" into its Fundamental Engineering Properties.
        {taxonomy_hint}
        [OUTPUT JSON]
        {{
            "materials": ["list", "of", "substances"],
            "structures": ["list", "of", "physical_forms"],
            "active_properties": ["list", "of", "behaviors", "e.g. piezoelectric, porous"]
        }}
        
        [REQUIREMENTS]
        - Return ONLY valid JSON
        - Be specific and technical
        - Include at least 2-3 items per category
        """
        try:
            response = self.model.models.generate_content(model='gemini-2.0-flash', contents=prompt)
            text = response.text
            
            import re
            json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
            if json_match:
                text = json_match.group(0)
            else:
                text = text.replace("```json", "").replace("```", "").strip()
            
            result = json.loads(text)
            
            if 'materials' not in result:
                result['materials'] = []
            if 'structures' not in result:
                result['structures'] = []
            if 'active_properties' not in result:
                result['active_properties'] = []
            
            logger.info(f"[INTERSECTION] Deconstructed '{concept}' into {len(result.get('materials', []))} materials, {len(result.get('structures', []))} structures")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"[INTERSECTION] JSON parsing failed for deconstruction: {e}")
            return {"materials": [], "structures": [], "active_properties": []}
        except Exception as e:
            logger.error(f"[INTERSECTION] Deconstruction failed: {e}")
            return {"materials": [], "structures": [], "active_properties": []}

    def find_bridges(self, domain_a: dict, domain_b: dict) -> list:
        """
        Identifies potential overlaps between two property sets.
        Uses taxonomy for bridge examples.
        """
        bridges = []
        bridge_example = self._get_bridge_example()
        
        prompt = f"""
        [TASK]
        Find "Scientific Bridges" between these two domains.
        
        DOMAIN A: {json.dumps(domain_a)}
        DOMAIN B: {json.dumps(domain_b)}
        
        [GOAL]
        Generate 3 hypothetical mechanisms that combine A and B. 
        {bridge_example}
        
        [OUTPUT JSON]
        [
            {{
                "mechanism": "Name of mechanism",
                "hypothesis": "How it works",
                "search_query": "Query to validate if this exists"
            }},
            ...
        ]
        """
        try:
            response = self.model.models.generate_content(model='gemini-2.0-flash', contents=prompt)
            text = response.text
            
            import re
            array_match = re.search(r'\[[^\]]*\]', text, re.DOTALL)
            if array_match:
                text = array_match.group(0)
            else:
                text = text.replace("```json", "").replace("```", "").strip()
            
            bridges = json.loads(text)
            
            validated_bridges = []
            for bridge in bridges:
                if isinstance(bridge, dict) and all(key in bridge for key in ['mechanism', 'hypothesis', 'search_query']):
                    validated_bridges.append(bridge)
                else:
                    logger.warning(f"[INTERSECTION] Invalid bridge format: {bridge}")
            
            if len(validated_bridges) < len(bridges):
                logger.warning(f"[INTERSECTION] Filtered {len(bridges) - len(validated_bridges)} invalid bridges")
            
            logger.info(f"[INTERSECTION] Found {len(validated_bridges)} bridges between domains")
            return validated_bridges
        except json.JSONDecodeError as e:
            logger.error(f"[INTERSECTION] JSON parsing failed for bridges: {e}")
            return []
        except Exception as e:
            logger.error(f"[INTERSECTION] Bridge finding failed: {e}")
            return []

    def solve(self, query: str, max_domains: int = 5):
        """
        Main Entry Point.
        Supports 2+ domains (multi-domain synthesis).
        Uses DomainTaxonomy for domain extraction and validation.
        
        Input: 
        - "Magnetic Bamboo" (2 domains)
        - "Bamboo + Magnetism + Wind Energy" (3 domains)
        - "Speaker + Lasers + Sound + Underwater" (4 domains)
        
        max_domains: Maximum number of domains to extract (default 5)
        """
        print(f"\n[INTERSECTION ENGINE] Spinning up for: '{query}'...")
        
        # 1. Try taxonomy-based extraction first
        taxonomy_domains = self.taxonomy.extract_domains(query, max_domains=max_domains)
        
        if len(taxonomy_domains) >= 2:
            print(f"[*] Taxonomy matched {len(taxonomy_domains)} domains: {', '.join(taxonomy_domains)}")
            domains = taxonomy_domains
        else:
            # Fall back to LLM extraction with dynamic examples
            dynamic_examples = self._get_dynamic_examples(3)
            examples_str = self._format_examples_for_prompt(dynamic_examples)
            
            split_prompt = f"""
            [TASK]
            Split '{query}' into distinct scientific/engineering domains.
            Extract ALL relevant domains from the query, even if they seem unrelated or wacky.
            
            Examples:
            {examples_str}
            
            [OUTPUT JSON]
            {{"domains": ["domain1", "domain2", "domain3", ...]}}
            
            [REQUIREMENTS]
            - Return ONLY valid JSON
            - Extract ALL distinct domains mentioned (up to {max_domains})
            - Domains can be ANY scientific/engineering field (physics, chemistry, biology, materials, etc.)
            - Don't be conservative - extract all relevant domains even if the combination seems unusual
            """
            try:
                split_resp = self.model.models.generate_content(model='gemini-2.0-flash', contents=split_prompt)
                text = split_resp.text
                
                import re
                json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
                if json_match:
                    text = json_match.group(0)
                else:
                    text = text.replace("```json", "").replace("```", "").strip()
                
                split = json.loads(text)
                domains = split.get('domains', [])
                
                if not domains or len(domains) < 2:
                    logger.error("[INTERSECTION] Failed to extract at least 2 domains")
                    return None
                
                domains = domains[:max_domains]
                
            except json.JSONDecodeError as e:
                logger.error(f"[INTERSECTION] JSON parsing failed for domain split: {e}")
                return None
            except Exception as e:
                logger.error(f"[INTERSECTION] Failed to split domains: {e}")
                return None

        print(f"[*] Deconstructing {len(domains)} domains: {', '.join(domains)}")
        
        # 2. Deconstruct all domains (with taxonomy enrichment)
        domain_props = []
        for domain in domains:
            props = self.deconstruct(domain)
            
            # Enrich with taxonomy properties if available
            taxonomy_domain = self.taxonomy.lookup(domain)
            if taxonomy_domain:
                props['taxonomy_properties'] = taxonomy_domain.properties
                props['related_domains'] = taxonomy_domain.related_domains
            
            domain_props.append((domain, props))
        
        # 3. Find Bridges (multi-way bridge finding)
        print("[*] Hunting for Interface Points...")
        if len(domains) == 2:
            bridges = self.find_bridges(domain_props[0][1], domain_props[1][1])
        else:
            bridges = self.find_multi_domain_bridges(domain_props)
        
        # 4. Score and Rank Mechanisms
        print("[*] Scoring mechanisms for feasibility...")
        scored_bridges = []
        for bridge in bridges:
            score = self._score_mechanism(bridge, domain_props)
            bridge['feasibility_score'] = score
            scored_bridges.append(bridge)
        
        scored_bridges.sort(key=lambda x: x.get('feasibility_score', 0), reverse=True)
        
        # 5. Validate Bridges with Deep Search (ONLY TOP SCORING)
        # Only validate top 10 bridges to avoid wasting time on low-scoring mechanisms
        top_bridges = scored_bridges[:10]
        validated_bridges = []
        
        for bridge in top_bridges:
            print(f"    -> Testing Hypothesis: {bridge['mechanism']} (Score: {bridge.get('feasibility_score', 0):.2f})")
            
            evidence = self._deep_validate_mechanism(bridge)
            bridge['evidence'] = evidence['papers']
            bridge['patents'] = evidence['patents']
            bridge['evidence_strength'] = evidence['strength']
            
            if evidence['papers'] or evidence['patents']:
                print(f"       [CONFIRMED] Found {len(evidence['papers'])} papers, {len(evidence['patents'])} patents (Strength: {evidence['strength']:.2f})")
            else:
                print(f"       [NOVEL] No existing research found - this might be novel.")
            
            bridge['prototype_suggestions'] = self._suggest_prototype(bridge, domain_props)
            
            validated_bridges.append(bridge)
        
        # Add remaining bridges without validation (faster)
        for bridge in scored_bridges[10:]:
            bridge['evidence'] = []
            bridge['patents'] = []
            bridge['evidence_strength'] = 0.0
            bridge['prototype_suggestions'] = self._suggest_prototype(bridge, domain_props)
            validated_bridges.append(bridge)

        return validated_bridges
    
    def find_multi_domain_bridges(self, domain_props: list) -> list:
        """
        Find bridges across 3+ domains using taxonomy for synthesis examples.
        """
        if len(domain_props) < 2:
            return []
        
        all_bridges = []
        
        # Generate bridges for each pair
        for i in range(len(domain_props)):
            for j in range(i + 1, len(domain_props)):
                domain_a_name, props_a = domain_props[i]
                domain_b_name, props_b = domain_props[j]
                
                pair_bridges = self.find_bridges(props_a, props_b)
                for bridge in pair_bridges:
                    bridge['domains'] = [domain_a_name, domain_b_name]
                all_bridges.extend(pair_bridges)
        
        # Synthesize multi-domain mechanisms
        if len(domain_props) >= 3:
            domain_names = [name for name, _ in domain_props]
            
            # Generate dynamic multi-domain examples from taxonomy
            multi_examples = self._generate_multi_domain_examples(len(domain_props))
            
            synthesis_prompt = f"""
            [TASK]
            Synthesize mechanisms that combine ALL {len(domain_props)} domains SIMULTANEOUSLY:
            Domains: {', '.join(domain_names)}
            
            Domain Properties:
            {json.dumps([(name, props) for name, props in domain_props], indent=2)}
            
            [GOAL]
            Find creative, scientifically plausible ways to combine these domains into a single unified mechanism.
            Even if the combination seems unusual or wacky, explore the possibilities.
            
            {multi_examples}
            
            [OUTPUT JSON]
            [
                {{
                    "mechanism": "Name of unified multi-domain mechanism",
                    "hypothesis": "Detailed explanation of how it works across ALL {len(domain_props)} domains simultaneously",
                    "search_query": "Query to validate if this exists in literature"
                }}
            ]
            
            [REQUIREMENTS]
            - Generate 2-3 mechanisms that truly integrate ALL domains
            - Be creative but scientifically grounded
            - Explain how each domain contributes to the unified mechanism
            """
            try:
                response = self.model.models.generate_content(model='gemini-2.0-flash', contents=synthesis_prompt)
                text = response.text
                import re
                array_match = re.search(r'\[[^\]]*\]', text, re.DOTALL)
                if array_match:
                    text = array_match.group(0)
                else:
                    text = text.replace("```json", "").replace("```", "").strip()
                
                multi_bridges = json.loads(text)
                for bridge in multi_bridges:
                    bridge['domains'] = [name for name, _ in domain_props]
                all_bridges.extend(multi_bridges)
            except:
                pass
        
        return all_bridges
    
    def _generate_multi_domain_examples(self, num_domains: int) -> str:
        """Generate multi-domain synthesis examples from taxonomy."""
        examples = []
        all_domains = list(self.taxonomy.domains.values())
        
        if len(all_domains) >= num_domains:
            for _ in range(2):
                selected = random.sample(all_domains, num_domains)
                domain_names = [d.name for d in selected]
                mechanism_desc = f"Multi-domain synthesis across {' + '.join(domain_names)}"
                examples.append(f"- {' + '.join(domain_names)} → \"{mechanism_desc}\"")
        
        if examples:
            return "Examples of multi-domain synthesis:\n" + "\n".join(examples)
        return ""
    
    def _score_mechanism(self, bridge: dict, domain_props: list) -> float:
        """
        Score mechanism by feasibility, plausibility, and complexity.
        Uses taxonomy for domain-aware scoring.
        Returns score 0.0-1.0 (higher = better).
        """
        score = 0.5
        
        hypothesis = bridge.get('hypothesis', '').lower()
        
        plausibility_keywords = ['principle', 'law', 'theory', 'mechanism', 'effect', 'phenomenon']
        if any(kw in hypothesis for kw in plausibility_keywords):
            score += 0.15
        
        feasibility_keywords = ['can be', 'possible', 'feasible', 'practical', 'implement']
        if any(kw in hypothesis for kw in feasibility_keywords):
            score += 0.1
        
        common_materials = ['metal', 'plastic', 'wood', 'ceramic', 'polymer', 'carbon', 'silicon']
        if any(mat in hypothesis for mat in common_materials):
            score += 0.1
        
        # Taxonomy-based scoring: bonus if domains have related_domains overlap
        if 'domains' in bridge:
            bridge_domains = bridge['domains']
            for domain_name in bridge_domains:
                taxonomy_domain = self.taxonomy.lookup(domain_name)
                if taxonomy_domain:
                    for other_domain in bridge_domains:
                        if other_domain != domain_name and other_domain.lower() in [r.lower() for r in taxonomy_domain.related_domains]:
                            score += 0.1
                            break
        
        if len(hypothesis) > 500:
            score -= 0.1
        elif len(hypothesis) < 100:
            score -= 0.05
        
        if 'domains' in bridge:
            domain_count = len(bridge['domains'])
            if domain_count > 2:
                score += 0.1
                if domain_count >= 4:
                    score += 0.15
                if domain_count >= 5:
                    score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _extract_key_terms(self, text: str, max_terms: int = 5) -> str:
        """
        Extract key technical terms from mechanism/hypothesis for search.
        Removes common words and focuses on technical nouns.
        """
        import re
        
        # Remove common stop words and technical fluff
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                     'of', 'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were', 'be', 'been',
                     'research', 'paper', 'study', 'patent', 'schematic', 'system', 'method',
                     'using', 'via', 'through', 'enhanced', 'integrated', 'based'}
        
        # Extract words (alphanumeric + hyphens, at least 3 chars)
        words = re.findall(r'\b[a-zA-Z0-9-]{3,}\b', text.lower())
        
        # Filter out stop words and keep only technical terms
        key_terms = [w for w in words if w not in stop_words and len(w) > 3]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_terms = []
        for term in key_terms:
            if term not in seen:
                seen.add(term)
                unique_terms.append(term)
        
        # Return top N terms
        return ' '.join(unique_terms[:max_terms])
    
    def _deep_validate_mechanism(self, bridge: dict) -> dict:
        """Deep validation with scientific papers and patents."""
        # Extract key terms instead of using full mechanism description
        mechanism_text = bridge.get('mechanism', '') + ' ' + bridge.get('hypothesis', '')
        search_query = self._extract_key_terms(mechanism_text, max_terms=5)
        
        if not search_query:
            # Fallback to mechanism name if extraction fails
            search_query = bridge.get('search_query', bridge.get('mechanism', ''))
            # Still try to simplify it
            search_query = ' '.join(search_query.split()[:5])
        
        # Simplified queries - no need to add "research paper study" or "patent" 
        # since run_patent_clerk already handles that
        papers = self.scout.run_patent_clerk(f"{search_query} research paper")
        patents = self.scout.run_patent_clerk(f"{search_query} patent")
        
        strength = 0.0
        if papers:
            strength += 0.3 * min(len(papers), 3)
        if patents:
            strength += 0.2 * min(len(patents), 2)
        
        strength = min(1.0, strength)
        
        return {
            'papers': papers[:3],
            'patents': patents[:2],
            'strength': strength
        }
    
    def _suggest_prototype(self, bridge: dict, domain_props: list) -> dict:
        """Suggest prototype approach, materials, and testing strategy."""
        domain_names = [name for name, _ in domain_props]
        
        # Use taxonomy to suggest materials
        suggested_materials = []
        for name, _ in domain_props:
            taxonomy_domain = self.taxonomy.lookup(name)
            if taxonomy_domain and taxonomy_domain.properties:
                suggested_materials.extend(taxonomy_domain.properties[:2])
        
        materials_hint = ""
        if suggested_materials:
            materials_hint = f"\n        [TAXONOMY SUGGESTED MATERIALS]: {', '.join(set(suggested_materials))}"
        
        prompt = f"""
        [TASK]
        Suggest a prototype approach for this mechanism:
        
        Mechanism: {bridge.get('mechanism', '')}
        Hypothesis: {bridge.get('hypothesis', '')}
        Domains: {domain_names}
        {materials_hint}
        
        [OUTPUT JSON]
        {{
            "approach": "Brief description of prototype approach",
            "materials": ["material1", "material2", ...],
            "testing_strategy": "How to test/validate the prototype",
            "risks": ["risk1", "risk2", ...],
            "estimated_complexity": "low|medium|high"
        }}
        """
        
        try:
            response = self.model.models.generate_content(model='gemini-2.0-flash', contents=prompt)
            text = response.text
            import re
            json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
            if json_match:
                text = json_match.group(0)
            else:
                text = text.replace("```json", "").replace("```", "").strip()
            
            return json.loads(text)
        except:
            return {
                "approach": "Standard prototype development",
                "materials": list(set(suggested_materials)) if suggested_materials else [],
                "testing_strategy": "Empirical testing",
                "risks": [],
                "estimated_complexity": "medium"
            }


# --- TEST ---
if __name__ == "__main__":
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
    
    engine = IntersectionEngine(model)
    
    # Test taxonomy integration
    print("\n=== TAXONOMY INTEGRATION TEST ===")
    print(f"Taxonomy loaded: {len(engine.taxonomy.domains)} domains")
    test_domains = engine.taxonomy.extract_domains("speaker underwater acoustics magnetism")
    print(f"Extracted domains from test query: {test_domains}")
    
    # Run synthesis
    res = engine.solve("Acoustics generating electricity from vibration using Piezoelectric materials")
    
    print("\n--- SYNTHESIS REPORT ---")
    if res:
        for r in res:
            print(f"\n[MECHANISM]: {r['mechanism']}")
            print(f"[HYPOTHESIS]: {r['hypothesis']}")
            if r.get('evidence'):
                print(f"[EVIDENCE]: {r['evidence'][0]['title']} ({r['evidence'][0]['link']})")
