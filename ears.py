import pvporcupine
from pvrecorder import PvRecorder
import speech_recognition as sr
import time

class Listener:
    def __init__(self, access_key):
        self.porcupine = pvporcupine.create(
            access_key=access_key,
            keywords=["jarvis"],
            sensitivities=[0.7]
        )

        self.recorder = PvRecorder(
            device_index=-1,
            frame_length=self.porcupine.frame_length
        )

        self.recognizer = sr.Recognizer()

        # 🔥 Accuracy tuning
        self.recognizer.pause_threshold = 0.8
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.5
        self.recognizer.energy_threshold = 400
        self.recognizer.dynamic_energy_threshold = True

    # -----------------------
    # Wake Word Detection
    # -----------------------
    def wait_for_wake_word(self):
        print("Listening for 'Jarvis'...", flush=True)
        self.recorder.start()
        try:
            while True:
                pcm = self.recorder.read()
                result = self.porcupine.process(pcm)
                if result >= 0:
                    print("Wake word detected!", flush=True)
                    return True
        finally:
            self.recorder.stop()

    # -----------------------
    # Command Recognition
    # -----------------------
    def listen_to_command(self, retries=2):
        with sr.Microphone() as source:
            print("Quickly calibrating...", flush=True)
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)

            for _ in range(retries):
                try:
                    print("Listening...", flush=True)

                    audio = self.recognizer.listen(
                        source,
                        timeout=8,
                        phrase_time_limit=15
                    )

                    print("Recognizing...", flush=True)

                    command = self.recognizer.recognize_google(
                        audio,
                        language="en-IN"
                    )

                    command = command.strip()

                    if len(command) < 2:
                        return None

                    print(f"Recognized: {command}", flush=True)
                    return command

                except sr.WaitTimeoutError:
                    print("Timeout...")

                except sr.UnknownValueError:
                    print("Didn't understand. Retrying...")

                except sr.RequestError as e:
                    print(f"API Error: {e}")
                    return None

                time.sleep(0.5)

        return None
