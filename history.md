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

## 2026-08-19 — Ordner `legacy/` in `old/` umbenannt

- Der Ordner mit den drei ursprünglichen Einzel-Kamera-Skripten wurde von `legacy/` in `old/` umbenannt (per `git mv`, Historie bleibt erhalten), auf Wunsch des Nutzers, um veraltete Dateien klarer zu kennzeichnen. Inhalt und Zweck unverändert: reine Referenz, nicht mehr für `app.py` benötigt.

## 2026-08-19 — Prüfung: Treiber der alten Kamera (USB_OLDLiMi_Cam.py) bereits integriert, fehlendes "NO SIGNAL"-Bild ergänzt

- Nutzerfrage: ob der Kamera-Zugriff aus `old/USB_OLDLiMi_Cam.py` noch in `app.py` integriert werden muss. Ergebnis der Analyse: Der eigentliche Treiberzugriff (`cv2.VideoCapture` mit `cv2.CAP_DSHOW`, Auflösung 640x480, Belichtungsbereich -13 bis 0 mit Default -5, 1s Warmup) ist bereits vollständig in `cameras/opencv_driver.py` (`OpenCVCameraDriver`) übernommen — die Werte in `config.py` (`OPENCV_FRAME_WIDTH/HEIGHT`, `OPENCV_EXPOSURE_MIN/MAX/DEFAULT`, `OPENCV_WARMUP_DELAY_SECONDS`) stammen direkt aus diesem Skript. Es war keine neue Integration nötig.
- Einzige noch fehlende Funktionalität aus dem alten Skript war das blaue "KEIN SIGNAL"-Platzhalterbild, das gezeigt wurde, wenn die Kamera (kurzzeitig) keine Frames liefert. Das wurde nun nachgezogen: neue Funktion `create_no_signal_frame()` in `cameras/imaging.py`, genutzt in `app.py`s Streaming-Generator sowohl wenn keine Kamera ausgewählt ist als auch wenn eine ausgewählte Kamera gerade kein Bild liefert. Texte/Farben zentral in `config.py` (`NO_SIGNAL_*`).

## 2026-08-19 — Bresser MikroCam SP 5.0: schwarzes Bild behoben (Verbindungsproblem, kein Software-Fehler) + responsives Videobild

- Fehlerbild: Kamera wurde im Dropdown erkannt, Bild blieb aber schwarz. Diagnose zeigte: Die MikroCam war zeitweise gar nicht mehr per DirectShow/PnP erreichbar (USB-Verbindung instabil bei diesem günstigen Gerät). Nach erneutem Ab-/Anstecken des USB-Kabels und "Refresh camera list" hat es funktioniert — kein Fehler im eigenen Code.
- Zusätzlich gewünscht und umgesetzt: Das Kamerabild im Browser (`#videoFeed`) skaliert jetzt responsiv zur Bildschirmgröße/-auflösung (`max-width: 90vw; max-height: 70vh; object-fit: contain` statt fester `min-height`), unabhängig von der nativen Auflösung der jeweiligen Kamera.

## 2026-09-18 — Python-3.14.6-Kompatibilität der Abhängigkeiten

- Die festgepinnten Versionen `numpy==1.24.3`, `opencv-python==4.8.1.78`, `Flask==2.3.3`, `Pillow==10.0.0` und `Werkzeug==2.3.7` wurden durch Python-3.14-fähige Versionsbereiche ersetzt.
- Verifiziert: Die Kamera-Abhängigkeiten lösen sich unter Python 3.14.6 vollständig auf, und die zentralen Kamera-Module importieren erfolgreich.

## 2026-09-18 — UVC-Kameras nicht mehr auf DirectShow festgelegt

- Der OpenCV-Treiber verwendete bisher ausschließlich `CAP_DSHOW`. Das konnte UVC-Kameras ausblenden, die unter Windows nur über Media Foundation verfügbar sind.
- Discovery und Öffnen verwenden jetzt `CAP_ANY`, sodass OpenCV das passende Windows-Backend automatisch auswählt.
- Verifiziert: Ein OpenCV-Gerät wurde unter Python 3.14.6 über `MSMF` geöffnet und lieferte erfolgreich einen Frame.

## 2026-09-18 — Pixelabstand im Kamerabild messen

- Die Browseransicht hat jetzt eine Mess-Overlay-Ebene über dem MJPEG-Kamerabild.
- Zwei Klicks im Kamerabild markieren eine Strecke und zeigen deren euklidischen Abstand in nativen Bild-Pixeln an; ein dritter Klick startet eine neue Messung.
- Klicks im angehängten Histogramm werden ignoriert. Die Skalierung des responsiv dargestellten Bildes wird auf die native Kamerabildgröße zurückgerechnet.
- Die Messung kann über einen Reset-Button gelöscht werden und wird beim Wechsel der Kamera automatisch zurückgesetzt.

## 2026-09-18 — Veraltete Dateien aus dem Branch entfernt

- Die vier früheren Einzel-Kamera-Skripte unter `old/` wurden entfernt, da ihre Funktionalität vollständig in der generischen Treiberarchitektur enthalten ist.
- Die veraltete `README_KAMERA.md` wurde ebenfalls entfernt; die aktuelle Dokumentation steht in `README.md`.
- Während der Bereinigung erzeugte lokale Python-Caches wurden gelöscht.

## 2026-09-18 — Mehrere Pixelmessungen im Kamerabild

- Abgeschlossene Messungen bleiben jetzt als Linien mit markierten Punkten und Abstandstext direkt im Kamerabild sichtbar.
- Der Button `Add another pair` startet ein weiteres Punktepaar, ohne vorherige Messungen zu löschen.
- Messungen werden beim Ändern der Fenstergröße aus den nativen Pixelkoordinaten neu auf das Bild skaliert.

## 2026-09-18 — Messannotationen im gespeicherten Bild

- Der Speichervorgang überträgt die nativen Messkoordinaten vom Browser an Flask.
- Punkte, Messlinien und Abstandstexte werden serverseitig in den aufgenommenen Frame gezeichnet, bevor die Bilddatei geschrieben wird.

## 2026-09-21 — Separate UVC-Startdateien für Ubuntu und Windows 11

- Zwei getrennte Startdateien ergänzt: `app_ubuntu.py` verwendet für UVC-USB-Kameras die in Ubuntu integrierte Video4Linux2-Schnittstelle, `app_windows11.py` lässt OpenCV unter Windows 11 den verfügbaren integrierten UVC-Backend (Media Foundation oder DirectShow) auswählen.
- Beide Varianten verwenden die gemeinsame Dashboard-Implementierung aus `app.py`; die Oberfläche und Funktionen bleiben identisch.
- Der Ordnerdialog ist nun optional. Fehlt Tkinter oder eine grafische Sitzung, speichert die Anwendung automatisch unter `~/Downloads` beziehungsweise `%USERPROFILE%\Downloads`. Damit ist unter Ubuntu kein separates Tkinter-Paket für den Start erforderlich.
- Gilt ausschließlich für UVC-konforme Kameras. Spezialkameras wie Allied Vision oder die Bresser MikroCam SP 5.0 benötigen weiterhin den jeweiligen Hersteller-Treiber beziehungsweise das SDK.

## 2026-09-21 — Windows-11-EXE für das Kamera-Dashboard

- PyInstaller-Spezifikation `app_windows11.spec` ergänzt. Sie bündelt den Windows-11-Starter, Python-Laufzeitbibliotheken, OpenCV, Flask und die Browser-Vorlage in einer Windows-Anwendung ohne sichtbares Konsolenfenster.
- Erfolgreich erstellt: `dist\CameraDashboard-Windows11\CameraDashboard-Windows11.exe` inklusive zugehörigem `_internal`-Ordner. Für die Weitergabe muss der gesamte Ordner kopiert werden; Python und die in `requirements.txt` genannten Pakete sind auf dem Ziel-PC nicht nötig.
- Die Bresser MikroCam SP 5.0 benötigt weiterhin den separat installierten signierten Bresser-DirectShow-Treiber. Dieser kann nicht als Bestandteil der Python-Anwendung ersetzt werden.

## 2026-09-21 — Offline-Einzeldatei für die Bresser MikroCam SP 5.0

- Fehleranalyse der ersten EXE anhand von `IMG_9198.JPG`: Der allgemeine Starter importierte den Allied-Vision-Treiber und damit `vmbpy`. Auf dem Bresser-PC fehlte erwartungsgemäß die Vimba-X-Installation, weshalb der Start mit `Expected VmbC to be included with VmbPy` abbrach.
- Neuer Bresser-spezifischer Starter `app_bresser_windows11.py`: Er registriert ausschließlich den OpenCV/DirectShow-Treiber und lädt den Allied-Vision-Treiber nicht.
- Neue PyInstaller-Spezifikation `app_bresser_windows11.spec` erzeugt eine einzelne selbstentpackende Datei: `dist\BresserCameraDashboard-Windows11.exe`. Python, OpenCV, Flask und die Browser-Vorlage sind eingebettet; `vmbpy` und Vimba-Bestandteile sind nicht enthalten.
- Die Bresser-EXE zeigt keinen Ordnerdialog und startet die Browseroberfläche direkt. Aufnahmen werden automatisch unter `%USERPROFILE%\Downloads` gespeichert.
- Weiterhin zwingende Voraussetzung bleibt der separat installierte Bresser-DirectShow-Treiber auf dem Ziel-PC. Für Python oder Internet besteht keine Anforderung.

## 2026-09-21 — DirectShow-Erkennung für die Bresser MikroCam

- Die Bresser-Anwendung verwendete bisher nur `CAP_ANY`. Dadurch konnte OpenCV für die Suche den Media-Foundation-Pfad wählen und die unter DirectShow registrierte MikroCam übersehen, obwohl sie im Windows-Gerätemanager unter Bildverarbeitungsgeräte erscheint.
- Der Bresser-Starter durchsucht jetzt zuerst DirectShow (`CAP_DSHOW`) und danach den allgemeinen Windows-Kamerapfad. Der gewählte Backend-Typ wird in der Geräte-ID gespeichert, sodass eine DirectShow-Kamera beim Öffnen nicht versehentlich über ein anderes Backend angesprochen wird.
- Im Dropdown heißen DirectShow-Treffer `MikroCam candidate / DirectShow camera #...`; allgemeine Kamera-Treffer heißen `USB webcam #...`. Die Kennzeichnung als Kandidat ist bewusst, da OpenCV den exakten Namen aus dem Windows-Gerätemanager nicht übermittelt und auch eine Webcam als DirectShow-Gerät vorkommen kann.

## 2026-09-21 — Zielsystem auf Windows 10 korrigiert

- Der Labor-PC mit der Bresser MikroCam SP 5.0 verwendet Windows 10, nicht Windows 11.
- Dafür wurden `app_bresser_windows10.py` und `app_bresser_windows10.spec` ergänzt und die einzelne Offline-Anwendung `dist\BresserCameraDashboard-Windows10.exe` erstellt.
- Die Windows-10-Variante verwendet weiterhin DirectShow für die Bresser-Erkennung, benötigt kein Internet und enthält die Python-Laufzeit samt Abhängigkeiten.
- Der Bresser-Starter sucht nun die Indizes 0 bis 9 wie der ursprüngliche Bresser-Viewer. Geöffnete DirectShow-Geräte bleiben auch dann auswählbar, wenn sie während des Discovery-Scans noch kein Frame liefern; diese erscheinen mit dem Zusatz `(initializing)` und der Live-Stream wartet nach der Auswahl weiter auf das erste Bild.

## 2026-09-21 — Proprietärer SDK-Zugriff für MikroCamLabII ergänzt

- Die Kennung `USB\VID_0547&PID_1236` stammt aus der vorhandenen Bresser-Notiz und bestätigt, dass die Kamera als proprietäres USB-Gerät statt als UVC-Webcam arbeitet. Dass MikroCamLabII Bilder liefert, beweist daher nicht, dass OpenCV sie als Kameraindex finden kann.
- Neuer Treiber `cameras/bresser_sdk_driver.py` sucht die mit MikroCamLabII installierte `BresserCam.dll` oder `toupcam.dll`, enumeriert darüber die Kameras und liest RGB-Bilder über deren Pull-Mode-API. Dieser Treiber wird in der Bresser-Windows-10-Variante vor dem OpenCV-Rückfallweg registriert.
- Der SDK-Treiber durchsucht übliche Installationsorte sowie die Windows-Uninstall-Registrierung. Bei einer benutzerdefinierten Installation kann der vollständige DLL-Pfad über `BRESSER_CAMERA_SDK_DLL` gesetzt werden.
- Die aktualisierte Datei `dist\BresserCameraDashboard-Windows10.exe` enthält den neuen Treiber. Die Hersteller-DLL selbst wird bewusst vom bereits installierten MikroCamLabII auf dem Labor-PC geladen.
