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

from utility_functions import get_latest_date_for_data_file


#############################################################
# Project Energy Use
#############################################################


def project_energy_use(config):
    start_year = config['start_year']
    end_year = config['end_year']
    all_projections = []

    for economy in config['economies']:
        name = economy['name']
        initial_data_growth_rate = economy['initial_data_activity_growth_rate']
        initial_ai_growth_rate = economy['initial_ai_training_activity_growth_rate']
        initial_data_intensity_improvement_rate = economy['initial_data_intensity_improvement_rate']
        initial_ai_intensity_improvement_rate = economy['initial_ai_training_intensity_improvement_rate']
        initial_ratio = economy['initial_data_to_ai_training_ratio']
        if 'initial_energy_pj' in economy.keys():
            initial_energy_pj = economy['initial_energy_pj']
        elif 'initial_energy_mw' in economy.keys():
            initial_energy_pj = ((economy['initial_energy_mw'] * 8760) / 3.6) * 1e-6
        elif 'initial_energy_mwh' in economy.keys():
            initial_energy_pj = (economy['initial_energy_mwh'] / 3.6) * 1e-6
        elif 'initial_energy_twh' in economy.keys():
            initial_energy_pj = economy['initial_energy_twh'] * 3.6
        else:
            raise ValueError('Initial energy not specified')
        scheduled_builds = economy.get('scheduled_builds', [])
        new_activity_growth_rates = economy.get('new_activity_growth_rates', [])
        new_intensity_improvement_rates = economy.get('new_intensity_improvement_rates', [])
        
        years = np.arange(start_year, end_year + 1)
        df = pd.DataFrame(index=years)
        df['year'] = years
        df['economy'] = name
        
        # Set initial growth rates
        df['data_growth_rate'] = initial_data_growth_rate
        df['ai_growth_rate'] = initial_ai_growth_rate
        df['data_intensity_improvement_rate'] = initial_data_intensity_improvement_rate
        df['ai_intensity_improvement_rate'] = initial_ai_intensity_improvement_rate
        # Apply any new growth rates based on the specified years
        for new_rate in new_activity_growth_rates:
            if new_rate['year'] in years:
                df.loc[new_rate['year']:, 'data_growth_rate'] = new_rate['new_data_growth_rate']
                df.loc[new_rate['year']:, 'ai_growth_rate'] = new_rate['new_ai_growth_rate']
        for new_rate in new_intensity_improvement_rates:
            if new_rate['year'] in years:
                df.loc[new_rate['year']:, 'data_intensity_improvement_rate'] = new_rate['new_data_intensity_improvement_rate']
                df.loc[new_rate['year']:, 'ai_intensity_improvement_rate'] = new_rate['new_ai_training_intensity_improvement_rate']
        # Initialize activity and intensity levels
        df['data_activity'] = initial_energy_pj * initial_ratio
        df['ai_training_activity'] = initial_energy_pj * (1 - initial_ratio)
        df['data_intensity'] = (initial_energy_pj * initial_ratio) / df['data_activity'].iloc[0]
        df['ai_training_intensity'] = (initial_energy_pj * (1 - initial_ratio)) / df['ai_training_activity'].iloc[0]
        
        df['data_to_ai_training_ratio'] = initial_ratio
        # Project activities, intensities, and scheduled builds over time
        for year in range(start_year + 1, end_year + 1):
            prev_year = year - 1
            breakpoint()
            SCHEDULED_BUILD_FOUND = False
            
            # Set the pre-set growth rates for the current year
            data_growth_rate = df.loc[year, 'data_growth_rate']
            ai_growth_rate = df.loc[year, 'ai_growth_rate']
            data_intensity_improvement_rate = df.loc[year, 'data_intensity_improvement_rate']
            ai_intensity_improvement_rate = df.loc[year, 'ai_intensity_improvement_rate']
                
            # Apply intensity improvements
            df.loc[year, 'data_intensity'] = df.loc[prev_year, 'data_intensity'] * (1 - data_intensity_improvement_rate) 
            df.loc[year, 'ai_training_intensity'] = df.loc[prev_year, 'ai_training_intensity'] * (1 - ai_intensity_improvement_rate)
            
            #set activity for the current year based on previous year 
            df.loc[year, 'data_activity'] = df.loc[prev_year, 'data_activity']
            df.loc[year, 'ai_training_activity'] = df.loc[prev_year, 'ai_training_activity']
            
            # Account for scheduled builds in the current year
            for build in scheduled_builds:
                if build['year'] == year:
                    SCHEDULED_BUILD_FOUND = True
                    if 'new_data_to_ai_training_ratio' in build.keys():
                        df.loc[year, 'data_to_ai_training_ratio'] = build['new_data_to_ai_training_ratio']
                    else:
                        df.loc[year, 'data_to_ai_training_ratio'] = df.loc[prev_year, 'data_to_ai_training_ratio']
                        
                    if 'additional_energy_mw' in build.keys():
                        total_energy = ((build['additional_energy_mw'] * 8760) / 3.6) * 1e-6
                    elif 'additional_energy_pj' in build.keys():                    
                        total_energy = build['additional_energy_pj']
                    elif 'additional_energy_mwh' in build.keys():
                        total_energy = (build['additional_energy_mwh'] / 3.6) * 1e-6
                    elif 'additional_energy_twh' in build.keys():
                        total_energy = build['additional_energy_twh'] * 3.6
                    else:
                        raise ValueError('Additional energy not specified')
                    
                    #calculate the energy use for data and ai_training using the ratio. This will either be based on the ratio from the previous year or a newly supplied ratio for this year:
                    total_energy_ai_training = total_energy * (1 - df.loc[year, 'data_to_ai_training_ratio'])
                    total_energy_data = total_energy * df.loc[year, 'data_to_ai_training_ratio']
                    
                    # Update activities based on the additional energy and current intensity
                    
                    df.loc[year, 'data_activity'] += total_energy_data / df.loc[year, 'data_intensity']
                    df.loc[year, 'ai_training_activity'] += total_energy_ai_training / df.loc[year, 'ai_training_intensity']
                    
            if not SCHEDULED_BUILD_FOUND:
                # Apply growth rates to the activity levels since no scheduled builds were found
                df.loc[year, 'data_activity'] *= (1 + data_growth_rate)
                df.loc[year, 'ai_training_activity'] *= (1 + ai_growth_rate)
        
        # Calculate energy use by sector
        df['data_energy_use'] = df['data_activity'] * df['data_intensity']
        df['ai_training_energy_use'] = df['ai_training_activity'] * df['ai_training_intensity']
        
        # Normalize activities for indexing
        df['data_activity_indexed'] = df['data_activity'] / df['data_activity'].iloc[0] * 100
        df['ai_training_activity_indexed'] = df['ai_training_activity'] / df['ai_training_activity'].iloc[0] * 100

        all_projections.append(df)

    # Combine all projections into a single DataFrame
    combined_projections = pd.concat(all_projections)
    return combined_projections

    return None
