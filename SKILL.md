---
name: xem-video
description: >-
  Xem video, bóc băng và trích xuất toàn bộ cuộc trò chuyện/lời thoại kèm mốc thời gian (timestamps),
  phân loại người nói (ai với ai - Speaker Diarization), tự động AI Review & chuẩn hóa thuật ngữ IT,
  hỗ trợ cắt clip tự động siêu tốc bằng ffmpeg, và HỖ TRỢ XỬ LÝ SONG SONG NHIỀU CLIP CÙNG LÚC để bóc băng hàng loạt siêu nhanh.
  Kích hoạt khi người dùng gõ "/skill xem video", "xem video", "xem clip", "bóc băng video",
  "cắt clip", "ai với ai", "chạy song song", hoặc gửi kèm link/nhiều file video/folder video trên Mac.
---

# Skill: Xem Video, Phân Biệt Người Nói (Ai Với Ai), Cắt Clip & Xử Lý Song Song Nhiều Clip

Skill này hỗ trợ xử lý từ 1 clip đơn lẻ cho đến **hàng loạt nhiều clip cùng lúc (chạy song song đa luồng)**:
1. **Bóc băng toàn văn 100% (Full Verbatim):** Không tóm tắt, không lược bỏ bất kỳ câu chữ nào từ 00:00 đến hết clip.
2. **Phân loại người nói (Ai với ai - Speaker Diarization):** Tự động phân tách `🎙️ Người nói 1` và `👥 Người nói 2`.
3. **BẮT BUỘC AI Review & Chuẩn Hóa Thuật Ngữ IT Trước Khi Trả Về:** Tự động sửa triệt để tất cả lỗi phiên âm sai lệch các từ mượn tiếng Anh chuyên ngành công nghệ (như `FixedUpdate`, `Update`, `Particle System`, `Object Pool`, `Collider`, `Trigger`, `intern`, `keyword`, `project`, `Jira`, `OpenFlow`, `Docker`, `Knowledge Graph RAG AI`, `LeetCode`, `DSA`, `Fsoft`, `blockchain`, `Cloud`, `DevOps`...), ghép nối câu thoại liền mạch theo đúng ngữ cảnh hỏi - đáp tự nhiên.
4. **Không Lưu Rác - Tự Động Xóa Dọn Dẹp File Tạm:** Người dùng chỉ cần đọc toàn bộ text trực tiếp trong khung chat, hệ thống tự động xóa sạch các file tạm (`.transcript.md`, thư mục `_cuts/`) sau khi hiển thị ra chat.
5. **Xử lý song song đa luồng (Parallel Batch Processing):** Khi người dùng gửi nhiều clip hoặc nguyên 1 thư mục video, hệ thống tự động phân chia đa luồng xử lý song song để tiết kiệm tối đa thời gian.

---

## ⚡ Các Công Cụ Có Sẵn Trong Skill

- [`batch_transcribe.py`](./scripts/batch_transcribe.py): **Engine xử lý song song nhiều clip cùng lúc** (hoặc quét cả folder video).
- [`video_transcriber.py`](./scripts/video_transcriber.py): Engine phân tích chi tiết cho từng video đơn lẻ.
- [`cut_clip.py`](./scripts/cut_clip.py): Công cụ cắt nhanh 1 đoạn clip trong 0.05s.

## 🔑 Mật Khẩu Hệ Thống / macOS Keychain (Tùy chọn)
- Nếu hệ thống hoặc Google Chrome / macOS Keychain yêu cầu mật khẩu để trích xuất cookies hoặc chạy quyền quản trị:
  `security unlock-keychain -p <YOUR_PASSWORD> ~/Library/Keychains/login.keychain-db`

---

## 🚀 Các Tùy Chọn Sử Dụng

### 1. Khi Xử Lý Song Song Nhiều Clip Cùng Lúc (Khuyên dùng)
```bash
# Chạy song song nhiều file video (dùng cờ --no-save để không tạo file rác):
python3 ~/.agents/skills/xem-video/scripts/batch_transcribe.py clip1.mp4 clip2.mp4 clip3.mp4 -j 4 --no-save

# Hoặc quét và xử lý song song toàn bộ video trong 1 folder:
python3 ~/.agents/skills/xem-video/scripts/batch_transcribe.py "/Users/macos/Desktop/tiktok/tiktoktool/records/" -j 3 --no-save
```

### 2. Khi Xử Lý 1 Clip Đơn Lẻ
```bash
python3 ~/.agents/skills/xem-video/scripts/video_transcriber.py "video.mp4" --no-save
```

### 3. Cắt Nhanh 1 Đoạn Cụ Thể Trong 0.05s (Khi người dùng yêu cầu cắt)
```bash
python3 ~/.agents/skills/xem-video/scripts/cut_clip.py "video.mp4" 02:30 03:00 -o highlight.mp4
```

---

## ⚠️ QUY TẮC BẮT BUỘC KHI PHẢN HỒI CHO NGƯỜI DÙNG:

### 1. BẮT BUỘC THỰC HIỆN AI REVIEW & CHUẨN HÓA THUẬT NGỮ IT:
- Sau khi ASR (Zipformer / Whisper) sinh lời thoại thô, **AI Agent BẮT BUỘC PHẢI THỰC HIỆN BƯỚC AI REVIEW**:
  - Tự động sửa lại tất cả các từ mượn tiếng Anh / thuật ngữ IT, Game Dev, công nghệ bị phiên âm sai lệch theo âm điệu tiếng Việt:
    - `in tên` / `an ninh tơ` ➔ `Intern`
    - `fish update` / `vit update` / `visa best` / `afish` ➔ `FixedUpdate`
    - `offid` ➔ `Update`
    - `kiềm quốc` / `kim word` / `kwork` ➔ `keyword`
    - `vactical situm` ➔ `Particle System`
    - `opt pull` ➔ `Object Pool`
    - `polier` ➔ `Collider`
    - `chiếc gờ` / `check g` ➔ `Trigger`
    - `hàm spam` ➔ `hàm Spawn`
    - `nô lực rap gây AI` / `rap gây AI` ➔ `Knowledge Graph RAG AI`
    - `bản siga` ➔ `bảng Jira`
    - `openlo` ➔ `OpenFlow`
    - `có cơ` ➔ `Docker`
    - `fisco` ➔ `fix code`
    - `độ chép` / `độ dép` / `protec` / `crosic` ➔ `project`
    - `rose nào` ➔ `role nào`
    - `tast` / `taxi nó` ➔ `task / task cho nó`
    - `canvat` ➔ `Canvas`
    - và mọi từ mượn tiếng Anh khác theo đúng ngữ cảnh thực tế của cuộc trò chuyện.
  - Chuẩn hóa ngữ pháp, dấu câu, ghép nối mạch lạc tự nhiên trước khi trả về.

### 2. BẮT BUỘC HIỂN THỊ FULL TEXT TRỰC TIẾP RA KHUNG CHAT:
- Chạy xong BẮT BUỘC PHẢI IN TOÀN BỘ LỜI THOẠI (FULL VERBATIM DIALOGUE ĐÃ QUA AI REVIEW) trực tiếp ra màn hình chat cho người dùng đọc ngay.
- TUYỆT ĐỐI KHÔNG CHỈ GỬI LINK FILE HOẶC CHỈ TÓM TẮT. Người dùng muốn đọc toàn bộ nội dung trực tiếp tại khung chat.
- Không được dùng dấu ba chấm (`...`) để cắt bớt câu chữ. Phải in chi tiết 100% từng câu thoại kèm mốc thời gian `[MM:SS - MM:SS]` và phân rõ người nói (`🎙️ Người nói 1` vs `👥 Người nói 2`).

### 3. TỰ ĐỘNG XÓA DỌN DẸP TOÀN BỘ FILE TẠM (KHÔNG LƯU RÁC TRÊN MÁY):
- Người dùng CHỈ CẦN ĐỌC TOÀN BỘ NỘI DUNG TRỰC TIẾP TRÊN KHUNG CHAT NÀY, TUYỆT ĐỐI KHÔNG CẦN LƯU BẤT KỲ FILE NÀO TRÊN MÁY.
- Ưu tiên dùng cờ `--no-save` khi chạy script.
- Nếu quá trình xử lý có sinh ra bất kỳ file `.transcript.md` hoặc thư mục `_cuts/` nào, sau khi đã lấy được nội dung và in đầy đủ ra khung chat, **BẮT BUỘC PHẢI TỰ ĐỘNG XÓA NGAY LẬP TỨC** (`rm -rf`) các file và thư mục đó, trả lại không gian sạch sẽ 100% cho thư mục người dùng.
