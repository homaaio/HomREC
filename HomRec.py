import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import time
import os
from datetime import datetime
import cv2
import numpy as np
from PIL import Image, ImageTk, ImageDraw
import mss
import threading
import json
import ctypes
import sys

class HomRecScreen:
    def __init__(self, root):
        self.root = root
        self.root.title("HomRec v1.0.2 - Screen Recorder")
        self.root.geometry("1000x700")
        self.root.minsize(900, 600)
        
        # Set application icon (Windows)
        self.set_app_icon()
        
        # Theme settings
        self.current_theme = "dark"  # dark or light
        self.colors = self.get_theme_colors("dark")
        
        # Apply theme
        self.apply_theme()
        
        # MSS для захвата экрана
        self.sct = mss.mss()
        
        # Settings
        self.scale_factor = 0.75
        self.output_folder = "recordings"
        self.quality = 70
        self.target_fps = 15
        self.recording_mode = "balanced"
        
        # Preview size (будет адаптироваться)
        self.preview_width = 640
        self.preview_height = 360
        
        # Load settings
        self.load_settings()
        
        # Recording variables
        self.recording = False
        self.paused = False
        self.out = None
        self.frame_count = 0
        self.start_time = 0
        self.recording_thread = None
        self.stop_flag = False
        
        # Monitor
        self.monitor_id = 1
        self.update_monitor_info()
        
        # Create folders
        os.makedirs(self.output_folder, exist_ok=True)
        
        # Create menu bar
        self.create_menu()
        
        # UI
        self.create_widgets()
        
        # Start preview
        self.update_preview()
        
        # Bind resize event
        self.root.bind('<Configure>', self.on_window_resize)
        
        # Hotkeys
        self.root.bind('<F9>', lambda e: self.toggle_recording())
        self.root.bind('<F10>', lambda e: self.toggle_pause() if self.recording else None)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        print(f"[HomRec v1.0.2] Started successfully")
    
    def set_app_icon(self):
        """Set application icon to camera instead of feather"""
        try:
            # Create a simple camera icon using PIL
            icon_size = (64, 64)
            icon_image = Image.new('RGBA', icon_size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(icon_image)
            
            # Draw camera body
            draw.rectangle([10, 20, 54, 44], fill="#89b4fa", outline="#cdd6f4", width=2)
            # Draw lens
            draw.ellipse([25, 25, 39, 39], fill="#1e1e2e", outline="#cdd6f4", width=2)
            # Draw lens inner
            draw.ellipse([29, 29, 35, 35], fill="#89b4fa")
            # Draw flash
            draw.rectangle([45, 15, 50, 20], fill="#f9e2af")
            
            # Convert to PhotoImage and set as icon
            icon_photo = ImageTk.PhotoImage(icon_image)
            self.root.iconphoto(True, icon_photo)
            
            # Also set for Windows taskbar
            if sys.platform == "win32":
                # Set the app ID for Windows taskbar
                myappid = 'homrec.screen.recorder.v1.0.2'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
                
        except Exception as e:
            print(f"Could not set icon: {e}")
    
    def on_window_resize(self, event):
        """Handle window resize to adjust preview size"""
        if event.widget == self.root:
            # Обновляем размер предпросмотра при изменении окна
            self.update_preview_size()
    
    def update_preview_size(self):
        """Update preview size based on window size"""
        try:
            # Получаем доступное пространство для предпросмотра
            right_panel_width = self.root.winfo_width() - 220  # 200px для левой панели + отступы
            right_panel_height = self.root.winfo_height() - 200  # Высота минус панели настроек
            
            # Вычисляем оптимальный размер предпросмотра (сохраняя пропорции 16:9)
            if right_panel_width > 0 and right_panel_height > 0:
                preview_w = min(right_panel_width - 40, 1280)  # Не больше 1280px
                preview_h = int(preview_w * 9 / 16)
                
                # Если слишком высоко для окна, подгоняем по высоте
                if preview_h > right_panel_height - 60:
                    preview_h = right_panel_height - 60
                    preview_w = int(preview_h * 16 / 9)
                
                self.preview_width = max(400, preview_w)  # Минимум 400px
                self.preview_height = max(225, preview_h)  # Минимум 225px
        except:
            pass
    
    def get_theme_colors(self, theme):
        """Get color scheme for theme"""
        if theme == "dark":
            return {
                "bg": "#1e1e2e",
                "fg": "#cdd6f4",
                "accent": "#89b4fa",
                "success": "#a6e3a1",
                "warning": "#f9e2af",
                "error": "#f38ba8",
                "surface": "#313244",
                "surface_light": "#45475a",
                "preview_bg": "#11111b",
                "text": "#cdd6f4",
                "text_secondary": "#a6adc8"
            }
        else:  # light theme
            return {
                "bg": "#f5f5f5",
                "fg": "#2c3e50",
                "accent": "#3498db",
                "success": "#27ae60",
                "warning": "#f39c12",
                "error": "#e74c3c",
                "surface": "#ecf0f1",
                "surface_light": "#bdc3c7",
                "preview_bg": "#ffffff",
                "text": "#2c3e50",
                "text_secondary": "#7f8c8d"
            }
    
    def apply_theme(self):
        """Apply current theme to root window"""
        self.root.configure(bg=self.colors["bg"])
        
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure("TFrame", background=self.colors["bg"])
        style.configure("TLabel", background=self.colors["bg"], foreground=self.colors["fg"])
        style.configure("TLabelframe", background=self.colors["bg"], foreground=self.colors["accent"])
        style.configure("TLabelframe.Label", background=self.colors["bg"], foreground=self.colors["accent"])
        style.configure("TButton", background=self.colors["surface"], foreground=self.colors["fg"])
        style.configure("TRadiobutton", background=self.colors["bg"], foreground=self.colors["fg"])
        style.configure("TCheckbutton", background=self.colors["bg"], foreground=self.colors["fg"])
        style.configure("TCombobox", fieldbackground=self.colors["surface"], foreground=self.colors["fg"])
        style.configure("TMenu", background=self.colors["surface"], foreground=self.colors["fg"])
    
    def create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root, bg=self.colors["surface"], fg=self.colors["fg"])
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0, bg=self.colors["surface"], fg=self.colors["fg"])
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Recordings Folder", command=self.open_recordings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0, bg=self.colors["surface"], fg=self.colors["fg"])
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Change Output Folder", command=self.select_folder)
        settings_menu.add_command(label="Save Settings", command=self.save_settings)
        settings_menu.add_separator()
        
        # Theme submenu
        theme_menu = tk.Menu(settings_menu, tearoff=0, bg=self.colors["surface"], fg=self.colors["fg"])
        settings_menu.add_cascade(label="Theme", menu=theme_menu)
        theme_menu.add_command(label="🌙 Dark Theme", command=lambda: self.change_theme("dark"))
        theme_menu.add_command(label="☀️ Light Theme", command=lambda: self.change_theme("light"))
        
        # Performance submenu
        perf_menu = tk.Menu(settings_menu, tearoff=0, bg=self.colors["surface"], fg=self.colors["fg"])
        settings_menu.add_cascade(label="Performance Mode", menu=perf_menu)
        perf_menu.add_command(label="🚀 Ultra (60 FPS)", command=lambda: self.set_mode("ultra"))
        perf_menu.add_command(label="⚡ Turbo (30 FPS)", command=lambda: self.set_mode("turbo"))
        perf_menu.add_command(label="⚖️ Balanced (15 FPS)", command=lambda: self.set_mode("balanced"))
        perf_menu.add_command(label="🐢 Eco (8 FPS)", command=lambda: self.set_mode("eco"))
    
    def change_theme(self, theme):
        """Change application theme - no message box"""
        self.current_theme = theme
        self.colors = self.get_theme_colors(theme)
        self.apply_theme()
        self.recreate_widgets()
        # Автоматически сохраняем настройки без сообщения
        self.save_settings(silent=True)
    
    def recreate_widgets(self):
        """Recreate all widgets after theme change"""
        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Recreate menu and widgets
        self.create_menu()
        self.create_widgets()
    
    def set_mode(self, mode):
        """Set performance mode from menu"""
        self.recording_mode = mode
        self.update_mode_settings()
        if hasattr(self, 'mode_var'):
            self.mode_var.set(mode)
    
    def update_mode_settings(self):
        """Update settings based on mode"""
        if self.recording_mode == "ultra":
            self.target_fps = 60
            self.quality = 95
            self.scale_factor = 1.0
        elif self.recording_mode == "turbo":
            self.target_fps = 30
            self.quality = 90
            self.scale_factor = 1.0
        elif self.recording_mode == "balanced":
            self.target_fps = 15
            self.quality = 70
            self.scale_factor = 0.75
        else:  # eco
            self.target_fps = 8
            self.quality = 50
            self.scale_factor = 0.5
        
        self.update_monitor_info()
    
    def load_settings(self):
        """Load user settings"""
        try:
            if os.path.exists("homrec_settings.json"):
                with open("homrec_settings.json", "r") as f:
                    settings = json.load(f)
                    self.output_folder = settings.get("output_folder", "recordings")
                    self.scale_factor = settings.get("scale_factor", 0.75)
                    self.target_fps = settings.get("target_fps", 15)
                    self.quality = settings.get("quality", 70)
                    self.recording_mode = settings.get("mode", "balanced")
                    self.current_theme = settings.get("theme", "dark")
        except:
            pass
    
    def save_settings(self, silent=False):
        """Save user settings - optional silent mode"""
        settings = {
            "output_folder": self.output_folder,
            "scale_factor": self.scale_factor,
            "target_fps": self.target_fps,
            "quality": self.quality,
            "mode": self.recording_mode,
            "theme": self.current_theme
        }
        with open("homrec_settings.json", "w") as f:
            json.dump(settings, f, indent=2)
        
        # Only show message if not silent
        if not silent:
            messagebox.showinfo("Settings", "Settings saved successfully!\n😘 Made by Homa4ella")
    
    def update_monitor_info(self):
        """Update monitor information"""
        self.monitor = self.sct.monitors[self.monitor_id]
        self.original_width = self.monitor['width']
        self.original_height = self.monitor['height']
        
        # Scaled resolution
        self.record_width = int(self.original_width * self.scale_factor)
        self.record_height = int(self.original_height * self.scale_factor)
        
        # Make even
        if self.record_width % 2 != 0:
            self.record_width -= 1
        if self.record_height % 2 != 0:
            self.record_height -= 1
    
    def create_widgets(self):
        # Main container - horizontal layout
        main_container = tk.Frame(self.root, bg=self.colors["bg"])
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left panel - Controls (фиксированная ширина)
        left_panel = tk.Frame(main_container, bg=self.colors["surface"], width=200)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Title in left panel
        title_frame = tk.Frame(left_panel, bg=self.colors["surface"])
        title_frame.pack(pady=15, fill="x")
        
        tk.Label(title_frame, text="HomRec", 
                font=("Segoe UI", 20, "bold"), 
                bg=self.colors["surface"], 
                fg=self.colors["accent"]).pack()
        
        tk.Label(title_frame, text="v1.0.2", 
                font=("Segoe UI", 10), 
                bg=self.colors["surface"], 
                fg=self.colors["text_secondary"]).pack()
        
        # Control buttons
        btn_frame = tk.Frame(left_panel, bg=self.colors["surface"])
        btn_frame.pack(pady=20, padx=10, fill="x")
        
        self.record_btn = tk.Button(btn_frame, text="▶ START", 
                                   command=self.start_with_countdown,
                                   bg=self.colors["success"], fg=self.colors["bg"],
                                   font=("Segoe UI", 12, "bold"),
                                   relief="flat", height=2,
                                   cursor="hand2")
        self.record_btn.pack(fill="x", pady=5)
        
        self.pause_btn = tk.Button(btn_frame, text="⏸ PAUSE", 
                                  command=self.toggle_pause,
                                  bg=self.colors["warning"], fg=self.colors["bg"],
                                  font=("Segoe UI", 12, "bold"),
                                  state="disabled", relief="flat", height=2,
                                  cursor="hand2")
        self.pause_btn.pack(fill="x", pady=5)
        
        self.stop_btn = tk.Button(btn_frame, text="■ STOP", 
                                 command=self.stop_recording,
                                 bg=self.colors["error"], fg=self.colors["bg"],
                                 font=("Segoe UI", 12, "bold"),
                                 state="disabled", relief="flat", height=2,
                                 cursor="hand2")
        self.stop_btn.pack(fill="x", pady=5)
        
        # Status in left panel
        status_frame = tk.Frame(left_panel, bg=self.colors["surface"])
        status_frame.pack(pady=20, padx=10, fill="x")
        
        tk.Label(status_frame, text="STATUS", 
                font=("Segoe UI", 10, "bold"),
                bg=self.colors["surface"], 
                fg=self.colors["accent"]).pack(anchor="w")
        
        status_row = tk.Frame(status_frame, bg=self.colors["surface"])
        status_row.pack(fill="x", pady=5)
        
        self.status_icon = tk.Label(status_row, text="⬤", 
                                   fg=self.colors["error"], 
                                   bg=self.colors["surface"], 
                                   font=("Arial", 16))
        self.status_icon.pack(side="left", padx=(0, 5))
        
        self.status_label = tk.Label(status_row, text="Ready", 
                                    bg=self.colors["surface"], 
                                    fg=self.colors["text"])
        self.status_label.pack(side="left")
        
        # Timer
        timer_frame = tk.Frame(left_panel, bg=self.colors["surface"])
        timer_frame.pack(pady=10, padx=10, fill="x")
        
        tk.Label(timer_frame, text="TIME", 
                font=("Segoe UI", 10, "bold"),
                bg=self.colors["surface"], 
                fg=self.colors["accent"]).pack(anchor="w")
        
        self.time_label = tk.Label(timer_frame, text="00:00:00", 
                                   font=("Consolas", 20, "bold"),
                                   bg=self.colors["surface"], 
                                   fg=self.colors["accent"])
        self.time_label.pack(pady=5)
        
        # Stats
        stats_frame = tk.Frame(left_panel, bg=self.colors["surface"])
        stats_frame.pack(pady=10, padx=10, fill="x")
        
        tk.Label(stats_frame, text="STATS", 
                font=("Segoe UI", 10, "bold"),
                bg=self.colors["surface"], 
                fg=self.colors["accent"]).pack(anchor="w")
        
        self.fps_label = tk.Label(stats_frame, text="FPS: 0", 
                                 bg=self.colors["surface"], 
                                 fg=self.colors["text"],
                                 font=("Consolas", 10))
        self.fps_label.pack(anchor="w", pady=2)
        
        self.res_label = tk.Label(stats_frame, 
                                 text=f"Res: {self.record_width}x{self.record_height}", 
                                 bg=self.colors["surface"], 
                                 fg=self.colors["text"],
                                 font=("Consolas", 10))
        self.res_label.pack(anchor="w", pady=2)
        
        # Right panel - Preview and settings
        right_panel = tk.Frame(main_container, bg=self.colors["bg"])
        right_panel.pack(side="right", fill="both", expand=True)
        
        # Preview container (с возможностью расширения)
        preview_container = tk.Frame(right_panel, bg=self.colors["surface_light"], relief="flat", bd=2)
        preview_container.pack(fill="both", expand=True, pady=(0, 10))
        
        preview_label_title = tk.Label(preview_container, text="LIVE PREVIEW", 
                                      bg=self.colors["surface_light"], 
                                      fg=self.colors["text_secondary"],
                                      font=("Segoe UI", 9))
        preview_label_title.pack(anchor="nw", padx=5, pady=2)
        
        # Frame для предпросмотра с фиксированным соотношением сторон
        preview_frame = tk.Frame(preview_container, bg=self.colors["preview_bg"])
        preview_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.preview_label = tk.Label(preview_frame, bg=self.colors["preview_bg"])
        self.preview_label.pack(fill="both", expand=True)
        
        # Settings panel (фиксированная высота)
        settings_container = tk.Frame(right_panel, bg=self.colors["surface"], height=180)
        settings_container.pack(fill="x")
        settings_container.pack_propagate(False)
        
        # Settings tabs
        notebook = ttk.Notebook(settings_container)
        notebook.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Video Settings Tab
        video_tab = ttk.Frame(notebook)
        notebook.add(video_tab, text="Video Settings")
        
        video_inner = tk.Frame(video_tab, bg=self.colors["bg"])
        video_inner.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Quality control
        quality_frame = tk.Frame(video_inner, bg=self.colors["bg"])
        quality_frame.pack(fill="x", pady=5)
        
        tk.Label(quality_frame, text="Quality:", 
                bg=self.colors["bg"], 
                fg=self.colors["text"],
                width=10, anchor="w").pack(side="left")
        
        self.quality_var = tk.StringVar(value=str(self.quality))
        quality_scale = tk.Scale(quality_frame, from_=10, to=100, 
                                 orient="horizontal", length=250,
                                 variable=self.quality_var, 
                                 command=self.update_quality,
                                 bg=self.colors["surface"], 
                                 fg=self.colors["text"],
                                 highlightthickness=0, 
                                 troughcolor=self.colors["surface_light"])
        quality_scale.pack(side="left", padx=5)
        
        tk.Label(quality_frame, text="%", 
                bg=self.colors["bg"], 
                fg=self.colors["text_secondary"]).pack(side="left")
        
        # Resolution control
        res_frame = tk.Frame(video_inner, bg=self.colors["bg"])
        res_frame.pack(fill="x", pady=5)
        
        tk.Label(res_frame, text="Resolution:", 
                bg=self.colors["bg"], 
                fg=self.colors["text"],
                width=10, anchor="w").pack(side="left")
        
        self.scale_var = tk.StringVar(value=str(int(self.scale_factor * 100)))
        scale_scale = tk.Scale(res_frame, from_=25, to=100, 
                              orient="horizontal", length=250,
                              variable=self.scale_var,
                              command=self.update_scale,
                              bg=self.colors["surface"], 
                              fg=self.colors["text"],
                              highlightthickness=0,
                              troughcolor=self.colors["surface_light"])
        scale_scale.pack(side="left", padx=5)
        
        tk.Label(res_frame, text="%", 
                bg=self.colors["bg"], 
                fg=self.colors["text_secondary"]).pack(side="left")
        
        # Performance mode
        mode_frame = tk.Frame(video_inner, bg=self.colors["bg"])
        mode_frame.pack(fill="x", pady=10)
        
        tk.Label(mode_frame, text="Mode:", 
                bg=self.colors["bg"], 
                fg=self.colors["text"],
                width=10, anchor="w").pack(side="left")
        
        self.mode_var = tk.StringVar(value=self.recording_mode)
        mode_combo = ttk.Combobox(mode_frame, textvariable=self.mode_var,
                                  values=["ultra", "turbo", "balanced", "eco"],
                                  width=15, state="readonly")
        mode_combo.pack(side="left", padx=5)
        mode_combo.bind("<<ComboboxSelected>>", self.on_mode_change)
        
        # Advanced Settings Tab
        adv_tab = ttk.Frame(notebook)
        notebook.add(adv_tab, text="Advanced")
        
        adv_inner = tk.Frame(adv_tab, bg=self.colors["bg"])
        adv_inner.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Monitor selection
        mon_frame = tk.Frame(adv_inner, bg=self.colors["bg"])
        mon_frame.pack(fill="x", pady=5)
        
        tk.Label(mon_frame, text="Monitor:", 
                bg=self.colors["bg"], 
                fg=self.colors["text"],
                width=10, anchor="w").pack(side="left")
        
        self.monitor_var = tk.StringVar(value=str(self.monitor_id))
        monitor_combo = ttk.Combobox(mon_frame, textvariable=self.monitor_var,
                                     values=[str(i) for i in range(1, len(self.sct.monitors))],
                                     width=10, state="readonly")
        monitor_combo.pack(side="left", padx=5)
        monitor_combo.bind("<<ComboboxSelected>>", lambda e: self.change_monitor())
        
        # Output folder
        folder_frame = tk.Frame(adv_inner, bg=self.colors["bg"])
        folder_frame.pack(fill="x", pady=5)
        
        tk.Label(folder_frame, text="Output:", 
                bg=self.colors["bg"], 
                fg=self.colors["text"],
                width=10, anchor="w").pack(side="left")
        
        self.folder_label = tk.Label(folder_frame, text=os.path.basename(self.output_folder), 
                                     bg=self.colors["surface"], 
                                     fg=self.colors["accent"],
                                     relief="flat", padx=5, pady=2)
        self.folder_label.pack(side="left", padx=5)
        
        tk.Button(folder_frame, text="Browse", command=self.select_folder,
                 bg=self.colors["surface"], 
                 fg=self.colors["text"],
                 relief="flat", padx=10).pack(side="left", padx=5)
        
        # Features
        features_frame = tk.Frame(adv_inner, bg=self.colors["bg"])
        features_frame.pack(fill="x", pady=10)
        
        self.countdown_var = tk.BooleanVar(value=True)
        tk.Checkbutton(features_frame, text="Countdown (3 sec)",
                      variable=self.countdown_var,
                      bg=self.colors["bg"], 
                      fg=self.colors["text"],
                      selectcolor=self.colors["surface"]).pack(anchor="w", pady=2)
        
        self.timestamp_var = tk.BooleanVar(value=False)
        tk.Checkbutton(features_frame, text="Add timestamp",
                      variable=self.timestamp_var,
                      bg=self.colors["bg"], 
                      fg=self.colors["text"],
                      selectcolor=self.colors["surface"]).pack(anchor="w", pady=2)
        
        self.cursor_var = tk.BooleanVar(value=False)
        tk.Checkbutton(features_frame, text="Highlight cursor",
                      variable=self.cursor_var,
                      bg=self.colors["bg"], 
                      fg=self.colors["text"],
                      selectcolor=self.colors["surface"]).pack(anchor="w", pady=2)
        
        # Bottom bar
        bottom_bar = tk.Frame(self.root, bg=self.colors["surface"], height=30)
        bottom_bar.pack(side="bottom", fill="x")
        
        self.file_label = tk.Label(bottom_bar, text="Ready to record...", 
                                   bg=self.colors["surface"], 
                                   fg=self.colors["text_secondary"])
        self.file_label.pack(side="left", padx=10)
        
        tk.Label(bottom_bar, text="😘 Homa4ella", 
                bg=self.colors["surface"], 
                fg=self.colors["accent"]).pack(side="right", padx=10)
        
        # Initial update
        self.update_quality(None)
        self.update_preview_size()
    
    def on_mode_change(self, event=None):
        """Handle mode change from combobox"""
        self.recording_mode = self.mode_var.get()
        self.update_mode_settings()
        self.scale_var.set(str(int(self.scale_factor * 100)))
        self.quality_var.set(str(self.quality))
        self.update_quality(None)
        self.res_label.config(text=f"Res: {self.record_width}x{self.record_height}")
    
    def change_monitor(self):
        """Change recording monitor"""
        self.monitor_id = int(self.monitor_var.get())
        self.update_monitor_info()
        self.res_label.config(text=f"Res: {self.record_width}x{self.record_height}")
    
    def select_folder(self):
        """Select output folder"""
        folder = filedialog.askdirectory(initialdir=self.output_folder)
        if folder:
            self.output_folder = folder
            self.folder_label.config(text=os.path.basename(folder))
            os.makedirs(self.output_folder, exist_ok=True)
            self.save_settings()
    
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
        countdown_window.configure(bg=self.colors["bg"])
        countdown_window.overrideredirect(True)
        
        # Center window
        countdown_window.update_idletasks()
        x = (countdown_window.winfo_screenwidth() // 2) - 150
        y = (countdown_window.winfo_screenheight() // 2) - 75
        countdown_window.geometry(f"+{x}+{y}")
        
        label = tk.Label(countdown_window, text="3", 
                        font=("Segoe UI", 48, "bold"),
                        bg=self.colors["bg"], 
                        fg=self.colors["success"])
        label.pack(expand=True)
        
        def countdown(count):
            if count > 0:
                label.config(text=str(count))
                countdown_window.after(1000, lambda: countdown(count - 1))
            else:
                label.config(text="Recording!", fg=self.colors["error"])
                countdown_window.after(500, countdown_window.destroy)
                self.start_recording()
        
        countdown(3)
    
    def update_quality(self, event):
        """Update compression quality"""
        try:
            self.quality = int(self.quality_var.get())
        except:
            pass
    
    def update_scale(self, event):
        """Update resolution scale"""
        try:
            self.scale_factor = int(self.scale_var.get()) / 100
            self.update_monitor_info()
            self.res_label.config(text=f"Res: {self.record_width}x{self.record_height}")
        except:
            pass
    
    def update_preview(self):
        """Update live preview with adaptive size"""
        try:
            screenshot = self.sct.grab(self.monitor)
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            # Используем адаптивный размер предпросмотра
            img.thumbnail((self.preview_width, self.preview_height), Image.Resampling.LANCZOS)
            
            if self.recording:
                draw = ImageDraw.Draw(img)
                if not self.paused:
                    draw.ellipse([10, 10, 30, 30], fill=self.colors["error"])
                else:
                    draw.rectangle([10, 10, 30, 30], fill=self.colors["warning"])
            
            photo = ImageTk.PhotoImage(img)
            self.preview_label.config(image=photo)
            self.preview_label.image = photo
        except Exception as e:
            print(f"Preview error: {e}")
        
        # Adaptive refresh rate
        delay = 200 if self.recording else 100
        self.root.after(delay, self.update_preview)
    
    def toggle_recording(self):
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """Start recording"""
        try:
            # Create filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.filename = f"{self.output_folder}/HomRec_{timestamp}.mp4"
            
            print(f"\n[HomRec] ========== STARTING RECORDING ==========")
            
            # Initialize video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.out = cv2.VideoWriter(
                self.filename, fourcc, self.target_fps, 
                (self.record_width, self.record_height)
            )
            
            if not self.out.isOpened():
                raise Exception("Cannot create video file")
            
            # Reset state
            self.recording = True
            self.paused = False
            self.frame_count = 0
            self.start_time = time.time()
            self.stop_flag = False
            
            # Update UI
            self.record_btn.config(text="⏺ RECORDING", bg=self.colors["error"])
            self.pause_btn.config(state="normal")
            self.stop_btn.config(state="normal")
            self.status_icon.config(fg=self.colors["success"])
            self.status_label.config(text="Recording")
            
            # Start recording thread
            self.recording_thread = threading.Thread(target=self._record_thread, daemon=True)
            self.recording_thread.start()
            
            # Start stats updater
            self._update_stats()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start recording:\n{str(e)}")
    
    def _record_thread(self):
        """Recording thread"""
        sct_local = mss.mss()
        actual_start_time = time.time()
        
        needs_resize = self.scale_factor < 1.0
        add_timestamp = self.timestamp_var.get()
        add_cursor = self.cursor_var.get()
        
        # Get cursor function
        get_cursor = None
        if add_cursor:
            try:
                import win32api
                get_cursor = win32api.GetCursorPos
            except:
                add_cursor = False
        
        while self.recording and not self.stop_flag:
            if self.paused:
                time.sleep(0.05)
                continue
            
            try:
                # Capture screen
                screenshot = sct_local.grab(self.monitor)
                
                # Convert to numpy
                frame = np.frombuffer(screenshot.bgra, dtype=np.uint8)
                frame = frame.reshape(screenshot.height, screenshot.width, 4)
                frame = frame[:, :, :3].copy()
                
                # Resize if needed
                if needs_resize:
                    frame = cv2.resize(frame, (self.record_width, self.record_height), 
                                     interpolation=cv2.INTER_NEAREST)
                
                # Add cursor if enabled
                if add_cursor and get_cursor:
                    try:
                        cx, cy = get_cursor()
                        sx = int((cx - self.monitor['left']) * self.scale_factor)
                        sy = int((cy - self.monitor['top']) * self.scale_factor)
                        if 0 <= sx < self.record_width and 0 <= sy < self.record_height:
                            cv2.circle(frame, (sx, sy), 20, (0, 255, 255), 3)
                    except:
                        pass
                
                # Add timestamp if enabled
                if add_timestamp:
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cv2.putText(frame, ts, (10, 30), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Write frame
                if self.out and self.out.isOpened():
                    self.out.write(frame)
                    self.frame_count += 1
                
                # Control frame rate
                target_time = actual_start_time + (self.frame_count / self.target_fps)
                sleep_time = target_time - time.time()
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
            except Exception as e:
                print(f"[HomRec] Frame error: {e}")
                time.sleep(0.01)
        
        # Clean up
        try:
            sct_local.close()
        except:
            pass
    
    def _update_stats(self):
        """Update recording statistics"""
        if self.recording:
            try:
                elapsed = time.time() - self.start_time
                if elapsed > 0:
                    actual_fps = self.frame_count / elapsed
                    self.fps_label.config(text=f"FPS: {actual_fps:.1f}")
                
                h = int(elapsed // 3600)
                m = int((elapsed % 3600) // 60)
                s = int(elapsed % 60)
                self.time_label.config(text=f"{h:02d}:{m:02d}:{s:02d}")
                
                if os.path.exists(self.filename):
                    size = os.path.getsize(self.filename) / (1024 * 1024)
                    self.file_label.config(text=f"Recording: {size:.1f} MB | {self.frame_count} frames")
            except:
                pass
            
            self.root.after(500, self._update_stats)
    
    def stop_recording(self):
        """Stop recording"""
        self.recording = False
        self.stop_flag = True
        
        # Wait for thread
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=3)
        
        time.sleep(0.3)
        
        # Release video writer
        if self.out:
            try:
                self.out.release()
            except:
                pass
        
        # Update UI
        self.record_btn.config(text="▶ START", bg=self.colors["success"])
        self.pause_btn.config(state="disabled", text="⏸ PAUSE")
        self.stop_btn.config(state="disabled")
        self.status_icon.config(fg=self.colors["error"])
        self.status_label.config(text="Ready")
        self.time_label.config(text="00:00:00")
        
        # Show results
        if self.frame_count > 0 and os.path.exists(self.filename):
            actual_duration = time.time() - self.start_time
            size = os.path.getsize(self.filename) / (1024 * 1024)
            actual_fps = self.frame_count / actual_duration
            
            self.file_label.config(text=f"✅ Saved: {size:.1f} MB | {actual_duration:.1f}s")
            
            info = (f"✅ Recording Saved!\n\n"
                   f"File: {os.path.basename(self.filename)}\n"
                   f"Size: {size:.1f} MB\n"
                   f"Duration: {actual_duration:.1f} sec\n"
                   f"Resolution: {self.record_width}x{self.record_height}\n"
                   f"FPS: {actual_fps:.1f}")
            
            info += f"\n\n😘 Made by Homa4ella (tg: @homaexe)"
            
            result = messagebox.askquestion("HomRec", info + "\n\nOpen folder?")
            if result == 'yes':
                self.open_recordings()
        else:
            self.file_label.config(text="❌ Failed")
            messagebox.showerror("Error", "Recording failed!")
    
    def toggle_pause(self):
        """Pause/resume recording"""
        if self.recording:
            self.paused = not self.paused
            if self.paused:
                self.pause_btn.config(text="▶ RESUME", bg=self.colors["success"])
                self.status_icon.config(fg=self.colors["warning"])
                self.status_label.config(text="Paused")
            else:
                self.pause_btn.config(text="⏸ PAUSE", bg=self.colors["warning"])
                self.status_icon.config(fg=self.colors["success"])
                self.status_label.config(text="Recording")
    
    def on_closing(self):
        """Handle window close"""
        if self.recording:
            result = messagebox.askyesno("Warning", "Recording in progress! Stop and exit?")
            if result:
                self.stop_recording()
                time.sleep(0.5)
            else:
                return
        
        self.stop_flag = True
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=1)
        
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = HomRecScreen(root)
    root.mainloop()