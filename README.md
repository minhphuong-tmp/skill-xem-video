# 🎬 Antigravity Skill: Xem Video, Phân Biệt Người Nói & Xử Lý Song Song Nhiều Clip

Skill chuyên dụng cho **Google Antigravity (AGY)** và CLI trên macOS:
1. **Bóc băng toàn văn 100% (Full Verbatim):** Không tóm tắt, không lược bỏ bất kỳ câu chữ nào từ 00:00 đến hết video kèm mốc thời gian chính xác `[MM:SS - MM:SS]`.
2. **Phân biệt người nói (Ai với ai - Speaker Diarization):** Tự động phân tách rành mạch `🎙️ Người nói 1` và `👥 Người nói 2`.
3. **AI Review & Chuẩn hóa thuật ngữ IT:** Tự động phát hiện và sửa các từ mượn tiếng Anh / chuyên ngành IT bị nhận dạng sai lệch theo âm điệu tiếng Việt (ví dụ: *FixedUpdate, Update, Particle System, Object Pool, Collider, Trigger, Intern, Project, Jira, Docker, Knowledge Graph RAG AI, LeetCode, DSA...*).
4. **Xử lý song song đa luồng (Parallel Batch Processing):** Chạy đồng thời nhiều clip hoặc quét cả folder video chỉ trong vài chục giây bằng engine **Zipformer (sherpa-onnx vi-30M)** cho Tiếng Việt và **Whisper** cho Tiếng Anh/đa ngôn ngữ.
5. **Cắt clip tự động siêu tốc:** Cắt đoạn trích bất kỳ trong 0.05s bằng `ffmpeg` stream copy không cần render lại.

---

## ⚡ Cấu Trúc Thư Mục

```text
xem-video/
├── SKILL.md             # File định nghĩa skill cho Antigravity
├── README.md            # Tài liệu hướng dẫn sử dụng
├── .gitignore           # Bỏ qua venv, cache và file tạm
├── scripts/
│   ├── batch_transcribe.py   # Engine xử lý song song nhiều video / folder
│   ├── video_transcriber.py  # Engine bóc băng & diarization chi tiết
│   ├── cut_clip.py           # Công cụ cắt clip nhanh bằng ffmpeg
│   └── video_transcriber.js  # Node.js wrapper
└── models/
    └── sherpa-onnx-zipformer-vi-30M-int8-2026-02-09/ # Model ASR tiếng Việt offline
```

---

## 🚀 Hướng Dẫn Sử Dụng

### 1. Xử lý song song nhiều video cùng lúc (Khuyên dùng)
```bash
# Xử lý nhiều video / link YouTube cùng lúc:
python3 scripts/batch_transcribe.py clip1.mp4 clip2.mp4 "https://www.youtube.com/watch?v=..." -j 4 --no-save

# Hoặc quét và xử lý toàn bộ folder video:
python3 scripts/batch_transcribe.py /path/to/videos/ -j 4 --no-save
```

### 2. Xử lý 1 video đơn lẻ
```bash
python3 scripts/video_transcriber.py "video.mp4" --no-save
```

### 3. Cắt nhanh 1 đoạn clip cụ thể trong 0.05s
```bash
python3 scripts/cut_clip.py "video.mp4" 02:30 03:00 -o highlight.mp4
```

---

## 🛠️ Yêu Cầu Môi Trường
- **Hệ điều hành:** macOS / Linux
- **Python:** 3.9+
- **Công cụ phụ trợ:** `ffmpeg`, `yt-dlp`
- **Thư viện Python chính:** `sherpa-onnx`, `numpy`, `scipy`, `openai-whisper`
