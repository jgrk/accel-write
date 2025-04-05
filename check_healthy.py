import pandas as pd
import numpy as np
from argparse import ArgumentParser

def check_sqr_sum(dir_path):
    counter = 0
    df = pd.read_csv(dir_path)
    print(f"Length: {len(df)}")

    for i in range(len(df)):
        if 1.1 < np.sqrt(df['X (g)'][i]**2 + df['Y (g)'][i]**2 + df['Z (g)'][i]**2) or np.sqrt(df['X (g)'][i]**2 + df['Y (g)'][i]**2 + df['Z (g)'][i]**2) < 0.9:
            print(np.sqrt(df['X (g)'][i]**2 + df['Y (g)'][i]**2 + df['Z (g)'][i]**2))
            counter += 1

    out_of_bounds_ratio = counter / len(df)
    print(f"Done. {counter} out of {len(df)} samples are out of bounds ({out_of_bounds_ratio:.2%}).")



if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('dir_path', type=str)
    args = parser.parse_args()
    check_sqr_sum(args.dir_path)