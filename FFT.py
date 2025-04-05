import numpy as np
import pathlib
from readData import convert_dat_to_csv
import pyfftw


# --- Input Parameters ---
# Replace this with your actual sampling rate in Hz
sampling_rate = 800  # Hz
data_dir = "data/"
save_dir = "fft/"



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
        freqs = np.fft.fftfreq(len(data), d=1/sampling_rate)



        # Perform FFT on csv


if __name__ == "__main__":
    main()