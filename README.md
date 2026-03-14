# Agent 6: Banana AI Banner Generator

Hệ thống tự động sinh ý tưởng và hình ảnh Banner quảng cáo cho ứng dụng học Piano Simpia.

## Tính năng
- Chọn Persona (Chân dung khách hàng) mục tiêu.
- Áp dụng các cấp độ P-Level (Tâm lý khách hàng) để tối ưu Idea.
- Sinh 3 Concept Banner hoàn chỉnh dựa trên Persona và Giai đoạn tâm lý.
- Tự động vẽ ảnh bằng Google Gemini Imagen 3 hoặc Fallback sang Pollinations AI.
- Tích hợp sẵn giá và nút CTA phù hợp với từng giai đoạn Acquisition/Retention.

## Cài đặt
1. Clone repo:
   ```bash
   git clone https://github.com/tupham-create/tupham-nghichngom
   cd tupham-nghichngom
   ```

2. Cài đặt thư viện:
   ```bash
   pip install -r requirements.txt
   ```

3. Cấu hình API Key:
   - Copy file `.env.example` thành `.env`.
   - Điền GEMINI_API_KEY của bạn vào.

## Chạy ứng dụng
```bash
python server.py
```
Sau đó truy cập: `http://127.0.0.1:8000/agent6`

## Cấu trúc thư mục
- `agent6_banner_generator.py`: Logic cốt lõi của Agent 6.
- `server.py`: FastAPI Server.
- `static/agent6.html`: Giao diện Web.
- `personas/`: Chứa các tài liệu Persona và Matrix P-Level.
