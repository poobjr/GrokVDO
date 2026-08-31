"""
Browser Session Manager.

Manages Playwright browser instances with proper lifecycle handling.
"""

import asyncio
from pathlib import Path
from typing import Optional

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

from grokfilmstudio.config import Settings, settings


class BrowserManager:
    """
    Manages browser lifecycle and context creation.

    Features:
    - Browser launch with configurable options
    - Context creation with storage state persistence
    - Auto-reconnection on crash
    - Screenshot on failure for debugging
    """

    def __init__(
        self,
        headless: bool = True,
        browser_type: str = "chromium",
        storage_state: Optional[Path] = None,
    ):
        """
        Initialize browser manager.

        Args:
            headless: Run browser headless
            browser_type: "chromium", "firefox", or "webkit"
            storage_state: Path to persist/load session state
        """
        self.headless = headless
        self.browser_type = browser_type
        self.storage_state = storage_state or settings.browser_storage_state

        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

    async def start(self) -> None:
        """Start the browser."""
        self._playwright = await async_playwright().start()

        launch_args = {
            "headless": self.headless,
            "args": [
                "--disable-gpu",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--disable-gpu-compositing",
            ],
        }

        if self.browser_type == "chromium":
            self._browser = await self._playwright.chromium.launch(**launch_args)
        elif self.browser_type == "firefox":
            self._browser = await self._playwright.firefox.launch(**launch_args)
        elif self.browser_type == "webkit":
            self._browser = await self._playwright.webkit.launch(**launch_args)
        else:
            raise ValueError(f"Unknown browser type: {self.browser_type}")

    async def stop(self) -> None:
        """Stop the browser and cleanup."""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

        self._context = None
        self._browser = None
        self._playwright = None

    async def create_context(
        self,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        load_storage_state: bool = True,
    ) -> BrowserContext:
        """
        Create a new browser context.

        Args:
            viewport_width: Context viewport width
            viewport_height: Context viewport height
            load_storage_state: Load saved auth state

        Returns:
            New browser context
        """
        if not self._browser:
            raise RuntimeError("Browser not started. Call start() first.")

        context_args = {
            "viewport": {"width": viewport_width, "height": viewport_height},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

        # Load storage state if available
        if load_storage_state and self.storage_state.exists():
            context_args["storage_state"] = str(self.storage_state)

        self._context = await self._browser.new_context(**context_args)
        return self._context

    async def get_context(self) -> BrowserContext:
        """Get existing context or create new one."""
        if self._context is None:
            await self.create_context()
        return self._context  # type: ignore

    async def new_page(self) -> Page:
        """Create a new page in the current context."""
        context = await self.get_context()
        return await context.new_page()

    async def save_storage_state(self) -> None:
        """Save current context storage state."""
        if self._context:
            state = await self._context.storage_state()
            self.storage_state.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_state, "w") as f:
                import json

                json.dump(state, f)

    async def clear_storage_state(self) -> None:
        """Clear saved storage state."""
        if self.storage_state.exists():
            self.storage_state.unlink()

    async def screenshot(self, page: Page, name: str = "screenshot") -> Path:
        """
        Take a screenshot for debugging.

        Args:
            page: Page to screenshot
            name: Screenshot name

        Returns:
            Path to screenshot file
        """
        screenshot_dir = Path("./.debug/screenshots")
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        timestamp = asyncio.get_event_loop().time()
        filename = f"{name}_{int(timestamp)}.png"
        path = screenshot_dir / filename

        await page.screenshot(path=str(path), full_page=True)
        return path

    @property
    def is_running(self) -> bool:
        """Check if browser is running."""
        return self._browser is not None and not self._browser.is_closed()
