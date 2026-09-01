"""
Streamlit Dashboard for GrokFilmStudio.

Web-based UI for project management and pipeline monitoring.
"""

import json
from pathlib import Path

import streamlit as st

from grokfilmstudio.compiler.prompt_compiler import PromptCompiler
from grokfilmstudio.compiler.script_parser import ScriptParser
from grokfilmstudio.models.production_bible import (
    AudioAnchor,
    CharacterAnchor,
    ProductionBible,
    WorldAnchor,
)
from grokfilmstudio.models.shotlist import ShotStatus
from grokfilmstudio.pipeline.timeline_export import TimelineExport
from grokfilmstudio.state import StatePersistenceManager

# Page config
st.set_page_config(
    page_title="GrokFilmStudio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
    <style>
    .main-header {font-size: 2rem; font-weight: bold; color: #1f77b4;}
    .sub-header {font-size: 1.2rem; color: #666;}
    .status-pending {color: #ffa500;}
    .status-complete {color: #22c55e;}
    .status-failed {color: #ef4444;}
    </style>
    """,
    unsafe_allow_html=True,
)


def init_session_state():
    """Initialize session state."""
    if "pm" not in st.session_state:
        st.session_state.pm = StatePersistenceManager()
    if "current_project" not in st.session_state:
        st.session_state.current_project = None
    if "bible" not in st.session_state:
        st.session_state.bible = None
    if "shotlist" not in st.session_state:
        st.session_state.shotlist = None
    if "state" not in st.session_state:
        st.session_state.state = None


def load_project(project_id: str):
    """Load project into session state."""
    pm = st.session_state.pm
    bible, shotlist, state = pm.recover_project(project_id)

    st.session_state.current_project = project_id
    st.session_state.bible = bible
    st.session_state.shotlist = shotlist
    st.session_state.state = state


def sidebar():
    """Render sidebar navigation."""
    st.sidebar.title("🎬 GrokFilmStudio")

    # Project selector
    pm = st.session_state.pm
    projects = []

    if st.session_state.pm.projects_dir.exists():
        projects = [
            d.name for d in st.session_state.pm.projects_dir.iterdir() if d.is_dir()
        ]

    selected_project = st.sidebar.selectbox(
        "Select Project",
        ["Create New..."] + projects,
        key="project_selector",
    )

    if selected_project == "Create New...":
        with st.sidebar.expander("New Project", expanded=True):
            new_name = st.text_input("Project Name", key="new_project_name")
            if st.button("Create Project"):
                if new_name:
                    project_id, bible, shotlist, state = pm.create_project(
                        project_name=new_name
                    )
                    st.success(f"Created: {project_id}")
                    load_project(project_id)
                    st.rerun()

    elif selected_project:
        if st.session_state.current_project != selected_project:
            load_project(selected_project)

        # Project info in sidebar
        if st.session_state.bible:
            st.sidebar.markdown(f"**Name:** {st.session_state.bible.project_name}")
            st.sidebar.markdown(f"**ID:** {st.session_state.current_project}")

            if st.session_state.shotlist:
                total = len(st.session_state.shotlist.shots)
                complete = sum(
                    1 for s in st.session_state.shotlist.shots if s.status == ShotStatus.COMPLETE
                )
                st.sidebar.progress(complete / total if total > 0 else 0)
                st.sidebar.text(f"{complete}/{total} shots complete")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Navigation")

    page = st.sidebar.radio(
        "Go to:",
        ["Overview", "Production Bible", "Character Sheet Builder", "Script & Shots", "Prompt Compiler", "Generate", "Export"],
        key="page_selector",
    )

    return page


def page_overview():
    """Render overview page."""
    st.markdown('<p class="main-header">Project Overview</p>', unsafe_allow_html=True)

    if not st.session_state.current_project:
        st.info("Select or create a project to get started.")
        return

    bible = st.session_state.bible
    shotlist = st.session_state.shotlist
    state = st.session_state.state

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Shots", len(shotlist.shots) if shotlist else 0)

    with col2:
        if shotlist:
            complete = sum(1 for s in shotlist.shots if s.status == ShotStatus.COMPLETE)
            st.metric("Complete", complete)
        else:
            st.metric("Complete", 0)

    with col3:
        st.metric("Characters", len(bible.character_anchors) if bible else 0)

    with col4:
        if state:
            st.metric("Current Phase", state.current_phase.value.replace("_", " ").title())
        else:
            st.metric("Current Phase", "N/A")

    # Project details
    st.markdown("### Project Details")

    if bible:
        st.json(
            {
                "project_id": bible.project_id,
                "project_name": bible.project_name,
                "created_at": str(bible.created_at),
                "logline": bible.logline,
                "world_style": bible.world_anchors.style_prompt if bible.world_anchors else "Not set",
            }
        )

    # Recent activity / shot status
    if shotlist and shotlist.shots:
        st.markdown("### Shot Status")

        status_counts = {}
        for shot in shotlist.shots:
            status = shot.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        status_cols = st.columns(len(status_counts))
        for i, (status, count) in enumerate(status_counts.items()):
            status_cols[i].metric(status.replace("_", " ").title(), count)


def page_production_bible():
    """Render production bible page."""
    st.markdown('<p class="main-header">Production Bible</p>', unsafe_allow_html=True)

    if not st.session_state.current_project:
        st.info("Select a project first.")
        return

    bible = st.session_state.bible
    pm = st.session_state.pm

    # Character Anchors
    st.markdown("### Character Anchors")

    if bible and bible.character_anchors:
        for char in bible.character_anchors:
            with st.expander(f"{char.name} ({char.character_id})"):
                st.text_area(
                    "DNA Prompt",
                    char.dna_prompt,
                    key=f"dna_{char.character_id}",
                    help="Max 150 characters, 3-4 distinct traits",
                )
                st.text_input(
                    "Reference Image",
                    char.master_reference_image or "",
                    key=f"ref_{char.character_id}",
                )
        st.success(f"{len(bible.character_anchors)} characters defined")
    else:
        st.warning("No characters defined yet.")

    # Add new character
    with st.expander("➕ Add Character"):
        with st.form("add_character_form"):
            new_name = st.text_input("Name")
            new_dna = st.text_area("DNA Prompt", help="Concise description, 3-4 traits")
            new_ref = st.text_input("Reference Image Path")

            if st.form_submit_button("Add Character"):
                if new_name and new_dna:
                    char = CharacterAnchor(name=new_name, dna_prompt=new_dna, master_reference_image=new_ref or None)
                    bible.add_character(char)
                    pm.save_bible(bible)
                    st.success(f"Added: {new_name}")
                    st.rerun()

    # World Anchors
    st.markdown("### World & Style Anchors")

    if bible and bible.world_anchors:
        world = bible.world_anchors
        st.text_input(
            "Style Prompt",
            world.style_prompt,
            key="style_prompt",
            on_change=lambda: save_world_changes(bible, pm),
        )
        st.selectbox(
            "Aspect Ratio",
            ["16:9", "9:16", "21:9", "1:1"],
            index=["16:9", "9:16", "21:9", "1:1"].index(world.aspect_ratio),
            key="aspect_ratio",
            on_change=lambda: save_world_changes(bible, pm),
        )
        st.text_input(
            "Color Grade",
            world.color_grade or "",
            key="color_grade",
            on_change=lambda: save_world_changes(bible, pm),
        )
    else:
        with st.form("set_world_form"):
            style = st.text_input("Style Prompt", placeholder="Cinematic 35mm, Kodak Portra 400...")
            aspect = st.selectbox("Aspect Ratio", ["16:9", "9:16", "21:9", "1:1"])
            color = st.text_input("Color Grade")

            if st.form_submit_button("Set World Anchor"):
                if style:
                    bible.world_anchors = WorldAnchor(
                        style_prompt=style,
                        aspect_ratio=aspect,
                        color_grade=color,
                    )
                    pm.save_bible(bible)
                    st.success("World anchor saved!")
                    st.rerun()


def save_world_changes(bible, pm):
    """Helper to save world anchor changes."""
    if bible.world_anchors:
        bible.world_anchors.style_prompt = st.session_state.style_prompt
        bible.world_anchors.aspect_ratio = st.session_state.aspect_ratio
        bible.world_anchors.color_grade = st.session_state.color_grade
        pm.save_bible(bible)


def page_script_shots():
    """Render script and shots page."""
    st.markdown('<p class="main-header">Script & Shotlist</p>', unsafe_allow_html=True)

    if not st.session_state.current_project:
        st.info("Select a project first.")
        return

    pm = st.session_state.pm
    bible = st.session_state.bible
    shotlist = st.session_state.shotlist

    # Script upload
    st.markdown("### Parse Script")

    uploaded = st.file_uploader("Upload Script", type=["txt", "md"])

    if uploaded:
        script_text = uploaded.read().decode("utf-8")

        col1, col2 = st.columns(2)
        with col1:
            duration = st.slider("Default Shot Duration", 1.0, 10.0, 3.0)
        with col2:
            format_type = st.selectbox("Format", ["auto", "synopsis", "treatment", "script"])

        if st.button("Parse Script"):
            parser = ScriptParser(bible, default_shot_duration=duration)
            shotlist = parser.auto_generate_shots(script_text, format=format_type)
            pm.save_shotlist(shotlist)
            st.session_state.shotlist = shotlist
            st.success(f"Parsed {len(shotlist.shots)} shots!")
            st.rerun()

    # Shot list
    if shotlist and shotlist.shots:
        st.markdown("### Shots")

        for i, shot in enumerate(shotlist.shots):
            with st.expander(
                f"{shot.shot_id} - {shot.status.value}",
                expanded=(i == 0),
            ):
                col1, col2 = st.columns(2)

                with col1:
                    st.text("Action Description")
                    st.write(shot.action_description)

                    st.text("Camera Specs")
                    if shot.camera_specs:
                        st.write(f"- Size: {shot.camera_specs.shot_size}")
                        st.write(f"- Angle: {shot.camera_specs.angle}")
                        st.write(f"- Motion: {shot.camera_specs.motion}")

                with col2:
                    st.text("Audio Script")
                    st.write(shot.audio_script or "N/A")

                    st.text("Duration")
                    st.write(f"{shot.duration_seconds}s")

                    st.text("Compiled Prompt")
                    st.code(shot.compiled_prompt or "Not compiled")


def page_prompt_compiler():
    """Render prompt compiler page."""
    st.markdown('<p class="main-header">Prompt Compiler</p>', unsafe_allow_html=True)

    if not st.session_state.current_project:
        st.info("Select a project first.")
        return

    bible = st.session_state.bible
    shotlist = st.session_state.shotlist
    pm = st.session_state.pm

    if not bible:
        st.error("Production bible not loaded.")
        return

    compiler = PromptCompiler(bible)

    # Compile all button
    if st.button("Compile All Prompts"):
        if shotlist:
            for shot in shotlist.shots:
                prompt, errors, warnings = compiler.compile_and_validate(shot)
                shot.compiled_prompt = prompt
            pm.save_shotlist(shotlist)
            st.success("All prompts compiled!")
            st.rerun()

    # Preview individual shots
    if shotlist and shotlist.shots:
        st.markdown("### Preview Prompts")

        shot_options = {s.shot_id: s for s in shotlist.shots}
        selected_id = st.selectbox("Select Shot", list(shot_options.keys()))

        if selected_id:
            shot = shot_options[selected_id]
            prompt, errors, warnings = compiler.compile_and_validate(shot)

            st.text_area("Compiled Prompt", prompt, height=150)

            if errors:
                st.error("Errors:")
                for e in errors:
                    st.write(f"- {e}")

            if warnings:
                st.warning("Warnings:")
                for w in warnings:
                    st.write(f"- {w}")


def page_generate():
    """Render generation page."""
    st.markdown('<p class="main-header">Generate</p>', unsafe_allow_html=True)

    st.info(
        "⚠️ Generation requires Grok credentials configured in `.env`\n\n"
        "Set `GROK_USERNAME` and `GROK_PASSWORD` before running generation."
    )

    if not st.session_state.current_project:
        st.info("Select a project first.")
        return

    shotlist = st.session_state.shotlist

    if shotlist:
        # Status overview
        status_counts = {}
        for shot in shotlist.shots:
            status = shot.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        st.metric("Shots Ready for Generation", status_counts.get("pending", 0))

        # Generation controls
        st.markdown("### Generation Controls")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🎬 Generate Keyframes", disabled=True):
                st.info("Browser automation not yet connected")

        with col2:
            if st.button("🎥 Generate Videos", disabled=True):
                st.info("Browser automation not yet connected")

        # Shot-by-shot status
        st.markdown("### Shot Status")

        for shot in shotlist.shots:
            cols = st.columns([1, 3, 1, 1])
            cols[0].write(shot.shot_id)
            cols[1].write(shot.action_description[:50] + "...")
            cols[2].write(shot.status.value)
            with cols[3]:
                if shot.status == ShotStatus.FAILED:
                    if st.button("Retry", key=f"retry_{shot.shot_id}"):
                        shot.status = ShotStatus.RETRY
                        st.rerun()


def page_export():
    """Render export page."""
    st.markdown('<p class="main-header">Export</p>', unsafe_allow_html=True)

    if not st.session_state.current_project:
        st.info("Select a project first.")
        return

    pm = st.session_state.pm
    shotlist = st.session_state.shotlist
    bible = st.session_state.bible

    if not shotlist:
        st.warning("No shotlist to export.")
        return

    # Timeline exports
    st.markdown("### Timeline Exports")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Export FCPXML"):
            exporter = TimelineExport(shotlist, bible.project_name if bible else "Project")
            output_dir = pm.get_project_dir(st.session_state.current_project) / "exports"
            path = exporter.to_fcpxml(output_dir / "timeline.fcpxml")
            st.success(f"Exported: {path}")

    with col2:
        if st.button("Export EDL"):
            exporter = TimelineExport(shotlist, bible.project_name if bible else "Project")
            output_dir = pm.get_project_dir(st.session_state.current_project) / "exports"
            path = exporter.to_edl(output_dir / "timeline.edl")
            st.success(f"Exported: {path}")

    with col3:
        if st.button("Export Premiere XML"):
            exporter = TimelineExport(shotlist, bible.project_name if bible else "Project")
            output_dir = pm.get_project_dir(st.session_state.current_project) / "exports"
            path = exporter.to_premiere_xml(output_dir / "timeline_premiere.xml")
            st.success(f"Exported: {path}")

    # FFmpeg assembly
    st.markdown("### FFmpeg Assembly")

    clips_ready = sum(1 for s in shotlist.shots if s.video_path)
    st.write(f"Clips ready for assembly: {clips_ready}")

    if st.button("Assemble Final Video"):
        st.info("FFmpeg assembly would run here")


# Import Character Sheet Builder
from grokfilmstudio.models.character_sheet import CharacterSheet, CharacterSheetBuilder


def page_character_sheet_builder():
    """Render Character Sheet Builder page."""
    st.markdown('<p class="main-header">Character Sheet Builder</p>', unsafe_allow_html=True)

    if not st.session_state.current_project:
        st.info("Select a project first.")
        return

    # Import the dedicated builder module
    from ui.character_sheet_builder import render_character_sheet_builder
    render_character_sheet_builder()


# Main app
def main():
    init_session_state()

    page = sidebar()

    if page == "Overview":
        page_overview()
    elif page == "Production Bible":
        page_production_bible()
    elif page == "Character Sheet Builder":
        page_character_sheet_builder()
    elif page == "Script & Shots":
        page_script_shots()
    elif page == "Prompt Compiler":
        page_prompt_compiler()
    elif page == "Generate":
        page_generate()
    elif page == "Export":
        page_export()


if __name__ == "__main__":
    main()
