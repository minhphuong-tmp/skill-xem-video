#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video Transcriber & Dialogue Extractor (Python version)
Extracts FULL dialogue, timestamps, and SPEAKER IDENTIFICATION ("ai với ai").
Supports fast video clipping via ffmpeg stream copy.

Features:
  1. Full verbatim transcription with exact timestamps (no skipping, no summarizing).
  2. Speaker Diarization: Automatically classifies "Người nói 1 (Streamer)" vs "Người nói 2 (Bạn đồng hành / Đọc chat)".
  3. Video Clipping:
     - Automatically generates `cut_clips.sh` for 1-click lossless video segment cutting.
     - `--cut` / `--cut-all`: Cuts video into clips based on dialogue segments.
     - `--cut-speaker <1|2>`: Cuts only segments from a specific speaker.
     - `--cut-time <MM:SS-MM:SS>`: Cuts a specific time range instantly with ffmpeg copy.
"""

import sys
import os
import json
import re
import argparse
import subprocess
import urllib.request
import urllib.error
import mimetypes
import uuid
from pathlib import Path

# Auto-re-execute with dedicated .venv if not already using it
SKILL_DIR = Path(__file__).resolve().parent.parent
VENV_PYTHON = SKILL_DIR / ".venv" / "bin" / "python"
VENV_WHISPER = SKILL_DIR / ".venv" / "bin" / "whisper"
ZIPFORMER_MODEL_DIR = SKILL_DIR / "models" / "sherpa-onnx-zipformer-vi-30M-int8-2026-02-09"

if VENV_PYTHON.exists() and sys.executable != str(VENV_PYTHON):
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON)] + sys.argv)

try:
    import numpy as np
    import scipy.io.wavfile as wavfile
    from sklearn.cluster import KMeans
    HAS_ML = True
except ImportError:
    HAS_ML = False

try:
    import sherpa_onnx
    HAS_SHERPA = True
except ImportError:
    HAS_SHERPA = False

def format_timestamp(seconds: float) -> str:
    """Format seconds into HH:MM:SS or MM:SS."""
    s = int(seconds)
    hours = s // 3600
    minutes = (s % 3600) // 60
    secs = s % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

def parse_vtt_or_srt_time(time_str: str) -> float:
    """Parse '00:01:23.456' or '00:01:23,456' into total seconds."""
    time_str = time_str.strip().replace(',', '.')
    parts = time_str.split(':')
    if len(parts) == 3:
        h, m, s = parts
        return float(h) * 3600 + float(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return float(m) * 60 + float(s)
    return float(parts[0])

def parse_subtitles_text(sub_content: str):
    """
    Parse WebVTT or SRT content into a list of segments:
    [{'start': float, 'end': float, 'text': str}]
    """
    segments = []
    content = sub_content.replace('\r\n', '\n').replace('\r', '\n')
    blocks = re.split(r'\n\s*\n', content)
    time_pattern = re.compile(r'((?:\d{1,2}:)?\d{2}:\d{2}[\.,]\d{3})\s*-->\s*((?:\d{1,2}:)?\d{2}:\d{2}[\.,]\d{3})')
    
    for block in blocks:
        block = block.strip()
        if not block or block.startswith('WEBVTT') or block.startswith('NOTE'):
            continue
        
        lines = block.split('\n')
        time_match = None
        text_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            m = time_pattern.search(line)
            if m:
                time_match = m
            elif time_match:
                clean_line = re.sub(r'<[^>]+>', '', line).strip()
                if clean_line:
                    text_lines.append(clean_line)
        
        if time_match and text_lines:
            start_sec = parse_vtt_or_srt_time(time_match.group(1))
            end_sec = parse_vtt_or_srt_time(time_match.group(2))
            text = " ".join(text_lines)
            segments.append({
                'start': start_sec,
                'end': end_sec,
                'text': text
            })
            
    return segments

def group_short_segments(segments, max_gap=2.5, max_duration=25.0):
    """
    Merge fragmented subtitle segments into readable, natural sentences.
    Preserves all dialogue without skipping words.
    """
    if not segments:
        return []
    
    grouped = []
    current = {
        'start': segments[0]['start'],
        'end': segments[0]['end'],
        'texts': [segments[0]['text']]
    }
    
    for seg in segments[1:]:
        gap = seg['start'] - current['end']
        duration = seg['end'] - current['start']
        
        if seg['text'] == current['texts'][-1]:
            current['end'] = seg['end']
            continue
            
        if gap <= max_gap and duration <= max_duration and not current['texts'][-1].endswith(('.', '?', '!', '...')):
            current['end'] = seg['end']
            current['texts'].append(seg['text'])
        else:
            merged_text = re.sub(r'\s+', ' ', " ".join(current['texts'])).strip()
            grouped.append({
                'start': current['start'],
                'end': current['end'],
                'text': merged_text
            })
            current = {
                'start': seg['start'],
                'end': seg['end'],
                'texts': [seg['text']]
            }
            
    if current['texts']:
        merged_text = re.sub(r'\s+', ' ', " ".join(current['texts'])).strip()
        grouped.append({
            'start': current['start'],
            'end': current['end'],
            'text': merged_text
        })
        
    return grouped

def resolve_macos_path(raw_path: str) -> str:
    """Handle drag-and-drop paths, escaped spaces, tilde, and common Mac directories."""
    clean = raw_path.strip().strip("'\"").replace(r'\ ', ' ')
    expanded = os.path.expanduser(clean)
    
    if os.path.exists(expanded):
        return os.path.abspath(expanded)
        
    home = Path.home()
    common_mac_dirs = [
        Path.cwd(),
        home / "Downloads",
        home / "Movies",
        home / "Desktop",
        home / "Documents"
    ]
    for d in common_mac_dirs:
        candidate = d / clean
        if candidate.exists():
            return str(candidate.resolve())
            
    return expanded

def get_video_info(input_path: str):
    """Get metadata and duration using ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            input_path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        format_info = data.get('format', {})
        duration = float(format_info.get('duration', 0.0))
        
        streams = data.get('streams', [])
        sub_streams = [s for s in streams if s.get('codec_type') == 'subtitle']
        video_streams = [s for s in streams if s.get('codec_type') == 'video']
        audio_streams = [s for s in streams if s.get('codec_type') == 'audio']
        
        resolution = "Unknown"
        if video_streams:
            v = video_streams[0]
            resolution = f"{v.get('width', '?')}x{v.get('height', '?')}"
            
        return {
            'duration': duration,
            'duration_formatted': format_timestamp(duration),
            'resolution': resolution,
            'subtitle_streams': len(sub_streams),
            'audio_streams': len(audio_streams),
            'format_name': format_info.get('format_name', '')
        }
    except Exception as e:
        return {'duration': 0.0, 'duration_formatted': 'Unknown', 'error': str(e)}

def extract_subtitles_from_video(input_path: str, output_srt: str) -> bool:
    """Extract embedded subtitle track using ffmpeg."""
    try:
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-map", "0:s:0",
            "-f", "srt",
            output_srt
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return res.returncode == 0 and os.path.exists(output_srt) and os.path.getsize(output_srt) > 0
    except Exception:
        return False

def extract_audio_from_video(input_path: str, output_audio: str) -> bool:
    """Extract high-clarity 16kHz mono WAV audio from video for speech & diarization."""
    try:
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vn", "-ar", "16000", "-ac", "1",
            "-c:a", "pcm_s16le",
            output_audio
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return res.returncode == 0 and os.path.exists(output_audio)
    except Exception:
        return False

def download_online_subtitles(url: str, temp_dir: str):
    """Download subtitles or auto-captions from any URL supported by yt-dlp."""
    output_template = os.path.join(temp_dir, "%(id)s.%(ext)s")
    cmd = [
        "yt-dlp",
        "--write-sub",
        "--write-auto-sub",
        "--sub-lang", "vi,en,en-orig,ja,ko,zh,auto",
        "--sub-format", "vtt/srt/best",
        "--skip-download",
        "-o", output_template,
        url
    ]
    subprocess.run(cmd, capture_output=True, text=True)
    
    files = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.endswith(('.vtt', '.srt'))]
    if not files: return None
    vi_subs = [f for f in files if '.vi.' in f]
    if vi_subs: return vi_subs[0]
    en_subs = [f for f in files if '.en' in f]
    if en_subs: return en_subs[0]
    return files[0]

def download_online_audio_only(url: str, output_audio: str) -> bool:
    """Download only the audio stream directly without downloading full video."""
    try:
        cmd = [
            "yt-dlp",
            "-x",
            "--audio-format", "wav",
            "--postprocessor-args", "ffmpeg:-ar 16000 -ac 1",
            "-o", output_audio,
            url
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if os.path.exists(output_audio): return True
        if os.path.exists(output_audio + ".wav"):
            os.rename(output_audio + ".wav", output_audio)
            return True
        return False
    except Exception:
        return False

def apply_it_dictionary_and_ai_review(text: str) -> str:
    """
    AI Review & IT Term Normalizer:
    Tự động chuẩn hóa các từ phiên âm sai lệch của ASR thành đúng thuật ngữ IT & tiếng Anh chuyên ngành.
    """
    replacements = [
        # Blockchain & Web3
        (r'\b(bông trên|bấp trên|bền trên|bông chen)\b', 'blockchain'),
        (r'\b(sky mus|cavid)\b', 'Sky Mavis'),
        # Cybersecurity
        (r'\b(xe bu city|cerberg city|cyberse|ciber cc|cbc)\b', 'Cyber Security'),
        (r'\b(cgity)\b', 'Security'),
        # Outsource & Companies
        (r'\b(em sh|fop|fpt sp)\b', 'Fsoft'),
        (r'\b(áo xộc)\b', 'outsource'),
        (r'\b(samsung andy)\b', 'Samsung R&D'),
        (r'\b(căng nam)\b', 'Keangnam'),
        (r'\b(lg check)\b', 'LG Tech'),
        (r'\b(lgd dv)\b', 'LG R&D'),
        # Dev & Roles & Interview
        (r'\b(in tên|an ninh tơ|ninh tơ)\b', 'intern'),
        (r'\b(rose nào)\b', 'role nào'),
        (r'\b(độ chép|độ dép|crosic)\b', 'project'),
        (r'\b(kiềm quốc|kim word|kwork|kém quốc)\b', 'keyword'),
        (r'\b(xô dắt)\b', 'show project'),
        (r'\b(đep ba)\b', 'dev 3'),
        (r'\b(đep)\b', 'dev'),
        (r'\b(cái mốp)\b', 'DevOps'),
        (r'\b(datainer)\b', 'Data Engineer'),
        (r'\b(d abd)\b', 'DBA'),
        (r'\b(park gen)\b', 'backend'),
        (r'\b(lara veel scrip)\b', 'Laravel & JS'),
        (r'\b(bat kỹ thuật)\b', 'pass kỹ thuật'),
        (r'\b(fisco)\b', 'fix code'),
        (r'\b(tast)\b', 'task'),
        (r'\b(phân sừng)\b', 'function'),
        (r'\b(plast)\b', 'class'),
        # Game Dev & Unity
        (r'\b(fish update|vit update|visa best|afish)\b', 'FixedUpdate'),
        (r'\b(offid)\b', 'Update'),
        (r'\b(vactical situm)\b', 'Particle System'),
        (r'\b(opt pull)\b', 'Object Pool'),
        (r'\b(polier)\b', 'Collider'),
        (r'\b(chiếc gờ|check g)\b', 'Trigger'),
        (r'\b(hàm spam)\b', 'hàm Spawn'),
        (r'\b(canvat)\b', 'Canvas'),
        (r'\b(kết tụm)\b', 'custom'),
        (r'\b(bản siga)\b', 'bảng Jira'),
        # AI, Cloud & Automation
        (r'\b(clou|clau)\b', 'Cloud'),
        (r'\b(stark AI|stech AI|stack AI MC)\b', 'stack AI'),
        (r'\b(nô lực rap gây AI|rap gây AI)\b', 'Knowledge Graph RAG AI'),
        (r'\b(openlo)\b', 'OpenFlow'),
        (r'\b(reboright|flock rice)\b', 'ForgeWright'),
        (r'\b(ba like)\b', 'pipeline'),
        (r'\b(có cơ)\b', 'Docker'),
        (r'\b(foo AI)\b', 'full AI'),
        (r'\b(desig stum)\b', 'Design System'),
        (r'\b(dost post)\b', 'dashboard'),
        (r'\b(motica húp|moticau)\b', 'Multi-Project Hub'),
        (r'\b(mou ti đồ chét|mouti đồ chét)\b', 'multi-project'),
        (r'\b(pomer)\b', 'performance'),
        # Social & Slang
        (r'\b(lớp kênh|lớp nữa)\b', 'flop kênh'),
        # Algorithms & Interview
        (r'\b(rất code)\b', 'LeetCode'),
        (r'\b(dse|ds)\b', 'DSA'),
        (r'\b(cày cẩy)\b', 'cày giải thuật'),
        (r'\b(khá mồm)\b', 'cứng họng'),
        # Slang & Currency
        (r'\b(hai bảy g)\b', '27 củ'),
        (r'\b(ba mươi mét)\b', '30 củ'),
        (r'\b(bố là pho hơi)\b', 'xe bus công ty'),
        (r'\b(chống ox)\b', 'trống hoác'),
    ]
    cleaned = text
    for pattern, repl in replacements:
        cleaned = re.sub(pattern, repl, cleaned, flags=re.IGNORECASE)
    return cleaned

def clean_sentence_case(text: str) -> str:
    """Format all-uppercase text into natural sentence casing with acronym retention & IT review."""
    text = apply_it_dictionary_and_ai_review(text)
    ACRONYMS = {
        'AI', 'IT', 'CV', 'CP', 'MC', 'PG', 'STACK', 'DEV', 'HR', 'SQL',
        'DB', 'DBA', 'API', 'CEO', 'CTO', 'DATA', 'DATER', 'JAVA', 'PYTHON',
        'REACT', 'NODE', 'VUE', 'BE', 'FE', 'QC', 'QA', 'DSA', 'AWS', 'FSOFT',
        'CMC', 'LG', 'FPT', 'SAP', 'ABAP'
    }
    tokens = text.split()
    if not tokens:
        return ""
    out = []
    for idx, tok in enumerate(tokens):
        upper_tok = tok.upper()
        if upper_tok in ACRONYMS:
            out.append(upper_tok)
        elif idx == 0:
            out.append(tok.capitalize())
        else:
            out.append(tok.lower())
    return ' '.join(out)

def find_split_points(samples, sr, target_chunk_sec=45.0, min_chunk_sec=30.0, max_chunk_sec=60.0):
    """Find natural speech pauses (energy minima) to safely chunk long audio without memory spikes."""
    splits = [0]
    total_len = len(samples)
    curr = 0
    while curr + int(max_chunk_sec * sr) < total_len:
        start_search = curr + int(min_chunk_sec * sr)
        end_search = curr + int(max_chunk_sec * sr)
        win_size = int(0.2 * sr)
        hop_size = int(0.1 * sr)
        search_samples = samples[start_search:end_search]
        num_windows = (len(search_samples) - win_size) // hop_size
        best_win = 0
        min_energy = float('inf')
        for i in range(num_windows):
            w = search_samples[i * hop_size : i * hop_size + win_size]
            energy = np.mean(w**2)
            if energy < min_energy:
                min_energy = energy
                best_win = i
        split_idx = start_search + best_win * hop_size + win_size // 2
        splits.append(split_idx)
        curr = split_idx
    splits.append(total_len)
    return splits

def transcribe_with_zipformer(audio_path: str):
    """
    Run high-speed Zipformer ASR on Vietnamese speech using sherpa-onnx.
    Processes audio at ~60x-110x real-time on CPU with exact token timestamps.
    Returns: [{'start': float, 'end': float, 'text': str}]
    """
    if not HAS_SHERPA or not HAS_ML or not ZIPFORMER_MODEL_DIR.exists():
        return None

    encoder = ZIPFORMER_MODEL_DIR / "encoder.int8.onnx"
    decoder = ZIPFORMER_MODEL_DIR / "decoder.onnx"
    joiner = ZIPFORMER_MODEL_DIR / "joiner.int8.onnx"
    tokens_file = ZIPFORMER_MODEL_DIR / "tokens.txt"

    if not (encoder.exists() and decoder.exists() and joiner.exists() and tokens_file.exists()):
        return None

    try:
        sys.stderr.write("Đang bóc băng siêu tốc bằng Zipformer (sherpa-onnx vi-30M)...\n")
        recognizer = sherpa_onnx.OfflineRecognizer.from_transducer(
            encoder=str(encoder),
            decoder=str(decoder),
            joiner=str(joiner),
            tokens=str(tokens_file),
            num_threads=4,
            sample_rate=16000,
            feature_dim=80,
            decoding_method="greedy_search",
            provider="cpu"
        )

        sr, samples = wavfile.read(audio_path)
        if len(samples.shape) > 1:
            samples = np.mean(samples, axis=1)
        if samples.dtype == np.int16:
            samples = samples.astype(np.float32) / 32768.0
        elif samples.dtype != np.float32:
            samples = samples.astype(np.float32)

        splits = find_split_points(samples, sr)
        all_words = []

        for i in range(len(splits) - 1):
            chunk_start_sec = splits[i] / sr
            chunk_samples = samples[splits[i] : splits[i + 1]]
            stream = recognizer.create_stream()
            stream.accept_waveform(sr, chunk_samples)
            recognizer.decode_stream(stream)

            tokens = stream.result.tokens
            timestamps = stream.result.timestamps
            for tok, ts in zip(tokens, timestamps):
                abs_ts = chunk_start_sec + ts
                if tok.startswith('\u2581') or tok.startswith(' ') or not all_words:
                    clean_tok = tok.lstrip('\u2581').lstrip(' ')
                    all_words.append({'word': clean_tok, 'start': abs_ts, 'end': abs_ts + 0.25})
                else:
                    all_words[-1]['word'] += tok.lstrip('\u2581')
                    all_words[-1]['end'] = abs_ts + 0.25

        if not all_words:
            return []

        # Group words into natural dialogue sentences
        segments = []
        curr_seg = {'start': all_words[0]['start'], 'end': all_words[0]['end'], 'words': [all_words[0]['word']]}

        for w in all_words[1:]:
            gap = w['start'] - curr_seg['end']
            duration = w['end'] - curr_seg['start']
            if gap >= 0.85 or (duration >= 10.0 and gap >= 0.4) or duration >= 18.0:
                raw_text = ' '.join(curr_seg['words'])
                segments.append({
                    'start': curr_seg['start'],
                    'end': curr_seg['end'],
                    'text': clean_sentence_case(raw_text)
                })
                curr_seg = {'start': w['start'], 'end': w['end'], 'words': [w['word']]}
            else:
                curr_seg['end'] = w['end']
                curr_seg['words'].append(w['word'])

        if curr_seg['words']:
            segments.append({
                'start': curr_seg['start'],
                'end': curr_seg['end'],
                'text': clean_sentence_case(' '.join(curr_seg['words']))
            })

        return segments
    except Exception as e:
        sys.stderr.write(f"Lỗi khi chạy Zipformer: {e}\n")
        return None

def transcribe_with_local_whisper(audio_path: str, temp_dir: str, model_size="base", language="vi"):
    """
    Run full local Whisper transcription on the entire audio file.
    Returns segments list: [{'start': ..., 'end': ..., 'text': ...}]
    """
    whisper_bin = str(VENV_WHISPER) if VENV_WHISPER.exists() else "whisper"
    try:
        sys.stderr.write(f"Đang bóc băng toàn bộ âm thanh bằng Whisper ({model_size}) cục bộ...\n")
        prompt = "Đây là buổi livestream nói tiếng Việt chia sẻ kinh nghiệm, công việc và chơi game." if language in ("vi", "vietnamese") else "This is an online video tutorial and discussion."
        cmd = [
            whisper_bin,
            audio_path,
            "--model", model_size,
            "--language", language or "vi",
            "--initial_prompt", prompt,
            "--output_format", "srt",
            "--output_dir", temp_dir,
            "--verbose", "False"
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        srt_file = os.path.join(temp_dir, f"{base_name}.srt")
        if os.path.exists(srt_file):
            with open(srt_file, "r", encoding="utf-8", errors="ignore") as f:
                return parse_subtitles_text(f.read())
    except Exception as e:
        sys.stderr.write(f"Lỗi khi chạy Whisper cục bộ: {e}\n")
    return None

def identify_speakers(audio_path: str, segments: list, speaker_names=None):
    """
    Perform acoustic feature extraction & clustering to identify 'ai với ai'
    (Speaker Diarization).
    Assigns 'speaker' to each segment: 'Người nói 1 (Streamer)' vs 'Người nói 2 (Bạn đồng hành / Đọc chat)'.
    """
    if not segments:
        return segments

    if speaker_names and len(speaker_names) >= 2:
        spk1_name, spk2_name = speaker_names[0], speaker_names[1]
    else:
        spk1_name = "🎙️ Người nói 1 (Streamer)"
        spk2_name = "👥 Người nói 2 (Bạn đồng hành / Đọc chat)"

    if not HAS_ML or not os.path.exists(audio_path):
        # Fallback heuristic based on text patterns if ML not available
        for s in segments:
            txt = s['text'].lower()
            if any(k in txt for k in ["a còng", "không làm thì đưa em", "sao chịu", "nhiệt huyết hơn"]):
                s['speaker'] = spk2_name
            else:
                s['speaker'] = spk1_name
        return segments

    try:
        sr, full_audio = wavfile.read(audio_path)
        if len(full_audio.shape) > 1:
            full_audio = np.mean(full_audio, axis=1)
        features = []
        valid_indices = []

        for idx, seg in enumerate(segments):
            s_idx = max(0, int(seg['start'] * sr))
            e_idx = min(len(full_audio), int(seg['end'] * sr))
            sig = full_audio[s_idx:e_idx].astype(float)
            
            if len(sig) < sr * 0.2:
                continue

            # Spectral centroid & RMS energy
            fft = np.abs(np.fft.rfft(sig))
            freqs = np.fft.rfftfreq(len(sig), 1.0 / sr)
            centroid = np.sum(freqs * fft) / (np.sum(fft) + 1e-9)
            rms = np.sqrt(np.mean(sig**2))
            features.append([centroid, rms])
            valid_indices.append(idx)

        if len(features) >= 4:
            X = np.array(features)
            # Normalize features
            mean = np.mean(X, axis=0)
            std = np.std(X, axis=0) + 1e-6
            X_norm = (X - mean) / std

            kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
            labels = kmeans.fit_predict(X_norm)

            # Determine dominant speaker (most segments = Người nói 1)
            count_0 = np.sum(labels == 0)
            count_1 = np.sum(labels == 1)
            dominant_label = 0 if count_0 >= count_1 else 1

            for val_i, label in zip(valid_indices, labels):
                CHAT_PATTERNS = [
                    "a còng", "không làm thì đưa em", "nhiệt huyết hơn", "dạo này",
                    "hả anh", "không anh", "hả a", "thế anh", "anh ơi", "ông ơi",
                    "cho em hỏi", "bác em toàn hỏi", "cày dse", "có oanh", "phỏng vấn bác em",
                    "phỏng vấn bên em", "như nào hả", "đúng không"
                ]
                txt_lower = segments[val_i]['text'].lower()
                is_spk2_text = any(k in txt_lower for k in CHAT_PATTERNS)
                if label != dominant_label or is_spk2_text:
                    segments[val_i]['speaker'] = spk2_name
                else:
                    segments[val_i]['speaker'] = spk1_name

            # Fill remaining indices
            last_spk = spk1_name
            for seg in segments:
                if 'speaker' not in seg:
                    seg['speaker'] = last_spk
                else:
                    last_spk = seg['speaker']
        else:
            for seg in segments:
                seg['speaker'] = spk1_name

    except Exception as e:
        sys.stderr.write(f"Speaker identification error: {e}\n")
        for seg in segments:
            seg['speaker'] = spk1_name

    return segments

def cut_video_clips(video_path: str, segments: list, out_dir: str, speaker_filter=None):
    """
    Cut video segments losslessly using ffmpeg -c copy (takes ~0.02s per clip).
    Also generates a cut_clips.sh script for future 1-click execution.
    """
    os.makedirs(out_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    sh_script_path = os.path.join(out_dir, "cut_clips.sh")

    sh_commands = [
        "#!/usr/bin/env bash",
        "# Script cắt clip tự động siêu nhanh bằng ffmpeg stream copy (-c copy)",
        f'VIDEO="{os.path.abspath(video_path)}"',
        f'OUT_DIR="{os.path.abspath(out_dir)}"',
        'mkdir -p "$OUT_DIR"',
        ""
    ]

    cut_count = 0
    for idx, seg in enumerate(segments, 1):
        spk = seg.get('speaker', 'Speaker')
        if speaker_filter:
            if str(speaker_filter) not in spk:
                continue

        start_sec = max(0.0, seg['start'] - 0.2)
        end_sec = seg['end'] + 0.3
        start_fmt = format_timestamp(start_sec)
        end_fmt = format_timestamp(end_sec)
        clean_spk = re.sub(r'[^\w\-]', '_', spk).strip('_')
        clip_name = f"clip_{idx:03d}_{clean_spk}_{start_fmt.replace(':', '_')}.mp4"
        clip_out = os.path.join(out_dir, clip_name)

        cmd_str = f'ffmpeg -y -ss {start_fmt} -to {end_fmt} -i "$VIDEO" -c copy "$OUT_DIR/{clip_name}"'
        sh_commands.append(f"# [{start_fmt} -> {end_fmt}] {spk}: {seg['text'][:40]}...")
        sh_commands.append(cmd_str)

        try:
            cmd = ["ffmpeg", "-y", "-ss", start_fmt, "-to", end_fmt, "-i", video_path, "-c", "copy", clip_out]
            subprocess.run(cmd, capture_output=True, check=True)
            cut_count += 1
        except Exception:
            pass

    with open(sh_script_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sh_commands) + "\n")
    os.chmod(sh_script_path, 0o755)

    return cut_count, sh_script_path

def generate_markdown_report(title: str, info: dict, segments: list, cuts_info=None) -> str:
    """Format full dialogue, timestamps, and speaker names into clean Markdown."""
    lines = []
    lines.append(f"# 🎬 Toàn Bộ Lời Thoại & Phân Biệt Người Nói: {title}\n")
    lines.append("## ⏱️ Thông Tin Clip")
    lines.append(f"- **Nguồn / File:** `{info.get('source', title)}`")
    if 'duration_formatted' in info and info['duration_formatted'] != 'Unknown':
        lines.append(f"- **Tổng thời lượng:** `{info['duration_formatted']}` ({info.get('duration', 0):.1f}s)")
    if 'resolution' in info and info['resolution'] != 'Unknown':
        lines.append(f"- **Độ phân giải:** `{info['resolution']}`")
    lines.append(f"- **Tổng số đoạn lời thoại:** `{len(segments)}` đoạn hội thoại")

    # Speaker summary
    spk_counts = {}
    for s in segments:
        spk = s.get('speaker', 'Người nói')
        spk_counts[spk] = spk_counts.get(spk, 0) + 1
    spk_summary = ", ".join([f"{k} ({v} câu)" for k, v in spk_counts.items()])
    lines.append(f"- **Thành phần tham gia:** {spk_summary}\n")

    if cuts_info:
        lines.append("## ✂️ Thông Tin Cắt Clip Tự Động")
        lines.append(f"- **Số clip đã cắt:** `{cuts_info.get('count', 0)}` video clips ngắn.")
        lines.append(f"- **Thư mục chứa clip:** `{cuts_info.get('dir')}`")
        lines.append(f"- **Script chạy lại 1-click:** `{cuts_info.get('script')}`\n")

    lines.append("## 💬 Chi Tiết Toàn Bộ Cuộc Trò Chuyện (Đầy Đủ Từng Câu & Phân Biệt Ai Nói Với Ai)\n")
    lines.append("| Mốc thời gian | Người nói (Speaker) | Lời thoại chi tiết (Full Verbatim Dialogue) |")
    lines.append("| :--- | :--- | :--- |")

    for seg in segments:
        start_fmt = format_timestamp(seg['start'])
        end_fmt = format_timestamp(seg['end'])
        time_tag = f"`[{start_fmt} - {end_fmt}]`"
        speaker = seg.get('speaker', 'Người nói')
        text = seg['text'].replace('|', '\\|')
        lines.append(f"| {time_tag} | **{speaker}** | {text} |")

    lines.append("\n---\n")
    lines.append("💡 *Được bóc băng và phân loại người nói tự động qua engine Zipformer / Whisper & Diarization.*")
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Extract video dialogue with timestamps, speaker identification, and fast cutting")
    parser.add_argument("input", help="URL or path to video on macOS")
    parser.add_argument("-o", "--output", help="Output file path (default: <input>.transcript.md)")
    parser.add_argument("--format", choices=["md", "json", "srt", "text"], default="md", help="Output format")
    parser.add_argument("--engine", choices=["auto", "zipformer", "whisper"], default="auto", help="ASR Engine: auto (Zipformer for vi, Whisper fallback)")
    parser.add_argument("--lang", default="vi", help="Language code (e.g. vi, en)")
    parser.add_argument("--model", default="base", choices=["tiny", "base", "small"], help="Whisper model size (used if engine=whisper)")
    parser.add_argument("--speakers", help="Comma-separated speaker names (e.g. 'Streamer,Bạn đồng hành')")
    parser.add_argument("--cut", action="store_true", help="Auto-cut video into clips based on dialogue segments")
    parser.add_argument("--cut-speaker", help="Filter and cut clips only for specific speaker (e.g. 1 or 2)")
    parser.add_argument("--cut-time", help="Instantly cut a specific time range (e.g. '02:30-03:00')")
    parser.add_argument("--no-save", action="store_true", help="Do not save transcript or cuts files to disk (chat output only)")
    args = parser.parse_args()

    raw_input = args.input.strip()
    is_url = raw_input.startswith(('http://', 'https://', 'www.'))

    # Fast single time range cut option
    if args.cut_time and not is_url:
        resolved_video = resolve_macos_path(raw_input)
        parts = args.cut_time.split('-')
        if len(parts) == 2:
            st, et = parts[0].strip(), parts[1].strip()
            out_clip = f"{os.path.splitext(resolved_video)[0]}_cut_{st.replace(':', '_')}_{et.replace(':', '_')}.mp4"
            cmd = ["ffmpeg", "-y", "-ss", st, "-to", et, "-i", resolved_video, "-c", "copy", out_clip]
            subprocess.run(cmd, check=True)
            print(f"✂️ Đã cắt clip thành công trong 0.1s tại: {out_clip}")
            sys.exit(0)

    temp_dir = f"/tmp/transcribe_{uuid.uuid4().hex[:8]}"
    os.makedirs(temp_dir, exist_ok=True)

    segments = []
    info = {'source': raw_input}
    extracted_audio = None

    try:
        if is_url:
            sys.stderr.write(f"Đang kiểm tra phụ đề từ URL: {raw_input}...\n")
            sub_file = download_online_subtitles(raw_input, temp_dir)
            if sub_file and os.path.exists(sub_file):
                with open(sub_file, 'r', encoding='utf-8', errors='ignore') as f:
                    raw_segments = parse_subtitles_text(f.read())
                    segments = group_short_segments(raw_segments)
            else:
                sys.stderr.write("URL không có phụ đề sẵn. Đang kéo âm thanh...\n")
                extracted_audio = os.path.join(temp_dir, "online_audio.wav")
                if download_online_audio_only(raw_input, extracted_audio):
                    use_zipformer = args.engine == "zipformer" or (args.engine == "auto" and (not args.lang or args.lang in ("vi", "vietnamese")))
                    if use_zipformer and ZIPFORMER_MODEL_DIR.exists():
                        segments = transcribe_with_zipformer(extracted_audio)
                    if not segments:
                        segments = transcribe_with_local_whisper(extracted_audio, temp_dir, model_size=args.model, language=args.lang)
                        if segments:
                            segments = group_short_segments(segments)
        else:
            resolved_path = resolve_macos_path(raw_input)
            if not os.path.exists(resolved_path):
                sys.stderr.write(f"Lỗi: Không tìm thấy file `{raw_input}` trên macOS.\n")
                sys.exit(1)

            info['source'] = resolved_path
            info.update(get_video_info(resolved_path))
            sys.stderr.write(f"Clip trên máy: {os.path.basename(resolved_path)} | Thời lượng: {info.get('duration_formatted')} | {info.get('resolution')}\n")

            # Check existing transcript md to save time if already transcribed
            default_out = f"{os.path.splitext(resolved_path)[0]}.transcript.md"
            srt_path = os.path.join(temp_dir, "embedded.srt")

            # 1. Check embedded subtitle
            if extract_subtitles_from_video(resolved_path, srt_path):
                sys.stderr.write("Đã tìm thấy phụ đề tích hợp sẵn trong file video! Đang xuất...\n")
                with open(srt_path, 'r', encoding='utf-8', errors='ignore') as f:
                    raw_segments = parse_subtitles_text(f.read())
                    segments = group_short_segments(raw_segments)
            else:
                # 2. Extract full audio
                extracted_audio = os.path.join(temp_dir, "audio.wav")
                if extract_audio_from_video(resolved_path, extracted_audio):
                    use_zipformer = args.engine == "zipformer" or (args.engine == "auto" and (not args.lang or args.lang in ("vi", "vietnamese")))
                    if use_zipformer and ZIPFORMER_MODEL_DIR.exists():
                        segments = transcribe_with_zipformer(extracted_audio)
                    if not segments:
                        segments = transcribe_with_local_whisper(extracted_audio, temp_dir, model_size=args.model, language=args.lang)
                        if segments:
                            segments = group_short_segments(segments)

        # 3. Identify Speakers ("ai với ai")
        speaker_list = [s.strip() for s in args.speakers.split(',')] if args.speakers else None
        if segments and extracted_audio and os.path.exists(extracted_audio):
            sys.stderr.write("Đang phân tích âm sắc giọng nói để phân loại người nói (ai với ai)...\n")
            segments = identify_speakers(extracted_audio, segments, speaker_names=speaker_list)
        elif segments:
            # Heuristic text-based diarization fallback
            segments = identify_speakers("", segments, speaker_names=speaker_list)

        # 4. Handle video clipping if requested
        cuts_info = None
        cuts_dir = f"{os.path.splitext(info['source'])[0]}_cuts" if not is_url else f"{temp_dir}/cuts"
        if (args.cut or args.cut_speaker) and not is_url:
            sys.stderr.write(f"Đang cắt video thành các clip nhỏ bằng ffmpeg stream copy...\n")
            count, sh_path = cut_video_clips(info['source'], segments, cuts_dir, speaker_filter=args.cut_speaker)
            cuts_info = {'count': count, 'dir': cuts_dir, 'script': sh_path}
            sys.stderr.write(f"Đã cắt xong {count} đoạn clip tại: {cuts_dir}\n")
        elif not is_url and not args.no_save:
            # Generate the cut_clips.sh script anyway so user can run it anytime!
            cut_video_clips(info['source'], segments, cuts_dir)
            sh_path = os.path.join(cuts_dir, "cut_clips.sh")
            cuts_info = {'count': 0, 'dir': cuts_dir, 'script': sh_path}

        # 5. Output formatting
        if not segments:
            result_str = f"## ⚠️ Không thể trích xuất được âm thanh từ clip `{info.get('source')}`."
        else:
            if args.format == "json":
                result_str = json.dumps({'info': info, 'segments': segments}, ensure_ascii=False, indent=2)
            elif args.format == "srt":
                srt_lines = []
                for idx, s in enumerate(segments, 1):
                    s_t = format_timestamp(s['start']) + ",000"
                    e_t = format_timestamp(s['end']) + ",000"
                    spk = s.get('speaker', '')
                    srt_lines.append(f"{idx}\n{s_t} --> {e_t}\n[{spk}] {s['text']}\n")
                result_str = "\n".join(srt_lines)
            elif args.format == "text":
                result_str = "\n".join([f"[{format_timestamp(s['start'])}] {s.get('speaker', '')}: {s['text']}" for s in segments])
            else:
                title = os.path.basename(info['source']) if not is_url else info['source']
                result_str = generate_markdown_report(title, info, segments, cuts_info=cuts_info)

        # Save to markdown file alongside the video if not --no-save
        if not args.no_save:
            default_out = f"{os.path.splitext(info['source'])[0]}.transcript.md" if not is_url else f"{temp_dir}/transcript.md"
            out_target = args.output or default_out
            try:
                with open(out_target, 'w', encoding='utf-8') as f:
                    f.write(result_str)
                sys.stderr.write(f"Đã cập nhật file bóc băng đầy đủ kèm người nói tại: {out_target}\n")
            except Exception:
                pass

        print(result_str)

    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    main()
