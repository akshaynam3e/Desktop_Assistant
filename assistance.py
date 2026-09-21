import numpy as np
import pyttsx3
import webbrowser
from datetime import datetime
import requests
import re
import os
import random
import speech_recognition as sr
import sys
import platform
import cv2
import time
import pywhatkit
import json
import threading
import calendar
from colorama import Fore, Style, init
from dotenv import load_dotenv
load_dotenv()
init(autoreset=True)
COLORS = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN, Fore.WHITE]
def printf(string):
    for i in string:
        print(i,end="",flush=True)
        time.sleep(0.02)
def colored_print(text, is_input=False):
    color = random.choice(COLORS)
    if is_input:
        printf(color + "You: " + text + Style.RESET_ALL)
    else:
        printf(color + text + Style.RESET_ALL)
API_KEY = os.getenv("Api_key")
MODEL = "openai/gpt-4o"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
stop_speaking = False
engine = pyttsx3.init()
engine.setProperty('rate', 170)
engine.setProperty('volume', 1.0)
voices = engine.getProperty('voices')
MEMORY_FILE = "memory.json"
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
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
    memory = load_memory()
    return memory.get(key, None)
def forget(key):
    memory = load_memory()
    if key in memory:
        del memory[key]
        save_memory(memory)
def detect_double_clap(threshold=3000, max_interval=3, timeout=10):
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        claps = []
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                return False
            try:
                audio = recognizer.listen(source, phrase_time_limit=0.8)
                audio_data = np.frombuffer(audio.get_raw_data(), np.int16)
                volume = np.abs(audio_data).mean()
                if volume > threshold:
                    current_time = time.time()
                    claps.append(current_time)
                    claps = [t for t in claps if current_time - t <= max_interval]
                    if len(claps) >= 2:
                        return True
            except Exception as e:
                colored_print(f"Error: {e}")
                continue
def speak(text):
    try:
        engine = pyttsx3.init(driverName='sapi5')
        engine.setProperty('rate', 170)
        engine.setProperty('volume', 1.0)
        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[1].id)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception:
        pass
def show_calendar(year):
    colored_print(calendar.calendar(year))
def listen_command(retries=2):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.energy_threshold = 1
        recognizer.pause_threshold = 1.2
        recognizer.adjust_for_ambient_noise(source, duration=1)
        colored_print("Listening...")
        try:
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=12)
        except sr.WaitTimeoutError:
            return listen_command(retries - 1) if retries > 0 else ""
    try:
        text = recognizer.recognize_google(audio, language="en-IN")
        colored_print(text, is_input=True)
        return text.lower()
    except sr.UnknownValueError:
        return listen_command(retries - 1) if retries > 0 else ""
    except sr.RequestError:
        return ""
def get_ai_response(prompt):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "Jarvis-AI"
    }
    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    }
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"]
        return re.sub(r'[^\w\s,.?!]', '', reply.strip())
    except Exception as e:
        colored_print(f"[AI ERROR]: {e}")
        return "Sorry, I couldn't think of a good answer."
def get_chat_history(limit=10):
    cursor.execute("SELECT user_input, bot_response FROM chat_history ORDER BY id DESC LIMIT %s", (limit,))
    return cursor.fetchall()
def music():
    speak("How would you like me to play music — randomly or by your choice?")
    b=listen_command()
    if "random" in b.lower():
        speak("Sure sir, have a well-deserved break!")
        music_folder = (r"C:\\Users\\jnv giridih\\Videos\\Snaptube Downloader")
        songs = [os.path.join(music_folder, f) for f in os.listdir(music_folder) if f.endswith(".mp3")]
        if not songs:
            speak("No mp3 files found in your folder.")
            return
        song_to_play = random.choice(songs)
        speak(f"Playing {song_to_play}")
        os.startfile(song_to_play)
    elif any(phrase in b for phrase in ["online", "choice", "my choice"]):
        speak("What should I play?")
        song_name =listen_command()
        if song_name:
            remember("last_song", song_name)
            speak(f"Playing {song_name} on YouTube.")
            pywhatkit.playonyt(song_name)
        else:
            speak("I didn't hear any song name.")
def set_timer(seconds):
    try:
        seconds = int(seconds)
    except:
        speak("I couldn't understand the number of seconds.")
        return
    if seconds <= 0:
        speak("Timer duration must be greater than zero.")
        return
    speak(f"Timer set for {seconds} seconds.")
    def countdown():
        time.sleep(seconds)
        speak("Time's up! Your timer has finished.")
    threading.Thread(target=countdown, daemon=True).start()
def set_alarm(alarm_time_str):
    if not re.match(r'^\d{1,2}:\d{2}$', alarm_time_str or ""):
        speak("Please say the time in HH colon MM format, like zero seven thirty.")
        return
    hh, mm = alarm_time_str.split(":")
    hh = int(hh); mm = int(mm)
    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        speak("That time is invalid.")
        return
    alarm_time_str = f"{hh:02d}:{mm:02d}"
    speak(f"Alarm set for {alarm_time_str}.")
    def alarm_checker():
        while True:
            now_str = datetime.now().strftime("%H:%M")
            if now_str == alarm_time_str:
                speak("Wake up! This is your alarm." * 10)
                break
            time.sleep(15)
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
        speak(f"Stopwatch stopped. Total time {int(elapsed // 60)} minutes and {int(elapsed % 60)} seconds.")
    else:
        speak("Stopwatch is not running.")
def image(payload):
    url = "https://apiimagestrax.vercel.app/api/genimage"
    print(f"Sending request to {url} with payload: {payload}")
    response = requests.post(url, json=payload)
    if response.status_code == 200 and response.headers.get("Content-Type") == "image/png":
        with open("output.png", "wb") as f:
            f.write(response.content)
        print("✅ Image saved as output.png")
    else:
        print("❌ Failed to generate image")
        print("Status code:", response.status_code)
        print("Headers:", response.headers)
        print("Response text:", response.text)
def reset_stopwatch():
    global stopwatch_running, stopwatch_start_time
    stopwatch_running = False
    stopwatch_start_time = None
    speak("Stopwatch reset.")
def help():
    colored_print("All commands are given below\n1 >>> stop speaking, shut up, wait, to pause while i am speaking.\n2 >>> bye, exit, quit to close me\n3 >>> time for time\n4 >>> date for date\n5 >>> website, open website, open web to open particular website\n6 >>> open camera to open camera\n7 >>> code, visual studio,  to open visual studio code\n8 >>> play game, start game to start a random game\n9 >>> play music to play music randomly (Offline) or particular music (Online). \n10 >>> shut down, power off for shut down\n11 >>> weather to know weather of your city. \n12 >>> if no condition matched Artificial Intelligence will reply to you\n13 >>> my name is ..., what is my name, forget my name (memory)\n14 >>> what was the last song, what was the last website, what was the last city (memory)\n15 >>> set timer, set alarm, start/stop/reset stopwatch (clock)\n16 >>> calendar to see calendar of a particular year\n\nNow you are ready to use it.\n")

def handler():
    global stop_speaking
    while True:
        command = listen_command().lower()
        if not command:
            continue
        if "create" in command.lower():
                speak("What should I create? Please type your prompt.")
                anp = input("You : ")
                url = "https://apiimagestrax.vercel.app/api/genimage"
                payload = {"prompt": anp}
                print("Generating...")
                response = requests.post(url, json=payload)
                if response.status_code == 200 and response.headers.get("Content-Type") == "image/png":
                    x=1
                    save = f"output{x}.jpg"
                    with open(save, "wb") as f:
                        f.write(response.content)
                    print(f"Image saved as {save}")
                    x+=1
                else:
                    print("Failed to generate image")
                os.startfile(save)
                time.sleep(5)
                continue
        if "my name is" in command:
            name = command.replace("my name is", "").strip()
            remember("user_name", name)
            speak(f"Nice to meet you, {name}!")
            continue
        if command == "help":
            help()
        elif "what is my name" in command:
            name = recall("user_name")
            if name:
                speak(f"Your name is {name}.")
            else:
                speak("I don't know your name yet. Please tell me.")
            continue
        elif "forget my name" in command:
            forget("user_name")
            speak("Okay, I forgot your name.")
            continue
        elif "what was the last song" in command:
            song = recall("last_song")
            if song:
                speak(f"The last song you asked me to play was {song}.")
            else:
                speak("I don't remember any song yet.")
            continue
        elif "set timer" in command:
            nums = re.findall(r'\d+', command)
            if nums:
                set_timer(nums[0])
            else:
                speak("For how many seconds should I set the timer?")
                sec_text = listen_command()
                nums = re.findall(r'\d+', sec_text)
                if nums:
                    set_timer(nums[0])
                else:
                    speak("I could not understand the duration for the timer.")
            continue
        elif "set alarm" in command:
            m = re.search(r'(\d{1,2}:\d{2})', command)
            if m:
                set_alarm(m.group(1))
            else:
                speak("Please tell me the alarm time in HH:MM format, like 07:30")
                alarm_text = listen_command()
                m = re.search(r'(\d{1,2}:\d{2})', alarm_text or "")
                if m:
                    set_alarm(m.group(1))
                else:
                    speak("I couldn't catch the alarm time.")
            continue
        elif "start stopwatch" in command:
            start_stopwatch()
            continue
        elif "stop stopwatch" in command:
            stop_stopwatch()
            continue
        elif "reset stopwatch" in command:
            reset_stopwatch()
            continue
        if any(phrase in command for phrase in ["stop speaking", "shut up", "wait","stop"]):
            stop_speaking = True
            engine.stop()
            continue
        elif any(phrase in command for phrase in ["bye", "exit", "quit"]):
            speak("Goodbye. Take care!")
            sys.exit()
        elif "time" in command:
            now = datetime.now()
            speak(f"The time is {now.strftime('%I:%M %p')}")
            continue
        elif "date" in command:
            now = datetime.now()
            print(f"Today is {now.strftime('%A, %B %d, %Y')}")
            speak(f"Today is {now.strftime('%A, %B %d, %Y')}")
            continue
        elif any(x in command for x in ["website", "open web", "open website"]):
            speak("Which website should I open?")
            site = listen_command()
            if site:
                remember("last_website", site)
                url = f"https://www.{site}.com"
                speak(f"Opening {site}.")
                webbrowser.open(url)
                continue
            else:
                speak("No website name heard.")
                continue
        elif "calendar" in command :
            colored_print("For Which Year?\n")
            speak("For Which Year?")
            x=listen_command()
            u=int(x)
            speak("Sure, Sir")
            show_calendar(u)
            speak(f"Here is the calendar of {u}")
        elif "weather" in command:
            API_KEY = "311f393b174a4e819fe65320251908"
            BASE_URL = "http://api.weatherapi.com/v1/current.json"
            speak("what is your city name?")
            b=listen_command()
            c=b.lower()
            remember("last_city", c)
            url = f"{BASE_URL}?key={API_KEY}&q={c}&aqi=no"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                location = data['location']['name']
                region = data['location']['region']
                country = data['location']['country']
                temp_c = data['current']['temp_c']
                condition = data['current']['condition']['text']
                humidity = data['current']['humidity']
                wind_kph = data['current']['wind_kph']
                colored_print(f"\nWeather in {location}, {region}, {country}:")
                colored_print(f"Temperature: {temp_c}°C")
                colored_print(f"Condition: {condition}")
                colored_print(f"Humidity: {humidity}%")
                colored_print(f"Wind Speed: {wind_kph} kph")
                speak(f"\nWeather in {location}, {region}, {country}:")
                speak(f"Temperature: {temp_c} degree Celsius")
                speak(f"Condition: {condition}")
                speak(f"Humidity: {humidity} Percentage")
                speak(f"Wind Speed: {wind_kph} kilometer per hour")
            else:
                colored_print(f"Error: Unable to fetch data (Status code: {response.status_code})")
            continue
        elif "open camera" in command:
            speak("Opening camera. Press Q to close.")
            cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 200)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 200)
            if not cap.isOpened():
                colored_print("Camera is not available.")
            else:
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    frame = cv2.flip(frame, 1)
                    cv2.imshow("Camera", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                cap.release()
                cv2.destroyAllWindows()
                continue
        elif "code" in command or "visual studio" in command:
            speak("Opening Visual Studio Code.")
            try:
                os.startfile("C:\\Users\\JNV\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe")
            except:
                speak("Unable to find or open VS Code.")
            continue
        elif "play game" in command or "start game" in command:
            continue
        elif "play music" in command:
            music()
            continue
        elif command in ("shutdown","power off","poweroff"):
            speak("Shutting down.")
            sys_os = platform.system()
            if sys_os == "Windows":
                os.system("shutdown /s /t 1")
            elif sys_os == "Linux":
                os.system("shutdown now")
            elif sys_os == "Darwin":
                os.system("sudo shutdown -h now")
            else:
                speak("Shutdown not supported on your OS.")
            continue
        else:
            response = get_ai_response(command)
            colored_print(f"Bot : {response}")
            speak(response)

#colored_print("All commands are given below\n1 >>> stop speaking, shut up, wait, to pause while i am speaking.\n2 >>> bye, exit, quit to close me\n3 >>> time for time\n4 >>> date for date\n5 >>> website, open website, open web to open particular website\n6 >>> open camera to open camera\n7 >>> code, visual studio,  to open visual studio code\n8 >>> play game, start game to start a random game\n9 >>> play music to play music randomly (Offline) or particular music (Online). \n10 >>> shut down, power off for shut down\n11 >>> weather to know weather of your city. \n12 >>> if no condition matched Artificial Intelligence will reply to you\n13 >>> my name is ..., what is my name, forget my name (memory)\n14 >>> what was the last song, what was the last website, what was the last city (memory)\n15 >>> set timer, set alarm, start/stop/reset stopwatch (clock)\n16 >>> calendar to see calendar of a particular year\n\nNow you are ready to use it.\n")
if __name__ == "__main__":
    h = datetime.now().hour
    if h < 12:
        speak("Good morning!")
    elif h < 17:
        speak("Good afternoon!")
    else:
        speak("Good evening!")
    speak("Say help, to see all inbuilt commands")
    b=input("type Space + Enter to start\n")
    c=b.lower()
    if c:
        handler()
