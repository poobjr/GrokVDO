"""Tests for the Prompt Compiler module."""

import pytest

from grokfilmstudio.models.production_bible import (
    CharacterAnchor,
    ProductionBible,
    WorldAnchor,
)
from grokfilmstudio.models.shotlist import CameraSpecs, Shot
from grokfilmstudio.compiler.prompt_compiler import PromptCompiler


@pytest.fixture
def sample_bible():
    """Create a sample production bible for testing."""
    bible = ProductionBible(project_name="Test Project")

    bible.add_character(
        CharacterAnchor(
            name="John Doe",
            dna_prompt="Middle-aged man, graying beard, leather jacket, scar on left cheek",
        )
    )

    bible.world_anchors = WorldAnchor(
        style_prompt="Cinematic 35mm, noir lighting, high contrast",
        aspect_ratio="16:9",
        color_grade="Desaturated, cool tones",
    )

    return bible


@pytest.fixture
def sample_shot():
    """Create a sample shot for testing."""
    return Shot(
        shot_id="SC01_SH01",
        scene_number=1,
        character_ids=["CHAR_001"],
        action_description="John turns to face the camera menacingly",
        camera_specs=CameraSpecs(
            shot_size="Medium Close-up",
            angle="Low Angle",
            motion="Slow Pan Right",
        ),
        duration_seconds=3.0,
    )


def test_compile_image_prompt(sample_bible, sample_shot):
    """Test basic image prompt compilation."""
    compiler = PromptCompiler(sample_bible)
    prompt = compiler.compile_image_prompt(sample_shot)

    # Should contain character DNA
    assert "leather jacket" in prompt

    # Should contain action
    assert "turns to face" in prompt

    # Should contain camera specs
    assert "Medium Close-up" in prompt
    assert "Low Angle" in prompt

    # Should contain world style
    assert "Cinematic 35mm" in prompt


def test_compile_motion_prompt_static(sample_bible):
    """Test motion prompt for static shot."""
    compiler = PromptCompiler(sample_bible)

    shot = Shot(
        shot_id="SC01_SH02",
        action_description="John stares intently",
        camera_specs=CameraSpecs(shot_size="Close-up", motion="Static"),
    )

    prompt = compiler.compile_motion_prompt(shot)
    assert "Subtle natural movement" in prompt or "breathing" in prompt


def test_compile_motion_prompt_motion(sample_bible):
    """Test motion prompt with camera motion."""
    compiler = PromptCompiler(sample_bible)

    shot = Shot(
        shot_id="SC01_SH03",
        action_description="John walks across the room",
        camera_specs=CameraSpecs(shot_size="Wide", motion="Tracking"),
    )

    prompt = compiler.compile_motion_prompt(shot)
    assert "Tracking" in prompt


def test_validate_prompt_length(sample_bible):
    """Test prompt length validation."""
    compiler = PromptCompiler(sample_bible)

    # Short prompt - should be valid
    is_valid, warnings = compiler.validate_prompt_length("Short prompt")
    assert is_valid
    assert len(warnings) == 0

    # Long prompt - should warn
    long_prompt = "x" * 450
    is_valid, warnings = compiler.validate_prompt_length(long_prompt)
    assert is_valid  # Under max
    assert len(warnings) > 0

    # Too long - should be invalid
    too_long = "x" * 600
    is_valid, warnings = compiler.validate_prompt_length(too_long)
    assert not is_valid


def test_detect_prompt_bloat(sample_bible):
    """Test bloat detection."""
    compiler = PromptCompiler(sample_bible)

    bloated = "Highly detailed, beautiful, stunning masterpiece with intricate details"
    warnings = compiler.detect_prompt_bloat(bloated)

    assert len(warnings) > 0
    assert any("highly detailed" in w for w in warnings)


def test_compile_and_validate(sample_bible, sample_shot):
    """Test full compilation with validation."""
    compiler = PromptCompiler(sample_bible)

    prompt, errors, warnings = compiler.compile_and_validate(sample_shot)

    assert prompt is not None
    assert isinstance(errors, list)
    assert isinstance(warnings, list)


def test_missing_character_dna(sample_bible):
    """Test error when character DNA is missing."""
    compiler = PromptCompiler(sample_bible)

    shot = Shot(
        shot_id="SC01_SH04",
        character_ids=["CHAR_UNKNOWN"],
        action_description="Someone walks in",
        camera_specs=CameraSpecs(shot_size="Medium"),
    )

    _, errors, _ = compiler.compile_and_validate(shot)

    assert len(errors) > 0
    assert "Missing character DNA" in errors[0]
