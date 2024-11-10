import whisper
from threading import Event
import os
import pickle
import numpy as np
import torch
import torchaudio
import pyaudio
from scipy.io.wavfile import read, write
import io
from queue import Queue
from google.cloud import speech
torch.set_num_threads(1)
torchaudio.set_audio_backend("soundfile")


# Taken from utils_vad.py
def validate(model,
             inputs: torch.Tensor):
    with torch.no_grad():
        outs = model(inputs)
    return outs


# Provided by Alexander Veysov
def int2float(sound):
    abs_max = np.abs(sound).max()
    sound = sound.astype('float32')
    if abs_max > 0:
        sound *= 1/32768
    sound = sound.squeeze()  # depends on the use case
    return sound


class SpeechToText():
    def __init__(self):
        torch.hub._validate_not_a_forked_repo = lambda a, b, c: True
        model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                      model='silero_vad',
                                      onnx=True)
        self.vad_model = model
        with open("./data/character/selfvoice.pickle", "rb") as f:
            self.selfvoice_model = pickle.load(f)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./data/minhanh-personal-web-517e58fb4618.json"

    def start(self, input_queue: Queue, command_queue: Queue, speaking_event: Event, interrupt_event: Event):
        client = speech.SpeechClient()

        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
            model="latest_short"
        )

        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        SAMPLE_RATE = 16000
        CHUNK = int(SAMPLE_RATE / 10)

        audio = pyaudio.PyAudio()
        # num_samples = 1536
        num_samples = 1600

        stream = audio.open(format=FORMAT,
                            channels=CHANNELS,
                            rate=SAMPLE_RATE,
                            input=True,
                            frames_per_buffer=CHUNK,
                            input_device_index=3)

        leading_offset = 3
        data = []
        leading = []
        listening = False
        transcribe = False
        print("Idling...")
        timeout = 0
        interrupt_cnt = 0
        silent_cnt = 0
        prev_speaking = False
        while True:
            if not command_queue.empty():
                payload = command_queue.get()
                print("Get command", payload)
                if payload == "stop":
                    break

            audio_chunk = stream.read(num_samples, exception_on_overflow=False)

            audio_int16 = np.frombuffer(audio_chunk, np.int16)
            audio_float32 = int2float(audio_int16)

            leading.append(audio_chunk)
            if len(leading) > leading_offset:
                leading = leading[-leading_offset:]

            # get the confidences and add them to the list to plot them later
            new_confidence = self.vad_model(torch.from_numpy(audio_float32), 16000).item()

            if speaking_event.is_set():
                if not prev_speaking:
                    interrupt_cnt = 0
                    silent_cnt = 0

                prev_speaking = True
                if new_confidence > 0.8:
                    x = audio_float32
                    x / np.linalg.norm(x)
                    label = self.selfvoice_model.predict(np.expand_dims(x, 0))[0]
                    if label == 1:
                        print("Interrupt")
                        interrupt_cnt += 1
                        silent_cnt = 0
                    else:
                        silent_cnt += 1

                    if silent_cnt > 5:
                        interrupt_cnt = 0

                    if interrupt_cnt >= 2:
                        interrupt_cnt = 0
                        print("Send Interrupt")
                        interrupt_event.set()
                        stream.close()
                        stream = audio.open(format=FORMAT,
                                            channels=CHANNELS,
                                            rate=SAMPLE_RATE,
                                            input=True,
                                            frames_per_buffer=CHUNK)
                        # input_queue.put("Stop please")
                continue

            prev_speaking = False

            if new_confidence > 0.2:
                if not listening:
                    print("Listening...")
                    data = leading.copy()
                else:
                    data.append(audio_chunk)
                listening = True
            elif listening:  # new_confidence < 0.2 and was listening -> stop listening
                if timeout < leading_offset:
                    data.append(audio_chunk)
                    timeout += 1
                    continue

                timeout = 0
                # meet a threshold to transcribe
                if transcribe:
                    transcribe = False
                    print("Transcribing...")

                    audio_data = b"".join(data)
                    audioReg = speech.RecognitionAudio(content=audio_data)
                    response = client.recognize(config=config, audio=audioReg)

                    text = ""
                    for result in response.results:
                        print(f"Transcript: {result.alternatives[0].transcript}")
                        text = result.alternatives[0].transcript
                    print(text)
                    input_queue.put(text)

                    # reset stream
                    stream.close()
                    stream = audio.open(format=FORMAT,
                                        channels=CHANNELS,
                                        rate=SAMPLE_RATE,
                                        input=True,
                                        frames_per_buffer=CHUNK)

                print("Idling...")

                data = []
                listening = False

            if new_confidence > 0.8:
                transcribe = True
        stream.close()

    def start_whisper(self):
        asr_model = whisper.load_model("tiny.en")

        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        SAMPLE_RATE = 16000
        CHUNK = int(SAMPLE_RATE / 10)

        audio = pyaudio.PyAudio()
        # num_samples = 1536
        num_samples = 1600

        stream = audio.open(format=FORMAT,
                            channels=CHANNELS,
                            rate=SAMPLE_RATE,
                            input=True,
                            frames_per_buffer=CHUNK)

        leading_offset = 3
        wait_count = 0
        wait_time = 4
        data_np = []
        leading_np = []
        listening = False
        transcribe = False
        print("Idling...")
        timeout = 0
        while True:
            audio_chunk = stream.read(num_samples, exception_on_overflow=False)

            audio_int16 = np.frombuffer(audio_chunk, np.int16)
            audio_float32 = int2float(audio_int16)

            leading_np.append(audio_float32)
            if len(leading_np) > leading_offset:
                leading_np = leading_np[-leading_offset:]

            # get the confidences and add them to the list to plot them later
            new_confidence = self.vad_model(torch.from_numpy(audio_float32), 16000).item()

            if new_confidence > 0.2:
                if not listening:
                    print("Listening...")
                    data_np = leading_np.copy()
                else:
                    data_np.append(audio_float32)
                listening = True
            elif wait_count < wait_time:
                wait_count += 1
            elif listening:  # new_confidence < 0.2 and was listening -> stop listening
                wait_count = 0
                if timeout < leading_offset:
                    data_np.append(audio_float32)
                    timeout += 1
                    continue

                timeout = 0
                # meet a threshold to transcribe
                if transcribe:
                    transcribe = False
                    print("Transcribing...")

                    audio_data = np.concatenate(data_np)
                    print(audio_data.shape)
                    result = asr_model.transcribe(audio_data, fp16=torch.cuda.is_available())
                    text = result['text'].strip()
                    print(text)
                    if "quit" in text:
                        break
                        print("Quitting...")
                print("Idling...")

                data_np = []
                listening = False

            if new_confidence > 0.8:
                transcribe = True

    def start_vosk(self, callback):
        from vosk import Model, KaldiRecognizer
        import json

        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        SAMPLE_RATE = 16000
        CHUNK = int(SAMPLE_RATE / 10)

        # model = Model(model_name="vosk-model-small-en-us-0.15")
        model = Model(model_name="vosk-model-en-us-0.22-lgraph")
        rec = KaldiRecognizer(model, SAMPLE_RATE)

        audio = pyaudio.PyAudio()
        # num_samples = 1536
        num_samples = 1600

        stream = audio.open(format=FORMAT,
                            channels=CHANNELS,
                            rate=SAMPLE_RATE,
                            input=True,
                            frames_per_buffer=CHUNK)

        leading_offset = 3
        data = []
        leading = []
        listening = False
        transcribe = False
        print("Idling...")
        timeout = 0
        while True:
            audio_chunk = stream.read(num_samples, exception_on_overflow=False)

            audio_int16 = np.frombuffer(audio_chunk, np.int16)
            audio_float32 = int2float(audio_int16)

            leading.append(audio_chunk)
            if len(leading) > leading_offset:
                leading = leading[-leading_offset:]

            # get the confidences and add them to the list to plot them later
            new_confidence = self.vad_model(torch.from_numpy(audio_float32), 16000).item()

            if new_confidence > 0.2:
                if not listening:
                    print("Listening...")
                    data = leading.copy()
                else:
                    data.append(audio_chunk)
                listening = True
            elif listening:  # new_confidence < 0.2 and was listening -> stop listening
                if timeout < leading_offset:
                    data.append(audio_chunk)
                    timeout += 1
                    continue

                timeout = 0
                # meet a threshold to transcribe
                if transcribe:
                    transcribe = False
                    print("Transcribing...")

                    audio_data = b"".join(data)
                    rec.AcceptWaveform(audio_data)
                    text = json.loads(rec.Result())['text']
                    _continue = callback(text)
                    if not _continue:
                        break

                print("Idling...")

                data = []
                listening = False

            if new_confidence > 0.8:
                transcribe = True


if __name__ == "__main__":
    s2t = SpeechToText()
    s2t.start()
