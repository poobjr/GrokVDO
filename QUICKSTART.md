# Quick Start Guide

## Setup (5 minutes)

### 1. Install Dependencies

```bash
cd E:\GrokVDO
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[all]"
playwright install chromium
```

### 2. Configure Credentials

Edit `.env` with your credentials:

```bash
GROK_USERNAME=your_username
GROK_PASSWORD=your_password
ELEVENLABS_API_KEY=your_api_key
```

### 3. Verify Installation

```bash
grokfilm --version
```

## First Project (10 minutes)

### Create Project

```bash
grokfilm project new "My First Film"
# Note the project ID: PROJ_20260831_XXXXXX
```

### Add Character

```bash
grokfilm bible add-character PROJ_XXX \
  --name "Alex" \
  --dna "Young adult, curly brown hair, denim jacket, confident smile"
```

### Set Style

```bash
grokfilm bible set-style PROJ_XXX \
  --style "Cinematic 35mm, warm golden hour lighting" \
  --aspect-ratio "16:9"
```

### Create Sample Script

Create `script.txt`:

```
Alex walks into the abandoned warehouse, flashlight scanning the darkness.
Suddenly, a sound echoes from the shadows. Alex freezes, eyes wide.
The flashlight reveals an old machine, covered in dust and cobwebs.
Alex approaches cautiously, reaching out to touch the strange symbols.
```

### Parse Script

```bash
grokfilm script parse PROJ_XXX script.txt
grokfilm script list PROJ_XXX
```

### Compile Prompts

```bash
grokfilm compile all PROJ_XXX
grokfilm compile preview PROJ_XXX SC01_SH01
```

### Export Timeline

```bash
grokfilm export timeline PROJ_XXX
```

## Using the Dashboard

```bash
streamlit run ui/app.py
```

Then open http://localhost:8501 in your browser.

## Next Steps

1. **Configure Grok credentials** - Required for generation
2. **Upload reference images** - For character consistency
3. **Run generation pipeline** - `grokfilm pipeline run PROJ_XXX`
4. **Review outputs** - Check `projects/PROJ_XXX/renders/`

## Troubleshooting

**Command not found**: Make sure virtual environment is activated
**Playwright error**: Run `playwright install chromium`
**Import error**: Run `pip install -e .`
