import sounddevice as sd
import numpy as np
import pyttsx3
import speech_recognition as sr
import datetime
import webbrowser

engine = pyttsx3.init()
recognizer = sr.Recognizer()

def speak_output(text):
    engine.say(text)
    engine.runAndWait()

def listen_command():
    # sounddevice se audio record karo
    print("Listening...")
    duration = 5  # seconds
    sample_rate = 16000
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
    sd.wait()

    # SpeechRecognition ke recognizer ko numpy array dena
    audio_data = sr.AudioData(audio.tobytes(), sample_rate, 2)
    try:
        command = recognizer.recognize_google(audio_data)
        print(f"You said: {command}")
        return command.lower()
    except sr.UnknownValueError:
        print("Could not understand audio")
        return ""
    except sr.RequestError:
        print("Speech Recognition service error")
        return ""

def process_command(command):
    if "hello" in command:
        speak_output("Hello Satyam, nice to meet you!")
    elif "time" in command:
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        speak_output(f"The time is {current_time}")
    elif "date" in command:
        today = datetime.date.today().strftime("%B %d, %Y")
        speak_output(f"Today's date is {today}")
    elif "search" in command:
        query = command.replace("search", "").strip()
        webbrowser.open(f"https://www.google.com/search?q={query}")
        speak_output(f"Searching for {query}")
    else:
        speak_output("Sorry, I did not understand that.")

if __name__ == "__main__":
    speak_output("Voice Assistant started. Say something!")
    cmd = listen_
    command()
    if cmd:
        process_command(cmd)
