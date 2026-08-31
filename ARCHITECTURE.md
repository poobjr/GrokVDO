# GrokFilmStudio - Architecture & Developer Guide

## 🎯 Project Vision

**GrokFilmStudio** คือระบบ automation สำหรับสร้างวิดีโอด้วย AI (Grok/Flux) ที่แก้ปัญหาสำคัญ 4 ประการ:

1. **Context Drift** - Prompt เสียความหมายเมื่อกenerate หลายครั้ง
2. **Character Inconsistency** - ตัวละครเปลี่ยนหน้าตา/ชุด
3. **Camera Randomness** - มุมกล้องไมคงที่
4. **Token Waste** - เสีย token ซ้ำซ้อนกับการ describe ตัวละครเดิมๆ

## 💡 Core Concept: DNA Locking System

ระบบใช้หลัก "DNA Locking" เพื่อล็อกองค์ประกอบสำคัญใหคงที่ตลอดการ generate:

```
┌─────────────────────────────────────────────────────────┐
│                    PROMPT FORMULA                       │
├─────────────────────────────────────────────────────────┤
│  [Character DNA] + [Location DNA] + [Action]           │
│  + [Camera Specs] + [Context] + [World Style]          │
└─────────────────────────────────────────────────────────┘
```

### DNA Types

| Type | Purpose | Example |
|------|---------|---------|
| **Character** | ล็อกหน้าตา/ลักษณะตัวละคร | "Asian woman, black hair, red jacket" |
| **Location** | ล็อกสภาพแวดล้อม | "Apartment, brick wall, large window" |
| **Context** | ล็อกเวลา/อากาศ/บรรยากาศ | "Night, raining, tense mood" |
| **World** | ล็อกสไตล์ภาพรวม | "Cinematic 35mm, Kodak Portra 400" |

## 🏗️ System Architecture

### 5-Phase Pipeline

```
┌──────────────────────────────────────────────────────────┐
│  PHASE 1: Production Bible Setup                         │
│  ─ Define Character/Location/Context/World Anchors      │
│  ─ Save to JSON with Pydantic validation                │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│  PHASE 2: Script Parsing & Storyboard Generation         │
│  ─ Parse synopsis/treatment/screenplay                  │
│  ─ Break into shots with camera inference               │
│  ─ Extract character/location references                │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│  PHASE 3: Prompt Compilation (DNA Locking)              │
│  ─ Compile prompts using locked DNA                     │
│  ─ Validate prompt length & bloat                       │
│  ─ Human review before generation                       │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│  PHASE 4: Batch Generation                               │
│  ─ Generate ALL keyframes first                         │
│  ─ [HUMAN REVIEW POINT] Approve/Reject                  │
│  ─ Generate videos from approved keyframes              │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│  PHASE 5: Timeline Assembly & Export                     │
│  ─ Stitch video clips with FFmpeg                       │
│  ─ Mix audio (TTS from ElevenLabs)                      │
│  ─ Export FCPXML/EDL/Premiere XML                       │
└──────────────────────────────────────────────────────────┘
```

## 📂 Project Structure

```
E:\GrokVDO\
├── src/grokfilmstudio/              # Main package
│   ├── config.py                    # Configuration (env vars)
│   ├── state.py                     # State persistence manager
│   ├── cli.py                       # Command-line interface
│   │
│   ├── models/                      # Data models (Pydantic)
│   │   ├── production_bible.py      # Character, Location, Context, World Anchors
│   │   ├── shotlist.py              # Shot & Shotlist schemas
│   │   └── project_state.py         # Pipeline state tracking
│   │
│   ├── compiler/                    # Prompt compilation
│   │   ├── prompt_compiler.py       # DNA Locking compiler
│   │   └── script_parser.py         # Script → Storyboard parser
│   │
│   ├── automation/                  # Browser automation
│   │   ├── browser.py               # Playwright session manager
│   │   ├── auth.py                  # Authentication handler
│   │   └── grok_controller.py       # Grok operations
│   │
│   ├── pipeline/                    # Video processing
│   │   ├── batch_generator.py       # Batch workflow manager
│   │   ├── downloader.py            # Asset downloader
│   │   ├── ffmpeg_assembly.py       # Video stitching
│   │   └── timeline_export.py       # FCPXML/EDL exporter
│   │
│   └── audio/                       # Audio generation
│       └── elevenlabs.py            # ElevenLabs TTS client
│
├── ui/app.py                        # Streamlit dashboard
├── tests/                           # Unit tests
├── projects/                        # Runtime project data
└── docs/                            # Documentation
```

## 🔧 Key Components

### 1. Production Bible (`models/production_bible.py`)

Source of truth สำหรับทุก creative element:

```python
class ProductionBible(BaseModel):
    project_id: str
    project_name: str
    character_anchors: list[CharacterAnchor]  # DNA ตัวละคร
    location_anchors: list[LocationAnchor]    # DNA สถานที่
    context_anchors: list[ContextAnchor]      # DNA บริบท
    world_anchors: WorldAnchor                # สไตล์ภาพรวม
    audio_anchors: list[AudioAnchor]          # Voice mapping
```

### 2. Prompt Compiler (`compiler/prompt_compiler.py`)

หัวใจของระบบ - Compile prompts ด้วย DNA ที่ล็อกไว้:

```python
class PromptCompiler:
    def compile_image_prompt(self, shot, location_id, context_id):
        # 1. ดึง Character DNA จาก bible
        # 2. ดึง Location DNA จาก bible
        # 3. ดึง Context DNA จาก bible
        # 4. ประกอบกับ Action + Camera + World Style
        # 5. Return prompt ที่ไม่เพี้ยน
```

### 3. Batch Generator (`pipeline/batch_generator.py`)

จัดการ workflow แบบ batch เพื่อประหยัด token:

```python
class BatchGenerationManager:
    async def run_keyframe_generation():
        # Generate ทุก keyframe ก่อน
        # หยุดให้ human review
        
    async def run_video_generation():
        # Generate video จาก keyframes ที่ approve
        
    def run_assembly():
        # ต่อ clips + export timeline
```

### 4. Script Parser (`compiler/script_parser.py`)

แปลง script เป็น shots อัตโนมัติ:

```python
class ScriptParser:
    def parse_to_storyboard(self, text):
        # 1. Detect format (synopsis/treatment/script)
        # 2. Split into scenes
        # 3. Extract characters/locations
        # 4. Infer camera directions
        # 5. Return StoryboardPanels
```

## 🚀 Usage Examples

### CLI Workflow

```bash
# 1. สร้างโปรเจค
grokfilm project new "My Short Film"

# 2. กำหนด DNA
grokfilm bible add-character PROJ_XXX \
  --name "Hero" \
  --dna "Asian woman, black hair, red leather jacket"

grokfilm bible add-location PROJ_XXX \
  --name "Apartment" \
  --dna "Studio apartment, exposed brick, large window"

# 3. Parse script
grokfilm script parse PROJ_XXX script.txt

# 4. Compile prompts (ใช้ DNA ที่ล็อกไว้)
grokfilm compile all PROJ_XXX

# 5. Generate แบบ batch (ประหยัด token)
grokfilm generate batch PROJ_XXX \
  --location "LOC_001" \
  --context "CTX_001" \
  --stage "all"
```

### Python API

```python
from grokfilmstudio.state import StatePersistenceManager
from grokfilmstudio.compiler.prompt_compiler import PromptCompiler
from grokfilmstudio.pipeline.batch_generator import BatchGenerationManager

# Initialize
pm = StatePersistenceManager()
bible, shotlist, state = pm.recover_project("PROJ_XXX")

# Compile with DNA locking
compiler = PromptCompiler(bible)
for shot in shotlist.shots:
    prompt, errors, warnings = compiler.compile_and_validate(
        shot,
        location_id="LOC_001",
        context_id="CTX_001"
    )

# Batch generate
batch_mgr = BatchGenerationManager("PROJ_XXX")
job = batch_mgr.create_batch_job(
    location_id="LOC_001",
    context_id="CTX_001"
)
await batch_mgr.run_keyframe_generation(job)
# [Review keyframes]
await batch_mgr.run_video_generation(job)
batch_mgr.run_assembly(job)
```

## 🎨 Data Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Script    │────▶│   Parser     │────▶│  Shotlist   │
└─────────────┘     └──────────────┘     └─────────────┘
                                              │
                                              ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Final MP4  │◀────│   Assembly   │◀────│   Videos    │
└─────────────┘     └──────────────┘     └─────────────┘
                                              ▲
                                              │
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Bible JSON │────▶│   Compiler   │────▶│  Keyframes  │
└─────────────┘     └──────────────┘     └─────────────┘
```

## 🔐 Authentication Flow

```
┌─────────────────────────────────────────────────────────┐
│  Browser Authentication (Playwright)                    │
├─────────────────────────────────────────────────────────┤
│  1. Launch browser (headless)                           │
│  2. Navigate to Grok login page                         │
│  3. Fill credentials from .env                          │
│  4. Save cookies to storage_state.json                  │
│  5. Reuse session for subsequent requests               │
│  6. Auto-reconnect on expiry                            │
└─────────────────────────────────────────────────────────┘
```

## 📊 State Management

ระบบเก็บ state แบบ JSON เพื่อรองรับการ resume:

```json
{
  "project_id": "PROJ_20260831_120000",
  "current_phase": "keyframe_gen",
  "phase_states": {
    "bible_setup": {"status": "completed"},
    "script_parsing": {"status": "completed"},
    "keyframe_gen": {"status": "in_progress"}
  },
  "shot_progress": [
    {"shot_id": "SC01_SH01", "status": "keyframe_generated"},
    {"shot_id": "SC01_SH02", "status": "pending"}
  ]
}
```

## 🧪 Testing Strategy

```bash
# Run unit tests
pytest tests/

# Test prompt compiler
pytest tests/test_prompt_compiler.py -v

# Test state persistence
pytest tests/test_state_persistence.py -v
```

## 🔧 Extending the System

### Adding New AI Provider

1. สร้าง class ใน `automation/` (เช่น `flux_controller.py`)
2. Implement interface เดียวกับ `GrokController`
3. เพิ่ม config ใน `config.py`
4. อัพเดท CLI ใน `cli.py`

### Adding New Export Format

1. สร้าง method ใน `pipeline/timeline_export.py`
2. เพิ่ม CLI command ใน `cli.py`
3. เพิ่ม option ใน dashboard

### Custom Script Format

1. เพิ่ม method ใน `compiler/script_parser.py`
2. อัพเดท `_detect_format()`
3. เพิ่ม test cases

## 📝 Best Practices

### DNA Writing

✅ DO:
- ใช้ 3-4 ลักษณะเด่นเท่านั้น
- ใช้คำที่ชัดเจน ไม่คลุมเครือ
- แยก Character/Location/Context ให้ชัด

❌ DON'T:
- ใส่รายละเอียดเยอะเกิน (เช่น "beautiful eyes with long lashes")
- ใช้คำฟุ่มเฟือย (เช่น "stunning, gorgeous, masterpiece")
- Repeat ข้อมูลเดิมใน prompt เดียวกัน

### Batch Generation

- Generate keyframes ทั้งหมดก่อน → Review → Generate videos
- ใช้ `--location` และ `--context` flag เพื่อล็อก DNA
- ตรวจสอบ prompt preview ก่อน generate จริง

## 🐛 Troubleshooting

### Character Inconsistency

1. ตรวจสอบ Character DNA สั้นกระชับ
2. ใช้ `--location` flag ตอน generate
3. Review keyframes ก่อน generate video

### Token Wasted

1. ใช้ Batch Generation แทน generate แยก shot
2. ตรวจสอบว่าไม่มี filler words ใน DNA
3. ใช้คำที่กระชับ ไม่เยิ่นเย้อ

### Browser Automation Fails

1. ตรวจสอบ credentials ใน `.env`
2. รัน `playwright install chromium`
3. อัพเดท selectors ใน `grok_controller.py`

## 📚 Resources

- [Playwright Docs](https://playwright.dev)
- [Pydantic Docs](https://docs.pydantic.dev)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [Streamlit Docs](https://docs.streamlit.io)

## 🤝 Contributing

1. Fork the repo
2. Create feature branch
3. Make changes
4. Add tests
5. Submit PR

## 📄 License

MIT License - See LICENSE file

---

**Built with ❤️ for AI Film Production**
