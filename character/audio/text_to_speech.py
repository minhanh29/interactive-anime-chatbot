import string
import librosa
# from nix.models.TTS import NixTTSInference
import sounddevice as sd
import unicodedata
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Mapping, Optional, Sequence, Union
import numpy as np
import onnxruntime
# from espeak_phonemizer import Phonemizer
from functools import partial
import logging
import logging.config
from phonemizer.backend import EspeakBackend


BANG_XOA_DAU = str.maketrans(
    "ÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÈÉẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴáàảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ",
    "A"*17 + "D" + "E"*11 + "I"*5 + "O"*17 + "U"*11 + "Y"*5 + "a"*17 + "d" + "e"*11 + "i"*5 + "o"*17 + "u"*11 + "y"*5
)


def xoa_dau(txt: str) -> str:
    if not unicodedata.is_normalized("NFC", txt):
        txt = unicodedata.normalize("NFC", txt)
    return txt.translate(BANG_XOA_DAU)


_FILE = Path(__file__)
_DIR = _FILE.parent

FORMAT = "%(levelname)s:%(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
model = None
synthesize = None
_BOS = "^"
_EOS = "$"
_PAD = "_"


@dataclass
class PiperConfig:
    num_symbols: int
    num_speakers: int
    sample_rate: int
    espeak_voice: str
    length_scale: float
    noise_scale: float
    noise_w: float
    phoneme_id_map: Mapping[str, Sequence[int]]


class Piper:
    def __init__(
        self,
        model_path: Union[str, Path],
        config_path: Optional[Union[str, Path]] = None,
        use_cuda: bool = False,
    ):
        if config_path is None:
            config_path = f"{model_path}.json"

        self.config = load_config(config_path)
        # self.phonemizer = Phonemizer(self.config.espeak_voice)
        self.phonemizer = EspeakBackend(
            language='en-uk-rp',
            preserve_punctuation = True,
            with_stress = True,
            language_switch="remove-flags"
        )

        self.model = onnxruntime.InferenceSession(
            str(model_path),
            sess_options=onnxruntime.SessionOptions(),
        providers=[
            # ("CUDAExecutionProvider", {"cudnn_conv_algo_search": "DEFAULT"}),
            "CPUExecutionProvider"
        ],
        )

    def synthesize(
        self,
        text: str,
        speaker_id: Optional[int] = None,
        length_scale: Optional[float] = None,
        noise_scale: Optional[float] = None,
        noise_w: Optional[float] = None,
    ) -> bytes:
        """Synthesize WAV audio from text."""
        if length_scale is None:
            length_scale = self.config.length_scale

        if noise_scale is None:
            noise_scale = self.config.noise_scale

        if noise_w is None:
            noise_w = self.config.noise_w

        phonemes_str = self.phonemizer.phonemize(text)
        phonemes = [_BOS] + list(phonemes_str)
        phoneme_ids: List[int] = []

        for phoneme in phonemes:
            if phoneme not in self.config.phoneme_id_map:
                continue
            phoneme_ids.extend(self.config.phoneme_id_map[phoneme])
            phoneme_ids.extend(self.config.phoneme_id_map[_PAD])

        phoneme_ids.extend(self.config.phoneme_id_map[_EOS])

        phoneme_ids_array = np.expand_dims(np.array(phoneme_ids, dtype=np.int64), 0)
        phoneme_ids_lengths = np.array([phoneme_ids_array.shape[1]], dtype=np.int64)
        scales = np.array(
            [noise_scale, length_scale, noise_w],
            dtype=np.float32,
        )

        # if (self.config.num_speakers > 1) and (speaker_id is not None):
        #     # Default speaker
        #     speaker_id = 0

        sid = None

        if speaker_id is not None:
            sid = np.array([speaker_id], dtype=np.int64)

        # Synthesize through Onnx
        audio = self.model.run(
            None,
            {
                "input": phoneme_ids_array,
                "input_lengths": phoneme_ids_lengths,
                "scales": scales,
                "sid": sid,
            },
        )[0].squeeze((0, 1))
        audio = audio_float_to_int16(audio.squeeze())
        return audio, self.config.sample_rate

def load_config(config_path: Union[str, Path]) -> PiperConfig:
    with open(config_path, "r", encoding="utf-8") as config_file:
        config_dict = json.load(config_file)
        inference = config_dict.get("inference", {})

        return PiperConfig(
            num_symbols=config_dict["num_symbols"],
            num_speakers=config_dict["num_speakers"],
            sample_rate=config_dict["audio"]["sample_rate"],
            espeak_voice=config_dict["espeak"]["voice"],
            noise_scale=inference.get("noise_scale", 0.667),
            length_scale=inference.get("length_scale", 1.0),
            noise_w=inference.get("noise_w", 0.8),
            phoneme_id_map=config_dict["phoneme_id_map"],
        )


def audio_float_to_int16(
    audio: np.ndarray, max_wav_value: float = 32767.0
) -> np.ndarray:
    """Normalize audio and convert to int16 range"""
    target_db = 1
    max_abs_amplitude = np.max(np.abs(audio))
    scaling_factor = 10 ** (target_db / 20) / max_abs_amplitude
    audio_norm = audio * scaling_factor
    # # print(audio_norm)
    # print(np.max(audio_norm))
    # print(np.min(audio_norm))

    # audio_norm = audio * (max_wav_value / max(0.01, np.max(np.abs(audio))))
    # audio_norm = np.clip(audio_norm, -max_wav_value, max_wav_value)
    # audio_norm = audio_norm.astype("int16")
    return audio_norm


def load_model():
    global synthesize
    if synthesize:
        return synthesize
    model = 'checkpoints/kiriha-gb.onnx'
    config_path = "./checkpoints/kiriha-gb.onnx.json"
    # model = 'checkpoints/keqing1.onnx'
    # config_path = "./checkpoints/keqing.onnx.json"
    speaker_id = None
    voice = Piper(model, config_path=config_path)
    synthesize = partial(
        voice.synthesize,
        speaker_id=speaker_id,
        length_scale=None,
        noise_scale=0.0,
        noise_w=0.0,)
    logging.debug("Model loaded.")
    return synthesize


class MyTTS:
    def __init__(self):
        self.model = load_model()

    def speak(self, text):
        text = xoa_dau(text)
        print(text)
        text = text.replace("?", ".").replace("!", ".").replace(";", ".")
        lines = [line.strip() for line in text.split(".")]
        for i, line in enumerate(lines):
            line = line.translate(str.maketrans('', '', "!\"#$%&\'()*+-./:;<=>?[\\]^_`{|}~")).strip()
            if line == "":
                continue

            audio_norm, sample_rate = self.model(line)
            if i > 0:
                sd.wait()
            sd.play(audio_norm, sample_rate)

