"""
Script intended for a basic fast-fourier-transform (FFT).
Results are dB-scaled
"""

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
from scipy.signal import savgol_filter, envelope, find_peaks


from readData import convert_dat_to_csv
from matplotlib import pyplot as plt

sampling_rate = 800  # data from accel generated with a rate of 800 Hz
data_dir = "data/"
save_dir = "fft/"
dt = 1 / sampling_rate  # time between samples
coords = ('x', 'y', 'z')
logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)


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
    return np.split(data, params['n_splits'])


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


def envelope_enhancer(data: ndarray[float], n_out = 100, width = (2, 5)):
    """

    the standard enhancer utilizes scipy envelope to wrap the data into a smooth function.
    after enveloping, segments are found by local maxima.
    """
    env, res = envelope(z=data, n_out=n_out)
    env = env + res
    peak_indices, props = find_peaks(env, width=width)
    left_bases = props['left_bases']
    right_bases = props['right_bases']
    adj_left_bases = left_bases*int(data.size/n_out) # should be an int right?
    adj_right_bases = right_bases*int(data.size/n_out)
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
            window_length=params['window_length'],
            polyorder=params['polyorder'],
            axis=params['axis'],
        )

    except ValueError as e:
        print("savgol filter has missing args")


def enhanced_fft(
    file: str | pathlib.Path = None,
    save_path: str = "enhanced_fft",
    enhance_method: Callable[[Iterable[float], ...], Iterable[np.array]] = simple_segmentation,
    freq_lim: int = None,
    filter: Callable[[ndarray[Any], ...], Any] = None,
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

    ids = re.findall(r'\d+', file.name)
    accel = ids[0]
    record = ids[1]
    data = np.loadtxt(file, delimiter=",", skiprows=1)

    if filter is not None:
        data = filter(data, params)

    for idx, col in enumerate(data.T[:3]):
        coord = coords[idx]
        # for each coordinate, segment apropriatly
        enhanced_data = enhance_method(col, params)
        for j, sub_data in enumerate(enhanced_data):
            # perform FFT on sub_data
            if freq_lim is None:
                freq_lim = sub_data.size // 2
            fft = np.fft.fft(sub_data)[:freq_lim]
            freqs = np.fft.fftfreq(sub_data.size, d=dt)[:freq_lim]
            mag = np.abs(fft)
            save_str = f'{save_path}/{enhance_method.__name__}/record_{record}/ac_{accel}/{coord}/'
            if not os.path.exists(save_str):
                os.makedirs(save_str)
            save_str = save_str + f"part_{j}.csv"
            combined = np.column_stack((freqs, mag))
            np.savetxt(save_str, combined, delimiter=",", header = "freq,mag"),


def fft(data_path="data/", save_path="fft/", freq_lim=None, scaling=False):
    """
    Run FFT on all data records.
    data_path: path to the data directory
    save_path: path to the directory where the results will be saved
    freq_lim: frequency limit for the FFT results
    """

    for file in pathlib.Path(data_path).glob("*.dat"):
        dat_filename = f"{data_path}{file.name}"
        convert_dat_to_csv(dat_filename)
        csv_filename = f"{data_path}{file.name.replace('dat', 'csv')}"

        data = np.loadtxt(csv_filename, delimiter=",", skiprows=1)
        N = len(data)
        if freq_lim is None:
            freq_lim = len(data) // 2
        else:
            freq_lim = int((freq_lim / sampling_rate) * len(data))

        freqs = np.fft.fftfreq(N, d=dt)[:freq_lim]  # freq > sampling_rate / 2

        # FFT-vals
        fft_x = np.fft.fft(data[:, 0])
        fft_y = np.fft.fft(data[:, 1])
        fft_z = np.fft.fft(data[:, 2])

        mag_x = np.abs(fft_x)
        mag_y = np.abs(fft_y)
        mag_z = np.abs(fft_z)

        if scaling:
            mag_x = (
                20 * np.log10(np.abs(fft_x) / np.max(np.abs(fft_x)) + 1e-12)[:freq_lim]
            )  #
            mag_y = (
                20 * np.log10(np.abs(fft_y) / np.max(np.abs(fft_y)) + 1e-12)[:freq_lim]
            )
            mag_z = (
                20 * np.log10(np.abs(fft_z) / np.max(np.abs(fft_z)) + 1e-12)[:freq_lim]
            )

        # saving results
        for vals in [(mag_x, "x"), (mag_y, "y"), (mag_z, "z")]:
            plt.figure(figsize=(10, 6))
            plt.plot(freqs, vals[0], label=f"{vals[1]}-axis (g)")

            plt.xlabel("Frequency (Hz)")
            plt.ylabel("Magnitude (dB)")
            plt.title("Accelerometer Data Frequency domain")
            plt.legend()
            plt.grid(True)

            save_to_dir = f"{save_path}{vals[1]}/"
            if not os.path.exists(save_to_dir):
                os.makedirs(save_to_dir)
            plt.savefig(f"{save_to_dir}{file.name.replace('dat', 'png')}")


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
