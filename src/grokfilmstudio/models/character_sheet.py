"""
Character Sheet Model.

Detailed character definition system for consistent AI generation.
Includes physical attributes, personality, wardrobe, and reference poses.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class Gender(str, Enum):
    """Character gender options."""

    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non-binary"
    OTHER = "other"


class BodyType(str, Enum):
    """Character body type options."""

    PETITE = "petite"
    SLIM = "slim"
    ATHLETIC = "athletic"
    AVERAGE = "average"
    CURVY = "curvy"
    MUSCULAR = "muscular"
    HEAVY = "heavy"


class FaceShape(str, Enum):
    """Character face shape options."""

    OVAL = "oval"
    ROUND = "round"
    SQUARE = "square"
    HEART = "heart"
    LONG = "long"
    DIAMOND = "diamond"


class HairStyle(str, Enum):
    """Character hair style options."""

    LONG_STRAIGHT = "long straight"
    LONG_WAVY = "long wavy"
    LONG_CURLY = "long curly"
    SHOULDER_LENGTH = "shoulder-length"
    BOB = "bob cut"
    PIXIE = "pixie cut"
    BUZZ_CUT = "buzz cut"
    BALD = "bald"
    PONYTAIL = "ponytail"
    BUN = "bun"
    BRAIDS = "braids"
    AFRO = "afro"
    MOHAWK = "mohawk"
    UNDERCUT = "undercut"


class EyeColor(str, Enum):
    """Character eye color options."""

    BROWN = "brown"
    BLUE = "blue"
    GREEN = "green"
    HAZEL = "hazel"
    GRAY = "gray"
    AMBER = "amber"
    VIOLET = "violet"
    RED = "red"


class SkinTone(str, Enum):
    """Character skin tone options (Fitzpatrick scale simplified)."""

    VERY_FAIR = "very fair (porcelain)"
    FAIR = "fair (light)"
    MEDIUM = "medium (olive)"
    OLIVE = "olive"
    BROWN = "brown"
    DARK_BROWN = "dark brown"
    DEEP = "deep (ebony)"


class PersonalityTrait(str, Enum):
    """Common personality traits for character reference."""

    CONFIDENT = "confident"
    SHY = "shy"
    OUTGOING = "outgoing"
    RESERVED = "reserved"
    OPTIMISTIC = "optimistic"
    PESSIMISTIC = "pessimistic"
    SERIOUS = "serious"
    PLAYFUL = "playful"
    AGGRESSIVE = "aggressive"
    GENTLE = "gentle"
    MYSTERIOUS = "mysterious"
    CHARISMATIC = "charismatic"
    NERVOUS = "nervous"
    CALM = "calm"
    INTENSE = "intense"


class PhysicalAttributes(BaseModel):
    """
    Detailed physical attributes for character sheet.
    """

    # Basic
    age_range: str = Field(default="25-35", description="Age range (e.g., '25-35', 'elderly')")
    gender: Gender = Field(default=Gender.FEMALE)
    height: str = Field(default="165 cm", description="Height (e.g., '165 cm', '5'6\"')")
    body_type: BodyType = Field(default=BodyType.AVERAGE)

    # Face
    face_shape: FaceShape = Field(default=FaceShape.OVAL)
    eye_color: EyeColor = Field(default=EyeColor.BROWN)
    eye_shape: Optional[str] = Field(default=None, description="Eye shape (e.g., 'almond', 'round', 'hooded')")
    eyebrows: Optional[str] = Field(default=None, description="Eyebrow description (e.g., 'thick arched', 'thin straight')")
    nose: Optional[str] = Field(default=None, description="Nose description (e.g., 'straight', 'button', 'aquiline')")
    lips: Optional[str] = Field(default=None, description="Lip description (e.g., 'full', 'thin', 'bow-shaped')")
    jawline: Optional[str] = Field(default=None, description="Jawline description (e.g., 'strong square', 'soft round')")
    facial_hair: Optional[str] = Field(default=None, description="Facial hair (e.g., 'clean shaven', 'stubble', 'full beard')")

    # Skin
    skin_tone: SkinTone = Field(default=SkinTone.MEDIUM)
    skin_details: Optional[str] = Field(default=None, description="Skin details (e.g., 'freckles on cheeks', 'scar on forehead')")

    # Hair
    hair_style: HairStyle = Field(default=HairStyle.LONG_STRAIGHT)
    hair_color: str = Field(default="black", description="Hair color (e.g., 'black', 'blonde', 'red with gray streaks')")
    hair_texture: Optional[str] = Field(default=None, description="Hair texture (e.g., 'fine', 'thick', 'coarse')")

    # Distinguishing features
    distinguishing_features: list[str] = Field(
        default_factory=list,
        description="Unique features (e.g., 'tattoo on left arm', 'mole above lip')",
    )

    def to_dna_prompt(self) -> str:
        """Convert physical attributes to concise DNA prompt."""
        parts = []

        # Gender and age
        gender_str = self.gender.value
        if self.age_range:
            gender_str = f"{self.age_range.replace('-', '-year-old ')} {gender_str}"
        parts.append(gender_str)

        # Body type
        if self.body_type != BodyType.AVERAGE:
            parts.append(f"{self.body_type.value} build")

        # Hair
        hair_parts = []
        if self.hair_style != HairStyle.LONG_STRAIGHT:
            hair_parts.append(self.hair_style.value)
        if self.hair_color != "black":
            hair_parts.append(f"{self.hair_color} hair")
        if hair_parts:
            parts.append(", ".join(hair_parts))
        else:
            parts.append("black hair")

        # Key facial features (max 2-3 for DNA)
        facial = []
        if self.eye_color != EyeColor.BROWN:
            facial.append(f"{self.eye_color.value} eyes")
        if self.face_shape != FaceShape.OVAL:
            facial.append(f"{self.face_shape.value} face")
        if self.distinguishing_features:
            facial.extend(self.distinguishing_features[:2])
        if facial:
            parts.append(", ".join(facial))

        return ", ".join(parts)


class StyleAttributes(BaseModel):
    """
    Character's wardrobe and style preferences.
    """

    # Overall style
    style_keywords: list[str] = Field(
        default_factory=list,
        description="Style keywords (e.g., ['edgy', 'minimalist', 'bohemian'])",
    )

    # Color palette
    signature_colors: list[str] = Field(
        default_factory=list,
        description="Signature colors (e.g., ['red', 'black', 'denim blue'])",
    )

    # Wardrobe items
    signature_items: list[str] = Field(
        default_factory=list,
        description="Signature wardrobe items (e.g., ['leather jacket', 'combat boots'])",
    )

    # Accessories
    accessories: list[str] = Field(
        default_factory=list,
        description="Regular accessories (e.g., ['silver necklace', 'leather watch'])",
    )

    # Style notes
    style_notes: Optional[str] = Field(
        default=None,
        description="Additional style notes",
    )

    def to_prompt(self) -> str:
        """Convert style attributes to prompt text."""
        parts = []

        if self.signature_items:
            parts.append(", ".join(self.signature_items[:3]))

        if self.accessories:
            parts.append("accessorized with " + ", ".join(self.accessories[:2]))

        if self.signature_colors:
            parts.append(f"in {', '.join(self.signature_colors[:2])} tones")

        return ", ".join(parts) if parts else ""


class FaceChart(BaseModel):
    """
    Face chart for consistent facial expressions.
    """

    neutral: Optional[str] = Field(default=None, description="Neutral expression reference image path")
    smile: Optional[str] = Field(default=None, description="Smiling expression reference")
    serious: Optional[str] = Field(default=None, description="Serious/intense expression reference")
    angry: Optional[str] = Field(default=None, description="Angry expression reference")
    surprised: Optional[str] = Field(default=None, description="Surprised expression reference")
    crying: Optional[str] = Field(default=None, description="Crying/sad expression reference")

    expression_notes: Optional[str] = Field(
        default=None,
        description="Notes on how expressions affect facial features",
    )


class PoseReference(BaseModel):
    """
    Pose reference for consistent character posing.
    """

    pose_name: str
    description: str
    image_path: Optional[str] = None
    prompt_modifier: Optional[str] = Field(
        default=None,
        description="Prompt modifier for this pose (e.g., 'arms crossed, weight on left leg')",
    )


class CharacterSheet(BaseModel):
    """
    Complete Character Sheet with all details for consistent AI generation.

    This is an extended version of CharacterAnchor with much more detail.
    Use this for main characters that need high consistency.
    """

    # Basic Info
    character_id: str = Field(default_factory=lambda: f"CHAR_{uuid4().hex[:6].upper()}")
    character_name: str
    project_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Physical Attributes (detailed)
    physical: PhysicalAttributes = Field(default_factory=PhysicalAttributes)

    # Style & Wardrobe
    style: StyleAttributes = Field(default_factory=StyleAttributes)

    # Personality (affects expressions and body language)
    personality_traits: list[PersonalityTrait] = Field(default_factory=list)
    personality_notes: Optional[str] = Field(
        default=None,
        description="How personality affects physical presence",
    )

    # Face Chart (expressions)
    face_chart: FaceChart = Field(default_factory=FaceChart)

    # Pose References
    pose_references: list[PoseReference] = Field(default_factory=list)

    # Reference Images
    reference_images: dict[str, str] = Field(
        default_factory=dict,
        description="Named reference images (e.g., 'full_body_front', 'profile_left', 'closeup')",
    )

    # Voice (for TTS)
    voice_description: Optional[str] = Field(
        default=None,
        description="Voice description for TTS (e.g., 'deep raspy voice, mid-Atlantic accent')",
    )

    # Background (for context)
    background: Optional[str] = Field(
        default=None,
        description="Character background/backstory (affects demeanor)",
    )

    # Notes
    additional_notes: Optional[str] = None

    def get_dna_prompt(self) -> str:
        """
        Get the primary DNA prompt for this character.

        This is the concise version used in generation prompts.
        """
        return self.physical.to_dna_prompt()

    def get_full_description(self) -> str:
        """
        Get full character description for reference.

        More detailed than DNA prompt - useful for documentation.
        """
        parts = []

        # Basic info
        parts.append(f"{self.character_name}")
        parts.append(f"{self.physical.age_range} {self.physical.gender.value}")
        parts.append(f"{self.physical.height}, {self.physical.body_type.value} build")

        # Physical details
        phys = self.physical
        details = []
        if phys.face_shape:
            details.append(f"{phys.face_shape.value} face")
        if phys.eye_color:
            details.append(f"{phys.eye_color.value} eyes")
        if phys.hair_style:
            details.append(f"{phys.hair_style.value} {phys.hair_color} hair")
        if phys.skin_tone:
            details.append(f"{phys.skin_tone.value} skin")
        if phys.distinguishing_features:
            details.extend(phys.distinguishing_features)

        if details:
            parts.append(", ".join(details))

        # Style
        if self.style.signature_items:
            parts.append(f"Typically wears: {', '.join(self.style.signature_items)}")

        # Personality
        if self.personality_traits:
            parts.append(f"Personality: {', '.join(t.value for t in self.personality_traits)}")

        return " | ".join(parts)

    def get_generation_prompt(
        self,
        include_style: bool = True,
        include_personality: bool = False,
    ) -> str:
        """
        Get prompt for generating consistent character images.

        Args:
            include_style: Include wardrobe/style details
            include_personality: Include personality cues

        Returns:
            Generation prompt string
        """
        parts = [self.get_dna_prompt()]

        if include_style:
            style_prompt = self.style.to_prompt()
            if style_prompt:
                parts.append(style_prompt)

        if include_personality and self.personality_traits:
            trait = self.personality_traits[0].value
            parts.append(f"expressing {trait} demeanor")

        return ", ".join(parts)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> "CharacterSheet":
        """Create from dictionary."""
        return cls.model_validate(data)


class CharacterSheetBuilder:
    """
    Builder class for creating CharacterSheet instances.

    Provides a fluent interface for step-by-step character creation.
    """

    def __init__(self, name: str, project_id: str):
        """Initialize builder with required fields."""
        self.sheet = CharacterSheet(
            character_name=name,
            project_id=project_id,
        )

    def physical_attributes(
        self,
        age_range: str = None,
        gender: Gender = None,
        height: str = None,
        body_type: BodyType = None,
        face_shape: FaceShape = None,
        eye_color: EyeColor = None,
        hair_style: HairStyle = None,
        hair_color: str = None,
        skin_tone: SkinTone = None,
        distinguishing_features: list[str] = None,
    ) -> "CharacterSheetBuilder":
        """Set physical attributes."""
        if age_range:
            self.sheet.physical.age_range = age_range
        if gender:
            self.sheet.physical.gender = gender
        if height:
            self.sheet.physical.height = height
        if body_type:
            self.sheet.physical.body_type = body_type
        if face_shape:
            self.sheet.physical.face_shape = face_shape
        if eye_color:
            self.sheet.physical.eye_color = eye_color
        if hair_style:
            self.sheet.physical.hair_style = hair_style
        if hair_color:
            self.sheet.physical.hair_color = hair_color
        if skin_tone:
            self.sheet.physical.skin_tone = skin_tone
        if distinguishing_features:
            self.sheet.physical.distinguishing_features = distinguishing_features

        return self

    def style_preferences(
        self,
        style_keywords: list[str] = None,
        signature_colors: list[str] = None,
        signature_items: list[str] = None,
        accessories: list[str] = None,
    ) -> "CharacterSheetBuilder":
        """Set style preferences."""
        if style_keywords:
            self.sheet.style.style_keywords = style_keywords
        if signature_colors:
            self.sheet.style.signature_colors = signature_colors
        if signature_items:
            self.sheet.style.signature_items = signature_items
        if accessories:
            self.sheet.style.accessories = accessories

        return self

    def personality(
        self,
        traits: list[PersonalityTrait] = None,
        notes: str = None,
    ) -> "CharacterSheetBuilder":
        """Set personality traits."""
        if traits:
            self.sheet.personality_traits = traits
        if notes:
            self.sheet.personality_notes = notes

        return self

    def voice(self, description: str) -> "CharacterSheetBuilder":
        """Set voice description."""
        self.sheet.voice_description = description
        return self

    def background(self, bg: str) -> "CharacterSheetBuilder":
        """Set character background."""
        self.sheet.background = bg
        return self

    def notes(self, notes: str) -> "CharacterSheetBuilder":
        """Set additional notes."""
        self.sheet.additional_notes = notes
        return self

    def build(self) -> CharacterSheet:
        """Build and return the CharacterSheet."""
        self.sheet.updated_at = datetime.now()
        return self.sheet
