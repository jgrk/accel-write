"""
Tools for performing analysis on ski data.
"""
# TODO: add so that the second accel is treated accordingly to its angle to the plane

from typing import Iterable, Callable, Any

import argparse
import os
import numpy as np
import pathlib
import re
import logging
import json

import pandas as pd
from numpy import ndarray
from scipy.signal import savgol_filter, envelope, find_peaks, detrend, windows


from readData import convert_dat_to_csv
from matplotlib import pyplot as plt
from dataclasses import dataclass

sampling_rate = 800  # data from accel generated with a rate of 800 Hz
data_dir = "data/"
save_dir = "fft/"
dt = 1 / sampling_rate  # time between samples
coords = ("x", "y", "z")
logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)


class DataRecord:
    """
    Struct for storing data and metadata
    """
    def __init__(self, json_file:str):

        with open(json_file, 'r') as f:
            json_data = json.load(f)

        self.metadata = json_data["metadata"]
        self.n = len(json_data["data"])
        self.data = json_data["data"]
        self.freqs, self.mags = zip(*self.data)
        self.record = self.metadata["record"]
        self.coord = self.metadata["coord"]
        self.accel = self.metadata["accel"]
        self.part = self.metadata["part"]
        self.start_idx = self.metadata["start_idx"]
        self.end_idx = self.metadata["end_idx"]


    @property
    def freq_peak(self):
        freq, mag = zip(*self.data[5:])  # skip first points
        idx = np.argmax(mag)
        return freq[idx]

    def peaks(self, **kwargs):
        """
        Find peaks in the data
        """
        return_vals = find_peaks(self.mags[5:], **kwargs)
        return return_vals


def simple_segmentation(data: np.array, params):
    """
    Split data into segments.
    """
    return np.array_split(data, params["n_splits"])


def correlation_segmemntation(ref, data, params):
    """
    Split data into segments based on correlation with reference data.
    """
    n_splits = params["n_splits"]
    corr = np.correlate(data, ref, mode="full")
    corr = corr / np.max(corr)
    split_points = np.linspace(0, len(corr), n_splits + 1).astype(int)
    segments = [corr[split_points[i]:split_points[i + 1]] for i in range(n_splits)]
    return segments


def envelope_enhancer(data: np.array, params) -> list[tuple[Any, tuple[Any, Any]]]:
    """
    the standard enhancer utilizes scipy envelope to wrap the data into a smooth function.
    after enveloping, segments are found by local maxima.
    """
    n = data.shape[0]
    try:
        n_out = params["n_out"]
        height = params["height"]
        k = int(np.ceil(n/n_out))  # int
        if k < 400:
            k = 400
            n_out = int(np.ceil(n/k))
        width = [np.ceil(x/k) for x in params["width"]]
        prominence = params["prominence"]
    except:
        raise ValueError("Params n_out, width, prominence and height not all given")
    env, res = envelope(z=data, n_out=n_out)
    env = env + res
    peak_indices, props = find_peaks(env, width=width, prominence=prominence, height=height)
    left_bases = props["left_ips"].round().astype(int)
    right_bases = props["right_ips"].round().astype(int)
    adj_left_bases = left_bases * int(k)  # should be an int right?
    adj_right_bases = right_bases * int(k)
    return [(data[x0:x1], (x0, x1)) for x0, x1 in zip(adj_left_bases, adj_right_bases)]


def savgol_helper(data: ndarray[Any], params):
    """
    savgol wrapper for enhanced_fft.
    When passing savgol_helper to enhanced_fft make sure to include required kwargs!
    Se required kwargs below.
    """
    try:
        return savgol_filter(
            x=data,
            window_length=params["window_length"],
            polyorder=params["polyorder"],
            axis=params["axis"],
        )

    except ValueError as e:
        print("savgol filter has missing args")


def enhanced_fft(
    file: str | pathlib.Path = None,
    save_path: str = "enhanced_fft/",
    enhance_method: Callable[
        [Iterable[float], ...], Iterable[np.array]
    ] = simple_segmentation,
    filter: Callable[[ndarray[Any], ...], Any] = None,
    detrending: bool = False,
    **kwargs,
):
    """
    Performs enhanced FFT on file and saves it to disk.
    Enhance method is used to segment accel data.
    Pass a filter to smoothen out the data

    Run this over all records to systematically perform FFT with filer applied.

    :param file: Project relative path to file.
    :param save_path: Project dir to save to.
    :param enhance_method: A function that takes data and kwargs, segments that data and returns the set of segments.
    :param freq_lim: Frequency limit for segments.
    :param filter: Function must take ndarray[float] and kwargs and return filtered data.
    """
    if file is None:
        raise ValueError("arg file cannot be None")


    params = kwargs

    if isinstance(file, str):
        file = pathlib.Path(file)

    ids = re.findall(r"\d+", file.name)
    accel = ids[0]
    record = ids[1]
    data: ndarray = np.loadtxt(file, delimiter=",", skiprows=1)



    if detrending:
        data = detrend(data, axis=0)
        window_length = data.shape[0]
        window = windows.hann(window_length)
        data = data * window[:, np.newaxis]

    if filter:
        data = filter(data, params)

    index = np.arange(data.shape[0]) * 1 / sampling_rate
    data = np.column_stack([index, data])

    for idx, col in enumerate(data.T[1:4]):
        coord = coords[idx]

        # for each coordinate, segment apropriatly
        enhanced_data = enhance_method(col, params)
        for j, sub_data in enumerate(enhanced_data):
            # perform FFT on sub_data
            segment = sub_data[0]
            interv = sub_data[1]
            freq_lim = segment.shape[0] // 2
            fft = np.fft.fft(segment)[:freq_lim]
            freqs = np.fft.fftfreq(segment.shape[0], d=dt)[:freq_lim]
            mag = np.abs(fft)
            save_str = f"{enhance_method.__name__}-record_{record}-ac_{accel}-{coord}-part_{j}.json"
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            combined = np.column_stack((freqs, mag))
            json_data = {
                "metadata": {
                    "coord": coord,
                    "record": record,
                    "accel": accel,
                    "part": j,
                    "start_idx": str(interv[0]),
                    "end_idx": str(interv[1]),
                    **params
                },

                "data": combined.tolist(),

            }
            with open(save_path+save_str, "w") as f:
                json.dump(json_data, f)
            # np.savetxt(save_str, combined, delimiter=",", header="freq,mag"),


def fft(data_path="data/", **kwargs):
    """
    Run operations on all data records.
    data_path: path to the data directory
    """

    for file in pathlib.Path(data_path).glob("*.csv"):
        enhanced_fft(file, **kwargs)
        pass


def main():
    fft(freq_lim=100)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="ski analysis", description="Analysis on ski data"
    )
    parser.add_argument(
        "--data_dir", type=str, default=data_dir, help="Path to the data directory"
    )
    parser.add_argument(
        "--save_dir",
        type=str,
        default=save_dir,
        help="Path to the directory where the results will be saved",
    )
    parser.add_argument(
        "--freq_lim", type=int, default=None, help="Frequency limit for the FFT results"
    )
    parser.add_argument("")