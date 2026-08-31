"""
Grok Controller.

High-level controller for Grok video generation operations.
"""

import asyncio
from pathlib import Path
from typing import Optional

from grokfilmstudio.automation.auth import AuthManager
from grokfilmstudio.automation.browser import BrowserManager
from grokfilmstudio.config import settings
from grokfilmstudio.models.shotlist import Shot


class GrokGenerationError(Exception):
    """Grok generation failed."""

    pass


class GrokController:
    """
    Controls Grok video generation workflow.

    Operations:
    - Generate image from prompt
    - Generate video from image (image-to-video)
    - Upload reference images
    - Download generated assets
    """

    def __init__(
        self,
        browser_manager: BrowserManager,
        auth_manager: Optional[AuthManager] = None,
    ):
        """
        Initialize Grok controller.

        Args:
            browser_manager: Browser manager instance
            auth_manager: Auth manager instance (creates one if not provided)
        """
        self.browser = browser_manager
        self.auth = auth_manager or AuthManager(browser_manager)
        self.base_url = settings.grok_base_url

    async def ensure_authenticated(self) -> None:
        """Ensure we are authenticated, login if needed."""
        if not await self.auth.is_authenticated():
            await self.auth.authenticate()

    async def generate_image(
        self,
        prompt: str,
        reference_image: Optional[Path] = None,
        aspect_ratio: str = "16:9",
        timeout: int = 60,
    ) -> Optional[Path]:
        """
        Generate an image from a prompt.

        Args:
            prompt: The generation prompt
            reference_image: Optional reference image for img2img
            aspect_ratio: Target aspect ratio
            timeout: Generation timeout in seconds

        Returns:
            Path to generated image or None if failed
        """
        await self.ensure_authenticated()
        page = await self.browser.new_page()

        try:
            # Navigate to Grok
            await page.goto(self.base_url, wait_until="networkidle")

            # Enter prompt
            await self._enter_prompt(page, prompt)

            # Upload reference image if provided
            if reference_image:
                await self._upload_reference_image(page, reference_image)

            # Set aspect ratio
            await self._set_aspect_ratio(page, aspect_ratio)

            # Trigger generation
            await self._trigger_generation(page)

            # Wait for completion
            image_path = await self._wait_for_image(page, timeout)

            return image_path

        except Exception as e:
            raise GrokGenerationError(f"Image generation failed: {e}")

        finally:
            await page.close()

    async def generate_video(
        self,
        image_path: Path,
        motion_prompt: Optional[str] = None,
        duration: float = 3.0,
        timeout: int = 300,
    ) -> Optional[Path]:
        """
        Generate video from an image (image-to-video).

        Args:
            image_path: Path to source keyframe image
            motion_prompt: Motion description prompt
            duration: Target duration in seconds
            timeout: Generation timeout in seconds

        Returns:
            Path to generated video or None if failed
        """
        await self.ensure_authenticated()
        page = await self.browser.new_page()

        try:
            # Navigate to video generation
            await page.goto(f"{self.base_url}/video", wait_until="networkidle")

            # Upload keyframe image
            await self._upload_keyframe(page, image_path)

            # Enter motion prompt
            if motion_prompt:
                await self._enter_motion_prompt(page, motion_prompt)

            # Set duration
            await self._set_duration(page, duration)

            # Trigger generation
            await self._trigger_video_generation(page)

            # Wait for completion
            video_path = await self._wait_for_video(page, timeout)

            return video_path

        except Exception as e:
            raise GrokGenerationError(f"Video generation failed: {e}")

        finally:
            await page.close()

    async def generate_shot(
        self,
        shot: Shot,
        project_dir: Path,
    ) -> tuple[Optional[Path], Optional[Path]]:
        """
        Generate complete shot (keyframe + video).

        Args:
            shot: Shot to generate
            project_dir: Project directory for saving assets

        Returns:
            Tuple of (keyframe_path, video_path)
        """
        keyframe_path = None
        video_path = None

        # Generate keyframe
        if shot.compiled_prompt:
            keyframe_path = await self.generate_image(
                prompt=shot.compiled_prompt,
                reference_image=self._get_reference_image(shot),
                timeout=60,
            )
            if keyframe_path:
                # Move to project directory
                dest = project_dir / "keyframes" / f"{shot.shot_id}.png"
                dest.parent.mkdir(parents=True, exist_ok=True)
                keyframe_path.rename(dest)
                shot.keyframe_path = str(dest)

        # Generate video from keyframe
        if keyframe_path:
            motion_prompt = shot.motion_prompt or self._extract_motion(shot)
            video_path = await self.generate_video(
                image_path=keyframe_path,
                motion_prompt=motion_prompt,
                duration=shot.duration_seconds,
                timeout=settings.video_gen_timeout,
            )
            if video_path:
                # Move to project directory
                dest = project_dir / "renders" / f"{shot.shot_id}.mp4"
                dest.parent.mkdir(parents=True, exist_ok=True)
                video_path.rename(dest)
                shot.video_path = str(dest)

        return keyframe_path, video_path

    def _get_reference_image(self, shot: Shot) -> Optional[Path]:
        """Get reference image for a shot."""
        # Return first character's reference image
        if shot.character_ids:
            # This would look up from production bible
            # For now, return None - reference injection needs bible access
            pass
        return None

    def _extract_motion(self, shot: Shot) -> str:
        """Extract motion description from shot."""
        if shot.camera_specs.motion != "Static":
            return shot.camera_specs.motion
        return "Subtle natural movement"

    # Internal methods for page interactions
    # Note: These selectors need to be updated for actual Grok UI

    async def _enter_prompt(self, page, prompt: str) -> None:
        """Enter prompt into Grok input."""
        # Placeholder - update with actual Grok selectors
        input_field = page.locator('textarea[placeholder*="prompt"], textarea[placeholder*="Describe"], input[type="text"]').first
        if await input_field.count() > 0:
            await input_field.fill(prompt)

    async def _upload_reference_image(self, page, image_path: Path) -> None:
        """Upload reference image."""
        # Placeholder - update with actual Grok selectors
        file_input = page.locator('input[type="file"]').first
        if await file_input.count() > 0:
            await file_input.set_input_files(str(image_path))

    async def _set_aspect_ratio(self, page, aspect_ratio: str) -> None:
        """Set aspect ratio."""
        # Placeholder - update with actual Grok selectors
        select = page.locator(f'select option[value="{aspect_ratio}"], button:has-text("{aspect_ratio}")').first
        if await select.count() > 0:
            await select.click()

    async def _trigger_generation(self, page) -> None:
        """Trigger image generation."""
        # Placeholder - update with actual Grok selectors
        button = page.locator('button:has-text("Generate"), button:has-text("Create"), button[type="submit"]').first
        if await button.count() > 0:
            await button.click()

    async def _wait_for_image(self, page, timeout: int) -> Optional[Path]:
        """Wait for image generation to complete."""
        # Placeholder - update with actual Grok selectors
        try:
            image = await page.locator('img.generation-result, [data-testid="result-image"]').first.wait_for(
                state="visible", timeout=timeout * 1000
            )
            # Download logic would go here
            return None
        except asyncio.TimeoutError:
            return None

    async def _upload_keyframe(self, page, image_path: Path) -> None:
        """Upload keyframe for video generation."""
        file_input = page.locator('input[type="file"]').first
        if await file_input.count() > 0:
            await file_input.set_input_files(str(image_path))

    async def _enter_motion_prompt(self, page, prompt: str) -> None:
        """Enter motion prompt."""
        input_field = page.locator('textarea[placeholder*="motion"], textarea[placeholder*="describe motion"]').first
        if await input_field.count() > 0:
            await input_field.fill(prompt)

    async def _set_duration(self, page, duration: float) -> None:
        """Set video duration."""
        # Placeholder - update with actual Grok selectors
        pass

    async def _trigger_video_generation(self, page) -> None:
        """Trigger video generation."""
        button = page.locator('button:has-text("Generate Video"), button:has-text("Create Video"), button:has-text("Animate")').first
        if await button.count() > 0:
            await button.click()

    async def _wait_for_video(self, page, timeout: int) -> Optional[Path]:
        """Wait for video generation to complete."""
        try:
            await page.locator('video, [data-testid="video-result"]').first.wait_for(
                state="visible", timeout=timeout * 1000
            )
            # Download logic would go here
            return None
        except asyncio.TimeoutError:
            return None
