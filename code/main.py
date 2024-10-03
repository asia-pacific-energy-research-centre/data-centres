
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
        initial_energy_pj = economy['initial_energy_pj']
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
        
        # Project activities, intensities, and scheduled builds over time
        for year in range(start_year + 1, end_year + 1):
            prev_year = year - 1
            
            # Use the pre-set growth rates for the current year
            data_growth_rate = df.loc[year, 'data_growth_rate']
            ai_growth_rate = df.loc[year, 'ai_growth_rate']
            data_intensity_improvement_rate = df.loc[year, 'data_intensity_improvement_rate']
            ai_intensity_improvement_rate = df.loc[year, 'ai_intensity_improvement_rate']
            
            # Apply growth rates
            df.loc[year, 'data_activity'] = df.loc[prev_year, 'data_activity'] * (1 + data_growth_rate)
            df.loc[year, 'ai_training_activity'] = df.loc[prev_year, 'ai_training_activity'] * (1 + ai_growth_rate)
            
            # Apply intensity improvements
            df.loc[year, 'data_intensity'] = df.loc[prev_year, 'data_intensity'] * (1 - data_intensity_improvement_rate) 
            df.loc[year, 'ai_training_intensity'] = df.loc[prev_year, 'ai_training_intensity'] * (1 - ai_intensity_improvement_rate)
            
            # Account for scheduled builds in the current year
            for build in scheduled_builds:
                if build['year'] == year:
                    total_energy = build['additional_energy_pj']
                    #calculate the energy use for data and ai_training using the ratio of the activities
                    data_energy = total_energy * (df.loc[year, 'data_activity'] / 
                                                  (df.loc[year, 'data_activity'] + df.loc[year, 'ai_training_activity']))
                    ai_training_energy = total_energy * (df.loc[year, 'ai_training_activity'] / 
                                                         (df.loc[year, 'data_activity'] + df.loc[year, 'ai_training_activity']))
                    
                    # Update activities based on the additional energy and current intensity
                    df.loc[year, 'data_activity'] += data_energy / df.loc[year, 'data_intensity']
                    df.loc[year, 'ai_training_activity'] += ai_training_energy / df.loc[year, 'ai_training_intensity']
        
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

def plot_projections(projections, output_dir='plotting_output'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Prepare data for energy use area chart
    energy = projections[['data_energy_use', 'ai_training_energy_use', 'year', 'economy']]
    energy = energy.melt(id_vars=['year', 'economy'], var_name='variable', value_name='value')
    
    # Plot area chart for energy use by sector
    fig_energy = px.area(energy, x='year', y='value', 
                         title='Energy Usage by Sector', labels={'value': 'Energy Use (PJ)', 'year': 'Year'}, 
                         color='variable', facet_col='economy', facet_col_wrap=7)
    
    fig_energy.update_yaxes(matches=None, showticklabels=True)
    fig_energy_path = os.path.join(output_dir, 'energy_use_area_by_economy.html')
    fig_energy.write_html(fig_energy_path)
    print(f'Saved energy area plot to {fig_energy_path}')
    
    #and do a twh version
    energy['value'] = energy['value'] / 3.6
    fig_energy = px.area(energy, x='year', y='value', 
                         title='Energy Usage by Sector', labels={'value': 'Energy Use (TWh)', 'year': 'Year'}, 
                         color='variable', facet_col='economy', facet_col_wrap=7)
    fig_energy.update_yaxes(matches=None, showticklabels=True)
    fig_energy_path = os.path.join(output_dir, 'energy_use_area_by_economy_TWh.html')
    fig_energy.write_html(fig_energy_path)
    print(f'Saved energy area plot to {fig_energy_path}')
    ##
    #and do one which is just all the economies together, no sectors:
    energy = projections[['data_energy_use', 'ai_training_energy_use', 'year', 'economy']]
    energy = energy.melt(id_vars=['year', 'economy'], var_name='variable', value_name='value')
    energy = energy.groupby(['year', 'economy']).sum().reset_index()
    #put economies in order of smallest to largest energy use sum
    energy = energy.sort_values('value')
    fig_energy = px.area(energy, x='year', y='value', 
                         title='Energy Usage by Economy', labels={'value': 'Energy Use (PJ)', 'year': 'Year'}, 
                         color='economy')
    fig_energy_path = os.path.join(output_dir, 'energy_use_area_by_economy_all.html')
    fig_energy = fig_energy.update_layout(legend_title='Economy')
    fig_energy.write_html(fig_energy_path)
    ##
    #and by twh
    energy['value'] = energy['value'] / 3.6
    fig_energy = px.area(energy, x='year', y='value',title='Energy Usage by Economy', labels={'value': 'Energy Use (TWh)', 'year': 'Year'}, color='economy')
    fig_energy_path = os.path.join(output_dir, 'energy_use_area_by_economy_all_TWh.html')
    fig_energy = fig_energy.update_layout(legend_title='Economy')
    fig_energy.write_html(fig_energy_path)
    ##
    # Prepare data for indexed activity line chart
    activity = projections[['data_activity_indexed', 'ai_training_activity_indexed', 'year', 'economy']]
    activity = activity.melt(id_vars=['year', 'economy'], var_name='variable', value_name='value')
    
    # Plot line chart for indexed activity by sector
    fig_activity = px.line(activity, x='year', y='value', 
                           title='Indexed Activity by Sector', labels={'value': 'Indexed Activity (Base Year = 100)', 'year': 'Year'}, 
                           color='variable', facet_col='economy', facet_col_wrap=7)
    
    fig_activity.update_yaxes(matches=None, showticklabels=True)
    fig_activity_path = os.path.join(output_dir, 'activity_indexed_line_by_economy.html')
    fig_activity.write_html(fig_activity_path)
    print(f'Saved activity index plot to {fig_activity_path}')

    # Prepare data for intensity line chart
    intensity = projections[['data_intensity', 'ai_training_intensity', 'year', 'economy']]
    intensity = intensity.melt(id_vars=['year', 'economy'], var_name='variable', value_name='value')
    
    # Plot line chart for intensity by sector
    fig_intensity = px.line(intensity, x='year', y='value', 
                             title='Intensity by Sector', labels={'value': 'Intensity', 'year': 'Year'}, 
                             color='variable', facet_col='economy', facet_col_wrap=7)
    
    fig_intensity.update_yaxes(matches=None, showticklabels=True)
    fig_intensity_path = os.path.join(output_dir, 'intensity_line_by_economy.html')
    fig_intensity.write_html(fig_intensity_path)
    print(f'Saved intensity plot to {fig_intensity_path}')

#%%
#############################################################
#APEC Aggregates
#############################################################

#%%
def aggregate_apec_values(projections, config):
    
    confidence_intervals = config['confidence_intervals_percentage_error']
    # Initialize APEC aggregate DataFrame
    apec_aggregate = projections.groupby('year').sum().reset_index()
    apec_aggregate['economy'] = 'APEC'
    
    # Recalculate intensity for APEC
    apec_aggregate['data_intensity'] = apec_aggregate['data_energy_use'] / apec_aggregate['data_activity']
    apec_aggregate['ai_training_intensity'] = apec_aggregate['ai_training_energy_use'] / apec_aggregate['ai_training_activity']
    
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
    apec_aggregate['data_energy_use'] = apec_aggregate['data_activity'] * apec_aggregate['data_intensity']
    apec_aggregate['data_energy_use_lower'] = apec_aggregate['data_activity_lower'] * apec_aggregate['data_intensity_lower']
    apec_aggregate['data_energy_use_upper'] = apec_aggregate['data_activity_upper'] * apec_aggregate['data_intensity_upper']
    
    apec_aggregate['ai_training_energy_use'] = apec_aggregate['ai_training_activity'] * apec_aggregate['ai_training_intensity']
    apec_aggregate['ai_training_energy_use_lower'] = apec_aggregate['ai_training_activity_lower'] * apec_aggregate['ai_training_intensity_lower']
    apec_aggregate['ai_training_energy_use_upper'] = apec_aggregate['ai_training_activity_upper'] * apec_aggregate['ai_training_intensity_upper']
    
    apec_aggregate['total_energy_use'] = apec_aggregate['data_energy_use'] + apec_aggregate['ai_training_energy_use']
    apec_aggregate['total_energy_use_lower'] = apec_aggregate['data_energy_use_lower'] + apec_aggregate['ai_training_energy_use_lower']
    apec_aggregate['total_energy_use_upper'] = apec_aggregate['data_energy_use_upper'] + apec_aggregate['ai_training_energy_use_upper']
    
    return apec_aggregate

def plot_apec_aggregate(apec_aggregate):

    # Function to add a trace for confidence intervals
    def add_confidence_interval(fig, x, y_upper, y_lower, fillcolor, name):
        fig.add_trace(go.Scatter(
            x=x,
            y=y_upper,
            mode='lines',
            line=dict(width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        fig.add_trace(go.Scatter(
            x=x,
            y=y_lower,
            mode='lines',
            line=dict(width=0),
            fill='tonexty',
            fillcolor=fillcolor,
            name=name,
            showlegend=True
        ))

    # Plot data and AI training activities with confidence intervals
    fig_activity = go.Figure()

    # Data Activity
    fig_activity.add_trace(go.Scatter(
        x=apec_aggregate['year'],
        y=apec_aggregate['data_activity'],
        mode='lines',
        name='Data Activity',
        line=dict(color='blue')
    ))

    add_confidence_interval(
        fig_activity,
        apec_aggregate['year'],
        apec_aggregate['data_activity_upper'],
        apec_aggregate['data_activity_lower'],
        fillcolor='rgba(0, 0, 255, 0.2)',
        name='Data Activity CI'
    )

    # AI Training Activity
    fig_activity.add_trace(go.Scatter(
        x=apec_aggregate['year'],
        y=apec_aggregate['ai_training_activity'],
        mode='lines',
        name='AI Training Activity',
        line=dict(color='green')
    ))
    add_confidence_interval(
        fig_activity,
        apec_aggregate['year'],
        apec_aggregate['ai_training_activity_upper'],
        apec_aggregate['ai_training_activity_lower'],
        fillcolor='rgba(0, 255, 0, 0.2)',
        name='AI Training Activity CI'
    )

    fig_activity.update_layout(
        title='APEC Aggregate - Activity with Confidence Intervals',
        xaxis_title='Year',
        yaxis_title='Activity',
        legend_title='Metrics'
    )

    fig_activity_path = os.path.join('plotting_output', 'apec_activity_ci.html')
    fig_activity.write_html(fig_activity_path)
    print(f'Saved APEC activity plot with CI to {fig_activity_path}')

    # Plot data and AI training intensity with confidence intervals
    fig_intensity = go.Figure()

    # Data Intensity
    fig_intensity.add_trace(go.Scatter(
        x=apec_aggregate['year'],
        y=apec_aggregate['data_intensity'],
        mode='lines',
        name='Data Intensity',
        line=dict(color='red')
    ))
    add_confidence_interval(
        fig_intensity,
        apec_aggregate['year'],
        apec_aggregate['data_intensity_upper'],
        apec_aggregate['data_intensity_lower'],
        fillcolor='rgba(255, 0, 0, 0.2)',
        name='Data Intensity CI'
    )

    # AI Training Intensity
    fig_intensity.add_trace(go.Scatter(
        x=apec_aggregate['year'],
        y=apec_aggregate['ai_training_intensity'],
        mode='lines',
        name='AI Training Intensity',
        line=dict(color='orange')
    ))
    add_confidence_interval(
        fig_intensity,
        apec_aggregate['year'],
        apec_aggregate['ai_training_intensity_upper'],
        apec_aggregate['ai_training_intensity_lower'],
        fillcolor='rgba(255, 165, 0, 0.2)',
        name='AI Training Intensity CI'
    )

    fig_intensity.update_layout(
        title='APEC Aggregate - Intensity with Confidence Intervals',
        xaxis_title='Year',
        yaxis_title='Intensity',
        legend_title='Metrics'
    )

    fig_intensity_path = os.path.join('plotting_output', 'apec_intensity_ci.html')
    fig_intensity.write_html(fig_intensity_path)
    print(f'Saved APEC intensity plot with CI to {fig_intensity_path}')

    # Plot total energy use with confidence intervals and sector breakdown
    fig_energy = go.Figure()

    # Total Energy Use
    fig_energy.add_trace(go.Scatter(
        x=apec_aggregate['year'],
        y=apec_aggregate['total_energy_use'],
        mode='lines',
        name='Total Energy Use',
        line=dict(color='purple')
    ))
    add_confidence_interval(
        fig_energy,
        apec_aggregate['year'],
        apec_aggregate['total_energy_use_upper'],
        apec_aggregate['total_energy_use_lower'],
        fillcolor='rgba(128, 0, 128, 0.2)',
        name='Total Energy Use CI'
    )

    # Data Energy Use (dashed line)
    fig_energy.add_trace(go.Scatter(
        x=apec_aggregate['year'],
        y=apec_aggregate['data_energy_use'],
        mode='lines',
        name='Data Energy Use',
        line=dict(color='blue', dash='dash')
    ))
    add_confidence_interval(
        fig_energy,
        apec_aggregate['year'],
        apec_aggregate['data_energy_use_upper'],
        apec_aggregate['data_energy_use_lower'],
        fillcolor='rgba(0, 0, 255, 0.2)',
        name='Data Energy Use CI'
    )

    # AI Training Energy Use (dashed line)
    fig_energy.add_trace(go.Scatter(
        x=apec_aggregate['year'],
        y=apec_aggregate['ai_training_energy_use'],
        mode='lines',
        name='AI Training Energy Use',
        line=dict(color='green', dash='dash')
    ))
    add_confidence_interval(
        fig_energy,
        apec_aggregate['year'],
        apec_aggregate['ai_training_energy_use_upper'],
        apec_aggregate['ai_training_energy_use_lower'],
        fillcolor='rgba(0, 255, 0, 0.2)',
        name='AI Training Energy Use CI'
    )

    fig_energy.update_layout(
        title='APEC Aggregate - Total Energy Use with Confidence Intervals',
        xaxis_title='Year',
        yaxis_title='Energy Use (PJ)',
        legend_title='Metrics'
    )

    fig_energy_path = os.path.join('plotting_output', 'apec_energy_ci.html')
    fig_energy.write_html(fig_energy_path)
    print(f'Saved APEC total energy use plot with CI to {fig_energy_path}')

def clean_results_for_outlook(projections, apec_aggregate):
    #use the following labels:
    #     sectors	sub1sectors	sub2sectors	sub3sectors	sub4sectors	fuels	subfuels
    # 16_other_sector	16_01_buildings	x	x	x	17_electricity	x
    
    #get toal energy use and call it value
    apec_aggregate = apec_aggregate.rename(columns={'total_energy_use':'value'})
    apec_aggregate = apec_aggregate[['year', 'economy', 'value']]
    apec_aggregate['economy'] = '00_APEC'
    apec_aggregate['sectors'] = '16_other_sector'
    apec_aggregate['sub1sectors'] = '16_01_buildings'
    apec_aggregate['sub2sectors'] = '16_01_01_commercial_and_public_services'
    apec_aggregate['sub3sectors'] = '16_01_01_02_data_centres'
    apec_aggregate['sub4sectors'] = 'x'
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
    projections['value'] = projections['data_energy_use'] + projections['ai_training_energy_use']
    projections = projections[['year', 'economy', 'value']]
    projections['sectors'] = '16_other_sector'
    projections['sub1sectors'] = '16_01_buildings'
    projections['sub2sectors'] = '16_01_01_commercial_and_public_services'
    projections['sub3sectors'] = '16_01_01_02_data_centres'
    projections['sub4sectors'] = 'x'
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

def import_and_compare_to_outlook_results(outlook_results, outlook_energy):

    #melt the df to long format ['scenarios	economy	sectors	sub1sectors	sub2sectors	sub3sectors	sub4sectors	fuels	subfuels	subtotal_layout	subtotal_results']
    outlook_energy = outlook_energy.melt(id_vars=['scenarios','economy','sectors','sub1sectors','sub2sectors','sub3sectors','sub4sectors','fuels','subfuels','subtotal_layout','subtotal_results'], var_name='year', value_name='value')
    
    outlook_energy_buildings = outlook_energy.loc[(outlook_energy['sectors']=='16_other_sector') & (outlook_energy['sub1sectors']=='16_01_buildings') & (~outlook_energy['fuels'].isin([ '17_x_green_electricity', '19_total', '20_total_renewables', '21_modern_renewables']))].copy()

    #create column outlook_energy_buildings['sub3sectors'] and set it to '16_01_01_01_commercial_and_public_services' where sub2sectors is '16_01_01_commercial_and_public_services', else set it to what it already is
    outlook_energy_buildings['sub3sectors'] = outlook_energy_buildings['sub2sectors']
    
    outlook_energy_buildings = outlook_energy_buildings.loc[outlook_energy_buildings['subtotal_layout']==False].copy()
    outlook_energy_buildings = outlook_energy_buildings.loc[outlook_energy_buildings['subtotal_results']==False].copy()

    outlook_electricity = outlook_energy.loc[(outlook_energy['sectors']=='12_total_final_consumption') & (outlook_energy['fuels']=='17_electricity')].copy()
    outlook_electricity = outlook_electricity.loc[outlook_electricity['subtotal_layout']==False].copy()
    outlook_electricity = outlook_electricity.loc[outlook_electricity['subtotal_results']==False].copy()
    
    # concat with outlook_results
    outlook_energy_buildings = pd.concat([outlook_energy_buildings, outlook_results])
    outlook_electricity = pd.concat([outlook_electricity, outlook_results])
    
    #where fuel is not electricity, label as other_fuel
    outlook_energy_buildings['fuels'] = np.where(outlook_energy_buildings['fuels']=='17_electricity', '17_electricity', 'other_fuel')
    outlook_energy_buildings['color'] = outlook_energy_buildings['sub3sectors']
    outlook_energy_buildings['pattern'] = outlook_energy_buildings['fuels']
    
    outlook_results_APEC = outlook_results.loc[outlook_results['economy']=='00_APEC'].copy()
    outlook_energy_APEC = outlook_energy.loc[outlook_energy['economy']=='00_APEC'].copy()
    outlook_energy_buildings_APEC = outlook_energy_buildings.loc[outlook_energy_buildings['economy']=='00_APEC'].copy()
    outlook_electricity_APEC = outlook_electricity.loc[outlook_electricity['economy']=='00_APEC'].copy()
    outlook_results = outlook_results.loc[outlook_results['economy']!='00_APEC'].copy()
    outlook_energy = outlook_energy.loc[outlook_energy['economy']!='00_APEC'].copy()
    outlook_energy_buildings = outlook_energy_buildings.loc[outlook_energy_buildings['economy']!='00_APEC'].copy()
    outlook_electricity = outlook_electricity.loc[outlook_electricity['economy']!='00_APEC'].copy()
    #now plot.
    #sum up by color,pattern,year,scenarios
    outlook_energy_buildings_scen = outlook_energy_buildings_APEC.groupby(['color','pattern','year','scenarios']).sum().reset_index()
    
    fig_energy_buildings = px.area(outlook_energy_buildings_scen, x='year', y='value', color='color', facet_col='scenarios', facet_col_wrap=2, pattern_shape='pattern', title='Energy Usage by Sector', labels={'value': 'Energy Use (PJ)', 'year': 'Year'})
    fig_energy_buildings_path = os.path.join('plotting_output', 'energy_use_area_buildings.html')
    fig_energy_buildings.write_html(fig_energy_buildings_path)
    print(f'Saved energy area plot to {fig_energy_buildings_path}')
    
    #write it again but for twh
    outlook_energy_buildings_scen['value'] = outlook_energy_buildings_scen['value'] / 3.6
    fig_energy_buildings = px.area(outlook_energy_buildings_scen, x='year', y='value', color='color', facet_col='scenarios', facet_col_wrap=2, pattern_shape='pattern', title='Energy Usage by Sector', labels={'value': 'Energy Use (TWh)', 'year': 'Year'})
    fig_energy_buildings_path = os.path.join('plotting_output', 'energy_use_area_buildings_TWh.html')
    fig_energy_buildings.write_html(fig_energy_buildings_path)
    print(f'Saved energy area plot to {fig_energy_buildings_path}')
    ##
    #BY ECONOMY: 
    outlook_energy_buildings_econ = outlook_energy_buildings.groupby(['economy', 'color','pattern','year','scenarios']).sum().reset_index()
    for scenario in outlook_energy_buildings_econ['scenarios'].unique():
        outlook_energy_buildings_scen = outlook_energy_buildings_econ.loc[outlook_energy_buildings_econ['scenarios']==scenario]
        fig_energy_buildings = px.area(outlook_energy_buildings_scen, x='year', y='value', color='color', facet_col='economy', facet_col_wrap=7, pattern_shape='pattern', title=f'Energy Usage by Sector and economy - {scenario}', labels={'value': 'Energy Use (PJ)', 'year': 'Year'})
        #make the axis independent
        fig_energy_buildings.update_yaxes(matches=None, showticklabels=True)
        fig_energy_buildings_path = os.path.join('plotting_output', f'energy_use_area_buildings_by_economy_{scenario}.html')
        fig_energy_buildings.write_html(fig_energy_buildings_path)
        print(f'Saved energy area plot to {fig_energy_buildings_path}')
        
        #write it again but for twh
        outlook_energy_buildings_scen['value'] = outlook_energy_buildings_scen['value'] / 3.6
        fig_energy_buildings = px.area(outlook_energy_buildings_scen, x='year', y='value', color='color', facet_col='scenarios', facet_col_wrap=2, pattern_shape='pattern', title=f'Energy Usage by Sector and economy - {scenario}', labels={'value': 'Energy Use (TWh)', 'year': 'Year'})
        #make the axis independent
        fig_energy_buildings.update_yaxes(matches=None, showticklabels=True)
        fig_energy_buildings_path = os.path.join('plotting_output', f'energy_use_area_buildings_TWh_by_economy_{scenario}.html')
        fig_energy_buildings.write_html(fig_energy_buildings_path)
        print(f'Saved energy area plot to {fig_energy_buildings_path}')
    #
    #concat the sectors for the color
    #make color the sectors where it is 12_total_final_consumption, then sub3sectors otherwise
    outlook_electricity_APEC['color'] = np.where(outlook_electricity_APEC['sectors']=='12_total_final_consumption', outlook_electricity_APEC['sectors'], outlook_electricity_APEC['sub3sectors'])   
    #sum up by color,year,scenarios
    outlook_electricity_APEC = outlook_electricity_APEC.groupby(['color','year','scenarios']).sum().reset_index()
    fig_energy_electricity = px.area(outlook_electricity_APEC, x='year', y='value', color='color', facet_col='scenarios', facet_col_wrap=2,  title='Energy Usage by Sector', labels={'value': 'Energy Use (PJ)', 'year': 'Year'})
    fig_energy_electricity_path = os.path.join('plotting_output', 'energy_use_area_electricity.html')
    fig_energy_electricity.write_html(fig_energy_electricity_path)
    print(f'Saved energy area plot to {fig_energy_electricity_path}')
    ##
    #write it again but for twh
    outlook_electricity_APEC['value'] = outlook_electricity_APEC['value'] / 3.6
    fig_energy_electricity = px.area(outlook_electricity_APEC, x='year', y='value', color='color', facet_col='scenarios', facet_col_wrap=2,  title='Energy Usage by Sector', labels={'value': 'Energy Use (TWh)', 'year': 'Year'})
    fig_energy_electricity_path = os.path.join('plotting_output', 'energy_use_area_electricity_TWh.html')
    fig_energy_electricity.write_html(fig_energy_electricity_path)
    print(f'Saved energy area plot to {fig_energy_electricity_path}')
    

def download_all_merged_file_energy_from_economys_from_onedrive(config):
    known_double_ups_and_their_solutions = ['merged_file_energy_10_MAS_20240905_TGT1.csv']
    breakpoint()
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
#%%
#############################################################
# Run projections and generate plots

# Load the YAML configuration
with open('config/parameters.yml', 'r') as file:
    config = yaml.safe_load(file)

projections = project_energy_use(config)
plot_projections(projections)
apec_aggregate = aggregate_apec_values(projections, config)
plot_apec_aggregate(apec_aggregate)
outlook_results = clean_results_for_outlook(projections, apec_aggregate)

file_date_id = get_latest_date_for_data_file('input_data', 'merged_file_energy_00_APEC_', file_name_end='.csv', EXCLUDE_DATE_STR_START=False)
outlook_energy_APEC = pd.read_csv(os.path.join('input_data', f'merged_file_energy_00_APEC_{file_date_id}.csv'))#this file can be found in Modelling\Integration\APEC\01_FinalEBT
DO_THIS=True
if DO_THIS:
    download_all_merged_file_energy_from_economys_from_onedrive(config)
#%%
outlook_energy_all_economies = concat_all_merged_file_energy_files_from_local(config) 

if outlook_energy_all_economies.columns.to_list() == outlook_energy_APEC.columns.to_list():
    outlook_energy_all_economies = pd.concat([outlook_energy_APEC, outlook_energy_all_economies])#assuming the structure is the same
else:
    raise ValueError
import_and_compare_to_outlook_results(outlook_results, outlook_energy_all_economies)

#save  outlook energy to csv in output_data
file_date = datetime.datetime.now().strftime("%Y%m%d")
outlook_results.to_csv(os.path.join('output_data', f'data_centres_energy_{file_date}.csv'), index=False)

#############################################################
#%%
