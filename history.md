# History

Dieses Dokument wird **immer nur erweitert (append-only)**. Bestehende Einträge werden nicht gelöscht oder verändert, auch wenn sie später überholt sind.

## 2026-08-19 — Vereinheitlichung zu generischer Kamera-Dashboard-Architektur

- Ausgangslage: Drei separate Skripte für drei Kameras, jedes mit eigener Initialisierung und eigener GUI:
  - `camera_dashboard.py` / `camera_dashboard_Alliedvision.py` (Allied Vision Alvium via `vmbpy`, Tkinter-GUI)
  - `Any_Cam_USB_WEBCAM-BROWSER.py` (generische USB-Webcam via OpenCV, Flask-Browser-GUI)
  - `USB_OLDLiMi_Cam.py` (ältere USB-Kamera via OpenCV/DirectShow, Flask-Browser-GUI mit Histogramm)
- Diese drei Skripte wurden nach `legacy/` verschoben (git-history bleibt erhalten) und dienen nur noch als Referenz.
- Neue Architektur eingeführt:
  - `cameras/base.py`: Abstrakte `CameraDriver`-Schnittstelle (open, close, read_frame, get/set exposure, discover). Das ist die generische API, gegen die die GUI programmiert.
  - `cameras/opencv_driver.py`: Ein generischer Treiber für alle OpenCV/DirectShow-USB-Kameras (ersetzt sowohl `Any_Cam_USB_WEBCAM-BROWSER.py` als auch `USB_OLDLiMi_Cam.py`, da beide technisch identisch sind).
  - `cameras/alliedvision_driver.py`: Treiber für Allied Vision Kameras via `vmbpy`, hält den Streaming-Callback und liefert das letzte Frame.
  - `cameras/registry.py`: Zentrale Registrierung aller Treiber-Klassen. Eine neue Kamera benötigt nur einen neuen Treiber + einen Eintrag hier, die GUI muss nicht angepasst werden.
  - `cameras/imaging.py`: Gemeinsame Bildverarbeitung (Histogramm, JPEG-Encoding).
  - `config.py`: Alle Magic Numbers (Ports, Auflösungen, Belichtungsgrenzen, Zeitkonstanten, Histogramm-Größen etc.) zentral an einem Ort.
  - `app.py`: Eine einzige Flask-basierte Browser-GUI mit Kamera-Dropdown. Das Kamerabild wird im Browser per MJPEG-Stream angezeigt (wie von den bisherigen Flask-Skripten bekannt), zusätzlich mit Live-Histogramm und Belichtungsregler, unabhängig vom gewählten Kameratyp.
  - `templates/index.html`: HTML-Oberfläche der neuen GUI.
- Konvention eingeführt: Jede Funktion bekommt einen einzeiligen `# HEADER: ...`-Kommentar als erste Zeile im Funktionskörper, der den Zweck der Funktion beschreibt. Diese Kommentare dürfen nie entfernt werden (siehe AGENTS.md).
- Code und Kommentare wurden komplett auf Englisch umgestellt (bisherige Skripte waren gemischt Deutsch/Englisch).
- Projekt soll zusätzlich zum bestehenden GitLab-Remote (`origin`, HTW Berlin) auch zu einem neuen GitHub-Repo (`https://github.com/ChristofSchultz81/Kamera-ansteuern`) gepusht werden.
- Fortschritts-Dokumente `handover.md`, `backlog.md` und `handoff.md` neu angelegt.
- Commit `3863a8c` erfolgreich zu `github`-Remote (main-Branch) gepusht.

## 2026-08-19 — Hardware-Test Allied Vision Kamera erfolgreich

- Die Allied-Vision-Kamera war nun physisch angeschlossen. `discover_all_cameras()` fand sie korrekt unter `driver_key='allied_vision'`, `device_id='DEV_1AB22C0301FB'` (zusätzlich wurden vom vmbpy-Discovery mehrere Demo-Geräte `DEV_Cam1/2/3` gemeldet, vermutlich Simulator-Einträge des Treibers/Transportlayers, keine echte Hardware).
- `AlliedVisionCameraDriver` wurde direkt (ohne GUI) gegen die echte Kamera getestet: `open()`, `read_frame()` (Bild 2064×2464, 1 Kanal, uint8), `get_exposure_range()` (27.138 – 200000.0), `get_exposure()` und `close()` funktionieren wie erwartet, kein Hänger beim ordnungsgemäßen Schließen.
- Wichtige Erkenntnis: Wird `open()` durch eine Exception unterbrochen bevor `close()` läuft, bleibt der interne vmbpy-`VmbSystem`-Kontext offen und der Python-Prozess hängt beim Beenden (Hintergrund-Threads werden nicht sauber beendet). Das führt zu einer dauerhaft blockierten Kamera (`VmbError.InUse`) und zu hängenden Terminals. Deshalb muss `driver.close()` beim Testen/Debuggen immer in einem `try/finally` aufgerufen werden; hängende Python-Prozesse müssen ggf. manuell beendet werden (`Stop-Process`), um die Kamera wieder freizugeben.
