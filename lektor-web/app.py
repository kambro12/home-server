from flask import Flask, render_template, request, jsonify
import os, subprocess, threading

app = Flask(__name__)
BASE_DIR = "/mnt/media/filmy"

is_processing = False
process_output = []

def run_lektor_tasks(pairs):
    global is_processing, process_output
    is_processing = True
    process_output = ["Rozpoczynam przetwarzanie zaznaczonych plików..."]
    
    try:
        for pair in pairs:
            video = pair.get('video')
            srt = pair.get('srt')
            process_output.append(f"Przetwarzam: {os.path.basename(video)}")
            
            p = subprocess.Popen(
                ['python3', '-u', '/app/lektor.py', video, srt],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
            for line in p.stdout:
                process_output.append(line.strip())
                if len(process_output) > 20:
                    process_output.pop(0)
            p.wait()
    except Exception as e:
        process_output.append(f"Błąd krytyczny: {e}")
    finally:
        process_output.append("Wszystkie zadania zakończone pomyślnie! IDLE")
        is_processing = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/browse')
def browse():
    path = request.args.get('path', BASE_DIR)
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
            try:
                os.remove(f)
            except:
                pass
    return jsonify({'status': 'ok'})

@app.route('/api/start', methods=['POST'])
def start():
    global is_processing
    pairs = request.json.get('pairs', [])
    if not is_processing and pairs:
        threading.Thread(target=run_lektor_tasks, args=(pairs,)).start()
        return jsonify({'status': 'started'})
    return jsonify({'status': 'busy'})

@app.route('/api/status')
def status():
    return jsonify({
        'is_processing': is_processing,
        'output': process_output[-1] if process_output else "IDLE"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
