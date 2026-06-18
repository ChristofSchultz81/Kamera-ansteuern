import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
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

class CameraApp:
    def __init__(self, root, cam, min_exp, max_exp, current_exp):
        self.root = root
        self.cam = cam
        
        self.root.title("Allied Vision Alvium - Kamera Dashboard")
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        target_w = screen_w // 2
        target_h = screen_h // 2

        # --- NEU: Ordner abfragen ---
        # Verstecke das Hauptfenster kurz, während der Dialog offen ist
        self.root.withdraw()
        selected_dir = filedialog.askdirectory(title="Bitte Ordner für Bildspeicherung auswählen")
        self.root.deiconify() # Hauptfenster wieder anzeigen
        
        if selected_dir:
            self.save_dir = os.path.normpath(selected_dir)
            print(f"[INFO] Gewählter Speicherpfad: {self.save_dir}")
        else:
            # Fallback, falls der Nutzer den Dialog abbricht
            self.save_dir = os.path.join(os.environ['USERPROFILE'], 'Downloads')
            messagebox.showinfo("Information", f"Kein Ordner ausgewählt. Bilder werden im Standard-Download-Ordner gespeichert:\n{self.save_dir}")

        # Layout-Struktur
        left_frame = tk.Frame(root)
        left_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)

        right_frame = tk.Frame(root)
        right_frame.pack(side=tk.RIGHT, padx=20, pady=10, fill=tk.Y)

        # UI-Elemente Links: Kamerabild
        self.img_label = tk.Label(left_frame, bg="black")
        self.img_label.pack(anchor=tk.CENTER, expand=True)

        # UI-Elemente Rechts: Schieberegler
        def on_slider_move(val):
            try:
                self.cam.get_feature_by_name('ExposureTime').set(float(val))
            except Exception as ex:
                print(f"Fehler beim Live-Anpassen der Belichtung: {ex}")

        self.slider = tk.Scale(
            right_frame, from_=int(min_exp), to=int(max_exp), orient=tk.HORIZONTAL, 
            label="Integrationszeit (µs)", length=256, command=on_slider_move
        )
        self.slider.pack(side=tk.TOP, pady=(20, 10))
        self.slider.set(int(current_exp))

        # Speicher-Button
        save_button = tk.Button(
            right_frame, text="Bild speichern", font=("Arial", 11, "bold"), command=self.save_image
        )
        save_button.pack(side=tk.TOP, pady=(10, 30), fill=tk.X)

        # UI-Elemente Rechts unten: Das Histogramm
        hist_title = tk.Label(right_frame, text="Helligkeitsverteilung (Histogramm)", font=("Arial", 10, "bold"))
        hist_title.pack(side=tk.TOP, anchor=tk.W)

        self.hist_label = tk.Label(right_frame, bg="black")
        self.hist_label.pack(side=tk.TOP, pady=10)

        # GUI-Update-Schleife starten
        self.update_gui(target_w, target_h)

    def save_image(self):
        global latest_frame
        if latest_frame is not None:
            img_to_save = latest_frame.copy()
            try:
                exp_time = self.cam.get_feature_by_name('ExposureTime').get()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{int(exp_time)}us.png"
                full_path = os.path.join(self.save_dir, filename)
                
                success = cv2.imwrite(full_path, img_to_save)
                if success:
                    messagebox.showinfo("Erfolg", f"Bild gespeichert unter:\n{full_path}")
                else:
                    messagebox.showerror("Fehler", f"Datei konnte nicht geschrieben werden:\n{full_path}")
            except Exception as ex:
                print(f"[FEHLER] Speichervorgang fehlgeschlagen: {ex}")
        else:
            messagebox.showwarning("Warnung", "Kein Live-Bild zum Speichern vorhanden.")

    def update_gui(self, target_w, target_h):
        global latest_frame
        if latest_frame is not None:
            img = latest_frame
            h, w = img.shape[:2]
            scale = min(target_w / w, target_h / h)
            new_w, new_h = int(w * scale), int(h * scale)
            
            resized_img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
            hist_img = create_histogram(resized_img)

            pil_cam = Image.fromarray(resized_img)
            self.tk_cam = ImageTk.PhotoImage(image=pil_cam)
            self.img_label.config(image=self.tk_cam)

            pil_hist = Image.fromarray(hist_img)
            self.tk_hist = ImageTk.PhotoImage(image=pil_hist)
            self.hist_label.config(image=self.tk_hist)

        self.root.after(20, lambda: self.update_gui(target_w, target_h))

def main():
    with VmbSystem.get_instance() as vmb:
        cams = vmb.get_all_cameras()
        if not cams:
            root_error = tk.Tk()
            root_error.withdraw()
            messagebox.showerror("Fehler", "Keine Kamera gefunden. Bitte USB-Verbindung prüfen.")
            return

        cam = cams[0]
        with cam:
            try:
                exposure_feature = cam.get_feature_by_name('ExposureTime')
                min_exp, max_exp = exposure_feature.get_range()
                current_exp = exposure_feature.get()
                if max_exp > 200000:  
                    max_exp = 200000
            except Exception as e:
                print(f"Fehler beim Lesen der Kamera-Features: {e}")
                return

            root = tk.Tk()
            app = CameraApp(root, cam, min_exp, max_exp, current_exp)

            def on_closing():
                root.quit()
            root.protocol("WM_DELETE_WINDOW", on_closing)

            try:
                cam.start_streaming(handler=frame_handler, buffer_count=5)
                root.mainloop()
            finally:
                cam.stop_streaming()

if __name__ == '__main__':
    main()