"""
Storyboard Parser with DNA Locking Support.

Parses high-level script inputs into structured shotlists with:
- Scene/Shot breakdown
- Character/Location/Context extraction
- Automatic camera inference
- Storyboard panel generation

Supports multiple input formats:
- Synopsis (paragraph form)
- Treatment (scene-by-scene)
- Full script (screenplay format)
- Storyboard description (panel-by-panel)
"""

import re
from dataclasses import dataclass, field
from typing import Optional

from grokfilmstudio.models.production_bible import (
    ContextAnchor,
    LocationAnchor,
    ProductionBible,
)
from grokfilmstudio.models.shotlist import CameraSpecs, Shot, Shotlist, ShotStatus


@dataclass
class StoryboardPanel:
    """
    A single storyboard panel with all visual elements.

    This represents one "shot" in the storyboard before conversion
    to the final Shot data structure.
    """

    panel_number: int
    scene_number: int
    description: str
    characters: list[str] = field(default_factory=list)
    location: Optional[str] = None
    time_of_day: Optional[str] = None
    camera_shot_size: Optional[str] = None
    camera_angle: Optional[str] = None
    camera_motion: Optional[str] = None
    dialogue: Optional[str] = None
    sound_effects: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class Scene:
    """
    A scene containing multiple storyboard panels.

    Groups panels that share the same location/context.
    """

    scene_number: int
    location_name: str
    time_of_day: str
    description: str
    panels: list[StoryboardPanel] = field(default_factory=list)
    context_mood: Optional[str] = None


class ScriptParser:
    """
    Advanced parser for scripts and storyboards.

    Features:
    - Multi-format support (synopsis, treatment, script, storyboard)
    - Automatic character/location extraction
    - Camera inference from action descriptions
    - DNA locking support for consistent generation
    - Batch shot creation for efficient processing

    Parser Flow:
    1. Parse input → StoryboardPanels
    2. Extract/Match characters, locations, contexts
    3. Infer camera directions
    4. Convert to Shotlist with DNA references
    """

    # Common camera shot sizes
    SHOT_SIZES = {
        "extreme close-up": "Extreme Close-up",
        "ecu": "Extreme Close-up",
        "close-up": "Close-up",
        "cu": "Close-up",
        "medium close-up": "Medium Close-up",
        "mcu": "Medium Close-up",
        "medium": "Medium",
        "med": "Medium",
        "medium wide": "Medium Wide",
        "mws": "Medium Wide",
        "wide": "Wide",
        "full shot": "Full Shot",
        "fs": "Full Shot",
        "establishing": "Establishing",
        "long shot": "Wide",
        "ls": "Wide",
    }

    # Common camera angles
    CAMERA_ANGLES = {
        "eye level": "Eye Level",
        "low angle": "Low Angle",
        "high angle": "High Angle",
        "overhead": "Overhead",
        "bird's eye": "Overhead",
        "worm's eye": "Low Angle",
        "dutch angle": "Dutch Angle",
        "tilted": "Dutch Angle",
        "over the shoulder": "Over the Shoulder",
        "ots": "Over the Shoulder",
        "point of view": "POV",
        "pov": "POV",
        "two shot": "Medium",
        "profile": "Eye Level",
    }

    # Common camera motions
    CAMERA_MOTIONS = {
        "static": "Static",
        "still": "Static",
        "pan left": "Pan Left",
        "pan right": "Pan Right",
        "tilt up": "Tilt Up",
        "tilt down": "Tilt Down",
        "zoom in": "Slow Zoom In",
        "zoom out": "Slow Zoom Out",
        "push in": "Push In",
        "pull out": "Pull Out",
        "track": "Tracking",
        "tracking": "Tracking",
        "dolly": "Dolly",
        "dolly in": "Dolly In",
        "dolly out": "Dolly Out",
        "handheld": "Handheld",
        "steady": "Steadycam",
        "steadicam": "Steadycam",
        "crane": "Crane Shot",
        "drone": "Aerial Shot",
    }

    # Time of day indicators
    TIME_OF_DAY = {
        "morning": "Morning",
        "dawn": "Dawn",
        "sunrise": "Dawn",
        "day": "Day",
        "afternoon": "Afternoon",
        "noon": "Noon",
        "evening": "Evening",
        "dusk": "Dusk",
        "sunset": "Dusk",
        "night": "Night",
        "midnight": "Midnight",
        "later": "Later",
        "continuous": "Continuous",
        "moments later": "Moments Later",
    }

    def __init__(
        self,
        production_bible: ProductionBible,
        default_shot_duration: float = 3.0,
        auto_create_anchors: bool = True,
    ):
        """
        Initialize parser.

        Args:
            production_bible: Reference bible for character/location matching
            default_shot_duration: Default duration per shot in seconds
            auto_create_anchors: If True, auto-create anchors for new elements
        """
        self.bible = production_bible
        self.default_duration = default_shot_duration
        self.auto_create_anchors = auto_create_anchors

        # Track extracted elements
        self._extracted_locations: dict[str, LocationAnchor] = {}
        self._extracted_contexts: dict[str, ContextAnchor] = {}

    def parse_to_storyboard(
        self,
        input_text: str,
        format: str = "auto",
    ) -> list[Scene]:
        """
        Parse input into storyboard panels grouped by scene.

        This is the first pass - creates intermediate StoryboardPanel
        structures before final conversion to Shotlist.

        Args:
            input_text: The input text to parse
            format: "auto", "synopsis", "treatment", "script", or "storyboard"

        Returns:
            List of Scene objects containing panels
        """
        if format == "auto":
            format = self._detect_format(input_text)

        if format == "synopsis":
            return self._parse_synopsis_to_scenes(input_text)
        elif format == "treatment":
            return self._parse_treatment_to_scenes(input_text)
        elif format == "script":
            return self._parse_script_to_scenes(input_text)
        elif format == "storyboard":
            return self._parse_storyboard_format(input_text)
        else:
            raise ValueError(f"Unknown format: {format}")

    def _detect_format(self, text: str) -> str:
        """Auto-detect input format based on content patterns."""
        text_lower = text.lower()

        # Check for screenplay format
        if re.search(r"^(INT|EXT)\.", text, re.MULTILINE | re.IGNORECASE):
            return "script"

        # Check for treatment format
        if re.search(r"SCENE\s*\d+|Scene\s*\d+", text, re.IGNORECASE):
            return "treatment"

        # Check for storyboard panel format
        if re.search(r"PANEL\s*\d+|Panel\s*\d+|SHOT\s*\d+|Shot\s*\d+", text):
            return "storyboard"

        # Default to synopsis
        return "synopsis"

    def _parse_synopsis_to_scenes(self, synopsis: str) -> list[Scene]:
        """Parse synopsis into scenes and panels."""
        scenes = []

        # Try to split into "beats" or paragraphs
        paragraphs = [p.strip() for p in synopsis.split("\n\n") if p.strip()]

        if len(paragraphs) <= 1:
            # Single paragraph - treat as one scene
            paragraphs = [synopsis]

        scene_num = 1
        for para in paragraphs:
            # Create a scene for each paragraph
            scene = Scene(
                scene_number=scene_num,
                location_name="Generic",
                time_of_day="Unknown",
                description=para[:200],
            )

            # Split into sentences for panels
            sentences = re.split(r"(?<=[.!?])\s+", para)
            panel_num = 1
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence:
                    panel = StoryboardPanel(
                        panel_number=panel_num,
                        scene_number=scene_num,
                        description=sentence,
                    )
                    scene.panels.append(panel)
                    panel_num += 1

            scenes.append(scene)
            scene_num += 1

        return scenes

    def _parse_treatment_to_scenes(self, treatment: str) -> list[Scene]:
        """Parse treatment format into scenes."""
        scenes = []

        # Split by scene headers
        scene_pattern = r"(?:SCENE\s*(\d+)|^(INT|EXT)\.\s*[^-]+-\s*(?:DAY|NIGHT))"

        parts = re.split(scene_pattern, treatment, flags=re.MULTILINE | re.IGNORECASE)

        scene_num = 1
        i = 0
        while i < len(parts):
            part = parts[i].strip()

            # Skip empty parts and match groups
            if not part or part.isdigit() or part.upper() in ["INT", "EXT"]:
                if part.isdigit():
                    scene_num = int(part)
                i += 1
                continue

            # Parse scene header for location/time
            location_name = "Unknown"
            time_of_day = "Unknown"

            header_match = re.match(
                r"^(?:INT|EXT)\.\s*([^-]+)\s*-\s*(DAY|NIGHT|MORNING|EVENING)",
                part,
                re.IGNORECASE,
            )
            if header_match:
                location_name = header_match.group(1).strip()
                time_of_day = header_match.group(2).upper()
                i += 1
                continue

            # Create scene
            scene = Scene(
                scene_number=scene_num,
                location_name=location_name,
                time_of_day=time_of_day,
                description=part[:200],
            )

            # Parse content into panels
            content = part
            if header_match:
                content = part[header_match.end():].strip()

            lines = [l.strip() for l in content.split("\n") if l.strip()]
            panel_num = 1
            for line in lines:
                if not line.startswith(("INT", "EXT")):
                    panel = StoryboardPanel(
                        panel_number=panel_num,
                        scene_number=scene_num,
                        description=line,
                    )
                    scene.panels.append(panel)
                    panel_num += 1

            if scene.panels:
                scenes.append(scene)
                scene_num += 1

            i += 1

        return scenes

    def _parse_script_to_scenes(self, script: str) -> list[Scene]:
        """Parse full screenplay format into scenes."""
        scenes = []
        lines = script.split("\n")

        current_scene: Optional[Scene] = None
        current_panel_desc = []
        panel_num = 1

        for line in lines:
            stripped = line.strip()

            # Scene heading
            if re.match(r"^(INT|EXT)\.", stripped, re.IGNORECASE):
                # Save previous scene
                if current_scene and current_panel_desc:
                    self._add_action_panels(
                        current_scene, current_panel_desc, panel_num
                    )
                    panel_num = 1
                    current_panel_desc = []

                if current_scene:
                    scenes.append(current_scene)

                # Parse scene heading
                location_name, time_of_day = self._parse_scene_heading(stripped)

                current_scene = Scene(
                    scene_number=len(scenes) + 1,
                    location_name=location_name,
                    time_of_day=time_of_day,
                    description=f"{location_name} - {time_of_day}",
                )
                continue

            # Action line
            if stripped and not stripped.startswith("(") and not stripped.isupper():
                current_panel_desc.append(stripped)

            # Empty line - end of action block
            elif not stripped and current_panel_desc:
                if current_scene:
                    self._add_action_panels(
                        current_scene, current_panel_desc, panel_num
                    )
                    panel_num += len(current_panel_desc)
                current_panel_desc = []

        # Handle remaining content
        if current_scene:
            if current_panel_desc:
                self._add_action_panels(current_scene, current_panel_desc, panel_num)
            scenes.append(current_scene)

        return scenes

    def _parse_scene_heading(
        self, heading: str
    ) -> tuple[str, str]:
        """Parse a scene heading into location and time."""
        # Pattern: INT./EXT. LOCATION - TIME
        match = re.match(
            r"^(INT|EXT)\.\s*([^-]+)\s*-\s*(.+)$",
            heading,
            re.IGNORECASE,
        )

        if match:
            location = match.group(2).strip()
            time = match.group(3).strip().upper()
            return location, time

        return heading.replace("INT.", "").replace("EXT.", "").strip(), "Unknown"

    def _add_action_panels(
        self,
        scene: Scene,
        action_lines: list[str],
        start_panel_num: int,
    ) -> None:
        """Convert action lines into storyboard panels."""
        for i, line in enumerate(action_lines):
            panel = StoryboardPanel(
                panel_number=start_panel_num + i,
                scene_number=scene.scene_number,
                description=line,
            )
            scene.panels.append(panel)

    def _parse_storyboard_format(self, text: str) -> list[Scene]:
        """Parse explicit storyboard panel format."""
        scenes = []
        current_scene: Optional[Scene] = None

        # Pattern for panel definitions
        panel_pattern = r"(?:PANEL|SHOT)\s*(\d+)[\s:.-]*(.*?)(?=(?:PANEL|SHOT)\s*\d+|$)"

        matches = re.findall(panel_pattern, text, re.DOTALL | re.IGNORECASE)

        scene_num = 1
        for panel_num, content in matches:
            # Try to extract scene info from content
            location = None
            time = None

            # Look for location/time in content
            loc_match = re.search(r"Location:\s*(.+)", content, re.IGNORECASE)
            time_match = re.search(r"Time:\s*(.+)", content, re.IGNORECASE)

            if loc_match:
                location = loc_match.group(1).strip()
            if time_match:
                time = time_match.group(1).strip()

            # Create new scene if location changed
            if location and (not current_scene or current_scene.location_name != location):
                if current_scene:
                    scenes.append(current_scene)

                current_scene = Scene(
                    scene_number=scene_num,
                    location_name=location or "Unknown",
                    time_of_day=time or "Unknown",
                    description=location or "Scene",
                )
                scene_num += 1

            if current_scene:
                panel = StoryboardPanel(
                    panel_number=int(panel_num),
                    scene_number=current_scene.scene_number,
                    description=content.strip(),
                )
                current_scene.panels.append(panel)

        if current_scene:
            scenes.append(current_scene)

        return scenes

    def storyboard_to_shotlist(
        self,
        scenes: list[Scene],
    ) -> Shotlist:
        """
        Convert storyboard panels to a Shotlist.

        This is the second pass - converts intermediate StoryboardPanel
        structures into final Shot objects with DNA references.

        Args:
            scenes: List of Scene objects from parse_to_storyboard

        Returns:
            Complete Shotlist ready for generation
        """
        shots = []

        for scene in scenes:
            # Extract/create location anchor
            location_id = None
            if self.auto_create_anchors:
                location_id = self._get_or_create_location_anchor(
                    scene.location_name,
                    scene.description,
                )

            # Extract/create context anchor
            context_id = None
            if self.auto_create_anchors and scene.context_mood:
                context_id = self._get_or_create_context_anchor(
                    f"Scene {scene.scene_number}",
                    scene.time_of_day,
                    scene.context_mood,
                )

            # Convert each panel to a shot
            for panel in scene.panels:
                # Extract characters from description
                char_ids = self._extract_characters(panel.description)

                # Infer camera from description
                camera = self._infer_camera(panel.description)

                # Override with panel-specific camera if provided
                if panel.camera_shot_size:
                    camera.shot_size = panel.camera_shot_size
                if panel.camera_angle:
                    camera.angle = panel.camera_angle
                if panel.camera_motion:
                    camera.motion = panel.camera_motion

                # Create shot
                shot = Shot(
                    shot_id=f"SC{scene.scene_number:02d}_SH{panel.panel_number:02d}",
                    scene_number=scene.scene_number,
                    character_ids=char_ids,
                    action_description=panel.description,
                    camera_specs=camera,
                    audio_script=panel.dialogue,
                    duration_seconds=self.default_duration,
                )

                # Store location/context references for DNA locking
                if location_id:
                    # Store in shot metadata for later use
                    pass  # Would need to add fields to Shot model

                shots.append(shot)

        return Shotlist(project_id=self.bible.project_id, shots=shots)

    def parse(
        self,
        input_text: str,
        format: str = "auto",
    ) -> Shotlist:
        """
        Parse input directly to Shotlist (convenience method).

        This combines parse_to_storyboard and storyboard_to_shotlist.

        Args:
            input_text: The input text to parse
            format: Input format

        Returns:
            Complete Shotlist
        """
        scenes = self.parse_to_storyboard(input_text, format)
        return self.storyboard_to_shotlist(scenes)

    def _get_or_create_location_anchor(
        self,
        location_name: str,
        description: str,
    ) -> str:
        """Get existing location anchor or create new one."""
        # Check if location exists
        for loc in self.bible.location_anchors:
            if loc.name.lower() == location_name.lower():
                return loc.location_id

        # Create new location anchor
        # Extract key visual elements from description
        dna_prompt = self._extract_location_dna(description)

        location = LocationAnchor(
            name=location_name,
            dna_prompt=dna_prompt[:200],  # Max length
        )

        if self.auto_create_anchors:
            self.bible.add_location(location)

        return location.location_id

    def _extract_location_dna(self, description: str) -> str:
        """Extract location DNA from scene description."""
        # Common location elements to look for
        elements = []

        location_keywords = {
            "wall": ["brick wall", "concrete wall", "white wall", "painted wall"],
            "window": ["large window", "bay window", "stained glass window"],
            "door": ["wooden door", "metal door", "glass door"],
            "furniture": ["couch", "chair", "table", "desk", "bed"],
            "lighting": ["lamp", "chandelier", "neon sign", "candlelight"],
            "decor": ["painting", "mirror", "shelf", "plant", "rug"],
        }

        desc_lower = description.lower()
        for category, keywords in location_keywords.items():
            for keyword in keywords:
                if keyword in desc_lower:
                    elements.append(keyword)

        if not elements:
            # Fallback to first descriptive phrase
            match = re.search(r"([^,.]+(?:, [^,.]+)*)", description)
            if match:
                return match.group(1).strip()[:200]

        return ", ".join(elements)[:200] if elements else "Generic location"

    def _get_or_create_context_anchor(
        self,
        name: str,
        time_period: Optional[str],
        mood: Optional[str],
    ) -> str:
        """Get existing context anchor or create new one."""
        # Check if context exists
        for ctx in self.bible.context_anchors:
            if ctx.name.lower() == name.lower():
                return ctx.context_id

        # Create new context anchor
        context = ContextAnchor(
            name=name,
            time_period=time_period,
            story_mood=mood,
        )

        if self.auto_create_anchors:
            self.bible.add_context(context)

        return context.context_id

    def _extract_characters(self, text: str) -> list[str]:
        """
        Extract character IDs from text.

        Matches against known characters in production bible.
        """
        found_ids = []

        for char in self.bible.character_anchors:
            # Check for character name in text
            if char.name.lower() in text.lower():
                found_ids.append(char.character_id)
            # Check for character ID directly
            if char.character_id in text:
                found_ids.append(char.character_id)

        return found_ids

    def _infer_camera(self, text: str) -> CameraSpecs:
        """
        Infer camera specs from text.

        Uses keyword matching to determine shot size, angle, motion.
        """
        text_lower = text.lower()

        # Default values
        shot_size = "Medium"
        angle = "Eye Level"
        motion = "Static"

        # Check for shot sizes
        for pattern, size in self.SHOT_SIZES.items():
            if pattern in text_lower:
                shot_size = size
                break

        # Check for angles
        for pattern, ang in self.CAMERA_ANGLES.items():
            if pattern in text_lower:
                angle = ang
                break

        # Check for motion
        for pattern, mov in self.CAMERA_MOTIONS.items():
            if pattern in text_lower:
                motion = mov
                break

        return CameraSpecs(shot_size=shot_size, angle=angle, motion=motion)
