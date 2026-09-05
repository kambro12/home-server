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
    try:
        st_dir = os.stat(target_dir)
        os.chown(out_dir, st_dir.st_uid, st_dir.st_gid)
        os.chmod(out_dir, 0o777)
    except: pass

def clean_text(text):
    text = re.sub(r'<[^>]*>', '', text)
    # Usuwamy napisy dla niesłyszących (didaskalia) w nawiasach okrągłych, kwadratowych i klamrowych
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'\{.*?\}', '', text)
    
    
    # Rozbudowany słownik wymowy (podmiana na zapis fonetyczny)
    replacements = {
        # Skróty
        r'\bFBI\b': 'ef bi aj',
        r'\bCIA\b': 'si aj ej',
        r'\bNSA\b': 'en es ej',
        r'\bUSA\b': 'ju es ej',
        r'\bUK\b': 'ju kej',
        r'\bUN\b': 'ju en',
        r'\bMI6\b': 'em aj siks',
        r'\bSWAT\b': 'słot',
        r'\bNYPD\b': 'en łaj pi di',
        r'\bLAPD\b': 'el ej pi di',
        r'\bOK\b': 'okej',
        r'\bCEO\b': 'si i o',
        r'\bVIP\b': 'wip',
        r'\bDNA\b': 'di en ej',
        
        # Zaimki / popularne zwroty
        r'\bSir\b': 'ser',
        r'\bMa\'am\b': 'mam',
        r'\bMister\b': 'mister',
        r'\bMrs\.\b': 'misis',
        r'\bMiss\b': 'mis',
        r'\bCop\b': 'kop',
        r'\bCops\b': 'kops',
        
        # Miejscowości i państwa
        r'\bNew York\b': 'Niu Jork',
        r'\bNew Yorku\b': 'Niu Jorku',
        r'\bLos Angeles\b': 'Los Andżeles',
        r'\bWashington\b': 'Waszyngton',
        r'\bWashingtonie\b': 'Waszyngtonie',
        r'\bChicago\b': 'Szikago',
        r'\bMiami\b': 'Majami',
        r'\bLas Vegas\b': 'Las Wegas',
        r'\bHollywood\b': 'Holiłud',
        r'\bTexas\b': 'Teksas',
        r'\bLondyn\b': 'Londyn', # just in case
        r'\bLondon\b': 'Londyn',
        r'\bParis\b': 'Paryż',
        r'\bSeattle\b': 'Sijatl',
        r'\bBoston\b': 'Boston',
        
        # Imiona - Męskie
        r'\bJason\b': 'Dżejson',
        r'\bJasona\b': 'Dżejsona',
        r'\bJohn\b': 'Dżon',
        r'\bJohna\b': 'Dżona',
        r'\bMichael\b': 'Majkel',
        r'\bMichaelowi\b': 'Majkelowi',
        r'\bGeorge\b': 'Dżordż',
        r'\bJack\b': 'Dżak',
        r'\bJacka\b': 'Dżaka',
        r'\bJames\b': 'Dżejms',
        r'\bJamesa\b': 'Dżejmsa',
        r'\bHarry\b': 'Hari',
        r'\bWilliam\b': 'Łiliam',
        r'\bDavid\b': 'Dawid',
        r'\bDavida\b': 'Dawida',
        r'\bRichard\b': 'Riszard',
        r'\bThomas\b': 'Tomas',
        r'\bCharles\b': 'Czarls',
        r'\bJoseph\b': 'Dżozef',
        r'\bPeter\b': 'Piter',
        r'\bPaul\b': 'Pol',
        r'\bMark\b': 'Mark',
        r'\bBrian\b': 'Brajan',
        r'\bKevin\b': 'Kewin',
        r'\bMatthew\b': 'Metiu',
        r'\bAnthony\b': 'Antoni',
        r'\bSteve\b': 'Stiw',
        r'\bSteven\b': 'Stiwen',
        r'\bStephen\b': 'Stiwen',
        r'\bArthur\b': 'Artur',
        r'\bChris\b': 'Kris',
        r'\bChristopher\b': 'Kristofer',
        r'\bDaniel\b': 'Daniel',
        
        # Imiona - Żeńskie
        r'\bSarah\b': 'Sara',
        r'\bMary\b': 'Meri',
        r'\bJessica\b': 'Dżesika',
        r'\bEmily\b': 'Emili',
        r'\bAshley\b': 'Aszli',
        r'\bAmanda\b': 'Amanda',
        r'\bMelissa\b': 'Melisa',
        r'\bMichelle\b': 'Miszel',
        r'\bLaura\b': 'Lora',
        r'\bJennifer\b': 'Dżenifer',
        r'\bRachel\b': 'Rejczel',
        r'\bNicole\b': 'Nikol',
        r'\bVictoria\b': 'Wiktoria',
        r'\bElizabeth\b': 'Elizabet',
        r'\bChloe\b': 'Klołi',
        r'\bJane\b': 'Dżejn',
        r'\bAlice\b': 'Alis',
        
        # Inne nazwy
        r'\bFacebook\b': 'Fejsbuk',
        r'\bTwitter\b': 'Tłiter',
        r'\bGoogle\b': 'Gugl',
        r'\bYouTube\b': 'Jutub',
        r'\bInternet\b': 'Internet',
        
        # Polskie i powszechne skrótowce (wymagają dokładnej wielkości liter)
        r'\bDNA\b': 'de en a',
        r'\bONZ\b': 'o en zet',
        r'\bUE\b': 'u e',
        r'\bPRL\b': 'pe er el',
        r'\bAGD\b': 'a gie de',
        r'\bRTV\b': 'er te fau',
        r'\bBHP\b': 'be ha pe',
        r'\bNFZ\b': 'en ef zet',
        r'\bCV\b': 'si wi',
        r'\bIT\b': 'aj ti',
        r'\bPR\b': 'pi ar',
        r'\bHR\b': 'ha er',
        r'\bSMS\b': 'esemes',
        r'\bMMS\b': 'ememes',
        r'\bUSB\b': 'u es be',
        r'\bPDF\b': 'pe de ef',
        r'\bGPS\b': 'dżi pi es',
        r'\bWi-Fi\b': 'waj faj',
        r'\bWWW\b': 'wu wu wu',
        r'\bHIV\b': 'hiw',
        r'\bAIDS\b': 'ejds',
        r'\bPKP\b': 'pe ka pe',
        r'\bPKS\b': 'pe ka es',
        r'\bPC\b': 'pi si'
    }
    
    for word, phonetic in replacements.items():
        # Usunęliśmy re.IGNORECASE, bo powodowało to, że skrót "DNA" łapał polskie słowo "dna" (od "dno").
        # Teraz wielkość liter ma znaczenie, co uchroni nas przed pomyłkami.
        text = re.sub(word, phonetic, text)

    text = re.sub(r'[^\w\s.,?!;:ąęłńóśźżĄĘŁŃÓŚŹŻ-]', '', text)
    text = re.sub(r'\.{2,}', '.', text)
    return text.replace('\n', ' ').strip()

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

    try:
        print(f"\n--- Analiza: {base_name} ---")

        if srt_file == "EMBEDDED":
            print("Próba wydobycia wbudowanych napisów z pliku wideo...")
            extracted_srt = os.path.join(out_dir, f"temp_{base_name}_extracted.srt")
            # Próbujemy najpierw polskie napisy, jeśli błąd to próbujemy pierwsze lepsze.
            ret = subprocess.run(["ffmpeg", "-y", "-i", video_file, "-map", "0:s:m:language:pol", "-c:s", "srt", extracted_srt], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if ret.returncode != 0 or not os.path.exists(extracted_srt) or os.path.getsize(extracted_srt) == 0:
                print("Brak wbudowanych polskich napisów. Próbuję wyciągnąć pierwszą domyślną ścieżkę napisów...")
                subprocess.run(["ffmpeg", "-y", "-i", video_file, "-map", "0:s:0", "-c:s", "srt", extracted_srt], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            if os.path.exists(extracted_srt) and os.path.getsize(extracted_srt) > 0:
                srt_file = extracted_srt
                print("Wbudowane napisy zostały pomyślnie wyodrębnione.")
            else:
                print("Błąd: Nie znaleziono żadnych napisów w pliku wideo.")
                return

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

        with open(temp_pcm, "wb") as f_pcm:
            for idx, group in enumerate(grouped_blocks):
                target_start_bytes = int(group["start"] * BYTES_PER_SECOND)
                if target_start_bytes % 2 != 0: target_start_bytes += 1

                pad_bytes = target_start_bytes - current_pcm_bytes
                if pad_bytes > 0:
                    if pad_bytes % 2 != 0: pad_bytes += 1
                    f_pcm.write(b'\x00' * pad_bytes)
                else:
                    # FIX DRIFT: przywracamy pozycję zapisu (nadpisujemy ogon poprzedniej, zbyt długiej kwestii)
                    f_pcm.seek(target_start_bytes)
                
                current_pcm_bytes = target_start_bytes

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

        print("Konwersja na WAV...")
        subprocess.run(["ffmpeg", "-y", "-f", "s16le", "-ar", "22050", "-ac", "1", "-i", temp_pcm, temp_wav], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        print("Miksowanie ścieżek z Audio Duckingiem (ściszanie tła)...")
        # AUDIO DUCKING FIX
        komenda_ffmpeg = [
            "ffmpeg", "-y",
            "-i", video_file,
            "-i", temp_wav,
            "-filter_complex", "[1:a]volume=1.2,asplit=2[sc][lektor_mix];[0:a:0][sc]sidechaincompress=threshold=0.08:ratio=4:attack=50:release=1000[ducked];[ducked][lektor_mix]amix=inputs=2:duration=first:dropout_transition=0[zmiksowane]",
            "-map", "[zmiksowane]",
            "-c:a", "ac3",      
            "-b:a", "384k",     
            temp_mixed
        ]
        
        try:
            subprocess.run(komenda_ffmpeg, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"Błąd FFmpeg (miksowanie): {e}")
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
        
        # Jeśli napisy pochodzą z zewnętrznego pliku, wtapiamy je jako osobną ścieżkę
        if sys.argv[2] != "EMBEDDED" and os.path.exists(sys.argv[2]):
            komenda_mkvmerge.extend([
                "--language", "0:pl",
                "--track-name", "0:Polskie Napisy",
                sys.argv[2]
            ])
        
        try:
            subprocess.run(komenda_mkvmerge, check=True, stdout=subprocess.DEVNULL)
            
            try:
                st = os.stat(video_file)
                os.chown(output_mkv, st.st_uid, st.st_gid)
                os.chmod(output_mkv, 0o777)
            except: pass
            
            print(f"Sukces! Gotowy plik leży w: {out_dir}")
        except Exception as e:
            print(f"Błąd mkvmerge: {e}")

    except Exception as e:
        print(f"Błąd krytyczny: {e}")
    finally:
        # CLEANUP FIX: Zawsze usuwaj pliki tymczasowe
        print("Czyszczenie plików tymczasowych...")
        temp_srt = os.path.join(out_dir, f"temp_{base_name}_extracted.srt")
        for tmp in [temp_pcm, temp_wav, temp_mixed, temp_srt]:
            if os.path.exists(tmp):
                try: os.remove(tmp)
                except: pass

process_media(video_file, srt_file)
