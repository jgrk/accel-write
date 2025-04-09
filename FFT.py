"""
Script intended for a basic fast-fourier-transform (FFT).
Results are dB-scaled
"""
# TODO: add so that the second accel is treated accordingly to its angle to the plane



import argparse
import os
import numpy as np
import pathlib
from readData import convert_dat_to_csv
from matplotlib import pyplot as plt

sampling_rate = 800  # data from accel generated with a rate of 800 Hz
data_dir = "data/"
save_dir = "fft/"
dt = 1/sampling_rate # time between samples


def _load_csv(file_name: str):
    """Load CSV file and return the data."""
    try:
        data = np.loadtxt(file_name, delimiter=',', skiprows=1)
        return data
    except Exception as e:
        print(f"Error loading CSV file: {e}")
        return None


def fft(data_path = "data/", save_path = "fft/", freq_lim = None, scaling = False):
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

        data = np.loadtxt(csv_filename, delimiter=',', skiprows=1)
        N = len(data)
        if freq_lim is None:
            freq_lim = len(data) // 2
        else:
            freq_lim = int( ( freq_lim / sampling_rate ) * len(data))

        freqs = np.fft.fftfreq(N, d=dt)[:freq_lim]  # freq > sampling_rate / 2

        # FFT-vals
        fft_x = np.fft.fft(data[:, 0])
        fft_y = np.fft.fft(data[:, 1])
        fft_z = np.fft.fft(data[:, 2])

        mag_x = np.abs(fft_x)
        mag_y = np.abs(fft_y)
        mag_z = np.abs(fft_z)

        if scaling:
            mag_x = 20 * np.log10( np.abs(fft_x) / np.max(np.abs(fft_x) ) + 1e-12 )[:freq_lim] #
            mag_y = 20 * np.log10(np.abs(fft_y) / np.max(np.abs(fft_y)) + 1e-12)[:freq_lim]
            mag_z = 20 * np.log10(np.abs(fft_z) / np.max(np.abs(fft_z)) + 1e-12)[:freq_lim]

        # saving results
        for vals in [(mag_x, 'x'), (mag_y, 'y'), (mag_z, 'z')]:
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
    parser = argparse.ArgumentParser(prog="ski analysis", description="Analysis on ski data")
    parser.add_argument("--data_dir", type=str, default=data_dir, help="Path to the data directory")
    parser.add_argument("--save_dir", type=str, default=save_dir, help="Path to the directory where the results will be saved")
    parser.add_argument("--freq_lim", type=int, default=None, help="Frequency limit for the FFT results")
    parser.add_argument("")
    parser.add_argument()
