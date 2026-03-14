"""
Agent 6 - Banana AI Banner Generator
Tự động sinh ảnh Banner quảng cáo Simpia Trọn Đời
dựa trên Persona + P_Level (Customer Journey Ax/Rx)
"""

import csv
import json
import os
import re
import time
import uuid
import base64
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    from config import GEMINI_KEYS, DEFAULT_MODEL
except ImportError:
    from dotenv import load_dotenv
    load_dotenv()
    k1 = os.getenv("GEMINI_API_KEY")
    k2 = os.getenv("GEMINI_API_KEY_2")
    GEMINI_KEYS = [k for k in [k1, k2] if k]
    DEFAULT_MODEL = "gemini-2.0-flash"

import google.generativeai as genai

# New SDK for Image Generation
try:
    from google import genai as genai_new
    from google.genai import types as genai_types
    IMAGEN_AVAILABLE = True
    print("[Agent6] google-genai SDK loaded - Imagen 3 available!")
except ImportError:
    IMAGEN_AVAILABLE = False
    print("[Agent6] google-genai SDK not available, image generation disabled")

# ============================================================
# PATHS
# ============================================================
BASE_DIR = Path(__file__).parent
TRON_DOI_DIR = BASE_DIR / "personas"
KNOWHOW_DIR = BASE_DIR / "personas"
STATIC_DIR = Path(__file__).parent / "static"
GENERATED_DIR = STATIC_DIR / "generated"
try:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass

PERSONA_FILES = {
    1: "1. Persona_MeChoCon_NghiHocTrungTam.md",
    2: "2. Persona_MeChoCon_SapNghiTrungTam.md",
    3: "3. Persona_MeChoCon_HocSongSong.md",
    4: "4. Persona_NhaHaiCungHoc_LonBietNhoChua.md",
    5: "5. Persona_CagiaDinh_TrangTinh.md",
    6: "6. Persona_CagiaDinh_ConDaHoc_BoMeHocCung.md",
    7: "7. Persona_NguoiLon_MoiVao.md",
    8: "8. Persona_NguoiLon_DaThatBai.md",
}

PERSONA_NAMES = {
    1: {"name": "Mẹ: Con đã nghỉ", "icon": "🔙", "desc": "Đã nghỉ trung tâm, muốn quay lại học", "segment": 3},
    2: {"name": "Mẹ: Con sắp nghỉ", "icon": "🚧", "desc": "Sắp nghỉ trung tâm, muốn duy trì", "segment": 3},
    3: {"name": "Mẹ: Học song song", "icon": "🎓", "desc": "Đang học trung tâm, app bổ trợ", "segment": 3},
    4: {"name": "Nhà 2 con", "icon": "👦👧", "desc": "Lớn đã biết chơi, gợi cảm hứng bé nhỏ", "segment": 3},
    5: {"name": "Nhà trắng tinh", "icon": "👨‍👩‍👧", "desc": "Cả nhà chưa biết gì, cùng khám phá", "segment": 3},
    6: {"name": "Mẹ bố học cùng con", "icon": "👨‍👧", "desc": "Con đã biết chơi, bố mẹ học đệm đàn", "segment": 3},
    7: {"name": "Người lớn mới học", "icon": "🌱", "desc": "Mới tinh, tìm công cụ xả stress cá nhân", "segment": 12},
    8: {"name": "Người lớn học lại", "icon": "💔", "desc": "Đã học cách khác và từng bỏ cuộc", "segment": 12},
}


# ============================================================
# DATA LOADING
# ============================================================

def _safe_read(filepath: Path) -> str:
    for enc in ['utf-8-sig', 'utf-8', 'cp1252', 'latin-1']:
        try:
            return filepath.read_text(encoding=enc)
        except (UnicodeDecodeError, FileNotFoundError):
            continue
    return ""


def load_persona(persona_id: int) -> Dict[str, Any]:
    filename = PERSONA_FILES.get(persona_id)
    if not filename:
        return {"error": f"Persona {persona_id} not found"}
    filepath = TRON_DOI_DIR / filename
    content = _safe_read(filepath)
    if not content:
        return {"error": f"Cannot read {filepath}"}
    meta = PERSONA_NAMES.get(persona_id, {})

    p_levels = []
    angle_match = re.search(r'## 9\. Góc độ nội dung.*?\n(.*?)(?=\n## |\Z)', content, re.DOTALL)
    if angle_match:
        for line in angle_match.group(1).strip().split('\n'):
            line = line.strip().lstrip('- ')
            if line.startswith('**P-Level'):
                p_levels.append(line)

    pains = []
    pain_match = re.search(r'## 5\. Nỗi đau chính.*?\n(.*?)(?=\n## |\Z)', content, re.DOTALL)
    if pain_match:
        for line in pain_match.group(1).strip().split('\n'):
            line = line.strip().lstrip('- ')
            if line and not line.startswith('##'):
                pains.append(line)

    messages = []
    msg_match = re.search(r'## 8\. Key Message.*?\n(.*?)(?=\n## |\Z)', content, re.DOTALL)
    if msg_match:
        for line in msg_match.group(1).strip().split('\n'):
            line = line.strip().lstrip('- ')
            if line and not line.startswith('##'):
                messages.append(line)

    visuals = []
    vis_match = re.search(r'## 10\. Gợi ý visual.*?\n(.*?)(?=\n## |\Z)', content, re.DOTALL)
    if vis_match:
        for line in vis_match.group(1).strip().split('\n'):
            line = line.strip().lstrip('- ')
            if line and not line.startswith('##') and not line.startswith('Visual:') and not line.startswith('Copy hook:'):
                visuals.append(line)

    return {
        "id": persona_id,
        "name": meta.get("name", f"Persona {persona_id}"),
        "icon": meta.get("icon", "👤"),
        "desc": meta.get("desc", ""),
        "segment": meta.get("segment", 12),
        "p_levels": p_levels,
        "pains": pains,
        "key_messages": messages,
        "visuals": visuals,
        "full_content": content,
    }


def load_plevel_matrix(segment: int) -> List[Dict[str, Any]]:
    if segment == 3:
        csv_file = KNOWHOW_DIR / "TOFU Simpia - P_Level (Segment 3).csv"
    else:
        csv_file = KNOWHOW_DIR / "TOFU Simpia - P_Level (Segment 1&2).csv"
    try:
        with open(csv_file, encoding='utf-8-sig', newline='') as f:
            all_rows = list(csv.reader(f))
    except Exception as e:
        print(f"[Agent6] Error reading CSV: {e}")
        return []

    results = []
    skip_codes = {'A0', 'A1', 'A2.A', 'A2.A1', 'A2.A2', 'A2.B', 'A2.C'}
    for row in all_rows[2:]:
        if len(row) < 6:
            continue
        phase = row[0].strip() if row[0] else ""
        level_sales = row[1].strip() if row[1] else ""
        level_psych = row[2].strip() if row[2] else ""
        code = row[3].strip() if row[3] else ""
        stage_name = row[4].strip() if row[4] else ""
        if not code or code in skip_codes:
            continue
        if segment == 3:
            thought_p11 = row[5].strip().replace('\\r\\n', '\n').replace('\\n', '\n') if len(row) > 5 and row[5] else ""
            thought_p12 = row[6].strip().replace('\\r\\n', '\n').replace('\\n', '\n') if len(row) > 6 and row[6] else ""
            thought = thought_p11 or thought_p12 or ""
        else:
            thought = row[5].strip().replace('\\r\\n', '\n').replace('\\n', '\n') if len(row) > 5 and row[5] else ""
        if not thought and not stage_name:
            continue
        funnel = "acquisition" if code.startswith('A') else ("retention" if code.startswith('R') else "other")
        results.append({
            "code": code, "phase": phase, "level_sales": level_sales if level_sales else "",
            "level_psych": level_psych, "stage_name": stage_name, "thought": thought, "funnel": funnel,
        })
    return results


def load_visual_guide() -> str:
    return _safe_read(TRON_DOI_DIR / "Ads_Expert_Visual_Guide_TronDoi.md")

def load_banana_guide() -> str:
    return _safe_read(TRON_DOI_DIR / "Agent_Banner_Generator_BananaAI.md")

def load_image_best_practices() -> str:
    return _safe_read(TRON_DOI_DIR / "5. Image_Best_Practices.md")


# ============================================================
# AI GENERATION
# ============================================================

class BannerAgent:
    def __init__(self):
        self.keys = GEMINI_KEYS
        self.current_key_idx = 0
        self.model_name = DEFAULT_MODEL
        self._init_model()
        self.visual_guide = load_visual_guide()
        self.banana_guide = load_banana_guide()
        self.image_best_practices = load_image_best_practices()

    def _init_model(self):
        if not self.keys:
            print("[Agent6] No Gemini Keys available!")
            return
        key = self.keys[self.current_key_idx]
        print(f"[Agent6] Using Key #{self.current_key_idx + 1} ({key[:5]}...)")
        genai.configure(api_key=key)
        self.model = genai.GenerativeModel(self.model_name)

    def _rotate_key(self):
        self.current_key_idx = (self.current_key_idx + 1) % len(self.keys)
        self._init_model()

    def _get_current_key(self) -> str:
        if not self.keys:
            return ""
        return self.keys[self.current_key_idx]

    def _call_ai(self, prompt: str) -> str:
        max_attempts = len(self.keys) * 2
        for attempt in range(max_attempts):
            try:
                response = self.model.generate_content(prompt)
                if response.parts:
                    return response.text
                else:
                    raise ValueError("Empty response from Gemini")
            except Exception as e:
                err = str(e)
                if "429" in err or "Quota" in err or "ResourceExhausted" in err:
                    print(f"[Agent6] Quota exceeded, rotating key...")
                    self._rotate_key()
                    time.sleep(1)
                    continue
                raise
        raise Exception("All API keys exhausted")

    def generate_ideas(self, persona: Dict, plevel_code: str, plevel_thought: str, plevel_stage: str) -> List[Dict]:
        """Generate 3 ad banner ideas using Chain-of-Thought and full Persona context."""
        
        # Inject richer persona data
        pains_str = '\n- '.join(persona.get('pains', []))
        msgs_str = '\n- '.join(persona.get('key_messages', []))
        visuals_str = '\n- '.join(persona.get('visuals', []))
        
        # Build an advanced Prompt with Chain-of-Thought
        prompt = f"""**ROLE**: Bạn là Senior Ads Creative Strategist & Art Director xuất sắc với 10 năm kinh nghiệm thiết kế quảng cáo cho App học Piano Simpia. Bạn rất am hiểu tâm lý khách hàng và các nguyên lý Visual Design.

**NHIỆM VỤ**: Dựa vào thông tin Persona và Giai đoạn tâm lý (P-Level) của khách hàng, hãy đề xuất 3 CONCEPT ẢNH BANNER xuất sắc nhất cho chiến dịch bán "Gói Simpia Trọn Đời".

=========================================
**NGỮ CẢNH KHÁCH HÀNG (PERSONA & P-LEVEL)**
- Tên khách hàng mục tiêu: {persona['name']} ({persona['desc']})
- Nỗi đau chính (Pain Points):
- {pains_str}
- Key Messages phù hợp: 
- {msgs_str}
- Gợi ý Visual truyền cảm hứng cho tệp này:
- {visuals_str}

**GIAI ĐOẠN TÂM LÝ HIỆN TẠI (CUSTOMER JOURNEY P-LEVEL)**:
- Mã: {plevel_code} - Giai đoạn: {plevel_stage}
- Suy nghĩ thực sự của khách hàng ở bước này: "{plevel_thought}"
=========================================

**HƯỚNG DẪN THIẾT KẾ CỐT LÕI (TRÍCH TỪ EXPERT GUIDE)**:
- Layout A: "Số liệu/Offer" – Con số thiết kế to (giá siêu hời, so sánh trung tâm với học tại nhà).
- Layout B: "Câu chuyện" – Hình nhân vật đại diện persona + block text insight hoặc testimonial.
- Layout C: "So sánh" – Chia layout 2 cột: Học Trung tâm vs Học Simpia trọn đời.
- Lợi ích kép: Bố mẹ nhàn - Con vui học; hoặc Đầu tư 1 lần - Học mãi mãi.
- Quy tắc vàng: 1 thông điệp chính/ảnh. Headline dưới 7 từ, Sub-Headline dưới 10 từ. Nhấn mạnh "TRỌN ĐỜI".

**CÁC ẢNH BEST PRACTICES CHIẾN THẮNG TRƯỚC ĐÂY**:
{self.image_best_practices}

**QUY TẮC NỘI DUNG BẮT BUỘC**:
1. **Hành vi**: Nhân vật trong ảnh BẮT BUỘC phải đang **chơi đàn piano** (playing piano).
2. **CTA Button**: Mọi ảnh phải có nút CTA với nội dung linh hoạt (biến thể cùng nghĩa):
   - Mã A (Acquisition): CTA mang nghĩa học thử/khám phá (ví dụ: "TRẢI NGHIỆM MIỄN PHÍ", "HỌC THỬ NGAY", "KHÁM PHÁ NGAY", "BẮT ĐẦU NGAY").
   - Mã R (Retention/Revenue): CTA mang nghĩa đăng ký/mua (ví dụ: "ĐĂNG KÝ NGAY", "MUA NGAY", "SỞ HỮU TRỌN ĐỜI", "NHẬN ƯU ĐÃI").
3. **Giá (Price)**:
   - Mã A: Hiển thị thông điệp học thử (ví dụ: "HỌC THỬ 0Đ", "FREE", "MIỄN PHÍ").
   - Mã R: Hiển thị giá gói cụ thể (ví dụ: "990.000đ/12 tháng" hoặc "2.990.000đ/trọn đời").

**YÊU CẦU ĐẦU RA (OUTPUT FORMAT)**:
Hãy suy nghĩ từng bước (Chain of Thought), phân tích sự kết nối giữa Persona và P-Level, sau đó mới trả về đúng 3 ideas dưới dạng JSON. Trả về đúng format sau, BAO GỒM cả block json (với ký hiệu ```json):

[THINKING]
- Phân tích insight: ...
- Ý tưởng cốt lõi: ...
- Chiến lược Visual: ...

```json
{{
    "ideas": [
        {{
            "id": 1,
            "layout": "A hoặc B hoặc C",
            "headline_vi": "Headline Cực Hook (tối đa 7 từ, IN HOA)",
            "sub_headline_vi": "Sub-headline giải thích (tối đa 10 từ)",
            "visual_description": "Mô tả background hoặc bối cảnh để AI vẽ (tiếng Anh, chi tiết, cinematic, lighting)",
            "persona_in_image": "Cách nhân vật chơi đàn piano (playing piano, biểu cảm, trang phục, tiếng Anh)",
            "mood": "Tone/Mood của ảnh (tiếng Anh)",
            "cta_button_vi": "Nội dung trên nút CTA (ví dụ: ĐĂNG KÝ NGAY hoặc TRẢI NGHIỆM MIỄN PHÍ NGAY)",
            "price_vi": "Giá hiển thị (ví dụ: 2.990.000đ hoặc HỌC THỬ 0Đ)",
            "rationale": "Vì sao ý tưởng này hiệu quả? (Tiếng Việt)"
        }}
    ]
}}
```"""
        raw = self._call_ai(prompt)
        
        # Robust JSON extraction
        try:
            # Find the JSON block
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', raw, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Fallback if AI didn't use markdown code blocks
                start = raw.find('{')
                end = raw.rfind('}') + 1
                json_str = raw[start:end]
                
            data = json.loads(json_str)
            return data.get("ideas", [])
        except Exception as e:
            print(f"[Agent6] JSON parse error: {e}")
            print(f"[Agent6] Raw output was: {raw[:200]}...")
            return [{"id": 1, "layout": "B", "headline_vi": "HỌC PIANO TRỌN ĐỜI", "sub_headline_vi": "Mua 1 lần, sở hữu mãi mãi", "visual_description": "A beautiful cinematic shot of a modern living room", "persona_in_image": "A person happily playing a digital piano with a tablet", "mood": "cinematic and warm", "cta_button_vi": "HỌC THỬ NGAY", "price_vi": "HỌC THỬ 0Đ", "rationale": "Fallback idea do lỗi JSON."}]
            
    def build_image_prompt(self, idea: Dict, persona: Dict) -> str:
        """Build the precise 4-Module Golden Template prompt for Image Generation."""
        
        # Module 1: Core Subject (Nhân vật) - Force playing behavior
        subject = idea.get('persona_in_image', 'A person happily playing a digital piano')
        if "playing" not in subject.lower():
            subject += " while playing a digital piano"
        
        # Module 2: Environment & Lighting (Bối cảnh)
        env = idea.get('visual_description', 'Cozy, modern home living room')
        mood = idea.get('mood', 'Cinematic, high-end, elegant')
        
        # Module 3: Composition & Style
        layout_side = "Left side has text, right side has subject" if idea.get("layout") == "A" else "Right side has text, left side has subject"
        
        # Module 4: Text Integration
        headline = idea.get('headline_vi', 'SIMPIA TRỌN ĐỜI')
        sub = idea.get('sub_headline_vi', 'Đầu tư 1 lần, học mãi mãi')
        cta_btn = idea.get('cta_button_vi', 'ĐĂNG KÝ NGAY')
        price = idea.get('price_vi', '')
        
        price_text = f' and a price tag saying "{price}"' if price else ""
        
        prompt = f"""Cinematic advertisement photography. 
[SUBJECT]: {subject}.
[ENVIRONMENT]: {env}. The scene is beautiful and engaging.
[MOOD/STYLE]: {mood}. Shallow depth of field, 4k resolution, high-end commercial quality. {layout_side}.
[AD GRAPHICS REPLICA]: The image should visibly include text graphics saying "{headline}" and "{sub}" cleanly integrated. In the bottom corner, there MUST be a high-quality call-to-action button saying "{cta_btn}"{price_text}."""
        
        return prompt

    def generate_image(self, prompt: str) -> Optional[str]:
        """Generate image using Gemini Imagen 3 API. Returns URL or None."""
        if not IMAGEN_AVAILABLE:
            print("[Agent6] Imagen SDK not available")
            return None
        if not self.keys:
            print("[Agent6] No API keys available for image generation")
            return None

        max_attempts = len(self.keys)
        for attempt in range(max_attempts):
            current_key = self._get_current_key()
            print(f"[Agent6] Generating image with Key #{self.current_key_idx + 1} (attempt {attempt + 1}/{max_attempts})...")
            try:
                client = genai_new.Client(api_key=current_key)
                response = client.models.generate_images(
                    model='imagen-3.0-generate-002',
                    prompt=prompt,
                    config=genai_types.GenerateImagesConfig(
                        number_of_images=1,
                        output_mime_type='image/png',
                    )
                )
                if response.generated_images and len(response.generated_images) > 0:
                    img_filename = f"banner_{uuid.uuid4().hex[:8]}.png"
                    img_path = GENERATED_DIR / img_filename
                    img_data = response.generated_images[0]
                    if hasattr(img_data, 'image') and hasattr(img_data.image, 'image_bytes'):
                        with open(img_path, 'wb') as f:
                            f.write(img_data.image.image_bytes)
                    elif hasattr(img_data, 'image') and hasattr(img_data.image, 'save'):
                        img_data.image.save(str(img_path))
                    else:
                        print(f"[Agent6] Unexpected image format: {type(img_data)}, attrs={dir(img_data)}")
                        return None
                    img_url = f"/static/generated/{img_filename}"
                    print(f"[Agent6] ✅ Image saved: {img_path}")
                    return img_url
                else:
                    print(f"[Agent6] No images in Imagen response")
                    return None
            except Exception as e:
                err = str(e)
                print(f"[Agent6] Image gen error: {err}")
                if "429" in err or "Quota" in err or "ResourceExhausted" in err:
                    print(f"[Agent6] Quota exceeded, rotating key...")
                    self._rotate_key()
                    time.sleep(2)
                    continue
                else:
                    # Fallback to Pollinations AI since Gemini Imagen might not be available/accessible
                    print("[Agent6] Gemini Image Gen failed/unavailable. Falling back to Pollinations AI...")
                    return self._generate_image_pollinations(prompt)
        
        print("[Agent6] All attempts exhausted, trying final fallback")
        return self._generate_image_pollinations(prompt)

    def _generate_image_pollinations(self, prompt: str) -> Optional[str]:
        """Free Fallback: Use Pollinations AI for image generation."""
        try:
            import urllib.request
            import urllib.parse
            
            # Use a fast flux model from Pollinations
            encoded_prompt = urllib.parse.quote(prompt)
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&model=flux"
            
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 SimpiaAgent/1.0'})
            
            img_filename = f"banner_poll_{uuid.uuid4().hex[:8]}.jpeg"
            img_path = GENERATED_DIR / img_filename
            
            with urllib.request.urlopen(req) as response:
                with open(img_path, 'wb') as f:
                    f.write(response.read())
                    
            img_url = f"/static/generated/{img_filename}"
            print(f"[Agent6] ✅ Image (Pollinations Fallback) saved: {img_path}")
            return img_url
            
        except Exception as e:
            print(f"[Agent6] Pollinations fallback error: {e}")
            return None


# Singleton
banner_agent = None

def get_banner_agent():
    global banner_agent
    if banner_agent is None:
        banner_agent = BannerAgent()
    return banner_agent
