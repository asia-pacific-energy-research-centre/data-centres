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

# Economies that should remain unchanged in the YAML file
ECONOMIES_TO_KEEP_AS_IS = ['12_NZ', '18_CT', '09_ROK', '06_HKC', '10_MAS', '20_USA', '07_INA', '01_AUS']

# Load the number of datacentres by economy and world, calculate energy use per datacentre
number_of_datacentres = pd.read_csv('input_data/Global_Data_Center_Statistics_2023_manuel.csv')
energy_use_datacentres_twh_2022 = 460
energy_use_datacentres_pj_2022 = energy_use_datacentres_twh_2022 * 3.6
world_datacentre_count_2023 = number_of_datacentres.loc[number_of_datacentres['Country'] == 'World', 'Data Center Count'].values[0]
world_datacentre_count_2022_est = world_datacentre_count_2023 * 0.85  # Estimate for 2022
energy_use_per_datacentre_pj = energy_use_datacentres_pj_2022 / world_datacentre_count_2022_est

# Estimate datacentre counts for 2021 and calculate energy use
number_of_datacentres['Year'] = 2021
number_of_datacentres['Data Center Count'] = number_of_datacentres['Data Center Count'] * 0.85 * 0.85
number_of_datacentres['Energy Use PJ'] = number_of_datacentres['Data Center Count'] * energy_use_per_datacentre_pj

# Copy the parameters to backup with timestamp
date_id = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
os.system(f'cp config/parameters.yml config/previous_parameter_versions/parameters_{date_id}.yml')
print(f'parameters.yml copied to config/previous_parameter_versions/parameters_{date_id}.yml')

# Load the parameters.yml file
with open('config/parameters.yml', 'r') as file:
    config = yaml.safe_load(file)
new_config = config.copy()

# Update economies in the parameters YAML file
for economy_ in config['economies']:
    if economy_['name'] in ECONOMIES_TO_KEEP_AS_IS:
        continue
    
    # Update energy use from datacentre data
    economy_name = economy_['name']
    economy_energy_pj = number_of_datacentres.loc[number_of_datacentres['Economy'] == economy_name, 'Energy Use PJ'].values[0]
    economy_['initial_traditional_data_energy_pj'] = float(economy_energy_pj)
    economy_['initial_ai_training_energy_pj'] = 0

    # Set growth rates and improvement rates for each economy
    economy_['initial_data_activity_growth_rate'] = 0.15
    economy_['initial_data_intensity_improvement_rate'] = 0.05
    economy_['initial_traditional_data_to_ai_training_ratio'] = 0.9999

    # Update scheduled builds, growth rates, and intensity improvement rates
    new_activity_growth_rates = {
        2025: {'new_data_growth_rate': 0.1},
        2030: {'new_data_growth_rate': 0.075},
        2035: {'new_data_growth_rate': 0.05},
        2040: {'new_data_growth_rate': 0.02},
        2045: {'new_data_growth_rate': 0.01}
    }
    economy_['new_activity_growth_rates'] = [
        {'year': year, 'new_data_growth_rate': rates['new_data_growth_rate']} for year, rates in new_activity_growth_rates.items()
    ]
    economy_['new_intensity_improvement_rates'] = [
        {'year': year, 'new_data_intensity_improvement_rate': rates['new_data_intensity_improvement_rate']} for year, rates in {
            2030: {'new_data_intensity_improvement_rate': 0.01},
            2040: {'new_data_intensity_improvement_rate': 0.005}
        }.items()
    ]
    economy_['scheduled_builds'] = [
        {'year': year, 'additional_energy_pj': value['additional_energy_pj'], 'new_traditional_data_to_ai_training_ratio': value['new_data_to_ai_training_ratio']} for year, value in {
            2030: {'additional_energy_pj': 0.001, 'new_data_to_ai_training_ratio': 0.75},
            2050: {'additional_energy_pj': 0.001, 'new_data_to_ai_training_ratio': 0.95}
        }.items()
    ]

    # Adjust specific economies with custom growth rates
    if economy_['name'] == '20_USA':
        economy_['initial_data_activity_growth_rate'] *= 1.5
        economy_['new_activity_growth_rates'] = [
            {'year': rate['year'], 'new_data_growth_rate': rate['new_data_growth_rate'] * 1.5}
            for rate in economy_['new_activity_growth_rates']
        ]

    elif economy_['name'] == '05_PRC':
        economy_['initial_data_activity_growth_rate'] *= 1.3
        economy_['new_activity_growth_rates'] = [
            {'year': rate['year'], 'new_data_growth_rate': rate['new_data_growth_rate'] * 1.3}
            for rate in economy_['new_activity_growth_rates']
        ]

    elif economy_['name'] in ['10_MAS', '08_JPN', '09_ROK', '03_CDA', '01_AUS']:
        economy_['initial_data_activity_growth_rate'] *= 1.2
        economy_['new_activity_growth_rates'] = [
            {'year': rate['year'], 'new_data_growth_rate': rate['new_data_growth_rate'] * 1.2}
            for rate in economy_['new_activity_growth_rates']
        ]

    elif economy_['name'] in ['06_HKC', '17_SGP']:
        economy_['initial_data_activity_growth_rate'] *= 0.8
        economy_['new_activity_growth_rates'] = [
            {'year': rate['year'], 'new_data_growth_rate': rate['new_data_growth_rate'] * 0.8}
            for rate in economy_['new_activity_growth_rates']
        ]

    elif economy_['name'] == '18_CT':
        scheduled_builds_mw = {
            2024: 13,
            2025: 12,
            2026: 25,
            2027: 27,
            2028: 33,
            2029: 33,
            2030: 42
        }
        economy_['scheduled_builds'] = [
            {'year': year, 'additional_energy_pj': mw * 24 * 365 * 3.6 * 10**-6}
            for year, mw in scheduled_builds_mw.items()
        ]
        economy_['initial_data_activity_growth_rate'] = 0
        economy_['new_activity_growth_rates'] = [
            {'year': year, 'new_data_growth_rate': rate['new_data_growth_rate'] * 1.1}
            for year, rate in new_activity_growth_rates.items() if year > 2029
        ]

# Write the updated parameters back to the file
with open('config/parameters.yml', 'w') as file:
    yaml.safe_dump(new_config, file, default_flow_style=False, sort_keys=False)

print("YAML parameters have been successfully updated.")
#%%