"""
Batch Generation Manager.

Handles batch generation workflow:
1. Generate all keyframes first (review/approve step)
2. Generate all videos from approved keyframes
3. Assemble final timeline

This approach:
- Saves tokens by locking DNA across generations
- Allows human review before video generation
- Enables efficient batch processing
- Reduces redundant regeneration
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from grokfilmstudio.automation.grok_controller import GrokController
from grokfilmstudio.compiler.prompt_compiler import PromptCompiler
from grokfilmstudio.models.project_state import PipelinePhase, ProjectState, ShotProgress
from grokfilmstudio.models.shotlist import Shot, ShotStatus
from grokfilmstudio.pipeline.ffmpeg_assembly import FFmpegAssembly
from grokfilmstudio.pipeline.timeline_export import TimelineExport
from grokfilmstudio.state import StatePersistenceManager


class BatchStatus(str, Enum):
    """Status of a batch generation job."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    KEYFRAMES_COMPLETE = "keyframes_complete"
    VIDEOS_COMPLETE = "videos_complete"
    ASSEMBLED = "assembled"
    FAILED = "failed"
    CANCELLED = "cancelled"


class GenerationStage(str, Enum):
    """Generation stages in batch workflow."""

    KEYFRAMES = "keyframes"
    VIDEOS = "videos"
    AUDIO = "audio"
    ASSEMBLY = "assembly"


@dataclass
class BatchJob:
    """
    Represents a batch generation job.

    A batch job processes multiple shots together,
    with checkpoints between stages for review.
    """

    job_id: str
    project_id: str
    shot_ids: list[str]
    location_id: Optional[str] = None
    context_id: Optional[str] = None

    # Status tracking
    status: BatchStatus = BatchStatus.PENDING
    current_stage: GenerationStage = GenerationStage.KEYFRAMES

    # Progress tracking
    total_shots: int = 0
    completed_shots: int = 0
    failed_shots: int = 0

    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Results
    keyframes_generated: list[str] = field(default_factory=list)
    videos_generated: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    # Settings
    concurrent_generations: int = 1  # Grok typically allows 1 at a time
    retry_on_failure: bool = True
    max_retries: int = 2

    def __post_init__(self):
        self.total_shots = len(self.shot_ids)

    @property
    def progress_percent(self) -> int:
        """Calculate overall progress percentage."""
        if self.total_shots == 0:
            return 0

        # Weight: keyframes 40%, videos 60%
        if self.current_stage == GenerationStage.KEYFRAMES:
            return int((self.completed_shots / self.total_shots) * 40)
        elif self.current_stage == GenerationStage.VIDEOS:
            return 40 + int((self.completed_shots / self.total_shots) * 60)
        elif self.current_stage == GenerationStage.ASSEMBLY:
            return 100
        return 0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "job_id": self.job_id,
            "project_id": self.project_id,
            "shot_ids": self.shot_ids,
            "location_id": self.location_id,
            "context_id": self.context_id,
            "status": self.status.value,
            "current_stage": self.current_stage.value,
            "total_shots": self.total_shots,
            "completed_shots": self.completed_shots,
            "failed_shots": self.failed_shots,
            "created_at": str(self.created_at),
            "started_at": str(self.started_at) if self.started_at else None,
            "completed_at": str(self.completed_at) if self.completed_at else None,
            "keyframes_generated": self.keyframes_generated,
            "videos_generated": self.videos_generated,
            "errors": self.errors,
            "progress_percent": self.progress_percent,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BatchJob":
        """Create from dictionary."""
        return cls(
            job_id=data["job_id"],
            project_id=data["project_id"],
            shot_ids=data["shot_ids"],
            location_id=data.get("location_id"),
            context_id=data.get("context_id"),
            status=BatchStatus(data["status"]),
            current_stage=GenerationStage(data["current_stage"]),
            total_shots=data["total_shots"],
            completed_shots=data["completed_shots"],
            failed_shots=data.get("failed_shots", 0),
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else datetime.now(),
            started_at=datetime.fromisoformat(data["started_at"])
            if data.get("started_at")
            else None,
            completed_at=datetime.fromisoformat(data["completed_at"])
            if data.get("completed_at")
            else None,
            keyframes_generated=data.get("keyframes_generated", []),
            videos_generated=data.get("videos_generated", []),
            errors=data.get("errors", []),
        )


class BatchGenerationManager:
    """
    Manages batch generation workflow.

    Workflow:
    ┌─────────────────────────────────────────────────────────────┐
    │  STAGE 1: Generate All Keyframes                            │
    │  ─ Compile prompts with locked DNA                          │
    │  ─ Generate keyframe for each shot                          │
    │  ─ [HUMAN REVIEW POINT]                                     │
    ├─────────────────────────────────────────────────────────────┤
    │  STAGE 2: Generate All Videos                               │
    │  ─ Use approved keyframes as input                          │
    │  ─ Generate video with motion prompts                       │
    │  ─ Download and organize clips                              │
    ├─────────────────────────────────────────────────────────────┤
    │  STAGE 3: Generate Audio (Optional)                         │
    │  ─ Generate TTS for dialogue                                │
    │  ─ Sync with video timing                                   │
    ├─────────────────────────────────────────────────────────────┤
    │  STAGE 4: Assemble Timeline                                 │
    │  ─ Concatenate all video clips                              │
    │  ─ Mix audio tracks                                         │
    │  ─ Export final video                                       │
    └─────────────────────────────────────────────────────────────┘
    """

    def __init__(
        self,
        project_id: str,
        grok_controller: Optional[GrokController] = None,
        state_manager: Optional[StatePersistenceManager] = None,
    ):
        """
        Initialize batch generation manager.

        Args:
            project_id: Project to generate
            grok_controller: Grok automation controller
            state_manager: State persistence manager
        """
        self.project_id = project_id
        self.grok_controller = grok_controller
        self.state_manager = state_manager or StatePersistenceManager()

        # Load project data
        bible, shotlist, state = self.state_manager.recover_project(project_id)

        self.bible = bible
        self.shotlist = shotlist
        self.state = state

        if not self.bible or not self.shotlist:
            raise ValueError(f"Project not found: {project_id}")

        # Initialize compiler with locked DNA
        self.compiler = PromptCompiler(self.bible)

        # Project directories
        self.project_dir = self.state_manager.get_project_dir(project_id)
        self.keyframes_dir = self.project_dir / "keyframes"
        self.renders_dir = self.project_dir / "renders"
        self.audio_dir = self.project_dir / "audio"
        self.exports_dir = self.project_dir / "exports"

        # Ensure directories exist
        for dir_path in [
            self.keyframes_dir,
            self.renders_dir,
            self.audio_dir,
            self.exports_dir,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Current job
        self.current_job: Optional[BatchJob] = None

    def create_batch_job(
        self,
        shot_ids: Optional[list[str]] = None,
        location_id: Optional[str] = None,
        context_id: Optional[str] = None,
    ) -> BatchJob:
        """
        Create a new batch generation job.

        Args:
            shot_ids: Specific shots to generate (or all pending)
            location_id: Location DNA to lock across all shots
            context_id: Context DNA to lock across all shots

        Returns:
            New BatchJob instance
        """
        # If no shot_ids specified, get all pending shots
        if shot_ids is None:
            shot_ids = [
                shot.shot_id for shot in self.shotlist.get_pending_shots()
            ]

        job_id = f"BATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        job = BatchJob(
            job_id=job_id,
            project_id=self.project_id,
            shot_ids=shot_ids,
            location_id=location_id,
            context_id=context_id,
        )

        self.current_job = job
        return job

    async def run_keyframe_generation(
        self,
        job: Optional[BatchJob] = None,
        require_approval: bool = False,
    ) -> BatchJob:
        """
        Run keyframe generation for all shots in batch.

        Args:
            job: BatchJob to run (or use current_job)
            require_approval: If True, wait for approval after each shot

        Returns:
            Updated BatchJob
        """
        job = job or self.current_job
        if not job:
            raise ValueError("No batch job specified")

        job.status = BatchStatus.IN_PROGRESS
        job.current_stage = GenerationStage.KEYFRAMES
        job.started_at = datetime.now()

        for shot_id in job.shot_ids:
            shot = self.shotlist.get_shot(shot_id)
            if not shot:
                job.errors.append(f"Shot not found: {shot_id}")
                job.failed_shots += 1
                continue

            try:
                # Compile prompt with locked DNA
                prompt, errors, warnings = self.compiler.compile_and_validate(
                    shot,
                    location_id=job.location_id,
                    context_id=job.context_id,
                )

                if errors:
                    job.errors.extend(errors)
                    continue

                shot.compiled_prompt = prompt

                # Generate keyframe (if GrokController available)
                if self.grok_controller:
                    keyframe_path, _ = await self.grok_controller.generate_shot(
                        shot,
                        self.project_dir,
                    )

                    if keyframe_path:
                        job.keyframes_generated.append(str(keyframe_path))
                        shot.status = ShotStatus.KEYFRAME_GENERATED
                        shot.keyframe_path = str(keyframe_path)
                    else:
                        job.errors.append(f"Keyframe generation failed: {shot_id}")
                        job.failed_shots += 1
                        shot.status = ShotStatus.RETRY
                else:
                    # Simulation mode - just mark as complete
                    shot.keyframe_path = str(
                        self.keyframes_dir / f"{shot_id}.png"
                    )
                    shot.status = ShotStatus.KEYFRAME_GENERATED
                    job.keyframes_generated.append(shot.keyframe_path)

                job.completed_shots += 1

                # Save state after each shot
                self.state_manager.save_shotlist(self.shotlist)
                self._save_job_state(job)

            except Exception as e:
                job.errors.append(f"Error generating {shot_id}: {e}")
                job.failed_shots += 1
                shot.status = ShotStatus.FAILED
                shot.error_message = str(e)

        job.status = BatchStatus.KEYFRAMES_COMPLETE

        # Save final state
        self.state_manager.save_shotlist(self.shotlist)
        self._save_job_state(job)

        return job

    async def run_video_generation(
        self,
        job: Optional[BatchJob] = None,
    ) -> BatchJob:
        """
        Run video generation for all approved keyframes.

        Args:
            job: BatchJob to run

        Returns:
            Updated BatchJob
        """
        job = job or self.current_job
        if not job:
            raise ValueError("No batch job specified")

        if job.status != BatchStatus.KEYFRAMES_COMPLETE:
            raise ValueError(
                "Cannot run video generation - keyframes not complete"
            )

        job.current_stage = GenerationStage.VIDEOS
        job.completed_shots = 0  # Reset for this stage

        for shot_id in job.shot_ids:
            shot = self.shotlist.get_shot(shot_id)
            if not shot:
                continue

            if shot.status != ShotStatus.KEYFRAME_GENERATED:
                continue

            try:
                # Generate video from keyframe
                if self.grok_controller:
                    motion_prompt = self.compiler.compile_motion_prompt(shot)

                    _, video_path = await self.grok_controller.generate_shot(
                        shot,
                        self.project_dir,
                    )

                    if video_path:
                        job.videos_generated.append(str(video_path))
                        shot.status = ShotStatus.VIDEO_GENERATED
                        shot.video_path = str(video_path)
                    else:
                        job.errors.append(f"Video generation failed: {shot_id}")
                        job.failed_shots += 1
                        shot.status = ShotStatus.RETRY
                else:
                    # Simulation mode
                    shot.video_path = str(self.renders_dir / f"{shot_id}.mp4")
                    shot.status = ShotStatus.VIDEO_GENERATED
                    job.videos_generated.append(shot.video_path)

                job.completed_shots += 1

                # Save state
                self.state_manager.save_shotlist(self.shotlist)
                self._save_job_state(job)

            except Exception as e:
                job.errors.append(f"Error generating video for {shot_id}: {e}")
                job.failed_shots += 1
                shot.status = ShotStatus.FAILED
                shot.error_message = str(e)

        job.status = BatchStatus.VIDEOS_COMPLETE

        # Save final state
        self.state_manager.save_shotlist(self.shotlist)
        self._save_job_state(job)

        return job

    def run_assembly(
        self,
        job: Optional[BatchJob] = None,
        output_name: Optional[str] = None,
    ) -> Path:
        """
        Assemble all video clips into final timeline.

        Args:
            job: BatchJob to assemble
            output_name: Output filename (default: project_id)

        Returns:
            Path to assembled video
        """
        job = job or self.current_job
        if not job:
            raise ValueError("No batch job specified")

        if job.status != BatchStatus.VIDEOS_COMPLETE:
            raise ValueError("Cannot assemble - videos not complete")

        job.current_stage = GenerationStage.ASSEMBLY

        # Collect clips in order
        clips = []
        for shot_id in job.shot_ids:
            shot = self.shotlist.get_shot(shot_id)
            if shot and shot.video_path:
                video_path = Path(shot.video_path)
                audio_path = Path(shot.audio_path) if shot.audio_path else None
                clips.append((video_path, audio_path))

        if not clips:
            raise ValueError("No video clips to assemble")

        # Assemble
        assembler = FFmpegAssembly(self.renders_dir)
        output_name = output_name or f"{self.project_id}_final"
        output_path = self.exports_dir / f"{output_name}.mp4"

        result = assembler.assemble_timeline(clips, output_path)

        job.status = BatchStatus.ASSEMBLED
        job.completed_at = datetime.now()

        # Generate timeline exports
        self._generate_timeline_exports()

        # Save final state
        self._save_job_state(job)

        return result

    def _generate_timeline_exports(self) -> None:
        """Generate FCPXML, EDL, and Premiere exports."""
        exporter = TimelineExport(self.shotlist, self.bible.project_name)
        exporter.generate_all(self.exports_dir)

    def _save_job_state(self, job: BatchJob) -> None:
        """Save job state to disk."""
        job_state_path = self.project_dir / "batch_job.json"
        with open(job_state_path, "w") as f:
            json.dump(job.to_dict(), f, indent=2)

    def load_job_state(self) -> Optional[BatchJob]:
        """Load job state from disk."""
        job_state_path = self.project_dir / "batch_job.json"
        if not job_state_path.exists():
            return None

        with open(job_state_path) as f:
            data = json.load(f)

        return BatchJob.from_dict(data)

    def get_shot_preview(self, shot_id: str) -> dict:
        """
        Get preview information for a shot.

        Includes compiled prompt, DNA references, and status.
        """
        shot = self.shotlist.get_shot(shot_id)
        if not shot:
            return {"error": "Shot not found"}

        prompt, errors, warnings = self.compiler.compile_and_validate(
            shot,
            location_id=self.current_job.location_id if self.current_job else None,
            context_id=self.current_job.context_id if self.current_job else None,
        )

        return {
            "shot_id": shot.shot_id,
            "status": shot.status.value,
            "compiled_prompt": prompt,
            "character_ids": shot.character_ids,
            "action": shot.action_description,
            "camera": {
                "shot_size": shot.camera_specs.shot_size,
                "angle": shot.camera_specs.angle,
                "motion": shot.camera_specs.motion,
            },
            "duration": shot.duration_seconds,
            "errors": errors,
            "warnings": warnings,
            "keyframe_path": shot.keyframe_path,
            "video_path": shot.video_path,
        }

    def get_batch_summary(self) -> dict:
        """Get summary of batch generation status."""
        if not self.current_job:
            return {"error": "No active batch job"}

        return {
            "job_id": self.current_job.job_id,
            "project_id": self.current_job.project_id,
            "status": self.current_job.status.value,
            "stage": self.current_job.current_stage.value,
            "progress_percent": self.current_job.progress_percent,
            "total_shots": self.current_job.total_shots,
            "completed_shots": self.current_job.completed_shots,
            "failed_shots": self.current_job.failed_shots,
            "keyframes_generated": len(self.current_job.keyframes_generated),
            "videos_generated": len(self.current_job.videos_generated),
            "errors": self.current_job.errors,
        }

    def approve_keyframes(self) -> None:
        """
        Approve all generated keyframes for video generation.

        Called after human review of keyframes.
        """
        if not self.current_job:
            raise ValueError("No active batch job")

        if self.current_job.status != BatchStatus.KEYFRAMES_COMPLETE:
            raise ValueError("No keyframes to approve")

        # Update all keyframe shots to approved status
        for shot_id in self.current_job.shot_ids:
            shot = self.shotlist.get_shot(shot_id)
            if shot and shot.status == ShotStatus.KEYFRAME_GENERATED:
                shot.status = ShotStatus.KEYFRAME_APPROVED

        self.state_manager.save_shotlist(self.shotlist)

    def reject_keyframe(self, shot_id: str, reason: str) -> None:
        """
        Reject a specific keyframe for regeneration.

        Args:
            shot_id: Shot to reject
            reason: Reason for rejection
        """
        shot = self.shotlist.get_shot(shot_id)
        if not shot:
            raise ValueError(f"Shot not found: {shot_id}")

        shot.status = ShotStatus.KEYFRAME_REJECTED
        shot.error_message = reason

        # Remove from completed list
        if self.current_job:
            if shot_id in self.current_job.shot_ids:
                self.current_job.shot_ids.remove(shot_id)

        self.state_manager.save_shotlist(self.shotlist)
