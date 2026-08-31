"""
Project State data models.

Defines state persistence schema for pipeline recovery and progress tracking.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class PipelinePhase(str, Enum):
    """Pipeline phases for state tracking."""

    BIBLE_SETUP = "bible_setup"
    SCRIPT_PARSING = "script_parsing"
    KEYFRAME_GEN = "keyframe_gen"
    VIDEO_GEN = "video_gen"
    AUDIO_ASSEMBLY = "audio_assembly"
    COMPLETE = "complete"


class PhaseStatus(str, Enum):
    """Status of a pipeline phase."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class PhaseState(BaseModel):
    """
    State tracking for a single pipeline phase.

    Attributes:
        status: Current phase status
        started_at: When phase started
        completed_at: When phase completed
        last_checkpoint: Last saved checkpoint data
        error_message: Error if phase failed
        progress_percent: Progress percentage (0-100)
    """

    status: PhaseStatus = PhaseStatus.NOT_STARTED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_checkpoint: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None
    progress_percent: int = 0

    def start(self) -> None:
        """Mark phase as started."""
        self.status = PhaseStatus.IN_PROGRESS
        self.started_at = datetime.now()

    def complete(self) -> None:
        """Mark phase as completed."""
        self.status = PhaseStatus.COMPLETED
        self.completed_at = datetime.now()
        self.progress_percent = 100

    def fail(self, error_message: str) -> None:
        """Mark phase as failed."""
        self.status = PhaseStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.now()

    def save_checkpoint(self, checkpoint: dict[str, Any]) -> None:
        """Save a checkpoint for recovery."""
        self.last_checkpoint = checkpoint
        self.started_at = self.started_at or datetime.now()


class ShotProgress(BaseModel):
    """
    Progress tracking for a single shot.

    Attributes:
        shot_id: Reference to shot
        status: Current shot status
        current_phase: Current pipeline phase for this shot
        last_error: Last error message
        retry_count: Number of retries
        render_path: Path to rendered video
        keyframe_path: Path to keyframe image
        timings: Timing information for each phase
    """

    shot_id: str
    status: str = "pending"
    current_phase: Optional[PipelinePhase] = None
    last_error: Optional[str] = None
    retry_count: int = 0
    render_path: Optional[str] = None
    keyframe_path: Optional[str] = None
    audio_path: Optional[str] = None

    # Timing tracking
    keyframe_generated_at: Optional[datetime] = None
    video_generated_at: Optional[datetime] = None
    audio_generated_at: Optional[datetime] = None

    def update_status(self, status: str, phase: Optional[PipelinePhase] = None) -> None:
        """Update shot progress status."""
        self.status = status
        if phase:
            self.current_phase = phase

    def mark_error(self, error: str) -> None:
        """Record an error."""
        self.last_error = error
        self.retry_count += 1

    def set_paths(
        self,
        keyframe: Optional[str] = None,
        video: Optional[str] = None,
        audio: Optional[str] = None,
    ) -> None:
        """Set asset paths."""
        if keyframe:
            self.keyframe_path = keyframe
            self.keyframe_generated_at = datetime.now()
        if video:
            self.render_path = video
            self.video_generated_at = datetime.now()
        if audio:
            self.audio_path = audio
            self.audio_generated_at = datetime.now()


class ProjectState(BaseModel):
    """
    Complete project state for pipeline recovery.

    This is the authoritative source for:
    - Current pipeline phase
    - Progress of each phase
    - Individual shot progress
    - Recovery checkpoints

    Attributes:
        project_id: Reference to project
        current_phase: Current pipeline phase
        created_at: Project creation time
        updated_at: Last update time
        phase_states: State of each pipeline phase
        shot_progress: Progress of individual shots
        metadata: Additional metadata
    """

    project_id: str
    current_phase: PipelinePhase = PipelinePhase.BIBLE_SETUP
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    phase_states: dict[str, PhaseState] = Field(default_factory=dict)
    shot_progress: dict[str, ShotProgress] = Field(default_factory=dict)

    metadata: dict[str, Any] = Field(default_factory=dict)

    def get_phase_state(self, phase: PipelinePhase) -> PhaseState:
        """Get or create state for a phase."""
        phase_key = phase.value
        if phase_key not in self.phase_states:
            self.phase_states[phase_key] = PhaseState()
        return self.phase_states[phase_key]

    def update_phase_state(
        self, phase: PipelinePhase, state: PhaseState
    ) -> None:
        """Update state for a phase."""
        self.phase_states[phase.value] = state
        self.updated_at = datetime.now()

    def get_shot_progress(self, shot_id: str) -> ShotProgress:
        """Get or create progress for a shot."""
        if shot_id not in self.shot_progress:
            self.shot_progress[shot_id] = ShotProgress(shot_id=shot_id)
        return self.shot_progress[shot_id]

    def update_shot_progress(self, shot_id: str, progress: ShotProgress) -> None:
        """Update progress for a shot."""
        self.shot_progress[shot_id] = progress
        self.updated_at = datetime.now()

    def is_phase_complete(self, phase: PipelinePhase) -> bool:
        """Check if a phase is complete."""
        if phase.value not in self.phase_states:
            return False
        return self.phase_states[phase.value].status == PhaseStatus.COMPLETED

    def get_completion_summary(self) -> dict[str, Any]:
        """Get a summary of project completion."""
        total_shots = len(self.shot_progress)
        completed_shots = sum(
            1
            for sp in self.shot_progress.values()
            if sp.status == "complete"
        )

        return {
            "project_id": self.project_id,
            "current_phase": self.current_phase.value,
            "total_shots": total_shots,
            "completed_shots": completed_shots,
            "completion_percent": round(
                (completed_shots / total_shots * 100) if total_shots > 0 else 0, 1
            ),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "project_id": "PROJ_20260831_120000",
                    "current_phase": "keyframe_gen",
                    "total_shots": 24,
                    "completed_shots": 8,
                }
            ]
        }
    }
