"""
Authentication Manager.

Handles Grok authentication with credential management and session persistence.
"""

import asyncio
from pathlib import Path
from typing import Optional

from playwright.async_api import Page

from grokfilmstudio.automation.browser import BrowserManager
from grokfilmstudio.config import settings


class AuthError(Exception):
    """Authentication failed."""

    pass


class AuthManager:
    """
    Manages Grok authentication flow.

    Features:
    - Credential injection from environment
    - Session persistence via storage state
    - Auto-reauthentication on expiry
    - Retry logic with backoff
    """

    def __init__(
        self,
        browser_manager: BrowserManager,
        username: Optional[str] = None,
        password: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initialize auth manager.

        Args:
            browser_manager: Browser manager instance
            username: Grok username (defaults to env)
            password: Grok password (defaults to env)
            base_url: Grok base URL (defaults to config)
        """
        self.browser = browser_manager
        self.username = username or settings.grok_username
        self.password = password or settings.grok_password
        self.base_url = base_url or settings.grok_base_url

        if not self.username or not self.password:
            raise ValueError(
                "Grok credentials required. Set GROK_USERNAME and GROK_PASSWORD in .env"
            )

    async def authenticate(self) -> bool:
        """
        Authenticate with Grok.

        Returns:
            True if authentication successful

        Raises:
            AuthError: If authentication fails
        """
        # Check if already authenticated
        if await self.is_authenticated():
            return True

        # Perform login
        return await self._perform_login()

    async def _perform_login(self) -> bool:
        """Perform the login flow."""
        page = None
        max_retries = settings.max_retries

        for attempt in range(max_retries):
            try:
                page = await self.browser.new_page()

                # Navigate to login page
                login_url = f"{self.base_url}/login"
                await page.goto(login_url, wait_until="networkidle")

                # Wait for and fill credentials
                await self._fill_credentials(page)

                # Submit form
                await self._submit_login(page)

                # Wait for navigation after login
                try:
                    await page.wait_for_url(
                        f"{self.base_url}/*", timeout=30000
                    )
                except asyncio.TimeoutError:
                    pass  # May already be on correct page

                # Verify login succeeded
                if await self._verify_login(page):
                    # Save session
                    await self.browser.save_storage_state()
                    return True

                raise AuthError("Login completed but verification failed")

            except AuthError:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(settings.retry_delay_seconds * (attempt + 1))

            except Exception as e:
                if attempt == max_retries - 1:
                    raise AuthError(f"Login failed after {max_retries} attempts: {e}")
                await asyncio.sleep(settings.retry_delay_seconds * (attempt + 1))

            finally:
                if page:
                    await page.close()

        return False

    async def _fill_credentials(self, page: Page) -> None:
        """Fill login credentials."""
        # Note: Selectors need to be updated based on actual Grok UI
        # These are example selectors

        # Try common username/email field selectors
        username_selectors = [
            'input[type="email"]',
            'input[name="email"]',
            'input[name="username"]',
            '#username',
            '#email',
        ]

        for selector in username_selectors:
            field = page.locator(selector).first
            if await field.count() > 0:
                await field.fill(self.username)
                break

        # Try common password field selectors
        password_selectors = [
            'input[type="password"]',
            'input[name="password"]',
            '#password',
        ]

        for selector in password_selectors:
            field = page.locator(selector).first
            if await field.count() > 0:
                await field.fill(self.password)
                break

    async def _submit_login(self, page: Page) -> None:
        """Submit the login form."""
        # Try common submit button selectors
        submit_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Sign In")',
            'button:has-text("Log In")',
            'button:has-text("Login")',
        ]

        for selector in submit_selectors:
            button = page.locator(selector).first
            if await button.count() > 0:
                await button.click()
                return

        # If no button found, try pressing Enter on password field
        password_field = page.locator('input[type="password"]').first
        if await password_field.count() > 0:
            await password_field.press("Enter")

    async def _verify_login(self, page: Page) -> bool:
        """Verify login succeeded."""
        # Check for indicators of successful login
        indicators = [
            # User profile/menu
            '[data-testid="user-menu"]',
            '[data-testid="user-profile"]',
            ".user-menu",
            ".profile-menu",
            # Grok-specific selectors
            '[data-testid="grok-input"]',
            '[data-testid="chat-input"]',
            # Logout link (means we're logged in)
            'a:has-text("Logout")',
            'button:has-text("Logout")',
        ]

        for selector in indicators:
            if await page.locator(selector).first.count() > 0:
                return True

        # Check we're not on login page
        current_url = page.url
        if "/login" in current_url or "/signin" in current_url:
            return False

        # Assume success if URL changed from login page
        return True

    async def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        if not self.browser.is_running:
            return False

        # Check if storage state exists and is valid
        if self.browser.storage_state.exists():
            # Create temporary page to test auth
            try:
                page = await self.browser.new_page()
                await page.goto(self.base_url, wait_until="networkidle", timeout=10000)

                # Quick check for logged-in indicators
                authenticated = await self._verify_login(page)
                await page.close()
                return authenticated

            except Exception:
                # Storage state may be expired
                return False

        return False

    async def logout(self) -> None:
        """Clear authentication."""
        await self.browser.clear_storage_state()

    async def refresh_session(self) -> bool:
        """
        Refresh the authentication session.

        Returns:
            True if refresh successful
        """
        await self.logout()
        return await self.authenticate()
