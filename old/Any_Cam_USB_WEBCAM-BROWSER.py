import cv2
import datetime
import os
import tkinter as tk
from tkinter import filedialog
from flask import Flask, render_template_string, Response, request, jsonify

# --- 1. FRAGE NACH DEM SPEICHERORT ---
# Wir starten ein unsichtbares Tkinter-Fenster, um den nativen Datei-Dialog zu nutzen
root = tk.Tk()
root.withdraw() 
root.attributes('-topmost', True) # Bringt das Fenster in den Vordergrund
save_directory = filedialog.askdirectory(title="Wo sollen die Bilder gespeichert werden?")

if not save_directory:
    print("Kein Verzeichnis ausgewählt. Speichere im aktuellen Ordner des Skripts.")
    save_directory = os.getcwd()

# --- 2. FLASK SERVER & KAMERA INITIALISIEREN ---
app = Flask(__name__)

# '0' ist meistens die erste angeschlossene USB-Kamera. 
# Falls du eine Webcam am Laptop hast, ist die USB-Kamera eventuell '1'.
camera = cv2.VideoCapture(0) 

# Globale Variable, um den jeweils aktuellsten Frame für das Speichern vorzuhalten
current_frame = None

# --- 3. DAS HTML/CSS/JS FÜR DEN BROWSER ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Retro USB-Kamera Steuerung</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f9; text-align: center; padding: 20px; }
        .container { background: white; padding: 20px; border-radius: 10px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); display: inline-block; max-width: 90%; }
        img { max-width: 100%; border: 2px solid #ddd; border-radius: 5px; margin-bottom: 20px; }
        .controls { margin: 20px 0; padding: 15px; background: #eef; border-radius: 8px; }
        input[type=range] { width: 80%; }
        button { background-color: #28a745; color: white; border: none; padding: 10px 20px; font-size: 16px; border-radius: 5px; cursor: pointer; }
        button:hover { background-color: #218838; }
        #status { margin-top: 15px; font-weight: bold; color: #333; }
    </style>
</head>
<body>

<div class="container">
    <h2>Retro Kamera Live-Bild</h2>
    
    <img src="{{ url_for('video_feed') }}" alt="Kamera Bild">

    <div class="controls">
        <label for="exposureSlider">Integrationszeit (Wert für die Kamera): <span id="exposureVal">0</span></label><br>
        <input type="range" id="exposureSlider" min="-10" max="10000" value="0" oninput="updateExposure(this.value)">
    </div>

    <button onclick="saveImage()">Bild Speichern</button>
    <p><strong>Speicherort:</strong> {{ save_dir }}</p>
    <p id="status"></p>
</div>

<script>
    // Aktualisiert die Anzeige neben dem Schieberegler und sendet den Wert an Python
    function updateExposure(val) {
        document.getElementById('exposureVal').innerText = val;
        
        let formData = new FormData();
        formData.append('exposure', val);

        fetch('/set_exposure', {
            method: 'POST',
            body: formData
        }).then(response => response.json())
          .then(data => console.log('Exposure set:', data));
    }

    // Sendet den Speicher-Befehl an Python
    function saveImage() {
        fetch('/save_image', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                let statusMsg = document.getElementById('status');
                if(data.success) {
                    statusMsg.style.color = 'green';
                    statusMsg.innerText = data.message;
                } else {
                    statusMsg.style.color = 'red';
                    statusMsg.innerText = "Fehler: " + data.message;
                }
                // Text nach 3 Sekunden verschwinden lassen
                setTimeout(() => statusMsg.innerText = '', 3000);
            });
    }
</script>

</body>
</html>
"""

# --- 4. FLASK ROUTEN ---
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, save_dir=save_directory)

def generate_frames():
    global current_frame
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            current_frame = frame.copy() # Frame für den Speicher-Button merken
            
            # Konvertiere das Bild in das JPEG-Format für den Browser
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            
            # Sende das Bild als "Multipart-Stream" an den Browser
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/set_exposure', methods=['POST'])
def set_exposure():
    exposure_val = float(request.form.get('exposure', 0))
    # Hier setzen wir den Wert über OpenCV. 
    # cv2.CAP_PROP_EXPOSURE ist der Eigenschafts-Code für Belichtungszeit.
    camera.set(cv2.CAP_PROP_EXPOSURE, exposure_val)
    return jsonify(success=True)

@app.route('/save_image', methods=['POST'])
def save_image():
    global current_frame
    if current_frame is not None:
        # Aktuelles Datum und Uhrzeit formatieren
        now = datetime.datetime.now()
        filename = now.strftime("%Y-%m-%d_%H-%M-%S") + ".jpg"
        filepath = os.path.join(save_directory, filename)
        
        # Bild auf der Festplatte speichern
        cv2.imwrite(filepath, current_frame)
        return jsonify(success=True, message=f"Gespeichert: {filename}")
    
    return jsonify(success=False, message="Kamera sendet kein Bild")

if __name__ == '__main__':
    print(f"Starte Server... Speicherort ist: {save_directory}")
    print("Öffne deinen Browser und gehe auf: http://127.0.0.1:5000")
    # Starte den Webserver auf Port 5000
    app.run(host='0.0.0.0', port=5000, debug=False)