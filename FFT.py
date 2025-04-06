import numpy as np
import pathlib
from readData import convert_dat_to_csv
from matplotlib import pyplot as plt
import pyfftw


# --- Input Parameters ---
# Replace this with your actual sampling rate in Hz
sampling_rate = 800  # Hz
data_dir = "data/"
save_dir = "fft/"
dt = 1/sampling_rate



def perform_FFT(file_name: str):
    pass

def load_csv(file_name: str):
    """Load CSV file and return the data."""
    try:
        data = np.loadtxt(file_name, delimiter=',', skiprows=1)
        return data
    except Exception as e:
        print(f"Error loading CSV file: {e}")
        return None


def main():
    for file in pathlib.Path(data_dir).glob("*.dat"):
        # convert data

        dat_filename = f"{data_dir}{file.name}"
        convert_dat_to_csv(dat_filename)
        csv_filename = f"{data_dir}{file.name.replace('dat', 'csv')}"
        # Load CSV file
        data = np.loadtxt(csv_filename, delimiter=',', skiprows=1)
        N = len(data)
        freqs = np.fft.fftfreq(N, d=dt)[:len(data) // 2]
        fft_x = np.fft.fft(data[:,0])
        fft_y = np.fft.fft(data[:,1])
        fft_z = np.fft.fft(data[:,2])
        mag_x = 20 * np.log10( np.abs(fft_x) / np.max(np.abs(fft_x)) + 1e-12 )[:len(data) // 2]
        mag_y = 20 * np.log10( np.abs(fft_y) / np.max(np.abs(fft_y)) + 1e-12 )[:len(data) // 2]
        mag_z = 20 * np.log10( np.abs(fft_z) / np.max(np.abs(fft_z)) + 1e-12 )[:len(data) // 2]

        #fft_x_ms2 = np.fft.rfft(data[:,3])
        #fft_x_ms2 = np.fft.rfft(data[:,4])
        #fft_x_ms2 = np.fft.rfft(data[:,5])

        for vals in [(mag_x, 'x'), (mag_y, 'y'), (mag_z, 'z')]:
            plt.figure(figsize=(10, 6))
            plt.plot(freqs, vals[0], label=f"{vals[1]}-axis (g)")

            # Configure plot labels and legend
            plt.xlabel("Frequency (Hz)")
            plt.ylabel("Magnitude (dB)")
            plt.title("Accelerometer Data Frequency domain")
            plt.legend()
            plt.grid(True)

            plt.savefig(f"{save_dir}{vals[1]}/{file.name.replace('dat', 'png')}")
            # Perform FFT on csv


if __name__ == "__main__":
    main()