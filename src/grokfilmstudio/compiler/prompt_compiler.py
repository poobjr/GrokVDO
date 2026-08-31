"""
Prompt Compiler with DNA Locking System.

Compiles structured shot data into deterministic prompts using the formula:
[LOCKED: Character DNA] + [LOCKED: Location DNA] + [Action] + [Camera] + [LOCKED: World Style]

DNA Locking ensures consistency across multiple generations by:
1. Reusing exact character DNA from Production Bible
2. Reusing exact location DNA from Production Bible
3. Injecting context anchors for story continuity
4. Suppressing redundant descriptions to save tokens
"""

from dataclasses import dataclass
from typing import Optional

from grokfilmstudio.models.production_bible import (
    CharacterAnchor,
    ContextAnchor,
    LocationAnchor,
    ProductionBible,
    WorldAnchor,
)
from grokfilmstudio.models.shotlist import Shot


@dataclass
class DNAComponents:
    """Container for locked DNA components."""

    character_dna: list[str]
    location_dna: Optional[str]
    context_dna: Optional[str]
    world_style: str


class PromptCompiler:
    """
    Compiles shots into deterministic prompts with DNA locking.

    DNA Locking System:
    ┌─────────────────────────────────────────────────────────┐
    │  CHARACTER DNA (Locked)                                 │
    │  ─ Each character has fixed traits that never change    │
    │  ─ Example: "Asian woman, black hair, red jacket"       │
    ├─────────────────────────────────────────────────────────┤
    │  LOCATION DNA (Locked)                                  │
    │  ─ Each location has fixed visual elements              │
    │  ─ Example: "Exposed brick, large window, plants"       │
    ├─────────────────────────────────────────────────────────┤
    │  CONTEXT DNA (Locked)                                   │
    │  ─ Story context for continuity across shots            │
    │  ─ Example: "Night, raining, tense mood"                │
    ├─────────────────────────────────────────────────────────┤
    │  WORLD STYLE (Locked)                                   │
    │  ─ Global visual style for entire project               │
    │  ─ Example: "Cinematic 35mm, Kodak Portra 400"          │
    └─────────────────────────────────────────────────────────┘

    Prompt Formula (with DNA Locking):
    [Character DNA] + [Location DNA] + [Action] + [Camera] + [Context] + [World Style]
    """

    def __init__(self, production_bible: ProductionBible):
        """
        Initialize compiler with production bible.

        Args:
            production_bible: The source of truth for all DNA anchors
        """
        self.bible = production_bible

        # DNA cache for performance (avoid repeated lookups)
        self._character_dna_cache: dict[str, str] = {}
        self._location_dna_cache: dict[str, str] = {}

    def get_character_dna(self, character_id: str) -> Optional[str]:
        """
        Get the locked DNA prompt for a character.

        Uses cache to avoid repeated bible lookups.
        """
        # Check cache first
        if character_id in self._character_dna_cache:
            return self._character_dna_cache[character_id]

        # Lookup in bible
        character = self.bible.get_character(character_id)
        if character:
            dna = character.dna_prompt
            self._character_dna_cache[character_id] = dna
            return dna

        return None

    def get_location_dna(self, location_id: str) -> Optional[str]:
        """
        Get the locked DNA prompt for a location.

        Uses cache to avoid repeated bible lookups.
        """
        # Check cache first
        if location_id in self._location_dna_cache:
            return self._location_dna_cache[location_id]

        # Lookup in bible
        location = self.bible.get_location(location_id)
        if location:
            dna = location.dna_prompt
            self._location_dna_cache[location_id] = dna
            return dna

        return None

    def get_context_dna(self, context_id: str) -> Optional[str]:
        """Get the context DNA for story continuity."""
        context = self.bible.get_context(context_id)
        if not context:
            return None

        # Build context DNA from components
        parts = []
        if context.time_period:
            parts.append(context.time_period)
        if context.weather:
            parts.append(context.weather)
        if context.story_mood:
            parts.append(f"{context.story_mood} atmosphere")
        if context.continuity_notes:
            parts.append(context.continuity_notes)

        return ", ".join(parts) if parts else None

    def get_world_style(self) -> str:
        """Get the locked global style prompt."""
        if self.bible.world_anchors:
            return self.bible.world_anchors.style_prompt
        return "Cinematic"

    def get_all_dna_for_shot(
        self,
        shot: Shot,
        location_id: Optional[str] = None,
        context_id: Optional[str] = None,
    ) -> DNAComponents:
        """
        Get all locked DNA components for a shot.

        This is the core method that assembles all DNA anchors.

        Args:
            shot: The shot to compile
            location_id: Optional location anchor ID
            context_id: Optional context anchor ID

        Returns:
            DNAComponents with all locked DNA strings
        """
        # Get character DNA for all characters in shot
        character_dna = []
        for char_id in shot.character_ids:
            dna = self.get_character_dna(char_id)
            if dna:
                character_dna.append(dna)

        # Get location DNA if specified
        location_dna = None
        if location_id:
            location_dna = self.get_location_dna(location_id)

        # Get context DNA if specified
        context_dna = None
        if context_id:
            context_dna = self.get_context_dna(context_id)

        # Get world style (always included)
        world_style = self.get_world_style()

        return DNAComponents(
            character_dna=character_dna,
            location_dna=location_dna,
            context_dna=context_dna,
            world_style=world_style,
        )

    def compile_image_prompt(
        self,
        shot: Shot,
        location_id: Optional[str] = None,
        context_id: Optional[str] = None,
        use_smart_ordering: bool = True,
    ) -> str:
        """
        Compile a full image generation prompt with DNA locking.

        Smart Prompt Ordering (when use_smart_ordering=True):
        1. Character DNA (most important - face/body consistency)
        2. Location DNA (environment consistency)
        3. Action/Emotion (what's happening)
        4. Camera Specs (shot composition)
        5. Context DNA (time/weather/mood)
        6. World Style (global aesthetic)

        Args:
            shot: The shot to compile
            location_id: Optional location anchor ID for environment locking
            context_id: Optional context anchor ID for story continuity
            use_smart_ordering: Order prompt elements for best AI comprehension

        Returns:
            Compiled prompt string with all locked DNA
        """
        # Get all DNA components
        dna = self.get_all_dna_for_shot(shot, location_id, context_id)

        parts = []

        # 1. Character DNA (locked - never changes for this character)
        if dna.character_dna:
            parts.append(", ".join(dna.character_dna))

        # 2. Location DNA (locked - same location = same DNA)
        if dna.location_dna:
            parts.append(dna.location_dna)

        # 3. Action/Emotion
        if shot.action_description:
            parts.append(shot.action_description)

        # 4. Camera Specs
        camera_str = shot.camera_specs.format_for_prompt()
        if camera_str:
            parts.append(camera_str)

        # 5. Context DNA (story continuity)
        if dna.context_dna:
            parts.append(dna.context_dna)

        # 6. World Style (locked - same for entire project)
        if dna.world_style and dna.world_style != "Cinematic":
            parts.append(dna.world_style)

        # Join all parts
        prompt = ", ".join(parts)

        # Clean up whitespace
        prompt = " ".join(prompt.split())

        return prompt

    def compile_motion_prompt(
        self,
        shot: Shot,
    ) -> str:
        """
        Compile a motion-focused prompt for video generation.

        This is used during image-to-video conversion.
        It focuses ONLY on motion, suppressing character/location descriptions
        to avoid model confusion and save tokens.

        Token Saving Strategy:
        - NO character descriptions (already in keyframe)
        - NO location descriptions (already in keyframe)
        - ONLY motion commands
        """
        parts = []

        # Motion from camera specs
        if shot.camera_specs.motion and shot.camera_specs.motion != "Static":
            parts.append(shot.camera_specs.motion)

        # Motion from action (if it implies movement)
        action = shot.action_description.lower() if shot.action_description else ""
        motion_keywords = [
            "turn",
            "walk",
            "run",
            "look",
            "reach",
            "grab",
            "fall",
            "rise",
            "move",
            "pan",
            "tilt",
            "zoom",
            "track",
            "push",
            "pull",
        ]
        for keyword in motion_keywords:
            if keyword in action:
                # Extract motion-focused part of action
                parts.append(shot.action_description)
                break

        # If no motion detected, use minimal static prompt
        if not parts:
            return "Subtle natural movement, breathing, micro-expressions"

        return ", ".join(parts)

    def compile_video_prompt(
        self,
        shot: Shot,
        location_id: Optional[str] = None,
        context_id: Optional[str] = None,
    ) -> str:
        """
        Compile full video generation prompt with DNA locking.

        Format:
            [Image Prompt with locked DNA] -- Motion: [Motion Prompt]

        Args:
            shot: The shot to compile
            location_id: Optional location anchor ID
            context_id: Optional context anchor ID

        Returns:
            Full video prompt string
        """
        image_prompt = self.compile_image_prompt(shot, location_id, context_id)
        motion_prompt = self.compile_motion_prompt(shot)

        return f"{image_prompt} -- Motion: {motion_prompt}"

    def compile_batch_prompts(
        self,
        shots: list[Shot],
        location_id: Optional[str] = None,
        context_id: Optional[str] = None,
    ) -> list[tuple[str, str]]:
        """
        Compile prompts for a batch of shots efficiently.

        This method is optimized for generating multiple shots in sequence.
        It reuses DNA lookups across shots for better performance.

        Args:
            shots: List of shots to compile
            location_id: Optional location anchor (same for all shots)
            context_id: Optional context anchor (same for all shots)

        Returns:
            List of (shot_id, compiled_prompt) tuples
        """
        results = []

        # Pre-load DNA cache for efficiency
        for shot in shots:
            for char_id in shot.character_ids:
                if char_id not in self._character_dna_cache:
                    self.get_character_dna(char_id)

        # Compile each shot
        for shot in shots:
            prompt = self.compile_image_prompt(shot, location_id, context_id)
            results.append((shot.shot_id, prompt))

        return results

    def validate_prompt_length(
        self,
        prompt: str,
        max_length: int = 500,
        warn_length: int = 400,
    ) -> tuple[bool, list[str]]:
        """
        Validate prompt length and return warnings.

        Args:
            prompt: The prompt to validate
            max_length: Maximum allowed length
            warn_length: Length at which to warn

        Returns:
            Tuple of (is_valid, list of warnings)
        """
        warnings = []

        if len(prompt) > max_length:
            warnings.append(
                f"Prompt exceeds maximum length ({len(prompt)}/{max_length})"
            )
            return False, warnings

        if len(prompt) > warn_length:
            warnings.append(
                f"Prompt is approaching maximum length ({len(prompt)}/{max_length})"
            )

        return True, warnings

    def detect_prompt_bloat(self, prompt: str) -> list[str]:
        """
        Detect common prompt bloat patterns.

        Bloat wastes tokens and can cause inconsistency.
        This method identifies filler words that should be removed.
        """
        warnings = []

        bloat_patterns = [
            "highly detailed",
            "intricate",
            "beautiful",
            "stunning",
            "amazing",
            "incredible",
            "masterpiece",
            "award-winning",
            "professional",
            "high quality",
            "4k",
            "8k",
        ]

        prompt_lower = prompt.lower()
        for pattern in bloat_patterns:
            if pattern in prompt_lower:
                warnings.append(f"Remove filler phrase: '{pattern}'")

        # Check for repeated character descriptions
        if prompt.count(",") > 15:
            warnings.append(
                "Prompt may be too complex (>15 comma-separated clauses)"
            )

        # Check for redundant descriptors
        redundant = ["very", "extremely", "really", "quite"]
        for word in redundant:
            if f" {word} " in prompt_lower:
                warnings.append(f"Remove redundant intensifier: '{word}'")

        return warnings

    def check_dna_consistency(
        self,
        shot: Shot,
        location_id: Optional[str] = None,
    ) -> list[str]:
        """
        Check if DNA is consistent with the production bible.

        This validates that:
        - All character IDs exist in the bible
        - Location ID exists (if provided)
        - No conflicting DNA elements

        Args:
            shot: The shot to validate
            location_id: Optional location anchor ID

        Returns:
            List of consistency errors
        """
        errors = []

        # Check all characters exist
        for char_id in shot.character_ids:
            if not self.bible.get_character(char_id):
                errors.append(f"Character '{char_id}' not found in production bible")

        # Check location exists
        if location_id and not self.bible.get_location(location_id):
            errors.append(f"Location '{location_id}' not found in production bible")

        return errors

    def compile_and_validate(
        self,
        shot: Shot,
        location_id: Optional[str] = None,
        context_id: Optional[str] = None,
    ) -> tuple[str, list[str], list[str]]:
        """
        Compile a prompt and run all validations.

        This is the main method for prompt compilation with full validation.

        Args:
            shot: The shot to compile
            location_id: Optional location anchor ID
            context_id: Optional context anchor ID

        Returns:
            Tuple of (prompt, errors, warnings)
        """
        errors = []
        warnings = []

        # Check DNA consistency
        dna_errors = self.check_dna_consistency(shot, location_id)
        errors.extend(dna_errors)

        # Compile prompt
        prompt = self.compile_image_prompt(shot, location_id, context_id)

        # Validate length
        is_valid, length_warnings = self.validate_prompt_length(prompt)
        warnings.extend(length_warnings)

        # Detect bloat
        bloat_warnings = self.detect_prompt_bloat(prompt)
        warnings.extend(bloat_warnings)

        # Check for missing character DNA
        if shot.character_ids:
            missing = [
                cid for cid in shot.character_ids if not self.get_character_dna(cid)
            ]
            if missing:
                errors.append(f"Missing character DNA for: {', '.join(missing)}")

        return prompt, errors, warnings

    def get_dna_summary(self) -> str:
        """
        Get a human-readable summary of all locked DNA.

        Useful for debugging and verification.
        """
        return self.bible.get_all_dna_summary()
