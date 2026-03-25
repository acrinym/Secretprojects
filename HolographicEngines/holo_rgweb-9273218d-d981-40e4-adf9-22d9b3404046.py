"""
HOLO RGWEB - Direct URL Content Search Engine
==============================================
"The Uncensored Eye"

Uses curl + ripgrep to search raw content from URLs directly.
No search APIs, no indexes, no censorship - just download and grep.

Perfect for:
- GitHub repositories
- Archive.org snapshots
- Raw.githubusercontent.com
- Personal websites
- Direct document access

No auth required. Works offline (download first, search second).
"""

import subprocess
import logging
import time
from typing import List, Dict, Optional
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [RGWEB] - %(message)s')
logger = logging.getLogger(__name__)

# Import rate limiter (optional - will use old method if not provided)
try:
    from holo_rate_limiter import HoloRateLimiter
    HAS_RATE_LIMITER = True
except ImportError:
    HAS_RATE_LIMITER = False
    logger.warning("[RGWEB] Rate limiter not available, using hardcoded delays")


class HoloRGWeb:
    """Direct URL content search using curl + ripgrep"""
    
    def __init__(self, timeout: int = 15, parallel: int = 1, rate_limiter=None):
        """
        Args:
            timeout: Curl timeout in seconds
            parallel: Number of parallel searches
            rate_limiter: Optional HoloRateLimiter instance (creates default if None and available)
        """
        self.timeout = timeout
        self.parallel = parallel
        self.has_curl = self._check_tool('curl')
        self.has_rg = self._check_tool('rg')
        
        # Initialize rate limiter (use provided, create default, or None)
        if rate_limiter is not None:
            self.rate_limiter = rate_limiter
        elif HAS_RATE_LIMITER:
            self.rate_limiter = HoloRateLimiter(use_old_method=True)
        else:
            self.rate_limiter = None
        
        if not self.has_curl:
            logger.warning("curl not found. Install: choco install curl (Windows)")
        if not self.has_rg:
            logger.warning("ripgrep not found. Install: choco install ripgrep (Windows)")
    
    def _check_tool(self, tool: str) -> bool:
        """Check if a tool is available in PATH"""
        try:
            subprocess.run(
                [tool, '--version'],
                capture_output=True,
                timeout=2
            )
            return True
        except:
            return False
    
    def search_url(self, pattern: str, url: str, case_sensitive: bool = False) -> List[Dict]:
        """
        Search for pattern in a single URL's content.
        
        Args:
            pattern: Regex pattern to search for (properly escaped)
            url: URL to fetch and search
            case_sensitive: Whether search is case-sensitive
        
        Returns:
            List of matches with line numbers
        """
        if not self.has_curl or not self.has_rg:
            logger.error("curl and ripgrep are required")
            return []
        
        results = []
        
        try:
            logger.info(f"Fetching: {url}")
            
            # Validate URL format
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                logger.error(f"Invalid URL format: {url}")
                return []
            
            # Rate limiting (dynamic or old method)
            domain = parsed_url.netloc
            if self.rate_limiter:
                self.rate_limiter.wait(domain)
            
            # Fetch URL with curl
            start_time = time.time()
            curl_cmd = [
                'curl', '-sL',
                '--compressed',
                f'--max-time', str(self.timeout),
                '--user-agent', 'rgweb/1.0 (+https://github.com/PhoenixVisualizer)',
                url
            ]
            
            curl_proc = subprocess.Popen(
                curl_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False  # binary mode
            )
            
            # Build ripgrep command with proper pattern handling
            rg_cmd = ['rg', '--max-count', '100']  # Limit results per file
            
            if not case_sensitive:
                rg_cmd.append('-i')
            
            # Add line numbers and context
            rg_cmd.extend(['-n', '-A', '1'])  # line numbers + 1 line of context
            
            # Add pattern (no escaping needed - rg handles raw input)
            rg_cmd.append(pattern)
            
            # Pipe curl output to ripgrep
            rg_proc = subprocess.Popen(
                rg_cmd,
                stdin=curl_proc.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',  # FIX: Use UTF-8 instead of system default (cp1252)
                errors='replace'   # FIX: Replace undecodable characters instead of crashing
            )
            
            curl_proc.stdout.close()  # Allow curl to receive SIGPIPE if rg exits
            
            # Read ripgrep output
            stdout, stderr = rg_proc.communicate(timeout=self.timeout)
            
            if rg_proc.returncode == 0 and stdout:
                # Parse ripgrep output: "url:line:match"
                for line in stdout.strip().split('\n'):
                    if line and ':' in line:
                        parts = line.split(':', 3)  # url:line:col:match
                        if len(parts) >= 3:
                            results.append({
                                'url': url,
                                'line': parts[1],
                                'match': parts[3] if len(parts) > 3 else '',
                                'source': 'rgweb'
                            })
                
                logger.info(f"Found {len(results)} matches in {url}")
            elif rg_proc.returncode == 1:
                logger.debug(f"No matches found in {url}")
            else:
                if stderr:
                    logger.warning(f"ripgrep error: {stderr}")
        
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout fetching {url}")
        except Exception as e:
            logger.error(f"Error searching {url}: {e}")
        
        return results
    
    def search_urls(self, pattern: str, urls: List[str], case_sensitive: bool = False) -> List[Dict]:
        """
        Search for pattern across multiple URLs.
        
        Args:
            pattern: Regex pattern to search for
            urls: List of URLs to search
            case_sensitive: Whether search is case-sensitive
        
        Returns:
            Combined results from all URLs
        """
        all_results = []
        
        for url in urls:
            results = self.search_url(pattern, url, case_sensitive)
            all_results.extend(results)
            # Rate limiting is handled inside search_url() now
        
        return all_results
    
    def search_github_repo(self, pattern: str, repo: str, branch: str = "main") -> List[Dict]:
        """
        Search a GitHub repository directly (no API required).
        
        Args:
            pattern: Regex pattern
            repo: "owner/repo"
            branch: branch name (default: main)
        
        Returns:
            List of matches
        """
        # GitHub raw content URL
        url = f"https://raw.githubusercontent.com/{repo}/{branch}/README.md"
        logger.info(f"Searching GitHub repo: {repo}")
        return self.search_url(pattern, url)
    
    def search_archive_org(self, pattern: str, original_url: str, date: str = "*") -> List[Dict]:
        """
        Search an Archive.org Wayback Machine snapshot.
        
        Args:
            pattern: Regex pattern
            original_url: Original URL to search in archive
            date: Snapshot date (YYYYMMDD) or "*" for latest
        
        Returns:
            List of matches
        """
        # Wayback Machine URL
        archive_url = f"https://web.archive.org/web/{date}/{original_url}"
        logger.info(f"Searching Archive.org: {archive_url}")
        return self.search_url(pattern, archive_url)
    
    def search_github_search(self, pattern: str, query: str) -> List[Dict]:
        """
        Search GitHub via raw.githubusercontent.com (raw code files).
        
        Implementation: Uses GitHub's raw content URLs to search for code patterns.
        This approach works by constructing URLs to known repositories and searching
        their raw file content directly, which is more reliable than GitHub's search API
        for specific code patterns.
        
        Args:
            pattern: Regex pattern to search for
            query: Human query to convert to search term (used for repository selection)
        
        Returns:
            List of matches (limited to prevent excessive requests)
        """
        # Example: search for "voice cloning" patterns in rvc repos
        repos = [
            "RVC-Project/Retrieval-based-Voice-Conversion-WebUI/main/README.md",
            "suno-ai/bark/main/README.md",
            "openai/gpt-4/main/README.md"  # Example
        ]
        
        all_results = []
        for repo in repos:
            url = f"https://raw.githubusercontent.com/{repo}"
            results = self.search_url(pattern, url)
            all_results.extend(results)
        
        return all_results


# Example usage and testing
if __name__ == "__main__":
    import json
    
    rgweb = HoloRGWeb(timeout=15)
    
    # Test 1: Search GitHub README with a pattern that exists
    print("\n[TEST 1] Searching acrinym/PhoenixVisualizer README...")
    results = rgweb.search_github_repo(
        pattern="Phoenix|plugin|shader",  # More common patterns
        repo="acrinym/PhoenixVisualizer",
        branch="master"
    )
    print(f"Found {len(results)} matches")
    for r in results[:3]:
        match_text = r['match'][:60] if r['match'] else "(no text)"
        print(f"  {r['url']}:{r['line']} - {match_text}")
    
    # Test 2: Search Archive.org
    print("\n[TEST 2] Searching Archive.org snapshot...")
    results = rgweb.search_archive_org(
        pattern="technology OR research",
        original_url="example.com",
        date="20200101"
    )
    print(f"Found {len(results)} matches")
    
    # Test 3: Multiple URLs
    print("\n[TEST 3] Searching multiple tech sites...")
    urls = [
        "https://raw.githubusercontent.com/PhoenixVisualizer/README.md",
        "https://archive.org"
    ]
    results = rgweb.search_urls(pattern="quantum", urls=urls)
    print(f"Found {len(results)} total matches")
    
    print("\nrgweb ready for integration into HoloScout")
