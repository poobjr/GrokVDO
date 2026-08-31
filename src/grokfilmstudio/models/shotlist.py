"""
Shotlist data models.

Defines structured shot data for deterministic prompt compilation.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ShotStatus(str, Enum):
    """Status of a shot in the pipeline."""

    PENDING = "pending"
    KEYFRAME_GENERATED = "keyframe_generated"
    KEYFRAME_APPROVED = "keyframe_approved"
    KEYFRAME_REJECTED = "keyframe_rejected"
    VIDEO_GENERATED = "video_generated"
    VIDEO_APPROVED = "video_approved"
    AUDIO_GENERATED = "audio_generated"
    COMPLETE = "complete"
    RETRY = "retry"
    FAILED = "failed"


class CameraSpecs(BaseModel):
    """
    Camera specifications for deterministic shot composition.

    Attributes:
        shot_size: Type of shot (e.g., "Extreme Close-up", "Medium", "Wide")
        angle: Camera angle (e.g., "Eye Level", "Low Angle", "Dutch Angle")
        motion: Camera/subject motion (e.g., "Static", "Slow Pan Right", "Tracking")
        lens: Optional lens specification (e.g., "35mm", "85mm")
        focus: Optional focus description (e.g., "Shallow DOF", "Deep focus")
    """

    shot_size: str
    angle: str = "Eye Level"
    motion: str = "Static"
    lens: Optional[str] = None
    focus: Optional[str] = None

    def format_for_prompt(self) -> str:
        """Format camera specs for prompt injection."""
        parts = [self.shot_size, self.angle]
        if self.motion and self.motion != "Static":
            parts.append(self.motion)
        if self.lens:
            parts.append(f"{self.lens} lens")
        if self.focus:
            parts.append(self.focus)
        return ", ".join(parts)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "shot_size": "Medium Close-up",
                    "angle": "Low Angle",
                    "motion": "Slow Pan Right",
                    "lens": "35mm",
                    "focus": "Shallow DOF",
                }
            ]
        }
    }


class Shot(BaseModel):
    """
    A single shot in the shotlist.

    Attributes:
        shot_id: Unique identifier (e.g., "SC01_SH01")
        scene_number: Scene number from script
        character_ids: List of character IDs present in shot
        action_description: Specific physical action or emotion
        camera_specs: Camera specifications
        audio_script: Dialogue, SFX, or voiceover text
        duration_seconds: Target duration (default 2-4 seconds)
        compiled_prompt: The final compiled prompt (populated during generation)
        status: Current pipeline status
        keyframe_path: Path to generated keyframe image
        video_path: Path to generated video clip
        audio_path: Path to generated audio file
        error_message: Last error message if failed
        retry_count: Number of retry attempts
    """

    shot_id: str
    scene_number: int = 1
    character_ids: list[str] = Field(default_factory=list)
    action_description: str
    camera_specs: CameraSpecs
    audio_script: Optional[str] = None
    duration_seconds: float = Field(default=3.0, ge=1.0, le=30.0)
    compiled_prompt: Optional[str] = None
    motion_prompt: Optional[str] = None

    # Pipeline state
    status: ShotStatus = ShotStatus.PENDING
    keyframe_path: Optional[str] = None
    video_path: Optional[str] = None
    audio_path: Optional[str] = None

    # Error handling
    error_message: Optional[str] = None
    retry_count: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def get_character_dna_refs(self) -> str:
        """Get character DNA references for prompt compilation."""
        if not self.character_ids:
            return ""
        return "Characters: {" + ",".join(self.character_ids) + "}"

    def mark_status(self, status: ShotStatus, error: Optional[str] = None) -> None:
        """Update shot status."""
        self.status = status
        self.updated_at = datetime.now()
        if error:
            self.error_message = error
        if status == ShotStatus.RETRY:
            self.retry_count += 1

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "shot_id": "SC01_SH01",
                    "scene_number": 1,
                    "character_ids": ["CHAR_001"],
                    "action_description": "Sarah turns to face the camera, eyes narrowing",
                    "camera_specs": {
                        "shot_size": "Medium Close-up",
                        "angle": "Low Angle",
                        "motion": "Slow Pan Right",
                    },
                    "audio_script": "You think you can stop me?",
                    "duration_seconds": 3.0,
                }
            ]
        }
    }


class Shotlist(BaseModel):
    """
    Complete shotlist for a project.

    Attributes:
        project_id: Reference to project
        created_at: Creation timestamp
        updated_at: Last update timestamp
        shots: List of shots in sequence order
        total_duration_seconds: Computed total duration
    """

    project_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    shots: list[Shot] = Field(default_factory=list)

    @property
    def total_duration_seconds(self) -> float:
        """Calculate total duration of all shots."""
        return sum(shot.duration_seconds for shot in self.shots)

    @property
    def total_shots(self) -> int:
        """Get total number of shots."""
        return len(self.shots)

    def add_shot(self, shot: Shot) -> None:
        """Add a shot to the shotlist."""
        self.shots.append(shot)
        self.updated_at = datetime.now()

    def get_shot(self, shot_id: str) -> Optional[Shot]:
        """Get a shot by ID."""
        for shot in self.shots:
            if shot.shot_id == shot_id:
                return shot
        return None

    def get_shots_by_status(self, status: ShotStatus) -> list[Shot]:
        """Get all shots with a specific status."""
        return [shot for shot in self.shots if shot.status == status]

    def get_pending_shots(self) -> list[Shot]:
        """Get all shots that haven't been processed."""
        return [
            shot
            for shot in self.shots
            if shot.status in [ShotStatus.PENDING, ShotStatus.RETRY]
        ]

    def get_next_shot(self) -> Optional[Shot]:
        """Get the next shot to process."""
        pending = self.get_pending_shots()
        return pending[0] if pending else None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "project_id": "PROJ_20260831_120000",
                    "total_shots": 24,
                    "total_duration_seconds": 72.0,
                }
            ]
        }
    }
