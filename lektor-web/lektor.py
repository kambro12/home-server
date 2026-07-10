#!/usr/bin/env python3
import os, sys, re, socket, json, subprocess, time

PIPER_HOST = os.environ.get("PIPER_HOST", "piper")
PIPER_PORT = int(os.environ.get("PIPER_PORT", 10200))
BYTES_PER_SECOND = 44100 

if len(sys.argv) < 3:
    print("Błąd: Nie podano pliku wideo i srt.")
    sys.exit(1)

video_file = sys.argv[1]
srt_file = sys.argv[2]
save_mode = sys.argv[3] if len(sys.argv) > 3 else "0"

target_dir = os.path.dirname(video_file)
out_dir = target_dir

if save_mode == "1":
    out_dir = os.path.join(target_dir, "Lektor_PL")
    os.makedirs(out_dir, exist_ok=True)

def clean_text(text):
    text = re.sub(r'<[^>]*>', '', text)
    text = re.sub(r'[^\w\s.,?!;:ąęłńóśźżĄĘŁŃÓŚŹŻ-]', '', text)
    text = re.sub(r'\.{2,}', '.', text)
    return text.replace('?', '.').replace('\n', ' ').strip()

def srt_time_to_seconds(time_str):
    match = re.match(r"(\d+):(\d+):(\d+),(\d+)", time_str)
    if match:
        h, m, s, ms = map(int, match.groups())
        return h * 3600 + m * 60 + s + ms / 1000.0
    return 0.0

def read_exact(sock_file, size):
    buf = bytearray()
    while len(buf) < size:
        chunk = sock_file.read(size - len(buf))
        if not chunk: break
        buf.extend(chunk)
    return bytes(buf)

def process_media(video_file, srt_file):
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    
    temp_pcm = os.path.join(out_dir, f"temp_{base_name}.pcm")
    temp_wav = os.path.join(out_dir, f"temp_{base_name}.wav")
    temp_mixed = os.path.join(out_dir, f"temp_{base_name}_mixed.ac3")
    output_mkv = os.path.join(out_dir, f"{base_name}_PL.mkv")

    print(f"\n--- Analiza: {base_name} ---")

    with open(srt_file, 'r', encoding='utf-8') as f:
        content = f.read().strip()

    parsed_blocks = []
    for block in re.split(r'\n\s*\n', content):
        lines = [l.strip() for l in block.split('\n') if l.strip()]
        if len(lines) >= 3 and "-->" in lines[1]:
            try:
                start_str, end_str = lines[1].split("-->")
                start = srt_time_to_seconds(start_str.strip())
                end = srt_time_to_seconds(end_str.strip())
                text = clean_text(" ".join(lines[2:]))
                if text: parsed_blocks.append({"start": start, "end": end, "text": text})
            except: continue

    if not parsed_blocks:
        print("Brak poprawnych napisów w pliku.")
        return

    grouped_blocks = []
    current_group = parsed_blocks[0]
    for next_block in parsed_blocks[1:]:
        if next_block["start"] - current_group["end"] < 1.5:
            current_group["text"] += " " + next_block["text"]
            current_group["end"] = next_block["end"]
        else:
            grouped_blocks.append(current_group)
            current_group = next_block
    grouped_blocks.append(current_group)

    print(f"Generowanie audio ({len(grouped_blocks)} sekwencji)...")
    current_pcm_bytes = 0

    try:
        with open(temp_pcm, "wb") as f_pcm:
            for idx, group in enumerate(grouped_blocks):
                target_start_bytes = int(group["start"] * BYTES_PER_SECOND)
                if target_start_bytes % 2 != 0: target_start_bytes += 1

                pad_bytes = target_start_bytes - current_pcm_bytes
                if pad_bytes > 0:
                    if pad_bytes % 2 != 0: pad_bytes += 1
                    f_pcm.write(b'\x00' * pad_bytes)
                    current_pcm_bytes += pad_bytes

                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    s.settimeout(60.0)
                    s.connect((PIPER_HOST, PIPER_PORT))
                    req = json.dumps({"type": "synthesize", "data": {"text": group["text"]}})
                    s.sendall(f"{req}\n".encode('utf-8'))

                    sock_file = s.makefile('rwb')
                    while True:
                        line = sock_file.readline()
                        if not line: break
                        try: event = json.loads(line.decode('utf-8'))
                        except: continue

                        d_len = event.get("data_length", 0)
                        if d_len > 0: read_exact(sock_file, d_len)

                        p_len = event.get("payload_length", 0)
                        if p_len > 0:
                            payload = read_exact(sock_file, p_len)
                            if event.get("type") == "audio-chunk":
                                if len(payload) % 2 != 0: payload = payload[:-1] 
                                f_pcm.write(payload)
                                current_pcm_bytes += len(payload)

                        if event.get("type") in ["audio-end", "audio-stop"]: break
                    sock_file.close()
                    s.close()
                except Exception as e:
                    print(f"Ostrzeżenie: Błąd w sekwencji {idx+1}: {e}")

                if (idx + 1) % 50 == 0 or (idx + 1) == len(grouped_blocks):
                    print(f"Postęp: {idx + 1}/{len(grouped_blocks)}")

    except Exception as e:
        print(f"Błąd krytyczny: {e}")
        return

    print("Miksowanie ścieżek z oryginalnym tłem (Tło: 100%, Lektor: 120%)...")
    subprocess.run(["ffmpeg", "-y", "-f", "s16le", "-ar", "22050", "-ac", "1", "-i", temp_pcm, temp_wav], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    komenda_ffmpeg = [
        "ffmpeg", "-y",
        "-i", video_file,
        "-i", temp_wav,
        # ZMIANA: Tło na 1.0 (100%), lektor na 1.2 (120%)
        "-filter_complex", "[0:a:0]volume=1.0[orig];[1:a]volume=1.2[lektor];[orig][lektor]amix=inputs=2:duration=first:dropout_transition=0[zmiksowane]",
        "-map", "[zmiksowane]",
        "-c:a", "ac3",      
        "-b:a", "384k",     
        temp_mixed
    ]
    try:
        subprocess.run(komenda_ffmpeg, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"Błąd FFmpeg: {e}")
        return

    if os.path.exists(output_mkv): os.remove(output_mkv)

    print("Ostateczne pakowanie mkvmerge...")
    komenda_mkvmerge = [
        "mkvmerge", "-o", output_mkv,
        video_file,                 
        "--language", "0:pl",
        "--track-name", "0:Polski Lektor AI",
        "--default-track", "0:yes",
        temp_mixed                  
    ]
    try:
        subprocess.run(komenda_mkvmerge, check=True, stdout=subprocess.DEVNULL)
        st = os.stat(video_file)
        os.chown(output_mkv, st.st_uid, st.st_gid)
        os.chmod(output_mkv, 0o664)
        print(f"Sukces! Gotowy plik leży w: {out_dir}")
    except Exception as e:
        print(f"Błąd mkvmerge: {e}")

    for tmp in [temp_pcm, temp_wav, temp_mixed]:
        if os.path.exists(tmp):
            try: os.remove(tmp)
            except: pass

process_media(video_file, srt_file)
