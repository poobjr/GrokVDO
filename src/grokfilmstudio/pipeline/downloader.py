"""
Asset Downloader.

Manages downloading of generated images and videos from Grok.
"""

import asyncio
from pathlib import Path
from typing import Optional

from playwright.async_api import Download, Page


class AssetDownloader:
    """
    Manages asset downloads from browser.

    Features:
    - Automatic download handling
    - Progress tracking
    - Retry on failure
    - Organized storage
    """

    def __init__(
        self,
        download_dir: Path,
        accept_patterns: Optional[list[str]] = None,
    ):
        """
        Initialize downloader.

        Args:
            download_dir: Directory to save downloads
            accept_patterns: File patterns to accept (e.g., ["*.mp4", "*.png"])
        """
        self.download_dir = download_dir
        self.accept_patterns = accept_patterns or ["*.png", "*.jpg", "*.mp4", "*.webm"]

        self.download_dir.mkdir(parents=True, exist_ok=True)

    def configure_page(self, page: Page) -> None:
        """
        Configure page for download handling.

        Args:
            page: Playwright page to configure
        """

        def on_download(download: Download) -> None:
            """Handle download event."""
            suggested_path = self.download_dir / download.suggested_filename

            # Check if file type is accepted
            if not self._is_accepted(download.suggested_filename):
                return

            # Save the file
            download.save_as(suggested_path)

        page.on("download", on_download)

    def _is_accepted(self, filename: str) -> bool:
        """Check if filename matches accepted patterns."""
        for pattern in self.accept_patterns:
            if Path(filename).match(pattern):
                return True
        return False

    async def download_from_element(
        self,
        page: Page,
        selector: str,
        save_as: str,
        timeout: int = 30000,
    ) -> Optional[Path]:
        """
        Download file by clicking an element.

        Args:
            page: Playwright page
            selector: Element selector (button, link, etc.)
            save_as: Filename to save as
            timeout: Download timeout in ms

        Returns:
            Path to downloaded file or None
        """
        save_path = self.download_dir / save_as

        try:
            # Wait for download
            async with page.expect_download(timeout=timeout) as download_info:
                element = page.locator(selector).first
                await element.click()

            download = await download_info.value
            await download.save_as(save_path)

            return save_path

        except Exception as e:
            print(f"Download failed: {e}")
            return None

    async def wait_for_download(
        self,
        page: Page,
        timeout: int = 60000,
    ) -> Optional[Download]:
        """
        Wait for a download to start.

        Args:
            page: Playwright page
            timeout: Timeout in ms

        Returns:
            Download object or None
        """
        try:
            async with page.expect_download(timeout=timeout) as download_info:
                pass  # Just wait for the event
            return await download_info.value
        except asyncio.TimeoutError:
            return None

    def organize_by_project(
        self,
        project_id: str,
        shot_id: str,
        asset_type: str,  # "keyframe" or "video"
    ) -> Path:
        """
        Get organized path for an asset.

        Args:
            project_id: Project ID
            shot_id: Shot ID
            asset_type: "keyframe" or "video"

        Returns:
            Path for the asset
        """
        base = Path(self.download_dir) / project_id

        if asset_type == "keyframe":
            dest_dir = base / "keyframes"
        else:
            dest_dir = base / "renders"

        dest_dir.mkdir(parents=True, exist_ok=True)

        ext = ".png" if asset_type == "keyframe" else ".mp4"
        return dest_dir / f"{shot_id}{ext}"
