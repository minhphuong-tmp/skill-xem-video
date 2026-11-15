---
name: xem-video
description: >-
  Xem video, bóc băng và trích xuất toàn bộ cuộc trò chuyện/lời thoại kèm mốc thời gian (timestamps),
  chia các đoạn hội thoại theo mạch nội dung kèm tóm tắt đầy đủ cả VẤN ĐỀ lẫn CÁCH XỬ LÝ/GIẢI PHÁP cụ thể trước mỗi đoạn,
  phân loại người nói (ai với ai - Speaker Diarization), tự động AI Review & chuẩn hóa thuật ngữ IT,
  hỗ trợ cắt clip tự động siêu tốc bằng ffmpeg, và HỖ TRỢ XỬ LÝ SONG SONG NHIỀU CLIP CÙNG LÚC để bóc băng hàng loạt siêu nhanh.
  Kích hoạt khi người dùng gõ "/skill xem video", "xem video", "xem clip", "bóc băng video",
  "cắt clip", "ai với ai", "chạy song song", hoặc gửi kèm link/nhiều file video/folder video trên Mac.
---

# Skill: Xem Video, Phân Biệt Người Nói (Ai Với Ai), Cắt Clip & Xử Lý Song Song Nhiều Clip

Skill này hỗ trợ xử lý từ 1 clip đơn lẻ cho đến **hàng loạt nhiều clip cùng lúc (chạy song song đa luồng)**:
1. **Bóc băng toàn văn 100% (Full Verbatim):** Không tóm tắt thay lời thoại, không lược bỏ bất kỳ câu chữ nào từ 00:00 đến hết clip.
2. **Chia đoạn theo mạch nội dung & Tóm tắt trọn vẹn "Vấn Đề ➔ Cách Xử Lý" trước mỗi đoạn:** Tự động chia cuộc trò chuyện thành các phân đoạn logic; ngay trước mỗi đoạn đều có khối tóm tắt Tiếng Việt nêu rõ **không chỉ vấn đề đang bàn mà bắt buộc phải chỉ rõ họ đã xử lý / giải quyết vấn đề đó như thế nào** (cơ chế, công cụ, quy trình, hướng tháo gỡ hoặc kết luận chốt lại).
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

### 2. BẮT BUỘC IN PHẦN TÓM TẮT NHANH TỔNG QUAN (OTM — ĐẦY ĐỦ CẢ VẤN ĐỀ LẪN CÁCH XỬ LÝ) TRƯỚC KHI IN FULL TRANSCRIPT:
- Sau khi bóc băng xong và trước khi in toàn bộ lời thoại, **BẮT BUỘC PHẢI IN MỘT KHỐI TÓM TẮT NHANH** (OTM - Overview/Tóm lược) gồm:
  - 🎯 **Chủ đề cốt lõi** của video (1–2 câu).
  - 👥 **Thành phần người nói** (bao nhiêu người, vai trò).
  - 🛠️ **Các vấn đề đặt ra & Cách xử lý / Giải pháp tương ứng (3–6 điểm chính):**
    - **NGHIÊM CẤM** kiểu tóm tắt chung chung chỉ nêu đầu mục/vấn đề (ví dụ: *"Bàn về lỗi lag game"*, *"Nói về khó khăn khi làm AI Agent"*).
    - Với mỗi điểm chính, **BẮT BUỘC phải viết theo cặp `Vấn đề / Thách thức ➔ Cách họ xử lý / Giải pháp / Kết luận cụ thể`** đã được bàn tới trong cuộc trò chuyện (họ dùng kỹ thuật gì, đổi sang công cụ nào, xử lý từng bước ra sao, tại sao cách đó hiệu quả).
  - ⏱️ **Thời lượng** và **ngôn ngữ**.
- Khối OTM này phải nằm **TRƯỚC** phần full transcript, giúp người dùng chỉ cần lướt qua là nắm được cả bài toán lẫn lời giải thực chiến của video.

### 3. BẮT BUỘC CHIA CÁC ĐOẠN CUỘC TRÒ CHUYỆN & TÓM TẮT RÕ "VẤN ĐỀ + CÁCH XỬ LÝ" TRƯỚC MỖI ĐOẠN:
- **TUYỆT ĐỐI KHÔNG** gộp toàn bộ cuộc trò chuyện thành một bảng dài liền tù tì từ đầu đến cuối mà không có phân đoạn.
- Phải chia phần `Full Transcript` thành **các đoạn hội thoại logic theo mạch chủ đề / chuyển ý / từng cặp câu hỏi - trả lời**.
- **Ngay phía trước mỗi đoạn cuộc trò chuyện**, **BẮT BUỘC** phải có:
  1. **Tiêu đề phân đoạn kèm khoảng thời gian** (`### 🔹 Đoạn X [MM:SS - MM:SS] — <Tiêu đề ngắn gọn>`).
  2. **Khối tóm tắt nội dung & cách giải quyết của đoạn đó** viết bằng **Tiếng Việt rõ ràng, đầy đủ ý (2–4 dòng)** (ngay cả khi lời thoại gốc là Tiếng Anh hay ngôn ngữ khác, phần tóm tắt vẫn viết bằng Tiếng Việt):
     - **BẮT BUỘC phải nêu đủ cả 2 vế:**
       - **❓ Vấn đề / Bối cảnh đặt ra:** Đoạn này đang nêu ra bài toán, lỗi, câu hỏi hay tình huống thực tế gì?
       - **💡 Cách xử lý / Giải pháp / Chốt ý:** Trong cuộc trò chuyện, người nói đã giải quyết/tháo gỡ vấn đề đó cụ thể như thế nào? (Nêu rõ phương pháp, cơ chế hoạt động, bước thực hiện, công cụ sử dụng, hoặc quyết định/bài học rút ra — nếu đoạn đó là phần giới thiệu/mở bài chưa có giải pháp thì ghi rõ hướng tiếp cận mà người nói dẫn dắt sang phần sau).
     - **Ví dụ đối chiếu để tránh lỗi tóm tắt hời hợt:**
       - ❌ *Sai (chỉ nêu vấn đề, bỏ sót cách xử lý):* `Đoạn này hai người thảo luận về việc context của AI bị đầy khi làm dự án lớn và lỗi sinh code sai.`
       - ✅ *Đúng (nêu rõ cả vấn đề lẫn cách xử lý):*
         - `❓ Vấn đề:` Khi dự án lớn dần, nhồi toàn bộ tài liệu vào làm đầy cửa sổ context khiến AI bị loạn và sửa code hỏng dây chuyền.
         - `💡 Cách xử lý:` Tách quy trình thành 3 bước (Research ➔ Plan ➔ Implement), lưu trạng thái ra file `SPEC.md` cố định trên ổ cứng và mở session mới sạch sẽ (`/clear`) cho từng tính năng nhỏ kèm bộ test tự động kiểm chứng.
- Ngay bên dưới khối tóm tắt là bảng lời thoại chi tiết 100% của đoạn đó.
- **Format hiển thị chuẩn bắt buộc (OTM + Các đoạn hội thoại có tóm tắt Vấn đề & Cách xử lý):**
  ```markdown
  ## 📋 Tóm Tắt Nhanh (OTM)
  🎯 **Chủ đề:** ...
  👥 **Người nói:** ...
  🛠️ **Vấn đề & Cách xử lý cốt lõi:**
    1. **[Tên vấn đề 1]:** [Mô tả ngắn vấn đề] ➔ **Cách xử lý:** [Giải pháp / cơ chế / các bước cụ thể họ áp dụng trong video].
    2. **[Tên vấn đề 2]:** [Mô tả ngắn vấn đề] ➔ **Cách xử lý:** [Giải pháp / hướng tháo gỡ / kết luận cụ thể].
    3. **[Tên vấn đề 3]:** [Mô tả ngắn vấn đề] ➔ **Cách xử lý:** [Giải pháp / hướng tháo gỡ / kết luận cụ thể].
  ⏱️ **Thời lượng:** ... | 🔤 **Ngôn ngữ:** ...

  ---

  ## 💬 Full Transcript (Toàn Bộ Lời Thoại Theo Từng Đoạn)

  ### 🔹 Đoạn 1 `[00:00 - 02:15]` — [Tiêu đề ngắn về chủ đề đoạn 1]
  > 📝 **Tóm tắt đoạn:**
  > - **Vấn đề / Bối cảnh:** [Bài toán, câu hỏi hoặc tình huống thực tế được đặt ra trong đoạn này]
  > - **Cách xử lý / Nội dung chính:** [Họ đã giải quyết, phân tích cơ chế hoặc chốt phương án hành động cụ thể như thế nào trong đoạn hội thoại bên dưới]

  | Mốc thời gian | Người nói | Lời thoại chi tiết (Full Verbatim Dialogue) |
  | :--- | :--- | :--- |
  | `[00:00 - 00:12]` | **🎙️ Người nói 1** | ... |
  | `[00:12 - 00:28]` | **👥 Người nói 2** | ... |

  ### 🔹 Đoạn 2 `[02:15 - 05:40]` — [Tiêu đề ngắn về chủ đề đoạn 2]
  > 📝 **Tóm tắt đoạn:**
  > - **Vấn đề / Bối cảnh:** [Vấn đề tiếp theo phát sinh trong cuộc trò chuyện]
  > - **Cách xử lý / Nội dung chính:** [Giải pháp kỹ thuật / quy trình thực tế mà người nói đưa ra để xử lý dứt điểm]

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
