# USB Kamera Web-Viewer für Windows

Ein Python-Programm zur Anzeige von USB-Kamerabildern im Browser mit Histogramm, Integrationszeit-Regler und Speicherfunktion. Funktioniert auf Windows 10 und Windows 11.

## Features

✅ **Live-Kamerabild** im Browser  
✅ **Histogramm-Anzeige** in Echtzeit  
✅ **Integrationszeit-Regler** (1-100 ms)  
✅ **Bild-Speicherung** mit Zeitstempel  
✅ **Responsives Web-Interface**  
✅ **Windows 10/11 kompatibel**  
✅ **Automatische Speicherort-Abfrage**  

## Installation

### 1. Python-Umgebung vorbereiten

```powershell
# Python 3.8+ erforderlich
python --version

# Virtual Environment erstellen (optional aber empfohlen)
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Abhängigkeiten installieren

```powershell
pip install -r requirements.txt
```

Falls Fehler bei OpenCV auftreten:
```powershell
pip install --upgrade opencv-python
```

## Verwendung

### Start des Programms

```powershell
python camera-web-viewer.py
```

### Ablauf:

1. **Speicherort-Dialog**: Wähle einen Ordner zum Speichern der Bilder
2. **Kamera-Erkennung**: Das Programm sucht verfügbare USB-Kameras
3. **Browser öffnet sich**: Navigiere zu `http://127.0.0.1:5000`

## Bedienung im Browser

| Funktion | Beschreibung |
|----------|-------------|
| **Integrationszeit-Regler** | Passt die Belichtungszeit an (1-100 ms) |
| **Histogramm** | Zeigt Helligkeitsverteilung des Bildes |
| **Bild Speichern** | Speichert aktuelles Frame mit Zeitstempel |
| **Programm Stoppen** | Beendet die Anwendung |

## USB-Kamera-Unterstützung

Das Programm nutzt OpenCV (`cv2.VideoCapture`) und sucht automatisch nach verfügbaren Kameras.

### Getestete Kameras:
- USB-Webcams (Standard Windows-Treiber)
- Industriekameras mit USB-UVC-Protokoll

### Die DeviceID `USB\VID_0547&PID_1236`

Diese wird vom Betriebssystem automatisch verwaltet. Das Programm:
- Sucht alle verfügbaren Video-Geräte
- Versucht, eine funktionierende Kamera zu verbinden
- Nutzt die erste gefundene Kamera

Falls mehrere Kameras angeschlossen sind, wird die erste verwendete Kamera genutzt.

## Troubleshooting

### "Keine Kamera gefunden"
```
✓ USB-Kabel überprüfen
✓ Treiber in Geräte-Manager prüfen
✓ Andere USB-Ports testen
✓ Kamera in Windows-Kamera-App testen
```

### Schlechte Bildqualität
- Regler "Integrationszeit" erhöhen
- Licht verbessern
- Kamera näher an Objekt rücken

### Port 5000 belegt
```powershell
# Andere Anwendung beenden oder:
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

## Dateistruktur

```
camera-web-viewer.py          # Hauptprogramm
requirements.txt              # Python-Abhängigkeiten
README_KAMERA.md              # Diese Datei
```

## Speicherpfade

Bilder werden mit Zeitstempel gespeichert:
```
Speicherpfad/camera_20241219_143022_456.jpg
```

Format: `camera_YYYYMMDD_HHMMSS_ms.jpg`

## Netzwerk-Zugriff

Das Programm läuft standardmäßig auf:
- **Lokal**: `http://127.0.0.1:5000` (nur dieser PC)
- **Netzwerk**: Mit Anpassung auch von anderen PCs erreichbar

Für Netzwerk-Zugriff in `camera-web-viewer.py`:
```python
app.run(host='0.0.0.0', port=5000)  # Alle Netzwerke
```

## Performance-Tipps

- **Frame-Rate**: Standardmäßig 30 FPS
- **Auflösung**: 640x480 (anpassbar im Code)
- **Browser-Refresh**: Alle 500ms

## Lizenz & Quellcode

Dieses Programm ist Open Source und kann frei verwendet werden.

## Support

Bei Problemen:
1. Fenster des Programms überprüfen (Fehlermeldungen)
2. Browser-Konsole öffnen (F12) für JavaScript-Fehler
3. `requirements.txt` erneut installieren

---

**Entwickelt für**: Windows 10 & 11  
**Python-Version**: 3.8+  
**Letzte Aktualisierung**: 2024
