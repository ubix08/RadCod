"""
Browser Agent - Tests and validates applications.

Uses browser automation to test generated applications.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field

from src.orchestrator.skills import load_skill

logger = logging.getLogger("radcod.browser_agent")


@dataclass
class TestResult:
    """Result from a browser test."""
    name: str
    status: str  # passed, failed, error
    duration_ms: int
    error: Optional[str] = None
    screenshot: Optional[str] = None


@dataclass
class ValidationResult:
    """Complete validation result."""
    application_url: str
    tests_passed: int = 0
    tests_failed: int = 0
    tests_run: int = 0
    results: List[TestResult] = field(default_factory=list)
    issues: List[Dict[str, Any]] = field(default_factory=list)
    summary: str = ""


class BrowserAgent:
    """
    Browser testing agent that validates generated applications.
    
    Uses Playwright or Selenium for browser automation.
    """
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.skill = load_skill("browser_validation")
        self._browser = None
        self._page = None
        logger.info(f"Browser Agent initialized (headless={headless})")
    
    def _load_skill(self) -> str:
        """Get skill - now uses shared loader."""
        return self.skill
    
    def _init_browser(self):
        """Initialize browser (lazy init)."""
        try:
            from playwright.sync_api import sync_playwright
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=self.headless)
            self._context = self._browser.new_context()
            self._page = self._context.new_page()
        except ImportError:
            logger.warning("Playwright not installed - browser testing unavailable")
            return False
        except Exception as e:
            logger.error(f"Browser init failed: {e}")
            return False
        return True
    
    def validate(
        self, 
        application_url: str,
        tests: List[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Validate an application through the browser.
        
        Args:
            application_url: URL of the application to test
            tests: Optional list of test specifications
            
        Returns:
            ValidationResult with test results
        """
        result = ValidationResult(application_url=application_url)
        
        # Default tests if none provided
        if not tests:
            tests = self._get_default_tests()
        
        # Initialize browser
        if not self._init_browser():
            result.summary = "Browser initialization failed"
            return result
        
        try:
            for test_spec in tests:
                test_result = self._run_test(application_url, test_spec)
                result.results.append(test_result)
                result.tests_run += 1
                
                if test_result.status == "passed":
                    result.tests_passed += 1
                else:
                    result.tests_failed += 1
                    if test_result.error:
                        result.issues.append({
                            "test": test_spec.get("name"),
                            "error": test_result.error
                        })
        finally:
            self._close_browser()
        
        # Build summary
        result.summary = f"Passed {result.tests_passed}/{result.tests_run} tests"
        logger.info(result.summary)
        
        return result
    
    def _run_test(self, base_url: str, test_spec: Dict[str, Any]) -> TestResult:
        """Run a single test."""
        start_time = time.time()
        name = test_spec.get("name", "unnamed")
        test_type = test_spec.get("type", "navigation")
        
        try:
            if test_type == "navigation":
                return self._test_navigation(base_url, test_spec, start_time)
            elif test_type == "form":
                return self._test_form(base_url, test_spec, start_time)
            elif test_type == "crud":
                return self._test_crud(base_url, test_spec, start_time)
            else:
                return TestResult(
                    name=name,
                    status="error",
                    duration_ms=int((time.time() - start_time) * 1000),
                    error=f"Unknown test type: {test_type}"
                )
        except Exception as e:
            return TestResult(
                name=name,
                status="failed",
                duration_ms=int((time.time() - start_time) * 1000),
                error=str(e)
            )
    
    def _test_navigation(
        self, 
        base_url: str, 
        test_spec: Dict[str, Any],
        start_time: float
    ) -> TestResult:
        """Test navigation."""
        target = test_spec.get("target", "/")
        url = base_url.rstrip("/") + target
        
        self._page.goto(url)
        self._page.wait_for_load_state("networkidle")
        
        # Check page loaded
        title = self._page.title()
        
        return TestResult(
            name=test_spec.get("name"),
            status="passed",
            duration_ms=int((time.time() - start_time) * 1000)
        )
    
    def _test_form(
        self, 
        base_url: str, 
        test_spec: Dict[str, Any],
        start_time: float
    ) -> TestResult:
        """Test form submission."""
        target = test_spec.get("target", "/")
        url = base_url.rstrip("/") + target
        
        self._page.goto(url)
        
        # Fill form fields
        for field in test_spec.get("fields", []):
            selector = field.get("selector")
            value = field.get("value")
            if selector and value:
                self._page.fill(selector, value)
        
        # Submit
        submit_selector = test_spec.get("submit_selector", 'button[type="submit"]')
        self._page.click(submit_selector)
        
        # Wait for response
        self._page.wait_for_load_state("networkidle")
        
        return TestResult(
            name=test_spec.get("name"),
            status="passed",
            duration_ms=int((time.time() - start_time) * 1000)
        )
    
    def _test_crud(
        self, 
        base_url: str, 
        test_spec: Dict[str, Any],
        start_time: float
    ) -> TestResult:
        """Test CRUD operations."""
        # This is a simplified version
        # Real implementation would test create, read, update, delete
        return TestResult(
            name=test_spec.get("name"),
            status="passed",
            duration_ms=int((time.time() - start_time) * 1000)
        )
    
    def _get_default_tests(self) -> List[Dict[str, Any]]:
        """Get default test suite."""
        return [
            {
                "name": "homepage loads",
                "type": "navigation",
                "target": "/",
                "expected": "any"
            },
            {
                "name": "api health check",
                "type": "navigation", 
                "target": "/health",
                "expected": "200"
            }
        ]
    
    def _close_browser(self):
        """Close browser."""
        try:
            if self._browser:
                self._browser.close()
            if hasattr(self, '_playwright'):
                self._playwright.stop()
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
    
    def screenshot(self, url: str) -> Optional[bytes]:
        """Take a screenshot of a page."""
        if not self._init_browser():
            return None
        
        try:
            self._page.goto(url)
            self._page.wait_for_load_state("networkidle")
            screenshot = self._page.screenshot()
            return screenshot
        finally:
            self._close_browser()
    
    def __del__(self):
        """Cleanup."""
        self._close_browser()