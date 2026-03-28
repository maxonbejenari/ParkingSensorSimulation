import tkinter as tk
from PIL import Image, ImageTk # load image 
import serial
import serial.tools.list_ports
import threading # reading serial without freeze the window
import os
import time
import pygame.mixer as mixer
import time

# Serial Configuration
SERIAL_PORT = 'AUTO' # aut0 detect port
BAUD_RATE = 9600

# Zone thresholds (cm)
ZONE_RED = 30
ZONE_YELLOW = 100
ZONE_GREEN = 150

# Colors 
BG_DARK     = "#0d0d1a"
BG_CARD     = "#13132b"
BG_CANVAS   = "#0d0d1a"

COLOR_GREEN  = "#00e676"
COLOR_YELLOW = "#ffca28"
COLOR_RED    = "#ff1744"

DIM_GREEN    = "#0a2a0a"
DIM_YELLOW   = "#2a1e00"
DIM_RED      = "#2a0008"

COLOR_TEXT   = "#e8e8f0"
COLOR_MUTED  = "#5a5a7a"

# Car image path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CAR_IMAGE = os.path.join(SCRIPT_DIR, 'car_top_view.png')

def get_zone(distance):
    if distance < ZONE_RED:
        return 'DANGER', COLOR_RED, DIM_RED
    elif distance < ZONE_YELLOW:
        return 'CAUTION', COLOR_YELLOW, DIM_YELLOW
    elif distance <= ZONE_GREEN:
        return 'SAFE', COLOR_GREEN, DIM_GREEN
    else:
        return 'OUT OF RANGE', COLOR_MUTED, BG_CARD

class ParkingApp:
    
    def __init__(self, root):
        self.root = root
        self.distance = 999
        self.ser = None
        self.is_running = True # Control flag for the thread
        mixer.init() # initilaze sound
        
        self.root.title('Parking Sensor')
        self.root.configure(bg=BG_DARK)
        self.root.geometry('500x720')
        self.root.resizable(False,False)
        self.last_beep_time = 0 # generate a short beep sound
        
        # Handle window close event to kill thread safely
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        self._load_car_image()
        self._build_ui()
        self._connect_serial() 

    def _load_car_image(self):
        try:
            img = Image.open(CAR_IMAGE)
            
            car_w = 150
            car_h = int(img.height * (car_w / img.width))
            img = img.resize((car_w, car_h), Image.LANCZOS)
        
            self.car_photo = ImageTk.PhotoImage(img)
            self.car_w = car_w
            self.car_h = car_h
            print("Car image loaded successfully.")
        
        except FileNotFoundError:
            print('CAR PHOTO FILE NOT FOUND. Drawing a simple rectangle instead.')
            self.car_photo = None
            self.car_w = 120
            self.car_h = 240
    
    def _build_ui(self):
        # ── Title ─────────────────────────────
        tk.Label(self.root, text="PARKING SENSOR", bg=BG_DARK, fg=COLOR_TEXT, font=("Courier New", 20, "bold")).pack(pady=(24, 2))
        tk.Label(self.root, text="CH340  ·  HC-SR04", bg=BG_DARK, fg=COLOR_MUTED, font=("Courier New", 9)).pack(pady=(0, 16))

        # ── Distance card ─────────────────────
        self.card = tk.Frame(self.root, bg=BG_CARD)
        self.card.pack(padx=40, pady=(0, 16), fill="x")

        tk.Label(self.card, text="DISTANCE", bg=BG_CARD, fg=COLOR_MUTED, font=("Courier New", 9, "bold")).pack(pady=(12, 0))

        self.lbl_dist = tk.Label(self.card, text="--- cm", bg=BG_CARD, fg=COLOR_GREEN, font=("Courier New", 48, "bold"))
        self.lbl_dist.pack()

        self.lbl_zone = tk.Label(self.card, text="CONNECTING...", bg=BG_CARD, fg=COLOR_MUTED, font=("Courier New", 14, "bold"))
        self.lbl_zone.pack(pady=(0, 12))
        
        # ── Canvas (The Radar) ────────────────
        self.canvas_w = 420
        self.canvas_h = 380

        self.canvas = tk.Canvas(self.root, width=self.canvas_w, height=self.canvas_h, bg=BG_CANVAS, highlightthickness=0)
        self.canvas.pack(pady=(0, 16))

        # Center reference points
        self.cx = self.canvas_w // 2
        self.cy = self.canvas_h - (self.car_h // 2) - 40

        self._draw_scene()

    def _draw_scene(self):
        """Draw statics and dynamic elements on radar."""
        self.canvas.delete("all")

        zone_text, active_color, dim_color = get_zone(self.distance)
        
        # Draw radar
        front_bumper_y = self.cy - (self.car_h // 3)
        
        visual_dist = min(self.distance, 180) 
        arc_radius = int((visual_dist / 150) * 200) + 20

        if self.distance <= ZONE_GREEN:
            # Draw "wave"
            bbox = (self.cx - arc_radius, front_bumper_y - arc_radius, 
                    self.cx + arc_radius, front_bumper_y + arc_radius)
            self.canvas.create_arc(bbox, start=45, extent=90, outline=active_color, width=6, style=tk.ARC)
            
            # Draw radar's shadow
            self.canvas.create_arc(bbox, start=45, extent=90, fill=dim_color, outline="", style=tk.PIESLICE)

        # 3. Draw car
        if self.car_photo:
            self.canvas.create_image(self.cx, self.cy, image=self.car_photo, anchor=tk.CENTER)
        else:
            self.canvas.create_rectangle(self.cx - self.car_w//2, self.cy - self.car_h//2, 
                                         self.cx + self.car_w//2, self.cy + self.car_h//2, 
                                         fill="gray", outline="white")

        if self.distance == 999:
            self.lbl_dist.config(text="--- cm", fg=COLOR_MUTED)
        elif self.distance > ZONE_GREEN:
            self.lbl_dist.config(text=f"{self.distance:.0f} cm", fg=COLOR_MUTED)
        else:
            self.lbl_dist.config(text=f"{self.distance:.0f} cm", fg=active_color)
            
        self.lbl_zone.config(text=zone_text, fg=active_color)
        self.card.config(bg=dim_color if self.distance <= ZONE_GREEN else BG_CARD)
        self.lbl_dist.config(bg=dim_color if self.distance <= ZONE_GREEN else BG_CARD)
        self.lbl_zone.config(bg=dim_color if self.distance <= ZONE_GREEN else BG_CARD)
        
        self.update_audio_feedback()
    
    def update_audio_feedback(self):
        if self.distance > ZONE_GREEN:
            return 

        now = time.time() 
        
        delay = max(0.05, (self.distance / 150.0))
        
        if now - self.last_beep_time >= delay:
            self._play_beep()
            self.last_beep_time = now        
    
    def _play_beep(self):
        mixer.Sound('beep.wav').play()

    # Serial Communication
    def _find_port(self):
        if SERIAL_PORT != 'AUTO':
            return SERIAL_PORT
            
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if "USB" in port.description or "CH340" in port.description or "Serial" in port.description:
                return port.device
        return None

    def _connect_serial(self):
        port_to_use = self._find_port()
        if not port_to_use:
            self.lbl_zone.config(text="NO CH340 FOUND", fg=COLOR_RED)
            return

        try:
            self.ser = serial.Serial(port_to_use, BAUD_RATE, timeout=1)
            time.sleep(2) # wait board reset
            self.lbl_zone.config(text="CONNECTED", fg=COLOR_GREEN)
            
            self.thread = threading.Thread(target=self._read_serial_loop, daemon=True)
            self.thread.start()
            
        except serial.SerialException as e:
            self.lbl_zone.config(text="PORT ACCESS DENIED", fg=COLOR_RED)
            print(f"Error opening serial port: {e}")

    def _read_serial_loop(self):
        while self.is_running and self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8').strip()
                    if line:
                        try:
                            dist = float(line)
                            if dist > 0:
                                self.distance = dist
                                self.root.after(0, self._draw_scene) 
                        except ValueError:
                            pass 
            except Exception as e:
                print(f"Serial read error: {e}")
                time.sleep(1)

    def _on_closing(self):
        self.is_running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.root.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    app = ParkingApp(root)
    root.mainloop()