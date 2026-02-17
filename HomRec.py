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
import pyaudio
import wave
import audioop
import subprocess

class AudioLevelMeter(tk.Canvas):
    """Виджет для отображения уровня громкости"""
    def __init__(self, parent, width=180, height=24, **kwargs):
        super().__init__(parent, width=width, height=height, bg='#313244', highlightthickness=0, **kwargs)
        self.width = width
        self.height = height
        self.level = 0
        self.draw_meter()
    
    def draw_meter(self):
        self.delete("all")
        # Рисуем фон
        self.create_rectangle(0, 0, self.width, self.height, fill='#45475a', outline='')
        
        # Рисуем уровень
        bar_width = int((self.level / 100) * (self.width - 4))
        if bar_width > 0:
            color = '#a6e3a1' if self.level < 70 else '#f9e2af' if self.level < 90 else '#f38ba8'
            self.create_rectangle(2, 2, bar_width, self.height-2, fill=color, outline='')
        
        # Рисуем деления
        for i in range(0, 101, 10):
            x = int((i / 100) * self.width)
            self.create_line(x, 0, x, self.height, fill='#1e1e2e', width=1)
    
    def set_level(self, level):
        self.level = max(0, min(100, level))
        self.draw_meter()

class CustomMessageBox:
    """Кастомное окно с галочкой Don't show again"""
    @staticmethod
    def show(title, message, info_text, dont_show_var):
        dialog = tk.Toplevel()
        dialog.title(title)
        dialog.geometry("500x400")
        dialog.configure(bg='#1e1e2e')
        dialog.transient()
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # Центрируем окно
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 250
        y = (dialog.winfo_screenheight() // 2) - 200
        dialog.geometry(f"+{x}+{y}")
        
        # Иконка
        icon_label = tk.Label(dialog, text="✅", font=("Segoe UI", 48), bg='#1e1e2e', fg='#a6e3a1')
        icon_label.pack(pady=(20, 10))
        
        # Заголовок
        tk.Label(dialog, text=message, font=("Segoe UI", 14, "bold"),
                bg='#1e1e2e', fg='#cdd6f4').pack(pady=(0, 10))
        
        # Информация
        info_frame = tk.Frame(dialog, bg='#313244', relief='flat', bd=2)
        info_frame.pack(pady=10, padx=20, fill='both', expand=True)
        
        info_label = tk.Label(info_frame, text=info_text, justify='left',
                              bg='#313244', fg='#cdd6f4',
                              font=("Consolas", 10))
        info_label.pack(pady=15, padx=15)
        
        # Галочка
        check_frame = tk.Frame(dialog, bg='#1e1e2e')
        check_frame.pack(pady=10)
        
        dont_show_check = tk.Checkbutton(check_frame, text="Don't show this message again",
                                         variable=dont_show_var,
                                         bg='#1e1e2e', fg='#cdd6f4',
                                         selectcolor='#313244',
                                         font=("Segoe UI", 9))
        dont_show_check.pack()
        
        # Кнопки
        btn_frame = tk.Frame(dialog, bg='#1e1e2e')
        btn_frame.pack(pady=15)
        
        result = {'value': False}
        
        def on_yes():
            result['value'] = True
            dialog.destroy()
        
        def on_no():
            result['value'] = False
            dialog.destroy()
        
        tk.Button(btn_frame, text="Open Folder", command=on_yes,
                  bg='#a6e3a1', fg='#1e1e2e',
                  font=("Segoe UI", 10, "bold"),
                  relief='flat', padx=20, pady=8, width=12).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="Close", command=on_no,
                  bg='#45475a', fg='#cdd6f4',
                  font=("Segoe UI", 10),
                  relief='flat', padx=20, pady=8, width=12).pack(side='left', padx=5)
        
        dialog.wait_window()
        return result['value']

class AudioPanel:
    """Панель управления звуком"""
    def __init__(self, parent, app):
        self.app = app
        self.frame = tk.LabelFrame(parent, text="  🎤 Audio Mixer  ", 
                                   bg='#313244', fg='#89b4fa',
                                   font=('Segoe UI', 11, 'bold'),
                                   padx=10, pady=10)
        self.frame.pack(side='left', fill='both', expand=True, padx=(5, 0))
        
        # Микрофон
        self.create_mic_section()
        
        # Системный звук
        self.create_system_section()
        
        # Устройства
        self.create_devices_section()
        
        self.is_testing = False
        self.audio_stream = None
        self.audio_p = None
    
    def create_mic_section(self):
        """Создать секцию микрофона"""
        mic_frame = tk.Frame(self.frame, bg='#313244')
        mic_frame.pack(fill='x', pady=8)
        
        # Заголовок и контролы
        header = tk.Frame(mic_frame, bg='#313244')
        header.pack(fill='x')
        
        tk.Label(header, text="🎤 Microphone", bg='#313244', fg='#a6e3a1',
                font=('Segoe UI', 10, 'bold')).pack(side='left')
        
        self.mic_mute = tk.BooleanVar(value=False)
        self.mic_mute_btn = tk.Button(header, text='Mute', 
                                      command=self.toggle_mic_mute,
                                      bg='#45475a', fg='#cdd6f4',
                                      font=('Segoe UI', 9),
                                      relief='flat', width=6, height=1,
                                      cursor='hand2')
        self.mic_mute_btn.pack(side='right', padx=2)
        
        # Ползунок громкости
        volume_frame = tk.Frame(mic_frame, bg='#313244')
        volume_frame.pack(fill='x', pady=5)
        
        tk.Label(volume_frame, text="Volume:", bg='#313244', fg='#cdd6f4',
                font=('Segoe UI', 9)).pack(side='left', padx=(0, 10))
        
        self.mic_volume = tk.Scale(volume_frame, from_=0, to=100, orient='horizontal',
                                   length=150, bg='#313244', fg='#cdd6f4',
                                   highlightthickness=0, troughcolor='#45475a',
                                   command=self.on_mic_volume_change)
        self.mic_volume.set(80)
        self.mic_volume.pack(side='left', padx=5)
        
        self.mic_volume_label = tk.Label(volume_frame, text="80%", 
                                        bg='#313244', fg='#cdd6f4',
                                        font=('Segoe UI', 9, 'bold'))
        self.mic_volume_label.pack(side='left', padx=5)
        
        # Индикатор
        meter_frame = tk.Frame(mic_frame, bg='#313244')
        meter_frame.pack(fill='x', pady=5)
        
        tk.Label(meter_frame, text="Level:", bg='#313244', fg='#cdd6f4',
                font=('Segoe UI', 9)).pack(side='left', padx=(0, 10))
        
        self.mic_meter = AudioLevelMeter(meter_frame, width=180, height=24)
        self.mic_meter.pack(side='left')
    
    def create_system_section(self):
        """Создать секцию системного звука"""
        sys_frame = tk.Frame(self.frame, bg='#313244')
        sys_frame.pack(fill='x', pady=8)
        
        # Заголовок и контролы
        header = tk.Frame(sys_frame, bg='#313244')
        header.pack(fill='x')
        
        tk.Label(header, text="🔊 Desktop Audio", bg='#313244', fg='#89b4fa',
                font=('Segoe UI', 10, 'bold')).pack(side='left')
        
        self.sys_mute = tk.BooleanVar(value=False)
        self.sys_mute_btn = tk.Button(header, text='Mute',
                                      command=self.toggle_sys_mute,
                                      bg='#45475a', fg='#cdd6f4',
                                      font=('Segoe UI', 9),
                                      relief='flat', width=6, height=1,
                                      cursor='hand2')
        self.sys_mute_btn.pack(side='right', padx=2)
        
        # Ползунок громкости
        volume_frame = tk.Frame(sys_frame, bg='#313244')
        volume_frame.pack(fill='x', pady=5)
        
        tk.Label(volume_frame, text="Volume:", bg='#313244', fg='#cdd6f4',
                font=('Segoe UI', 9)).pack(side='left', padx=(0, 10))
        
        self.sys_volume = tk.Scale(volume_frame, from_=0, to=100, orient='horizontal',
                                   length=150, bg='#313244', fg='#cdd6f4',
                                   highlightthickness=0, troughcolor='#45475a',
                                   command=self.on_sys_volume_change)
        self.sys_volume.set(80)
        self.sys_volume.pack(side='left', padx=5)
        
        self.sys_volume_label = tk.Label(volume_frame, text="80%",
                                        bg='#313244', fg='#cdd6f4',
                                        font=('Segoe UI', 9, 'bold'))
        self.sys_volume_label.pack(side='left', padx=5)
        
        # Индикатор
        meter_frame = tk.Frame(sys_frame, bg='#313244')
        meter_frame.pack(fill='x', pady=5)
        
        tk.Label(meter_frame, text="Level:", bg='#313244', fg='#cdd6f4',
                font=('Segoe UI', 9)).pack(side='left', padx=(0, 10))
        
        self.sys_meter = AudioLevelMeter(meter_frame, width=180, height=24)
        self.sys_meter.pack(side='left')
    
    def create_devices_section(self):
        """Создать секцию устройств"""
        devices_frame = tk.Frame(self.frame, bg='#313244')
        devices_frame.pack(fill='x', pady=8)
        
        # Выбор микрофона
        mic_select = tk.Frame(devices_frame, bg='#313244')
        mic_select.pack(fill='x', pady=5)
        
        tk.Label(mic_select, text="Microphone:", bg='#313244', fg='#cdd6f4',
                font=('Segoe UI', 9, 'bold')).pack(side='left', padx=(0, 10))
        
        # Получаем список микрофонов
        self.mic_list = ["Default Microphone"]
        try:
            p = pyaudio.PyAudio()
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    name = info['name'].encode('ascii', 'ignore').decode('ascii')
                    self.mic_list.append(f"{name}")
            p.terminate()
        except:
            self.mic_list.append("Microphone")
        
        self.mic_var = tk.StringVar(value="Default Microphone")
        self.mic_combo = ttk.Combobox(mic_select, textvariable=self.mic_var,
                                      values=self.mic_list, width=30, state='readonly',
                                      font=('Segoe UI', 9))
        self.mic_combo.pack(side='left', padx=5)
        
        # Тест микрофона
        self.test_btn = tk.Button(devices_frame, text="Test Microphone", 
                                  command=self.test_microphone,
                                  bg='#45475a', fg='#cdd6f4',
                                  font=('Segoe UI', 9),
                                  relief='flat', width=15, height=1, 
                                  cursor='hand2')
        self.test_btn.pack(pady=5)
        
        # Кнопка включения записи звука
        self.audio_enabled = tk.BooleanVar(value=True)
        self.audio_check = tk.Checkbutton(devices_frame, text="Enable Audio Recording",
                                         variable=self.audio_enabled,
                                         bg='#313244', fg='#cdd6f4',
                                         selectcolor='#45475a',
                                         font=('Segoe UI', 9, 'bold'))
        self.audio_check.pack(pady=5)
        
        # Информация о FFmpeg
        ffmpeg_text = "FFmpeg: " + ("✅ Found" if self.app.check_ffmpeg() else "❌ Not Found")
        ffmpeg_color = '#a6e3a1' if self.app.check_ffmpeg() else '#f38ba8'
        
        self.ffmpeg_label = tk.Label(devices_frame, 
                                     text=ffmpeg_text,
                                     bg='#313244', 
                                     fg=ffmpeg_color,
                                     font=('Segoe UI', 8))
        self.ffmpeg_label.pack(pady=2)
    
    def on_mic_volume_change(self, value):
        """Изменение громкости микрофона"""
        self.mic_volume_label.config(text=f"{int(float(value))}%")
    
    def on_sys_volume_change(self, value):
        """Изменение громкости системного звука"""
        self.sys_volume_label.config(text=f"{int(float(value))}%")
    
    def toggle_mic_mute(self):
        self.mic_mute.set(not self.mic_mute.get())
        self.mic_mute_btn.config(bg='#f38ba8' if self.mic_mute.get() else '#45475a',
                                 text='Unmute' if self.mic_mute.get() else 'Mute')
    
    def toggle_sys_mute(self):
        self.sys_mute.set(not self.sys_mute.get())
        self.sys_mute_btn.config(bg='#f38ba8' if self.sys_mute.get() else '#45475a',
                                 text='Unmute' if self.sys_mute.get() else 'Mute')
    
    def update_mic_level(self, level):
        """Обновление уровня микрофона"""
        self.mic_meter.set_level(level)
    
    def update_sys_level(self, level):
        """Обновление уровня системного звука"""
        self.sys_meter.set_level(level)
    
    def test_microphone(self):
        """Тестирование микрофона"""
        if not self.is_testing:
            self.is_testing = True
            self.test_btn.config(text="Stop Test", bg='#f38ba8')
            
            # Запускаем тестовую запись
            self.app.start_audio_test()
            
            def stop_test():
                self.is_testing = False
                self.app.stop_audio_test()
                self.test_btn.config(text="Test Microphone", bg='#45475a')
                self.update_mic_level(0)
            
            self.frame.after(3000, stop_test)
        else:
            self.is_testing = False
            self.app.stop_audio_test()
            self.test_btn.config(text="Test Microphone", bg='#45475a')
            self.update_mic_level(0)

class SettingsDialog:
    """Диалог настроек"""
    def __init__(self, parent, app):
        self.app = app
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("HomRec Settings")
        self.dialog.geometry("500x500")
        self.dialog.configure(bg=app.colors["bg"])
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Центрируем окно
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - 250
        y = (self.dialog.winfo_screenheight() // 2) - 250
        self.dialog.geometry(f"+{x}+{y}")
        
        self.create_widgets()
    
    def create_widgets(self):
        # Notebook для вкладок
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Video Settings Tab
        video_tab = ttk.Frame(notebook)
        notebook.add(video_tab, text="Video Settings")
        
        video_inner = tk.Frame(video_tab, bg=self.app.colors["bg"])
        video_inner.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Quality control
        quality_frame = tk.Frame(video_inner, bg=self.app.colors["bg"])
        quality_frame.pack(fill="x", pady=10)
        
        tk.Label(quality_frame, text="Quality:", 
                bg=self.app.colors["bg"], 
                fg=self.app.colors["text"],
                font=("Segoe UI", 10),
                width=10, anchor="w").pack(side="left")
        
        self.quality_var = tk.StringVar(value=str(self.app.quality))
        quality_scale = tk.Scale(quality_frame, from_=10, to=100, 
                                 orient="horizontal", length=250,
                                 variable=self.quality_var, 
                                 command=self.update_quality,
                                 bg=self.app.colors["surface"], 
                                 fg=self.app.colors["text"],
                                 highlightthickness=0, 
                                 troughcolor=self.app.colors["surface_light"])
        quality_scale.pack(side="left", padx=5)
        
        tk.Label(quality_frame, text="%", 
                bg=self.app.colors["bg"], 
                fg=self.app.colors["text_secondary"],
                font=("Segoe UI", 10)).pack(side="left")
        
        # Resolution control
        res_frame = tk.Frame(video_inner, bg=self.app.colors["bg"])
        res_frame.pack(fill="x", pady=10)
        
        tk.Label(res_frame, text="Resolution:", 
                bg=self.app.colors["bg"], 
                fg=self.app.colors["text"],
                font=("Segoe UI", 10),
                width=10, anchor="w").pack(side="left")
        
        self.scale_var = tk.StringVar(value=str(int(self.app.scale_factor * 100)))
        scale_scale = tk.Scale(res_frame, from_=25, to=100, 
                              orient="horizontal", length=250,
                              variable=self.scale_var,
                              command=self.update_scale,
                              bg=self.app.colors["surface"], 
                              fg=self.app.colors["text"],
                              highlightthickness=0,
                              troughcolor=self.app.colors["surface_light"])
        scale_scale.pack(side="left", padx=5)
        
        tk.Label(res_frame, text="%", 
                bg=self.app.colors["bg"], 
                fg=self.app.colors["text_secondary"],
                font=("Segoe UI", 10)).pack(side="left")
        
        # Performance mode
        mode_frame = tk.Frame(video_inner, bg=self.app.colors["bg"])
        mode_frame.pack(fill="x", pady=10)
        
        tk.Label(mode_frame, text="Mode:", 
                bg=self.app.colors["bg"], 
                fg=self.app.colors["text"],
                font=("Segoe UI", 10),
                width=10, anchor="w").pack(side="left")
        
        self.mode_var = tk.StringVar(value=self.app.recording_mode)
        mode_combo = ttk.Combobox(mode_frame, textvariable=self.mode_var,
                                  values=["ultra", "turbo", "balanced", "eco"],
                                  width=15, state="readonly",
                                  font=("Segoe UI", 10))
        mode_combo.pack(side="left", padx=5)
        mode_combo.bind("<<ComboboxSelected>>", self.on_mode_change)
        
        # Advanced Tab
        adv_tab = ttk.Frame(notebook)
        notebook.add(adv_tab, text="Advanced")
        
        adv_inner = tk.Frame(adv_tab, bg=self.app.colors["bg"])
        adv_inner.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Monitor selection
        mon_frame = tk.Frame(adv_inner, bg=self.app.colors["bg"])
        mon_frame.pack(fill="x", pady=10)
        
        tk.Label(mon_frame, text="Monitor:", 
                bg=self.app.colors["bg"], 
                fg=self.app.colors["text"],
                font=("Segoe UI", 10),
                width=10, anchor="w").pack(side="left")
        
        self.monitor_var = tk.StringVar(value=str(self.app.monitor_id))
        monitor_combo = ttk.Combobox(mon_frame, textvariable=self.monitor_var,
                                     values=[str(i) for i in range(1, len(self.app.sct.monitors))],
                                     width=10, state="readonly",
                                     font=("Segoe UI", 10))
        monitor_combo.pack(side="left", padx=5)
        monitor_combo.bind("<<ComboboxSelected>>", self.on_monitor_change)
        
        # Output folder
        folder_frame = tk.Frame(adv_inner, bg=self.app.colors["bg"])
        folder_frame.pack(fill="x", pady=10)
        
        tk.Label(folder_frame, text="Output:", 
                bg=self.app.colors["bg"], 
                fg=self.app.colors["text"],
                font=("Segoe UI", 10),
                width=10, anchor="w").pack(side="left")
        
        self.folder_label = tk.Label(folder_frame, text=os.path.basename(self.app.output_folder), 
                                     bg=self.app.colors["surface"], 
                                     fg=self.app.colors["accent"],
                                     font=("Consolas", 10),
                                     relief="flat", padx=8, pady=4)
        self.folder_label.pack(side="left", padx=5)
        
        tk.Button(folder_frame, text="Browse", command=self.select_folder,
                 bg=self.app.colors["surface"], 
                 fg=self.app.colors["text"],
                 font=("Segoe UI", 10),
                 relief="flat", padx=12).pack(side="left", padx=5)
        
        # Features
        features_frame = tk.Frame(adv_inner, bg=self.app.colors["bg"])
        features_frame.pack(fill="x", pady=10)
        
        self.countdown_var = tk.BooleanVar(value=self.app.countdown_var.get())
        tk.Checkbutton(features_frame, text="Countdown (3 sec)",
                      variable=self.countdown_var,
                      bg=self.app.colors["bg"], 
                      fg=self.app.colors["text"],
                      font=("Segoe UI", 10),
                      selectcolor=self.app.colors["surface"]).pack(anchor="w", pady=5)
        
        self.timestamp_var = tk.BooleanVar(value=self.app.timestamp_var.get())
        tk.Checkbutton(features_frame, text="Timestamp",
                      variable=self.timestamp_var,
                      bg=self.app.colors["bg"], 
                      fg=self.app.colors["text"],
                      font=("Segoe UI", 10),
                      selectcolor=self.app.colors["surface"]).pack(anchor="w", pady=5)
        
        self.cursor_var = tk.BooleanVar(value=self.app.cursor_var.get())
        tk.Checkbutton(features_frame, text="Cursor",
                      variable=self.cursor_var,
                      bg=self.app.colors["bg"], 
                      fg=self.app.colors["text"],
                      font=("Segoe UI", 10),
                      selectcolor=self.app.colors["surface"]).pack(anchor="w", pady=5)
        
        # Notification settings
        notif_frame = tk.Frame(adv_inner, bg=self.app.colors["bg"])
        notif_frame.pack(fill="x", pady=10)
        
        self.show_summary_var = tk.BooleanVar(value=self.app.show_summary)
        tk.Checkbutton(notif_frame, text="Show summary after recording",
                      variable=self.show_summary_var,
                      bg=self.app.colors["bg"], 
                      fg=self.app.colors["text"],
                      font=("Segoe UI", 10),
                      selectcolor=self.app.colors["surface"]).pack(anchor="w", pady=5)
        
        # Кнопки
        btn_frame = tk.Frame(self.dialog, bg=self.app.colors["bg"])
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Button(btn_frame, text="Save", command=self.save_settings,
                 bg=self.app.colors["success"], fg=self.app.colors["bg"],
                 font=("Segoe UI", 10, "bold"),
                 relief="flat", padx=20, pady=8).pack(side="right", padx=5)
        
        tk.Button(btn_frame, text="Cancel", command=self.dialog.destroy,
                 bg=self.app.colors["surface"], fg=self.app.colors["text"],
                 font=("Segoe UI", 10),
                 relief="flat", padx=20, pady=8).pack(side="right", padx=5)
    
    def update_quality(self, event):
        pass
    
    def update_scale(self, event):
        pass
    
    def on_mode_change(self, event=None):
        pass
    
    def on_monitor_change(self, event=None):
        pass
    
    def select_folder(self):
        folder = filedialog.askdirectory(initialdir=self.app.output_folder)
        if folder:
            self.app.output_folder = folder
            self.folder_label.config(text=os.path.basename(folder))
    
    def save_settings(self):
        self.app.quality = int(self.quality_var.get())
        self.app.recording_mode = self.mode_var.get()
        self.app.update_mode_settings()
        self.app.scale_factor = int(self.scale_var.get()) / 100
        self.app.update_monitor_info()
        self.app.monitor_id = int(self.monitor_var.get())
        self.app.update_monitor_info()
        self.app.countdown_var.set(self.countdown_var.get())
        self.app.timestamp_var.set(self.timestamp_var.get())
        self.app.cursor_var.set(self.cursor_var.get())
        self.app.show_summary = self.show_summary_var.get()
        self.app.res_label.config(text=f"Res: {self.app.record_width}x{self.app.record_height}")
        self.app.save_settings(silent=True)
        self.dialog.destroy()
        messagebox.showinfo("Settings", "Settings saved successfully!")

class HomRecScreen:
    def __init__(self, root):
        self.root = root
        self.root.title("HomRec (v1.1.0)")
        self.root.geometry("1300x750")
        self.root.minsize(1200, 650)
        
        # Set application icon
        self.set_app_icon()
        
        # Theme settings
        self.current_theme = "dark"
        self.colors = self.get_theme_colors("dark")
        
        # Apply theme
        self.apply_theme()
        
        # MSS для захвата экрана
        self.sct = mss.mss()
        
        # Audio recording
        self.audio_recording = False
        self.audio_thread = None
        self.audio_frames = []
        self.audio_stream = None
        self.audio_p = None
        self.audio_testing = False
        
        # Settings
        self.scale_factor = 0.75
        self.output_folder = "recordings"
        self.quality = 70
        self.target_fps = 15
        self.recording_mode = "balanced"
        self.show_summary = True
        
        # Features
        self.countdown_var = tk.BooleanVar(value=True)
        self.timestamp_var = tk.BooleanVar(value=False)
        self.cursor_var = tk.BooleanVar(value=False)
        
        # Preview size
        self.preview_width = 900
        self.preview_height = 500
        
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
        print(f"[HomRec v1.1.0] Started successfully")
    
    def check_ffmpeg(self):
        """Проверка наличия FFmpeg"""
        try:
            if os.path.exists("ffmpeg.exe"):
                return True
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            return True
        except:
            return False
    
    def merge_audio_video(self, video_file, audio_file):
        """Скрепить аудио с видео в один файл используя FFmpeg"""
        if not os.path.exists(audio_file):
            return False
        
        output_file = video_file.replace('.mp4', '_temp.mp4')
        
        try:
            ffmpeg_path = 'ffmpeg'
            if os.path.exists("ffmpeg.exe"):
                ffmpeg_path = "ffmpeg.exe"
            
            cmd = [
                ffmpeg_path,
                '-i', video_file,
                '-i', audio_file,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-map', '0:v:0',
                '-map', '1:a:0',
                '-shortest',
                '-y',
                output_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(output_file):
                os.remove(video_file)
                os.remove(audio_file)
                os.rename(output_file, video_file)
                print("[HomRec] Audio merged successfully")
                return True
            else:
                print(f"[HomRec] FFmpeg error: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"[HomRec] Merge error: {e}")
            return False
    
    def set_app_icon(self):
        try:
            icon_size = (64, 64)
            icon_image = Image.new('RGBA', icon_size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(icon_image)
            draw.rectangle([10, 20, 54, 44], fill="#89b4fa", outline="#cdd6f4", width=2)
            draw.ellipse([25, 25, 39, 39], fill="#1e1e2e", outline="#cdd6f4", width=2)
            draw.ellipse([29, 29, 35, 35], fill="#89b4fa")
            draw.rectangle([45, 15, 50, 20], fill="#f9e2af")
            icon_photo = ImageTk.PhotoImage(icon_image)
            self.root.iconphoto(True, icon_photo)
            if sys.platform == "win32":
                myappid = 'homrec.screen.recorder.v1.1.0'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            pass
    
    def on_window_resize(self, event):
        if event.widget == self.root:
            self.update_preview_size()
    
    def update_preview_size(self):
        try:
            preview_height = self.root.winfo_height() - 200
            preview_width = self.root.winfo_width() - 280
            if preview_width > 0 and preview_height > 0:
                self.preview_width = max(600, min(preview_width - 40, 1280))
                self.preview_height = max(350, min(preview_height - 40, 720))
        except:
            pass
    
    def get_theme_colors(self, theme):
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
        else:
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
        self.root.configure(bg=self.colors["bg"])
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background=self.colors["bg"])
        style.configure("TLabel", background=self.colors["bg"], foreground=self.colors["fg"])
        style.configure("TLabelframe", background=self.colors["bg"], foreground=self.colors["accent"])
        style.configure("TLabelframe.Label", background=self.colors["bg"], foreground=self.colors["accent"], font=("Segoe UI", 11, "bold"))
        style.configure("TButton", background=self.colors["surface"], foreground=self.colors["fg"])
        style.configure("TRadiobutton", background=self.colors["bg"], foreground=self.colors["fg"])
        style.configure("TCheckbutton", background=self.colors["bg"], foreground=self.colors["fg"])
        style.configure("TCombobox", fieldbackground=self.colors["surface"], foreground=self.colors["fg"])
        style.configure("TMenu", background=self.colors["surface"], foreground=self.colors["fg"])
    
    def create_menu(self):
        menubar = tk.Menu(self.root, bg=self.colors["surface"], fg=self.colors["fg"])
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0, bg=self.colors["surface"], fg=self.colors["fg"])
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Recordings Folder", command=self.open_recordings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        settings_menu = tk.Menu(menubar, tearoff=0, bg=self.colors["surface"], fg=self.colors["fg"])
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Preferences...", command=self.open_settings)
        settings_menu.add_separator()
        
        theme_menu = tk.Menu(settings_menu, tearoff=0, bg=self.colors["surface"], fg=self.colors["fg"])
        settings_menu.add_cascade(label="Theme", menu=theme_menu)
        theme_menu.add_command(label="🌙 Dark Theme", command=lambda: self.change_theme("dark"))
        theme_menu.add_command(label="☀️ Light Theme", command=lambda: self.change_theme("light"))
        
        perf_menu = tk.Menu(settings_menu, tearoff=0, bg=self.colors["surface"], fg=self.colors["fg"])
        settings_menu.add_cascade(label="Performance Mode", menu=perf_menu)
        perf_menu.add_command(label="🚀 Ultra (60 FPS)", command=lambda: self.set_mode("ultra"))
        perf_menu.add_command(label="⚡ Turbo (30 FPS)", command=lambda: self.set_mode("turbo"))
        perf_menu.add_command(label="⚖️ Balanced (15 FPS)", command=lambda: self.set_mode("balanced"))
        perf_menu.add_command(label="🐢 Eco (8 FPS)", command=lambda: self.set_mode("eco"))
    
    def open_settings(self):
        SettingsDialog(self.root, self)
    
    def change_theme(self, theme):
        self.current_theme = theme
        self.colors = self.get_theme_colors(theme)
        self.apply_theme()
        self.recreate_widgets()
        self.save_settings(silent=True)
    
    def recreate_widgets(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.create_menu()
        self.create_widgets()
    
    def set_mode(self, mode):
        self.recording_mode = mode
        self.update_mode_settings()
        self.save_settings(silent=True)
        self.res_label.config(text=f"Res: {self.record_width}x{self.record_height}")
    
    def update_mode_settings(self):
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
        else:
            self.target_fps = 8
            self.quality = 50
            self.scale_factor = 0.5
        self.update_monitor_info()
    
    def load_settings(self):
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
                    self.countdown_var.set(settings.get("countdown", True))
                    self.timestamp_var.set(settings.get("timestamp", False))
                    self.cursor_var.set(settings.get("cursor", False))
                    self.show_summary = settings.get("show_summary", True)
        except:
            pass
    
    def save_settings(self, silent=False):
        settings = {
            "output_folder": self.output_folder,
            "scale_factor": self.scale_factor,
            "target_fps": self.target_fps,
            "quality": self.quality,
            "mode": self.recording_mode,
            "theme": self.current_theme,
            "countdown": self.countdown_var.get(),
            "timestamp": self.timestamp_var.get(),
            "cursor": self.cursor_var.get(),
            "show_summary": self.show_summary
        }
        with open("homrec_settings.json", "w") as f:
            json.dump(settings, f, indent=2)
        if not silent:
            messagebox.showinfo("Settings", "Settings saved successfully!\n😘 Made by Homa4ella")
    
    def update_monitor_info(self):
        self.monitor = self.sct.monitors[self.monitor_id]
        self.original_width = self.monitor['width']
        self.original_height = self.monitor['height']
        self.record_width = int(self.original_width * self.scale_factor)
        self.record_height = int(self.original_height * self.scale_factor)
        if self.record_width % 2 != 0:
            self.record_width -= 1
        if self.record_height % 2 != 0:
            self.record_height -= 1
    
    def create_widgets(self):
        main_container = tk.Frame(self.root, bg=self.colors["bg"])
        main_container.pack(fill="both", expand=True, padx=15, pady=15)
        
        left_panel = tk.Frame(main_container, bg=self.colors["surface"], width=240)
        left_panel.pack(side="left", fill="y", padx=(0, 15))
        left_panel.pack_propagate(False)
        
        title_frame = tk.Frame(left_panel, bg=self.colors["surface"])
        title_frame.pack(pady=20, fill="x")
        tk.Label(title_frame, text="HomRec", 
                font=("Segoe UI", 22, "bold"), 
                bg=self.colors["surface"], 
                fg=self.colors["accent"]).pack()
        tk.Label(title_frame, text="v1.1.0", 
                font=("Segoe UI", 11), 
                bg=self.colors["surface"], 
                fg=self.colors["text_secondary"]).pack()
        
        btn_frame = tk.Frame(left_panel, bg=self.colors["surface"])
        btn_frame.pack(pady=25, padx=15, fill="x")
        
        self.record_btn = tk.Button(btn_frame, text="▶ START", 
                                   command=self.start_with_countdown,
                                   bg=self.colors["success"], fg=self.colors["bg"],
                                   font=("Segoe UI", 13, "bold"),
                                   relief="flat", height=2,
                                   cursor="hand2")
        self.record_btn.pack(fill="x", pady=5)
        
        self.pause_btn = tk.Button(btn_frame, text="⏸ PAUSE", 
                                  command=self.toggle_pause,
                                  bg=self.colors["warning"], fg=self.colors["bg"],
                                  font=("Segoe UI", 13, "bold"),
                                  state="disabled", relief="flat", height=2,
                                  cursor="hand2")
        self.pause_btn.pack(fill="x", pady=5)
        
        self.stop_btn = tk.Button(btn_frame, text="■ STOP", 
                                 command=self.stop_recording,
                                 bg=self.colors["error"], fg=self.colors["bg"],
                                 font=("Segoe UI", 13, "bold"),
                                 state="disabled", relief="flat", height=2,
                                 cursor="hand2")
        self.stop_btn.pack(fill="x", pady=5)
        
        status_frame = tk.Frame(left_panel, bg=self.colors["surface"])
        status_frame.pack(pady=15, padx=15, fill="x")
        tk.Label(status_frame, text="STATUS", 
                font=("Segoe UI", 11, "bold"),
                bg=self.colors["surface"], 
                fg=self.colors["accent"]).pack(anchor="w")
        
        status_row = tk.Frame(status_frame, bg=self.colors["surface"])
        status_row.pack(fill="x", pady=8)
        self.status_icon = tk.Label(status_row, text="⬤", 
                                   fg=self.colors["error"], 
                                   bg=self.colors["surface"], 
                                   font=("Arial", 18))
        self.status_icon.pack(side="left", padx=(0, 8))
        self.status_label = tk.Label(status_row, text="Ready", 
                                    bg=self.colors["surface"], 
                                    fg=self.colors["text"],
                                    font=("Segoe UI", 11))
        self.status_label.pack(side="left")
        
        timer_frame = tk.Frame(left_panel, bg=self.colors["surface"])
        timer_frame.pack(pady=15, padx=15, fill="x")
        tk.Label(timer_frame, text="TIME", 
                font=("Segoe UI", 11, "bold"),
                bg=self.colors["surface"], 
                fg=self.colors["accent"]).pack(anchor="w")
        self.time_label = tk.Label(timer_frame, text="00:00:00", 
                                   font=("Consolas", 24, "bold"),
                                   bg=self.colors["surface"], 
                                   fg=self.colors["accent"])
        self.time_label.pack(pady=8)
        
        stats_frame = tk.Frame(left_panel, bg=self.colors["surface"])
        stats_frame.pack(pady=15, padx=15, fill="x")
        tk.Label(stats_frame, text="STATS", 
                font=("Segoe UI", 11, "bold"),
                bg=self.colors["surface"], 
                fg=self.colors["accent"]).pack(anchor="w")
        
        self.fps_label = tk.Label(stats_frame, text="FPS: 0", 
                                 bg=self.colors["surface"], 
                                 fg=self.colors["text"],
                                 font=("Consolas", 11))
        self.fps_label.pack(anchor="w", pady=3)
        
        self.res_label = tk.Label(stats_frame, 
                                 text=f"Res: {self.record_width}x{self.record_height}", 
                                 bg=self.colors["surface"], 
                                 fg=self.colors["text"],
                                 font=("Consolas", 11))
        self.res_label.pack(anchor="w", pady=3)
        
        right_panel = tk.Frame(main_container, bg=self.colors["bg"])
        right_panel.pack(side="right", fill="both", expand=True)
        
        preview_container = tk.Frame(right_panel, bg=self.colors["surface_light"], relief="flat", bd=2)
        preview_container.pack(fill="both", expand=True, pady=(0, 15))
        
        preview_label_title = tk.Label(preview_container, text="LIVE PREVIEW", 
                                      bg=self.colors["surface_light"], 
                                      fg=self.colors["text_secondary"],
                                      font=("Segoe UI", 10, "bold"))
        preview_label_title.pack(anchor="nw", padx=8, pady=5)
        
        preview_frame = tk.Frame(preview_container, bg=self.colors["preview_bg"])
        preview_frame.pack(fill="both", expand=True, padx=8, pady=8)
        
        self.preview_label = tk.Label(preview_frame, bg=self.colors["preview_bg"])
        self.preview_label.pack(fill="both", expand=True)
        
        bottom_panel = tk.Frame(right_panel, bg=self.colors["bg"], height=320)
        bottom_panel.pack(fill="x")
        bottom_panel.pack_propagate(False)
        
        self.audio_panel = AudioPanel(bottom_panel, self)
        
        bottom_bar = tk.Frame(self.root, bg=self.colors["surface"], height=35)
        bottom_bar.pack(side="bottom", fill="x")
        
        self.file_label = tk.Label(bottom_bar, text="Ready to record...", 
                                   bg=self.colors["surface"], 
                                   fg=self.colors["text_secondary"],
                                   font=("Segoe UI", 10))
        self.file_label.pack(side="left", padx=15)
        
        tk.Label(bottom_bar, text="😘 Homa4ella", 
                bg=self.colors["surface"], 
                fg=self.colors["accent"],
                font=("Segoe UI", 10, "bold")).pack(side="right", padx=15)
        
        self.update_preview_size()
    
    def start_audio_test(self):
        """Запуск теста микрофона"""
        try:
            self.audio_testing = True
            self.audio_p = pyaudio.PyAudio()
            self.audio_stream = self.audio_p.open(
                format=pyaudio.paInt16,
                channels=2,
                rate=44100,
                input=True,
                frames_per_buffer=1024
            )
            
            def test_thread():
                while self.audio_testing:
                    try:
                        data = self.audio_stream.read(1024, exception_on_overflow=False)
                        rms = audioop.rms(data, 2)
                        level = min(100, int(rms / 300))
                        self.audio_panel.update_mic_level(level)
                    except:
                        pass
                    time.sleep(0.05)
            
            threading.Thread(target=test_thread, daemon=True).start()
        except Exception as e:
            print(f"Test error: {e}")
    
    def stop_audio_test(self):
        """Остановка теста микрофона"""
        self.audio_testing = False
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
        if self.audio_p:
            self.audio_p.terminate()
    
    def select_folder(self):
        folder = filedialog.askdirectory(initialdir=self.output_folder)
        if folder:
            self.output_folder = folder
            os.makedirs(self.output_folder, exist_ok=True)
            self.save_settings(silent=True)
    
    def open_recordings(self):
        if os.path.exists(self.output_folder):
            os.startfile(self.output_folder)
        else:
            messagebox.showwarning("Warning", "Recordings folder doesn't exist yet!")
    
    def start_with_countdown(self):
        if not self.recording:
            if self.countdown_var.get():
                self.show_countdown()
            else:
                self.start_recording()
        else:
            self.stop_recording()
    
    def show_countdown(self):
        countdown_window = tk.Toplevel(self.root)
        countdown_window.title("Starting...")
        countdown_window.geometry("350x180")
        countdown_window.configure(bg=self.colors["bg"])
        countdown_window.overrideredirect(True)
        
        countdown_window.update_idletasks()
        x = (countdown_window.winfo_screenwidth() // 2) - 175
        y = (countdown_window.winfo_screenheight() // 2) - 90
        countdown_window.geometry(f"+{x}+{y}")
        
        label = tk.Label(countdown_window, text="3", 
                        font=("Segoe UI", 56, "bold"),
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
    
    def update_preview(self):
        try:
            screenshot = self.sct.grab(self.monitor)
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            img.thumbnail((self.preview_width, self.preview_height), Image.Resampling.LANCZOS)
            
            if self.recording:
                draw = ImageDraw.Draw(img)
                if not self.paused:
                    draw.ellipse([10, 10, 35, 35], fill=self.colors["error"])
                else:
                    draw.rectangle([10, 10, 35, 35], fill=self.colors["warning"])
            
            photo = ImageTk.PhotoImage(img)
            self.preview_label.config(image=photo)
            self.preview_label.image = photo
        except:
            pass
        
        delay = 200 if self.recording else 100
        self.root.after(delay, self.update_preview)
    
    def toggle_recording(self):
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_audio_recording(self):
        """Start audio recording"""
        try:
            self.audio_p = pyaudio.PyAudio()
            self.audio_frames = []
            
            self.audio_stream = self.audio_p.open(
                format=pyaudio.paInt16,
                channels=2,
                rate=44100,
                input=True,
                frames_per_buffer=1024
            )
            
            self.audio_recording = True
            
            def record_audio():
                while self.audio_recording and not self.stop_flag:
                    if not self.paused and not self.audio_panel.mic_mute.get():
                        try:
                            data = self.audio_stream.read(1024, exception_on_overflow=False)
                            self.audio_frames.append(data)
                            
                            # Обновляем индикатор громкости
                            rms = audioop.rms(data, 2)
                            level = min(100, int(rms / 300))
                            self.audio_panel.update_mic_level(level)
                        except:
                            pass
                    else:
                        time.sleep(0.01)
            
            self.audio_thread = threading.Thread(target=record_audio, daemon=True)
            self.audio_thread.start()
            print("[HomRec] Audio recording started")
            
        except Exception as e:
            print(f"[HomRec] Audio error: {e}")
            self.audio_recording = False
    
    def stop_audio_recording(self):
        """Stop audio recording"""
        self.audio_recording = False
        
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=2)
        
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
        
        if self.audio_p:
            self.audio_p.terminate()
        
        # Сохраняем аудио если есть кадры
        if self.audio_frames and not self.audio_panel.mic_mute.get():
            audio_filename = self.filename.replace('.mp4', '_audio.wav')
            wf = wave.open(audio_filename, 'wb')
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(44100)
            wf.writeframes(b''.join(self.audio_frames))
            wf.close()
            print(f"[HomRec] Audio saved: {audio_filename}")
            return audio_filename
        return None
    
    def start_recording(self):
        """Start recording"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.filename = f"{self.output_folder}/HomRec_{timestamp}.mp4"
            
            print(f"\n[HomRec] ========== STARTING RECORDING ==========")
            print(f"[HomRec] Audio enabled: {self.audio_panel.audio_enabled.get()}")
            print(f"[HomRec] FFmpeg available: {self.check_ffmpeg()}")
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.out = cv2.VideoWriter(
                self.filename, fourcc, self.target_fps, 
                (self.record_width, self.record_height)
            )
            
            if not self.out.isOpened():
                raise Exception("Cannot create video file")
            
            # ВАЖНО: Проверяем включен ли звук перед запуском
            if self.audio_panel.audio_enabled.get():
                self.start_audio_recording()
            
            self.recording = True
            self.paused = False
            self.frame_count = 0
            self.start_time = time.time()
            self.stop_flag = False
            
            self.record_btn.config(text="⏺ RECORDING", bg=self.colors["error"])
            self.pause_btn.config(state="normal")
            self.stop_btn.config(state="normal")
            self.status_icon.config(fg=self.colors["success"])
            self.status_label.config(text="Recording")
            
            self.recording_thread = threading.Thread(target=self._record_thread, daemon=True)
            self.recording_thread.start()
            
            self._update_stats()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start recording:\n{str(e)}")
    
    def _record_thread(self):
        """Recording thread with PRECISE timing"""
        sct_local = mss.mss()
        
        needs_resize = self.scale_factor < 1.0
        add_timestamp = self.timestamp_var.get()
        add_cursor = self.cursor_var.get()
        
        get_cursor = None
        if add_cursor:
            try:
                import win32api
                get_cursor = win32api.GetCursorPos
            except:
                add_cursor = False
        
        # Рассчитываем время для каждого кадра
        frame_duration = 1.0 / self.target_fps
        start_time = time.time()
        frame_count = 0
        
        while self.recording and not self.stop_flag:
            if self.paused:
                time.sleep(0.05)
                continue
            
            # Вычисляем, когда должен быть этот кадр
            expected_time = start_time + (frame_count * frame_duration)
            current_time = time.time()
            
            # Если еще рано - ждем
            if current_time < expected_time:
                time.sleep(expected_time - current_time)
                continue
            
            try:
                # Захватываем кадр
                screenshot = sct_local.grab(self.monitor)
                
                frame = np.frombuffer(screenshot.bgra, dtype=np.uint8)
                frame = frame.reshape(screenshot.height, screenshot.width, 4)
                frame = frame[:, :, :3].copy()
                
                if needs_resize:
                    frame = cv2.resize(frame, (self.record_width, self.record_height), 
                                     interpolation=cv2.INTER_NEAREST)
                
                if add_cursor and get_cursor:
                    try:
                        cx, cy = get_cursor()
                        sx = int((cx - self.monitor['left']) * self.scale_factor)
                        sy = int((cy - self.monitor['top']) * self.scale_factor)
                        if 0 <= sx < self.record_width and 0 <= sy < self.record_height:
                            cv2.circle(frame, (sx, sy), 20, (0, 255, 255), 3)
                    except:
                        pass
                
                if add_timestamp:
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cv2.putText(frame, ts, (10, 30), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                if self.out and self.out.isOpened():
                    self.out.write(frame)
                    frame_count += 1
                    self.frame_count = frame_count
                    
                    if frame_count % 30 == 0:
                        actual_fps = frame_count / (time.time() - start_time)
                        print(f"[HomRec] Frame {frame_count}, FPS: {actual_fps:.1f}")
                
            except Exception as e:
                print(f"[HomRec] Frame error: {e}")
        
        try:
            sct_local.close()
        except:
            pass
    
    def _update_stats(self):
        """Update stats"""
        if self.recording:
            try:
                elapsed = time.time() - self.start_time
                if elapsed > 0 and self.frame_count > 0:
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
        """Stop recording and merge audio"""
        print("[HomRec] Stopping recording...")
        
        self.recording = False
        self.stop_flag = True
        
        # Stop audio recording
        audio_file = None
        if self.audio_recording:
            audio_file = self.stop_audio_recording()
        
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=3)
        
        time.sleep(0.3)
        
        if self.out:
            try:
                self.out.release()
            except:
                pass
        
        # Проверяем наличие FFmpeg и скрещиваем аудио с видео
        has_ffmpeg = self.check_ffmpeg()
        audio_merged = False
        
        if audio_file and os.path.exists(self.filename) and self.audio_panel.audio_enabled.get():
            if has_ffmpeg:
                print("[HomRec] Merging audio with video using FFmpeg...")
                audio_merged = self.merge_audio_video(self.filename, audio_file)
                if audio_merged:
                    print("[HomRec] Audio merged successfully!")
            else:
                print("[HomRec] FFmpeg not found - keeping separate files")
        
        self.record_btn.config(text="▶ START", bg=self.colors["success"])
        self.pause_btn.config(state="disabled", text="⏸ PAUSE")
        self.stop_btn.config(state="disabled")
        self.status_icon.config(fg=self.colors["error"])
        self.status_label.config(text="Ready")
        self.time_label.config(text="00:00:00")
        
        if self.frame_count > 0 and os.path.exists(self.filename):
            actual_duration = time.time() - self.start_time
            size = os.path.getsize(self.filename) / (1024 * 1024)
            actual_fps = self.frame_count / actual_duration
            
            self.file_label.config(text=f"✅ Saved: {size:.1f} MB | {actual_duration:.1f}s")
            
            audio_status = "Merged" if audio_merged else "Separate file" if audio_file else "No"
            
            # Формируем информационный текст
            info_lines = [
                f"📁 File: {os.path.basename(self.filename)}",
                f"📊 Size: {size:.1f} MB",
                f"⏱️ Duration: {actual_duration:.1f} sec",
                f"📏 Resolution: {self.record_width}x{self.record_height}",
                f"⚡ FPS: {actual_fps:.1f}",
                f"🎤 Audio: {audio_status}"
            ]
            
            if audio_file and not audio_merged:
                info_lines.append(f"📢 Audio file: {os.path.basename(audio_file)}")
            
            if not has_ffmpeg and audio_file:
                info_lines.append("")
                info_lines.append("⚠️ FFmpeg not found - audio saved separately")
                info_lines.append("Download FFmpeg from: https://ffmpeg.org/download.html")
            
            info_lines.append("")
            info_lines.append("😘 Made by Homa4ella (tg: @homaexe)")
            
            info_text = "\n".join(info_lines)
            
            # ТОЛЬКО одно окно - кастомное
            if self.show_summary:
                dont_show_var = tk.BooleanVar(value=False)
                result = CustomMessageBox.show(
                    "HomRec v1.1.0",
                    "✅ Recording Saved!",
                    info_text,
                    dont_show_var
                )
                
                # Сохраняем настройку если поставили галочку
                if dont_show_var.get():
                    self.show_summary = False
                    self.save_settings(silent=True)
                
                if result:
                    self.open_recordings()
        else:
            self.file_label.config(text="❌ Failed")
            messagebox.showerror("Error", "Recording failed!")
    
    def toggle_pause(self):
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