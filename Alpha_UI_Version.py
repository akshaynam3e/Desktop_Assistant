import customtkinter as ctk
import tkinter as tk
import math
import threading
import time
from datetime import datetime
import requests
import re
import os
import random
import sys
import platform
import pyautogui
import pywhatkit as kit
import json
import calendar
import urllib.parse
import pyttsx3
import webbrowser
from dotenv import load_dotenv

# ================== LOAD SECRETS ==================
load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
MODEL = "deepseek/deepseek-v4-flash-0731"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MEMORY_FILE = "memory.json"

# ================== TTS ==================
engine = pyttsx3.init()
engine.setProperty('rate', 175)
engine.setProperty('volume', 1.0)
for voice in engine.getProperty('voices'):
    if any(x in voice.name.lower() for x in ["female", "zira", "samantha"]):
        engine.setProperty('voice', voice.id)
        break

def speak(text):
    def _speak():
        try:
            engine.say(text)
            engine.runAndWait()
        except:
            pass
    threading.Thread(target=_speak, daemon=True).start()

# ================== MEMORY ==================
def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=4)

def remember(key, value):
    memory = load_memory()
    memory[key] = value
    save_memory(memory)

def recall(key):
    return load_memory().get(key)

def forget(key):
    memory = load_memory()
    if key in memory:
        del memory[key]
        save_memory(memory)

# ================== AI ==================
def get_ai_response(prompt):
    if not API_KEY:
        return "API key missing. Please check your .env file."
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "Alpha-GUI"
    }
    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful, slightly flirty and playful AI assistant named Alpha. Never use emojis. Keep language clean and natural."},
            {"role": "user", "content": prompt}
        ]
    }
    try:
        r = requests.post(API_URL, headers=headers, json=data, timeout=30)
        r.raise_for_status()
        reply = r.json()["choices"][0]["message"]["content"]
        reply = re.sub(r'[^\w\s,.?!\'\"\-]', '', reply)
        return reply.strip()
    except Exception as e:
        return f"Sorry, something went wrong: {e}"

# ================== MAIN APP ==================
class AlphaApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ALPHA")
        self.geometry("1280x720")
        self.minsize(1000, 600)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # Stopwatch variables
        self.stopwatch_running = False
        self.stopwatch_start_time = None

        # ========== MAIN HORIZONTAL PANED WINDOW ==========
        self.main_paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashwidth=8, sashrelief="flat", bg="#1a1a25", bd=0)
        self.main_paned.pack(fill="both", expand=True)

        # ========== LEFT SIDE - ANIMATION ==========
        self.left_frame = ctk.CTkFrame(self.main_paned, corner_radius=0, fg_color="#05050a")
        self.main_paned.add(self.left_frame, width=520, minsize=300)

        self.canvas = tk.Canvas(self.left_frame, bg="#05050a", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.angle = 0
        self.pulse = 0
        self.particles = []
        self.init_particles()
        self.animate()

        self.title_label = ctk.CTkLabel(self.left_frame, text="ALPHA", font=ctk.CTkFont(family="Segoe UI", size=32, weight="bold"), text_color="#00f0ff")
        self.title_label.place(relx=0.5, rely=0.06, anchor="center")

        self.status_label = ctk.CTkLabel(self.left_frame, text="SYSTEMS ONLINE", font=ctk.CTkFont(size=12), text_color="#00ff9f")
        self.status_label.place(relx=0.5, rely=0.94, anchor="center")

        # ========== RIGHT SIDE - VERTICAL PANED ==========
        self.right_paned = tk.PanedWindow(self.main_paned, orient=tk.VERTICAL, sashwidth=8, sashrelief="flat", bg="#1a1a25", bd=0)
        self.main_paned.add(self.right_paned, width=760, minsize=400)

        # ---- TOP: Command Buttons ----
        self.btn_frame = ctk.CTkFrame(self.right_paned, fg_color="#0f0f18", corner_radius=0)
        self.right_paned.add(self.btn_frame, height=150, minsize=90)

        buttons = [
            ("Time", self.cmd_time),
            ("Date", self.cmd_date),
            ("Weather", self.cmd_weather),
            ("Music", self.cmd_music),
            ("Screenshot", self.cmd_screenshot),
            ("Message", self.cmd_message),
            ("Map", self.cmd_map),
            ("Help", self.cmd_help),
            ("Timer", self.cmd_timer),
            ("Alarm", self.cmd_alarm),
            ("Website", self.cmd_website),
            ("Calendar", self.cmd_calendar),
        ]

        for i, (text, cmd) in enumerate(buttons):
            btn = ctk.CTkButton(
                self.btn_frame, text=text, command=cmd,
                width=100, height=34, corner_radius=8,
                fg_color="#1a1a28", hover_color="#00b4d8",
                font=ctk.CTkFont(size=12, weight="bold")
            )
            btn.grid(row=i // 4, column=i % 4, padx=8, pady=8, sticky="nsew")

        for i in range(4):
            self.btn_frame.grid_columnconfigure(i, weight=1)

        # ---- BOTTOM: Chat Area ----
        self.chat_frame = ctk.CTkFrame(self.right_paned, fg_color="#0f0f18", corner_radius=0)
        self.right_paned.add(self.chat_frame, minsize=200)

        self.chat_box = ctk.CTkTextbox(
            self.chat_frame, font=ctk.CTkFont(family="Consolas", size=14),
            fg_color="#0a0a12", text_color="#e0e0e0", corner_radius=10, wrap="word",
            activate_scrollbars=True, scrollbar_button_color="#00b4d8", scrollbar_button_hover_color="#0096c7"
        )
        self.chat_box.pack(fill="both", expand=True, padx=12, pady=(12, 8))
        self.chat_box.configure(state="disabled")

        # Input row
        self.input_frame = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        self.input_frame.pack(fill="x", padx=12, pady=(0, 12))

        self.entry = ctk.CTkEntry(
            self.input_frame, placeholder_text="Type your command or talk to me...",
            height=42, font=ctk.CTkFont(size=14),
            fg_color="#0a0a12", border_color="#00b4d8", border_width=1
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry.bind("<Return>", self.process_input)

        self.clear_btn = ctk.CTkButton(
            self.input_frame, text="Clear", width=75, height=42,
            command=self.clear_chat, fg_color="#2a2a3a", hover_color="#ff4757",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.clear_btn.pack(side="right", padx=(0, 8))

        self.send_btn = ctk.CTkButton(
            self.input_frame, text="Send", width=85, height=42,
            command=self.process_input, fg_color="#00b4d8", hover_color="#0096c7",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.send_btn.pack(side="right")

        self.after(600, self.welcome)

    def init_particles(self):
        self.particles = []
        for _ in range(18):
            self.particles.append({
                "angle": random.uniform(0, 360),
                "radius": random.uniform(110, 230),
                "speed": random.uniform(0.4, 1.8),
                "size": random.uniform(2, 4.5)
            })

    def animate(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 10 or h < 10:
            self.after(30, self.animate)
            return

        cx, cy = w // 2, h // 2
        self.angle = (self.angle + 1.2) % 360
        self.pulse = (self.pulse + 0.055) % (2 * math.pi)

        for i in range(6):
            r = 260 + i * 18 + math.sin(self.pulse + i) * 6
            color = f"#{0:02x}{30+i*8:02x}{60+i*12:02x}"
            self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline=color, width=1)

        rings = [
            {"radius": 95, "speed": 1.0, "width": 2, "color": "#00e5ff"},
            {"radius": 130, "speed": -0.7, "width": 2, "color": "#00b4d8"},
            {"radius": 165, "speed": 0.5, "width": 1.5, "color": "#0096c7"},
            {"radius": 200, "speed": -0.35, "width": 1.5, "color": "#0077b6"},
        ]
        for ring in rings:
            r = ring["radius"] + math.sin(self.pulse * 1.5) * 4
            start = self.angle * ring["speed"]
            for j in range(3):
                self.canvas.create_arc(cx-r, cy-r, cx+r, cy+r, start=start + j*120, extent=55, style="arc", outline=ring["color"], width=ring["width"])

        for p in self.particles:
            p["angle"] = (p["angle"] + p["speed"]) % 360
            rad = math.radians(p["angle"])
            x = cx + math.cos(rad) * p["radius"]
            y = cy + math.sin(rad) * p["radius"]
            size = p["size"]
            self.canvas.create_oval(x-size, y-size, x+size, y+size, fill="#00f0ff", outline="")

        for i in range(3):
            wave_r = 70 + i * 35 + math.sin(self.pulse * 2 + i) * 12
            self.canvas.create_oval(cx-wave_r, cy-wave_r, cx+wave_r, cy+wave_r, outline="#00d4ff", width=1)

        core = 22 + math.sin(self.pulse * 3) * 5
        self.canvas.create_oval(cx-core-8, cy-core-8, cx+core+8, cy+core+8, outline="#00f0ff", width=2)
        self.canvas.create_oval(cx-core, cy-core, cx+core, cy+core, fill="#00e5ff", outline="#ffffff", width=2)
        self.canvas.create_oval(cx-9, cy-9, cx+9, cy+9, fill="#ffffff", outline="")

        self.after(28, self.animate)

    def add_message(self, sender, text):
        self.chat_box.configure(state="normal")
        if sender == "You":
            self.chat_box.insert("end", f"You → {text}\n\n")
        else:
            self.chat_box.insert("end", f"Alpha → {text}\n\n")
        self.chat_box.configure(state="disabled")
        self.chat_box.see("end")

    def clear_chat(self):
        self.chat_box.configure(state="normal")
        self.chat_box.delete("1.0", "end")
        self.chat_box.configure(state="disabled")
        self.add_message("Alpha", "Chat cleared.")
        speak("Chat cleared.")

    def welcome(self):
        hour = datetime.now().hour
        greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"
        msg = f"{greeting}. Alpha systems online. How can I help you?"
        self.add_message("Alpha", msg)
        speak(msg)

    def process_input(self, event=None):
        command = self.entry.get().strip()
        if not command:
            return
        self.entry.delete(0, "end")
        self.add_message("You", command)
        threading.Thread(target=self.handle_command, args=(command.lower(),), daemon=True).start()

    def handle_command(self, command):
        # Exit
        if command in ["bye", "exit", "quit"]:
            msg = "Goodbye sir... come back soon."
            self.add_message("Alpha", msg)
            speak(msg)
            self.after(1500, self.destroy)
            return

        # Time
        if "time" in command:
            msg = f"The time is {datetime.now().strftime('%I:%M %p')}"
            self.add_message("Alpha", msg)
            speak(msg)
            return

        # Date
        if "date" in command:
            msg = f"Today is {datetime.now().strftime('%A, %B %d, %Y')}"
            self.add_message("Alpha", msg)
            speak(msg)
            return

        # Name memory
        if "my name is" in command:
            name = command.replace("my name is", "").strip()
            remember("user_name", name)
            msg = f"Nice to meet you, {name}."
            self.add_message("Alpha", msg)
            speak(msg)
            return

        if "what is my name" in command:
            name = recall("user_name")
            msg = f"Your name is {name}." if name else "I don't know your name yet."
            self.add_message("Alpha", msg)
            speak(msg)
            return

        if "forget my name" in command:
            forget("user_name")
            msg = "Okay, I forgot your name."
            self.add_message("Alpha", msg)
            speak(msg)
            return

        if "last song" in command:
            song = recall("last_song")
            msg = f"The last song was {song}." if song else "I don't remember any song."
            self.add_message("Alpha", msg)
            speak(msg)
            return

        # Screenshot
        if "screenshot" in command:
            img = pyautogui.screenshot()
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            img.save(filename)
            msg = f"Screenshot saved as {filename}"
            self.add_message("Alpha", msg)
            speak("Screenshot taken.")
            try:
                os.startfile(filename)
            except:
                pass
            return

        # Image generation
        if command.startswith("create") or "generate image" in command:
            self.add_message("Alpha", "What should I create? Type your prompt in the next dialog.")
            speak("What should I create?")
            dialog = ctk.CTkInputDialog(text="Image prompt:", title="Create Image")
            prompt = dialog.get_input()
            if prompt:
                self.add_message("Alpha", "Generating image... please wait.")
                speak("Generating image")
                try:
                    r = requests.post("https://apiimagestrax.vercel.app/api/genimage", json={"prompt": prompt}, timeout=60)
                    if r.status_code == 200:
                        filename = f"output_{int(time.time())}.png"
                        with open(filename, "wb") as f:
                            f.write(r.content)
                        msg = "Image generated and saved."
                        self.add_message("Alpha", msg)
                        speak(msg)
                        os.startfile(filename)
                    else:
                        msg = "Image generation failed."
                        self.add_message("Alpha", msg)
                        speak(msg)
                except:
                    msg = "Something went wrong while generating the image."
                    self.add_message("Alpha", msg)
                    speak(msg)
            return

        # Timer
        if "set timer" in command or command == "timer":
            nums = re.findall(r'\d+', command)
            if nums:
                self.set_timer(nums[0])
            else:
                self.cmd_timer()
            return

        # Alarm
        if "set alarm" in command or command == "alarm":
            m = re.search(r'(\d{1,2}:\d{2})', command)
            if m:
                self.set_alarm(m.group(1))
            else:
                self.cmd_alarm()
            return

        # Stopwatch
        if "start stopwatch" in command:
            self.start_stopwatch()
            return
        if "stop stopwatch" in command:
            self.stop_stopwatch()
            return
        if "reset stopwatch" in command:
            self.reset_stopwatch()
            return

        # Music
        if "play music" in command or command == "music":
            self.cmd_music()
            return

        # Weather
        if "weather" in command:
            self.cmd_weather()
            return

        # Message
        if "message" in command:
            self.cmd_message()
            return

        # Map
        if "map" in command:
            self.cmd_map()
            return

        # Website
        if any(x in command for x in ["website", "open web", "open website"]):
            self.cmd_website()
            return

        # Calendar
        if "calendar" in command:
            self.cmd_calendar()
            return

        # Shutdown
        if command in ["shutdown", "power off", "poweroff"]:
            msg = "Shutting down the system."
            self.add_message("Alpha", msg)
            speak(msg)
            if platform.system() == "Windows":
                os.system("shutdown /s /t 1")
            return

        # Help
        if command == "help":
            self.cmd_help()
            return

        # Default AI
        response = get_ai_response(command)
        self.add_message("Alpha", response)
        speak(response)

    # ================== EXTRA FEATURES ==================
    def set_timer(self, seconds):
        try:
            seconds = int(seconds)
            if seconds <= 0:
                msg = "Timer must be greater than zero."
                self.add_message("Alpha", msg)
                speak(msg)
                return
            msg = f"Timer set for {seconds} seconds."
            self.add_message("Alpha", msg)
            speak(msg)
            def countdown():
                time.sleep(seconds)
                speak("Time's up! " * 3)
                self.add_message("Alpha", "Time's up!")
            threading.Thread(target=countdown, daemon=True).start()
        except:
            msg = "I couldn't understand the number of seconds."
            self.add_message("Alpha", msg)
            speak(msg)

    def set_alarm(self, alarm_time_str):
        if not re.match(r'^\d{1,2}:\d{2}$', alarm_time_str or ""):
            msg = "Please give time in HH:MM format, like 07:30"
            self.add_message("Alpha", msg)
            speak(msg)
            return
        hh, mm = map(int, alarm_time_str.split(":"))
        if not (0 <= hh <= 23 and 0 <= mm <= 59):
            msg = "Invalid time."
            self.add_message("Alpha", msg)
            speak(msg)
            return
        alarm_time_str = f"{hh:02d}:{mm:02d}"
        msg = f"Alarm set for {alarm_time_str}"
        self.add_message("Alpha", msg)
        speak(msg)
        def alarm_checker():
            while True:
                if datetime.now().strftime("%H:%M") == alarm_time_str:
                    speak("Wake up! This is your alarm!" * 5)
                    self.add_message("Alpha", "Wake up! This is your alarm!")
                    break
                time.sleep(10)
        threading.Thread(target=alarm_checker, daemon=True).start()

    def start_stopwatch(self):
        if not self.stopwatch_running:
            self.stopwatch_running = True
            self.stopwatch_start_time = time.time()
            msg = "Stopwatch started."
            self.add_message("Alpha", msg)
            speak(msg)
        else:
            msg = "Stopwatch is already running."
            self.add_message("Alpha", msg)
            speak(msg)

    def stop_stopwatch(self):
        if self.stopwatch_running:
            elapsed = time.time() - self.stopwatch_start_time
            self.stopwatch_running = False
            mins = int(elapsed // 60)
            secs = int(elapsed % 60)
            msg = f"Stopwatch stopped. {mins} minutes and {secs} seconds."
            self.add_message("Alpha", msg)
            speak(msg)
        else:
            msg = "Stopwatch is not running."
            self.add_message("Alpha", msg)
            speak(msg)

    def reset_stopwatch(self):
        self.stopwatch_running = False
        self.stopwatch_start_time = None
        msg = "Stopwatch reset."
        self.add_message("Alpha", msg)
        speak(msg)

    # ================== BUTTON COMMANDS ==================
    def cmd_time(self):
        self.handle_command("time")

    def cmd_date(self):
        self.handle_command("date")

    def cmd_weather(self):
        self.add_message("Alpha", "Which city?")
        speak("Which city?")
        dialog = ctk.CTkInputDialog(text="Enter city name:", title="Weather")
        city = dialog.get_input()
        if city:
            try:
                r = requests.get(f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}&aqi=no", timeout=10)
                data = r.json()
                temp = data['current']['temp_c']
                condition = data['current']['condition']['text']
                msg = f"In {city} it is {temp}°C and {condition}"
                self.add_message("Alpha", msg)
                speak(msg)
            except:
                msg = "Couldn't fetch weather."
                self.add_message("Alpha", msg)
                speak(msg)

    def cmd_music(self):
        self.add_message("Alpha", "What should I play?")
        speak("What should I play?")
        dialog = ctk.CTkInputDialog(text="Song name:", title="Music")
        song = dialog.get_input()
        if song:
            remember("last_song", song)
            msg = f"Playing {song} on YouTube"
            self.add_message("Alpha", msg)
            speak(msg)
            kit.playonyt(song)

    def cmd_screenshot(self):
        self.handle_command("screenshot")

    def cmd_message(self):
        self.add_message("Alpha", "Opening message...")
        speak("Enter phone number and message")
        try:
            mob = ctk.CTkInputDialog(text="Phone (+91...):", title="WhatsApp").get_input()
            msg_text = ctk.CTkInputDialog(text="Message:", title="WhatsApp").get_input()
            if mob and msg_text:
                kit.sendwhatmsg_instantly(mob, msg_text, wait_time=8)
                msg = f"Sending message to {mob}"
                self.add_message("Alpha", msg)
                speak("Sending your message")
        except:
            msg = "Message cancelled."
            self.add_message("Alpha", msg)
            speak(msg)

    def cmd_map(self):
        dialog = ctk.CTkInputDialog(text="Enter address:", title="Maps")
        address = dialog.get_input()
        if address:
            url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(address)}"
            webbrowser.open(url)
            msg = f"Opening map for {address}"
            self.add_message("Alpha", msg)
            speak(msg)

    def cmd_timer(self):
        dialog = ctk.CTkInputDialog(text="Enter seconds:", title="Timer")
        sec = dialog.get_input()
        if sec:
            self.set_timer(sec)

    def cmd_alarm(self):
        dialog = ctk.CTkInputDialog(text="Enter time (HH:MM):", title="Alarm")
        t = dialog.get_input()
        if t:
            self.set_alarm(t)

    def cmd_website(self):
        dialog = ctk.CTkInputDialog(text="Website name or URL:", title="Open Website")
        site = dialog.get_input()
        if site:
            remember("last_website", site)
            url = site if site.startswith("http") else f"https://www.{site}.com"
            webbrowser.open(url)
            msg = f"Opening {site}"
            self.add_message("Alpha", msg)
            speak(msg)

    def cmd_calendar(self):
        dialog = ctk.CTkInputDialog(text="Enter year:", title="Calendar")
        year = dialog.get_input()
        if year:
            try:
                year = int(year)
                cal_text = calendar.calendar(year)
                self.add_message("Alpha", f"Calendar for {year}:\n{cal_text}")
                speak(f"Here's the calendar for {year}")
            except:
                msg = "Invalid year."
                self.add_message("Alpha", msg)
                speak(msg)

    def cmd_help(self):
        help_text = (
            "Available commands:\n"
            "• time / date\n"
            "• weather\n"
            "• play music\n"
            "• screenshot\n"
            "• message\n"
            "• map\n"
            "• set timer / timer\n"
            "• set alarm / alarm\n"
            "• start / stop / reset stopwatch\n"
            "• calendar\n"
            "• open website\n"
            "• create (image generation)\n"
            "• my name is ... / what is my name / forget my name\n"
            "• last song\n"
            "• shutdown\n"
            "• or just talk to me normally"
        )
        self.add_message("Alpha", help_text)
        speak("I printed all the available commands.")

# ================== RUN ==================
if __name__ == "__main__":
    app = AlphaApp()
    app.mainloop()
