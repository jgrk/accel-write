"""
Script intended for a basic fast-fourier-transform (FFT).
Results are dB-scaled
"""

# TODO: add so that the second accel is treated accordingly to its angle to the plane

from typing import Iterable, Callable

import argparse
import os
import numpy as np
import pathlib

import pandas as pd
from numpy import ndarray
from scipy.signal import savgol_filter

from dispPlotData import SAMPLE_RATE
from readData import convert_dat_to_csv
from matplotlib import pyplot as plt

sampling_rate = 800  # data from accel generated with a rate of 800 Hz
data_dir = "data/"
save_dir = "fft/"
dt = 1 / sampling_rate  # time between samples


def load_csv(file_name: str):
    """Load CSV file and return the data."""
    try:
        data = np.loadtxt(file_name, delimiter=",", skiprows=1)
        return data
    except Exception as e:
        print(f"Error loading CSV file: {e}")
        return None


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


def std_enhancer():
    pass


def for_all_files(func):
    def wrapper(*args, **kwargs):
        # TODO: loop over all files in direcory and run func
        result = func(*args, **kwargs)
        # do something with results

    return wrapper


def savgol_helper(data: ndarray[float], kwargs):
    return savgol_filter(
        x=data,
        window_length=kwargs["window_length"],
        polyorder=kwargs["order"],
        axis=kwargs["axis"],
    )


@for_all_files
def enhanced_fft(
    file_dir: str = None,
    save_path: str = "enhanced_fft/",
    time_frame: float = 0.5,
    enhance_method: Callable[[Iterable[float], ...], Iterable[np.array]] = std_enhancer,
    freq_lim: int = None,
    filter: Callable[..., Iterable[float]] = None,
    **kwargs,
):
    """
    Perform enhanced FFT
    """

    if file_dir is None:
        raise ValueError("file_dir cannot be None")

    data = np.loadtxt(file_dir, delimiter=",", skiprows=1)

    if filter is not None:
        data = filter(data, kwargs)

    # for each coordinate, segment apropriatly
    for col in data.T:
        enhanced_data = enhance_method(col, kwargs)
        for sub_data in enhanced_data:
            # perform FFT on sub_data
            if freq_lim is None:
                freq_lim = sub_data.size // 2
            freqs = np.fft.fftfreq(sub_data.size, d=dt)[:freq_lim]
            # TODO: add coordinate meta info, structured saved functionality.


def simple_segmentation(data: np.array, kwargs: dict):
    """
    Split data into segments.
    """
    if "n_splits" not in kwargs:
        kwargs["n_splits"] = 1
    return np.split(data, kwargs["n_splits"])


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
