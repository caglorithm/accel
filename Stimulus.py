import time
import numpy as np
import pyaudio
import threading
import logging

class AudioStimulus():
    def __init__(self, base_fr=40.0, stim_fr=0.8, stim_len=5, bitrate=48000):
        self.PyAudio = pyaudio.PyAudio
        self.bitrate = bitrate
        self.isActive = False
        self.base_fr = base_fr
        self.stim_fr = stim_fr
        self.stim_len = stim_len  # second

        self.SLEEP_AFTER_LOOP = 0.0 # in seconds

        logging.info("Initializing audio interface ...")
        self.p = self.PyAudio()
        self.stream = self.p.open(format=pyaudio.paFloat32,
                        channels=1,
                        rate=int(self.bitrate),
                        output=True)
                        
        logging.info("Generating waveform ...")
        self.waveform = self.generate_sin_waveform()
        logging.info("AudioStimulus initialized.")

    def terminate_audio_stream(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        logging.info("Audio stream terminated.")

    def generate_sin_waveform(self,):
        sound_len = self.stim_len  # second
        waveform = np.ndarray(
            (int(sound_len * self.bitrate)), dtype=np.float32)

        f1 = self.base_fr
        f2 = self.base_fr + self.stim_fr

        # generate waveform
        for i in range(len(waveform)):
            frac = 1 + i / len(waveform)
            waveform[i] = np.sin(f1 * i / self.bitrate * 2 * np.pi) + \
                np.sin(f2 * i / self.bitrate * 2 * np.pi + np.pi)
        waveform /= np.max(waveform)  # normalize
        return waveform

    def play_audio(self, waveform):
        # start loop that generates audio
        while self.isActive:
            logging.info("Play stimulus.")
            self.stream.write(waveform, num_frames=len(waveform))
            time.sleep(self.SLEEP_AFTER_LOOP)

        self.isActive = False
        logging.info("Stimulus stopped.")

    def start_stimulus(self):
        self.isActive = True
        # kick off a thread that loops
        x = threading.Thread(target=self.play_audio,
                             args=(self.waveform,))
        x.start()

    def play_waveform(self, waveform):
        self.isActive = True
        # kick off a thread that loops
        x = threading.Thread(target=self.play_audio,
                             args=(waveform,))
        x.start()

    def stop_stimulus(self):
        self.isActive = False
        logging.info("Stopping stimulus ...")