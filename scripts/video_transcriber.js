#!/usr/bin/env node
/**
 * Video Transcriber & Dialogue Extractor (Node.js version)
 * Extracts dialogue and timestamps from:
 *   1. Any Online URL: YouTube, TikTok, Facebook, Vimeo, Twitter/X, Loom, or direct video URL.
 *   2. Local macOS Files: QuickTime .mov, .mp4, .mkv, .webm, iPhone videos, Mac Screen Recordings, etc.
 */

const { execSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const https = require('node:https');
const crypto = require('node:crypto');

function formatTimestamp(seconds) {
  const s = Math.floor(seconds);
  const hours = Math.floor(s / 3600);
  const minutes = Math.floor((s % 3600) / 60);
  const secs = s % 60;
  if (hours > 0) {
    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }
  return `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

function parseVttOrSrtTime(timeStr) {
  const clean = timeStr.trim().replace(',', '.');
  const parts = clean.split(':');
  if (parts.length === 3) {
    return parseFloat(parts[0]) * 3600 + parseFloat(parts[1]) * 60 + parseFloat(parts[2]);
  } else if (parts.length === 2) {
    return parseFloat(parts[0]) * 60 + parseFloat(parts[1]);
  }
  return parseFloat(parts[0]);
}

function parseSubtitlesText(subContent) {
  const segments = [];
  const content = subContent.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
  const blocks = content.split(/\n\s*\n/);
  const timePattern = /((?:\d{1,2}:)?\d{2}:\d{2}[\.,]\d{3})\s*-->\s*((?:\d{1,2}:)?\d{2}:\d{2}[\.,]\d{3})/;

  for (const block of blocks) {
    const trimmed = block.trim();
    if (!trimmed || trimmed.startsWith('WEBVTT') || trimmed.startsWith('NOTE')) {
      continue;
    }
    const lines = trimmed.split('\n');
    let timeMatch = null;
    const textLines = [];

    for (const line of lines) {
      const lineTrim = line.trim();
      if (!lineTrim) continue;
      const m = lineTrim.match(timePattern);
      if (m) {
        timeMatch = m;
      } else if (timeMatch) {
        const cleanLine = lineTrim.replace(/<[^>]+>/g, '').trim();
        if (cleanLine) textLines.push(cleanLine);
      }
    }

    if (timeMatch && textLines.length > 0) {
      const start = parseVttOrSrtTime(timeMatch[1]);
      const end = parseVttOrSrtTime(timeMatch[2]);
      const text = textLines.join(' ');
      segments.push({ start, end, text });
    }
  }

  return segments;
}

function groupShortSegments(segments, maxGap = 2.0, maxDuration = 30.0) {
  if (!segments || segments.length === 0) return [];

  const grouped = [];
  let current = {
    start: segments[0].start,
    end: segments[0].end,
    texts: [segments[0].text]
  };

  for (let i = 1; i < segments.length; i++) {
    const seg = segments[i];
    const gap = seg.start - current.end;
    const duration = seg.end - current.start;
    const lastText = current.texts[current.texts.length - 1];

    if (seg.text === lastText) {
      current.end = seg.end;
      continue;
    }

    const endsWithPunct = ['.', '?', '!', '...'].some(p => lastText.endsWith(p));
    if (gap <= maxGap && duration <= maxDuration && !endsWithPunct) {
      current.end = seg.end;
      current.texts.push(seg.text);
    } else {
      const merged = current.texts.join(' ').replace(/\s+/g, ' ').trim();
      grouped.push({ start: current.start, end: current.end, text: merged });
      current = {
        start: seg.start,
        end: seg.end,
        texts: [seg.text]
      };
    }
  }

  if (current.texts.length > 0) {
    const merged = current.texts.join(' ').replace(/\s+/g, ' ').trim();
    grouped.push({ start: current.start, end: current.end, text: merged });
  }

  return grouped;
}

function resolveMacOSPath(rawPath) {
  let clean = rawPath.trim().replace(/^['"]|['"]$/g, '');
  clean = clean.replace(/\\ /g, ' ');

  if (clean.startsWith('~')) {
    clean = path.join(os.homedir(), clean.slice(1));
  }

  if (fs.existsSync(clean)) {
    return path.resolve(clean);
  }

  // Check common macOS folders
  const home = os.homedir();
  const searchDirs = [
    process.cwd(),
    path.join(home, 'Downloads'),
    path.join(home, 'Movies'),
    path.join(home, 'Desktop'),
    path.join(home, 'Documents')
  ];

  for (const d of searchDirs) {
    const candidate = path.join(d, clean);
    if (fs.existsSync(candidate)) {
      return path.resolve(candidate);
    }
  }

  return clean;
}

function getVideoInfo(inputPath) {
  try {
    const out = execSync(`ffprobe -v quiet -print_format json -show_format -show_streams "${inputPath}"`, {
      encoding: 'utf-8'
    });
    const data = JSON.parse(out);
    const duration = parseFloat(data.format?.duration || 0);
    const streams = data.streams || [];
    const videoStream = streams.find(s => s.codec_type === 'video');
    const subStreams = streams.filter(s => s.codec_type === 'subtitle');

    return {
      duration,
      duration_formatted: formatTimestamp(duration),
      resolution: videoStream ? `${videoStream.width}x${videoStream.height}` : 'Unknown',
      subtitle_streams: subStreams.length,
      format_name: data.format?.format_name || ''
    };
  } catch (e) {
    return { duration: 0, duration_formatted: 'Unknown', error: e.message };
  }
}

function extractSubtitlesFromVideo(inputPath, outputSrt) {
  try {
    execSync(`ffmpeg -y -i "${inputPath}" -map 0:s:0 -f srt "${outputSrt}"`, { stdio: 'pipe' });
    return fs.existsSync(outputSrt) && fs.statSync(outputSrt).size > 0;
  } catch {
    return false;
  }
}

function extractAudioFromVideo(inputPath, outputAudio) {
  try {
    execSync(`ffmpeg -y -i "${inputPath}" -vn -ar 16000 -ac 1 -c:a libmp3lame -q:a 5 "${outputAudio}"`, {
      stdio: 'pipe'
    });
    return fs.existsSync(outputAudio);
  } catch {
    return false;
  }
}

function downloadOnlineSubtitles(url, tempDir) {
  const outputTemplate = path.join(tempDir, '%(id)s.%(ext)s');
  try {
    execSync(
      `yt-dlp --write-sub --write-auto-sub --sub-lang "vi,en,en-orig,ja,ko,zh,auto" --sub-format "vtt/srt/best" --skip-download -o "${outputTemplate}" "${url}"`,
      { stdio: 'pipe' }
    );
  } catch {}

  const files = fs.readdirSync(tempDir).filter(f => f.endsWith('.vtt') || f.endsWith('.srt'));
  if (files.length === 0) return null;

  const vi = files.find(f => f.includes('.vi.'));
  if (vi) return path.join(tempDir, vi);
  const en = files.find(f => f.includes('.en'));
  if (en) return path.join(tempDir, en);
  return path.join(tempDir, files[0]);
}

function downloadOnlineAudioOnly(url, outputAudio) {
  try {
    execSync(`yt-dlp -x --audio-format mp3 --audio-quality 5 -o "${outputAudio}" "${url}"`, {
      stdio: 'pipe'
    });
    if (fs.existsSync(outputAudio)) return true;
    if (fs.existsSync(outputAudio + '.mp3')) {
      fs.renameSync(outputAudio + '.mp3', outputAudio);
      return true;
    }
    return false;
  } catch {
    return false;
  }
}

function transcribeAudioAPI(audioPath, apiType = 'groq', apiKey = null, language = null) {
  return new Promise((resolve) => {
    const isGroq = apiType === 'groq';
    const host = isGroq ? 'api.groq.com' : 'api.openai.com';
    const endpoint = '/openai/v1/audio/transcriptions';
    const model = isGroq ? 'whisper-large-v3' : 'whisper-1';
    const token = apiKey || (isGroq ? process.env.GROQ_API_KEY : process.env.OPENAI_API_KEY);

    if (!token) return resolve(null);

    const boundary = `----WebKitFormBoundary${crypto.randomBytes(16).toString('hex')}`;
    const fileBuffer = fs.readFileSync(audioPath);
    const fileName = path.basename(audioPath);

    const parts = [
      Buffer.from(`--${boundary}\r\nContent-Disposition: form-data; name="model"\r\n\r\n${model}\r\n`),
      Buffer.from(`--${boundary}\r\nContent-Disposition: form-data; name="response_format"\r\n\r\nverbose_json\r\n`)
    ];

    if (language) {
      parts.push(Buffer.from(`--${boundary}\r\nContent-Disposition: form-data; name="language"\r\n\r\n${language}\r\n`));
    }

    parts.push(
      Buffer.from(
        `--${boundary}\r\nContent-Disposition: form-data; name="file"; filename="${fileName}"\r\nContent-Type: audio/mpeg\r\n\r\n`
      ),
      fileBuffer,
      Buffer.from(`\r\n--${boundary}--\r\n`)
    );

    const payload = Buffer.concat(parts);

    const req = https.request(
      {
        hostname: host,
        port: 443,
        path: endpoint,
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': `multipart/form-data; boundary=${boundary}`,
          'Content-Length': payload.length
        },
        timeout: 120000
      },
      (res) => {
        let raw = '';
        res.on('data', chunk => { raw += chunk; });
        res.on('end', () => {
          try {
            const data = JSON.parse(raw);
            const segments = (data.segments || []).map(s => ({
              start: parseFloat(s.start || 0),
              end: parseFloat(s.end || 0),
              text: (s.text || '').trim()
            }));
            resolve(segments.length > 0 ? segments : null);
          } catch {
            resolve(null);
          }
        });
      }
    );

    req.on('error', () => resolve(null));
    req.write(payload);
    req.end();
  });
}

function generateMarkdownReport(title, info, segments) {
  const lines = [];
  lines.push(`# 🎬 Bóc Băng & Lời Thoại Clip: ${title}\n`);
  lines.push('## ⏱️ Thông Tin Nguồn Clip');
  lines.push(`- **Nguồn / File:** \`${info.source || title}\``);
  if (info.duration_formatted && info.duration_formatted !== 'Unknown') {
    lines.push(`- **Tổng thời lượng:** \`${info.duration_formatted}\` (${(info.duration || 0).toFixed(1)}s)`);
  }
  if (info.resolution && info.resolution !== 'Unknown') {
    lines.push(`- **Độ phân giải:** \`${info.resolution}\``);
  }
  lines.push(`- **Số đoạn hội thoại:** \`${segments.length}\`\n`);

  lines.push('## 💬 Cuộc Trò Chuyện & Mốc Thời Gian (Transcript)\n');
  lines.push('| Thời gian (Timestamp) | Lời thoại / Cuộc trò chuyện (Dialogue) |');
  lines.push('| :--- | :--- |');

  for (const seg of segments) {
    const timeTag = `\`[${formatTimestamp(seg.start)} - ${formatTimestamp(seg.end)}]\``;
    const cleanText = seg.text.replace(/\|/g, '\\|');
    lines.push(`| ${timeTag} | ${cleanText} |`);
  }

  lines.push('\n---\n💡 *Được trích xuất tự động qua công cụ video-transcriber.*');
  return lines.join('\n');
}

async function main() {
  const args = process.argv.slice(2);
  if (args.length === 0 || args.includes('-h') || args.includes('--help')) {
    console.log('Cách dùng: node video_transcriber.js <file_video_mac_hoac_url> [--format md|json|srt|text] [-o output.md]');
    process.exit(0);
  }

  const rawInput = args[0].trim();
  const isUrl = rawInput.startsWith('http://') || rawInput.startsWith('https://') || rawInput.startsWith('www.');
  const tempDir = path.join(os.tmpdir(), `transcribe_${crypto.randomBytes(4).toString('hex')}`);
  fs.mkdirSync(tempDir, { recursive: true });

  const formatIdx = args.indexOf('--format');
  const format = formatIdx !== -1 && args[formatIdx + 1] ? args[formatIdx + 1] : 'md';

  const outIdx = args.indexOf('-o');
  const outFile = outIdx !== -1 && args[outIdx + 1] ? args[outIdx + 1] : null;

  let segments = [];
  const info = { source: rawInput };

  try {
    if (isUrl) {
      process.stderr.write(`Đang kiểm tra phụ đề từ URL: ${rawInput}...\n`);
      const subFile = downloadOnlineSubtitles(rawInput, tempDir);
      if (subFile && fs.existsSync(subFile)) {
        const rawText = fs.readFileSync(subFile, 'utf-8');
        const rawSegments = parseSubtitlesText(rawText);
        segments = groupShortSegments(rawSegments);
        process.stderr.write(`Đã trích xuất ${segments.length} đoạn phụ đề trực tiếp từ URL.\n`);
      } else {
        process.stderr.write('URL không có phụ đề sẵn. Đang kéo luồng âm thanh trực tiếp...\n');
        const audioPath = path.join(tempDir, 'online_audio.mp3');
        if (downloadOnlineAudioOnly(rawInput, audioPath)) {
          if (process.env.GROQ_API_KEY) {
            process.stderr.write('Đang bóc băng âm thanh online qua Groq Whisper...\n');
            const apiSegs = await transcribeAudioAPI(audioPath, 'groq');
            if (apiSegs) segments = groupShortSegments(apiSegs);
          }
          if (segments.length === 0 && process.env.OPENAI_API_KEY) {
            process.stderr.write('Đang bóc băng âm thanh online qua OpenAI Whisper...\n');
            const apiSegs = await transcribeAudioAPI(audioPath, 'openai');
            if (apiSegs) segments = groupShortSegments(apiSegs);
          }
        }
      }
    } else {
      const resolvedPath = resolveMacOSPath(rawInput);
      if (!fs.existsSync(resolvedPath)) {
        process.stderr.write(`Lỗi: Không tìm thấy file "${rawInput}" trên macOS.\n`);
        process.stderr.write(`Đã thử tìm tại: ${resolvedPath}\n`);
        process.exit(1);
      }

      info.source = resolvedPath;
      Object.assign(info, getVideoInfo(resolvedPath));
      process.stderr.write(`Clip trên máy: ${path.basename(resolvedPath)} | Thời lượng: ${info.duration_formatted} | ${info.resolution}\n`);

      const srtPath = path.join(tempDir, 'embedded.srt');
      if (extractSubtitlesFromVideo(resolvedPath, srtPath)) {
        process.stderr.write('Đã tìm thấy phụ đề tích hợp sẵn trong video! Đang bóc tách...\n');
        const rawText = fs.readFileSync(srtPath, 'utf-8');
        const rawSegments = parseSubtitlesText(rawText);
        segments = groupShortSegments(rawSegments);
      } else {
        process.stderr.write('Clip không có phụ đề tích hợp. Đang tách audio bằng ffmpeg...\n');
        const audioPath = path.join(tempDir, 'audio.mp3');
        if (extractAudioFromVideo(resolvedPath, audioPath)) {
          if (process.env.GROQ_API_KEY) {
            process.stderr.write('Đang bóc băng giọng nói qua Groq Whisper...\n');
            const apiSegs = await transcribeAudioAPI(audioPath, 'groq');
            if (apiSegs) segments = groupShortSegments(apiSegs);
          }
          if (segments.length === 0 && process.env.OPENAI_API_KEY) {
            process.stderr.write('Đang bóc băng giọng nói qua OpenAI Whisper...\n');
            const apiSegs = await transcribeAudioAPI(audioPath, 'openai');
            if (apiSegs) segments = groupShortSegments(apiSegs);
          }
        }
      }
    }

    let resultStr = '';
    if (segments.length === 0) {
      resultStr = `## ⚠️ Không tìm thấy phụ đề trong clip\n\n- **Nguồn clip:** \`${info.source}\`\n- **Thời lượng:** \`${info.duration_formatted || 'N/A'}\`\n- Để bóc băng âm thanh tự động, hãy thiết lập \`GROQ_API_KEY\` (miễn phí) hoặc \`OPENAI_API_KEY\`.`;
    } else {
      if (format === 'json') {
        resultStr = JSON.stringify({ info, segments }, null, 2);
      } else if (format === 'srt') {
        resultStr = segments
          .map((s, idx) => `${idx + 1}\n${formatTimestamp(s.start)},000 --> ${formatTimestamp(s.end)},000\n${s.text}\n`)
          .join('\n');
      } else if (format === 'text') {
        resultStr = segments.map(s => `[${formatTimestamp(s.start)}] ${s.text}`).join('\n');
      } else {
        const title = isUrl ? info.source : path.basename(info.source);
        resultStr = generateMarkdownReport(title, info, segments);
      }
    }

    if (outFile) {
      fs.writeFileSync(outFile, resultStr, 'utf-8');
      console.log(`Đã lưu kết quả tại: ${outFile}`);
    } else {
      console.log(resultStr);
    }
  } finally {
    fs.rmSync(tempDir, { recursive: true, force: true });
  }
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
