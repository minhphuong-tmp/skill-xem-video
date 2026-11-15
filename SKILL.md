---
name: xem-video
description: >-
  Xem video, bóc băng và trích xuất toàn bộ cuộc trò chuyện/lời thoại kèm mốc thời gian (timestamps),
  chia các đoạn hội thoại theo mạch nội dung kèm dòng tóm tắt ngắn trước mỗi đoạn để biết ngay đoạn đó nói về gì,
  phân loại người nói (ai với ai - Speaker Diarization), tự động AI Review & chuẩn hóa thuật ngữ IT,
  hỗ trợ cắt clip tự động siêu tốc bằng ffmpeg, và HỖ TRỢ XỬ LÝ SONG SONG NHIỀU CLIP CÙNG LÚC để bóc băng hàng loạt siêu nhanh.
  Kích hoạt khi người dùng gõ "/skill xem video", "xem video", "xem clip", "bóc băng video",
  "cắt clip", "ai với ai", "chạy song song", hoặc gửi kèm link/nhiều file video/folder video trên Mac.
---

# Skill: Xem Video, Phân Biệt Người Nói (Ai Với Ai), Cắt Clip & Xử Lý Song Song Nhiều Clip

Skill này hỗ trợ xử lý từ 1 clip đơn lẻ cho đến **hàng loạt nhiều clip cùng lúc (chạy song song đa luồng)**:
1. **Bóc băng toàn văn 100% (Full Verbatim):** Không tóm tắt thay lời thoại, không lược bỏ bất kỳ câu chữ nào từ 00:00 đến hết clip.
2. **Chia đoạn theo mạch nội dung & Tóm tắt trước mỗi đoạn hội thoại:** Tự động chia cuộc trò chuyện thành các phân đoạn logic theo chủ đề/mạch chuyện; ngay trước mỗi đoạn đều có dòng **📝 Tóm tắt đoạn** (bằng Tiếng Việt súc tích) để biết ngay đoạn hội thoại bên dưới đang nói về cái gì.
3. **Phân loại người nói (Ai với ai - Speaker Diarization):** Tự động phân tách `🎙️ Người nói 1` và `👥 Người nói 2`.
4. **BẮT BUỘC AI Review & Chuẩn Hóa Thuật Ngữ IT Trước Khi Trả Về:** Tự động sửa triệt để tất cả lỗi phiên âm sai lệch các từ mượn tiếng Anh chuyên ngành công nghệ (như `FixedUpdate`, `Update`, `Particle System`, `Object Pool`, `Collider`, `Trigger`, `intern`, `keyword`, `project`, `Jira`, `OpenFlow`, `Docker`, `Knowledge Graph RAG AI`, `LeetCode`, `DSA`, `Fsoft`, `blockchain`, `Cloud`, `DevOps`...), ghép nối câu thoại liền mạch theo đúng ngữ cảnh hỏi - đáp tự nhiên.
5. **Không Lưu Rác - Tự Động Xóa Dọn Dẹp File Tạm:** Người dùng chỉ cần đọc toàn bộ text trực tiếp trong khung chat, hệ thống tự động xóa sạch các file tạm (`.transcript.md`, thư mục `_cuts/`) sau khi hiển thị ra chat.
6. **Xử lý song song đa luồng (Parallel Batch Processing):** Khi người dùng gửi nhiều clip hoặc nguyên 1 thư mục video, hệ thống tự động phân chia đa luồng xử lý song song để tiết kiệm tối đa thời gian.

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

### 2. BẮT BUỘC IN PHẦN TÓM TẮT NHANH TỔNG QUAN (OTM) TRƯỚC KHI IN FULL TRANSCRIPT:
- Sau khi bóc băng xong và trước khi in toàn bộ lời thoại, **BẮT BUỘC PHẢI IN MỘT KHỐI TÓM TẮT NHANH** (OTM - Overview/Tóm lược) gồm:
  - 🎯 **Chủ đề chính** của video (1-2 câu)
  - 👥 **Thành phần người nói** (bao nhiêu người, vai trò)
  - 📌 **3-5 điểm chính** (key takeaways) của toàn bộ nội dung video
  - ⏱️ **Thời lượng** và **ngôn ngữ**
- Khối OTM này phải nằm **TRƯỚC** phần full transcript, giúp người dùng nắm bắt tổng quan trước khi đọc chi tiết.

### 3. BẮT BUỘC CHIA CÁC ĐOẠN CUỘC TRÒ CHUYỆN & ĐẶT DÒNG TÓM TẮT TRƯỚC MỖI ĐOẠN:
- **TUYỆT ĐỐI KHÔNG** gộp toàn bộ cuộc trò chuyện thành một bảng dài liền tù tì từ đầu đến cuối mà không có phân đoạn.
- Phải chia phần `Full Transcript` thành **các đoạn hội thoại logic theo mạch chủ đề / chuyển ý / từng câu hỏi - trả lời** (ví dụ mỗi đoạn kéo dài vài câu đến vài phút tùy độ dài video).
- **Ngay phía trước mỗi đoạn cuộc trò chuyện**, **BẮT BUỘC** phải có:
  1. **Tiêu đề phân đoạn kèm khoảng thời gian** (`### 🔹 Đoạn X [MM:SS - MM:SS] — <Tiêu đề ngắn gọn>`).
  2. **Dòng tóm tắt nội dung tương ứng của đoạn đó** (`> 📝 **Tóm tắt đoạn:** ...`) viết bằng **Tiếng Việt ngắn gọn (1–2 câu)** giải thích rõ đoạn cuộc trò chuyện ngay bên dưới đang nói về vấn đề gì (ngay cả khi lời thoại gốc là Tiếng Anh hay ngôn ngữ khác, dòng tóm tắt đoạn vẫn viết bằng Tiếng Việt để lướt nhanh nắm ý ngay).
- Ngay bên dưới dòng tóm tắt là bảng lời thoại chi tiết 100% của đoạn đó.
- **Format hiển thị chuẩn bắt buộc (OTM + Các đoạn hội thoại có tóm tắt riêng):**
  ```markdown
  ## 📋 Tóm Tắt Nhanh (OTM)
  🎯 **Chủ đề:** ...
  👥 **Người nói:** ...
  📌 **Điểm chính:**
    1. ...
    2. ...
    3. ...
  ⏱️ **Thời lượng:** ... | 🔤 **Ngôn ngữ:** ...

  ---

  ## 💬 Full Transcript (Toàn Bộ Lời Thoại Theo Từng Đoạn)

  ### 🔹 Đoạn 1 `[00:00 - 02:15]` — [Tiêu đề ngắn về chủ đề đoạn 1]
  > 📝 **Tóm tắt đoạn:** [1–2 câu tóm tắt nội dung tương ứng để người đọc biết ngay đoạn hội thoại này đang bàn về cái gì]

  | Mốc thời gian | Người nói | Lời thoại chi tiết (Full Verbatim Dialogue) |
  | :--- | :--- | :--- |
  | `[00:00 - 00:12]` | **🎙️ Người nói 1** | ... |
  | `[00:12 - 00:28]` | **👥 Người nói 2** | ... |

  ### 🔹 Đoạn 2 `[02:15 - 05:40]` — [Tiêu đề ngắn về chủ đề đoạn 2]
  > 📝 **Tóm tắt đoạn:** [1–2 câu tóm tắt nội dung chính của đoạn hội thoại thứ 2]

  | Mốc thời gian | Người nói | Lời thoại chi tiết (Full Verbatim Dialogue) |
  | :--- | :--- | :--- |
  | `[02:15 - 02:40]` | **🎙️ Người nói 1** | ... |
  | `[02:40 - 03:05]` | **👥 Người nói 2** | ... |
  ```

### 4. BẮT BUỘC ĐỌC HẾT FILE OUTPUT BỊ TRUNCATE & LUÔN IN ĐẦY ĐỦ 100% TỪNG CÂU THOẠI (NGHIÊM CẤM CẮT NGẮN DÙ VIDEO DÀI):
- **Xử lý khi kết quả terminal bị ẩn bớt (`truncated due to being too long`):** Với các video dài (30 phút, 1 tiếng, 2 tiếng+), output của lệnh chạy script thường bị hệ thống cắt bớt phần giữa trong khung preview và lưu bản đầy đủ tại file tạm `.../output.txt`. Khi gặp thông báo này, **AI Agent BẮT BUỘC PHẢI dùng tool đọc file (`read_file` kết hợp `StartLine`/`EndLine` lặp nhiều lần cho đến dòng cuối cùng)** để đọc trọn vẹn **100% tất cả các dòng lời thoại** từ `00:00` đến giây cuối cùng trước khi trả lời.
- **NGHIÊM CẤM TUYỆT ĐỐI VIỆC RÚT GỌN / TÓM TẮT ĐOẠN GIỮA TRONG BẢNG LỜI THOẠI:**
  - Tuyệt đối **KHÔNG ĐƯỢC** vì thấy video dài (500–1000+ câu) mà lười biếng gộp hàng chục phút thành 1 dòng mô tả kiểu `[18:45 - 28:10] Deep dive into...` hay `[08:30 - 12:00] Discussing...`. Làm vậy là **VI PHẠM NGHIÊM TRỌNG** quy tắc của skill.
  - Video có bao nhiêu câu thoại thực tế thì phải hiển thị **đầy đủ 100% từng câu thoại nguyên văn (Full Verbatim)** từ giây đầu tiên đến giây cuối cùng, bất kể video dài 5 phút hay 2 tiếng.
  - Dòng `> 📝 **Tóm tắt đoạn:**` nằm **phía trên** mỗi bảng chỉ để dẫn nhập cho dễ nắm ý, **tuyệt đối không được dùng nó để cắt bớt bất kỳ câu chữ nào bên trong bảng lời thoại**.
  - Không được dùng dấu ba chấm (`...`) để lược bỏ câu chữ, không được chỉ gửi link file tạm.
  - Trường hợp duy nhất nếu video siêu dài (nhiều giờ đồng hồ) khiến tổng số chữ vượt quá giới hạn output tối đa của 1 tin nhắn đơn lẻ: phải in nguyên văn 100% từng câu liên tục từ `00:00` đi xa nhất có thể (không được nhảy cóc đoạn giữa), và báo rõ mốc thời gian dừng để in nối tiếp phần còn lại nguyên văn 100% ở lượt kế tiếp.

### 5. TỰ ĐỘNG XÓA DỌN DẸP TOÀN BỘ FILE TẠM (KHÔNG LƯU RÁC TRÊN MÁY):
- Người dùng CHỈ CẦN ĐỌC TOÀN BỘ NỘI DUNG TRỰC TIẾP TRÊN KHUNG CHAT NÀY, TUYỆT ĐỐI KHÔNG CẦN LƯU BẤT KỲ FILE NÀO TRÊN MÁY.
- Ưu tiên dùng cờ `--no-save` khi chạy script.
- Nếu quá trình xử lý có sinh ra bất kỳ file `.transcript.md` hoặc thư mục `_cuts/` nào, sau khi đã lấy được nội dung và in đầy đủ ra khung chat, **BẮT BUỘC PHẢI TỰ ĐỘNG XÓA NGAY LẬP TỨC** (`rm -rf`) các file và thư mục đó, trả lại không gian sạch sẽ 100% cho thư mục người dùng.
