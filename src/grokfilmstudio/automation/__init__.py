"""
Grok Browser Automation.

Playwright-based browser automation for Grok video generation.
"""

from grokfilmstudio.automation.browser import BrowserManager
from grokfilmstudio.automation.auth import AuthManager
from grokfilmstudio.automation.grok_controller import GrokController

__all__ = ["BrowserManager", "AuthManager", "GrokController"]
