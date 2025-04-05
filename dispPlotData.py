import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse
from scipy.integrate import cumtrapz
from scipy.signal import butter, filtfilt
SAMPLE_RATE = 500
# Define a high-pass filter to remove drift
def highpass_filter(data, cutoff=0.1, fs=SAMPLE_RATE, order=2):
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype='high', analog=False)
    return filtfilt(b, a, data)

def compute_displacement(accel_data, sampling_rate=SAMPLE_RATE):
    """ Compute displacement from acceleration using numerical integration. """
    
    # Convert acceleration from g to m/s²
    g_to_m_s2 = 9.81  # Gravity constant
    accel_data["X (m/s²)"] = accel_data["X (g)"] * g_to_m_s2
    accel_data["Y (m/s²)"] = accel_data["Y (g)"] * g_to_m_s2
    accel_data["Z (m/s²)"] = accel_data["Z (g)"] * g_to_m_s2

    dt = 1 / sampling_rate  # Time step

    # Compute velocity by integrating acceleration
    accel_data["Vx (m/s)"] = cumtrapz(accel_data["X (m/s²)"], dx=dt, initial=0)
    accel_data["Vy (m/s)"] = cumtrapz(accel_data["Y (m/s²)"], dx=dt, initial=0)
    accel_data["Vz (m/s)"] = cumtrapz(accel_data["Z (m/s²)"], dx=dt, initial=0)

    # Apply high-pass filter to remove drift
    # accel_data["Vx (m/s)"] = highpass_filter(accel_data["Vx (m/s)"], cutoff=0.1, fs=sampling_rate)
    # accel_data["Vy (m/s)"] = highpass_filter(accel_data["Vy (m/s)"], cutoff=0.1, fs=sampling_rate)
    # accel_data["Vz (m/s)"] = highpass_filter(accel_data["Vz (m/s)"], cutoff=0.1, fs=sampling_rate)

    # Compute displacement by integrating velocity
    accel_data["Dx (m)"] = highpass_filter(cumtrapz(accel_data["Vx (m/s)"], dx=dt, initial=0), cutoff=0.1, fs=sampling_rate)
    accel_data["Dy (m)"] = highpass_filter(cumtrapz(accel_data["Vy (m/s)"], dx=dt, initial=0), cutoff=0.1, fs=sampling_rate)
    accel_data["Dz (m)"] = highpass_filter(cumtrapz(accel_data["Vz (m/s)"], dx=dt, initial=0), cutoff=0.1, fs=sampling_rate)

    return accel_data

def plot_displacement(csv_filename, sampling_rate=SAMPLE_RATE):
    """ Read accelerometer data, compute displacement, and plot. """
    
    # Load CSV file into a DataFrame
    try:
        accel_data = pd.read_csv(csv_filename)
    except FileNotFoundError:
        print(f"Error: File '{csv_filename}' not found.")
        return
    except pd.errors.EmptyDataError:
        print(f"Error: File '{csv_filename}' is empty.")
        return

    # Check if required columns exist
    if not {"X (g)", "Y (g)", "Z (g)"}.issubset(accel_data.columns):
        print(f"Error: CSV file is missing expected columns. Found: {list(accel_data.columns)}")
        return

    # Compute displacement
    accel_data = compute_displacement(accel_data, SAMPLE_RATE)

    # Plot displacement
    plt.figure(figsize=(10, 6))
    plt.plot(accel_data.index, accel_data["Dx (m)"], label="X Displacement (m)")
    plt.plot(accel_data.index, accel_data["Dy (m)"], label="Y Displacement (m)")
    plt.plot(accel_data.index, accel_data["Dz (m)"], label="Z Displacement (m)")

    # Configure plot labels and legend
    plt.xlabel("Sample Index")
    plt.ylabel("Displacement (m)")
    plt.title("Accelerometer Displacement Over Time")
    plt.legend()
    plt.grid(True)

    # Show the plot
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot displacement from accelerometer data.")
    parser.add_argument("csv_filename", type=str, help="Path to the CSV file to plot")
    args = parser.parse_args()

    plot_displacement(args.csv_filename)

