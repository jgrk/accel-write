from ski_analys import enhanced_fft, simple_segmentation, savgol_helper
import pytest
file_dir = 'csv_data/ac2_9.csv'



def test_enhanced_fft():

    enhanced_fft(file=file_dir, enhance_method=simple_segmentation, filter=savgol_helper, window_length = 20, polyorder=3, axis=0, n_splits = 3) # savgol helper
