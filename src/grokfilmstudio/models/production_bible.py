"""
Production Bible data models.

Defines the core creative anchors for a project:
- Character Anchors: DNA prompts, reference images
- World Anchors: Style, aspect ratio, color grade
- Audio Anchors: Voice mappings for TTS
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class CharacterAnchor(BaseModel):
    """
    Character anchor defining consistent identity across shots.

    Attributes:
        character_id: Unique identifier (e.g., "CHAR_001")
        name: Character name
        dna_prompt: Concise DNA description (max 150 chars, 3-4 traits)
        master_reference_image: Path to master reference image
        notes: Additional character notes
    """

    character_id: str = Field(default_factory=lambda: f"CHAR_{uuid4().hex[:6].upper()}")
    name: str
    dna_prompt: str = Field(..., max_length=150)
    master_reference_image: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("dna_prompt")
    @classmethod
    def validate_dna_prompt(cls, v: str) -> str:
        """Ensure DNA prompt is concise and trait-focused."""
        if not v.strip():
            raise ValueError("DNA prompt cannot be empty")
        # Warn if too long (soft validation)
        if len(v) > 100:
            pass  # Could log warning
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "character_id": "CHAR_001",
                    "name": "Sarah Chen",
                    "dna_prompt": "Asian woman, shoulder-length black hair, red leather jacket, determined expression",
                    "master_reference_image": "./projects/proj_001/keyframes/char_001_ref.png",
                }
            ]
        }
    }


class WorldAnchor(BaseModel):
    """
    World and style anchors for visual consistency.

    Attributes:
        style_prompt: Global aesthetic prompt (e.g., "Cinematic 35mm, Kodak Portra 400")
        aspect_ratio: Target aspect ratio (16:9, 9:16, 21:9, 1:1)
        color_grade: Color palette/grade description
        time_period: Optional time period setting
        location_notes: Optional location descriptions
    """

    style_prompt: str
    aspect_ratio: str = Field(default="16:9", pattern=r"^(16:9|9:16|21:9|1:1)$")
    color_grade: Optional[str] = None
    time_period: Optional[str] = None
    location_notes: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "style_prompt": "Cinematic 35mm, Kodak Portra 400, dark thriller lighting",
                    "aspect_ratio": "16:9",
                    "color_grade": "Teal and orange, high contrast",
                    "time_period": "Near future, 2045",
                }
            ]
        }
    }


class AudioAnchor(BaseModel):
    """
    Audio anchor mapping characters to TTS voices.

    Attributes:
        character_id: Reference to CharacterAnchor
        voice_provider: TTS provider (e.g., "elevenlabs")
        voice_id: Provider-specific voice ID
        voice_name: Human-readable voice name
    """

    character_id: str
    voice_provider: str = "elevenlabs"
    voice_id: str
    voice_name: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "character_id": "CHAR_001",
                    "voice_provider": "elevenlabs",
                    "voice_id": "21m00Tcm4TlvDq8ikWAM",
                    "voice_name": "Rachel - Young American Female",
                }
            ]
        }
    }


class LocationAnchor(BaseModel):
    """
    Location anchor for consistent environment/setting generation.

    Use this to lock down recurring locations across multiple shots.
    This prevents the AI from randomly generating different versions
    of the same location.

    Attributes:
        location_id: Unique identifier (e.g., "LOC_001")
        name: Location name (e.g., "Sarah's Apartment", "Abandoned Warehouse")
        dna_prompt: Concise location DNA (max 200 chars, key visual elements)
        master_reference_image: Path to master reference image
        lighting: Typical lighting condition (e.g., "dim neon glow", "bright daylight")
        mood: Emotional atmosphere (e.g., "tense", "peaceful", "mysterious")
        key_props: Important props that must appear consistently
    """

    location_id: str = Field(default_factory=lambda: f"LOC_{uuid4().hex[:6].upper()}")
    name: str
    dna_prompt: str = Field(..., max_length=200)
    master_reference_image: Optional[str] = None
    lighting: Optional[str] = None
    mood: Optional[str] = None
    key_props: list[str] = Field(default_factory=list)

    @field_validator("dna_prompt")
    @classmethod
    def validate_dna_prompt(cls, v: str) -> str:
        """Ensure DNA prompt is concise and element-focused."""
        if not v.strip():
            raise ValueError("Location DNA prompt cannot be empty")
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "location_id": "LOC_001",
                    "name": "Sarah's Apartment",
                    "dna_prompt": "Small studio apartment, exposed brick wall, large window with fire escape, plants everywhere, bookshelf overflowing",
                    "lighting": "Warm evening light through window",
                    "mood": "Cozy but cluttered",
                    "key_props": ["vintage typewriter", "succulent plants", "vinyl records"],
                }
            ]
        }
    }


class ContextAnchor(BaseModel):
    """
    Context anchor for locking story context/time/continuity.

    Use this to maintain consistency across shots that happen
    in the same story moment or time period.

    Attributes:
        context_id: Unique identifier (e.g., "CTX_001")
        name: Context name (e.g., "The Chase Scene", "Flashback to 1995")
        time_period: When this happens (e.g., "Night, 2 AM", "Summer 1995")
        weather: Weather conditions if relevant
        story_mood: Overall emotional tone
        continuity_notes: What must remain consistent across shots
    """

    context_id: str = Field(default_factory=lambda: f"CTX_{uuid4().hex[:6].upper()}")
    name: str
    time_period: Optional[str] = None
    weather: Optional[str] = None
    story_mood: Optional[str] = None
    continuity_notes: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "context_id": "CTX_001",
                    "name": "The Confrontation",
                    "time_period": "Night, raining",
                    "story_mood": "Tense, dangerous",
                    "continuity_notes": "Sarah's jacket must be wet, street lights reflecting on pavement",
                }
            ]
        }
    }


class ProductionBible(BaseModel):
    """
    Complete production bible containing all creative anchors.

    This is the source of truth for a project's creative direction.
    All prompt compilation references data from the production bible.

    DNA Locking System:
    - Character DNA: Locked identity traits (face, hair, clothing)
    - Location DNA: Locked environment elements (walls, furniture, props)
    - Context DNA: Locked story context (time, weather, mood)
    - World DNA: Locked visual style (camera, color, lighting)

    This prevents drift when generating multiple clips sequentially.
    """

    project_id: str = Field(default_factory=lambda: f"PROJ_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    project_name: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Core Anchors
    character_anchors: list[CharacterAnchor] = Field(default_factory=list)
    location_anchors: list[LocationAnchor] = Field(default_factory=list)
    context_anchors: list[ContextAnchor] = Field(default_factory=list)
    world_anchors: Optional[WorldAnchor] = None
    audio_anchors: list[AudioAnchor] = Field(default_factory=list)

    # Metadata
    logline: Optional[str] = None
    synopsis: Optional[str] = None
    genre: Optional[str] = None
    tone: Optional[str] = None

    def add_character(self, character: CharacterAnchor) -> None:
        """Add a character anchor to the bible."""
        self.character_anchors.append(character)
        self.updated_at = datetime.now()

    def add_location(self, location: LocationAnchor) -> None:
        """Add a location anchor to the bible."""
        self.location_anchors.append(location)
        self.updated_at = datetime.now()

    def add_context(self, context: ContextAnchor) -> None:
        """Add a context anchor to the bible."""
        self.context_anchors.append(context)
        self.updated_at = datetime.now()

    def get_character(self, character_id: str) -> Optional[CharacterAnchor]:
        """Get a character by ID."""
        for char in self.character_anchors:
            if char.character_id == character_id:
                return char
        return None

    def get_location(self, location_id: str) -> Optional[LocationAnchor]:
        """Get a location by ID."""
        for loc in self.location_anchors:
            if loc.location_id == location_id:
                return loc
        return None

    def get_context(self, context_id: str) -> Optional[ContextAnchor]:
        """Get a context by ID."""
        for ctx in self.context_anchors:
            if ctx.context_id == context_id:
                return ctx
        return None

    def get_audio_anchor(self, character_id: str) -> Optional[AudioAnchor]:
        """Get audio anchor for a character."""
        for anchor in self.audio_anchors:
            if anchor.character_id == character_id:
                return anchor
        return None

    def get_all_dna_summary(self) -> str:
        """
        Get a summary of all DNA for quick reference.
        Useful for prompt compilation and consistency checks.
        """
        summary_parts = []

        if self.character_anchors:
            chars = "\n".join(
                f"  - {c.name}: {c.dna_prompt}"
                for c in self.character_anchors
            )
            summary_parts.append(f"Characters:\n{chars}")

        if self.location_anchors:
            locs = "\n".join(
                f"  - {loc.name}: {loc.dna_prompt}"
                for loc in self.location_anchors
            )
            summary_parts.append(f"Locations:\n{locs}")

        if self.context_anchors:
            ctxs = "\n".join(
                f"  - {ctx.name}: {ctx.time_period or ''} {ctx.weather or ''}"
                for ctx in self.context_anchors
            )
            summary_parts.append(f"Contexts:\n{ctxs}")

        if self.world_anchors:
            summary_parts.append(f"World Style: {self.world_anchors.style_prompt}")

        return "\n\n".join(summary_parts)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "project_id": "PROJ_20260831_120000",
                    "project_name": "The Last Stand",
                    "logline": "A lone detective faces her past in a neon-soaked underworld.",
                    "genre": "Neo-noir thriller",
                }
            ]
        }
    }

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "project_id": "PROJ_20260831_120000",
                    "project_name": "The Last Stand",
                    "logline": "A lone detective faces her past in a neon-soaked underworld.",
                }
            ]
        }
    }
