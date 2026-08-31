"""
State Persistence Manager.

Handles loading, saving, and recovery of project state from JSON files.
Enables crash recovery and resume functionality.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, TypeVar

from pydantic import BaseModel

from grokfilmstudio.config import Settings, settings
from grokfilmstudio.models.production_bible import ProductionBible
from grokfilmstudio.models.project_state import (
    PipelinePhase,
    ProjectState,
)
from grokfilmstudio.models.shotlist import Shotlist

T = TypeVar("T", bound=BaseModel)


class StatePersistenceManager:
    """
    Manages persistence of project state to JSON files.

    Features:
    - Atomic writes (write to temp, then rename)
    - Automatic backup before overwrites
    - Type-safe loading with validation
    - Recovery from crashed states
    """

    def __init__(self, projects_dir: Optional[Path] = None):
        """
        Initialize the persistence manager.

        Args:
            projects_dir: Base directory for projects (defaults to config)
        """
        self.projects_dir = projects_dir or settings.projects_dir
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def get_project_dir(self, project_id: str) -> Path:
        """Get the directory for a specific project."""
        project_dir = self.projects_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (project_dir / "renders").mkdir(exist_ok=True)
        (project_dir / "keyframes").mkdir(exist_ok=True)
        (project_dir / "audio").mkdir(exist_ok=True)

        return project_dir

    def get_bible_path(self, project_id: str) -> Path:
        """Get path to production bible JSON file."""
        return self.get_project_dir(project_id) / "production_bible.json"

    def get_shotlist_path(self, project_id: str) -> Path:
        """Get path to shotlist JSON file."""
        return self.get_project_dir(project_id) / "shotlist.json"

    def get_state_path(self, project_id: str) -> Path:
        """Get path to project state JSON file."""
        return self.get_project_dir(project_id) / "state.json"

    def _atomic_write(self, path: Path, data: dict) -> None:
        """
        Write data atomically to avoid corruption on crash.

        Writes to temp file first, then renames.
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        # Create backup if file exists
        if path.exists():
            backup_path = path.with_suffix(".json.bak")
            shutil.copy2(path, backup_path)

        # Write to temp file
        temp_path = path.with_suffix(".json.tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        # Atomic rename
        temp_path.rename(path)

    def _load_json(self, path: Path) -> Optional[dict]:
        """Load JSON file, return None if not exists."""
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # Production Bible operations

    def save_bible(self, bible: ProductionBible) -> None:
        """Save production bible to disk."""
        path = self.get_bible_path(bible.project_id)
        self._atomic_write(path, bible.model_dump())

    def load_bible(self, project_id: str) -> Optional[ProductionBible]:
        """Load production bible from disk."""
        path = self.get_bible_path(project_id)
        data = self._load_json(path)
        if data is None:
            return None
        return ProductionBible.model_validate(data)

    # Shotlist operations

    def save_shotlist(self, shotlist: Shotlist) -> None:
        """Save shotlist to disk."""
        path = self.get_shotlist_path(shotlist.project_id)
        self._atomic_write(path, shotlist.model_dump())

    def load_shotlist(self, project_id: str) -> Optional[Shotlist]:
        """Load shotlist from disk."""
        path = self.get_shotlist_path(project_id)
        data = self._load_json(path)
        if data is None:
            return None
        return Shotlist.model_validate(data)

    # Project State operations

    def save_state(self, state: ProjectState) -> None:
        """Save project state to disk."""
        path = self.get_state_path(state.project_id)
        self._atomic_write(path, state.model_dump())

    def load_state(self, project_id: str) -> Optional[ProjectState]:
        """Load project state from disk."""
        path = self.get_state_path(project_id)
        data = self._load_json(path)
        if data is None:
            return None
        return ProjectState.model_validate(data)

    # Recovery operations

    def recover_project(
        self, project_id: str
    ) -> tuple[Optional[ProductionBible], Optional[Shotlist], Optional[ProjectState]]:
        """
        Recover all project data from disk.

        Returns:
            Tuple of (bible, shotlist, state) - any may be None if not found
        """
        bible = self.load_bible(project_id)
        shotlist = self.load_shotlist(project_id)
        state = self.load_state(project_id)
        return bible, shotlist, state

    def get_resume_point(
        self, project_id: str
    ) -> Optional[tuple[PipelinePhase, int]]:
        """
        Get the resume point for a project.

        Returns:
            Tuple of (phase, shot_index) or None if no recovery needed
        """
        state = self.load_state(project_id)
        if state is None:
            return None

        # Find first incomplete shot
        for i, shot_progress in enumerate(state.shot_progress.values()):
            if shot_progress.status not in ["complete", "failed"]:
                return (state.current_phase, i)

        return None

    def create_project(
        self,
        project_name: str,
        bible: Optional[ProductionBible] = None,
        shotlist: Optional[Shotlist] = None,
    ) -> tuple[str, ProductionBible, Shotlist, ProjectState]:
        """
        Create a new project with initial state.

        Args:
            project_name: Name for the project
            bible: Optional pre-configured production bible
            shotlist: Optional pre-configured shotlist

        Returns:
            Tuple of (project_id, bible, shotlist, state)
        """
        # Create bible if not provided
        if bible is None:
            bible = ProductionBible(project_name=project_name)

        # Create shotlist if not provided
        if shotlist is None:
            shotlist = Shotlist(project_id=bible.project_id)

        # Create initial state
        state = ProjectState(project_id=bible.project_id)

        # Save all
        self.save_bible(bible)
        self.save_shotlist(shotlist)
        self.save_state(state)

        return bible.project_id, bible, shotlist, state

    def export_project(self, project_id: str, output_path: Path) -> None:
        """
        Export complete project to a single JSON file.

        Useful for backup or transfer.
        """
        bible, shotlist, state = self.recover_project(project_id)

        export_data = {
            "exported_at": datetime.now().isoformat(),
            "project_id": project_id,
            "production_bible": bible.model_dump() if bible else None,
            "shotlist": shotlist.model_dump() if shotlist else None,
            "project_state": state.model_dump() if state else None,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, default=str)

    def import_project(self, import_path: Path) -> str:
        """
        Import project from an export file.

        Returns:
            project_id of imported project
        """
        with open(import_path, "r", encoding="utf-8") as f:
            import_data = json.load(f)

        # Load components
        if import_data.get("production_bible"):
            bible = ProductionBible.model_validate(import_data["production_bible"])
        else:
            raise ValueError("Import file missing production bible")

        if import_data.get("shotlist"):
            shotlist = Shotlist.model_validate(import_data["shotlist"])
        else:
            shotlist = Shotlist(project_id=bible.project_id)

        if import_data.get("project_state"):
            state = ProjectState.model_validate(import_data["project_state"])
        else:
            state = ProjectState(project_id=bible.project_id)

        # Save all
        self.save_bible(bible)
        self.save_shotlist(shotlist)
        self.save_state(state)

        return bible.project_id
