import cv2
import datetime
import os
import signal
import numpy as np
import tkinter as tk
from tkinter import filedialog
from flask import Flask, render_template_string, Response, request, jsonify

# --- 1. KAMERA-SUCHE UND AUSWAHL ---
def select_camera():
    print("Prüfe USB-Ports auf Kameras... (Bitte warten)")
    available_cameras = []
    
    # Prüfe IDs 0 bis 4
    for i in range(5):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW) 
        if cap.isOpened():
            ret, _ = cap.read()
            if ret: 
                available_cameras.append(i)
            cap.release()
            
    if not available_cameras:
        print("Fehler: Keine Kamera gefunden! Bitte USB-Verbindung prüfen.")
        exit()
        
    print(f"\n--- Gefundene Kameras ---")
    for cam in available_cameras:
        print(f"Kamera ID: {cam}")
        
    while True:
        try:
            choice = int(input(f"\nBitte wähle die Kamera-ID {available_cameras}: "))
            if choice in available_cameras:
                return choice
            else:
                print("Ungültige ID. Bitte wähle eine aus der Liste.")
        except ValueError:
            print("Bitte gib eine gültige Zahl ein.")

selected_cam_id = select_camera()

# --- 2. SPEICHERORT ABFRAGEN ---
root = tk.Tk()
root.withdraw()
root.attributes('-topmost', True)
save_directory = filedialog.askdirectory(title="Speicherort für Bilder wählen")

if not save_directory: 
    print("Kein Verzeichnis ausgewählt. Speichere im aktuellen Skript-Ordner.")
    save_directory = os.getcwd()

# --- 3. FLASK SERVER & KAMERA SETUP ---
app = Flask(__name__)
camera = cv2.VideoCapture(selected_cam_id, cv2.CAP_DSHOW)

# Zwinge die Kamera auf eine klassische VGA-Auflösung (wichtig für alte Chips)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Falls das Bild farblich komisch aussieht, entferne das '#' in der nächsten Zeile:
# camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'YUYV')) 

current_frame = None

# --- 4. DAS HTML/CSS/JS INTERFACE ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Retro Kamera Kontrollzentrum</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #1a1a1a; color: white; text-align: center; margin: 0; padding: 20px; }
        .grid { display: flex; flex-direction: column; align-items: center; gap: 20px; margin-top: 20px; }
        img { border: 3px solid #444; border-radius: 8px; background: black; max-width: 90vw; }
        .controls { background: #2a2a2a; padding: 20px; border-radius: 12px; width: 600px; max-width: 90vw; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        input[type=range] { width: 100%; margin: 15px 0; cursor: pointer; }
        .btns { display: flex; gap: 15px; justify-content: center; margin-top: 15px; }
        button { padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 16px; transition: 0.2s; }
        .btn-save { background: #28a745; color: white; }
        .btn-save:hover { background: #218838; }
        .btn-stop { background: #dc3545; color: white; }
        .btn-stop:hover { background: #c82333; }
        #status { margin-top: 15px; font-size: 1em; color: #ccc; }
        .info-text { font-size: 0.8em; color: #888; margin-top: 10px; }
    </style>
</head>
<body>
    <h1>Retro Kamera Kontrollzentrum</h1>
    <div class="grid">
        <img src="{{ url_for('video_feed') }}" alt="Kamera Stream (Läd...)">
        
        <div class="controls">
            <label>Integrationszeit (Belichtung): <span id="expVal">-5</span></label>
            <input type="range" min="-13" max="0" value="-5" oninput="updateExp(this.value)">
            
            <div class="btns">
                <button class="btn-save" onclick="saveImg()">Bild Speichern</button>
                <button class="btn-stop" onclick="stopSw()">Software Beenden</button>
            </div>
            
            <p id="status"><strong>Speicherort:</strong> {{ save_dir }}</p>
            <p class="info-text">Server läuft auf Port 5000</p>
        </div>
    </div>

    <script>
        function updateExp(v) {
            document.getElementById('expVal').innerText = v;
            fetch('/set_exp?val=' + v);
        }

        function saveImg() {
            let statusEl = document.getElementById('status');
            statusEl.style.color = '#ffc107';
            statusEl.innerText = "Speichere...";
            
            fetch('/save')
                .then(r => r.json())
                .then(d => {
                    statusEl.style.color = '#28a745';
                    statusEl.innerText = d.msg;
                    setTimeout(() => {
                        statusEl.style.color = '#ccc';
                        statusEl.innerHTML = "<strong>Speicherort:</strong> {{ save_dir | replace('\\', '\\\\') }}";
                    }, 4000);
                })
                .catch(err => {
                    statusEl.style.color = '#dc3545';
                    statusEl.innerText = "Fehler beim Speichern!";
                });
        }

        function stopSw() {
            if(confirm("Möchten Sie die Kameraverbindung und den Server wirklich beenden?")) {
                fetch('/shutdown').then(() => { 
                    window.close(); 
                });
                document.body.innerHTML = "<h1 style='margin-top: 20%; color: #28a745;'>Programm sicher beendet.</h1><p>Sie können diesen Tab nun schließen.</p>";
            }
        }
    </script>
</body>
</html>
"""

# --- 5. BILDVERARBEITUNG & HISTOGRAMM ---
def get_histogram(image):
    try:
        if image is None or image.size == 0:
            return np.zeros((480, 256, 3), dtype=np.uint8)

        # In Graustufen umwandeln und Histogramm berechnen
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        cv2.normalize(hist, hist, 0, 150, cv2.NORM_MINMAX)
        
        hist_w, hist_h = 256, image.shape[0]
        canvas = np.zeros((hist_h, hist_w, 3), dtype=np.uint8)
        
        # Zeichne die Histogramm-Linien
        for i in range(1, 256):
            val_prev = int(hist[i-1][0])
            val_curr = int(hist[i][0])
            cv2.line(canvas, (i-1, hist_h - val_prev), (i, hist_h - val_curr), (0, 255, 255), 2)
            
        return canvas
    except Exception as e:
        print(f"Fehler bei Histogramm-Erstellung: {e}")
        return np.zeros((image.shape[0] if image is not None else 480, 256, 3), dtype=np.uint8)

def gen_frames():
    global current_frame
    while True:
        try:
            success, frame = camera.read()
            
            if not success or frame is None:
                continue 
            
            current_frame = frame.copy()
            
            hist_img = get_histogram(frame)
            
            # Sicherheitscheck für die Zusammenführung (Bilder müssen gleich hoch sein)
            if frame.shape[0] == hist_img.shape[0]:
                combined = cv2.hconcat([frame, hist_img])
            else:
                combined = frame 
            
            ret, buffer = cv2.imencode('.jpg', combined)
            if not ret:
                continue
                
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            
        except Exception as e:
            print(f"Warnung - Fehler im Video-Stream: {e}")

# --- 6. FLASK ROUTEN ---
@app.route('/')
def index(): 
    return render_template_string(HTML_TEMPLATE, save_dir=save_directory)

@app.route('/video_feed')
def video_feed(): 
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/set_exp')
def set_exp():
    val = request.args.get('val', type=float)
    camera.set(cv2.CAP_PROP_EXPOSURE, val)
    return jsonify(success=True)

@app.route('/save')
def save():
    global current_frame
    if current_frame is not None:
        fname = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".jpg"
        filepath = os.path.join(save_directory, fname)
        cv2.imwrite(filepath, current_frame)
        return jsonify(msg=f"Bild gespeichert: {fname}")
    return jsonify(msg="Fehler: Kein Bild zum Speichern vorhanden")

@app.route('/shutdown')
def shutdown():
    print("Fahre Server herunter und gebe Kamera frei...")
    camera.release()
    os.kill(os.getpid(), signal.SIGINT)
    return "Server beendet"

# --- 7. SERVER START ---
if __name__ == '__main__':
    print(f"\n--- SETUP ABGESCHLOSSEN ---")
    print(f"Speicherort: {save_directory}")
    print(f"Öffne jetzt deinen Webbrowser und gehe auf: http://127.0.0.1:5000")
    print(f"Um das Programm zu beenden, nutze den roten Button im Browser.")
    print(f"---------------------------\n")
    
    # Server starten (debug=True hilft bei weiteren Fehleranalysen)
    app.run(host='0.0.0.0', port=5000, debug=True)