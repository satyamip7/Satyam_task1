import speech_recognition as sr
import pyttsx3
import sounddevice as sd
import numpy as np
import webbrowser
import datetime

# Initialize recognizer and text-to-speech engine
recognizer = sr.Recognizer()
engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

def listen():
    # Record audio using sounddevice
    duration = 5  # seconds
    fs = 44100    # sample rate
    print("🎤 Listening...")
    audio_data = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()

    # Convert to AudioData for recognition
    audio_bytes = audio_data.tobytes()
    audio = sr.AudioData(audio_bytes, fs, 2)

    try:
        command = recognizer.recognize_google(audio)
        print(f"👉 You said: {command}")
        return command.lower()
    except sr.UnknownValueError:
        speak("Sorry, I did not understand.")
        return ""
    except sr.RequestError:
        speak("Network error.")
        return ""

def process_command(command):
    if "time" in command:
        now = datetime.datetime.now().strftime("%H:%M:%S")
        speak(f"The time is {now}")
    elif "open youtube" in command:
        webbrowser.open("https://www.youtube.com")
        speak("Opening YouTube")
    elif "open google" in command:
        webbrowser.open("https://www.google.com")
        speak("Opening Google")
    elif "hello" in command:
        speak("Hello Satyam, how are you?")
    elif "exit" in command or "quit" in command:
        speak("Goodbye!")
        exit()
    else:
        speak("I can’t do that yet.")

if __name__ == "__main__":
    speak("Voice Assistant activated. Say something!")
    while True:
        command = listen()
        if command:
            process_command(command)
