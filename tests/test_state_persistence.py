"""Tests for the State Persistence Manager."""

import json
import tempfile
from pathlib import Path

import pytest

from grokfilmstudio.models.production_bible import ProductionBible
from grokfilmstudio.models.shotlist import Shot, Shotlist
from grokfilmstudio.models.project_state import ProjectState
from grokfilmstudio.state import StatePersistenceManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def pm(temp_dir):
    """Create a state persistence manager with temp directory."""
    return StatePersistenceManager(projects_dir=temp_dir)


@pytest.fixture
def sample_bible():
    """Create a sample production bible."""
    bible = ProductionBible(project_name="Test Project")
    return bible


@pytest.fixture
def sample_shotlist(sample_bible):
    """Create a sample shotlist."""
    shotlist = Shotlist(project_id=sample_bible.project_id)
    shotlist.add_shot(
        Shot(
            shot_id="SC01_SH01",
            scene_number=1,
            action_description="Test action",
            camera_specs={"shot_size": "Medium", "angle": "Eye Level", "motion": "Static"},
        )
    )
    return shotlist


def test_create_project(pm, sample_bible):
    """Test project creation."""
    project_id, bible, shotlist, state = pm.create_project(
        project_name="New Project",
        bible=sample_bible,
    )

    assert project_id is not None
    assert bible.project_name == "New Project"
    assert shotlist.project_id == project_id
    assert state.project_id == project_id


def test_save_and_load_bible(pm, sample_bible):
    """Test saving and loading production bible."""
    pm.save_bible(sample_bible)

    loaded = pm.load_bible(sample_bible.project_id)

    assert loaded is not None
    assert loaded.project_id == sample_bible.project_id
    assert loaded.project_name == sample_bible.project_name


def test_save_and_load_shotlist(pm, sample_shotlist):
    """Test saving and loading shotlist."""
    pm.save_shotlist(sample_shotlist)

    loaded = pm.load_shotlist(sample_shotlist.project_id)

    assert loaded is not None
    assert loaded.project_id == sample_shotlist.project_id
    assert len(loaded.shots) == len(sample_shotlist.shots)


def test_save_and_load_state(pm):
    """Test saving and loading project state."""
    state = ProjectState(project_id="PROJ_TEST")

    pm.save_state(state)

    loaded = pm.load_state("PROJ_TEST")

    assert loaded is not None
    assert loaded.project_id == state.project_id


def test_recover_project(pm, sample_bible, sample_shotlist):
    """Test full project recovery."""
    # Save all components
    pm.save_bible(sample_bible)
    pm.save_shotlist(sample_shotlist)

    state = ProjectState(project_id=sample_bible.project_id)
    pm.save_state(state)

    # Recover
    bible, shotlist, state = pm.recover_project(sample_bible.project_id)

    assert bible is not None
    assert shotlist is not None
    assert state is not None


def test_project_directory_creation(pm, sample_bible):
    """Test that project directories are created properly."""
    project_dir = pm.get_project_dir(sample_bible.project_id)

    assert project_dir.exists()
    assert (project_dir / "renders").exists()
    assert (project_dir / "keyframes").exists()
    assert (project_dir / "audio").exists()


def test_atomic_write(pm):
    """Test atomic write creates backup."""
    test_path = pm.projects_dir / "test.json"
    test_data = {"key": "value"}

    # First write
    pm._atomic_write(test_path, test_data)

    # Second write should create backup
    pm._atomic_write(test_path, {"key": "new_value"})

    # Backup should exist
    backup_path = test_path.with_suffix(".json.bak")
    assert backup_path.exists()

    # Backup should have original data
    with open(backup_path) as f:
        backup_data = json.load(f)
    assert backup_data["key"] == "value"


def test_load_nonexistent_returns_none(pm):
    """Test that loading nonexistent files returns None."""
    assert pm.load_bible("NONEXISTENT") is None
    assert pm.load_shotlist("NONEXISTENT") is None
    assert pm.load_state("NONEXISTENT") is None
