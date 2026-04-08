import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import os

# --- Voice Recording Logic ---
class VoiceRecorder:
    def __init__(self, filename="temp_voice.wav", fs=44100):
        self.filename = filename
        self.fs = fs
        self.recording = None

    def start_recording(self):
        # Start recording 10 seconds (you can make this dynamic later)
        print("Recording...")
        self.recording = sd.rec(int(10 * self.fs), samplerate=self.fs, channels=1)

    def stop_recording(self):
        sd.stop()
        print("Recording stopped.")
        # Save to file
        write(self.filename, self.fs, self.recording)
        return self.filename

# --- Updated Main Window (Simplified logic) ---
# In your ReadEchoMain class, add a new button for Voice
# self.voice_btn = QPushButton('Hold to Record Thoughts')
# self.voice_btn.pressed.connect(self.start_voice)
# self.voice_btn.released.connect(self.stop_voice)

# --- Test Script ---
if __name__ == "__main__":
    recorder = VoiceRecorder()
    
    # 录制 5 秒钟
    print("Start recording for 5 seconds...")
    recorder.start_recording()
    
    import time
    time.sleep(5) # 让程序等 5 秒，不然它会立刻跑完结束
    
    recorder.stop_recording()
    print("Done! Check temp_voice.wav in your folder.")