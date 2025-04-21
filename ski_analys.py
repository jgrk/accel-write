"""
Script intended for a basic fast-fourier-transform (FFT).
Results are dB-scaled
"""
import dataclasses
import weakref
# TODO: add so that the second accel is treated accordingly to its angle to the plane

from typing import Iterable, Callable, Any

import argparse
import os
import numpy as np
import pathlib
import re
import logging

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
_records = weakref.WeakValueDictionary()


class DataRecord:
    def __init__(self, path_str:str):
        x=path_str.split("/")
        self.root: str = x[0]
        self.method: str = x[1]
        self.record: str = x[2]
        self.accel: str = x[3]
        self.coord: str = x[4]
        self.part: str = x[5]
        self.skier: str = "Hanna" if int(self.record.strip("record_")) < 10 else "Erik"


def load_csv(file_name: str):
    """Load CSV file and return the data."""
    try:
        data = np.loadtxt(file_name, delimiter=",", skiprows=1)
        return data
    except Exception as e:
        print(f"Error loading CSV file: {e}")
        return None


def simple_segmentation(data: np.array, params):
    """
    Split data into segments.
    """
    return np.split(data, params["n_splits"])


def stack_data(accel_data: Iterable[ndarray[float]]):
    """
    Takes simultaneously generated accel data records of different sizes and
    stacks them into a single numpy array by interpolation.

    accel_data: Array of simultaneously generated accel data records.
    returns: Stacked numpy array.
    """

    N = 0
    for record in accel_data:
        if record.size > N:
            N = record.size

    for record in accel_data:
        if record.size < N:
            pass


def envelope_enhancer(data: np.array, params):
    """
    the standard enhancer utilizes scipy envelope to wrap the data into a smooth function.
    after enveloping, segments are found by local maxima.
    """
    n_out = params["n_out"]
    width = params["width"]
    env, res = envelope(z=data, n_out=n_out)
    env = env + res
    peak_indices, props = find_peaks(env, width=width)
    left_bases = props["left_bases"]
    right_bases = props["right_bases"]
    adj_left_bases = left_bases * int(data.size / n_out)  # should be an int right?
    adj_right_bases = right_bases * int(data.size / n_out)
    return [data[x0:x1] for x0, x1 in zip(adj_left_bases, adj_right_bases)]


def savgol_helper(data: ndarray[Any], params):
    """
    savgol wrapper for enhanced_fft.
    When passing savgol_helper to enhanced_fft, make sure to include required kwargs!
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
    save_path: str = "enhanced_fft",
    enhance_method: Callable[
        [Iterable[float], ...], Iterable[np.array]
    ] = simple_segmentation,
    freq_lim: int = None,
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


    for idx, col in enumerate(data.T[:3]):
        coord = coords[idx]

        # for each coordinate, segment apropriatly
        enhanced_data = enhance_method(col, params)
        for j, sub_data in enumerate(enhanced_data):
            # perform FFT on sub_data
            if freq_lim is None:
                freq_lim = sub_data.shape[0] // 2
            fft = np.fft.fft(sub_data)[:freq_lim]
            freqs = np.fft.fftfreq(sub_data.shape[0], d=dt)[:freq_lim]
            mag = np.abs(fft)
            save_str = f"{save_path}/{enhance_method.__name__}/record_{record}/ac_{accel}/{coord}/"
            if not os.path.exists(save_str):
                os.makedirs(save_str)
            save_str = save_str + f"part_{j}.csv"
            combined = np.column_stack((freqs, mag))
            np.savetxt(save_str, combined, delimiter=",", header="freq,mag"),


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
