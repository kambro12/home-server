from flask import Flask, render_template, request, jsonify
import os, subprocess, threading

app = Flask(__name__)
BASE_DIR = "/mnt/media"

is_processing = False
stop_requested = False
current_process = None
current_file_name = "-"
process_output = []

def run_lektor_tasks(pairs, save_mode):
    global is_processing, process_output, current_process, stop_requested, current_file_name
    is_processing = True
    stop_requested = False
    process_output = ["Rozpoczynam sesję przetwarzania..."]
    
    try:
        for pair in pairs:
            if stop_requested:
                process_output.append("--- SESJA PRZERWANA PRZEZ UŻYTKOWNIKA ---")
                break
                
            video = pair.get('video')
            srt = pair.get('srt')
            current_file_name = os.path.basename(video)
            
            # Flaga: "1" jeśli chcemy subfolder, "0" w przeciwnym razie
            mode_str = "1" if save_mode else "0"

            current_process = subprocess.Popen(
                ['python3', '-u', '/app/lektor.py', video, srt, mode_str],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
            
            for line in current_process.stdout:
                process_output.append(line.strip())
                # Trzymamy tylko 20 ostatnich linii logów, by strona działała szybko
                if len(process_output) > 20:
                    process_output.pop(0)
            
            current_process.wait()
            
    except Exception as e:
        process_output.append(f"Błąd krytyczny: {e}")
    finally:
        if not stop_requested:
            process_output.append("Wszystkie zadania zakończone pomyślnie! IDLE")
        is_processing = False
        current_process = None
        current_file_name = "-"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/browse')
def browse():
    path = request.args.get('path', '/mnt/media/filmy')
    if not os.path.isdir(path):
        path = BASE_DIR
    parent_dir = os.path.dirname(path)
    if path == "/" or path == "/mnt":
        parent_dir = path

    dirs = []
    files = []
    try:
        for f in sorted(os.listdir(path)):
            full_path = os.path.join(path, f)
            if os.path.isdir(full_path):
                dirs.append({'name': f, 'path': full_path})
            elif f.endswith(('.mkv', '.mp4', '.avi', '.srt', '.pl.srt')):
                files.append({'name': f, 'path': full_path})
    except:
        pass

    return jsonify({
        'current': path,
        'parent': parent_dir,
        'dirs': dirs,
        'files': files
    })

@app.route('/api/delete', methods=['POST'])
def delete_files():
    files_to_delete = request.json.get('files', [])
    for f in files_to_delete:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass
    return jsonify({'status': 'ok'})

@app.route('/api/start', methods=['POST'])
def start():
    global is_processing
    pairs = request.json.get('pairs', [])
    save_mode = request.json.get('save_mode', False)
    
    if not is_processing and pairs:
        threading.Thread(target=run_lektor_tasks, args=(pairs, save_mode)).start()
        return jsonify({'status': 'started'})
    return jsonify({'status': 'busy'})

@app.route('/api/stop', methods=['POST'])
def stop():
    global stop_requested, current_process
    if is_processing:
        stop_requested = True
        if current_process:
            current_process.kill()
        return jsonify({'status': 'stopping'})
    return jsonify({'status': 'not_running'})

@app.route('/api/status')
def status():
    return jsonify({
        'is_processing': is_processing,
        'current_file': current_file_name,
        'output': process_output
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
