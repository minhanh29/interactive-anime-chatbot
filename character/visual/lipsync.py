import os
import math
import librosa
import numpy as np
import cv2
import json
import sounddevice as sd

img_dir = "./anime/lips"
img_names = ["aeil", "bmpfv", "cdnkgstxyz", "ouwq"]
silence_key = img_names[1]
transition_keys = ["aeil-bmpfv", "bmpfv-cdnkgstxyz", "bmpfv-ouwq", "bmpfv-smile", "cdnkgstxyz-ouwq"]
img_map = {}
for img_name in img_names + transition_keys:
    img_map[img_name] = cv2.imread(os.path.join(img_dir, img_name + ".png"))
transition_keys = set(transition_keys)


# features
feature_arr = np.load("./features.npy")
with open("./feature_map.json", "r") as f:
    feature_map = json.load(f)["data"]


y, sr = librosa.load("./test.wav")
window_size = 4410
prev_key = silence_key
img_name_sequence = []
for i in range(math.ceil(len(y) / window_size)):
    sample = y[i*window_size:min((i+1)*window_size, len(y))]
    S = np.abs(librosa.stft(sample))
    S = np.mean(S, axis=-1)

    if np.max(S) < 20:  # silence
        img_name = silence_key
    else:
        min_val = np.min(S)
        max_val = np.max(S)
        S = (S - min_val) / (max_val - min_val)
        distances = np.sqrt(np.sum(np.power(S - feature_arr, 2), axis=-1))
        idx = np.argmin(distances)
        img_name = feature_map[idx]

    if prev_key == img_name:
        transition_key = prev_key
    else:
        transition_key = [prev_key, img_name]
        transition_key.sort()
        transition_key = "-".join(transition_key)
    img_name_sequence.append(transition_key)
    img_name_sequence.append(img_name)

sd.play(y, sr)
for img_name in img_name_sequence:
    img = img_map[img_name]
    cv2.imshow("Serena", img)
    cv2.waitKey(100)

