import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import time
import os
from datetime import datetime
import cv2
import numpy as np
from PIL import Image, ImageTk, ImageDraw, ImageFont
import mss
import threading
import json
import queue

class HomRecScreen:
    def __init__(self, root):
        self.root = root
        self.root.title("HomRec v1.0 - Screen Recorder")
        self.root.geometry("800x720")
        self.root.configure(bg="#1e1e2e")
        
        # Apply modern theme
        self.setup_styles()
        
        # MSS для захвата экрана
        self.sct = mss.mss()
        
        # Settings
        self.scale_factor = 0.75
        self.output_folder = "recordings"
        self.show_webcam = False
        self.webcam_cap = None
        self.include_audio = False
        self.hotkey_enabled = True
        self.countdown_enabled = True
        
        # Load settings
        self.load_settings()
        
        # Переменные
        self.recording = False
        self.paused = False
        self.out = None
        self.target_fps = 15
        self.actual_fps = 0
        self.frame_count = 0
        self.start_time = 0
        self.last_frame_time = 0
        self.frame_times = []
        self.recording_thread = None
        self.stop_event = threading.Event()
        
        # Frame buffer for smoother recording
        self.frame_buffer = queue.Queue(maxsize=5)
        
        # Точный тайминг для правильной скорости видео
        self.frame_interval = 1.0 / self.target_fps
        self.next_frame_time = 0
        
        # Сжатие кадров
        self.compression_params = [cv2.IMWRITE_JPEG_QUALITY, 70]
        
        # Монитор
        self.monitor_id = 1
        self.update_monitor_info()
        
        # Создаем папки
        os.makedirs(self.output_folder, exist_ok=True)
        
        # Интерфейс
        self.create_widgets()
        
        # Запускаем предпросмотр
        self.update_preview()
        
        # Hotkeys
        self.root.bind('<F9>', lambda e: self.toggle_recording())
        self.root.bind('<F10>', lambda e: self.toggle_pause() if self.recording else None)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.log("HomRec v1.0")
    
    def setup_styles(self):
        """Setup modern UI styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        bg_color = "#1e1e2e"
        fg_color = "#cdd6f4"
        accent_color = "#89b4fa"
        
        style.configure("TFrame", background=bg_color)
        style.configure("TLabel", background=bg_color, foreground=fg_color)
        style.configure("TLabelframe", background=bg_color, foreground=accent_color)
        style.configure("TLabelframe.Label", background=bg_color, foreground=accent_color, font=("Segoe UI", 10, "bold"))
        style.configure("TButton", background="#45475a", foreground=fg_color)
        style.configure("TRadiobutton", background=bg_color, foreground=fg_color)
        style.configure("TCheckbutton", background=bg_color, foreground=fg_color)
    
    def load_settings(self):
        """Load user settings from file"""
        try:
            if os.path.exists("homrec_settings.json"):
                with open("homrec_settings.json", "r") as f:
                    settings = json.load(f)
                    self.output_folder = settings.get("output_folder", "recordings")
                    self.scale_factor = settings.get("scale_factor", 0.75)
        except:
            pass
    
    def save_settings(self):
        """Save user settings to file"""
        settings = {
            "output_folder": self.output_folder,
            "scale_factor": self.scale_factor
        }
        with open("homrec_settings.json", "w") as f:
            json.dump(settings, f)
    
    def update_monitor_info(self):
        """Update monitor information"""
        self.monitor = self.sct.monitors[self.monitor_id]
        self.original_width = self.monitor['width']
        self.original_height = self.monitor['height']
        
        # Уменьшенное разрешение для записи
        self.record_width = int(self.original_width * self.scale_factor)
        self.record_height = int(self.original_height * self.scale_factor)
        
        # Делаем размеры четными
        if self.record_width % 2 != 0:
            self.record_width -= 1
        if self.record_height % 2 != 0:
            self.record_height -= 1
    
    def create_widgets(self):
        # Main container
        main_frame = tk.Frame(self.root, bg="#1e1e2e")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Заголовок с градиентом
        title_frame = tk.Frame(main_frame, bg="#1e1e2e")
        title_frame.pack(pady=(0, 10))
        
        title_label = tk.Label(title_frame, text="HomRec v2.0", 
                font=("Segoe UI", 24, "bold"), bg="#1e1e2e", fg="#89b4fa")
        title_label.pack()
        
        subtitle = tk.Label(title_frame, text="Professional Screen Recording Suite", 
                font=("Segoe UI", 10), bg="#1e1e2e", fg="#a6adc8")
        subtitle.pack()
        
        # Предпросмотр с border
        preview_container = tk.Frame(main_frame, bg="#45475a", relief="flat", bd=2)
        preview_container.pack(pady=5, fill="both", expand=True)
        
        preview_frame = ttk.LabelFrame(preview_container, text="  Live Preview  ")
        preview_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        self.preview_label = tk.Label(preview_frame, bg="#11111b")
        self.preview_label.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Статус бар
        status_frame = tk.Frame(main_frame, bg="#313244", relief="flat")
        status_frame.pack(pady=10, fill="x")
        
        status_left = tk.Frame(status_frame, bg="#313244")
        status_left.pack(side="left", padx=10, pady=5)
        
        self.status_icon = tk.Label(status_left, text="⬤", fg="#f38ba8", bg="#313244", font=("Arial", 16))
        self.status_icon.pack(side="left", padx=(0, 5))
        
        self.status_label = tk.Label(status_left, text="Ready to Record", fg="#cdd6f4", bg="#313244", font=("Segoe UI", 10))
        self.status_label.pack(side="left")
        
        self.time_label = tk.Label(status_frame, text="00:00:00", 
                                   font=("Consolas", 14, "bold"), bg="#313244", fg="#89b4fa")
        self.time_label.pack(side="right", padx=10)
        
        # Control buttons with modern style
        btn_frame = tk.Frame(main_frame, bg="#1e1e2e")
        btn_frame.pack(pady=10)
        
        self.record_btn = tk.Button(btn_frame, text="  ▶  START RECORDING  ", 
                                   command=self.start_with_countdown,
                                   bg="#a6e3a1", fg="#1e1e2e", 
                                   font=("Segoe UI", 11, "bold"),
                                   relief="flat", padx=20, pady=10,
                                   cursor="hand2")
        self.record_btn.pack(side="left", padx=5)
        
        self.pause_btn = tk.Button(btn_frame, text="  ⏸  PAUSE  ", 
                                  command=self.toggle_pause,
                                  bg="#f9e2af", fg="#1e1e2e",
                                  font=("Segoe UI", 10, "bold"),
                                  state="disabled", relief="flat", padx=15, pady=10,
                                  cursor="hand2")
        self.pause_btn.pack(side="left", padx=5)
        
        self.stop_btn = tk.Button(btn_frame, text="  ■  STOP  ", 
                                 command=self.stop_recording,
                                 bg="#f38ba8", fg="#1e1e2e",
                                 font=("Segoe UI", 10, "bold"),
                                 state="disabled", relief="flat", padx=15, pady=10,
                                 cursor="hand2")
        self.stop_btn.pack(side="left", padx=5)
        
        # Settings tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(pady=5, fill="both")
        
        # Tab 1: Performance
        perf_tab = ttk.Frame(notebook)
        notebook.add(perf_tab, text="  ⚡ Performance  ")
        
        modes_frame = tk.Frame(perf_tab, bg="#1e1e2e")
        modes_frame.pack(pady=15)
        
        self.mode_var = tk.StringVar(value="balanced")
        
        modes = [
            ("🚀 Ultra (60 FPS)", "ultra", "#a6e3a1"),
            ("⚡ Turbo (30 FPS)", "turbo", "#89b4fa"),
            ("⚖️  Balanced (15 FPS)", "balanced", "#f9e2af"),
            ("🐢 Eco (8 FPS)", "eco", "#fab387")
        ]
        
        for text, value, color in modes:
            btn = tk.Radiobutton(modes_frame, text=text, 
                          variable=self.mode_var, value=value,
                          command=self.change_mode,
                          bg="#1e1e2e", fg=color, 
                          selectcolor="#313244",
                          font=("Segoe UI", 10),
                          indicatoron=True)
            btn.pack(anchor="w", padx=20, pady=3)
        
        # Quality controls
        quality_frame = ttk.LabelFrame(perf_tab, text="  Quality Settings  ")
        quality_frame.pack(fill="x", padx=20, pady=10)
        
        q_inner = tk.Frame(quality_frame, bg="#1e1e2e")
        q_inner.pack(fill="x", pady=10, padx=10)
        
        tk.Label(q_inner, text="Video Quality:", width=12, anchor="w", bg="#1e1e2e", fg="#cdd6f4").grid(row=0, column=0, sticky="w", pady=5)
        self.quality_var = tk.StringVar(value="70")
        quality_scale = tk.Scale(q_inner, from_=10, to=100, 
                                 orient="horizontal", length=250,
                                 variable=self.quality_var, 
                                 command=self.update_quality,
                                 bg="#313244", fg="#cdd6f4", 
                                 highlightthickness=0, troughcolor="#45475a")
        quality_scale.grid(row=0, column=1, padx=5)
        tk.Label(q_inner, text="% (lower = smaller)", bg="#1e1e2e", fg="#a6adc8", font=("Segoe UI", 8)).grid(row=0, column=2, padx=5)
        
        tk.Label(q_inner, text="Resolution:", width=12, anchor="w", bg="#1e1e2e", fg="#cdd6f4").grid(row=1, column=0, sticky="w", pady=5)
        self.scale_var = tk.StringVar(value="75")
        scale_scale = tk.Scale(q_inner, from_=25, to=100, 
                              orient="horizontal", length=250,
                              variable=self.scale_var,
                              command=self.update_scale,
                              bg="#313244", fg="#cdd6f4",
                              highlightthickness=0, troughcolor="#45475a")
        scale_scale.grid(row=1, column=1, padx=5)
        tk.Label(q_inner, text="% (lower = faster)", bg="#1e1e2e", fg="#a6adc8", font=("Segoe UI", 8)).grid(row=1, column=2, padx=5)
        
        # Tab 2: Advanced
        adv_tab = ttk.Frame(notebook)
        notebook.add(adv_tab, text="  🎯 Advanced  ")
        
        adv_inner = tk.Frame(adv_tab, bg="#1e1e2e")
        adv_inner.pack(fill="both", expand=True, padx=20, pady=15)
        
        # Monitor selection
        mon_frame = ttk.LabelFrame(adv_inner, text="  Monitor Selection  ")
        mon_frame.pack(fill="x", pady=5)
        
        mon_inner = tk.Frame(mon_frame, bg="#1e1e2e")
        mon_inner.pack(pady=10, padx=10)
        
        tk.Label(mon_inner, text="Select Monitor:", bg="#1e1e2e", fg="#cdd6f4").pack(side="left", padx=5)
        
        self.monitor_var = tk.StringVar(value="1")
        monitor_combo = ttk.Combobox(mon_inner, textvariable=self.monitor_var, 
                                     values=[str(i) for i in range(1, len(self.sct.monitors))],
                                     width=10, state="readonly")
        monitor_combo.pack(side="left", padx=5)
        monitor_combo.bind("<<ComboboxSelected>>", lambda e: self.change_monitor())
        
        # Output folder
        folder_frame = ttk.LabelFrame(adv_inner, text="  Output Location  ")
        folder_frame.pack(fill="x", pady=5)
        
        folder_inner = tk.Frame(folder_frame, bg="#1e1e2e")
        folder_inner.pack(pady=10, padx=10)
        
        self.folder_label = tk.Label(folder_inner, text=self.output_folder, 
                                     bg="#313244", fg="#89b4fa", 
                                     relief="flat", padx=10, pady=5,
                                     font=("Consolas", 9))
        self.folder_label.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        tk.Button(folder_inner, text="Browse...", command=self.select_folder,
                 bg="#45475a", fg="#cdd6f4", relief="flat", padx=10).pack(side="left")
        
        # Extra features
        extra_frame = ttk.LabelFrame(adv_inner, text="  Additional Features  ")
        extra_frame.pack(fill="x", pady=5)
        
        extra_inner = tk.Frame(extra_frame, bg="#1e1e2e")
        extra_inner.pack(pady=10, padx=10)
        
        self.countdown_var = tk.BooleanVar(value=True)
        tk.Checkbutton(extra_inner, text="3-second countdown before recording",
                      variable=self.countdown_var, bg="#1e1e2e", fg="#cdd6f4",
                      selectcolor="#313244", font=("Segoe UI", 9)).pack(anchor="w", pady=2)
        
        self.timestamp_var = tk.BooleanVar(value=False)
        tk.Checkbutton(extra_inner, text="Add timestamp overlay to video",
                      variable=self.timestamp_var, bg="#1e1e2e", fg="#cdd6f4",
                      selectcolor="#313244", font=("Segoe UI", 9)).pack(anchor="w", pady=2)
        
        self.cursor_var = tk.BooleanVar(value=False)
        tk.Checkbutton(extra_inner, text="Highlight cursor (yellow circle)",
                      variable=self.cursor_var, bg="#1e1e2e", fg="#cdd6f4",
                      selectcolor="#313244", font=("Segoe UI", 9)).pack(anchor="w", pady=2)
        
        # Tab 3: Info
        info_tab = ttk.Frame(notebook)
        notebook.add(info_tab, text="  ℹ️  Info  ")
        
        info_inner = tk.Frame(info_tab, bg="#1e1e2e")
        info_inner.pack(fill="both", expand=True, padx=20, pady=15)
        
        # Stats
        stats_frame = ttk.LabelFrame(info_inner, text="  Recording Stats  ")
        stats_frame.pack(fill="x", pady=5)
        
        stats_inner = tk.Frame(stats_frame, bg="#1e1e2e")
        stats_inner.pack(pady=10, padx=10, fill="x")
        
        self.fps_label = tk.Label(stats_inner, text="Current FPS: 0", 
                                 bg="#1e1e2e", fg="#89b4fa", font=("Consolas", 10))
        self.fps_label.pack(anchor="w", pady=2)
        
        self.res_label = tk.Label(stats_inner, text=f"Resolution: {self.record_width}x{self.record_height}", 
                                 bg="#1e1e2e", fg="#a6e3a1", font=("Consolas", 10))
        self.res_label.pack(anchor="w", pady=2)
        
        self.size_label = tk.Label(stats_inner, text="Est. size: 0 MB/min", 
                                  bg="#1e1e2e", fg="#f9e2af", font=("Consolas", 10))
        self.size_label.pack(anchor="w", pady=2)
        
        self.file_label = tk.Label(stats_inner, text="Ready to record...", 
                                  bg="#1e1e2e", fg="#a6adc8", font=("Segoe UI", 9))
        self.file_label.pack(anchor="w", pady=2)
        
        # Hotkeys
        hotkey_frame = ttk.LabelFrame(info_inner, text="  Keyboard Shortcuts  ")
        hotkey_frame.pack(fill="x", pady=5)
        
        hotkey_inner = tk.Frame(hotkey_frame, bg="#1e1e2e")
        hotkey_inner.pack(pady=10, padx=10)
        
        hotkeys = [
            ("F9", "Start/Stop Recording"),
            ("F10", "Pause/Resume")
        ]
        
        for key, desc in hotkeys:
            row = tk.Frame(hotkey_inner, bg="#1e1e2e")
            row.pack(fill="x", pady=2)
            tk.Label(row, text=key, bg="#313244", fg="#89b4fa", 
                    font=("Consolas", 9, "bold"), padx=8, pady=2).pack(side="left")
            tk.Label(row, text=desc, bg="#1e1e2e", fg="#cdd6f4", 
                    font=("Segoe UI", 9)).pack(side="left", padx=10)
        
        # Bottom buttons
        bottom_frame = tk.Frame(main_frame, bg="#1e1e2e")
        bottom_frame.pack(pady=5, fill="x")
        
        tk.Button(bottom_frame, text="📁 Open Recordings Folder", 
                 command=self.open_recordings,
                 bg="#45475a", fg="#cdd6f4", relief="flat", 
                 font=("Segoe UI", 9), padx=15, pady=8,
                 cursor="hand2").pack(side="left", padx=5)
        
        tk.Button(bottom_frame, text="⚙️ Save Settings", 
                 command=self.save_settings,
                 bg="#45475a", fg="#cdd6f4", relief="flat",
                 font=("Segoe UI", 9), padx=15, pady=8,
                 cursor="hand2").pack(side="left", padx=5)
        
        # Initial update
        self.update_quality(None)
    
    def change_monitor(self):
        """Change recording monitor"""
        self.monitor_id = int(self.monitor_var.get())
        self.update_monitor_info()
        self.res_label.config(text=f"Resolution: {self.record_width}x{self.record_height}")
    
    def select_folder(self):
        """Select output folder"""
        folder = filedialog.askdirectory(initialdir=self.output_folder)
        if folder:
            self.output_folder = folder
            self.folder_label.config(text=folder)
            os.makedirs(self.output_folder, exist_ok=True)
    
    def open_recordings(self):
        """Open recordings folder"""
        if os.path.exists(self.output_folder):
            os.startfile(self.output_folder)
        else:
            messagebox.showwarning("Warning", "Recordings folder doesn't exist yet!")
    
    def start_with_countdown(self):
        """Start recording with optional countdown"""
        if not self.recording:
            if self.countdown_var.get():
                self.show_countdown()
            else:
                self.start_recording()
        else:
            self.stop_recording()
    
    def show_countdown(self):
        """Show 3-2-1 countdown"""
        countdown_window = tk.Toplevel(self.root)
        countdown_window.title("Starting...")
        countdown_window.geometry("300x150")
        countdown_window.configure(bg="#1e1e2e")
        countdown_window.overrideredirect(True)
        
        # Center window
        countdown_window.update_idletasks()
        x = (countdown_window.winfo_screenwidth() // 2) - 150
        y = (countdown_window.winfo_screenheight() // 2) - 75
        countdown_window.geometry(f"+{x}+{y}")
        
        label = tk.Label(countdown_window, text="3", 
                        font=("Segoe UI", 48, "bold"),
                        bg="#1e1e2e", fg="#a6e3a1")
        label.pack(expand=True)
        
        def countdown(count):
            if count > 0:
                label.config(text=str(count))
                countdown_window.after(1000, lambda: countdown(count - 1))
            else:
                label.config(text="Recording!", fg="#f38ba8")
                countdown_window.after(500, countdown_window.destroy)
                self.start_recording()
        
        countdown(3)
    
    def change_mode(self):
        """Change performance mode"""
        mode = self.mode_var.get()
        if mode == "ultra":
            self.target_fps = 60
            self.quality_var.set("95")
            self.scale_var.set("100")
        elif mode == "turbo":
            self.target_fps = 30
            self.quality_var.set("90")
            self.scale_var.set("100")
        elif mode == "balanced":
            self.target_fps = 15
            self.quality_var.set("70")
            self.scale_var.set("75")
        else:  # eco
            self.target_fps = 8
            self.quality_var.set("50")
            self.scale_var.set("50")
        
        self.frame_interval = 1.0 / self.target_fps
        self.update_quality(None)
    
    def update_quality(self, event):
        """Update compression quality"""
        quality = int(self.quality_var.get())
        self.compression_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
        size_est = self.estimate_file_size()
        self.size_label.config(text=f"Est. size: ~{size_est} MB/min")
    
    def update_scale(self, event):
        """Update resolution scale"""
        self.scale_factor = int(self.scale_var.get()) / 100
        self.update_monitor_info()
        self.res_label.config(text=f"Resolution: {self.record_width}x{self.record_height}")
        self.update_quality(None)
    
    def estimate_file_size(self):
        """Estimate file size in MB per minute"""
        quality_factor = int(self.quality_var.get()) / 100
        bytes_per_min = (self.record_width * self.record_height * 
                        self.target_fps * 60 * 3 * quality_factor * 0.3)
        return int(bytes_per_min / (1024 * 1024))
    
    def update_preview(self):
        """Update live preview with low resolution"""
        try:
            screenshot = self.sct.grab(self.monitor)
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            # Маленький предпросмотр для экономии CPU
            img.thumbnail((500, 300), Image.Resampling.LANCZOS)
            
            # Add recording indicator
            if self.recording:
                draw = ImageDraw.Draw(img)
                if not self.paused:
                    draw.ellipse([10, 10, 30, 30], fill="#f38ba8")
                else:
                    draw.rectangle([10, 10, 30, 30], fill="#f9e2af")
            
            photo = ImageTk.PhotoImage(img)
            self.preview_label.config(image=photo)
            self.preview_label.image = photo
        except:
            pass
        
        # Предпросмотр обновляем реже (10 FPS)
        self.root.after(100, self.update_preview)
    
    def get_fourcc(self):
        """Get optimized codec"""
        return cv2.VideoWriter_fourcc(*'mp4v')
    
    def toggle_recording(self):
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        try:
            # Создаем имя файла
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.filename = f"{self.output_folder}/HomRec_{timestamp}.mp4"
            
            # Создаем VideoWriter с оптимизациями
            fourcc = self.get_fourcc()
            self.out = cv2.VideoWriter(
                self.filename, fourcc, self.target_fps, 
                (self.record_width, self.record_height)
            )
            
            if not self.out.isOpened():
                raise Exception("Cannot create video file")
            
            self.recording = True
            self.paused = False
            self.frame_count = 0
            self.start_time = time.time()
            self.last_frame_time = time.time()
            self.next_frame_time = time.time()
            self.frame_times = []
            self.stop_event.clear()
            
            # Clear frame buffer
            while not self.frame_buffer.empty():
                try:
                    self.frame_buffer.get_nowait()
                except:
                    break
            
            # Обновляем UI
            self.record_btn.config(text="  ⏺  RECORDING  ", bg="#f38ba8")
            self.pause_btn.config(state="normal")
            self.stop_btn.config(state="normal")
            self.status_icon.config(fg="#a6e3a1")
            self.status_label.config(text="Recording in Progress...")
            
            # Запускаем запись в отдельном потоке для стабильности
            self.recording_thread = threading.Thread(target=self.record_loop, daemon=True)
            self.recording_thread.start()
            
            # Запускаем обновление UI
            self.update_recording_stats()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start recording: {str(e)}")
    
    def record_loop(self):
        """Main recording loop running in separate thread"""
        frame_duration = 1.0 / self.target_fps
        expected_frame_time = time.time()
        
        # Pre-compile cursor position getter if needed
        get_cursor = None
        if self.cursor_var.get():
            try:
                import win32api
                get_cursor = win32api.GetCursorPos
            except:
                pass
        
        while self.recording and not self.stop_event.is_set():
            if self.paused:
                time.sleep(0.05)
                expected_frame_time = time.time()  # Reset timing when resuming
                continue
            
            current_time = time.time()
            
            # Wait until it's time for the next frame
            if current_time < expected_frame_time:
                sleep_time = expected_frame_time - current_time
                if sleep_time > 0.001:  # Only sleep if significant time
                    time.sleep(sleep_time * 0.95)  # Sleep 95% of time, busy-wait the rest
                continue
            
            try:
                # Capture frame
                screenshot = self.sct.grab(self.monitor)
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                
                # Resize if needed
                if self.scale_factor < 1.0:
                    frame = cv2.resize(frame, (self.record_width, self.record_height), 
                                     interpolation=cv2.INTER_LINEAR)
                
                # Add cursor highlight (optimized)
                if get_cursor:
                    try:
                        cursor_x, cursor_y = get_cursor()
                        scaled_x = int((cursor_x - self.monitor['left']) * self.scale_factor)
                        scaled_y = int((cursor_y - self.monitor['top']) * self.scale_factor)
                        if 0 <= scaled_x < self.record_width and 0 <= scaled_y < self.record_height:
                            cv2.circle(frame, (scaled_x, scaled_y), 20, (0, 255, 255), 3)
                    except:
                        pass
                
                # Add timestamp (optimized - only if enabled)
                if self.timestamp_var.get():
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cv2.putText(frame, timestamp, (10, 30), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Write frame immediately (no buffering for better sync)
                self.out.write(frame)
                self.frame_count += 1
                
                # Calculate next frame time (critical for correct playback speed)
                expected_frame_time += frame_duration
                
                # If we're falling behind, skip to current time
                if expected_frame_time < current_time - frame_duration:
                    expected_frame_time = current_time
                
                # Track actual performance
                self.last_frame_time = current_time
                
            except Exception as e:
                print(f"Recording error: {e}")
                time.sleep(0.01)
    
    def update_recording_stats(self):
        """Update UI stats during recording"""
        if self.recording:
            try:
                current_time = time.time()
                
                # Calculate actual FPS
                if self.frame_count > 0:
                    elapsed = current_time - self.start_time
                    actual_fps = self.frame_count / elapsed if elapsed > 0 else 0
                    self.fps_label.config(text=f"Current FPS: {actual_fps:.1f} (Target: {self.target_fps})")
                
                # Update timer
                elapsed = current_time - self.start_time
                h = int(elapsed // 3600)
                m = int((elapsed % 3600) // 60)
                s = int(elapsed % 60)
                self.time_label.config(text=f"{h:02d}:{m:02d}:{s:02d}")
                
                # Update file info
                if os.path.exists(self.filename):
                    size = os.path.getsize(self.filename) / (1024 * 1024)
                    self.file_label.config(
                        text=f"Recording: {size:.1f} MB | {self.frame_count} frames")
                
            except Exception as e:
                print(f"Stats update error: {e}")
            
            # Schedule next update (500ms for UI responsiveness)
            self.root.after(500, self.update_recording_stats)
    
    def stop_recording(self):
        self.recording = False
        self.stop_event.set()
        
        # Wait for recording thread to finish (with timeout)
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=2.0)
        
        # Small delay to ensure all frames are written
        time.sleep(0.2)
        
        if self.out:
            self.out.release()
        
        # Обновляем UI
        self.record_btn.config(text="  ▶  START RECORDING  ", bg="#a6e3a1")
        self.pause_btn.config(state="disabled", text="  ⏸  PAUSE  ")
        self.stop_btn.config(state="disabled")
        self.status_icon.config(fg="#f38ba8")
        self.status_label.config(text="Ready to Record")
        self.time_label.config(text="00:00:00")
        
        # Результат
        if self.frame_count > 0 and os.path.exists(self.filename):
            size = os.path.getsize(self.filename) / (1024 * 1024)
            duration = self.frame_count / self.target_fps
            
            self.file_label.config(
                text=f"✅ Saved: {size:.1f} MB | {duration:.1f}s | {self.frame_count} frames")
            
            # Детальная информация
            info = (f"✅ Recording Saved Successfully!\n\n"
                   f"📁 File: {os.path.basename(self.filename)}\n"
                   f"📊 Size: {size:.1f} MB\n"
                   f"🎬 Frames: {self.frame_count}\n"
                   f"⏱️ Duration: {duration:.1f} sec\n"
                   f"📏 Resolution: {self.record_width}x{self.record_height}\n"
                   f"⚡ Target FPS: {self.target_fps}\n"
                   f"📌 Mode: {self.mode_var.get()}\n\n"
                   f"Location: {self.output_folder}")
            
            result = messagebox.askquestion("HomRec v1.0", 
                                          info + "\n\nOpen recordings folder?")
            if result == 'yes':
                self.open_recordings()
        else:
            self.file_label.config(text="❌ Recording Failed")
            messagebox.showerror("Error", "No frames were captured!")
    
    def toggle_pause(self):
        if self.recording:
            self.paused = not self.paused
            if self.paused:
                self.pause_btn.config(text="  ▶  RESUME  ", bg="#a6e3a1")
                self.status_icon.config(fg="#f9e2af")
                self.status_label.config(text="Paused")
            else:
                self.pause_btn.config(text="  ⏸  PAUSE  ", bg="#f9e2af")
                self.status_icon.config(fg="#a6e3a1")
                self.status_label.config(text="Recording in Progress...")
    
    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    
    def on_closing(self):
        if self.recording:
            result = messagebox.askyesno("Warning", 
                                        "Recording in progress! Stop and exit?")
            if result:
                self.stop_recording()
            else:
                return
        
        # Clean up
        self.stop_event.set()
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=1.0)
        
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = HomRecScreen(root)
    root.mainloop()