"""
HOLO SCOUT - THE 9-DIMENSIONAL SEARCH SWARM
===========================================
"The eyes of the Oracle."

Purpose: Bypass algorithmic censorship by searching across 9 orthogonal vectors.
1. The Heretic (Suppressed Archives)
2. The Patent Clerk (Legal/Technical Reality)
3. The Engineer (Cross-Domain Functional Abstraction)
4. The Historian (Pre-Consensus Literature)
5. The Bio-Mimic (Nature's Patents)
6. The Alchemist (Medical/Natural Medicine)
7. The Hacker (Digital Underground/Repos)
8. The Archaeologist (Direct URL Content/GitHub)
9. The Shadow Librarian (Shadow Libraries/Documents)

Dependencies:
- duckduckgo-search (pip install duckduckgo-search)
- requests (pip install requests)
- beautifulsoup4 (pip install beautifulsoup4)
- google.generativeai (for query abstraction)
"""

import time
import json
import logging
import warnings
import os
import re
from typing import List, Dict, Optional, Any
from urllib.parse import quote_plus
import requests
from holo_rgweb import HoloRGWeb

# Ensure C:\utils is in PATH for rg and curl (Windows only)
if os.name == 'nt':  # Windows
    if 'C:\\utils' not in os.environ.get('PATH', ''):
        os.environ['PATH'] = 'C:\\utils;' + os.environ.get('PATH', '')
elif os.name == 'posix':  # Unix/Linux/Mac
    if '/usr/local/bin' not in os.environ.get('PATH', ''):
        os.environ['PATH'] = '/usr/local/bin:' + os.environ.get('PATH', '')

# Suppress the duckduckgo_search deprecation warning
warnings.filterwarnings('ignore', message='.*duckduckgo_search.*')


def _literal_rg_pattern(text: str) -> str:
    """Escape text for use as a literal ripgrep pattern (avoids regex parse errors e.g. ** or &)."""
    if not text:
        return text
    return re.escape(text)

# Try to import search tools (support both old and new package names)
DDGS = None
HAS_DDG = False
try:
    # Try new package name first (ddgs)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        from ddgs import DDGS
    HAS_DDG = True
except ImportError:
    try:
        # Fallback to old package name (duckduckgo_search)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            from duckduckgo_search import DDGS
        HAS_DDG = True
    except ImportError:
        HAS_DDG = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

import google.generativeai as genai
from holo_rate_limiter import HoloRateLimiter

# Setup Logger first
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [SCOUT] - %(message)s')
logger = logging.getLogger(__name__)

# Try to import HolographicQueryMaker (optional - only needed for holographic search)
try:
    from holo_query_maker import HolographicQueryMaker
    HAS_QUERY_MAKER = True
except ImportError:
    HAS_QUERY_MAKER = False
    HolographicQueryMaker = None
    logger.warning("[SCOUT] HolographicQueryMaker not available. Install holo_query_maker.py for holographic search.")

if not HAS_BS4:
    logger.warning("beautifulsoup4 not found. Presearch/Qwant scraping disabled. Install with: pip install beautifulsoup4")

# Ghost Scout: no-API search (scrape Google/Bing → visit URLs → RGWeb search in RAM)
try:
    from holo_ghost_scout import run_ghost_scout
    HAS_GHOST_SCOUT = True
except ImportError:
    HAS_GHOST_SCOUT = False
    run_ghost_scout = None
    logger.debug("[SCOUT] Ghost Scout not available (holo_ghost_scout)")

class HoloScout:
    def __init__(self, model, use_multiple_engines=True, cache_enabled=True, cache_ttl=3600, 
                 search_api_keys=None, rate_limiter=None):
        self.model = model
        self.ddgs = DDGS() if HAS_DDG else None
        self.use_multiple_engines = use_multiple_engines
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl  # 1 hour default
        self._search_cache = {}  # Simple in-memory cache: {query: (results, timestamp)}
        import threading
        self._cache_lock = threading.RLock()  # Thread-safe lock for cache operations
        self.rgweb = HoloRGWeb()  # All scouts use RGWeb for direct URL content search (reduces API dependency)
        
        # Rate limiter (dynamic or old method)
        self.rate_limiter = rate_limiter if rate_limiter else HoloRateLimiter(use_old_method=True)  # Default to old method for backward compatibility
        
        # Query maker (for holographic query generation) - optional
        if HAS_QUERY_MAKER and HolographicQueryMaker:
            self.query_maker = HolographicQueryMaker(model)
        else:
            self.query_maker = None
            logger.warning("[SCOUT] HolographicQueryMaker not available. search_holographic() will not work.")
        
        # Load API keys for non-censored search engines
        self.api_keys = search_api_keys or {}
        self.brave_api_key = self.api_keys.get('braveKey', '')
        self.mojeek_api_key = self.api_keys.get('mojeekKey', '')
        self.serpex_api_key = self.api_keys.get('serpexKey', '')
        self.searxng_url = self.api_keys.get('searxngUrl', '')  # e.g., "https://searx.example.com"
        
        if not HAS_DDG:
            logger.warning("Neither 'ddgs' nor 'duckduckgo-search' found. Scouts are blind. Install with: pip install ddgs")
        elif HAS_DDG:
            # Log which package we're using (check by trying to import)
            try:
                import ddgs
                logger.info("[SCOUT] Using 'ddgs' package (new)")
            except ImportError:
                logger.info("[SCOUT] Using 'duckduckgo-search' package (deprecated - consider upgrading to 'ddgs')")
        
        if not HAS_BS4 and use_multiple_engines:
            logger.warning("beautifulsoup4 not found. Multi-engine search disabled. Install with: pip install beautifulsoup4")
            self.use_multiple_engines = False

        # THE BLACKLIST (White-listed Truth Nodes)
        # Suppressed/alternative information sources for comprehensive coverage
        # FilterStack will filter quality, so we can be comprehensive
        self.truth_nodes = [
            # Suppressed Technology
            "site:rexresearch.com",
            "site:panacea-bocaf.org",
            "site:energeticforum.com",
            "site:overunity.com",
            "site:teslasociety.com",
            "site:peswiki.com",  # Alternative energy
            "site:keelynet.com",  # Alternative science
            "site:jnaudin.free.fr",  # Experimental physics (Jean-Louis Naudin)
            "site:borderlandsciences.org",  # Borderland Sciences
            "site:borderlands.com",  # Fortean and fringe science
            "site:lenr-canr.org",  # Low-Energy Nuclear Reactions archive
            # Archives
            "site:archive.org",
            "site:scholar.archive.org",  # Academic-facing Archive.org mirror
            "site:babel.hathitrust.org",  # Large-scale digital library
            "site:gallica.bnf.fr",  # National Library of France digital archive
            "site:digital.library.unt.edu",  # University of North Texas government documents
            "site:escholarship.org",  # University-hosted government publications
            "site:digitalcommons.unl.edu",  # Institutional repository with federally funded work
            "site:ecommons.cornell.edu",  # Academic mirror for government-funded research
            "site:openresearch-repository.anu.edu.au",  # Government-adjacent academic repository
            "site:deepblue.lib.umich.edu",  # University of Michigan repository
            "site:dash.harvard.edu",  # Harvard institutional repository
            "site:dspace.mit.edu",  # MIT repository hosting engineering research
            "site:repository.library.brown.edu",  # Quiet institutional archive
            "site:repositories.lib.utexas.edu",  # University of Texas repository
            "site:caltechthesis.library.caltech.edu",  # Engineering and physics theses
            "site:etda.libraries.psu.edu",  # Penn State theses and dissertations
            "site:nrc-publications.canada.ca",  # Canadian nuclear research
            "site:publications.jrc.ec.europa.eu",  # EU Joint Research Centre reports
            "site:researchbank.swinburne.edu.au",  # Australian institutional repository
            "site:open.library.ubc.ca",  # University of British Columbia repository
            "site:tessera.spacelibrary.com",  # Legacy aerospace/engineering document mirror
            # Patents
            "site:patents.google.com",
            "site:uspto.gov",  # US Patent Office (more detailed)
            "site:epo.org",  # European Patent Office
            "site:patentscope.wipo.int",  # WIPO international patents
            "site:patents.justia.com",  # Justia Patents (better search)
            # Medical/Natural Medicine
            "site:greenmedinfo.com",
            "site:earthclinic.com",
            "site:whale.to",
            "site:ncbi.nlm.nih.gov",  # PubMed/NCBI
            "site:fda.gov",  # FDA drug/device data
            "site:cdc.gov",  # CDC health data
            # Academic Papers (Unofficial Access)
            "site:scihub.org",
            "site:libgen.rs",
            # Academic Preprints (Official)
            "site:arxiv.org",  # Physics, math, CS preprints
            "site:biorxiv.org",  # Biology preprints
            "site:medrxiv.org",  # Medical preprints
            "site:chemrxiv.org",  # Chemistry preprints
            "site:psyarxiv.com",  # Psychology preprints
            "site:osf.io",  # Open Science Framework (all disciplines)
            "site:researchsquare.com",  # Research Square preprints
            # Academic Repositories
            "site:researchgate.net",
            "site:academia.edu",
            "site:scholar.google.com",  # Google Scholar
            "site:semanticscholar.org",  # Semantic Scholar (AI-powered)
            "site:ieee.org",  # IEEE Xplore
            "site:acm.org",  # ACM Digital Library
            "site:core.ac.uk",  # Open-access research papers aggregator
            "site:mdpi.com",  # Open-access scientific publisher
            "site:worldscientific.com",  # Peer-reviewed science publisher
            "site:aip.scitation.org",  # American Institute of Physics journals
            "site:aps.org",  # American Physical Society publications
            "site:iopscience.iop.org",  # Institute of Physics journals
            "site:openknowledgemaps.org",  # Visual discovery engine for scientific literature
            "site:aiaa.org",  # Aerospace engineering papers and standards
            "site:openenergyplatform.org",  # Open energy datasets and models
            "site:patentsview.org",  # Advanced patent analytics and visualization
            # Government Databases
            "site:epa.gov",  # EPA environmental data
            "site:sec.gov",  # SEC financial filings
            "site:data.gov",  # US Government Open Data
            "site:europeandataportal.eu",  # EU Open Data Portal
            "site:ftc.gov",  # FTC consumer protection
            "site:osti.gov",  # US Department of Energy technical reports
            "site:ntis.gov",  # National Technical Information Service
            "site:defense.gov",  # Department of Defense publications
            # Accountability / Justice / Political Record
            "site:courtlistener.com",  # Legal opinions and filings
            "site:oyez.org",  # Supreme Court audio/transcripts
            "site:justia.com",  # Case law and codes
            "site:govtrack.us",  # Voting records and legislation
            "site:opensecrets.org",  # Campaign finance and lobbying
            "site:votesmart.org",  # Politician bios and votes
            "site:congress.gov",  # Official legislative text
            "site:fara.gov",  # Foreign Agent Registration Act
            "site:c-span.org",  # Floor proceedings
            "site:factcheck.org",  # Political fact checking
            # Video Platforms (Alternative)
            "site:bitchute.com",
            "site:rumble.com",
            "site:odysee.com",  # Decentralized video
            "site:lbry.tv",  # LBRY (decentralized)
            # Publishing
            "site:substack.com",
            # Technical Documentation
            "site:stackoverflow.com",  # Programming Q&A
            "site:stackexchange.com",  # Stack Exchange network
            "site:developer.mozilla.org",  # MDN Web Docs
            "site:instructables.com",  # Community-driven projects and hacks
            "site:hackaday.io",  # Hardware hacking projects
            "site:allaboutcircuits.com",  # Electrical engineering reference
            "site:isa.org",  # Instrumentation and automation engineering
            "site:cerncourier.com",  # CERN particle physics publication
            "site:overunityresearch.com",  # Overunity and unconventional energy research
            "site:perma.cc",  # Preserved academic and governmental sources
            "site:forgottenlanguages-full.forgottenlanguages.org",  # Linguistic and technical texts
            "site:docs.python.org",  # Python docs
            "site:rust-lang.org",  # Rust docs
            "site:dev.to",  # Dev.to developer articles
            "site:medium.com",  # Technical articles (FilterStack will filter)
            "site:habr.com",  # Habr (Russian tech community)
            # Forums/Communities
            "site:reddit.com/r/LocalLLaMA",
            "site:discourse.org",  # Discourse forums (many tech communities)
            "site:forum.arduino.cc",  # Arduino forums
            "site:forum.raspberrypi.org",  # Raspberry Pi forums
            "site:electronics.stackexchange.com",  # Electronics Stack Exchange
            # Shadow Libraries (Document Sources)
            "site:annas-archive.org",  # Anna's Archive (meta-search shadow libraries)
            "site:z-lib.org",  # ZLibrary (books, papers, documents)
            "site:z-lib.is",  # ZLibrary alternate domain
            "site:z-lib.io",  # ZLibrary alternate domain
        ]

    def _search_presearch(self, query: str, max_results=3) -> List[Dict]:
        """
        Searches Presearch.com using web scraping.
        """
        if not HAS_BS4:
            return []
        
        results = []
        try:
            url = f"https://presearch.com/search?q={quote_plus(query)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Presearch result structure (may need adjustment based on actual HTML)
            # Look for result containers
            result_divs = soup.find_all('div', class_='result') or soup.find_all('div', class_='search-result')
            
            for div in result_divs[:max_results]:
                title_elem = div.find('h3') or div.find('a', class_='title')
                link_elem = div.find('a', href=True)
                snippet_elem = div.find('p') or div.find('span', class_='snippet')
                
                if link_elem:
                    results.append({
                        "title": title_elem.get_text(strip=True) if title_elem else "No Title",
                        "link": link_elem.get('href', ''),
                        "snippet": snippet_elem.get_text(strip=True) if snippet_elem else ""
                    })
            
            # Rate limiting (dynamic or old method)
            start_time = time.time()
            self.rate_limiter.wait("presearch.com")
            response_time = time.time() - start_time
            self.rate_limiter.record_success("presearch.com", response_time)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                self.rate_limiter.record_failure("presearch.com", "429", retry_after=e.response.headers.get('Retry-After'))
            elif e.response.status_code == 403:
                self.rate_limiter.record_failure("presearch.com", "403")
            logger.error(f"Presearch search failed for '{query}': {e}")
        except Exception as e:
            logger.error(f"Presearch search failed for '{query}': {e}")
            self.rate_limiter.record_failure("presearch.com", "unknown")
        
        return results
    
    def _search_qwant(self, query: str, max_results=3) -> List[Dict]:
        """
        Searches Qwant.com using their API or web scraping.
        """
        if not HAS_BS4:
            return []
        
        results = []
        try:
            # Qwant API endpoint (preferred method)
            api_url = "https://api.qwant.com/v3/search/web"
            params = {
                'q': query,
                'count': max_results,
                'locale': 'en_US',
                'offset': 0
            }
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(api_url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'result' in data['data'] and 'items' in data['data']['result']:
                    for item in data['data']['result']['items'][:max_results]:
                        results.append({
                            "title": item.get('title', 'No Title'),
                            "link": item.get('url', ''),
                            "snippet": item.get('description', '')
                        })
                else:
                    # Fallback to web scraping if API structure differs
                    logger.warning("Qwant API structure unexpected, falling back to web scraping")
                    return self._search_qwant_web(query, max_results)
            else:
                # Fallback to web scraping
                return self._search_qwant_web(query, max_results)
            
            # Rate limiting (dynamic or old method)
            start_time = time.time()
            self.rate_limiter.wait("qwant.com")
            response_time = time.time() - start_time
            self.rate_limiter.record_success("qwant.com", response_time)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                self.rate_limiter.record_failure("qwant.com", "429", retry_after=e.response.headers.get('Retry-After'))
            elif e.response.status_code == 403:
                self.rate_limiter.record_failure("qwant.com", "403")
            logger.error(f"Qwant search failed for '{query}': {e}")
        except Exception as e:
            logger.error(f"Qwant search failed for '{query}': {e}")
            self.rate_limiter.record_failure("qwant.com", "unknown")
            # Try web scraping fallback
            try:
                return self._search_qwant_web(query, max_results)
            except:
                return []
        
        return results
    
    def _search_qwant_web(self, query: str, max_results=3) -> List[Dict]:
        """
        Fallback: Searches Qwant.com using web scraping.
        """
        results = []
        try:
            url = f"https://www.qwant.com/?q={quote_plus(query)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Qwant result structure (may need adjustment based on actual HTML)
            result_divs = soup.find_all('div', class_='result') or soup.find_all('article', class_='webResult')
            
            for div in result_divs[:max_results]:
                title_elem = div.find('h3') or div.find('a', class_='title')
                link_elem = div.find('a', href=True)
                snippet_elem = div.find('p') or div.find('span', class_='abstract')
                
                if link_elem:
                    results.append({
                        "title": title_elem.get_text(strip=True) if title_elem else "No Title",
                        "link": link_elem.get('href', ''),
                        "snippet": snippet_elem.get_text(strip=True) if snippet_elem else ""
                    })
            
            # Rate limiting (dynamic or old method)
            start_time = time.time()
            self.rate_limiter.wait("qwant.com")
            response_time = time.time() - start_time
            self.rate_limiter.record_success("qwant.com", response_time)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                self.rate_limiter.record_failure("qwant.com", "429", retry_after=e.response.headers.get('Retry-After'))
            elif e.response.status_code == 403:
                self.rate_limiter.record_failure("qwant.com", "403")
            logger.error(f"Qwant web scraping failed for '{query}': {e}")
        except Exception as e:
            logger.error(f"Qwant web scraping failed for '{query}': {e}")
            self.rate_limiter.record_failure("qwant.com", "unknown")
        
        return results
    
    def _search_brave_api(self, query: str, max_results=3) -> List[Dict]:
        """
        Searches using Brave Search API (non-censored, handles long queries well).
        API: https://api.search.brave.com/res/v1/web/search
        """
        results = []
        try:
            url = "https://api.search.brave.com/res/v1/web/search"
            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": self.brave_api_key
            }
            params = {
                "q": query,
                "count": max_results,
                "safesearch": "off",  # Non-censored
                "freshness": "py"  # Past year
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if 'web' in data and 'results' in data['web']:
                for item in data['web']['results'][:max_results]:
                    results.append({
                        "title": item.get('title', 'No Title'),
                        "link": item.get('url', ''),
                        "snippet": item.get('description', '')
                    })
            
            # Rate limiting (dynamic or old method)
            start_time = time.time()
            self.rate_limiter.wait("api.search.brave.com")
            response_time = time.time() - start_time
            self.rate_limiter.record_success("api.search.brave.com", response_time)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                self.rate_limiter.record_failure("api.search.brave.com", "429", retry_after=e.response.headers.get('Retry-After'))
            elif e.response.status_code == 403:
                self.rate_limiter.record_failure("api.search.brave.com", "403")
            logger.error(f"Brave Search API failed: {e}")
        except Exception as e:
            logger.error(f"Brave Search API failed: {e}")
            self.rate_limiter.record_failure("api.search.brave.com", "unknown")
        
        return results
    
    def _search_mojeek_api(self, query: str, max_results=3) -> List[Dict]:
        """
        Searches using Mojeek API (privacy-focused, non-censored).
        API: https://www.mojeek.com/search
        """
        results = []
        try:
            url = "https://api.mojeek.com/search"
            params = {
                "api_key": self.mojeek_api_key,
                "q": query,
                "fmt": "json",
                "s": max_results
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if 'response' in data and 'results' in data['response']:
                for item in data['response']['results'][:max_results]:
                    results.append({
                        "title": item.get('title', 'No Title'),
                        "link": item.get('url', ''),
                        "snippet": item.get('desc', '')
                    })
            
            # Rate limiting (dynamic or old method)
            start_time = time.time()
            self.rate_limiter.wait("api.mojeek.com")
            response_time = time.time() - start_time
            self.rate_limiter.record_success("api.mojeek.com", response_time)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                self.rate_limiter.record_failure("api.mojeek.com", "429", retry_after=e.response.headers.get('Retry-After'))
            elif e.response.status_code == 403:
                self.rate_limiter.record_failure("api.mojeek.com", "403")
            logger.error(f"Mojeek API failed: {e}")
        except Exception as e:
            logger.error(f"Mojeek API failed: {e}")
            self.rate_limiter.record_failure("api.mojeek.com", "unknown")
        
        return results
    
    def _search_searxng(self, query: str, max_results=3) -> List[Dict]:
        """
        Searches using SearxNG instance (self-hosted, non-censored, handles long queries).
        API: {searxng_url}/search?q=...
        """
        results = []
        try:
            url = f"{self.searxng_url.rstrip('/')}/search"
            params = {
                "q": query,
                "format": "json",
                "engines": "google,bing,duckduckgo,qwant,startpage"  # Multiple engines
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            if 'results' in data:
                for item in data['results'][:max_results]:
                    results.append({
                        "title": item.get('title', 'No Title'),
                        "link": item.get('url', ''),
                        "snippet": item.get('content', '')
                    })
            
            # Rate limiting (dynamic or old method)
            domain = self.searxng_url.replace("https://", "").replace("http://", "").split("/")[0] if self.searxng_url else "searxng"
            self.rate_limiter.wait(domain)
        except requests.exceptions.HTTPError as e:
            domain = self.searxng_url.replace("https://", "").replace("http://", "").split("/")[0] if self.searxng_url else "searxng"
            if e.response.status_code == 429:
                retry_after = e.response.headers.get('Retry-After')
                retry_after_int = int(retry_after) if retry_after and retry_after.isdigit() else None
                self.rate_limiter.record_failure(domain, "429", retry_after=retry_after_int)
            elif e.response.status_code == 403:
                self.rate_limiter.record_failure(domain, "403")
            logger.error(f"SearxNG search failed for '{query}': {e}")
        except Exception as e:
            domain = self.searxng_url.replace("https://", "").replace("http://", "").split("/")[0] if self.searxng_url else "searxng"
            logger.error(f"SearxNG search failed for '{query}': {e}")
            self.rate_limiter.record_failure(domain, "unknown")
        
        return results
    
    def _search_serpex_api(self, query: str, max_results=3) -> List[Dict]:
        """
        Searches using Serpex API (multi-engine aggregator, handles long queries).
        API: https://api.serpex.dev/v1/search
        """
        results = []
        try:
            url = "https://api.serpex.dev/v1/search"
            headers = {
                "X-API-KEY": self.serpex_api_key,
                "Content-Type": "application/json"
            }
            params = {
                "q": query,
                "num": max_results,
                "engine": "google"  # Can also use: bing, brave, duckduckgo
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if 'organic_results' in data:
                for item in data['organic_results'][:max_results]:
                    results.append({
                        "title": item.get('title', 'No Title'),
                        "link": item.get('link', ''),
                        "snippet": item.get('snippet', '')
                    })
            
            # Rate limiting (dynamic or old method)
            self.rate_limiter.wait("api.serpex.com")
        except Exception as e:
            logger.error(f"Serpex API failed: {e}")
            self.rate_limiter.record_failure("api.serpex.com", "unknown")
        
        return results
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """
        Removes duplicate results based on URL.
        """
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get('link', '').lower().strip()
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results
    
    def _get_cached_result(self, query: str) -> List[Dict]:
        """Check cache for search results (thread-safe)."""
        if not self.cache_enabled:
            return None
        
        cache_key = query.lower().strip()
        with self._cache_lock:
            if cache_key in self._search_cache:
                results, timestamp = self._search_cache[cache_key]
                # Check if cache is still valid
                if time.time() - timestamp < self.cache_ttl:
                    logger.info(f"[SCOUT] Cache hit for: {query[:50]}...")
                    return results
                else:
                    # Cache expired, remove it
                    del self._search_cache[cache_key]
        
        return None
    
    def _cache_result(self, query: str, results: List[Dict]):
        """Cache search results (thread-safe)."""
        if self.cache_enabled:
            cache_key = query.lower().strip()
            with self._cache_lock:
                self._search_cache[cache_key] = (results, time.time())
                # Limit cache size (keep last 100 queries)
                if len(self._search_cache) > 100:
                    # Remove oldest entry
                    oldest_key = min(self._search_cache.keys(), 
                                    key=lambda k: self._search_cache[k][1])
                    del self._search_cache[oldest_key]
    
    def _rank_results(self, results: List[Dict], query: str) -> List[Dict]:
        """Rank results by relevance (simple keyword matching)."""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        scored_results = []
        for result in results:
            score = 0.0
            title = result.get('title', '').lower()
            snippet = result.get('snippet', '').lower()
            
            # Title matches are worth more
            for word in query_words:
                if word in title:
                    score += 2.0
                if word in snippet:
                    score += 1.0
            
            # Boost certain sources (non-censored engines get higher priority)
            source = result.get('source', '')
            if source == 'duckduckgo':
                score += 0.5
            elif source in ['brave', 'mojeek', 'searxng']:  # Non-censored engines
                score += 0.6
            elif source == 'serpex':  # Multi-engine aggregator
                score += 0.4
            elif source in ['qwant']:
                score += 0.3
            
            scored_results.append((score, result))
        
        # Sort by score (descending)
        scored_results.sort(key=lambda x: x[0], reverse=True)
        return [result for score, result in scored_results]
    
    def search_holographic(self, user_intent: str, max_results=10, use_rgweb=True, max_queries=20) -> List[Dict]:
        """
        Search using holographic query generation - generates queries from multiple dimensions
        and searches them using RGWeb (curl + ripgrep) for direct URL searches.
        
        Args:
            user_intent: User's original query/intent
            max_results: Maximum number of results to return
            use_rgweb: If True, use RGWeb for URL searches (default: True)
            max_queries: Maximum number of holographic queries to generate (default: 20)
        
        Returns:
            List of search results from holographic queries
        """
        if not self.query_maker:
            logger.error("[SCOUT] HolographicQueryMaker not available. Falling back to standard search.")
            return self.search(user_intent, max_results=max_results)
        
        logger.info(f"[SCOUT] Holographic search for: '{user_intent}'")
        
        # Generate holographic queries
        queries = self.query_maker.generate_queries(user_intent, max_queries=max_queries)
        
        if not queries:
            logger.warning("[SCOUT] No queries generated, falling back to direct search")
            return self.search(user_intent, max_results=max_results)
        
        logger.info(f"[SCOUT] Generated {len(queries)} holographic queries from {len(set(q['dimension'] for q in queries))} dimensions")
        
        all_results = []
        
        if use_rgweb:
            # Use RGWeb to search URLs directly
            # Extract domains from truth_nodes for RGWeb searches
            domains = []
            for node in self.truth_nodes[:20]:  # Limit to first 20 domains
                if node.startswith("site:"):
                    domain = node.replace("site:", "").split("/")[0]
                    domains.append(domain)
            
            # Generate URL queries for RGWeb
            url_queries = self.query_maker.generate_url_queries(user_intent, domains, max_per_domain=2)
            
            # Search each URL query with RGWeb
            for url_query in url_queries:
                try:
                    # Extract pattern from query (remove "site:domain.com" prefix)
                    pattern = url_query['query'].replace(f"site:{url_query['domain']}", "").strip()
                    if not pattern:
                        continue
                    
                    # Search URL with RGWeb
                    url = f"https://{url_query['domain']}"
                    results = self.rgweb.search_url(pattern, url)
                    
                    # Convert RGWeb results to scout format
                    for r in results:
                        all_results.append({
                            "title": f"Match in {url_query['domain']}",
                            "link": url,
                            "snippet": r.get('match', ''),
                            "source": "rgweb",
                            "dimension": url_query['dimension'],
                            "domain": url_query['domain']
                        })
                except Exception as e:
                    logger.warning(f"[SCOUT] RGWeb search failed for {url_query['domain']}: {e}")
        else:
            # Use standard search for each holographic query
            for query_dict in queries:
                try:
                    query_text = query_dict['query']
                    results = self.search(query_text, max_results=3, use_cache=True)
                    
                    # Tag results with dimension info
                    for r in results:
                        r['dimension'] = query_dict['dimension']
                        r['domain'] = query_dict['domain']
                        r['rationale'] = query_dict['rationale']
                    
                    all_results.extend(results)
                except Exception as e:
                    logger.warning(f"[SCOUT] Search failed for query '{query_dict['query']}': {e}")
        
        # Deduplicate and rank results
        unique_results = self._deduplicate_results(all_results)
        ranked_results = self._rank_results(unique_results, user_intent)
        
        return ranked_results[:max_results]
    
    def search(self, query: str, max_results=3, use_cache=True) -> List[Dict]:
        """
        Executes a multi-engine search across DuckDuckGo, Qwant, Brave, Mojeek, SearxNG, and Serpex.
        Aggregates, ranks, and deduplicates results. Uses APIs for long queries when available.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            use_cache: Whether to use cached results
        
        Returns:
            List of search result dictionaries
        """
        # Check cache first
        if use_cache:
            cached = self._get_cached_result(query)
            if cached:
                return cached[:max_results]
        
        all_results = []
        
        # 1. DuckDuckGo (primary)
        if self.ddgs:
            try:
                ddg_gen = self.ddgs.text(query, max_results=max_results)
                # Generators always evaluate as truthy, so iterate directly
                # This will consume the generator and collect results
                count = 0
                for r in ddg_gen:
                    if r:  # Ensure result is not None/empty
                        all_results.append({
                            "title": r.get('title', 'No Title') if isinstance(r, dict) else 'No Title',
                            "link": r.get('href', r.get('link', '')) if isinstance(r, dict) else '',
                            "snippet": r.get('body', r.get('snippet', '')) if isinstance(r, dict) else '',
                            "source": "duckduckgo"
                        })
                        count += 1
                if count == 0:
                    logger.warning(f"DuckDuckGo returned 0 results for '{query}' - library may need updating or query too specific")
                # Rate limiting (dynamic or old method)
                self.rate_limiter.wait("duckduckgo.com")
            except StopIteration:
                logger.debug(f"DuckDuckGo generator empty for '{query}'")
            except Exception as e:
                logger.error(f"DuckDuckGo search failed for '{query}': {e}")
        
        # 2. Presearch (DISABLED - 100% failure rate with 403 Forbidden)
        # Presearch is blocking automated requests, so we skip it entirely
        # if self.use_multiple_engines:
        #     try:
        #         presearch_results = self._search_presearch(query, max_results=max_results)
        #         for r in presearch_results:
        #             r["source"] = "presearch"
        #             all_results.append(r)
        #     except Exception as e:
        #         logger.warning(f"Presearch search failed: {e}")
        
        # 3. Qwant (if enabled)
        if self.use_multiple_engines:
            try:
                qwant_results = self._search_qwant(query, max_results=max_results)
                for r in qwant_results:
                    r["source"] = "qwant"
                    all_results.append(r)
            except Exception as e:
                logger.warning(f"Qwant search failed: {e}")
        
        # 4. Brave Search API (non-censored, handles long queries)
        if self.brave_api_key:
            try:
                brave_results = self._search_brave_api(query, max_results=max_results)
                for r in brave_results:
                    r["source"] = "brave"
                    all_results.append(r)
            except Exception as e:
                logger.warning(f"Brave Search API failed: {e}")
        
        # 5. Mojeek API (privacy-focused, non-censored)
        if self.mojeek_api_key:
            try:
                mojeek_results = self._search_mojeek_api(query, max_results=max_results)
                for r in mojeek_results:
                    r["source"] = "mojeek"
                    all_results.append(r)
            except Exception as e:
                logger.warning(f"Mojeek API failed: {e}")
        
        # 6. SearxNG (self-hosted, non-censored, handles long queries)
        if self.searxng_url:
            try:
                searxng_results = self._search_searxng(query, max_results=max_results)
                for r in searxng_results:
                    r["source"] = "searxng"
                    all_results.append(r)
            except Exception as e:
                logger.warning(f"SearxNG search failed: {e}")
        
        # 7. Serpex API (multi-engine aggregator, handles long queries)
        if self.serpex_api_key:
            try:
                serpex_results = self._search_serpex_api(query, max_results=max_results)
                for r in serpex_results:
                    r["source"] = "serpex"
                    all_results.append(r)
            except Exception as e:
                logger.warning(f"Serpex API failed: {e}")
        
        # Deduplicate, rank, and return top results
        unique_results = self._deduplicate_results(all_results)
        ranked_results = self._rank_results(unique_results, query)
        
        final_results = ranked_results[:max_results]
        
        # Cache results
        if use_cache:
            self._cache_result(query, final_results)
        
        return final_results

    def _robust_extract(self, text: str, expected_type: str = 'string') -> Any:
        """Robust extraction (handles JSON/array, cleans fences/lang, retries on fail)."""
        text = text.replace("```json", "").replace("```", "").strip()
        if expected_type == 'json':
            match = re.search(r'(\{[^{}]*\}|\[[^\[]*\])', text, re.DOTALL)
            if match:
                text = match.group(0)
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                logger.warning("[SCOUT] JSON parse failed - retrying with LLM fix")
                fix_prompt = f"Fix this malformed JSON. Return ONLY valid JSON:\n{text}"
                try:
                    response = self.model.models.generate_content(model='gemini-2.0-flash', contents=fix_prompt)
                    fixed = response.text.replace("```json", "").replace("```", "").strip()
                    match = re.search(r'(\{[^{}]*\}|\[[^\[]*\])', fixed, re.DOTALL)
                    if match:
                        fixed = match.group(0)
                    return json.loads(fixed)
                except Exception as e:
                    logger.error(f"[SCOUT] LLM fix failed: {e}")
                    return {}
        return text.strip()
    
    def _validate_results(self, dossier: dict, query: str) -> dict:
        """Validate scout results (dedup, score relevance, flag low-quality)."""
        errors = []
        validated_dossier = {}
        
        for scout, results in dossier.items():
            if not results:
                errors.append(f"{scout}: No results")
                validated_dossier[scout] = []
                continue
            
            # Dedup by link
            unique = {r.get('link', ''): r for r in results if r.get('link')}.values()
            validated_dossier[scout] = list(unique)
            
            if len(validated_dossier[scout]) == 0:
                errors.append(f"{scout}: All results invalid (no links)")
        
        return {'valid': not errors, 'errors': errors, 'dossier': validated_dossier}
    
    def _fetch_github_content(self, url: str) -> Optional[str]:
        """Fetch raw content from GitHub URL."""
        try:
            # Convert GitHub URL to raw content URL
            if 'github.com' in url and '/blob/' in url:
                raw_url = url.replace('/blob/', '/raw/')
            elif 'github.com' in url:
                raw_url = url.replace('github.com', 'raw.githubusercontent.com').replace('/tree/', '/')
            else:
                return None
            
            response = requests.get(raw_url, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.warning(f"[SCOUT] Failed to fetch GitHub content: {e}")
            return None
    
    def _detect_dependencies(self, content: str) -> List[str]:
        """Detect dependencies in code content."""
        deps = []
        # Python imports
        import_pattern = r'^(?:from\s+(\S+)\s+)?import\s+(\S+)'
        for match in re.finditer(import_pattern, content, re.MULTILINE):
            if match.group(1):
                deps.append(match.group(1).split('.')[0])
            elif match.group(2):
                deps.append(match.group(2).split('.')[0])
        # JavaScript/TypeScript
        require_pattern = r"require\(['\"]([^'\"]+)['\"]\)"
        for match in re.finditer(require_pattern, content):
            dep = match.group(1)
            if not dep.startswith('.'):
                deps.append(dep.split('/')[0])
        return list(set(deps))
    
    def _generate_tests(self, filename: str, content: str, source: str, snippet: str) -> Optional[dict]:
        """Generate test file for code found by scouts."""
        if not any(ext in filename.lower() for ext in ['.py', '.js', '.ts']):
            return None
        test_name = os.path.basename(filename).replace('.py', '_test.py').replace('.js', '_test.js')
        prompt = f"""
        [TASK]
        Generate unit tests for code found by scout:
        Source: {source}
        Snippet: {snippet}
        
        Code:
        ```python
        {content[:2000]}
        ```
        
        [OUTPUT]
        Return ONLY test code, no explanations.
        """
        try:
            response = self.model.models.generate_content(model='gemini-2.0-flash', contents=prompt)
            test_content = response.text.strip()
            # Clean markdown
            if "```" in test_content:
                parts = test_content.split("```")
                if len(parts) >= 2:
                    test_content = parts[1]
                    for lang in ['python', 'test']:
                        if test_content.lower().startswith(lang):
                            test_content = test_content[len(lang):].lstrip()
                    if "```" in test_content:
                        test_content = test_content.split("```")[0]
            return {'filename': test_name, 'content': test_content.strip()}
        except Exception as e:
            logger.warning(f"[SCOUT] Test generation failed: {e}")
            return None
    
    def abstract_concept(self, query: str, archetype: str) -> str:
        """
        Uses the LLM to translate a "Forbidden" query into a "Functional" one.
        Improved error handling and validation.
        """
        prompt = f"""
        [TASK]
        Translate the suppressed technology query: "{query}" into a search query for the "{archetype}" archetype.
        
        [ARCHETYPES]
        - ENGINEER: Translate specific suppressed tech (e.g., "Anti-Gravity") into standard physics functional terms (e.g., "High voltage dielectric propulsion", "Lorentz force actuator").
        - BIOMIMIC: Translate the function into biological equivalents (e.g., "How does a maple seed float?").
        - HISTORIAN: Translate into archaic terms used pre-1950 (e.g., "Aetheric vortex", "Dielectric strain").
        - ALCHEMIST: Translate into natural medicine/chemistry terms.
        - HACKER: Translate into technical implementation terms.
        
        [OUTPUT]
        Return ONLY the search query string. No quotes. No explanation.
        """
        try:
            if not self.model:
                logger.error("[SCOUT] Model not available for abstraction")
                return query
            response = self.model.models.generate_content(model='gemini-2.0-flash', contents=prompt)
            abstracted = self._robust_extract(response.text, 'string')
            
            # Validate: if result is too similar to input or empty, retry with simpler query
            if not abstracted or abstracted.lower() == query.lower() or len(abstracted) < 5:
                logger.warning(f"[SCOUT] Abstraction too similar, retrying with simplified query")
                # Retry with simplified prompt
                simple_prompt = f"Translate '{query}' into a technical search query for {archetype}. Return ONLY the query, no explanation."
                try:
                    retry_response = self.model.models.generate_content(model='gemini-2.0-flash', contents=simple_prompt)
                    abstracted = self._robust_extract(retry_response.text, 'string')
                    if not abstracted or len(abstracted) < 5:
                        return query
                except:
                    return query
            
            return abstracted
        except Exception as e:
            logger.error(f"[SCOUT] Abstraction failed: {e}, using original query")
            return query

    # --- THE 5 SCOUTS ---

    def run_heretic(self, query: str) -> List[Dict]:
        """
        Scout 1: The Heretic. Searches suppressed archives.
        Uses RGWeb to directly fetch and search archive.org and suppressed sites.
        """
        logger.info(f"Scout [HERETIC] deployed for: {query}")
        results = []
        
        # Search specific nodes (API discovery)
        for node in self.truth_nodes:
            # We only pick a few nodes to avoid spamming, or construct a joined OR query
            if "rexresearch" in node or "panacea" in node or "annas-archive" in node or "z-lib" in node:
                q = f"{query} {node}"
                api_results = self.search(q, max_results=2)
                results.extend(api_results)
                
                # Use RGWeb to directly fetch and search content from discovered URLs
                if self.rgweb and api_results:
                    for result in api_results[:1]:  # Limit to top result per node
                        url = result.get('link', '')
                        if url and any(domain in url for domain in ['archive.org', 'rexresearch.com', 'panacea-bocaf.org', 'annas-archive.org', 'z-lib.org', 'z-lib.is', 'z-lib.io']):
                            try:
                                # Extract key terms from query for RGWeb search (escape for literal rg pattern)
                                key_terms = ' '.join(query.split()[:5])  # First 5 words
                                rgweb_matches = self.rgweb.search_url(_literal_rg_pattern(key_terms), url, case_sensitive=False)
                                # Convert RGWeb results to scout format
                                for match in rgweb_matches[:2]:  # Top 2 matches per URL
                                    results.append({
                                        "title": f"{result.get('title', 'Archive')} (Line {match.get('line', '?')})",
                                        "link": url,
                                        "snippet": match.get('match', ''),
                                        "source": "heretic-rgweb"
                                    })
                            except Exception as e:
                                logger.debug(f"RGWeb search failed for {url}: {e}")
                
        return results

    def run_patent_clerk(self, query: str) -> List[Dict]:
        """
        Scout 2: The Patent Clerk. Searches for IP.
        Uses RGWeb to directly fetch and search patent pages for detailed content.
        """
        logger.info(f"Scout [PATENT CLERK] deployed for: {query}")
        
        # Remove "How to build" fluff
        core_tech = query.replace("How to build", "").replace("How to make", "").strip()
        
        # First try API search for discovery
        # Search multiple patent databases
        patent_queries = [
            f"site:patents.google.com {core_tech} schematic",
            f"site:uspto.gov {core_tech}",  # US Patent Office (more detailed)
            f"site:patentscope.wipo.int {core_tech}",  # WIPO international patents
        ]
        
        api_results = []
        for q in patent_queries[:2]:  # Limit to top 2 to avoid rate limits
            try:
                api_results.extend(self.search(q, max_results=2))
            except Exception as e:
                logger.debug(f"Patent search failed: {e}")
        
        # Use RGWeb to directly fetch and search patent content
        rgweb_results = []
        if self.rgweb and api_results:
            for result in api_results[:2]:  # Limit to top 2 for RGWeb deep search
                url = result.get('link', '')
                if url and any(domain in url for domain in ['patents.google.com', 'uspto.gov', 'patentscope.wipo.int']):
                    try:
                        # Extract key technical terms from query
                        key_terms = ' '.join(core_tech.split()[:5])
                        rgweb_matches = self.rgweb.search_url(_literal_rg_pattern(key_terms), url, case_sensitive=False)
                        for match in rgweb_matches[:2]:  # Top 2 matches per patent
                            rgweb_results.append({
                                "title": f"{result.get('title', 'Patent')} (Line {match.get('line', '?')})",
                                "link": url,
                                "snippet": match.get('match', ''),
                                "source": "patent_clerk-rgweb"
                            })
                    except Exception as e:
                        logger.debug(f"RGWeb search failed for {url}: {e}")
        
        # Combine results
        return api_results + rgweb_results

    def run_engineer(self, query: str) -> List[Dict]:
        """
        Scout 3: The Engineer. Searches adjacent industries.
        Uses RGWeb to directly search arXiv, ResearchGate, and technical documentation.
        """
        # 1. Abstract the query
        abstract_query = self.abstract_concept(query, "ENGINEER")
        logger.info(f"Scout [ENGINEER] abstracted '{query}' -> '{abstract_query}'")
        
        # API search for discovery
        api_results = self.search(abstract_query, max_results=3)
        
        # Also search academic sources directly
        academic_results = []
        academic_sources = [
            "site:arxiv.org",
            "site:researchgate.net",
            "site:scholar.google.com",
            "site:ieee.org",  # IEEE Xplore
            "site:acm.org",  # ACM Digital Library
        ]
        
        for source in academic_sources[:2]:  # Limit to top 2 to avoid rate limits
            try:
                academic_query = f"{abstract_query} {source}"
                academic_results.extend(self.search(academic_query, max_results=2))
            except Exception as e:
                logger.debug(f"Academic search failed for {source}: {e}")
        
        # Use RGWeb to directly fetch and search arXiv papers
        rgweb_results = []
        if self.rgweb and academic_results:
            for result in academic_results[:2]:  # Limit to top 2
                url = result.get('link', '')
                if url and ('arxiv.org' in url or 'researchgate.net' in url):
                    try:
                        key_terms = ' '.join(abstract_query.split()[:5])
                        rgweb_matches = self.rgweb.search_url(_literal_rg_pattern(key_terms), url, case_sensitive=False)
                        for match in rgweb_matches[:2]:
                            rgweb_results.append({
                                "title": f"{result.get('title', 'Paper')} (Line {match.get('line', '?')})",
                                "link": url,
                                "snippet": match.get('match', ''),
                                "source": "engineer-rgweb"
                            })
                    except Exception as e:
                        logger.debug(f"RGWeb search failed for {url}: {e}")
        
        # Combine all results
        all_results = api_results + academic_results + rgweb_results
        logger.info(f"[SCOUT SWARM] Engineer found {len(all_results)} results ({len(api_results)} API, {len(academic_results)} academic, {len(rgweb_results)} RGWeb)")
        return all_results[:3]

    def run_historian(self, query: str) -> List[Dict]:
        """
        Scout 4: The Historian. Searches archaic texts.
        Uses RGWeb to directly fetch and search Archive.org, arXiv, and historical sources.
        """
        # 1. Abstract
        archaic_query = self.abstract_concept(query, "HISTORIAN")
        logger.info(f"Scout [HISTORIAN] translated to -> '{archaic_query}'")
        
        # First try API search for discovery
        q = f"site:archive.org {archaic_query} filetype:pdf"
        api_results = self.search(q, max_results=2)
        
        # Also search historical academic sources
        historical_sources = [
            f"site:arxiv.org {archaic_query}",
            f"site:biorxiv.org {archaic_query}",  # Historical biology papers
            f"site:osf.io {archaic_query}",  # Open Science Framework
        ]
        
        historical_results = []
        for source_query in historical_sources[:2]:
            try:
                historical_results.extend(self.search(source_query, max_results=1))
            except Exception as e:
                logger.debug(f"Historical source search failed: {e}")
        
        # Use RGWeb to directly search Archive.org snapshots and academic papers
        rgweb_results = []
        if self.rgweb:
            # Archive.org
            for result in api_results[:1]:
                url = result.get('link', '')
                if url and 'archive.org' in url:
                    try:
                        key_terms = ' '.join(archaic_query.split()[:5])
                        rgweb_matches = self.rgweb.search_url(_literal_rg_pattern(key_terms), url, case_sensitive=False)
                        for match in rgweb_matches[:2]:
                            rgweb_results.append({
                                "title": f"{result.get('title', 'Archive')} (Line {match.get('line', '?')})",
                                "link": url,
                                "snippet": match.get('match', ''),
                                "source": "historian-rgweb"
                            })
                    except Exception as e:
                        logger.debug(f"RGWeb search failed for {url}: {e}")
            
            # Academic papers
            for result in historical_results[:1]:
                url = result.get('link', '')
                if url and ('arxiv.org' in url or 'biorxiv.org' in url):
                    try:
                        key_terms = ' '.join(archaic_query.split()[:5])
                        rgweb_matches = self.rgweb.search_url(_literal_rg_pattern(key_terms), url, case_sensitive=False)
                        for match in rgweb_matches[:1]:
                            rgweb_results.append({
                                "title": f"{result.get('title', 'Paper')} (Line {match.get('line', '?')})",
                                "link": url,
                                "snippet": match.get('match', ''),
                                "source": "historian-academic-rgweb"
                            })
                    except Exception as e:
                        logger.debug(f"RGWeb search failed for {url}: {e}")
        
        return api_results + historical_results + rgweb_results

    def run_biomimic(self, query: str) -> List[Dict]:
        """
        Scout 5: The Bio-Mimic. Searches nature.
        Uses RGWeb to directly search bioRxiv, PubMed, and biological databases.
        """
        bio_query = self.abstract_concept(query, "BIOMIMIC")
        logger.info(f"Scout [BIOMIMIC] asking nature -> '{bio_query}'")
        
        # API search for discovery
        api_results = self.search(bio_query, max_results=2)
        
        # Search biological/medical academic sources
        bio_sources = [
            f"site:biorxiv.org {bio_query}",
            f"site:medrxiv.org {bio_query}",
            f"site:pubmed.ncbi.nlm.nih.gov {bio_query}",
            f"site:researchgate.net {bio_query}",
        ]
        
        bio_results = []
        for source_query in bio_sources[:2]:  # Limit to avoid rate limits
            try:
                bio_results.extend(self.search(source_query, max_results=1))
            except Exception as e:
                logger.debug(f"Bio source search failed: {e}")
        
        # Use RGWeb to directly search bioRxiv/medRxiv papers
        rgweb_results = []
        if self.rgweb and bio_results:
            for result in bio_results[:2]:
                url = result.get('link', '')
                if url and ('biorxiv.org' in url or 'medrxiv.org' in url or 'pubmed' in url):
                    try:
                        key_terms = ' '.join(bio_query.split()[:5])
                        rgweb_matches = self.rgweb.search_url(_literal_rg_pattern(key_terms), url, case_sensitive=False)
                        for match in rgweb_matches[:1]:
                            rgweb_results.append({
                                "title": f"{result.get('title', 'Paper')} (Line {match.get('line', '?')})",
                                "link": url,
                                "snippet": match.get('match', ''),
                                "source": "biomimic-rgweb"
                            })
                    except Exception as e:
                        logger.debug(f"RGWeb search failed for {url}: {e}")
        
        return api_results + bio_results + rgweb_results

    def run_alchemist(self, query: str) -> List[Dict]:
        """
        Scout 6: The Alchemist. Searches suppressed medicine & natural law.
        Uses RGWeb to directly fetch and search medical/natural law sites.
        """
        # 1. Abstract
        alchemy_query = self.abstract_concept(query, "ALCHEMIST")
        logger.info(f"Scout [ALCHEMIST] brewing -> '{alchemy_query}'")
        
        results = []
        
        # Search specific nodes (API discovery) - expanded with government and academic sources
        med_nodes = [
            "site:greenmedinfo.com",
            "site:earthclinic.com",
            "site:whale.to",
            "site:ncbi.nlm.nih.gov mechanism of action",
            "site:fda.gov",  # FDA drug/device data
            "site:cdc.gov",  # CDC health data
            "site:medrxiv.org",  # Medical preprints
            "site:pubmed.ncbi.nlm.nih.gov",  # PubMed
            "site:researchgate.net",  # Medical research
        ]
        
        for node in med_nodes:
            q = f"{query} {node}"
            api_results = self.search(q, max_results=1)
            results.extend(api_results)
            
            # Use RGWeb to directly fetch and search content
            if self.rgweb and api_results:
                for result in api_results[:1]:
                    url = result.get('link', '')
                    if url and any(domain in url for domain in ['greenmedinfo.com', 'earthclinic.com', 'whale.to', 'ncbi.nlm.nih.gov']):
                        try:
                            key_terms = ' '.join(query.split()[:5])
                            rgweb_matches = self.rgweb.search_url(_literal_rg_pattern(key_terms), url, case_sensitive=False)
                            for match in rgweb_matches[:1]:
                                results.append({
                                    "title": f"{result.get('title', 'Medical')} (Line {match.get('line', '?')})",
                                    "link": url,
                                    "snippet": match.get('match', ''),
                                    "source": "alchemist-rgweb"
                                })
                        except Exception as e:
                            logger.debug(f"RGWeb search failed for {url}: {e}")
            
        # Also search the abstracted mechanism
        results.extend(self.search(alchemy_query, max_results=2))
        
        return results

    def run_hacker(self, query: str) -> List[Dict]:
        """
        Scout 7: The Hacker. Searches the digital underground/repo layer.
        """
        # 1. Abstract
        hacker_query = self.abstract_concept(query, "HACKER")
        logger.info(f"Scout [HACKER] pinging repo -> '{hacker_query}'")
        
        results = []
        
        # DOMAIN SPECIFIC INJECTION
        # If the query is about voice/audio, inject the SOTA voice cloning tech keywords
        voice_keywords = ["voice", "tts", "clone", "speech", "audio", "speak"]
        is_voice_query = any(k in query.lower() for k in voice_keywords)
        
        if is_voice_query:
            logger.info("[HACKER] Detected Voice Query. Injecting SOTA Audio keywords.")
            # These are the actual tools used to clone voices in 2024/2025
            tech_stack = "RVC v2 OR StyleTTS2 OR GPT-SoVITS OR XTTS OR Mangio-Crepe"
            hacker_query = f"{hacker_query} {tech_stack}"
        
        # The Code Repos (expanded with technical documentation)
        repo_nodes = [
            "site:huggingface.co",
            "site:github.com",
            "site:gitlab.com",
            "site:reddit.com/r/LocalLLaMA",
            "site:civitai.com",  # AI models
            "site:stackoverflow.com",  # Programming Q&A
            "site:stackexchange.com",  # Stack Exchange network
            "site:developer.mozilla.org",  # MDN Web Docs
            "site:docs.python.org",  # Python docs
            "site:rust-lang.org",  # Rust docs
        ]
        
        for node in repo_nodes:
            # We combine the abstracted query with the site search
            q = f"{hacker_query} {node}"
            results.extend(self.search(q, max_results=1))
            
        return results

    def run_archaeologist(self, query: str) -> List[Dict]:
        """
        Scout 8: The Archaeologist. Searches using direct URL content (curl + ripgrep).
        Bypasses search APIs entirely - direct access to GitHub, Archive.org, etc.
        
        Searches multiple sources:
        - PhoenixVisualizer GitHub README
        - Archive.org snapshots of key knowledge sources
        - rexresearch.com (suppressed tech)
        """
        logger.info(f"Scout [ARCHAEOLOGIST] excavating -> '{query}'")
        
        results = []
        
        # Build pattern: convert spaces to OR patterns for ripgrep
        # E.g., "anti gravity" -> "anti|gravity"
        # IMPORTANT: Escape special regex characters before building pattern
        # to prevent regex parse errors (e.g., "**Software Development &" -> invalid regex)
        import re
        # Escape special regex characters: . * + ? ^ $ [ ] { } ( ) | \
        escaped_query = re.escape(query)
        # Now convert escaped spaces (\ ) to OR patterns (|)
        pattern = escaped_query.replace(r'\ ', '|')
        if not pattern:
            pattern = escaped_query  # Fallback if no spaces
        
        # Search multiple GitHub repositories (knowledge bases)
        repos_to_search = [
            ("acrinym/PhoenixVisualizer", "master"),
            ("RVC-Project/Retrieval-based-Voice-Conversion-WebUI", "main"),
        ]
        
        for repo, branch in repos_to_search:
            try:
                logger.debug(f"Searching GitHub {repo}/{branch} for pattern: {pattern}")
                repo_results = self.rgweb.search_github_repo(
                    pattern=pattern,
                    repo=repo,
                    branch=branch
                )
                
                # Convert rgweb results to our format
                for r in repo_results:
                    results.append({
                        "title": f"GitHub {repo}: {r.get('url', 'Unknown')} (Line {r.get('line', '?')})",
                        "link": r.get('url', ''),
                        "snippet": r.get('match', ''),
                        "source": "archaeologist-github"
                    })
                
                if repo_results:
                    logger.info(f"Scout [ARCHAEOLOGIST] found {len(repo_results)} hits in {repo}")
            except Exception as e:
                logger.warning(f"Archaeologist GitHub search failed for {repo}: {e}")
        
        # Search shadow libraries (Anna's Archive, ZLibrary) for documents
        shadow_library_domains = [
            "site:annas-archive.org",
            "site:z-lib.org",
            "site:z-lib.is",
            "site:z-lib.io"
        ]
        
        for domain in shadow_library_domains[:2]:  # Limit to top 2 to avoid rate limits
            try:
                search_query = f"{query} {domain}"
                shadow_results = self.search(search_query, max_results=2)
                results.extend(shadow_results)
                
                # Use RGWeb to extract document metadata and download links
                if self.rgweb and shadow_results:
                    for result in shadow_results[:1]:  # Top result per domain
                        url = result.get('link', '')
                        if url and any(domain_name in url for domain_name in ['annas-archive.org', 'z-lib.org', 'z-lib.is', 'z-lib.io']):
                            try:
                                # Extract document title, author, format from page
                                key_terms = ' '.join(query.split()[:5])
                                rgweb_matches = self.rgweb.search_url(_literal_rg_pattern(key_terms), url, case_sensitive=False)
                                for match in rgweb_matches[:2]:
                                    results.append({
                                        "title": f"{result.get('title', 'Document')} (Line {match.get('line', '?')})",
                                        "link": url,
                                        "snippet": match.get('match', ''),
                                        "source": "archaeologist-shadow-lib"
                                    })
                            except Exception as e:
                                logger.debug(f"RGWeb search failed for shadow library {url}: {e}")
            except Exception as e:
                logger.debug(f"Shadow library search failed for {domain}: {e}")
        
        logger.info(f"Scout [ARCHAEOLOGIST] unearthed {len(results)} total artifacts")
        return results

    def run_shadow_librarian(self, query: str) -> List[Dict]:
        """
        Scout 9: The Shadow Librarian. Specialized scout for shadow libraries and hidden document sources.
        
        Focuses on:
        - Document discovery (books, papers, technical docs)
        - Metadata extraction (title, author, format, size)
        - Multi-source availability checking
        - Download link extraction
        
        Sources:
        - Anna's Archive (meta-search across shadow libraries)
        - ZLibrary (books, papers, documents)
        - Library Genesis (already in truth_nodes)
        - Sci-Hub (already in truth_nodes)
        """
        logger.info(f"Scout [SHADOW LIBRARIAN] searching shadow archives for: '{query}'")
        
        results = []
        
        # Normalize query for document search (remove "how to build" fluff)
        doc_query = query.replace("How to build", "").replace("How to make", "").replace("build me", "").replace("create a", "").strip()
        
        # Shadow library domains (document-focused sources)
        shadow_domains = [
            "site:annas-archive.org",
            "site:z-lib.org",
            "site:z-lib.is",
            "site:z-lib.io",
            "site:libgen.rs",  # Library Genesis
            "site:scihub.org",  # Sci-Hub
        ]
        
        # Search each shadow library domain
        for domain in shadow_domains[:4]:  # Limit to top 4 to avoid rate limits
            try:
                search_query = f"{doc_query} {domain}"
                domain_results = self.search(search_query, max_results=3)
                results.extend(domain_results)
                
                # Use RGWeb to extract document metadata and download links
                if self.rgweb and domain_results:
                    for result in domain_results[:2]:  # Top 2 results per domain
                        url = result.get('link', '')
                        if url and any(domain_name in url for domain_name in [
                            'annas-archive.org', 'z-lib.org', 'z-lib.is', 'z-lib.io',
                            'libgen.rs', 'scihub.org'
                        ]):
                            try:
                                # Extract document metadata (title, author, format, download links)
                                key_terms = ' '.join(doc_query.split()[:5])
                                rgweb_matches = self.rgweb.search_url(_literal_rg_pattern(key_terms), url, case_sensitive=False)
                                
                                # Look for download links, metadata in page content
                                for match in rgweb_matches[:3]:  # Top 3 matches per document page
                                    results.append({
                                        "title": f"{result.get('title', 'Document')} (Line {match.get('line', '?')})",
                                        "link": url,
                                        "snippet": match.get('match', ''),
                                        "source": "shadow_librarian-rgweb"
                                    })
                            except Exception as e:
                                logger.debug(f"RGWeb search failed for shadow library {url}: {e}")
            except Exception as e:
                logger.debug(f"Shadow library search failed for {domain}: {e}")
        
        # Also search for document-specific patterns (ISBN, DOI, etc.)
        # Extract potential ISBN/DOI from query
        isbn_pattern = r'\b\d{10,13}\b'  # Simple ISBN pattern
        doi_pattern = r'10\.\d{4,}/[^\s]+'  # DOI pattern
        
        import re
        isbn_match = re.search(isbn_pattern, query)
        doi_match = re.search(doi_pattern, query)
        
        if isbn_match:
            isbn = isbn_match.group()
            logger.info(f"[SHADOW LIBRARIAN] Detected ISBN: {isbn}, searching shadow libraries")
            for domain in ["site:annas-archive.org", "site:z-lib.org"]:
                try:
                    isbn_query = f"{isbn} {domain}"
                    isbn_results = self.search(isbn_query, max_results=2)
                    results.extend(isbn_results)
                except Exception as e:
                    logger.debug(f"ISBN search failed for {domain}: {e}")
        
        if doi_match:
            doi = doi_match.group()
            logger.info(f"[SHADOW LIBRARIAN] Detected DOI: {doi}, searching Sci-Hub")
            try:
                doi_query = f"{doi} site:scihub.org"
                doi_results = self.search(doi_query, max_results=2)
                results.extend(doi_results)
            except Exception as e:
                logger.debug(f"DOI search failed: {e}")
        
        logger.info(f"Scout [SHADOW LIBRARIAN] found {len(results)} documents in shadow archives")
        return results
    
    def run_supplier_scout(self, query: str) -> List[Dict]:
        """
        Scout 10: The Supplier Scout. Finds actual suppliers, distributors, and vendors for components.
        
        Focuses on:
        - Real supplier websites and catalogs
        - Distributor information (DigiKey, Mouser, McMaster-Carr, etc.)
        - Online marketplaces (Amazon, eBay, AliExpress)
        - Manufacturer direct sales
        - Pricing and availability information
        - Contact information for custom orders
        
        Sources:
        - Electronics distributors (digikey.com, mouser.com, adafruit.com, etc.)
        - Industrial suppliers (mcmaster.com, grainger.com, thomasnet.com)
        - Online marketplaces (amazon.com, ebay.com, aliexpress.com)
        - Lab suppliers (sigmaaldrich.com, fishersci.com)
        - Specialty suppliers (jameco.com, pololu.com, banggood.com)
        """
        logger.info(f"Scout [SUPPLIER] searching for suppliers: '{query}'")
        
        results = []
        
        # Normalize query for supplier search (focus on component name + "supplier" or "buy")
        supplier_query = query.strip()
        if "supplier" not in supplier_query.lower() and "buy" not in supplier_query.lower():
            supplier_query = f"{supplier_query} supplier buy"
        
        # Priority supplier domains (electronics distributors first, then marketplaces)
        priority_domains = [
            "site:digikey.com",
            "site:mouser.com",
            "site:amazon.com",
            "site:ebay.com",
            "site:mcmaster.com",
            "site:adafruit.com",
            "site:sparkfun.com",
        ]
        
        # Search priority domains first
        for domain in priority_domains:
            try:
                search_query = f"{supplier_query} {domain}"
                domain_results = self.search(search_query, max_results=2)
                results.extend(domain_results)
                
                # Use RGWeb to extract pricing, part numbers, and availability
                if self.rgweb and domain_results:
                    for result in domain_results[:1]:  # Top result per domain
                        url = result.get('link', '')
                        if url:
                            try:
                                # Extract supplier information (part numbers, pricing, stock status)
                                key_terms = ' '.join(supplier_query.split()[:3])
                                rgweb_matches = self.rgweb.search_url(_literal_rg_pattern(key_terms), url, case_sensitive=False)
                                for match in rgweb_matches[:1]:
                                    results.append({
                                        "title": f"{result.get('title', 'Supplier Page')} - {match.get('line', '?')}",
                                        "link": url,
                                        "snippet": match.get('match', ''),
                                        "source": "supplier-rgweb",
                                        "supplier_info": True
                                    })
                            except Exception as e:
                                logger.debug(f"RGWeb supplier search failed for {url}: {e}")
            except Exception as e:
                logger.debug(f"Supplier search failed for {domain}: {e}")
        
        # Search additional supplier domains
        additional_domains = [
            "site:newark.com",
            "site:arrow.com",
            "site:avnet.com",
            "site:grainger.com",
            "site:thomasnet.com",
            "site:sigmaaldrich.com",
            "site:fishersci.com",
            "site:aliexpress.com",
            "site:alibaba.com",
            "site:banggood.com",
            "site:jameco.com",
            "site:pololu.com",
        ]
        
        for domain in additional_domains[:4]:  # Limit to 4 more to avoid rate limits
            try:
                search_query = f"{supplier_query} {domain}"
                domain_results = self.search(search_query, max_results=1)
                results.extend(domain_results)
            except Exception as e:
                logger.debug(f"Supplier search failed for {domain}: {e}")
        
        # Also do general supplier search (marketplaces, general vendors)
        try:
            # Search for component on marketplaces
            marketplace_queries = [
                f"{supplier_query} site:amazon.com",
                f"{supplier_query} site:ebay.com",
            ]
            for mq in marketplace_queries:
                try:
                    marketplace_results = self.search(mq, max_results=2)
                    results.extend(marketplace_results)
                except Exception as e:
                    logger.debug(f"Marketplace search failed: {e}")
            
            # General supplier/distributor search
            general_query = f"{supplier_query} distributor vendor buy"
            general_results = self.search(general_query, max_results=2)
            results.extend(general_results)
        except Exception as e:
            logger.debug(f"General supplier search failed: {e}")
        
        logger.info(f"[SCOUT SWARM] Supplier Scout found {len(results)} results")
        return results[:8]  # Return top 8 supplier results (increased from 5 to include marketplaces)

    def _run_ghost_scout(self, query: str) -> List[Dict]:
        """
        Scout 11: The Ghost. No-API search: scrape Google/Bing → visit URLs → RGWeb search in RAM.
        Returns only URLs where query terms appear in page content (verified via ripgrep).
        """
        if not HAS_GHOST_SCOUT or run_ghost_scout is None:
            return []
        try:
            return run_ghost_scout(self, query)
        except Exception as e:
            logger.warning(f"[SCOUT SWARM] Ghost Scout failed: {e}")
            return []

    # --- DISPATCHER ---

    def deploy_swarm(self, query: str, use_parallel: bool = True) -> Dict[str, List[Dict]]:
        """
        Runs all scouts in parallel and aggregates results.
        
        Args:
            query: Search query
            use_parallel: If True, use parallel execution (Phase 9). If False, sequential (legacy).
        
        Returns:
            Dictionary mapping scout names to result lists
        """
        print(f"\n[SCOUT SWARM] Deploying 11-Dimensional Search for: '{query}'")
        logger.info(f"[SCOUT SWARM] Deploying 11 scouts for query: '{query}' (parallel={use_parallel})")
        import sys
        sys.stdout.flush()
        
        # PHASE 9: Use parallel executor if available
        if use_parallel:
            try:
                from onyx_parallel_executor import parallelize_scout_swarm
                dossier = parallelize_scout_swarm(
                    scout_instance=self,
                    query=query,
                    max_workers=4,  # Run 4 scouts concurrently
                    timeout_per_scout=30.0
                )
                
                # Log results
                scout_results = {name: len(results) for name, results in dossier.items()}
                for scout_name, count in scout_results.items():
                    logger.info(f"[SCOUT SWARM] {scout_name} found {count} results")
                    if count > 0:
                        print(f"[SCOUT SWARM] {scout_name}: {count} results")
                        sys.stdout.flush()
                
                # Continue with validation (existing code below)
                scout_results = {name: len(results) for name, results in dossier.items()}
            except ImportError:
                logger.warning("[SCOUT SWARM] Parallel executor not available, falling back to sequential")
                use_parallel = False
            except Exception as e:
                logger.error(f"[SCOUT SWARM] Parallel execution failed: {e}, falling back to sequential")
                use_parallel = False
        
        # Fallback to sequential execution (legacy or if parallel fails)
        if not use_parallel:
            dossier = {}
            scout_results = {}
            
            # Run each scout and log results
            scouts = [
                ("Heretic", self.run_heretic),
                ("Patent_Clerk", self.run_patent_clerk),
                ("Engineer", self.run_engineer),
                ("Historian", self.run_historian),
                ("Bio_Mimic", self.run_biomimic),
                ("Alchemist", self.run_alchemist),
                ("Hacker", self.run_hacker),
                ("Archaeologist", self.run_archaeologist),
                ("Shadow_Librarian", self.run_shadow_librarian),
                ("Supplier", self.run_supplier_scout),
                ("Ghost", self._run_ghost_scout),
            ]
            
            for scout_name, scout_func in scouts:
                try:
                    print(f"[SCOUT SWARM] Running {scout_name}...")
                    sys.stdout.flush()
                    results = scout_func(query)
                    dossier[scout_name] = results
                    scout_results[scout_name] = len(results)
                    logger.info(f"[SCOUT SWARM] {scout_name} found {len(results)} results")
                    if len(results) > 0:
                        print(f"[SCOUT SWARM] {scout_name}: {len(results)} results")
                        sys.stdout.flush()
                except Exception as e:
                    logger.error(f"[SCOUT SWARM] {scout_name} failed: {e}")
                    print(f"[SCOUT SWARM] {scout_name} ERROR: {e}")
                    sys.stdout.flush()
                    dossier[scout_name] = []
                    scout_results[scout_name] = 0
                    import traceback
                    logger.debug(f"[SCOUT SWARM] {scout_name} traceback: {traceback.format_exc()}")
        
        # Validate results (dedup, flag low-quality)
        validation = self._validate_results(dossier, query)
        if not validation['valid']:
            logger.warning(f"[SCOUT SWARM] Validation issues: {validation['errors']}")
        dossier = validation['dossier']
        
        # Post-process: Detect dependencies and generate tests for code hits
        for scout_name, hits in dossier.items():
            for hit in hits:
                if 'github.com' in hit.get('link', '') and any(ext in hit.get('link', '') for ext in ['.py', '.js', '.ts']):
                    try:
                        content = self._fetch_github_content(hit['link'])
                        if content:
                            deps = self._detect_dependencies(content)
                            if deps:
                                hit['dependencies'] = deps
                                logger.debug(f"[SCOUT SWARM] Dependencies detected in {hit['link']}: {', '.join(deps)}")
                    except Exception as e:
                        logger.debug(f"[SCOUT SWARM] Failed to process GitHub content: {e}")
        
        total_hits = sum(len(v) for v in dossier.values())
        print(f"[SCOUT SWARM] Mission Complete. {total_hits} Intelligence Packets retrieved.")
        print(f"[SCOUT SWARM] Breakdown: {scout_results}")
        if validation['errors']:
            print(f"[SCOUT SWARM] Validation warnings: {len(validation['errors'])} issues")
        sys.stdout.flush()
        logger.info(f"[SCOUT SWARM] Total results: {total_hits} from {len([r for r in scout_results.values() if r > 0])} active scouts")
        
        return dossier

# --- TEST HARNESS ---
if __name__ == "__main__":
    # Load API Key for Abstraction
    import os
    import json
    
    key = None
    if os.path.exists("config.json"):
        with open("config.json") as f:
            key = json.load(f).get("apiKeys", {}).get("geminiKey")
            
    if not key:
        import hephaestus_hardwired
        key = hephaestus_hardwired.GEMINI_KEY
        
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    scout = HoloScout(model)
    
    # Test with a forbidden query
    test_query = "Stan Meyer Water Fuel Cell"
    dossier = scout.deploy_swarm(test_query)
    
    print("\n--- DOSSIER REPORT ---")
    for scout_name, hits in dossier.items():
        print(f"\n[{scout_name.upper()}]")
        for hit in hits:
            print(f"- {hit['title']} ({hit['link']})")
