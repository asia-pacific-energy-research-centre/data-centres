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

def download_all_merged_file_energy_from_economys_from_onedrive(config):
    known_double_ups_and_their_solutions = ['merged_file_energy_10_MAS_20240905_TGT1.csv']
    
    root_onedrive = os.path.join('C:', 'Users', 'finbar.maunsell', 'OneDrive - APERC', 'outlook 9th', 'Modelling', 'Integration')
    #follow C: with \\
    root_onedrive = root_onedrive.replace('C:', 'C:\\')
    root_local = os.path.join('input_data')
    #look for the csv's in outlook 9th\Modelling\Integration\{ECONOMY}\08_Final, if theres multiple then find the one with the latest date using get_latest_date_for_data_file().
    file_name_start= 'merged_file_energy'
    for economy in config['economies_list']:#need a list of econmoies
        file_name_start_econ = file_name_start+'_'+economy
        data_folder_path = os.path.join(root_onedrive, economy, '08_Final')
        date_id = get_latest_date_for_data_file(data_folder_path, file_name_start_econ, file_name_end='.csv', EXCLUDE_DATE_STR_START=False)
        csvs = [file for file in os.listdir(data_folder_path) if file_name_start_econ in file and date_id in file]
        if len(csvs) > 1:
            print(f'Multiple files found for {file_name_start_econ} on {date_id}')
            found=False
            for file in csvs:
                if file in known_double_ups_and_their_solutions:
                    csv = file
                    found = True
                    break
            if not found:
                breakpoint()
                raise ValueError
        elif len(csvs) == 0:
            print(f'No files found for {file_name_start_econ} on {date_id}')
            # raise ValueError
            continue
        else:
            csv = csvs[0]
        #check th local folder exists
        if not os.path.exists(os.path.join(root_local, economy)):
            os.makedirs(os.path.join(root_local, economy))
        else:
            # if the file name is the same dont do anything, if not, empty the folder of ifles begining weith merged_file_energy and copy the new file in
            if not os.path.exists(os.path.join(root_local, economy, csv)):
                for file in os.listdir(os.path.join(root_local, economy)):
                    if file_name_start_econ in file:
                        os.remove(os.path.join(root_local, economy, file))
        #copy the file
        shutil.copyfile(os.path.join(data_folder_path, csv), os.path.join(root_local, economy, csv))
    return None


def concat_all_merged_file_energy_files_from_local(config):
    all_data = pd.DataFrame()
    for economy in config['economies_list']:
        #get the date of the latest file
        if not os.path.exists(os.path.join('input_data', economy)):
            continue
        date_id = get_latest_date_for_data_file(os.path.join('input_data', economy), file_name_start='merged_file_energy', file_name_end='.csv', EXCLUDE_DATE_STR_START=False)
        #get all the files in the local folder
        all_files = os.listdir(os.path.join('input_data', economy))
        #filter for only the files with the correct file extension
        latest_file = [file for file in all_files if date_id in file and 'merged_file_energy' in file]
        if len(latest_file) == 0:
            # raise ValueError
            print(f'No files found for {economy} on {date_id}')
        elif len(latest_file) > 1:
            print(f'Multiple files found for {economy} on {date_id}')
            breakpoint()
            raise ValueError
        else:
            latest_file = latest_file[0]
        
        all_data = pd.concat([all_data, pd.read_csv(os.path.join('input_data', economy, latest_file))])
    return all_data

def clean_results_for_outlook(projections, apec_aggregate):
    #use the following labels:
    #     sectors	sub1sectors	sub2sectors	sub3sectors	sub4sectors	fuels	subfuels
    # 16_other_sector	16_01_buildings	x	x	x	17_electricity	x
    #get toal energy use and call it value
    #first metl so that apec_aggregate['data_energy_use'] and apec_aggregate['ai_training_energy_use'] are in the sae column and create a column with their names as ;sub4sectors'
    apec_aggregate = apec_aggregate.melt(id_vars=['year', 'economy'], value_vars=['traditional_data_energy_use', 'ai_training_energy_use'], var_name='sub4sectors', value_name='value')
    # apec_aggregate = apec_aggregate.rename(columns={'total_energy_use':'value'})
    apec_aggregate = apec_aggregate[['year', 'economy','sub4sectors', 'value']]
    apec_aggregate['economy'] = '00_APEC'
    apec_aggregate['sectors'] = '16_other_sector'
    apec_aggregate['sub1sectors'] = '16_01_buildings'
    apec_aggregate['sub2sectors'] = '16_01_01_commercial_and_public_services'
    apec_aggregate['sub3sectors'] = '16_01_01_02_data_centres'
    apec_aggregate['sub4sectors'] = np.where(apec_aggregate['sub4sectors']=='traditional_data_energy_use', '16_01_04_traditional_data_centres', '16_01_03_ai_training')
    apec_aggregate['fuels'] = '17_electricity'
    apec_aggregate['subfuels'] = 'x'
    apec_aggregate['subtotal_layout'] = False
    apec_aggregate['subtotal_results'] = False
    
    #add the reference and target scenarios   
    apec_aggregate_ref = apec_aggregate.copy()
    apec_aggregate_tgt = apec_aggregate.copy()
    apec_aggregate_ref['scenarios'] = 'reference'
    apec_aggregate_tgt['scenarios'] = 'target'
    
    #do same for projections
    projections = projections.melt(id_vars=['year', 'economy'], value_vars=['traditional_data_energy_use', 'ai_training_energy_use'], var_name='sub4sectors', value_name='value')
    # projections['value'] = projections['data_energy_use'] + projections['ai_training_energy_use']
    projections = projections[['year', 'economy','sub4sectors', 'value']]
    projections['sectors'] = '16_other_sector'
    projections['sub1sectors'] = '16_01_buildings'
    projections['sub2sectors'] = '16_01_01_commercial_and_public_services'
    projections['sub3sectors'] = '16_01_01_02_data_centres'
    projections['sub4sectors'] = np.where(projections['sub4sectors']=='traditional_data_energy_use', '16_01_04_traditional_data_centres', '16_01_03_ai_training')
    projections['fuels'] = '17_electricity'
    projections['subfuels'] = 'x'
    projections['subtotal_layout'] = False
    projections['subtotal_results'] = False
    
    #add the reference and target scenarios   
    projections_ref = projections.copy()
    projections_tgt = projections.copy()
    projections_ref['scenarios'] = 'reference'
    projections_tgt['scenarios'] = 'target'
    
    #combine the dataframes
    outlook_results = pd.concat([apec_aggregate_ref, apec_aggregate_tgt, projections_ref, projections_tgt])
    
    return outlook_results
    

def aggregate_apec_values(projections, config):
    
    confidence_intervals = config['confidence_intervals_percentage_error']
    # Initialize APEC aggregate DataFrame
    apec_aggregate = projections.groupby('year').sum().reset_index()
    apec_aggregate['economy'] = 'APEC'
    
    # Recalculate intensity for APEC
    apec_aggregate['data_intensity'] = (apec_aggregate['traditional_data_energy_use'] + apec_aggregate['ai_training_energy_use']) / (apec_aggregate['traditional_data_activity'] + apec_aggregate['ai_training_activity'])
    
    def calculate_confidence_interval_simple(metric_values, ci_value):
        # Calculate the confidence interval based on a simple percentage error
        lower = metric_values * (1 - ci_value)
        upper = metric_values * (1 + ci_value)
        return lower, upper

    # Calculate confidence intervals for each metric
    for metric, ci_value in confidence_intervals.items():
        metric_values = apec_aggregate[metric]
        lower, upper = calculate_confidence_interval_simple(metric_values, ci_value)
        apec_aggregate[f'{metric}_lower'] = lower
        apec_aggregate[f'{metric}_upper'] = upper
        
        
    # Calculate confidence intervals for energy use based on intensity and activity CIs
    apec_aggregate['traditional_data_energy_use'] = apec_aggregate['traditional_data_activity'] * apec_aggregate['data_intensity']
    apec_aggregate['traditional_data_energy_use_lower'] = apec_aggregate['traditional_data_activity_lower'] * apec_aggregate['data_intensity_lower']
    apec_aggregate['traditional_data_energy_use_upper'] = apec_aggregate['traditional_data_activity_upper'] * apec_aggregate['data_intensity_upper']
    
    apec_aggregate['ai_training_energy_use'] = apec_aggregate['ai_training_activity'] * apec_aggregate['data_intensity']
    apec_aggregate['ai_training_energy_use_lower'] = apec_aggregate['ai_training_activity_lower'] * apec_aggregate['data_intensity_lower']
    apec_aggregate['ai_training_energy_use_upper'] = apec_aggregate['ai_training_activity_upper'] * apec_aggregate['data_intensity_upper']
    
    apec_aggregate['total_energy_use'] = apec_aggregate['traditional_data_energy_use'] + apec_aggregate['ai_training_energy_use']
    apec_aggregate['total_energy_use_lower'] = apec_aggregate['traditional_data_energy_use_lower'] + apec_aggregate['ai_training_energy_use_lower']
    apec_aggregate['total_energy_use_upper'] = apec_aggregate['traditional_data_energy_use_upper'] + apec_aggregate['ai_training_energy_use_upper']
    
    return apec_aggregate


def save_outputs(outlook_results):
    #make it so the years are pivoted
    outlook_results = outlook_results.pivot(index=['scenarios','economy','sectors','sub1sectors','sub2sectors','sub3sectors','sub4sectors','fuels','subfuels','subtotal_layout','subtotal_results'], columns='year', values='value').reset_index()
    breakpoint()
    ###############
    #also, TEMP FIX we are going to change things so the sub2sectr is the sub4sectr, and the sub3sectr and sub4sectr are x
    outlook_results['sub2sectors'] = outlook_results['sub4sectors']
    outlook_results['sub3sectors'] = 'x'
    outlook_results['sub4sectors'] = 'x'
    #we should impelment this at the beginning of the code, but for now we will do it here since there will have to be some thigns changed in the plotting and so on
    ###############
    #save  outlook energy to csv in output_data
    file_date = datetime.datetime.now().strftime("%Y%m%d")
    outlook_results.to_csv(os.path.join('output_data', f'data_centres_energy_{file_date}.csv'), index=False)
    #get the economies
    economies = outlook_results['economy'].unique()
    for economy in economies:
        economy_results = outlook_results.loc[outlook_results['economy']==economy].copy()
        # economy_results = economy_results.drop(columns='economy')
        economy_results.to_csv(os.path.join('output_data', 'by_economy', f'data_centres_energy_{economy}_{file_date}.csv'), index=False)