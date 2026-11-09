#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parallel Batch Video Transcriber & Diarization Engine
Xử lý song song nhiều clip cùng lúc để lấy mốc thời gian, lời thoại ("ai với ai") và script cắt.

Cách dùng:
  # 1. Chạy nhiều file clip cùng lúc:
  python3 batch_transcribe.py clip1.mp4 clip2.mp4 clip3.mp4

  # 2. Quét cả một folder chứa nhiều video:
  python3 batch_transcribe.py /path/to/video_folder/

  # 3. Tùy chỉnh số luồng song song (mặc định: 3):
  python3 batch_transcribe.py *.mp4 -j 4 --model tiny
"""

import sys
import os
import argparse
import subprocess
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Auto-re-execute with dedicated .venv if not already using it
SKILL_DIR = Path(__file__).resolve().parent.parent
VENV_PYTHON = SKILL_DIR / ".venv" / "bin" / "python"
SINGLE_TRANSCRIBER = SKILL_DIR / "scripts" / "video_transcriber.py"

if VENV_PYTHON.exists() and sys.executable != str(VENV_PYTHON):
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON)] + sys.argv)

VIDEO_EXTENSIONS = {'.mp4', '.mov', '.mkv', '.webm', '.avi', '.m4v', '.flv', '.wmv'}

def collect_videos(inputs):
    """Collect all valid video files or URLs from arguments."""
    results = []
    for item in inputs:
        item_str = item.strip().strip("'\"")
        # Check URL
        if item_str.startswith(('http://', 'https://', 'www.')):
            results.append(item_str)
            continue
        
        # Expand path
        p = Path(os.path.expanduser(item_str.replace(r'\ ', ' ')))
        if p.is_dir():
            # Scan directory
            for f in sorted(p.iterdir()):
                if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS:
                    results.append(str(f.resolve()))
        elif p.is_file():
            results.append(str(p.resolve()))
        else:
            # Check in Downloads/Movies
            home = Path.home()
            found = False
            for parent in [Path.cwd(), home / "Downloads", home / "Movies", home / "Desktop"]:
                cand = parent / item_str
                if cand.exists():
                    if cand.is_dir():
                        for f in sorted(cand.iterdir()):
                            if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS:
                                results.append(str(f.resolve()))
                    else:
                        results.append(str(cand.resolve()))
                    found = True
                    break
            if not found:
                sys.stderr.write(f"⚠️ Cảnh báo: Không tìm thấy nguồn `{item_str}`\n")
    return list(dict.fromkeys(results))  # Deduplicate preserving order

def process_one_video(video_item, engine="auto", model="base", lang="vi", cut_flag=False, no_save=False):
    """Execute video_transcriber.py on a single video in a subprocess."""
    start_t = time.time()
    v_name = os.path.basename(video_item) if not video_item.startswith(('http://', 'https://')) else video_item
    print(f"🚀 [Bắt đầu xử lý song song] {v_name}")
    
    cmd = [
        str(VENV_PYTHON) if VENV_PYTHON.exists() else "python3",
        str(SINGLE_TRANSCRIBER),
        video_item,
        "--engine", engine,
        "--model", model,
        "--lang", lang
    ]
    if cut_flag:
        cmd.append("--cut")
    if no_save:
        cmd.append("--no-save")

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        elapsed = time.time() - start_t
        print(f"✅ [Hoàn tất trong {elapsed:.1f}s] {v_name}")
        
        transcript_path = f"{os.path.splitext(video_item)[0]}.transcript.md" if not video_item.startswith(('http://', 'https://')) else "transcript.md"
        cuts_script = f"{os.path.splitext(video_item)[0]}_cuts/cut_clips.sh" if not video_item.startswith(('http://', 'https://')) else "cut_clips.sh"
        
        return {
            'video': video_item,
            'name': v_name,
            'success': True,
            'elapsed': elapsed,
            'transcript': transcript_path,
            'cuts_script': cuts_script if os.path.exists(cuts_script) else None,
            'output': res.stdout
        }
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start_t
        print(f"❌ [Lỗi sau {elapsed:.1f}s] {v_name}")
        return {
            'video': video_item,
            'name': v_name,
            'success': False,
            'elapsed': elapsed,
            'error': e.stderr
        }

def main():
    parser = argparse.ArgumentParser(description="Parallel batch video transcriber")
    parser.add_argument("inputs", nargs="+", help="Video files, URLs, or directories containing videos")
    parser.add_argument("-j", "--jobs", type=int, default=3, help="Number of parallel workers (default: 3)")
    parser.add_argument("--engine", default="auto", choices=["auto", "zipformer", "whisper"], help="ASR Engine (default: auto)")
    parser.add_argument("--model", default="base", choices=["tiny", "base", "small"], help="Whisper model size")
    parser.add_argument("--lang", default="vi", help="Language code")
    parser.add_argument("--cut", action="store_true", help="Automatically cut video clips for all processed videos")
    parser.add_argument("--no-save", action="store_true", help="Do not save transcript or cuts files to disk (chat output only)")
    args = parser.parse_args()

    videos = collect_videos(args.inputs)
    if not videos:
        print("❌ Không tìm thấy video hợp lệ nào để xử lý.")
        sys.exit(1)

    print(f"\n=======================================================")
    print(f"🎬 TỔNG SỐ CLIP CẦN XỬ LÝ SONG SONG: {len(videos)} clip")
    print(f"⚡ Số luồng xử lý đồng thời (Concurrency): {args.jobs} workers")
    print(f"🤖 Engine ASR: {args.engine} (Zipformer / Whisper)")
    print(f"=======================================================\n")

    start_all = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=min(args.jobs, len(videos))) as executor:
        future_to_video = {
            executor.submit(process_one_video, v, engine=args.engine, model=args.model, lang=args.lang, cut_flag=args.cut, no_save=args.no_save): v
            for v in videos
        }
        for future in as_completed(future_to_video):
            res = future.result()
            results.append(res)

    total_time = time.time() - start_all
    print(f"\n=======================================================")
    print(f"🎉 TẤT CẢ {len(videos)} CLIP ĐÃ XỬ LÝ XONG (Tổng thời gian: {total_time:.1f}s)")
    print(f"=======================================================\n")

    # Sort results to match original video inputs order
    results_ordered = []
    for v in videos:
        match = next((r for r in results if r['video'] == v), None)
        if match:
            results_ordered.append(match)

    print("| STT | Clip | Thời gian xử lý |")
    print("| :--- | :--- | :--- |")
    for idx, r in enumerate(results_ordered, 1):
        status = f"`{r['elapsed']:.1f}s`" if r['success'] else "❌ Lỗi xử lý"
        print(f"| {idx} | **{r['name']}** | {status} |")

    # Print full transcripts
    for idx, r in enumerate(results_ordered, 1):
        if r['success'] and r.get('output'):
            print(f"\n\n--- [FULL_TRANSCRIPT_START: {r['name']}] ---")
            print(r['output'].strip())
            print(f"--- [FULL_TRANSCRIPT_END: {r['name']}] ---\n")

if __name__ == "__main__":
    main()
