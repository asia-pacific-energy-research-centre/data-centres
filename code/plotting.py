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
    fig_energy_path = os.path.join(output_dir, 'data_centres_energy_use_area_by_economy.html')
    fig_energy.write_html(fig_energy_path)
    print(f'Saved energy area plot to {fig_energy_path}')
    
    #and do a twh version
    energy['value'] = energy['value'] / 3.6
    fig_energy = px.area(energy, x='year', y='value', 
                         title='Energy Usage by Sector', labels={'value': 'Energy Use (TWh)', 'year': 'Year'}, 
                         color='variable', facet_col='economy', facet_col_wrap=7)
    fig_energy.update_yaxes(matches=None, showticklabels=True)
    fig_energy_path = os.path.join(output_dir, 'data_centres_energy_use_area_by_economy_TWh.html')
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
    fig_energy_path = os.path.join(output_dir, 'data_centres_energy_use_area_by_economy_all.html')
    fig_energy = fig_energy.update_layout(legend_title='Economy')
    fig_energy.write_html(fig_energy_path)
    ##
    #and by twh
    energy['value'] = energy['value'] / 3.6
    fig_energy = px.area(energy, x='year', y='value',title='Energy Usage by Economy', labels={'value': 'Energy Use (TWh)', 'year': 'Year'}, color='economy')
    fig_energy_path = os.path.join(output_dir, 'data_centres_energy_use_area_by_economy_all_TWh.html')
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
    outlook_energy_buildings['color'] = np.where(outlook_energy_buildings['sub3sectors']=='16_01_01_02_data_centres', outlook_energy_buildings['sub4sectors'], outlook_energy_buildings['sub3sectors'])
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
    outlook_electricity_APEC['color'] = np.where(outlook_electricity_APEC['sectors']=='12_total_final_consumption', outlook_electricity_APEC['sectors'], outlook_electricity_APEC['sub4sectors'])   
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
    
    #plot these by economy
    for economy in outlook_energy_buildings['economy'].unique():
        outlook_energy_buildings_econ = outlook_energy_buildings.loc[outlook_energy_buildings['economy']==economy].copy()
        outlook_electricity_econ = outlook_electricity.loc[outlook_electricity['economy']==economy].copy()
        #we will plot all charts we want in one dashboard. so that will be:
        #energy use in buildings by sector - target
        #energy use in buildings by sector - reference
        #whole economy electricity use compared to data centre electricity use - target
        #whole economy electricity use compared to data centre electricity use - reference
        #data centre electricity use by subsector - target
        #data centre electricity use by subsector - reference
        
        #we will create a df which is the concat of the df's needed to make these plots and create a column called 'title' which will be the name of the plot
        #we will then use this column to facet the plots:
        outlook_energy_buildings_econ['title'] = np.where(outlook_energy_buildings_econ['scenarios']=='reference', 'Energy Use in Buildings by Sector - Reference', 'Energy Use in Buildings by Sector - Target')
        outlook_electricity_econ['title'] = np.where(outlook_electricity_econ['scenarios']=='reference', 'Electricity Use by Sector - Reference', 'Electricity Use by Sector - Target')
        data_centres_energy = outlook_energy_buildings_econ.loc[outlook_energy_buildings_econ['sub3sectors']=='16_01_01_02_data_centres'].copy()
        data_centres_energy['title'] = np.where(data_centres_energy['scenarios']=='reference', 'Data Centre Electricity Use by Subsector - Reference', 'Data Centre Electricity Use by Subsector - Target')
        #create a color col in each df
        outlook_energy_buildings_econ['color'] = np.where(outlook_energy_buildings_econ['sub3sectors']=='16_01_01_02_data_centres', outlook_energy_buildings_econ['sub4sectors'], outlook_energy_buildings_econ['sub3sectors'])
        #also if a value is zero drop it (to get rid of empty sectors)
        outlook_energy_buildings_econ = outlook_energy_buildings_econ.loc[outlook_energy_buildings_econ['value']!=0].copy()
        
        outlook_electricity_econ['color'] = np.where(outlook_electricity_econ['sectors']=='12_total_final_consumption', outlook_electricity_econ['sectors'], outlook_electricity_econ['sub4sectors'])
        data_centres_energy['color'] = data_centres_energy['sub4sectors']        
        #concat
        all_data = pd.concat([outlook_energy_buildings_econ, outlook_electricity_econ, data_centres_energy])
        #group and sum alll:
        all_data = all_data.groupby(['year','color','title']).sum().reset_index()
        #plot
        fig_energy_econ = px.area(all_data, x='year', y='value', color='color', facet_col='title', facet_col_wrap=2,  title=f'Data centres energy usage dashbaord - {economy} - all other values are from first iteration', labels={'value': 'Energy Use (PJ)', 'year': 'Year'})
        #make the axis independent
        fig_energy_econ.update_yaxes(matches=None, showticklabels=True)
        fig_energy_econ_path = os.path.join('plotting_output', 'by_economy', f'energy_use_area_econ_{economy}.html')
        fig_energy_econ.write_html(fig_energy_econ_path)
        print(f'Saved energy area plot to {fig_energy_econ_path}')
        
