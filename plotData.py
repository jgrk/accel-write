import pandas as pd
import matplotlib.pyplot as plt
import argparse
import scipy.signal as signal
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def plot_accel_data(csv_filename, filter=False):
    """Read accelerometer data from CSV and plot X, Y, Z values."""

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
        print(
            f"Error: CSV file is missing expected columns. Found: {list(accel_data.columns)}"
        )
        return

    if filter:
        for col in accel_data.columns:
            logger.info(f"Filtering '{col}'")
            accel_data[col] = signal.savgol_filter(accel_data[col], 10, 3)

    # Plot the accelerometer data
    plt.figure(figsize=(10, 6))
    plt.plot(accel_data.index, accel_data["X (g)"], label="X-axis (g)")
    plt.plot(accel_data.index, accel_data["Y (g)"], label="Y-axis (g)")
    plt.plot(accel_data.index, accel_data["Z (g)"], label="Z-axis (g)")

    # Configure plot labels and legend
    plt.xlabel("Sample Index")
    plt.ylabel("Acceleration (g)")
    plt.title("Accelerometer Data Over Time")
    plt.legend()
    plt.grid(True)

    # Show the plot
    plt.show()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting plotting.")
    parser = argparse.ArgumentParser(
        description="Plot accelerometer data from a CSV file."
    )
    parser.add_argument("csv_filename", type=str, help="Path to the CSV file to plot")
    parser.add_argument("--filter", action="store_true", help="Filter data")
    args = parser.parse_args()

    plot_accel_data(args.csv_filename, args.filter)
