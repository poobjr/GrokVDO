"""
Data models for GrokFilmStudio.

Defines Pydantic schemas for:
- Production Bible (characters, locations, contexts, world, style anchors)
- Character Sheet (detailed character definition)
- Shotlist (structured shot data)
- Project State (pipeline state persistence)
"""

from grokfilmstudio.models.production_bible import (
    CharacterAnchor,
    LocationAnchor,
    ContextAnchor,
    WorldAnchor,
    AudioAnchor,
    ProductionBible,
)
from grokfilmstudio.models.character_sheet import (
    CharacterSheet,
    CharacterSheetBuilder,
    PhysicalAttributes,
    StyleAttributes,
    FaceChart,
    PoseReference,
    Gender,
    BodyType,
    FaceShape,
    HairStyle,
    EyeColor,
    SkinTone,
    PersonalityTrait,
)
from grokfilmstudio.models.shotlist import (
    CameraSpecs,
    Shot,
    Shotlist,
)
from grokfilmstudio.models.project_state import (
    PhaseState,
    ShotProgress,
    ProjectState,
)

__all__ = [
    # Production Bible
    "CharacterAnchor",
    "LocationAnchor",
    "ContextAnchor",
    "WorldAnchor",
    "AudioAnchor",
    "ProductionBible",
    # Character Sheet
    "CharacterSheet",
    "CharacterSheetBuilder",
    "PhysicalAttributes",
    "StyleAttributes",
    "FaceChart",
    "PoseReference",
    "Gender",
    "BodyType",
    "FaceShape",
    "HairStyle",
    "EyeColor",
    "SkinTone",
    "PersonalityTrait",
    # Shotlist
    "CameraSpecs",
    "Shot",
    "Shotlist",
    # Project State
    "PhaseState",
    "ShotProgress",
    "ProjectState",
]
