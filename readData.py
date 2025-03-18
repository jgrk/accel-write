import argparse
import struct
import csv
import os

# KX132 range and sensitivity settings (change according to config)
ACCEL_RANGE = 16  # Choose from 2, 4, 8, or 16 g
SENSITIVITY = {2: 16384, 4: 8192, 8: 4096, 16: 2048}[ACCEL_RANGE]  # LSB per g
G_TO_MS2 = 9.81  # Convert g to m/s²


def convert_dat_to_csv(dat_filename):
    """Convert a binary .dat file to a CSV file with acceleration values."""
    if not os.path.exists(dat_filename):
        print(f"Error: File '{dat_filename}' not found.")
        return

    csv_filename = os.path.splitext(dat_filename)[0] + ".csv"

    try:
        with open(dat_filename, "rb") as f:
            data = f.read()

        file_size = len(data)
        print(f"File size: {file_size} bytes")

        # Ensure data is a multiple of 6
        if file_size % 6 != 0:
            print(f"⚠️ Warning: File size ({file_size} bytes) is not a multiple of 6. Some data may be corrupted.")
            num_samples = file_size // 6  # Adjust sample count
            data = data[:num_samples * 6]  # Trim excess bytes
        else:
            num_samples = file_size // 6

        print(f"Processing {num_samples} samples...")

        # Unpack raw 16-bit values from binary data (little-endian format)
        values = struct.unpack("<" + "hhh" * num_samples, data)

        # Write to CSV file
        with open(csv_filename, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["X (g)", "Y (g)", "Z (g)", "X (m/s²)", "Y (m/s²)", "Z (m/s²)"])  # Headers

            for i in range(num_samples):
                x_raw = values[i * 3]
                y_raw = values[i * 3 + 1]
                z_raw = values[i * 3 + 2]

                # Convert raw values to g and m/s²
                x_g = x_raw / SENSITIVITY
                y_g = y_raw / SENSITIVITY
                z_g = z_raw / SENSITIVITY

                x_ms2 = x_g * G_TO_MS2
                y_ms2 = y_g * G_TO_MS2
                z_ms2 = z_g * G_TO_MS2

                writer.writerow([x_g, y_g, z_g, x_ms2, y_ms2, z_ms2])

        print(f"✅ Successfully converted '{dat_filename}' to '{csv_filename}'")

    except struct.error as e:
        print(f"❌ Struct unpack error: {e}. The file might be corrupted or have an incorrect format.")
    except Exception as e:
        print(f"❌ Error processing file: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert a binary .dat file to a CSV file.")
    parser.add_argument("dat_filename", type=str, help="Path to the .dat file to convert")
    args = parser.parse_args()

    convert_dat_to_csv(args.dat_filename)
