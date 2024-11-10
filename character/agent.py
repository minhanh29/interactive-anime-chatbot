from queue import Queue
import time
from threading import Thread, Event
import pickle
import os
import librosa
import wave
import math
import json
import numpy as np
import io
from scipy.io.wavfile import write
import pyaudio
import unicodedata
from threading import Thread
from .audio.text_to_speech import load_model
from .audio.speech_to_text import SpeechToText


BANG_XOA_DAU = str.maketrans(
    "ÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÈÉẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴáàảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ",
    "A"*17 + "D" + "E"*11 + "I"*5 + "O"*17 + "U"*11 + "Y"*5 + "a"*17 + "d" + "e"*11 + "i"*5 + "o"*17 + "u"*11 + "y"*5
)


def xoa_dau(txt: str) -> str:
    if not unicodedata.is_normalized("NFC", txt):
        txt = unicodedata.normalize("NFC", txt)
    return txt.translate(BANG_XOA_DAU)


class MyCharacter:
    def __init__(self, face_dir, queue):
        # audio
        self.s2t = SpeechToText()
        self.tts = load_model()
        self.window_size = 4410
        self.hop_length = 2205
        self.chunk_size = self.window_size // 3
        self.min_volumne = 0.05
        self.audio_scale_factor = 50

        # communicate with speech to text
        self.speaking_event = Event()
        self.interrupt_event = Event()

        # video
        self.img_dir = os.path.join(face_dir, "lips")
        self.queue = queue
        self.command_queue = Queue()
        self.stop_queue = False
        img_names = ["aeil", "bmpfv", "cdnkgstxyz", "ouwq"]
        self.silence_key = img_names[1]
        transition_keys = ["aeil-bmpfv", "bmpfv-cdnkgstxyz", "bmpfv-ouwq", "bmpfv-smile", "cdnkgstxyz-ouwq"]
        self.transition_keys = set(transition_keys)

        # features
        self.feature_arr = np.load(os.path.join(face_dir, "features.npy"))
        with open(os.path.join(face_dir, "feature_map.json"), "r") as f:
            self.feature_map = json.load(f)["data"]

        with open(os.path.join(face_dir, "lipmodel.pickle"), "rb") as f:
            self.lipmodel = pickle.load(f)

    def map_lipsync_images(self, audio):
        audio = librosa.util.normalize(audio)
        prev_key = self.silence_key
        img_name_sequence = []
        img_names = ["bmpfv", "cdnkgstxyz", "aeil", "ouwq"]
        for i in range(math.ceil(len(audio) / self.hop_length)):
            start_t = i * self.hop_length
            end_t = start_t + self.window_size
            if end_t >= len(audio):
                break

            sample = audio[start_t:end_t]
            volumne = np.mean(np.abs(sample))

            if volumne < self.min_volumne:  # silence
                img_name = self.silence_key
            elif len(sample) < self.window_size:
                img_name = img_names[0]
            else:
                sample = sample[::self.audio_scale_factor]
                pred = self.lipmodel.predict([sample])[0]
                img_name = img_names[int(pred)]

            if prev_key == img_name:
                transition_key = prev_key
            else:
                transition_key = [prev_key, img_name]
                transition_key.sort()
                transition_key = "-".join(transition_key)
                if transition_key not in self.transition_keys:
                    transition_key = prev_key
            prev_key = img_name
            img_name_sequence.append(transition_key)
            img_name_sequence.append(img_name)

        return img_name_sequence

    # def speak_thread(self, audio_norm, img_name_sequence):
    def speak_thread(self, queue: Queue):
        while True:
            if queue.empty():
                time.sleep(0.05)
                continue

            item = queue.get()
            if item["done"]:
                break

            audio_norm, img_name_sequence = item["payload"]
            max_wav_value = 32767
            audio_norm = audio_norm * (max_wav_value / max(0.01, np.max(np.abs(audio_norm))))
            audio_norm = np.clip(audio_norm, -max_wav_value, max_wav_value)
            audio_norm = audio_norm.astype("int16")

            bytes_wav = bytes()
            byte_io = io.BytesIO(bytes_wav)
            write(byte_io, 22050, audio_norm)
            wf = wave.open(byte_io)
            p = pyaudio.PyAudio()
            stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                            channels=wf.getnchannels(),
                            rate=wf.getframerate(),
                            output=True,
                            frames_per_buffer=self.chunk_size)
            frame_size = int(wf.getnframes() / len(img_name_sequence))
            cnt = 0
            stop = False
            while len(data := wf.readframes(self.chunk_size)):
                if self.interrupt_event.is_set():
                    stop = True
                    break

                stream.write(data)
                cnt += self.chunk_size
                self.queue.value = {
                    "type": "speaking",
                    "stop": False,
                    "img_name": img_name_sequence[min(cnt // frame_size, len(img_name_sequence)-1)],
                    "is_last": False
                }
            self.queue.value = None
            stream.stop_stream()
            stream.close()
            if stop:
                break

        p.terminate()

    def speak(self, text):
        text = xoa_dau(text)
        text = text.replace("?", ".").replace("!", ".").replace(";", ".").replace("\n", ".")
        lines = [line.strip() for line in text.split(".")]
        thread = None
        queue = Queue()
        self.interrupt_event.clear()
        self.speaking_event.set()
        for i, line in enumerate(lines):
            line = line.translate(str.maketrans('', '', "!\"#$%&\'()*+-./:;<=>?[\\]^_`{|}~")).strip()
            if line == "":
                continue

            audio_norm, sample_rate = self.tts(line)
            len_au = len(audio_norm)
            extra_sil = int(math.ceil(len_au // self.chunk_size) * self.chunk_size - len_au)
            if extra_sil > 0:
                audio_norm = np.concatenate([audio_norm, np.zeros(extra_sil)])
            img_name_sequence = self.map_lipsync_images(audio_norm)
            queue.put({
                "done": False,
                "payload": (audio_norm, img_name_sequence)
            })
            if self.interrupt_event.is_set():
                break

            if thread is None:
                thread = Thread(target=self.speak_thread, args=(queue,))
                thread.start()

        queue.put({
            "done": True
        })

        if thread is not None:
            thread.join()
        self.speaking_event.clear()
        self.interrupt_event.clear()

    def thinking(self):
        self.queue.value = {
            "type": "thinking",
            "stop": False,
            "img_name": None,
            "is_last": False
        }

    def listen(self, input_queue):
        self.s2t.start(input_queue, self.command_queue, self.speaking_event, self.interrupt_event)
        # query = self.s2t.start_vosk(callback)
        # return query

    def stop(self):
        self.queue.value = {
            "type": "stopping",
            "stop": True,
            "img_name": self.silence_key,
            "is_last": True
        }
        self.command_queue.put("stop")
