"""
Character Sheet Builder UI.

Streamlit-based UI for creating detailed character sheets.
"""

import streamlit as st
from datetime import datetime
from pathlib import Path

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
from grokfilmstudio.state import StatePersistenceManager


def render_character_sheet_builder():
    """Render the Character Sheet Builder UI."""

    st.set_page_config(
        page_title="Character Sheet Builder",
        page_icon="🎭",
        layout="wide",
    )

    st.title("🎭 Character Sheet Builder")
    st.markdown("สร้าง Character Sheet แบบละเอียดเพื่อความคงท่ีของตวละคร")

    # Sidebar - Project selection
    st.sidebar.header("Project Selection")
    pm = StatePersistenceManager()

    projects = []
    if pm.projects_dir.exists():
        projects = [d.name for d in pm.projects_dir.iterdir() if d.is_dir()]

    selected_project = st.sidebar.selectbox(
        "Select Project",
        ["Create New..."] + projects,
    )

    if selected_project == "Create New...":
        with st.sidebar.expander("New Project", expanded=True):
            new_name = st.text_input("Project Name", key="new_proj_name")
            if st.button("Create Project"):
                if new_name:
                    project_id, bible, shotlist, state = pm.create_project(
                        project_name=new_name
                    )
                    st.success(f"Created: {project_id}")
                    st.rerun()
        st.stop()

    if not selected_project:
        st.info("Please select or create a project")
        st.stop()

    # Load project
    bible, shotlist, state = pm.recover_project(selected_project)
    if not bible:
        st.error("Project not found")
        st.stop()

    st.sidebar.success(f"**Project:** {bible.project_name}")

    # Main content - Tabs for different sections
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📋 Basic Info",
        "👤 Physical Attributes",
        "👔 Style & Wardrobe",
        "💭 Personality",
        "😊 Face Chart",
        "📸 References",
    ])

    # Initialize session state for character data
    if "char_name" not in st.session_state:
        st.session_state.char_name = ""
    if "char_data" not in st.session_state:
        st.session_state.char_data = {}

    # Tab 1: Basic Info
    with tab1:
        render_basic_info_tab()

    # Tab 2: Physical Attributes
    with tab2:
        render_physical_attributes_tab()

    # Tab 3: Style & Wardrobe
    with tab3:
        render_style_tab()

    # Tab 4: Personality
    with tab4:
        render_personality_tab()

    # Tab 5: Face Chart
    with tab5:
        render_face_chart_tab()

    # Tab 6: References & Export
    with tab6:
        render_references_tab(selected_project, bible)


def render_basic_info_tab():
    """Render Basic Info tab."""
    st.header("📋 Basic Information")

    col1, col2 = st.columns(2)

    with col1:
        st.session_state.char_name = st.text_input(
            "Character Name",
            value=st.session_state.char_name,
            placeholder="e.g., Sarah Chen",
        )

        st.session_state.char_data["age_range"] = st.selectbox(
            "Age Range",
            ["18-24", "25-35", "36-50", "51-65", "65+", "Child (5-12)", "Teen (13-17)"],
            index=1,
        )

        st.session_state.char_data["gender"] = st.selectbox(
            "Gender",
            ["female", "male", "non-binary", "other"],
            index=0,
        )

        st.session_state.char_data["height"] = st.text_input(
            "Height",
            value="165 cm",
            placeholder="e.g., 165 cm, 5'6\"",
        )

    with col2:
        st.session_state.char_data["body_type"] = st.selectbox(
            "Body Type",
            ["petite", "slim", "athletic", "average", "curvy", "muscular", "heavy"],
            index=3,
        )

        st.session_state.char_data["occupation"] = st.text_input(
            "Occupation/Role",
            placeholder="e.g., Detective, Student, Warrior",
        )

        st.session_state.char_data["background"] = st.text_area(
            "Background (brief)",
            placeholder="One or two sentences about character's backstory...",
            height=100,
        )

    st.divider()

    # Preview
    if st.session_state.char_name:
        st.subheader("Preview")
        preview = f"**{st.session_state.char_name}** | "
        preview += f"{st.session_state.char_data.get('age_range', 'Unknown')} | "
        preview += f"{st.session_state.char_data.get('gender', 'Unknown').title()} | "
        preview += f"{st.session_state.char_data.get('body_type', 'average').title()} build"
        st.markdown(preview)


def render_physical_attributes_tab():
    """Render Physical Attributes tab."""
    st.header("👤 Physical Attributes")

    st.markdown("### Face & Head")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.session_state.char_data["face_shape"] = st.selectbox(
            "Face Shape",
            ["oval", "round", "square", "heart", "long", "diamond"],
            index=0,
        )

        st.session_state.char_data["eye_color"] = st.selectbox(
            "Eye Color",
            ["brown", "blue", "green", "hazel", "gray", "amber", "violet"],
            index=0,
        )

        st.session_state.char_data["eye_shape"] = st.text_input(
            "Eye Shape",
            placeholder="e.g., almond, round, hooded",
        )

    with col2:
        st.session_state.char_data["eyebrows"] = st.text_input(
            "Eyebrows",
            placeholder="e.g., thick arched, thin straight",
        )

        st.session_state.char_data["nose"] = st.text_input(
            "Nose",
            placeholder="e.g., straight, button, aquiline",
        )

        st.session_state.char_data["lips"] = st.text_input(
            "Lips",
            placeholder="e.g., full, thin, bow-shaped",
        )

    with col3:
        st.session_state.char_data["jawline"] = st.text_input(
            "Jawline",
            placeholder="e.g., strong square, soft round",
        )

        st.session_state.char_data["facial_hair"] = st.text_input(
            "Facial Hair",
            placeholder="e.g., clean shaven, stubble, full beard",
        )

    st.markdown("### Hair")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.session_state.char_data["hair_style"] = st.selectbox(
            "Hair Style",
            [
                "long straight",
                "long wavy",
                "long curly",
                "shoulder-length",
                "bob cut",
                "pixie cut",
                "buzz cut",
                "bald",
                "ponytail",
                "bun",
                "braids",
                "afro",
                "mohawk",
                "undercut",
            ],
            index=0,
        )

        st.session_state.char_data["hair_color"] = st.text_input(
            "Hair Color",
            value="black",
            placeholder="e.g., black, blonde, red with gray streaks",
        )

    with col2:
        st.session_state.char_data["hair_texture"] = st.text_input(
            "Hair Texture",
            placeholder="e.g., fine, thick, coarse",
        )

    st.markdown("### Skin")

    col1, col2 = st.columns(2)

    with col1:
        st.session_state.char_data["skin_tone"] = st.selectbox(
            "Skin Tone",
            [
                "very fair (porcelain)",
                "fair (light)",
                "medium (olive)",
                "olive",
                "brown",
                "dark brown",
                "deep (ebony)",
            ],
            index=2,
        )

    with col2:
        st.session_state.char_data["skin_details"] = st.text_area(
            "Skin Details",
            placeholder="e.g., freckles on cheeks, scar on forehead, dimples",
            height=80,
        )

    st.markdown("### Distinguishing Features")

    st.session_state.char_data["distinguishing_features"] = st.text_area(
        "Distinguishing Features",
        placeholder="e.g., tattoo on left arm, mole above lip, pierced ears",
        height=80,
    )

    st.divider()

    # DNA Preview
    if st.button("Generate DNA Preview", key="dna_preview"):
        dna = generate_dna_preview()
        st.success("**DNA Prompt:** " + dna)


def render_style_tab():
    """Render Style & Wardrobe tab."""
    st.header("👔 Style & Wardrobe")

    st.markdown("### Overall Style")

    style_keywords = st.text_input(
        "Style Keywords (comma-separated)",
        placeholder="e.g., edgy, minimalist, bohemian, vintage",
    )
    st.session_state.char_data["style_keywords"] = [
        s.strip() for s in style_keywords.split(",") if s.strip()
    ]

    st.markdown("### Signature Look")

    col1, col2 = st.columns(2)

    with col1:
        st.session_state.char_data["signature_colors"] = st.text_area(
            "Signature Colors",
            placeholder="e.g., red, black, denim blue",
            height=80,
        )

        st.session_state.char_data["signature_items"] = st.text_area(
            "Signature Wardrobe Items",
            placeholder="e.g., leather jacket, combat boots, silver necklace",
            height=80,
        )

    with col2:
        st.session_state.char_data["accessories"] = st.text_area(
            "Regular Accessories",
            placeholder="e.g., leather watch, pearl earrings, leather belt",
            height=80,
        )

        st.session_state.char_data["style_notes"] = st.text_area(
            "Style Notes",
            placeholder="Any additional notes about character's style...",
            height=80,
        )

    st.divider()

    # Style examples
    st.markdown("### Outfit Examples")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.text_area(
            "Casual Outfit",
            placeholder="Describe their casual look...",
            height=100,
            key="outfit_casual",
        )

    with col2:
        st.text_area(
            "Formal Outfit",
            placeholder="Describe their formal look...",
            height=100,
            key="outfit_formal",
        )

    with col3:
        st.text_area(
            "Action/Work Outfit",
            placeholder="Describe their action/work look...",
            height=100,
            key="outfit_action",
        )


def render_personality_tab():
    """Render Personality tab."""
    st.header("💭 Personality & Voice")

    st.markdown("### Personality Traits")

    personality_options = [
        "confident", "shy", "outgoing", "reserved",
        "optimistic", "pessimistic", "serious", "playful",
        "aggressive", "gentle", "mysterious", "charismatic",
        "nervous", "calm", "intense",
    ]

    selected_traits = st.multiselect(
        "Select Personality Traits (up to 5)",
        personality_options,
        default=[],
        max_selections=5,
    )
    st.session_state.char_data["personality_traits"] = selected_traits

    st.markdown("### Personality Notes")

    st.session_state.char_data["personality_notes"] = st.text_area(
        "How Personality Affects Physical Presence",
        placeholder="e.g., 'Walks with confident stride, maintains strong eye contact, gestures frequently when speaking'",
        height=100,
    )

    st.divider()

    st.markdown("### Voice Description (for TTS)")

    st.session_state.char_data["voice_description"] = st.text_area(
        "Voice Description",
        placeholder="e.g., 'Deep raspy voice, mid-Atlantic accent, speaks slowly and deliberately'",
        height=100,
    )

    col1, col2 = st.columns(2)

    with col1:
        st.session_state.char_data["voice_pitch"] = st.select_slider(
            "Voice Pitch",
            ["Very Low", "Low", "Medium-Low", "Medium", "Medium-High", "High", "Very High"],
            value="Medium",
        )

    with col2:
        st.session_state.char_data["voice_tempo"] = st.select_slider(
            "Speech Tempo",
            ["Very Slow", "Slow", "Medium-Slow", "Medium", "Medium-Fast", "Fast", "Very Fast"],
            value="Medium",
        )


def render_face_chart_tab():
    """Render Face Chart tab."""
    st.header("😊 Face Chart - Expressions")

    st.markdown("""
    Define how your character looks with different expressions.
    This helps maintain consistency across different emotional shots.
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Neutral Expression**")
        st.session_state.char_data["expr_neutral"] = st.text_area(
            "Neutral",
            placeholder="Describe neutral expression...",
            height=60,
            value="Relaxed face, slight natural smile, eyes calm",
        )

        st.markdown("**Smile Expression**")
        st.session_state.char_data["expr_smile"] = st.text_area(
            "Smile",
            placeholder="Describe smile...",
            height=60,
            value="Wide genuine smile showing upper teeth, eyes crinkle at corners",
        )

        st.markdown("**Serious Expression**")
        st.session_state.char_data["expr_serious"] = st.text_area(
            "Serious",
            placeholder="Describe serious look...",
            height=60,
            value="Jaw set firm, eyebrows slightly furrowed, intense gaze",
        )

    with col2:
        st.markdown("**Angry Expression**")
        st.session_state.char_data["expr_angry"] = st.text_area(
            "Angry",
            placeholder="Describe angry expression...",
            height=60,
            value="Eyebrows drawn together, nostrils flare, lips pressed tight",
        )

        st.markdown("**Surprised Expression**")
        st.session_state.char_data["expr_surprised"] = st.text_area(
            "Surprised",
            placeholder="Describe surprised look...",
            height=60,
            value="Eyes wide, eyebrows raised, mouth slightly open",
        )

        st.markdown("**Sad Expression**")
        st.session_state.char_data["expr_sad"] = st.text_area(
            "Sad",
            placeholder="Describe sad expression...",
            height=60,
            value="Corners of mouth turned down, eyes downcast, slight frown",
        )

    st.divider()

    st.markdown("### Expression Notes")

    st.session_state.char_data["expression_notes"] = st.text_area(
        "How Expressions Affect Facial Features",
        placeholder="e.g., 'When smiling, deep dimples appear on both cheeks. When angry, prominent forehead wrinkles.'",
        height=80,
    )


def render_references_tab(project_id, bible):
    """Render References & Export tab."""
    st.header("📸 References & Export")

    st.markdown("### Reference Images")

    st.info("Upload reference images for your character (optional)")

    col1, col2 = st.columns(2)

    with col1:
        st.file_uploader(
            "Front View Reference",
            type=["png", "jpg", "jpeg"],
            key="ref_front",
        )

        st.file_uploader(
            "Profile View Reference",
            type=["png", "jpg", "jpeg"],
            key="ref_profile",
        )

    with col2:
        st.file_uploader(
            "Full Body Reference",
            type=["png", "jpg", "jpeg"],
            key="ref_fullbody",
        )

        st.file_uploader(
            "Expression Sheet Reference",
            type=["png", "jpg", "jpeg"],
            key="ref_expressions",
        )

    st.divider()

    st.markdown("### Create Character Sheet")

    if st.button("🎭 Generate Character Sheet", type="primary", size="large"):
        # Build character sheet
        char_sheet = build_character_sheet(project_id)

        # Display preview
        st.success("Character Sheet Generated!")

        # Show DNA prompt
        st.markdown("**DNA Prompt:**")
        st.code(char_sheet.get_dna_prompt(), language="text")

        # Show full description
        st.markdown("**Full Description:**")
        st.write(char_sheet.get_full_description())

        # Export options
        st.markdown("### Export Options")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("💾 Save to Project", width="full"):
                save_to_project(char_sheet, project_id, bible)
                st.success("Saved to Production Bible!")

        with col2:
            if st.button("📄 Export JSON", width="full"):
                export_json(char_sheet)

        with col3:
            if st.button("📋 Copy DNA", width="full"):
                st.code(char_sheet.get_dna_prompt(), language="text")


def generate_dna_preview() -> str:
    """Generate DNA preview from current form data."""
    data = st.session_state.char_data

    parts = []

    # Age and gender
    age = data.get("age_range", "25-35")
    gender = data.get("gender", "female")
    parts.append(f"{age.replace('-', '-year-old ')} {gender}")

    # Body type
    body = data.get("body_type", "average")
    if body != "average":
        parts.append(f"{body} build")

    # Hair
    hair_style = data.get("hair_style", "long straight")
    hair_color = data.get("hair_color", "black")
    parts.append(f"{hair_style} {hair_color} hair")

    # Face shape
    face = data.get("face_shape", "oval")
    if face != "oval":
        parts.append(f"{face} face")

    # Eye color
    eyes = data.get("eye_color", "brown")
    if eyes != "brown":
        parts.append(f"{eyes} eyes")

    # Distinguishing features
    features = data.get("distinguishing_features", "")
    if features:
        parts.append(features)

    return ", ".join(parts)


def build_character_sheet(project_id: str) -> CharacterSheet:
    """Build CharacterSheet from form data."""
    data = st.session_state.char_data
    name = st.session_state.char_name or "Unnamed Character"

    builder = CharacterSheetBuilder(name, project_id)

    # Physical attributes
    builder.physical_attributes(
        age_range=data.get("age_range", "25-35"),
        gender=Gender(data.get("gender", "female")),
        height=data.get("height", "165 cm"),
        body_type=BodyType(data.get("body_type", "average")),
        face_shape=FaceShape(data.get("face_shape", "oval")),
        eye_color=EyeColor(data.get("eye_color", "brown")),
        hair_style=HairStyle(data.get("hair_style", "long straight")),
        hair_color=data.get("hair_color", "black"),
        skin_tone=SkinTone(data.get("skin_tone", "medium (olive)")),
        distinguishing_features=[
            f.strip()
            for f in data.get("distinguishing_features", "").split(",")
            if f.strip()
        ],
    )

    # Style
    builder.style_preferences(
        style_keywords=data.get("style_keywords", []),
        signature_colors=[
            c.strip()
            for c in data.get("signature_colors", "").split(",")
            if c.strip()
        ],
        signature_items=[
            i.strip()
            for i in data.get("signature_items", "").split(",")
            if i.strip()
        ],
        accessories=[
            a.strip()
            for a in data.get("accessories", "").split(",")
            if a.strip()
        ],
    )

    # Personality
    personality_traits = [
        PersonalityTrait(t)
        for t in data.get("personality_traits", [])
        if t in [e.value for e in PersonalityTrait]
    ]
    builder.personality(
        traits=personality_traits,
        notes=data.get("personality_notes"),
    )

    # Voice
    if data.get("voice_description"):
        builder.voice(data["voice_description"])

    # Background
    if data.get("background"):
        builder.background(data["background"])

    return builder.build()


def save_to_project(char_sheet: CharacterSheet, project_id: str, bible):
    """Save character sheet to production bible."""
    from grokfilmstudio.models.production_bible import CharacterAnchor
    from grokfilmstudio.state import StatePersistenceManager

    pm = StatePersistenceManager()

    # Create CharacterAnchor from sheet
    anchor = CharacterAnchor(
        character_id=char_sheet.character_id,
        name=char_sheet.character_name,
        dna_prompt=char_sheet.get_dna_prompt(),
        notes=char_sheet.get_full_description(),
    )

    bible.add_character(anchor)
    pm.save_bible(bible)

    # Also save full character sheet
    sheet_path = pm.get_project_dir(project_id) / "character_sheets"
    sheet_path.mkdir(exist_ok=True)

    import json
    sheet_file = sheet_path / f"{char_sheet.character_id}.json"
    with open(sheet_file, "w") as f:
        json.dump(char_sheet.model_dump(), f, indent=2, default=str)


def export_json(char_sheet: CharacterSheet):
    """Export character sheet as JSON."""
    import json

    json_str = json.dumps(char_sheet.model_dump(), indent=2, default=str)
    st.download_button(
        label="📥 Download JSON",
        data=json_str,
        file_name=f"{char_sheet.character_name.replace(' ', '_')}_character_sheet.json",
        mime="application/json",
    )


if __name__ == "__main__":
    render_character_sheet_builder()
