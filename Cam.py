import cv2
import numpy as np
import tkinter as tk
import os
from datetime import datetime
from PIL import Image, ImageTk
from vmbpy import VmbSystem, FrameStatus

# Globale Variable für das aktuellste Kamerabild
latest_frame = None

def frame_handler(cam, stream, frame):
    """Callback-Funktion: Wird asynchron aufgerufen, sobald ein neues Bild da ist."""
    global latest_frame
    if frame.get_status() == FrameStatus.Complete:
        latest_frame = frame.as_opencv_image().copy()
    cam.queue_frame(frame)

def create_histogram(img):
    """Berechnet das Graustufen-Histogramm."""
    hist = cv2.calcHist([img], [0], None, [256], [0, 256])
    hist_h, hist_w = 150, 256
    hist_canvas = np.zeros((hist_h, hist_w), dtype=np.uint8)
    
    cv2.normalize(hist, hist, 0, hist_h - 1, cv2.NORM_MINMAX)
    
    for i in range(1, 256):
        y1 = int(hist_h - 1 - hist[i - 1][0])
        y2 = int(hist_h - 1 - hist[i][0])
        cv2.line(hist_canvas, (i - 1, y1), (i, y2), 255, 1)
        
    return hist_canvas

def main():
    global latest_frame

    with VmbSystem.get_instance() as vmb:
        cams = vmb.get_all_cameras()
        if not cams:
            print("Keine Kamera gefunden.")
            return

        cam = cams[0]

        with cam:
            print(f"Kamera erfolgreich geöffnet: {cam.get_name()}")

            # 1. Belichtungsfeatures der Alvium auslesen
            try:
                exposure_feature = cam.get_feature_by_name('ExposureTime')
                min_exp, max_exp = exposure_feature.get_range()
                current_exp = exposure_feature.get()
                
                # Begrenzung des Reglers auf max. 200.000 µs (200ms) für feinfühlige Bedienung.
                # Falls Sie längere Belichtungen benötigen, diesen Wert einfach erhöhen!
                if max_exp > 200000:  
                    max_exp = 200000
                    
                print(f"Kamera-Belichtungsbereich für Regler gesetzt auf: {int(min_exp)} µs bis {int(max_exp)} µs")
            except Exception as e:
                print(f"Fehler beim Lesen der Kamera-Features: {e}")
                return

            # 2. Hauptfenster initialisieren
            root = tk.Tk()
            root.title("Allied Vision Alvium - Kamera Dashboard")
            
            screen_w = root.winfo_screenwidth()
            screen_h = root.winfo_screenheight()
            
            target_w = screen_w // 2
            target_h = screen_h // 2

            # Layout-Struktur
            left_frame = tk.Frame(root)
            left_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)

            right_frame = tk.Frame(root)
            right_frame.pack(side=tk.RIGHT, padx=20, pady=10, fill=tk.Y)

            # UI-Elemente Links: Kamerabild
            img_label = tk.Label(left_frame, bg="black")
            img_label.pack(anchor=tk.CENTER, expand=True)

            # UI-Elemente Rechts: Schieberegler (JETZT IN µs)
            def on_slider_move(val):
                # Der 'val'-Wert kommt direkt als µs-String vom Slider
                target_exposure = float(val)
                try:
                    cam.get_feature_by_name('ExposureTime').set(target_exposure)
                except Exception as ex:
                    print(f"Fehler beim Live-Anpassen der Belichtung: {ex}")

            # Der Slider nutzt nun direkt min_exp und max_exp als Grenzen
            slider = tk.Scale(
                right_frame, 
                from_=int(min_exp), 
                to=int(max_exp), 
                orient=tk.HORIZONTAL, 
                label="Integrationszeit (µs)", 
                length=256, 
                command=on_slider_move
            )
            slider.pack(side=tk.TOP, pady=(20, 10))
            
            # Aktuellen Kamera-Wert beim Start auf dem Regler einstellen
            slider.set(int(current_exp))

            # Speicher-Funktion für den Button
            def save_image():
                global latest_frame
                if latest_frame is not None:
                    img_to_save = latest_frame.copy()
                    try:
                        exp_time = cam.get_feature_by_name('ExposureTime').get()
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{timestamp}_{int(exp_time)}us.png"
                        
                        download_dir = r"C:\Users\chris\Downloads"
                        full_path = os.path.join(download_dir, filename)
                        
                        if not os.path.exists(download_dir):
                            os.makedirs(download_dir)
                        
                        success = cv2.imwrite(full_path, img_to_save)
                        if success:
                            print(f"[INFO] Bild erfolgreich gespeichert: {full_path}")
                        else:
                            print(f"[FEHLER] Datei konnte nicht geschrieben werden: {full_path}")
                            
                    except Exception as ex:
                        print(f"[FEHLER] Fehler beim Speichervorgang: {ex}")
                else:
                    print("[WARNUNG] Kein Bild zum Speichern vorhanden.")

            # Speicher-Button
            save_button = tk.Button(
                right_frame, 
                text=" Save", 
                font=("Arial", 11, "bold"),
                command=save_image
            )
            save_button.pack(side=tk.TOP, pady=(10, 30), fill=tk.X)

            # UI-Elemente Rechts unten: Das Histogramm
            hist_title = tk.Label(right_frame, text="Helligkeitsverteilung (Histogramm)", font=("Arial", 10, "bold"))
            hist_title.pack(side=tk.TOP, anchor=tk.W)

            hist_label = tk.Label(right_frame, bg="black")
            hist_label.pack(side=tk.TOP, pady=10)

            # 4. GUI-Update-Schleife
            def update_gui():
                global latest_frame
                if latest_frame is not None:
                    img = latest_frame
                    
                    h, w = img.shape[:2]
                    scale = min(target_w / w, target_h / h)
                    new_w, new_h = int(w * scale), int(h * scale)
                    
                    resized_img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
                    hist_img = create_histogram(resized_img)

                    pil_cam = Image.fromarray(resized_img)
                    tk_cam = ImageTk.PhotoImage(image=pil_cam)
                    img_label.config(image=tk_cam)
                    img_label.image = tk_cam

                    pil_hist = Image.fromarray(hist_img)
                    tk_hist = ImageTk.PhotoImage(image=pil_hist)
                    hist_label.config(image=tk_hist)
                    hist_label.image = tk_hist

                root.after(20, update_gui)

            def on_closing():
                root.quit()
            root.protocol("WM_DELETE_WINDOW", on_closing)

            # 5. Stream und GUI starten
            try:
                cam.start_streaming(handler=frame_handler, buffer_count=5)
                update_gui()
                root.mainloop()
            finally:
                cam.stop_streaming()

if __name__ == '__main__':
    main()