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

    for econ_entry in config['economies']:
        economy = econ_entry['name']
        initial_data_growth_rate = econ_entry['initial_data_activity_growth_rate']
        # initial_ai_growth_rate = econ_entry['initial_ai_training_activity_growth_rate']
        initial_data_intensity_improvement_rate = econ_entry['initial_data_intensity_improvement_rate']
        # initial_ai_intensity_improvement_rate = econ_entry['initial_ai_training_intensity_improvement_rate']
        initial_ratio = econ_entry['initial_traditional_data_to_ai_training_ratio']
        if 'initial_traditional_data_energy_pj' in econ_entry.keys():
            initial_traditional_data_energy_pj = econ_entry['initial_traditional_data_energy_pj']
        elif 'initial_traditional_data_energy_mw' in econ_entry.keys():
            initial_traditional_data_energy_pj = ((econ_entry['initial_traditional_data_energy_mw'] * 8760) * 3.6) * 1e-6
        elif 'initial_traditional_data_energy_mwh' in econ_entry.keys():
            initial_traditional_data_energy_pj = (econ_entry['initial_traditional_data_energy_mwh'] * 3.6) * 1e-6
        elif 'initial_traditional_data_energy_twh' in econ_entry.keys():
            initial_traditional_data_energy_pj = econ_entry['initial_traditional_data_energy_twh'] * 3.6
        else:
            raise ValueError('Initial traditional_data energy not specified')
        if 'initial_ai_training_energy_pj' in econ_entry.keys():
            initial_ai_training_energy_pj = econ_entry['initial_ai_training_energy_pj']
        elif 'initial_ai_training_energy_mw' in econ_entry.keys():
            initial_ai_training_energy_pj = ((econ_entry['initial_ai_training_energy_mw'] * 8760) * 3.6) * 1e-6
        elif 'initial_ai_training_energy_mwh' in econ_entry.keys():
            initial_ai_training_energy_pj = (econ_entry['initial_ai_training_energy_mwh'] * 3.6) * 1e-6
        elif 'initial_ai_training_energy_twh' in econ_entry.keys():
            initial_ai_training_energy_pj = econ_entry['initial_ai_training_energy_twh'] * 3.6
        else:
            raise ValueError('Initial ai_training energy not specified')
    
        initial_energy_pj = initial_traditional_data_energy_pj + initial_ai_training_energy_pj
        
        scheduled_builds = econ_entry.get('scheduled_builds', [])
        new_activity_growth_rates = econ_entry.get('new_activity_growth_rates', [])
        new_intensity_improvement_rates = econ_entry.get('new_intensity_improvement_rates', [])
        
        years = np.arange(start_year, end_year + 1)
        df = pd.DataFrame(index=years)
        df['year'] = years
        df['economy'] = economy
        
        # Set initial growth rates
        df['data_growth_rate'] = initial_data_growth_rate
        # df['ai_growth_rate'] = initial_ai_growth_rate
        df['data_intensity_improvement_rate'] = initial_data_intensity_improvement_rate
        
        df['traditional_data_to_ai_training_ratio'] = initial_ratio
        # df['ai_intensity_improvement_rate'] = initial_ai_intensity_improvement_rate
        # Apply any new growth rates based on the specified years and years after (also the ratio is applied too)
        for new_rate in new_activity_growth_rates:
            if economy =='02_BD':
                breakpoint()
            if new_rate['year'] in years:
                if 'new_data_growth_rate' in new_rate.keys():
                    df.loc[new_rate['year']:, 'data_growth_rate'] = new_rate['new_data_growth_rate']
                if 'new_traditional_data_to_ai_training_ratio' in new_rate.keys():
                    df.loc[new_rate['year']:,'traditional_data_to_ai_training_ratio'] = new_rate['new_traditional_data_to_ai_training_ratio']
                # df.loc[new_rate['year']:, 'ai_growth_rate'] = new_rate['new_ai_growth_rate']
        for new_rate in new_intensity_improvement_rates:
            if new_rate['year'] in years:
                df.loc[new_rate['year']:, 'data_intensity_improvement_rate'] = new_rate['new_data_intensity_improvement_rate']
                # df.loc[new_rate['year']:, 'ai_intensity_improvement_rate'] = new_rate['new_ai_training_intensity_improvement_rate']
        # Initialize activity and intensity levels, basing them off energy. (its unimportant to know the actual activity, just to have a starting point)
        df['traditional_data_activity'] = initial_traditional_data_energy_pj
        df['ai_training_activity'] = initial_ai_training_energy_pj
        
        df['data_intensity'] = 1
        # Project activities, intensities, and scheduled builds over time
        
        for year in range(start_year + 1, end_year + 1):
            if economy =='02_BD' and year > 2025:
                breakpoint()
            prev_year = year - 1
            
            SCHEDULED_BUILD_FOUND = False
            
            # Set the pre-set growth rates for the current year
            data_growth_rate = df.loc[year, 'data_growth_rate']
            # ai_growth_rate = df.loc[year, 'ai_growth_rate']
            data_intensity_improvement_rate = df.loc[year, 'data_intensity_improvement_rate']
                
            # Apply intensity improvements
            df.loc[year, 'data_intensity'] = df.loc[prev_year, 'data_intensity'] * (1 - data_intensity_improvement_rate)
            
            #set activity for the current year based on previous year 
            df.loc[year, 'traditional_data_activity'] = df.loc[prev_year, 'traditional_data_activity']
            df.loc[year, 'ai_training_activity'] = df.loc[prev_year, 'ai_training_activity']
            
            #wats going on here with weir resutls
            # Account for scheduled builds in the current year
            for build in scheduled_builds:
                if build['year'] == year:
                    SCHEDULED_BUILD_FOUND = True
                    if 'new_traditional_data_to_ai_training_ratio' in build.keys():
                        df.loc[year, 'traditional_data_to_ai_training_ratio'] = build['new_traditional_data_to_ai_training_ratio']
                    else:
                        df.loc[year, 'traditional_data_to_ai_training_ratio'] = df.loc[prev_year, 'traditional_data_to_ai_training_ratio']
                        
                    if 'additional_energy_mw' in build.keys():
                        total_energy = ((build['additional_energy_mw'] * 8760) * 3.6) * 1e-6
                    elif 'additional_energy_pj' in build.keys():                    
                        total_energy = build['additional_energy_pj']
                    elif 'additional_energy_mwh' in build.keys():
                        total_energy = (build['additional_energy_mwh'] * 3.6) * 1e-6
                    elif 'additional_energy_twh' in build.keys():
                        total_energy = build['additional_energy_twh'] * 3.6
                    else:
                        raise ValueError('Additional energy not specified')
                    #calculate the energy use for data and ai_training using the ratio. This will either be based on the ratio from the previous year or a newly supplied ratio for this year:
                    total_energy_ai_training = total_energy * (1 - df.loc[year, 'traditional_data_to_ai_training_ratio'])
                    total_energy_data = total_energy * df.loc[year, 'traditional_data_to_ai_training_ratio']
                    
                    # Update activities based on the additional energy and current intensity
                    
                    df.loc[year, 'traditional_data_activity'] += total_energy_data / df.loc[year, 'data_intensity']
                    df.loc[year, 'ai_training_activity'] += total_energy_ai_training / df.loc[year, 'data_intensity']
                    
            if not SCHEDULED_BUILD_FOUND:
                if economy =='18_CT':
                    breakpoint()
                # Apply growth rates to the activity levels since no scheduled builds were found. we woill apply the growth rate to sum of both activities and then multiply by the ratio to get the individual activities
                # df.loc[year, 'data_activity'] *= (1 + data_growth_rate)
                # df.loc[year, 'ai_training_activity'] *= (1 + ai_growth_rate)
                df.loc[year, 'traditional_data_activity'] += ((df.loc[year, 'traditional_data_activity']  + df.loc[year, 'ai_training_activity'] ) * data_growth_rate * df.loc[year, 'traditional_data_to_ai_training_ratio'])
                df.loc[year, 'ai_training_activity'] += (df.loc[year, 'traditional_data_activity']  + df.loc[year, 'ai_training_activity']) * data_growth_rate * (1 - df.loc[year, 'traditional_data_to_ai_training_ratio'])
        
        # Calculate energy use by sector
        df['traditional_data_energy_use'] = df['traditional_data_activity'] * df['data_intensity']
        df['ai_training_energy_use'] = df['ai_training_activity'] * df['data_intensity']
        
        # Normalize activities for indexing take the 2nd year so 0 values wont cause issues
        df['traditional_data_activity_indexed'] = df['traditional_data_activity'] / df['traditional_data_activity'].iloc[1] * 100
        df['ai_training_activity_indexed'] = df['ai_training_activity'] / df['ai_training_activity'].iloc[1] * 100

        all_projections.append(df)

    # Combine all projections into a single DataFrame
    combined_projections = pd.concat(all_projections)
    return combined_projections

    return None
