"""
ElevenLabs TTS Integration.

Generates character dialogue using ElevenLabs API.
"""

import asyncio
from pathlib import Path
from typing import Optional

import aiohttp

from grokfilmstudio.config import settings
from grokfilmstudio.models.production_bible import AudioAnchor


class ElevenLabsError(Exception):
    """ElevenLabs API error."""

    pass


class ElevenLabsClient:
    """
    Client for ElevenLabs Text-to-Speech API.

    Features:
    - Async text-to-speech generation
    - Voice selection by character
    - Batch generation for efficiency
    - Automatic retry on failure
    """

    BASE_URL = "https://api.elevenlabs.io/v1"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize ElevenLabs client.

        Args:
            api_key: API key (defaults to ELEVENLABS_API_KEY env var)
        """
        self.api_key = api_key or settings.elevenlabs_api_key

        if not self.api_key:
            raise ValueError(
                "ElevenLabs API key required. Set ELEVENLABS_API_KEY in .env"
            )

        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "xi-api-key": self.api_key,
                    "Content-Type": "application/json",
                }
            )
        return self._session

    async def close(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def generate_speech(
        self,
        text: str,
        voice_id: str,
        output_path: Path,
        model_id: str = "eleven_monolingual_v1",
        stability: float = 0.5,
        similarity_boost: float = 0.75,
    ) -> Path:
        """
        Generate speech from text.

        Args:
            text: Text to synthesize
            voice_id: Voice ID to use
            output_path: Output file path
            model_id: Model ID to use
            stability: Voice stability (0-1)
            similarity_boost: Voice similarity boost (0-1)

        Returns:
            Path to generated audio file
        """
        session = await self._get_session()

        url = f"{self.BASE_URL}/text-to-speech/{voice_id}"

        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
            },
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_data = await response.json()
                        raise ElevenLabsError(
                            f"API error {response.status}: {error_data}"
                        )

                    # Write audio content
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, "wb") as f:
                        f.write(await response.read())

                    return output_path

            except aiohttp.ClientError as e:
                if attempt == max_retries - 1:
                    raise ElevenLabsError(f"Request failed after {max_retries} attempts: {e}")
                await asyncio.sleep(2**attempt)

        raise ElevenLabsError("Failed to generate speech")

    async def generate_character_dialogue(
        self,
        text: str,
        character_id: str,
        audio_anchors: list[AudioAnchor],
        output_dir: Path,
    ) -> Optional[Path]:
        """
        Generate dialogue for a character.

        Args:
            text: Dialogue text
            character_id: Character ID
            audio_anchors: List of audio anchors
            output_dir: Output directory

        Returns:
            Path to generated audio file
        """
        # Find voice for character
        voice_id = None
        voice_name = None

        for anchor in audio_anchors:
            if anchor.character_id == character_id:
                voice_id = anchor.voice_id
                voice_name = anchor.voice_name
                break

        if not voice_id:
            raise ValueError(f"No voice configured for character {character_id}")

        # Generate filename
        safe_name = "".join(c for c in text[:30] if c.isalnum() or c in " -_").strip()
        safe_name = safe_name.replace(" ", "_") or "dialogue"

        output_path = output_dir / f"{safe_name}_{character_id}.mp3"

        return await self.generate_speech(text, voice_id, output_path)

    async def generate_batch(
        self,
        texts: list[tuple[str, str, Path]],  # (text, voice_id, output_path)
        concurrency: int = 3,
    ) -> list[tuple[Path, Optional[Exception]]]:
        """
        Generate speech for multiple texts in parallel.

        Args:
            texts: List of (text, voice_id, output_path) tuples
            concurrency: Maximum concurrent requests

        Returns:
            List of (output_path, error) tuples
        """
        semaphore = asyncio.Semaphore(concurrency)

        async def generate_with_semaphore(text, voice_id, output_path):
            async with semaphore:
                try:
                    result = await self.generate_speech(text, voice_id, output_path)
                    return (result, None)
                except Exception as e:
                    return (output_path, e)

        tasks = [
            generate_with_semaphore(text, voice_id, path)
            for text, voice_id, path in texts
        ]

        return await asyncio.gather(*tasks)

    async def list_voices(self) -> list[dict]:
        """
        List available voices.

        Returns:
            List of voice dictionaries
        """
        session = await self._get_session()
        url = f"{self.BASE_URL}/voices"

        async with session.get(url) as response:
            if response.status != 200:
                raise ElevenLabsError(f"Failed to list voices: {response.status}")

            data = await response.json()
            return data.get("voices", [])

    async def get_voice_info(self, voice_id: str) -> dict:
        """
        Get voice information.

        Args:
            voice_id: Voice ID

        Returns:
            Voice information dictionary
        """
        session = await self._get_session()
        url = f"{self.BASE_URL}/voices/{voice_id}"

        async with session.get(url) as response:
            if response.status != 200:
                raise ElevenLabsError(f"Voice not found: {voice_id}")

            return await response.json()
