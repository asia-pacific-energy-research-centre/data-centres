
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

ECONOMIES_TO_KEEP_AS_IS = ['12_NZ']


#take in manuels number of datacentres by economy and in the world and also the energy use from datacentres in the world, then estiamte the energy use per datacentre, then claculate the energy use for each economy by multiplying the number of datacentres by the energy use per datacentre. 

number_of_datacentres = pd.read_csv('input_data/Global_Data_Center_Statistics_2023_manuel.csv')#Year	Country	Data Center Count	Economy

energy_use_datacentres_twh_2022 = 460
energy_use_datacentres_pj_2022 = energy_use_datacentres_twh_2022 * 3.6

world_datacentre_count_2023 = number_of_datacentres.loc[number_of_datacentres['Country'] == 'World', 'Data Center Count'].values[0]
#decrease datacentre count by 15% to account for the fact that the datacentre count is from 2023 and the energy use is from 2022
world_datacentre_count_2022_est = world_datacentre_count_2023 * 0.85

energy_use_per_datacentre_pj = energy_use_datacentres_pj_2022 / world_datacentre_count_2022_est

#change the year in the number of datacentres to 2021 and decrease the datacentre count by 15% twice to account for the fact that the datacentre count is from 2023 and we are estimating the energy use for 2021 (makes assumption that intensity was held constant but whateeves)
number_of_datacentres['Year'] = 2021
number_of_datacentres['Data Center Count'] = number_of_datacentres['Data Center Count'] * 0.85 * 0.85
number_of_datacentres['Energy Use PJ'] = number_of_datacentres['Data Center Count'] * energy_use_per_datacentre_pj

#copy the parameters to config/previous_parameter_versions/parameters_DATE.yml
date_id = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
os.system(f'cp config/parameters.yml config/previous_parameter_versions/parameters_{date_id}.yml')
print(f'parameters.yml copied to config/previous_parameter_versions/parameters_{date_id}.yml')
#open up the yaml and insert the values for each economy:
with open('config/parameters.yml', 'r') as file:
    config = yaml.safe_load(file)
    #
#%%
#for each item in economies, find the name key and extract the Energy Use PJ from number_of_datacentres and insert it into the yaml as initial_energy_pj:
# e.g.
# economies:
#   - name: '01_AUS'
#     initial_energy_pj: number_of_datacentres.loc[number_of_datacentres['Economy'] == '01_AUS', 'Energy Use PJ'].values[0]
#%%
for economy in config['economies']:
    if economy['name'] in ECONOMIES_TO_KEEP_AS_IS:
        continue
    economy_name = economy['name']
    economy_energy_pj = number_of_datacentres.loc[number_of_datacentres['Economy'] == economy_name, 'Energy Use PJ'].values[0]
    economy['initial_energy_pj'] = float(economy_energy_pj) 
    
#%%
with open('config/parameters.yml', 'w') as file:
    yaml.safe_dump(config, file, default_flow_style=False, sort_keys=False)
#%%

#now do the same thing but for other parameters and no need for calculations:

# - name: 01_AUS
#   data_activity_growth_rate: 0.03
#   ai_training_activity_growth_rate: 0.07
#   data_intensity_improvement_rate: 0.02
#   ai_training_intensity_improvement_rate: 0.015
#   initial_data_to_ai_training_ratio: 0.8
#   initial_energy_pj: 39.235343414100925
#   scheduled_builds:
#   - year: 2030
#     additional_energy_pj: 0.3
#   - year: 2050
#     additional_energy_pj: 0.5
#   new_activity_growth_rates:
#   - year: 2030
#     new_data_growth_rate: 0.01
#     new_ai_growth_rate: 0.02

initial_data_activity_growth_rate = 0.2
initial_ai_training_activity_growth_rate = 0.2
initial_data_intensity_improvement_rate = 0.05
initial_ai_training_intensity_improvement_rate = 0.05
initial_data_to_ai_training_ratio = 0.8
new_activity_growth_rates = {
    2025: {'new_data_growth_rate': 0.15, 'new_ai_growth_rate': 0.15},
    2030: {'new_data_growth_rate': 0.075, 'new_ai_growth_rate': 0.075},
    2035: {'new_data_growth_rate': 0.05, 'new_ai_growth_rate': 0.05},
    2040: {'new_data_growth_rate': 0.02, 'new_ai_growth_rate': 0.02},
    2045: {'new_data_growth_rate': 0.01, 'new_ai_growth_rate': 0.01}
}
new_intensity_improvement_rates = {
    2030: {'new_data_intensity_improvement_rate': 0.01, 'new_ai_training_intensity_improvement_rate': 0.01},
    2040: {'new_data_intensity_improvement_rate': 0.005, 'new_ai_training_intensity_improvement_rate': 0.005}
}
scheduled_builds = {
    2030: {'additional_energy_pj': 0.001},
    2050: {'additional_energy_pj': 0.001}
}

#now implement them:
for economy in config['economies']:
    if economy['name'] in ECONOMIES_TO_KEEP_AS_IS:
        continue
    economy['initial_data_activity_growth_rate'] = float(initial_data_activity_growth_rate)
    economy['initial_ai_training_activity_growth_rate'] = float(initial_ai_training_activity_growth_rate)
    economy['initial_data_intensity_improvement_rate'] = float(initial_data_intensity_improvement_rate)
    economy['initial_ai_training_intensity_improvement_rate'] = float(initial_ai_training_intensity_improvement_rate)
    economy['initial_data_to_ai_training_ratio'] = float(initial_data_to_ai_training_ratio)
        
    # Format the new_activity_growth_rates
    economy['new_activity_growth_rates'] = [
        {'year': year, **rates} for year, rates in new_activity_growth_rates.items()
    ]
    #format the new_intensity_improvement_rates
    economy['new_intensity_improvement_rates'] = [
        {'year': year, **rates} for year, rates in new_intensity_improvement_rates.items()
    ]
    economy['scheduled_builds'] = [
        {'year': year, 'additional_energy_pj': value['additional_energy_pj']} for year, value in scheduled_builds.items()]
    
    #if vlaue is for 20_USA economy then add some specific vlaues:
    #usa might have an even higher level ofgrowth for data but especially ai, so increase the growth rates for usa
    if economy['name'] == '20_USA':
            
        economy['initial_data_activity_growth_rate'] = float(initial_data_activity_growth_rate) * 1.5
        economy['initial_ai_training_activity_growth_rate'] = float(initial_ai_training_activity_growth_rate) * 1.5
        economy['new_activity_growth_rates']  = [ 
            {'year': year, 'new_data_growth_rate': rate['new_data_growth_rate']*1.5, 'new_ai_growth_rate': rate['new_ai_growth_rate']*1.5} for year, rate in new_activity_growth_rates.items()
        ]
    #same for china but slightly less than usa
    if economy['name'] == '05_PRC':
            
        economy['initial_data_activity_growth_rate'] = float(initial_data_activity_growth_rate) * 1.3
        economy['initial_ai_training_activity_growth_rate'] = float(initial_ai_training_activity_growth_rate) * 1.3
        economy['new_activity_growth_rates']  = [ 
            {'year': year, 'new_data_growth_rate': rate['new_data_growth_rate']*1.3, 'new_ai_growth_rate': rate['new_ai_growth_rate']*1.3} for year, rate in new_activity_growth_rates.items()
        ]
    #and then same for countries which are seen as data centre hotspots, but slightly less than china
    if economy['name'] in ['10_MAS','08_JPN', '09_ROK', '03_CDA', '01_AUS']:
            
        economy['initial_data_activity_growth_rate'] = float(initial_data_activity_growth_rate) * 1.2
        economy['initial_ai_training_activity_growth_rate'] = float(initial_ai_training_activity_growth_rate) * 1.2
        economy['new_activity_growth_rates']  = [ 
            {'year': year, 'new_data_growth_rate': rate['new_data_growth_rate']*1.2, 'new_ai_growth_rate': rate['new_ai_growth_rate']*1.2} for year, rate in new_activity_growth_rates.items()
        ]
    #and also a bit lower than avg for economies which have expensive energy, eg hkc sg
    if economy['name'] in ['06_HKC','17_SGP']:
            
        economy['initial_data_activity_growth_rate'] = float(initial_data_activity_growth_rate) * 0.8
        economy['initial_ai_training_activity_growth_rate'] = float(initial_ai_training_activity_growth_rate) * 0.8
        economy['new_activity_growth_rates']  = [ 
            {'year': year, 'new_data_growth_rate': rate['new_data_growth_rate']*0.8, 'new_ai_growth_rate': rate['new_ai_growth_rate']*0.8} for year, rate in new_activity_growth_rates.items()
        ]


#%%
with open('config/parameters.yml', 'w') as file:
    yaml.safe_dump(config, file, default_flow_style=False, sort_keys=False)
# %%
#add specific