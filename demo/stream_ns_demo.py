#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import os
import wave
from ctypes import *

import numpy as np

ll = cdll.LoadLibrary

lib = ll("./_simple_ns.so")
lib.webrtc_nsx_create.restype = c_void_p
webrtc_nsx = lib.webrtc_nsx_create(2)


def ns_process(pcm_str):
    """
    :param pcm_str: pcm字节流
    :return: 降噪后的pcm字节流
    :rtype: str
    """
    data = np.frombuffer(pcm_str, dtype=np.int16)
    nframes = len(data)
    window = 80
    cycle = nframes // window
    pcm_after_ns_all = np.zeros(nframes).astype(np.int16)
    chunk_after_ns = np.zeros((window)).astype(np.int16)
    for i in range(cycle):
        chunk = data[i * window:(i + 1) * window]
        chunk_arr = (c_short * window)(*chunk)
        chunk_after_ns_arr = (c_short * window)(*chunk_after_ns)
        lib.webrtc_nsx_process(webrtc_nsx, chunk_arr, chunk_after_ns_arr)
        for j in range(window):
            pcm_after_ns_all[j + i * window] = chunk_after_ns_arr[j]
    # TODO 感觉下面是多余的，应该不会存在非80整数倍的情况
    remainder = nframes % window
    if remainder > 0:
        chunk = data[-remainder:]
        for i in range(remainder):
            pcm_after_ns_all[i - remainder] = chunk[i]
    return pcm_after_ns_all.tostring()


def save_pcm_2_wav(pcm_str, out_name):
    wave_out = wave.open(out_name, 'wb')
    wave_out.setnchannels(1)
    wave_out.setsampwidth(2)
    wave_out.setframerate(8000)
    wave_out.writeframes(pcm_str)
    wave_out.close()


if __name__ == '__main__':
    wav_path = "wavs"
    out_path = "out"
    files = os.listdir(wav_path)
    for file in files:
        if not os.path.isdir(file):
            path_file = os.path.join(wav_path, file)
            f_in = open(path_file)
            f_in.seek(0)
            f_in.read(44)
            pcm_str = f_in.read()
            data_out = ns_process(pcm_str)
            out_name = os.path.join(out_path, file)

            save_pcm_2_wav(data_out, out_name)
