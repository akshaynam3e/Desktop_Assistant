import pyttsx3
import webbrowser
from datetime import datetime
import requests
import re
import os
import random
import sys
import platform
import time
import pyautogui
import pywhatkit as kit
import json
import threading
import calendar
import urllib.parse
from dotenv import load_dotenv

# ================== LOAD SECRETS FROM .env ==================
load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
MODEL = "deepseek/deepseek-v4-flash-0731"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MEMORY_FILE = "memory.json"

if not API_KEY:
    print("❌ ERROR: OPENROUTER_API_KEY not found in .env file!")
if not WEATHER_API_KEY:
    print("⚠️ WARNING: WEATHER_API_KEY not found in .env file!")

# ================== MEMORY ==================
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {}
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

# ================== SPEAK ==================
engine = pyttsx3.init()
engine.setProperty('rate', 175)
engine.setProperty('volume', 1.0)
for voice in engine.getProperty('voices'):
    if any(x in voice.name.lower() for x in ["female", "zira", "samantha"]):
        engine.setProperty('voice', voice.id)
        break

def speak(text):
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"[Speak Error] {e}")

# ================== AI ==================
def get_ai_response(prompt):
    if not API_KEY:
        return "API key missing. Please check your .env file."
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "Alpha-Text"
    }
    data = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful, slightly flirty and playful AI assistant named Alpha. Never use any emojis or special symbols in your responses. Keep the language clean and natural."
            },
            {"role": "user", "content": prompt}
        ]
    }
    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"]
        reply = re.sub(r'[^\w\s,.?!\'\"\-]', '', reply)
        return reply.strip()
    except Exception as e:
        print(f"[AI ERROR]: {e}")
        return "Sorry, my brain just went blank for a second..."

# ================== HELPERS ==================
def message():
    mob = input("Phone Number with country code [+91] : ").strip()
    msg = input("Message : ").strip()
    if mob and msg:
        kit.sendwhatmsg_instantly(mob, msg, wait_time=5)
        speak(f"Sending your message to {mob}")

def show_calendar(year):
    print(calendar.calendar(year))

def set_timer(seconds):
    try:
        seconds = int(seconds)
        if seconds <= 0:
            speak("Timer must be greater than zero.")
            return
        speak(f"Timer set for {seconds} seconds.")
        def countdown():
            time.sleep(seconds)
            speak("Time's up!" * 3)
        threading.Thread(target=countdown, daemon=True).start()
    except:
        speak("I couldn't understand the number of seconds.")

def set_alarm(alarm_time_str):
    if not re.match(r'^\d{1,2}:\d{2}$', alarm_time_str or ""):
        speak("Please give time in HH:MM format, like 07:30")
        return
    hh, mm = map(int, alarm_time_str.split(":"))
    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        speak("Invalid time.")
        return
    alarm_time_str = f"{hh:02d}:{mm:02d}"
    speak(f"Alarm set for {alarm_time_str}")
    def alarm_checker():
        while True:
            if datetime.now().strftime("%H:%M") == alarm_time_str:
                speak("Wake up! This is your alarm!" * 5)
                break
            time.sleep(10)
    threading.Thread(target=alarm_checker, daemon=True).start()

stopwatch_running = False
stopwatch_start_time = None

def start_stopwatch():
    global stopwatch_running, stopwatch_start_time
    if not stopwatch_running:
        stopwatch_running = True
        stopwatch_start_time = time.time()
        speak("Stopwatch started.")
    else:
        speak("Stopwatch is already running.")

def stop_stopwatch():
    global stopwatch_running, stopwatch_start_time
    if stopwatch_running:
        elapsed = time.time() - stopwatch_start_time
        stopwatch_running = False
        mins = int(elapsed // 60)
        secs = int(elapsed % 60)
        speak(f"Stopwatch stopped. {mins} minutes and {secs} seconds.")
    else:
        speak("Stopwatch is not running.")

def reset_stopwatch():
    global stopwatch_running, stopwatch_start_time
    stopwatch_running = False
    stopwatch_start_time = None
    speak("Stopwatch reset.")

def open_location_on_map():
    while True:
        address = input("\nEnter address (or type quit): ").strip()
        if address.lower() in ["quit", "exit", "q"]:
            speak("Bye... come back soon!")
            return
        if not address:
            speak("You didn’t type anything... try again.")
            continue
        url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(address)}"
        speak(f"Opening {address}")
        webbrowser.open(url)

def music():
    speak("Do you want random offline music or something online?")
    choice = input("You: ").lower()
    if "random" in choice or "offline" in choice:
        music_folder = r"C:\Users\jnv giridih\Videos\Snaptube Downloader"
        try:
            songs = [os.path.join(music_folder, f) for f in os.listdir(music_folder) if f.endswith(".mp3")]
            if songs:
                song = random.choice(songs)
                speak(f"Playing {os.path.basename(song)}")
                os.startfile(song)
            else:
                speak("No mp3 files found.")
        except:
            speak("Couldn't access the music folder.")
    else:
        speak("What should I play?")
        song_name = input("You: ").strip()
        if song_name:
            remember("last_song", song_name)
            speak(f"Playing {song_name} on YouTube")
            kit.playonyt(song_name)

def help_menu():
    help_text = """
Available commands:
• time / date
• screenshot
• open website
• message
• weather
• play music
• set timer / set alarm
• start / stop / reset stopwatch
• calendar
• my name is ...
• what is my name / forget my name
• last song
• create (image generation)
• map
• bye / exit / quit
• or just talk to me normally...
"""
    print(help_text)
    speak("I just printed all the commands for you.")

def screenshot():
    img = pyautogui.screenshot()
    filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    img.save(filename)
    print(f"Screenshot saved as {filename}")
    os.startfile(filename)

# ================== MAIN HANDLER ==================
def handler():
    while True:
        try:
            command = input("\nYou: ").strip().lower()
            if not command:
                continue

            # Image generation
            if command.startswith("create") or "generate image" in command:
                speak("What should I create? Type your prompt.")
                prompt = input("Prompt: ").strip()
                if prompt:
                    speak("Generating image... this might take a moment.")
                    try:
                        response = requests.post(
                            "https://apiimagestrax.vercel.app/api/genimage",
                            json={"prompt": prompt},
                            timeout=60
                        )
                        if response.status_code == 200:
                            filename = f"output_{int(time.time())}.png"
                            with open(filename, "wb") as f:
                                f.write(response.content)
                            speak("Image generated and saved.")
                            os.startfile(filename)
                        else:
                            speak("Sorry, image generation failed.")
                    except:
                        speak("Something went wrong while generating the image.")
                continue

            # Memory
            if "my name is" in command:
                name = command.replace("my name is", "").strip()
                remember("user_name", name)
                speak(f"Nice to meet you, {name}.")
                continue

            if "message" in command:
                message()
                continue

            if "what is my name" in command:
                name = recall("user_name")
                speak(f"Your name is {name}." if name else "I don't know your name yet.")
                continue

            if "forget my name" in command:
                forget("user_name")
                speak("Okay, I forgot your name.")
                continue

            if "last song" in command:
                song = recall("last_song")
                speak(f"The last song was {song}." if song else "I don't remember any song.")
                continue

            # Timer / Alarm / Stopwatch
            if "set timer" in command:
                nums = re.findall(r'\d+', command)
                if nums:
                    set_timer(nums[0])
                else:
                    speak("How many seconds?")
                    set_timer(input("Seconds: "))
                continue

            if "set alarm" in command:
                m = re.search(r'(\d{1,2}:\d{2})', command)
                if m:
                    set_alarm(m.group(1))
                else:
                    speak("Tell me the time in HH:MM")
                    set_alarm(input("Time: "))
                continue

            if "start stopwatch" in command:
                start_stopwatch()
                continue
            if "stop stopwatch" in command:
                stop_stopwatch()
                continue
            if "reset stopwatch" in command:
                reset_stopwatch()
                continue

            if "map" in command:
                open_location_on_map()
                continue

            # Basic commands
            if command in ["bye", "exit", "quit"]:
                speak("Goodbye sir... come back soon.")
                sys.exit()

            if "time" in command:
                speak(f"The time is {datetime.now().strftime('%I:%M %p')}")
                continue

            if "date" in command:
                speak(f"Today is {datetime.now().strftime('%A, %B %d, %Y')}")
                continue

            if any(x in command for x in ["website", "open web", "open website"]):
                speak("Which website?")
                site = input("Website: ").strip()
                if site:
                    remember("last_website", site)
                    url = site if site.startswith("http") else f"https://www.{site}.com"
                    speak(f"Opening {site}")
                    webbrowser.open(url)
                continue

            if "calendar" in command:
                speak("Which year?")
                try:
                    year = int(input("Year: "))
                    show_calendar(year)
                    speak(f"Here's the calendar for {year}")
                except:
                    speak("Invalid year.")
                continue

            if "weather" in command:
                speak("Which city?")
                city = input("City: ").strip()
                if city:
                    remember("last_city", city)
                    try:
                        r = requests.get(
                            f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}&aqi=no",
                            timeout=10
                        )
                        data = r.json()
                        temp = data['current']['temp_c']
                        condition = data['current']['condition']['text']
                        speak(f"In {city} it is {temp} degrees Celsius and {condition}")
                    except:
                        speak("Couldn't fetch weather.")
                continue

            if "play music" in command:
                music()
                continue

            if command in ["shutdown", "power off", "poweroff"]:
                speak("Shutting down the system.")
                if platform.system() == "Windows":
                    os.system("shutdown /s /t 1")
                continue

            if "screenshot" in command:
                screenshot()
                continue

            if command == "help":
                help_menu()
                continue

            # Default → AI
            response = get_ai_response(command)
            print(f"Alpha: {response}")
            speak(response)

        except KeyboardInterrupt:
            speak("Okay, stopping.")
            break
        except Exception as e:
            print(f"Error: {e}")
            speak("Something went wrong.")

# ================== START ==================
if __name__ == "__main__":
    hour = datetime.now().hour
    if hour < 12:
        speak("Good morning...")
    elif hour < 17:
        speak("Good afternoon...")
    else:
        speak("Good evening...")

    speak("I'm ready. Type your commands. Type help if you need me.")
    print("\n" + "="*50)
    print("  Type 'help' to see commands | Type 'bye' to exit")
    print("="*50 + "\n")
    handler()