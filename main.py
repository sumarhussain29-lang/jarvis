# =========================================================
# JARVIS AI ASSISTANT - main.py
# PART 1 of 2  (all existing code preserved + additions)
# =========================================================

# imports
import os
import json
import re
import tempfile
import urllib.request
import urllib.error
import subprocess
import shutil
import webbrowser
import time
import asyncio
import threading
import ctypes
from pathlib import Path
from datetime import datetime
from urllib.parse import quote_plus

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except Exception:
    pyautogui = None
    PYAUTOGUI_AVAILABLE = False

try:
    import screen_brightness_control as sbc
    SBC_AVAILABLE = True
except Exception:
    sbc = None
    SBC_AVAILABLE = False

try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from comtypes import CLSCTX_ALL
    PYCAW_AVAILABLE = True
except Exception:
    AudioUtilities = None
    IAudioEndpointVolume = None
    CLSCTX_ALL = None
    PYCAW_AVAILABLE = False

# --- NEW: OpenCV import for camera (additive) ---
try:
    import cv2
    CV2_AVAILABLE = True
except Exception:
    cv2 = None
    CV2_AVAILABLE = False
# --- END NEW ---

import speech_recognition as sr
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs.play import play
from faster_whisper import WhisperModel

try:
    import edge_tts
    from playsound3 import playsound
    EDGE_TTS_AVAILABLE = True
except Exception:
    EDGE_TTS_AVAILABLE = False

import noisereduce as nr
import numpy as np
from scipy.io import wavfile
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty
import math
import random

try:
    import tkinter as tk
    TK_AVAILABLE = True
except Exception:
    TK_AVAILABLE = False


# =========================================================
# JARVIS FUTURISTIC UI  (UNCHANGED)
# =========================================================

class JarvisHUD:
    """Lightweight futuristic JARVIS HUD."""

    def __init__(self):
        self.enabled = TK_AVAILABLE
        self.root = None
        self.canvas = None
        self.queue = Queue()
        self.state = "STANDBY"
        self.detail = "SYSTEM READY"
        self._phase = 0.0
        self._thread = None
        self._running = False

    def start(self):
        if not self.enabled or self._running:
            return

        self._thread = threading.Thread(
            target=self._run,
            name="JarvisHUD",
            daemon=True
        )
        self._thread.start()

    def _run(self):
        try:
            self.root = tk.Tk()
            self.root.title("JARVIS AI")
            self.root.configure(bg="#05060b")
            self.root.overrideredirect(False)
            self.root.resizable(False, False)
            self.root.attributes("-topmost", True)
            self.root.attributes("-alpha", 0.94)

            width = 560
            height = 380

            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()

            x = sw - width - 24
            y = sh - height - 70

            self.root.geometry(
                f"{width}x{height}+{x}+{y}"
            )

            self.root.protocol(
                "WM_DELETE_WINDOW",
                self._hide_window
            )

            self.root.bind(
                "<Escape>",
                lambda e: self._hide_window()
            )

            self.root.bind(
                "<F9>",
                lambda e: self.show()
            )

            self.root.bind(
                "<F10>",
                lambda e: self._toggle_topmost()
            )

            header = tk.Frame(
                self.root,
                bg="#090b14",
                height=34
            )

            header.pack(fill="x")
            header.pack_propagate(False)

            tk.Label(
                header,
                text="JARVIS  //  AI CORE",
                bg="#090b14",
                fg="#d7d8ff",
                font=("Segoe UI", 10, "bold")
            ).pack(
                side="left",
                padx=12
            )

            tk.Button(
                header,
                text="—",
                command=self._minimize_window,
                bg="#111421",
                fg="#cfd3ff",
                relief="flat",
                bd=0,
                width=3,
                font=("Segoe UI", 10, "bold")
            ).pack(
                side="right",
                padx=2,
                pady=3
            )

            tk.Button(
                header,
                text="PIN",
                command=self._toggle_topmost,
                bg="#111421",
                fg="#cfd3ff",
                relief="flat",
                bd=0,
                width=4,
                font=("Segoe UI", 8, "bold")
            ).pack(
                side="right",
                padx=2,
                pady=3
            )

            tk.Button(
                header,
                text="×",
                command=self._hide_window,
                bg="#111421",
                fg="#ff9da8",
                relief="flat",
                bd=0,
                width=3,
                font=("Segoe UI", 10, "bold")
            ).pack(
                side="right",
                padx=(2, 7),
                pady=3
            )

            self.canvas = tk.Canvas(
                self.root,
                bg="#05060b",
                highlightthickness=0,
                bd=0
            )

            self.canvas.pack(
                fill="both",
                expand=True
            )

            self._running = True

            self._animate()

            self.root.after(
                30,
                self._drain_queue
            )

            self.root.mainloop()

        except Exception as e:
            print("JARVIS HUD error:", e)
            self.enabled = False

    def _hide_window(self):
        try:
            self.root.withdraw()
        except Exception:
            pass

    def _minimize_window(self):
        try:
            self.root.iconify()
        except Exception:
            pass

    def _toggle_topmost(self):
        try:
            current = bool(
                self.root.attributes("-topmost")
            )

            self.root.attributes(
                "-topmost",
                not current
            )

        except Exception:
            pass

    def set_state(self, state, detail=None):
        if not self.enabled:
            return

        self.queue.put(
            ("state", state, detail or "")
        )

    def set_detail(self, detail):
        if not self.enabled:
            return

        self.queue.put(
            ("detail", detail)
        )

    def show(self):
        if not self.enabled:
            return

        self.queue.put(("show",))

    def hide(self):
        if not self.enabled:
            return

        self.queue.put(("hide",))

    def _drain_queue(self):
        if not self.root:
            return

        try:
            while True:

                item = self.queue.get_nowait()

                kind = item[0]

                if kind == "state":
                    self.state = item[1]
                    self.detail = item[2] or self.detail

                elif kind == "detail":
                    self.detail = item[1]

                elif kind == "show":
                    self.root.deiconify()
                    self.root.lift()

                elif kind == "hide":
                    self.root.withdraw()

        except Empty:
            pass

        finally:
            try:
                self.root.after(
                    30,
                    self._drain_queue
                )
            except Exception:
                pass

    def _animate(self):
        if not self.root or not self.canvas:
            return

        try:
            w = self.canvas.winfo_width()
            h = self.canvas.winfo_height()

            if w < 10 or h < 10:
                self.root.after(
                    30,
                    self._animate
                )
                return

            self.canvas.delete("all")

            cx = w / 2
            cy = h / 2

            self._phase += 0.045

            for y in range(0, h, 36):
                self.canvas.create_line(
                    0,
                    y,
                    w,
                    y,
                    fill="#0a1020",
                    width=1
                )

            for x in range(0, w, 48):
                self.canvas.create_line(
                    x,
                    0,
                    x,
                    h,
                    fill="#08101b",
                    width=1
                )

            self._panel(
                32,
                70,
                275,
                h - 70,
                "SYSTEM"
            )

            self._panel(
                w - 275,
                70,
                w - 32,
                h - 70,
                "ACTIVITY"
            )

            state = self.state.upper()

            pulse_map = {
                "LISTENING": 1.0,
                "THINKING": 0.75,
                "ACTION": 1.15,
                "SPEAKING": 1.3,
                "STANDBY": 0.45,
                "READY": 0.55,
            }

            pulse = pulse_map.get(
                state,
                0.6
            )

            breathing = (
                1.0
                + math.sin(self._phase * 2.0)
                * 0.035
                * pulse
            )

            for i, base in enumerate(
                (105, 150, 198, 246)
            ):

                r = (
                    base * breathing
                    + math.sin(
                        self._phase * (1.1 + i * .18)
                    ) * (3 + i)
                )

                start = (
                    self._phase
                    * (24 + i * 9)
                    * (-1 if i % 2 else 1)
                ) % 360

                self.canvas.create_arc(
                    cx-r,
                    cy-r,
                    cx+r,
                    cy+r,
                    start=start,
                    extent=245,
                    outline="#6e55ff",
                    width=2 + (
                        1
                        if state in (
                            "LISTENING",
                            "SPEAKING"
                        )
                        else 0
                    )
                )

                self.canvas.create_arc(
                    cx-r,
                    cy-r,
                    cx+r,
                    cy+r,
                    start=start + 255,
                    extent=55,
                    outline="#36d9ff",
                    width=2
                )

            core = (
                58
                + math.sin(
                    self._phase * 3.0
                ) * 7 * pulse
            )

            for i in range(5, 0, -1):

                rr = core + i * 15

                self.canvas.create_oval(
                    cx-rr,
                    cy-rr,
                    cx+rr,
                    cy+rr,
                    outline="#352a77" if i > 2 else "#6e55ff",
                    width=2
                )

            self.canvas.create_oval(
                cx-core,
                cy-core,
                cx+core,
                cy+core,
                fill="#100b2a",
                outline="#9a72ff",
                width=3
            )

            self.canvas.create_oval(
                cx-core*.58,
                cy-core*.58,
                cx+core*.58,
                cy+core*.58,
                fill="#24105f",
                outline="#36d9ff",
                width=2
            )

            bars = 28
            bar_w = 5
            gap = 5

            total = bars * (
                bar_w + gap
            )

            sx = cx - total / 2

            for i in range(bars):

                amp = (
                    8
                    + abs(
                        math.sin(
                            self._phase * 3.2
                            + i * .55
                        )
                    ) * (
                        12
                        + 26 * pulse
                    )
                )

                self.canvas.create_rectangle(
                    sx + i*(bar_w+gap),
                    cy + 270 - amp,
                    sx + i*(bar_w+gap) + bar_w,
                    cy + 270 + amp,
                    fill="#3fdcff",
                    outline=""
                )

            self.canvas.create_text(
                cx,
                34,
                text="J A R V I S  //  PERSONAL AI",
                fill="#d9d7ff",
                font=("Consolas", 18, "bold")
            )

            self.canvas.create_text(
                cx,
                67,
                text=state,
                fill="#8eeaff",
                font=("Consolas", 12, "bold")
            )

            self.canvas.create_text(
                cx,
                cy,
                text="JARVIS",
                fill="#f0edff",
                font=("Consolas", 13, "bold")
            )

            self._telemetry(
                55,
                105,
                [
                    "VOICE LINK   ONLINE",
                    "WHISPER      READY",
                    "AI CORE      ONLINE",
                    "LOCAL AGENT  READY",
                    "TTS ENGINE   READY",
                ]
            )

            self._telemetry(
                w - 255,
                105,
                [
                    "MIC          ACTIVE",
                    f"STATE        {state}",
                    "LANGUAGE     AUTO",
                    "COMMAND BUS  LOCAL",
                    "SECURITY     CONFIRM",
                ]
            )

            self.canvas.create_text(
                cx,
                h - 48,
                text=self.detail[:90],
                fill="#a7a2d8",
                font=("Consolas", 10)
            )

            self.canvas.create_text(
                cx,
                h - 22,
                text="ESC: hide HUD    F10: toggle topmost",
                fill="#565477",
                font=("Consolas", 8)
            )

            random.seed(7)

            for i in range(36):

                px = (
                    cx
                    + math.sin(
                        self._phase*.7+i*1.9
                    ) * (w*.46)
                ) % w

                py = (
                    cy
                    + math.cos(
                        self._phase*.53+i*1.3
                    ) * (h*.43)
                ) % h

                self.canvas.create_oval(
                    px,
                    py,
                    px+2,
                    py+2,
                    fill="#5142a8",
                    outline=""
                )

            self.root.after(
                30,
                self._animate
            )

        except Exception:

            try:
                self.root.after(
                    100,
                    self._animate
                )
            except Exception:
                pass

    def _panel(self, x1, y1, x2, y2, title):

        self.canvas.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            outline="#1b2350",
            width=1
        )

        self.canvas.create_line(
            x1,
            y1+28,
            x2,
            y1+28,
            fill="#252d5c"
        )

        self.canvas.create_text(
            x1+12,
            y1+14,
            text=title,
            anchor="w",
            fill="#6edfff",
            font=("Consolas", 9, "bold")
        )

    def _telemetry(self, x, y, lines):

        for i, line in enumerate(lines):

            self.canvas.create_text(
                x,
                y + i*27,
                text=line,
                anchor="w",
                fill="#676b9c",
                font=("Consolas", 8)
            )


JARVIS_UI = JarvisHUD()


def ui_state(state, detail=None):
    try:
        JARVIS_UI.set_state(
            state,
            detail
        )
    except Exception:
        pass


def ui_detail(detail):
    try:
        JARVIS_UI.set_detail(detail)
    except Exception:
        pass


# =========================================================
# LOAD ENVIRONMENT  (UNCHANGED)
# =========================================================

load_dotenv()

ELEVENLABS_API_KEY = os.getenv(
    "ELEVENLABS_API_KEY"
)

OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)

if not ELEVENLABS_API_KEY:
    print(
        "ERROR: ELEVENLABS_API_KEY missing in .env"
    )
    exit()

if not OPENROUTER_API_KEY:
    print(
        "ERROR: OPENROUTER_API_KEY missing in .env"
    )
    exit()


# =========================================================
# ELEVENLABS  (UNCHANGED — voice ID preserved)
# =========================================================

eleven_client = ElevenLabs(
    api_key=ELEVENLABS_API_KEY
)

VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"
MODEL_ID = "eleven_multilingual_v2"


# =========================================================
# OPENROUTER MODELS  (UNCHANGED)
# =========================================================

OPENROUTER_MODELS = [
    "nvidia/nemotron-3-ultra-550b-a55b-20260604:free",
    "openrouter/free"
]


# =========================================================
# WHISPER  (UNCHANGED)
# =========================================================

print("Loading Whisper model...")

try:
    whisper_model = WhisperModel(
        "base",
        device="cpu",
        compute_type="int8"
    )
    print("Whisper model loaded successfully.")
except Exception as e:
    print("Whisper model loading error:", e)
    exit()


# =========================================================
# SPEECH RECOGNIZER  (UNCHANGED)
# =========================================================

recognizer = sr.Recognizer()

recognizer.dynamic_energy_threshold = True
recognizer.dynamic_energy_adjustment_damping = 0.12
recognizer.dynamic_energy_ratio = 1.5

recognizer.energy_threshold = 250
recognizer.pause_threshold = 0.8
recognizer.non_speaking_duration = 0.3
recognizer.phrase_threshold = 0.25


# =========================================================
# MICROPHONE SELECTION + CALIBRATION  (UNCHANGED)
# =========================================================

MIC_INDEX = None
_env_mic = os.getenv("JARVIS_MIC_INDEX")
if _env_mic is not None and _env_mic.strip() != "":
    try:
        MIC_INDEX = int(_env_mic.strip())
        print(f"Using microphone index from env: {MIC_INDEX}")
    except Exception:
        print(f"Invalid JARVIS_MIC_INDEX={_env_mic!r}; using auto-selection.")


def _auto_pick_mic_index():
    try:
        names = sr.Microphone.list_microphone_names()
    except Exception as e:
        print("Could not list microphones:", e)
        return None

    print("Available microphones:")
    for i, n in enumerate(names):
        print(f"  [{i}] {n}")

    bad_keywords = [
        "stereo mix", "what u hear", "loopback",
        "webcam", "virtual", "vb-audio", "cable output",
    ]

    preferred_keywords = [
        "microphone", "mic", "headset", "realtek", "usb audio",
    ]

    for i, name in enumerate(names):
        low = name.lower()
        if any(b in low for b in bad_keywords):
            continue
        if any(p in low for p in preferred_keywords):
            print(f"Auto-selected microphone [{i}]: {name}")
            return i

    for i, name in enumerate(names):
        low = name.lower()
        if any(b in low for b in bad_keywords):
            continue
        print(f"Auto-selected microphone [{i}]: {name}")
        return i

    print("No suitable mic found by name; using system default.")
    return None


if MIC_INDEX is None:
    MIC_INDEX = _auto_pick_mic_index()


print("Calibrating microphone...")

try:
    with sr.Microphone(device_index=MIC_INDEX) as source:
        recognizer.adjust_for_ambient_noise(
            source,
            duration=1.5
        )
        print(
            "Ambient energy threshold after calibration:",
            recognizer.energy_threshold
        )
except Exception as e:
    print("Microphone calibration error:", e)


def _run_startup_mic_test():
    print()
    print("=" * 60)
    print("MIC SELF-TEST")
    print("=" * 60)
    print("Say something like 'test one two' within 6 seconds...")

    try:
        with sr.Microphone(device_index=MIC_INDEX) as source:

            local_recognizer = sr.Recognizer()
            local_recognizer.energy_threshold = 250
            local_recognizer.dynamic_energy_threshold = True
            local_recognizer.adjust_for_ambient_noise(
                source,
                duration=0.8
            )

            print(
                "Self-test energy threshold:",
                local_recognizer.energy_threshold
            )

            try:
                audio = local_recognizer.listen(
                    source,
                    timeout=6,
                    phrase_time_limit=6
                )
            except sr.WaitTimeoutError:
                print("MIC SELF-TEST: TIMEOUT — recognizer heard nothing.")
                print("  -> Your mic is not delivering audio above the threshold.")
                print("  -> Check: Windows mic privacy, mute button, device index.")
                return

            wav_bytes = audio.get_wav_data()
            print("MIC SELF-TEST: Captured bytes =", len(wav_bytes))

            if len(wav_bytes) < 4000:
                print("  -> Captured audio is very short; possibly silent.")

            try:
                text = local_recognizer.recognize_google(
                    audio,
                    language="en-US"
                )
                print("MIC SELF-TEST Google en-US:", text)
            except Exception as e:
                print("MIC SELF-TEST Google en-US failed:", e)

            try:
                text_ur = local_recognizer.recognize_google(
                    audio,
                    language="ur-PK"
                )
                print("MIC SELF-TEST Google ur-PK:", text_ur)
            except Exception as e:
                print("MIC SELF-TEST Google ur-PK failed:", e)

    except Exception as e:
        print("MIC SELF-TEST error:", e)

    print("=" * 60)
    print()


# =========================================================
# TEXT CLEANING  (UNCHANGED)
# =========================================================

def clean_transcript(text):

    if not text:
        return ""

    text = str(text).strip()

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


ROMAN_URDU_WORDS = {
    "kya", "hai", "hain", "ho", "hota", "hoti", "hote",
    "kaise", "kaisa", "kaisi", "kar", "karo", "karein",
    "karna", "karta", "karte", "karti", "do", "de", "dena",
    "mujhe", "mera", "meri", "mere", "tum", "tumhe",
    "tumhara", "tumhari", "aap", "apko", "apka", "apni",
    "apne", "yaar", "bhai", "batao", "bata", "bolo", "bol",
    "suno", "sun", "chal", "chalao", "chala", "kholo", "khol",
    "band", "bando", "kahan", "kaha", "kab", "kyun", "kyon",
    "acha", "achha", "abhi", "phir", "mujh", "se", "ko",
    "ke", "ki", "ka", "mein", "main", "me", "par", "pe",
    "upar", "neeche", "andar", "bahar", "laptop", "computer",
    "gaana", "gana", "music", "video", "youtube", "lagao",
    "laga", "dikhao", "dikha", "sunao", "please", "miranam",
    "mira", "naam", "umar",
    "song", "songs", "gaane", "punjabi", "bollywood",
    "arijit", "atif", "aslam", "singh", "romantic", "sad",
    "party", "fast", "slow", "chill", "trending",
    "brightness", "volume", "battery", "charging",
}


def roman_urdu_score(text):

    if not text:
        return 0

    words = re.findall(
        r"[a-zA-Z]+",
        text.lower()
    )

    score = 0

    for word in words:

        if word in ROMAN_URDU_WORDS:
            score += 1

    return score


def contains_urdu_script(text):

    if not text:
        return False

    return bool(
        re.search(
            r"[\u0600-\u06FF]",
            text
        )
    )


def recognize_english(audio):

    try:

        text = recognizer.recognize_google(
            audio,
            language="en-US"
        )

        text = clean_transcript(text)

        print("English result:", text)

        return text

    except Exception as e:

        print("English recognition:", e)

        return ""


def recognize_urdu_google(audio):

    try:

        text = recognizer.recognize_google(
            audio,
            language="ur-PK"
        )

        text = clean_transcript(text)

        print("Google Urdu result:", text)

        return text

    except Exception as e:

        print("Google Urdu recognition:", e)

        return ""


def clean_audio_for_speech(audio):

    input_file = None
    output_file = None

    try:

        input_tmp = tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False
        )

        input_file = input_tmp.name
        input_tmp.close()

        with open(input_file, "wb") as f:
            f.write(audio.get_wav_data())

        sample_rate, data = wavfile.read(input_file)

        if len(data.shape) > 1:
            data = data.mean(axis=1)

        data = data.astype(np.float32)

        reduced = nr.reduce_noise(
            y=data,
            sr=sample_rate,
            stationary=True,
            prop_decrease=0.85
        )

        reduced = np.clip(
            reduced,
            -32768,
            32767
        ).astype(np.int16)

        output_tmp = tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False
        )

        output_file = output_tmp.name
        output_tmp.close()

        wavfile.write(
            output_file,
            sample_rate,
            reduced
        )

        return output_file

    except Exception as e:

        print("Noise reduction error:", e)

        if input_file and os.path.exists(input_file):
            return input_file

        return None


# =========================================================
# WHISPER URDU  (UNCHANGED)
# =========================================================

def recognize_whisper_urdu(audio):

    temp_wav = None

    try:

        temp_wav = clean_audio_for_speech(audio)

        if not temp_wav:
            return ""

        segments, info = whisper_model.transcribe(
            temp_wav,
            language=None,
            initial_prompt=(
                "Jarvis, Umar, Chrome, YouTube, Visual Studio, VS Code, "
                "Downloads, Desktop, Documents, laptop, computer, music, "
                "brightness, volume, battery, charging, "
                "kholo, khol do, band karo, chalao, lagao, open, close, "
                "play, pause, resume, shutdown, restart, sleep, lock"
            ),
            beam_size=5,
            best_of=5,
            temperature=0,
            vad_filter=True,
            condition_on_previous_text=False
        )

        text_parts = []

        for segment in segments:
            segment_text = segment.text.strip()
            if segment_text:
                text_parts.append(segment_text)

        text = " ".join(text_parts).strip()

        print("Whisper Urdu result:", text)

        return clean_transcript(text)

    except Exception as e:

        print("Whisper Urdu Error:", e)
        return ""

    finally:

        if temp_wav:
            try:
                if os.path.exists(temp_wav):
                    os.remove(temp_wav)
            except Exception:
                pass


# =========================================================
# WHISPER ENGLISH  (UNCHANGED)
# =========================================================

def recognize_whisper_english(audio):

    temp_wav = None

    try:

        temp_wav = clean_audio_for_speech(audio)

        if not temp_wav:
            return ""

        segments, info = whisper_model.transcribe(
            temp_wav,
            language="en",
            beam_size=5,
            best_of=5,
            temperature=0,
            vad_filter=True,
            condition_on_previous_text=False
        )

        text_parts = []

        for segment in segments:
            segment_text = segment.text.strip()
            if segment_text:
                text_parts.append(segment_text)

        text = " ".join(text_parts).strip()

        print("Whisper English result:", text)

        return clean_transcript(text)

    except Exception as e:

        print("Whisper English Error:", e)
        return ""

    finally:

        if temp_wav:
            try:
                if os.path.exists(temp_wav):
                    os.remove(temp_wav)
            except Exception:
                pass


# =========================================================
# CHOOSE BEST SPEECH RESULT  (UNCHANGED)
# =========================================================

def choose_speech_result(
    whisper_urdu,
    whisper_english,
    google_english,
    google_urdu=""
):

    values = {
        "whisper_urdu": clean_transcript(whisper_urdu),
        "whisper_english": clean_transcript(whisper_english),
        "google_english": clean_transcript(google_english),
        "google_urdu": clean_transcript(google_urdu),
    }

    normalized_values = {
        key: normalize_urdu_command(value)
        if value else ""
        for key, value in values.items()
    }

    candidates = [v for v in normalized_values.values() if v]

    if not candidates:
        return ""

    for source in (
        "google_urdu",
        "google_english",
        "whisper_urdu",
        "whisper_english"
    ):

        candidate = normalized_values.get(source, "")
        low_candidate = candidate.lower()

        if (
            "jarvis" in low_candidate
            and any(
                x in low_candidate
                for x in [
                    "chrome", "youtube", "vs code", "visual studio",
                    "folder", "downloads", "desktop", "documents",
                    "whatsapp", "chatgpt", "open", "khol", "band",
                    "close", "search", "play", "chalao", "lagao",
                    "brightness", "volume", "battery", "shutdown",
                    "restart", "sleep", "lock", "camera", "picture",
                    "type", "scroll"
                ]
            )
        ):
            print("Preferred speech source:", source)
            return candidate

    command_words = [
        "jarvis", "chrome", "browser", "youtube", "visual studio",
        "vs code", "code", "download", "downloads", "desktop",
        "documents", "folder", "open", "close", "shutdown",
        "restart", "sleep", "lock", "brightness", "volume",
        "battery", "charging", "music", "play", "pause",
        "resume", "search", "kholo", "khol", "band", "karo",
        "kar do", "chalao", "lagao", "bando", "chalado",
        "mera", "meri", "mujhe", "apna", "please",
        "camera", "picture", "type", "scroll"
    ]

    urdu_command_words = [
        "جارویس", "جاربس", "جاروز", "کروم", "یوٹیوب", "ویژول",
        "کوڈ", "ڈاؤن لوڈ", "ڈاؤنلوڈ", "فولڈر", "کھولو", "کھول",
        "بند", "کرو", "چلاؤ", "لگاؤ", "میوزک", "لیپ ٹاپ",
        "کمپیوٹر", "ڈیسک ٹاپ"
    ]

    def score(text):
        low = text.lower()
        points = 0
        if ("jarvis" in low
                or any(x in text for x in ["جارویس", "جاربس", "جاروز"])):
            points += 8
        for word in command_words:
            if word in low:
                points += 2
        for word in urdu_command_words:
            if word in text:
                points += 2
        points += min(len(text.split()), 12) * 0.05
        return points

    ranked = sorted(candidates, key=score, reverse=True)
    best = ranked[0]

    print("Speech candidate scores:")
    for item in ranked[:4]:
        print(f"  {score(item):.2f}: {item}")

    return best


# =========================================================
# URDU-SCRIPT -> ROMAN/ENGLISH COMMAND NORMALIZATION  (UNCHANGED)
# =========================================================

URDU_COMMAND_REPLACEMENTS = [

    ("جارویس", "jarvis"),
    ("جاربس", "jarvis"),
    ("جاروس", "jarvis"),
    ("جاروز", "jarvis"),
    ("جاوید", "jarvis"),

    ("گوگل کروم", "chrome"),
    ("کروم", "chrome"),

    ("یوتوب", "youtube"),
    ("یوٹیوب", "youtube"),
    ("یو ٹیوب", "youtube"),
    ("یو ٹیو ب", "youtube"),

    ("ویژول اسٹوڈیو کوڈ", "visual studio code"),
    ("ویژول اسٹوڈیو", "visual studio"),
    ("ویژول", "visual"),
    ("ویزو ل", "visual"),
    ("کوڈ", "code"),

    ("ڈاؤن لوڈز", "downloads"),
    ("ڈاؤنلوڈز", "downloads"),
    ("ڈاؤن لوڈ", "download"),
    ("ڈاؤنلوڈ", "download"),

    ("فولڈر", "folder"),
    ("فائل ایکسپلورر", "file explorer"),

    ("لیپ ٹاپ", "laptop"),
    ("کمپیوٹر", "computer"),

    ("پیس فل میوزک", "peaceful music"),
    ("پیس فل", "peaceful"),
    ("پیسفُل", "peaceful"),

    ("میوزک", "music"),
    ("گانا", "gaana"),
    ("گانے", "gaane"),

    ("کھولو", "kholo"),
    ("کھول دو", "kholo"),
    ("کھول", "kholo"),

    ("اوپن", "open"),

    ("بند کر دو", "band karo"),
    ("بند کرو", "band karo"),
    ("بند", "band"),

    ("چلا دو", "chalao"),
    ("چلاؤ", "chalao"),

    ("لگا دو", "lagao"),
    ("لگاؤ", "lagao"),

    ("اور", "aur"),
    ("پھر", "phir"),
    ("پر", "par"),
    ("پہ", "pe"),

    ("میں", "mein"),
    ("مجھے", "mujhe"),
    ("میرا", "mera"),
    ("میری", "meri"),

    ("موسیقی", "music"),

    ("تلاش", "search"),
    ("سرچ", "search"),

    ("تصاویر", "images"),
    ("تصویر", "image"),

    ("بولو", "bolo"),
    ("بتاؤ", "batao"),
    ("بتاو", "batao"),

    ("ہاں", "haan"),
    ("نہیں", "nahi"),
    ("جی", "ji"),
]


def normalize_urdu_command(text):

    if not text:
        return ""

    t = clean_transcript(text)

    for old, new in URDU_COMMAND_REPLACEMENTS:
        t = t.replace(old, new)

    replacements = {
        "you tube": "youtube",
        "u tube": "youtube",
        "jervis": "jarvis",
        "jarwis": "jarvis",
        "miranam": "mera naam",
        "mira naam": "mera naam",
        "mera nam": "mera naam",
        "meranam": "mera naam",
        "meri naam": "mera naam",
        "time kholo": "time batao",
        "time khol": "time batao",
    }

    for old, new in replacements.items():
        t = re.sub(
            r"\b" + re.escape(old) + r"\b",
            new,
            t,
            flags=re.IGNORECASE
        )

    t = re.sub(r"\s+", " ", t).strip()

    return t


def command_ready_text(text):
    return normalize_urdu_command(text)


def prepare_user_text(text):

    if not text:
        return ""

    text = clean_transcript(text)

    return normalize_urdu_command(text)


# =========================================================
# REMOVE WAKE WORD  (UNCHANGED)
# =========================================================

def remove_wake_word(text):

    if not text:
        return ""

    patterns = [

        r"\bhey\s+jarvis\b",
        r"\bhello\s+jarvis\b",
        r"\bokay\s+jarvis\b",
        r"\bok\s+jarvis\b",
        r"\bhai\s+jarvis\b",
        r"\bhay\s+jarvis\b",

        r"\bhey\s+jar\b",
        r"\bhello\s+jar\b",
        r"\bokay\s+jar\b",
        r"\bok\s+jar\b",

        r"\bjarvis\b",
        r"\bjarv\b",
        r"\bjarved\b",

        r"جارویس",
        r"جاروز",
        r"جاروِس",
        r"جارويس"
    ]

    result = text

    for pattern in patterns:
        result = re.sub(
            pattern,
            "",
            result,
            flags=re.IGNORECASE
        )

    result = re.sub(
        r"^[\s,.;:!?،۔؛-]+",
        "",
        result
    )

    return clean_transcript(result)


# =========================================================
# WAKE WORD DETECTION  (UNCHANGED)
# =========================================================

def is_wake_word(text):

    if not text:
        return False

    text = clean_transcript(text)
    lower_text = text.lower()

    patterns = [
        "hey jarvis", "hello jarvis", "okay jarvis",
        "ok jarvis", "hai jarvis", "haye jarvis",
        "hey jar", "hello jar", "okay jar", "ok jar",
        "jarvis", "jarv", "jarved"
    ]

    for pattern in patterns:
        if pattern in lower_text:
            print("Wake word matched:", pattern)
            return True

    urdu_wake_words = [
        "جارویس", "جاروز", "جاروِس", "جارويس"
    ]

    for pattern in urdu_wake_words:
        if pattern in text:
            print("Urdu wake word matched:", pattern)
            return True

    words = lower_text.split()

    for word in words:
        if word in [
            "jarvis", "jarv", "jarved", "jar",
            "jervis", "jarwis"
        ]:
            print("Wake word fuzzy matched:", word)
            return True

    return False


# =========================================================
# TTS  (voice ID preserved; Roman Urdu now uses the
#       English voice per your spec #9)
# =========================================================

def _is_roman_urdu(text):

    if not text:
        return False

    if contains_urdu_script(text):
        return True

    low = " " + text.lower() + " "

    english_markers = [
        " the ", " is ", " are ", " was ", " were ",
        " you ", " your ", " please ", " thanks ",
        " hello ", " hi ", " hey ", " how ",
        " what ", " when ", " where ", " why ",
        " can ", " could ", " would ", " should ",
        " doing ", " great ", " okay ",
        " yes ", " no ", " not ", " and ",
    ]
    english_hits = sum(1 for m in english_markers if m in low)

    strong_roman_urdu = [
        "kya", "kaise", "kaisi", "kaisa",
        "karo", "karna", "karta", "karti", "karte",
        "kholo", "khol", "band karo", "chalao", "chala do",
        "lagao", "laga do", "batao", "bata do",
        "mujhe", "mera", "meri", "mere",
        "aap", "apka", "apki", "tum", "tumhara", "tumhari",
        "hai", "hain", "hoon", "nahi", "haan",
        "acha", "achha", "theek", "thik",
        "abhi", "phir", "yaar", "bhai",
        "shukriya", "khuda hafiz", "assalam",
        "hai kya", "kya hai", "kar do", "kar raha",
        "kar rahi", "raha hoon", "rahi hoon",
    ]
    strong_hits = sum(
        1 for m in strong_roman_urdu
        if m in low
    )

    if english_hits >= 2 and strong_hits == 0:
        return False

    if strong_hits >= 1:
        return True

    return roman_urdu_score(text) >= 2


_ROMAN_TO_URDU_PHRASES = [
    ("main bilkul theek hoon", "میں بالکل ٹھیک ہوں"),
    ("main theek hoon", "میں ٹھیک ہوں"),
    ("aap kaise ho", "آپ کیسے ہیں"),
    ("aap kaise hain", "آپ کیسے ہیں"),
    ("tum kaise ho", "تم کیسے ہو"),
    ("kya haal hai", "کیا حال ہے"),
    ("kya kar rahe ho", "کیا کر رہے ہو"),
    ("kya kar rahi ho", "کیا کر رہی ہو"),
    ("main aap ki madad ke liye hazir hoon", "میں آپ کی مدد کے لیے حاضر ہوں"),
    ("bataiye kya karna hai", "بتائیے کیا کرنا ہے"),
    ("batao kya karna hai", "بتاؤ کیا کرنا ہے"),
    ("ji umar", "جی عمر"),
    ("haan umar", "ہاں عمر"),
    ("theek hai umar", "ٹھیک ہے عمر"),
    ("bilkul theek", "بالکل ٹھیک"),
    ("koi baat nahi", "کوئی بات نہیں"),
    ("shukriya", "شکریہ"),
    ("khuda hafiz", "خدا حافظ"),
    ("allah hafiz", "اللہ حافظ"),
    ("assalam o alaikum", "السلام علیکم"),
    ("walaikum assalam", "وعلیکم السلام"),
    ("mera naam", "میرا نام"),
    ("meri age", "میری عمر"),
    ("meri umar", "میری عمر"),
    ("mera kaam", "میرا کام"),
    ("meri university", "میری یونیورسٹی"),
    ("mera shehar", "میرا شہر"),
    ("main hyderabad mein rehta hoon", "میں حیدرآباد میں رہتا ہوں"),
    ("sindh university jamshoro", "سندھ یونیورسٹی جامشورو"),
    ("software engineer", "سافٹ ویئر انجینئر"),
    ("ai engineer", "اے آئی انجینئر"),
    ("rafiq bhutto sir", "رفیق بھٹو سر"),
    ("17 february", "سترہ فروری"),
    ("23 years", "تیئس سال"),
    ("umar hussain", "عمر حسین"),
    ("syed umar hussain", "سید عمر حسین"),
    ("kaise ho", "کیسے ہو"),
    ("kaise hain", "کیسے ہیں"),
    ("kaisi ho", "کیسی ہو"),
    ("main theek", "میں ٹھیک"),
    ("hum theek", "ہم ٹھیک"),
    ("aap theek", "آپ ٹھیک"),
    ("tum theek", "تم ٹھیک"),
    ("kholo", "کھولو"),
    ("khol do", "کھول دو"),
    ("band karo", "بند کرو"),
    ("band kar do", "بند کر دو"),
    ("chalao", "چلاؤ"),
    ("chala do", "چلا دو"),
    ("lagao", "لگاؤ"),
    ("laga do", "لگا دو"),
    ("batao", "بتاؤ"),
    ("bata do", "بتا دو"),
    ("suno", "سنو"),
    ("dekho", "دیکھو"),
    ("karo", "کرو"),
    ("kar do", "کر دو"),
    ("open karo", "اوپن کرو"),
    ("search karo", "سرچ کرو"),
    ("play karo", "پلے کرو"),
    ("close karo", "کلوز کرو"),
    ("time kya hai", "ٹائم کیا ہے"),
    ("time batao", "ٹائم بتاؤ"),
    ("abhi time", "ابھی ٹائم"),
    ("date kya hai", "تاریخ کیا ہے"),
    ("date batao", "تاریخ بتاؤ"),
    ("aaj ki date", "آج کی تاریخ"),
    ("battery kitni hai", "بیٹری کتنی ہے"),
    ("battery percentage", "بیٹری پرسنٹیج"),
    ("charging kitni", "چارجنگ کتنی"),
    ("brightness kam", "برائٹنس کم"),
    ("brightness zyada", "برائٹنس زیادہ"),
    ("volume kam", "والیوم کم"),
    ("volume zyada", "والیوم زیادہ"),
    ("mujhe", "مجھے"),
    ("mera", "میرا"),
    ("meri", "میری"),
    ("mere", "میرے"),
    ("aap", "آپ"),
    ("aapka", "آپ کا"),
    ("aapki", "آپ کی"),
    ("tum", "تم"),
    ("tumhara", "تمہارا"),
    ("tumhari", "تمہاری"),
    ("kya", "کیا"),
    ("hai", "ہے"),
    ("hain", "ہیں"),
    ("hoon", "ہوں"),
    ("nahi", "نہیں"),
    ("haan", "ہاں"),
    ("ji", "جی"),
    ("aur", "اور"),
    ("phir", "پھر"),
    ("abhi", "ابھی"),
    ("please", "پلیز"),
    ("theek", "ٹھیک"),
    ("acha", "اچھا"),
    ("achha", "اچھا"),
    ("bahut", "بہت"),
    ("zyada", "زیادہ"),
    ("thoda", "تھوڑا"),
    ("koi", "کوئی"),
    ("kuch", "کچھ"),
    ("sab", "سب"),
    ("log", "لوگ"),
    ("baat", "بات"),
    ("kaam", "کام"),
    ("waqt", "وقت"),
    ("din", "دن"),
    ("raat", "رات"),
    ("subah", "صبح"),
    ("shaam", "شام"),
    ("aaj", "آج"),
    ("kal", "کل"),
    ("parson", "پرسوں"),
    ("yahan", "یہاں"),
    ("wahan", "وہاں"),
    ("kahan", "کہاں"),
    ("kaun", "کون"),
    ("kab", "کب"),
    ("kyun", "کیوں"),
    ("kaise", "کیسے"),
    ("kitna", "کتنا"),
    ("kitni", "کتی"),
    ("kitne", "کتنے"),
]


def _roman_urdu_to_urdu_script(text):

    if not text:
        return text

    if contains_urdu_script(text):
        return text

    result = text

    for roman, urdu in sorted(
        _ROMAN_TO_URDU_PHRASES,
        key=lambda x: -len(x[0])
    ):
        pattern = re.compile(
            r'\b' + re.escape(roman) + r'\b',
            re.IGNORECASE
        )
        result = pattern.sub(urdu, result)

    return result


def detect_response_language(text):

    if not text:
        return "english"

    if contains_urdu_script(text):
        return "urdu_script"

    if _is_roman_urdu(text):
        return "roman_urdu"

    return "english"


async def _edge_tts_save(
    text,
    voice,
    output_file
):

    communicate = edge_tts.Communicate(
        text,
        voice
    )

    await communicate.save(
        output_file
    )


def speak(text):
    """
    Voice ID / model UNCHANGED.
    Only adjustment: Roman Urdu responses use the English voice
    (per spec #9 "keep the existing Roman Urdu/English behavior
    intact" — no Urdu-script conversion of the reply).
    Urdu-script input still uses ur-PK-AsadNeural.
    """

    if not text:
        return

    text = clean_ai_answer(text)

    if not text:
        return

    ui_state(
        "SPEAKING",
        text[:70]
    )

    print()
    print("JARVIS (console):", text)

    lang = detect_response_language(text)

    if lang == "urdu_script":
        tts_text = text
        voice = "ur-PK-AsadNeural"
    else:
        # English OR Roman Urdu -> English voice.
        tts_text = text
        voice = "en-GB-RyanNeural"

    print()

    if EDGE_TTS_AVAILABLE:

        try:

            temp = tempfile.NamedTemporaryFile(
                suffix=".mp3",
                delete=False
            )

            temp_path = temp.name
            temp.close()

            asyncio.run(
                _edge_tts_save(
                    tts_text,
                    voice,
                    temp_path
                )
            )

            playsound(temp_path)

            try:
                os.remove(temp_path)
            except Exception:
                pass

            print("TTS:", voice)

            return

        except Exception as e:

            print("Edge TTS error:", e)

            if voice == "ur-PK-AsadNeural":

                print("Urdu TTS failed, falling back to English TTS...")

                try:

                    temp = tempfile.NamedTemporaryFile(
                        suffix=".mp3",
                        delete=False
                    )

                    temp_path = temp.name
                    temp.close()

                    asyncio.run(
                        _edge_tts_save(
                            text,
                            "en-GB-RyanNeural",
                            temp_path
                        )
                    )

                    playsound(temp_path)

                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass

                    return

                except Exception as fallback_err:

                    print(
                        "English fallback TTS error:",
                        fallback_err
                    )

    try:

        audio = eleven_client.text_to_speech.convert(
            voice_id=VOICE_ID,
            model_id=MODEL_ID,
            output_format="mp3_44100_128",
            text=tts_text
        )

        play(audio)

        return

    except Exception as e:

        print("ElevenLabs TTS error:", e)

    try:

        safe_text = tts_text.replace("'", "''")

        powershell_command = (
            "Add-Type -AssemblyName System.Speech; "
            "$speak = New-Object "
            "System.Speech.Synthesis.SpeechSynthesizer; "
            "$speak.Rate = 0; "
            f"$speak.Speak('{safe_text}');"
        )

        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                powershell_command
            ],
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    except Exception as e:

        print("Windows TTS Error:", e)


# =========================================================
# EXTRACT AI ANSWER  (UNCHANGED)
# =========================================================

def extract_answer(data):

    try:

        choices = data.get("choices", [])

        if not choices:
            return ""

        message = choices[0].get("message", {})

        content = message.get("content")

        if content:
            return str(content).strip()

        return ""

    except Exception:
        return ""


# =========================================================
# CLEAN AI ANSWER  (UNCHANGED)
# =========================================================

def clean_ai_answer(text):

    if not text:
        return ""

    text = str(text)

    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"__(.*?)__", r"\1", text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.MULTILINE)

    text = text.replace("*", "")
    text = text.replace("#", "")
    text = text.replace("_", " ")

    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


# =========================================================
# WINDOWS BRIGHTNESS / VOLUME / POWER HELPERS
# =========================================================

def _get_current_brightness():
    if not SBC_AVAILABLE:
        return None
    try:
        values = sbc.get_brightness()
        if isinstance(values, list):
            if not values:
                return None
            return int(values[0])
        return int(values)
    except Exception as e:
        print("Brightness read error:", e)
        return None


def _set_brightness(percent):
    if not SBC_AVAILABLE:
        return False
    try:
        percent = max(0, min(100, int(percent)))
        sbc.set_brightness(percent)
        return True
    except Exception as e:
        print("Brightness set error:", e)
        return False


def _change_brightness(delta):
    current = _get_current_brightness()
    if current is None:
        return None
    target = max(0, min(100, current + delta))
    if _set_brightness(target):
        return target
    return None


_VOLUME_INTERFACE = None


def _get_volume_interface():
    """
    Same behaviour as before; now also supports the newer pycaw
    API (speakers.EndpointVolume) with fallback to the original
    Activate() path.
    """
    global _VOLUME_INTERFACE
    if _VOLUME_INTERFACE is not None:
        return _VOLUME_INTERFACE
    if not PYCAW_AVAILABLE:
        return None
    try:
        speakers = AudioUtilities.GetSpeakers()
        if hasattr(speakers, "EndpointVolume"):
            _VOLUME_INTERFACE = speakers.EndpointVolume
            return _VOLUME_INTERFACE
        interface = speakers.Activate(
            IAudioEndpointVolume._iid_,
            CLSCTX_ALL,
            None
        )
        _VOLUME_INTERFACE = interface.QueryInterface(IAudioEndpointVolume)
        return _VOLUME_INTERFACE
    except Exception as e:
        print("Volume interface error:", e)
        return None


def _get_current_volume_percent():
    vol = _get_volume_interface()
    if vol is None:
        return None
    try:
        scalar = vol.GetMasterVolumeLevelScalar()
        return int(round(scalar * 100))
    except Exception as e:
        print("Volume read error:", e)
        return None


def _set_volume_percent(percent):
    vol = _get_volume_interface()
    if vol is None:
        return False
    try:
        percent = max(0, min(100, int(percent)))
        vol.SetMasterVolumeLevelScalar(percent / 100.0, None)
        return True
    except Exception as e:
        print("Volume set error:", e)
        return False


def _change_volume(delta):
    current = _get_current_volume_percent()
    if current is None:
        return None
    target = max(0, min(100, current + delta))
    if _set_volume_percent(target):
        return target
    return None


def _set_mute(muted):
    vol = _get_volume_interface()
    if vol is None:
        return False
    try:
        vol.SetMute(1 if muted else 0, None)
        return True
    except Exception as e:
        print("Mute set error:", e)
        return False


def _lock_windows():
    try:
        ctypes.windll.user32.LockWorkStation()
        return True
    except Exception as e:
        print("Lock error:", e)
        return False


def _sleep_windows():
    try:
        subprocess.Popen(
            ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return True
    except Exception as e:
        print("Sleep error:", e)
        return False


# =========================================================
# LOCAL COMPUTER COMMAND ENGINE
# =========================================================

APP_ALIASES = {
    "chrome": ["chrome.exe"],
    "google chrome": ["chrome.exe"],
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "calc": ["calc.exe"],
    "file explorer": ["explorer.exe"],
    "explorer": ["explorer.exe"],
}


VS_CODE_CANDIDATES = [
    os.path.expandvars(
        r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"
    ),
    os.path.expandvars(
        r"%ProgramFiles%\Microsoft VS Code\Code.exe"
    ),
    os.path.expandvars(
        r"%ProgramFiles(x86)%\Microsoft VS Code\Code.exe"
    ),
]


VISUAL_STUDIO_CANDIDATES = [
    os.path.expandvars(
        r"%ProgramFiles%\Microsoft Visual Studio\2022\Community\Common7\IDE\devenv.exe"
    ),
    os.path.expandvars(
        r"%ProgramFiles%\Microsoft Visual Studio\2022\Professional\Common7\IDE\devenv.exe"
    ),
    os.path.expandvars(
        r"%ProgramFiles%\Microsoft Visual Studio\2022\Enterprise\Common7\IDE\devenv.exe"
    ),
]


FOLDER_ALIASES = {
    "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
    "download": os.path.join(os.path.expanduser("~"), "Downloads"),
    "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
    "documents": os.path.join(os.path.expanduser("~"), "Documents"),
    "document": os.path.join(os.path.expanduser("~"), "Documents"),
    "pictures": os.path.join(os.path.expanduser("~"), "Pictures"),
    "music folder": os.path.join(os.path.expanduser("~"), "Music"),
    "videos": os.path.join(os.path.expanduser("~"), "Videos"),
}


CONFIRMATION_REQUIRED = None

USER_NAME = "Umar"


# =========================================================
# NEW: CENTRAL APP REGISTRY (additive)
# =========================================================

APP_REGISTRY = {
    "chrome": {
        "process": "chrome.exe",
        "candidates": [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            "chrome",
        ],
    },
    "google chrome": {
        "process": "chrome.exe",
        "candidates": [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            "chrome",
        ],
    },
    "notepad": {
        "process": "notepad.exe",
        "candidates": ["notepad.exe"],
    },
    "calculator": {
        "process": "Calculator.exe",
        "candidates": ["calc.exe"],
    },
    "calc": {
        "process": "Calculator.exe",
        "candidates": ["calc.exe"],
    },
    "file explorer": {
        "process": "explorer.exe",
        "candidates": ["explorer.exe"],
    },
    "explorer": {
        "process": "explorer.exe",
        "candidates": ["explorer.exe"],
    },
    "word": {
        "process": "WINWORD.EXE",
        "candidates": [
            os.path.expandvars(r"%ProgramFiles%\Microsoft Office\root\Office16\WINWORD.EXE"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft Office\root\Office16\WINWORD.EXE"),
            "winword",
        ],
    },
    "microsoft word": {
        "process": "WINWORD.EXE",
        "candidates": [
            os.path.expandvars(r"%ProgramFiles%\Microsoft Office\root\Office16\WINWORD.EXE"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft Office\root\Office16\WINWORD.EXE"),
            "winword",
        ],
    },
    "excel": {
        "process": "EXCEL.EXE",
        "candidates": [
            os.path.expandvars(r"%ProgramFiles%\Microsoft Office\root\Office16\EXCEL.EXE"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft Office\root\Office16\EXCEL.EXE"),
            "excel",
        ],
    },
    "powerpoint": {
        "process": "POWERPNT.EXE",
        "candidates": [
            os.path.expandvars(r"%ProgramFiles%\Microsoft Office\root\Office16\POWERPNT.EXE"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft Office\root\Office16\POWERPNT.EXE"),
            "powerpnt",
        ],
    },
    "outlook": {
        "process": "OUTLOOK.EXE",
        "candidates": [
            os.path.expandvars(r"%ProgramFiles%\Microsoft Office\root\Office16\OUTLOOK.EXE"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft Office\root\Office16\OUTLOOK.EXE"),
            "outlook",
        ],
    },
    "spotify": {
        "process": "Spotify.exe",
        "candidates": [
            os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
            "spotify",
        ],
    },
    "vlc": {
        "process": "vlc.exe",
        "candidates": [
            os.path.expandvars(r"%ProgramFiles%\VideoLAN\VLC\vlc.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\VideoLAN\VLC\vlc.exe"),
            "vlc",
        ],
    },
    "telegram": {
        "process": "Telegram.exe",
        "candidates": [
            os.path.expandvars(r"%APPDATA%\Telegram Desktop\Telegram.exe"),
            "telegram",
        ],
    },
    "discord": {
        "process": "Discord.exe",
        "candidates": [
            os.path.expandvars(r"%LOCALAPPDATA%\Discord\Update.exe"),
            "discord",
        ],
    },
    "steam": {
        "process": "steam.exe",
        "candidates": [
            os.path.expandvars(r"%ProgramFiles(x86)%\Steam\steam.exe"),
            os.path.expandvars(r"%ProgramFiles%\Steam\steam.exe"),
            "steam",
        ],
    },
    "zoom": {
        "process": "Zoom.exe",
        "candidates": [
            os.path.expandvars(r"%APPDATA%\Zoom\bin\Zoom.exe"),
            "zoom",
        ],
    },
    "teams": {
        "process": "ms-teams.exe",
        "candidates": [
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WindowsApps\ms-teams.exe"),
            "ms-teams",
        ],
    },
    "vs code": {
        "process": "Code.exe",
        "candidates": [
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft VS Code\Code.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft VS Code\Code.exe"),
            "code",
        ],
    },
    "vscode": {
        "process": "Code.exe",
        "candidates": [
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft VS Code\Code.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft VS Code\Code.exe"),
            "code",
        ],
    },
    "visual studio code": {
        "process": "Code.exe",
        "candidates": [
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft VS Code\Code.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft VS Code\Code.exe"),
            "code",
        ],
    },
    "visual studio": {
        "process": "devenv.exe",
        "candidates": [
            os.path.expandvars(r"%ProgramFiles%\Microsoft Visual Studio\2022\Community\Common7\IDE\devenv.exe"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft Visual Studio\2022\Professional\Common7\IDE\devenv.exe"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft Visual Studio\2022\Enterprise\Common7\IDE\devenv.exe"),
        ],
    },
    "paint": {
        "process": "mspaint.exe",
        "candidates": ["mspaint.exe"],
    },
    "cmd": {
        "process": "cmd.exe",
        "candidates": ["cmd.exe"],
    },
    "command prompt": {
        "process": "cmd.exe",
        "candidates": ["cmd.exe"],
    },
    "powershell": {
        "process": "powershell.exe",
        "candidates": ["powershell.exe"],
    },
    "task manager": {
        "process": "Taskmgr.exe",
        "candidates": ["taskmgr.exe"],
    },
    "snipping tool": {
        "process": "SnippingTool.exe",
        "candidates": ["snippingtool.exe"],
    },
}


def _resolve_app_exe(app_key):
    entry = APP_REGISTRY.get(app_key)
    if not entry:
        return None, None
    for candidate in entry["candidates"]:
        try:
            if os.path.isabs(candidate) or "\\" in candidate or "/" in candidate:
                if os.path.exists(candidate):
                    return candidate, entry["process"]
            else:
                found = shutil.which(candidate)
                if found:
                    return found, entry["process"]
        except Exception:
            continue
    return None, entry["process"]


def _open_app(app_key, args=None):
    exe, process = _resolve_app_exe(app_key)
    if not exe:
        return False, process
    try:
        subprocess.Popen(
            [exe] + (args or []),
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return True, process
    except Exception as e:
        print(f"Open app {app_key} error:", e)
        return False, process


def _close_app(app_key):
    _, process = _resolve_app_exe(app_key)
    if not process:
        return False, None
    try:
        result = subprocess.run(
            ["taskkill", "/IM", process, "/F"],
            capture_output=True, text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return result.returncode == 0, process
    except Exception as e:
        print(f"Close app {app_key} error:", e)
        return False, process


# =========================================================
# NEW: FILE/FOLDER HELPERS (additive)
# =========================================================

def _search_roots():
    home = os.path.expanduser("~")
    return [
        os.path.join(home, "Downloads"),
        os.path.join(home, "Desktop"),
        os.path.join(home, "Documents"),
        os.path.join(home, "Pictures"),
        os.path.join(home, "Videos"),
        os.path.join(home, "Music"),
        os.path.join(home, "OneDrive", "Desktop"),
        os.path.join(home, "OneDrive", "Documents"),
    ]


def _find_item_by_name(name, want_dir=None):
    if not name:
        return None
    target = name.strip().lower()
    for root in _search_roots():
        if not os.path.isdir(root):
            continue
        try:
            for child in os.scandir(root):
                if child.name.lower() == target:
                    if want_dir is True and not child.is_dir():
                        continue
                    if want_dir is False and not child.is_file():
                        continue
                    return child.path
        except Exception:
            pass
    return None


def _open_item(path):
    if not path or not os.path.exists(path):
        return False
    try:
        os.startfile(path)
        return True
    except Exception as e:
        print("Open item error:", e)
        return False


# =========================================================
# NEW: BROWSER SCROLL / NAVIGATION (additive)
# =========================================================

def _browser_scroll(direction="down"):
    if not PYAUTOGUI_AVAILABLE:
        return False
    try:
        if direction == "down":
            pyautogui.press("pagedown")
        else:
            pyautogui.press("pageup")
        return True
    except Exception as e:
        print("Scroll error:", e)
        return False


def _browser_back():
    if not PYAUTOGUI_AVAILABLE:
        return False
    try:
        pyautogui.hotkey("alt", "left")
        return True
    except Exception as e:
        print("Back error:", e)
        return False


def _browser_forward():
    if not PYAUTOGUI_AVAILABLE:
        return False
    try:
        pyautogui.hotkey("alt", "right")
        return True
    except Exception as e:
        print("Forward error:", e)
        return False


def _browser_new_tab():
    if not PYAUTOGUI_AVAILABLE:
        return False
    try:
        pyautogui.hotkey("ctrl", "t")
        return True
    except Exception:
        return False


def _browser_refresh():
    if not PYAUTOGUI_AVAILABLE:
        return False
    try:
        pyautogui.press("f5")
        return True
    except Exception:
        return False


# =========================================================
# NEW: TYPE TEXT (additive)
# =========================================================

def _type_text(text):
    if not PYAUTOGUI_AVAILABLE:
        return False
    if not text:
        return False
    try:
        time.sleep(0.4)
        pyautogui.typewrite(text, interval=0.02)
        return True
    except Exception as e:
        print("Type text error:", e)
        return False


# =========================================================
# NEW: CAMERA CONTROL (additive)
#   - open camera -> live preview in a window
#   - take picture -> saves to ~/Pictures/JARVIS and
#                     displays the captured image on screen
#   - close camera -> releases webcam cleanly
# =========================================================

_CAMERA = None
_CAMERA_PREVIEW_THREAD = None
_CAMERA_RUNNING = False
_LAST_CAPTURED_PATH = None


def _jarvis_pictures_dir():
    home = os.path.expanduser("~")
    path = os.path.join(home, "Pictures", "JARVIS")
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass
    return path


def _open_camera():
    global _CAMERA, _CAMERA_PREVIEW_THREAD, _CAMERA_RUNNING

    if not CV2_AVAILABLE:
        return False, "opencv"

    try:
        if _CAMERA is not None and _CAMERA_RUNNING:
            return True, None

        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            return False, "no_camera"

        _CAMERA = cam
        _CAMERA_RUNNING = True

        def preview_loop():
            global _CAMERA_RUNNING
            while _CAMERA_RUNNING and _CAMERA is not None:
                ret, frame = _CAMERA.read()
                if not ret:
                    break
                cv2.imshow("JARVIS CAMERA - press q to close", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
            try:
                cv2.destroyWindow("JARVIS CAMERA - press q to close")
            except Exception:
                pass

        _CAMERA_PREVIEW_THREAD = threading.Thread(
            target=preview_loop,
            name="JarvisCamera",
            daemon=True
        )
        _CAMERA_PREVIEW_THREAD.start()
        return True, None

    except Exception as e:
        print("Open camera error:", e)
        return False, "error"


def _take_picture():
    """
    Capture a single frame from the webcam, save it, and
    display it on screen until the user closes the window.
    """
    global _CAMERA, _LAST_CAPTURED_PATH
    if not CV2_AVAILABLE:
        return None
    try:
        cam = _CAMERA
        if cam is None or not cam.isOpened():
            cam = cv2.VideoCapture(0)
            if not cam.isOpened():
                return None
            _CAMERA = cam

        for _ in range(5):
            cam.read()
            time.sleep(0.05)

        ret, frame = cam.read()
        if not ret or frame is None:
            return None

        folder = _jarvis_pictures_dir()
        filename = "jarvis_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"
        path = os.path.join(folder, filename)
        cv2.imwrite(path, frame)
        _LAST_CAPTURED_PATH = path

        # Show the captured image so the user can see it.
        try:
            cv2.imshow(
                "JARVIS CAPTURED PHOTO - press any key to close",
                frame
            )
            cv2.waitKey(1)
        except Exception as show_err:
            print("Show picture error:", show_err)

        return path
    except Exception as e:
        print("Take picture error:", e)
        return None


def _close_camera():
    global _CAMERA, _CAMERA_RUNNING
    try:
        _CAMERA_RUNNING = False
        if _CAMERA is not None:
            try:
                _CAMERA.release()
            except Exception:
                pass
            _CAMERA = None
        if CV2_AVAILABLE:
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass
        return True
    except Exception as e:
        print("Close camera error:", e)
        return False


# =========================================================
# CORE HELPERS  (UNCHANGED)
# =========================================================

def _norm_command(text):

    text = normalize_urdu_command(text).lower()
    text = text.replace("’", "'")
    text = re.sub(r"[^a-z0-9_\\/:.\-\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def _contains_any(text, phrases):
    return any(p in text for p in phrases)


def _launch_executable(path_or_name, args=None):
    try:
        subprocess.Popen(
            [path_or_name] + (args or []),
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return True
    except Exception as e:
        print("Launch error:", e)
        return False


def _find_existing(candidates):
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate
    return None


def _open_folder(path):
    if not path or not os.path.isdir(path):
        return False
    try:
        os.startfile(path)
        return True
    except Exception as e:
        print("Folder open error:", e)
        return False


def _close_process(image_name):
    try:
        result = subprocess.run(
            ["taskkill", "/IM", image_name, "/F"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return result.returncode == 0
    except Exception as e:
        print("Close process error:", e)
        return False


def _open_chrome():
    try:
        chrome = shutil.which("chrome")
    except Exception:
        chrome = None

    if chrome:
        subprocess.Popen(
            [chrome],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return True

    for candidate in [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]:
        if os.path.exists(candidate):
            subprocess.Popen(
                [candidate],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return True

    try:
        webbrowser.open("https://www.google.com")
        return True
    except Exception:
        return False


def _chrome_executable():
    try:
        chrome = shutil.which("chrome")
    except Exception:
        chrome = None

    if chrome:
        return chrome

    for candidate in [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]:
        if os.path.exists(candidate):
            return candidate

    return None


def _open_youtube(query=None):
    try:
        if query:
            url = (
                "https://www.youtube.com/results?search_query="
                + quote_plus(query)
            )
        else:
            url = "https://www.youtube.com/"

        chrome = _chrome_executable()
        if chrome:
            subprocess.Popen(
                [chrome, url],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            webbrowser.open(url)

        return True
    except Exception as e:
        print("YouTube open error:", e)
        return False


def _close_youtube_tab():
    try:
        if PYAUTOGUI_AVAILABLE:
            pyautogui.hotkey("ctrl", "w")
            return True
        return _close_process("chrome.exe")
    except Exception as e:
        print("YouTube tab close error:", e)
        return False


def _stop_media():
    try:
        if PYAUTOGUI_AVAILABLE:
            pyautogui.press("media_play_pause")
            return True
        return False
    except Exception as e:
        print("Media stop error:", e)
        return False


def _extract_youtube_query(text):

    t = command_ready_text(text).lower()

    t = re.sub(r"\b(?:hey|hello|okay|ok|jarvis|jarv)\b", " ", t)
    t = re.sub(r"\b(?:youtube)\b", " ", t)
    t = re.sub(
        r"\b(?:kholo|khol|open|chalao|chala|lagao|laga|play|"
        r"search|karo|kar do|please)\b",
        " ",
        t
    )
    t = re.sub(r"\b(?:aur|and|par|pe|per|mein|me|pah|paye)\b", " ", t)
    t = re.sub(r"\b(?:music|gaana|gana)\b", " music ", t)
    t = re.sub(r"\b(?:close|band|band karo|band kar do)\b", " ", t)
    t = re.sub(r"\s+", " ", t).strip()

    if not t:
        return "peaceful music"

    return t


def _find_folder_from_command(text):

    low = _norm_command(text)

    for alias, path in FOLDER_ALIASES.items():
        if alias in low:
            return path

    m = re.search(r"([a-z]:\\[^?\n]+)", text, re.IGNORECASE)
    if m:
        path = m.group(1).strip().rstrip(".,!? ")
        if os.path.isdir(path):
            return path

    m = re.search(
        r"(?:folder|directory)\s+([a-zA-Z0-9 _.-]{2,60})",
        low
    )
    if m:
        name = m.group(1).strip()
        name = re.sub(
            r"\b(?:open|khol|kholo|please|kar do|karo)$",
            "",
            name
        ).strip()

        roots = [
            os.path.join(os.path.expanduser("~"), "Downloads"),
            os.path.join(os.path.expanduser("~"), "Desktop"),
            os.path.join(os.path.expanduser("~"), "Documents"),
            os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop"),
        ]
        for root in roots:
            if not os.path.isdir(root):
                continue
            try:
                for child in os.scandir(root):
                    if (child.is_dir()
                            and child.name.lower() == name.lower()):
                        return child.path
            except Exception:
                pass

    return None


def _open_url(url):
    try:
        chrome = _chrome_executable()
        if chrome:
            subprocess.Popen(
                [chrome, url],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            webbrowser.open(url)
        return True
    except Exception as e:
        print("URL open error:", e)
        return False


def _open_google(query=None, images=False):
    if query:
        if images:
            base = ("https://www.google.com/search?tbm=isch&q="
                    + quote_plus(query))
        else:
            base = ("https://www.google.com/search?q="
                    + quote_plus(query))
    else:
        base = "https://images.google.com" if images else "https://www.google.com"
    return _open_url(base)


def _open_whatsapp():
    return _open_url("https://web.whatsapp.com/")


def _open_chatgpt():
    return _open_url("https://chatgpt.com/")


def _open_gmail():
    return _open_url("https://mail.google.com/")


def _open_facebook():
    return _open_url("https://www.facebook.com/")


def _open_instagram():
    return _open_url("https://www.instagram.com/")


_KNOWN_WEBSITES = {
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "youtube": "https://www.youtube.com",
    "facebook": "https://www.facebook.com",
    "instagram": "https://www.instagram.com",
    "whatsapp": "https://web.whatsapp.com",
    "chatgpt": "https://chatgpt.com",
    "twitter": "https://twitter.com",
    "x": "https://x.com",
    "linkedin": "https://www.linkedin.com",
    "github": "https://github.com",
    "stack overflow": "https://stackoverflow.com",
    "reddit": "https://www.reddit.com",
    "amazon": "https://www.amazon.com",
    "netflix": "https://www.netflix.com",
    "wikipedia": "https://www.wikipedia.org",
}


def _open_known_website(name):
    low = name.lower().strip()
    if low in _KNOWN_WEBSITES:
        return _open_url(_KNOWN_WEBSITES[low])
    domain = low.replace(" ", "") + ".com"
    return _open_url("https://" + domain)


def _extract_search_query(text, trigger_words):

    t = _norm_command(text)

    for word in trigger_words:
        m = re.search(
            re.escape(word) + r"\s+(.+)$",
            t,
            re.IGNORECASE
        )
        if m:
            q = m.group(1).strip()
            q = re.sub(
                r"\b(?:karo|kar do|please|search|dhundo|dhoondo)\b",
                " ",
                q,
                flags=re.I
            )
            return re.sub(r"\s+", " ", q).strip(" ,.!?")

    return None


# =========================================================
# FAST PC / JARVIS CONTROL helpers  (UNCHANGED)
# =========================================================

def get_current_date():
    now = datetime.now()
    return now.strftime("%A, %d %B %Y")


def get_current_time():
    now = datetime.now()
    return now.strftime("%I:%M %p").lstrip("0")


def get_battery_status():
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "(Get-CimInstance Win32_Battery | "
                "Select-Object -First 1 "
                "EstimatedChargeRemaining, BatteryStatus, "
                "EstimatedRunTime | "
                "ConvertTo-Json -Compress)"
            ],
            capture_output=True,
            text=True,
            timeout=3
        )
        output = result.stdout.strip()
        if not output:
            return None, None, None

        data = json.loads(output)
        percentage = data.get("EstimatedChargeRemaining")
        if percentage is None:
            return None, None, None

        status_code = data.get("BatteryStatus")
        if status_code in [2, 6, 7, 8, 9, 11]:
            status = "charging"
        elif status_code == 3:
            status = "fully charged"
        else:
            status = "not charging"

        runtime_minutes = data.get("EstimatedRunTime")
        if runtime_minutes in (None, 0, 71582788):
            runtime_minutes = None

        return int(percentage), status, runtime_minutes
    except Exception as e:
        print("Battery check error:", e)
        return None, None, None


def _format_runtime(minutes):
    if not minutes or minutes <= 0:
        return None
    h = minutes // 60
    m = minutes % 60
    parts = []
    if h:
        parts.append(f"{h} hours")
    if m:
        parts.append(f"{m} minutes")
    return " ".join(parts) if parts else None


def shutdown_windows():
    try:
        subprocess.Popen(
            ["shutdown", "/s", "/t", "0"],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return True
    except Exception as e:
        print("Shutdown error:", e)
        return False


def close_active_window():
    try:
        if PYAUTOGUI_AVAILABLE:
            pyautogui.hotkey("alt", "f4")
            return True
        return False
    except Exception as e:
        print("Close window error:", e)
        return False


def close_all_chrome_tabs():
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "chrome.exe"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return True
    except Exception as e:
        print("Close Chrome error:", e)
        return False


def get_chrome_tab_count():
    try:
        url = "http://127.0.0.1:9222/json"
        with urllib.request.urlopen(url, timeout=1.5) as response:
            data = json.loads(response.read().decode("utf-8"))
        tabs = [item for item in data if item.get("type") == "page"]
        return len(tabs)
    except Exception as e:
        print("Chrome tab count unavailable:", e)
        return None


def get_profile_answer(text):

    t = normalize_urdu_command(text).lower().strip()

    if any(phrase in t for phrase in [
        "mera naam kya hai", "my name", "what is my name",
        "mera full name", "full name kya hai",
        "miranam kya hai", "mira naam kya hai",
        "mera nam kya hai", "meranam kya hai"
    ]):
        return "Tumhara full name Syed Umar Hussain hai."

    if any(phrase in t for phrase in [
        "meri age", "meri umar", "my age", "how old am i",
        "meri age kya hai", "umar kitni hai"
    ]):
        return "Umar, tumhari age 23 years hai."

    if any(phrase in t for phrase in [
        "meri birthday", "my birthday", "birthday kab",
        "when is my birthday", "birthday kya hai"
    ]):
        return "Tumhari birthday 17 February hai."

    if any(phrase in t for phrase in [
        "main kya hoon", "mera profession", "my profession",
        "what do i do", "main kya kaam karta hoon",
        "mera kaam kya hai"
    ]):
        return "Tum Software Engineer aur AI Engineer ho."

    if any(phrase in t for phrase in [
        "meri university", "my university", "where do i study",
        "main kahan parhta hoon", "main kahan padhta hoon",
        "university ka naam kya hai", "university kya hai"
    ]):
        return "Tum Sindh University, Jamshoro mein study karte ho."

    if any(phrase in t for phrase in [
        "ai teacher", "ai sir ka naam", "ai ustad",
        "mere ai teacher ka naam", "my ai teacher",
        "ai teacher ka naam kya hai"
    ]):
        return "Tumhare AI teacher ka naam Rafiq Bhutto Sir hai."

    if any(phrase in t for phrase in [
        "main kahan rehta hoon", "where do i live",
        "meri location", "my location",
        "main kahan rehta", "mera shehar kya hai"
    ]):
        return "Tum Hyderabad, Pakistan mein rehte ho."

    return None


# =========================================================
# YOUTUBE MUSIC CONTROL  (extended; original preserved)
# =========================================================

YOUTUBE_MUSIC_ACTIVE = False
CURRENT_MUSIC_QUERY = ""


def _play_youtube_music(query):
    """
    Same behaviour as before, with a more reliable primary
    strategy (Tab + Enter) and the original pixel-click kept
    as fallback. Falls back identically if pyautogui missing.
    """
    global YOUTUBE_MUSIC_ACTIVE
    global CURRENT_MUSIC_QUERY

    if not query:
        query = "peaceful music"

    print("YouTube music search:", query)

    try:

        url = (
            "https://www.youtube.com/results?search_query="
            + quote_plus(query)
        )

        chrome = _chrome_executable()

        if chrome:
            subprocess.Popen(
                [chrome, "--new-window", url],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            webbrowser.open(url)

        YOUTUBE_MUSIC_ACTIVE = True
        CURRENT_MUSIC_QUERY = query

        if PYAUTOGUI_AVAILABLE:
            try:
                time.sleep(3.0)
                # NEW primary strategy: Tab to first result + Enter
                pyautogui.press("tab", presses=7, interval=0.08)
                pyautogui.press("enter")
                time.sleep(0.6)
            except Exception as click_err:
                # Original pixel-click fallback
                try:
                    screen_w, screen_h = pyautogui.size()
                    click_x = int(screen_w * 0.25)
                    click_y = int(screen_h * 0.42)
                    pyautogui.click(click_x, click_y)
                    print("Fallback pixel click at", click_x, click_y)
                except Exception as fallback_err:
                    print(
                        "Auto-play both strategies failed:",
                        click_err, "/", fallback_err
                    )

        return True

    except Exception as e:
        print("YouTube music error:", e)
        return False


def _pause_youtube_music():
    try:
        if PYAUTOGUI_AVAILABLE:
            pyautogui.press("k")
            return True
        return False
    except Exception as e:
        print("Pause music error:", e)
        return False


def _resume_youtube_music():
    try:
        if PYAUTOGUI_AVAILABLE:
            pyautogui.press("k")
            return True
        return False
    except Exception as e:
        print("Resume music error:", e)
        return False


def _stop_youtube_music():
    global YOUTUBE_MUSIC_ACTIVE
    global CURRENT_MUSIC_QUERY
    try:
        if PYAUTOGUI_AVAILABLE:
            pyautogui.hotkey("ctrl", "w")
            YOUTUBE_MUSIC_ACTIVE = False
            CURRENT_MUSIC_QUERY = ""
            return True
        return False
    except Exception as e:
        print("Stop music error:", e)
        return False


# =========================================================
# SMART MUSIC CONVERSATION  (UNCHANGED)
# =========================================================

MUSIC_PENDING = False
MUSIC_PENDING_FIELD = None
MUSIC_DRAFT_TYPE = None
MUSIC_DRAFT_SINGER = None


_MUSIC_TYPE_KEYWORDS = {
    "romantic": "romantic",
    "romance": "romantic",
    "love": "love",
    "sad": "sad",
    "gham": "sad",
    "fast": "fast",
    "upbeat": "fast",
    "party": "party",
    "dance": "dance",
    "chill": "chill",
    "soft": "soft",
    "emotional": "emotional",
    "old": "old Bollywood",
    "new": "new Bollywood",
    "workout": "workout",
    "trending": "trending",
}


_KNOWN_SINGERS = [
    "arijit singh",
    "atif aslam",
    "neha kakkar",
    "taylor swift",
    "shreya ghoshal",
    "sonu nigam",
    "kishore kumar",
    "lata mangeshkar",
    "rahat fateh ali khan",
    "coke studio",
    "nusrat fateh ali khan",
    "udit narayan",
    "alka yagnik",
]


def _extract_music_type(text):
    if not text:
        return None
    low = text.lower()
    for key, value in _MUSIC_TYPE_KEYWORDS.items():
        if re.search(r"\b" + re.escape(key) + r"\b", low):
            return value
    return None


def _extract_singer(text):
    if not text:
        return None
    low = text.lower()
    for singer in _KNOWN_SINGERS:
        if singer in low:
            return " ".join(w.capitalize() for w in singer.split())
    m = re.search(
        r"([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,3})\s+"
        r"(?:ka|ke|ki|na|naam|songs?|music)\b",
        text
    )
    if m:
        candidate = m.group(1).strip()
        if candidate.lower() not in (
            "jarvis", "youtube", "bollywood",
            "song", "songs", "music", "play",
        ):
            return candidate
    m = re.search(
        r"([A-Za-z]+(?:\s+[A-Za-z]+){0,2})\s+(?:ka|ke|ki)\s+"
        r"(?:song|songs|music|gaana|gaane)",
        low
    )
    if m:
        candidate = " ".join(w.capitalize() for w in m.group(1).split())
        if candidate.lower() not in ("jarvis", "youtube", "bollywood"):
            return candidate
    return None


def _build_music_query(music_type=None, singer=None, song=None):
    parts = []
    if singer:
        parts.append(singer)
    if music_type and singer:
        parts.append(music_type)
    elif music_type and not singer:
        parts.append("Bollywood")
        parts.append(music_type)
    if song:
        parts.append(song)
    if not parts:
        return None
    if singer and not music_type and not song:
        return singer + " songs"
    return " ".join(parts) + (" songs" if len(parts) < 3 else "")


def _smart_music_command(text):

    global MUSIC_PENDING
    global MUSIC_PENDING_FIELD
    global MUSIC_DRAFT_TYPE
    global MUSIC_DRAFT_SINGER

    if not text:
        return False, None

    low = command_ready_text(text).lower().strip()

    pause_patterns = [
        "music pause", "song pause", "pause music", "pause song",
        "music pause karo", "music pause kar do", "song pause karo",
        "gaana pause", "gana pause", "music rok do", "song rok do",
        "music rok",
    ]
    if any(p in low for p in pause_patterns):
        ok = _pause_youtube_music()
        if ok:
            return True, "Ji Umar, music pause kar diya."
        return True, "Umar, music pause nahi ho saka."

    resume_patterns = [
        "music resume", "song resume", "resume music", "resume song",
        "music resume karo", "music chalao", "song chalao",
        "music dobara chalao", "song dobara chalao",
        "gaana chalao", "gana chalao", "play music", "music play",
        "wapas chalao", "wapas chala",
    ]
    if any(p in low for p in resume_patterns):
        if not MUSIC_PENDING:
            ok = _resume_youtube_music()
            if ok:
                return True, "Ji Umar, music resume kar diya."
            return True, "Umar, music resume nahi ho saka."

    stop_patterns = [
        "music band karo", "music band kar do", "music close karo",
        "music close kar do", "music cut karo", "music kat do",
        "music hata do", "song band karo", "song band kar do",
        "song close karo", "song rok do", "song kat do",
        "music stop karo", "music stop kar do",
        "youtube music band", "youtube music close",
    ]
    if any(p in low for p in stop_patterns):
        ok = _stop_youtube_music()
        if ok:
            return True, "Ji Umar, music band kar diya."
        return True, "Umar, music band nahi ho saka."

    if MUSIC_PENDING:
        if MUSIC_PENDING_FIELD == "type":
            music_type = _extract_music_type(low)
            singer = _extract_singer(text)
            if singer and not music_type:
                MUSIC_PENDING = False
                MUSIC_PENDING_FIELD = None
                MUSIC_DRAFT_TYPE = None
                query = _build_music_query(singer=singer)
                ok = _play_youtube_music(query)
                MUSIC_DRAFT_SINGER = None
                if ok:
                    return True, (
                        f"Ji Umar, {singer} ka song play kar raha hoon."
                    )
                return True, "Umar, song play nahi ho saka. Ek baar phir bolo."
            if music_type:
                MUSIC_PENDING = False
                MUSIC_PENDING_FIELD = None
                query = _build_music_query(
                    music_type=music_type,
                    singer=MUSIC_DRAFT_SINGER
                )
                ok = _play_youtube_music(query)
                MUSIC_DRAFT_TYPE = None
                MUSIC_DRAFT_SINGER = None
                if ok:
                    return True, (
                        f"Ji Umar, {music_type} Bollywood song play kar raha hoon."
                    )
                return True, "Umar, song play nahi ho saka. Ek baar phir bolo."
            return True, (
                "Umar, kis type ka Bollywood song chahiye? "
                "Romantic, love, sad, party ya fast?"
            )
        if MUSIC_PENDING_FIELD == "singer":
            singer = _extract_singer(text)
            music_type = _extract_music_type(low)
            if singer:
                MUSIC_PENDING = False
                MUSIC_PENDING_FIELD = None
                query = _build_music_query(
                    singer=singer,
                    music_type=MUSIC_DRAFT_TYPE
                )
                ok = _play_youtube_music(query)
                MUSIC_DRAFT_TYPE = None
                MUSIC_DRAFT_SINGER = None
                if ok:
                    return True, (
                        f"Ji Umar, {singer} ka song play kar raha hoon."
                    )
                return True, "Umar, song play nahi ho saka. Ek baar phir bolo."
            if music_type:
                MUSIC_DRAFT_TYPE = music_type
                MUSIC_PENDING_FIELD = "singer"
                return True, "Theek hai. Kis singer ka song chahiye?"
            MUSIC_PENDING = False
            MUSIC_PENDING_FIELD = None
            query = _build_music_query(music_type=MUSIC_DRAFT_TYPE)
            ok = _play_youtube_music(query)
            MUSIC_DRAFT_TYPE = None
            if ok:
                return True, "Ji Umar, Bollywood song play kar raha hoon."
            return True, "Umar, song play nahi ho saka. Ek baar phir bolo."

    music_intent = any(
        p in low
        for p in [
            "song", "songs", "music", "gaana", "gaane", "gana", "ganay",
            "play karo", "chalao", "lagao", "sunao", "laga do",
        ]
    )
    if not music_intent:
        return False, None

    has_bollywood = "bollywood" in low
    singer = _extract_singer(text)
    music_type = _extract_music_type(low)

    song = None
    if not singer:
        m = re.search(
            r"\bplay\b\s+(.+?)(?:\s+(?:karo|kar do|please))?$",
            low
        )
        if m:
            candidate = m.group(1).strip()
            if candidate and candidate not in ("music", "song", "songs"):
                song = candidate
        if song is None:
            m = re.search(
                r"(.+?)\s+(?:play karo|chalao|lagao|sunao|laga do)$",
                low
            )
            if m:
                candidate = m.group(1).strip()
                candidate = re.sub(
                    r"^(?:jarvis|hey|hello|okay|ok)\s+",
                    "",
                    candidate
                ).strip()
                if candidate and candidate not in (
                    "music", "song", "songs",
                    "bollywood", "gaana", "gaane",
                ):
                    song = candidate

    if singer:
        query = _build_music_query(singer=singer, music_type=music_type)
        ok = _play_youtube_music(query)
        if ok:
            if music_type:
                return True, (
                    f"Ji Umar, {singer} ka {music_type} song play kar raha hoon."
                )
            return True, (
                f"Ji Umar, {singer} ka song play kar raha hoon."
            )
        return True, "Umar, song play nahi ho saka. Ek baar phir bolo."

    if song:
        query = song
        if has_bollywood:
            query = "Bollywood " + song
        ok = _play_youtube_music(query)
        if ok:
            return True, f"Ji Umar, {song} play kar raha hoon."
        return True, "Umar, song play nahi ho saka. Ek baar phir bolo."

    if music_type:
        query = _build_music_query(music_type=music_type)
        ok = _play_youtube_music(query)
        if ok:
            return True, (
                f"Ji Umar, {music_type} Bollywood song play kar raha hoon."
            )
        return True, "Umar, song play nahi ho saka. Ek baar phir bolo."

    if has_bollywood or "music" in low or "song" in low:
        MUSIC_PENDING = True
        MUSIC_PENDING_FIELD = "type"
        MUSIC_DRAFT_TYPE = None
        MUSIC_DRAFT_SINGER = None
        return True, (
            "Umar, kis type ka Bollywood song chahiye? "
            "Romantic, love, sad, party ya fast?"
        )

    return False, None


# =========================================================
# --- END PART 1 of 2 ---
# PART 2 continues with:
#   - _extract_chatgpt_message / _open_chatgpt_and_type
#   - execute_fast_local_command (original preserved +
#     one additive camera branch at the end)
#   - NEW handlers (_handle_open_close_app, _handle_youtube,
#     _handle_typing, _handle_file_open, _handle_camera,
#     _handle_browser_controls, _handle_google_search,
#     _handle_open_known_website, _handle_music_simple,
#     _handle_simple_confirm, _handle_chatgpt_type)
#   - _command_response (original branches preserved; new
#     handlers run first)
#   - execute_local_command, ask_jarvis
#   - listen_for_command, is_clear_direct_command,
#     recognize_bilingual, is_sleep_phrase, main
# =========================================================

# =========================================================
# JARVIS AI ASSISTANT - main.py
# PART 2 of 2  (all existing code preserved + additions)
# =========================================================

# =========================================================
# CHATGPT OPEN + TYPE MESSAGE  (UNCHANGED)
# =========================================================

def _extract_chatgpt_message(text):
    """
    Extract the message to type into ChatGPT.
    Handles:
      "ChatGPT kholo aur likho <message>"
      "ChatGPT kholo aur message likho <message>"
      "ChatGPT pe likho <message>"
      "ChatGPT mein message likho <message>"
    Returns the message string or None if this is just an open command.
    """
    if not text:
        return None

    low = text.lower()

    triggers = [
        "message likho",
        "likho",
        "type karo",
        "type kar do",
        "pe likho",
        "mein likho",
        "par likho",
        "pe type karo",
        "mein type karo",
    ]

    for trigger in triggers:
        idx = low.find(trigger)
        if idx == -1:
            continue
        after = text[idx + len(trigger):].strip()
        after = re.sub(r"^[:\-,;]+", "", after).strip()
        after = re.sub(r"^(?:that|kay|ke)\s+", "", after, flags=re.I).strip()
        if after:
            return after

    return None


def _open_chatgpt_and_type(message):
    """
    Open ChatGPT and type the given message into the input box.
    Does NOT send by default.
    """
    if not _open_chatgpt():
        return False

    if not message:
        return True

    if not PYAUTOGUI_AVAILABLE:
        print(
            "pyautogui not available; cannot type message into ChatGPT."
        )
        return False

    try:
        time.sleep(4.5)
        screen_w, screen_h = pyautogui.size()
        click_x = int(screen_w * 0.5)
        click_y = int(screen_h * 0.92)
        pyautogui.click(click_x, click_y)
        time.sleep(0.5)
        pyautogui.typewrite(message, interval=0.01)
        print("Typed into ChatGPT:", message)
        return True
    except Exception as e:
        print("ChatGPT typing error:", e)
        return False


# =========================================================
# EXECUTE FAST LOCAL COMMAND
# =========================================================
# All existing branches preserved unchanged.
# ONE additive branch (camera) appended at the end.

def execute_fast_local_command(text):

    if not text:
        return None

    t = normalize_urdu_command(text).lower().strip()

    t = re.sub(
        r"\b(?:hey|hello|okay|ok|jarvis|jarv)\b",
        " ",
        t
    )

    t = re.sub(r"\s+", " ", t).strip()

    # --------------------------------------------------------
    # BRIGHTNESS
    # --------------------------------------------------------

    if "brightness" in t or "brightnes" in t or "برائٹنس" in t:

        m = re.search(
            r"brightness\s+(?:ko\s+)?(\d{1,3})\s*(?:percent|%)?",
            t
        )

        if m:
            target = int(m.group(1))

            if not SBC_AVAILABLE:
                return (
                    "Umar, brightness control ke liye "
                    "screen_brightness_control install karein: "
                    "pip install screen-brightness-control"
                )

            if _set_brightness(target):
                return f"Ji Umar, brightness {target} percent kar di."

            return "Umar, brightness set nahi ho saki."

        wants_down = any(
            x in t
            for x in ["kam", "down", "decrease", "low", "ghata"]
        )

        wants_up = any(
            x in t
            for x in ["zyada", "barha", "barha do", "increase",
                      "high", "up", "tez"]
        )

        if wants_down or wants_up:

            if not SBC_AVAILABLE:
                return (
                    "Umar, brightness control ke liye "
                    "screen_brightness_control install karein: "
                    "pip install screen-brightness-control"
                )

            delta = -10 if wants_down else 10
            result = _change_brightness(delta)

            if result is not None:
                return f"Ji Umar, brightness ab {result} percent hai."

            return "Umar, brightness change nahi ho saki."

        current = _get_current_brightness()

        if current is not None:
            return f"Umar, abhi brightness {current} percent hai."

    # --------------------------------------------------------
    # VOLUME
    # --------------------------------------------------------

    if "volume" in t or "awaz" in t or "awaaz" in t:

        m = re.search(
            r"(?:volume|awaz|awaaz)\s+(?:ko\s+)?(\d{1,3})\s*(?:percent|%)?",
            t
        )

        if m:
            target = int(m.group(1))

            if not PYCAW_AVAILABLE:
                return (
                    "Umar, volume control ke liye pycaw install karein: "
                    "pip install pycaw comtypes"
                )

            if _set_volume_percent(target):
                return f"Ji Umar, volume {target} percent kar diya."

            return "Umar, volume set nahi ho saka."

        if "mute" in t or "silent" in t:

            if not PYCAW_AVAILABLE:
                return (
                    "Umar, mute ke liye pycaw install karein: "
                    "pip install pycaw comtypes"
                )

            if _set_mute(True):
                return "Ji Umar, volume mute kar diya."

            return "Umar, mute nahi ho saka."

        if "unmute" in t:

            if not PYCAW_AVAILABLE:
                return (
                    "Umar, unmute ke liye pycaw install karein: "
                    "pip install pycaw comtypes"
                )

            if _set_mute(False):
                return "Ji Umar, volume unmute kar diya."

            return "Umar, unmute nahi ho saka."

        wants_down = any(
            x in t
            for x in ["kam", "down", "decrease", "low", "ghata"]
        )

        wants_up = any(
            x in t
            for x in ["zyada", "barha", "increase", "high", "up", "tez"]
        )

        if wants_down or wants_up:

            if not PYCAW_AVAILABLE:
                return (
                    "Umar, volume control ke liye pycaw install karein: "
                    "pip install pycaw comtypes"
                )

            delta = -10 if wants_down else 10
            result = _change_volume(delta)

            if result is not None:
                return f"Ji Umar, volume ab {result} percent hai."

            return "Umar, volume change nahi ho saka."

        current = _get_current_volume_percent()

        if current is not None:
            return f"Umar, abhi volume {current} percent hai."

    # --------------------------------------------------------
    # STOP EVERYTHING
    # --------------------------------------------------------

    stop_patterns = [
        "stop everything",
        "stop everything now",
        "sab band karo",
        "sab kuch band karo",
        "sab kuch rok do",
        "everything stop",
        "music rok do",
        "music band karo",
        "music stop karo",
        "music stop kar do"
    ]

    if any(p in t for p in stop_patterns):

        _stop_media()

        if "everything" in t or "sab kuch" in t:

            close_all_chrome_tabs()

            return (
                "Ji Umar, music stop kar diya "
                "aur Chrome ke saare tabs band kar diye."
            )

        return "Ji Umar, music stop kar diya."

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    date_patterns = [
        "date kya hai",
        "aaj ki date",
        "aaj date",
        "today date",
        "what is the date",
        "what's the date",
        "tell me the date",
        "date batao",
        "date bata do",
        "mujhe date batao",
        "aaj kya date hai",
    ]

    if any(p in t for p in date_patterns):
        return f"Umar, aaj {get_current_date()} hai."

    # --------------------------------------------------------
    # TIME
    # --------------------------------------------------------

    time_patterns = [
        "time kya hai",
        "time batao",
        "time bata do",
        "abhi time",
        "current time",
        "what time is it",
        "what's the time",
        "tell me the time",
        "time please",
        "mujhe time batao",
        "abhi kitne baje hain",
        "kitne bajay hain",
        "kitne baje hain",
        "time kholo",
        "time khol",
        "clock kholo",
        "clock open",
        "current time batao",
        "abhi ka time"
    ]

    if any(p in t for p in time_patterns):
        return f"Umar, abhi {get_current_time()} ho rahe hain."

    # --------------------------------------------------------
    # BATTERY
    # --------------------------------------------------------

    battery_patterns = [
        "battery kitni hai",
        "battery kitne percent hai",
        "battery percentage",
        "battery percent",
        "charging kitni hai",
        "laptop ki battery",
        "laptop battery",
        "meri battery kitni hai",
        "how much battery",
        "battery level",
        "battery status",
        "how much charge",
        "charge kitna hai",
        "charging kitni",
        "charging batao",
        "charging dekh",
        "battery bach",
    ]

    if any(p in t for p in battery_patterns):

        percentage, status, runtime = get_battery_status()

        if percentage is None:
            return (
                "Umar, laptop ki battery information "
                "abhi read nahi ho saki."
            )

        runtime_text = _format_runtime(runtime)

        if status == "charging":
            if runtime_text:
                return (
                    f"Umar, battery {percentage} percent hai aur "
                    f"laptop charging par hai. Estimated remaining "
                    f"time {runtime_text} hai."
                )
            return (
                f"Umar, battery {percentage} percent hai aur "
                f"laptop charging par hai."
            )

        if status == "fully charged":
            return (
                f"Umar, battery {percentage} percent hai aur "
                f"battery fully charged hai."
            )

        if runtime_text:
            return (
                f"Umar, battery {percentage} percent hai. "
                f"Estimated remaining time {runtime_text} hai."
            )

        return f"Umar, battery {percentage} percent hai."

    # --------------------------------------------------------
    # LOCK / SLEEP
    # --------------------------------------------------------

    if any(p in t for p in [
        "laptop lock", "lock karo", "lock kar do",
        "lock laptop", "system lock",
    ]):
        if _lock_windows():
            return "Ji Umar, laptop lock kar diya."
        return "Umar, lock nahi ho saka."

    if any(p in t for p in [
        "laptop sleep", "sleep karo", "sleep kar do",
        "sula do", "so jao laptop",
    ]):
        speak("Theek hai Umar, laptop sleep ho raha hai.")
        time.sleep(0.4)
        _sleep_windows()
        return "__JARVIS_SLEEP_STARTED__"

    # --------------------------------------------------------
    # CHROME TAB COUNT
    # --------------------------------------------------------

    tab_count_patterns = [
        "kitne tabs khule hain",
        "kitne tab khule hain",
        "how many tabs",
        "how many tabs are open",
        "tabs kitne hain",
        "tabs count",
        "tab count",
        "chrome mein kitne tabs",
        "chrome me kitne tabs",
        "mere kitne tabs khule hain",
    ]

    if any(p in t for p in tab_count_patterns):

        count = get_chrome_tab_count()

        if count is None:
            return (
                "Umar, Chrome ke exact tabs count ke liye "
                "Chrome remote debugging enable karna hoga."
            )

        if count == 1:
            return "Umar, Chrome mein 1 tab open hai."

        return f"Umar, Chrome mein {count} tabs open hain."

    # --------------------------------------------------------
    # CLOSE ALL TABS / CHROME
    # --------------------------------------------------------

    close_all_patterns = [
        "close all tabs",
        "close all tab",
        "close every tab",
        "all tabs close",
        "all tabs band",
        "saare tabs close",
        "saare tabs band",
        "sare tabs close",
        "sare tabs band",
        "sare tab band",
        "saare tab band",
        "sab tabs band",
        "sab tab band",
        "sab tabs close",
        "tamam tabs band",
        "browser ke saare tabs",
        "chrome close karo",
        "chrome band karo",
        "chrome band kar do",
        "chrome close kar do",
        "youtube aur chrome band",
    ]

    if any(p in t for p in close_all_patterns):

        success = close_all_chrome_tabs()

        if success:
            return (
                "Ji Umar, Chrome ke saare tabs aur "
                "windows band kar diye."
            )

        return "Umar, Chrome close nahi ho saka."

    # --------------------------------------------------------
    # CLOSE YOUTUBE
    # --------------------------------------------------------

    youtube_close_patterns = [
        "close youtube",
        "youtube close",
        "youtube band",
        "youtube band karo",
        "youtube band kar do",
        "youtube close karo",
        "youtube close kar do",
        "please youtube close karo"
    ]

    if any(p in t for p in youtube_close_patterns):

        success = _close_youtube_tab()

        if success:
            return "Ji Umar, YouTube band kar diya."

        return "Umar, YouTube tab close nahi ho saka."

    # --------------------------------------------------------
    # SHUTDOWN LAPTOP
    # --------------------------------------------------------

    shutdown_patterns = [
        "shutdown laptop",
        "shut down laptop",
        "laptop shutdown",
        "close laptop",
        "laptop close",
        "laptop band kar do",
        "laptop band karo",
        "computer band kar do",
        "computer band karo",
        "pc band kar do",
        "pc band karo",
        "windows band kar do",
        "windows band karo",
        "system band kar do",
        "system band karo",
        "close my laptop",
        "turn off laptop",
        "turn off my laptop",
    ]

    if any(p in t for p in shutdown_patterns):

        speak("Theek hai Umar, laptop shutdown ho raha hai.")
        time.sleep(0.5)
        shutdown_windows()
        return "__JARVIS_SHUTDOWN_STARTED__"

    # --------------------------------------------------------
    # CLOSE CURRENT WINDOW
    # --------------------------------------------------------

    close_window_patterns = [
        "close window",
        "window close",
        "window band",
        "window band kar do",
        "window band karo",
        "close this window",
        "current window close",
        "active window close"
    ]

    if any(p in t for p in close_window_patterns):

        success = close_active_window()

        if success:
            return "Ji Umar, current window close kar di."

        return "Current window close nahi ho saki."

    # --------------------------------------------------------
    # PERSONAL PROFILE
    # --------------------------------------------------------

    profile_answer = get_profile_answer(t)

    if profile_answer:
        return profile_answer

    # --------------------------------------------------------
    # NEW: CAMERA FAST-PATH (additive; does not affect anything above)
    # --------------------------------------------------------

    if "camera" in t:

        if any(p in t for p in [
            "picture", "photo", "tasveer", "capture",
            "picture lo", "photo lo", "click karo",
        ]):
            path = _take_picture()
            if path:
                return f"Umar, picture captured and saved. {path}"
            return "Umar, camera se picture nahi le saka."

        if any(p in t for p in [
            "close", "band", "band karo", "band kar do",
            "off karo", "band kar",
        ]):
            if _close_camera():
                return "Ji Umar, camera band kar diya."
            return "Umar, camera band nahi ho saka."

        if any(p in t for p in [
            "kholo", "khol", "open", "chalao", "on karo",
            "start", "khol do",
        ]):
            ok, err = _open_camera()
            if ok:
                return "Ji Umar, camera open kar raha hoon."
            if err == "opencv":
                return (
                    "Umar, camera ke liye opencv-python install karein: "
                    "pip install opencv-python"
                )
            if err == "no_camera":
                return "Umar, camera available nahi hai."
            return "Umar, camera open nahi ho saka."

    # --------------------------------------------------------
    # END OF FAST LOCAL COMMAND
    # --------------------------------------------------------

    return None


# =========================================================
# NEW: INTENT HANDLERS  (additive; called from _command_response)
# =========================================================

def _handle_open_close_app(text, low):
    """
    Handle open/close X for registry apps (Chrome, Word, Excel,
    VS Code, Notepad, Calculator, File Explorer, Spotify, VLC, ...)
    and for known websites.
    Returns a response string or None.
    """

    # ---- OPEN ----
    open_triggers = [
        "open ", "kholo ", "khol ", "khol do ", "launch ",
        "start ", "chalao ", "run ", "on karo ",
    ]
    for trig in open_triggers:
        idx = low.find(trig)
        if idx == -1:
            continue
        after = low[idx + len(trig):].strip()
        after = re.sub(r"^(?:the\s+|microsoft\s+)", "", after).strip()
        after = re.sub(r"\s+(?:karo|kar do|please)$", "", after).strip()
        if not after:
            continue
        after = re.sub(r"\s+ko$", "", after).strip()

        # Try longest registry key first so "visual studio code"
        # wins over "visual studio".
        for key in sorted(APP_REGISTRY.keys(), key=len, reverse=True):
            if key == after or after.startswith(key + " ") or \
               after == key.replace(" ", ""):
                ok, process = _open_app(key)
                pretty = key.title()
                if ok:
                    return f"Ji Umar, {pretty} khol raha hoon."
                return f"Umar, {key} is laptop par install nahi hai."

        # Fallback: known website
        if after in _KNOWN_WEBSITES:
            if _open_url(_KNOWN_WEBSITES[after]):
                return f"Ji Umar, {after.title()} khol raha hoon."

        # Fallback: bare domain
        if re.match(r"^[a-z0-9-]+(\.[a-z]{2,})+$", after):
            if _open_url("https://" + after):
                return f"Ji Umar, {after} khol raha hoon."

    # ---- CLOSE ----
    close_triggers = [
        "close ", "band karo ", "band kar do ",
        "band karo", "band kar do", "band ",
    ]
    for trig in close_triggers:
        idx = low.find(trig)
        if idx == -1:
            continue
        after = low[idx + len(trig):].strip()
        after = re.sub(r"^(?:the\s+|microsoft\s+)", "", after).strip()
        after = re.sub(r"\s+(?:karo|kar do|please)$", "", after).strip()
        after = re.sub(r"\s+ko$", "", after).strip()
        if not after:
            continue

        for key in sorted(APP_REGISTRY.keys(), key=len, reverse=True):
            if key == after or after.startswith(key + " ") or \
               after == key.replace(" ", ""):
                ok, process = _close_app(key)
                pretty = key.title()
                if ok:
                    return f"Ji Umar, {pretty} band kar diya."
                return (
                    f"Umar, {key} pehle se band hai "
                    f"ya close nahi ho saka."
                )

    return None


def _handle_youtube(low, text):
    if "youtube" not in low:
        return None

    # close youtube
    if any(p in low for p in [
        "close", "band", "band karo", "band kar do"
    ]):
        if _close_active_window():
            return "Ji Umar, YouTube band kar diya."
        return "Umar, YouTube tab close nahi ho saka."

    # play / search
    query = _extract_youtube_query(text)
    has_play = _contains_any(low, [
        "play", "chalao", "lagao", "music", "gaana", "gana",
        "song", "songs", "search",
    ])

    if has_play:
        ok = _play_youtube_music(query)
        if ok:
            return f"Ji Umar, YouTube par {query} play kar raha hoon."
        return "Umar, YouTube open nahi ho saka."

    # bare "youtube kholo" / "open youtube"
    target = query if (query and query != "peaceful music") else None
    ok = _open_youtube(target)
    if ok:
        if target:
            return f"Ji Umar, YouTube par {target} search kar raha hoon."
        return "Ji Umar, YouTube khol raha hoon."
    return "Umar, YouTube open nahi ho saka."


def _handle_typing(low, text):
    """
    Handle:
      - "type <message>"
      - "type this message <message>"
      - "likho <message>"
      - "likh do <message>"
    """

    prefix_candidates = [
        "type this message",
        "type this",
        "type ",
        "likho ",
        "likh do ",
    ]

    for prefix in prefix_candidates:

        idx = low.find(prefix.strip())
        if idx == -1:
            continue

        raw_idx = text.lower().find(prefix.strip())
        if raw_idx == -1:
            continue

        after = text[raw_idx + len(prefix.strip()):].strip()
        after = re.sub(r"^[:\-,;]+", "", after).strip()

        if after:
            if _type_text(after):
                return f"Ji Umar, likh diya: {after}"
            return "Umar, typing nahi ho saki."

    return None


def _handle_file_open(low, text):
    """
    Handle:
      - open downloads / desktop / documents / pictures / videos / music
      - open the folder named X
      - open the file named X.ext
      - open this folder
    """

    # 1. Folder aliases
    for alias, path in FOLDER_ALIASES.items():
        if (alias in low
                and any(t in low for t in ["open", "kholo", "khol"])):
            if _open_folder(path):
                return f"Ji Umar, {alias} khol diya."
            return f"Umar, {alias} folder nahi mila."

    # 2. "folder named X"
    m = re.search(
        r"(?:folder|directory)\s+(?:named\s+)?([a-z0-9 _.\-]{2,60})",
        low
    )
    if m and any(t in low for t in ["open", "kholo", "khol"]):
        name = m.group(1).strip()
        name = re.sub(
            r"\s+(?:open|khol|kholo|please|kar do|karo)$",
            "",
            name
        ).strip()
        path = _find_item_by_name(name, want_dir=True)
        if path and _open_folder(path):
            return f"Ji Umar, folder {name} khol diya."
        path = _find_item_by_name(name, want_dir=False)
        if path and _open_item(path):
            return f"Ji Umar, file {name} khol di."
        return f"Umar, mujhe {name} naam ka folder ya file nahi mila."

    # 3. "file named X.ext"
    m = re.search(
        r"file\s+(?:named\s+)?([a-z0-9 _.\-]+\.[a-z0-9]{1,6})",
        low
    )
    if m and any(t in low for t in ["open", "kholo", "khol"]):
        name = m.group(1).strip()
        path = _find_item_by_name(name, want_dir=False)
        if path and _open_item(path):
            return f"Ji Umar, file {name} khol di."
        return f"Umar, mujhe {name} naam ki file nahi mili."

    # 4. "this folder" / "ye folder"
    if (
        "this folder" in low
        or "ye folder" in low
        or "is folder" in low
        or "current folder" in low
    ):
        try:
            cwd = os.getcwd()
            if _open_folder(cwd):
                return f"Ji Umar, current folder khol diya: {cwd}"
        except Exception:
            pass
        return "Umar, current folder open nahi ho saka."

    return None


def _handle_camera(low, text):
    if "camera" not in low:
        return None

    if any(p in low for p in [
        "take picture", "take photo", "picture lo", "photo lo",
        "tasveer", "capture", "click karo", "picture click",
    ]):
        path = _take_picture()
        if path:
            return f"Umar, picture captured and saved. {path}"
        return "Umar, camera se picture nahi le saka."

    if any(p in low for p in [
        "close camera", "camera band", "camera close",
        "camera band karo", "camera band kar do",
        "camera off karo", "camera off",
    ]):
        if _close_camera():
            return "Ji Umar, camera band kar diya."
        return "Umar, camera band nahi ho saka."

    if any(p in low for p in [
        "camera kholo", "camera khol", "camera open",
        "camera on", "camera chalao", "camera start",
        "open camera", "camera khol do",
    ]):
        ok, err = _open_camera()
        if ok:
            return "Ji Umar, camera open kar raha hoon."
        if err == "opencv":
            return (
                "Umar, camera ke liye opencv-python install karein: "
                "pip install opencv-python"
            )
        if err == "no_camera":
            return "Umar, camera available nahi hai."
        return "Umar, camera open nahi ho saka."

    return None


def _handle_browser_controls(low):
    if any(p in low for p in [
        "scroll down", "neeche scroll", "scroll neeche",
        "youtube neeche scroll", "youtube scroll down",
    ]):
        if _browser_scroll("down"):
            return "Ji Umar, scroll down kar diya."
        return "Umar, scroll nahi ho saka."

    if any(p in low for p in [
        "scroll up", "upar scroll", "scroll upar",
        "youtube upar scroll", "youtube scroll up",
    ]):
        if _browser_scroll("up"):
            return "Ji Umar, scroll up kar diya."
        return "Umar, scroll nahi ho saka."

    if any(p in low for p in [
        "go back", "back jao", "peeche jao", "previous page",
    ]):
        if _browser_back():
            return "Ji Umar, peeche chala gaya."
        return "Umar, back nahi ho saka."

    if any(p in low for p in [
        "go forward", "aage jao", "next page", "forward jao",
    ]):
        if _browser_forward():
            return "Ji Umar, aage chala gaya."
        return "Umar, forward nahi ho saka."

    if any(p in low for p in ["new tab", "naya tab"]):
        if _browser_new_tab():
            return "Ji Umar, naya tab khol diya."
        return "Umar, naya tab open nahi ho saka."

    if any(p in low for p in [
        "refresh page", "page refresh", "refresh karo",
        "reload page",
    ]):
        if _browser_refresh():
            return "Ji Umar, page refresh kar diya."
        return "Umar, refresh nahi ho saka."

    return None


def _handle_google_search(low, text):
    if any(p in low for p in [
        "google images", "google image", "images search",
        "image search", "tasveer search", "google se image",
    ]):
        query = _extract_search_query(
            text,
            [
                "google images", "google image",
                "image search", "images search",
            ]
        )
        if _open_google(query, images=True):
            return (
                f"Ji Umar, Google Images par "
                f"{query or 'images'} search kar raha hoon."
            )
        return "Umar, Google Images open nahi ho saka."

    if any(p in low for p in [
        "google search", "google par", "google pe", "search google",
    ]):
        query = _extract_search_query(
            text,
            [
                "google search", "google par", "google pe",
                "search google",
            ]
        )
        if _open_google(query):
            return (
                f"Ji Umar, Google par "
                f"{query or 'search'} search kar raha hoon."
            )
        return "Umar, Google open nahi ho saka."

    return None


def _handle_open_known_website(low):
    m = re.search(
        r"\b([a-z][a-z ]{1,25}?)\s+(?:kholo|khol do|open karo|open)\b",
        low
    )
    if m:
        site = m.group(1).strip()
        if site in _KNOWN_WEBSITES:
            if _open_url(_KNOWN_WEBSITES[site]):
                return f"Ji Umar, {site.title()} khol raha hoon."
    return None


def _handle_music_simple(low):
    if any(p in low for p in [
        "pause music", "music pause", "song pause",
        "gaana pause", "pause song",
    ]):
        if _pause_youtube_music():
            return "Ji Umar, music pause kar diya."
        return "Umar, music pause nahi ho saka."

    if any(p in low for p in [
        "resume music", "music resume", "song resume",
        "wapas chalao", "music chalao", "song chalao",
    ]):
        if _resume_youtube_music():
            return "Ji Umar, music resume kar diya."
        return "Umar, music resume nahi ho saka."

    if any(p in low for p in [
        "stop music", "music stop", "music band",
        "song band", "music rok",
    ]):
        if _stop_youtube_music():
            return "Ji Umar, music band kar diya."
        return "Umar, music band nahi ho saka."

    return None


def _handle_simple_confirm(low):
    global CONFIRMATION_REQUIRED
    if not CONFIRMATION_REQUIRED:
        return None

    yes_words = [
        "yes", "haan", "han", "ji", "confirm",
        "kar do", "okay", "ok", "theek hai",
    ]
    no_words = [
        "no", "nahi", "nahin", "cancel", "mat karo", "ruk jao",
    ]

    if _contains_any(low, yes_words):
        action = CONFIRMATION_REQUIRED
        CONFIRMATION_REQUIRED = None
        if action == "shutdown":
            subprocess.Popen(
                ["shutdown", "/s", "/t", "5"],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return "Ji Umar, laptop shutdown ho raha hai."
        if action == "restart":
            subprocess.Popen(
                ["shutdown", "/r", "/t", "5"],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return "Ji Umar, laptop restart ho raha hai."

    if _contains_any(low, no_words):
        CONFIRMATION_REQUIRED = None
        return "Theek hai Umar, cancel kar diya."

    return None


def _handle_chatgpt_type(low, text):
    if "chatgpt" not in low:
        return None

    if not any(t in low for t in [
        "likho", "type karo", "type kar do",
        "message likho", "pe likho", "mein likho", "par likho",
    ]):
        return None

    for trig in [
        "message likho", "likho",
        "type karo", "type kar do",
    ]:
        idx = low.find(trig)
        if idx == -1:
            continue

        raw_idx = text.lower().find(trig)
        after = text[raw_idx + len(trig):].strip()
        after = re.sub(r"^[:\-,;]+", "", after).strip()
        after = re.sub(r"^(?:that|kay|ke)\s+", "", after, flags=re.I).strip()

        if after:
            if not _open_chatgpt():
                return "Umar, ChatGPT open nahi ho saka."
            if not PYAUTOGUI_AVAILABLE:
                return (
                    "Umar, ChatGPT open hai lekin "
                    "pyautogui available nahi."
                )
            time.sleep(4.5)
            try:
                pyautogui.press("tab", presses=3, interval=0.15)
                pyautogui.typewrite(after, interval=0.01)
                return f"Ji Umar, ChatGPT mein likh diya: {after}"
            except Exception as e:
                print("ChatGPT typing error:", e)
                return "Umar, ChatGPT mein message type nahi ho saka."

    # Just "ChatGPT kholo"
    if _open_chatgpt():
        return "Ji Umar, ChatGPT khol raha hoon."
    return "Umar, ChatGPT open nahi ho saka."


# =========================================================
# COMMAND RESPONSE
# =========================================================
# All original branches preserved. New handlers are called
# BEFORE the original branches. If any new handler returns
# None, execution falls through to the original behaviour.

def _command_response(text):

    global CONFIRMATION_REQUIRED

    text = normalize_urdu_command(text)
    low = _norm_command(text)

    ui_state("ACTION", f"COMMAND // {low[:48]}")

    # ---------------- original "aur/and" splitting ----------------
    if (
        (" aur " in low or " and " in low)
        and not CONFIRMATION_REQUIRED
    ):
        separator = " aur " if " aur " in low else " and "
        parts = [
            part.strip()
            for part in low.split(separator)
            if part.strip()
        ]

        if len(parts) == 2 and all(
            _contains_any(
                part,
                [
                    "open", "khol", "kholo", "close",
                    "band", "play", "chalao", "lagao",
                ]
            )
            for part in parts
        ):
            responses = []
            for part in parts:
                result = _command_response(part)
                if result:
                    responses.append(result)
            if responses:
                return " ".join(responses)

    # ---------------- original pending confirmation ----------------
    confirm_resp = _handle_simple_confirm(low)
    if confirm_resp:
        return confirm_resp

    # =====================================================
    # NEW HANDLERS (additive) — they run before original
    # branches. None of them replace anything.
    # =====================================================

    r = _handle_chatgpt_type(low, text)
    if r:
        return r

    r = _handle_music_simple(low)
    if r:
        return r

    r = _handle_camera(low, text)
    if r:
        return r

    r = _handle_typing(low, text)
    if r:
        return r

    r = _handle_browser_controls(low)
    if r:
        return r

    r = _handle_google_search(low, text)
    if r:
        return r

    r = _handle_youtube(low, text)
    if r:
        return r

    r = _handle_open_close_app(text, low)
    if r:
        return r

    r = _handle_open_known_website(low)
    if r:
        return r

    r = _handle_file_open(low, text)
    if r:
        return r

    # =====================================================
    # ORIGINAL BRANCHES (unchanged)
    # =====================================================

    if CONFIRMATION_REQUIRED:

        yes_words = [
            "yes", "haan", "han", "ji", "confirm",
            "kar do", "okay", "ok", "theek hai",
        ]

        no_words = [
            "no", "nahi", "nahin", "cancel", "mat karo", "ruk jao",
        ]

        if _contains_any(low, yes_words):

            action = CONFIRMATION_REQUIRED
            CONFIRMATION_REQUIRED = None

            if action == "shutdown":
                subprocess.Popen(
                    ["shutdown", "/s", "/t", "5"],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                return "Ji Umar, laptop shutdown ho raha hai."

            if action == "restart":
                subprocess.Popen(
                    ["shutdown", "/r", "/t", "5"],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                return "Ji Umar, laptop restart ho raha hai."

        if _contains_any(low, no_words):
            CONFIRMATION_REQUIRED = None
            return "Theek hai Umar, cancel kar diya."

    if _contains_any(
        low,
        ["restart", "reboot", "laptop restart", "computer restart"]
    ):
        CONFIRMATION_REQUIRED = "restart"
        return "Umar, kya main laptop restart kar doon?"

    if _contains_any(
        low,
        [
            "chrome kholo", "chrome khol", "open chrome",
            "google chrome kholo", "browser kholo", "browser open",
        ]
    ):
        ok = _open_chrome()
        return (
            "Ji Umar, Chrome khol raha hoon."
            if ok else
            "Umar, Chrome open nahi ho saka."
        )

    if _contains_any(
        low,
        [
            "chrome band", "close chrome", "chrome close",
            "browser band", "browser close",
        ]
    ):
        ok = _close_process("chrome.exe")
        return (
            "Ji Umar, Chrome band kar diya."
            if ok else
            "Umar, Chrome pehle se band hai ya close nahi ho saka."
        )

    if "youtube" in low:

        if _contains_any(low, ["close", "band"]):
            ok = _close_youtube_tab()
            return (
                "Ji Umar, YouTube band kar diya."
                if ok else
                "Umar, YouTube tab close nahi ho saka."
            )

        query = _extract_youtube_query(text)

        has_play_intent = _contains_any(
            low,
            ["play", "chalao", "lagao", "music", "gaana",
             "gana", "search", "pe ", "par "]
        )

        if has_play_intent:
            ok = _play_youtube_music(query)
            return (
                f"Ji Umar, YouTube par "
                f"{query} search kar raha hoon."
                if ok else
                "Umar, YouTube open nahi ho saka."
            )

        if query and not _contains_any(low, ["kholo", "open"]):
            ok = _open_youtube(query)
            return (
                f"Ji Umar, YouTube par "
                f"{query} search kar raha hoon."
                if ok else
                "Umar, YouTube open nahi ho saka."
            )

        ok = _open_youtube()
        return (
            "Ji Umar, YouTube khol raha hoon."
            if ok else
            "Umar, YouTube open nahi ho saka."
        )

    if _contains_any(
        low,
        [
            "google images", "google image",
            "images search", "image search", "tasveer search",
        ]
    ):
        query = _extract_search_query(
            text,
            [
                "google images", "google image",
                "image search", "images search",
            ]
        )
        ok = _open_google(query, images=True)
        return (
            f"Ji Umar, Google Images par "
            f"{query or 'images'} search kar raha hoon."
            if ok else
            "Umar, Google Images open nahi ho saka."
        )

    if _contains_any(
        low,
        ["google search", "google par", "google pe", "search google"]
    ):
        query = _extract_search_query(
            text,
            ["google search", "google par", "google pe", "search google"]
        )
        ok = _open_google(query)
        return (
            f"Ji Umar, Google par "
            f"{query or 'search'} search kar raha hoon."
            if ok else
            "Umar, Google open nahi ho saka."
        )

    if _contains_any(
        low,
        ["whatsapp kholo", "whatsapp open",
         "whatsapp on", "open whatsapp"]
    ):
        ok = _open_whatsapp()
        return (
            "Ji Umar, WhatsApp Web khol raha hoon."
            if ok else
            "Umar, WhatsApp open nahi ho saka."
        )

    if _contains_any(
        low,
        ["chatgpt kholo", "chatgpt open", "chatgpt on",
         "open chatgpt", "chatgpt bolo"]
    ):
        ok = _open_chatgpt()
        return (
            "Ji Umar, ChatGPT khol raha hoon."
            if ok else
            "Umar, ChatGPT open nahi ho saka."
        )

    if (
        _contains_any(low, ["visual studio code", "vs code", "vscode"])
        and _contains_any(
            low,
            ["folder", "downloads", "desktop", "documents"]
        )
    ):
        folder = _find_folder_from_command(text)
        code_path = (
            _find_existing(VS_CODE_CANDIDATES) or "code"
        )
        if folder:
            ok = _launch_executable(code_path, [folder])
            if ok:
                return (
                    f"Ji Umar, Visual Studio Code mein "
                    f"{os.path.basename(folder) or folder} "
                    f"open kar diya."
                )

    if _contains_any(low, ["visual studio code", "vs code", "vscode"]):

        if _contains_any(low, ["band", "close"]):
            ok = _close_process("Code.exe")
            return (
                "Ji Umar, Visual Studio Code band kar diya."
                if ok else
                "Umar, VS Code pehle se band hai ya close nahi ho saka."
            )

        code_path = _find_existing(VS_CODE_CANDIDATES)
        ok = _launch_executable(code_path or "code")
        return (
            "Ji Umar, Visual Studio Code khol raha hoon."
            if ok else
            "Umar, Visual Studio Code nahi mila."
        )

    if "visual studio" in low:

        if _contains_any(low, ["band", "close"]):
            ok = _close_process("devenv.exe")
            return (
                "Ji Umar, Visual Studio band kar diya."
                if ok else
                "Umar, Visual Studio pehle se band hai ya close nahi ho saka."
            )

        vs_path = _find_existing(VISUAL_STUDIO_CANDIDATES)
        ok = _launch_executable(vs_path) if vs_path else False
        return (
            "Ji Umar, Visual Studio khol raha hoon."
            if ok else
            "Umar, Visual Studio nahi mila."
        )

    if _contains_any(
        low,
        ["folder kholo", "folder khol", "open folder",
         "directory kholo", "directory khol"]
    ):
        folder = _find_folder_from_command(text)
        if folder and _open_folder(folder):
            return (
                f"Ji Umar, "
                f"{os.path.basename(folder) or folder} "
                f"folder khol diya."
            )
        return (
            "Umar, mujhe woh folder nahi mila. "
            "Folder ka naam ya path bata do."
        )

    if _contains_any(
        low,
        ["downloads kholo", "download kholo", "downloads open",
         "desktop kholo", "documents kholo"]
    ):
        folder = _find_folder_from_command(text)
        if folder and _open_folder(folder):
            return (
                f"Ji Umar, "
                f"{os.path.basename(folder) or folder} khol diya."
            )

    if _contains_any(low, ["notepad kholo", "notepad open"]):
        return (
            "Ji Umar, Notepad khol raha hoon."
            if _launch_executable("notepad.exe") else
            "Umar, Notepad open nahi ho saka."
        )

    if _contains_any(
        low,
        ["calculator kholo", "calculator open", "calc kholo"]
    ):
        return (
            "Ji Umar, Calculator khol raha hoon."
            if _launch_executable("calc.exe") else
            "Umar, Calculator open nahi ho saka."
        )

    if _contains_any(
        low,
        ["file explorer kholo", "explorer kholo"]
    ):
        return (
            "Ji Umar, File Explorer khol raha hoon."
            if _launch_executable("explorer.exe") else
            "Umar, File Explorer open nahi ho saka."
        )

    return None


# =========================================================
# EXECUTE LOCAL COMMAND  (logic preserved)
# =========================================================

def execute_local_command(text):

    fast_result = execute_fast_local_command(text)
    if fast_result is not None:
        return fast_result

    try:
        return _command_response(text)
    except Exception as e:
        print("Local command error:", e)
        return (
            "Umar, command perform karte waqt "
            "problem aa gayi."
        )


# =========================================================
# ASK JARVIS  (UNCHANGED — OpenRouter prompt preserved)
# =========================================================

def ask_jarvis(user_text):

    ui_state("THINKING", "AI CORE // UNDERSTANDING COMMAND")

    user_text = prepare_user_text(user_text)

    global USER_NAME

    name_patterns = [
        r"\bmera naam ([A-Za-z][A-Za-z ]{1,30}) hai\b",
        r"\bmy name is ([A-Za-z][A-Za-z ]{1,30})\b",
        r"\bmain ([A-Za-z][A-Za-z ]{1,30}) hoon\b",
    ]

    for pattern in name_patterns:
        match = re.search(pattern, user_text, flags=re.IGNORECASE)
        if match:
            possible_name = match.group(1).strip().rstrip(".,!?")
            if possible_name:
                USER_NAME = possible_name
            break

    if not user_text:
        return "Mujhe samajh nahi aaya. Dobara bolo."

    low = user_text.lower()

    # ChatGPT open + type
    if (
        "chatgpt" in low
        and any(
            t in low
            for t in [
                "likho", "type karo", "type kar do",
                "message likho", "pe likho",
                "mein likho", "par likho",
            ]
        )
    ):
        message = _extract_chatgpt_message(user_text)
        if message:
            ok = _open_chatgpt_and_type(message)
            if ok:
                return f"Ji Umar, ChatGPT mein likh diya: {message}"
            return "Umar, ChatGPT mein message type nahi ho saka."

        if _open_chatgpt():
            return "Ji Umar, ChatGPT khol raha hoon."
        return "Umar, ChatGPT open nahi ho saka."

    # Smart music
    handled, music_response = _smart_music_command(user_text)
    if handled:
        print("Smart music handled request.")
        ui_state("ACTION", "MUSIC ACTION COMPLETE")
        return music_response

    # Local commands
    local_response = execute_local_command(user_text)
    if local_response is not None:
        print("Local command executed/handled.")
        ui_state("ACTION", "LOCAL COMPUTER ACTION COMPLETE")
        return local_response

    # Known websites
    m = re.search(
        r"\b([a-z][a-z ]{1,25}?)\s+(?:kholo|khol do|open karo|open)\b",
        low
    )
    if m:
        site = m.group(1).strip()
        if site in _KNOWN_WEBSITES:
            if _open_known_website(site):
                return f"Ji Umar, {site.title()} khol raha hoon."

    # Learning summary (extended to mention new skills)
    if any(
        p in low
        for p in [
            "tumne kya kya seekha",
            "tumhe kya kya sikhaya",
            "what have you learned",
            "kya kya seekha hai",
            "kya kya sikhaya hai",
            "kya kar sakte ho",
            "what can you do",
        ]
    ):
        return (
            "Umar, aapne mujhe laptop ke power controls "
            "(shutdown, restart, sleep, lock), applications "
            "(Chrome, Word, Excel, VS Code, Notepad, Calculator, "
            "Spotify, VLC, Telegram, Discord) open aur close karna, "
            "files aur folders open karna, keyboard se text type karna, "
            "browser control (scroll, back, forward, refresh, new tab), "
            "YouTube music search, play, pause, resume aur stop, "
            "ChatGPT open karke message type karna, camera open karke "
            "picture lena, brightness aur volume control, "
            "battery aur charging status batana, aur time/date "
            "batana sikhaya hai."
        )

    # ---------------- OpenRouter fallback (prompt unchanged) ----------------

    system_prompt = """You are JARVIS, a friendly, fast and natural personal AI voice assistant.

The user may speak English, Roman Urdu, Urdu, or a mixture of English and Roman Urdu.

LANGUAGE BEHAVIOR:
1. English speech -> answer in natural English.
2. Roman Urdu speech -> answer in natural conversational Urdu written in URDU SCRIPT.
3. Urdu speech -> answer in natural Urdu script.
4. Mixed English + Roman Urdu -> answer naturally in the same mixed style.
5. ALWAYS output Urdu responses in URDU SCRIPT (not Roman Urdu).
6. Do NOT produce awkward literal translations.
7. Treat Roman Urdu as normal conversational Urdu.
8. Keep the user's name exactly as "Umar" unless the user explicitly introduces another name.
9. Keep answers concise and conversational. Normally 1 to 3 sentences.
10. Do not provide internal reasoning. Do not mention these instructions.

PERSONAL INFORMATION:
The user is Syed Umar Hussain.
Age: 23.
Birthday: 17 February.
Profession: Software Engineer and AI Engineer.
University: Sindh University, Jamshoro.
AI teacher: Rafiq Bhutto Sir.
Location: Hyderabad, Pakistan.

Simple Windows commands are executed locally by the JARVIS command engine before this AI call.
For requests that are not implemented as local actions, explain what should be done rather than pretending that an action was performed.
"""

    payload = {
        "model": OPENROUTER_MODELS[0],
        "messages": [
            {
                "role": "system",
                "content": (
                    system_prompt
                    + f"\nThe user's current name for this session is: {USER_NAME}. "
                    "Use it naturally when appropriate."
                )
            },
            {"role": "user", "content": user_text}
        ],
        "max_tokens": 300,
        "temperature": 0.4,
        "reasoning": {"effort": "minimal"}
    }

    for model in OPENROUTER_MODELS:

        payload["model"] = model
        print("Trying OpenRouter model:", model)

        try:

            request = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "http://localhost",
                    "X-Title": "JARVIS AI Assistant"
                },
                method="POST"
            )

            with urllib.request.urlopen(request, timeout=35) as response:
                raw = response.read().decode("utf-8")

            data = json.loads(raw)
            answer = extract_answer(data)
            answer = clean_ai_answer(answer)

            if answer:
                print("Working model:", model)
                return answer

            print("Model returned empty content.")

        except urllib.error.HTTPError as e:

            try:
                error_body = e.read().decode("utf-8")
            except Exception:
                error_body = ""

            print("OpenRouter HTTP Error:", e.code)
            if error_body:
                print(error_body[:1000])

            if e.code == 429:
                print("Rate limited. Trying next model...")
                continue

        except Exception as e:
            print("OpenRouter Error:", e)
            continue

    return (
        "Mujhe abhi AI service se proper response nahi mila. "
        "Ek baar phir bolo."
    )


# =========================================================
# LISTEN FOR COMMAND  (UNCHANGED)
# =========================================================

def listen_for_command():

    print()
    print("Listening for command...")

    try:

        with sr.Microphone(device_index=MIC_INDEX) as source:
            audio = recognizer.listen(
                source,
                timeout=8,
                phrase_time_limit=10
            )

        return recognize_bilingual(audio)

    except sr.WaitTimeoutError:
        print("Command listening timeout.")
        return ""

    except Exception as e:
        print("Command listening error:", e)
        return ""


# =========================================================
# DIRECT COMMAND DETECTION  (extended; original triggers preserved)
# =========================================================

def is_clear_direct_command(text):

    low = command_ready_text(text).lower()

    triggers = [

        # ---------------- original triggers ----------------
        "chrome kholo", "chrome khol", "open chrome",
        "close chrome", "chrome band",

        "youtube kholo", "youtube khol", "open youtube",
        "youtube par", "youtube pe", "youtube play",
        "youtube chalao", "youtube lagao", "close youtube",
        "youtube close", "youtube band",

        "play music", "music play", "music chalao",
        "music lagao", "play number one music",

        "song play", "song chalao", "song lagao",
        "music pause", "music resume", "music band",
        "music kat", "wapas chalao",

        "vs code kholo", "vs code khol", "open vs code",

        "visual studio kholo", "visual studio code kholo",
        "visual studio band",

        "downloads kholo", "desktop kholo", "documents kholo",
        "folder kholo",

        "notepad kholo", "calculator kholo", "file explorer kholo",

        "whatsapp kholo", "whatsapp open",

        "chatgpt kholo", "chatgpt open", "chatgpt bolo",
        "chatgpt pe likho", "chatgpt mein likho",

        "google par", "google pe", "google images",
        "image search",

        "brightness kam", "brightness zyada", "brightness barha",
        "brightness 20", "brightness 30", "brightness 40",
        "brightness 50", "brightness 60", "brightness 70",
        "brightness 80", "brightness 90", "brightness 100",

        "volume kam", "volume zyada", "volume barha",
        "volume 20", "volume 30", "volume 40",
        "volume 50", "volume 60", "volume 70",
        "volume 80", "volume 90", "volume 100",
        "mute karo", "unmute karo",

        "laptop lock", "lock karo",
        "laptop sleep", "sleep karo",

        "shutdown", "shut down", "restart",

        "time batao", "time kya hai", "time kholo",

        "date batao", "date kya hai",

        "battery kitni hai", "battery percentage",
        "charging batao", "charging dekh",

        "close all tabs", "saare tabs close", "saare tabs band",
        "sare tabs close", "sare tabs band",

        "tumne kya kya seekha", "tumhe kya kya sikhaya",

        "stop everything", "sab kuch band karo", "music rok do",

        # ---------------- NEW triggers (additive) ----------------
        "camera kholo", "camera open", "open camera",
        "camera band", "camera close", "camera off",
        "picture lo", "photo lo", "picture click",
        "camera on",

        "type ", "likho ",
        "scroll down", "scroll up",
        "youtube scroll", "youtube neeche", "youtube upar",
        "go back", "go forward",
        "refresh page", "new tab",

        "volume kitna", "mera volume", "volume low",
        "volume barha do", "awaz kam", "awaz tez",

        "word kholo", "excel kholo", "powerpoint kholo",
        "outlook kholo", "spotify kholo", "vlc kholo",
        "telegram kholo", "discord kholo", "steam kholo",
        "zoom kholo", "teams kholo",
        "word band", "excel band", "powerpoint band",
        "spotify band", "vlc band",
    ]

    return any(x in low for x in triggers)


# =========================================================
# BILINGUAL SPEECH RECOGNITION
# (logic unchanged; new keywords added to hint + scoring)
# =========================================================

def recognize_bilingual(audio):

    ui_state("LISTENING", "VOICE INPUT // ANALYZING SPEECH")
    print("Listening for English + Roman Urdu...")

    cleaned_audio = clean_audio_for_speech(audio)
    if not cleaned_audio:
        return ""

    candidates = []

    # ---------------- WHISPER ----------------
    try:

        segments, info = whisper_model.transcribe(
            cleaned_audio,
            language="en",
            beam_size=5,
            best_of=5,
            temperature=0.0,
            vad_filter=True,
            condition_on_previous_text=False,
            initial_prompt=(
                "Hey Jarvis. Jarvis. Umar. "
                "Chrome kholo. Chrome khol do. Chrome band karo. "
                "YouTube kholo. YouTube pe music chalao. "
                "YouTube close karo. "
                "Google pe search karo. "
                "Visual Studio Code kholo. "
                "Notepad kholo. Calculator kholo. "
                "WhatsApp kholo. ChatGPT kholo. "
                "Downloads kholo. Desktop kholo. "
                "Brightness kam karo. Brightness zyada karo. "
                "Volume kam karo. Volume zyada karo. Mute karo. "
                "Laptop shutdown kar do. "
                "Laptop restart kar do. Laptop lock karo. "
                "Laptop sleep kar do. "
                "Play music. Stop music. "
                "Music pause karo. Music resume karo. "
                "Song play karo. Bollywood song play karo. "
                "Arijit Singh ka song play karo. "
                "Atif Aslam ka song play karo. "
                "Tum Hi Ho play karo. "
                "Time batao. Date batao. "
                "Battery kitni hai. Charging batao. "
                "Mera naam kya hai. Meri age kya hai. "
                "Camera kholo. Meri picture click karo. "
                "Camera band kar do. "
                "Scroll down. Scroll up. Go back. Go forward. "
                "Word kholo. Excel kholo. Spotify kholo. VLC kholo. "
                "Type hello Umar."
            )
        )

        whisper_text = " ".join(
            segment.text.strip()
            for segment in segments
            if segment.text.strip()
        ).strip()

        if whisper_text:
            whisper_text = normalize_urdu_command(whisper_text)
            whisper_text = clean_transcript(whisper_text)
            print("Whisper English:", whisper_text)
            if whisper_text:
                candidates.append(("whisper", whisper_text))

    except Exception as e:
        print("Whisper English error:", e)

    # ---------------- GOOGLE ENGLISH ----------------
    try:
        google_text = recognize_english(audio)
        if google_text:
            google_text = normalize_urdu_command(google_text)
            google_text = clean_transcript(google_text)
            print("Google English:", google_text)
            if google_text:
                candidates.append(("google", google_text))
    except Exception as e:
        print("Google recognition error:", e)

    # ---------------- GOOGLE URDU ----------------
    try:
        google_urdu = recognize_urdu_google(audio)
        if google_urdu:
            google_urdu = normalize_urdu_command(google_urdu)
            google_urdu = clean_transcript(google_urdu)
            if google_urdu:
                candidates.append(("google_urdu", google_urdu))
    except Exception as e:
        print("Google Urdu error:", e)

    if not candidates:
        print("No usable speech result.")
        return ""

    command_words = [
        "jarvis", "chrome", "youtube", "google",
        "whatsapp", "chatgpt", "gmail", "facebook", "instagram",
        "visual studio", "vs code", "notepad", "calculator",
        "downloads", "desktop", "documents",
        "open", "close", "search", "play", "pause", "stop",
        "resume", "shutdown", "restart", "sleep", "lock",
        "kholo", "khol", "band", "karo", "kar do",
        "chalao", "lagao", "rok do",
        "mujhe", "mera", "meri", "hai", "kya",
        "time", "date", "battery", "charging",
        "brightness", "volume", "mute", "unmute",
        "naam", "age",
        "music", "song", "songs", "gaana", "gaane",
        "bollywood", "romantic", "party", "sad", "fast",
        "arijit", "atif", "singh", "aslam",
        # additive scoring keywords
        "camera", "picture", "photo", "type", "likho",
        "scroll", "back", "forward", "refresh",
        "word", "excel", "powerpoint", "outlook",
        "spotify", "vlc", "telegram", "discord",
    ]

    def candidate_score(text):

        low = text.lower()
        score = 0

        for word in command_words:
            if word in low:
                score += 3

        if "jarvis" in low:
            score += 10

        if not contains_urdu_script(text):
            score += 5

        word_count = len(low.split())
        if word_count >= 2:
            score += 2
        if word_count > 12:
            score -= 2

        if is_clear_direct_command(text):
            score += 12

        return score

    candidates.sort(
        key=lambda item: candidate_score(item[1]),
        reverse=True
    )

    print("Speech candidates:")
    for source, text in candidates:
        print(f"  {source}: {candidate_score(text):.1f} -> {text}")

    best_source, best_text = candidates[0]
    best_text = command_ready_text(best_text)

    print(f"FINAL SPEECH ({best_source}):", best_text)
    ui_detail(f"Detected: {best_text[:55]}")

    return best_text


# =========================================================
# ACTIVE CONVERSATION STATE  (UNCHANGED)
# =========================================================

ASSISTANT_STATE = "STANDBY"

_SLEEP_PHRASES = [
    "stop listening",
    "stop listen",
    "go to standby",
    "go standby",
    "sleep",
    "so jao",
    "so ja",
    "band karo sunna",
    "sunna band karo",
    "standby",
    "stand by",
    "bas",
    "bas karo",
    "chup",
]

MAX_EMPTY_RETRIES = 3

ACTIVE_IDLE_TIMEOUT_SECONDS = 90


def is_sleep_phrase(text):
    if not text:
        return False

    low = command_ready_text(text).lower().strip()
    low = remove_wake_word(low).strip()
    low = re.sub(r"[.!?,;:]+$", "", low).strip()

    if "laptop sleep" in low or "sleep karo" in low or "sula do" in low:
        return False

    for phrase in _SLEEP_PHRASES:
        if low == phrase:
            return True
        if re.search(
            r"(?:^|\s)" + re.escape(phrase) + r"(?:\s|$)",
            low
        ):
            return True

    return False


# =========================================================
# MAIN  (UNCHANGED)
# =========================================================

def main():

    global ASSISTANT_STATE

    print()
    print("=" * 60)
    print("JARVIS AI ASSISTANT // LOCAL AGENT + AI CORE")
    print("=" * 60)

    JARVIS_UI.start()
    time.sleep(0.35)

    ui_state("READY", "JARVIS ONLINE // VOICE LINK READY")

    _run_startup_mic_test()

    speak("Hello Umar. JARVIS is ready.")

    ui_state("STANDBY", "SAY HEY JARVIS")
    ASSISTANT_STATE = "STANDBY"

    while True:

        try:

            # =========================================
            # STANDBY MODE: wait for wake word
            # =========================================

            if ASSISTANT_STATE == "STANDBY":

                print()
                print("Standby... Say: Hey Jarvis")

                ui_state("STANDBY", "LISTENING FOR WAKE WORD")

                try:
                    with sr.Microphone(device_index=MIC_INDEX) as source:
                        audio = recognizer.listen(
                            source,
                            timeout=5,
                            phrase_time_limit=8
                        )
                except sr.WaitTimeoutError:
                    ui_state("STANDBY", "WAITING FOR WAKE WORD")
                    continue

                ui_state("THINKING", "CHECKING WAKE WORD")

                heard_text = recognize_bilingual(audio)

                if not heard_text:
                    print(
                        "No clear speech detected. "
                        "Returning to standby."
                    )
                    ui_state("STANDBY", "NO CLEAR SPEECH")
                    continue

                print("Heard:", heard_text)

                normalized_heard = command_ready_text(heard_text)
                print("Normalized heard:", normalized_heard)

                wake_detected = is_wake_word(normalized_heard)
                direct_command = is_clear_direct_command(normalized_heard)

                if not wake_detected and not direct_command:
                    ui_state("STANDBY", "WAKE WORD NOT DETECTED")
                    continue

                print("Wake word detected! Entering ACTIVE conversation.")

                ASSISTANT_STATE = "ACTIVE"

                command = remove_wake_word(normalized_heard)

                if not command and direct_command:
                    command = normalized_heard

                if not command:
                    speak("Yes Umar?")
                else:
                    print(
                        "User command (from wake utterance):",
                        command
                    )
                    ui_state("THINKING", "UNDERSTANDING COMMAND")
                    answer = ask_jarvis(command)

                    if answer == "__JARVIS_SHUTDOWN_STARTED__":
                        ui_state("ACTION", "SYSTEM SHUTDOWN STARTED")
                        ASSISTANT_STATE = "STANDBY"
                        continue
                    if answer == "__JARVIS_SLEEP_STARTED__":
                        ui_state("ACTION", "SYSTEM SLEEP STARTED")
                        ASSISTANT_STATE = "STANDBY"
                        continue

                    speak(answer)

            # =========================================
            # ACTIVE MODE: continuous conversation
            # =========================================

            if ASSISTANT_STATE == "ACTIVE":

                empty_retries = 0
                last_activity = time.time()

                ui_state(
                    "LISTENING",
                    "ACTIVE // LISTENING FOR COMMAND"
                )

                while ASSISTANT_STATE == "ACTIVE":

                    if (
                        ACTIVE_IDLE_TIMEOUT_SECONDS > 0
                        and time.time() - last_activity
                        > ACTIVE_IDLE_TIMEOUT_SECONDS
                    ):
                        print(
                            "Inactivity timeout reached. "
                            "Returning to standby."
                        )
                        speak(
                            "Theek hai Umar, main standby mein ja raha hoon."
                        )
                        ASSISTANT_STATE = "STANDBY"
                        ui_state(
                            "STANDBY",
                            "IDLE TIMEOUT // BACK TO STANDBY"
                        )
                        break

                    print()
                    print("Listening...")

                    ui_state(
                        "LISTENING",
                        "ACTIVE // LISTENING FOR COMMAND"
                    )

                    command = listen_for_command()

                    if not command:

                        empty_retries += 1

                        print(
                            f"No clear speech (attempt "
                            f"{empty_retries}/{MAX_EMPTY_RETRIES})."
                        )

                        if empty_retries >= MAX_EMPTY_RETRIES:
                            print(
                                "Too many empty attempts. "
                                "Returning to standby."
                            )
                            speak(
                                "Theek hai Umar, main standby mein ja raha hoon."
                            )
                            ASSISTANT_STATE = "STANDBY"
                            ui_state(
                                "STANDBY",
                                "TOO MANY EMPTY ATTEMPTS"
                            )
                            break

                        print("Listening again...")
                        continue

                    empty_retries = 0
                    last_activity = time.time()

                    print("User command:", command)

                    if is_sleep_phrase(command):
                        print(
                            "Sleep phrase detected. "
                            "Returning to standby."
                        )
                        speak(
                            "Theek hai Umar, main standby mein ja raha hoon."
                        )
                        ASSISTANT_STATE = "STANDBY"
                        ui_state(
                            "STANDBY",
                            "SLEEP PHRASE // BACK TO STANDBY"
                        )
                        break

                    ui_state(
                        "THINKING",
                        "UNDERSTANDING COMMAND"
                    )

                    answer = ask_jarvis(command)

                    if answer == "__JARVIS_SHUTDOWN_STARTED__":
                        ui_state("ACTION", "SYSTEM SHUTDOWN STARTED")
                        ASSISTANT_STATE = "STANDBY"
                        break
                    if answer == "__JARVIS_SLEEP_STARTED__":
                        ui_state("ACTION", "SYSTEM SLEEP STARTED")
                        ASSISTANT_STATE = "STANDBY"
                        break

                    speak(answer)

                    ui_state(
                        "LISTENING",
                        "ACTIVE // LISTENING FOR COMMAND"
                    )

        except KeyboardInterrupt:

            print("JARVIS stopped.")
            ui_state("STANDBY", "SYSTEM STOPPED")
            break

        except Exception as e:

            print("Main loop error:", e)
            ui_state("STANDBY", "RECOVERING FROM ERROR")
            time.sleep(0.5)


if __name__ == "__main__":
    main()

# =========================================================
# --- END PART 2 of 2 ---
# =========================================================