from ski_analys import (
    enhanced_fft,
    simple_segmentation,
    savgol_helper,
    envelope_enhancer,
)
import pytest

file_dir = "csv_data/ac2_9.csv"


def test_enhanced_fft():
    # with simple segmentation
    enhanced_fft(
        file=file_dir,
        enhance_method=simple_segmentation,
        filter=savgol_helper,
        window_length=20,
        polyorder=3,
        axis=0,
        n_splits=3,
    )  # savgol helper



def test_detrend():
    import pathlib
    dir = "csv_data/"
    for file in pathlib.Path(dir).iterdir():
        enhanced_fft(file=file, enhance_method=envelope_enhancer, filter=savgol_helper, window_length=20, polyorder=3,
                     axis=0, n_out=100, width=(3, 100), detrending=True)

def test_get_data():
    import pathlib
    csv_data_path = pathlib.Path("csv_data/")
    result_path = pathlib.Path("testing/")
    for file in csv_data_path.iterdir():
        enhanced_fft(file=file, save_path="testing/", enhance_method=envelope_enhancer, filter=savgol_helper,
                     window_length=20, polyorder=3, axis=0, n_out=100, width=1, detrending=False)