# DNA Locking System คู่มือการใช้งาน

## ภาพรวม

**DNA Locking** คือระบบที่ช่วยให้การ generate คลิปวิดีโอหลายๆ คลิปมีความคงที่ของ:
- หน้าตาตัวละคร (Character Consistency)
- สถานที่ (Location Consistency)
- บรบทเรื่องราว (Context Consistency)
- สไตล์ภาพ (Visual Style)

## ปญหาที่ระบบนี้แก

### กอนใช DNA Locking
```
Clip 1: "Asian woman, long hair, red jacket, walking in apartment..."
Clip 2: "Woman with short hair, blue shirt, in a room..."
Clip 3: "Girl with curly hair, green dress, indoor scene..."
```
❌ **ผลลพธ**: ตัวละครไมเหมือนกัน, สถานที่เปลี่ยนไปมา

### หลังใช DNA Locking
```
Character DNA (Locked): "Asian woman, shoulder-length black hair, red leather jacket"
Location DNA (Locked): "Small studio apartment, exposed brick wall, large window, plants everywhere"

Clip 1: [Character DNA] + [Location DNA] + "walking across room"
Clip 2: [Character DNA] + [Location DNA] + "sitting at desk"
Clip 3: [Character DNA] + [Location DNA] + "looking out window"
```
✅ **ผลลพธ**: ตัวละครและสถานที่คงที่ตลอดทุกคลิป

---

## โครงสราง DNA Anchors

### 1. Character Anchor (DNA ตัวละคร)

ใชล็อกหนาลกษณะตัวละครใหคงที่

```bash
grokfilm bible add-character PROJ_XXX \
  --name "Sarah Chen" \
  --dna "Asian woman, shoulder-length black hair, red leather jacket, determined expression"
```

**หลักการเขียน DNA ที่ดี:**
- ✅ ระบุ 3-4 ลกษณะเด่นเทานั้น (ผม, เสือ, ลกษณะหนา)
- ✅ ใชคำทชดเจน ไมคลุมเครือ
- ❌ อยาใสรายละเอียดเยอะเกินไป (เช่น "beautiful eyes with long lashes...")
- ❌ อยาใสคำฟุมเฟอย (เช่น "stunning, gorgeous, masterpiece")

**ตวอยาง DNA ที่ดี:**
```
"Middle-aged man, graying beard, black leather jacket, scar on left cheek"
"Young woman, curly brown hair, denim jacket, confident smile"
"Elderly lady, white bun, floral dress, walking cane"
```

---

### 2. Location Anchor (DNA สถานที่)

ใชล็อกสถานที่ใหคงที่ เมื่อตองการ generate หลายช็อตในสถานที่เดียวกัน

```bash
grokfilm bible add-location PROJ_XXX \
  --name "Sarah's Apartment" \
  --dna "Small studio apartment, exposed brick wall, large window with fire escape, plants everywhere, bookshelf overflowing" \
  --lighting "Warm evening light through window" \
  --mood "Cozy but cluttered"
```

**หลักการเขียน Location DNA:**
- ✅ ระบุองคประกอบถาวรทไมเปลี่ยน (ผน, หนตาง, เฟอร์นเจอรใหญ)
- ✅ ระบุแสงและบรรยากาศ
- ❌ อยาใสรายละเอียดทอาจเปลยนได (เช่น "coffee cup on table")

**ตวอยาง Location DNA:**
```
"Abandoned warehouse, concrete floors, rusted metal beams, broken skylights, dust motes in air"
"Modern office, glass walls, white desks, fluorescent lighting, city view"
"Forest clearing, tall pine trees, moss-covered rocks, dappled sunlight"
```

---

### 3. Context Anchor (DNA บรบท)

ใชล็อกบรบทเรื่องราว เวลา อากาศ อารมณ

```bash
grokfilm bible add-context PROJ_XXX \
  --name "The Chase Scene" \
  --time "Night, 2 AM" \
  --weather "Heavy rain" \
  --mood "Tense, dangerous" \
  --notes "Sarah's jacket must be wet, street lights reflecting on pavement"
```

**เมื่อไหรควรใช Context Anchor:**
- ✅ เมื่อตองการใหทกช็อตอยูในเวลาเดยวกน
- ✅ เมื่อตองการใหม atmospheric elements รวมกน (ฝน, หมอก, แสง)
- ✅ เมื่อม continuity notes ทตองตาม

---

### 4. World Anchor (สไตล์ภาพรวม)

ใชล็อกสไตล์ภาพของทงโปรเจกต

```bash
grokfilm bible set-style PROJ_XXX \
  --style "Cinematic 35mm, Kodak Portra 400, dark thriller lighting" \
  --aspect-ratio "16:9" \
  --color-grade "Teal and orange, high contrast"
```

---

## การใชงาน DNA Locking ใน Pipeline

### ขนตอนท 1: สราง Production Bible

```bash
# 1. สรางโปรเจกต
grokfilm project new "My Short Film"
# ได PROJ_20260831_120000

# 2. เพิ่มตัวละคร
grokfilm bible add-character PROJ_XXX \
  --name "Sarah" \
  --dna "Asian woman, shoulder-length black hair, red leather jacket"

# 3. เพิ่มสถานที่
grokfilm bible add-location PROJ_XXX \
  --name "Sarah's Apartment" \
  --dna "Studio apartment, exposed brick, large window, plants everywhere"

# 4. เพิ่มบรบท
grokfilm bible add-context PROJ_XXX \
  --name "Opening Scene" \
  --time "Evening" \
  --mood "Melancholic"

# 5. ตั้งคาสไตล์
grokfilm bible set-style PROJ_XXX \
  --style "Cinematic 35mm, Kodak Portra 400" \
  --aspect-ratio "16:9"
```

### ขนตอนท 2: Parse Script

```bash
grokfilm script parse PROJ_XXX my_script.txt
```

### ขนตอนท 3: Compile Prompts (พรอม DNA Locking)

```bash
# Compile ทก shots พรอมใช DNA ที่ล็อกไว
grokfilm compile all PROJ_XXX
```

### ขนตอนท 4: Batch Generation (พรอม DNA Locking)

```bash
# Generate ทกช็อตพรอมล็อก DNA
grokfilm generate batch PROJ_XXX \
  --location "LOC_001" \
  --context "CTX_001"
```

---

## Batch Generation Workflow

ระบบใช **Batch Generation** แทนการ generate ทละช็อต เพอ:
1. ลด token usage (ไมตอง repeat DNA ทกครง)
2. ให human review กอน generate video
3. จัดการ dependency ระหวางช็อต

### Workflow

```
┌─────────────────────────────────────────────────────────┐
│ STAGE 1: Generate All Keyframes                         │
│ ─ Compile prompts with LOCKED DNA                       │
│ ─ Generate keyframe for EACH shot                       │
│ ─ ⏸ [HUMAN REVIEW POINT]                                │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ STAGE 2: Generate All Videos                            │
│ ─ Use APPROVED keyframes as input                       │
│ ─ Generate video with motion prompts                    │
│ ─ Download and organize clips                           │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ STAGE 3: Assemble Timeline                              │
│ ─ Concatenate all video clips                           │
│ ─ Mix audio tracks                                      │
│ ─ Export final video + FCPXML/EDL                       │
└─────────────────────────────────────────────────────────┘
```

### คำสั่ง Batch Generation

```bash
# Generate keyframes กอน (หยดให review)
grokfilm generate batch PROJ_XXX --stage=keyframes

# Review keyframes (ดาชบอรดหรอ CLI)
grokfilm script list PROJ_XXX

# ตอไป generate videos
grokfilm generate batch PROJ_XXX --stage=videos

# Assemble timeline
grokfilm generate batch PROJ_XXX --stage=assemble
```

---

## ตวอยางการใชงานจรنگ

### Storyboard: ฉากตอสูในอพารทเมนต

```bash
# 1. สร้าง DNA
grokfilm bible add-character PROJ_XXX \
  --name "Sarah" \
  --dna "Asian woman, shoulder-length black hair, red leather jacket, athletic build"

grokfilm bible add-character PROJ_XXX \
  --name "Mike" \
  --dna "Caucasian man, shaved head, black tactical vest, muscular"

grokfilm bible add-location PROJ_XXX \
  --name "Sarah's Apartment" \
  --dna "Small studio, exposed brick wall, large window with fire escape, plants, bookshelf"

grokfilm bible add-context PROJ_XXX \
  --name "The Fight" \
  --time "Night" \
  --mood "Violent, tense" \
  --notes "Furniture overturned, broken glass on floor"

# 2. Parse script
grokfilm script parse PROJ_XXX fight_scene.txt

# 3. Generate แบบ batch พรอม DNA locking
grokfilm generate batch PROJ_XXX \
  --location "LOC_001" \
  --context "CTX_001" \
  --stage=all
```

### ผลลพธทได

**Prompt สำหรับ Shot 1:**
```
Asian woman, shoulder-length black hair, red leather jacket, athletic build,
Small studio, exposed brick wall, large window with fire escape, plants, bookshelf,
Sarah dodges Mike's punch,
Medium Close-up, Low Angle, Handheld,
Night, Violent tense atmosphere,
Cinematic 35mm, Kodak Portra 400
```

**Prompt สำหรับ Shot 2:**
```
Caucasian man, shaved head, black tactical vest, muscular,
Small studio, exposed brick wall, large window with fire escape, plants, bookshelf,
Mike lunges forward, fist extended,
Medium, Eye Level, Tracking,
Night, Violent tense atmosphere,
Cinematic 35mm, Kodak Portra 400
```

✅ **สังเกต**: Character DNA และ Location DNA ซำกนทก shot → ความคงที่สงสุด

---

## การแกปญหา

### ปญหา: ตัวละครเปลยนหนาทกช็อต

**แกโดย:**
1. ตรวจสอบ Character DNA วาสั้นกระชช ไมม contradiction
2. ใช `--location` และ `--context` flag เพอล็อก DNA
3. ตรวจสอบวา character ID ถูกตองใน shotlist

### ปญหา: สถานที่ไมคงที่

**แกโดย:**
1. สราง Location Anchor สำหรบสถานที่นน
2. ใช `--location LOC_XXX` ตอน generate batch
3. ตรวจสอบวา location DNA มองคประกอบทชดเจน

### ปญหา: ใช้ token เยอะเกินไป

**แกโดย:**
1. ใช Batch Generation แทน generation แยกช็อต
2. ตรวจสอบวาไมม filler words ใน DNA
3. ใชคำสทกระชบ ไมเยอความ

---

## สรุป

| Anchor | ใชเมอ | ตวอยาง |
|--------|------|--------|
| **Character** | ล็อกหนาลกษณะตัวละคร | "Asian woman, black hair, red jacket" |
| **Location** | ล็อกสถานที่ | "Apartment, brick wall, large window" |
| **Context** | ล็อกเวลา/อากาศ/บรบท | "Night, raining, tense mood" |
| **World** | ล็อกสไตล์ภาพ | "Cinematic 35mm, Kodak Portra 400" |

**สูตร Prompt ทด:**
```
[Character DNA] + [Location DNA] + [Action] + [Camera] + [Context] + [World Style]
```
