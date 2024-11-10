import numpy as np
import random
import os
from glob import glob
import cv2
from multiprocessing import Queue


def render_video(data_dir, queue):
    lip_img_dir = os.path.join(data_dir, "lips")
    eye_img_dir = os.path.join(data_dir, "eyes")
    frame_dir = os.path.join(data_dir, "frames")
    frame_names = glob(os.path.join(frame_dir, "*.png"))
    frame_names.sort()
    frame_list = []
    for img_path in frame_names:
        img = cv2.imread(img_path)
        frame_list.append(img)

    # affine transformation
    eye_matrices = np.load(os.path.join(data_dir, "affine_eye_matrices.npy"))
    lip_matrices = np.load(os.path.join(data_dir, "affine_lip_matrices.npy"))

    # eyes
    eye_img_names = ["lv0", "lv1", "lv2", "lv3", "lv4"]
    eye_y1 = 200
    eye_y2 = 290
    eye_x1 = 210
    eye_x2 = 430
    eye_img_list = []
    eye_alpha_list = []
    eye_kernel = np.ones((2, 2), np.uint8)
    for img_name in eye_img_names:
        img = cv2.imread(
            os.path.join(eye_img_dir, img_name + ".png"),
            cv2.IMREAD_UNCHANGED
        )
        img = img[eye_y1:eye_y2, eye_x1:eye_x2]
        alpha = img[:, :, 3].copy()
        img = img[:, :, :3]

        eye_img_list.append(img)
        eye_alpha_list.append(alpha)

    # lips
    lip_y1 = 300
    lip_y2 = 340
    lip_x1 = 280
    lip_x2 = 345
    img_names = ["aeil", "bmpfv", "cdnkgstxyz", "ouwq"]
    silence_key = img_names[1]
    transition_keys = ["aeil-bmpfv", "bmpfv-cdnkgstxyz", "bmpfv-ouwq", "bmpfv-smile", "cdnkgstxyz-ouwq"]
    img_map = {}
    lip_kernel = np.ones((5, 5), np.uint8)
    for i, img_name in enumerate(img_names + transition_keys):
        img = cv2.imread(os.path.join(lip_img_dir, img_name + ".png"))[lip_y1:lip_y2, lip_x1:lip_x2]
        alpha = (np.ones_like(img) * 255).astype("uint8")
        alpha[:2] = 0
        alpha[-2:] = 0
        alpha[:, :2] = 0
        alpha[:, -2:] = 0
        img_map[img_name] = [img, alpha]

    waitTime = 10
    frame_cnt = 0
    frame_idx = 0
    frame_waitTime = waitTime * 2

    # eye config
    eye_waitTime = waitTime * 2
    eye_frame_cnt = 0
    eye_img_idx = 0
    eye_direction = 1
    blink = False

    thinking = False
    while True:
        frame_cnt += waitTime
        img = frame_list[frame_idx].copy()
        # y_offset, x_offset = offset[frame_idx]
        payload = queue.value
        if payload is None:
            img_name = silence_key
        else:
            if payload["stop"]:
                break

            if payload["type"] == "thinking":
                thinking = True
            elif payload["type"] == "idling":
                thinking = False
            else:
                thinking = False
                img_name = payload["img_name"]
                # if payload["is_last"]:
                #     lip_waitTime = waitTime
                # else:
                #     lip_waitTime = waitTime * lip_scale

        lip_img, lip_alpha = img_map[img_name]
        lip_img, lip_alpha = lip_img.copy(), lip_alpha.copy()
        lip_img = cv2.warpAffine(lip_img, lip_matrices[frame_idx], (lip_img.shape[1], lip_img.shape[0]))
        lip_alpha = cv2.warpAffine(lip_alpha, lip_matrices[frame_idx], (lip_alpha.shape[1], lip_alpha.shape[0]), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
        lip_alpha = cv2.erode(lip_alpha, lip_kernel, iterations=2)
        lip_alpha = lip_alpha[:, :, :1].astype(np.float32) / 255.0
        base_crop = img[lip_y1:lip_y2, lip_x1:lip_x2]
        img[lip_y1:lip_y2, lip_x1:lip_x2] = (base_crop * (1 - lip_alpha) + lip_img * lip_alpha).astype("uint8")

        # determine to blink or not
        eye_frame_cnt += waitTime
        if not blink:
            if eye_frame_cnt > 500 and random.random() > 0.8:
                blink = True  # blink next iteration
                eye_frame_cnt = eye_waitTime
            eye_img = eye_img_list[0]
            eye_alpha = eye_alpha_list[0]
        else:
            # blink
            eye_img = eye_img_list[eye_img_idx]
            eye_alpha = eye_alpha_list[eye_img_idx]

            if eye_frame_cnt >= eye_waitTime:
                eye_frame_cnt = 0

                if eye_img_idx == len(eye_img_list) - 1:
                    eye_direction = -1

                if eye_img_idx == 0:
                    eye_direction = 1
                    blink = False

                eye_img_idx += eye_direction

        if thinking:
            eye_img = eye_img_list[-1]
            eye_alpha = eye_alpha_list[-1]

        eye_img = cv2.warpAffine(eye_img, eye_matrices[frame_idx], (eye_img.shape[1], eye_img.shape[0]))
        eye_alpha = cv2.warpAffine(eye_alpha, eye_matrices[frame_idx], (eye_alpha.shape[1], eye_alpha.shape[0]))
        eye_alpha = cv2.erode(eye_alpha, eye_kernel, iterations=1)
        eye_alpha = eye_alpha[:, :, np.newaxis].astype(np.float32) / 255.0
        base_crop = img[eye_y1:eye_y2, eye_x1:eye_x2]
        img[eye_y1:eye_y2, eye_x1:eye_x2] = (base_crop * (1 - eye_alpha) + eye_img * eye_alpha).astype("uint8")

        if frame_cnt >= frame_waitTime:
            frame_cnt = 0
            frame_idx = (frame_idx + 1) % len(frame_list)

        cv2.imshow("Serena", img)
        cv2.waitKey(waitTime)
