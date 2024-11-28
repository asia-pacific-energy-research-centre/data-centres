
#%%
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
# Change directory to the root of the project 'data-centres'
root_dir = re.split('data-centres', os.getcwd())[0] + '/data-centres'
os.chdir(root_dir)
import plotting as plotting
import data_processing as data_processing
from utility_functions import get_latest_date_for_data_file
import projection_functions as projection_functions

#%%
#############################################################
# Run projections and generate plots

# Load the YAML configuration
with open('config/parameters.yml', 'r') as file:
    config = yaml.safe_load(file)

#MAIN FUNCTION
projections = projection_functions.project_energy_use(config)
#MAIN FUNCTION
#%%
plotting.plot_projections(projections)
apec_aggregate = data_processing.aggregate_apec_values(projections, config)
plotting.plot_apec_aggregate(apec_aggregate)
outlook_results = data_processing.clean_results_for_outlook(projections, apec_aggregate)

file_date_id = get_latest_date_for_data_file('input_data', 'merged_file_energy_00_APEC_', file_name_end='.csv', EXCLUDE_DATE_STR_START=False)
outlook_energy_APEC = pd.read_csv(os.path.join('input_data', f'merged_file_energy_00_APEC_{file_date_id}.csv'))#this file can be found in Modelling\Integration\APEC\01_FinalEBT

DO_THIS=False
if DO_THIS:
    data_processing.download_all_merged_file_energy_from_economys_from_onedrive(config)
    
outlook_energy_all_economies = data_processing.concat_all_merged_file_energy_files_from_local(config) 

if outlook_energy_all_economies.columns.to_list() == outlook_energy_APEC.columns.to_list():
    outlook_energy_all_economies = pd.concat([outlook_energy_APEC, outlook_energy_all_economies])#assuming the structure is the same
else:
    raise ValueError
plotting.import_and_compare_to_outlook_results(outlook_results, outlook_energy_all_economies)

data_processing.save_outputs(outlook_results)


#############################################################
#%%
