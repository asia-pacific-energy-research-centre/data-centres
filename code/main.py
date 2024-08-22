#%%
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

# Load the YAML configuration
with open('config/parameters.yml', 'r') as file:
    config = yaml.safe_load(file)


#############################################################
# Project Energy Use
#############################################################


def project_energy_use(config):
    start_year = config['start_year']
    end_year = config['end_year']
    all_projections = []

    for economy in config['economies']:
        name = economy['name']
        initial_data_growth_rate = economy['data_activity_growth_rate']
        initial_ai_growth_rate = economy['ai_training_activity_growth_rate']
        data_intensity_rate = economy['data_intensity_improvement_rate']
        ai_intensity_rate = economy['ai_training_intensity_improvement_rate']
        initial_ratio = economy['initial_data_to_ai_training_ratio']
        initial_energy = economy['initial_energy']
        scheduled_builds = economy.get('scheduled_builds', [])
        new_activity_growth_rates = economy.get('new_activity_growth_rates', [])
        
        years = np.arange(start_year, end_year + 1)
        df = pd.DataFrame(index=years)
        df['year'] = years
        df['economy'] = name
        
        # Set initial growth rates
        df['data_growth_rate'] = initial_data_growth_rate
        df['ai_growth_rate'] = initial_ai_growth_rate
        
        # Apply any new growth rates based on the specified years
        for new_rate in new_activity_growth_rates:
            if new_rate['year'] in years:
                df.loc[new_rate['year']:, 'data_growth_rate'] = new_rate['new_data_growth_rate']
                df.loc[new_rate['year']:, 'ai_growth_rate'] = new_rate['new_ai_growth_rate']
                
        # Initialize activity and intensity levels
        df['data_activity'] = initial_energy * initial_ratio
        df['ai_training_activity'] = initial_energy * (1 - initial_ratio)
        df['data_intensity'] = (initial_energy * initial_ratio) / df['data_activity'].iloc[0]
        df['ai_training_intensity'] = (initial_energy * (1 - initial_ratio)) / df['ai_training_activity'].iloc[0]
        
        # Project activities, intensities, and scheduled builds over time
        for year in range(start_year + 1, end_year + 1):
            prev_year = year - 1
            
            # Use the pre-set growth rates for the current year
            data_growth_rate = df.loc[year, 'data_growth_rate']
            ai_growth_rate = df.loc[year, 'ai_growth_rate']

            # Apply growth rates
            df.loc[year, 'data_activity'] = df.loc[prev_year, 'data_activity'] * (1 + data_growth_rate)
            df.loc[year, 'ai_training_activity'] = df.loc[prev_year, 'ai_training_activity'] * (1 + ai_growth_rate)
            
            # Apply intensity improvements
            df.loc[year, 'data_intensity'] = df.loc[prev_year, 'data_intensity'] * (1 - data_intensity_rate)
            df.loc[year, 'ai_training_intensity'] = df.loc[prev_year, 'ai_training_intensity'] * (1 - ai_intensity_rate)
            
            # Account for scheduled builds in the current year
            for build in scheduled_builds:
                if build['year'] == year:
                    total_energy = build['additional_energy']
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
                         title='Energy Usage by Sector', labels={'value': 'Energy Use (MWh)', 'year': 'Year'}, 
                         color='variable', facet_col='economy', facet_col_wrap=7)
    
    fig_energy.update_yaxes(matches=None, showticklabels=True)
    fig_energy_path = os.path.join(output_dir, 'energy_use_area.html')
    fig_energy.write_html(fig_energy_path)
    print(f'Saved energy area plot to {fig_energy_path}')
    
    # Prepare data for indexed activity line chart
    activity = projections[['data_activity_indexed', 'ai_training_activity_indexed', 'year', 'economy']]
    activity = activity.melt(id_vars=['year', 'economy'], var_name='variable', value_name='value')
    
    # Plot line chart for indexed activity by sector
    fig_activity = px.line(activity, x='year', y='value', 
                           title='Indexed Activity by Sector', labels={'value': 'Indexed Activity (Base Year = 100)', 'year': 'Year'}, 
                           color='variable', facet_col='economy', facet_col_wrap=7)
    
    fig_activity.update_yaxes(matches=None, showticklabels=True)
    fig_activity_path = os.path.join(output_dir, 'activity_indexed_line.html')
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
    fig_intensity_path = os.path.join(output_dir, 'intensity_line.html')
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
        yaxis_title='Energy Use (MWh)',
        legend_title='Metrics'
    )

    fig_energy_path = os.path.join('plotting_output', 'apec_energy_ci.html')
    fig_energy.write_html(fig_energy_path)
    print(f'Saved APEC total energy use plot with CI to {fig_energy_path}')

    
#%%
#############################################################
# Run projections and generate plots
projections = project_energy_use(config)
plot_projections(projections)
apec_aggregate = aggregate_apec_values(projections, config)
plot_apec_aggregate(apec_aggregate)
#############################################################
#%%
