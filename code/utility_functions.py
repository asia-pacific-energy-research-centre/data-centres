import datetime as datetime
import os
import yaml
import numpy as np
import pandas as pd
import re
from scipy.stats import norm
import plotly.graph_objects as go
import plotly.express as px
import shutil


def get_latest_date_for_data_file(data_folder_path, file_name_start, file_name_end='', EXCLUDE_DATE_STR_START=False):
    """Note that if file_name_end is not specified then it will just take the first file that matches the file_name_start, eben if that matches the end if the file name as well. This is because the file_name_end is not always needed, and this cahnge was made post hoc, so we want to keep the old functionality.

    Args:
        data_folder_path (_type_): _description_
        file_name_start (_type_): _description_
        file_name_end (_type_, optional): _description_. Defaults to None.
        EXCLUDE_DATE_STR_START if true, if there is DATE at th start of a file_date_id dont treat it as a date. Defaults to False.

    Returns:
        _type_: _description_
    """
    regex_pattern_date = r'\d{8}'
    if EXCLUDE_DATE_STR_START:
        regex_pattern_date = r'(?<!DATE)\d{8}'
    
    #get list of all files in the data folder
    all_files = os.listdir(data_folder_path)
    #filter for only the files with the correct file extension
    if file_name_end == '':
        all_files = [file for file in all_files if file_name_start in file]
    else:
        all_files = [file for file in all_files if file_name_start in file and file_name_end in file]
    #drop any files with no date in the name
    all_files = [file for file in all_files if re.search(regex_pattern_date, file)]
    #get the date from the file name
    all_files = [re.search(regex_pattern_date, file).group() for file in all_files]
    #convert the dates to datetime objects
    all_files = [datetime.datetime.strptime(date, '%Y%m%d') for date in all_files]
    #get the latest date
    if len(all_files) == 0:
        print('No files found for ' + file_name_start + ' ' + file_name_end)
        return None
    # try:
    latest_date = max(all_files)
    # except ValueError:
    #     print('No files found for ' + file_name_start + ' ' + file_name_end)
    #     return None
    #convert the latest date to a string
    latest_date = latest_date.strftime('%Y%m%d')
    return latest_date
