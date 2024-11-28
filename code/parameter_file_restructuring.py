
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
# Change directory to the root of the project 'data-centres'
root_dir = re.split('data-centres', os.getcwd())[0] + '/data-centres'
os.chdir(root_dir)
#%%
#%%
#copy the parameters to config/previous_parameter_versions/parameters_DATE.yml
date_id = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
os.system(f'cp config/parameters.yml config/previous_parameter_versions/parameters_{date_id}.yml')
print(f'parameters.yml copied to config/previous_parameter_versions/parameters_{date_id}.yml')
#%%

# #CREATE A SCRIPT TO RUN THROUGH EVERY ECONOMY AND REMOVE ROWS FOR:
# initial_ai_training_activity_growth_rate: ##
# #and make initial_data_activity_growth_rate the average of the two
# initial_data_activity_growth_rate: ##
# #and also remove rows for:
# initial_ai_training_intensity_improvement_rate: 0.05
# #and also rename 
# initial_data_to_ai_training_ratio: 0.9999
# # to
# initial_traditional_data_to_ai_training_ratio: 0.8
# #and also rename
# initial_energy_pj: 39.235343414100925
# # to
# initial_traditional_data_energy_pj: ##
# #and create a row for:
# initial_ai_training_energy_pj: 0
#same with any vriations of initial_energy_pj and initial_ai_training_energy_pj such as initial_energy_mw, initial_energy_mwh, initial_energy_twh mapping to their respective energy values e.g. initial_energy_mw to initial_traditional_data_energy_mw and initial_ai_training_energy_mw 

# #and drop any rows for 
# new_ai_growth_rate: xx
# # and 
# new_ai_training_intensity_improvement_rate: xx
# #and rename any rows for 
# new_data_to_ai_training_ratio:xx 
# # to
# new_traditional_data_to_ai_training_ratio: xx

#e.g. turn this:

# - name: 01_AUS
#   initial_data_activity_growth_rate: 0.18
#   initial_ai_training_activity_growth_rate: 0.36
#   initial_data_intensity_improvement_rate: 0.05
#   initial_ai_training_intensity_improvement_rate: 0.05
#   initial_data_to_ai_training_ratio: 0.9999
#   initial_energy_pj: 39.235343414100925
#   scheduled_builds:
#   - year: 2025
#     additional_energy_mw: 300
#     new_data_to_ai_training_ratio: 0.5
#   - year: 2026
#     additional_energy_mw: 300
#     new_data_to_ai_training_ratio: 0.5
#   - year: 2027
#     additional_energy_mw: 300
#     new_data_to_ai_training_ratio: 0.5
#   - year: 2028
#     additional_energy_mw: 300
#     new_data_to_ai_training_ratio: 0.5
#   - year: 2029
#     additional_energy_mw: 300
#     new_data_to_ai_training_ratio: 0.5
#   - year: 2030
#     additional_energy_mw: 300
#     new_data_to_ai_training_ratio: 0.5
#   new_activity_growth_rates:
#   - year: 2030
#     new_data_growth_rate: 0.09
#     new_ai_growth_rate: 0.09
#   - year: 2035
#     new_data_growth_rate: 0.06
#     new_ai_growth_rate: 0.06
#   - year: 2040
#     new_data_growth_rate: 0.024
#     new_ai_growth_rate: 0.024
#   - year: 2045
#     new_data_growth_rate: 0.012
#     new_ai_growth_rate: 0.012
#   new_intensity_improvement_rates:
#   - year: 2030
#     new_data_intensity_improvement_rate: 0.01
#     new_ai_training_intensity_improvement_rate: 0.01
#   - year: 2040
#     new_data_intensity_improvement_rate: 0.005
#     new_ai_training_intensity_improvement_rate: 0.005

#into:

# - name: 01_AUS
#   initial_data_activity_growth_rate: 0.27
#   initial_data_intensity_improvement_rate: 0.05
#   initial_traditional_data_to_ai_training_ratio: 0.9999
#   initial_traditional_data_energy_pj: 39.235343414100925
#   initial_ai_training_energy_pj: 0
#   scheduled_builds:
#   - year: 2025
#     additional_energy_mw: 300
#     new_traditional_data_to_ai_training_ratio: 0.5
#   - year: 2026
#     additional_energy_mw: 300
#     new_traditional_data_to_ai_training_ratio: 0.5
#   - year: 2027
#     additional_energy_mw: 300
#     new_traditional_data_to_ai_training_ratio: 0.5
#   - year: 2028
#     additional_energy_mw: 300
#     new_traditional_data_to_ai_training_ratio: 0.5
#   - year: 2029
#     additional_energy_mw: 300
#     new_traditional_data_to_ai_training_ratio: 0.5
#   - year: 2030
#     additional_energy_mw: 300
#     new_traditional_data_to_ai_training_ratio: 0.5
#   new_activity_growth_rates:
#   - year: 2030
#     new_data_growth_rate: 0.09
#   - year: 2035
#     new_data_growth_rate: 0.06
#   - year: 2040
#     new_data_growth_rate: 0.024
#   - year: 2045
#     new_data_growth_rate: 0.012
#   new_intensity_improvement_rates:
#   - year: 2030
#     new_data_intensity_improvement_rate: 0.01
#   - year: 2040
#     new_data_intensity_improvement_rate: 0.005

#create script:

# Load current parameters.yml file
#%%
#open up the yaml and insert the values for each economy:
with open('config/parameters.yml', 'r') as file:
    config = yaml.safe_load(file)
new_config = config.copy()
for economy_ in config['economies_list']:
    #find economy in config
    for i, economy in enumerate(config['economies']):
        if economy['name'] == economy_:
            break
        
    # Remove rows for initial_ai_training_activity_growth_rate and make initial_data_activity_growth_rate the average of both
    if 'initial_ai_training_activity_growth_rate' in economy:
        ai_training_rate = economy.pop('initial_ai_training_activity_growth_rate')
        if 'initial_data_activity_growth_rate' in economy:
            economy['initial_data_activity_growth_rate'] = (economy['initial_data_activity_growth_rate'] + ai_training_rate) / 2
    
    # Remove initial_ai_training_intensity_improvement_rate
    if 'initial_ai_training_intensity_improvement_rate' in economy:
        economy.pop('initial_ai_training_intensity_improvement_rate')

    # Rename initial_data_to_ai_training_ratio to initial_traditional_data_to_ai_training_ratio
    if 'initial_data_to_ai_training_ratio' in economy:
        economy['initial_traditional_data_to_ai_training_ratio'] = economy.pop('initial_data_to_ai_training_ratio')
    
    # Rename initial_energy_pj to initial_traditional_data_energy_pj and create initial_ai_training_energy_pj
    if 'initial_energy_pj' in economy:
        economy['initial_traditional_data_energy_pj'] = economy.pop('initial_energy_pj')
        economy['initial_ai_training_energy_pj'] = 0
        initial_unit = 'pj'
    elif 'initial_energy_mw' in economy:
        economy['initial_traditional_data_energy_mw'] = economy.pop('initial_energy_mw')
        economy['initial_ai_training_energy_mw'] = 0
        initial_unit = 'mw'
    elif 'initial_energy_mwh' in economy:
        'initial_traditional_data_energy_mwh' = economy.pop('initial_energy_mwh')
        economy['initial_ai_training_energy_mwh'] = 0
        initial_unit = 'mwh'
    elif 'initial_energy_twh' in economy:
        economy['initial_traditional_data_energy_twh'] = economy.pop('initial_energy_twh')
        economy['initial_ai_training_energy_twh'] = 0
        initial_unit = 'twh'
        
    # Rename other variations of initial energy metrics if they exist
    for energy_key in ['initial_energy_mw', 'initial_energy_mwh', 'initial_energy_twh']:
        if energy_key in economy:
            new_key = energy_key.replace('initial_energy', 'initial_traditional_data_energy')
            economy[new_key] = economy.pop(energy_key)
            economy[f'initial_ai_training_energy_{energy_key.split("_")[-1]}'] = 0

    # Drop rows for new_ai_growth_rate and new_ai_training_intensity_improvement_rate
    if 'new_activity_growth_rates' in economy:
        for rate in economy['new_activity_growth_rates']:
            rate.pop('new_ai_growth_rate', None)
    
    if 'new_intensity_improvement_rates' in economy:
        for rate in economy['new_intensity_improvement_rates']:
            rate.pop('new_ai_training_intensity_improvement_rate', None)
                
    # Rename new_data_to_ai_training_ratio to new_traditional_data_to_ai_training_ratio
    if 'scheduled_builds' in economy:
        for build in economy['scheduled_builds']:
            if 'new_data_to_ai_training_ratio' in build:
                build['new_traditional_data_to_ai_training_ratio'] = build.pop('new_data_to_ai_training_ratio')
        
    #put it all in order:
    ordered_economy = {
        'name': economy['name'],
        'initial_data_activity_growth_rate': economy.get('initial_data_activity_growth_rate'),
        'initial_traditional_data_to_ai_training_ratio': economy.get('initial_traditional_data_to_ai_training_ratio'),
        f'initial_traditional_data_energy_{initial_unit}': economy.get(f'initial_traditional_data_energy_{initial_unit}'),
        f'initial_ai_training_energy_{initial_unit}': economy.get(f'initial_ai_training_energy_{initial_unit}'),
        'initial_data_intensity_improvement_rate': economy.get('initial_data_intensity_improvement_rate'),
        'scheduled_builds': economy.get('scheduled_builds', []),
        'new_activity_growth_rates': economy.get('new_activity_growth_rates', []),
        'new_intensity_improvement_rates': economy.get('new_intensity_improvement_rates', [])
    }
    
    new_config['economies'][i] = ordered_economy
    
# Write the updated parameters back to the file
with open('config/parameters.yml', 'w') as file:
    yaml.dump(config, file, default_flow_style=False, sort_keys=False)





print("YAML parameters have been successfully updated.")

# %%
