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

## 2026-08-19 — Bugfix: schwarzes Bild im Browser bei der Allied-Vision-Kamera

- Fehlerbild: Kamera wurde im Dropdown korrekt erkannt, aber das Live-Bild im Browser blieb schwarz.
- Ursache 1: `create_histogram()` in `cameras/imaging.py` behandelte Frames mit Shape `(H, W, 1)` (Mono-Bild der Allied-Vision-Kamera) fälschlich als 3-Kanal-Farbbild und rief `cv2.cvtColor(..., COLOR_BGR2GRAY)` darauf auf, was eine OpenCV-Assertion auslöst und den Stream-Generator in `app.py` zum Abbruch des jeweiligen Frames zwang (kein Bild wurde je gesendet).
- Ursache 2: Selbst ohne Absturz wäre das Histogramm nie neben dem Kamerabild angezeigt worden, da `create_histogram()` eine feste Höhe (`config.HISTOGRAM_HEIGHT` = 150 px) verwendete, während `app.py` Bild und Histogramm nur dann nebeneinander legte (`cv2.hconcat`), wenn beide Bilder exakt gleich hoch waren — bei echten Kameraauflösungen praktisch nie der Fall.
- Fix: `create_histogram()` erkennt jetzt Mono-Frames mit explizitem Einzelkanal (`shape[2] == 1`) korrekt und akzeptiert einen `height`-Parameter, um das Histogramm passend zur Höhe des jeweiligen Kamerabilds zu rendern. Neue Hilfsfunktion `ensure_bgr()` in `cameras/imaging.py` konvertiert Mono-Frames zuverlässig nach BGR, bevor sie mit dem Histogramm zusammengefügt werden. `app.py` nutzt beides jetzt konsistent, wodurch Bild und Histogramm bei jeder Kamera (mono oder Farbe, beliebige Auflösung) zuverlässig nebeneinander im Browser erscheinen.
- Verifiziert mit synthetischen Mono-/Farb-Testbildern und live gegen die echte Allied-Vision-Kamera (Bild + Histogramm werden korrekt kombiniert und als JPEG kodiert).

## 2026-08-19 — Zweite Kamera (Bresser MikroCam SP 5.0) erfolgreich angebunden

- Die MikroCam SP 5.0 war zunächst nur als generisches `WinUSB`-Gerät (PnP-Klasse `USBDevice`) eingebunden und daher für DirectShow/OpenCV unsichtbar (Discovery fand nur die Laptop-Webcam).
- Nach Installation des vom Nutzer bereitgestellten Treibers `BresserDshowMicroSetup.exe` (ein reiner DirectShow-Filter-Treiber, keine vollständige Bedienoberfläche) erscheint die Kamera als zusätzliches DirectShow-Gerät — unser bestehender generischer `OpenCVCameraDriver` erkennt sie automatisch ohne jede Codeanpassung. Das bestätigt das Treiber-Architektur-Konzept in der Praxis.

## 2026-08-19 — Automatisches Öffnen des Browsers und Auto-Shutdown bei geschlossenem Tab

- `app.py` öffnet beim Start automatisch den Standardbrowser mit der Dashboard-URL (`webbrowser.open`, kurze Verzögerung über `threading.Timer`, siehe `config.AUTO_OPEN_BROWSER` / `AUTO_OPEN_BROWSER_DELAY_SECONDS`).
- Der Browser-Tab sendet alle paar Sekunden einen Heartbeat (`POST /api/heartbeat`, Intervall `config.HEARTBEAT_INTERVAL_MS`). Ein Hintergrund-Thread (`_watchdog_loop`) prüft laufend, ob der letzte Heartbeat zu lange her ist (`config.HEARTBEAT_TIMEOUT_SECONDS`); ist das der Fall (Tab/Fenster wurde geschlossen), wird die aktive Kamera sauber geschlossen und der gesamte Prozess beendet (`_shutdown_server`).
- Ein einfacher Seiten-Refresh löst keinen Shutdown aus, da die Toleranzzeit (6s) größer ist als die Zeit bis zum nächsten Heartbeat nach einem Reload.
- Verifiziert mit isolierten Tests: (1) ohne Heartbeats fährt der Server nach ca. 2–3s automatisch herunter, (2) mit laufenden Heartbeats bleibt er aktiv und fährt erst nach Ausbleiben der Heartbeats + Timeout herunter.
