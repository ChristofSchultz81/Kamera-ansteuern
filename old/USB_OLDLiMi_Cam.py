import cv2
import datetime
import os
import signal
import time
import numpy as np
import tkinter as tk
from tkinter import filedialog
from flask import Flask, render_template_string, Response, request, jsonify

# --- 1. KAMERA-SUCHE UND AUSWAHL ---
def select_camera():
    print("Prüfe USB-Ports auf Kameras... (Bitte warten)")
    available_cameras = []
    
    for i in range(5):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW) 
        if cap.isOpened():
            ret, _ = cap.read()
            if ret: 
                available_cameras.append(i)
            cap.release()
            
    if not available_cameras:
        print("\n[FEHLER] Keine Kamera gefunden! Bitte USB-Kabel prüfen.")
        # Falls gar nichts gefunden wird, erlauben wir trotzdem die manuelle Eingabe von ID 0 oder 1 zum Testen
        choice = input("Keine aktive Kamera erkannt. ID manuell erzwingen? (0/1) oder 'q' zum Beenden: ")
        if choice.lower() == 'q': exit()
        return int(choice)
        
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
    save_directory = os.getcwd()

# --- 3. FLASK SERVER & KAMERA SETUP ---
app = Flask(__name__)

print(f"Initialisiere Kamera ID {selected_cam_id}...")
camera = cv2.VideoCapture(selected_cam_id, cv2.CAP_DSHOW)

# Auflösung für alte Chips festlegen
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Kurz warten, damit der alte Treiber Zeit hat aufzuwachen
time.sleep(1)

current_frame = None

# --- 4. DAS HTML INTERFACE ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Retro Kamera Kontrollzentrum</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #1a1a1a; color: white; text-align: center; margin: 0; padding: 20px; }
        .grid { display: flex; flex-direction: column; align-items: center; gap: 20px; margin-top: 20px; }
        img { border: 3px solid #444; border-radius: 8px; background: black; max-width: 90vw; min-height: 300px; }
        .controls { background: #2a2a2a; padding: 20px; border-radius: 12px; width: 600px; max-width: 90vw; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        input[type=range] { width: 100%; margin: 15px 0; }
        .btns { display: flex; gap: 15px; justify-content: center; margin-top: 15px; }
        button { padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 16px; }
        .btn-save { background: #28a745; color: white; }
        .btn-stop { background: #dc3545; color: white; }
        #status { margin-top: 15px; color: #ccc; }
    </style>
</head>
<body>
    <h1>Retro Kamera Kontrollzentrum</h1>
    <div class="grid">
        <img src="{{ url_for('video_feed') }}" alt="Kamera Live-Stream">
        <div class="controls">
            <label>Integrationszeit (Belichtung): <span id="expVal">-5</span></label>
            <input type="range" min="-13" max="0" value="-5" oninput="updateExp(this.value)">
            <div class="btns">
                <button class="btn-save" onclick="saveImg()">Bild Speichern</button>
                <button class="btn-stop" onclick="stopSw()">Software Beenden</button>
            </div>
            <p id="status"><strong>Speicherort:</strong> {{ save_dir }}</p>
        </div>
    </div>
    <script>
        function updateExp(v) {
            document.getElementById('expVal').innerText = v;
            fetch('/set_exp?val=' + v);
        }
        function saveImg() {
            let statusEl = document.getElementById('status');
            statusEl.innerText = "Speichere...";
            fetch('/save').then(r => r.json()).then(d => {
                statusEl.innerText = d.msg;
            });
        }
        function stopSw() {
            if(confirm("Programm beenden?")) {
                fetch('/shutdown').then(() => { window.close(); });
                document.body.innerHTML = "<h1 style='margin-top:20%; color:#28a745;'>Programm beendet.</h1>";
            }
        }
    </script>
</body>
</html>
"""

# --- 5. BILDVERARBEITUNG & HISTOGRAMM ---
def get_histogram(image):
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        cv2.normalize(hist, hist, 0, 150, cv2.NORM_MINMAX)
        
        hist_w, hist_h = 256, image.shape[0]
        canvas = np.zeros((hist_h, hist_w, 3), dtype=np.uint8)
        
        for i in range(1, 256):
            val_prev = int(hist[i-1][0])
            val_curr = int(hist[i][0])
            cv2.line(canvas, (i-1, hist_h - val_prev), (i, hist_h - val_curr), (0, 255, 255), 2)
        return canvas
    except:
        return np.zeros((480, 256, 3), dtype=np.uint8)

def gen_frames():
    global current_frame
    last_error_time = 0
    
    while True:
        try:
            success, frame = camera.read()
            
            # FALLBACK: Wenn die Kamera keine Bilder liefert
            if not success or frame is None:
                current_time = time.time()
                if current_time - last_error_time > 5:
                    print("[WARNUNG] Kamera geöffnet, liefert aber aktuell keine Bilddaten.")
                    last_error_time = current_time
                
                # Erzeuge ein blaues "KEIN SIGNAL" Testbild für den Browser
                error_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                error_frame[:] = [120, 50, 50] # Blau/Grauer Hintergrund
                cv2.putText(error_frame, "KEIN SIGNAL", (180, 230), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
                cv2.putText(error_frame, "Treiber blockiert oder falsches Format", (90, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
                
                blank_hist = np.zeros((480, 256, 3), dtype=np.uint8)
                combined = cv2.hconcat([error_frame, blank_hist])
                
                ret, buffer = cv2.imencode('.jpg', combined)
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                time.sleep(0.2) # Verhindert CPU-Überlastung im Fehlerfall
                continue 
            
            # Wenn ein echtes Bild kommt:
            current_frame = frame.copy()
            hist_img = get_histogram(frame)
            
            if frame.shape[0] == hist_img.shape[0]:
                combined = cv2.hconcat([frame, hist_img])
            else:
                combined = frame 
            
            ret, buffer = cv2.imencode('.jpg', combined)
            if not ret: continue
                
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            time.sleep(0.03) # Begrenzung auf ca. 30 FPS entlastet den alten USB-Bus
            
        except Exception as e:
            print(f"Fehler im Video-Stream-Loop: {e}")
            time.sleep(1)

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
        cv2.imwrite(os.path.join(save_directory, fname), current_frame)
        return jsonify(msg=f"Bild gespeichert: {fname}")
    return jsonify(msg="Fehler: Kein Live-Bild zum Speichern vorhanden")

@app.route('/shutdown')
def shutdown():
    print("Beende Server...")
    camera.release()
    os.kill(os.getpid(), signal.SIGINT)
    return "OK"

# --- 7. SERVER START ---
if __name__ == '__main__':
    print(f"\n--- SERVER STARTET ---")
    print(f"Adresse im Browser: http://127.0.0.1:5000")
    
    # CRITICAL FIX: debug=True MUSS use_reloader=False haben, 
    # da sonst die Kamera doppelt geöffnet und blockiert wird!
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)