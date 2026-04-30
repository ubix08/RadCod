"""
RadCod Browser Agent
===================
Web browsing capabilities for research and documentation.

The Browser Agent can:
- Navigate web pages
- Search documentation
- Extract code examples
- Find solutions to errors
"""

import asyncio
from dataclasses import dataclass
from typing import Any

try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False


# =============================================================================
# Browser Configuration
# =============================================================================

@dataclass
class BrowserConfig:
    """Configuration for browser agent."""
    
    headless: bool = True
    viewport_width: int = 1280
    viewport_height: int = 720
    timeout: int = 30000
    user_agent: str | None = None


# =============================================================================
# Browser Session
# =============================================================================

class BrowserSession:
    """Browser session for navigation."""
    
    def __init__(self, config: BrowserConfig | None = None):
        self.config = config or BrowserConfig()
        self._browser = None
        self._page = None
        self._context = None
    
    async def __aenter__(self):
        """Context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, *args):
        """Context manager exit."""
        await self.stop()
    
    async def start(self) -> None:
        """Start browser."""
        if not HAS_PLAYWRIGHT:
            raise RuntimeError("Playwright not installed. Run: pip install playwright")
        
        pw = await async_playwright().start()
        self._browser = await pw.chromium.launch(
            headless=self.config.headless,
        )
        self._context = await self._browser.new_context(
            viewport={
                "width": self.config.viewport_width,
                "height": self.config.viewport_height,
            },
            user_agent=self.config.user_agent,
        )
        self._page = await self._context.new_page()
    
    async def stop(self) -> None:
        """Stop browser."""
        if self._browser:
            await self._browser.close()
    
    async def navigate(self, url: str) -> str:
        """Navigate to URL."""
        if not self._page:
            raise RuntimeError("Browser not started")
        
        await self._page.goto(url, timeout=self.config.timeout)
        return await self.get_content()
    
    async def get_content(self) -> str:
        """Get page content."""
        if not self._page:
            return ""
        
        return await self._page.content()
    
    async def get_text(self, selector: str) -> str:
        """Get text from element."""
        if not self._page:
            return ""
        
        element = await self._page.query_selector(selector)
        if element:
            return await element.text_content()
        return ""
    
    async def click(self, selector: str) -> None:
        """Click element."""
        if not self._page:
            return
        
        await self._page.click(selector)
    
    async def type(self, selector: str, text: str) -> None:
        """Type into element."""
        if not self._page:
            return
        
        await self._page.type(selector, text)
    
    async def evaluate(self, script: str) -> Any:
        """Evaluate JavaScript."""
        if not self._page:
            return None
        
        return await self._page.evaluate(script)


# =============================================================================
# Browser Agent
# =============================================================================

class BrowserAgent:
    """
    Browser Agent for web research.
    
    Capabilities:
    - Navigate documentation
    - Find code examples
    - Extract error solutions
    - Browse GitHub, StackOverflow, etc.
    """
    
    def __init__(self, config: BrowserConfig | None = None):
        self.config = config or BrowserConfig()
        self.session: BrowserSession | None = None
    
    async def __aenter__(self):
        """Async context manager."""
        self.session = BrowserSession(self.config)
        await self.session.__aenter__()
        return self
    
    async def __aexit__(self, *args):
        """Async context manager exit."""
        if self.session:
            await self.session.__aexit__(*args)
    
    async def search_documentation(self, library: str) -> dict:
        """
        Search for library documentation.
        
        Args:
            library: Library name to search
            
        Returns:
            Documentation content
        """
        doc_urls = {
            "python": "https://docs.python.org/3/",
            "react": "https://react.dev/",
            "flask": "https://flask.palletsprojects.com/",
            "fastapi": "https://fastapi.tiangolo.com/",
            "django": "https://docs.djangoproject.com/",
            "numpy": "https://numpy.org/doc/stable/",
            "pandas": "https://pandas.pydata.org/docs/",
        }
        
        url = doc_urls.get(library.lower())
        if not url:
            # Generic search
            url = f"https://www.google.com/search?q={library}+documentation"
        
        if self.session:
            content = await self.session.navigate(url)
            return {"url": url, "content": content}
        
        return {"error": "Browser not started"}
    
    async def get_stackoverflow(self, query: str) -> dict:
        """Get StackOverflow results."""
        url = f"https://stackoverflow.com/search?q={query.replace(' ', '+')}"
        
        if self.session:
            content = await self.session.navigate(url)
            return {"query": query, "content": content}
        
        return {"error": "Browser not started"}
    
    async def get_github(self, repo: str, path: str = "") -> dict:
        """Get GitHub file or repo."""
        url = f"https://github.com/{repo}/{path}" if path else f"https://github.com/{repo}"
        
        if self.session:
            content = await self.session.navigate(url)
            return {"repo": repo, "content": content}
        
        return {"error": "Browser not started"}
    
    async def extract_code_examples(self, url: str) -> list[str]:
        """Extract code examples from a page."""
        if not self.session:
            return []
        
        # Get all code blocks
        code_blocks = await self.session.evaluate("""
            () => Array.from(document.querySelectorAll('pre code, code'))
                .map(el => el.textContent)
        """)
        
        return code_blocks or []


# =============================================================================
# HTTP Fallback (when no browser)
# =============================================================================

class HTTPBrowser:
    """Simple HTTP browser fallback."""
    
    async def fetch(self, url: str) -> str:
        """Fetch URL content."""
        import urllib.request
        
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                return response.read().decode('utf-8')
        except Exception as e:
            return f"Error: {e}"
    
    async def search(self, query: str) -> dict:
        """Simple search via DuckDuckGo."""
        url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        content = await self.fetch(url)
        
        return {"query": query, "content": content[:5000]}


# =============================================================================
# Functions
# =============================================================================

async def search_docs(library: str) -> dict:
    """Quick documentation search."""
    async with BrowserAgent() as agent:
        return await agent.search_documentation(library)


async def search_stackoverflow(error: str) -> dict:
    """Search StackOverflow for error."""
    async with BrowserAgent() as agent:
        return await agent.get_stackoverflow(error)


def create_browser_agent(config: BrowserConfig | None = None) -> BrowserAgent:
    """Create browser agent."""
    return BrowserAgent(config)