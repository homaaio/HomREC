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
import ctypes
import sys
import pyaudio
import wave
import audioop
import subprocess
import pystray
from pystray import MenuItem, Icon
import psutil
import GPUtil
import webbrowser
import locale
import math

# ==================== ЯЗЫКОВЫЕ ФАЙЛЫ ====================
LANGUAGES = {
    "en": {
        # Основное окно
        "app_title": "HomRec (v1.2.0)",
        "live_preview": "LIVE PREVIEW",
        "ready": "Ready",
        "recording": "Recording",
        "paused": "Paused",
        "fps": "FPS:",
        "resolution": "Resolution:",
        "start": "▶ START",
        "pause": "⏸ PAUSE",
        "stop": "■ STOP",
        "resume": "▶ RESUME",
        "recording_btn": "⏺ RECORDING",
        
        # Audio Mixer
        "audio_mixer": "Audio Mixer",
        "microphone": "Microphone",
        "desktop_audio": "Desktop Audio",
        "mute": "Mute",
        "unmute": "Unmute",
        "vol": "Vol:",
        "level": "Level:",
        "enable_desktop": "Enable Desktop Audio",
        "stereo_mix_status": "(Not found)",
        "stereo_available": "(Available)",
        "stereo_not_found": "(Not found)",
        
        # Меню
        "file_menu": "File",
        "open_recordings": "Open Recordings Folder",
        "exit": "Exit",
        "view_menu": "View",
        "statistics": "Statistics",
        "settings_menu": "Settings",
        "preferences": "Preferences...",
        "theme_menu": "Theme",
        "dark_theme": "Dark Theme",
        "light_theme": "Light Theme",
        "performance_menu": "Performance Mode",
        "ultra": "Ultra (60 FPS)",
        "turbo": "Turbo (30 FPS)",
        "balanced": "Balanced (15 FPS)",
        "eco": "Eco (8 FPS)",
        "language_menu": "Language",
        "english": "English",
        "russian": "Русский",
        
        # Статистика
        "stats_title": "System Statistics",
        "stats_fps": "FPS:",
        "stats_cpu": "CPU:",
        "stats_ram": "RAM:",
        "stats_disk": "Disk:",
        "stats_bitrate": "Bitrate:",
        "close": "Close",
        
        # Настройки
        "settings_title": "HomRec Settings",
        "video_settings": "Video Settings",
        "quality": "Quality:",
        "mode": "Mode:",
        "advanced": "Advanced",
        "monitor": "Monitor:",
        "output": "Output:",
        "browse": "Browse",
        "features": "Features",
        "countdown": "Countdown (3 sec)",
        "timestamp": "Timestamp",
        "cursor": "Cursor",
        "tray_settings": "Tray Settings",
        "minimize_to_tray": "Minimize to tray when closing",
        "notification_settings": "Notification Settings",
        "show_summary": "Show summary after recording",
        "save": "Save",
        "cancel": "Cancel",
        "language_settings": "Language",
        "select_language": "Select language:",
        
        # Сообщения
        "warning": "Warning",
        "error": "Error",
        "info": "Info",
        "folder_not_exist": "Recordings folder doesn't exist yet!",
        "recording_failed": "Recording failed!",
        "settings_saved": "Settings saved successfully!",
        "recording_saved": "Recording Saved!",
        "open_folder": "Open folder?",
        "ffmpeg_not_found": "FFmpeg not found - audio saved separately\nDownload FFmpeg from: https://ffmpeg.org/download.html",
        
        # Статусы файлов
        "file": "File:",
        "size": "Size:",
        "duration": "Duration:",
        "audio": "Audio:",
        "mic_file": "Mic file:",
        "system_file": "System file:",
        
        # Трей
        "tray_show": "Show Window",
        "tray_start": "Start Recording",
        "tray_stop": "Stop Recording",
        "tray_open": "Open Recordings",
        "tray_exit": "Exit",
        
        # Тест микрофона
        "test_mic": "Test Mic",
        "stop_test": "Stop Test",
        
        # Статус записи
        "recording_status": "Recording: {size:.1f} MB | {frames} frames",
        "saved_status": "Saved: {size:.1f} MB | {duration:.1f}s",
    },
    "ru": {
        # Основное окно
        "app_title": "HomRec (v1.2.0)",
        "live_preview": "ПРЕДПРОСМОТР",
        "ready": "Готов",
        "recording": "Запись",
        "paused": "Пауза",
        "fps": "FPS:",
        "resolution": "Разрешение:",
        "start": "▶ СТАРТ",
        "pause": "⏸ ПАУЗА",
        "stop": "■ СТОП",
        "resume": "▶ ПРОДОЛЖИТЬ",
        "recording_btn": "⏺ ЗАПИСЬ",
        
        # Audio Mixer
        "audio_mixer": "Аудио Микшер",
        "microphone": "Микрофон",
        "desktop_audio": "Системный звук",
        "mute": "Выкл",
        "unmute": "Вкл",
        "vol": "Громк:",
        "level": "Уровень:",
        "enable_desktop": "Включить системный звук",
        "stereo_mix_status": "(Не найден)",
        "stereo_available": "(Доступен)",
        "stereo_not_found": "(Не найден)",
        
        # Меню
        "file_menu": "Файл",
        "open_recordings": "Открыть папку записей",
        "exit": "Выход",
        "view_menu": "Вид",
        "statistics": "Статистика",
        "settings_menu": "Настройки",
        "preferences": "Параметры...",
        "theme_menu": "Тема",
        "dark_theme": "Темная",
        "light_theme": "Светлая",
        "performance_menu": "Режим",
        "ultra": "Ультра (60 FPS)",
        "turbo": "Турбо (30 FPS)",
        "balanced": "Средний (15 FPS)",
        "eco": "Эко (8 FPS)",
        "language_menu": "Язык",
        "english": "English",
        "russian": "Русский",
        
        # Статистика
        "stats_title": "Системная статистика",
        "stats_fps": "FPS:",
        "stats_cpu": "CPU:",
        "stats_ram": "RAM:",
        "stats_disk": "Диск:",
        "stats_bitrate": "Битрейт:",
        "close": "Закрыть",
        
        # Настройки
        "settings_title": "Настройки HomRec",
        "video_settings": "Видео",
        "quality": "Качество:",
        "mode": "Режим:",
        "advanced": "Дополнительно",
        "monitor": "Монитор:",
        "output": "Папка:",
        "browse": "Обзор",
        "features": "Функции",
        "countdown": "Отсчет (3 сек)",
        "timestamp": "Время на видео",
        "cursor": "Курсор",
        "tray_settings": "Трей",
        "minimize_to_tray": "Сворачивать в трей",
        "notification_settings": "Уведомления",
        "show_summary": "Показывать сводку",
        "save": "Сохранить",
        "cancel": "Отмена",
        "language_settings": "Язык",
        "select_language": "Выберите язык:",
        
        # Сообщения
        "warning": "Предупреждение",
        "error": "Ошибка",
        "info": "Информация",
        "folder_not_exist": "Папка записей не существует!",
        "recording_failed": "Запись не удалась!",
        "settings_saved": "Настройки сохранены!",
        "recording_saved": "Запись сохранена!",
        "open_folder": "Открыть папку?",
        "ffmpeg_not_found": "FFmpeg не найден - аудио отдельно\nСкачать: ffmpeg.org",
        
        # Статусы файлов
        "file": "Файл:",
        "size": "Размер:",
        "duration": "Длит:",
        "audio": "Аудио:",
        "mic_file": "Микрофон:",
        "system_file": "Система:",
        
        # Трей
        "tray_show": "Показать окно",
        "tray_start": "Начать запись",
        "tray_stop": "Остановить",
        "tray_open": "Открыть записи",
        "tray_exit": "Выход",
        
        # Тест микрофона
        "test_mic": "Тест",
        "stop_test": "Стоп",
        
        # Статус записи
        "recording_status": "Запись: {size:.1f} МБ | {frames} кадров",
        "saved_status": "Сохранено: {size:.1f} МБ | {duration:.1f}с",
    }
}

class AudioLevelMeter(tk.Canvas):
    """Виджет для отображения уровня громкости с градиентом"""
    def __init__(self, parent, width=180, height=20, **kwargs):
        super().__init__(parent, width=width, height=height, bg='#2a2a2a', highlightthickness=0, **kwargs)
        self.width = width
        self.height = height
        self.level = 0
        self.draw_meter()
    
    def draw_meter(self):
        self.delete("all")
        
        # Рисуем фон с закругленными углами
        self.create_rounded_rect(0, 0, self.width, self.height, 5, fill='#3a3a3a', outline='')
        
        # Рисуем уровень с градиентом
        bar_width = int((self.level / 100) * (self.width - 4))
        if bar_width > 0:
            # Градиент от зеленого к красному
            if self.level < 50:
                color = self.interpolate_color('#4ade80', '#fbbf24', self.level / 50)
            else:
                color = self.interpolate_color('#fbbf24', '#f87171', (self.level - 50) / 50)
            
            self.create_rounded_rect(2, 2, bar_width, self.height-2, 4, fill=color, outline='')
        
        # Рисуем деления
        for i in range(0, 101, 20):
            x = int((i / 100) * self.width)
            self.create_line(x, 0, x, self.height, fill='#4a4a4a', width=1)
    
    def create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = []
        for x in [x1, x2]:
            for y in [y1, y2]:
                points.extend([x, y])
        self.create_polygon(points, smooth=True, **kwargs)
    
    def interpolate_color(self, color1, color2, ratio):
        """Интерполяция между двумя цветами"""
        c1 = tuple(int(color1[i:i+2], 16) for i in (1, 3, 5))
        c2 = tuple(int(color2[i:i+2], 16) for i in (1, 3, 5))
        
        r = int(c1[0] + (c2[0] - c1[0]) * ratio)
        g = int(c1[1] + (c2[1] - c1[1]) * ratio)
        b = int(c1[2] + (c2[2] - c1[2]) * ratio)
        
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def set_level(self, level):
        self.level = max(0, min(100, level))
        self.draw_meter()

class SystemAudioRecorder:
    """Класс для записи системного звука (Stereo Mix)"""
    def __init__(self):
        self.audio_format = pyaudio.paInt16
        self.channels = 2
        self.rate = 44100
        self.chunk = 1024
        self.frames = []
        self.recording = False
        self.stream = None
        self.audio = None
        self.device_index = None
        
    def find_stereo_mix(self):
        """Поиск устройства Stereo Mix"""
        try:
            self.audio = pyaudio.PyAudio()
            for i in range(self.audio.get_device_count()):
                info = self.audio.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0 and 'stereo mix' in info['name'].lower():
                    self.device_index = i
                    return True
            return False
        except:
            return False
    
    def start(self):
        """Запуск записи системного звука"""
        try:
            if not self.audio:
                self.audio = pyaudio.PyAudio()
            
            self.frames = []
            self.recording = True
            
            # Пробуем найти Stereo Mix, если нет - используем default
            device_index = self.device_index if self.device_index else None
            
            self.stream = self.audio.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk
            )
            
            return True
        except Exception as e:
            print(f"[SystemAudio] Error: {e}")
            return False
    
    def read_chunk(self):
        """Чтение чанка аудио"""
        if self.stream and self.recording:
            try:
                return self.stream.read(self.chunk, exception_on_overflow=False)
            except:
                return None
        return None
    
    def stop(self):
        """Остановка записи"""
        self.recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio:
            self.audio.terminate()

class CustomMessageBox:
    """Кастомное окно с галочкой Don't show again и поддержкой языков"""
    @staticmethod
    def show(app, title_key, message_key, info_text, dont_show_var):
        dialog = tk.Toplevel()
        dialog.title(app.lang[title_key])
        dialog.geometry("450x350")
        dialog.configure(bg='#2a2a2a')
        dialog.transient()
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # Центрируем окно
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 225
        y = (dialog.winfo_screenheight() // 2) - 175
        dialog.geometry(f"+{x}+{y}")
        
        # Иконка
        icon_label = tk.Label(dialog, text="✓", font=("Segoe UI", 48), bg='#2a2a2a', fg='#4ade80')
        icon_label.pack(pady=(20, 5))
        
        # Заголовок
        tk.Label(dialog, text=app.lang[message_key], font=("Segoe UI", 14, "bold"),
                bg='#2a2a2a', fg='#ffffff').pack(pady=(0, 10))
        
        # Информация
        info_frame = tk.Frame(dialog, bg='#3a3a3a', relief='flat')
        info_frame.pack(pady=10, padx=20, fill='both', expand=True)
        
        info_label = tk.Label(info_frame, text=info_text, justify='left',
                              bg='#3a3a3a', fg='#e0e0e0',
                              font=("Consolas", 9))
        info_label.pack(pady=10, padx=10)
        
        # Галочка
        check_frame = tk.Frame(dialog, bg='#2a2a2a')
        check_frame.pack(pady=5)
        
        dont_show_check = tk.Checkbutton(check_frame, 
                                         text="Don't show again" if app.current_language == "en" else "Больше не показывать",
                                         variable=dont_show_var,
                                         bg='#2a2a2a', fg='#e0e0e0',
                                         selectcolor='#3a3a3a',
                                         activebackground='#2a2a2a',
                                         font=("Segoe UI", 9))
        dont_show_check.pack()
        
        # Кнопки
        btn_frame = tk.Frame(dialog, bg='#2a2a2a')
        btn_frame.pack(pady=10)
        
        result = {'value': False}
        
        def on_yes():
            result['value'] = True
            dialog.destroy()
        
        def on_no():
            result['value'] = False
            dialog.destroy()
        
        tk.Button(btn_frame, text=app.lang["open_folder"], 
                 command=on_yes,
                 bg='#3b82f6', fg='white',
                 font=("Segoe UI", 10),
                 relief='flat', padx=20, pady=5, width=12,
                 activebackground='#2563eb').pack(side='left', padx=5)
        
        tk.Button(btn_frame, text=app.lang["close"], 
                 command=on_no,
                 bg='#6b7280', fg='white',
                 font=("Segoe UI", 10),
                 relief='flat', padx=20, pady=5, width=12,
                 activebackground='#4b5563').pack(side='left', padx=5)
        
        dialog.wait_window()
        return result['value']

class AudioPanel:
    """Панель управления звуком с улучшенным дизайном"""
    def __init__(self, parent, app):
        self.app = app
        self.frame = tk.Frame(parent, bg='#2a2a2a')
        self.frame.pack(side='left', fill='both', expand=True, padx=2)
        
        # Заголовок
        title_frame = tk.Frame(self.frame, bg='#2a2a2a')
        title_frame.pack(fill='x', pady=(5, 10))
        
        tk.Label(title_frame, text="🎤 " + app.lang["audio_mixer"], 
                bg='#2a2a2a', fg='#3b82f6',
                font=("Segoe UI", 12, "bold")).pack()
        
        # Контейнер для двух колонок
        columns = tk.Frame(self.frame, bg='#2a2a2a')
        columns.pack(fill='both', expand=True)
        
        # Левая колонка - Микрофон
        left_col = tk.Frame(columns, bg='#2a2a2a', relief='flat', bd=1)
        left_col.pack(side='left', fill='both', expand=True, padx=5)
        
        self.create_mic_section(left_col)
        
        # Правая колонка - Системный звук
        right_col = tk.Frame(columns, bg='#2a2a2a', relief='flat', bd=1)
        right_col.pack(side='right', fill='both', expand=True, padx=5)
        
        self.create_system_section(right_col)
        
        self.is_testing = False
        self.audio_stream = None
        self.audio_p = None
        self.test_btn = None
    
    def create_mic_section(self, parent):
        """Создать секцию микрофона"""
        # Заголовок с иконкой
        header = tk.Frame(parent, bg='#2a2a2a')
        header.pack(fill='x', pady=(5, 5))
        
        tk.Label(header, text="🎤", bg='#2a2a2a', fg='#4ade80',
                font=("Segoe UI", 14)).pack(side='left', padx=(5, 2))
        
        tk.Label(header, text=self.app.lang["microphone"], bg='#2a2a2a', fg='#4ade80',
                font=("Segoe UI", 10, 'bold')).pack(side='left')
        
        self.mic_mute = tk.BooleanVar(value=False)
        self.mic_mute_btn = tk.Button(header, text=self.app.lang["mute"], 
                                      command=self.toggle_mic_mute,
                                      bg='#6b7280', fg='white',
                                      font=("Segoe UI", 8),
                                      relief='flat', width=5, height=1,
                                      cursor='hand2', activebackground='#4b5563')
        self.mic_mute_btn.pack(side='right', padx=5)
        
        # Ползунок громкости
        volume_frame = tk.Frame(parent, bg='#2a2a2a')
        volume_frame.pack(fill='x', pady=5, padx=5)
        
        tk.Label(volume_frame, text=self.app.lang["vol"], bg='#2a2a2a', fg='#e0e0e0',
                font=("Segoe UI", 8)).pack(side='left', padx=(0, 5))
        
        self.mic_volume = tk.Scale(volume_frame, from_=0, to=100, orient='horizontal',
                                   length=120, bg='#3a3a3a', fg='#e0e0e0',
                                   highlightthickness=0, troughcolor='#4a4a4a',
                                   command=self.on_mic_volume_change)
        self.mic_volume.set(80)
        self.mic_volume.pack(side='left', padx=5)
        
        self.mic_volume_label = tk.Label(volume_frame, text="80%", 
                                        bg='#2a2a2a', fg='#4ade80',
                                        font=("Segoe UI", 8, 'bold'))
        self.mic_volume_label.pack(side='left')
        
        # Индикатор
        meter_frame = tk.Frame(parent, bg='#2a2a2a')
        meter_frame.pack(fill='x', pady=5, padx=5)
        
        tk.Label(meter_frame, text=self.app.lang["level"], bg='#2a2a2a', fg='#e0e0e0',
                font=("Segoe UI", 8)).pack(side='left', padx=(0, 5))
        
        self.mic_meter = AudioLevelMeter(meter_frame, width=150, height=16)
        self.mic_meter.pack(side='left')
        
        # Кнопка теста микрофона
        self.test_btn = tk.Button(parent, text=self.app.lang["test_mic"],
                                  command=self.app.start_audio_test,
                                  bg='#3b82f6', fg='white',
                                  font=("Segoe UI", 8, "bold"),
                                  relief='flat', pady=4,
                                  activebackground='#2563eb',
                                  cursor='hand2')
        self.test_btn.pack(pady=5, padx=5, fill='x')
    
    def create_system_section(self, parent):
        """Создать секцию системного звука"""
        # Заголовок с иконкой
        header = tk.Frame(parent, bg='#2a2a2a')
        header.pack(fill='x', pady=(5, 5))
        
        tk.Label(header, text="🔊", bg='#2a2a2a', fg='#fbbf24',
                font=("Segoe UI", 14)).pack(side='left', padx=(5, 2))
        
        tk.Label(header, text=self.app.lang["desktop_audio"], bg='#2a2a2a', fg='#fbbf24',
                font=("Segoe UI", 10, 'bold')).pack(side='left')
        
        self.sys_mute = tk.BooleanVar(value=False)
        self.sys_mute_btn = tk.Button(header, text=self.app.lang["mute"],
                                      command=self.toggle_sys_mute,
                                      bg='#6b7280', fg='white',
                                      font=("Segoe UI", 8),
                                      relief='flat', width=5, height=1,
                                      cursor='hand2', activebackground='#4b5563')
        self.sys_mute_btn.pack(side='right', padx=5)
        
        # Ползунок громкости
        volume_frame = tk.Frame(parent, bg='#2a2a2a')
        volume_frame.pack(fill='x', pady=5, padx=5)
        
        tk.Label(volume_frame, text=self.app.lang["vol"], bg='#2a2a2a', fg='#e0e0e0',
                font=("Segoe UI", 8)).pack(side='left', padx=(0, 5))
        
        self.sys_volume = tk.Scale(volume_frame, from_=0, to=100, orient='horizontal',
                                   length=120, bg='#3a3a3a', fg='#e0e0e0',
                                   highlightthickness=0, troughcolor='#4a4a4a',
                                   command=self.on_sys_volume_change)
        self.sys_volume.set(80)
        self.sys_volume.pack(side='left', padx=5)
        
        self.sys_volume_label = tk.Label(volume_frame, text="80%",
                                        bg='#2a2a2a', fg='#fbbf24',
                                        font=("Segoe UI", 8, 'bold'))
        self.sys_volume_label.pack(side='left')
        
        # Индикатор
        meter_frame = tk.Frame(parent, bg='#2a2a2a')
        meter_frame.pack(fill='x', pady=5, padx=5)
        
        tk.Label(meter_frame, text=self.app.lang["level"], bg='#2a2a2a', fg='#e0e0e0',
                font=("Segoe UI", 8)).pack(side='left', padx=(0, 5))
        
        self.sys_meter = AudioLevelMeter(meter_frame, width=150, height=16)
        self.sys_meter.pack(side='left')
        
        # Чекбокс включения системного звука
        check_frame = tk.Frame(parent, bg='#2a2a2a')
        check_frame.pack(fill='x', pady=5, padx=5)
        
        self.sys_audio_enabled = tk.BooleanVar(value=False)
        self.sys_audio_check = tk.Checkbutton(check_frame, 
                                             text=self.app.lang["enable_desktop"],
                                             variable=self.sys_audio_enabled,
                                             bg='#2a2a2a', fg='#e0e0e0',
                                             selectcolor='#3a3a3a',
                                             activebackground='#2a2a2a',
                                             font=("Segoe UI", 8))
        self.sys_audio_check.pack(side='left')
        
        # Статус Stereo Mix
        self.sys_status_label = tk.Label(check_frame, 
                                        text=self.app.lang["stereo_mix_status"],
                                        bg='#2a2a2a', 
                                        fg='#f87171',
                                        font=("Segoe UI", 7))
        self.sys_status_label.pack(side='left', padx=5)
    
    def on_mic_volume_change(self, value):
        """Изменение громкости микрофона"""
        self.mic_volume_label.config(text=f"{int(float(value))}%")
    
    def on_sys_volume_change(self, value):
        """Изменение громкости системного звука"""
        self.sys_volume_label.config(text=f"{int(float(value))}%")
    
    def toggle_mic_mute(self):
        self.mic_mute.set(not self.mic_mute.get())
        self.mic_mute_btn.config(bg='#f87171' if self.mic_mute.get() else '#6b7280',
                                 text=self.app.lang["unmute"] if self.mic_mute.get() else self.app.lang["mute"])
    
    def toggle_sys_mute(self):
        self.sys_mute.set(not self.sys_mute.get())
        self.sys_mute_btn.config(bg='#f87171' if self.sys_mute.get() else '#6b7280',
                                 text=self.app.lang["unmute"] if self.sys_mute.get() else self.app.lang["mute"])
    
    def update_mic_level(self, level):
        """Обновление уровня микрофона"""
        self.mic_meter.set_level(level)
    
    def update_sys_level(self, level):
        """Обновление уровня системного звука"""
        self.sys_meter.set_level(level)
    
    def update_language(self):
        """Обновление языка в виджетах"""
        self.app.recreate_widgets()

class StatisticsWindow:
    """Окно статистики"""
    def __init__(self, parent, app):
        self.app = app
        self.window = tk.Toplevel(parent)
        self.window.title(app.lang["stats_title"])
        self.window.geometry("320x250")
        self.window.configure(bg='#2a2a2a')
        self.window.transient(parent)
        self.window.resizable(False, False)
        
        # Центрируем окно
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - 160
        y = (self.window.winfo_screenheight() // 2) - 125
        self.window.geometry(f"+{x}+{y}")
        
        self.create_widgets()
        self.update_stats()
    
    def create_widgets(self):
        # Заголовок
        title = tk.Label(self.window, text=self.app.lang["stats_title"], 
                        font=("Segoe UI", 12, "bold"),
                        bg='#2a2a2a', fg='#3b82f6')
        title.pack(pady=5)
        
        # Статистика
        stats_frame = tk.Frame(self.window, bg='#3a3a3a')
        stats_frame.pack(pady=5, padx=10, fill='both', expand=True)
        
        # FPS
        fps_frame = tk.Frame(stats_frame, bg='#3a3a3a')
        fps_frame.pack(fill='x', pady=2, padx=5)
        
        tk.Label(fps_frame, text=self.app.lang["stats_fps"], bg='#3a3a3a', fg='#e0e0e0',
                font=("Segoe UI", 9)).pack(side='left')
        
        self.fps_value = tk.Label(fps_frame, text="0.0", bg='#3a3a3a', fg='#4ade80',
                                  font=("Consolas", 9, 'bold'))
        self.fps_value.pack(side='right')
        
        # CPU Usage
        cpu_frame = tk.Frame(stats_frame, bg='#3a3a3a')
        cpu_frame.pack(fill='x', pady=2, padx=5)
        
        tk.Label(cpu_frame, text=self.app.lang["stats_cpu"], bg='#3a3a3a', fg='#e0e0e0',
                font=("Segoe UI", 9)).pack(side='left')
        
        self.cpu_value = tk.Label(cpu_frame, text="0%", bg='#3a3a3a', fg='#fbbf24',
                                 font=("Consolas", 9, 'bold'))
        self.cpu_value.pack(side='right')
        
        # RAM Usage
        ram_frame = tk.Frame(stats_frame, bg='#3a3a3a')
        ram_frame.pack(fill='x', pady=2, padx=5)
        
        tk.Label(ram_frame, text=self.app.lang["stats_ram"], bg='#3a3a3a', fg='#e0e0e0',
                font=("Segoe UI", 9)).pack(side='left')
        
        self.ram_value = tk.Label(ram_frame, text="0 MB", bg='#3a3a3a', fg='#3b82f6',
                                 font=("Consolas", 9, 'bold'))
        self.ram_value.pack(side='right')
        
        # Disk Space
        disk_frame = tk.Frame(stats_frame, bg='#3a3a3a')
        disk_frame.pack(fill='x', pady=2, padx=5)
        
        tk.Label(disk_frame, text=self.app.lang["stats_disk"], bg='#3a3a3a', fg='#e0e0e0',
                font=("Segoe UI", 9)).pack(side='left')
        
        self.disk_value = tk.Label(disk_frame, text="0 GB", bg='#3a3a3a', fg='#f87171',
                                  font=("Consolas", 9, 'bold'))
        self.disk_value.pack(side='right')
        
        # Bitrate
        bitrate_frame = tk.Frame(stats_frame, bg='#3a3a3a')
        bitrate_frame.pack(fill='x', pady=2, padx=5)
        
        tk.Label(bitrate_frame, text=self.app.lang["stats_bitrate"], bg='#3a3a3a', fg='#e0e0e0',
                font=("Segoe UI", 9)).pack(side='left')
        
        self.bitrate_value = tk.Label(bitrate_frame, text="0 kbps", bg='#3a3a3a', fg='#c084fc',
                                     font=("Consolas", 9, 'bold'))
        self.bitrate_value.pack(side='right')
        
        # Close button
        tk.Button(self.window, text=self.app.lang["close"], command=self.window.destroy,
                 bg='#6b7280', fg='white',
                 font=("Segoe UI", 9),
                 relief='flat', padx=15, pady=3,
                 activebackground='#4b5563').pack(pady=5)
    
    def update_stats(self):
        """Обновление статистики"""
        try:
            # FPS
            if self.app.recording and self.app.frame_count > 0:
                elapsed = time.time() - self.app.start_time
                fps = self.app.frame_count / elapsed if elapsed > 0 else 0
                self.fps_value.config(text=f"{fps:.1f}")
            else:
                self.fps_value.config(text="0.0")
            
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.cpu_value.config(text=f"{cpu_percent}%")
            
            # RAM
            ram = psutil.virtual_memory()
            ram_used = ram.used / (1024 * 1024)
            ram_total = ram.total / (1024 * 1024)
            self.ram_value.config(text=f"{int(ram_used)}/{int(ram_total)} MB")
            
            # Disk
            if os.path.exists(self.app.output_folder):
                disk = psutil.disk_usage(self.app.output_folder)
                free_gb = disk.free / (1024 * 1024 * 1024)
                self.disk_value.config(text=f"{free_gb:.1f} GB")
            
            # Bitrate (во время записи)
            if self.app.recording and os.path.exists(self.app.filename):
                file_size = os.path.getsize(self.app.filename)
                elapsed = time.time() - self.app.start_time
                if elapsed > 0:
                    bitrate = (file_size * 8) / (1000 * elapsed)  # kbps
                    self.bitrate_value.config(text=f"{int(bitrate)} kbps")
            else:
                self.bitrate_value.config(text="0 kbps")
            
        except:
            pass
        
        self.window.after(1000, self.update_stats)

class SettingsDialog:
    """Диалог настроек с поддержкой языков"""
    def __init__(self, parent, app):
        self.app = app
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(app.lang["settings_title"])
        self.dialog.geometry("550x500")
        self.dialog.configure(bg='#2a2a2a')
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Центрируем окно
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - 275
        y = (self.dialog.winfo_screenheight() // 2) - 250
        self.dialog.geometry(f"+{x}+{y}")
        
        self.create_widgets()
    
    def create_widgets(self):
        # Notebook для вкладок
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background='#2a2a2a')
        style.configure("TNotebook.Tab", background='#3a3a3a', foreground='#e0e0e0')
        style.map("TNotebook.Tab", background=[("selected", '#3b82f6')])
        
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Video Settings Tab
        video_tab = ttk.Frame(notebook)
        notebook.add(video_tab, text=self.app.lang["video_settings"])
        
        video_inner = tk.Frame(video_tab, bg='#2a2a2a')
        video_inner.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Quality control
        quality_frame = tk.Frame(video_inner, bg='#2a2a2a')
        quality_frame.pack(fill="x", pady=5)
        
        tk.Label(quality_frame, text=self.app.lang["quality"], 
                bg='#2a2a2a', fg='#e0e0e0',
                font=("Segoe UI", 9),
                width=10, anchor="w").pack(side="left")
        
        self.quality_var = tk.StringVar(value=str(self.app.quality))
        quality_scale = tk.Scale(quality_frame, from_=10, to=100, 
                                 orient="horizontal", length=200,
                                 variable=self.quality_var, 
                                 command=self.update_quality,
                                 bg='#3a3a3a', fg='#e0e0e0',
                                 highlightthickness=0, 
                                 troughcolor='#4a4a4a')
        quality_scale.pack(side="left", padx=5)
        
        tk.Label(quality_frame, text="%", 
                bg='#2a2a2a', fg='#e0e0e0',
                font=("Segoe UI", 9)).pack(side="left")
        
        # Resolution control
        res_frame = tk.Frame(video_inner, bg='#2a2a2a')
        res_frame.pack(fill="x", pady=5)
        
        tk.Label(res_frame, text=self.app.lang["resolution"].replace(":", ""), 
                bg='#2a2a2a', fg='#e0e0e0',
                font=("Segoe UI", 9),
                width=10, anchor="w").pack(side="left")
        
        self.scale_var = tk.StringVar(value=str(int(self.app.scale_factor * 100)))
        scale_scale = tk.Scale(res_frame, from_=25, to=100, 
                              orient="horizontal", length=200,
                              variable=self.scale_var,
                              command=self.update_scale,
                              bg='#3a3a3a', fg='#e0e0e0',
                              highlightthickness=0,
                              troughcolor='#4a4a4a')
        scale_scale.pack(side="left", padx=5)
        
        tk.Label(res_frame, text="%", 
                bg='#2a2a2a', fg='#e0e0e0',
                font=("Segoe UI", 9)).pack(side="left")
        
        # Performance mode
        mode_frame = tk.Frame(video_inner, bg='#2a2a2a')
        mode_frame.pack(fill="x", pady=10)
        
        tk.Label(mode_frame, text=self.app.lang["mode"], 
                bg='#2a2a2a', fg='#e0e0e0',
                font=("Segoe UI", 9),
                width=10, anchor="w").pack(side="left")
        
        self.mode_var = tk.StringVar(value=self.app.recording_mode)
        mode_combo = ttk.Combobox(mode_frame, textvariable=self.mode_var,
                                  values=["ultra", "turbo", "balanced", "eco"],
                                  width=12, state="readonly")
        mode_combo.pack(side="left", padx=5)
        mode_combo.bind("<<ComboboxSelected>>", self.on_mode_change)
        
        # Language Tab
        lang_tab = ttk.Frame(notebook)
        notebook.add(lang_tab, text=self.app.lang["language_settings"])
        
        lang_inner = tk.Frame(lang_tab, bg='#2a2a2a')
        lang_inner.pack(fill="both", expand=True, padx=10, pady=10)
        
        tk.Label(lang_inner, text=self.app.lang["select_language"],
                bg='#2a2a2a', fg='#e0e0e0',
                font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=5)
        
        self.lang_var = tk.StringVar(value=self.app.current_language)
        
        tk.Radiobutton(lang_inner, text="English", variable=self.lang_var, value="en",
                      bg='#2a2a2a', fg='#e0e0e0',
                      selectcolor='#3a3a3a',
                      activebackground='#2a2a2a',
                      font=("Segoe UI", 9)).pack(anchor="w", pady=2)
        
        tk.Radiobutton(lang_inner, text="Русский", variable=self.lang_var, value="ru",
                      bg='#2a2a2a', fg='#e0e0e0',
                      selectcolor='#3a3a3a',
                      activebackground='#2a2a2a',
                      font=("Segoe UI", 9)).pack(anchor="w", pady=2)
        
        # Advanced Tab
        adv_tab = ttk.Frame(notebook)
        notebook.add(adv_tab, text=self.app.lang["advanced"])
        
        adv_inner = tk.Frame(adv_tab, bg='#2a2a2a')
        adv_inner.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Monitor selection
        mon_frame = tk.Frame(adv_inner, bg='#2a2a2a')
        mon_frame.pack(fill="x", pady=5)
        
        tk.Label(mon_frame, text=self.app.lang["monitor"], 
                bg='#2a2a2a', fg='#e0e0e0',
                font=("Segoe UI", 9),
                width=10, anchor="w").pack(side="left")
        
        self.monitor_var = tk.StringVar(value=str(self.app.monitor_id))
        monitor_combo = ttk.Combobox(mon_frame, textvariable=self.monitor_var,
                                     values=[str(i) for i in range(1, len(self.app.sct.monitors))],
                                     width=8, state="readonly")
        monitor_combo.pack(side="left", padx=5)
        monitor_combo.bind("<<ComboboxSelected>>", self.on_monitor_change)
        
        # Output folder
        folder_frame = tk.Frame(adv_inner, bg='#2a2a2a')
        folder_frame.pack(fill="x", pady=5)
        
        tk.Label(folder_frame, text=self.app.lang["output"], 
                bg='#2a2a2a', fg='#e0e0e0',
                font=("Segoe UI", 9),
                width=10, anchor="w").pack(side="left")
        
        self.folder_label = tk.Label(folder_frame, text=os.path.basename(self.app.output_folder), 
                                     bg='#3a3a3a', fg='#3b82f6',
                                     font=("Consolas", 9),
                                     relief='flat', padx=5, pady=2)
        self.folder_label.pack(side="left", padx=5)
        
        tk.Button(folder_frame, text=self.app.lang["browse"], command=self.select_folder,
                 bg='#6b7280', fg='white',
                 font=("Segoe UI", 9),
                 relief='flat', padx=8,
                 activebackground='#4b5563').pack(side="left", padx=5)
        
        # Features
        features_frame = tk.Frame(adv_inner, bg='#2a2a2a')
        features_frame.pack(fill="x", pady=10)
        
        self.countdown_var = tk.BooleanVar(value=self.app.countdown_var.get())
        tk.Checkbutton(features_frame, text=self.app.lang["countdown"],
                      variable=self.countdown_var,
                      bg='#2a2a2a', fg='#e0e0e0',
                      selectcolor='#3a3a3a',
                      activebackground='#2a2a2a',
                      font=("Segoe UI", 9)).pack(anchor="w", pady=2)
        
        self.timestamp_var = tk.BooleanVar(value=self.app.timestamp_var.get())
        tk.Checkbutton(features_frame, text=self.app.lang["timestamp"],
                      variable=self.timestamp_var,
                      bg='#2a2a2a', fg='#e0e0e0',
                      selectcolor='#3a3a3a',
                      activebackground='#2a2a2a',
                      font=("Segoe UI", 9)).pack(anchor="w", pady=2)
        
        self.cursor_var = tk.BooleanVar(value=self.app.cursor_var.get())
        tk.Checkbutton(features_frame, text=self.app.lang["cursor"],
                      variable=self.cursor_var,
                      bg='#2a2a2a', fg='#e0e0e0',
                      selectcolor='#3a3a3a',
                      activebackground='#2a2a2a',
                      font=("Segoe UI", 9)).pack(anchor="w", pady=2)
        
        self.minimize_to_tray_var = tk.BooleanVar(value=self.app.minimize_to_tray)
        tk.Checkbutton(features_frame, text=self.app.lang["minimize_to_tray"],
                      variable=self.minimize_to_tray_var,
                      bg='#2a2a2a', fg='#e0e0e0',
                      selectcolor='#3a3a3a',
                      activebackground='#2a2a2a',
                      font=("Segoe UI", 9)).pack(anchor="w", pady=2)
        
        self.show_summary_var = tk.BooleanVar(value=self.app.show_summary)
        tk.Checkbutton(features_frame, text=self.app.lang["show_summary"],
                      variable=self.show_summary_var,
                      bg='#2a2a2a', fg='#e0e0e0',
                      selectcolor='#3a3a3a',
                      activebackground='#2a2a2a',
                      font=("Segoe UI", 9)).pack(anchor="w", pady=2)
        
        # Кнопки
        btn_frame = tk.Frame(self.dialog, bg='#2a2a2a')
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Button(btn_frame, text=self.app.lang["save"], command=self.save_settings,
                 bg='#3b82f6', fg='white',
                 font=("Segoe UI", 10, "bold"),
                 relief='flat', padx=15, pady=5,
                 activebackground='#2563eb').pack(side="right", padx=5)
        
        tk.Button(btn_frame, text=self.app.lang["cancel"], command=self.dialog.destroy,
                 bg='#6b7280', fg='white',
                 font=("Segoe UI", 10),
                 relief='flat', padx=15, pady=5,
                 activebackground='#4b5563').pack(side="right", padx=5)
    
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
        new_lang = self.lang_var.get()
        if new_lang != self.app.current_language:
            self.app.current_language = new_lang
            self.app.lang = LANGUAGES[new_lang]
            self.app.update_ui_language()
        
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
        self.app.minimize_to_tray = self.minimize_to_tray_var.get()
        self.app.show_summary = self.show_summary_var.get()
        self.app.res_label.config(text=f"{self.app.lang['resolution']} {self.app.record_width}x{self.app.record_height}")
        self.app.save_settings(silent=True)
        self.dialog.destroy()
        messagebox.showinfo(self.app.lang["info"], self.app.lang["settings_saved"])

class HomRecScreen:
    def __init__(self, root):
        self.root = root
        self.current_language = "en"
        self.lang = LANGUAGES[self.current_language]
        
        self.root.title(self.lang["app_title"])
        self.root.geometry("1300x750")
        self.root.minsize(1200, 650)
        self.root.configure(bg='#1a1a1a')
        
        self.set_app_icon()
        
        self.current_theme = "dark"
        self.colors = {
            "bg": "#1a1a1a",
            "surface": "#2a2a2a",
            "surface_light": "#3a3a3a",
            "accent": "#3b82f6",
            "success": "#4ade80",
            "warning": "#fbbf24",
            "error": "#f87171",
            "preview_bg": "#000000",
            "text": "#e0e0e0",
            "text_secondary": "#a0a0a0"
        }
        
        self.sct = mss.mss()
        
        self.audio_recording = False
        self.audio_thread = None
        self.audio_frames = []
        self.audio_stream = None
        self.audio_p = None
        self.audio_testing = False
        
        self.sys_audio_recording = False
        self.sys_audio_thread = None
        self.sys_audio_frames = []
        self.sys_audio_recorder = None
        
        self.scale_factor = 0.75
        self.output_folder = "recordings"
        self.quality = 70
        self.target_fps = 15
        self.recording_mode = "balanced"
        self.show_summary = True
        self.minimize_to_tray = False
        
        self.countdown_var = tk.BooleanVar(value=True)
        self.timestamp_var = tk.BooleanVar(value=False)
        self.cursor_var = tk.BooleanVar(value=False)
        
        self.tray_icon = None
        self.tray_thread = None
        self.preview_width = 900
        self.preview_height = 500
        self.stats_window = None
        
        self.load_settings()
        
        self.recording = False
        self.paused = False
        self.out = None
        self.frame_count = 0
        self.start_time = 0
        self.recording_thread = None
        self.stop_flag = False
        
        self.monitor_id = 1
        self.update_monitor_info()
        
        os.makedirs(self.output_folder, exist_ok=True)
        
        self.create_menu()
        self.create_widgets()
        self.update_preview()
        
        self.root.bind('<Configure>', self.on_window_resize)
        self.root.bind('<F9>', lambda e: self.toggle_recording())
        self.root.bind('<F10>', lambda e: self.toggle_pause() if self.recording else None)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        print(f"[HomRec v1.2.0] Started")
    
    def update_ui_language(self):
        self.root.title(self.lang["app_title"])
        self.recreate_widgets()
    
    def create_menu(self):
        menubar = tk.Menu(self.root, bg='#2a2a2a', fg='#e0e0e0')
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0, bg='#2a2a2a', fg='#e0e0e0')
        menubar.add_cascade(label=self.lang["file_menu"], menu=file_menu)
        file_menu.add_command(label=self.lang["open_recordings"], command=self.open_recordings)
        file_menu.add_separator()
        file_menu.add_command(label=self.lang["exit"], command=self.on_closing)
        
        view_menu = tk.Menu(menubar, tearoff=0, bg='#2a2a2a', fg='#e0e0e0')
        menubar.add_cascade(label=self.lang["view_menu"], menu=view_menu)
        view_menu.add_command(label=self.lang["statistics"], command=self.show_statistics)
        
        settings_menu = tk.Menu(menubar, tearoff=0, bg='#2a2a2a', fg='#e0e0e0')
        menubar.add_cascade(label=self.lang["settings_menu"], menu=settings_menu)
        settings_menu.add_command(label=self.lang["preferences"], command=self.open_settings)
        settings_menu.add_separator()
        
        lang_menu = tk.Menu(settings_menu, tearoff=0, bg='#2a2a2a', fg='#e0e0e0')
        settings_menu.add_cascade(label=self.lang["language_menu"], menu=lang_menu)
        lang_menu.add_command(label="English", command=lambda: self.change_language("en"))
        lang_menu.add_command(label="Русский", command=lambda: self.change_language("ru"))
        
        theme_menu = tk.Menu(settings_menu, tearoff=0, bg='#2a2a2a', fg='#e0e0e0')
        settings_menu.add_cascade(label=self.lang["theme_menu"], menu=theme_menu)
        theme_menu.add_command(label=self.lang["dark_theme"], command=lambda: self.change_theme("dark"))
        theme_menu.add_command(label=self.lang["light_theme"], command=lambda: self.change_theme("light"))
        
        perf_menu = tk.Menu(settings_menu, tearoff=0, bg='#2a2a2a', fg='#e0e0e0')
        settings_menu.add_cascade(label=self.lang["performance_menu"], menu=perf_menu)
        perf_menu.add_command(label=self.lang["ultra"], command=lambda: self.set_mode("ultra"))
        perf_menu.add_command(label=self.lang["turbo"], command=lambda: self.set_mode("turbo"))
        perf_menu.add_command(label=self.lang["balanced"], command=lambda: self.set_mode("balanced"))
        perf_menu.add_command(label=self.lang["eco"], command=lambda: self.set_mode("eco"))
    
    def change_language(self, lang):
        if lang != self.current_language:
            self.current_language = lang
            self.lang = LANGUAGES[lang]
            self.update_ui_language()
            self.save_settings(silent=True)
    
    def show_statistics(self):
        if self.stats_window is None or not self.stats_window.winfo_exists():
            self.stats_window = StatisticsWindow(self.root, self)
    
    def create_tray_icon(self):
        if self.tray_icon:
            return
        
        icon_size = (64, 64)
        icon_image = Image.new('RGBA', icon_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(icon_image)
        
        if self.recording:
            draw.ellipse([12, 12, 52, 52], fill="#f87171", outline="#ffffff", width=2)
            draw.ellipse([22, 22, 42, 42], fill="#1a1a1a")
        else:
            draw.rectangle([10, 20, 54, 44], fill="#3b82f6", outline="#ffffff", width=2)
            draw.ellipse([25, 25, 39, 39], fill="#1a1a1a", outline="#ffffff", width=2)
            draw.ellipse([29, 29, 35, 35], fill="#3b82f6")
            draw.rectangle([45, 15, 50, 20], fill="#fbbf24")
        
        menu = (
            MenuItem(self.lang["tray_show"], self.show_window),
            MenuItem(self.lang["tray_start"], self.tray_start_recording),
            MenuItem(self.lang["tray_stop"], self.tray_stop_recording, enabled=lambda: self.recording),
            MenuItem(self.lang["tray_open"], self.open_recordings),
            MenuItem(self.lang["tray_exit"], self.quit_app),
        )
        
        self.tray_icon = Icon("HomRec", icon_image, "HomRec", menu)
        self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        self.tray_thread.start()
    
    def update_tray_icon(self):
        if self.tray_icon:
            icon_size = (64, 64)
            icon_image = Image.new('RGBA', icon_size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(icon_image)
            
            if self.recording:
                draw.ellipse([12, 12, 52, 52], fill="#f87171", outline="#ffffff", width=2)
                if int(time.time() * 2) % 2 == 0:
                    draw.ellipse([27, 27, 37, 37], fill="#ffffff")
                else:
                    draw.ellipse([27, 27, 37, 37], fill="#1a1a1a")
            else:
                draw.rectangle([10, 20, 54, 44], fill="#3b82f6", outline="#ffffff", width=2)
                draw.ellipse([25, 25, 39, 39], fill="#1a1a1a", outline="#ffffff", width=2)
                draw.ellipse([29, 29, 35, 35], fill="#3b82f6")
                draw.rectangle([45, 15, 50, 20], fill="#fbbf24")
            
            self.tray_icon.icon = icon_image
    
    def show_window(self):
        self.root.deiconify()
        self.root.lift()
    
    def tray_start_recording(self):
        if not self.recording:
            self.root.after(0, self.start_recording)
    
    def tray_stop_recording(self):
        if self.recording:
            self.root.after(0, self.stop_recording)
    
    def quit_app(self):
        self.root.after(0, self.on_closing)
    
    def check_ffmpeg(self):
        try:
            if os.path.exists("ffmpeg.exe"):
                return True
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            return True
        except:
            return False
    
    def merge_audio_video(self, video_file, audio_file, audio_file2=None):
        if not os.path.exists(audio_file):
            return False
        
        output_file = video_file.replace('.mp4', '_temp.mp4')
        
        try:
            ffmpeg_path = 'ffmpeg'
            if os.path.exists("ffmpeg.exe"):
                ffmpeg_path = "ffmpeg.exe"
            
            if audio_file2 and os.path.exists(audio_file2):
                cmd = [
                    ffmpeg_path,
                    '-i', video_file,
                    '-i', audio_file,
                    '-i', audio_file2,
                    '-filter_complex', '[1:a][2:a]amix=inputs=2:duration=longest[a]',
                    '-map', '0:v:0',
                    '-map', '[a]',
                    '-c:v', 'copy',
                    '-c:a', 'aac',
                    '-shortest',
                    '-y',
                    output_file
                ]
            else:
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
                if audio_file2 and os.path.exists(audio_file2):
                    os.remove(audio_file2)
                os.rename(output_file, video_file)
                return True
            else:
                return False
                
        except:
            return False
    
    def set_app_icon(self):
        try:
            icon_size = (64, 64)
            icon_image = Image.new('RGBA', icon_size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(icon_image)
            draw.rectangle([10, 20, 54, 44], fill="#3b82f6", outline="#ffffff", width=2)
            draw.ellipse([25, 25, 39, 39], fill="#1a1a1a", outline="#ffffff", width=2)
            draw.ellipse([29, 29, 35, 35], fill="#3b82f6")
            draw.rectangle([45, 15, 50, 20], fill="#fbbf24")
            icon_photo = ImageTk.PhotoImage(icon_image)
            self.root.iconphoto(True, icon_photo)
            if sys.platform == "win32":
                myappid = 'homrec.screen.recorder.v1.2.0'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            pass
    
    def on_window_resize(self, event):
        if event.widget == self.root:
            self.update_preview_size()
    
    def update_preview_size(self):
        try:
            preview_height = self.root.winfo_height() - 250
            preview_width = self.root.winfo_width() - 250
            if preview_width > 0 and preview_height > 0:
                self.preview_width = max(600, min(preview_width - 40, 1280))
                self.preview_height = max(350, min(preview_height - 40, 720))
        except:
            pass
    
    def get_theme_colors(self, theme):
        if theme == "dark":
            return {
                "bg": "#1a1a1a",
                "surface": "#2a2a2a",
                "surface_light": "#3a3a3a",
                "accent": "#3b82f6",
                "success": "#4ade80",
                "warning": "#fbbf24",
                "error": "#f87171",
                "preview_bg": "#000000",
                "text": "#e0e0e0",
                "text_secondary": "#a0a0a0"
            }
        else:
            return {
                "bg": "#f5f5f5",
                "surface": "#e5e5e5",
                "surface_light": "#d4d4d4",
                "accent": "#2563eb",
                "success": "#22c55e",
                "warning": "#f59e0b",
                "error": "#ef4444",
                "preview_bg": "#ffffff",
                "text": "#1f2937",
                "text_secondary": "#6b7280"
            }
    
    def apply_theme(self):
        self.root.configure(bg=self.colors["bg"])
    
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
        self.res_label.config(text=f"{self.lang['resolution']} {self.record_width}x{self.record_height}")
    
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
                    self.current_language = settings.get("language", "en")
                    self.lang = LANGUAGES[self.current_language]
                    self.countdown_var.set(settings.get("countdown", True))
                    self.timestamp_var.set(settings.get("timestamp", False))
                    self.cursor_var.set(settings.get("cursor", False))
                    self.show_summary = settings.get("show_summary", True)
                    self.minimize_to_tray = settings.get("minimize_to_tray", False)
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
            "language": self.current_language,
            "countdown": self.countdown_var.get(),
            "timestamp": self.timestamp_var.get(),
            "cursor": self.cursor_var.get(),
            "show_summary": self.show_summary,
            "minimize_to_tray": self.minimize_to_tray
        }
        with open("homrec_settings.json", "w") as f:
            json.dump(settings, f, indent=2)
        if not silent:
            messagebox.showinfo(self.lang["info"], self.lang["settings_saved"])
    
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
        # Main container
        main_container = tk.Frame(self.root, bg=self.colors["bg"])
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Preview
        preview_container = tk.Frame(main_container, bg=self.colors["surface_light"], relief='flat', bd=1)
        preview_container.pack(fill="both", expand=True)
        
        preview_label_title = tk.Label(preview_container, text=self.lang["live_preview"], 
                                      bg=self.colors["surface_light"], 
                                      fg=self.colors["text_secondary"],
                                      font=("Segoe UI", 9))
        preview_label_title.pack(anchor="nw", padx=5, pady=2)
        
        preview_frame = tk.Frame(preview_container, bg=self.colors["preview_bg"])
        preview_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.preview_label = tk.Label(preview_frame, bg=self.colors["preview_bg"])
        self.preview_label.pack(fill="both", expand=True)
        
        # Bottom panel
        bottom_panel = tk.Frame(main_container, bg=self.colors["bg"], height=200)
        bottom_panel.pack(fill="x", pady=(5, 0))
        bottom_panel.pack_propagate(False)
        
        # Audio Mixer
        audio_frame = tk.Frame(bottom_panel, bg=self.colors["bg"])
        audio_frame.pack(side='left', fill='both', expand=True)
        
        self.audio_panel = AudioPanel(audio_frame, self)
        
        # Right panel
        right_bottom = tk.Frame(bottom_panel, bg=self.colors["surface"], width=240)
        right_bottom.pack(side='right', fill='y', padx=(5, 0))
        right_bottom.pack_propagate(False)
        
        # Control buttons
        btn_frame = tk.Frame(right_bottom, bg=self.colors["surface"])
        btn_frame.pack(pady=10, padx=10, fill='x')
        
        self.record_btn = tk.Button(btn_frame, text=self.lang["start"], 
                                   command=self.start_with_countdown,
                                   bg=self.colors["success"], fg='white',
                                   font=("Segoe UI", 11, "bold"),
                                   relief='flat', height=2,
                                   cursor='hand2', activebackground='#22c55e')
        self.record_btn.pack(fill="x", pady=2)
        
        self.pause_btn = tk.Button(btn_frame, text=self.lang["pause"], 
                                  command=self.toggle_pause,
                                  bg=self.colors["warning"], fg='white',
                                  font=("Segoe UI", 11, "bold"),
                                  state="disabled", relief='flat', height=2,
                                  cursor='hand2', activebackground='#f59e0b')
        self.pause_btn.pack(fill="x", pady=2)
        
        self.stop_btn = tk.Button(btn_frame, text=self.lang["stop"], 
                                 command=self.stop_recording,
                                 bg=self.colors["error"], fg='white',
                                 font=("Segoe UI", 11, "bold"),
                                 state="disabled", relief='flat', height=2,
                                 cursor='hand2', activebackground='#ef4444')
        self.stop_btn.pack(fill="x", pady=2)
        
        # Separator
        ttk.Separator(right_bottom, orient='horizontal').pack(fill='x', pady=5, padx=10)
        
        # Status
        status_frame = tk.Frame(right_bottom, bg=self.colors["surface"])
        status_frame.pack(pady=5, padx=10, fill="x")
        
        status_row = tk.Frame(status_frame, bg=self.colors["surface"])
        status_row.pack(fill="x", pady=2)
        
        self.status_icon = tk.Label(status_row, text="●", 
                                   fg=self.colors["error"], 
                                   bg=self.colors["surface"], 
                                   font=("Arial", 12))
        self.status_icon.pack(side="left", padx=(0, 5))
        
        self.status_label = tk.Label(status_row, text=self.lang["ready"], 
                                    bg=self.colors["surface"], 
                                    fg=self.colors["text"],
                                    font=("Segoe UI", 9))
        self.status_label.pack(side="left")
        
        # Timer
        timer_frame = tk.Frame(right_bottom, bg=self.colors["surface"])
        timer_frame.pack(pady=5, padx=10, fill="x")
        
        self.time_label = tk.Label(timer_frame, text="00:00:00", 
                                   font=("Consolas", 14, "bold"),
                                   bg=self.colors["surface"], 
                                   fg=self.colors["accent"])
        self.time_label.pack()
        
        # FPS
        fps_frame = tk.Frame(right_bottom, bg=self.colors["surface"])
        fps_frame.pack(pady=2, padx=10, fill="x")
        
        tk.Label(fps_frame, text=self.lang["fps"], bg=self.colors["surface"], fg=self.colors["text_secondary"],
                font=("Segoe UI", 8)).pack(side='left')
        
        self.fps_label = tk.Label(fps_frame, text="0", 
                                 bg=self.colors["surface"], 
                                 fg=self.colors["text"],
                                 font=("Consolas", 8))
        self.fps_label.pack(side='right')
        
        # Resolution
        res_frame = tk.Frame(right_bottom, bg=self.colors["surface"])
        res_frame.pack(pady=2, padx=10, fill="x")
        
        tk.Label(res_frame, text=self.lang["resolution"], bg=self.colors["surface"], fg=self.colors["text_secondary"],
                font=("Segoe UI", 8)).pack(side='left')
        
        self.res_label = tk.Label(res_frame, 
                                 text=f"{self.record_width}x{self.record_height}", 
                                 bg=self.colors["surface"], 
                                 fg=self.colors["text"],
                                 font=("Consolas", 8))
        self.res_label.pack(side='right')
        
        # Bottom bar
        bottom_bar = tk.Frame(self.root, bg=self.colors["surface"], height=25)
        bottom_bar.pack(side="bottom", fill="x")
        
        self.file_label = tk.Label(bottom_bar, text=self.lang["ready"], 
                                   bg=self.colors["surface"], 
                                   fg=self.colors["text_secondary"],
                                   font=("Segoe UI", 8))
        self.file_label.pack(side="left", padx=10)
        
        tk.Label(bottom_bar, text="HomRec", 
                bg=self.colors["surface"], 
                fg=self.colors["accent"],
                font=("Segoe UI", 8, "bold")).pack(side="right", padx=10)
        
        self.update_preview_size()
        self.check_stereo_mix()
    
    def check_stereo_mix(self):
        try:
            p = pyaudio.PyAudio()
            found = False
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0 and 'stereo mix' in info['name'].lower():
                    found = True
                    break
            p.terminate()
            
            if found:
                self.audio_panel.sys_status_label.config(text=self.lang["stereo_available"], fg='#4ade80')
            else:
                self.audio_panel.sys_status_label.config(text=self.lang["stereo_not_found"], fg='#f87171')
        except:
            self.audio_panel.sys_status_label.config(text="(Check failed)", fg='#f87171')
    
    def start_audio_test(self):
        if not hasattr(self, 'audio_panel') or self.audio_panel is None:
            return
        
        if not hasattr(self.audio_panel, 'test_btn') or self.audio_panel.test_btn is None:
            return
        
        if hasattr(self, 'audio_testing') and self.audio_testing:
            self.stop_audio_test()
        
        self.audio_testing = True
        self.audio_panel.test_btn.config(text=self.lang["stop_test"], bg='#f87171')
        
        try:
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
                        self.root.after(0, lambda l=level: self.audio_panel.update_mic_level(l))
                    except:
                        pass
                    time.sleep(0.05)
            
            self.test_thread = threading.Thread(target=test_thread, daemon=True)
            self.test_thread.start()
            self.root.after(3000, self.stop_audio_test)
            
        except Exception as e:
            print(f"Test error: {e}")
            self.stop_audio_test()
    
    def stop_audio_test(self):
        self.audio_testing = False
        
        if hasattr(self, 'audio_panel') and self.audio_panel is not None:
            if hasattr(self.audio_panel, 'test_btn') and self.audio_panel.test_btn is not None:
                self.audio_panel.test_btn.config(text=self.lang["test_mic"], bg='#3b82f6')
        
        if hasattr(self, 'audio_stream') and self.audio_stream:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            except:
                pass
        
        if hasattr(self, 'audio_p') and self.audio_p:
            try:
                self.audio_p.terminate()
            except:
                pass
        
        if hasattr(self, 'audio_panel') and self.audio_panel is not None:
            self.audio_panel.update_mic_level(0)
    
    def select_folder(self):
        folder = filedialog.askdirectory(initialdir=self.output_folder)
        if folder:
            self.output_folder = folder
            self.save_settings(silent=True)
    
    def open_recordings(self):
        if os.path.exists(self.output_folder):
            os.startfile(self.output_folder)
        else:
            messagebox.showwarning(self.lang["warning"], self.lang["folder_not_exist"])
    
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
        countdown_window.geometry("200x150")
        countdown_window.configure(bg=self.colors["bg"])
        countdown_window.overrideredirect(True)
        
        countdown_window.update_idletasks()
        x = (countdown_window.winfo_screenwidth() // 2) - 100
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
                label.config(text="✓", fg=self.colors["success"])
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
                    draw.ellipse([10, 10, 30, 30], fill=self.colors["error"])
                else:
                    draw.rectangle([10, 10, 30, 30], fill=self.colors["warning"])
            
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
                            rms = audioop.rms(data, 2)
                            level = min(100, int(rms / 300))
                            self.root.after(0, lambda l=level: self.audio_panel.update_mic_level(l))
                        except:
                            pass
                    else:
                        time.sleep(0.01)
            
            self.audio_thread = threading.Thread(target=record_audio, daemon=True)
            self.audio_thread.start()
            
        except Exception as e:
            print(f"[HomRec] Microphone error: {e}")
            self.audio_recording = False
    
    def start_system_audio_recording(self):
        try:
            self.sys_audio_recorder = SystemAudioRecorder()
            if self.sys_audio_recorder.start():
                self.sys_audio_recording = True
                self.sys_audio_frames = []
                
                def record_system_audio():
                    while self.sys_audio_recording and not self.stop_flag:
                        if not self.paused and not self.audio_panel.sys_mute.get():
                            data = self.sys_audio_recorder.read_chunk()
                            if data:
                                self.sys_audio_frames.append(data)
                                rms = audioop.rms(data, 2)
                                level = min(100, int(rms / 500))
                                self.root.after(0, lambda l=level: self.audio_panel.update_sys_level(l))
                        else:
                            time.sleep(0.01)
                
                self.sys_audio_thread = threading.Thread(target=record_system_audio, daemon=True)
                self.sys_audio_thread.start()
                return True
            else:
                return False
        except Exception as e:
            print(f"[HomRec] System audio error: {e}")
            return False
    
    def stop_audio_recording(self):
        self.audio_recording = False
        
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=2)
        
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
        
        if self.audio_p:
            self.audio_p.terminate()
        
        if self.audio_frames and not self.audio_panel.mic_mute.get():
            audio_filename = self.filename.replace('.mp4', '_mic.wav')
            wf = wave.open(audio_filename, 'wb')
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(44100)
            wf.writeframes(b''.join(self.audio_frames))
            wf.close()
            return audio_filename
        return None
    
    def stop_system_audio_recording(self):
        self.sys_audio_recording = False
        
        if self.sys_audio_thread and self.sys_audio_thread.is_alive():
            self.sys_audio_thread.join(timeout=2)
        
        if self.sys_audio_recorder:
            self.sys_audio_recorder.stop()
        
        if self.sys_audio_frames and not self.audio_panel.sys_mute.get():
            audio_filename = self.filename.replace('.mp4', '_system.wav')
            wf = wave.open(audio_filename, 'wb')
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(44100)
            wf.writeframes(b''.join(self.sys_audio_frames))
            wf.close()
            return audio_filename
        return None
    
    def start_recording(self):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.filename = f"{self.output_folder}/HomRec_{timestamp}.mp4"
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.out = cv2.VideoWriter(
                self.filename, fourcc, self.target_fps, 
                (self.record_width, self.record_height)
            )
            
            if not self.out.isOpened():
                raise Exception("Cannot create video file")
            
            self.start_audio_recording()
            
            if self.audio_panel.sys_audio_enabled.get():
                self.start_system_audio_recording()
            
            self.recording = True
            self.paused = False
            self.frame_count = 0
            self.start_time = time.time()
            self.stop_flag = False
            
            self.record_btn.config(text=self.lang["recording_btn"], bg=self.colors["error"])
            self.pause_btn.config(state="normal")
            self.stop_btn.config(state="normal")
            self.status_icon.config(fg=self.colors["success"])
            self.status_label.config(text=self.lang["recording"])
            
            self.create_tray_icon()
            self.recording_thread = threading.Thread(target=self._record_thread, daemon=True)
            self.recording_thread.start()
            self._update_stats()
            
        except Exception as e:
            messagebox.showerror(self.lang["error"], f"Failed: {str(e)}")
    
    def _record_thread(self):
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
        
        frame_duration = 1.0 / self.target_fps
        start_time = time.time()
        frame_count = 0
        
        while self.recording and not self.stop_flag:
            if self.paused:
                time.sleep(0.05)
                continue
            
            expected_time = start_time + (frame_count * frame_duration)
            current_time = time.time()
            
            if current_time < expected_time:
                time.sleep(expected_time - current_time)
                continue
            
            try:
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
                            cv2.circle(frame, (sx, sy), 15, (0, 255, 255), 2)
                    except:
                        pass
                
                if add_timestamp:
                    ts = datetime.now().strftime("%H:%M:%S")
                    cv2.putText(frame, ts, (10, 30), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                if self.out and self.out.isOpened():
                    self.out.write(frame)
                    frame_count += 1
                    self.frame_count = frame_count
                
                self.update_tray_icon()
                
            except Exception as e:
                print(f"Frame error: {e}")
        
        try:
            sct_local.close()
        except:
            pass
        
        self.update_tray_icon()
    
    def _update_stats(self):
        if self.recording:
            try:
                elapsed = time.time() - self.start_time
                if elapsed > 0 and self.frame_count > 0:
                    actual_fps = self.frame_count / elapsed
                    self.fps_label.config(text=f"{actual_fps:.1f}")
                
                h = int(elapsed // 3600)
                m = int((elapsed % 3600) // 60)
                s = int(elapsed % 60)
                self.time_label.config(text=f"{h:02d}:{m:02d}:{s:02d}")
                
                if os.path.exists(self.filename):
                    size = os.path.getsize(self.filename) / (1024 * 1024)
                    status_text = self.lang["recording_status"].format(size=size, frames=self.frame_count)
                    self.file_label.config(text=status_text)
            except:
                pass
            
            self.root.after(500, self._update_stats)
    
    def stop_recording(self):
        print("Stopping recording...")
        
        self.recording = False
        self.stop_flag = True
        
        mic_file = None
        if self.audio_recording:
            mic_file = self.stop_audio_recording()
        
        sys_file = None
        if self.sys_audio_recording:
            sys_file = self.stop_system_audio_recording()
        
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=3)
        
        time.sleep(0.3)
        
        if self.out:
            try:
                self.out.release()
            except:
                pass
        
        has_ffmpeg = self.check_ffmpeg()
        audio_merged = False
        
        if mic_file and sys_file and os.path.exists(self.filename):
            if has_ffmpeg:
                audio_merged = self.merge_audio_video(self.filename, mic_file, sys_file)
        elif mic_file and os.path.exists(self.filename):
            if has_ffmpeg:
                audio_merged = self.merge_audio_video(self.filename, mic_file)
        elif sys_file and os.path.exists(self.filename) and self.audio_panel.sys_audio_enabled.get():
            if has_ffmpeg:
                audio_merged = self.merge_audio_video(self.filename, sys_file)
        
        self.record_btn.config(text=self.lang["start"], bg=self.colors["success"])
        self.pause_btn.config(state="disabled", text=self.lang["pause"])
        self.stop_btn.config(state="disabled")
        self.status_icon.config(fg=self.colors["error"])
        self.status_label.config(text=self.lang["ready"])
        self.time_label.config(text="00:00:00")
        
        if self.frame_count > 0 and os.path.exists(self.filename):
            actual_duration = time.time() - self.start_time
            size = os.path.getsize(self.filename) / (1024 * 1024)
            actual_fps = self.frame_count / actual_duration
            
            saved_text = self.lang["saved_status"].format(size=size, duration=actual_duration)
            self.file_label.config(text=saved_text)
            
            audio_status = []
            if mic_file:
                audio_status.append("Mic")
            if sys_file:
                audio_status.append("System")
            audio_status_str = " + ".join(audio_status) if audio_status else "No"
            if audio_merged:
                audio_status_str += " (Merged)"
            
            info_lines = [
                f"{self.lang['file']} {os.path.basename(self.filename)}",
                f"{self.lang['size']} {size:.1f} MB",
                f"{self.lang['duration']} {actual_duration:.1f}s",
                f"{self.lang['resolution']} {self.record_width}x{self.record_height}",
                f"{self.lang['stats_fps']} {actual_fps:.1f}",
                f"{self.lang['audio']} {audio_status_str}"
            ]
            
            if mic_file and not audio_merged:
                info_lines.append(f"{self.lang['mic_file']} {os.path.basename(mic_file)}")
            if sys_file and not audio_merged:
                info_lines.append(f"{self.lang['system_file']} {os.path.basename(sys_file)}")
            
            if not has_ffmpeg and (mic_file or sys_file):
                info_lines.append("")
                info_lines.append(self.lang["ffmpeg_not_found"])
            
            info_text = "\n".join(info_lines)
            
            if self.show_summary:
                dont_show_var = tk.BooleanVar(value=False)
                result = CustomMessageBox.show(
                    self,
                    "recording_saved",
                    "recording_saved",
                    info_text,
                    dont_show_var
                )
                
                if dont_show_var.get():
                    self.show_summary = False
                    self.save_settings(silent=True)
                
                if result:
                    self.open_recordings()
        else:
            self.file_label.config(text=self.lang["recording_failed"])
            messagebox.showerror(self.lang["error"], self.lang["recording_failed"])
    
    def toggle_pause(self):
        if self.recording:
            self.paused = not self.paused
            if self.paused:
                self.pause_btn.config(text=self.lang["resume"], bg=self.colors["success"])
                self.status_icon.config(fg=self.colors["warning"])
                self.status_label.config(text=self.lang["paused"])
            else:
                self.pause_btn.config(text=self.lang["pause"], bg=self.colors["warning"])
                self.status_icon.config(fg=self.colors["success"])
                self.status_label.config(text=self.lang["recording"])
    
    def on_closing(self):
        if self.recording:
            result = messagebox.askyesno(self.lang["warning"], "Recording in progress! Stop and exit?")
            if result:
                self.stop_recording()
                time.sleep(0.5)
            else:
                return
        
        if self.minimize_to_tray:
            self.root.withdraw()
            if not self.tray_icon:
                self.create_tray_icon()
        else:
            self.stop_flag = True
            if self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=1)
            if self.tray_icon:
                self.tray_icon.stop()
            self.root.destroy()

if __name__ == "__main__":
    try:
        import psutil
        import GPUtil
    except ImportError:
        print("Installing required packages...")
        subprocess.run([sys.executable, "-m", "pip", "install", "psutil", "gputil"])
        import psutil
        import GPUtil
    
    root = tk.Tk()
    app = HomRecScreen(root)
    root.mainloop()