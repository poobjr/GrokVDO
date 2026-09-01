# Character Sheet Builder - คู่มือการใช้งาน

## ภาพรวม

**Character Sheet** คือระบบสร้างโปรไฟล์ตัวละครแบบละเอียด เพื่อให้ AI สร้างภาพตัวละครได้คงที่ตลอดทั้งโปรเจกต์

แตกต่างจาก **Character Anchor** แบบธรรมดาอย่างไร?

| Character Anchor (เดิม) | Character Sheet (ใหม่) |
|------------------------|------------------------|
| DNA Prompt สั้นๆ (150 ตัวอักษร) | โปรไฟล์ครบถ้วนทุกมิติ |
| ระบุแค่ลักษณะภายนอก | รวมถึงนิสัย, น้ำเสียง, ท่าทาง |
| ใช้สำหรับตัวประกอบ | ใช้สำหรับตัวละครหลัก |

## เมื่อไหร่ควรใช้ Character Sheet

✅ **ใช้ Character Sheet เมื่อ:**
- ตัวละครหลักของเรื่อง
- ตัวละครที่ปรากฏในหลายฉาก
- ต้องการความคงที่สูงสุด

✅ **ใช้ Character Anchor เมื่อ:**
- ตัวประกอบที่ปรากฏแค่ 1-2 ฉาก
- ตัวละครพื้นหลัง
- ไม่ต้องการรายละเอียดมาก

## องค์ประกอบของ Character Sheet

### 1. Physical Attributes (ลักษณะทางกายภาพ)

```
┌─────────────────────────────────────────────────────┐
│  Face & Head                                        │
│  ├─ Face Shape: Oval, Round, Square, Heart...      │
│  ├─ Eye Color: Brown, Blue, Green, Hazel...        │
│  ├─ Eye Shape: Almond, Round, Hooded...            │
│  ├─ Eyebrows: Thick arched, Thin straight...       │
│  ├─ Nose: Straight, Button, Aquiline...            │
│  ├─ Lips: Full, Thin, Bow-shaped...                │
│  └─ Jawline: Strong square, Soft round...          │
├─────────────────────────────────────────────────────┤
│  Hair                                               │
│  ├─ Style: Long straight, Bob, Pixie, Buzz...      │
│  ├─ Color: Black, Blonde, Red, Brown with gray...  │
│  └─ Texture: Fine, Thick, Coarse...                │
├─────────────────────────────────────────────────────┤
│  Skin                                               │
│  ├─ Tone: Very fair, Fair, Medium, Olive, Brown... │
│  └─ Details: Freckles, Scars, Dimples...           │
└─────────────────────────────────────────────────────┘
```

### 2. Style & Wardrobe (สไตล์และการแต่งกาย)

```
┌─────────────────────────────────────────────────────┐
│  Style Keywords: Edgy, Minimalist, Bohemian...     │
│  Signature Colors: Red, Black, Denim blue...       │
│  Signature Items: Leather jacket, Combat boots...  │
│  Accessories: Silver necklace, Leather watch...    │
└─────────────────────────────────────────────────────┘
```

### 3. Personality (นิสัยและบุคลิก)

```
┌─────────────────────────────────────────────────────┐
│  Traits: Confident, Shy, Outgoing, Reserved...     │
│  Physical Presence:                                │
│  "Walks with confident stride, maintains strong    │
│   eye contact, gestures frequently when speaking"  │
└─────────────────────────────────────────────────────┘
```

### 4. Voice Description (ลักษณะเสียง)

```
┌─────────────────────────────────────────────────────┐
│  Voice: Deep raspy voice, mid-Atlantic accent,     │
│         speaks slowly and deliberately             │
│  Pitch: Medium-Low                                 │
│  Tempo: Medium                                     │
└─────────────────────────────────────────────────────┘
```

### 5. Face Chart (สีหน้าและอารมณ์)

```
┌─────────────────────────────────────────────────────┐
│  Neutral: Relaxed face, slight natural smile       │
│  Smile: Wide genuine smile showing upper teeth,    │
│         eyes crinkle at corners                    │
│  Serious: Jaw set firm, eyebrows slightly furrowed │
│  Angry: Eyebrows drawn together, nostrils flare    │
│  Surprised: Eyes wide, eyebrows raised             │
│  Sad: Corners of mouth turned down, eyes downcast  │
└─────────────────────────────────────────────────────┘
```

## การใช้งาน

### ผ่าน Dashboard (แนะนำ)

1. **เปิด Dashboard**
   ```bash
   streamlit run ui/app.py
   ```

2. **เลือก Project** จาก Sidebar

3. **คลิก "Character Sheet Builder"** ในเมนู

4. **กรอกข้อมูลทีละ Tab:**
   - 📋 Basic Info: ชื่อ, อายุ, เพศ, บทบาท
   - 👤 Physical Attributes: ลักษณะร่างกาย
   - 👔 Style & Wardrobe: การแต่งกาย
   - 💭 Personality: นิสัยและน้ำเสียง
   - 😊 Face Chart: สีหน้าและอารมณ์
   - 📸 References & Export: รูปภาพอ้างอิงและ Export

5. **กด "Generate Character Sheet"**

6. **Preview และ Export:**
   - DNA Prompt: สำหรับใช้ generate
   - Full Description: สำหรับอ้างอิง
   - JSON: สำหรับบันทึก

### ผ่าน CLI

```bash
# ดูคำสั่ง Character Sheet
grokfilm character --help

# สร้าง Character Sheet จาก template
grokfilm character create PROJ_XXX --name "Sarah Chen"

# Export Character Sheet
grokfilm character export PROJ_XXX CHAR_001 --format json
```

## ตัวอย่าง Character Sheet ที่สมบูรณ์

```json
{
  "character_id": "CHAR_A1B2C3",
  "character_name": "Sarah Chen",
  "project_id": "PROJ_20260901_120000",
  
  "physical": {
    "age_range": "25-35",
    "gender": "female",
    "height": "165 cm",
    "body_type": "athletic",
    "face_shape": "oval",
    "eye_color": "brown",
    "eye_shape": "almond",
    "eyebrows": "thick arched",
    "nose": "straight",
    "lips": "full",
    "jawline": "strong square",
    "facial_hair": "clean shaven",
    "skin_tone": "medium (olive)",
    "skin_details": "small scar on left eyebrow",
    "hair_style": "shoulder-length",
    "hair_color": "black with red highlights",
    "hair_texture": "thick",
    "distinguishing_features": [
      "tattoo of phoenix on right shoulder",
      "mole above left lip"
    ]
  },
  
  "style": {
    "style_keywords": ["edgy", "minimalist", "urban"],
    "signature_colors": ["black", "red", "denim blue"],
    "signature_items": ["red leather jacket", "combat boots"],
    "accessories": ["silver chain necklace", "leather wristband"]
  },
  
  "personality_traits": ["confident", "intense", "charismatic"],
  "personality_notes": "Walks with purpose, maintains intense eye contact",
  
  "voice_description": "Contralto voice, slight British accent",
  
  "face_chart": {
    "neutral": "Relaxed face, slight natural smile",
    "smile": "Wide genuine smile showing upper teeth",
    "serious": "Jaw set firm, eyebrows slightly furrowed",
    "angry": "Eyebrows drawn together, nostrils flare"
  }
}
```

### DNA Prompt ที่ Generate

```
25-35-year-old female, athletic build, shoulder-length black with red highlights hair, oval face, brown eyes, tattoo of phoenix on right shoulder, mole above left lip
```

## เคล็ดลับการเขียน Character Sheet ที่ดี

### ✅ DO (ควรทำ)

1. **ระบุลักษณะเด่น 3-4 อย่าง** สำหรับ DNA Prompt
   - ผม: สี, ทรง
   - หน้า: รูปหน้า, สีตา
   - ลักษณะพิเศษ: รอยแผลเป็น, รอยสัก

2. **ใช้คำที่ชัดเจน**
   - ✅ "shoulder-length black hair"
   - ❌ "nice looking hair"

3. **ระบุสี Signature**
   - ช่วยให้ AI ใช้สีคงที่ตลอด

4. **เขียน Face Chart ครบทุกอารมณ์**
   - จะช่วยให้ generate ฉากอารมณ์ต่างๆ ได้คงที่

### ❌ DON'T (ไม่ควรทำ)

1. **อย่าระบุรายละเอียดเยอะเกินไป**
   - ❌ "beautiful eyes with long curly lashes and a hint of gold..."
   - ✅ "brown eyes"

2. **อย่าใช้คำฟุ่มเฟือย**
   - ❌ "stunning, gorgeous, beautiful"
   - ✅ คำที่อธิบายลักษณะจริง

3. **อย่าขัดแย้งกันเอง**
   - ❌ "bald" + "long straight hair"
   - ✅ เลือกอย่างใดอย่างหนึ่ง

## การ Export และนำไปใช้

### Export Formats

1. **JSON** - สำหรับบันทึกและแก้ไขต่อ
2. **DNA Prompt** - สำหรับ copy ไปใช้ generate
3. **Full Description** - สำหรับอ้างอิง

### การใช้งานใน Pipeline

```bash
# 1. สร้าง Character Sheet
grokfilm character create PROJ_XXX --name "Hero"

# 2. Generate DNA Prompt
grokfilm character export PROJ_XXX CHAR_001 --format dna

# 3. ใช้กับ Prompt Compiler
grokfilm compile all PROJ_XXX

# 4. Generate ด้วย DNA Locking
grokfilm generate batch PROJ_XXX --location "LOC_001"
```

## การแก้ไขและอัปเดต

1. **เปิด Dashboard**
2. **ไปที่ Character Sheet Builder**
3. **เลือกตัวละครที่ต้องการแก้ไข**
4. **แก้ไขข้อมูลใน Tab ต่างๆ**
5. **กด "Update Character Sheet"**

## ตัวอย่างการใช้งานจริง

### เรื่อง: Neo-Noir Thriller

**ตัวละครหลัก: Detective Sarah Chen**

```
Physical:
- 30-35 ปี, หญิง, เอเชีย
- ผมดำยาวระดับไหล่ ปลายสีแดง
- รูปร่างสมส่วน สูง 165 ซม.
- ตาสีน้ำตาลเข้ม รูปอัลมอนด์
- รอยแผลเป็นเล็กๆ เหนือคิ้วซ้าย

Style:
- เสื้อหนังสีแดง (signature item)
- รองเท้าบู้ทสีดำ
- สไตล์: Edgy, Urban, Minimalist

Personality:
- Confident, Intense, Mysterious
- เดินอย่างมั่นใจ สบตาโดยตรง

Voice:
- เสียงต่ำแหบเล็กน้อย
- พูดช้าและชัดเจน
```

**DNA Prompt:**
```
30-35-year-old Asian female, athletic build, shoulder-length black hair with red tips, brown almond eyes, small scar above left eyebrow, wearing red leather jacket
```

---

## สรุป

Character Sheet ช่วยให้:
- ✅ ตัวละครคงที่ตลอดทั้งเรื่อง
- ✅ ลดการ generate ซ้ำ
- ✅ ประหยัด token
- ✅ ทำงานเป็นทีมได้ง่าย

**เริ่มใช้งานเลย:**
```bash
streamlit run ui/app.py
→ เลือก Project → Character Sheet Builder
```
