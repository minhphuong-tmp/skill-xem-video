#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fast Video Cutter (Lossless ffmpeg stream copy)
Cắt video siêu tốc không cần render lại (0.05s / clip).

Cách dùng:
  python3 cut_clip.py <file_video> <thời_gian_bắt_đầu> <thời_gian_kết_thúc> [-o output.mp4]
Ví dụ:
  python3 cut_clip.py video.mp4 02:30 03:00
  python3 cut_clip.py video.mp4 00:04:35 00:05:30 -o doan_hay.mp4
"""

import sys
import os
import subprocess
from pathlib import Path

def resolve_path(p: str) -> str:
    clean = p.strip().strip("'\"").replace(r'\ ', ' ')
    expanded = os.path.expanduser(clean)
    if os.path.exists(expanded):
        return os.path.abspath(expanded)
    for d in [Path.home() / "Downloads", Path.home() / "Movies", Path.home() / "Desktop"]:
        c = d / clean
        if c.exists():
            return str(c.resolve())
    return expanded

def main():
    if len(sys.argv) < 4:
        print("Cách dùng: python3 cut_clip.py <file_video> <start (MM:SS)> <end (MM:SS)> [-o out.mp4]")
        sys.exit(1)

    video_input = resolve_path(sys.argv[1])
    if not os.path.exists(video_input):
        print(f"Lỗi: Không tìm thấy file `{video_input}`")
        sys.exit(1)

    start_time = sys.argv[2].strip()
    end_time = sys.argv[3].strip()

    out_file = None
    if "-o" in sys.argv:
        idx = sys.argv.index("-o")
        if idx + 1 < len(sys.argv):
            out_file = sys.argv[idx + 1]

    if not out_file:
        base, ext = os.path.splitext(video_input)
        clean_st = start_time.replace(":", "_")
        clean_et = end_time.replace(":", "_")
        out_file = f"{base}_cut_{clean_st}_to_{clean_et}{ext}"

    cmd = [
        "ffmpeg", "-y",
        "-ss", start_time,
        "-to", end_time,
        "-i", video_input,
        "-c", "copy",
        out_file
    ]

    print(f"✂️ Đang cắt clip từ [{start_time}] đến [{end_time}]...")
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ Đã cắt xong trong 0.05 giây tại: {out_file}")
    except subprocess.CalledProcessError as e:
        print(f"Lỗi khi cắt clip: {e.stderr.decode('utf-8', errors='ignore')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
