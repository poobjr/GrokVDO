# GrokFilmStudio

**AI Film Production Automation System** - A full-stack, modular automation layer for Grok/Flux video workflows.

## Overview

GrokFilmStudio solves the key challenges in AI-assisted film production:

- **Context Drift**: Prompts lose consistency across shots
- **Character Inconsistency**: Faces/appearances change between generations
- **Camera Angle Randomness**: Uncontrolled shot composition
- **Redundant Generation Credits**: Wasted tokens on repeated character descriptions

## Features

### 5-Phase Pipeline Architecture

```
[Phase 1: Session Auth & Production Bible Setup]
    ↓
[Phase 2: Automated Script & Shotlist Expansion]
    ↓
[Phase 3: Keyframe & Character Generation Engine]
    ↓
[Phase 4: Motion Control & Animation Pipeline]
    ↓
[Phase 5: Audio Assembly & Timeline Export Engine]
```

### Core Modules

| Module | Description |
|--------|-------------|
| **Data Models** | Pydantic schemas for Production Bible, Shotlist, and Project State |
| **Prompt Compiler** | Deterministic prompt compilation with character/world anchors |
| **Script Parser** | Parse synopsis, treatment, or full screenplay into structured shots |
| **Browser Automation** | Playwright-based Grok session management |
| **FFmpeg Pipeline** | Video stitching, audio mixing, timeline assembly |
| **Timeline Export** | FCPXML, EDL, Premiere XML export for NLE integration |
| **TTS Integration** | ElevenLabs API client for character dialogue |
| **CLI & Dashboard** | Command-line tool and Streamlit web UI |

## Installation

### Prerequisites

- Python 3.11 or 3.12
- Node.js (optional, for some features)
- FFmpeg (installed and in PATH)

### Step 1: Clone/Setup

```bash
cd E:\GrokVDO
```

### Step 2: Create Virtual Environment

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # macOS/Linux
```

### Step 3: Install Dependencies

```bash
pip install -e ".[all]"
# or
pip install -r requirements.txt
```

### Step 4: Install Playwright Browsers

```bash
playwright install chromium
```

### Step 5: Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```env
GROK_USERNAME=your_grok_username
GROK_PASSWORD=your_grok_password
ELEVENLABS_API_KEY=your_elevenlabs_api_key
PROJECTS_DIR=./projects
BROWSER_HEADLESS=true
```

## Quick Start

### 1. Create a New Project

```bash
grokfilm project new "My Short Film"
```

### 2. Add Characters

```bash
grokfilm bible add-character PROJ_XXX \
  --name "Sarah Chen" \
  --dna "Asian woman, shoulder-length black hair, red leather jacket, determined expression"
```

### 3. Set Visual Style

```bash
grokfilm bible set-style PROJ_XXX \
  --style "Cinematic 35mm, Kodak Portra 400, dark thriller lighting" \
  --aspect-ratio "16:9" \
  --color-grade "Teal and orange, high contrast"
```

### 4. Parse Script

```bash
grokfilm script parse PROJ_XXX my_script.txt --format auto
```

### 5. Compile Prompts

```bash
grokfilm compile all PROJ_XXX
```

### 6. Generate (Requires Credentials)

```bash
grokfilm generate keyframes PROJ_XXX
grokfilm generate videos PROJ_XXX
```

### 7. Export Timeline

```bash
grokfilm export timeline PROJ_XXX --format all
```

## CLI Commands

### Project Management

| Command | Description |
|---------|-------------|
| `grokfilm project new <name>` | Create new project |
| `grokfilm project list` | List all projects |
| `grokfilm project info <id>` | Show project details |

### Production Bible

| Command | Description |
|---------|-------------|
| `grokfilm bible add-character` | Add character anchor |
| `grokfilm bible set-style` | Set world/style anchor |

### Script & Shots

| Command | Description |
|---------|-------------|
| `grokfilm script parse <file>` | Parse script into shots |
| `grokfilm script list` | List all shots |

### Compilation

| Command | Description |
|---------|-------------|
| `grokfilm compile all` | Compile all prompts |
| `grokfilm compile preview <shot_id>` | Preview a prompt |

### Generation

| Command | Description |
|---------|-------------|
| `grokfilm generate keyframes` | Generate keyframe images |
| `grokfilm generate videos` | Generate video clips |
| `grokfilm pipeline run` | Run full pipeline |

### Export

| Command | Description |
|---------|-------------|
| `grokfilm export timeline` | Export FCPXML/EDL/XML |
| `grokfilm export assembly` | Assemble final video |

## Web Dashboard

Start the Streamlit dashboard:

```bash
streamlit run ui/app.py
```

The dashboard provides:
- Visual project management
- Character/style editor
- Script parser interface
- Shot list inspector
- Prompt preview
- Generation monitoring
- Timeline export

## Project Structure

```
E:\GrokVDO\
├── src/grokfilmstudio/
│   ├── __init__.py
│   ├── config.py              # Configuration loader
│   ├── state.py               # State persistence manager
│   ├── models/
│   │   ├── production_bible.py # Character, World, Style anchors
│   │   ├── shotlist.py        # Shot data model
│   │   └── project_state.py   # Pipeline state
│   ├── compiler/
│   │   ├── prompt_compiler.py # Deterministic prompt builder
│   │   └── script_parser.py   # Script → Shotlist parser
│   ├── automation/
│   │   ├── browser.py         # Playwright session manager
│   │   ├── auth.py            # Authentication handler
│   │   └── grok_controller.py # Grok operations
│   ├── pipeline/
│   │   ├── downloader.py      # Asset download manager
│   │   ├── ffmpeg_assembly.py # Video stitching
│   │   └── timeline_export.py # FCPXML/EDL exporters
│   └── audio/
│       └── elevenlabs.py      # TTS API client
├── ui/
│   └── app.py                 # Streamlit dashboard
├── projects/                  # Runtime project data
├── tests/                     # Unit tests
├── .env.example              # Environment template
├── pyproject.toml            # Project metadata
└── README.md                 # This file
```

## Data Models

### Production Bible

```json
{
  "project_id": "PROJ_20260831_120000",
  "project_name": "The Last Stand",
  "character_anchors": [
    {
      "character_id": "CHAR_001",
      "name": "Sarah Chen",
      "dna_prompt": "Asian woman, shoulder-length black hair, red leather jacket",
      "master_reference_image": "./projects/proj_001/keyframes/char_001_ref.png"
    }
  ],
  "world_anchors": {
    "style_prompt": "Cinematic 35mm, Kodak Portra 400, dark thriller lighting",
    "aspect_ratio": "16:9",
    "color_grade": "Teal and orange"
  }
}
```

### Shot Structure

```json
{
  "shot_id": "SC01_SH01",
  "scene_number": 1,
  "character_ids": ["CHAR_001"],
  "action_description": "Sarah turns to face the camera, eyes narrowing",
  "camera_specs": {
    "shot_size": "Medium Close-up",
    "angle": "Low Angle",
    "motion": "Slow Pan Right"
  },
  "audio_script": "You think you can stop me?",
  "duration_seconds": 3.0,
  "compiled_prompt": "...",
  "status": "pending"
}
```

## Prompt Compilation Formula

```
[Character DNA] + [Action/Emotion] + [Camera Specs] + [World Style]
```

Example output:
```
Asian woman, shoulder-length black hair, red leather jacket,
Sarah turns to face the camera, eyes narrowing,
Medium Close-up, Low Angle, Slow Pan Right, 35mm lens,
Cinematic 35mm, Kodak Portra 400, dark thriller lighting
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GROK_USERNAME` | Grok account username | Yes (for generation) |
| `GROK_PASSWORD` | Grok account password | Yes (for generation) |
| `ELEVENLABS_API_KEY` | ElevenLabs API key | Yes (for TTS) |
| `PROJECTS_DIR` | Projects storage directory | No (default: ./projects) |
| `BROWSER_HEADLESS` | Run browser headless | No (default: true) |
| `MAX_RETRIES` | Max retry attempts | No (default: 3) |
| `VIDEO_GEN_TIMEOUT` | Video generation timeout (s) | No (default: 300) |

## Development

### Run Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/ tests/
ruff check src/ tests/
```

### Type Checking

```bash
mypy src/
```

## Troubleshooting

### Browser Automation Issues

1. **Login fails**: Verify credentials in `.env`
2. **Selectors not found**: Grok UI may have changed; update selectors in `grok_controller.py`
3. **Downloads fail**: Check browser permissions and download directory

### FFmpeg Issues

1. **Not found**: Install FFmpeg and add to PATH
2. **Codec errors**: Try `-c:v libx264` for H.264 encoding
3. **Sync issues**: Adjust `sync_offset` in `add_audio()`

### TTS Issues

1. **API errors**: Verify `ELEVENLABS_API_KEY`
2. **Voice not found**: Check voice ID in production bible
3. **Rate limits**: Reduce batch concurrency

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions welcome! Please read CONTRIBUTING.md first.

---

**Built with ❤️ by GrokFilmStudio Team**
